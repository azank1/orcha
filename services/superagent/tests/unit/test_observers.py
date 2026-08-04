"""Tests for the ExecutionObserver open/closed seam."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from superagent.middleware.observers import (
    ExecutionObserver,
    NoOpObserver,
    StepResult,
    emit_step_complete,
    get_observer,
    set_observer,
)


def _record(**overrides) -> StepResult:
    base = {
        "call_id": "call-1",
        "agent_id": "did:orcha:agent:web-scraper",
        "capability_id": "scrape",
        "protocol": "A2A",
        "tool_name": "web-scraper.scrape",
        "success": True,
        "content": "ok",
    }
    base.update(overrides)
    return StepResult(**base)


@pytest.fixture(autouse=True)
def _restore_default_observer():
    """Each test starts and ends with the default NoOpObserver installed."""
    set_observer(NoOpObserver())
    yield
    set_observer(NoOpObserver())


def test_default_observer_is_noop():
    assert isinstance(get_observer(), NoOpObserver)


@pytest.mark.asyncio
async def test_noop_observer_does_nothing():
    # Should complete without error and return None.
    assert await get_observer().on_step_complete(_record()) is None


@pytest.mark.asyncio
async def test_injected_observer_receives_record():
    seen: list[StepResult] = []

    class Recorder:
        async def on_step_complete(self, record: StepResult) -> None:
            seen.append(record)

    recorder = Recorder()
    assert isinstance(recorder, ExecutionObserver)  # structural Protocol check
    set_observer(recorder)

    await emit_step_complete(_record(call_id="call-42"))

    assert len(seen) == 1
    assert seen[0].call_id == "call-42"
    assert seen[0].agent_id == "did:orcha:agent:web-scraper"


@pytest.mark.asyncio
async def test_broken_observer_never_raises_to_caller():
    class Broken:
        async def on_step_complete(self, record: StepResult) -> None:
            raise RuntimeError("observer blew up")

    set_observer(Broken())

    # emit_step_complete must swallow the error — execution must not break.
    await emit_step_complete(_record())


def test_step_result_is_immutable():
    rec = _record()
    with pytest.raises(FrozenInstanceError):
        rec.success = False  # type: ignore[misc]
