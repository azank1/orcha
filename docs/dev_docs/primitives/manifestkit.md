# ManifestKit

**Versioned, validated schemas for AI-native artifacts.**

> "zod for agentic constructs."

The existing `emerge.yaml` is an Agent Manifest — it defines what an agent is, what it can do, and how to call it. ManifestKit is the formalization and extension of that pattern into a full schema library covering every kind of AI-native artifact.

---

## Existing foundation

Agent Manifests already exist and are governed under RFC. The spec lives at `docs/spec/emerge-yaml.schema.json`. What ManifestKit adds:

| Schema | What it describes | Status |
|--------|------------------|--------|
| **AgentManifest** | An individual agent (already `emerge.yaml`) | ✅ Stable (v1.0) |
| **AppManifest** | A composed application — agents + triggers + data sources + UI | 📐 Spec |
| **AutomationManifest** | A set of triggers and conditions that invoke agents | 📐 Spec |
| **UIManifest** | A structured description of an interface (see [CanvasKit](canvaskit.md)) | 🔧 v0.1 |
| **ConnectorManifest** | An integration data source with normalized schema | 📐 Spec |

---

## AppManifest (draft)

An App Manifest is the declarative description of a deployed AI-native application. The Domain Expert agent compiles it from a conversational interview. The runtime provisions infrastructure from it.

```yaml
schema_version: "1.0"
kind: app

identity:
  id: "app:personal-finance-tracker"
  name: "Alex's Finance Tracker"
  owner_did: "did:orcha:user:alex"
  domain: "finance"
  version: "1.0.0"

agents:
  - ref: "did:orcha:agent:market-data-agent"
    role: "data_source"
  - ref: "did:orcha:agent:sync-agent"
    role: "processor"
  - ref: "did:orcha:agent:notification-agent"
    role: "alerter"
  - ref: "did:orcha:agent:finance-domain-expert"
    role: "planner"

data_sources:
  - connector: "plaid"
    scope: ["transactions", "balances"]
  - connector: "alpaca"
    scope: ["positions", "portfolio_value"]
  - connector: "coinbase"
    scope: ["balances"]

automations:
  - id: "daily_sync"
    trigger: { type: "cron", schedule: "0 9 * * *" }
    action: { agent: "did:orcha:agent:sync-agent", task: "sync_all_sources" }
  - id: "drop_alert"
    trigger: { type: "threshold", metric: "portfolio_pct_change", operator: "<", value: -5 }
    action: { agent: "did:orcha:agent:notification-agent", task: "send_alert" }

ui:
  layout: "dashboard"
  primary_view: "portfolio_overview"

billing:
  plan: "app_subscriber"
  base_price_usd: "15.00"
  billing_cycle: "monthly"
```

---

## AutomationManifest (draft)

Emitted by the Studio Plane (Automation Builder); consumed by OrchFlow.

```yaml
schema_version: "1.0"
kind: automation

id: "auto-portfolio-sync"
app_id: "app:personal-finance-tracker"

triggers:
  - type: "cron"
    id: "daily_9am"
    schedule: "0 9 * * *"
    timezone: "America/New_York"
  - type: "webhook"
    id: "alpaca_webhook"
    endpoint: "/webhooks/alpaca/{app_id}"
    hmac_secret_key: "vault:alpaca_webhook_secret"

steps:
  - id: "fetch_positions"
    agent: "did:orcha:agent:market-data-agent"
    task: "get_positions"
    on_error: "retry:3"
  - id: "update_dashboard"
    agent: "did:orcha:agent:sync-agent"
    task: "update_user_portfolio"
    depends_on: ["fetch_positions"]
  - id: "check_alerts"
    agent: "did:orcha:agent:notification-agent"
    task: "evaluate_thresholds"
    depends_on: ["update_dashboard"]
```

---

## Governance

All ManifestKit schemas follow the same RFC governance as `emerge.yaml`:

1. Open an issue with `spec-change` + `manifestkit` labels before sending a PR
2. Draft RFC at `docs/spec/rfcs/NNNN-title.md`
3. Acceptance requires maintainer sign-off
4. Breaking changes increment major version; additions increment minor

The AgentManifest spec (`emerge.yaml`) is the north star: stable, versioned, governed. AppManifest and AutomationManifest follow the same discipline.

---

## Open questions → RFC issues

- [ ] **App versioning:** What happens when an AppManifest is updated? In-place patch or new deployment? How does rollback work?
- [ ] **Agent versioning in apps:** If an app pins `market-data-agent@1.2`, what happens when v1.3 ships? Automatic upgrade, manual approval, or semver range?
- [ ] **Cross-app data sharing:** Can two AppManifests share a ConnectorManifest instance (e.g., two apps reading from the same Plaid connection)? Who owns the credential?
- [ ] **IDE tooling:** ManifestKit should ship VS Code extensions for schema validation and autocomplete. Community opportunity.
