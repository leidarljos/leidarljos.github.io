"""Every claim the compare pages make about another tool links its source."""

from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("docs/compare/index.html", "compare/index.html", "docs/alternatives/index.html")

# The projects these pages set ljos beside; a sentence that names one says something about it.
OTHERS = (
    "Mem0", "Zep", "Graphiti", "Letta", "CLAUDE.md", "AGENTS.md",
    "agentmemory", "HippoRAG", "MINJA", "InjecMEM",
)
# A figure someone else published or reports is their claim even when the sentence names no one.
QUOTES = re.compile(r"\b(?:published|reports?)\b", re.IGNORECASE)
CHECKED = re.compile(
    r"checked on \d{1,2} (?:January|February|March|April|May|June|July|August"
    r"|September|October|November|December) \d{4}"
)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
BLOCKS = {"p", "li", "caption"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Node:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]], parent: Node | None) -> None:
        self.tag = tag
        self.attrs = {k: v or "" for k, v in attrs}
        self.parent = parent
        self.children: list[Node | str] = []


class Tree(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", [], None)
        self.cur = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_endtag(self, tag: str) -> None:
        node = self.cur
        while node.parent is not None and node.tag != tag:
            node = node.parent
        if node.parent is not None:
            self.cur = node.parent

    def handle_data(self, data: str) -> None:
        self.cur.children.append(data)


def main_of(rel: str) -> Node | None:
    tree = Tree()
    tree.feed((ROOT / rel).read_text(encoding="utf-8"))
    found = [n for n in walk(tree.root) if n.tag == "main"]
    return found[0] if found else None


def walk(node: Node):
    for child in node.children:
        if isinstance(child, Node):
            yield child
            yield from walk(child)


def is_source(href: str) -> bool:
    url = urlparse(href)
    if url.scheme not in ("http", "https") or url.hostname == "leidarljos.github.io":
        return False
    return not (url.hostname == "github.com" and url.path.startswith("/leidarljos/"))


def marked_text(node: Node) -> tuple[str, list[tuple[int, int]]]:
    """The node's text, with the character ranges that sit inside a source link."""
    parts: list[str] = []
    marks: list[tuple[int, int]] = []

    def visit(n: Node, linked: bool) -> None:
        for child in n.children:
            if isinstance(child, str):
                start = sum(map(len, parts))
                parts.append(child)
                if linked:
                    marks.append((start, start + len(child)))
            else:
                visit(child, linked or (child.tag == "a" and is_source(child.attrs.get("href", ""))))

    visit(node, False)
    return "".join(parts), marks


def names_another(text: str) -> bool:
    return any(name in text for name in OTHERS)


def is_claim(text: str) -> bool:
    return names_another(text) or bool(QUOTES.search(text))


def sourced(start: int, end: int, marks: list[tuple[int, int]]) -> bool:
    return any(a < end and b > start for a, b in marks)


def claim_sentences(main: Node) -> list[tuple[str, bool]]:
    out: list[tuple[str, bool]] = []
    for node in walk(main):
        if node.tag not in BLOCKS:
            continue
        text, marks = marked_text(node)
        start = 0
        for piece in SENTENCE_END.split(text):
            if not piece:
                continue
            at = text.index(piece, start)
            start = at + len(piece)
            sentence = " ".join(piece.split())
            if is_claim(sentence):
                out.append((sentence, sourced(at, start, marks)))
    return out


def claim_cells(main: Node) -> list[tuple[str, bool]]:
    """Cells under another tool's column, or in another tool's row, plus any cell that names one."""
    out: list[tuple[str, bool]] = []
    for table in (n for n in walk(main) if n.tag == "table"):
        rows = [r for r in walk(table) if r.tag == "tr"]
        head = [r for r in rows if r.parent is not None and r.parent.tag == "thead"]
        columns: list[str] = []
        for cell in head[0].children if head else []:
            if isinstance(cell, Node):
                columns += [marked_text(cell)[0]] * int(cell.attrs.get("colspan") or 1)
        for row in rows:
            if row in head:
                continue
            cells = [c for c in row.children if isinstance(c, Node) and c.tag in ("td", "th")]
            about_row = bool(cells) and names_another(marked_text(cells[0])[0])
            col = 0
            for cell in cells:
                span = int(cell.attrs.get("colspan") or 1)
                text, marks = marked_text(cell)
                under = columns[col] if col < len(columns) else ""
                col += span
                # A cell spanning several tools says what none of them ship; an absence has no page to link.
                if cell.tag != "td" or span > 1:
                    continue
                if names_another(under) or about_row or is_claim(text):
                    out.append((" ".join(text.split()), bool(marks)))
    return out


class CompareClaims(unittest.TestCase):
    def test_each_claim_sentence_links_its_source(self) -> None:
        bare = []
        for rel in PAGES:
            main = main_of(rel)
            if main is None:
                continue
            bare += [f"{rel}: {s}" for s, ok in claim_sentences(main) if not ok]
        self.assertEqual(bare, [])

    def test_each_claim_cell_links_its_source(self) -> None:
        bare = []
        for rel in PAGES:
            main = main_of(rel)
            if main is None:
                continue
            bare += [f"{rel}: {c}" for c, ok in claim_cells(main) if not ok]
        self.assertEqual(bare, [])

    def test_pages_with_claims_say_when_they_were_checked(self) -> None:
        undated = []
        for rel in PAGES:
            main = main_of(rel)
            if main is None or not (claim_sentences(main) or claim_cells(main)):
                continue
            if not CHECKED.search(" ".join(marked_text(main)[0].split())):
                undated.append(rel)
        self.assertEqual(undated, [])

    def test_compare_pages_make_claims(self) -> None:
        for rel in ("docs/compare/index.html", "docs/alternatives/index.html"):
            main = main_of(rel)
            self.assertIsNotNone(main, rel)
            self.assertTrue(claim_sentences(main) and claim_cells(main), rel)


if __name__ == "__main__":
    unittest.main()
