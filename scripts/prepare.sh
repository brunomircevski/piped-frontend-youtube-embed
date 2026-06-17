#!/usr/bin/env bash
# Prepare a local working copy of upstream Piped with our overlay + patches applied.
# Result lands in .work/ and is ready for `pnpm install && pnpm dev`.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/.work"
UPSTREAM_REPO="${UPSTREAM_REPO:-https://github.com/TeamPiped/Piped.git}"
UPSTREAM_REF="$(tr -d '[:space:]' < "$ROOT/UPSTREAM_REF")"

echo ">> Upstream: $UPSTREAM_REPO @ $UPSTREAM_REF"

rm -rf "$WORK"
git clone --quiet "$UPSTREAM_REPO" "$WORK"
git -C "$WORK" fetch --quiet --depth 1 origin "$UPSTREAM_REF"
git -C "$WORK" checkout --quiet FETCH_HEAD

echo ">> Copying overlay files"
cp -a "$ROOT/overlay/." "$WORK/"

echo ">> Applying patches"
for p in "$ROOT"/patches/*.patch; do
    [ -e "$p" ] || continue
    echo "   - $(basename "$p")"
    git -C "$WORK" apply --whitespace=nowarn "$p"
done

echo ">> Done. Next:"
echo "   cd .work && pnpm install && pnpm dev"
