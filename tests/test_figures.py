"""Each measured number on the site is printed beside its public source."""

from __future__ import annotations

import html
import os
import re
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_TREE = "https://github.com/leidarljos/leidarljos.github.io/tree/main/"

PACKSET_LME = "https://leidarljos.github.io/packset/explanation.html#what-a-search-ranks"
PACKSET_080 = "https://github.com/leidarljos/packset/blob/main/CHANGELOG.md#080-2026-09-12"
INSTALL_RUN = SITE_TREE + "measurements/2026-11-03-install"
DEMO_CAST = "/demo/ljos-demo.cast"

INSTALL_SUMMARY = ROOT / "measurements/2026-11-03-install/summary.txt"


def install_figures() -> tuple[tuple[str, str, str, tuple[str, ...]], ...]:
    """Fig. 5 as summary.txt says the page should print it, each with the lines it comes from."""
    said = INSTALL_SUMMARY.read_text(encoding="utf-8")

    def line(pattern: str) -> re.Match[str]:
        found = re.search(pattern, said, re.M)
        if found is None:
            raise AssertionError(f"{INSTALL_SUMMARY.name} has no line like {pattern!r}")
        return found

    ljos = line(r"^install ljos: (\d+) s wall.*$")
    packset = line(r"^install packset: (\d+) s wall.*$")
    binaries = re.findall(r"^binary \S+: ([\d.]+) MB$", said, re.M)
    if len(binaries) != 5:
        raise AssertionError(f"{INSTALL_SUMMARY.name} lists {len(binaries)} binaries, not 5")
    # This run's summary.txt is kept as printed, labelled MB; its value is kB / 1024.
    rss = line(r"^packsetd rss_after_search: ([\d.]+) Mi?B$")
    search = line(r"^search .*: p50 ([\d.]+) ms, p95 ([\d.]+) ms$")
    live = line(r"^pack size during the search runs: (\d+) live claims$")
    sizes = tuple(re.findall(r"^binary .*$", said, re.M))
    return (
        ("index.html", f"{ljos[1]} s + {packset[1]} s", INSTALL_RUN, (ljos[0], packset[0])),
        ("index.html", f"{sum(map(float, binaries)):.1f} MB", INSTALL_RUN, sizes),
        ("index.html", f"{rss[1]} MiB", INSTALL_RUN, (rss[0],)),
        ("index.html", f"{search[1]} / {search[2]} ms", INSTALL_RUN, (search[0],)),
        ("index.html", f"{live[1]} claims in the pack", INSTALL_RUN, (live[0],)),
    )


FUSED_QA = (
    "labelled sessions (oracle) 0.778 0.405 0.982 0.467 0.938 0.504 0.634",
    "sessions, fused panel 0.792 0.355 0.911 0.300 0.891 0.323 0.549",
)

# The page, the number as it prints it, the source linked beside it, and
# what that source prints for it.
FIGURES = (
    ("index.html", "n = 470 answerable questions", PACKSET_LME, ("470 answerable questions",)),
    ("index.html", "BM25+ with e5-large-v2", PACKSET_LME, ("CombMNZ (BM25+ plus e5-large-v2)",)),
    ("index.html", "0.914", PACKSET_LME, ("BM25+ alone reaches 0.914 recall@5",)),
    ("index.html", "0.949", PACKSET_LME, ("0.949 recall@5",)),
    ("index.html", "0.549 / 0.634", PACKSET_LME, FUSED_QA),
    (
        "index.html",
        "7\N{NO-BREAK SPACE}B reader and judge, top five sessions",
        PACKSET_LME,
        ("Qwen2.5-7B-Instruct", "as reader and judge", "top five sessions"),
    ),
    ("index.html", "about a minute long", DEMO_CAST, ()),
    ("index.html", "8-thread Xeon with two build jobs", INSTALL_RUN, ()),
    *install_figures(),
    (
        "docs/island/index.html",
        "hit@1 0.377 against the fused panel's 0.889",
        PACKSET_080,
        ("hit@1 0.377 against the fused 0.889",),
    ),
    ("PRODUCT.md", "`0.949`", PACKSET_LME, ("0.949 recall@5",)),
    ("PRODUCT.md", "`0.549 / 0.634`", PACKSET_LME, FUSED_QA),
)

OPEN = re.compile(r"<(figure|section|p)\b")

# The public sources answered in 0.10 s or less on 2026-11-03; the bound
# only stops a hung connection from hanging the run.
FETCH_TIMEOUT_S = 30


def page(rel: str) -> str:
    return html.unescape((ROOT / rel).read_text(encoding="utf-8"))


def plain(text: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def beside(text: str, at: int) -> str:
    """The innermost figure, section or paragraph around `at`; a Markdown file is one block."""
    for tag in reversed(list(OPEN.finditer(text, 0, at))):
        end = text.find(f"</{tag.group(1)}>", tag.start())
        if end > at:
            return text[tag.start() : end]
    return text


def in_repo(source: str) -> Path | None:
    if source.startswith("/"):
        return ROOT / source.lstrip("/")
    if source.startswith(SITE_TREE):
        return ROOT / source[len(SITE_TREE) :]
    return None


class Figures(unittest.TestCase):
    def test_each_number_has_its_source_beside_it(self) -> None:
        for rel, figure, source, _ in FIGURES:
            text = page(rel)
            spots = [m.start() for m in re.finditer(re.escape(figure), text)]
            self.assertTrue(spots, f"{rel} no longer prints {figure!r}")
            for at in spots:
                self.assertIn(source, beside(text, at), f"{rel}: {figure!r}")

    def test_sources_in_this_repo_print_the_numbers(self) -> None:
        for _, figure, source, quotes in FIGURES:
            path = in_repo(source)
            if path is None:
                continue
            self.assertTrue(path.exists(), source)
            said = (path / "summary.txt" if path.is_dir() else path).read_text(encoding="utf-8")
            for quote in quotes:
                self.assertIn(quote, said, f"{source} for {figure!r}")

    def test_island_captions_count_the_points_drawn(self) -> None:
        island = page("docs/island/index.html")
        for svg in ("island.svg", "island-graph.svg"):
            points = (ROOT / svg).read_text(encoding="utf-8").count("<circle")
            self.assertIn(f"{points} atoms", beside(island, island.index(f'src="/{svg}"')))

    @unittest.skipUnless(os.environ.get("FIGURES_ONLINE"), "FIGURES_ONLINE=1 fetches the sources")
    def test_public_sources_print_the_numbers(self) -> None:
        fetched: dict[str, str] = {}
        for _, figure, source, quotes in FIGURES:
            if in_repo(source) is not None:
                continue
            url = source.split("#", 1)[0]
            if url.startswith("https://github.com/"):
                url = url.replace("https://github.com/", "https://raw.githubusercontent.com/", 1)
                url = url.replace("/blob/", "/", 1)
            if url not in fetched:
                with urllib.request.urlopen(url, timeout=FETCH_TIMEOUT_S) as answer:
                    fetched[url] = plain(answer.read().decode("utf-8"))
            for quote in quotes:
                self.assertIn(quote, fetched[url], f"{url} for {figure!r}")


if __name__ == "__main__":
    unittest.main()
