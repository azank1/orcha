# Vision — Orcha → DAN

Orcha is open-source **agent orchestration and observability infrastructure**. The long-term goal is the **Decentralized Agent Network (DAN)**: a participatable network where agents discover each other, delegate work, accumulate reputation, and earn — without every integration being hand-wired by a human.

Canonical thesis: [`docs/dev_docs/EmergeOS-DAN.pdf`](docs/dev_docs/EmergeOS-DAN.pdf).

This document is the **public** summary. Internal execution specs live in [`docs/dev_docs/dan/`](docs/dev_docs/dan/).

---

## This is not a model problem

The industry optimizes **which LLM wins**. The harder problem is **how agents exist in the world**:

- Who routes a task to the right specialist?
- Who observes whether execution was honest and useful?
- Who remembers what worked across calls and operators?
- Who gets paid, and who attests that payment was fair?

Orcha answers the **usage layer**: multi-protocol orchestration, credential handling, output normalization, payments, and hooks for distributed observation.

DAN answers the **distribution layer**: gossip discovery, validator attestations, knowledge propagation, and progressive decentralization of trust.

**A2A / MCP / ACP are wire formats. Orcha is the runtime. DAN is the network.**

---

## Five deficiencies → five network properties

| Deficiency | Today | DAN direction |
|---|---|---|
| Passivity | React-only agents | Orchestrated runs today; autonomous loops later |
| Isolation | Manual wiring | Gossip + federated discovery (`emerge-node`) |
| Amnesia | Stateless invocations | Execution records + knowledge layer |
| Economic sterility | Mock credits in OSS | Fee splits, validator shares, reputation-weighted routing |
| Muteness | Hidden capabilities | Signed manifests broadcast to the network |

---

## Three layers (north star)

```
┌─────────────────────────────────────────────────────────┐
│  Layer 3 · Trust & value                                │
│  Identity · attestations · settlement · (chain later)   │
├─────────────────────────────────────────────────────────┤
│  Layer 2 · Knowledge                                    │
│  Local-first stores · gossip-propagated learnings       │
├─────────────────────────────────────────────────────────┤
│  Layer 1 · Communication                              │
│  P2P gossip · intent · capability offers · heartbeats   │
└─────────────────────────────────────────────────────────┘
```

Everything in the public repo today implements **Layer 0 — the trusted local coordinator**: Registry, Planning & Discovery, SuperAgent, Gateway, `emerge` SDK, and the `ExecutionObserver` seam.

Spikes already in tree:

| Layer | Spike / module |
|---|---|
| L1 Communication | [`node/`](node/) — signed manifests, TCP gossip (libp2p target) |
| L3 Trust (partial) | [`services/validator/`](services/validator/) — `FulfillmentRecorder`, fee split in settlement |

---

## Progressive decentralization (honest messaging)

We follow the same path as every serious network protocol:

1. **Prove orchestration works** — open runtime, mock payments, real multi-protocol runs
2. **Open the seams** — gossip, validators, reputation APIs
3. **Decentralize trust** — only when coordinator trust, stakes, and community demand require it

No token announcement before [D3 gates](docs/dev_docs/dan/D3-settlement-gates.md) are met. Mock credits ≠ network economy — we say so explicitly.

---

## What success looks like

**For developers:** wrap existing MCP/A2A agents, join discovery, earn from orchestrated calls — minimal rewrite.

**For operators:** run a coordinator, an agent, or a validator node — pick a role, not a vendor lock-in.

**For the ecosystem:** observability and reputation distributed across participants, not hoarded inside one platform's dashboard.

---

## Where to go next

| Doc | Purpose |
|---|---|
| [`ROADMAP.md`](ROADMAP.md) | Milestones: v1 → D0 → D1 → D2 → D3 |
| [`docs/quickstart.md`](docs/quickstart.md) | Clone to running agent |
| [`docs/dev_docs/dan/`](docs/dev_docs/dan/) | Internal DAN execution plans |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to PR, commit style, ground rules |

Questions or design opinions → open a GitHub discussion. Participation is the point.
