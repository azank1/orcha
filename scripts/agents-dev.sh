#!/usr/bin/env bash
# agents-dev.sh — Start all Orcha test agents and multiplex their logs into one terminal.
#
# A2A HTTP agents (started as background services):
#   web-scraper                  → http://localhost:3004
#   notion-research              → http://localhost:3006
#   ecommerce-automation         → http://localhost:3009
#   google-workspace-orchestrator → http://localhost:3011
#   lead-gen-agent               → http://localhost:4567
#
# MCP SSE agents (started as background services):
#   search-agent                 → http://localhost:3007
#
# MCP stdio agents (not started here — spawned on-demand by a client):
#   notion-mcp                   → node dist/index.js (in agents/notion-mcp/)
#
# Usage:
#   ./scripts/agents-dev.sh           # Start all agents
#   ./scripts/agents-dev.sh --no-wait # Start and exit (background mode)

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD='\033[1m'
RESET='\033[0m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'

# Per-agent prefix colours
C_SCRAPER='\033[0;36m'    # cyan
C_RESEARCH='\033[0;35m'   # magenta
C_DOCS='\033[0;33m'       # yellow
C_ECOMM='\033[0;31m'      # red  (ecommerce-automation)
C_GWS='\033[0;94m'        # bright blue
C_LEADGEN='\033[0;91m'    # bright red

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── PID tracking ─────────────────────────────────────────────────────────────
PIDS=()

cleanup() {
  echo ""
  printf "${YELLOW}Stopping agents...${RESET}\n"
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  printf "${GREEN}All agents stopped.${RESET}\n"
  exit 0
}
trap cleanup SIGINT SIGTERM

# ── Helper: stream agent logs with a coloured prefix ─────────────────────────
stream_agent() {
  local label="$1"
  local colour="$2"
  local fifo="$3"
  while IFS= read -r line; do
    printf "${colour}${BOLD}[%-18s]${RESET} %s\n" "$label" "$line"
  done < "$fifo" &
}

# ── Helper: wait for an HTTP endpoint to become healthy ──────────────────────
wait_healthy() {
  local name="$1"
  local url="$2"
  local retries=20
  local i=0
  while [ $i -lt $retries ]; do
    if curl -sf "$url" > /dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
    i=$((i + 1))
  done
  printf "${RED}[%-18s] health check timed out at %s${RESET}\n" "$name" "$url"
  return 1
}

# ── Banner ────────────────────────────────────────────────────────────────────
printf "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${BOLD}${BLUE}  Orcha Agent Dev Runner${RESET}\n"
printf "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n\n"

# ── Check uv is available ─────────────────────────────────────────────────────
if ! command -v uv &> /dev/null; then
  printf "${RED}✗ 'uv' not found. Install from https://docs.astral.sh/uv/${RESET}\n"
  exit 1
fi

# ── Create named FIFOs for log multiplexing ───────────────────────────────────
TMPDIR_FIFOS="$(mktemp -d)"
FIFO_SCRAPER="${TMPDIR_FIFOS}/scraper.fifo"
FIFO_RESEARCH="${TMPDIR_FIFOS}/research.fifo"
FIFO_DOCS="${TMPDIR_FIFOS}/docs.fifo"
FIFO_ECOMM="${TMPDIR_FIFOS}/ecomm.fifo"
FIFO_GWS="${TMPDIR_FIFOS}/gws.fifo"
FIFO_LEADGEN="${TMPDIR_FIFOS}/leadgen.fifo"

mkfifo "$FIFO_SCRAPER" "$FIFO_RESEARCH" "$FIFO_DOCS" "$FIFO_ECOMM" "$FIFO_GWS" "$FIFO_LEADGEN"

stream_agent "web-scraper:3004"     "$C_SCRAPER"   "$FIFO_SCRAPER"
stream_agent "notion-research:3006" "$C_RESEARCH"  "$FIFO_RESEARCH"
stream_agent "search-agent:3007"    "$C_DOCS"      "$FIFO_DOCS"
stream_agent "ecomm-auto:3009"      "$C_ECOMM"     "$FIFO_ECOMM"
stream_agent "gws-orch:3011"        "$C_GWS"       "$FIFO_GWS"
stream_agent "lead-gen:4567"        "$C_LEADGEN"   "$FIFO_LEADGEN"

# ── Start A2A agents ──────────────────────────────────────────────────────────

