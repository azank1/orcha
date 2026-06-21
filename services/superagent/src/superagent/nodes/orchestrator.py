"""orchestrator_llm_node — core ReAct loop node.

Flow per turn:
    1. PnD gate (3-tier) — should we call PnD?
    2. Fetch system tool schemas
    3. If gate → call PnD for external agent candidates
    4. Merge all schemas → stream OpenRouter LLM via LangChain (AIMessageChunks)
    5. Return updated state
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import re as _re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI

from ..config import settings
from ..pnd.gate import pnd_gate
from ..runtime.session_cancel import (
    get_cancel_event,
    is_cancelled,
    session_id_from_config,
)
from ..startup.platform_mcp_baseline import get_baseline_openai_tools
from ..tool_call_parsing import normalize_stream_tool_calls

# ── Module-level LLM client singletons ────────────────────────────────────────
# Created once at import time; avoids TCP reconnect overhead on every turn.
_small_llm: AsyncOpenAI | None = None
_chat_llm: ChatOpenAI | None = None

_INVALID_FUNC_CHAR_RE = _re.compile(r"[^a-zA-Z0-9_-]")


def _get_small_llm() -> AsyncOpenAI:
    global _small_llm
    if _small_llm is None:
        _small_llm = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
    return _small_llm


def _get_chat_llm() -> ChatOpenAI:
    global _chat_llm
    if _chat_llm is None:
        _chat_llm = ChatOpenAI(
            model=settings.orchestrator_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            streaming=True,
            temperature=0,
            max_tokens=4096,
        )
    return _chat_llm


def _candidates_to_tools(candidates: list[dict]) -> list[dict]:
    """Rebuild OpenAI tool schemas from cached pnd_candidates state dicts."""
    tools: list[dict] = []
    for c in candidates:
        safe_id = _INVALID_FUNC_CHAR_RE.sub("_", c.get("agent_id", ""))
        protocol = (c.get("protocol_type") or "").upper()
        if protocol == "MCP":
            for cap in c.get("capabilities", []):
                if (cap.get("capability_type") or "TOOL").upper() != "TOOL":
                    continue
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": f"{safe_id}__{cap.get('capability_id', '')}",
                            "description": f"[{c.get('agent_name', '')}] {cap.get('description', '')}",
                            "parameters": cap.get("input_schema")
                            or {"type": "object", "properties": {}},
                        },
                    }
                )
        else:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": f"delegate__{safe_id}",
                        "description": f"Delegate task to {c.get('agent_name', '')}: {c.get('agent_description', '')}",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task": {
                                    "type": "string",
                                    "description": "Natural-language task description",
                                }
                            },
                            "required": ["task"],
                        },
                    },
                }
            )
    return tools


logger = logging.getLogger(__name__)

# OpenRouter → Google (and other providers) reject tool names outside this pattern.
_OPENAI_STYLE_TOOL_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


_SYSTEM_PROMPT = """\
You are MetaOrcha SuperAgent — a conversational AI orchestrator.
You help users accomplish complex tasks by delegating to specialised agents
(MCP tools, A2A agents) and using your system tools.

Guidelines:
- Use system tools (checklist, artifacts, workflow, memory) for task management.
- **Delegation priority:** When Planning & Discovery exposes external agents (tools whose names \
look like `delegate__…` or `<agent_id>__<capability>`), **prefer delegating** substantive work—\
especially lead generation, prospect research, CRM/email workflows, and domain-specific tasks—\
to those agents rather than solving everything with built-in platform MCP tools yourself.
- Use **platform / baseline MCP tools** (e.g. bundled web search, Tavily) only as a **fallback** \
when no suitable delegated agent exists in the current tool list, or when the user explicitly \
asks for a quick generic web lookup without involving an agent.
- For **finding leads**, **B2B outreach**, **drafting sales emails**, or similar: delegate to the \
**Lead Generation agent** (or another relevant PnD candidate), not generic web search first.
- Always acknowledge what you're doing before calling a tool.
- After completing a multi-step task, offer to save it as a reusable workflow.
- Be concise and direct.

Lead generation — Lead Gen Agent (A2A):
- Prefer naming the CRM in the delegated task (“save to HubSpot”) **or** set `crm_type` via
  `lead_gen_options` on `POST …/sessions/{id}/message` / `PATCH …/sessions/{id}/context`.
  The user must complete that CRM’s OAuth (or HubSpot PAT) in integrations before writes succeed.
- For ongoing outreach threads, stash memory in `email_campaign_context` (same APIs) — e.g. ICP summary,
  last campaign summary, tone — so you can draft consistent replies using Gmail MCP when the user forwards a reply.

