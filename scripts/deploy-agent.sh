#!/bin/bash
# Deploy a single agent to AWS Lightsail Containers.
# Usage: ./scripts/deploy-agent.sh <agent-name>
#
# Fully idempotent — safe to re-run; creates resources on first run,
# updates them on subsequent runs.
#
# Lightsail uses its own internal container registry — no ECR credentials
# needed. Images are pushed via `aws lightsail push-container-image`.
#
# Environment:
#   AWS_REGION                 — default us-east-1
#   METAORCHA_AGENT_SECRET_ID  — Secrets Manager secret id
#                                 (default: /metaorcha/dev/agent/<agent-name>).
#                                 SecretString must be a flat JSON object of env vars.
set -euo pipefail

AGENT="${1:-}"

[[ -n "$AGENT" ]] || {
  echo "Usage: ./scripts/deploy-agent.sh <agent-name>"
  echo "  e.g. ./scripts/deploy-agent.sh lead-gen-agent"
  exit 1
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_DIR="$REPO_ROOT/agents/$AGENT"

[[ -d "$AGENT_DIR" ]] || { echo "ERROR: Agent directory not found: $AGENT_DIR"; exit 1; }

# ── AWS config ───────────────────────────────────────────────────────────────
AWS_REGION="${AWS_REGION:-us-east-1}"
SERVICE_NAME="metaorcha-agent-${AGENT}"
LOCAL_IMAGE="${AGENT}:deploy"

echo ""
echo "=================================================="
echo "  Deploying: ${AGENT}"
echo "  Service:   ${SERVICE_NAME}"
echo "  Region:    ${AWS_REGION}"
echo "=================================================="
echo ""

# ── Step 1: Build image ───────────────────────────────────────────────────────
echo "==> [1/5] Building image (linux/amd64)"
docker build --platform linux/amd64 -t "${LOCAL_IMAGE}" "${AGENT_DIR}"

# ── Step 2: Ensure Lightsail container service exists ─────────────────────────
echo "==> [2/5] Ensuring Lightsail container service: ${SERVICE_NAME}"
SERVICE_STATE=$(aws lightsail get-container-services \
  --service-name "${SERVICE_NAME}" \
  --region "${AWS_REGION}" \
  --no-cli-pager \
  --query "containerServices[0].state" \
  --output text 2>/dev/null || echo "NOTFOUND")

if [[ "${SERVICE_STATE}" == "NOTFOUND" || "${SERVICE_STATE}" == "None" || -z "${SERVICE_STATE}" ]]; then
  echo "     Service not found — creating"
  aws lightsail create-container-service \
    --service-name "${SERVICE_NAME}" \
    --power nano \
    --scale 1 \
    --region "${AWS_REGION}" \
    --no-cli-pager > /dev/null

  echo "     Waiting for service to reach READY..."
  for attempt in $(seq 1 30); do
    STATE=$(aws lightsail get-container-services \
      --service-name "${SERVICE_NAME}" \
      --region "${AWS_REGION}" \
      --no-cli-pager \
      --query "containerServices[0].state" \
      --output text)
    echo "     [${attempt}/30] State: ${STATE}"
    [[ "${STATE}" == "READY" ]] && break
    [[ "${attempt}" -eq 30 ]] && { echo "ERROR: Timed out waiting for READY"; exit 1; }
    sleep 10
  done
else
  echo "     Service exists (state: ${SERVICE_STATE})"
fi

# ── Step 3: Push image to Lightsail registry ──────────────────────────────────
echo "==> [3/5] Pushing image to Lightsail registry (this may take a few minutes)"
if ! command -v lightsailctl &>/dev/null; then
  echo "     lightsailctl not found — installing"
  sudo curl -fsSL "https://s3.us-west-2.amazonaws.com/lightsailctl/latest/linux-amd64/lightsailctl" \
    -o /usr/local/bin/lightsailctl
  sudo chmod +x /usr/local/bin/lightsailctl
fi
aws lightsail push-container-image \
  --service-name "${SERVICE_NAME}" \
  --label "${AGENT}" \
  --image "${LOCAL_IMAGE}" \
  --region "${AWS_REGION}" \
  --no-cli-pager

# Fetch the latest image reference pushed to the Lightsail registry
LIGHTSAIL_IMAGE=$(aws lightsail get-container-images \
  --service-name "${SERVICE_NAME}" \
  --region "${AWS_REGION}" \
  --no-cli-pager \
  --query "containerImages[0].image" \
  --output text)
[[ -n "${LIGHTSAIL_IMAGE}" ]] || { echo "ERROR: Could not retrieve Lightsail image reference"; exit 1; }
echo "     Lightsail image: ${LIGHTSAIL_IMAGE}"

# ── Step 4: Resolve env vars from Secrets Manager ────────────────────────────
SECRET_ID="${METAORCHA_AGENT_SECRET_ID:-/metaorcha/dev/agent/${AGENT}}"
echo "==> [4/5] Resolving agent secrets (secret: ${SECRET_ID})"

ENV_JSON="{}"
if RAW_SECRET=$(aws secretsmanager get-secret-value \
     --secret-id "${SECRET_ID}" \
     --region "${AWS_REGION}" \
     --query 'SecretString' \
     --output text \
     --no-cli-pager 2>/dev/null); then
  ENV_JSON=$(echo "${RAW_SECRET}" | python3 -c \
    'import json,sys; d=json.load(sys.stdin); print(json.dumps({k: str(v) for k,v in d.items()}))')
  COUNT=$(echo "${ENV_JSON}" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')
  echo "     Loaded ${COUNT} env vars"
else
  echo "     (no secret at ${SECRET_ID} — deploying without env vars)"
fi

# ── Step 5: Create deployment ─────────────────────────────────────────────────
echo "==> [5/5] Creating Lightsail deployment"

CONTAINERS_JSON=$(python3 -c "
import json
print(json.dumps({
    '${AGENT}': {
        'image': '${LIGHTSAIL_IMAGE}',
        'ports': {'8080': 'HTTP'},
        'environment': json.loads('${ENV_JSON}')
    }
}))
")

PUBLIC_ENDPOINT_JSON=$(python3 -c "
import json
print(json.dumps({
    'containerName': '${AGENT}',
    'containerPort': 8080,
    'healthCheck': {
        'path': '/health',
        'intervalSeconds': 30,
        'timeoutSeconds': 5,
        'unhealthyThreshold': 2,
        'healthyThreshold': 2
    }
}))
")

aws lightsail create-container-service-deployment \
  --service-name "${SERVICE_NAME}" \
  --region "${AWS_REGION}" \
  --no-cli-pager \
  --containers "${CONTAINERS_JSON}" \
  --public-endpoint "${PUBLIC_ENDPOINT_JSON}" > /dev/null

echo "     Deployment submitted — waiting for ACTIVE state..."
for attempt in $(seq 1 24); do
  DEP_STATE=$(aws lightsail get-container-services \
    --service-name "${SERVICE_NAME}" \
    --region "${AWS_REGION}" \
    --no-cli-pager \
    --query "containerServices[0].currentDeployment.state" \
    --output text 2>/dev/null || echo "UNKNOWN")
  SVC_STATE=$(aws lightsail get-container-services \
    --service-name "${SERVICE_NAME}" \
    --region "${AWS_REGION}" \
    --no-cli-pager \
    --query "containerServices[0].state" \
    --output text)
  echo "     [${attempt}/24] Service: ${SVC_STATE} | Deployment: ${DEP_STATE}"

  [[ "${DEP_STATE}" == "ACTIVE" && "${SVC_STATE}" == "RUNNING" ]] && break
  [[ "${DEP_STATE}" == "FAILED" ]] && { echo "ERROR: Deployment failed"; exit 1; }
  [[ "${attempt}" -eq 24 ]] && { echo "ERROR: Timed out waiting for deployment"; exit 1; }
  sleep 15
done

SERVICE_URL=$(aws lightsail get-container-services \
  --service-name "${SERVICE_NAME}" \
  --region "${AWS_REGION}" \
  --no-cli-pager \
  --query "containerServices[0].url" \
  --output text)

echo ""
echo "=================================================="
echo "  Done!  ${AGENT} deployed successfully"
echo "  Service URL: ${SERVICE_URL}"
echo "=================================================="
