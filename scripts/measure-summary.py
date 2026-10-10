#!/usr/bin/env python3
"""Summarise one measure-install.sh run: scripts/measure-summary.py OUTDIR"""
import pathlib, re, statistics, sys
out = pathlib.Path(sys.argv[1])
def wall(p):
    t = re.search(r"Elapsed \(wall clock\) time.*: (.+)", p.read_text()).group(1)
    parts = [float(x) for x in t.split(":")]
    s = sum(v * 60 ** i for i, v in enumerate(reversed(parts)))
    rss = int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", p.read_text()).group(1))
    return s, rss
for c in ("ljos", "packset"):
    s, r = wall(out / f"time-{c}.txt")
    print(f"install {c}: {s:.0f} s wall, largest single build process {r/1024:.0f} MB RSS")
for line in (out / "sizes.txt").read_text().splitlines()[1:]:
    f = line.split()
    print(f"binary {f[-1]}: {int(f[4])/1e6:.1f} MB")
for line in (out / "rss.txt").read_text().splitlines():
    k, v = line.split()
    print(f"packsetd {k[:-3]}: {int(v)/1024:.1f} MB")
us = sorted(int(x) for x in (out / "latency-us.txt").read_text().split())
q = lambda p: us[min(len(us) - 1, int(p * len(us)))] / 1000
print(f"search (lexical, one process per query, n={len(us)}): p50 {q(0.5):.1f} ms, p95 {q(0.95):.1f} ms")
print((out / "seed.txt").read_text().splitlines()[0])
import json
st = (out / "seed.txt").read_text()
live = json.loads(st[st.index("{"):st.rindex("}") + 1])["live"]
print(f"pack size during the search runs: {live} live claims")
