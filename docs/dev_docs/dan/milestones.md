# DAN milestones tracker

Internal execution tracker. Thesis: [`../../../INCEPTION.md`](../../../INCEPTION.md). Contributor journey: [`CONTRIBUTOR-JOURNEY.md`](CONTRIBUTOR-JOURNEY.md).

## Experimental gate (pre Day-30)

DAN code may land behind `network.experimental: true` in emerge.yaml. The **Day-30 gate** (≥1 external agent registered) controls:

- Default-on in SDK templates
- Phase 0 spec freeze
- Public advertising of gossip / validate UX

| Check | Status |
|---|---|
| `network.experimental` in JSON Schema | Done |
| CLI guards for live DAN modes | Done |
| Day-30 external agent signal | Pending |

---

## Phase 0 — Gossip

**Gate:** ≥1 external agent registered (Day-30). Spec: [`phase-0-gossip.md`](phase-0-gossip.md).

| ID | Deliverable | Experimental | Status |
|---|---|---|---|
| P0-1 | `node/` + `emerge-node` CLI | yes | Spike (TCP; libp2p TBD) |
| P0-2 | Signed manifest envelopes | yes | Spike in `node/src/emerge_node/envelope.py` |
| P0-3 | Two-peer gossip test | yes | `node/tests/test_gossip_spike.py` |
| P0-4 | SDK `emerge publish --network` | yes | Not started |
| P0-5 | Registry signature verify on ingest | yes | Not started |
| P0-6 | PnD gossip manifest index | yes | Not started |
| P0-7 | AC: machine B discovers machine A | no (post-gate) | Not started |
| P0-8 | libp2p GossipSub + domain topics | no (post-gate) | Spec in phase-0-gossip.md |

---

## Phase 1 — Autonomous loop

**Gate:** 10+ active agents in gossip mesh. Spec: [`phase-1-autonomy.md`](phase-1-autonomy.md).

| ID | Deliverable | Experimental | Status |
|---|---|---|---|
| P1-1 | `@autonomous` decorator + cognitive loop | yes | Not started |
| P1-2 | Tiered fast/slow path | yes | Spec only |
| P1-3 | `FulfillmentRecorder` reference observer | yes | `services/validator/` |
| P1-4 | `execution.step_complete` Kafka fan-out | yes | Spike in SuperAgent middleware |
| P1-5 | `emerge validate --once` demo CLI | yes | SDK spike |
| P1-6 | Live `emerge validate` Kafka consumer | yes | Not started |
| P1-7 | `KNOWLEDGE_BROADCAST` messages | yes | Not started |

---

## Phase 2 — Knowledge

**Gate:** Autonomous tasks <5% failure rate. Spec: [`phase-2-knowledge.md`](phase-2-knowledge.md).

| ID | Deliverable | Status |
|---|---|---|
| P2-1 | LanceDB local store in emerge-node | Not started |
| P2-2 | Knowledge fragment propagation | Not started |
| P2-3 | Merge semantic judge with Harness v1.2 | RFC pending |

---

## Phase 3 — Trust

**Gate:** Coordinator no longer trusted at scale. Spec: [`phase-3-trust.md`](phase-3-trust.md).

| ID | Deliverable | Status |
|---|---|---|
| P3-1 | `split_revenue_dan` mock three-way split | Spike (env BPS on SuperAgent) |
| P3-2 | Reputation API | Not started |
| P3-3 | PoF consensus + on-chain anchors | Spec only |
| P3-4 | Chain/token | Blocked on four gates in INCEPTION.md |

---

## Phase 4 — Open network

**Gate:** Legal review + community validators. See [`ROADMAP.md`](../../../ROADMAP.md).

| ID | Deliverable | Status |
|---|---|---|
| P4-1 | DAN Chain mainnet | Not started |
| P4-2 | Community bootstrap nodes | Not started |
| P4-3 | `emerge-node` full OSS release | Partial (spike in `node/`) |
