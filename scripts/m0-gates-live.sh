#!/usr/bin/env bash
# M0 gates 3–5 — live API verification (no browser required).
# Gate 3: goal routes to finance-dashboard-agent (SSE invocation events)
# Gate 4: canvas_manifest SSE event present
# Gate 5: manifest contains MetricCard, LineChart, DataTable, AlertFeed
#
# Usage: ./scripts/m0-gates-live.sh [--gateway URL]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATEWAY="${GATEWAY_URL:-http://localhost:8080}"
GOAL="Show me my portfolio dashboard"
PASS=0
FAIL=0

_pass() { echo "  ✅ $1"; PASS=$((PASS + 1)); }
_fail() { echo "  ❌ $1"; FAIL=$((FAIL + 1)); }
header() { echo; echo "── $1 ──"; }

header "Gate 3–5 — SSE goal → finance-dashboard → canvas_manifest"

# Auth: register ephemeral user
EMAIL="m0gate-$(date +%s)@example.com"
REG=$(curl -sf -X POST "$GATEWAY/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"m0gate-test-123\",\"display_name\":\"M0 Gate\"}")
TOKEN=$(echo "$REG" | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

SESSION=$(curl -sf -X POST "$GATEWAY/api/v1/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{}')
SID=$(echo "$SESSION" | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")

OUT=$(mktemp)
trap 'rm -f "$OUT"' EXIT

# Stream SSE for up to 120s
curl -sf -N -X POST "$GATEWAY/api/v1/sessions/$SID/message" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"message\":\"$GOAL\"}" \
  --max-time 120 > "$OUT" 2>/dev/null || true

if grep -q 'finance-dashboard' "$OUT"; then
  _pass "Gate 3 — finance-dashboard-agent referenced in SSE stream"
else
  _fail "Gate 3 — finance-dashboard-agent not seen in SSE stream"
fi

if grep -q 'canvas_manifest' "$OUT"; then
  _pass "Gate 4 — canvas_manifest SSE event emitted"
else
  _fail "Gate 4 — no canvas_manifest in SSE stream"
fi

if python3 - "$OUT" <<'PY'
import json, re, sys
path = sys.argv[1]
text = open(path, errors="replace").read()
required = {"metric_card", "line_chart", "data_table", "alert_feed"}
found = set()
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
            found.add(t)
if required <= found:
    print("ok")
    sys.exit(0)
print(f"missing: {required - found}")
sys.exit(1)
PY
then
  _pass "Gate 5 — CanvasKit components present (MetricCard, LineChart, DataTable, AlertFeed)"
else
  _fail "Gate 5 — required CanvasKit components missing in canvas_manifest"
fi

echo
echo "══════════════════════════════════════"
echo "  Live gates 3–5: $PASS passed, $FAIL failed"
echo "══════════════════════════════════════"

# Fallback: direct agent canvas envelope (validates pipeline without LLM routing)
if [[ "$FAIL" -gt 0 ]]; then
  header "Fallback — direct finance agent canvas envelope"
  if curl -sf http://localhost:3010/health >/dev/null 2>&1; then
    ENV_JSON=$(cd "$ROOT/agents/finance-dashboard-agent" && uv run python -c "
import asyncio, json
from server import get_portfolio_dashboard
raw = asyncio.run(get_portfolio_dashboard())
data = json.loads(raw)
m = data['manifest']
types = {c['type'] for c in m['components']}
need = {'metric_card','line_chart','data_table','alert_feed'}
assert data.get('__canvas__') is True
assert need <= types, f'missing {need-types}'
print('ok')
")
    if [[ "$ENV_JSON" == "ok" ]]; then
      _pass "Fallback — finance agent returns valid canvas envelope with all 4 component families"
      echo "  ℹ  Full gates 3–5 need a valid OPENROUTER_API_KEY for planner routing"
    fi
  else
    echo "  ℹ  finance-dashboard-agent not running on :3010"
  fi
fi

[[ "$FAIL" -eq 0 ]]
