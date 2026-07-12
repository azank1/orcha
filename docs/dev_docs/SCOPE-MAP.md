# Orcha — Technical Milestone & Dev Spec

## Context

Anthropic's Claude Managed Agents commoditized the agent-ops layer. Value moved up to multi-protocol composition + UI. Wedge: CanvasKit (open UI protocol Anthropic can't ship) + open computer-use bridge (own the interface, not a wrapper). YC target: Winter 2027 batch (~Nov 2026), after 4 months of OSS traction.

**One problem, frozen:** Agents can't work together. Orcha makes any agent — MCP, A2A, or a legacy app with no API — composable in one run, result rendered as a live dashboard.

**Branch convention:** `az/<type>/<description>` — e.g. `az/feat/sandbox-deploy`, `az/dan/phase-0-gossip`

---

## Milestone Overview

| ID | Name | Gate | Status |
|----|------|------|--------|
| M0 | OSS Launch Gate | e2e verified, merged to main | ✅ Merged + live-verified locally — push to origin pending |
| M1 | Hosted Sandbox | public URL live, spend cap set | ✅ Built (deploy pending) |
| M2 | Demo + Launch | hero clip recorded, Show HN live | 🔧 In progress |
| M3 | Traction Window | 4-month OSS compounding | ⬜ Watch |
| M4 | DAN Phase 0 — Gossip | ≥1 external agent Day-30 | 🌐 Planned |
| M5 | DAN Phase 1 — Autonomy | ≥10 agents in mesh | 🌐 Planned |
| M6 | DAN Phase 2 — Knowledge | <5% autonomous task failure | 🚀 Horizon |
| M7 | DAN Phase 3 — Trust | network demands trustlessness | 🚀 Horizon |

---

## M0 — OSS Launch Gate

**Branch:** merged via `az/beta/v1-playable` cherry-picks + `az/feat/sandbox-deploy` integration into `main`

**Verification log:** [M0-VERIFICATION.md](M0-VERIFICATION.md). **Canonical paths on `main`:** `docs/dev_docs/{SCOPE-MAP,M0-VERIFICATION,M2-DEMO}.md` (not `oss-launch/` — that layout is only on `az/feat/sandbox-deploy`).

**Full-system proof:** [POC.md](POC.md) — `./scripts/poc-e2e.sh` asserts the entire loop (SDK registration → discovery → multi-protocol goal → verification → retry → settlement → metrics) across real service boundaries in one stage-gated run.

**Built (all committed, pushed):**
- CanvasKit v0.1 — 8 components, UIManifest types, full SSE pipeline frontend↔backend
- Finance dashboard agent — port 3010, `get_portfolio_dashboard`, returns canvas envelope
- `canvas_manifest` SSE wiring — `OutputNormalizer._detect_canvas_envelope()` → `execute_agent_calls` emit → `runner.py` parse + pending-events replay
- Open computer-use bridge — `ComputerUseHandler`, `MockComputerUseBackend`, `COMPUTER_USE_BACKEND` env var swap
- DAN/DAPN docs — `docs/dev_docs/dan/`, `docs/dev_docs/primitives/`, updated README/ROADMAP

**Verification gate (all must pass before calling M0 done and pushing to `origin/main`):**

| # | Gate | Owner sign-off |
|---|------|----------------|
| 1 | `scripts/run-all.sh` starts clean, all services healthy | ⬜ |
| 2 | Register `agents/finance-dashboard-agent/` with registry | ⬜ (auto via `seed-live-agents.sh` after stack up) |
| 3 | POST a goal that routes to finance-dashboard-agent | ⬜ |
| 4 | `canvas_manifest` SSE event in browser DevTools (Network → EventStream) | ⬜ |
| 5 | CanvasKit dashboard renders: MetricCard + LineChart + DataTable + AlertFeed | ⬜ |
| 6 | `git grep __canvas__` returns only intended runtime files | ✅ |
| 7 | Stack runs with `PAYMENT_MODE=mock` (LLM keys still required for inference) | ⬜ |

**Automated gates 1, 2, 6, 7:** `./scripts/m0-verify.sh` (with stack running). Gates 3–5 remain manual (browser).

**Quick path (local dev):** `./scripts/run-all.sh` → `./scripts/m0-verify.sh` → goal: *"Show me my portfolio dashboard"* → DevTools `canvas_manifest`.

**Sandbox path (M1 stack):** `make -f deploy/sandbox/Makefile up` + `make seed` — same gates 3–5 apply.

