# DAPN Primitives

**DAN is the substrate. DAPN is the surface.**

Apps are just compositions of agents. A finance tracker is a market data agent + a sync agent + a notification agent + a budget categorization agent, bound together by a manifest, with a UI on top. DAPN assembles that composition on demand, deploys it, and runs it. The user never writes code.

These five open-source primitives are the infrastructure layer of the AI-native application era. Each is independently useful. Together they replace the need for any AI platform to reinvent authentication, UI rendering, automation scheduling, or integration wiring.

---

## The Five Primitives

| Primitive | What it solves | Repo | Status |
|-----------|---------------|------|--------|
| **[CanvasKit](canvaskit.md)** | Declarative UI for AI-native apps — agents emit structured data, not fragile React code | `emergeOS/canvas-kit` | 🔧 v0.1 building |
| **[AgentKey](agentkey.md)** | Per-action capability tokens — OAuth for autonomous agents | `emergeOS/agentkey` | 📐 Spec |
| **[ManifestKit](manifestkit.md)** | Versioned schemas for App, Automation, and UI manifests | `emergeOS/manifest-kit` | 📐 Spec |
| **[OrchFlow](orchflow.md)** | Automation substrate — cron, webhooks, event consumers | `emergeOS/orchflow` | 📐 Spec |
| **[ConnectKit](connectkit.md)** | Typed integration connector interface — any API, normalized schema | `emergeOS/connect-kit` | 📐 Spec |

---

## How they compose

```
User describes app
  ↓
ManifestKit: AppManifest compiled by Domain Expert agent
  ↓
OrchFlow: triggers provisioned (cron, webhook, event)
  ↓
ConnectKit: integrations resolved (Plaid, Alpaca, Coinbase...)
  ↓
AgentKey: per-action tokens issued as agents execute
  ↓
CanvasKit: UIManifest emitted → rendered as real application UI
```

The user sees: a bespoke, persistent finance dashboard that just works. Not a chat answer. Not a generated codebase. An application.

---

## What this is NOT

- Not a model company. We use models; we don't train them.
- Not a workflow builder. OrchFlow is the substrate under a workflow builder.
- Not an API gateway. These are primitives other platforms embed.

The strategic thesis: if these primitives become the standard, any platform building AI-native apps adopts them — including ones that compete with us on other dimensions. That's what it means to own infrastructure.

---

## Contributing

**CanvasKit** is the highest-leverage contribution right now:
- Build a new component: subclass the `CanvasComponent` type in `frontend/src/types/canvas.ts` and add a renderer in `frontend/src/components/canvas/`
- Ship an agent that emits `canvas_manifest` events
- See [canvaskit.md](canvaskit.md) for the full component spec and developer earning model

For AgentKey, ManifestKit, OrchFlow, ConnectKit: specs are open for RFC discussion. File an issue with the `rfc` + `primitives` labels.
