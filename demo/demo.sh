#!/usr/bin/env bash
[ -z "${DEMO_CLEAN:-}" ] && exec env -i DEMO_CLEAN=1 TERM=xterm-256color HOME="$HOME" DEMO_BIN="${DEMO_BIN:-$HOME/.cargo/bin}" bash "$0" "$@"
# A real ljos session in a scratch seat. Commands are typed by this script; every output is real.
set -u
S=/tmp/ljos-demo
REAL_HOME=$HOME
export HOME=$S/home VISSUE_ROOT=$S/tracker DEEDAR_URL=file://$S/deeds CLAIMDAG_DIR=$S/claims
export PACKSET_URL=http://127.0.0.1:18797 PACKSET_EMBED_CACHE="$REAL_HOME/.cache/packset/embed"
export LJOS_SEAT=you LJOS_TRACKER_GIT=commit GIT_AUTHOR_NAME=you GIT_AUTHOR_EMAIL=you@example.org
export GIT_COMMITTER_NAME=you GIT_COMMITTER_EMAIL=you@example.org
export PATH="$DEMO_BIN:$REAL_HOME/.cargo/bin:/usr/bin:/bin"
cd $S/work
type_run() {
  local cmd="$1"
  printf '\033[33m$\033[0m '
  for ((i = 0; i < ${#cmd}; i++)); do printf '%s' "${cmd:i:1}"; sleep 0.035; done
  sleep 0.5; printf '\n'
  eval "$cmd"
  sleep "${2:-2.2}"
}
say() { printf '\033[2m# %s\033[0m\n' "$1"; sleep 1.4; }
clear
say "Write a memory only when you mean it."
type_run 'ljos remember "Never force push to main. Open a pull request instead."'
type_run 'ljos prefer "Run cargo test before every push."'
say "Search it back. A hook does this on every prompt."
type_run 'ljos search "push to main" -n 3' 3
say "The same rules gate shell commands, with no model in the loop."
type_run 'ljos policy -- git push --force origin main' 3
say "Tracked work: open a ticket and sit on it."
type_run 'id=$(vissue q -p demo "Ship the fuse change")' 0.6
say "(doctor and sync rows trimmed to fit the screen)"
type_run 'ljos sitting $id 2>&1 | sed -n "/^== due/,\$p" | grep -v "^ *$" | head -24' 5
type_run 'ljos note $id "fuse patch drafted; tests pass"' 1.8
type_run 'deedar create file --name "the fuse patch" --path fuse.patch --agent you' 1.8
type_run 'ljos deed $id --add deed-file-the-fuse-patch' 1.8
type_run 'ljos finish $id --lesson "The fuse change shipped as one patch. cargo test caught nothing new." 2>&1 | tee $S/finish.out | grep -v "^sync:"' 3
say "A lesson an agent wrote waits for you to accept it."
type_run "ljos accept $(awk '/^proposed/{print $2}' $S/finish.out)" 2.2
type_run 'ljos search "fuse change" -n 2' 4
