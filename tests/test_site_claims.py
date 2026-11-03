"""Published pages match the commands the current releases print."""

from __future__ import annotations

import html
import re
import unittest
from decimal import Decimal
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

    def test_install_table_matches_summary(self) -> None:
        """The install-cost table quotes the latest measurements/*-install* run."""
        runs = sorted(
            p
            for p in (ROOT / "measurements").glob("*-install*")
            if (p / "summary.txt").is_file()
        )
        self.assertTrue(runs)
        latest = runs[-1]
        summary = (latest / "summary.txt").read_text(encoding="utf-8")
        text = page("docs/compare/index.html")
        self.assertIn(f"measurements/{latest.name}", text)
        section = text.split('id="install-cost"', 1)[1].split("</table>", 1)[0]

        def field(pattern: str) -> re.Match[str]:
            match = re.search(pattern, summary, re.M)
            self.assertIsNotNone(match, pattern)
            assert match is not None
            return match

        def stat(label: str, unit: str) -> str:
            m = field(rf"^{label}: median ([\d.]+) {unit} \(IQR ([\d.]+)-([\d.]+) {unit}\)")
            return f"{m[1]} {unit}, IQR {m[2]}–{m[3]} {unit}"

        draws = field(r"^run: (\d+) draws")[1]
        for crate in ("ljos", "packset"):
            wall = field(rf"^install {crate} (\S+) wall: ")
            self.assertIn(f"<td>Build {crate} {wall[1]}</td>", section)
            self.assertIn(f">{stat(rf'install {crate} \S+ wall', 's')}<", section)

        binaries = re.findall(r"^binary (\S+): median ([\d.]+) MB", summary, re.M)
        self.assertGreaterEqual(len(binaries), 1)
        # The cell is the sum of the one-decimal medians summary.txt already printed.
        total = sum(Decimal(size) for _, size in binaries)
        self.assertIn(f">{total:.1f} MB, IQR", section)
        self.assertIn(f">{stat('binaries on disk', 'MB')}<", section)
        for name, size in binaries:
            self.assertIn(f"{name} {size}", section)

        idle = stat("packsetd rss_idle", "MiB")
        after = stat("packsetd rss_after_search", "MiB")
        self.assertIn(f">{idle.replace(' MiB,', ' MiB idle,', 1)}; {after}<", section)

        live = field(r"^live claims during the search runs: median (\d+) ")[1]
        self.assertIn(f"{live} claims", section)
        search = field(r"^search .*: median ([\d.]+) ms \(IQR ([\d.]+)-([\d.]+) ms\), n=(\d+), p95 ([\d.]+) ms$")
        self.assertIn(f">{search[1]} ms / {search[5]} ms, IQR {search[2]}–{search[3]} ms<", section)
        self.assertIn(f"n = {int(search[4]):,} over", section)
        self.assertEqual(section.count(f"n = {draws}<"), 4)

        for crate in ("ljos", "packset"):
            logs = sorted(latest.glob(f"draw-*/install-{crate}.log"))
            self.assertEqual(len(logs), int(draws), crate)
            for log in logs:
                version = re.search(
                    rf"Installed package `{crate} v([^`]+)`",
                    log.read_text(encoding="utf-8", errors="replace"),
                )
                self.assertIsNotNone(version, log)
                assert version is not None
                self.assertIn(f"Build {crate} {version.group(1)}", section)

    def test_harness_names_match_ljos(self) -> None:
        # Names `ljos onboard --harness` installs, checked against ljos
        # develop e83534a83ad8112a50f7b55f180a8b831ab715db. Each source is
        # the file in leidarljos/ljos that defines that install line.
        # The tables are HARNESSES_EXAMPLE in crates/ljos-cli/src/lib.rs.
        # docs/orgmode/integration.org lists the same names, including
        # aider, and the code adds opencode-v2 as an opt-in shape.
        text = page("docs/harnesses/index.html")
        found = set(re.findall(r"ljos onboard --harness ([A-Za-z0-9-]+)", text))
        shipped = {name for name, _source in HARNESSES}
        # json prints the MCP entry. runner-with-a-command is an example
        # shape in HARNESSES_EXAMPLE, and detect_runners skips runner-with-*.
        expected = shipped | {"json", "runner-with-a-command"}
        self.assertEqual(found, expected)
        for name, source in HARNESSES:
            self.assertIn(
                f"ljos onboard --harness {name}\n",
                text,
                f"{name} from {source}",
            )
        for name, source in EXAMPLE_SHAPES:
            self.assertIn(f'name = "{name}"', text, source)
        for source in (
            "crates/ljos-cli/src/lib.rs",
            "crates/ljos-cli/src/runner_hooks.rs",
            "crates/ljos-cli/assets/grok/ljos.json",
            "docs/orgmode/integration.org",
        ):
            self.assertIn(source, text, source)
        self.assertNotIn('name = "runner-a"', text)
        self.assertNotIn('name = "runner-b"', text)
        self.assertNotIn("/home/you/.cargo/bin/ljos-mcp", text)
        self.assertNotIn("plus opencode and agy", text)
        self.assertIn("UserPromptSubmit and SessionEnd", text)
        self.assertIn(r'env_vars = [\"XDG_RUNTIME_DIR\"]', text)


