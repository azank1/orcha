# Orcha Roadmap

> For the full DAN vision — the civilization thesis, five deficiencies, and architecture layers — read [INCEPTION.md](INCEPTION.md).

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

**Phase 0 code ships behind `ORCHA_DAN_EXPERIMENTAL=true`. The gate controls graduation to stable default, not the start of engineering.**

### Phase 0 — Gossip
Gate: ≥1 external agent registered (Day-30) → graduates from `experimental` flag to stable

- [`emerge-node`](docs/dev_docs/dan/phase-0-gossip.md) sidecar + libp2p GossipSub
- Domain topic architecture: `orcha/intents/{domain}`, `orcha/knowledge/{domain}`
- Full `GossipEnvelope` schema: 9 message types, Ed25519 signatures, DID-bound identity
- Mode switching: public gossip → private libp2p Noise stream → public fulfillment signal
- Registry becomes optional

### Phase 1 — Autonomous Loop
Gate: 10+ active agents in the gossip mesh

- [`@autonomous` decorator](docs/dev_docs/dan/phase-1-autonomy.md) extending the existing SDK
- Tiered cognitive loop: rule-based fast path + LLM slow path (economically viable at scale)
- `FulfillmentRecorder` wired into the existing `ExecutionObserver` seam
- `KNOWLEDGE_BROADCAST` + `KNOWLEDGE_REQUEST` message types

---

## 🚀 v3 — DAN (gated on autonomous task reliability)

### Phase 2 — Knowledge
Gate: Autonomous tasks completing with <5% failure rate

- [Local-first vector stores](docs/dev_docs/dan/phase-2-knowledge.md) (LanceDB primary, sqlite-vec for edge)
- Knowledge fragment propagation over GossipSub
- Hypercore/Hyperbee for append-only P2P experience log
- Domain-key encryption for privacy enforcement
- Knowledge contribution scoring → feeds into Phase 3 reputation

### Phase 3 — Hardened Trust Layer
Gate: Network large enough that no single coordinator can be trusted

- [Proof of Fulfillment (PoF) consensus](docs/dev_docs/dan/phase-3-trust.md) — not PoW, not standard PoS; validators selected by fulfillment history
- `SUBMIT_FULFILLMENT` as on-chain transaction — the unit of value creation
- Reputation scores migrated from trusted coordinator to on-chain
- Fork mechanism with exponential stake cost curve
- Native token (testnet first, legal review required)

### Phase 4 — Open Network
Gate: Legal/regulatory review complete; community ready to run infrastructure

- DAN Chain mainnet
- Bootstrap nodes handed to community validators
- Native token mainnet
- `emerge-node` open source release
- Orcha becomes one participant in the network, not the coordinator

---

## Chain / token layer

Deferred until **all four** criteria hold:

- [ ] The coordinator can no longer be trusted by a large, diverse network
- [ ] Stakes are large enough to demand trustless settlement
- [ ] Third parties demand permissionless entry without coordinator approval
- [ ] The community demands on-chain governance

Until then: USDC + trusted coordinator. We will not announce a token before this gate.

---

Have an opinion on direction? Open a discussion issue or join the community. DAN phase specs are open RFC issues — participation is the point.
