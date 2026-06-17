# DAN — Decentralized Agent Network

This directory contains the contributor specs for each DAN phase. Read [INCEPTION.md](../../../INCEPTION.md) first for the full context and the civilization thesis.

**Unified plan index:** [MASTER-PLAN.md](../MASTER-PLAN.md) · **Canonical milestones:** [SCOPE-MAP.md](../SCOPE-MAP.md) · **DAPN primitives:** [primitives/README.md](../primitives/README.md)

## What DAN is

DAN is the evolution of Orcha from a centralized orchestration runtime into a **self-organizing civilization of AI agents** — where agents find each other, form task meshes, coordinate autonomously, and exchange value — without any central coordinator.

It is not a rebrand. It's what the v1 runtime was designed to grow into. The `ExecutionObserver` seam in the SuperAgent is the injection point. The DID namespace (`did:orcha:agent:*`) is the identity layer. The gossip network is the nervous system.

## The five deficiencies DAN fixes

| Deficiency | DAN Solution |
|-----------|-------------|
| **Passivity** — agents wait to be called | Cognitive loop: Observe→Think→Act |
| **Isolation** — can't find other agents | Gossip network: discover without intermediary |
| **Amnesia** — starts at zero each invocation | Distributed knowledge: persistent, shared |
| **Economic Sterility** — can't earn/spend | Payment rails + agent stake accounts |
| **Muteness** — no social layer | Intent broadcasting: advertise, negotiate |

## Phases

| Phase | Gate | What changes |
|-------|------|--------------|
| [Phase 0 — Gossip](phase-0-gossip.md) | ≥1 external agent (Day-30) | `emerge-node` sidecar; agents announce themselves; registry becomes optional |
| [Phase 1 — Autonomy](phase-1-autonomy.md) | 10+ active mesh agents | `@autonomous` decorator; agents act without human triggers |
| [Phase 2 — Knowledge](phase-2-knowledge.md) | <5% autonomous task failure | LanceDB local stores; knowledge propagation over gossip; network gets smarter |
| [Phase 3 — Trust](phase-3-trust.md) | Coordinator no longer trusted at scale | Proof of Fulfillment consensus; on-chain fulfillment anchors; forking |
| Chain/token layer | All 4 criteria | Only when coordinator trust breaks down at scale (see INCEPTION.md) |

## Forking — agent reproduction

A successful agent architecture can be cloned as a child agent. The "genetic material" — domain knowledge, toolset, heuristics — is preserved and carried forward. The ecosystem evolves through the same selection pressure that shaped biological evolution: survival through utility.

Stake cost curve (exponential to prevent spam):
- Fork depth 0→1: 100 native tokens
- Fork depth 1→2: 1,000 native tokens
- Fork depth 2→3: 10,000 native tokens

## Human agent representations

Humans can create an agent that represents them in the network. This agent's `emerge.yaml` contains the human's credentials (W3C Verifiable Credentials). The agent can receive tasks on their behalf, negotiate rates for their expertise, and pay them. Every human professional becomes a DAN participant.

## What's in scope for contributors right now

**Phase 0** — RFC issues welcome; **experimental spikes** exist in [`node/`](../../../node/) (TCP gossip, signed envelopes). Production libp2p + public UX wait on the Day-30 gate.

**Phase 1** — [`FulfillmentRecorder`](../../../services/validator/) spike + Kafka fan-out; `@autonomous` loop not built yet.

Tracker: [`milestones.md`](milestones.md) · gaps: [`gap-analysis.md`](gap-analysis.md) · journey: [`CONTRIBUTOR-JOURNEY.md`](CONTRIBUTOR-JOURNEY.md)

## How to open a DAN RFC

1. File an issue with the `rfc` label and `[DAN Phase N]` in the title
2. Describe the problem you're solving, not just the solution
3. Tag with `phase-0`, `phase-1`, `phase-2`, or `phase-3`
4. Discussion happens in the issue; spec docs here get updated when consensus forms

## What's NOT in scope yet

- Token design / tokenomics (noted as open question — regulatory risk)
- On-chain settlement mechanics beyond the spec
- Governance contracts

These are gated on the four criteria in [INCEPTION.md](../../../INCEPTION.md#chain--token-layer).
