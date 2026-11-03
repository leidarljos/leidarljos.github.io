"""Published pages name images, label inputs, and keep a straight outline."""

from __future__ import annotations

import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The asciinema player is vendored. Its markup is not a page on this site.
SKIP_PARTS = {".git", "vendor"}

# These input types carry their own name, or they are not shown.
# HTML living standard, the input element: hidden is not exposed,
# and submit, button and reset are named by their value.
NAMED_WITHOUT_LABEL = {"hidden", "submit", "button", "reset"}


def _attrs(raw: list[tuple[str, str | None]]) -> dict[str, str]:
    return {key: ("" if value is None else value) for key, value in raw}


def _is_nav_landmark(tag: str, attr: dict[str, str]) -> bool:
    role = attr.get("role", "").strip().lower()
    # role=none and role=presentation remove the landmark.
    if role in {"none", "presentation"}:
        return False
    if tag == "nav":
        return True
    return role == "navigation"


class Page(HTMLParser):
    """One document. Problems are lines a reader of the test output can act on."""

    def __init__(self, name: str) -> None:
        super().__init__(convert_charrefs=True)
        self.name = name
        self.problems: list[str] = []
        self.headings: list[int] = []
        self.redirect = False
        self.nav_landmarks = 0
        self._svg: list[dict[str, object]] = []
        self._label: list[dict[str, object]] = []
        self._labels: list[dict[str, object]] = []
        self._inputs: list[dict[str, object]] = []
        self._ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = _attrs(attrs)
        if tag == "meta" and attr.get("http-equiv", "").lower() == "refresh":
            self.redirect = True
        element_id = attr.get("id", "").strip()
        if element_id:
            self._ids.add(element_id)
        if _is_nav_landmark(tag, attr):
            self.nav_landmarks += 1
        if tag == "img":
            self._check_img(attr)
        elif tag == "svg":
            self._svg.append({"attr": attr, "title": "", "in_title": False})
        elif tag == "title" and self._svg:
            self._svg[-1]["in_title"] = True
        elif tag == "input":
            self._inputs.append(
                {"attr": attr, "label": self._label[-1] if self._label else None}
            )
        elif tag == "label":
            self._label.append({"for": attr.get("for", "").strip(), "text": ""})
        elif len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
            self.headings.append(int(tag[1]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._svg and self._svg[-1]["in_title"]:
            self._svg[-1]["in_title"] = False
        elif tag == "svg" and self._svg:
            self._check_svg(self._svg.pop())
        elif tag == "label" and self._label:
            self._labels.append(self._label.pop())

    def handle_data(self, data: str) -> None:
        if self._svg and self._svg[-1]["in_title"]:
            self._svg[-1]["title"] = str(self._svg[-1]["title"]) + data
        if self._label:
            self._label[-1]["text"] = str(self._label[-1]["text"]) + data

    def finish(self) -> None:
        while self._svg:
            self._check_svg(self._svg.pop())
        self._check_inputs()
        self._check_outline()

    def _check_img(self, attr: dict[str, str]) -> None:
        # alt="" is a name: it marks a decorative image. Removing the
        # attribute is the failure. A title counts only when it has text,
        # because an empty title is not a name.
        if "alt" in attr or attr.get("title", "").strip():
            return
        src = attr.get("src", "")
        self.problems.append(f"{self.name}: img {src} has no alt or title")

    def _check_svg(self, info: dict[str, object]) -> None:
        attr = info["attr"]
        assert isinstance(attr, dict)
        # aria-hidden removes the svg from the accessibility tree
        # (WAI-ARIA). The theme and footer icons use it so they are not
        # read beside the button or the link text. A title attribute would
        # be a hover tooltip, which changes the page.
        if str(attr.get("aria-hidden", "")).strip().lower() == "true":
            return
        title = str(info.get("title", "")).strip()
        if "alt" in attr or str(attr.get("title", "")).strip() or title:
            return
        self.problems.append(f"{self.name}: svg has no alt or title")

    def _check_inputs(self) -> None:
        labelled_ids = {
            str(label["for"])
            for label in self._all_labels()
            if str(label["for"]) and str(label["text"]).strip()
        }
        for item in self._inputs:
            attr = item["attr"]
            assert isinstance(attr, dict)
            kind = attr.get("type", "text").strip().lower() or "text"
            if kind in NAMED_WITHOUT_LABEL:
                continue
            # type=image is a picture button. HTML requires alt on it.
            if kind == "image":
                if "alt" not in attr and not attr.get("title", "").strip():
                    src = attr.get("src", "")
                    self.problems.append(
                        f"{self.name}: img {src} has no alt or title"
                    )
                continue
            if attr.get("aria-label", "").strip():
                continue
            refs = attr.get("aria-labelledby", "").split()
            # aria-labelledby names the input from those elements.
            # A missing id leaves it unnamed.
            if refs and all(ref in self._ids for ref in refs):
                continue
            label = item["label"]
            if isinstance(label, dict) and str(label["text"]).strip():
                continue
            element_id = attr.get("id", "").strip()
            if element_id and element_id in labelled_ids:
                continue
            who = element_id or attr.get("name", "") or kind
            self.problems.append(f"{self.name}: input {who} has no label")

    def _all_labels(self) -> list[dict[str, object]]:
        # A label still open at EOF (truncated markup) still has its text.
        return [*self._labels, *self._label]

    def _check_outline(self) -> None:
        # A refresh stub only bounces the visitor. It is not the document.
        # The page it points at is checked on its own.
        if self.redirect:
            return
        h1 = self.headings.count(1)
        if h1 != 1:
            self.problems.append(f"{self.name}: {h1} h1, want 1")
        # Heading ranks step by one. h1 then h3 skips h2. HTML outline.
        previous = 0
        for level in self.headings:
            if level > previous + 1:
                self.problems.append(
                    f"{self.name}: heading level jumped to h{level}"
                )
                break
            previous = level
        if self.nav_landmarks < 1:
            self.problems.append(f"{self.name}: no nav landmark")


def audit(html: str, name: str) -> list[str]:
    page = Page(name)
    try:
        page.feed(html)
        page.close()
    except Exception as exc:  # pragma: no cover - parser errors name the file
        return [f"{name}: {exc}"]
    page.finish()
    return page.problems


def published_pages() -> list[Path]:
    found: list[Path] = []
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        # org/templates are fragments pasted into the handbook.
        # The published handbook HTML is what a visitor gets.
        if "org" in path.parts and "templates" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "<html" not in text.lower():
            continue
        found.append(path)
    return found


class Accessibility(unittest.TestCase):
    def test_images_have_alt_or_title(self) -> None:
        bad: list[str] = []
        for path in published_pages():
            rel = str(path.relative_to(ROOT))
            for line in audit(path.read_text(encoding="utf-8"), rel):
                if "img " in line or "svg has no alt" in line:
                    bad.append(line)
        self.assertEqual(bad, [])

    def test_inputs_have_labels(self) -> None:
        bad: list[str] = []
        for path in published_pages():
            rel = str(path.relative_to(ROOT))
            for line in audit(path.read_text(encoding="utf-8"), rel):
                if "input " in line:
                    bad.append(line)
        self.assertEqual(bad, [])

    def test_one_h1_and_no_skipped_heading(self) -> None:
        bad: list[str] = []
        for path in published_pages():
            rel = str(path.relative_to(ROOT))
            for line in audit(path.read_text(encoding="utf-8"), rel):
                if "h1" in line or "heading level" in line:
                    bad.append(line)
        self.assertEqual(bad, [])

    def test_nav_is_a_landmark(self) -> None:
        bad: list[str] = []
        for path in published_pages():
            rel = str(path.relative_to(ROOT))
            for line in audit(path.read_text(encoding="utf-8"), rel):
                if "nav landmark" in line:
                    bad.append(line)
        self.assertEqual(bad, [])

    def test_removed_alt_fails(self) -> None:
        path = ROOT / "index.html"
        original = path.read_text(encoding="utf-8")
        self.assertEqual(audit(original, "index.html"), [])
        removed = original.replace('alt=""', "", 1)
        self.assertNotEqual(removed, original)
        found = audit(removed, "index.html")
        self.assertTrue(any("has no alt or title" in line for line in found), found)

        bare = (
            "<html><body><nav aria-label='Site'></nav><h1>T</h1>"
            "<img src='/og.png'><img src='/icon.svg'></body></html>"
        )
        bare_problems = audit(bare, "bare")
        self.assertTrue(any("/og.png" in line for line in bare_problems), bare_problems)
        self.assertTrue(any("/icon.svg" in line for line in bare_problems), bare_problems)
        named = bare.replace("<img src='/og.png'>", "<img src='/og.png' alt=''>")
        named = named.replace("<img src='/icon.svg'>", "<img src='/icon.svg' alt='mark'>")
        self.assertEqual(audit(named, "named"), [])

    def test_search_input_without_label_fails(self) -> None:
        bare = (
            "<html><body><nav aria-label='Site'></nav><h1>Find</h1>"
            "<input id='q' type='search' name='q'>"
            "</body></html>"
        )
        found = audit(bare, "search")
        self.assertTrue(any("input q has no label" in line for line in found), found)
        labelled = bare.replace(
            "<input",
            "<label for='q'>Search</label><input",
        )
        self.assertEqual(audit(labelled, "search"), [])

    def test_skipped_heading_fails(self) -> None:
        skipped = "<html><body><nav></nav><h1>T</h1><h3>Jump</h3></body></html>"
        found = audit(skipped, "skip")
        self.assertTrue(any("heading level jumped to h3" in line for line in found), found)
        straight = "<html><body><nav></nav><h1>T</h1><h2>Next</h2></body></html>"
        self.assertEqual(audit(straight, "straight"), [])
        two = "<html><body><nav></nav><h1>One</h1><h1>Two</h1></body></html>"
        found = audit(two, "two")
        self.assertTrue(any("2 h1, want 1" in line for line in found), found)

    def test_page_needs_a_nav_landmark(self) -> None:
        missing = "<html><body><h1>T</h1></body></html>"
        found = audit(missing, "nonav")
        self.assertTrue(any("no nav landmark" in line for line in found), found)
        element = "<html><body><nav aria-label='Site'></nav><h1>T</h1></body></html>"
        self.assertEqual(audit(element, "nav"), [])
        role = "<html><body><div role='navigation'>Menu</div><h1>T</h1></body></html>"
        self.assertEqual(audit(role, "role"), [])

    def test_svg_needs_alt_or_title(self) -> None:
        bare = "<html><body><nav></nav><h1>T</h1><svg viewBox='0 0 1 1'></svg></body></html>"
        found = audit(bare, "svg")
        self.assertTrue(any("svg has no alt or title" in line for line in found), found)
        titled = (
            "<html><body><nav></nav><h1>T</h1>"
            "<svg viewBox='0 0 1 1'><title>Mark</title></svg></body></html>"
        )
        self.assertEqual(audit(titled, "titled"), [])
        hidden = (
            "<html><body><nav></nav><h1>T</h1>"
            "<svg aria-hidden='true' viewBox='0 0 1 1'></svg></body></html>"
        )
        self.assertEqual(audit(hidden, "hidden"), [])


if __name__ == "__main__":
    unittest.main()
