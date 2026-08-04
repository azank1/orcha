"""Enforcement gating system tool (KY-A supervisory harness, WS6).

``propose_enforcement`` is the supervisor-side gate for any enforcement action
against a supervised agent (suspend, revoke scope, restrict counterparties,
...). It embodies the red line (dev-srs FR-6.4):

    The agent proposes; a named human disposes.

The tool ALWAYS suspends the graph with ``InterruptType.HITL_APPROVAL`` and
never executes an enforcement side-effect itself. On resume it records the
named-human decision (from the authenticated Gateway user, injected into the
resume payload server-side) into the hash-chained audit ledger (FR-6.3) and
returns the outcome as text for the orchestrator.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from internal_commons.interrupts import (
    InterruptEvent,
    InterruptType,
)
from internal_commons.interrupts.payloads import HitlApprovalMetadata
from langgraph.types import interrupt

from .registry import SystemToolRegistry, SystemToolSpec

logger = logging.getLogger(__name__)

_APPROVED = {"approved", "approve", "complete"}


async def _record_decision_in_ledger(
    *,
    session_id: str,
    proposal_id: str,
    enforcement_action: str,
    target_agent_id: str,
    decision: str,
    approved: bool,
    authoriser_user_id: str,
    authoriser_display_name: str,
    decided_at: str,
    justification: str,
) -> bool:
    """Persist the named-human decision into the audit ledger (FR-6.3).

    Returns True when the decision was ledger-persisted. Never raises — a
    ledger outage must not break the supervisory run (fail closed), but the
    caller surfaces non-persistence in its result text so it is never silent.
    """
    from ..middleware.audit_ledger import ENTRY_TYPE_HITL_DECISION, LedgerObserver
    from ..middleware.observers import get_observer

    observer = get_observer()
    if not isinstance(observer, LedgerObserver):
        logger.warning(
            "propose_enforcement: audit ledger not enabled — decision for "
            "proposal=%s recorded in transcript only",
            proposal_id,
        )
        return False
    row = await observer.append(
        entry_type=ENTRY_TYPE_HITL_DECISION,
        agent_id=target_agent_id,
        protocol="system",
        success=approved,
        session_id=session_id,
        payload={
            "proposal_id": proposal_id,
            "enforcement_action": enforcement_action,
            "decision": decision,
            "authoriser_user_id": authoriser_user_id,
            "authoriser_display_name": authoriser_display_name,
            "decided_at": decided_at,
            "justification": justification,
        },
    )
    return row is not None


async def _propose_enforcement(args: dict[str, Any], state: dict[str, Any]) -> str:
    """Propose an enforcement action; ALWAYS gates on named-human approval."""
    enforcement_action = str(args.get("enforcement_action") or "").strip()
    target_agent_id = str(args.get("target_agent_id") or "").strip()
    justification = str(args.get("justification") or "").strip()
    risk_level = str(args.get("risk_level") or "high").lower()
    if risk_level not in ("low", "medium", "high"):
        risk_level = "high"
    if not enforcement_action or not target_agent_id:
        return (
            "Error: propose_enforcement requires 'enforcement_action' and "
            "'target_agent_id'."
        )

    session_id = str(state.get("session_id") or "")
    proposal_id = str(uuid.uuid4())
    description = (
        f"Enforcement proposal {proposal_id}: {enforcement_action} against "
        f"{target_agent_id}. Justification: {justification or 'not provided'}."
    )

    metadata = HitlApprovalMetadata(
        action_description=description,
        risk_level=risk_level,  # type: ignore[arg-type]
        agent_display_name="KY-A Supervisor",
        capability_name="propose_enforcement",
        proposal_id=proposal_id,
        enforcement_action=enforcement_action,
    )
    event = InterruptEvent(
        interrupt_type=InterruptType.HITL_APPROVAL,
        interrupt_id=f"hitl_approval__propose_enforcement__{proposal_id[:8]}",
        agent_id="did:orcha:system:kya-supervisor",
        session_id=session_id,
        message=description,
        metadata=metadata.model_dump(),
    )

    # Suspends the graph. On resume, returns the resume payload; the Gateway
    # injects the authenticated authoriser identity server-side.
    resume_value = interrupt(event.model_dump())
    resume_dict: dict[str, Any] = resume_value if isinstance(resume_value, dict) else {}

    raw_status = str(resume_dict.get("status") or "").lower()
    approved = raw_status in _APPROVED
    decision = "approved" if approved else "denied"
    decided_at = datetime.now(UTC).isoformat()

    # Named-human attribution: server-injected authenticated identity first,
    # then the session owner; never trust free-text client fields alone.
    authoriser_user_id = (
        str(resume_dict.get("authoriser_user_id") or "").strip()
        or str(state.get("user_id") or "").strip()
    )
    authoriser_display_name = (
        str(resume_dict.get("authoriser_display_name") or "").strip()
        or authoriser_user_id
    )

    persisted = await _record_decision_in_ledger(
        session_id=session_id,
        proposal_id=proposal_id,
        enforcement_action=enforcement_action,
        target_agent_id=target_agent_id,
        decision=decision,
        approved=approved,
        authoriser_user_id=authoriser_user_id,
        authoriser_display_name=authoriser_display_name,
        decided_at=decided_at,
        justification=justification,
    )
    ledger_note = (
        "Decision recorded in the audit ledger."
        if persisted
        else "WARNING: decision NOT persisted to the audit ledger (ledger disabled/unavailable)."
    )

    if not approved:
        return (
            f"Enforcement proposal {proposal_id} DENIED by "
            f"{authoriser_display_name} (user {authoriser_user_id}) at {decided_at}. "
            f"No enforcement action taken. {ledger_note}"
        )
    return (
        f"Enforcement proposal {proposal_id} APPROVED by "
        f"{authoriser_display_name} (user {authoriser_user_id}) at {decided_at} "
        f"for action '{enforcement_action}' against {target_agent_id}. "
        f"The authorisation is on record; execution of the enforcement action "
        f"itself remains an out-of-band, human-operated procedure. {ledger_note}"
    )


def register_enforcement_tools(registry: SystemToolRegistry) -> None:
    """Register KY-A enforcement gating tools."""
    registry.register(
        SystemToolSpec(
            name="propose_enforcement",
            description=(
                "Propose an enforcement action against a supervised agent "
                "(e.g. suspend_agent, revoke_scope, restrict_counterparties). "
                "ALWAYS pauses for named-human approval before anything happens; "
                "the decision is recorded in the audit ledger. Use this instead of "
                "ever attempting an enforcement action directly."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "enforcement_action": {
                        "type": "string",
                        "description": (
                            "The enforcement action proposed, e.g. 'suspend_agent', "
                            "'revoke_scope', 'restrict_counterparties'."
                        ),
                    },
                    "target_agent_id": {
                        "type": "string",
                        "description": "DID of the supervised agent the action targets.",
                    },
                    "justification": {
                        "type": "string",
                        "description": (
                            "Evidence-backed reason for the proposal (cite findings "
                            "and rulebook citations from earlier steps)."
                        ),
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Risk classification (defaults to high).",
                    },
                },
                "required": ["enforcement_action", "target_agent_id", "justification"],
            },
            handler=_propose_enforcement,
        )
    )
