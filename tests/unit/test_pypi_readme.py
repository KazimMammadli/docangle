import os
import re

from tools import pypi_readme

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = pypi_readme.REPO


def test_links_images_anchors_and_absolute_targets():
    src = "[a](docs/x.md#s) ![i](docs/images/p.webp) [u](https://e.org/x) [h](#top)"
    assert pypi_readme.rewrite(src) == (
        f"[a](https://github.com/{R}/blob/main/docs/x.md#s) ![i](https://raw.githubusercontent.com/{R}/main/docs/images/p.webp) "
        "[u](https://e.org/x) [h](#top)")


def test_nested_badge_link_is_rewritten():
    assert pypi_readme.rewrite("[![b](https://i.org/b.svg)](LICENSE)").endswith(f"](https://github.com/{R}/blob/main/LICENSE)")


def test_mermaid_block_is_replaced():
    out = pypi_readme.rewrite("a\n```mermaid\nflowchart TD\n```\nb")
    assert "mermaid" not in out and out.startswith("a\n") and out.endswith("\nb")


def test_real_readme_has_no_relative_target_left():
    text = pypi_readme.rewrite(open(os.path.join(ROOT, "README.md"), encoding="utf-8").read())
    assert not re.findall(r"\]\((?!https?:|#|mailto:)[^)\s]+\)", text) and "```mermaid" not in text
