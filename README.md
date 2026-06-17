<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&pause=1000&color=6366F1&center=true&vCenter=true&width=700&lines=Orchestrate+AI+agents+across+any+protocol;One+goal.+Many+agents.+Any+protocol.;Apps+assembled+from+agents.+Not+chat.;The+road+to+DAN+starts+here." alt="Orcha" />

**The open runtime for multi-protocol AI agent orchestration — and the foundation of DAN.**

[![Build](https://github.com/azank1/orcha/actions/workflows/ci.yml/badge.svg)](https://github.com/azank1/orcha/actions)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Discord](https://img.shields.io/badge/community-Discord-5865F2)](https://discord.gg/orcha)

</div>

---

## The problem

AI agents today are islands. MCP servers live here. A2A agents live there. Glue code everywhere.

**This is not a model problem. It's an orchestration, observability, and distribution problem.**

Orcha is the runtime that fixes it: one natural-language goal gets planned, routed, and executed across agents speaking **different** protocols in the same run — with a credential vault, auth cascade, output normalization, and per-call payments (mock mode by default, no wallet needed).

## Register an agent in 4 lines

```python
import emerge

@emerge.agent(name="My Agent", description="What I do")
def handle(task: str) -> str:
    return f"handled: {task}"
```

```bash
emerge run     # serve locally and register with the runtime
```

## Roadmap

| Phase | Status | What it means |
|-------|--------|---------------|
| **v1 — OSS Runtime** | ✅ Now | MCP + A2A + ACP in one run, SDK, CLI, 7 agents |
| **v1.2 — Harness** | 🔧 Next | DAG executor, retry/fallback, semantic judging |
| **v2 — DAN Alpha** | 🌐 Planned | Gossip mesh, `emerge-node`, agents find each other |
| **v3 — DAN** | 🚀 Horizon | Observe→Think→Act, knowledge graph, no central coordinator |
| **DAPN** | 🏗 Building | Apps assembled from agents over the mesh — bespoke dashboard, not a chat answer |

## Where we're going: DAN + DAPN

DAN is a **self-organizing civilization of AI agents** — with communication, memory, economics, reputation, and reproduction. Not a marketplace. Not an API gateway. A civilization.

DAPN is the surface above DAN. Apps assembled from agents discovered over the network, rendered through **[CanvasKit](docs/dev_docs/primitives/canvaskit.md)** — an open declarative UI protocol — so users get a bespoke, persistent finance dashboard instead of a chat answer that evaporates. No token before [four hard gates pass](ROADMAP.md#chain--token-layer).

> **Read the full vision:** [INCEPTION.md](INCEPTION.md) · **[Five Primitives](docs/dev_docs/primitives/README.md)**

## Quickstart

```bash
git clone https://github.com/azank1/orcha && cd orcha
./scripts/run-all.sh        # infra + all services + seed agents
emerge init my-agent && cd my-agent && emerge run
```

Full setup with manual service control: [docs/quickstart.md](docs/quickstart.md) · [docs/join.md](docs/join.md)

## Architecture

```
Goal
 └─► Registry ──► Planning & Discovery ──► SuperAgent
                                               │
                         ┌─────────────────────┼─────────────────────┐
                         ▼                     ▼                     ▼
                   MCP handler           A2A handler           ACP handler
```

<details>
<summary>Service map</summary>

| Service | Port | Role |
|---------|------|------|
| Registry | 8000 | Agent registration + gRPC |
| Planning & Discovery | 8001 | Vector search + LLM planner |
| SuperAgent | 8002 | LangGraph orchestration engine |
| Gateway | 8080 | Auth + BFF + mock payments |
| Frontend | 3000 | React chat UI |

</details>

## Contribute

Three paths — no prior discussion needed for any of them:

| What | Where | Why it matters |
|------|-------|----------------|
| **New bridge** | `templates/your-first-bridge/` | Adds a protocol — highest leverage contribution |
| **New agent** | `agents/` | Grows the fleet, stress-tests the runtime |
| **CanvasKit component** | `frontend/src/components/canvas/` | Earns per-render in every deployed app |
| **DAN spec** | [`docs/dev_docs/dan/`](docs/dev_docs/dan/) | Shape Phase 0–2 via RFC issues |

→ [CONTRIBUTING.md](CONTRIBUTING.md) · [Write a bridge](docs/bridges.md) · [Open a RFC](https://github.com/azank1/orcha/issues/new?labels=rfc)

---

<div align="center">Apache 2.0 · <a href="https://discord.gg/orcha">Discord</a> · <a href="INCEPTION.md">The DAN vision</a></div>
