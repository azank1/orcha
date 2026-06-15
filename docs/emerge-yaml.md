# emerge.yaml reference

`emerge.yaml` is an agent's manifest — its identity, how to reach it, how to
authenticate, and what it costs. It is the contract the registry validates and
the planner reads. The SDK generates it for you (`emerge run`), but you can also
write it by hand.

The manifest is **versioned and frozen-by-default**. The canonical schema is
[`docs/spec/emerge-yaml.schema.json`](spec/emerge-yaml.schema.json); changes go
through the [RFC process](spec/governance.md).

## Minimal example

```yaml
schema_version: "1.0"

identity:
  id: "did:orcha:agent:my-agent"      # did:orcha:agent:* (user) | did:orcha:system:* (platform)
  name: "My Agent"
  version: "0.1.0"
  description: "One sentence the planner uses to decide when to route to you."
  tags: ["example"]

protocol:
  type: "a2a"                          # mcp | a2a | acp
  version: "1.0"
  transport:
    type: "http"                       # sse | stdio | http
    endpoint: "http://localhost:8900"

health_endpoint: "http://localhost:8900/health"

security:
  transport_layer:
    type: "none"                       # none | tls | mtls
  auth_strategies: []
```

## Fields

### `schema_version`
String, defaults to `"1.0"` if absent. Tooling treats a missing value as `1.0`.

### `identity`
| Field | Required | Notes |
|---|---|---|
| `id` | ✓ | DID. `did:orcha:agent:<slug>` for user agents, `did:orcha:system:<slug>` for platform tools. |
| `name` | ✓ | Human-readable name. |
| `version` | ✓ | Agent version (semver recommended). |
| `description` | ✓ | One sentence — the planner reads this for routing. |
| `tags` | | Free-form discovery tags. |
| `public_key` | | Optional base64 Ed25519 key for signed identity (emerge/1.1). Unused in mock mode. |

### `protocol`
`type` is `mcp`, `a2a`, or `acp`. `transport.type` is `sse`, `stdio`, or `http`.
- `http`/`sse` require `endpoint`.
- `stdio` requires `command` (and optionally `args`, `env` with `${VAR}` templates).

### `health_endpoint`
URL the registry polls to confirm the agent is alive at registration.

### `security`
`transport_layer.type` is `none`, `tls`, or `mtls`. `auth_strategies` is a list
of `x_api_key` / `http_bearer` / `oauth2` / `oauth2_dcr` strategies; the runtime
resolves credentials from the vault before invoking your agent.

### `payment` (optional)
```yaml
payment:
  enabled: true
  base_fee: "0.15"     # USD per invocation, as a string. Absent/null = free.
```
Metered in **mock mode** by default — no wallet required.

### `skills` (A2A)
Declared capabilities, surfaced on the agent card and harvested by the registry.
Each has `id`, `name`, `description`, `tags`, `examples`. Good descriptions and
examples make the planner route to you correctly.

## Validation

The registry validates on registration. To check locally:

```bash
python -c "import json,sys,yaml; from jsonschema import validate; \
  validate(yaml.safe_load(open('emerge.yaml')), json.load(open('docs/spec/emerge-yaml.schema.json')))"
```
