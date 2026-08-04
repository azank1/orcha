"""Tests for the hash-chained audit ledger observer (WS7 / FR-7)."""

from __future__ import annotations

from typing import Any

import pytest
from superagent.middleware.audit_ledger import (
    ENTRY_TYPE_HITL_DECISION,
    ENTRY_TYPE_STEP,
    LedgerObserver,
    compute_content_hash,
    verify_chain,
)
from superagent.middleware.observers import StepResult


class _FakeTable:
    """In-memory stand-in for the audit_ledger Prisma table."""

    def __init__(self, fail_on_create: bool = False) -> None:
        self.rows: list[dict[str, Any]] = []
        self.fail_on_create = fail_on_create

    async def find_first(self, order: Any = None) -> Any:
        if not self.rows:
            return None
        row = self.rows[-1]
        return type("Row", (), row)()

    async def create(self, data: dict[str, Any]) -> None:
        if self.fail_on_create:
            raise RuntimeError("db down")
        # The real client unwraps PrismaJson (fields.Json wraps values in .data)
        # and returns plain JSON types; mirror that here.
        self.rows.append({k: getattr(v, "data", v) for k, v in data.items()})

    async def find_many(self, where: dict[str, Any], order: Any = None) -> list[Any]:
        return [
            type("Row", (), r)()
            for r in self.rows
            if r.get("session_id") == where.get("session_id")
        ]


class _FakeDB:
    def __init__(self, fail_on_create: bool = False) -> None:
        self.auditledgerentry = _FakeTable(fail_on_create)

    def is_connected(self) -> bool:
        return True

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None


def _step_result(call_id: str, session_id: str = "sess-1") -> StepResult:
    return StepResult(
        call_id=call_id,
        agent_id="did:orcha:agent:demo",
        capability_id="cap-1",
        protocol="a2a",
        tool_name="run",
        success=True,
        content="some output",
        session_id=session_id,
        latency_ms=42,
        verdict={"verified": True},
    )


class TestLedgerObserver:
    @pytest.mark.asyncio
    async def test_rows_chain_in_append_order(self):
        """Row count matches step count and the hash chain verifies (FR-7.2)."""
        db = _FakeDB()
        observer = LedgerObserver(db=db)

        for i in range(3):
            await observer.on_step_complete(_step_result(f"call-{i}"))

        rows = db.auditledgerentry.rows
        assert len(rows) == 3
        assert rows[0]["prev_hash"] == ""
        for prev, cur in zip(rows, rows[1:], strict=False):
            assert cur["prev_hash"] == prev["content_hash"]
        assert verify_chain(rows) is True

    @pytest.mark.asyncio
    async def test_step_result_fields_mapped(self):
        """Ledger row covers the FR-7.2 field set, with a content digest not content."""
        db = _FakeDB()
        observer = LedgerObserver(db=db)

        await observer.on_step_complete(_step_result("call-x"))

        row = db.auditledgerentry.rows[0]
        assert row["entry_type"] == ENTRY_TYPE_STEP
        assert row["call_id"] == "call-x"
        assert row["agent_id"] == "did:orcha:agent:demo"
        assert row["capability_id"] == "cap-1"
        assert row["protocol"] == "a2a"
        assert row["success"] is True
        assert row["latency_ms"] == 42
        assert row["session_id"] == "sess-1"
        assert row["payload"]["tool_name"] == "run"
        assert row["payload"]["content_digest"].startswith("sha256:")
        assert "some output" not in str(row)

    @pytest.mark.asyncio
    async def test_observer_fails_closed(self):
        """A DB failure is swallowed — the execution path never sees it (FR-7.3)."""
        db = _FakeDB(fail_on_create=True)
        observer = LedgerObserver(db=db)

        # Must not raise.
        await observer.on_step_complete(_step_result("call-fail"))
        assert db.auditledgerentry.rows == []

    @pytest.mark.asyncio
    async def test_chain_detects_tampering(self):
        db = _FakeDB()
        observer = LedgerObserver(db=db)
        for i in range(2):
            await observer.on_step_complete(_step_result(f"call-{i}"))

        rows = db.auditledgerentry.rows
        tampered = [dict(r) for r in rows]
        tampered[0]["success"] = False  # rewrite history
        assert verify_chain(tampered) is False

    @pytest.mark.asyncio
    async def test_hitl_decision_rows_join_the_same_chain(self):
        """Decision rows (WS6) chain onto step rows — one tamper-evident history."""
        db = _FakeDB()
        observer = LedgerObserver(db=db)

        await observer.on_step_complete(_step_result("call-1"))
        await observer.append(
            entry_type=ENTRY_TYPE_HITL_DECISION,
            session_id="sess-1",
            success=True,
            payload={
                "decision": "approve",
                "authoriser_user_id": "user-1",
                "authoriser_display_name": "Officer One",
            },
        )

        rows = db.auditledgerentry.rows
        assert len(rows) == 2
        assert rows[1]["entry_type"] == ENTRY_TYPE_HITL_DECISION
        assert rows[1]["prev_hash"] == rows[0]["content_hash"]
        assert verify_chain(rows) is True

    def test_compute_content_hash_is_stable(self):
        row = {
            "entry_type": ENTRY_TYPE_STEP,
            "call_id": "c",
            "agent_id": "a",
            "capability_id": "cap",
            "protocol": "mcp",
            "success": True,
            "verdict": None,
            "latency_ms": 1,
            "session_id": "s",
            "completed_at": "2026-07-21T00:00:00+00:00",
            "payload": None,
            "prev_hash": "",
        }
        assert compute_content_hash(row) == compute_content_hash(dict(row))
        assert compute_content_hash(row).startswith("sha256:")
