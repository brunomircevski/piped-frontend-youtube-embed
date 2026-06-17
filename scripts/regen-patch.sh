#!/usr/bin/env bash
# Regenerate patches/piped-youtube-embed.patch from the current state of .work/.
#
# Workflow:
#   1. ./scripts/prepare.sh           (or manually clone upstream into .work/)
#   2. edit existing files inside .work/ (NOT the overlay/ ones)
#   3. ./scripts/regen-patch.sh
#
# The patch only captures changes to files that already exist upstream. Brand-new
# files belong in overlay/ and must NOT be tracked by the patch.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/.work"
OUT="$ROOT/patches/piped-youtube-embed.patch"

if [ ! -d "$WORK/.git" ]; then
    echo "ERROR: .work/ not found. Run ./scripts/prepare.sh first." >&2
    exit 1
fi

mkdir -p "$ROOT/patches"

# Build a list of files we own via overlay/ so we can exclude them from the diff.
EXCLUDES=()
while IFS= read -r f; do
    rel="${f#"$ROOT"/overlay/}"
    EXCLUDES+=(":(exclude)$rel")
done < <(find "$ROOT/overlay" -type f)

echo ">> Generating $OUT"
git -C "$WORK" diff -- . "${EXCLUDES[@]}" > "$OUT"

echo ">> Patch summary:"
git -C "$WORK" diff --stat -- . "${EXCLUDES[@]}"
