# Orcha — YC W2027 Application Draft

Internal working doc. Fill traction numbers before submitting (~Nov 2026).

---

## Company

**Orcha** — open-source runtime for multi-agent AI orchestration.

---

## One sentence

Orcha is the open infrastructure layer for multi-agent AI loops: any agent, any protocol, one goal-driven run, structured output instead of text.

---

## Problem

Every company is building an "agent stack." But agents speak different protocols — MCP tools here, A2A services there, legacy desktop apps via computer-use. Building a loop that coordinates them produces either chat-bubble text nobody keeps, or a custom glue-code explosion that breaks when any agent changes.

Today's "loop engineering" tools solve the wrong layer: one agent, one protocol, looping on one task. The composition problem — routing across protocol boundaries in a single goal-driven run with verifiable output — has no OSS solution.

**The evidence:** the June 2026 "loop engineering" discourse surfaced this gap explicitly. "In any loop, the verifier is the bottleneck, not the model." The bottleneck isn't single-agent looping; it's multi-agent composition with structured, verifiable output. Nobody ships that today.

---

## Solution

Orcha is the missing layer. A natural-language goal enters; a structured dashboard exits.

**1. 5-stage planning pipeline (Planning & Discovery)**
- Decomposes the goal into a dependency-ordered agent DAG
- Resolves which registered agent handles each step
- Wires I/O schemas so outputs chain into inputs
- Pre-flight verifier checks every agent's health and capability before execution starts
- Produces a `WorkflowManifest` — a checkable, auditable execution plan

**2. Multi-protocol ReAct loop (SuperAgent)**
- Executes the DAG, routing each step to its protocol handler: MCP tool call, A2A service, ACP endpoint, or COMPUTER_USE action
- Hard iteration cap (recursion_limit), user kill-switch, and a pluggable `ExecutionObserver` seam for post-step verification
- LangGraph state machine — no prompt spaghetti

**3. CanvasKit output**
- Agents return `{"__canvas__": true, "manifest": {...}}` — a declarative `UIManifest`
- Runtime renders metric cards, line charts, data tables, alert feeds in the browser
- Structured output that persists, not text that evaporates

**4. Open SDK (`emerge`)**
- `emerge init my-agent` + `@emerge.agent` decorator + `emerge run` — any agent registers in 4 lines
- Works with any Python function; no rewrite required

---

## Why now

1. MCP (Anthropic) and A2A (Google) protocol standards landed in 2025–2026 with real ecosystem adoption. The composition layer is now the unlocked bottleneck.
2. Enterprise agent automation is mainstream. Every Fortune 500 is building an agent stack. The composition + output layer is the infrastructure tax they all pay.
3. The "loop engineering" discourse (June 2026 viral moment) named the gap publicly. Practitioners understand the problem; the OSS solution doesn't exist yet.
4. **Demand is proven, not hypothetical.** Traycer built the plan→orchestrate→verify→ship layer for *coding* agents and reached 100k+ users, 550k+ tasks, bootstrapped to profitability, in ~one quarter (public launch April 2026). That validates the primitive and the appetite. Orcha applies it one layer up — across every protocol, not one vertical.

---

## Market

**Beachhead:** agent platform engineers at companies already using MCP or A2A — the people who hit the composition wall first.

**Expansion:** any enterprise building more than one agent. The orchestration layer is horizontal — finance (portfolio dashboard), legal (document research), engineering (code review loop), customer success (ticket triage) all need the same composition + output substrate.

**Analog:** Kubernetes didn't invent containers; it became the substrate every container deployment runs on. Orcha doesn't invent agents; it becomes the substrate every agent composition runs on.

**TAM framing:** $50B+ enterprise agent automation market. Infrastructure platforms (not apps) capture disproportionate value once they become the standard.

---

## Traction

_(Fill before submission — Nov 2026 target)_

- **GitHub stars:** ___  (target: 500+ by Nov 2026)
- **External agent registrations:** ___ from ___ unique orgs (target: 5+ orgs)
- **Sandbox sessions:** ___ (target: 1,000+)
- **Notable integrations:** ___ (target: 1–2 named MCP servers or A2A agents from outside the team)
- **Show HN:** posted ___, ___ upvotes, ___ comments
- **Discord members:** ___

---

## Why us

- Shipped working multi-protocol composition first — MCP + A2A + ACP + COMPUTER_USE in one loop, in OSS, with a live demo
- CanvasKit is the first open declarative UI protocol for agent output — a new primitive, not a wrapper
- The planning pipeline (pre-flight verified DAG) is the part nobody else has — composition without a plan is just chaos
- The `ExecutionObserver` seam means the verifier layer plugs in without changing the loop — the architecture anticipates the problem the discourse named

---

## Competitive landscape

**Closest comparable — Traycer** (`traycer.ai`). The same architecture (plan → orchestrate → verify → ship, bring-your-own-agent), verticalized to coding agents in the IDE. 100k+ users bootstrapped in a quarter — the best evidence our primitive is real and fundable.

**Why Traycer doesn't eat this space:** its DNA and product are IDE/code-native and assume **homogeneous** agents — every "agent" is a CLI coding tool operating on a repo. Orcha routes across **heterogeneous** protocols (MCP + A2A + ACP + COMPUTER_USE), emits structured non-code output (CanvasKit), and opens a registry any third party publishes to. That's a different runtime they'd have to rebuild, and horizontal-from-coding is a hard pivot into a different buyer and surface. We win where the agents are *different from each other* — which is every enterprise stack.

**The rest of the field:**
- **LangGraph / AutoGen / CrewAI** — single-framework or simulated multi-agent; no real cross-protocol routing, no structured output layer, no open registry.
- **Vertex Agent Builder / Bedrock AgentCore** — cloud-locked to one vendor's agents; Orcha is cloud-agnostic and self-hostable.
- **n8n / Zapier** — human-wired DAGs; Orcha is AI-native goal decomposition with a verifier, not drag-and-drop.
- **The model labs (Anthropic / OpenAI / Google)** — they make the workers; Orcha is the neutral ground *between* their ecosystems, which each is structurally disincentivized to own (a Google runtime routing to Claude is self-defeating).

---

## What we're asking YC for

_(Standard terms)_

**The one thing funding buys that time alone doesn't:** full-time to build the D2 semantic verifier (closes the "verifier bottleneck" critique completely) and drive M3 traction before the Nov deadline. Currently bootstrapped/part-time.

---

## What's not in the pitch (honest)

- The semantic verifier (post-step quality judge) is on the roadmap (D2), not shipped. We claim the architecture and the seam; the semantic judge is hosted-only for now.
- DAN (decentralized agent network) is M4+ — roadmap, not pitched here.
- Token / payment rails are mock-mode in OSS — no onchain settlement in the pitch.

---

## Pre-flight checklist before submitting

- [ ] Fill traction numbers (stars, sessions, orgs, Show HN results)
- [ ] Record 90-second hero clip — `docs/assets/demo-hero.gif` and a video version
- [ ] Link to live sandbox URL (Vercel frontend + stable Cloudflare tunnel)
- [ ] Add 1–2 real external agent registrations (ask Discord / Show HN commenters to try `emerge init`)
- [ ] Confirm D2 semantic verifier is either shipped or scoped with a concrete timeline
