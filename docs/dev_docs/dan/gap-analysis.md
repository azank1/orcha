# DAN gap analysis — v1 substrate vs phases

Reference: v1 on `main`. Thesis: [`../../../INCEPTION.md`](../../../INCEPTION.md). PDF: [`../EmergeOS-DAN.pdf`](../EmergeOS-DAN.pdf).

## v1 substrate (present)

| Capability | Location | Phase-ready? |
|---|---|---|
| Agent registration (HTTP) | Registry `POST /api/v1/agents/register` | Phase 0 — add signature verify |
| Manifest schema + JSON Schema | `docs/spec/emerge-yaml.schema.json` | Phase 0 — `network.experimental` added |
| `identity.public_key` field | `EmergeConfig` | Phase 0 signing |
| Discovery / planning | PnD | Phase 0 — gossip index |
| Execution pipeline | SuperAgent `ExecutionMiddleware` | Yes |
| Observer seam | `ExecutionObserver` / `NoOpObserver` | Phase 1 — `FulfillmentRecorder` |
| Mock payments | Gateway `PAYMENT_MODE=mock` | Phase 3 preview |
| Revenue split (2-way) | `common_pricing.formulae.split_revenue` | Phase 3 — `split_revenue_dan` spike |
| `emerge publish --registry URL` | SDK CLI | Phase 0 — add `--network` |
| Kafka events | registry + planning topics | Phase 1 — `execution.step_complete` spike |

## Code spikes → canonical phase

| Code on `main` | Phase | Notes |
|---|---|---|
| [`node/`](../../../node/) TCP gossip + signed envelopes | **Phase 0** | Replace with libp2p post-gate |
| [`services/validator/`](../../../services/validator/) | **Phase 1** experimental | Not a standalone “validator phase” |
| [`step_events.py`](../../../services/superagent/src/superagent/middleware/step_events.py) | **Phase 1** experimental | Kafka fan-out |
| Settlement `compute_revenue_split` + env BPS | **Phase 3** preview | Mock ledger only |
| `emerge validate --once` | **Phase 1** experimental | Live consumer TBD |

## Phase 0 gaps

| Missing | Needed for |
|---|---|
| libp2p GossipSub (production transport) | Domain topics, NAT traversal |
| SDK `--network` + gossip publish | Operator UX |
| Registry Ed25519 verify | Trustworthy federated ingest |
| PnD gossip index | Cross-coordinator discovery |
| Day-30 gate passed | Spec freeze + public gossip UX |

## Phase 1 gaps

| Missing | Needed for |
|---|---|
| `@autonomous` + tiered cognitive loop | Agency without human trigger |
| Live `emerge validate` consumer | Validator role |
| Attestation DB + reputation API | Routing by trust |

## Phase 2–3 gaps

See [`phase-2-knowledge.md`](phase-2-knowledge.md) and [`phase-3-trust.md`](phase-3-trust.md). On-chain settlement deferred per four gates in INCEPTION.md.

## Honest messaging

- **Experimental spikes ≠ production DAN** — require `network.experimental: true` until Day-30.
- **Phase 0 is federated, not fully decentralized** — trusted bootstrap first.
- **Mock credits ≠ network economy** — Phase 3+ for real settlement.
