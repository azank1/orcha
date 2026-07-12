# M0 — OSS Launch Gate verification log

Canonical spec: [SCOPE-MAP.md](SCOPE-MAP.md) § M0.

## Status

| Item | State |
|------|--------|
| Code on local `main` | ✅ Merged (CanvasKit, finance agent, computer-use, sandbox infra, cyber-technical theme, real Google OAuth) |
| Code on `origin/main` | ⬜ Not pushed — **2 commits ahead**; push after live gates pass |
| Automated gates | ✅ 7/7 passing (`./scripts/m0-verify.sh`) |
| Live gates 1, 3–5 | ✅ Verified via live stack + direct API (2026-07-12) — see Gate results below |

## Automated check (gates 1, 2, 6, 7)

With the stack running:

```bash
./scripts/m0-verify.sh
```

Exits 0 if automated gates pass; prints manual steps for gates 3–5 (DevTools SSE + CanvasKit render).

## Gate results

| # | Gate | Result | How to verify |
|---|------|--------|---------------|
| 1 | `run-all.sh` / stack healthy | ✅ Pass | `./scripts/run-all.sh` **or** `make -f deploy/sandbox/Makefile up` — `finance-dashboard-agent` (3010) is now included in Phase 3b (previously omitted; see below) |
| 2 | finance-dashboard-agent registered | ✅ Pass | `./scripts/seed-live-agents.sh` — confirmed `did:orcha:agent:finance-dashboard` in registry |
| 3 | Goal routes to finance-dashboard-agent | ✅ Pass | Verified via direct API call — `invocation_result` for `did_orcha_agent_finance-dashboard__get_portfolio_dashboard`, `status: success` |
| 4 | `canvas_manifest` SSE in DevTools | ✅ Pass | Verified via raw SSE stream — `type: canvas_manifest` event present |
| 5 | CanvasKit renders 4 components | ✅ Pass | Manifest components: `metric_card` ×4, `line_chart`, `data_table`, `alert_feed` |
| 6 | `git grep __canvas__` (runtime only) | ✅ Pass | `agents/finance-dashboard-agent/*` + `agents/google-workspace-orchestrator/*` + `output_normalizer.py` only |
| 7 | `PAYMENT_MODE=mock` | ✅ Pass | `PAYMENT_MODE=mock` in `.env.sandbox` |

**Root cause found and fixed for gates 1–5:** `finance-dashboard-agent`'s
`pyproject.toml` declared a `[build-system]` (hatchling) with no valid
package layout — `uv run` tried to build it as an installable package and
failed, which is why it was never wired into `run-all.sh` Phase 3b locally
(the Docker path bypasses `uv` entirely via `pip install`, so it worked in
the sandbox but not local dev). Fixed by removing the unneeded
`[build-system]` section, matching the flat-script pattern already used by
`search-agent`.

## Owner sign-off

| Gate | Owner | Date | Notes |
|------|-------|------|-------|
| 1 run-all / sandbox up | agent-verified | 2026-07-12 | All 5 services + finance-dashboard-agent healthy |
| 2 finance agent registered | agent-verified | 2026-07-12 | `did:orcha:agent:finance-dashboard` |
| 3 goal routes correctly | agent-verified | 2026-07-12 | Direct API test, `status: success` |
| 4 canvas_manifest SSE | agent-verified | 2026-07-12 | Raw SSE stream inspection |
| 5 CanvasKit renders | agent-verified | 2026-07-12 | All 4 required component types present |
| 7 mock payments | agent-verified | 2026-07-12 | `.env.sandbox` |

All gates verified via direct API testing this session (not yet browser/DevTools-verified by a human — recommended before public launch, since browser rendering and DevTools inspection are a different code path from the raw SSE stream, even though the underlying data is identical).

M2 live gates (3-protocol: MCP + A2A + COMPUTER_USE) also verified — 5/5 runs
passed, best wall clock 13s. See `docs/dev_docs/M2-DEMO.md`.

Next: push `main` to `origin` (2 commits ahead), then proceed to M2 launch assets.

## M1 note (not M0)

`SANDBOX_MAX_DAILY_MESSAGES` is required **before the public sandbox URL goes live** (M1 gate), not before M0 merge. Set in `.env.sandbox` (see `.env.sandbox.example`, default 500).
