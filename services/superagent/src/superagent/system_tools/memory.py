"""Memory system tools — store_to_memory and query_memory (Graphiti stub)."""

from __future__ import annotations

import logging
from typing import Any

from .registry import SystemToolRegistry, SystemToolSpec

logger = logging.getLogger(__name__)


async def _store_to_memory(
    args: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    """Store a fact or preference to long-term memory (Graphiti stub)."""
    content = args["content"]
    memory_type = args.get("type", "fact")
    user_id = state.get("user_id", "")
    logger.info(
        "store_to_memory: user=%s type=%s content='%.60s'",
        user_id,
        memory_type,
        content,
    )
    # TODO: integrate with Graphiti knowledge graph when available
    return {
        "stored": True,
        "type": memory_type,
        "note": "Memory storage stub — Graphiti not yet integrated",
    }


async def _query_memory(args: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Query long-term memory for relevant facts (Graphiti stub)."""
    query = args["query"]
    user_id = state.get("user_id", "")
    logger.info("query_memory: user=%s query='%.60s'", user_id, query)
    # TODO: integrate with Graphiti knowledge graph when available
    return {"results": [], "note": "Memory query stub — Graphiti not yet integrated"}


def register_memory_tools(registry: SystemToolRegistry) -> None:
    registry.register(
        SystemToolSpec(
            name="store_to_memory",
            description=(
                "Store a fact, preference, or important piece of information "
                "to the user's long-term memory for future sessions."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The information to remember",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["fact", "preference", "instruction"],
                        "description": "Category of memory",
                    },
                },
                "required": ["content"],
            },
            handler=_store_to_memory,
        )
    )
    registry.register(
        SystemToolSpec(
            name="query_memory",
            description="Query the user's long-term memory for relevant information.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for"},
                },
                "required": ["query"],
            },
            handler=_query_memory,
        )
    )
