#!/usr/bin/env bash
# Commit and push kalshi/data.json if (and only if) the fetch changed it.
# Run by .github/workflows/kalshi.yml after the fetch step. Prints exactly one
# result line: "No changes: ..." when nothing was committed, or the new
# commit's hash when it committed and pushed.
set -euo pipefail

DATA_FILE="kalshi/data.json"

if git diff --quiet -- "$DATA_FILE"; then
    echo "No changes: $DATA_FILE is identical, nothing committed."
    exit 0
fi

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add "$DATA_FILE"
git commit --quiet -m "Update Kalshi dashboard data"
git push --quiet
echo "Committed $DATA_FILE as $(git rev-parse --short HEAD) and pushed."
