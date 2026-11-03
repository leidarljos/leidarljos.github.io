"""The search index lists every content page, and every entry is a real page."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "search-index.json"
# Sources, the publisher, and crate marks. None of these are pages.
NOT_A_PAGE = {".git", "scripts", "org", "orgmode", "marks"}


class _Refresh(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refresh = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta":
            return
        named = {key.lower(): (value or "") for key, value in attrs}
        if named.get("http-equiv", "").lower() == "refresh":
            self.refresh = True


def is_refresh(raw: str) -> bool:
    probe = _Refresh()
    probe.feed(raw)
    return probe.refresh


def url_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def content_urls() -> list[str]:
    found: list[str] = []
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in NOT_A_PAGE for part in path.parts):
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        if is_refresh(raw):
            continue
        found.append(url_for(path))
    return found


def file_for_url(url: str) -> Path:
    if not url.startswith("/") or url.startswith("//"):
        return ROOT / "__missing__"
    rel = url[1:]
    path = ROOT / rel / "index.html" if url.endswith("/") or rel == "" else ROOT / rel
    if path.is_dir():
        path = path / "index.html"
    resolved = path.resolve()
    resolved.relative_to(ROOT.resolve())
    return resolved


def load_docs() -> list[dict[str, str]]:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    docs = data["docs"]
    if not isinstance(docs, list):
        raise AssertionError("search-index.json docs is not a list")
    return docs


def indexed_urls() -> list[str]:
    return [doc["url"] for doc in load_docs()]


def _index_diff(committed: bytes, rebuilt: bytes) -> str:
    lines = ["search-index.json does not match a rebuild."]
    try:
        old = json.loads(committed)["docs"]
        new = json.loads(rebuilt)["docs"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        lines.append(str(exc))
        return "\n".join(lines)
    old_urls = [doc.get("url") for doc in old]
    new_urls = [doc.get("url") for doc in new]
    dropped = [url for url in old_urls if url not in new_urls]
    added = [url for url in new_urls if url not in old_urls]
    if dropped:
        lines.append("dropped: " + ", ".join(str(url) for url in dropped))
    if added:
        lines.append("added: " + ", ".join(str(url) for url in added))
    old_by = {doc.get("url"): doc for doc in old}
    for doc in new:
        prev = old_by.get(doc.get("url"))
        if prev is not None and prev != doc:
            lines.append(f"changed: {doc.get('url')}")
    if len(lines) == 1:
        lines.append(f"bytes {len(committed)} -> {len(rebuilt)}")
    return "\n".join(lines)


class SearchIndex(unittest.TestCase):
    def test_committed_index_matches_rebuild(self) -> None:
        committed = INDEX.read_bytes()
        try:
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build-search-index.py")],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            rebuilt = INDEX.read_bytes()
            if rebuilt != committed:
                self.fail(_index_diff(committed, rebuilt))
        finally:
            INDEX.write_bytes(committed)

    def test_every_content_page_is_indexed(self) -> None:
        indexed = set(indexed_urls())
        missing = [url for url in content_urls() if url not in indexed]
        self.assertEqual(missing, [])

    def test_every_indexed_url_exists(self) -> None:
        missing = [url for url in indexed_urls() if not file_for_url(url).is_file()]
        self.assertEqual(missing, [])

    def test_index_lists_only_real_pages(self) -> None:
        extra = sorted(set(indexed_urls()) - set(content_urls()))
        self.assertEqual(extra, [])


if __name__ == "__main__":
    unittest.main()
