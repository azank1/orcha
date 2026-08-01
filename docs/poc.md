# Orcha System PoC — end-to-end foundational-operation proof

> **One command:** `./scripts/poc-e2e.sh` against a running sandbox stack.
> If it prints `POC: PROVEN`, every public claim below was just verified live
> on your machine — not in a mocked test, not in a recording.

## Why this exists

The demo GIF shows the *idea*. This harness proves the *machine*. Before it,
every e2e test mocked the service boundary and every gate script was a
substring check on the SSE text — five core claims had **no automated proof**:

1. Devs build agents with the `emerge` SDK and register them (dev end)
2. A goal composes those agents across protocols in one run (consumer end)
3. Every step's output is verified — and retried on transient failure
4. Paid invocations settle: the developer gets paid (mock ledger)
5. Every execution feeds the behavioral metrics the learning layer trains on

The harness exercises all five across **real service boundaries** — gateway →
superagent → planning-discovery → registry → a live agent process — with no
mocks in the path.

## The loop being proven

```
dev machine                          sandbox stack (docker)
───────────                          ─────────────────────────────────────────
emerge SDK                            Registry ── Payment row (base_fee)
  @emerge.agent ──register──────────▶   │
  A2A server (host-side)              PnD ─── embeddings ─── hybrid search
        ▲                               │
        │ invoke (paid A2A)           SuperAgent ReAct loop
        └───────────────────────────    ├─ PaymentGuard (soft reserve)
              503 on 1st call?          ├─ protocol handler (MCP | A2A)
              → invocation_retry        ├─ StructuralVerifier (verified/reason)
              → re-run → ✓              ├─ retry-gate (v1.3, transient only)
                                        ├─ emit SSE (invocation_*, canvas_manifest)
                                        └─ settle_invocation
                                             ├─ Transaction row (80/20 split)
                                             └─ Agent.execution_count / success_rate
                                      Gateway ── SSE relay ── wallet/transactions
```

## Stage map — claim → assertion → code path

| # | Stage | Claim proven | Assertion | Code path exercised |
|---|-------|--------------|-----------|---------------------|
| 1 | Infra | Stack runs, mock mode | `/health` × 4 services; `PAYMENT_MODE=mock` in env | compose stack |
| 2 | SDK registration | "Register an agent in 4 lines" | `emerge publish` (SDK client, **not** curl) succeeds; DID listed by registry; PnD embeddings processed | `sdk/src/emerge/{cli,client,manifest}.py` → `registry/services/registration.py` (incl. `_create_payment`) → `PnD /api/v1/manifests/process` |
| 3 | Discovery | Agents are found semantically | `POST /api/v1/candidates` returns `poc-probe` for a matching goal | PnD hybrid search (GIN + FTS + HNSW + RRF + cross-encoder) |
| 4 | Goal run | Multi-protocol composition | One goal → `invocation_start`+`invocation_result` for **both** finance-dashboard (MCP, free) and poc-probe (A2A, paid); result carries `PROBE-REPORT` | gateway auth/session/SSE → superagent orchestrator → `execute_agent_calls` → MCP + A2A handlers |
| 5 | Verifier | "Verified plan / verified output" | Every external `invocation_result` has `verified: true` + `verdict_reason`; `canvas_manifest` carries all 4 component families | `pipeline.py::_structural_verify` (step 5.5) → SSE fields |
| 6 | Retry-gate | "Goal achieved or retried" | Probe restarted flaky (1st `message/send` → HTTP 503) → `invocation_retry` event → final result `verified: true` | `httpx raise_for_status` → `_classify_stream_error` (transient) → `_execute_with_retry` (v1.3) |
| 7 | Settlement | "Devs monetize agents" | `GET /wallet/transactions` shows a row for poc-probe with `developer_payout > 0`, `platform_cut > 0`, payout+cut = base_fee | `pricing/guard.py` (soft reserve) → `pricing/settlement.py` → `Transaction` table → gateway wallet route |
| 8 | Metrics | Learning layer is being fed | Registry agent row shows `execution_count ≥ 1` (+ updated `success_rate`) | `settlement.py` → `Agent` metrics — the exact data the D2 judge/GNN will train on |
| 9 | Summary | — | All stages green → `POC: PROVEN`, exit 0 | — |

