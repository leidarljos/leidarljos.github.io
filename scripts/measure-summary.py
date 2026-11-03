#!/usr/bin/env python3
"""Summarise one measure-install.sh run: scripts/measure-summary.py OUTDIR

Median and IQR are linear quartiles, statistics.quantiles(method="inclusive"), the
same estimator as numpy's default. The p95 is that estimator at 0.95. Memory is kB
from the kernel over 1024, so MiB; binary sizes are bytes over 10**6, so MB.
"""
import json, pathlib, re, statistics, sys

out = pathlib.Path(sys.argv[1])
draws = sorted(out.glob("draw-*"), key=lambda p: int(p.name.split("-")[1]))


def body(p):
    return [l for l in p.read_text(errors="replace").splitlines() if not l.startswith("# ")]


def head(p, key):
    return next(l for l in p.read_text().splitlines() if l.startswith(f"# {key}: "))[len(key) + 4 :]


def quartiles(xs):
    return statistics.quantiles(xs, n=4, method="inclusive") if len(xs) > 1 else [xs[0]] * 3


def stat(xs, fmt, unit=""):
    q1, med, q3 = quartiles(xs)
    u = f" {unit}" if unit else ""
    return f"median {med:{fmt}}{u} (IQR {q1:{fmt}}-{q3:{fmt}}{u}), n={len(xs)}"


def wall(p):
    text = "\n".join(body(p))
    t = re.search(r"Elapsed \(wall clock\) time.*: (.+)", text).group(1)
    s = sum(float(v) * 60**i for i, v in enumerate(reversed(t.split(":"))))
    rss = int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", text).group(1))
    return s, rss / 1024


env = {k: v for k, v in (l.split(": ", 1) for l in body(out / "env.txt"))}
first = {d.name[5:]: re.search(r"\(order: (\S+)", head(d / "time-ljos.txt", "command"))[1] for d in draws}
led = {c: ", ".join(k for k, v in first.items() if v == c) for c in ("ljos", "packset")}
print(f"run: {len(draws)} draws, ljos built first in draws {led['ljos']}, packset first in draws {led['packset']}")
print(f"machine: {env['cpu']}, jobs: {env['jobs']}, {env['rustc']}")
print('method: median and IQR are linear quartiles, statistics.quantiles(method="inclusive"); p95 is the same estimator at 0.95')

for c in ("ljos", "packset"):
    runs = [wall(d / f"time-{c}.txt") for d in draws]
    log = "\n".join(body(draws[0] / f"install-{c}.log"))
    version = re.search(rf"Installed package `{c} v([\d.]+)", log).group(1)
    print(f"install {c} {version} wall: {stat([s for s, _ in runs], '.0f', 's')}")
    print(f"install {c} {version} largest single build process RSS: {stat([r for _, r in runs], '.0f', 'MiB')}")

sizes = {}
for d in draws:
    for line in body(d / "sizes.txt"):
        f = line.split()
        if len(f) > 4 and not line.startswith("total"):
            sizes.setdefault(f[-1], []).append(int(f[4]) / 1e6)
for name, xs in sizes.items():
    print(f"binary {name}: {stat(xs, '.1f', 'MB')}")
print(f"binaries on disk: {stat([sum(v) for v in zip(*sizes.values())], '.1f', 'MB')}")

rss = {}
for d in draws:
    for line in body(d / "rss.txt"):
        k, v = line.split()
        rss.setdefault(k[:-3], []).append(int(v) / 1024)
for k, xs in rss.items():
    print(f"packsetd {k}: {stat(xs, '.1f', 'MiB')}")

us = [int(x) / 1000 for d in draws for x in body(d / "latency-us.txt")]
p95 = statistics.quantiles(us, n=20, method="inclusive")[18]
print(f"search (lexical, one process per query, {len(draws)} seeded runs): {stat(us, '.1f', 'ms')}, p95 {p95:.1f} ms")

seeded, secs, live = [], [], []
for d in draws:
    text = "\n".join(body(d / "seed.txt"))
    n, s = re.search(r"seeded (\d+) claims in ([\d.]+) s", text).groups()
    seeded.append(int(n)); secs.append(float(s))
    live.append(json.loads(text[text.index("{") : text.rindex("}") + 1])["live"])
print(f"claims seeded per draw: {stat(seeded, '.0f')}")
print(f"seeding time per draw: {stat(secs, '.1f', 's')}")
print(f"live claims during the search runs: {stat(live, '.0f')}")
