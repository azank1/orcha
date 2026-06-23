# Show HN — draft

Internal launch copy. Paste into HN when hero GIF and sandbox URL are ready.

## Title

**Show HN: Orcha – orchestrate MCP/A2A agents into a live dashboard, not a chat reply**

## Body

### Problem

AI agents are islands. MCP tools live in one repo, A2A agents in another, and every product team writes glue code to stitch them together. Worse: the output is almost always **text** — a summary you read once and forget.

### What Orcha does

Orcha is an open-source orchestration runtime. You type one goal; it plans a run, routes to the right agents across **MCP, A2A, ACP, and COMPUTER_USE**, and renders the result as a **CanvasKit dashboard** — metric cards, charts, tables — not a chat bubble.

**Demo goal we use:**

> Show me my portfolio performance, search for NVDA earnings coverage, and screenshot the Alpaca dashboard

In one run you should see: finance dashboard agent (MCP) → search agent (MCP) → mock computer-use screenshot — with a live portfolio dashboard in the UI.

![Demo](../assets/demo-hero.gif)

### How it works

```
Goal → Registry → Planning & Discovery → SuperAgent → protocol handlers → canvas_manifest SSE → React dashboard
```

- **Mock-first:** runs with `PAYMENT_MODE=mock` — no wallet, no closed service required
- **SDK:** `emerge init` + `@emerge.agent` decorator + `emerge run`
- **CanvasKit:** agents emit structured `UIManifest` JSON; the frontend renders curated components

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
