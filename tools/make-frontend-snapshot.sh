#!/usr/bin/env bash
#
# make-frontend-snapshot.sh — create a redacted, scanned snapshot of the
# frontend working tree for publishing to the relay.
#
# Why this exists: publishing raw frontend trees repeatedly tripped GitHub
# push protection on `sk_test_...` fixture keys (a false positive). This tool
# produces a snapshot from tracked files only (so node_modules/, .next/ and any
# .env* never leak in), redacts test-key literals in the relay copy, and runs a
# secret scan so a round never hits push protection again.
#
# Usage:
#   [SNAPSHOT_ROOT=...] [FORCE=1] bash tools/make-frontend-snapshot.sh [TREE_PATH]
#
set -euo pipefail

# --- locate relay root relative to this script ---------------------------------
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
RELAY_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

# --- inputs --------------------------------------------------------------------
TREE=${1:-/home/aika/.qwenpaw/workspaces/default/work/c2-clerk-login-20260910}

if [ ! -d "$TREE/.git" ] && ! git -C "$TREE" rev-parse --git-dir >/dev/null 2>&1; then
  echo "ERROR: '$TREE' is not a git working tree" >&2
  exit 1
fi

SHORT=$(git -C "$TREE" rev-parse HEAD | cut -c1-8)

# SNAPSHOT_ROOT is overridable (for testing without touching the real snapshots/)
SNAPSHOT_ROOT=${SNAPSHOT_ROOT:-$RELAY_ROOT/snapshots}
DEST="$SNAPSHOT_ROOT/frontend-$SHORT"

# --- refuse to clobber an already-published snapshot ---------------------------
if [ -e "$DEST" ] && [ "${FORCE:-0}" != "1" ]; then
  echo "ERROR: destination already exists: $DEST" >&2
  echo "       refusing to overwrite a published snapshot (set FORCE=1 to override)" >&2
  exit 1
fi

echo "Frontend tree : $TREE"
echo "HEAD (short)  : $SHORT"
echo "Snapshot dest : $DEST"

# --- export tracked files only -------------------------------------------------
# `git archive HEAD` emits ONLY tracked files at HEAD, so untracked/ignored
# paths (node_modules/, .next/, .env*, build caches) are excluded by construction.
mkdir -p "$DEST"
git -C "$TREE" archive --format=tar HEAD | tar -x -C "$DEST"

# --- redact test-key literals in the RELAY COPY ONLY ---------------------------
# Replace `sk_test_` followed by 10+ alphanumeric chars with a fixed placeholder.
# Report file:line and the ORIGINAL match length only — never the matched value.
echo "--- redaction (relay copy only) ---"
KEY_RE='sk_test_[A-Za-z0-9]{10,}'
redacted=0
while IFS= read -r hit; do
  [ -n "$hit" ] || continue
  file=${hit%%:*}; rest=${hit#*:}
  lineno=${rest%%:*}; match=${rest#*:}
  echo "  redacted $file:$lineno (original match length ${#match})"
  redacted=$((redacted + 1))
done < <(grep -rIn -oE "$KEY_RE" "$DEST" || true)

# apply the replacement in place across any matching files
while IFS= read -r f; do
  [ -n "$f" ] || continue
  perl -i -pe 's/sk_test_[A-Za-z0-9]{10,}/sk_test_FIXTURE_REDACTED/g' "$f"
done < <(grep -rIlE "$KEY_RE" "$DEST" || true)
echo "  redacted $redacted occurrence(s)"

# --- secret scan over the new snapshot -----------------------------------------
# Print counts and file:line locations only — never the matched values.
echo "--- secret scan ---"
SCAN_RE='sk_live|BEGIN PRIVATE KEY|AKIA|ghp_|postgres://'
scan_count=0
while IFS= read -r hit; do
  [ -n "$hit" ] || continue
  file=${hit%%:*}; rest=${hit#*:}; lineno=${rest%%:*}
  echo "  match $file:$lineno"
  scan_count=$((scan_count + 1))
done < <(grep -rIn -E "$SCAN_RE" "$DEST" || true)
echo "  scan matches: $scan_count"
echo "  NOTE: pre-existing pattern literals in services/rag/*redact*, their tests,"
echo "        and the docs are known false positives."

# --- summary -------------------------------------------------------------------
file_count=$(find "$DEST" -type f | wc -l | tr -d ' ')
echo "--- summary ---"
echo "Snapshot path : $DEST"
echo "File count    : $file_count"
