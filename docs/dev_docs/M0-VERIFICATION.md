# M0 — OSS Launch Gate verification log

Canonical spec: [SCOPE-MAP.md](SCOPE-MAP.md) § M0.

## Status

| Item | State |
|------|--------|
| Code on local `main` | ✅ Merged (CanvasKit, finance agent, computer-use, sandbox infra) |
| Code on `origin/main` | ⬜ Not pushed — **21 commits ahead**; push after live gates pass |
| Automated gates | Partial (see table) |
| Live gates 1, 3–5 | ⬜ **Owner-driven** — requires running stack |

## Automated check (gates 1, 2, 6, 7)

With the stack running:

```bash
./scripts/m0-verify.sh
```

Exits 0 if automated gates pass; prints manual steps for gates 3–5 (DevTools SSE + CanvasKit render).

## Gate results

| # | Gate | Result | How to verify |
|---|------|--------|---------------|
| 1 | `run-all.sh` / stack healthy | ⬜ Pending | `./scripts/run-all.sh` **or** `make -f deploy/sandbox/Makefile up` |
| 2 | finance-dashboard-agent registered | ⬜ Pending | `./scripts/seed-live-agents.sh` after registry up |
| 3 | Goal routes to finance-dashboard-agent | ⬜ Pending | Goal: *"Show me my portfolio dashboard"* — check progress stream |
| 4 | `canvas_manifest` SSE in DevTools | ⬜ Pending | Network tab → EventStream → event `type: canvas_manifest` |
| 5 | CanvasKit renders 4 components | ⬜ Pending | MetricCard, LineChart, DataTable, AlertFeed visible (not markdown) |
| 6 | `git grep __canvas__` (runtime only) | ✅ Pass | `agents/finance-dashboard-agent/*` + `output_normalizer.py` only |
| 7 | `PAYMENT_MODE=mock` | ⬜ Pending live | Set in gateway `.env` or `.env.sandbox`; mock credits on register/guest |

## Owner sign-off

| Gate | Owner | Date | Notes |
|------|-------|------|-------|
| 1 run-all / sandbox up | | | |
| 2 finance agent registered | | | |
| 3 goal routes correctly | | | |
| 4 canvas_manifest SSE | | | |
| 5 CanvasKit renders | | | |
| 7 mock payments | | | |

When all rows are checked: update SCOPE-MAP M0 → Done, push `main` to `origin`.

## M1 note (not M0)

`SANDBOX_MAX_DAILY_MESSAGES` is required **before the public sandbox URL goes live** (M1 gate), not before M0 merge. Set in `.env.sandbox` (see `.env.sandbox.example`, default 500).