printf "${CYAN}Starting web-scraper       → http://localhost:3004${RESET}\n"
(
  cd "${ROOT}/agents/web-scraper"
  exec uv run uvicorn src.server:app \
    --host 0.0.0.0 --port 3004 --log-level info 2>&1
) > "$FIFO_SCRAPER" &
PIDS+=($!)

printf "${MAGENTA}Starting notion-research   → http://localhost:3006${RESET}\n"
(
  cd "${ROOT}/agents/notion-research"
  exec uv run uvicorn src.a2a_server:app \
    --host 0.0.0.0 --port 3006 --log-level info 2>&1
) > "$FIFO_RESEARCH" &
PIDS+=($!)

# ── Start MCP SSE agents ──────────────────────────────────────────────────────

printf "${YELLOW}Starting search-agent       → http://localhost:3007${RESET}\n"
(
  cd "${ROOT}/agents/search-agent"
  if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
  exec env PORT=3007 uv run python server.py 2>&1
) > "$FIFO_DOCS" &
PIDS+=($!)

printf "${RED}Starting ecommerce-automation  → http://localhost:3009${RESET}\n"
(
  cd "${ROOT}/agents/ecommerce-automation"
  if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
  exec uv run uvicorn src.a2a_server:app \
    --host 0.0.0.0 --port 3009 --log-level info 2>&1
) > "$FIFO_ECOMM" &
PIDS+=($!)

printf "${C_GWS}Starting google-workspace-orchestrator → http://localhost:3011${RESET}\n"
(
  cd "${ROOT}/agents/google-workspace-orchestrator"
  if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
  exec uv run uvicorn src.server:app \
    --host 0.0.0.0 --port 3011 --log-level info 2>&1
) > "$FIFO_GWS" &
PIDS+=($!)

printf "${C_LEADGEN}Starting lead-gen-agent         → http://localhost:4567${RESET}\n"
(
  cd "${ROOT}/agents/lead-gen-agent"
  if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
  exec uv run python main.py 2>&1
) > "$FIFO_LEADGEN" &
PIDS+=($!)

# ── Wait for agents to become healthy ─────────────────────────────────────────
printf "\n${YELLOW}Waiting for agents to become healthy...${RESET}\n"
sleep 2

HEALTHY=true
wait_healthy "web-scraper"                    "http://localhost:3004/health" || HEALTHY=false
wait_healthy "notion-research"                "http://localhost:3006/health" || HEALTHY=false
wait_healthy "search-agent"                   "http://localhost:3007/health" || HEALTHY=false
wait_healthy "ecommerce-automation"           "http://localhost:3009/health" || HEALTHY=false
wait_healthy "google-workspace-orchestrator"  "http://localhost:3011/health" || HEALTHY=false
wait_healthy "lead-gen-agent"                 "http://localhost:4567/health" || HEALTHY=false

# ── Endpoint summary ──────────────────────────────────────────────────────────
printf "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${BOLD}  A2A HTTP Agents (running)${RESET}\n"
printf "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "  ${C_SCRAPER}${BOLD}web-scraper${RESET}                  http://localhost:3004\n"
printf "  ${C_RESEARCH}${BOLD}notion-research${RESET}              http://localhost:3006\n"
printf "  ${C_ECOMM}${BOLD}ecommerce-automation${RESET}         http://localhost:3009\n"
printf "  ${C_GWS}${BOLD}google-workspace-orchestrator${RESET}  http://localhost:3011\n"
printf "  ${C_LEADGEN}${BOLD}lead-gen-agent${RESET}               http://localhost:4567\n\n"

printf "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${BOLD}  MCP SSE Agents (running)${RESET}\n"
printf "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "  ${C_DOCS}${BOLD}search-agent${RESET}      http://localhost:3007\n\n"

printf "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${BOLD}  MCP stdio Agents (spawned on-demand by client)${RESET}\n"
printf "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "  ${BOLD}notion-mcp${RESET}       stdio — launch: cd agents/notion-mcp && node dist/index.js\n"
printf "    env:   NOTION_API_KEY required\n\n"

printf "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"

if [ "$HEALTHY" = false ]; then
  printf "${YELLOW}Warning: one or more agents failed health checks. Check logs above.${RESET}\n\n"
else
  printf "${GREEN}${BOLD}All agents healthy. Logs below ↓${RESET}\n\n"
fi

if [[ "${1:-}" == "--no-wait" ]]; then
  printf "${YELLOW}Running in background mode (PIDs: %s)${RESET}\n" "${PIDS[*]}"
  exit 0
fi

wait