## What is REAL vs what is MOCK

**Real (no simulation):** SDK registration round-trip, PnD semantic discovery,
LLM planning + routing, protocol handlers over live HTTP, structural
verification, the transient retry-gate, SSE streaming, all database writes
(Payment, Transaction, AgentInvocation, agent metrics).

**Mock (by design, OSS launch scope):** the payment *ledger* (`PAYMENT_MODE=mock`
— credits, no on-chain settlement; the split math and DB rows are real),
computer-use backend (`MockComputerUseBackend`), the ephemeral harness user.
The semantic LLM judge and learned ranking do **not** exist yet — verification
here is the deterministic structural check, exactly as documented.

## Running it

```bash
# 1. Stack up + seeded (once)
make -f deploy/sandbox/Makefile up && make -f deploy/sandbox/Makefile seed

# 2. The proof
./scripts/poc-e2e.sh

# Through nginx instead of the direct gateway port:
GATEWAY_URL=http://localhost/api ./scripts/poc-e2e.sh

# Linux (containers reach the host at the docker bridge, not host.docker.internal):
POC_AGENT_HOST=172.17.0.1 ./scripts/poc-e2e.sh
```

The harness starts `agents/poc-probe-agent/agent.py` host-side (that *is* the
dev story — your agent runs on your machine), registers it with the sandbox
registry via the emerge SDK, and drives everything else through the public
gateway API. Re-runs are idempotent (409 on re-register is accepted).

Routing is LLM-driven and therefore probabilistic; stage 4/6 goals name the
probe capability explicitly to make routing near-deterministic. If a run
fails on routing rather than a real defect, re-run the script.

### Known operational failure mode — HealthMonitor staleness

Symptom: stages 3/4/6/7 all fail together on a stack that was healthy last
session, while stage 2 passes. Cause: the registry's background HealthMonitor
polls every registered agent's `health_endpoint` on a 5-minute cycle. A DID
left registered while its process is down (e.g. days between manual runs)
accumulates failed checks and flips to `UNHEALTHY` — and PnD discovery's
Step-1 GIN pre-filter hard-requires `health_status = 'HEALTHY'`, so the agent
is **silently excluded** from the candidate pool even though its embeddings
are fine. Everything downstream of discovery then fails.

The harness defends against this two ways (Stage 2): it soft-deletes any
prior `poc-probe` registration before `emerge publish` — re-registration
purges the inactive row (`registration.py::_purge_soft_deleted_agent`) and
re-creates it with a fresh live connectivity probe (`HEALTHY` immediately) —
and it explicitly asserts `health_status == "HEALTHY"` on the registry row
before proceeding, failing fast with this diagnosis instead of a silent
cascade.

First-time users are unaffected: a fresh registration live-probes to HEALTHY
and the harness completes well inside the 5-minute window. The mode only
bites long-lived idle registrations — which also makes it worth knowing for
**external devs returning after a gap**: if your agent stopped being
discovered, check its `health_status` and re-register (or just keep it
running).

### The fixture

`agents/poc-probe-agent/agent.py` — a paid A2A agent (`base_fee: 0.05`) built
entirely on the emerge SDK, returning a deterministic `PROBE-REPORT` line.
`--flaky` puts an HTTP shim in front of the SDK server that 503s the first
`message/send` and forwards everything else. The flake is at the HTTP layer on
purpose: a handler-level failure becomes a *failed task* → `Error:` content →
the **permanent** path that must NOT retry; only a raised transient (timeout /
connection / 5xx) may trigger the retry-gate.

## Relationship to the other gates

- `scripts/m0-verify.sh`, `m0-gates-live.sh`, `m2-gates-live.sh` — launch-asset
  gates (health, canvas render, 3-protocol demo). Still authoritative for the
  hero-GIF checklist.
- `scripts/launch-gate-ci.sh` — registry boot + fixture registration smoke (CI).
- **`scripts/poc-e2e.sh` (this)** — the full-system proof across all five
  previously-unproven claims. Supersedes nothing; sits above everything.

For external developers: this script doubles as the onboarding proof — clone,
run one script, and watch your agent get discovered, planned, verified,
retried, and paid.
