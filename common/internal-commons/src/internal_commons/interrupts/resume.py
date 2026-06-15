"""ResumePayload — what the UI POSTs to /sessions/{id}/resume."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from .types import InterruptType


class ResumePayload(BaseModel):
    """
    Body of POST /sessions/{session_id}/resume.

    Sent by:  UI → Gateway → SuperAgent
    Used by:  SuperAgent to call Command(resume=value) on LangGraph

    Value shape is interrupt_type-specific:

    AUTH_CALLBACK / AGENT_OAUTH_CALLBACK:
        {"status": "complete"} | {"status": "denied", "reason": str}

    AUTH_FORM_SUBMISSION:
        {"vault_key": str, "status": "complete"}
        Note: the actual secret value is NOT included here.
        It is submitted separately via POST /sessions/{id}/submit-credential
        and stored in vault BEFORE this resume call is made.

    HITL_APPROVAL:
        {"approved": True} | {"approved": False, "reason": str}

    HITL_CLARIFICATION / AGENT_CLARIFICATION:
        {"response": str}  — the user's free-text answer
    """

    interrupt_id: str
    """Must match the interrupt_id from the InterruptEvent that triggered the pause."""

    interrupt_type: InterruptType
    """Redundant but required — allows Gateway to route without decoding interrupt_id."""

    value: dict[str, Any]
    """Resume value passed into Command(resume=value)."""
