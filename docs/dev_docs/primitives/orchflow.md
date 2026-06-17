# OrchFlow

**The automation substrate for AI-native applications.**

The gap in every agentic platform: "I want to trigger an agent on a schedule" → either hand-roll cron, or buy a full workflow engine. OrchFlow fills the gap between those extremes.

OrchFlow is the engine that makes Plane 3 (Runtime) work. It runs constantly, but cheaply. Agents are NOT running 24/7 — they fire on-demand when OrchFlow triggers them. The cost insight: 10,000 active apps → ~$100/month in compute for the daemon. Agents bill per invocation.

---

## What OrchFlow handles

```
Trigger types:
  ├── cron          → pg_cron schedules (standard cron syntax)
  ├── webhook       → per-app HMAC-signed HTTP endpoints
  ├── event         → Kafka consumer (topic per app domain)
  └── threshold     → metric value crossing a configured boundary

On trigger fire:
  ├── Evaluate conditions (if-then branching in AutomationManifest)
  ├── Dispatch agent invocation (emit task to SuperAgent queue)
  └── Record trigger history (for debugging + audit)
```

---

## Configuration (via AutomationManifest)

OrchFlow is configured entirely via API — no UI required. The Studio Plane emits AutomationManifests; OrchFlow runs them. See [ManifestKit](manifestkit.md) for the AutomationManifest schema.

```yaml
triggers:
  - type: "cron"
    schedule: "0 9 * * *"       # Standard cron syntax; pg_cron executes
    timezone: "America/New_York"

  - type: "webhook"
    endpoint: "/webhooks/alpaca/{app_id}"
    hmac_secret_key: "vault:alpaca_hmac"

  - type: "event"
    topic: "orcha/finance/price_update"   # GossipSub topic (Phase 0+)
    filter: { symbol: "ETH", change_pct: { lt: -5 } }

  - type: "threshold"
    metric: "portfolio_pct_change_24h"
    operator: "<"
    value: -5
```

---

## Community extension points

The highest-leverage community contribution is a new **trigger type**. Each trigger type is a small adapter that normalizes an external event into an OrchFlow signal:

| Trigger type | What fires it | Who builds it |
|-------------|--------------|---------------|
| `cron` | pg_cron schedule | Core (built) |
| `webhook` | HTTP POST to signed endpoint | Core (built) |
| `stripe_payment` | Stripe `payment_intent.succeeded` | Community |
| `github_pr` | GitHub `pull_request.opened` | Community |
| `pagerduty_alert` | PagerDuty alert webhook | Community |
| `slack_message` | Slack event webhook | Community |

Each community trigger earns a **per-trigger-fire fee** when running in deployed apps (80% contributor / 20% platform).

---

## App Runtime daemon

OrchFlow's companion is the App Runtime daemon — a lightweight process (Go) running per active app:

- Watches for trigger events from OrchFlow
- Maintains app state (last sync time, cached metrics, alert thresholds)
- Dispatches agent calls via the SuperAgent queue
- Pushes real-time updates to the client via WebSocket

The daemon is tiny. For 10,000 active apps: ~$0.001/hour per app → ~$100/month total. Agents fire on-demand and bill per-invocation — this is the key cost insight that makes the DAPN economics work.

---

## Open questions → RFC issues

- [ ] **Multi-tenant isolation:** Each app gets its own webhook endpoint namespace. How are shared connectors (e.g., Stripe master account) isolated per tenant?
- [ ] **Trigger ordering guarantees:** If a cron and a threshold fire simultaneously for the same app, what's the ordering? Queue-per-app with FIFO? Or concurrent with conflict detection?
- [ ] **Back-pressure:** If an agent invocation takes longer than the trigger interval, does OrchFlow skip, queue, or signal the app?
- [ ] **State persistence:** The App Runtime daemon needs to persist its last state across restarts. Supabase row? Redis? SQLite sidecar?
