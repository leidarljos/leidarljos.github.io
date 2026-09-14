#!/usr/bin/env python3
"""Build /search-index.json from committed HTML. Run from the site root."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "scripts", "org", "orgmode", "marks"}


class Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.parts: list[str] = []
        self._in_title = False
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "nav", "footer"}:
            self._skip += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer"} and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        t = " ".join(data.split())
        if not t:
            return
        if self._in_title:
            self.title = t
        elif not self._skip:
            self.parts.append(t)


def url_for(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    if rel == "index.html":
        return "/"
    return "/" + rel


def main() -> None:
    docs: list[dict[str, str]] = []
    for html in sorted(ROOT.rglob("*.html")):
        if any(p in SKIP for p in html.parts):
            continue
        raw = html.read_text(encoding="utf-8", errors="ignore")
        p = Text()
        p.feed(raw)
        text = " ".join(p.parts)
        if len(text) < 40:
            continue
        title = p.title.split("—")[0].strip() or html.stem
        docs.append({"url": url_for(html), "title": title, "text": text[:8000]})
    out = ROOT / "search-index.json"
    out.write_text(json.dumps({"docs": docs}, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out} ({len(docs)} pages)")


if __name__ == "__main__":
    main()
