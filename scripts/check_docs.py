"""Check local Markdown links/anchors and current integration source references.

This is an offline structural check. It does not claim external URLs work or
that a documented integration has passed live verification.
"""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^\n)]+)\)")
SOURCE = re.compile(r"`((?:src|web|scripts|integrations|docs|runtime-skills|agents|\.agents)/[\w./\[\]+-]+)`")


def headings(path: Path) -> set[str]:
    counts, result = Counter(), set()
    fence = False
    for line in path.read_text().splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
        if fence:
            continue
        match = re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?$", line)
        if not match:
            continue
        title = re.sub(r"<[^>]*>", "", match[1]).lower()
        slug = re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
        result.add(slug + (f"-{counts[slug]}" if counts[slug] else ""))
        counts[slug] += 1
    return result


def check() -> list[str]:
    files = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode().split("\0")
    errors = []
    for name in sorted(set(files)):
        path = ROOT / name
        if path.suffix != ".md" or not path.is_file():
            continue
        text = path.read_text()
        for match in LINK.finditer(text):
            raw = match[1].strip()
            raw = raw[1:raw.index(">")] if raw.startswith("<") and ">" in raw else raw.split(' "', 1)[0]
            parsed = urlsplit(raw)
            if parsed.scheme or raw.startswith("//"):
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            line = text.count("\n", 0, match.start()) + 1
            if not target.exists():
                errors.append(f"{name}:{line}: missing local link {raw}")
            elif parsed.fragment and target.suffix == ".md" and unquote(parsed.fragment) not in headings(target):
                errors.append(f"{name}:{line}: missing Markdown anchor {raw}")
        if name.startswith("docs/history/"):
            continue
        for match in SOURCE.finditer(text):
            if not (ROOT / match[1]).exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{name}:{line}: missing current source reference {match[1]}")
    registry = ROOT / "src/learning_lab/source_index.py"
    tree = ast.parse(registry.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SOURCES" for t in node.targets):
            for source_id, value in ast.literal_eval(node.value).items():
                if not (ROOT / value[0]).is_file():
                    errors.append(f"source_index.py: {source_id} refers to missing integration file {value[0]}")
    # Superseded diagrams belong to the immutable v0.2 source snapshot. Current
    # architecture uses an inline diagram; never regenerate historical files.
    archive = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_archive.py")],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if archive.returncode:
        errors.append("v0.2 source archive failed integrity verification: " + archive.stdout + archive.stderr)
    return errors


if __name__ == "__main__":
    problems = check()
    if problems:
        print("\n".join(problems))
        raise SystemExit(1)
    print("Local Markdown links, anchors, integration paths and v0.2 archive integrity passed (external URLs not probed).")
