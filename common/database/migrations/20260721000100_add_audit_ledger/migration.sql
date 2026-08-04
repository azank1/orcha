-- Append-only hash-chained audit ledger (KY-A supervisory harness, WS7 / FR-7).
-- Rows are never updated or deleted by application code; the hash chain
-- (content_hash over row content + prev_hash) makes tampering evident.

CREATE TABLE "audit_ledger" (
    "id" TEXT NOT NULL,
    "entry_type" TEXT NOT NULL DEFAULT 'step_complete',
    "call_id" TEXT NOT NULL DEFAULT '',
    "agent_id" TEXT NOT NULL DEFAULT '',
    "capability_id" TEXT NOT NULL DEFAULT '',
    "protocol" TEXT NOT NULL DEFAULT '',
    "success" BOOLEAN NOT NULL DEFAULT false,
    "verdict" JSONB,
    "latency_ms" INTEGER NOT NULL DEFAULT 0,
    "session_id" TEXT NOT NULL DEFAULT '',
    "completed_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "payload" JSONB,
    "content_hash" TEXT NOT NULL,
    "prev_hash" TEXT NOT NULL DEFAULT '',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "audit_ledger_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "audit_ledger_session_id_idx" ON "audit_ledger"("session_id");
CREATE INDEX "audit_ledger_call_id_idx" ON "audit_ledger"("call_id");
