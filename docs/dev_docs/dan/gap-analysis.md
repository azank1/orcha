# DAN gap analysis — v1 substrate vs network phases

Reference: v1 merged at `main` (SDK, launch gate, ExecutionObserver seam). Thesis: [`../EmergeOS-DAN.pdf`](../EmergeOS-DAN.pdf).

## v1 substrate (present)

| Capability | Location | DAN-ready? |
|---|---|---|
| Agent registration (HTTP) | Registry `POST /api/v1/agents/register` | Yes — extend with signature verify |
| Manifest schema + JSON Schema | `docs/spec/emerge-yaml.schema.json` | Yes — add fee-split fields in D1 RFC |
| `identity.public_key` field | `EmergeConfig` | Present — signing not wired in SDK yet |
| Discovery / planning | PnD | Yes — needs gossip-fed manifest index |
| Execution pipeline | SuperAgent `ExecutionMiddleware` | Yes |
| Observer seam | `ExecutionObserver` / `NoOpObserver` | Yes — D1 injects `FulfillmentRecorder` |
| Mock payments | Gateway `PAYMENT_MODE=mock` | Yes — extend settlement split |
| Revenue split (2-way) | `common_pricing.formulae.split_revenue` | Partial — needs validator/coordinator BPS |
| `emerge publish --registry URL` | SDK CLI | Yes — add `--network` in D0 |
| Kafka events | `registry.agent.registered`, etc. | Yes — add `execution.step_complete` (D1 spike) |

## D0 gaps

| Missing | Needed for |
|---|---|
| `emerge-node` process | Gossip transport between operators |
| Signed manifest envelopes | Trustworthy federated registry ingest |
| Bootstrap peer configuration | Join network without manual URLs |
| PnD gossip index | Discover remote agents |
| libp2p GossipSub (production) | Replace TCP spike transport |

## D1 gaps

| Missing | Needed for |
|---|---|
| `FulfillmentRecorder` + `emerge validate` | Validator role |
| Attestation store + schema | Reputation |
| `execution.step_complete` fan-out | Validators consume without blocking execution |
| Three-way fee split | Operator + validator + coordinator |
| `GET /agents/{did}/reputation` | Consumer-facing trust signal |

## D2 gaps

Local-first vector propagation, cross-node execution summaries — spec in [D2-knowledge.md](D2-knowledge.md); overlaps v1.2 Harness semantic judging (merge judge systems in one RFC).

## D3 gaps

On-chain settlement, permissionless entry, token — explicitly deferred. Hosted USDC/Privy remains out of OSS per [SECURITY.md](../../../SECURITY.md).

## Honest messaging

- **D0 is federated, not fully decentralized** — trusted bootstrap peers, coordinator still routes.
- **Mock credits ≠ network economy** — document in all public-facing copy until D3 gates pass.
- **Validators require D0 keys** — attestations without signed identity are spoofable.
