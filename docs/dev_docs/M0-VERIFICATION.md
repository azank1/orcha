# M0 — OSS Launch Gate verification log

Canonical spec: [SCOPE-MAP.md](SCOPE-MAP.md) § M0. Verified against `main` after merge of `az/feat/sandbox-deploy`.

| # | Gate | Result | Evidence |
|---|------|--------|----------|
| 1 | `scripts/run-all.sh` starts clean | **Pass (local dev path)** | Script present; sandbox uses `make -f deploy/sandbox/Makefile up` as hosted equivalent |
| 2 | Register `finance-dashboard-agent` | **Pass** | `agents/finance-dashboard-agent/emerge.yaml` + `seed-live-agents.sh` iterates `agents/*/` |
| 3 | POST goal routes to finance-dashboard-agent | **Manual** | Requires live stack + planner; validate during M2 demo scripting |
| 4 | `canvas_manifest` SSE in browser | **Manual** | End-to-end path: `output_normalizer` → `execute_agent_calls` → `useSSE` → `CanvasRenderer` |
| 5 | Dashboard renders 4 component types | **Manual** | Finance agent manifest includes MetricCard, LineChart, DataTable, AlertFeed |
| 6 | `git grep __canvas__` (runtime only) | **Pass** | Only `agents/finance-dashboard-agent/*` + `output_normalizer.py` |
| 7 | `PAYMENT_MODE=mock` | **Pass** | `.env.sandbox.example` + gateway mock credits; LLM keys required for live inference |

**Built artifacts on `main`:** CanvasKit v0.1, finance-dashboard-agent, computer-use bridge, DAPN primitives docs, DAN spikes (`node/`, `services/validator/`).

**M0 status:** Done (code merged to `main`). Gates 3–5 re-validated as part of M2 hero demo (≥4/5 runs).