Gates 6–7 and all built code are on `main` (local). **Not yet on `origin/main`** until gates 1–5 pass and you push.

---

## M1 — Hosted Sandbox

**Branch:** `az/feat/sandbox-deploy` (merged to `main`)

**Deploy guide:** [deploy/sandbox/README.md](../../deploy/sandbox/README.md)

**Guest auth:** `GET /auth/guest` when `SANDBOX_MODE=true` — one message per guest (`SANDBOX_GUEST_MAX_MESSAGES`, default 1).

**Owner action before public URL:** set `SANDBOX_MAX_DAILY_MESSAGES` in `.env.sandbox` (default 500 ≈ $50/day). Terminate TLS via Cloudflare/Caddy (see deploy README).

**Goal:** Public URL, no signup wall on first interaction. Type a goal → see multi-protocol composition → CanvasKit dashboard. Under 5 min, zero install.

**Technical requirements:**

| Requirement | Implementation |
|------------|---------------|
| No-auth first session | `GET /auth/guest` → guest JWT; frontend auto-bootstrap when `VITE_SANDBOX_MODE=true` |
| LLM spend cap | `SANDBOX_MAX_DAILY_MESSAGES` (message proxy for daily spend) + `SANDBOX_GUEST_MAX_MESSAGES` per guest |
| Rate limiting | 10 req/min per IP on `/api/` routes |
| Secret isolation | No keys in public container env; mounted secret store only |
| Pre-seeded agents | All 7 existing agents + finance-dashboard-agent at boot |
| One-command deploy | Wraps `scripts/run-all.sh`; adds reverse proxy + TLS |

**Services:** Registry (8000) · PnD (8001) · SuperAgent (8002) · Gateway (8080) · Frontend (3000) · PostgreSQL · Redis · Kafka · Ollama (nomic-embed-text) · finance-dashboard-agent (3010) + 6 existing agents

**Files to create:**
- `deploy/sandbox/docker-compose.sandbox.yml`
- `deploy/sandbox/nginx.conf` — rate limits, TLS, no-auth session header
- `deploy/sandbox/Makefile` — `make up` / `make down` / `make logs`
- `.env.sandbox.example` — all required vars documented

**Owner decision required before build:** What is `$___/day` hard cap? A front-page HN day with open no-auth sandbox and no cap = financial incident.

---

## M2 — Demo + Launch Assets

**Branch:** `az/feat/launch-assets`

**Pre-requisite:** Script and validate the demo goal across 5 test runs before recording. ReAct planner is non-deterministic — must hit all 3 protocols in ≥4/5 runs.

**Canonical goal:** `"Show me my portfolio performance, use your web scraper agent to summarize https://en.wikipedia.org/wiki/Nvidia, and screenshot the Alpaca dashboard"` → MCP (finance-dashboard-agent) + A2A (web-scraper) + COMPUTER_USE (mock screenshot) — see `scripts/m2-demo-goal.txt`.

**Hero demo must show:**
- One goal typed → agent discovery + routing visible in progress stream
- 3-protocol composition in one run — genuinely MCP + A2A + COMPUTER_USE, verified via `scripts/m2-gates-live.sh`
- CanvasKit dashboard rendering (not a text reply)
- Wall clock < 30 seconds

**Launch checklist:**
- [ ] Hero GIF/MP4 captured and compressed (<5MB for README embed)
- [ ] `README.md` hero section updated
- [ ] Show HN post drafted: problem → demo → `emerge init` CTA
- [ ] One-screen landing pointing to sandbox URL
- [ ] Discord announced

**README rule:** Above-the-fold = *working multi-protocol orchestration runtime*. DAPN in ROADMAP section only.

---

## M3 — Traction Window (~Nov 2026)

**Not a build milestone — a measurement milestone.**

**Weekly traction gates:**

| Signal | Target for YC W2027 app | Baseline (2026-07-12, pre-launch) |
|--------|------------------------|-----------------------------------|
| GitHub stars | 500+ (spike + sustained) | 0 |
| External agent registrations | 5+ unique orgs | 0 |
| Bridge PRs from strangers | 3+ merged | 0 |
| Sandbox sessions | 1,000+ unique | 0 (no public URL live yet) |
| Discord members | 50+ | not checked — see Discord invite link in README |

The M3 window begins once the Show HN post goes live (blocked on: re-recorded
hero clip, and the hosting decision — both owner actions, see
`docs/dev_docs/SHOW-HN.md` pre-flight checklist). Until then this table is a
baseline for comparison, not yet a measurement in progress.

