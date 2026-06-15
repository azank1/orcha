# DAN milestones tracker

Internal execution tracker (like [oss-launch/sprint-plan.md](../oss-launch/sprint-plan.md)).

## D0 — Network surface

| ID | Deliverable | Status |
|---|---|---|
| D0-1 | `node/` package + `emerge-node` CLI | Spike done (TCP gossip; libp2p TBD) |
| D0-2 | Signed manifest envelope (Ed25519) | Spike in `node/src/emerge_node/envelope.py` |
| D0-3 | Two-peer gossip integration test | `node/tests/test_gossip_spike.py` |
| D0-4 | SDK `emerge publish --network` | Not started |
| D0-5 | Registry verify signature on ingest | Not started |
| D0-6 | PnD index gossip manifests | Not started |
| D0-7 | Acceptance: machine B discovers machine A agent | Not started |

## D1 — Validator layer

| ID | Deliverable | Status |
|---|---|---|
| D1-1 | `execution.step_complete` Kafka topic | Spike in `common/kafka/src/topics.py` |
| D1-2 | Fan-out from `emit_step_complete` | Spike in observers module |
| D1-3 | `FulfillmentRecorder` reference observer | `services/validator/` |
| D1-4 | `emerge validate` CLI | Spike in SDK |
| D1-5 | Attestation JSON schema | [D1-validators.md](D1-validators.md) |
| D1-6 | Three-way mock fee split | `split_revenue_dan` + settlement hook |
| D1-7 | Reputation API on Registry | Not started |

## D2 — Knowledge propagation

| ID | Deliverable | Status |
|---|---|---|
| D2-1 | Spec merge with v1.2 Harness judge | [D2-knowledge.md](D2-knowledge.md) draft |
| D2-2 | Implementation | Not started |

## D3 — Trustless settlement

| ID | Deliverable | Status |
|---|---|---|
| D3-1 | Four gate criteria documented | [D3-settlement-gates.md](D3-settlement-gates.md) |
| D3-2 | Chain/token engineering | Blocked on gates |
