#!/usr/bin/env bash
# Measure a default install of ljos and packset from crates.io on this machine.
#
#   scripts/measure-install.sh OUTDIR [JOBS] [DRAWS]
#
# Each draw installs both crates into a fresh prefix. Every build gets its own fresh
# CARGO_HOME and target directory, so it pays its own index and source downloads and
# reuses nothing. The build order runs ABBA across draws (ljos first, packset first,
# packset first, ljos first, ...), so drift on a shared box falls on both crates alike.
# Each draw then starts its own packsetd, seeds the same claims and times one fresh
# `packset search` process per query. The encoder (packset-embed) is not part of this
# install, so search runs lexical, as it does for anyone who runs the two install lines.
# Raw files go to OUTDIR/draw-N/, each opening with "# " lines that name the run, the
# command, the UTC date, the host and CPU, n and the draw index. OUTDIR/summary.txt
# gives median and IQR over the draws.
set -euo pipefail
usage="usage: measure-install.sh OUTDIR [JOBS] [DRAWS]"
out=$(realpath -m "${1:?$usage}")
jobs=${2:-2}
# Six draws is the smallest n the site's measurement rule accepts for a median and IQR.
draws=${3:-6}
mkdir -p "$out"
here=$(cd "$(dirname "$0")/.." && pwd)
run="scripts/measure-install.sh $1 $jobs $draws"
work=$(mktemp -d /tmp/ljos-measure.XXXXXX)
port=${MEASURE_PORT:-8799}
host="$(uname -srm)"
cpu="$(lscpu | sed -n 's/^Model name: *//p') ($(nproc) threads)"
trap 'rm -rf "$work"' EXIT

header() { # FILE DRAW COMMAND
  {
    echo "# run: $run"
    echo "# command: $3"
    echo "# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "# host: $host"
    echo "# cpu: $cpu"
    echo "# n: $draws draws"
    echo "# draw: $2 of $draws"
  } >"$1"
}

# Seed claims: sentences from this site's own pages (public text), taken once so every
# draw seeds the same pack.
python3 - "$here/search-index.json" "${SEED:-1000}" >"$work/claims.txt" <<'PY'
import json, re, sys
docs = json.load(open(sys.argv[1]))["docs"]
seen, out = set(), []
for d in docs:
    for s in re.split(r"(?<=[.!?])\s+", d["text"]):
        s = s.strip()
        if 40 <= len(s) <= 220 and s not in seen:
            seen.add(s); out.append(s)
print("\n".join(out[: int(sys.argv[2])]))
PY

header "$out/env.txt" all "environment of the run"
{
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "host: $host"
  echo "cpu: $cpu"
  echo "mem: $(free -g | awk '/^Mem:/{print $2" GB total, "$7" GB available"}')"
  echo "rustc: $(rustc --version)"
  echo "cargo: $(cargo --version)"
  echo "jobs: $jobs"
  echo "draws: $draws"
  echo "seed claims offered: $(wc -l <"$work/claims.txt")"
} | tee -a "$out/env.txt"

queries=(fuse "search it back" tracker "policy gate" "force push" sitting deed
         "remember a lesson" consensus "what blocks this" encoder island
         "review clock" handbook install)

for d in $(seq "$draws"); do
  dir="$out/draw-$d"
  tmp="$work/draw-$d"
  root="$tmp/root"
  mkdir -p "$dir" "$tmp"
  case $(( (d - 1) % 4 )) in 0|3) order="ljos packset" ;; *) order="packset ljos" ;; esac

  # 1. Install time from crates.io, each crate from a clean cache.
  for crate in $order; do
    cmd="cargo install --locked --root $root -j $jobs $crate"
    header "$dir/time-$crate.txt" "$d" "/usr/bin/time -v $cmd (order: $order)"
    header "$dir/install-$crate.log" "$d" "$cmd (order: $order)"
    CARGO_HOME="$tmp/cargo-$crate" CARGO_TARGET_DIR="$tmp/target-$crate" \
      /usr/bin/time -v -a -o "$dir/time-$crate.txt" $cmd >>"$dir/install-$crate.log" 2>&1
    rm -rf "$tmp/target-$crate" "$tmp/cargo-$crate"
  done

  # 2. Binary sizes, as installed (cargo's release profile, not stripped further).
  header "$dir/sizes.txt" "$d" "ls -l $root/bin"
  ls -l "$root/bin" | tee -a "$dir/sizes.txt"

  # 3. A scratch writer with only the fresh binaries on PATH.
  (
    export PATH="$root/bin:/usr/bin:/bin" HOME="$tmp/home" PACKSET_HOME="$tmp/pack"
    export PACKSET_URL="http://127.0.0.1:$port"
    mkdir -p "$HOME" "$PACKSET_HOME"
    header "$dir/packsetd.log" "$d" "packsetd --port $port --home $PACKSET_HOME"
    "$root/bin/packsetd" --port "$port" --home "$PACKSET_HOME" >>"$dir/packsetd.log" 2>&1 &
    pid=$!
    trap 'kill $pid 2>/dev/null; wait $pid 2>/dev/null || true' EXIT
    for _ in $(seq 50); do curl -fs "$PACKSET_URL/health" >/dev/null 2>&1 && break; sleep 0.2; done
    rss() { awk '/^VmRSS/{print $2}' "/proc/$pid/status"; }
    header "$dir/rss.txt" "$d" "VmRSS of packsetd from /proc/PID/status, kB"
    echo "rss_idle_kb $(rss)" | tee -a "$dir/rss.txt"

    # 4. Seed the pack.
    header "$dir/seed.txt" "$d" "packset remember --workspace measure CLAIM, one per claim; packset status measure"
    header "$dir/seed.err" "$d" "stderr of packset remember"
    n=0; t0=$(date +%s.%N)
    while IFS= read -r line; do
      packset remember --workspace measure "$line" >/dev/null 2>>"$dir/seed.err" && n=$((n+1))
    done <"$work/claims.txt"
    t1=$(date +%s.%N)
    echo "seeded $n claims in $(awk "BEGIN{printf \"%.1f\", $t1 - $t0}") s" | tee -a "$dir/seed.txt"
    packset status measure >>"$dir/seed.txt" 2>&1 || true
    echo "rss_seeded_kb $(rss)" | tee -a "$dir/rss.txt"

    # 5. Search latency: one `packset search` process per query, as a hook pays it.
    for _ in 1 2; do for q in "${queries[@]}"; do packset search --workspace measure "$q" >/dev/null; done; done
    header "$dir/latency-us.txt" "$d" \
      "packset search --workspace measure QUERY, one process per query, ${#queries[@]} queries x 20 rounds after 2 warm-up rounds, wall us"
    for round in $(seq 20); do
      for q in "${queries[@]}"; do
        a=$(date +%s%N); packset search --workspace measure "$q" >/dev/null; b=$(date +%s%N)
        echo $(( (b - a) / 1000 )) >>"$dir/latency-us.txt"
      done
    done
    echo "rss_after_search_kb $(rss)" | tee -a "$dir/rss.txt"
  )
  rm -rf "$tmp"
done

python3 "$here/scripts/measure-summary.py" "$out" | tee "$out/summary.txt"
