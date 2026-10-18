"""Tables of the open-source comparison, generated from the raw result files that `bench/compare_open_models.py run` writes.

  python -m bench.compare_report summarize reports/benchmark/raw_*.json.gz --out reports/benchmark/RESULTS.md
  python -m bench.compare_report fill-docs reports/benchmark/raw_*.json.gz --docs README.md docs/05-comparison.md [--check]

`fill-docs` rewrites the blocks between ``<!-- generated:KEY -->`` and ``<!-- /generated -->`` in the given Markdown files, so that no number of
chapter 5 is typed by hand; `--check` changes nothing and exits 1 when a block is out of date (tests/unit/test_docs.py runs it).

Statistics (docs/05-comparison.md 5.1): the truth is the quadrant that was applied; cases within 5 degrees of a quadrant boundary are left out; a tool that
gives no answer is wrong; intervals are 95 % Wilson intervals whose sample size is the number of PAGES, not of cases.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import re
import sys

import numpy as np

from bench.compare_open_models import STRAIGHT, DocAngle, DocAngleCrop, DocAngleHough, MinAreaRect

SHORT = {"docangle 4.4": "docangle", "docangle 4.4 + doc_crop": "docangle + doc_crop", "PP-LCNet_x1_0_doc_ori": "PP-LCNet", "docTR page orientation": "docTR",
         "DocOrient 0.4.1": "DocOrient", "EfficientNetV2-S orientation model": "EfficientNetV2", "Tesseract 5 OSD": "Tesseract OSD",
         "docangle fine tilt by Hough": "docangle Hough", "textbook cv2.minAreaRect deskew": "minAreaRect"}
UNSEEN = ("az", "ext_funsd")       # pools that docangle's own classifier never saw (docs/04-evaluation-protocol.md 4.2)
Z = 1.96


def short(name):
    base = name[:-len(STRAIGHT)] if name.endswith(STRAIGHT) else name.split(" (")[0]
    return SHORT.get(base, base) + (" + straightening" if name.endswith(STRAIGHT) else "")


# ------------------------------------------------------------------------------------------------ statistics #
def cluster_ci(err, clusters):
    """Mean of ``err`` (1 = wrong) over the cases and a 95 % Wilson interval whose sample size is the number of PAGES (clusters), not of cases.

    The cases of one page (its four turned copies, its three photo levels) are not independent, so counting them as independent would make the interval too
    tight. Counting each page as one trial is conservative. Unlike a bootstrap over pages it stays sensible when there are few errors or none: a bootstrap of
    a row without any error collapses to [0, 0], and of a row with one error it is narrower than the honest bound for the row without."""
    err = np.asarray(err, float)
    n = len(set(clusters))
    p = float(err.mean())
    centre = (p + Z * Z / (2 * n)) / (1 + Z * Z / n)
    half = Z * np.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / (1 + Z * Z / n)
    return p, float(max(0.0, centre - half)), float(min(1.0, centre + half))


def sign_test(b, d):
    """Two-sided exact sign test: p-value of a split b : d when both outcomes are equally likely."""
    n = b + d
    return 1.0 if n == 0 else min(1.0, 2.0 * sum(math.comb(n, i) for i in range(min(b, d) + 1)) / 2 ** n)


def paired(ok, c, base):
    """Same cases, two tools: ((cases only ``base`` got right, cases only ``c`` got right), (pages where base was better, pages where c was better), sign-test p).
    A page counts for the tool that won more of its cases; the test is over pages because the cases of one page are not independent."""
    per = {}
    for r in ok:
        b_ok, c_ok = r[base]["q"] == r["gt_q"], r[c]["q"] == r["gt_q"]
        e = per.setdefault(r["page"], [0, 0])
        e[0] += int(b_ok and not c_ok)
        e[1] += int(c_ok and not b_ok)
    cases = (sum(v[0] for v in per.values()), sum(v[1] for v in per.values()))
    pages = (sum(v[0] > v[1] for v in per.values()), sum(v[1] > v[0] for v in per.values()))
    return cases, pages, sign_test(*pages)


def quadrant_table(rows, cands, base):
    ok = [r for r in rows if not r["ambiguous"]]
    lines = ["| tool | cases | wrong quadrant % [95 % interval] | no answer | median ms | p95 ms | same cases: docangle-only right / this-only right (pages: docangle better / this better, sign test) |",
             "|---|---|---|---|---|---|---|"]
    for c in cands:
        err = [0.0 if r[c]["q"] == r["gt_q"] else 1.0 for r in ok]
        m, lo, hi = cluster_ci(err, [r["page"] for r in ok])
        ms = np.array([r[c]["ms"] for r in ok])
        none = sum(r[c]["q"] is None for r in ok)
        if c == base:
            pair = "—"
        else:
            (b, d), (pb, pd), pv = paired(ok, c, base)
            pair = f"{b} / {d} (pages {pb} / {pd}, {'p < 0.001' if pv < 0.001 else f'p = {pv:.3f}'})"
        lines.append(f"| {short(c)} | {len(ok)} | **{100 * m:.1f}** [{100 * lo:.1f}, {100 * hi:.1f}] | {none} | {np.median(ms):.0f} | {np.percentile(ms, 95):.0f} | {pair} |")
    return "\n".join(lines)


def per_group_table(rows, cands, key):
    groups = sorted({r[key] for r in rows if not r["ambiguous"]})
    head = "| " + key + " (cases) | " + " | ".join(short(c) for c in cands) + " |\n|---|" + "---|" * len(cands)
    out = [head]
    for g in groups:
        sub = [r for r in rows if r[key] == g and not r["ambiguous"]]
        out.append(f"| {g} ({len(sub)}) | " + " | ".join(f"{100 * np.mean([r[c]['q'] != r['gt_q'] for r in sub]):.1f}" for c in cands) + " |")
    return "\n".join(out)


def fine_table(rows, cands):
    lines = ["| estimator | cases | median error ° | within 0.5° % | within 1° % | error > 5° % [95 % interval] | median ms |", "|---|---|---|---|---|---|---|"]
    for c in cands:
        sub = [r for r in rows if "tilt" in r[c]]
        if not sub:
            continue
        e = np.array([abs(((r[c]["tilt"] - r["gt"]) + 45.0) % 90.0 - 45.0) for r in sub])
        big = cluster_ci((e > 5).astype(float), [r["page"] for r in sub])
        lines.append(f"| {short(c)} | {len(sub)} | {np.median(e):.2f} | {100 * np.mean(e <= 0.5):.1f} | {100 * np.mean(e <= 1.0):.1f} | {100 * big[0]:.1f} [{100 * big[1]:.1f}, {100 * big[2]:.1f}] | {np.median([r[c]['ms'] for r in sub]):.0f} |")
    return "\n".join(lines)


def selective_table(rows, cands, base):
    """What the tools do when they may hold pages back for a person (docs/04 4.4, equal review rate).

    docangle uses its review rule. A tool that has a score holds back its least certain pages, the same share of pages as docangle held back; the last column says
    how many pages such a tool would have to hold back to be as reliable as docangle on the pages it answers. A tool with its own 'not reliable' flag, or one that
    stays silent when it has no answer, is also shown at that operating point. Pages that are held back are not counted."""
    ok = [r for r in rows if not r["ambiguous"]]
    n = len(ok)
    pages = np.array([r["page"] for r in ok])
    held_base = np.array([bool(r[base].get("flag")) or r[base]["q"] is None for r in ok])
    k = int(round(float(held_base.mean()) * n))
    base_wrong = np.array([r[base]["q"] != r["gt_q"] for r in ok])
    target = float(base_wrong[~held_base].mean()) if (~held_base).any() else 0.0        # docangle's error rate among the pages it answers
    lines = ["| tool: which cases it holds back | held back, % of cases | wrong among the cases it answered: n / N | % [95 % interval over pages] | cases it must hold back to match docangle's rate, % |",
             "|---|---|---|---|---|"]

    def must_hold(order, wrong):
        """Smallest share of the least certain pages whose removal brings the error rate of the rest to ``target`` (None: never)."""
        w = wrong[order].astype(float)
        left_wrong = w.sum() - np.concatenate([[0.0], np.cumsum(w)])          # errors left after holding back the first i pages
        left = n - np.arange(n + 1)
        ok_i = np.nonzero(left_wrong <= target * left + 1e-12)[0]
        ok_i = ok_i[left[ok_i] > 0]
        return None if len(ok_i) == 0 else 100.0 * ok_i[0] / n

    def add(label, held, wrong, order=None):
        keep = ~held
        if not keep.any():
            return
        m, lo, hi = cluster_ci(wrong[keep], list(pages[keep]))
        must = "—" if order is None else ("never" if (v := must_hold(order, wrong)) is None else f"{v:.1f}")
        lines.append(f"| {label} | {100 * held.mean():.1f} | {int(wrong[keep].sum())} / {int(keep.sum())} | **{100 * m:.1f}** [{100 * lo:.1f}, {100 * hi:.1f}] | {must} |")

    for c in cands:
        wrong = np.array([r[c]["q"] != r["gt_q"] for r in ok])
        has_conf = any("conf" in r[c] for r in ok)
        has_flag = any("flag" in r[c] for r in ok)
        silent = np.array([r[c]["q"] is None for r in ok])
        if has_conf and has_flag:                                   # docangle and its variants
            add(f"{short(c)}: its own review rule", np.array([bool(r[c].get("flag")) or r[c]["q"] is None for r in ok]), wrong)
            continue
        if has_conf:                                                # least certain first; a missing answer counts as the least certain
            score = np.array([r[c].get("conf", -1.0) if r[c]["q"] is not None else -1.0 for r in ok])
            order = np.argsort(score, kind="stable")
            held = np.zeros(n, bool)
            held[order[:k]] = True
            add(f"{short(c)}: its least certain cases, same share as docangle", held, wrong, order)
        if has_flag:
            add(f"{short(c)}: its own 'not reliable' flag", np.array([bool(r[c].get("flag")) or r[c]["q"] is None for r in ok]), wrong)
        elif silent.any():
            add(f"{short(c)}: silent when it has no answer", silent, wrong)
    return "\n".join(lines)


# ------------------------------------------------------------------------------------------------- blocks #
def load_runs(files):
    """Raw result files, merged by mode: files of one mode hold the same cases with other candidates, and are joined case by case."""
    runs = {}
    for path in files:
        d = json.load(gzip.open(path, "rt"))
        if d["mode"] in runs:
            base = runs[d["mode"]]
            index = {(r["set"], r["pool"], r["level"], r["page"], r["gt"]): r for r in base["rows"]}
            for r in d["rows"]:
                k = (r["set"], r["pool"], r["level"], r["page"], r["gt"])
                if k in index:
                    index[k].update({c: r[c] for c in d["candidates"] if c in r})
            base["candidates"] += [c for c in d["candidates"] if c not in base["candidates"]]
            base["paths"].append(path)
        else:
            d["paths"] = [path]
            runs[d["mode"]] = d
    return runs


def slug(s):
    return "whole" if "whole frame" in s else "cutout" if "cut out" in s else "main"


SUMMARY_COLUMNS = [("quarter/main", "exact quarter turns"), ("handheld/main", "hand-held photo (quadrant ± 25°)"), ("uniform/main", "any angle"),
                   ("smartdoc/cutout", "real phone frames, page cut out"), ("smartdoc/whole", "real phone frames, whole frame")]


def summary_table(runs):
    """One line per as-shipped tool: wrong-quadrant % in each setting, and the median time per page on the 'any angle' cases."""
    cols = [(k, h) for k, h in SUMMARY_COLUMNS if k.split("/")[0] in runs]
    shipped = [c for c in runs["uniform"]["candidates"] if c not in (DocAngleHough.name, MinAreaRect.name) and not c.endswith(STRAIGHT)]
    lines = ["| tool | " + " | ".join(h for _, h in cols) + " | median ms per page, any angle |", "|---|" + "---|" * (len(cols) + 1)]
    for c in shipped:
        cells = []
        for k, _ in cols:
            mode, sl = k.split("/")
            rows = [r for r in runs[mode]["rows"] if slug(r["set"]) == sl and not r["ambiguous"] and c in r]
            cells.append("—" if not rows else f"{100 * np.mean([r[c]['q'] != r['gt_q'] for r in rows]):.1f} %")
        ms = [r[c]["ms"] for r in runs["uniform"]["rows"] if not r["ambiguous"] and c in r]
        lines.append(f"| {short(c)} | " + " | ".join(cells) + f" | {np.median(ms):.0f} |")
    return "\n".join(lines)


def speed_table(runs):
    """Median (95th percentile) milliseconds per page of every as-shipped tool in every setting; the whole call, one case at a time, CPU, two threads."""
    cols = [(k, h) for k, h in SUMMARY_COLUMNS if k.split("/")[0] in runs]
    shipped = [c for c in runs["uniform"]["candidates"] if c not in (DocAngleHough.name, MinAreaRect.name) and not c.endswith(STRAIGHT)]
    lines = ["| tool | " + " | ".join(h for _, h in cols) + " |", "|---|" + "---|" * len(cols)]
    for c in shipped:
        cells = []
        for k, _ in cols:
            mode, sl = k.split("/")
            ms = [r[c]["ms"] for r in runs[mode]["rows"] if slug(r["set"]) == sl and not r["ambiguous"] and c in r]
            cells.append("—" if not ms else f"{np.median(ms):.0f} ({np.percentile(ms, 95):.0f})")
        lines.append(f"| {short(c)} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def blocks(runs):
    """[(key, heading, markdown)]: every table. The same blocks fill RESULTS.md and the generated parts of docs/05-comparison.md and the README."""
    out = []
    for mode, d in runs.items():
        rows, cands = d["rows"], d["candidates"]
        quad = [c for c in cands if c not in (DocAngleHough.name, MinAreaRect.name)]
        for s in sorted({r["set"] for r in rows}):
            sub = [r for r in rows if r["set"] == s]
            k = f"{mode}/{slug(s)}"
            out.append((f"{k}/quadrant", f"Quadrant task — {s}", quadrant_table(sub, quad, DocAngle.name)))
            unseen = [r for r in sub if r["pool"] in UNSEEN]
            if unseen:
                out.append((f"{k}/unseen", f"Only the pools docangle's own classifier never saw ({', '.join(UNSEEN)}) — {s}", quadrant_table(unseen, quad, DocAngle.name)))
            if any("conf" in r.get(DocAngle.name, {}) for r in sub):
                out.append((f"{k}/selective", f"Pages held back for a person — {s}", selective_table(sub, quad, DocAngle.name)))
            out.append((f"{k}/pool", f"Wrong-quadrant % by pool — {s}", per_group_table(sub, quad, "pool")))
            if len({r["level"] for r in sub}) > 1:
                out.append((f"{k}/level", f"Wrong-quadrant % by degradation level — {s}", per_group_table(sub, quad, "level")))
            if any("tilt" in r.get(DocAngle.name, {}) for r in sub) and mode != "quarter":
                fine = [c for c in cands if c in (DocAngle.name, DocAngleCrop.name, DocAngleHough.name, MinAreaRect.name)]
                out.append((f"{k}/fine", f"Fine-angle task — {s}", fine_table(sub, fine)))
    if "uniform" in runs:
        out.append(("summary", "Summary", summary_table(runs)))
        out.append(("speed", "Speed", speed_table(runs)))
    return out


def summarize(a):
    runs = load_runs(a.files)
    out = ["# Benchmark results (generated by `bench/compare_report.py summarize`; do not edit by hand)\n"]
    for d in runs.values():
        out.append(f"## {', '.join(os.path.basename(p) for p in d['paths'])} — mode `{d['mode']}`, {len(d['rows'])} cases\n")
        out.append("Versions: " + ", ".join(f"{k} {v}" for k, v in d["versions"].items()) + "\n")
        for key, heading, md in blocks({d["mode"]: d}):
            if key not in ("summary", "speed"):
                out.append(f"### {heading}\n\n{md}\n")
    if "uniform" in runs:
        out.append(f"## Summary (wrong-quadrant %, as-shipped tools)\n\n{summary_table(runs)}\n")
        out.append(f"## Speed (median, 95th percentile in brackets, ms per page)\n\n{speed_table(runs)}\n")
    text = "\n".join(out)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0


GEN = re.compile(r"(?P<open><!-- generated:(?P<key>[\w/]+) -->)\n.*?\n?(?P<close><!-- /generated -->)", re.S)


def fill_text(text, table):
    """Replace the body of every ``<!-- generated:KEY -->`` ... ``<!-- /generated -->`` block by the table of that key."""
    def one(m):
        if m["key"] not in table:
            raise KeyError(f"no table named {m['key']!r}; known: {', '.join(table)}")
        return f"{m['open']}\n{table[m['key']]}\n{m['close']}"
    return GEN.sub(one, text)


def fill_docs(a):
    table = {k: md for k, _, md in blocks(load_runs(a.files))}
    stale = []
    for path in a.docs:
        with open(path, encoding="utf-8") as fh:
            old = fh.read()
        new = fill_text(old, table)
        if new != old:
            stale.append(path)
            if not a.check:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new)
    print(("stale: " if a.check else "updated: ") + (", ".join(stale) or "nothing"))
    return 1 if (a.check and stale) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("summarize", help="write all tables as one Markdown file")
    s.add_argument("files", nargs="+", help="raw result files")
    s.add_argument("--out", default=None)
    f = sub.add_parser("fill-docs", help="rewrite the generated table blocks of the given Markdown files from the raw results")
    f.add_argument("files", nargs="+", help="raw result files")
    f.add_argument("--docs", nargs="+", required=True)
    f.add_argument("--check", action="store_true", help="change nothing; exit 1 if a block is out of date")
    a = ap.parse_args(argv)
    return fill_docs(a) if a.cmd == "fill-docs" else summarize(a)


if __name__ == "__main__":
    sys.exit(main())
