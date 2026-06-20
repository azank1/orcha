"""A2AHandler — stateful A2A task lifecycle with polling and HITL clarification.

Interrupt mechanics
-------------------
A downstream A2A agent can signal a pause in two distinct ways:

1. **A2A protocol** — the task transitions to ``input-required`` (or ``auth-required``)
   during polling.  The handler inspects the task metadata to route this to
   either HITL_APPROVAL (destructive action) or AGENT_CLARIFICATION (free text
   question), then calls ``interrupt()`` to suspend the graph.

2. **Escaped LangGraph interrupt** — the A2A agent is itself a LangGraph graph
   and called ``langgraph.interrupt()`` internally.  That propagates as an
   unhandled exception, causing the task to ``fail`` with the interrupt payload
   serialised in the error message.  The handler detects this pattern, parses
   the payload, and promotes it to an interrupt event — exactly as if the task
   had entered ``input-required``.

In both cases the resume path is ``message/send`` with the original ``taskId``
so the downstream agent continues the same task context.  The interrupt
metadata always carries ``task_id`` and ``endpoint`` for the frontend/gateway
to echo back in ``Command(resume=...)``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import secrets
import urllib.parse
import uuid
from typing import Any

import httpx
from internal_commons.interrupts import (
    AgentClarificationMetadata,
    AgentOAuthCallbackMetadata,
    CrmSetupMetadata,
    HitlApprovalMetadata,
    InterruptEvent,
    InterruptType,
)
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from .base import AgentHandler

logger = logging.getLogger(__name__)

_POLL_INITIAL = 0.5  # first status check after 500 ms
_POLL_MAX = 2.0  # cap per interval
_MAX_POLLS = 240  # 240 × avg ~2 s ≈ 8-minute budget

# Maps raw A2A / LangGraph interrupt_type strings → canonical InterruptType.
# Unknown values fall back to AGENT_CLARIFICATION.
_A2A_INTERRUPT_TYPE_MAP: dict[str, InterruptType] = {
    "clarify": InterruptType.AGENT_CLARIFICATION,
    "clarification": InterruptType.AGENT_CLARIFICATION,
    "approval": InterruptType.HITL_APPROVAL,
    "approve": InterruptType.HITL_APPROVAL,
    "auth": InterruptType.AGENT_OAUTH_CALLBACK,
    "auth-required": InterruptType.AGENT_OAUTH_CALLBACK,
    # Lead Gen Agent (and other agents that manage their own OAuth) use this type
    # to signal an agent-side OAuth flow with an auth_url already embedded in metadata.
    "oauth_required": InterruptType.AGENT_OAUTH_CALLBACK,
    "oauth-required": InterruptType.AGENT_OAUTH_CALLBACK,
    # CRM selection — agent needs the user to connect a CRM before it can write results.
    "crm_setup": InterruptType.CRM_SETUP,
}


def _map_interrupt_type(raw: str) -> InterruptType:
    return _A2A_INTERRUPT_TYPE_MAP.get(
        raw.strip().lower(), InterruptType.AGENT_CLARIFICATION
    )


def _extract_text_from_message(msg: Any) -> str:
    """Pull plain text from an A2A message object or raw string."""
    if isinstance(msg, str):
        return msg
    if isinstance(msg, dict):
        parts = msg.get("parts", [])
        return " ".join(
            p.get("text", "") for p in parts if p.get("kind") == "text"
        ).strip()
    return str(msg)


def _classify_input_required(
    task_state: dict[str, Any],
) -> tuple[InterruptType, str, dict[str, Any]]:
    """
    Determine whether an input-required task state is an approval or clarification.

    Returns:
        (interrupt_type, question_text, extra_metadata)

    Decision tree (first match wins):
    1. ``metadata.interrupt_type`` on the task or its status message — explicit signal.
    2. ``metadata.pending_tool`` on the task — Google Workspace Orchestrator HITL approval.
    3. Text heuristics — "approval required" / "approve … deny" in message text.
    4. Default → AGENT_CLARIFICATION.
    """
    status_obj = task_state.get("status", {}) or {}
    status_msg = status_obj.get("message", {}) or {}
    task_meta = task_state.get("metadata", {}) or {}
    msg_meta = status_msg.get("metadata", {}) if isinstance(status_msg, dict) else {}

    question = (
        _extract_text_from_message(status_msg) or "The agent needs more information."
    )

    # 1. Explicit hint
    hint = (
        msg_meta.get("interrupt_type") or task_meta.get("interrupt_type") or ""
    ).lower()
    if hint:
        return _map_interrupt_type(hint), question, {**msg_meta, **task_meta}

    # 2. Google Workspace Orchestrator HITL (has pending_tool in task metadata)
    if task_meta.get("pending_tool"):
        return InterruptType.HITL_APPROVAL, question, task_meta

    # 3. Text heuristics
    q_lower = question.lower()
    if "approval required" in q_lower or ("approve" in q_lower and "deny" in q_lower):
        return InterruptType.HITL_APPROVAL, question, task_meta

    return InterruptType.AGENT_CLARIFICATION, question, {**msg_meta, **task_meta}


def _parse_escaped_interrupt(error_text: str) -> dict[str, Any] | None:
    """
    Detect a LangGraph interrupt that escaped from an A2A agent as a ``failed``
    task error message.

    When an A2A agent built on LangGraph calls ``interrupt()`` internally and
    its server doesn't handle the GraphInterrupt, the exception is caught by
    the agent's generic error handler and the str(exc) is returned as the task
    failure message.  It looks like::

        (Interrupt(value={'interrupt_id': 'clarify__...', 'interrupt_type': 'clarify',
                          'message': {...}, 'metadata': {...}}, id='abc...'))

    Returns the parsed interrupt value dict, or None if the text does not
    contain a recognisable interrupt payload.
    """
    if "Interrupt(value=" not in error_text and "interrupt_type" not in error_text:
        return None

    # Try to pull out the value={...} portion and round-trip through JSON.
    # The regex is deliberately liberal — stop at the last } before ', id='.
    try:
        m = re.search(r"Interrupt\(value=(\{.+\}),\s*id=", error_text, re.DOTALL)
        if m:
            raw = m.group(1)
            # Python repr → JSON: single-quote strings, Python bool/None literals.
            raw = re.sub(
                r"'([^'\\]*(?:\\.[^'\\]*)*)'", lambda x: '"' + x.group(1) + '"', raw
            )
            raw = (
                raw.replace("True", "true")
                .replace("False", "false")
                .replace("None", "null")
            )
            return json.loads(raw)
    except Exception as exc:
        logger.debug("Could not parse interrupt payload from error text: %s", exc)

    # If full parse fails but the text clearly is an interrupt, return a stub
    # so the caller knows to surface a generic clarification.
    if "interrupt" in error_text.lower():
        return {
            "interrupt_type": "clarify",
            "_escaped": True,
            "_raw": error_text[:500],
        }
    return None


def _escape_to_input_required(escaped: dict[str, Any], task_id: str) -> dict[str, Any]:
    """Synthesise a task_state dict for an escaped interrupt, mimicking input-required."""
    raw_msg = escaped.get("message", {})
    hint_type = escaped.get("interrupt_type", "clarify")
    meta = {**(escaped.get("metadata") or {}), "interrupt_type": hint_type}
    return {
        "status": {"state": "input-required", "message": raw_msg},
        "metadata": meta,
        # Preserve the original (escaped) task_id from the interrupt metadata
        # so _send_clarification targets the right task.
        "_escaped_task_id": escaped.get("metadata", {}).get("task_id") or task_id,
    }


def _resume_value_to_text(resume_value: Any) -> str:
    """
    Map a resume payload from ``Command(resume=...)`` to the text string
    the A2A agent expects via ``message/send``.

    HITL_APPROVAL resume values carry ``status: "approved"/"denied"`` and
    optionally ``edited_drafts`` (list of draft dicts with edits applied by the user).
    When edited_drafts are present the entire payload is JSON-serialised so the
    downstream agent's ``_parse_resume_data`` can reconstruct it.

    AGENT_CLARIFICATION resume values carry free text or an ``answer`` key.
    """
    if isinstance(resume_value, dict):
        # If user edited drafts, send full JSON so the agent can apply edits.
        if "edited_drafts" in resume_value:
            return json.dumps(resume_value)
        status = (resume_value.get("status") or "").lower()
        if status in ("approved", "approve"):
            return "approve"
        if status in ("denied", "deny"):
            return "deny"
        if status == "complete" and resume_value.get("response"):
            return str(resume_value["response"])
        # Free-text answer variants
        for key in ("answer", "value", "text", "message", "response"):
            if resume_value.get(key):
                return str(resume_value[key])
    if isinstance(resume_value, str):
        return resume_value
    return str(resume_value)


def _build_lead_gen_a2a_parts(task: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    """Compose A2A message parts: mandatory text plus optional structured opts for Lead Gen."""
    parts: list[dict[str, Any]] = [{"kind": "text", "text": task}]
    opts_src = dict(state.get("lead_gen_options") or {})
    inferred = _infer_crm_choice_from_task(task)
    if inferred and "crm_type" not in opts_src:
        opts_src["crm_type"] = inferred
    allow = (
        "crm_type",
        "write_to_crm",
        "send_outreach_email",
        "max_leads",
        "tenant_id",
    )
    blob = {k: opts_src[k] for k in allow if k in opts_src}
    if blob:
        parts.append({"kind": "data", "data": blob})
    return parts


def _infer_crm_choice_from_task(task: str) -> str | None:
    """Infer preferred CRM from user task text for CRM_SETUP auto-resume."""
    text = (task or "").lower()
    if any(
        k in text for k in ("excel", "xlsx", "spreadsheet in excel", "export to excel")
    ):
        return "excel"
    if any(
        k in text for k in ("google sheet", "google sheets", "gsheet", "spreadsheet")
    ):
        return "gsheets"
    if "notion" in text:
        return "notion"
    if "hubspot" in text:
        return "hubspot"
    return None


async def _fetch_auth_url_from_agent(
    transport_endpoint: str,
    cfg: dict[str, Any],
    session_id: str,
) -> str:
    """Call the agent's own OAuth connect endpoint to get a valid auth URL.

    Used when the manifest's client_id contains an unresolved placeholder
    (e.g. ${GOOGLE_CLIENT_ID}) that only the agent itself can expand.
    """
    scopes_str = " ".join(cfg.get("scopes", [])).lower()
    provider_hint = cfg.get("provider_hint", "").lower()

    if "gmail" in scopes_str:
        path = "gmail"
    elif "spreadsheets" in scopes_str or "drive.file" in scopes_str:
        path = "gsheets"
    elif provider_hint == "notion":
        path = "notion"
    elif provider_hint == "microsoft":
        path = "excel"
    else:
        logger.warning(
            "Cannot determine OAuth connect path for provider=%s scopes=%s",
            provider_hint,
            scopes_str[:80],
        )
        return ""

    connect_url = f"{transport_endpoint.rstrip('/')}/oauth/{path}/connect"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(connect_url, params={"tenant_id": session_id})
            resp.raise_for_status()
            return resp.json().get("auth_url", "")
    except Exception:
        logger.warning(
            "Failed to fetch auth URL from agent connect endpoint %s",
            connect_url,
            exc_info=True,
        )
        return ""


async def _build_oauth_interrupt(agent_id: str, session_id: str) -> InterruptEvent:
    """
    Build an AGENT_OAUTH_CALLBACK InterruptEvent directly from the agent's manifest.

    This mirrors the logic in PreFlightManager._build_auth_interrupt_event /
    _build_auth_url without requiring a full PreFlightManager instance (which
    needs a VaultClient). Called from inside the A2A poll loop when the downstream
    agent returns ``auth-required``.

    When the manifest's client_id contains an unresolved placeholder (e.g.
    ${GOOGLE_CLIENT_ID}), delegates to the agent's own connect endpoint to
    obtain a valid auth URL.
    """
    from ..middleware.manifest_cache import MANIFEST_CACHE

    manifest = await MANIFEST_CACHE.get_manifest(agent_id)
    display_name: str = manifest.get("name", agent_id)
    nonce = secrets.token_urlsafe(8)
    transport_endpoint: str = manifest.get("transport", {}).get("endpoint", "")

    security = manifest.get("security", {}) or {}
    oauth_strategy: dict[str, Any] = next(
        (
            s
            for s in (security.get("auth_strategies") or [])
            if s.get("type", "").upper() in ("OAUTH2", "OAUTH2_DCR")
        ),
        {},
    )
    cfg: dict[str, Any] = oauth_strategy.get("config", {}) or {}

    client_id = cfg.get("client_id", "")
    base_url = cfg.get("authorization_url", "")
    auth_url = ""

    # When client_id has an unresolved ${VAR} placeholder, the superagent cannot
    # expand it (the credential lives in the downstream agent). Delegate to the
    # agent's own connect endpoint which knows its own OAuth credentials.
    if "${" in client_id and transport_endpoint:
        auth_url = await _fetch_auth_url_from_agent(transport_endpoint, cfg, session_id)

    if not auth_url and base_url:
        url_params: dict[str, str] = {
            "client_id": client_id,
            "response_type": "code",
            "scope": " ".join(cfg.get("scopes") or []),
            "state": f"{session_id}:{agent_id}:{nonce}",
        }
        redirect_uri = cfg.get("redirect_uri", "")
        if redirect_uri:
            url_params["redirect_uri"] = redirect_uri
        auth_url = f"{base_url}?{urllib.parse.urlencode(url_params)}"

    meta = AgentOAuthCallbackMetadata(
        auth_url=auth_url,
        provider_name=cfg.get("provider_hint", display_name),
        scopes=list(cfg.get("scopes") or []),
        agent_id=agent_id,
    )
    return InterruptEvent(
        interrupt_type=InterruptType.AGENT_OAUTH_CALLBACK,
        interrupt_id=f"{agent_id}__auth__{nonce}",
        agent_id=agent_id,
        session_id=session_id,
        message=f"Authorization required for {display_name}",
        metadata=meta.model_dump(),
    )


def _a2a_progress_message(status: str, task_state: dict[str, Any]) -> str:
    if status == "working":
        return "Agent is processing…"
    if status == "submitted":
        return "Task submitted…"
    if status == "completed":
        return "Task completed"
    if status == "failed":
        return str(task_state.get("status", {}).get("message", "Task failed"))
    if status == "input-required":
        msg = task_state.get("status", {}).get(
            "message", "The agent needs more information."
        )
        return _extract_text_from_message(msg)
    return f"Status: {status}"


class A2AHandler(AgentHandler):
    """
    Handles A2A protocol agent calls.

    Flow: POST message/send → poll tasks/get → handle input-required → result.
    """

    async def send_task(
        self,
        agent_id: str,
        task: str,
        transport: dict[str, Any],
        state: dict[str, Any],
        config: RunnableConfig | None = None,
        call_id: str = "",
    ) -> Any:
        """Send a task to an A2A agent and poll until completion or HITL."""
        endpoint = transport.get("endpoint", "").rstrip("/")
        message_id = str(uuid.uuid4())
        session_id = str(state.get("session_id", ""))
        preferred_crm = _infer_crm_choice_from_task(task)

        logger.info(
            "a2a_handler: → send_task agent=%s call_id=%s endpoint=%s task_preview=%s",
            agent_id,
            call_id,
            endpoint,
            task[:400],
        )

        async with httpx.AsyncClient(
            headers=self._auth_headers, timeout=httpx.Timeout(30.0)
        ) as client:
            # Pass session_id in params.metadata so the downstream A2A agent can
            # look up the OAuth token it stored after the callback (keyed by session_id).
            # Optional data part: crm prefs + flags (see Lead Gen Agent main._handle_message_send).
            params: dict[str, Any] = {
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": _build_lead_gen_a2a_parts(task, state),
                },
            }
            if session_id:
                params["metadata"] = {"session_id": session_id}
            payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": params,
                "id": message_id,
            }
            resp = await client.post(f"{endpoint}/", json=payload)
            resp.raise_for_status()
            data = resp.json()

            task_id: str = (
                data.get("result", {}).get("id") or data.get("id") or message_id
            )

            last_poll_status: str | None = None
            _interval = _POLL_INITIAL

            for _ in range(_MAX_POLLS):
                await asyncio.sleep(_interval)
                _interval = min(_interval * 2, _POLL_MAX)
                task_state = await self._get_task(client, endpoint, task_id)
                status = task_state.get("status", {}).get("state", "unknown")

                if status != last_poll_status:
                    last_poll_status = status
                    await self.emit_event(
                        config,
                        {
                            "type": "invocation_progress",
                            "call_id": call_id,
                            "status": status,
                            "message": _a2a_progress_message(status, task_state),
                        },
                    )

                if status == "completed":
                    result_text = self._extract_result(task_state)
                    logger.info(
                        "a2a_handler: ← completed agent=%s task=%s result_preview=%s",
                        agent_id,
                        task_id,
                        result_text[:600],
                    )
                    return result_text

                if status == "failed":
                    raw_error = task_state.get("status", {}).get(
                        "message", "Task failed"
                    )
                    error_text = _extract_text_from_message(raw_error)

                    escaped = _parse_escaped_interrupt(error_text)
                    if escaped:
                        logger.info(
                            "a2a_handler: escaped LangGraph interrupt detected "
                            "agent=%s task=%s type=%s",
                            agent_id,
                            task_id,
                            escaped.get("interrupt_type"),
                        )
                        task_state = _escape_to_input_required(escaped, task_id)
                        status = "input-required"
                    else:
                        logger.warning(
                            "a2a_handler: task failed agent=%s task=%s error=%r",
                            agent_id,
                            task_id,
                            error_text[:200],
                        )
                        return f"Error: {error_text}"

                if status == "auth-required":
                    # The A2A agent explicitly signals it cannot proceed without OAuth.
                    # Build an AGENT_OAUTH_CALLBACK interrupt from the agent's manifest
                    # so the SuperAgent node-level handler triggers the standard OAuth
                    # flow (user clicks → callback → token stored → task retried with
                    # session_id in metadata → bearer found → task succeeds).
                    logger.info(
                        "a2a_handler: auth-required from A2A agent agent=%s task=%s",
                        agent_id,
                        task_id,
                    )
                    auth_event = await _build_oauth_interrupt(agent_id, session_id)
                    from ..middleware.preflight import AuthInterruptRequired

                    raise AuthInterruptRequired(auth_event)

                if status == "input-required":
                    interrupt_type, question, extra_meta = _classify_input_required(
                        task_state
                    )

                    # The effective task_id for resume may differ from the polled
                    # task_id when the interrupt escaped from a failed task.
                    resume_task_id = task_state.get("_escaped_task_id") or task_id

                    # Auto-resume CRM setup when user intent already names a CRM.
                    # This removes an unnecessary confirmation turn ("select Excel")
                    # while still allowing downstream OAuth/auth interrupts as needed.
                    if interrupt_type == InterruptType.CRM_SETUP and preferred_crm in {
                        "hubspot",
                        "gsheets",
                        "notion",
                        "excel",
                    }:
                        auto_answer = json.dumps({"crm_type": preferred_crm})
                        logger.info(
                            "a2a_handler: auto-resume CRM setup agent=%s task=%s crm=%s",
                            agent_id,
                            resume_task_id,
                            preferred_crm,
                        )
                        await self._send_clarification(
                            client,
                            endpoint,
                            resume_task_id,
                            auto_answer,
                            session_id=session_id,
                        )
                        continue

                    event = self._build_interrupt_event(
                        interrupt_type=interrupt_type,
                        question=question,
                        agent_id=agent_id,
                        session_id=session_id,
                        task_id=resume_task_id,
                        endpoint=endpoint,
                        extra_meta=extra_meta,
                    )

                    logger.info(
                        "a2a_handler: suspending graph agent=%s task=%s type=%s",
                        agent_id,
                        resume_task_id,
                        interrupt_type,
                    )
                    user_answer = interrupt(event.model_dump())
                    answer_text = _resume_value_to_text(user_answer)

                    if (
                        interrupt_type == InterruptType.HITL_APPROVAL
                        and answer_text == "deny"
                    ):
                        logger.info(
                            "a2a_handler: user denied action agent=%s task=%s",
                            agent_id,
                            resume_task_id,
                        )
                        return "Error: Action denied by user."

                    logger.info(
                        "a2a_handler: resuming A2A task agent=%s task=%s answer=%r",
                        agent_id,
                        resume_task_id,
                        answer_text,
                    )
                    await self._send_clarification(
                        client,
                        endpoint,
                        resume_task_id,
                        answer_text,
                        session_id=session_id,
                    )
                    # Fall through — continue polling for completion.

                # "working" | "submitted" → keep polling

            return "Error: Task timed out"

    # ── helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_interrupt_event(
        interrupt_type: InterruptType,
        question: str,
        agent_id: str,
        session_id: str,
        task_id: str,
        endpoint: str,
        extra_meta: dict[str, Any],
    ) -> InterruptEvent:
        """Construct the canonical InterruptEvent for a given interrupt type."""
        if interrupt_type == InterruptType.HITL_APPROVAL:
            pending_tool = extra_meta.get("pending_tool", "")
            agent_display = extra_meta.get("agent_display_name") or agent_id
            meta_obj = HitlApprovalMetadata(
                action_description=extra_meta.get("action_description") or question,
                risk_level=extra_meta.get("risk_level") or "medium",
                agent_display_name=agent_display,
                capability_name=extra_meta.get("capability_name")
                or (str(pending_tool) if pending_tool else ""),
            )
        elif interrupt_type == InterruptType.AGENT_OAUTH_CALLBACK:
            # Agent-managed OAuth: the agent already built the auth_url and embedded
            # it in interrupt_meta. Extract it directly — don't re-derive from manifest.
            auth_url = extra_meta.get("auth_url", "")
            provider = (
                extra_meta.get("provider")
                or extra_meta.get("provider_name")
                or extra_meta.get("agent_display_name")
                or agent_id
            )
            scopes = extra_meta.get("scopes", [])
            if isinstance(scopes, str):
                scopes = scopes.split()
            meta_obj = AgentOAuthCallbackMetadata(
                auth_url=auth_url,
                provider_name=str(provider),
                scopes=list(scopes),
                agent_id=agent_id,
            )
        elif interrupt_type == InterruptType.CRM_SETUP:
            meta_obj = CrmSetupMetadata(
                tenant_id=extra_meta.get("tenant_id", session_id),
                agent_display_name=extra_meta.get("agent_display_name", agent_id),
                lead_gen_url=extra_meta.get("lead_gen_url", "http://localhost:4567"),
            )
        else:
            # AGENT_CLARIFICATION (default) or any unrecognised type
            interrupt_type = InterruptType.AGENT_CLARIFICATION
            meta_obj = AgentClarificationMetadata(
                question=question,
                agent_display_name=agent_id,
                agent_id=agent_id,
            )

        extra: dict[str, Any] = {
            "task_id": task_id,
            "endpoint": endpoint,
        }
        # For HITL_APPROVAL: pass email drafts through so the frontend can
        # render them for review/editing before the user clicks Approve.
        if interrupt_type == InterruptType.HITL_APPROVAL and extra_meta.get("drafts"):
            extra["drafts"] = extra_meta["drafts"]
        if interrupt_type == InterruptType.CRM_SETUP:
            if extra_meta.get("options"):
                extra["options"] = extra_meta["options"]
            if extra_meta.get("connection_urls"):
                extra["connection_urls"] = extra_meta["connection_urls"]
            if extra_meta.get("resume_schema"):
                extra["resume_schema"] = extra_meta["resume_schema"]

        return InterruptEvent(
            interrupt_type=interrupt_type,
            interrupt_id=f"{interrupt_type.lower()}__{task_id}",
            agent_id=agent_id,
            session_id=session_id,
            message=question,
            metadata={**meta_obj.model_dump(), **extra},
        )

    @staticmethod
    async def _get_task(
        client: httpx.AsyncClient, endpoint: str, task_id: str
    ) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {"id": task_id},
            "id": task_id,
        }
        resp = await client.post(f"{endpoint}/", json=payload)
        resp.raise_for_status()
        return resp.json().get("result", {})

    @staticmethod
    async def _send_clarification(
        client: httpx.AsyncClient,
        endpoint: str,
        task_id: str,
        answer: str,
        session_id: str = "",
    ) -> None:
        params: dict[str, Any] = {
            "message": {
                "messageId": str(uuid.uuid4()),
                "taskId": task_id,
                "role": "user",
                "parts": [{"kind": "text", "text": answer}],
            },
        }
        if session_id:
            params["metadata"] = {"session_id": session_id}
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": params,
            "id": task_id,
        }
        resp = await client.post(f"{endpoint}/", json=payload)
        resp.raise_for_status()

    @staticmethod
    def _extract_result(task_state: dict[str, Any]) -> str:
        artifacts = task_state.get("artifacts", [])
        if artifacts:
            parts = []
            for art in artifacts:
                for part in art.get("parts", []):
                    if part.get("kind") == "text":
                        parts.append(part.get("text", ""))
            if parts:
                return "\n".join(parts)
        return _extract_text_from_message(
            task_state.get("status", {}).get("message", "Task completed")
        )
