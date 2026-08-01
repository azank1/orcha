"""InterruptEvent — canonical SSE wire envelope for all interrupt types."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, model_validator

from .payloads import INTERRUPT_METADATA_MAP
from .types import InterruptType


class InterruptEvent(BaseModel):
    """
    The canonical SSE event envelope for all interrupt types.

    Serialised as:
        data: {"type": "interrupt", "interrupt_type": "AUTH_CALLBACK", ...}

    Both SuperAgent (emitter) and Gateway (relay) must use this model.
    The UI discriminates on `interrupt_type` to select the correct
    modal/component to render.
    """

    type: str = "interrupt"

    interrupt_type: InterruptType

    interrupt_id: str
    """
    Unique ID for this interrupt instance.
    Format: {interrupt_type}__{agent_id}__{capability_id}__{nonce[:8]}
    Used by the UI as the key in POST /sessions/{id}/resume.
    """

    agent_id: str
    """Agent that triggered the interrupt."""

    session_id: str
    """Session this interrupt belongs to."""

    message: str
    """Human-readable summary for display or logging."""

    metadata: dict[str, Any]
    """
    Type-specific payload. Shape is defined by INTERRUPT_METADATA_MAP.
    Typed as dict for SSE serialisation compatibility — consumers should
    validate against the appropriate metadata model using interrupt_type.
    """

    resumable: bool = True
    """
    If False, this interrupt cannot be resumed — it is terminal.
    e.g. agent is permanently unavailable, user explicitly cancelled.
    """

    @model_validator(mode="after")
    def validate_metadata_shape(self) -> InterruptEvent:
        """Validate metadata matches the declared interrupt_type."""
        model_cls = INTERRUPT_METADATA_MAP.get(self.interrupt_type)
        if model_cls:
            # This will raise ValidationError if metadata shape is wrong.
            # Catches mismatches at construction time, not at the UI.
            model_cls(**self.metadata)
        return self

    def to_sse_line(self) -> str:
        """Serialise to a single SSE data line."""
        return f"data: {self.model_dump_json()}\n\n"
