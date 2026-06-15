# DAN — Decentralized Agent Network (internal program)

Canonical thesis: [`../EmergeOS-DAN.pdf`](../EmergeOS-DAN.pdf). These markdown files are the **execution plan** derived from that document.

## North star

Orcha is not only a local orchestrator. DAN turns it into a **participatable network** where independent operators host agents, coordinators route work, validators attest execution quality, and consumers pay per call — without a single black-box platform owning discovery or reputation.

v1 OSS (merged to `main`) is **substrate**: Registry, PnD, SuperAgent, Gateway, `emerge` SDK, mock payments, and the `ExecutionObserver` seam. DAN phases build the network layer on top.

## Network roles

| Role | Runs | CLI / entry | Monetization (target) |
|---|---|---|---|
| **Agent operator** | Agent HTTP/MCP server | `emerge run`, `emerge publish` | `payment.base_fee` → operator share |
| **Coordinator** | Registry + PnD + SuperAgent (+ Gateway) | `./scripts/run-all.sh`, `make *-dev` | Coordinator fee slice from `base_fee` |
| **Validator** | Observer node + attestation store | `emerge validate` (D1) | Validator share from `base_fee` |
| **Consumer** | Web UI or CLI session | Frontend / `make chat` | Pays credits (`credits_usd`); mock in OSS |

### Mapping to existing code (v1 substrate)

| Role | Service / module |
|---|---|
| Agent operator | [`sdk/src/emerge/`](../../../sdk/src/emerge/), [`agents/*/emerge.yaml`](../../../agents/) |
| Coordinator | [`services/registry/`](../../../services/registry/), [`services/planning-discovery/`](../../../services/planning-discovery/), [`services/superagent/`](../../../services/superagent/), [`services/gateway/`](../../../services/gateway/) |
| Validator | [`services/superagent/src/superagent/middleware/observers.py`](../../../services/superagent/src/superagent/middleware/observers.py) (seam); spike: [`services/validator/`](../../../services/validator/) |
| Consumer | [`frontend/`](../../../frontend/), Gateway mock credits |
| Payments | [`services/superagent/src/superagent/pricing/`](../../../services/superagent/src/superagent/pricing/), Gateway wallet (hosted rails out of OSS) |
| Gossip (D0) | Spike: [`node/`](../../../node/) (`emerge-node`) |

## Phase map

| Phase | Doc | Goal | Status |
|---|---|---|---|
| **D0** | [D0-gossip.md](D0-gossip.md) | Signed manifests propagate; federated discovery | Spike in `node/` |
| **I** | [INCEPTION.md](INCEPTION.md) | First devs: local → contribute → optional sandbox | Doc |
| **D1** | [D1-validators.md](D1-validators.md) | Validators attest executions; fee split + reputation | Spike in `services/validator/` |
| **D2** | [D2-knowledge.md](D2-knowledge.md) | Cross-node knowledge propagation | Spec only |
| **D3** | [D3-settlement-gates.md](D3-settlement-gates.md) | Chain/token when trustless settlement required | Gates unchanged |

Tracker: [milestones.md](milestones.md). Gap vs v1: [gap-analysis.md](gap-analysis.md). **Phased journey:** [INCEPTION.md](INCEPTION.md) · public entry [join.md](../../join.md).

## Program order

1. v1 substrate on `main` (done)
2. D0 gossip + signed identity
3. D1 validators + mock fee split
4. D2 knowledge (optional parallel)
5. D3 chain only when [D3 gates](D3-settlement-gates.md) pass

Public-facing summary lives in [`VISION.md`](../../../VISION.md) and [`ROADMAP.md`](../../../ROADMAP.md); detailed DAN specs stay in this folder.
