"""Circuit breaker for protecting external dependency calls."""

from __future__ import annotations

import logging
import time
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class CircuitState(StrEnum):
    CLOSED = "closed"  # Normal operation — calls pass through
    OPEN = "open"  # Failing — calls are rejected immediately
    HALF_OPEN = "half_open"  # Testing recovery — one probe call allowed


class CircuitBreakerError(Exception):
    """Raised when a call is rejected because the circuit is OPEN."""


class CircuitBreaker:
    """
    Circuit breaker for external dependencies (LLM API, database).

    State machine:
        CLOSED  →(failure_threshold reached)→  OPEN
        OPEN    →(timeout elapsed)→            HALF_OPEN
        HALF_OPEN →(success)→                  CLOSED
        HALF_OPEN →(failure)→                  OPEN

    Usage::

        breaker = CircuitBreaker(failure_threshold=5, timeout=60)

        try:
            result = await breaker.call(my_async_func, arg1, arg2)
        except CircuitBreakerError:
            # Circuit is open — return a fallback response
            ...
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type[Exception] = Exception,
        name: str = "circuit_breaker",
    ) -> None:
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.name = name

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float | None = None

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute *func* with circuit breaker protection."""
        self._check_state()

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as exc:
            self._on_failure()
            raise exc from exc

    def _check_state(self) -> None:
        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time is not None
                and time.time() - self.last_failure_time > self.timeout
            ):
                logger.info("Circuit '%s' transitioning to HALF_OPEN", self.name)
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerError(
                    f"Circuit '{self.name}' is OPEN — call rejected"
                )

    def _on_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit '%s' recovered — transitioning to CLOSED", self.name)
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.error(
                    "Circuit '%s' OPENED after %d failures",
                    self.name,
                    self.failure_count,
                )
            self.state = CircuitState.OPEN
