#!/usr/bin/env bash
# Publish tree for Cloudflare Pages. Does not ship .git or Emacs source.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
bash "$ROOT/org/build.sh"
DEST="$ROOT/public"
if [[ -d "$DEST" ]]; then
  rtrash -rf "$DEST"
fi
mkdir -p "$DEST"
rsync -a \
  --exclude '.git/' \
  --exclude '.gitignore' \
  --exclude 'org/' \
  --exclude 'orgmode/' \
  --exclude 'public/' \
  --exclude 'sphinx/' \
  --exclude '.venv/' \
  --exclude '*.org' \
  "$ROOT/" "$DEST/"
printf '%s\n' 'leidarljos.rgoswami.me' > "$DEST/CNAME"
echo "assembled $DEST"
