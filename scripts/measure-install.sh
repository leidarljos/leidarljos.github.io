#!/usr/bin/env bash
# Measure a default install of ljos and packset from crates.io on this machine.
#
#   scripts/measure-install.sh OUTDIR [JOBS]
#
# Builds in a fresh CARGO_HOME and target directory, so nothing is reused from an
# earlier build. Writes every raw number to OUTDIR, plus summary.txt. The encoder
# (packset-embed) is not part of this install, so search runs lexical, as it does
# for anyone who runs the two install lines.
set -euo pipefail
out=$(realpath -m "${1:?usage: measure-install.sh OUTDIR [JOBS]}")
jobs=${2:-2}
mkdir -p "$out"
tmp=$(mktemp -d /tmp/ljos-measure.XXXXXX)
export CARGO_HOME="$tmp/cargo" CARGO_TARGET_DIR="$tmp/target"
root="$tmp/root"
port=${MEASURE_PORT:-8799}

{
  echo "date: $(date -Is)"
  echo "host: $(uname -srm)"
  echo "cpu: $(lscpu | sed -n 's/^Model name: *//p') ($(nproc) threads)"
  echo "mem: $(free -g | awk '/^Mem:/{print $2" GB total, "$7" GB available"}')"
  echo "rustc: $(rustc --version)"
  echo "cargo: $(cargo --version)"
  echo "jobs: $jobs"
} | tee "$out/env.txt"

# 1. Install time, one crate after the other, from crates.io.
for crate in ljos packset; do
  /usr/bin/time -v -o "$out/time-$crate.txt" \
    cargo install --locked --root "$root" -j "$jobs" "$crate" >"$out/install-$crate.log" 2>&1
done

# 2. Binary sizes, as installed (cargo's release profile, not stripped further).
ls -l "$root/bin" | tee "$out/sizes.txt"

# 3. A scratch writer with only the fresh binaries on PATH.
export PATH="$root/bin:/usr/bin:/bin" HOME="$tmp/home" PACKSET_HOME="$tmp/pack"
export PACKSET_URL="http://127.0.0.1:$port"
mkdir -p "$HOME" "$PACKSET_HOME"
"$root/bin/packsetd" --port "$port" --home "$PACKSET_HOME" >"$out/packsetd.log" 2>&1 &
pid=$!
trap 'kill $pid 2>/dev/null || true; mv "$tmp" "$tmp.done"' EXIT
for _ in $(seq 50); do curl -fs "$PACKSET_URL/health" >/dev/null 2>&1 && break; sleep 0.2; done
rss() { awk '/^VmRSS/{print $2}' "/proc/$pid/status"; }
echo "rss_idle_kb $(rss)" | tee "$out/rss.txt"

# 4. Seed the pack with sentences from this site's own pages (public text).
here=$(cd "$(dirname "$0")/.." && pwd)
python3 - "$here/search-index.json" "${SEED:-1000}" >"$tmp/claims.txt" <<'PY'
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
n=0; t0=$(date +%s.%N)
while IFS= read -r line; do
  packset remember --workspace measure "$line" >/dev/null 2>>"$out/seed.err" && n=$((n+1))
done <"$tmp/claims.txt"
t1=$(date +%s.%N)
echo "seeded $n claims in $(awk "BEGIN{printf \"%.1f\", $t1 - $t0}") s" | tee "$out/seed.txt"
packset status measure >>"$out/seed.txt" 2>&1 || true
echo "rss_seeded_kb $(rss)" | tee -a "$out/rss.txt"

# 5. Search latency: one `packset search` process per query, as a hook pays it.
queries=(fuse "search it back" tracker "policy gate" "force push" sitting deed
         "remember a lesson" consensus "what blocks this" encoder island
         "review clock" handbook install)
for _ in 1 2; do for q in "${queries[@]}"; do packset search --workspace measure "$q" >/dev/null; done; done
: >"$out/latency-us.txt"
for round in $(seq 20); do
  for q in "${queries[@]}"; do
    a=$(date +%s%N); packset search --workspace measure "$q" >/dev/null; b=$(date +%s%N)
    echo $(( (b - a) / 1000 )) >>"$out/latency-us.txt"
  done
done
echo "rss_after_search_kb $(rss)" | tee -a "$out/rss.txt"

python3 "$here/scripts/measure-summary.py" "$out" | tee "$out/summary.txt"