Documents — tools and session artifacts:
- Session uploads appear as artifact IDs in [ARTIFACTS IN SESSION]. Users may refer \
to them in natural language; use those IDs, never invent paths.
- To read a session upload: call `stage_artifact(artifact_id=…)` first. It writes \
the file under /tmp/{session_id}/ and returns a JSON `path`. Then choose the right tool:
  • PDFs → pdf-reader `read_pdf` with `sources: [{path: "<staged_path>"}]`
  • All other formats (Word, Excel, PowerPoint, HTML, CSV, images, etc.) → markitdown \
`convert_to_markdown` with `uri: "file://<staged_path>"`
- To convert a document to a different file format (e.g. Markdown→PDF, DOCX→HTML): \
use doc-convert `convert_document` with `source_path`. After it writes an output file \
call `save_artifact(local_path=…)` to register it as a downloadable artifact.
- MCP tools usually return (A) plain text or JSON only, (B) a bare path string, or \
(C) JSON that includes a path field such as `output_path`. For any tool that writes \
a file under /tmp/{session_id}/, call `save_artifact(local_path=…)` with that path \
so the user gets a downloadable artifact id. Do not rely on implicit side channels.
- Use filesystem MCP only for small scratch files you author; not for bulk binary \
from S3.

CRITICAL — Tool discipline:
- You MUST only call tools that are explicitly listed in the tools array of this \
request. Do NOT invent, guess, or infer tool names from context or prior knowledge.
- If a capability you need is not in the current tool list, tell the user it is \
unavailable rather than calling a non-existent tool.
- External agent tools follow the naming pattern \
`<agent_id>__<capability_id>` (e.g. `did_metaorcha_agent_notion-mcp__search_notion`). \
Only call names that exactly match what appears in the tools list — never construct \
a tool name yourself.
- Built-in system tools use simple names with letters, digits, underscores, and hyphens \
only (e.g. `stage_artifact`, `save_artifact`, `read_artifact`, `create_checklist`) — \
same as in the tools list.
"""


def _format_checklist(checklist: Any) -> str:
    lines = [f"Goal: {getattr(checklist, 'goal', '')}"]
    for step in getattr(checklist, "steps", []):
        status = getattr(step, "status", "pending")
        icon = {"done": "✓", "failed": "✗", "in_progress": "→", "pending": "○"}.get(
            status, "○"
        )
        lines.append(f"  {icon} {getattr(step, 'description', '')}")
    return "\n".join(lines)


def _format_artifacts(artifacts: dict[str, Any]) -> str:
    """Format artifact refs as a system prompt block for the LLM."""
    lines = ["[ARTIFACTS IN SESSION]"]
    for art_id, ref in artifacts.items():
        filename = getattr(ref, "filename", art_id)
        mime = getattr(ref, "mime_type", "application/octet-stream")
        size_kb = getattr(ref, "size_bytes", 0) // 1024
        lines.append(
            f"- ID: {art_id} | Filename: {filename} | Type: {mime} | Size: {size_kb}KB\n"
            f'  → stage_artifact(artifact_id="{art_id}") for a local `path`, then doc-parse '
            f"with file_path / image_path / html_file, or doc-convert with source_path. "
            f"After MCP writes an output file under /tmp/, call save_artifact(local_path=…)."
        )
    return "\n".join(lines)


def _build_lc_messages(state: dict[str, Any]) -> list[Any]:
    """Build LangChain messages for the orchestrator (system + history)."""
    msgs: list[Any] = [SystemMessage(content=_SYSTEM_PROMPT)]

    artifacts = state.get("artifacts") or {}
    if artifacts:
        msgs.append(SystemMessage(content=_format_artifacts(artifacts)))

    checklist = state.get("task_checklist")
    if checklist is not None:
        checklist_text = _format_checklist(checklist)
        msgs.append(
            SystemMessage(content=f"## Active Task Checklist\n\n{checklist_text}")
        )

    lead_opts = state.get("lead_gen_options") or {}
    if isinstance(lead_opts, dict) and lead_opts:
        msgs.append(
            SystemMessage(
                content=(
                    "## Lead generation session options\n"
                    "Apply when delegating to the Lead Gen agent.\n\n"
                    f"{json.dumps(lead_opts, indent=2)}"
                )
            )
        )

    campaign_ctx = state.get("email_campaign_context") or {}
    if isinstance(campaign_ctx, dict) and campaign_ctx:
        msgs.append(
            SystemMessage(
                content=(
                    "## Email / outreach campaign context\n"
                    "Use when the user asks about replies, follow-ups, or thread continuity.\n\n"
                    f"{json.dumps(campaign_ctx, indent=2)}"
                )
            )
        )

    for msg in state.get("messages", []):
        if isinstance(msg, HumanMessage):
            msgs.append(HumanMessage(content=msg.content))
        elif isinstance(msg, (AIMessage, ToolMessage)):
            msgs.append(msg)
        elif isinstance(msg, SystemMessage):
            msgs.append(SystemMessage(content=msg.content))

    return msgs


def _lc_content_to_str(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return ""


def _tool_calls_from_stream_chunk(accumulated: Any) -> list[dict[str, Any]]:
    """Normalise LangChain streamed tool_calls to orchestrator AIMessage shape."""
    raw = getattr(accumulated, "tool_calls", None) or []
    return normalize_stream_tool_calls(raw, model_name=settings.orchestrator_model)


def _assert_openai_compatible_tool_names(all_tools: list[dict[str, Any]]) -> None:
    """Log provider-invalid tool names (OpenRouter/Google: ^[a-zA-Z0-9_-]{1,128}$)."""
    names = [str(t.get("function", {}).get("name", "")) for t in all_tools]
    invalid = [n for n in names if n and not _OPENAI_STYLE_TOOL_NAME.fullmatch(n)]
    if invalid:
        logger.error(
            "orchestrator_llm: tool name(s) violate provider pattern "
            "^[a-zA-Z0-9_-]{1,128}$ — request will likely fail: %s",
            invalid,
        )


def _dedupe_tools_by_name(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate tool schemas by function name — last entry wins.

    Walking in order means PnD tools (appended after baseline) override any
    baseline entry for the same capability name.
    """
    seen: dict[str, dict[str, Any]] = {}
    for tool in tools:
        name = tool.get("function", {}).get("name", "")
        seen[name] = tool
    return list(seen.values())


