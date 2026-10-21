"""Published pages match the commands the current releases print."""

from __future__ import annotations

import html
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INSTALL = (
    "curl -fsSLO https://github.com/leidarljos/ljos/releases/latest/download/install.sh"
    " && sh install.sh"
)
CARGO = (
    "cargo install --locked ljos packset vissue-cli vissue-mcp deedar-cli"
    " claimdag-cli ljos-policyd ljos-consensus"
)
SITTING = (
    "== doctor",
    "== cards",
    "== due",
    "== island",
    "== blockers",
    "== playbook",
    "== recall",
    "== timeline",
    "== reclaim",
    "== claim",
)
ASK = (
    "ask: a force push rewrites shared history; the agent asks you first"
    " (rule: built-in push)"
)
HOOK_ASK = (
    '"permissionDecision":"ask","permissionDecisionReason":"a force push'
    " rewrites shared history; the agent asks you first"
    " (ljos rule `built-in push`)\""
)


def page(rel: str) -> str:
    return html.unescape((ROOT / rel).read_text(encoding="utf-8"))


class SiteClaims(unittest.TestCase):
    def test_install_lines_match_release(self) -> None:
        start = page("docs/start/index.html")
        index = page("index.html")
        ref = page("docs/reference/index.html")
        for name, text in (("start", start), ("index", index), ("reference", ref)):
            self.assertIn(INSTALL, text, name)
        self.assertIn(CARGO, start)
        self.assertIn(CARGO, page("orgmode/docs/start/index.org"))

    def test_verbose_sitting_order(self) -> None:
        index = page("index.html")
        self.assertEqual(index.count("ljos sitting demo-k29f --verbose"), 2)
        scene = index.split("ljos sitting demo-k29f --verbose", 1)[1].split("gen=2", 1)[0]
        positions = [scene.index(header) for header in SITTING]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("== sync", scene)
        sit = page("docs/sit/index.html")
        self.assertIn("reclaim, then the claim", sit)
        self.assertIn("A repository with no such file says nothing about sync", sit)
        self.assertNotIn("doctor, sync, cards", sit)

    def test_force_push_asks(self) -> None:
        index = page("index.html")
        policy = page("docs/policy/index.html")
        argv = page("orgmode/handbook/argv.org")
        handbook = page("handbook/argv.html")
        self.assertIn(ASK, index)
        self.assertNotIn("deny\tgit-force-push", index)
        self.assertNotIn("rule: git-force-push", index)
        for name, text in (("policy", policy), ("argv.org", argv), ("argv.html", handbook)):
            self.assertIn(HOOK_ASK, text, name)
            self.assertNotIn('permissionDecision":"deny"', text, name)
            self.assertNotIn("ljos rule `git-force-push`", text, name)
        self.assertIn("deny: Never force push. (rule: *--force*)", policy)
        self.assertIn("On a force push the binary prints", policy)

    def test_reference_matches_shipped_verbs(self) -> None:
        ref = page("docs/reference/index.html")
        self.assertIn("PACKSET_URL=off", ref)
        self.assertNotIn("Needs PACKSET_URL", ref)
        self.assertIn("--compare", ref)
        self.assertIn("vissue consensus", ref)
        self.assertIn("Runs nothing", ref)
        self.assertIn("a force push asks", ref)
        overview = page("docs/index.html")
        self.assertIn("nine other sections", overview)
        self.assertIn("ljos finish ID --close", overview)
        self.assertNotIn("status done closes", overview)
        start = page("docs/start/index.html")
        self.assertNotIn("Score is how the scorers ranked", start)
        self.assertIn("standing: the hook shows it from the next prompt it bears on", start)

    def test_internal_links_resolve(self) -> None:
        missing: list[str] = []
        href = re.compile(r"""(?:href|src)=["']([^"']+)["']""")
        for path in ROOT.rglob("*.html"):
            if any(part in {".git", "vendor"} for part in path.parts):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for raw in href.findall(text):
                url = html.unescape(raw).split("#", 1)[0].split("?", 1)[0]
                if not url or url.startswith(("http://", "https://", "mailto:", "data:")):
                    continue
                if url.startswith("/"):
                    target = ROOT / url.lstrip("/")
                else:
                    target = (path.parent / url).resolve()
                if url.endswith("/"):
                    target = target / "index.html"
                elif target.is_dir():
                    target = target / "index.html"
                try:
                    target.relative_to(ROOT)
                except ValueError:
                    missing.append(f"{path.relative_to(ROOT)} -> {raw}")
                    continue
                if not target.is_file():
                    missing.append(f"{path.relative_to(ROOT)} -> {raw}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
