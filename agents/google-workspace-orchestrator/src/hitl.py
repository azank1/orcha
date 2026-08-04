"""Human-in-the-loop gates for destructive MCP tool names."""

from __future__ import annotations


def tool_requires_hitl(tool_name: str) -> bool:
    t = tool_name.lower()
    needles = (
        "send",
        "delete",
        "trash",
        "remove",
        "purge",
        "transfer_owner",
        "publish",
        "invite",
    )
    return any(n in t for n in needles)


def hitl_message(tool_name: str) -> str:
    return (
        f"Approval required before executing workspace action `{tool_name}` "
        "(potentially destructive). Reply **approve** to continue or **deny** to cancel."
    )
