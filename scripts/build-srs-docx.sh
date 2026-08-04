#!/usr/bin/env bash
# Build docs/srs.docx from docs/srs.md with Mermaid/ASCII diagrams rendered as
# embedded PNG figures and a Google-Docs-friendly reference style.
#
# Steps: render *.mmd -> *.png -> preprocess markdown (swap diagram fences for
# captioned images) -> pandoc -> docs/srs.docx
#
# Requirements:
#   - pandoc on PATH (or set PANDOC=/path/to/pandoc)
#   - Mermaid CLI for (re)rendering: set MMDC=/path/to/mmdc. If unset/missing,
#     existing PNGs in docs/assets/srs/ are reused.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS="$REPO_ROOT/docs"
ASSETS="$DOCS/assets/srs"
SRC="$DOCS/srs.md"
OUT="$DOCS/srs.docx"

PANDOC="${PANDOC:-pandoc}"
command -v "$PANDOC" >/dev/null 2>&1 || { echo "pandoc not found; set PANDOC=/path/to/pandoc" >&2; exit 1; }

FIGS=(fig-2-1-high-level fig-2-2-call-graph fig-3-1-langgraph-loop fig-3-2-pipeline fig-4-1-persistence)

# 1. Render diagrams if a Mermaid CLI is available.
if [[ -n "${MMDC:-}" && -x "${MMDC}" ]]; then
  echo "Rendering Mermaid diagrams with $MMDC"
  for f in "${FIGS[@]}"; do
    "$MMDC" -i "$ASSETS/$f.mmd" -o "$ASSETS/$f.png" \
      -c "$ASSETS/mermaid-config.json" -p "$ASSETS/puppeteer.json" -b white -s 3
  done
else
  echo "MMDC not set; reusing existing PNGs in $ASSETS"
fi

# 2. Preprocess markdown: swap diagram code fences for captioned images.
PRE="$(mktemp --suffix=.md)"
trap 'rm -f "$PRE"' EXIT

python3 - "$SRC" "$PRE" <<'PY'
import re, sys

src, out = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()

def fig(png, caption, width):
    # `width` may be a width ("6.5in") or a height ("h:8in") constraint.
    dim = f"height={width[2:]}" if width.startswith("h:") else f"width={width}"
    return f"![{caption}]({png}){{{dim}}}"

# Fenced-block replacements (matched by content signature, not line number).
blocks = [
    # (compiled regex over the whole fenced block, replacement image)
    (re.compile(r"```mermaid\nflowchart TB\n    User\(.*?```", re.S),
     fig("fig-2-1-high-level.png", "Figure 2.1 - High-level architecture", "6.5in")),
    (re.compile(r"```mermaid\nflowchart LR\n    FE\[Frontend\].*?```", re.S),
     fig("fig-2-2-call-graph.png", "Figure 2.2 - Inter-service call graph", "6.5in")),
    # LangGraph loop is a plain (non-mermaid) fenced ASCII block.
    (re.compile(r"```\norchestrator_llm .*?```", re.S),
     fig("fig-3-1-langgraph-loop.png", "Figure 3.1 - SuperAgent LangGraph loop", "6.0in")
     + "\n\n"
     + fig("fig-3-2-pipeline.png", "Figure 3.2 - Execution middleware pipeline (7 steps)", "h:7.5in")),
]

for rx, rep in blocks:
    new, n = rx.subn(lambda m: rep, text)
    if n != 1:
        raise SystemExit(f"Expected exactly 1 match, got {n} for {rx.pattern[:40]!r}")
    text = new

# Insert the persistence figure after the section 4.1 store table.
anchor = "\n### 4.2 Relational Model"
img41 = "\n" + fig("fig-4-1-persistence.png",
                    "Figure 4.1 - Persistence stores and their owners", "6.5in") + "\n"
if anchor not in text:
    raise SystemExit("Anchor for Figure 4.1 not found")
text = text.replace(anchor, img41 + anchor, 1)

open(out, "w", encoding="utf-8").write(text)
PY

# 3. Pandoc -> DOCX.
"$PANDOC" "$PRE" -o "$OUT" \
  --from markdown --to docx \
  --reference-doc "$ASSETS/reference.docx" \
  --resource-path "$ASSETS" \
  --toc --toc-depth=3

echo "Wrote $OUT"
