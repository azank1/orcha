#!/usr/bin/env bash
# M2 demo gates — live API verification (no browser required).
# Extends M0 gates 3–5 with search + computer-use legs for the canonical M2 goal.
#
# Usage:
#   GATEWAY_URL=http://localhost/api ./scripts/m2-gates-live.sh
#   M2_RUNS=5 M2_PASS=4 ./scripts/m2-gates-live.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATEWAY="${GATEWAY_URL:-http://localhost:8080}"
GOAL_FILE="$ROOT/scripts/m2-demo-goal.txt"
GOAL="$(tr -d '\n' < "$GOAL_FILE")"
RUNS="${M2_RUNS:-1}"
PASS_THRESHOLD="${M2_PASS:-1}"

_pass() { echo "  ✅ $1"; }
_fail() { echo "  ❌ $1"; }
header() { echo; echo "── $1 ──"; }

analyze_stream() {
  local path="$1"
  local elapsed="$2"
  python3 - "$path" "$elapsed" <<'PY'
import json, sys
path, elapsed = sys.argv[1], int(sys.argv[2])
text = open(path, errors="replace").read()
checks = {
    "finance_dashboard": "finance-dashboard" in text,
    "canvas_manifest": "canvas_manifest" in text,
    "search_agent": "search" in text.lower(),
    "computer_use": "COMPUTER_USE" in text or "computer_use" in text.lower(),
    "no_graph_error": '"type": "error"' not in text,
}
required_types = {"metric_card", "line_chart", "data_table", "alert_feed"}
found_types = set()
for line in text.splitlines():
    if not line.startswith("data:"):
        continue
    payload = line[5:].strip()
    if not payload or payload == "[DONE]":
        continue
    try:
        ev = json.loads(payload)
    except json.JSONDecodeError:
        continue
    if ev.get("type") != "canvas_manifest":
        continue
    manifest = ev.get("manifest") or {}
    for comp in manifest.get("components", []):
        t = comp.get("type", "")
        if t:
            found_types.add(t)
checks["canvas_components"] = required_types <= found_types
ok = all(checks.values())
print(json.dumps({"elapsed_s": elapsed, "checks": checks, "pass": ok}))
sys.exit(0 if ok else 1)
PY
}

run_once() {
  local run_num="$1"
  local OUT
  OUT=$(mktemp)

  local EMAIL="m2gate-${run_num}-$(date +%s)@example.com"
  local REG TOKEN SID
  REG=$(curl -sf -X POST "$GATEWAY/auth/register" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\",\"password\":\"m2gate-test-123\",\"display_name\":\"M2 Gate\"}")
  TOKEN=$(echo "$REG" | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

  SID=$(curl -sf -X POST "$GATEWAY/api/v1/sessions" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d '{}' | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")

  local start end elapsed
  start=$(date +%s)
  curl -sf -N -X POST "$GATEWAY/api/v1/sessions/$SID/message" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"message\":$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$GOAL")}" \
    --max-time 180 > "$OUT" 2>/dev/null || true
  end=$(date +%s)
  elapsed=$((end - start))

  analyze_stream "$OUT" "$elapsed"
  rm -f "$OUT"
}

header "M2 gates — 3-protocol goal + CanvasKit"
echo "Goal: $GOAL"
echo "Runs: $RUNS (pass if >= $PASS_THRESHOLD succeed)"
echo

PASS_COUNT=0
BEST_ELAPSED=9999
for i in $(seq 1 "$RUNS"); do
  echo "Run $i/$RUNS"
  set +e
  RESULT=$(run_once "$i")
  RC=$?
  set -e
  if [[ "$RC" -eq 0 ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    ELAPSED=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['elapsed_s'])")
    _pass "Run $i passed (${ELAPSED}s)"
    if [[ "$ELAPSED" -lt "$BEST_ELAPSED" ]]; then
      BEST_ELAPSED=$ELAPSED
    fi
  else
    _fail "Run $i failed"
    if [[ -n "$RESULT" ]]; then
      echo "$RESULT" | python3 - <<'PY'
import json, sys
d = json.loads(sys.stdin.read())
for k, v in d.get("checks", {}).items():
    print(f"    {k}: {'ok' if v else 'FAIL'}")
PY
    fi
  fi
  echo
done

echo "══════════════════════════════════════"
echo "  M2 live gates: $PASS_COUNT/$RUNS passed (need >= $PASS_THRESHOLD)"
if [[ "$BEST_ELAPSED" -lt 9999 ]]; then
  echo "  Best wall clock: ${BEST_ELAPSED}s (target <30s for hero clip)"
fi
echo "══════════════════════════════════════"

[[ "$PASS_COUNT" -ge "$PASS_THRESHOLD" ]]
