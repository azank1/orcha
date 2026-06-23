#!/usr/bin/env bash
# M2 demo validation helper — prints the canonical goal and checks stack health.
# Full 5-run protocol requires manual observation of planner routing (non-deterministic).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GOAL_FILE="$ROOT/scripts/m2-demo-goal.txt"
REGISTRY_URL="${REGISTRY_URL:-http://localhost:8000}"
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"
RUNS="${M2_DEMO_RUNS:-5}"
PASS_THRESHOLD="${M2_DEMO_PASS:-4}"

echo "=== M2 Demo validation ==="
echo "Goal ($(wc -c < "$GOAL_FILE" | tr -d ' ') bytes):"
cat "$GOAL_FILE"
echo

echo "--- Stack health ---"
for url in "$REGISTRY_URL/health" "$GATEWAY_URL/health"; do
  if curl -sf "$url" >/dev/null 2>&1; then
    echo "  OK  $url"
  else
    echo "  FAIL $url (is the stack running?)"
    exit 1
  fi
done

echo "--- Required agents (registry) ---"
agents_json=$(curl -sf "$REGISTRY_URL/api/v1/agents" 2>/dev/null || echo "{}")
for pattern in finance-dashboard search; do
  if echo "$agents_json" | grep -q "$pattern"; then
    echo "  OK  $pattern registered"
  else
    echo "  WARN $pattern not found — run seed-live-agents.sh"
  fi
done

echo
echo "Automated M2 gate script:"
echo "  GATEWAY_URL=http://localhost/api M2_RUNS=5 M2_PASS=4 ./scripts/m2-gates-live.sh"
echo
echo "Manual step: submit the goal above $RUNS times via UI or API."
echo "Pass if >=$PASS_THRESHOLD runs hit MCP (finance) + MCP (search) + COMPUTER_USE"
echo "and canvas_manifest SSE renders MetricCard + LineChart + DataTable + AlertFeed."
echo "See docs/dev_docs/M2-DEMO.md"
