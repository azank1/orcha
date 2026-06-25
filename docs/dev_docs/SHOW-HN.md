# Show HN — draft

Internal launch copy. Paste into HN when hero GIF and sandbox URL are ready.

## Title

**Show HN: Orcha – open runtime for multi-agent loops: any protocol, verified plan, live dashboard output**

## Body

### Problem

Everyone's building agent loops. The problem is they stop at the single-agent layer: one model, one tool, one protocol. Real enterprise workflows span **MCP tools, A2A services, legacy desktop apps, and cloud APIs** — different protocols that today's loop tools don't compose. And when you do stitch them together, the output is text that evaporates in a chat bubble.

Today's "loop engineering" tools handle one agent looping on one task. The harder problem — composing agents that speak different protocols into a single **verified**, goal-driven run with structured output — has no open-source solution.

### What Orcha does

Orcha is the open-source runtime that fills that gap. You type one goal; a **5-stage planning pipeline** decomposes it into a dependency-ordered agent DAG and pre-flight-verifies every step before execution starts. Then a **ReAct loop** routes each step to its protocol handler — **MCP, A2A, ACP, COMPUTER_USE** — and renders the result as a **CanvasKit dashboard** (metric cards, charts, tables), not a chat bubble.

**Demo goal we use:**

> Show me my portfolio performance, search for NVDA earnings coverage, and screenshot the Alpaca dashboard

In one run you should see: finance dashboard agent (MCP) → search agent (MCP) → mock computer-use screenshot — with a live portfolio dashboard in the UI.

![Demo](../assets/demo-hero.gif)

### How it works

```
Goal → Registry → Planning & Discovery (5-stage DAG) → SuperAgent ReAct loop
         ↓ pre-flight plan verifier                        ↓ protocol handlers
                                              MCP | A2A | ACP | COMPUTER_USE
                                                        ↓
                                         canvas_manifest SSE → CanvasKit dashboard
```

- **Mock-first:** runs with `PAYMENT_MODE=mock` — no wallet, no closed service required
- **Planning:** 5-stage DAG — decompose → resolve agents → wire I/O → refine deps → validate. Pre-flight verifier checks agent health before execution.
- **SDK:** `emerge init` + `@emerge.agent` decorator + `emerge run` — any agent registers in 4 lines
- **CanvasKit:** agents emit structured `UIManifest` JSON; the frontend renders curated components — not text

### Try it

```bash
git clone https://github.com/azank1/orcha && cd orcha
./scripts/run-all.sh
# open http://localhost:3000 — or use the hosted sandbox (see deploy/sandbox/README.md)
```

**Live sandbox:** _(pin your public URL here before posting)_

### What we're NOT claiming

- Portfolio numbers in the demo are **sample data** — no brokerage connection in the OSS sandbox
- DAN / gossip / token are **roadmap**, not shipped — see [ROADMAP.md](../../ROADMAP.md)

### Ask

- Feedback on the **CanvasKit** manifest schema ([spec](primitives/canvaskit.md))
- Bridge and agent contributions — `templates/your-first-bridge/`, `agents/`
- Would you run this for a real workflow? What agent would you register first?

---

## Pre-flight checklist

- [ ] Hero GIF embedded in README (`docs/assets/demo-hero.gif`, &lt;5MB)
- [ ] `GATEWAY_URL=http://localhost/api ./scripts/m0-gates-live.sh` passes
- [ ] `M2_RUNS=5 M2_PASS=4 GATEWAY_URL=http://localhost/api ./scripts/m2-gates-live.sh` passes
- [ ] OpenRouter credits topped up
- [ ] Public sandbox URL stable (Cloudflare or named tunnel)
- [ ] Discord cross-post ready
