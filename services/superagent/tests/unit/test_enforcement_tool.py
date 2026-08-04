"""Tests for the propose_enforcement system tool (WS6 / FR-6)."""

from __future__ import annotations

from typing import Any

import pytest
from superagent.middleware import audit_ledger
from superagent.middleware.observers import NoOpObserver, set_observer
from superagent.system_tools import enforcement
from superagent.system_tools.enforcement import (
    _propose_enforcement,
    register_enforcement_tools,
)
from superagent.system_tools.registry import SystemToolRegistry


class _FakeTable:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    async def find_first(self, order: Any = None) -> Any:
        return type("Row", (), self.rows[-1])() if self.rows else None

    async def create(self, data: dict[str, Any]) -> None:
        self.rows.append({k: getattr(v, "data", v) for k, v in data.items()})


class _FakeDB:
    def __init__(self) -> None:
        self.auditledgerentry = _FakeTable()

    def is_connected(self) -> bool:
        return True


@pytest.fixture
def ledger_db():
    db = _FakeDB()
    set_observer(audit_ledger.LedgerObserver(db=db))
    yield db
    set_observer(NoOpObserver())


def _args(**overrides: Any) -> dict[str, Any]:
    base = {
        "enforcement_action": "suspend_agent",
        "target_agent_id": "did:orcha:agent:rogue-agent",
        "justification": "Scope violation: paid counterparty not in allowed list.",
    }
    base.update(overrides)
    return base


def _state() -> dict[str, Any]:
    return {"session_id": "sess-1", "user_id": "session-owner"}


class TestProposeEnforcement:
    def test_tool_registered(self):
        registry = SystemToolRegistry()
        register_enforcement_tools(registry)
        assert registry.has("propose_enforcement")
        schema = registry.get_all_schemas()[0]["function"]
        assert set(schema["parameters"]["required"]) == {
            "enforcement_action",
            "target_agent_id",
            "justification",
        }

    @pytest.mark.asyncio
    async def test_missing_args_returns_error_without_interrupt(self, monkeypatch):
        called = False

        def _fake_interrupt(event: Any) -> Any:
            nonlocal called
            called = True
            return {}

        monkeypatch.setattr(enforcement, "interrupt", _fake_interrupt)
        result = await _propose_enforcement({"justification": "x"}, _state())
        assert result.startswith("Error:")
        assert called is False

    @pytest.mark.asyncio
    async def test_always_raises_hitl_interrupt(self, monkeypatch):
        """The tool suspends with HITL_APPROVAL before anything happens (FR-6.1)."""
        seen: list[dict[str, Any]] = []

        def _fake_interrupt(event: dict[str, Any]) -> Any:
            seen.append(event)
            return {"status": "denied"}

        monkeypatch.setattr(enforcement, "interrupt", _fake_interrupt)
        await _propose_enforcement(_args(), _state())

        assert len(seen) == 1
        event = seen[0]
        assert event["interrupt_type"] == "HITL_APPROVAL"
        meta = event["metadata"]
        assert meta["enforcement_action"] == "suspend_agent"
        assert meta["proposal_id"]
        assert meta["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_approval_records_named_human_in_ledger(self, monkeypatch, ledger_db):
        """Approve → named officer + decision persisted in the ledger (FR-6.3)."""
        monkeypatch.setattr(
            enforcement,
            "interrupt",
            lambda event: {
                "status": "approved",
                "authoriser_user_id": "officer-7",
                "authoriser_display_name": "Officer Seven",
            },
        )
        result = await _propose_enforcement(_args(), _state())

        assert "APPROVED" in result
        assert "Officer Seven" in result
        assert "officer-7" in result

        rows = ledger_db.auditledgerentry.rows
        assert len(rows) == 1
        row = rows[0]
        assert row["entry_type"] == "hitl_decision"
        assert row["success"] is True
        payload = row["payload"]
        assert payload["decision"] == "approved"
        assert payload["authoriser_user_id"] == "officer-7"
        assert payload["authoriser_display_name"] == "Officer Seven"
        assert payload["enforcement_action"] == "suspend_agent"
        assert payload["decided_at"]

    @pytest.mark.asyncio
    async def test_denial_stops_action_and_is_recorded(self, monkeypatch, ledger_db):
        """Deny → no action, decision still on record (FR-6.4)."""
        monkeypatch.setattr(
            enforcement, "interrupt", lambda event: {"status": "denied"}
        )
        result = await _propose_enforcement(_args(), _state())

        assert "DENIED" in result
        assert "No enforcement action taken" in result
        # Falls back to the session owner when the Gateway injection is absent.
        assert "session-owner" in result

        row = ledger_db.auditledgerentry.rows[0]
        assert row["payload"]["decision"] == "denied"
        assert row["success"] is False

    @pytest.mark.asyncio
    async def test_ledger_disabled_still_returns_with_warning(self, monkeypatch):
        """No LedgerObserver installed → decision returned, non-persistence flagged."""
        set_observer(NoOpObserver())
        monkeypatch.setattr(
            enforcement, "interrupt", lambda event: {"status": "approved"}
        )
        try:
            result = await _propose_enforcement(_args(), _state())
        finally:
            set_observer(NoOpObserver())
        assert "APPROVED" in result
        assert "WARNING" in result
