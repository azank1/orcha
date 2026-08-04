"""respond_node — final node that emits the assistant's reply to the user."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage

from ..config import settings

logger = logging.getLogger(__name__)

_CDV_STOP_REASON = (
    "Execution paused: the verification guard determined further steps are "
    "unlikely to improve the result. Partial results are summarized above."
)


async def respond_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Terminal node — the last AI message IS the response.

    Pass-through except for two seams: the CDV stop-reason guard below
    (flag-gated) and post-processing hooks (context compression,
    notification dispatch) that can be added without touching other nodes.
    """
    messages = state.get("messages", [])
    if not messages:
        logger.warning("respond_node: no messages in state")
        return {}

    # CDV stop guard: when the stopper halted the loop on an AIMessage that
    # only carried tool calls, the user would see a blank reply — emit a
    # step_budget-style reason instead.
    if settings.cdv_verification_enabled:
        from ..verification.cdv_integration import stopper_should_stop

        last = messages[-1]
        if (
            isinstance(last, AIMessage)
            and not str(last.content or "").strip()
            and stopper_should_stop(state)
        ):
            return {"messages": [AIMessage(content=_CDV_STOP_REASON)]}

    # Context window management — compress if over threshold
    try:
        from ..context.window_manager import ContextWindowManager

        compressed = ContextWindowManager.maybe_compress(state)
        if compressed:
            return {"messages": compressed}
    except Exception:
        logger.debug("Context compression skipped", exc_info=True)

    return {}
