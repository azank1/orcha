#!/usr/bin/env bash
# delete-agent.sh — Hard-delete an agent and all its FK-related rows from the DB.
#
# Cascade order (all have onDelete: Cascade on agents.id):
#   auth_strategies   ← security_configs (also via capabilities)
#   capabilities      ← agents
#   transports        ← agents
#   security_configs  ← agents
#   payment_configs   ← agents
#   agent_versions    ← agents
#   agent_embeddings  ← agents
#   agents            (root delete — triggers any remaining cascades)
#
# Usage:
#   ./scripts/delete-agent.sh <agent-did>
#   ./scripts/delete-agent.sh did:metaorcha:agent:docs-search
#
# DATABASE_URL is read from the environment or discovered from nearby .env files.

set -euo pipefail

BOLD='\033[1m'
RESET='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── Args ──────────────────────────────────────────────────────────────────────
if [ $# -lt 1 ]; then
  printf "${RED}Usage: %s <agent-did>${RESET}\n" "$(basename "$0")"
  printf "  Example: %s did:metaorcha:agent:docs-search\n" "$(basename "$0")"
  exit 1
fi

AGENT_DID="$1"

# ── Validate DID format (only safe characters — prevents SQL injection) ────────
if ! echo "$AGENT_DID" | grep -qE '^[a-zA-Z0-9:_-]+$'; then
  printf "${RED}✗ Invalid DID format. Only alphanumeric, ':', '_', '-' are allowed.${RESET}\n"
  exit 1
fi

# ── Resolve DATABASE_URL ──────────────────────────────────────────────────────
if [ -z "${DATABASE_URL:-}" ]; then
  for env_file in \
      "${ROOT}/.env" \
      "${ROOT}/services/registry/.env" \
      "${ROOT}/services/planning-discovery/.env.development" \
      "${ROOT}/services/planning-discovery/.env"; do
    if [ -f "$env_file" ]; then
      val="$(grep -E '^DATABASE_URL=' "$env_file" | head -1 | cut -d= -f2- | tr -d "\"'")"
      if [ -n "$val" ]; then
        DATABASE_URL="$val"
        printf "${CYAN}Using DATABASE_URL from %s${RESET}\n" "$env_file"
        break
      fi
    fi
  done
fi

if [ -z "${DATABASE_URL:-}" ]; then
  printf "${RED}✗ DATABASE_URL not set and could not be found in any .env file.${RESET}\n"
  exit 1
fi

# ── Check psql is available ───────────────────────────────────────────────────
if ! command -v psql &> /dev/null; then
  printf "${RED}✗ psql not found. Install postgresql-client.${RESET}\n"
  exit 1
fi

# ── Preview what will be deleted ──────────────────────────────────────────────
printf "\n${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${BOLD}  Checking agent: %s${RESET}\n" "$AGENT_DID"
printf "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n\n"

PREVIEW="$(psql "$DATABASE_URL" -t -A -F $'\t' <<EOSQL
SELECT
  a.name,
  a.version,
  a.protocol_type,
  a.health_status,
  COUNT(DISTINCT c.id)                                              AS capabilities,
  COUNT(DISTINCT av.id)                                             AS versions,
  (SELECT COUNT(*) FROM transports        WHERE agent_id = a.id)   AS transports,
  (SELECT COUNT(*) FROM security_configs  WHERE agent_id = a.id)   AS security_rows,
  (SELECT COUNT(*) FROM payment_configs   WHERE agent_id = a.id)   AS payment_rows,
  (SELECT COUNT(*) FROM agent_embeddings  WHERE agent_id = a.id)   AS embeddings,
  (SELECT COUNT(*) FROM auth_strategies s2
     JOIN security_configs sc ON sc.id = s2.security_id
    WHERE sc.agent_id = a.id)                                       AS auth_strategies
FROM agents a
LEFT JOIN capabilities   c  ON c.agent_id  = a.id
LEFT JOIN agent_versions av ON av.agent_id = a.id
WHERE a.id = '${AGENT_DID}'
GROUP BY a.id, a.name, a.version, a.protocol_type, a.health_status;
EOSQL
)"

if [ -z "$PREVIEW" ]; then
  printf "${YELLOW}⚠  Agent '%s' not found in database. Nothing to delete.${RESET}\n\n" "$AGENT_DID"
  exit 0
fi

IFS=$'\t' read -r name version protocol health caps vers trans sec pay emb auth <<< "$PREVIEW"

printf "  ${BOLD}Name:${RESET}          %s\n"  "$name"
printf "  ${BOLD}Version:${RESET}       %s\n"  "$version"
printf "  ${BOLD}Protocol:${RESET}      %s\n"  "$protocol"
printf "  ${BOLD}Health:${RESET}        %s\n"  "$health"
printf "\n  ${BOLD}Rows to be deleted:${RESET}\n"
printf "    agents           1\n"
printf "    capabilities     %s\n"  "$caps"
printf "    agent_versions   %s\n"  "$vers"
printf "    transports       %s\n"  "$trans"
printf "    security_configs %s\n"  "$sec"
printf "    auth_strategies  %s\n"  "$auth"
printf "    payment_configs  %s\n"  "$pay"
printf "    agent_embeddings %s\n"  "$emb"
printf "\n"

# ── Confirm ───────────────────────────────────────────────────────────────────
printf "${RED}${BOLD}This is irreversible. Type the agent DID to confirm:${RESET} "
read -r confirm

if [ "$confirm" != "$AGENT_DID" ]; then
  printf "${YELLOW}Aborted — DID did not match.${RESET}\n\n"
  exit 0
fi

# ── Delete (explicit order, wrapped in a transaction) ─────────────────────────
printf "\n${YELLOW}Deleting...${RESET}\n"

psql "$DATABASE_URL" <<EOSQL
BEGIN;

-- 1. Auth strategies tied to this agent's security config
DELETE FROM auth_strategies
  USING security_configs sc
  WHERE auth_strategies.security_id = sc.id
    AND sc.agent_id = '${AGENT_DID}';

-- 2. Auth strategies tied to this agent's capabilities
DELETE FROM auth_strategies
  USING capabilities c
  WHERE auth_strategies.capability_id = c.id
    AND c.agent_id = '${AGENT_DID}';

-- 3. Remaining child tables
DELETE FROM capabilities     WHERE agent_id = '${AGENT_DID}';
DELETE FROM transports        WHERE agent_id = '${AGENT_DID}';
DELETE FROM security_configs  WHERE agent_id = '${AGENT_DID}';
DELETE FROM payment_configs   WHERE agent_id = '${AGENT_DID}';
DELETE FROM agent_versions    WHERE agent_id = '${AGENT_DID}';
DELETE FROM agent_embeddings  WHERE agent_id = '${AGENT_DID}';

-- 4. Root row — any future cascades handled here
DELETE FROM agents WHERE id = '${AGENT_DID}';

COMMIT;
EOSQL

printf "\n${GREEN}${BOLD}✓ Agent '%s' and all related rows deleted.${RESET}\n\n" "$AGENT_DID"
