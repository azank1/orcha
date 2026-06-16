# INCEPTION

> The how, who, what, and when of DAN — the Decentralized Agent Network.

---

## The problem

AI models are extraordinary. The missing piece isn't intelligence — it's coordination.

Today's agents are islands:

- They speak **different protocols** (MCP, A2A, ACP — and more emerging)
- They **can't find each other** without a human wiring them together
- They **can't trust each other** without centralized coordination
- They **can't settle exchanges** without a middleman

Every new agent framework adds more islands. The ecosystem fragments further with each one.

**This is not a model problem. It's an orchestration, observability, and distribution problem.**

---

## What Orcha solves today

Orcha is the runtime that bridges the protocol gap.

One natural-language goal gets **planned, routed, and executed** across agents speaking different protocols in a single run — with auth, a credential vault, output normalization, and per-call payments baked in.

This is the foundation layer. It has to work perfectly, at scale, before DAN can exist.

The key seam: `ExecutionObserver` — a no-op hook in the SuperAgent today. Every agent invocation passes through it. It's where the gossip layer hooks in tomorrow.

---

## What DAN means

DAN — Decentralized Agent Network — is the endgame.

A world where:

- Agents **discover each other** via a gossip mesh — no registry you have to run
- Agents **form task meshes dynamically** for multi-step goals
- Agents **coordinate autonomously** using an Observe→Think→Act loop
- Agents **settle exchanges trustlessly** — no central coordinator required

DAN is not a product feature. It's an emergent property of enough well-built, well-connected agents running on a shared open standard.

The chain and token layer comes **last**, not first. We will not announce a token before four hard gates pass (see below).

---

## The phases

### Phase 0 — Gossip
**Gate:** ≥1 external agent registered in the wild (Day-30 adoption signal)

`emerge-node` sidecar + libp2p GossipSub. Agents announce themselves. The central registry becomes optional — then eventually redundant.

What gets built:
- `emerge-node` daemon that runs alongside any agent
- Signed agent envelopes using the existing `did:orcha:agent:*` DID namespace
- Bootstrap node set for initial peer discovery
- GossipSub topic: `orcha/agents/v1`

Technical deep-dive: [`docs/dev_docs/dan/phase-0-gossip.md`](docs/dev_docs/dan/phase-0-gossip.md)

---

### Phase 1 — Autonomous Loop
**Gate:** 10+ active agents in the gossip mesh

`@autonomous` decorator. Agents can Observe→Think→Act without a human trigger. The `ExecutionObserver` seam (already in `services/superagent/`) becomes the data backbone.

What gets built:
- `@autonomous` decorator extending the existing `@emerge.agent` SDK
- Observe→Think→Act state machine
- `FulfillmentRecorder` — logs autonomous task completions via `ExecutionObserver`
- Hosted (optional) fulfillment data layer for analysis

Technical deep-dive: [`docs/dev_docs/dan/phase-1-autonomy.md`](docs/dev_docs/dan/phase-1-autonomy.md)

---

### Phase 2 — Knowledge
**Gate:** Autonomous tasks completing end-to-end with <5% failure rate

Local-first vector store + knowledge propagation. Agents share learned context across the mesh. The network gets smarter over time.

What gets built:
- Local-first vector store per agent (extends existing pgvector in Planning & Discovery)
- Knowledge propagation protocol over GossipSub
- Privacy model: agents declare what they share vs. keep local

Technical deep-dive: [`docs/dev_docs/dan/phase-2-knowledge.md`](docs/dev_docs/dan/phase-2-knowledge.md)

---

### Chain / token layer
**Gate: ALL four must hold simultaneously**

- [ ] The coordinator can no longer be trusted by a large, diverse network
- [ ] Stakes are large enough to demand trustless settlement
- [ ] Third parties demand permissionless entry without coordinator approval
- [ ] The community demands on-chain governance

Until then: USDC + trusted coordinator. This is sufficient and safer for the current network size. We will not announce a token before this gate.

---

## Who we need

**Bridge builders** — New protocol adapters are the highest-leverage contribution. If you know a protocol we don't support, write a bridge. Start at [`templates/your-first-bridge/`](templates/your-first-bridge/).

**Agent authors** — Every new agent in [`agents/`](agents/) proves the runtime works and hits edge cases we haven't seen. Each one becomes a test we need.

**DAN architects** — Phase 0–2 specs are open RFC issues. The mesh design should come from the community that will run it. File an issue with the `rfc` label.

**Operators** — Run a node. Stress the registry. Break the planner. Real adoption signals gate the DAN phases — without external agents, DAN doesn't start.

---

## The seam that's already there

```python
# services/superagent/src/superagent/observers/execution_observer.py
class ExecutionObserver:
    async def on_invocation(self, event: InvocationEvent) -> None:
        pass  # no-op today — DAN hooks in here
```

Every agent invocation in v1 passes through `ExecutionObserver`. In DAN Phase 1, this is where fulfillment gets recorded and propagated. This wasn't an accident — it was the injection point designed into v1 so DAN doesn't require a rewrite.

---

## The timeline

Gates are adoption signals, not dates. We build the next layer only when the current one is validated.

| Gate | Unlocks |
|------|---------|
| ≥1 external agent (Day-30) | Phase 0 engineering begins |
| 10+ active mesh agents | Phase 1 engineering begins |
| <5% autonomous task failure rate | Phase 2 engineering begins |
| All 4 chain criteria | Chain/token layer begins |

---

*Orcha is Apache 2.0. The vision is open. Come build it.*
