#!/usr/bin/env bash
# Fail when a handbook rebuild differs from the committed HTML.
# org/build.sh is run first. This step then puts back the two tokens
# that move on an unchanged export, and runs git diff --exit-code.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

python3 - <<'PY'
import pathlib
import re
import subprocess
import sys

root = pathlib.Path(".").resolve()

# ox-html writes this with format-time-string and
# org-html-metadata-timestamp-format ("%Y-%m-%d %a %H:%M").
stamp_re = re.compile(r"<!-- \d{4}-\d{2}-\d{2} [A-Za-z]{3} \d{2}:\d{2} -->")
# org-export-format-reference prints (random #x10000000) as org%07x.
id_re = re.compile(r"org[0-9a-f]{7}")


def show(rel: str) -> bytes | None:
    proc = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True)
    if proc.returncode != 0:
        return None
    return proc.stdout


def align(committed: str, generated: str) -> str:
    """Swap the generated stamps and ids for the committed ones, in order.

    Counts must match. A changed heading stays on its line, so the diff
    still shows it. A different number of ids or stamps is left alone.
    """
    stamps_c = stamp_re.findall(committed)
    stamps_g = stamp_re.findall(generated)
    ids_c = id_re.findall(committed)
    ids_g = id_re.findall(generated)
    if len(stamps_c) != len(stamps_g) or len(ids_c) != len(ids_g):
        return generated

    def sub(text: str, regex: re.Pattern[str], repls: list[str]) -> str:
        found = iter(repls)
        return regex.sub(lambda _match: next(found), text)

    return sub(sub(generated, stamp_re, stamps_c), id_re, ids_c)


# A removed org note is not republished, so the old HTML would still
# match the commit. Drop generated pages whose source is gone.
orgs = {path.stem for path in (root / "orgmode" / "handbook").glob("*.org")}
for html in (root / "handbook").glob("*.html"):
    if html.stem not in orgs:
        html.unlink()

for html in sorted((root / "handbook").glob("*.html")):
    rel = html.relative_to(root).as_posix()
    blob = show(rel)
    if blob is None:
        continue
    generated = html.read_bytes()
    try:
        aligned = align(blob.decode("utf-8"), generated.decode("utf-8")).encode("utf-8")
    except UnicodeError:
        continue
    if aligned != generated:
        html.write_bytes(aligned)

untracked = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard", "--", "handbook"],
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
fresh = [path for path in untracked if path.endswith(".html")]
if fresh:
    subprocess.run(["git", "add", "-N", "--", *fresh], check=True)

sys.exit(
    subprocess.call(
        ["git", "--no-pager", "diff", "--exit-code", "--", "handbook"]
    )
)
PY
