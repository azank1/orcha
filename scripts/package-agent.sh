#!/bin/bash
set -e

AGENT=$1
[ "$AGENT" ] || { echo "Usage: ./scripts/package-agent.sh <agent-name>"; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_DIR="$REPO_ROOT/agents/$AGENT"
BUILD_DIR="/tmp/orcha-agent-build-$$"
ZIP_OUT="$REPO_ROOT/dist/${AGENT}.zip"

[ -d "$AGENT_DIR" ] || { echo "ERROR: Agent directory not found: $AGENT_DIR"; exit 1; }

echo "==> Packaging $AGENT..."

rm -rf "$BUILD_DIR" && mkdir -p "$BUILD_DIR" "$REPO_ROOT/dist"

# Export deps from agent's pyproject.toml and install into build dir
cd "$AGENT_DIR"
uv export --format requirements-txt --no-hashes > /tmp/agent-req-$$.txt
uv pip install --target "$BUILD_DIR" -r /tmp/agent-req-$$.txt
rm -f /tmp/agent-req-$$.txt

# Copy agent source
[ -d "$AGENT_DIR/src" ] && cp -r "$AGENT_DIR/src" "$BUILD_DIR/"
[ -f "$AGENT_DIR/main.py" ] && cp "$AGENT_DIR/main.py" "$BUILD_DIR/"
[ -f "$AGENT_DIR/server.py" ] && cp "$AGENT_DIR/server.py" "$BUILD_DIR/"
cp "$AGENT_DIR/lambda_handler.py" "$BUILD_DIR/"

# Copy shared common libs (rename to importable names)
[ -d "$REPO_ROOT/common/emerge-tools" ] && cp -r "$REPO_ROOT/common/emerge-tools" "$BUILD_DIR/emerge_tools"
[ -d "$REPO_ROOT/common/utils" ] && cp -r "$REPO_ROOT/common/utils" "$BUILD_DIR/utils"
[ -d "$REPO_ROOT/common/internal-commons" ] && cp -r "$REPO_ROOT/common/internal-commons" "$BUILD_DIR/internal_commons"

# Zip it
cd "$BUILD_DIR"
zip -r9 "$ZIP_OUT" . \
  --exclude "*.pyc" \
  --exclude "__pycache__/*" \
  --exclude "*.dist-info/*" \
  --exclude "*.egg-info/*"

rm -rf "$BUILD_DIR"

echo "==> Done: $ZIP_OUT ($(du -sh "$ZIP_OUT" | cut -f1))"
