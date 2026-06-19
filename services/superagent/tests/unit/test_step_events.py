"""D1 spike — StepResult Kafka fan-out."""

from __future__ import annotations

import pytest
from superagent.middleware.observers import StepResult
from superagent.middleware.step_events import fan_out_step_complete, step_result_payload


def _record() -> StepResult:
    return StepResult(
        call_id="call-1",
        agent_id="did:orcha:agent:demo",
        capability_id="demo",
        protocol="A2A",
        tool_name="demo.run",
        success=True,
        content="ok",
        latency_ms=10,
    )


def test_step_result_payload_matches_dataclass() -> None:
    payload = step_result_payload(_record())
    assert payload["call_id"] == "call-1"
    assert payload["agent_id"] == "did:orcha:agent:demo"
    assert payload["success"] is True


@pytest.mark.asyncio
async def test_fan_out_skips_when_kafka_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KAFKA_ENABLED", "false")
    await fan_out_step_complete(_record())