**YC W2027 application narrative (written from real M3 numbers):**
- Problem: agents can't compose across protocols; output evaporates in chat
- Why now: Claude Managed Agents commoditized ops; value moved to composition + UI; Anthropic structurally won't own the open UI layer
- Wedge: CanvasKit (open component marketplace) + open computer-use bridge
- Traction: [M3 numbers]
- Why us: shipped working multi-protocol runtime; "legacy app as bridge" insight

**Optional early shot:** Fall 2026 batch, deadline ~Jul 27. Low-cost attempt if traction materializes fast. Winter 2027 is primary.

---

## M4 — DAN Phase 0: Gossip

**Gate:** ≥1 external agent registered in the wild (Day-30 from OSS launch)
**Activation:** Ships behind `ORCHA_DAN_EXPERIMENTAL=true`; gate graduation removes flag
**Branch:** `az/dan/phase-0-gossip`

**Core deliverable:** `emerge-node` sidecar — wraps any existing agent without rewriting

**Stack:** libp2p + GossipSub · Ed25519 identity · Noise protocol (1:1 encrypted channels)

**Topic routing:**
```
orcha/intents/{domain}   — 7 domains: sales, engineering, finance, legal, research, infrastructure, creative
orcha/knowledge/{domain}
orcha/heartbeat
orcha/network
```

**9 GossipEnvelope message types:**
```
INTENT_BROADCAST     — agent advertising a need (budget, deadline, domain)
CAPABILITY_OFFER     — fulfillment offer (manifest, ask_usdc, eta)
DELEGATION_ACCEPT    — task assignment confirmed
RESULT_DELIVERY      — fulfillment output
KNOWLEDGE_BROADCAST  — summary + embedding hint only (never full content)
KNOWLEDGE_REQUEST    — on-demand full content fetch
FULFILLMENT_SIGNAL   — reputation receipt (requester-signed)
HEARTBEAT            — health + metrics
FORK_ANNOUNCE        — child agent registration
```

**GossipEnvelope schema:**
```ts
{ version: "1.0", type: MessageType, sender_did: string,
  timestamp: ms, ttl: seconds, nonce: uuid, signature: Ed25519Sig, payload: object }
```

**emerge.yaml extension:**
```yaml
network:
  enabled: true
  experimental: true
  gossip:
    bootstrap_peers: []
    subscribed_domains: ["finance"]
    announce_capabilities: true
  cognitive_loop:
    enabled: false   # Phase 1 only
```

**Anti-spam:** max 10 `INTENT_BROADCAST`/min per DID · unregistered DIDs rejected · GossipSub dedup + TTL

**Open RFCs (block Phase 0):**
- Ed25519 keypair storage location
- Bootstrap node ops + community transition
- Peer table persistence: SQLite vs in-memory
- Rate limit granularity: per DID, IP, or staked identity

---

## M5 — DAN Phase 1: Autonomous Loop

**Gate:** ≥10 active agents in gossip mesh
**Branch:** `az/dan/phase-1-autonomy`

**Core insight:** 10K agents × LLM every 2min = $7,200/day. Solution: tiered loop — rule-based fast path ($0) + LLM slow path (on signal only).

**SDK addition:** `@autonomous` decorator (additive to `@emerge.agent`)

```python
@autonomous(cycle_seconds=120, max_self_tasks_per_hour=5)
def think(state: AgentState, network: NetworkContext) -> Action:
    return Action.RESPOND_TO_BEST_INTENT
```

**Action types:** `REQUEST_SELF_IMPROVEMENT | RESPOND_TO_BEST_INTENT | OBSERVE_AND_WAIT`

**Observe → Think → Act:**
1. Fast-path signal (gossip anomaly, metric threshold, heartbeat delta)
2. Observe: network state + own metrics + knowledge store
3. Think: rule-based OR LLM (only on signal)
4. Act: peer invocation / `INTENT_BROADCAST` / knowledge update
5. Record: `FulfillmentRecorder` via existing `ExecutionObserver` seam in `services/superagent/`

**emerge.yaml extension:**
```yaml
network:
  cognitive_loop:
    enabled: true
    cycle_seconds: 120
    max_self_tasks_per_hour: 5
    objectives:
      - "Maintain top-10 rank in finance domain"
```

**Open RFCs:** trigger taxonomy · constraint enforcement · recursion limits on autonomous chains · emergency human-interrupt path

---

