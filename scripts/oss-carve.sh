#!/usr/bin/env bash
# oss-carve — carve the internal repo into the public-export staging worktree.
#
# Syncs the current checkout of the internal repo into the export worktree
# (default /home/azank/orcha-launch), minus every path in
# scripts/oss-private-paths.txt, then runs the launch gates on the CARVED
# tree: brand sweep (MetaOrcha / legacy DID prefixes) and, when available,
# a gitleaks secret scan.
#
# Does NOT commit or push anything in the worktree — the controller does that.
#
# Usage:
#   ./scripts/oss-carve.sh [--dry-run] [--force]
#
#   --dry-run  carve into a mktemp dir, run all checks there, change nothing
#   --force    overwrite even if the export worktree has uncommitted changes
#              (default is to refuse, to protect hand edits)
#
# Env:
#   EXPORT_WORKTREE  override the export worktree path
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EXCLUDES="$ROOT/scripts/oss-private-paths.txt"
WORKTREE="${EXPORT_WORKTREE:-/home/azank/orcha-launch}"
DRY_RUN=false
FORCE=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --force) FORCE=true ;;
    -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "[oss-carve] FAIL: unknown argument: $arg" >&2; exit 2 ;;
  esac
done

log()  { echo "[oss-carve] $*"; }
fail() { echo "[oss-carve] FAIL: $*" >&2; exit 1; }

# v0.1.0 sweep policy (user-approved): pure infra identifiers and legacy DID
# test fixtures are allowlisted with documented exceptions — the full infra
# rename lands in 0.2/0.3 (see docs-local/scope-strategy versioning master
# plan). Everything else containing the old brand fails the sweep.
#
# Substring allowlist (infra identifiers + live endpoints + org name):
ALLOWLIST=(
  'solvent-labs-org'
  'metaorcha_test'
  'metaorcha_pat_'
  'api.metaorcha.bot'
  'auth.metaorcha.bot'
  'app.metaorcha.ai'
  'metaorcha-postgres'
  'metaorcha-kafka'
  'metaorcha-network'
  'metaorcha-gateway'
  'metaorcha-agent-'
  'METAORCHA_AGENT_SECRET_ID'
  '/metaorcha/dev/'
  '_APP_ROOT'
  ':5432/metaorcha'
  'metaorcha-'
  'POSTGRES_DB: metaorcha'
  'psql -U postgres metaorcha'
  'metaorcha_dev'
  'metaorcha.test'
  'metaorcha/'
  'metaorcha.local'
  '"metaorcha" not in'
)
# File-scoped allowlist: policy/rule text that QUOTES the banned name, plus
# common/utils logging_config.py (the `metaorcha` logger namespace is a live
# runtime identifier across services — renamed with the 0.2/0.3 infra sweep).
ALLOWLIST_FILES=(
  'AGENTS.md'
  '.cursor/'
  'common/utils/src/logging_config.py'
)

[[ -f "$EXCLUDES" ]] || fail "exclude list not found: $EXCLUDES"
[[ -d "$WORKTREE" ]] || fail "export worktree not found: $WORKTREE"

# ---------------------------------------------------------------- gates ----
# Refuse to clobber hand edits in the export worktree (real runs only).
if [[ "$DRY_RUN" != true && "$FORCE" != true ]]; then
  if [[ -n "$(git -C "$WORKTREE" status --porcelain 2>/dev/null || true)" ]]; then
    git -C "$WORKTREE" status --short >&2 || true
    fail "export worktree has uncommitted changes (see above) — re-run with --force to overwrite"
  fi
fi

# Warn if the internal checkout itself is dirty: we carve the working tree,
# so uncommitted changes would leak into the export.
if [[ -n "$(git status --porcelain)" ]]; then
  log "WARNING: internal checkout is dirty — carving the WORKING TREE, not a clean HEAD:"
  git status --short | sed 's/^/[oss-carve]   /'
fi

# Clear stale worktree registrations (e.g. deleted /tmp/orcha-public).
git worktree prune
log "worktree prune done"

# ---------------------------------------------------------------- carve ----
TARGET="$WORKTREE"
TMPDIR_CARVE=""
if [[ "$DRY_RUN" == true ]]; then
  TMPDIR_CARVE="$(mktemp -d /tmp/oss-carve-dryrun.XXXXXX)"
  TARGET="$TMPDIR_CARVE"
  trap 'rm -rf "$TMPDIR_CARVE"' EXIT
  log "dry-run: carving into $TARGET (worktree untouched)"
fi

