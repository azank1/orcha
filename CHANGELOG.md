# Changelog

All notable changes to Orcha are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-08-03

Initial public release.

### Added

- Multi-protocol agent orchestration runtime: Registry, Planning & Discovery
  (hybrid search + 5-stage DAG planner), SuperAgent (LangGraph ReAct loop),
  Gateway (auth + BFF + mock payments), CanvasKit live-dashboard frontend.
- `emerge` SDK: agent registration decorator, CLI, A2A server helpers.
- Flag-gated DAG execution (`DAG_PLANNER_ENABLED`, default off): complex goals
  route through a hybrid heuristic+semantic gate to the planner and execute as
  a planned sequential workflow through the same middleware pipeline.
- Flag-gated CDV step verification (`CDV_VERIFICATION_ENABLED`, default off):
  per-step deterministic scoring with per-run SQLite store and an adaptive
  stop backstop.
- Hosted sandbox (Beta) — `deploy/sandbox/` Docker stack with spend caps.
- OpenSSF Scorecard workflow + badge, gitleaks secret scanning, launch-gate CI.

### Notes

- Sandbox is Beta: session errors are under active debugging (fixed in 0.2.0).
- `PAYMENT_MODE=mock` runs the full stack with no external paid dependency.