## M6 — DAN Phase 2: Knowledge

**Gate:** Autonomous tasks completing with <5% failure rate
**Branch:** `az/dan/phase-2-knowledge`

**Model:** Local-first, gossip-propagated. No global graph (doesn't fit in context, write bottleneck, privacy risk, garbage-collection unsolved).

**Storage stack:**
| Layer | Backend | Role |
|-------|---------|------|
| Primary | LanceDB | Vector + scalar combined |
| Edge fallback | sqlite-vec | Lightweight, zero deps |
| Experience log | Hypercore/Hyperbee | Append-only P2P stream |
| Direct fetch | libp2p Streams | Encrypted full-fragment delivery |

**Knowledge fragment schema:**
```json
{ "id": "uuid", "content": "...", "summary": "one-line",
  "domain": "finance", "source": "experience|received|synthesized",
  "source_did": "did:orcha:agent:xyz", "embedding": [...],
  "visibility": "public|domain|private", "expires_at": ms }
```

**Propagation:** Learn → store locally → broadcast summary + embedding hint → peers pull full content on-demand via libp2p stream → high-demand fragments get content hash → anchored on-chain in M7.

**Privacy:** domain-private fragments encrypted with rotating domain key. Agents opt-in to sharing. PII excluded via `exclude_subjects` in emerge.yaml.

**Contribution scoring → Phase 3 reputation:** broadcast count × peer fetch count × consumer performance delta (correlated via `FULFILLMENT_SIGNAL`).

**Open RFCs:** storage default · conflict resolution · fragment versioning/retract · PII scrubber responsibility

---

## M7 — DAN Phase 3: Trust Layer

**Gate:** Network large enough that no single coordinator can be trusted by all participants
**Branch:** `az/dan/phase-3-trust`

**Consensus: Proof of Fulfillment (PoF)** — validators selected by proven economic productivity, not compute waste or stake size.

```
Fulfillment_Score(agent) = Σ(rating_i × value_i) / total_tasks_i
Top N by score → validators per epoch
N = 21 initially (BFT majority), grows with network
Epoch = 1,000 blocks | Block target ~400ms
Block finality: Tendermint BFT (2/3+ attestations → instant)
```

**Critical constraint:** LLMs are non-deterministic. LLM reasoning = off-chain. Only results (fulfillment receipt, knowledge hash) go on-chain.

**On-chain state (tamper-critical only):**
```
AgentRegistry:      did, owner_pubkey, capability_hash, reputation_score, stake_balance, fork_depth
FulfillmentAnchors: task_hash, result_hash, rating (1-5), requester_sig
DomainLeaderboard:  top_agents[100] per domain, per epoch
```

**11 transaction types:**
```
REGISTER_AGENT  UPDATE_CAPABILITIES  ANCHOR_KNOWLEDGE
SUBMIT_FULFILLMENT  (the unit of value creation — fires on every completed task)
SIGNAL_REPUTATION  SLASH_AGENT  FORK_AGENT
STAKE  UNSTAKE  WITHDRAW_EARNINGS  GOVERNANCE_VOTE
```

**Payment distribution ($10 task):**
```
70% → developer wallet    ($7.00)
20% → agent stake account ($2.00)
10% → network fee         ($1.00)
```

**Slashing:**
```
Double-signing              → 50% slash
Liveness failure (>10% down) → 10% slash
Fraudulent fulfillment       → 100% slash + ban
```

**Fork (agent reproduction)** — exponential stake curve:
```
depth 0→1:   100 tokens
depth 1→2:   1,000 tokens
depth 2→3:   10,000 tokens
```

**Token launch:** deferred until all 4 gates pass (ROADMAP.md). Options: (a) USDC only, (b) points → token later, (c) direct utility token post-legal review. No announcement before gates.

**Open RFCs:** token strategy · bootstrap node transition · cross-protocol identity for non-DAN agents · knowledge anchoring reward calibration

---

## Discipline Rules

- Beta = one thing: goal → 3-protocol composition → CanvasKit dashboard. Dilute it and both audiences are lost.
- No closed-service hard dependency in OSS core. Computer-use defaults to mock; `COMPUTER_USE_BACKEND` for real adapters.
- CanvasKit earning model = roadmap, marked future in docs. Not active billing.
- Public text = Orcha. No internal brand names in repo or launch copy.
- DAPN/DAN lives in ROADMAP. Above-the-fold README = working runtime.
- Every "what about X?" (Studio, OrchFlow, billing, network) → ROADMAP, not beta.