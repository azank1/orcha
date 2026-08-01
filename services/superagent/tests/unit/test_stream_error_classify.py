"""Unit tests for graph-stream error classification.

The runner used to surface every failure as one opaque "Internal graph error"
string, so the UI always offered a blanket retry. _classify_stream_error maps
exceptions to typed events with a retriable flag so the UI only suggests retry
when it could actually help.
"""

from __future__ import annotations

from superagent.graph.runner import _classify_stream_error


class _StatusError(Exception):
    """Stand-in for an LLM/HTTP client error carrying an HTTP status code."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"status {status_code}")
        self.status_code = status_code


class GraphRecursionError(Exception):
    """Name-compatible stand-in for langgraph's GraphRecursionError."""


def test_402_is_fatal_credits() -> None:
    ev = _classify_stream_error(_StatusError(402))
    assert ev["type"] == "error"
    assert ev["category"] == "llm_credits"
    assert ev["retriable"] is False
    assert "credit" in ev["error"].lower()


def test_recursion_limit_is_fatal_step_budget() -> None:
    ev = _classify_stream_error(GraphRecursionError("exceeded"))
    assert ev["category"] == "step_budget"
    assert ev["retriable"] is False


def test_429_is_transient_retriable() -> None:
    ev = _classify_stream_error(_StatusError(429))
    assert ev["category"] == "transient"
    assert ev["retriable"] is True


def test_503_is_transient_retriable() -> None:
    ev = _classify_stream_error(_StatusError(503))
    assert ev["retriable"] is True


def test_unknown_is_internal_non_retriable() -> None:
    ev = _classify_stream_error(ValueError("boom"))
    assert ev["category"] == "internal"
    assert ev["retriable"] is False
    assert "server logs" in ev["error"].lower()
