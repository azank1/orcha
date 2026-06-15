# Phase D2 — Knowledge propagation

Thesis reference: [`../EmergeOS-DAN.pdf`](../EmergeOS-DAN.pdf).

## Goal

Execution summaries and manifest embeddings propagate across the network so coordinators and validators share **local-first knowledge** without a central data warehouse.

## Overlap with v1.2 Harness

ROADMAP v1.2 includes:

- Output verification / semantic judging
- Context manager for long-running tasks

D2 must **not** introduce a second judge system. One RFC will define:

- Harness judge (inline, blocks retry decisions)
- Validator attestation judge (async, feeds reputation)

## Planned capabilities

| Capability | Description |
|---|---|
| Cross-node manifest summaries | Gossip compact capability vectors after registration |
| Execution digest propagation | Validators publish anonymized fulfillment digests |
| Local-first vector store | Each node retains embeddings; periodic sync with CRDT or gossip |
| Reputation-weighted retrieval | PnD merges semantic match + validator consensus |

## Status

Spec only — implementation blocked until D1 attestation store exists.

## Acceptance criteria (future)

- Node A registration visible in Node B PnD index within N seconds
- Validator attestation changes agent ranking on Node B without central DB write
