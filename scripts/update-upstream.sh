#!/usr/bin/env bash
# Bump UPSTREAM_REF to the latest upstream master commit, re-prepare the working
# copy, and verify our patches still apply. Reports conflicts if they don't.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/.work"
UPSTREAM_REPO="${UPSTREAM_REPO:-https://github.com/TeamPiped/Piped.git}"
BRANCH="${UPSTREAM_BRANCH:-master}"

echo ">> Fetching latest $BRANCH from $UPSTREAM_REPO"
NEW_REF="$(git ls-remote "$UPSTREAM_REPO" "refs/heads/$BRANCH" | cut -f1)"
OLD_REF="$(tr -d '[:space:]' < "$ROOT/UPSTREAM_REF")"

if [ -z "$NEW_REF" ]; then
    echo "ERROR: could not resolve $BRANCH" >&2
    exit 1
fi

echo "   old: $OLD_REF"
echo "   new: $NEW_REF"

if [ "$NEW_REF" = "$OLD_REF" ]; then
    echo ">> Already up to date."
    exit 0
fi

echo "$NEW_REF" > "$ROOT/UPSTREAM_REF"

echo ">> Re-preparing working copy against new ref"
if "$ROOT/scripts/prepare.sh"; then
    echo ">> SUCCESS: patches apply cleanly against $NEW_REF"
    echo "   Test with: cd .work && pnpm install && pnpm dev"
    echo "   Then rebuild the image and bump the Dockerfile default UPSTREAM_REF if desired."
else
    echo "!! Patches did NOT apply cleanly against $NEW_REF." >&2
    echo "   Resolve manually:" >&2
    echo "     1. ./scripts/prepare.sh may have left .work/ partially patched." >&2
    echo "     2. Re-apply edits by hand inside .work/, then ./scripts/regen-patch.sh" >&2
    echo "   UPSTREAM_REF has been updated to $NEW_REF; revert it if you abort." >&2
    exit 1
fi
