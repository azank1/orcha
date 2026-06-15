"""Read PnD candidate payloads from checkpoint state (dict or ToolCandidate)."""

from __future__ import annotations

from typing import Any


def cand_agent_id(c: Any) -> str:
    if isinstance(c, dict):
        return str(c.get("agent_id") or "")
    return str(getattr(c, "agent_id", "") or "")


def cand_agent_name(c: Any) -> str:
    if isinstance(c, dict):
        return str(c.get("agent_name") or "")
    return str(getattr(c, "agent_name", "") or "")


def cand_protocol_type(c: Any) -> str:
    if isinstance(c, dict):
        return str(c.get("protocol_type") or "")
    return str(getattr(c, "protocol_type", "") or "")


def cand_capabilities(c: Any) -> list[Any]:
    if isinstance(c, dict):
        raw = c.get("capabilities")
        return list(raw) if raw else []
    caps = getattr(c, "capabilities", None)
    return list(caps) if caps else []


def cap_capability_id(cap: Any) -> str:
    if isinstance(cap, dict):
        return str(cap.get("capability_id") or "")
    return str(getattr(cap, "capability_id", "") or "")


def cap_capability_type(cap: Any) -> str:
    if isinstance(cap, dict):
        return str(cap.get("capability_type") or "TOOL").upper()
    return str(getattr(cap, "capability_type", "TOOL") or "TOOL").upper()
