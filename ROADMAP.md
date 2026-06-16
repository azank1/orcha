# Orcha Roadmap

> For the full DAN vision — the why, who, what, and when — read [INCEPTION.md](INCEPTION.md).

This is the public trajectory for Orcha. It describes direction, not dated commitments. Each phase is gated on the phase before it being validated by real adoption — we build the next layer only when the current one is earned.

---

## ✅ v1 — OSS Runtime (now)

The multi-protocol orchestration runtime, fully usable locally in mock payment mode.

- Core services: Registry, Planning & Discovery, SuperAgent, Gateway
- Three protocols orchestrated in one run: **MCP**, **A2A**, **ACP**
- Execution pipeline: input validation, credential vault + auth cascade (OAuth), output normalization, human-in-the-loop interrupts, per-call payments (mock mode by default)
- 7 example agents + agent/bridge templates
- `emerge` CLI (`init` / `run` / `publish`) and the `@emerge.agent` SDK decorator
- Versioned `emerge.yaml` spec with JSON Schema + RFC governance
- `ExecutionObserver` seam — a no-op hook today; the DAN injection point tomorrow

---

## 🔧 v1.2 — Harness (gated on v1 validation)

Reliability work for production-grade orchestration. Does not block launch.

- DAG executor for parallel and dependent step execution
- Output verification and semantic judging
- Retry and fallback policies
- Context manager for long-running multi-step tasks

---

## 🌐 v2 — DAN Alpha (gated on Day-30 adoption signal)

The decentralized agent network begins. **No DAN engineering starts before ≥1 external agent registers in the wild.**

### Phase 0 — Gossip
Gate: ≥1 external agent registered (Day-30)

- [`emerge-node`](docs/dev_docs/dan/phase-0-gossip.md) sidecar + libp2p GossipSub
- Signed agent envelopes using the `did:orcha:agent:*` DID namespace
- Bootstrap node set for peer discovery
- Registry becomes optional

### Phase 1 — Autonomous Loop
Gate: 10+ active agents in the gossip mesh

- [`@autonomous` decorator](docs/dev_docs/dan/phase-1-autonomy.md) extending the existing SDK
- Observe→Think→Act state machine
- `FulfillmentRecorder` wired into the existing `ExecutionObserver` seam
- Hosted fulfillment data layer (optional, opt-in)

---

## 🚀 v3 — DAN (gated on autonomous task reliability)

### Phase 2 — Knowledge
Gate: Autonomous tasks completing with <5% failure rate

- [Local-first vector store](docs/dev_docs/dan/phase-2-knowledge.md) per agent
- Knowledge fragment propagation over GossipSub
- Privacy-first sharing model: opt-in, typed, signed, TTL-bounded

---

## Chain / token layer

Deferred until **all four** criteria hold:

- [ ] The coordinator can no longer be trusted by a large, diverse network
- [ ] Stakes are large enough to demand trustless settlement
- [ ] Third parties demand permissionless entry without coordinator approval
- [ ] The community demands on-chain governance

Until then: USDC + trusted coordinator. We will not announce a token before this gate.

---

Have an opinion on direction? Open a discussion issue or join the community. DAN phase specs are filed as public RFC issues — participation is the point.
