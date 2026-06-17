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

**No DAN engineering starts before ≥1 external agent registers in the wild.**

### Phase 0 — Gossip
Gate: ≥1 external agent registered (Day-30)

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

## 🏗 DAPN — Decentralized Agentic App Network

**DAN is the substrate. DAPN is the surface.**

Apps are just compositions of agents. A finance tracker is a market data agent + a sync agent + a notification agent + a budget categorization agent, bound together by a manifest, with a UI on top. DAPN assembles that composition on demand, deploys it, and runs it. The user never writes code. The developer who built the market data agent earns every time it syncs a user's portfolio.

This is how SaaS gets replaced — not by building a better SaaS, but by making SaaS unnecessary.

### The Four Planes

| Plane | What | Status |
|-------|------|--------|
| **Plane 1 — Execution** | Request → response; the SuperAgent runtime today | ✅ Built |
| **Plane 2 — Studio** | App Builder: conversational interview → AppManifest → live app | 📐 Planned |
| **Plane 3 — Runtime** | Always-on daemon: OrchFlow triggers agents 24/7 | 📐 Planned |
| **Plane 4 — Consumer** | The rendered app — CanvasKit makes this genuinely excellent | 🔧 Building |

### The Five Primitives

| Primitive | Role | Status |
|-----------|------|--------|
| **[CanvasKit](docs/dev_docs/primitives/canvaskit.md)** | Declarative UI protocol — what makes Plane 4 genuinely good | 🔧 v0.1 |
| **[AgentKey](docs/dev_docs/primitives/agentkey.md)** | Per-action capability tokens — OAuth for autonomous agents | 📐 Spec |
| **[ManifestKit](docs/dev_docs/primitives/manifestkit.md)** | Versioned schemas — AppManifest, AutomationManifest, UIManifest | 📐 Spec |
| **[OrchFlow](docs/dev_docs/primitives/orchflow.md)** | Automation substrate — cron, webhooks, Kafka event consumers | 📐 Spec |
| **[ConnectKit](docs/dev_docs/primitives/connectkit.md)** | Typed integration interface — any API, normalized schema | 📐 Spec |

The primitives are open-source under Apache 2.0 / MIT. If they become the standard, any platform building AI-native apps adopts them. That's the moat: not a closed platform feature — a standard.

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
