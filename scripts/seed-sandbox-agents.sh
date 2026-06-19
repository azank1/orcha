#!/usr/bin/env bash
# Register fleet agents against sandbox registry using docker-internal endpoints.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY_URL="${REGISTRY_URL:-http://localhost:8000}"

registered=0
failed=0

for agent_dir in "$ROOT"/agents/*/; do
  yaml="$agent_dir/emerge.yaml"
  [[ -f "$yaml" ]] || continue
  agent_name=$(basename "$agent_dir")

  patched=$(mktemp)
  sed \
    -e 's|localhost:3010|finance-dashboard:3010|g' \
    -e 's|localhost:3007|search-agent:3007|g' \
    -e 's|localhost:3004|web-scraper:3004|g' \
    -e 's|localhost:3006|notion-research:3006|g' \
    -e 's|localhost:3009|ecommerce:8080|g' \
    -e 's|localhost:3011|gws-orchestrator:8080|g' \
    -e 's|localhost:4567|lead-gen:8080|g' \
    "$yaml" > "$patched"

  result=$(curl -s -w "\n%{http_code}" \
    -F "emerge_yaml=@$patched" \
    "${REGISTRY_URL}/api/v1/agents/register" 2>/dev/null || echo -e '{}\n000')
  rm -f "$patched"

  http_code=$(echo "$result" | tail -1)
  body=$(echo "$result" | sed '$d')
  agent_id=$(echo "$body" | python3 -c \
    "import json,sys; print(json.load(sys.stdin).get('data', {}).get('agent_id', ''))" 2>/dev/null || echo "")

  if [[ -n "$agent_id" && "$http_code" =~ ^2 ]]; then
    echo "  registered ${agent_name} -> ${agent_id}"
    registered=$((registered + 1))
  elif [[ "$http_code" == "409" ]]; then
    echo "  already registered ${agent_name}"
    registered=$((registered + 1))
  else
    echo "  failed to register ${agent_name} (HTTP ${http_code})" >&2
    failed=$((failed + 1))
  fi
done

echo "Done: ${registered} registered, ${failed} failed"
[[ "$failed" -eq 0 ]]