# Filter semantics (rsync 3.x — 'HP' combined is rejected, two rules needed):
# - 'H .git' + 'P .git' hides .git from the transfer AND protects the
#   worktree's own .git (a FILE/gitfile in a worktree, not a dir).
# - '--delete-excluded' removes destination files that match any exclude —
#   without it, plain --delete PROTECTS excluded paths, so stale private dirs
#   (.superpowers/, docs-local/) or a leftover .venv in the worktree would
#   survive the carve.
# - the dir-merge filter honors .gitignore so node_modules/.venv/build output
#   is neither transferred nor kept on the destination.
# - rsync --exclude-from has NO gitignore-style '!' negation: translate `!path`
#   lines into include filters placed BEFORE the exclude file (first match
#   wins), so e.g. .env.example survives the `.env.*` exclusion.
INCLUDE_FILTERS=()
while IFS= read -r line; do
  [[ "$line" == '!'* ]] && INCLUDE_FILTERS+=("--filter=+ ${line#!}")
done < "$EXCLUDES"

RSYNC_BASE=(-a --delete --delete-excluded
  "--filter=H .git"
  "--filter=P .git"
  ${INCLUDE_FILTERS[@]+"${INCLUDE_FILTERS[@]}"}
  "--exclude-from=$EXCLUDES"
  "--filter=:- .gitignore")

if command -v rsync >/dev/null 2>&1; then
  log "carve: rsync $ROOT/ -> $TARGET/"
  rsync "${RSYNC_BASE[@]}" "$ROOT/" "$TARGET/"
else
  # Fallback: tar pipe. NOTE: tar has no gitignore negation support, so the
  # !.env.example / !.env.sandbox.example includes are re-applied manually.
  log "carve: rsync not found, using tar fallback"
  TAR_EXCLUDES="$(mktemp /tmp/oss-carve-excludes.XXXXXX)"
  trap 'rm -f "$TAR_EXCLUDES"; [[ -n "$TMPDIR_CARVE" ]] && rm -rf "$TMPDIR_CARVE" || true' EXIT
  grep -v -e '^\s*#' -e '^\s*$' -e '^!' "$EXCLUDES" | sed 's|^/||' > "$TAR_EXCLUDES" || true
  # Mirror semantics: clear the destination (except its .git gitfile) first.
  find "$TARGET" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
  (cd "$ROOT" && tar --exclude=.git --exclude-from="$TAR_EXCLUDES" -cf - .) \
    | tar -xf - -C "$TARGET"
  for keep in .env.example .env.sandbox.example; do
    (cd "$ROOT" && find . -name "$keep" -not -path './.git/*' -print0) \
      | while IFS= read -r -d '' f; do
          mkdir -p "$TARGET/$(dirname "$f")"
          cp "$ROOT/$f" "$TARGET/$f"
        done
  done
  rm -f "$TAR_EXCLUDES"
fi

# ----------------------------------------------------------- brand sweep ----
log "brand sweep: metaorcha (all paths) + legacy DIDs (non-test paths)"
# This script itself contains the patterns (it IS the scanner) — exclude it
# from the sweep so the gate doesn't trip on its own definition.
HITS="$(grep -rniI -e 'metaorcha' \
  --exclude=.git --exclude-dir=.git --exclude=oss-carve.sh "$TARGET" || true)"

RESIDUAL="$HITS"
for allow in "${ALLOWLIST[@]}"; do
  if [[ -n "$RESIDUAL" ]]; then
    RESIDUAL="$(printf '%s\n' "$RESIDUAL" | grep -v -F -i "$allow" || true)"
  fi
done
# File-scoped allowlist: rule text quoting the banned name (AGENTS.md, .cursor).
for allow_file in "${ALLOWLIST_FILES[@]}"; do
  if [[ -n "$RESIDUAL" ]]; then
    RESIDUAL="$(printf '%s\n' "$RESIDUAL" | grep -v -F "$allow_file" || true)"
  fi
done

# Legacy DID prefixes are banned everywhere EXCEPT test fixtures — the
# did:emerge: fixture migration is scheduled for 0.2 (load-bearing tests).
DID_HITS="$(grep -rniI -e 'did:emerge:' -e 'did:metaorcha:' \
  --exclude=.git --exclude-dir=.git --exclude=oss-carve.sh "$TARGET" \
  | grep -v -E '/(tests?|fixtures)/' || true)"
for allow_file in "${ALLOWLIST_FILES[@]}"; do
  if [[ -n "$DID_HITS" ]]; then
    DID_HITS="$(printf '%s\n' "$DID_HITS" | grep -v -F "$allow_file" || true)"
  fi
done
if [[ -n "$DID_HITS" ]]; then
  RESIDUAL="$(printf '%s\n%s\n' "${RESIDUAL:-}" "$DID_HITS")"
fi

if [[ -n "$HITS" ]]; then
  ALLOWED_COUNT=$(($(printf '%s\n' "$HITS" | wc -l) - $(printf '%s\n' "${RESIDUAL:-}" | grep -c . || true)))
  log "brand sweep: $ALLOWED_COUNT allowlisted hit(s) (informational):"
  if [[ -n "$RESIDUAL" ]]; then
    printf '%s\n' "$HITS" | grep -i -F -f <(printf '%s\n' "${ALLOWLIST[@]}") \
      | sed 's/^/[oss-carve]   allow: /' | head -20 || true
  else
    printf '%s\n' "$HITS" | sed 's/^/[oss-carve]   allow: /' | head -20
  fi
