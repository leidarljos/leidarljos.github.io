"""Redirect stubs name one target, and each content page can be previewed."""

from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]

# Public origin of this site. Canonical links are absolute so a stub and
# the page it names do not depend on which host served the file.
ORIGIN = "https://leidarljos.github.io"

# The site publishes one preview image. Pages share it.
OG_IMAGE = ORIGIN + "/og.png"

# Not published pages: the Org sources, the head template, and vendored assets.
SKIP = {".git", "org", "orgmode", "vendor", "scripts", "measurements", "demo"}

# HTML refresh delay is in seconds. Zero is immediate: a stub is not a second
# copy of the page a visitor should read.
IMMEDIATE = 0

_REFRESH = re.compile(
    r"^\s*(?P<delay>\d+)\s*;\s*url\s*=\s*(?P<url>\S+)\s*$",
    re.IGNORECASE,
)


class Head(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_head = False
        self.in_title = False
        self.title = ""
        self.canonical: list[str] = []
        self.description: list[str] = []
        self.og_title: list[str] = []
        self.og_image: list[str] = []
        self.refresh: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): (value or "") for key, value in attrs}
        if tag == "head":
            self.in_head = True
        if tag == "title":
            self.in_title = True
        if not self.in_head:
            return
        if tag == "link" and attr.get("rel", "").lower() == "canonical":
            self.canonical.append(attr.get("href", ""))
        if tag != "meta":
            return
        if attr.get("name", "").lower() == "description":
            self.description.append(attr.get("content", ""))
        if attr.get("property", "").lower() == "og:title":
            self.og_title.append(attr.get("content", ""))
        if attr.get("property", "").lower() == "og:image":
            self.og_image.append(attr.get("content", ""))
        if attr.get("http-equiv", "").lower() == "refresh":
            self.refresh.append(attr.get("content", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag == "head":
            self.in_head = False
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data


def pages() -> list[Path]:
    found: list[Path] = []
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in SKIP for part in path.parts):
            continue
        found.append(path)
    return found


def public_url(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return ORIGIN + "/"
    if rel.endswith("/index.html"):
        return ORIGIN + "/" + rel[: -len("index.html")]
    return ORIGIN + "/" + rel


def parse_refresh(content: str) -> tuple[int, str]:
    match = _REFRESH.match(content.strip())
    if match is None:
        raise AssertionError(f"refresh is not a url redirect: {content!r}")
    url = match.group("url").strip("'\"")
    return int(match.group("delay")), url


def local_page(url: str) -> Path | None:
    """File this URL names when its first segment lives in the repo.

    /vissue and /consensus/ are sibling sites on the same host. They have
    no directory here. A path under a directory that does exist, such as
    /docs/, has to name a real file.
    """
    if url != ORIGIN + "/" and not url.startswith(ORIGIN + "/"):
        return None
    path = url[len(ORIGIN):]
    parts = [part for part in path.split("/") if part]
    if not parts:
        return ROOT / "index.html"
    if not (ROOT / parts[0]).exists():
        return None
    if path.endswith("/"):
        return ROOT / path.lstrip("/") / "index.html"
    candidate = ROOT / path.lstrip("/")
    if candidate.is_dir():
        return candidate / "index.html"
    return candidate


class Meta(unittest.TestCase):
    def test_redirect_stubs_name_one_target(self) -> None:
        seen = 0
        for path in pages():
            head = Head()
            head.feed(path.read_text(encoding="utf-8"))
            if not head.refresh:
                continue
            seen += 1
            rel = path.relative_to(ROOT).as_posix()
            self.assertEqual(len(head.refresh), 1, rel)
            self.assertEqual(len(head.canonical), 1, rel)
            delay, refresh_url = parse_refresh(head.refresh[0])
            self.assertEqual(delay, IMMEDIATE, rel)
            here = public_url(path)
            target = urljoin(here, refresh_url)
            named = urljoin(here, head.canonical[0])
            self.assertEqual(target, named, rel)
            self.assertNotEqual(target, here, rel)
            self.assertTrue(target.startswith(ORIGIN + "/") or target == ORIGIN + "/", rel)
            local = local_page(target.split("#", 1)[0])
            if local is not None:
                self.assertTrue(local.is_file(), f"{rel} -> {target}")
        self.assertGreater(seen, 0)

    def test_content_pages_have_canonical_and_preview(self) -> None:
        seen = 0
        for path in pages():
            head = Head()
            head.feed(path.read_text(encoding="utf-8"))
            if head.refresh:
                continue
            seen += 1
            rel = path.relative_to(ROOT).as_posix()
            here = public_url(path)
            self.assertEqual(head.canonical, [here], rel)
            self.assertEqual(len(head.description), 1, rel)
            self.assertTrue(head.description[0].strip(), rel)
            title = " ".join(head.title.split())
            self.assertEqual(head.og_title, [title], rel)
            self.assertTrue(title, rel)
            self.assertEqual(head.og_image, [OG_IMAGE], rel)
        self.assertGreater(seen, 0)


if __name__ == "__main__":
    unittest.main()
