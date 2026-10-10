#!/usr/bin/env bash
# Fresh scratch seat for demo.sh; moves an old one aside instead of deleting it.
set -eu
S=/tmp/ljos-demo
[ -e $S ] && mv $S $S.old.$(date +%s)
mkdir -p $S/home $S/tracker/Software $S/deeds $S/claims $S/work $S/pack
cd $S/tracker && git init -q && git -c user.name=you -c user.email=you@example.org commit -q --allow-empty -m init
cd $S/work && printf 'fuse = "combmnz"\n' > fuse.patch
PACKSET_EMBED_CACHE="$HOME/.cache/packset/embed" nohup "${DEMO_BIN:-$HOME/.cargo/bin}/packsetd" --port 18797 --home $S/pack > $S/packsetd.log 2>&1 &
echo $! > $S/packsetd.pid
for _ in $(seq 50); do curl -fs http://127.0.0.1:18797/health >/dev/null && break; sleep 0.2; done
echo ready
