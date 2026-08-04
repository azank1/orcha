-- Ed25519-signed case attestations (supervisory attestation layer).
-- Each row binds a session's case payload (case_hash = sha256 of the canonical
-- payload) to an Ed25519 signature. The thin anchor adapter later fills
-- chain_id/tx_hash when status → anchored; "skipped" means anchoring was
-- disabled (mock-first demo path). Independent of the payment "transactions"
-- table (FR-9.2).

CREATE TABLE "attestations" (
    "id" TEXT NOT NULL,
    "session_id" TEXT NOT NULL,
    "case_hash" TEXT NOT NULL,
    "payload" JSONB NOT NULL,
    "signature" TEXT NOT NULL,
    "public_key" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "chain_id" TEXT,
    "tx_hash" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "anchored_at" TIMESTAMP(3),

    CONSTRAINT "attestations_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "attestations_session_id_idx" ON "attestations"("session_id");
