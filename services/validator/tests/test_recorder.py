"""D1 spike tests for FulfillmentRecorder."""

from __future__ import annotations

import pytest
from superagent.middleware.observers import StepResult
from validator.recorder import FulfillmentRecorder


@pytest.mark.asyncio
async def test_fulfillment_recorder_records_attestation() -> None:
    recorder = FulfillmentRecorder(validator_did="did:orcha:validator:alice")
    record = StepResult(
        call_id="c1",
        agent_id="did:orcha:agent:demo",
        capability_id="demo",
        protocol="A2A",
        tool_name="demo.run",
        success=True,
        content="ok",
        latency_ms=50,
    )
    await recorder.on_step_complete(record)
    assert len(recorder.attestations) == 1
    assert recorder.attestations[0].validator_did == "did:orcha:validator:alice"
    assert recorder.attestations[0].judge_score >= 0.8
