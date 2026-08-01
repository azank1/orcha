#!/usr/bin/env bash
# Manual launch-gate smoke runner — automated portions of docs/dev_docs/launch-gate-smoke.md
#
# Usage:
#   ./scripts/launch-gate-smoke.sh           # automated checks only
#   ./scripts/launch-gate-smoke.sh --full    # also requires docker for postgres
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Orcha launch gate smoke (automated) =="
echo

echo "[1/4] SDK tests"
uv run pytest sdk/tests/ -q

echo "[2/4] ExecutionObserver seam tests"
PYTHONPATH=. uv run pytest services/superagent/tests/unit/test_observers.py -q

echo "[3/4] Fleet manifest validation"
DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/orcha}" \
  PYTHONPATH=. uv run pytest services/registry/tests/test_fleet_manifests.py -q

if [[ "${1:-}" == "--full" ]]; then
  echo "[4/4] Full launch gate (requires postgres on :5432)"
  docker compose -f docker-compose.local.yml up -d postgres >/dev/null 2>&1 || true
  ./scripts/launch-gate-ci.sh
else
  echo "[4/4] Skipped full stack (pass --full to run ./scripts/launch-gate-ci.sh)"
fi

echo
echo "Automated smoke checks passed."
echo "Complete the manual checklist in docs/dev_docs/launch-gate-smoke.md before release."
