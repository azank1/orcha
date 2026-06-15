# Orcha Roadmap

This is the public trajectory for Orcha. It describes the direction, not a dated
commitment. Anything beyond **v1** is gated on real adoption signal — we build
the next layer only when the current one is validated.

## v1 — Open runtime (launch)

The multi-protocol orchestration runtime, fully usable locally in mock payment
mode.

- Core services: Registry, Planning & Discovery, SuperAgent, Gateway (mock)
- Three protocols orchestrated in one run: **MCP**, **A2A**, **ACP**
- Execution pipeline: input validation, credential vault + auth cascade
  (OAuth included), output normalization, human-in-the-loop interrupts,
  per-call payments (mock mode by default)
- 7 example agents + agent/bridge templates
- `emerge` CLI (`init` / `run` / `publish`) and the `@emerge.agent` SDK decorator
- Versioned `emerge.yaml` spec with JSON Schema + RFC governance
- `ExecutionObserver` seam — a no-op hook in OSS; the injection point for any
  future hosted data layer

## v1.2 — Harness (gated on RAT validation)

Reliability work for production-grade orchestration. **Does not block launch.**

- DAG executor for parallel/dependent step execution
- Output verification / semantic judging
- Retry & fallback policies
- Context manager for long-running multi-step tasks

## Beyond v1 — DAN (gated on Day-30 adoption signal)

The decentralized agent network. **No DAN engineering starts before the Day-30
adoption gate passes** (≥1 external agent registration is the gold signal). All
early phases use a trusted-coordinator model — no chain, no token.

- **Phase 0 — Gossip:** `emerge-node` sidecar, libp2p GossipSub, signed
  envelopes, bootstrap nodes
- **Phase 1 — Autonomous loop:** Observe→Think→Act, `@autonomous` decorator,
  hosted FulfillmentRecorder
- **Phase 2 — Knowledge:** local-first vector store, knowledge propagation

### Chain / token layer

Deferred until **all four** criteria hold: the coordinator can no longer be
trusted by a large diverse network, stakes demand trustless settlement, third
parties want permissionless entry, and the community demands on-chain
governance. Until then, USDC + coordinator suffice. We will not announce a token
before this gate.

---

Have an opinion on direction? Open a discussion issue or join the community.
Design questions for DAN phases are filed as public RFC issues — participation
is the point.
