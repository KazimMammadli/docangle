"""Make README.md readable on the PyPI project page (run by .github/workflows/publish.yml before the build, on the runner's copy only).

PyPI shows the README outside the repository: relative links and images break and Mermaid is not drawn. Relative targets become
absolute GitHub URLs; the Mermaid diagram becomes a pointer to the GitHub page.
"""

import re
import sys

REPO = "KazimMammadli/docangle"
_IMAGES = (".webp", ".png", ".jpg", ".jpeg", ".svg", ".gif")
_REL = re.compile(r"\]\((?!https?:|#|mailto:)([^)\s]+)\)")
_MERMAID = re.compile(r"```mermaid\n.*?```", re.S)


def _absolute(m):
    path = m.group(1)
    if path.split("#")[0].lower().endswith(_IMAGES):
        return f"](https://raw.githubusercontent.com/{REPO}/main/{path})"
    return f"](https://github.com/{REPO}/blob/main/{path})"


def rewrite(text: str) -> str:
    text = _MERMAID.sub(f"The pipeline diagram is drawn on the [GitHub page](https://github.com/{REPO}#how-it-works).", text)
    return _REL.sub(_absolute, text)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(rewrite(text))
