# Roadmap

Direction, not dates. We ship **open substrate first**, then **network participation** — aligned with the [DAN thesis](docs/dev_docs/EmergeOS-DAN.pdf).

**One-line goal:** move from *“run agents on my machine”* to *“participate in a network of orchestrated, observable agents.”*

Public vision summary: [`VISION.md`](VISION.md).

---

## Now — v1 open runtime ✅

Multi-protocol orchestration you can clone and run locally.

| Shipped | Why it matters |
|---|---|
| Registry · PnD · SuperAgent · Gateway | Plan, discover, execute one goal across agents |
| MCP + A2A + ACP in one run | Not a model — **usage** across protocols |
| `emerge` SDK + JSON Schema spec | Every agent is a first-class network citizen (DID, manifest) |
| Mock payments + credential vault | Full flow without wallets |
| `ExecutionObserver` seam | **Observability distribution** starts here — validators plug in without blocking execution |

**Try it:** [`docs/quickstart.md`](docs/quickstart.md)

---

## Next — v1.2 harness (parallel, non-blocking)

Production-grade orchestration reliability — does **not** gate DAN.

- DAG executor · semantic verification · retries · long-context manager

---

## DAN program — orchestration → network

Internal specs: [`docs/dev_docs/dan/`](docs/dev_docs/dan/). Contributor journey: [`docs/join.md`](docs/join.md) · maintainer detail: [`docs/dev_docs/dan/INCEPTION.md`](docs/dev_docs/dan/INCEPTION.md).

### Phase I — Inception *(first external devs)*

Local quickstart first; optional hosted sandbox for allowlisted early adopters.

| Step | Outcome |
|---|---|
| I0 Run locally | Launch gate green on fresh clone |
| I1 First PR | Agent, bridge, or DAN spike merged |
| I2 Sandbox (opt-in) | External agent on shared test network |

Exit I2 → D0 hardening sprint.

### D0 · Network surface *(in progress)*

**Outcome:** Machine B discovers and invokes an agent on Machine A — no manual URL paste.

| Item | Status |
|---|---|
| `emerge-node` gossip sidecar | Spike in [`node/`](node/) (TCP; libp2p GossipSub target) |
| Signed manifest envelopes | Spike in [`node/src/emerge_node/envelope.py`](node/src/emerge_node/envelope.py) |
| Bootstrap peers + federated registry read | Spec in [`docs/dev_docs/dan/D0-gossip.md`](docs/dev_docs/dan/D0-gossip.md) |
| `emerge run --network …` | Planned |

**Not in D0:** chain, token, autonomous agents, semantic judging.

---

### D1 · Validator layer *(spike landed)*

**Outcome:** Third parties run observer nodes; execution quality is attested and rewarded.

| Item | Status |
|---|---|
| `FulfillmentRecorder` reference observer | [`services/validator/`](services/validator/) |
| `execution.step_complete` Kafka fan-out | SuperAgent middleware |
| `emerge validate --once` | Demo CLI |
| Three-way mock fee split | `COORDINATOR_SHARE_BPS` / `VALIDATOR_SHARE_BPS` env |
| `GET /agents/{did}/reputation` | Target |

Trustworthy production attestations require **D0 signed identity**.

---

### D2 · Knowledge propagation

Local-first vector stores + gossip-propagated fragments. Merge with v1.2 semantic judge — one judge system, not two.

Spec: [`docs/dev_docs/dan/D2-knowledge.md`](docs/dev_docs/dan/D2-knowledge.md)

---

### D3 · Trustless settlement *(gated)*

Chain / native token **only when all four hold:**

1. Coordinator cannot be trusted by a large, diverse network  
2. Economic stakes require trustless settlement  
3. Third parties demand permissionless entry  
4. Community demands on-chain governance  

Until then: **USDC + coordinator** (hosted wallet code stays out of OSS). Details: [`docs/dev_docs/dan/D3-settlement-gates.md`](docs/dev_docs/dan/D3-settlement-gates.md)

---

## Network roles

| Role | Run | Today | Target |
|---|---|---|---|
| Agent operator | Agent + `emerge` | Local only | Gossip publish · earn per call |
| Coordinator | Core stack | `run-all.sh` | Federated bootstrap |
| Validator | `emerge validate` | `--once` demo | Live attestation · fee share |
| Consumer | UI / CLI | Mock credits | Reputation-aware routing |

---

## How to help

| Want to… | Start here |
|---|---|
| Run locally | [`docs/quickstart.md`](docs/quickstart.md) |
| Add a protocol | [`docs/bridges.md`](docs/bridges.md) |
| Work on DAN | [`docs/dev_docs/dan/milestones.md`](docs/dev_docs/dan/milestones.md) |
| Propose spec changes | [`docs/spec/governance.md`](docs/spec/governance.md) |

Open a discussion issue if you're unsure where your change fits.
