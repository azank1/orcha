<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&pause=1000&color=6366F1&center=true&vCenter=true&width=700&lines=Orchestrate+AI+agents+across+any+protocol;One+goal.+Many+agents.+Any+protocol.;Apps+assembled+from+agents.+Not+chat." alt="Orcha" />

**The open runtime for multi-protocol AI agent orchestration.**

[![Build](https://github.com/azank1/orcha/actions/workflows/ci.yml/badge.svg)](https://github.com/azank1/orcha/actions)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Discord](https://img.shields.io/badge/community-Discord-5865F2)](https://discord.gg/orcha)

</div>

---

![Orcha demo — one goal, CanvasKit dashboard](docs/assets/demo-hero.gif)

## The problem

AI agents today are islands. MCP servers live here. A2A agents live there. Glue code everywhere.

**This is not a model problem. It's an orchestration, observability, and distribution problem.**

Orcha is the runtime that fixes it: one natural-language goal gets planned, routed, and executed across agents speaking **different** protocols in the same run — with a credential vault, auth cascade, output normalization, and per-call payments (mock mode by default, no wallet needed).

## See it work

Type a goal → Orcha discovers agents → composes MCP, A2A, and COMPUTER_USE in one run → renders a **[CanvasKit](docs/dev_docs/primitives/canvaskit.md) dashboard**, not a chat reply.

| Chat reply (before) | CanvasKit dashboard (Orcha) |
|---------------------|----------------------------|
| Prose summary you scroll past | Metric cards, charts, tables, alerts — live UI |

**Try it:** run the [hosted sandbox](deploy/sandbox/README.md) locally (`make -f deploy/sandbox/Makefile up`) or clone and `./scripts/run-all.sh`. Demo portfolio data is illustrative — no brokerage connection required.

**Hero goal (3-protocol demo):** *"Show me my portfolio performance, search for NVDA earnings coverage, and screenshot the Alpaca dashboard"* → finance MCP + search MCP + mock computer-use in one run.

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

## Quickstart

```bash
git clone https://github.com/azank1/orcha && cd orcha
./scripts/run-all.sh        # infra + all services + seed agents
emerge init my-agent && cd my-agent && emerge run
```

Full setup: [docs/quickstart.md](docs/quickstart.md) · [docs/join.md](docs/join.md)

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

| What | Where | Why it matters |
|------|-------|----------------|
| **New bridge** | `templates/your-first-bridge/` | Adds a protocol — highest leverage contribution |
| **New agent** | `agents/` | Grows the fleet, stress-tests the runtime |
| **CanvasKit component** | `frontend/src/components/canvas/` | New dashboard primitives for agent output |

→ [CONTRIBUTING.md](CONTRIBUTING.md) · [Write a bridge](docs/bridges.md) · [Open a RFC](https://github.com/azank1/orcha/issues/new?labels=rfc)

## What's next

**Harness reliability (v1.2)**, then a decentralized agent network (DAN) — full trajectory in [ROADMAP.md](ROADMAP.md). Vision essay: [INCEPTION.md](INCEPTION.md).

---

<div align="center">Apache 2.0 · <a href="https://discord.gg/orcha">Discord</a> · <a href="ROADMAP.md">Roadmap</a></div>