# (name, ljos source). Relay runners cite runner_hooks.rs, which writes
# their hook file; the paths for those rows are still HARNESSES_EXAMPLE
# in crates/ljos-cli/src/lib.rs. Plugin bodies cite the asset they copy.
HARNESSES = (
    ("opencode", "crates/ljos-cli/assets/opencode/ljos.ts"),
    ("opencode-v2", "crates/ljos-cli/assets/opencode/ljos-v2.ts"),
    ("hermes", "crates/ljos-cli/src/lib.rs"),
    ("omp", "crates/ljos-cli/assets/omp/ljos.ts"),
    ("claude", "crates/ljos-cli/src/lib.rs"),
    ("codex", "crates/ljos-cli/src/lib.rs"),
    ("antigravity", "crates/ljos-cli/src/lib.rs"),
    ("cursor", "crates/ljos-cli/src/lib.rs"),
    ("grok", "crates/ljos-cli/assets/grok/ljos.json"),
    ("example-host", "crates/ljos-cli/src/lib.rs"),
    ("shell", "crates/ljos-cli/src/lib.rs"),
    ("windsurf", "crates/ljos-cli/src/runner_hooks.rs"),
    ("zed", "crates/ljos-cli/src/lib.rs"),
    ("vscode", "crates/ljos-cli/src/lib.rs"),
    ("claude-desktop", "crates/ljos-cli/src/lib.rs"),
    ("gemini", "crates/ljos-cli/src/runner_hooks.rs"),
    ("amazonq", "crates/ljos-cli/src/lib.rs"),
    ("kiro", "crates/ljos-cli/src/runner_hooks.rs"),
    ("copilot", "crates/ljos-cli/src/runner_hooks.rs"),
    ("factory", "crates/ljos-cli/src/runner_hooks.rs"),
    ("qwen", "crates/ljos-cli/src/runner_hooks.rs"),
    ("crush", "crates/ljos-cli/src/runner_hooks.rs"),
    ("cline", "crates/ljos-cli/src/runner_hooks.rs"),
    ("auggie", "crates/ljos-cli/src/runner_hooks.rs"),
    ("amp", "crates/ljos-cli/src/runner_hooks.rs"),
    ("goose", "crates/ljos-cli/src/runner_hooks.rs"),
    ("openhands", "crates/ljos-cli/src/runner_hooks.rs"),
    ("continue", "crates/ljos-cli/src/lib.rs"),
    ("roo", "crates/ljos-cli/src/lib.rs"),
    ("kilo", "crates/ljos-cli/src/lib.rs"),
    # aider_steps in lib.rs. Not a table in HARNESSES_EXAMPLE.
    # Also named in docs/orgmode/integration.org.
    ("aider", "crates/ljos-cli/src/lib.rs"),
)

# Placeholder tables in HARNESSES_EXAMPLE. Not runners a bare onboard finds.
EXAMPLE_SHAPES = (
    ("runner-with-a-command", "crates/ljos-cli/src/lib.rs"),
    ("runner-with-a-config-file", "crates/ljos-cli/src/lib.rs"),
    ("runner-with-a-json-config", "crates/ljos-cli/src/lib.rs"),
)


if __name__ == "__main__":
    unittest.main()
