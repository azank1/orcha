<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&pause=1000&color=6366F1&center=true&vCenter=true&width=700&lines=Orchestrate+AI+agents+across+any+protocol;One+goal.+Many+agents.+Any+protocol.;Apps+assembled+from+agents.+Not+chat." alt="Orcha" />

**One goal. Many agents. Any protocol.**

*The open source agent harness. One goal planned, routed, and verified across agents that speak different protocols.*

[![Build](https://github.com/solvent-metaorcha/orcha/actions/workflows/ci.yml/badge.svg)](https://github.com/solvent-metaorcha/orcha/actions)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/solvent-metaorcha/orcha/badge)](https://securityscorecards.dev/viewer/?uri=github.com/solvent-metaorcha/orcha)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Discord](https://img.shields.io/badge/community-Discord-5865F2)](https://discord.gg/orcha)

</div>

---

![Orcha demo: one goal, CanvasKit dashboard](docs/assets/demo-hero.gif)

## The problem

AI agents today are islands. MCP servers live here. A2A agents live there. Legacy software with no API gets driven through computer use.

MCP and A2A standardize how a message gets from A to B. They say nothing about how a dozen independently running agents get planned into one goal, called in the right order, authenticated, verified, and rendered. That missing layer is an **agent harness**, and that is what Orcha is. MCP and A2A are just the first two bridges.

Calling Orcha "an orchestrator of MCP and A2A agents" is like calling Kubernetes a Docker runner. Technically true, categorically wrong.

## What a run looks like

Type a goal. The planner decomposes it into a DAG. Discovery matches each step to a registered agent through vector search. The SuperAgent dispatches every call through its protocol handler: MCP, A2A, ACP (accepted and routed as A2A), or COMPUTER_USE.

Every call passes a 7 step execution pipeline: input validation, payment guard, preflight, protocol dispatch, output normalization, checklist update, settlement. Each step gets a verdict, and any run can be downloaded as a JSON evidence package (**Verified Runs**): per step agent, protocol, verdict, cost, and timing.

**Hero goal, 3 protocols in one run:** *"Show me my portfolio performance, use your web scraper agent to summarize https://en.wikipedia.org/wiki/Nvidia, and screenshot the dashboard"* → finance MCP + web scraper A2A + mock computer use. Verified live, 5/5 runs, best wall clock 13s.

Output is not a chat bubble. Agents return a declarative **[CanvasKit](docs/spec/canvaskit.md) manifest** and the runtime renders metric cards, charts, tables, and alert feeds as a live dashboard. Structured output persists, and structured output can be checked.

## Register an agent in 4 lines

> Orcha ships the **`emerge` SDK** for agent registration. `emerge init` scaffolds your agent manifest, `emerge run` serves it and registers it with the runtime. No clone required: `uvx emerge init my-agent`.

```python
import emerge

@emerge.agent(name="My Agent", description="What I do")
def handle(task: str) -> str:
    return f"handled: {task}"
```

```bash
emerge run     # serve locally and register with the runtime
```

Agents are described by a versioned, JSON Schema validated `emerge.yaml` manifest, governed through RFCs. Version 1.1 (RFC 0001) adds `authorized_scope`: agents declare what they are *allowed* to do, not just what they can do.

## Quickstart

Just building an agent? Zero clone:

```bash
uvx emerge init my-agent && cd my-agent && uvx emerge run
```

Running the full harness (registry, planner, orchestrator, dashboard):

```bash
git clone https://github.com/solvent-metaorcha/orcha && cd orcha
./scripts/run-all.sh        # infra + all services + seed agents
```

Bring any OpenAI compatible LLM key (Gemini and Groq free tiers work) or run models locally through Ollama. Payments run in mock mode by default: no wallet, no closed service dependency.

Full setup: [docs/quickstart.md](docs/quickstart.md) · [docs/join.md](docs/join.md)

**Prove it yourself:** `./scripts/poc-e2e.sh` registers a paid agent via the SDK, runs a goal across protocols, and asserts verification, retry, and settlement end to end. Details: [docs/poc.md](docs/poc.md)

## Architecture

```
Goal
 └─► Registry ──► Planning & Discovery ──► SuperAgent
                                               │
                         ┌─────────────────────┼─────────────────────┐
                         ▼                     ▼                     ▼
                   MCP handler           A2A handler          COMPUTER_USE handler
```

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
| **New bridge** | `templates/your-first-bridge/` | Adds a protocol. Highest leverage contribution |
| **New agent** | `agents/` | Grows the fleet, stress tests the harness |
| **CanvasKit component** | `frontend/src/components/canvas/` | New dashboard primitives for agent output |

→ [CONTRIBUTING.md](CONTRIBUTING.md) · [Write a bridge](docs/bridges.md) · [Open a RFC](https://github.com/solvent-metaorcha/orcha/issues/new?labels=rfc)

## What's next

**Harness reliability (v1.2):** DAG executor for parallel and dependent steps, output verification with semantic judging, retry and fallback policies, context management for long running tasks. Full trajectory in [ROADMAP.md](ROADMAP.md).

---

<div align="center">Apache 2.0 · <a href="https://discord.gg/orcha">Discord</a> · <a href="ROADMAP.md">Roadmap</a></div>
