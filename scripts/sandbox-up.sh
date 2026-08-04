#!/usr/bin/env bash
# One-command sandbox recovery: stack up + tunnel up + health check.
# Use after a machine restart. The tunnel and stack both die with the host —
# this is the bridge setup, not the permanent home (see deploy/sandbox/RUNBOOK.md).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "── starting sandbox stack ──"
docker compose -f deploy/sandbox/docker-compose.sandbox.yml --env-file .env.sandbox up -d
sleep 20
curl -sf -o /dev/null http://localhost && echo "  ✅ origin healthy (localhost:80)"

echo "── starting tunnel ──"
if pgrep -f 'cloudflared tunnel run orcha-sandbox' >/dev/null; then
  echo "  (already running)"
else
  nohup "$HOME/.local/bin/cloudflared" tunnel run orcha-sandbox > /tmp/cf-tunnel.log 2>&1 &
  sleep 10
fi
SANDBOX_URL="${ORCHA_SANDBOX_URL:-https://sandbox.orcha.ai}"
curl -sf -o /dev/null "$SANDBOX_URL" && echo "  ✅ $SANDBOX_URL live"
curl -sf "$SANDBOX_URL/api/auth/guest" > /dev/null && echo "  ✅ guest auth OK"
echo "sandbox up."