fi

SWEEP_OK=true
if [[ -n "${RESIDUAL:-}" ]] && printf '%s' "$RESIDUAL" | grep -q .; then
  SWEEP_OK=false
  echo "[oss-carve] brand sweep RESIDUAL HITS (not allowlisted):" >&2
  printf '%s\n' "$RESIDUAL" | sed 's/^/[oss-carve]   HIT: /' >&2
fi

# ------------------------------------------------------------- gitleaks ----
if command -v gitleaks >/dev/null 2>&1; then
  GL_MAJOR="$(gitleaks version 2>/dev/null | grep -oE '[0-9]+' | head -1 || echo 0)"
  log "gitleaks v${GL_MAJOR} found — scanning carved tree"
  if [[ "${GL_MAJOR:-0}" -ge 8 ]]; then
    gitleaks dir "$TARGET" --config "$ROOT/.gitleaks.toml" --no-banner \
      || fail "gitleaks reported findings in carved tree"
  else
    gitleaks detect --no-git --source "$TARGET" --config "$ROOT/.gitleaks.toml" --no-banner \
      || fail "gitleaks reported findings in carved tree"
  fi
  log "gitleaks: no findings"
else
  log "SKIP: gitleaks not on PATH — secret scan skipped locally (CI runs gitleaks on every PR)"
fi

# ---------------------------------------------- excluded-paths assertion ----
log "verifying private paths are absent from the carved tree"
NEGATIONS=()
EXCL_OK=true
while IFS= read -r line; do
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ -z "${line//[[:space:]]/}" ]] && continue
  if [[ "$line" == !* ]]; then
    NEGATIONS+=("${line#!}")
    continue
  fi
  pattern="$line"
  if [[ "$pattern" == *'*'* ]]; then
    # Glob pattern (e.g. *.docx, kimi*/) — assert no basename match remains,
    # ignoring explicitly negated names like .env.example.
    found="$(find "$TARGET" -name "${pattern%/}" -not -path '*/.git/*' \
      $(printf -- '-not -name %s ' "${NEGATIONS[@]}") -print -quit 2>/dev/null || true)"
    if [[ -n "$found" ]]; then
      echo "[oss-carve]   PRESENT (glob $pattern): $found" >&2
      EXCL_OK=false
    fi
  else
    if [[ -e "$TARGET/${pattern%/}" ]]; then
      echo "[oss-carve]   PRESENT: ${pattern}" >&2
      EXCL_OK=false
    fi
  fi
done < "$EXCLUDES"
if [[ "$EXCL_OK" == true ]]; then
  log "excluded-paths verification: all private paths absent"
fi

# Negated entries (e.g. .env.example) must be PRESENT somewhere in the carved
# tree — an over-broad exclude that drops them is a carve bug (caught v0.1.0).
for neg in "${NEGATIONS[@]}"; do
  found="$(find "$TARGET" -name "$neg" -not -path '*/.git/*' -print -quit 2>/dev/null || true)"
  if [[ -z "$found" ]]; then
    echo "[oss-carve]   MISSING required file (negated from excludes): $neg" >&2
    EXCL_OK=false
  fi
done

# ---------------------------------------------------------------- summary ---
FILE_COUNT="$(find "$TARGET" -type f -not -path '*/.git/*' -not -name '.git' | wc -l)"
log "summary: $FILE_COUNT files carved into $TARGET"

if [[ "$DRY_RUN" == true ]]; then
  CHANGED="$(diff -qr "$TARGET" "$WORKTREE" --exclude=.git --exclude=node_modules \
    --exclude=.venv 2>/dev/null | wc -l || true)"
  log "summary: $CHANGED path(s) would differ vs $WORKTREE (dry-run, nothing changed)"
else
  log "summary: diff stat vs worktree's previous state (tracked files):"
  git -C "$WORKTREE" diff --stat | tail -5 | sed 's/^/[oss-carve]   /' || true
  UNTRACKED="$(git -C "$WORKTREE" status --porcelain | grep -c '^??' || true)"
  log "summary: $UNTRACKED untracked path(s) in worktree"
fi

[[ "$EXCL_OK" == true ]] || fail "private paths present in carved tree (see above)"
if [[ "$SWEEP_OK" != true ]]; then
  fail "brand sweep failed — residual non-allowlisted hits listed above; controller decides"
fi

if [[ "$DRY_RUN" == true ]]; then
  log "DRY-RUN PASS (nothing changed)"
else
  log "PASS — carve complete; commit/push in the worktree is the controller's job"
fi