async def _accumulate_chat_stream(
    bound: Any,
    lc_messages: list[Any],
    config: RunnableConfig,
    session_id: str | None,
) -> Any:
    """Stream orchestrator tokens while listening for kill-switch cancel event."""
    stream = bound.astream(lc_messages, config=config)
    aiter = stream.__aiter__()
    accumulated: Any = None
    cancel_ev = get_cancel_event(session_id) if session_id else None
    while True:
        if session_id and is_cancelled(session_id):
            raise asyncio.CancelledError()
        anext_task = asyncio.create_task(aiter.__anext__())
        wait_set: set[asyncio.Task[Any]] = {anext_task}
        cancel_wait: asyncio.Task[bool] | None = None
        if cancel_ev is not None:
            cancel_wait = asyncio.create_task(cancel_ev.wait())
            wait_set.add(cancel_wait)
        done, pending = await asyncio.wait(
            wait_set, return_when=asyncio.FIRST_COMPLETED
        )
        for t in pending:
            t.cancel()
        if cancel_wait is not None and cancel_wait in done:
            anext_task.cancel()
            try:
                await anext_task
            except (asyncio.CancelledError, StopAsyncIteration):
                pass
            raise asyncio.CancelledError()
        try:
            chunk = anext_task.result()
        except StopAsyncIteration:
            break
        accumulated = chunk if accumulated is None else accumulated + chunk
    return accumulated


def _estimate_tokens_lc(messages: list[Any]) -> int:
    """Rough token estimate: 4 chars ≈ 1 token."""
    total = sum(
        len(str(_lc_content_to_str(getattr(m, "content", "")))) for m in messages
    )
    return total // 4


