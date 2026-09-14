#!/usr/bin/env bash
# org-publish: orgmode/handbook/*.org → handbook/*.html
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
emacs --batch -l "$ROOT/org/export.el"
python3 "$ROOT/scripts/build-search-index.py"
