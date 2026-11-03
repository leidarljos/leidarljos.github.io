"""Internal hrefs in committed HTML resolve to a file, and fragments to an id."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

# This checkout is the GitHub Pages site at this host. Other leidarljos
# repositories are published beside it at /<repo>/ and are not files here.
SITE_HOST = "leidarljos.github.io"

# Schemes that do not name a file in this checkout.
_LEAVES = {"mailto", "tel", "javascript", "data"}


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.anchors: set[str] = set()
        self._silent = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, void=False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag, attrs, void=True)

    def _start(
        self, tag: str, attrs: list[tuple[str, str | None]], *, void: bool
    ) -> None:
        # Markup-like text inside script or style is not an element a reader can open.
        if tag in {"script", "style"} and not void:
            self._silent += 1
        if self._silent:
            return
        for key, value in attrs:
            if key == "id" and value:
                self.anchors.add(value)
            elif tag == "a" and key == "name" and value:
                # After ids, the HTML fragment algorithm accepts <a name>.
                self.anchors.add(value)
            elif key == "href":
                self.hrefs.append(value or "")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._silent:
            self._silent -= 1


def _parse(path: Path) -> _Page:
    page = _Page()
    page.feed(path.read_text(encoding="utf-8"))
    page.close()
    return page


def _committed_html(root: Path) -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=root, text=True)
    return [root / rel for rel in raw.split("\0") if rel.endswith(".html")]


def _host(netloc: str) -> str:
    return netloc.rsplit("@", 1)[-1].split(":", 1)[0].lower()


def _other_repository(root: Path, path: str) -> bool:
    """True when an absolute URL on this host names another Pages project.

    A first path segment that is not a file or directory in this checkout is
    one of those projects. The checker stays on disk and does not fetch it.
    """
    parts = [part for part in path.split("/") if part]
    if not parts:
        return False
    return not (root / parts[0]).exists()


def _internal(root: Path, href: str) -> tuple[str, str, bool] | None:
    """Return (path, fragment, absolute) for an href in this checkout.

    None means the href leaves the site. Absolute is true when the href
    carries this site's host, so an empty path is the site root rather than
    the current document.
    """
    parts = urlsplit(href.strip())
    scheme = parts.scheme.lower()
    if scheme in _LEAVES:
        return None
    absolute = scheme in {"http", "https"} or (scheme == "" and bool(parts.netloc))
    if absolute:
        if _host(parts.netloc) != SITE_HOST:
            return None
    elif scheme:
        return None
    # Split first, then percent-decode. '+' is not a space in a fragment.
    path = unquote(parts.path)
    fragment = unquote(parts.fragment)
    if absolute and _other_repository(root, path):
        return None
    return path, fragment, absolute


def _base_document(root: Path, page: Path) -> Path:
    templates = (root / "org" / "templates").resolve()
    try:
        page.resolve().relative_to(templates)
    except ValueError:
        return page
    # org/export.el splices these partials into handbook/*.html, so a relative
    # href is resolved from that directory. A fragment-only href names an id on
    # the published page. Each handbook page is also checked from its own copy.
    return root / "handbook" / "index.html"


def _locate(root: Path, base: Path, path: str, absolute: bool) -> Path:
    # An empty fragment is the top of the document, so the file still resolves.
    if absolute and path in {"", "/"}:
        return (root / "index.html").resolve()
    if not absolute and path == "":
        return base.resolve()
    raw = root / path.lstrip("/") if path.startswith("/") else base.parent / path
    # A trailing slash, or a directory, is that directory's index page.
    if path.endswith("/") or raw.is_dir():
        raw = raw / "index.html"
    return raw.resolve()


def _inside(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def survey(root: Path, files: list[Path]) -> tuple[list[str], int]:
    """Return miss lines and how many internal hrefs were checked."""
    root = root.resolve()
    parsed: dict[Path, _Page] = {path.resolve(): _parse(path) for path in files}
    problems: list[str] = []
    checked = 0
    for path in files:
        page = parsed[path.resolve()]
        base = _base_document(root, path)
        rel = path.resolve().relative_to(root).as_posix()
        for href in page.hrefs:
            target = _internal(root, href)
            if target is None:
                continue
            checked += 1
            url_path, fragment, absolute = target
            located = _locate(root, base, url_path, absolute)
            if not _inside(root, located):
                problems.append(f"{rel}: {href} leaves the checkout")
                continue
            if not located.is_file():
                problems.append(f"{rel}: {href} does not resolve to a file")
                continue
            if not fragment:
                continue
            target_rel = located.relative_to(root).as_posix()
            if located.suffix.lower() != ".html":
                problems.append(f"{rel}: {href} has no anchor in {target_rel}")
                continue
            doc = parsed.get(located)
            if doc is None:
                doc = _parse(located)
                parsed[located] = doc
            if fragment not in doc.anchors:
                problems.append(f"{rel}: {href} has no anchor in {target_rel}")
    return sorted(set(problems)), checked


class InternalLinks(unittest.TestCase):
    def test_internal_hrefs_and_anchors_resolve(self) -> None:
        files = _committed_html(ROOT)
        # An empty list, or a parse that sees no href, would pass with no misses.
        # This site has internal hrefs, so zero is a broken checker.
        self.assertNotEqual(files, [])
        problems, checked = survey(ROOT, files)
        self.assertGreater(checked, 0)
        self.assertEqual(problems, [])

    def test_broken_href_and_anchor_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "index.html").write_text(
                '<!DOCTYPE html><html><body><main id="main"></main></body></html>',
                encoding="utf-8",
            )
            (root / "ok.html").write_text(
                '<!DOCTYPE html><html><body><h2 id="here">Here</h2>'
                '<h2 id="a b">Spaced</h2></body></html>',
                encoding="utf-8",
            )
            index = root / "index.html"
            index.write_text(
                """<!DOCTYPE html><html><body>
                <a href="#main">skip</a>
                <a href="/docs/">docs</a>
                <a href="ok.html#here">good</a>
                <a href="ok.html#a%20b">space</a>
                <a href="ok.html#">top</a>
                <a href="missing.html">missing</a>
                <a href="ok.html#gone">gone</a>
                <a href="../outside.html">out of tree</a>
                <a href="https://example.com/nope">external</a>
                <a href="https://leidarljos.github.io/vissue/">other project</a>
                <a href="https://leidarljos.github.io/docs/missing/">typo</a>
                <main id="main"></main>
                </body></html>
                """,
                encoding="utf-8",
            )
            problems, _checked = survey(
                root, [index, root / "ok.html", docs / "index.html"]
            )
        self.assertEqual(
            problems,
            [
                "index.html: ../outside.html leaves the checkout",
                "index.html: https://leidarljos.github.io/docs/missing/"
                " does not resolve to a file",
                "index.html: missing.html does not resolve to a file",
                "index.html: ok.html#gone has no anchor in ok.html",
            ],
        )


if __name__ == "__main__":
    unittest.main()
