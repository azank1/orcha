# Phase D1 — Validator layer

Thesis reference: [`../EmergeOS-DAN.pdf`](../EmergeOS-DAN.pdf) (fulfillment / attestation chapters).

## Goal

Third parties run **validator nodes** that observe agent executions, publish signed attestations, earn a fee share, and influence discovery reputation — without blocking user-facing latency.

## Validator = ExecutionObserver

Validators implement the existing seam in [`observers.py`](../../../services/superagent/src/superagent/middleware/observers.py):

```python
class ExecutionObserver(Protocol):
    async def on_step_complete(self, record: StepResult) -> None: ...
```

OSS ships `NoOpObserver`. D1 ships:

- **`FulfillmentRecorder`** — reference observer in [`services/validator/`](../../../services/validator/)
- **`emerge validate`** — standalone process subscribing to the observer stream

Observers run **after** OutputNormalizer; failures must not break execution (already tested).

## Event fan-out

SuperAgent publishes each `StepResult` to Kafka topic **`execution.step_complete`** (in addition to in-process observer).

Payload mirrors `StepResult` dataclass fields as JSON.

Validators consume the topic; coordinators may also consume for metrics.

Env: `KAFKA_ENABLED=true`, `KAFKA_BOOTSTRAP_SERVERS=...` (same as registry).

## Attestation schema

Validators emit signed attestations:

```json
{
  "schema_version": "1.0",
  "call_id": "call-abc",
  "agent_id": "did:orcha:agent:web-scraper",
  "validator_did": "did:orcha:validator:alice",
  "success": true,
  "latency_ms": 120,
  "judge_score": 0.92,
  "notes": "output matched task intent",
  "observed_at": "2026-06-16T00:00:01Z",
  "signature_b64": "..."
}
```

- `judge_score` ∈ [0, 1] — D1 spike uses heuristic; D2 merges semantic judge.
- Store: Postgres table `validator_attestations` (future migration) or spike in-memory/file.

## Fee split (mock first)

Extend emerge.yaml payment block (RFC before schema bump):

```yaml
payment:
  enabled: true
  base_fee: "0.10"
  coordinator_share_bps: 1000   # 10% — optional, default from platform constant
  validator_share_bps: 500        # 5% — paid to attesting validator pool
```

Settlement (`settle_invocation`) uses [`split_revenue_dan`](../../../common/pricing/src/common_pricing/formulae.py):

```
agent_share = base_fee - coordinator_cut - validator_cut
```

Spike: when `VALIDATOR_DID` env set on SuperAgent, attribute validator_cut to mock ledger field on transaction row (log-only if DB column missing).

## Reputation API (target)

```
GET /api/v1/agents/{did}/reputation
```

Response:

```json
{
  "agent_id": "did:orcha:agent:...",
  "attestation_count": 42,
  "mean_judge_score": 0.88,
  "validator_quorum": 3
}
```

PnD `routing_score()` adds reputation term (future).

## CLI

```bash
emerge validate \
  --bootstrap /ip4/127.0.0.1/tcp/9100 \
  --validator-did did:orcha:validator:alice \
  --kafka localhost:9092
```

Spike: `emerge validate --once` processes one synthetic StepResult for demo.

## Acceptance criteria

| # | Test |
|---|---|
| AC-D1-1 | `emit_step_complete` publishes to Kafka when enabled |
| AC-D1-2 | `FulfillmentRecorder` writes attestation without raising |
| AC-D1-3 | `split_revenue_dan` sums to `base_fee` |
| AC-D1-4 | Settlement logs validator_cut when `VALIDATOR_DID` set |

## Dependencies

- **D0 signed identity** required for trustworthy attestations in production.
- D1 spike may use synthetic keys for local demo.

## Out of scope (D1)

- On-chain validator staking / slashing
- Autonomous `@autonomous` agent loop (ROADMAP Phase 1 overlap — separate RFC)
