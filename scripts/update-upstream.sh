#!/usr/bin/env bash
# Merge the latest upstream TeamPiped/Piped master into frontend/ (git subtree).
# Conflicts, if any, show up as normal merge conflicts in frontend/.
set -euo pipefail

cd "$(dirname "$0")/.."
UPSTREAM_REPO="${UPSTREAM_REPO:-https://github.com/TeamPiped/Piped.git}"
BRANCH="${UPSTREAM_BRANCH:-master}"

git subtree pull --prefix=frontend "$UPSTREAM_REPO" "$BRANCH" --squash \
    -m "Merge upstream Piped $BRANCH into frontend/"
