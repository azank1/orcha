"""KY-A supervisor cyber guardrails — single-sourced tool allowlist (WS10 / FR-10.1).

When ``settings.kya_mode_enabled`` is true the supervisor run is scope-limited:

- External agent tools are restricted to the DIDs in
  ``settings.kya_allowed_agents`` (comma-separated).
- System tools are restricted to :data:`KYA_ALLOWED_SYSTEM_TOOLS`.
- Baseline/platform MCP tools are not exposed at all.

The allowlist defined here is consumed by BOTH enforcement seams —
``nodes/orchestrator.py`` (filters the tool list shown to the LLM) and
``nodes/execute_agent_calls.py`` (rejects a disallowed call with an error
ToolMessage instead of executing it). Keep it single-sourced: never redefine
the allowed sets at a call site.

Default off: when ``kya_mode_enabled`` is false every helper is permissive and
stock OSS behaviour is unchanged.
"""

from __future__ import annotations

import logging
from typing import Any

from .config import settings

logger = logging.getLogger(__name__)

# System tools the KY-A supervisor may use: checklist, memory, utils, and the
# enforcement-gating tools. ``propose_enforcement`` MUST stay in this set —
# it is the HITL gate (FR-6.4), not a bypass of it.
KYA_ALLOWED_SYSTEM_TOOLS: frozenset[str] = frozenset(
    {
        # checklist
        "create_checklist",
        "add_checklist_step",
        "update_checklist_step",
        "abandon_checklist",
        # memory
        "store_to_memory",
        "query_memory",
        # utils
        "get_datetime",
        "list_tools",
        # enforcement gating + case attestation
        "propose_enforcement",
        "sign_case_attestation",
    }
)


def kya_mode_enabled() -> bool:
    """Read the flag at call time so tests can monkeypatch the settings singleton."""
    return bool(getattr(settings, "kya_mode_enabled", False))


def kya_allowed_agent_ids() -> set[str]:
    """Parse ``settings.kya_allowed_agents`` (comma-separated DIDs) into a set."""
    raw = str(getattr(settings, "kya_allowed_agents", "") or "")
    return {part.strip() for part in raw.split(",") if part.strip()}


def system_tool_allowed(tool_name: str) -> bool:
    """True when a system tool may run under the current mode."""
    return not kya_mode_enabled() or tool_name in KYA_ALLOWED_SYSTEM_TOOLS


def agent_allowed(agent_id: str) -> bool:
    """True when an external agent DID may be invoked under the current mode."""
    return not kya_mode_enabled() or agent_id in kya_allowed_agent_ids()


def filter_pnd_candidates(candidates: list[Any]) -> list[Any]:
    """Drop PnD candidates whose agent DID is not allowlisted (KY-A mode only)."""
    if not kya_mode_enabled():
        return candidates
    allowed = kya_allowed_agent_ids()
    return [
        c
        for c in candidates
        if (c.get("agent_id") if isinstance(c, dict) else getattr(c, "agent_id", ""))
        in allowed
    ]


def filter_system_tool_schemas(schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop system tool schemas outside KYA_ALLOWED_SYSTEM_TOOLS (KY-A mode only)."""
    if not kya_mode_enabled():
        return schemas
    return [
        s
        for s in schemas
        if s.get("function", {}).get("name") in KYA_ALLOWED_SYSTEM_TOOLS
    ]


async def pin_allowed_agent_candidates(candidates: list[Any]) -> list[Any]:
    """Ensure every allowlisted agent is present in the candidate list (KY-A mode).

    PnD hybrid search ranks candidates per query — a playbook agent that ranks
    below top_k would silently drop out of the tool list and the LLM would
    hallucinate its tool names ("unknown tool" errors). The supervisor
    playbook needs its fleet deterministically, so in KY-A mode any missing
    allowlisted agent is pinned from the manifest cache. No-op when disabled.
    """
    if not kya_mode_enabled():
        return candidates

    from .middleware.manifest_cache import MANIFEST_CACHE

    present = {
        c.get("agent_id") if isinstance(c, dict) else getattr(c, "agent_id", "")
        for c in candidates
    }
    out = list(candidates)
    for agent_id in sorted(kya_allowed_agent_ids() - present):
        manifest = await MANIFEST_CACHE.get_manifest(agent_id)
        capabilities = manifest.get("capabilities") or []
        if not capabilities:
            logger.warning(
                "kya_policy: cannot pin %s — no capabilities in manifest", agent_id
            )
            continue
        transport_type = str(
            (manifest.get("transport") or {}).get("type") or ""
        ).lower()
        out.append(
            {
                "agent_id": agent_id,
                "agent_name": manifest.get("name") or agent_id,
                "agent_description": manifest.get("description") or "",
                # Fleet MCP agents are SSE; anything else delegates (A2A).
                "protocol_type": "MCP" if transport_type == "sse" else "A2A",
                "capabilities": [
                    {
                        "capability_id": cap.get("capability_id") or cap.get("id", ""),
                        "capability_type": (cap.get("type") or "tool").upper(),
                        "name": cap.get("name", ""),
                        "description": cap.get("description", ""),
                        "input_schema": cap.get("input_schema")
                        or {"type": "object", "properties": {}},
                    }
                    for cap in capabilities
                ],
            }
        )
        logger.info("kya_policy: pinned allowlisted agent %s", agent_id)
    return out
