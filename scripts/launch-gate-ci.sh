#!/usr/bin/env bash
# Launch gate — minimal end-to-end proof for CI and local smoke runs.
#
# Proves: infra → migrate → registry up → fixture agent registered → SDK scaffold.
# Does not start the full agent fleet or PnD embeddings (keeps CI fast).
#
# Usage:
#   ./scripts/launch-gate-ci.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/orcha?schema=public}"
export PYTHONPATH="${PYTHONPATH:-.}"
export DISABLE_AUTH=true
export KAFKA_ENABLED=false
export SERVICE_NAME=registry-service
export ENVIRONMENT=test
export HOST=0.0.0.0
export PORT=8000
export RELOAD=false
export GRPC_HOST="[::]"
export GRPC_PORT=50051
export PAT_TOKEN_PREFIX=orcha_pat_
export PAT_TOKEN_LENGTH=40
export ADAPTER_TIMEOUT=10
export ADAPTER_MAX_RETRIES=3
export HEALTH_CHECK_INTERVAL=300
export MAX_HEALTH_FAILURES=3
export PAYMENT_FACILITATOR_URL=https://api.orcha.bot/verify
export MCP_PROTOCOL_VERSION=2025-11-25
export LOG_LEVEL=INFO
REGISTRY_URL="${REGISTRY_URL:-http://localhost:8000}"

REGISTRY_PID=""
cleanup() {
  if [[ -n "$REGISTRY_PID" ]] && kill -0 "$REGISTRY_PID" 2>/dev/null; then
    kill "$REGISTRY_PID" 2>/dev/null || true
    wait "$REGISTRY_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

wait_for() {
  local url="$1" max="${2:-60}" i=0
  while [[ $i -lt $max ]]; do
    if curl -sf --max-time 2 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    i=$((i + 1))
  done
  return 1
}

echo "[launch-gate] prisma generate + migrate + grpc stubs"
uv run prisma generate --schema=common/database/schema.prisma >/dev/null
make grpc-generate >/dev/null
DATABASE_URL="$DATABASE_URL" uv run prisma migrate deploy --schema=common/database/schema.prisma >/dev/null

echo "[launch-gate] start registry"
uv run uvicorn services.registry.src.main:app \
  --host 0.0.0.0 --port 8000 --log-level warning &
REGISTRY_PID=$!

wait_for "http://localhost:8000/api/v1/health" 60

echo "[launch-gate] start manifest server + register one fixture agent"
uv run uvicorn services.registry.tests.manifest_server:app \
  --host 0.0.0.0 --port 9000 --log-level warning &
MANIFEST_PID=$!
trap 'kill "$MANIFEST_PID" 2>/dev/null || true; cleanup' EXIT

wait_for "http://localhost:9000/health" 30

fixture="services/registry/tests/fixtures/a2a_hotel_booking.yaml"
reg_result=$(curl -s -w "\n%{http_code}" \
  -F "emerge_yaml=@${fixture}" \
  "${REGISTRY_URL:-http://localhost:8000}/api/v1/agents/register")
reg_code=$(echo "$reg_result" | tail -1)
if [[ ! "$reg_code" =~ ^2 && "$reg_code" != "409" ]]; then
  echo "[launch-gate] FAIL: fixture registration HTTP ${reg_code}" >&2
  echo "$reg_result" | sed '$d' >&2
  exit 1
fi
kill "$MANIFEST_PID" 2>/dev/null || true
wait "$MANIFEST_PID" 2>/dev/null || true
MANIFEST_PID=""
trap cleanup EXIT

REGISTRY_URL="${REGISTRY_URL:-http://localhost:8000}"
agents_json=$(curl -sf "${REGISTRY_URL}/api/v1/agents?limit=100")
agent_count=$(echo "$agents_json" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); agents=(d.get('data') or {}).get('agents') or []; print(len(agents))")

if [[ "${agent_count:-0}" -lt 1 ]]; then
  echo "[launch-gate] FAIL: expected registered agents, got: $agents_json" >&2
  exit 1
fi
echo "[launch-gate] OK: ${agent_count} agent(s) registered"

echo "[launch-gate] SDK emerge init smoke"
rm -rf /tmp/launch-gate-agent
uv run emerge init "Launch Gate Agent" --dir /tmp/launch-gate-agent
test -f /tmp/launch-gate-agent/agent.py

echo "[launch-gate] fleet manifest validation"
DATABASE_URL="$DATABASE_URL" uv run pytest services/registry/tests/test_fleet_manifests.py -q

echo "[launch-gate] PASS"
