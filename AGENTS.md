# AGENTS.md

Instructions for AI coding agents (Cursor, Claude Code, Codex, aider, etc.)
working in this repository. Human contributors: see [CONTRIBUTING.md](CONTRIBUTING.md).

- The default branch is `main`. Branch naming: `<type>/<description>`
  (e.g. `feat/sandbox-deploy`, `fix/registry-health`). Never push to
  `main` directly without review.

## Project Overview

Orcha is an open-source multi-protocol AI agent orchestration runtime. Users
submit a free-text goal; Orcha plans and routes it across MCP, A2A, and
COMPUTER_USE protocols (ACP manifests are accepted as a compatibility alias
routed through the A2A handler), executes it in a ReAct orchestration loop,
and renders results as a live dashboard via CanvasKit — not a text reply.
(The 5-stage DAG planner in `services/planning-discovery/` is wired in behind
`DAG_PLANNER_ENABLED` (default off): complex goals route to `/plan` via a
hybrid heuristic+semantic gate and execute as a planned workflow; simple goals
stay on the ReAct loop. CDV step verification is available behind
`CDV_VERIFICATION_ENABLED`.) The full stack runs with
`PAYMENT_MODE=mock` and no closed-service dependency (see OSS Hard Rules below).

Everything in this repo — planner, verifier, protocol handlers, CanvasKit,
SDK — is Apache 2.0 and stays that way. There is no closed "host" binary and
no planned open-core split.

### Service map

| Path | Service | Port | Role |
|---|---|---|---|
| `services/registry/` | Registry | 8000 | Agent registration + gRPC |
| `services/planning-discovery/` | Planning & Discovery | 8001 | Vector search + LLM planner (5-stage DAG) |
| `services/superagent/` | SuperAgent | 8002 | LangGraph orchestration engine, protocol dispatch |
| `services/gateway/` | Gateway | 8080 | Auth + BFF + mock payments |
| `frontend/` | Frontend | 3000 | React chat + CanvasKit UI |
| `sdk/` | `emerge` SDK | — | Agent registration decorator, CLI, A2A server |
| `agents/finance-dashboard-agent/` | Reference agent | 3010 | Canonical CanvasKit-emitting agent, started separately |
| `agents/search-agent/` | Search agent | 3007 | |
| `node/` | `emerge-node` package | — | Ed25519 signed-envelope helpers used by charter + attestation |
| `services/validator/` | Validator | — | `FulfillmentRecorder` observer (attestation reference implementation) |

> **Note:** the charter/AAC crypto (`node/`, `common/charter/`, RFCs 0001-0002)
> and the SuperAgent's default-off `KYA_MODE_ENABLED` policy +
> attestation/enforcement tools are intentional parts of this repo — a
> supervisory layer built on them was extracted to a separate project.

## Common Commands

```bash
make install                # install Python + JS deps (uv / npm)
make prisma-generate
make grpc-generate
./scripts/run-all.sh        # infra + all services + seed agents
make check                  # lint + format + tests, run before every PR
./scripts/poc-e2e.sh        # end-to-end proof: register → run → verify → settle
```

> Port note: the `deploy/sandbox/` Docker stack binds host 8000
> (`sandbox-registry`) and will silently shadow a local Registry — stop it
> before running the stack locally.

## Milestone Context

- **M0 — OSS Launch Gate**: merged on `main`
- **M1 — Hosted Sandbox**: built (`deploy/sandbox/`)
- **M2 — Demo + Launch**: in progress

If a request touches CanvasKit billing, token/staking, or any product name
not in the README, add it to `ROADMAP.md` and stop rather than implementing it.

## Architecture

### Canvas Envelope Contract

Agents that return a rich dashboard output MUST use this exact structure:

```json
{
  "__canvas__": true,
  "summary": "Portfolio dashboard: $142,300 total value across 8 positions.",
  "manifest": {
    "version": "1.0",
    "title": "Portfolio — Demo",
    "layout": "dashboard",
    "components": [
      { "type": "metric_card", "label": "Total Value", "value": "$142,300", "trend": "up" }
    ]
  }
}
```

- `__canvas__` must be boolean `true`; `manifest.version` is the string `"1.0"`
- Component `type` values are snake_case, fields flat (no `props` wrapper)
- `manifest.layout` is one of `dashboard` | `single` | `table` | `timeline`
- Pipeline: agent output → `output_normalizer.py` detects the envelope →
  `execute_agent_calls.py` emits SSE `canvas_manifest` → `runner.py` forwards
  to the Gateway stream. Reference agent: `agents/finance-dashboard-agent/server.py`.

### Protocol Dispatch

Never hard-code a computer-use or protocol backend — use the env-var swap
pattern already in `services/superagent/src/superagent/handlers/`. The
`ExecutionObserver` seam (`services/superagent/src/superagent/middleware/pipeline.py`)
is where post-execution hooks (metrics, the validator's `FulfillmentRecorder`,
etc.) go.
Do not add side effects directly in `execute_agent_calls.py` or `runner.py`.

### emerge.yaml / DID Rules

```yaml
identity:
  id: "did:orcha:agent:my-agent-name"   # user agents
# id: "did:orcha:system:my-tool"        # platform/system tools
```

Never `did:emerge:`, `did:metaorcha:`, or a bare name. The schema
(`docs/spec/emerge-yaml.schema.json`) is versioned; breaking changes need an
RFC in `docs/spec/governance.md` — additive optional fields are fine without one.

## OSS Hard Rules (non-negotiable)

1. **Mock-first**: full stack runs with `PAYMENT_MODE=mock`, no hard dependency
   on a paid/closed/hosted service. Provide a mock fallback for anything external.
2. **Public brand = Orcha only** — never "MetaOrcha" or any internal name in
   any committed file.
3. **No secrets in files** — no API keys, credentials, tokens, or service
   account files. `.env.*` is gitignored except `.env.example` /
   `.env.sandbox.example`. CI runs gitleaks on every PR (`.gitleaks.toml`).
4. **DID namespace is fixed** — see above.
5. **emerge.yaml schema is versioned** — RFC required for breaking changes.
6. **No token announcement** — no tokenomics or launch timelines anywhere.
7. **Closed-service adapters** (if any) are named only in adapter-specific
   internal docs — never in product text, README, public docs, or code comments.

## Do NOT Edit (Generated Files)

- `common/proto/src/*_pb2.py`, `*_pb2_grpc.py`, `*_pb2.pyi` — regenerate via `make grpc-generate`
- `common/database/src/generated_client/` — regenerate via `prisma generate`

## Before Opening a PR

- `make check` passes (lint + format + tests)
- New code has tests; bridges/agents include a minimal example + manifest
- No secrets or client references in the diff
- Public-facing text says **Orcha**, never an internal brand
