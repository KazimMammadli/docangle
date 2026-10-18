"""Check the relative links and #anchors of the Markdown files (GitHub's heading-slug rules), and the repository paths named in code spans.

  python -m tools.check_links            # README, CONTRIBUTING, CHANGELOG, NOTICE, MODEL_CARD, models/README, data/README, docs/**
  python -m tools.check_links --root DIR

Exit status 1 when something does not resolve. External links (http, https, mailto) are not fetched. A path in a code span such as
`reports/benchmark/RESULTS.md` or `bench/run.py` must exist, unless it points into the runtime directories that the data scripts create
(`data/cache`, `data/external`, `data/splits`, `data/az_test_pages`, ...: data that is not part of the repository).
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP = ["README.md", "CONTRIBUTING.md", "CHANGELOG.md", "NOTICE.md", "MODEL_CARD.md", "models/README.md", "data/README.md"]
CODE_PATH = re.compile(r"`((?:reports|bench|tools|src|docs|models|data|tests|docangle)/[A-Za-z0-9_./-]+)`")
RUNTIME_DIRS = ("data/cache", "data/external", "data/splits", "data/az_test_pages", "data/invoices_rvl_certified", "data/invoices_rvl_test",
                "models/experimental", "models/checkpoints", "reports/failures")


def _plain(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return text.replace("`", "").replace("*", "").strip()


def slug(heading: str) -> str:
    out = []
    for ch in _plain(heading).lower():
        if ch in "-_ ":
            out.append(ch)
        elif unicodedata.category(ch)[0] not in "PSCZ":
            out.append(ch)
    return "".join(out).replace(" ", "-")


def anchors(path: str) -> set:
    seen, found, in_code = {}, set(), False
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        m = None if in_code else re.match(r"#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m:
            s = slug(m.group(1))
            n = seen.get(s, 0)
            seen[s] = n + 1
            found.add(s if n == 0 else f"{s}-{n}")
    return found


def check(root: str):
    files = [os.path.join(root, f) for f in TOP if os.path.exists(os.path.join(root, f))]
    files += sorted(glob.glob(os.path.join(root, "docs", "**", "*.md"), recursive=True))
    problems, cache, n_links = [], {}, 0
    for f in files:
        rel_f = os.path.relpath(f, root)
        text = open(f, encoding="utf-8").read()
        body = re.sub(r"```.*?```", "", text, flags=re.S)
        for m in re.finditer(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", body):
            target = m.group(1)
            if re.match(r"(https?|mailto):", target):
                continue
            n_links += 1
            path, _, frag = target.partition("#")
            dest = f if not path else os.path.normpath(os.path.join(os.path.dirname(f), path))
            if not os.path.exists(dest):
                problems.append(f"{rel_f}: link target does not exist: {target}")
            elif frag and dest.endswith(".md"):
                if dest not in cache:
                    cache[dest] = anchors(dest)
                if frag not in cache[dest]:
                    problems.append(f"{rel_f}: no heading for anchor: {target}")
        for m in CODE_PATH.finditer(body):
            p = m.group(1).rstrip(".")
            if p.endswith("/") or "*" in p or p.startswith(RUNTIME_DIRS):
                continue
            if not os.path.exists(os.path.join(root, p)) and not os.path.exists(os.path.join(root, p + ".py")) \
                    and not os.path.exists(os.path.join(root, p.replace(".", "/") + ".py")):
                problems.append(f"{rel_f}: named path does not exist: {p}")
    return files, n_links, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT)
    a = ap.parse_args()
    files, n_links, problems = check(a.root)
    for p in sorted(set(problems)):
        print(p)
    print(f"{len(files)} files, {n_links} relative links, {len(set(problems))} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
