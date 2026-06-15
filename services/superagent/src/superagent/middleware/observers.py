"""ExecutionObserver — the open/closed seam in the execution pipeline.

This is the boundary between the open-source runtime and any future hosted /
closed data layer. The public package ships a ``NoOpObserver`` that does
nothing. A hosted deployment injects its own observer (e.g. a
``FulfillmentRecorder`` feeding a semantic judge / GNN) *server-side only* —
it is never part of the public package.

The contract is deliberately tiny: one coroutine, called once per agent
execution, immediately after the OutputNormalizer step. Observers MUST NOT
raise — a failing observer must never break a user-facing execution. The
pipeline guards the call, but observers should also fail closed internally.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StepResult:
    """Immutable record of a single agent execution.

    This is the unit the observer seam emits. It is intentionally
    transport-agnostic and contains no credentials or raw auth headers.
    """

    call_id: str
    agent_id: str
    capability_id: str
    protocol: str
    tool_name: str
    success: bool
    content: str
    user_id: str = ""
    session_id: str = ""
    latency_ms: int = 0
    base_fee: str = "0"
    total_cost_usd: str = "0"
    completed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ExecutionObserver(Protocol):
    """Hook invoked after each agent execution completes.

    The public repo ships :class:`NoOpObserver`. Hosted deployments inject a
    recorder server-side. Implementations must be non-blocking-friendly and
    must never raise out to the caller.
    """

    async def on_step_complete(self, record: StepResult) -> None: ...


class NoOpObserver:
    """Default observer — does nothing. Shipped in the open-source package."""

    async def on_step_complete(self, record: StepResult) -> None:  # noqa: D102
        return None


# Module-level singleton. Hosted deployments call ``set_observer`` at startup
# to swap in their recorder; the OSS package leaves the no-op in place.
_observer: ExecutionObserver = NoOpObserver()


def set_observer(observer: ExecutionObserver) -> None:
    """Install the process-wide execution observer (server-side injection point)."""
    global _observer
    _observer = observer
    logger.info("ExecutionObserver installed: %s", type(observer).__name__)


def get_observer() -> ExecutionObserver:
    """Return the currently installed observer (defaults to NoOpObserver)."""
    return _observer


async def emit_step_complete(record: StepResult) -> None:
    """Dispatch a completed step to the installed observer, swallowing errors.

    A broken observer must never surface to the user-facing execution path.
    """
    try:
        await _observer.on_step_complete(record)
    except Exception:  # pragma: no cover - defensive; observers must fail closed
        logger.exception(
            "ExecutionObserver.on_step_complete raised for call_id=%s; ignoring",
            record.call_id,
        )