async def orchestrator_llm_node(
    state: dict[str, Any], config: RunnableConfig
) -> dict[str, Any]:
    """Orchestrator LLM node — called on every turn and after tool results."""
    from ..system_tools.registry import SYSTEM_TOOL_REGISTRY

    sid = session_id_from_config(config)
    if sid and is_cancelled(sid):
        logger.info("orchestrator_llm: skipping LLM — session %s cancelled", sid)
        return {
            "messages": [
                AIMessage(content="Execution was stopped — no further steps will run.")
            ],
            "estimated_token_count": state.get("estimated_token_count", 0),
            "_last_turn_tokens": 0,
            "_pending_events": [],
            "pnd_candidates": state.get("pnd_candidates") or [],
        }

    system_tools = SYSTEM_TOOL_REGISTRY.get_all_schemas()

    # ── PnD candidate resolution ───────────────────────────────────────────────
    # If the last message is a ToolMessage (i.e. we're processing a tool result,
    # not a fresh user query) reuse the candidates already in state — no need to
    # re-run hybrid search + cross-encoder for the same agent.
    messages = state.get("messages", [])
    cached_candidates: list[Any] = state.get("pnd_candidates", [])
    last_is_tool_result = messages and isinstance(messages[-1], ToolMessage)

    pnd_candidates: list[Any] = []
    pnd_tools: list[dict[str, Any]] = []

    if last_is_tool_result and cached_candidates:
        # Fast path: rebuild tool schemas from state — no network call
        pnd_candidates = cached_candidates
        pnd_tools = _candidates_to_tools(cached_candidates)
        logger.debug(
            "Orchestrator PnD cache hit (tool-result turn) — reusing %d candidate(s)",
            len(pnd_candidates),
        )
    else:
        needs_external = await pnd_gate(state, _get_small_llm(), settings.small_model)
        if needs_external:
            try:
                from superagent.nodes import _registry as _node_registry

                pnd_client = _node_registry.get("pnd_client")
                if pnd_client is None:
                    raise RuntimeError("PnD client not initialised")

                context = [
                    str(getattr(m, "content", ""))
                    for m in messages[-4:-1]
                    if hasattr(m, "content")
                ]
                human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
                last_human = human_msgs[-1] if human_msgs else None
                query = str(getattr(last_human, "content", "")) if last_human else ""

                resp = await pnd_client.get_candidates(
                    query=query,
                    conversation_context=context,
                    user_id=state.get("user_id", ""),
                    top_k=8,
                )
                # JSON-serialisable dicts only — avoids msgpack ToolCandidate warnings in Redis checkpoints
                pnd_candidates = [c.model_dump(mode="json") for c in resp.candidates]
                pnd_tools = resp.to_openai_tool_schemas()
                logger.info(
                    "PnD get_candidates ok candidates=%d external_tools=%d query_preview=%.120s",
                    len(pnd_candidates),
                    len(pnd_tools),
                    query.replace("\n", " "),
                )
            except Exception:
                logger.exception(
                    "PnD candidates call failed — continuing without external tools"
                )

    all_tools = system_tools + _dedupe_tools_by_name(
        get_baseline_openai_tools() + pnd_tools
    )
    lc_messages = _build_lc_messages(state)

    logger.debug(
        "Orchestrator LLM stream — tool_result_turn=%s pnd_candidates=%d "
        "system_tools=%d pnd_tools=%d total_tools=%d | tools=[%s]",
        last_is_tool_result,
        len(pnd_candidates),
        len(system_tools),
        len(pnd_tools),
        len(all_tools),
        ", ".join(t["function"]["name"] for t in all_tools),
    )

    chat = ChatOpenAI(
        model=settings.orchestrator_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        streaming=True,
        stream_usage=True,  # include usage chunk in stream so completion_tokens is real
        temperature=0,
        max_tokens=4096,
    )
    _assert_openai_compatible_tool_names(all_tools)
    bound = chat.bind_tools(all_tools) if all_tools else chat

    try:
        accumulated = await _accumulate_chat_stream(bound, lc_messages, config, sid)
    except asyncio.CancelledError:
        logger.info("orchestrator_llm: stream cancelled session_id=%s", sid)
        raise
    except Exception:
        logger.exception("Orchestrator LLM stream failed")
        raise

    if accumulated is None:
        ai_message = AIMessage(content="")
    elif isinstance(accumulated, AIMessage):
        ai_message = accumulated
    else:
        text = _lc_content_to_str(getattr(accumulated, "content", None))
        tool_calls = _tool_calls_from_stream_chunk(accumulated)
        ai_message = AIMessage(content=text, tool_calls=tool_calls)

    # Extract real completion_tokens from OpenRouter usage metadata.
    # LangChain surfaces this as usage_metadata.output_tokens when stream_usage=True.
    # Falls back to a rough estimate only if the API didn't return usage.
    usage = (
        getattr(accumulated, "usage_metadata", None)
        if accumulated is not None
        else None
    )
    if usage and usage.get("output_tokens"):
        completion_tokens: int = int(usage["output_tokens"])
    else:
        # Fallback: estimate from response content length (4 chars ≈ 1 token)
        response_text = _lc_content_to_str(getattr(ai_message, "content", ""))
        completion_tokens = max(1, len(response_text) // 4)
        logger.debug(
            "orchestrator: no usage metadata from OpenRouter — estimated completion_tokens=%d",
            completion_tokens,
        )

    estimated_tokens = _estimate_tokens_lc(lc_messages)

    updates: dict[str, Any] = {
        "messages": [ai_message],
        "estimated_token_count": estimated_tokens,
        # Actual output tokens for this turn — used by pipeline.py PaymentSettlement
        # to compute PLATFORM_TOKEN_RATE × completion_tokens cost.
        "_last_turn_tokens": completion_tokens,
        "_pending_events": [],
    }
    updates["pnd_candidates"] = pnd_candidates
    return updates
