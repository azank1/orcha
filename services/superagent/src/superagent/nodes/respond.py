"""respond_node — final node that emits the assistant's reply to the user."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def respond_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Terminal node — the last AI message IS the response.

    Currently a pass-through; hooks for post-processing (context compression,
    notification dispatch) can be added here without touching other nodes.
    """
    messages = state.get("messages", [])
    if not messages:
        logger.warning("respond_node: no messages in state")
        return {}

    # Context window management — compress if over threshold
    try:
        from ..context.window_manager import ContextWindowManager

        compressed = ContextWindowManager.maybe_compress(state)
        if compressed:
            return {"messages": compressed}
    except Exception:
        logger.debug("Context compression skipped", exc_info=True)

    return {}
