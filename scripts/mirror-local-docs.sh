#!/usr/bin/env bash
# Mirror moat / idea / strategy docs into docs-local/ (gitignored).
# Idempotent — safe to re-run after local-only edits.
#
# Usage: ./scripts/mirror-local-docs.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DEST="$ROOT/docs-local"
SCOPE="$ROOT/docs/dev_docs/SCOPE-MAP.md"

copy_if_exists() {
  local src="$1" dst="$2"
  if [[ -f "$src" ]]; then
    mkdir -p "$(dirname "$dst")"
    cp -a "$src" "$dst"
    echo "  $src"
  else
    echo "  (skip missing) $src" >&2
  fi
}

copy_dir_if_exists() {
  local src="$1" dst="$2"
  if [[ -d "$src" ]]; then
    mkdir -p "$dst"
    rsync -a --delete "$src/" "$dst/"
    echo "  $src/ -> $dst/"
  else
    echo "  (skip missing dir) $src" >&2
  fi
}

echo "Mirroring moat / idea docs to docs-local/ ..."

mkdir -p "$DEST/inception" "$DEST/dan" "$DEST/primitives" "$DEST/pdfs" \
  "$DEST/scope-strategy" "$DEST/srs"

# Inception / vision
copy_if_exists "$ROOT/INCEPTION.md" "$DEST/inception/INCEPTION.md"
copy_if_exists "$ROOT/VISION.md" "$DEST/inception/VISION.md"

# DAN phase specs
copy_dir_if_exists "$ROOT/docs/dev_docs/dan" "$DEST/dan"

# DAPN moat primitives (canvaskit stays in repo for M0 dev)
for f in README.md agentkey.md manifestkit.md orchflow.md connectkit.md; do
  copy_if_exists "$ROOT/docs/dev_docs/primitives/$f" "$DEST/primitives/$f"
done

# PDFs
copy_if_exists "$ROOT/docs/dev_docs/EmergeOS-DAN.pdf" "$DEST/pdfs/EmergeOS-DAN.pdf"
while IFS= read -r pdf; do
  base=$(basename "$pdf")
  copy_if_exists "$pdf" "$DEST/pdfs/$base"
done < <(find "$ROOT/docs/archtecture" "$ROOT/docs/services" -name '*.pdf' 2>/dev/null || true)

# SCOPE-MAP strategy extracts (Context + M4–M7)
if [[ -f "$SCOPE" ]]; then
  awk '/^## Context$/,/^---$/{if(NR>1) print}' "$SCOPE" | head -n -1 \
    > "$DEST/scope-strategy/context.md"
  awk '/^## M4 — DAN Phase 0/,/^## Discipline Rules$/{if(!/^## Discipline Rules/) print}' "$SCOPE" \
    > "$DEST/scope-strategy/m4-m7-strategy.md"
  echo "  $SCOPE -> scope-strategy/{context,m4-m7-strategy}.md"
fi

# SRS placeholder
if [[ ! -f "$DEST/srs/README.md" ]]; then
  cat > "$DEST/srs/README.md" <<'EOF'
# Software Requirements (local)

SRS is authored locally until promoted to the public dev tier.
Do not commit this directory — it lives under gitignored `docs-local/`.
EOF
fi

# Write manifest with checksums
MANIFEST="$DEST/MANIFEST.md"
{
  echo "# docs-local manifest"
  echo ""
  echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo ""
  echo "Source repo: \`$ROOT\`"
  echo ""
  echo "| File | SHA256 |"
  echo "|------|--------|"
  while IFS= read -r f; do
    rel="${f#"$DEST"/}"
    hash=$(sha256sum "$f" | awk '{print $1}')
    echo "| \`$rel\` | \`${hash:0:16}…\` |"
  done < <(find "$DEST" -type f ! -name MANIFEST.md | sort)
  echo ""
  echo "## Source paths"
  echo ""
  echo "- \`INCEPTION.md\`, \`VISION.md\` → \`inception/\`"
  echo "- \`docs/dev_docs/dan/**\` → \`dan/\`"
  echo "- Moat primitives (not canvaskit) → \`primitives/\`"
  echo "- PDFs → \`pdfs/\`"
  echo "- SCOPE-MAP Context + M4–M7 → \`scope-strategy/\`"
  echo ""
  echo "Re-run: \`./scripts/mirror-local-docs.sh\`"
} > "$MANIFEST"

echo ""
echo "Done. Manifest: docs-local/MANIFEST.md"
file_count=$(find "$DEST" -type f ! -name MANIFEST.md | wc -l)
echo "Files mirrored: $file_count"
