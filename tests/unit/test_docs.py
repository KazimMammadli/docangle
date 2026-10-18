"""The book must not rot: generated parts match the code and every relative link resolves."""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINK = re.compile(r"\]\(([^)\s]+)\)")


def test_configuration_appendix_matches_the_code():
    from tools.gen_config_doc import OUT, render
    assert open(OUT, encoding="utf-8").read() == render(), "run: python -m tools.gen_config_doc"


def test_relative_links_in_the_documentation_resolve():
    files = glob.glob(os.path.join(ROOT, "docs", "**", "*.md"), recursive=True) + [os.path.join(ROOT, n) for n in ("README.md", "CONTRIBUTING.md", "CHANGELOG.md", "NOTICE.md")]
    broken = []
    for f in files:
        if not os.path.exists(f):
            continue
        for target in LINK.findall(open(f, encoding="utf-8").read()):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = os.path.normpath(os.path.join(os.path.dirname(f), target.split("#")[0]))
            if not os.path.exists(path):
                broken.append(f"{os.path.relpath(f, ROOT)} -> {target}")
    assert not broken, "\n".join(broken)


def test_comparison_tables_match_the_stored_results():
    """Every table of chapter 5 and of the README comparison is generated from reports/benchmark/raw_*.json.gz and must not be edited by hand."""
    import pytest
    from bench import compare_report
    raw = sorted(glob.glob(os.path.join(ROOT, "reports", "benchmark", "raw_*.json.gz")))
    if not raw:
        pytest.skip("no stored comparison results")
    docs = [os.path.join(ROOT, "README.md"), os.path.join(ROOT, "docs", "05-comparison.md")]
    az = os.path.join(ROOT, "docs", "az", "README.md")                 # private Azerbaijani summary, not in the public tree
    docs += [az] if os.path.exists(az) else []
    assert compare_report.main(["fill-docs", *raw, "--docs", *docs, "--check"]) == 0, "run: python -m bench.compare_report fill-docs reports/benchmark/raw_*.json.gz --docs README.md docs/05-comparison.md"


def test_the_book_has_no_unfinished_markers():
    bad = []
    for f in glob.glob(os.path.join(ROOT, "docs", "**", "*.md"), recursive=True) + [os.path.join(ROOT, "README.md")]:
        for i, line in enumerate(open(f, encoding="utf-8").read().splitlines(), 1):
            if re.search(r"TBD|TODO|@@|<!--COMPARISON-->|[Ww]ork in progress", line):
                bad.append(f"{os.path.relpath(f, ROOT)}:{i}: {line.strip()[:80]}")
    assert not bad, "\n".join(bad)


def test_markdown_links_anchors_and_named_paths_resolve():
    from tools.check_links import check
    _, n_links, problems = check(ROOT)
    assert n_links > 50 and not problems, "\n".join(sorted(set(problems)))
