"""Append-only, hash-chained audit ledger (KY-A supervisory harness, WS7).

A ``LedgerObserver`` installed via ``set_observer()`` appends one row per
completed execution step to the ``audit_ledger`` table. Each row carries a
``content_hash`` over the canonical row content plus the previous row's hash
(``prev_hash``), forming a tamper-evident chain.

Design contract (dev-srs FR-7 / NFR 6.3):

- DB append is the source of truth — no Kafka dependency.
- Rows are never updated or deleted by application code.
- The observer fails closed: any ledger error is logged, never raised into
  the user-facing execution path (the pipeline already guards the call; this
  module additionally never raises internally).
- Content stays credential-free: only the fields already present on the
  credential-free ``StepResult`` plus explicit decision payloads are hashed.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from .observers import StepResult

logger = logging.getLogger(__name__)

ENTRY_TYPE_STEP = "step_complete"
ENTRY_TYPE_HITL_DECISION = "hitl_decision"

# Fields covered by the content hash for step rows (FR-7.2).
_HASH_FIELDS = (
    "entry_type",
    "call_id",
    "agent_id",
    "capability_id",
    "protocol",
    "success",
    "verdict",
    "latency_ms",
    "session_id",
    "completed_at",
    "payload",
)


def _canonical_default(value: Any) -> str:
    """JSON default that renders datetimes as ISO strings (stable hashing)."""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def compute_content_hash(row: dict[str, Any]) -> str:
    """Return ``sha256:<hex>`` over the canonical row content + ``prev_hash``.

    Canonicalisation (sorted keys, compact separators, ISO datetimes) makes the
    hash stable across processes so the chain can be verified offline.
    """
    material = {field: row.get(field) for field in _HASH_FIELDS}
    material["prev_hash"] = row.get("prev_hash", "")
    canonical = json.dumps(
        material, sort_keys=True, separators=(",", ":"), default=_canonical_default
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_chain(entries: list[dict[str, Any]]) -> bool:
    """Verify a sequence of ledger rows (in append order) forms a valid chain."""
    prev_hash = ""
    for entry in entries:
        if entry.get("prev_hash", "") != prev_hash:
            return False
        if compute_content_hash(entry) != entry.get("content_hash"):
            return False
        prev_hash = entry["content_hash"]
    return True


def _parse_completed_at(raw: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed
    except (TypeError, ValueError):
        return datetime.now(UTC)


class LedgerObserver:
    """ExecutionObserver that appends each StepResult to the audit ledger.

    A single instance is installed process-wide at SuperAgent boot when
    ``AUDIT_LEDGER_ENABLED=true``. Owns its Prisma connection lazily so a
    missing database degrades to log-only behaviour (fail closed).
    """

    def __init__(self, db: Any = None) -> None:
        self._db = db
        self._owns_db = db is None

    async def _ensure_db(self) -> Any:
        if self._db is None:
            from src.generated_client import Prisma

            self._db = Prisma()
        if self._owns_db and not self._db.is_connected():
            await self._db.connect()
        return self._db

    async def _current_tip_hash(self, db: Any) -> str:
        tip = await db.auditledgerentry.find_first(
            order=[{"created_at": "desc"}, {"id": "desc"}]
        )
        return tip.content_hash if tip else ""

    async def append(
        self,
        *,
        entry_type: str,
        call_id: str = "",
        agent_id: str = "",
        capability_id: str = "",
        protocol: str = "",
        success: bool = False,
        verdict: dict[str, Any] | None = None,
        latency_ms: int = 0,
        session_id: str = "",
        completed_at: datetime | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Append one row to the ledger. Returns the stored row dict, or None on failure.

        Never raises — ledger failures must not break the caller.
        """
        try:
            db = await self._ensure_db()
            prev_hash = await self._current_tip_hash(db)
            ts = completed_at or datetime.now(UTC)
            # Postgres TIMESTAMP(3) stores milliseconds — truncate so the hash
            # matches the row when read back from the DB for verification.
            ts = ts.replace(microsecond=(ts.microsecond // 1000) * 1000)
            row: dict[str, Any] = {
                "entry_type": entry_type,
                "call_id": call_id,
                "agent_id": agent_id,
                "capability_id": capability_id,
                "protocol": protocol,
                "success": success,
                "verdict": verdict,
                "latency_ms": latency_ms,
                "session_id": session_id,
                "completed_at": ts.isoformat(),
                "payload": payload,
                "prev_hash": prev_hash,
            }
            row["content_hash"] = compute_content_hash(row)

            from src.generated_client.fields import Json as PrismaJson

            data: dict[str, Any] = {
                "entry_type": entry_type,
                "call_id": call_id,
                "agent_id": agent_id,
                "capability_id": capability_id,
                "protocol": protocol,
                "success": success,
                "latency_ms": latency_ms,
                "session_id": session_id,
                "completed_at": ts,
                "content_hash": row["content_hash"],
                "prev_hash": prev_hash,
            }
            if verdict is not None:
                data["verdict"] = PrismaJson(verdict)
            if payload is not None:
                data["payload"] = PrismaJson(payload)
            await db.auditledgerentry.create(data=data)
            return row
        except Exception:
            logger.exception(
                "Audit ledger append failed (entry_type=%s call_id=%s); continuing",
                entry_type,
                call_id,
            )
            return None

    async def on_step_complete(self, record: StepResult) -> None:
        """Observer contract — one ledger row per completed execution step."""
        await self.append(
            entry_type=ENTRY_TYPE_STEP,
            call_id=record.call_id,
            agent_id=record.agent_id,
            capability_id=record.capability_id,
            protocol=record.protocol,
            success=record.success,
            verdict=record.verdict,
            latency_ms=record.latency_ms,
            session_id=record.session_id,
            completed_at=_parse_completed_at(record.completed_at),
            payload={
                "tool_name": record.tool_name,
                "content_digest": "sha256:"
                + hashlib.sha256((record.content or "").encode("utf-8")).hexdigest(),
            },
        )


async def get_session_trail(session_id: str, db: Any = None) -> list[dict[str, Any]]:
    """Assemble the per-case rationale trail for a session (FR-7.4).

    Returns ledger rows in append order as plain dicts. Used by the case-file
    composer (WS8) and the attestation signer (WS9).
    """
    owns_db = db is None
    if owns_db:
        from src.generated_client import Prisma

        db = Prisma()
        await db.connect()
    try:
        rows = await db.auditledgerentry.find_many(
            where={"session_id": session_id},
            order=[{"created_at": "asc"}, {"id": "asc"}],
        )
        return [
            {
                "entry_type": r.entry_type,
                "call_id": r.call_id,
                "agent_id": r.agent_id,
                "capability_id": r.capability_id,
                "protocol": r.protocol,
                "success": r.success,
                "verdict": r.verdict,
                "latency_ms": r.latency_ms,
                "session_id": r.session_id,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "payload": r.payload,
                "content_hash": r.content_hash,
                "prev_hash": r.prev_hash,
            }
            for r in rows
        ]
    finally:
        if owns_db:
            await db.disconnect()


async def has_approved_hitl_decision(session_id: str, db: Any = None) -> bool:
    """True when the session's ledger holds an APPROVED hitl_decision row.

    Used by the case-attestation ordering guard: a case that warrants
    enforcement may only be sealed after a named human has approved the
    proposal (FR-6.3 / FR-9).
    """
    owns_db = db is None
    if owns_db:
        from src.generated_client import Prisma

        db = Prisma()
        await db.connect()
    try:
        row = await db.auditledgerentry.find_first(
            where={
                "session_id": session_id,
                "entry_type": ENTRY_TYPE_HITL_DECISION,
                "success": True,
            }
        )
        return row is not None
    except Exception:
        logger.exception(
            "has_approved_hitl_decision: lookup failed for session %s", session_id
        )
        return False
    finally:
        if owns_db:
            await db.disconnect()
