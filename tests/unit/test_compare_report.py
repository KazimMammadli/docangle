"""The statistics and the table generator of the open-source comparison (bench/compare_report.py)."""
import numpy as np
import pytest

from bench import compare_report as cr
from bench.compare_open_models import DocAngle


def test_wilson_interval_without_errors_has_an_upper_bound_that_shrinks_with_pages():
    m, lo, hi = cr.cluster_ci(np.zeros(40), [f"p{i}" for i in range(10)])
    assert (m, lo) == (0.0, 0.0) and hi == pytest.approx(cr.Z ** 2 / (10 + cr.Z ** 2), abs=1e-9)
    assert cr.cluster_ci(np.zeros(400), [f"p{i}" for i in range(100)])[2] < hi


def test_interval_counts_pages_not_cases():
    err = np.array([1.0] * 4 + [0.0] * 36)                    # 10 % wrong
    wide = cr.cluster_ci(err, [f"p{i // 4}" for i in range(40)])          # 10 pages with 4 copies each
    narrow = cr.cluster_ci(err, [f"p{i}" for i in range(40)])             # as if every case were its own page
    assert wide[0] == narrow[0] == pytest.approx(0.1) and (wide[2] - wide[1]) > (narrow[2] - narrow[1])


def test_generated_blocks_are_replaced_and_unknown_keys_fail():
    text = "intro\n<!-- generated:a/b -->\nold\n<!-- /generated -->\noutro"
    assert cr.fill_text(text, {"a/b": "| new |"}) == "intro\n<!-- generated:a/b -->\n| new |\n<!-- /generated -->\noutro"
    with pytest.raises(KeyError):
        cr.fill_text(text, {"x": "y"})


def row(page, gt_q, base_q, base_flag, other_q, other_conf):
    return {"page": page, "ambiguous": False, "gt_q": gt_q, DocAngle.name: {"q": base_q, "ms": 1.0, "conf": 0.9, "flag": base_flag},
            "other": {"q": other_q, "ms": 1.0, "conf": other_conf}}


def test_equal_review_rate_holds_back_the_least_certain_pages_of_the_other_tool():
    # docangle holds back 1 of 10 pages; the other tool has 2 wrong answers, the least certain of which is among its two lowest scores
    rows = [row(f"p{i}", 0, 0, i == 0, 0, 0.9) for i in range(10)]
    rows[3]["other"] = {"q": 1, "ms": 1.0, "conf": 0.2}        # wrong and the least certain: held back
    rows[4]["other"] = {"q": 1, "ms": 1.0, "conf": 0.6}        # wrong and more certain: stays
    table = cr.selective_table(rows, [DocAngle.name, "other"], DocAngle.name)
    lines = {ln.split("|")[1].strip(): ln for ln in table.splitlines()[2:]}
    assert "0 / 9" in lines["docangle: its own review rule"]
    assert "1 / 9" in lines["other: its least certain cases, same share as docangle"]
    assert lines["other: its least certain cases, same share as docangle"].rstrip().endswith("| 20.0 |")     # both of its wrong pages must go to reach docangle's 0 %


def test_sign_test_is_exact_and_two_sided():
    assert cr.sign_test(0, 0) == 1.0
    assert cr.sign_test(5, 5) == 1.0
    assert cr.sign_test(7, 0) == pytest.approx(2 / 128)
    assert cr.sign_test(0, 7) == cr.sign_test(7, 0)


def test_paired_counts_count_pages_by_who_won_more_of_their_cases():
    rows = [row("a", 0, 0, False, 1, 0.5), row("a", 0, 0, False, 1, 0.5), row("a", 0, 1, False, 0, 0.5),    # page a: docangle better in 2 cases, other in 1
            row("b", 0, 1, False, 0, 0.5)]                                                                   # page b: other better
    (b, d), (pb, pd), p = cr.paired(rows, "other", DocAngle.name)
    assert (b, d) == (2, 2) and (pb, pd) == (1, 1) and p == 1.0


def test_page_interval_is_wider_than_the_case_interval_and_zero_without_flips():
    from collections import Counter
    from bench.page_interval import interval
    cases, flips = Counter({f"p{i}": 4 for i in range(100)}), Counter({"p0": 4, "p1": 4})
    m, lo, hi, k, n, pages, bad = interval(cases, flips, draws=2000)
    assert (k, n, pages, bad) == (8, 400, 100, 2) and lo < m < hi and hi - lo > 1.0
    assert interval(cases, Counter(), draws=200)[:3] == (0.0, 0.0, 0.0)
