"""Utility system tools — get_datetime, list_tools, send_notification."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .registry import SystemToolRegistry, SystemToolSpec

logger = logging.getLogger(__name__)


async def _get_datetime(args: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Return the current date and time in UTC."""
    tz_name = args.get("timezone", "UTC")
    now = datetime.now(tz=UTC)
    return {
        "utc": now.isoformat(),
        "timestamp": now.timestamp(),
        "timezone": tz_name,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A"),
    }



async def _list_tools(args: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """List all tools currently available to the orchestrator."""
    from .registry import SYSTEM_TOOL_REGISTRY

    system_tool_names = list(SYSTEM_TOOL_REGISTRY._tools.keys())  # noqa: SLF001

    # pnd_candidates holds the last turn's external agent candidates
    pnd_candidates = state.get("pnd_candidates", [])
    external_tools: list[dict[str, Any]] = []
    from ..pnd.candidate_compat import (
        cand_agent_id,
        cand_capabilities,
        cand_protocol_type,
        cap_capability_id,
        cap_capability_type,
    )

    for candidate in pnd_candidates:
        agent_id = cand_agent_id(candidate)
        protocol = cand_protocol_type(candidate)
        capabilities = cand_capabilities(candidate)
        tool_names = [
            f"{agent_id}__{cap_capability_id(cap)}"
            for cap in capabilities
            if cap_capability_type(cap) == "TOOL"
        ]
        external_tools.append(
            {
                "agent_id": agent_id,
                "protocol": protocol,
                "tools": tool_names,
            }
        )

    return {
        "system_tools": system_tool_names,
        "external_agent_tools": external_tools,
        "total_system": len(system_tool_names),
        "total_external_agents": len(external_tools),
        "note": "External tools reflect last PnD query result (may be empty if PnD gate did not fire this turn)",
    }


def register_util_tools(registry: SystemToolRegistry) -> None:
    registry.register(
        SystemToolSpec(
            name="get_datetime",
            description="Get the current date and time.",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "default": "UTC"},
                },
            },
            handler=_get_datetime,
        )
    )
    registry.register(
        SystemToolSpec(
            name="list_tools",
            description="List all tools currently available to you: system tools and external agent tools fetched from PnD this turn. Use this to debug what tools are loaded.",
            parameters={"type": "object", "properties": {}},
            handler=_list_tools,
        )
    )