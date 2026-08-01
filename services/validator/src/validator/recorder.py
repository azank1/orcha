"""FulfillmentRecorder — reference ExecutionObserver for validator attestations."""

from __future__ import annotations

import logging
from typing import Any

from .attestation import Attestation, build_attestation

logger = logging.getLogger(__name__)


class FulfillmentRecorder:
    """Records attestations for each StepResult (in-memory spike store)."""

    def __init__(self, validator_did: str) -> None:
        self.validator_did = validator_did
        self.attestations: list[Attestation] = []

    async def on_step_complete(self, record: Any) -> None:
        att = build_attestation(
            call_id=record.call_id,
            agent_id=record.agent_id,
            validator_did=self.validator_did,
            success=record.success,
            latency_ms=record.latency_ms,
            content=record.content,
        )
        self.attestations.append(att)
        logger.info(
            "FulfillmentRecorder attested call_id=%s agent=%s score=%.2f",
            att.call_id,
            att.agent_id,
            att.judge_score,
        )
