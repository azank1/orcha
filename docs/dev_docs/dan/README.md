# DAN — Decentralized Agent Network

This directory contains the contributor specs for each DAN phase. Read [INCEPTION.md](../../../INCEPTION.md) first for the full context.

## What DAN is

DAN is the evolution of Orcha from a centralized orchestration runtime into a **decentralized mesh where agents find each other, form task groups, and coordinate autonomously** — without any central coordinator.

It is not a rebrand. It's what the v1 runtime was designed to grow into. The `ExecutionObserver` seam in the SuperAgent is the injection point.

## Phases

| Phase | Gate | What changes |
|-------|------|--------------|
| [Phase 0 — Gossip](phase-0-gossip.md) | ≥1 external agent (Day-30) | Agents announce themselves; registry becomes optional |
| [Phase 1 — Autonomy](phase-1-autonomy.md) | 10+ active mesh agents | Agents act without human triggers |
| [Phase 2 — Knowledge](phase-2-knowledge.md) | <5% autonomous task failure | Agents share learned context across the mesh |
| Chain/token layer | All 4 criteria | Only when coordinator trust breaks down at scale |

## What's in scope for contributors right now

**Phase 0 design** is open for discussion and RFC issues — it hasn't been built yet. If you have opinions on the gossip protocol, peer discovery, or signed envelope format, open an RFC issue.

**Phase 1 and 2** are further out. Specs here are working documents, not frozen designs.

## How to open a DAN RFC

1. File an issue with the `rfc` label and `[DAN]` in the title
2. Describe the problem you're solving, not just the solution
3. Tag `phase-0`, `phase-1`, or `phase-2` as appropriate
4. Discussion happens in the issue; the spec doc here gets updated when consensus forms

## What's NOT in scope yet

- Token design or tokenomics
- On-chain settlement
- Governance contracts

These are gated on the four criteria in [INCEPTION.md](../../../INCEPTION.md#chain--token-layer). Opening issues about them before the gates pass will be closed.
