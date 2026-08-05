<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&pause=1000&color=6366F1&center=true&vCenter=true&width=700&lines=Orchestrate+AI+agents+across+any+protocol;One+goal.+Many+agents.+Any+protocol.;Apps+assembled+from+agents.+Not+chat." alt="Orcha" />

**One goal. Many agents. Any protocol.**

*The open-source runtime for multi-protocol AI agent orchestration.*

[![Build](https://github.com/solvent-labs-org/orcha/actions/workflows/ci.yml/badge.svg)](https://github.com/solvent-labs-org/orcha/actions)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/solvent-labs-org/orcha/badge)](https://securityscorecards.dev/viewer/?uri=github.com/solvent-labs-org/orcha)
[![Version](https://img.shields.io/badge/version-0.1.2-blue)](CHANGELOG.md)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)

</div>

---

## The problem

AI agents today are islands. MCP servers live here. A2A agents live there. Glue code everywhere.

Today's "loop engineering" tools handle one agent looping on one task. The harder problem — composing agents that speak **different protocols** into a single verified run with structured output — has no open-source solution.

**This is not a model problem. It's an orchestration, observability, and distribution problem.**

Orcha is the runtime that fixes it: one natural-language goal gets planned, routed, and executed across agents speaking **different** protocols in the same run — with a credential vault, auth cascade, output normalization, and per-call payments (mock mode by default, no wallet needed).

## See it work

Type a goal → Orcha discovers agents → composes MCP, A2A, and COMPUTER_USE in one run → renders a **CanvasKit dashboard**, not a chat reply.

Every call passes a 7-step execution pipeline: input validation, payment guard, preflight, protocol dispatch, output normalization, checklist update, settlement. Each step gets a verdict, and any run can be downloaded as a JSON evidence package (**Verified Runs**): per-step agent, protocol, verdict, cost, and timing.

Output is not a chat bubble. Agents return a declarative **[CanvasKit](docs/spec/canvaskit.md) manifest** and the runtime renders metric cards, charts, tables, and alert feeds as a live dashboard. Structured output persists, and structured output can be checked.

| Chat reply (before) | CanvasKit dashboard (Orcha) |
|---------------------|----------------------------|
| Prose summary you scroll past | Metric cards, charts, tables, alerts — live UI |

**Try it:** run the [hosted sandbox](deploy/sandbox/README.md) locally (`make -f deploy/sandbox/Makefile up`) or clone and `./scripts/run-all.sh`. Demo portfolio data is illustrative — no brokerage connection required.

**Hero goal (3-protocol demo):** *"Show me my portfolio performance, use your web scraper agent to summarize https://en.wikipedia.org/wiki/Nvidia, and screenshot the Alpaca dashboard"* → finance MCP + web-scraper A2A + mock computer-use in one run. Verified live, 5/5 runs, best wall clock 13s.

## Register an agent in 4 lines

> Orcha ships the **`emerge` SDK** for agent registration — `emerge init` scaffolds your agent manifest, `emerge register` publishes it to the runtime. No clone required: `uvx emerge init my-agent`.

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

Just building an agent? Zero clone:

```bash
uvx emerge init my-agent && cd my-agent && uvx emerge run
```

Running the full runtime (registry, planner, orchestrator, dashboard):

```bash
git clone https://github.com/solvent-labs-org/orcha && cd orcha
./scripts/run-all.sh        # infra + all services + seed agents
```

Per-service details live in the [docs](https://metaorcha.ai/docs).

Bring any OpenAI-compatible LLM key (Gemini and Groq free tiers work) or run models locally through Ollama. Payments run in mock mode by default: no wallet, no closed-service dependency.

**Prove it yourself:** `./scripts/poc-e2e.sh` — one script registers a paid agent via the `emerge` SDK, runs a multi-protocol goal, and asserts verification, retry, and settlement end-to-end.

## Architecture

```
Goal
 └─► Registry ──► Planning & Discovery ──► SuperAgent
                                               │
                         ┌─────────────────────┼─────────────────────┐
                         ▼                     ▼                     ▼
                   MCP handler           A2A handler          COMPUTER_USE handler
```

(`protocol.type: "acp"` is still accepted in `emerge.yaml` and routes through
the A2A handler — a compatibility alias, not a fourth independently-bridged
protocol. The `emerge.yaml` schema and its governance rules live in
[docs/spec/](docs/spec/).)

<details>
<summary>Service map</summary>

| Service | Port | Role |
|---------|------|------|
| Registry | 8000 | Agent registration + gRPC |
| Planning & Discovery | 8001 | Vector search + LLM planner |
| SuperAgent | 8002 | LangGraph orchestration engine, protocol dispatch |
| Gateway | 8080 | Auth + BFF + mock payments |
| Frontend | 3000 | React chat + CanvasKit renderer |

</details>

The harness stays neutral ground between agents. Agents remain external, independently running services. Orcha plans, routes, verifies, and renders; it does not embody any single agent.

## Contribute

| What | Where | Why it matters |
|------|-------|----------------|
| **New bridge** | `templates/your-first-bridge/` | Adds a protocol — highest leverage contribution |
| **New agent** | `agents/` | Grows the fleet, stress-tests the runtime |
| **CanvasKit component** | `frontend/src/components/canvas/` | New dashboard primitives for agent output |

→ [CONTRIBUTING.md](CONTRIBUTING.md) · [Write a bridge](templates/your-first-bridge/) · [Open a RFC](https://github.com/solvent-labs-org/orcha/issues/new?labels=rfc)

## What's next

**Sandbox hardening + UIUX (v0.2.0)** — full trajectory in the [roadmap](https://metaorcha.ai/roadmap).

---

<div align="center">Apache 2.0 · <a href="https://metaorcha.ai/roadmap">Roadmap</a></div>
