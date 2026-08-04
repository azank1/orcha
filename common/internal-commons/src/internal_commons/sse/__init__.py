"""SSE event type catalogue."""

from .events import (
    _KNOWN_EVENT_TYPES,
    AnySSEEvent,
    AuthCompleteEvent,
    DoneEvent,
    ErrorEvent,
    InterruptEvent,
    ProgressEvent,
    TokenEvent,
    is_known_event_type,
)

__all__ = [
    "AnySSEEvent",
    "ProgressEvent",
    "TokenEvent",
    "DoneEvent",
    "ErrorEvent",
    "InterruptEvent",
    "AuthCompleteEvent",
    "is_known_event_type",
    "_KNOWN_EVENT_TYPES",
]
