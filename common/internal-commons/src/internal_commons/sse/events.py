"""Full SSE event type catalogue — all event types that can appear on the SSE stream."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from ..interrupts.events import InterruptEvent


class ProgressEvent(BaseModel):
    type: Literal["progress"] = "progress"
    message: str
    """Status message from the orchestrator or an agent handler."""

    def to_sse_line(self) -> str:
        return f"data: {self.model_dump_json()}\n\n"


class TokenEvent(BaseModel):
    type: Literal["token"] = "token"
    content: str
    """Single LLM token for streaming display."""

    def to_sse_line(self) -> str:
        return f"data: {self.model_dump_json()}\n\n"


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"
    session_id: str
    response: str = ""
    """Full final response text from the orchestrator."""

    def to_sse_line(self) -> str:
        return f"data: {self.model_dump_json()}\n\n"


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str
    error_type: str = ""
    """
    Machine-readable error category. Examples:
    'preflight_error', 'agent_unavailable', 'schema_validation_error'
    """

    def to_sse_line(self) -> str:
        return f"data: {self.model_dump_json()}\n\n"


class AuthCompleteEvent(BaseModel):
    """
    Emitted by Gateway after an OAuth callback is processed.
    Signals to the UI that the popup can be closed and execution is resuming.
    """

    type: Literal["auth_complete"] = "auth_complete"
    interrupt_type: str
    message: str = ""

    def to_sse_line(self) -> str:
        return f"data: {self.model_dump_json()}\n\n"


# Union of all possible SSE events — discriminated on the `type` field at runtime
AnySSEEvent = (
    ProgressEvent
    | TokenEvent
    | DoneEvent
    | ErrorEvent
    | InterruptEvent
    | AuthCompleteEvent
)

# Set of known event types — used by the gateway proxy for logging unknowns.
# The proxy ALWAYS forwards ALL events regardless of whether the type is known.
_KNOWN_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "progress",
        "token",
        "done",
        "error",
        "interrupt",
        "auth_complete",
        # SuperAgent internal events (passthrough)
        "checklist_snapshot",
        "token_usage",
        "artifact_created",
        "invocation_start",
        "invocation_progress",
        "invocation_result",
        "agents_discovered",
    }
)


def is_known_event_type(event_type: str) -> bool:
    """Return True if the event type is in the known catalogue."""
    return event_type in _KNOWN_EVENT_TYPES
