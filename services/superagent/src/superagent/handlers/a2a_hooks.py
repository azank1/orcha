"""A2A capability hooks — domain-specific request enrichment and interrupt
auto-answering, decoupled from the generic A2A transport handler.

The default hook (LeadGenOptionsHook) carries the lead-gen CRM behavior that
used to be inline in a2a_handler.py. Embedders/tests may register a different
hook via register_a2a_hook().
"""

from __future__ import annotations

import json
from typing import Any, Protocol, runtime_checkable

from internal_commons.interrupts.types import InterruptType

_LEAD_GEN_ALLOW_KEYS = (
    "crm_type",
    "write_to_crm",
    "send_outreach_email",
    "max_leads",
    "tenant_id",
)

_KNOWN_CRMS = {"hubspot", "gsheets", "notion", "excel"}


def infer_crm_choice_from_task(task: str) -> str | None:
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


@runtime_checkable
class A2ACapabilityHook(Protocol):
    """Domain hook the generic A2AHandler calls per agent call."""

    def enrich_request_parts(
        self, task: str, state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Compose A2A message parts for the outgoing message/send."""
        ...

    def auto_answer_interrupt(
        self, interrupt_type: InterruptType, task: str, state: dict[str, Any]
    ) -> str | None:
        """Return a JSON answer string to auto-resume an interrupt, or None to
        escalate to the user via the normal interrupt flow."""
        ...


class LeadGenOptionsHook(A2ACapabilityHook):
    """Default hook: lead-gen CRM options passthrough + CRM_SETUP auto-resume."""

    def enrich_request_parts(
        self, task: str, state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        parts: list[dict[str, Any]] = [{"kind": "text", "text": task}]
        opts_src = dict(state.get("lead_gen_options") or {})
        inferred = infer_crm_choice_from_task(task)
        if inferred and "crm_type" not in opts_src:
            opts_src["crm_type"] = inferred
        blob = {k: opts_src[k] for k in _LEAD_GEN_ALLOW_KEYS if k in opts_src}
        if blob:
            parts.append({"kind": "data", "data": blob})
        return parts

    def auto_answer_interrupt(
        self, interrupt_type: InterruptType, task: str, state: dict[str, Any]
    ) -> str | None:
        if interrupt_type != InterruptType.CRM_SETUP:
            return None
        preferred_crm = infer_crm_choice_from_task(task)
        if preferred_crm not in _KNOWN_CRMS:
            return None
        return json.dumps({"crm_type": preferred_crm})


_default_hook: A2ACapabilityHook = LeadGenOptionsHook()


def register_a2a_hook(hook: A2ACapabilityHook) -> None:
    """Replace the process-wide A2A capability hook (tests, embedders)."""
    global _default_hook
    _default_hook = hook


def get_a2a_hook() -> A2ACapabilityHook:
    return _default_hook
