"""AgentHandler ABC and shared event types."""

from __future__ import annotations

import logging
from abc import ABC
from dataclasses import dataclass, field
from typing import Any

from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)


@dataclass
class AgentEvent:
    event_type: str  # "progress" | "result" | "clarify" | "error"
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClarifyEvent(AgentEvent):
    """A2A input-required: agent needs clarification from user."""

    question: str = ""
    task_id: str = ""

    def __post_init__(self) -> None:
        self.event_type = "clarify"


class AgentHandler(ABC):  # noqa: B024
    """Abstract base class for all agent protocol handlers."""

    def __init__(self, auth_headers: dict[str, str]) -> None:
        self._auth_headers = auth_headers

    async def emit_event(
        self, config: RunnableConfig | None, event_data: dict[str, Any]
    ) -> None:
        """Best-effort custom stream event (only when ``astream`` uses ``stream_mode='custom'``)."""
        if not config:
            return
        try:
            await adispatch_custom_event("agent_invocation", event_data, config=config)
        except Exception:
            logger.debug("emit_event: custom dispatch skipped", exc_info=True)
