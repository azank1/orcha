"""Validator attestation schema (D1 spike)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class Attestation:
    schema_version: str
    call_id: str
    agent_id: str
    validator_did: str
    success: bool
    latency_ms: int
    judge_score: float
    notes: str
    observed_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_attestation(
    *,
    call_id: str,
    agent_id: str,
    validator_did: str,
    success: bool,
    latency_ms: int,
    content: str,
) -> Attestation:
    """Heuristic judge for D1 spike — replaced by semantic judge in D2."""
    score = 0.85 if success and content and not content.startswith("Error:") else 0.2
    return Attestation(
        schema_version="1.0",
        call_id=call_id,
        agent_id=agent_id,
        validator_did=validator_did,
        success=success,
        latency_ms=latency_ms,
        judge_score=score,
        notes="spike-heuristic",
        observed_at=datetime.now(UTC).isoformat(),
    )
