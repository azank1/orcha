"""Case attestation system tool (KY-A supervisory harness, WS8 / FR-8).

``sign_case_attestation`` seals a supervisory case with an Ed25519-signed
attestation. The orchestrator calls it BEFORE rendering the regulator case
file so the signed ``case_hash``/``signature``/``public_key`` can be embedded
in the CanvasKit case file itself. Chain anchoring (testnet) is fired
asynchronously by the validator package and is never on the critical path.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .registry import SystemToolRegistry, SystemToolSpec

logger = logging.getLogger(__name__)


def _enforcement_warranted(case_payload: dict[str, Any]) -> bool:
    """True when the case content shows enforcement should have been proposed."""
    flags = case_payload.get("payment_flags")
    if isinstance(flags, list) and flags:
        return True
    verification = case_payload.get("verification")
    return isinstance(verification, dict) and verification.get("overall") == "fail"


async def _sign_case_attestation(args: dict[str, Any], state: dict[str, Any]) -> str:
    """Sign the case payload and return the attestation as a JSON string.

    Never raises for a missing validator package — a mock-first stack without
    the validator installed must degrade to an explanatory error string so
    the orchestrator can still render the case file with attestation absent.
    """
    case_payload = args.get("case_payload")
    if not isinstance(case_payload, dict) or not case_payload:
        return (
            "Error: sign_case_attestation requires a non-empty 'case_payload' object."
        )

    session_id = str(state.get("session_id") or "")
    if not session_id:
        return "Error: sign_case_attestation requires a session_id in the run state."

    # Ordering guard (KY-A mode): a case that warrants enforcement — payment
    # flags or failed scope verification — may only be sealed AFTER a named
    # human has approved the enforcement proposal. Without this, the model can
    # skip the mandatory HITL gate and seal an ungated case.
    from ..kya_policy import kya_mode_enabled

    if kya_mode_enabled() and _enforcement_warranted(case_payload):
        from ..middleware.audit_ledger import has_approved_hitl_decision

        if not await has_approved_hitl_decision(session_id):
            return (
                "Error: this case has payment flags or failed verification, so "
                "enforcement must be decided by a named human BEFORE the case "
                "can be sealed. Call propose_enforcement now — it will pause "
                "for approval; after the decision is recorded, retry "
                "sign_case_attestation."
            )

    try:
        from validator import finalize_case  # lazy: optional workspace member
    except ImportError:
        logger.warning("sign_case_attestation: validator package unavailable")
        return (
            "Error: the 'validator' package is unavailable, so the case could "
            "not be signed. Render the case file with attestation=null and note "
            "that the case is unsigned."
        )

    summary = str(args.get("summary") or "").strip()
    if summary:
        case_payload = {**case_payload, "summary": summary}

    try:
        result = await finalize_case(session_id, case_payload)
    except Exception as exc:  # signing/DB outage must not break the run
        logger.exception("sign_case_attestation: finalize_case failed")
        return f"Error: case attestation failed: {exc}"

    logger.info(
        "sign_case_attestation: session=%s attestation=%s status=%s",
        session_id,
        result.get("attestation_id"),
        result.get("status"),
    )
    return json.dumps(result)


def register_attestation_tools(registry: SystemToolRegistry) -> None:
    """Register KY-A case attestation tools."""
    registry.register(
        SystemToolSpec(
            name="sign_case_attestation",
            description=(
                "Seal a supervisory case with an Ed25519-signed attestation. "
                "Call this to sign the assembled case payload BEFORE rendering "
                "the regulator case file, then pass the returned attestation "
                "(case_hash, signature, public_key, status) into render_case_file. "
                "Chain anchoring is asynchronous and optional; do not wait for it."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "case_payload": {
                        "type": "object",
                        "description": (
                            "The full supervisory case JSON to sign: verification "
                            "findings, rulebook citations, payment flags, and the "
                            "HITL decision."
                        ),
                    },
                    "summary": {
                        "type": "string",
                        "description": "Optional one-line case summary folded into the signed payload.",
                    },
                },
                "required": ["case_payload"],
            },
            handler=_sign_case_attestation,
        )
    )
