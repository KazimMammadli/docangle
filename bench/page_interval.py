"""Page-level (cluster-bootstrap) interval of the flip rate of a stored `bench.run` result.

  python -m bench.page_interval reports/bench_final_v4_4.json --pools az invoices tobacco_cert rvl_heldout --out reports/page_interval_v4_4.txt

The cases of a benchmark are rotations of far fewer distinct pages, and the flips sit on few of them, so the case-level interval is too narrow. The pages of the
pools are rebuilt with the same seeds as the run (`bench.run.make_cases`), the flips (error > 45 deg) are read from the stored list of errors, and whole pages
(with all their cases) are resampled 10 000 times. Also reported without the one source page that is itself sideways.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter

import numpy as np

from .metrics import circ_err
from .run import make_cases

SIDEWAYS = "certified_invoice_030.png"
CAP = 40                               # bench.run stores at most this many errors > 5 deg per cell


def collect(result, pools):
    cases, flips = Counter(), Counter()
    for r in result["results"]:
        if r["dataset"] not in pools:
            continue
        a = result["args"]
        cs, _, _ = make_cases(r["dataset"], r["level"], r["angle_mode"], a["seeds"], a["n"])
        assert len(cs) == r["summary"]["n"], (r["dataset"], r["level"], "case list differs from the run")
        bad = r["errors_gt5"]
        assert len(bad) < CAP, f"{r['dataset']}/{r['level']}: the stored error list was cut at {CAP}"
        for f, *_ in cs:
            cases[os.path.basename(f)] += 1
        for b in bad:
            if circ_err(b["pred"], b["gt"]) > 45.0:
                flips[b["file"]] += 1
    return cases, flips


def interval(cases, flips, drop=(), draws=10000, seed=0):
    pages = [p for p in cases if p not in drop]
    n = np.array([cases[p] for p in pages], float)
    k = np.array([flips[p] for p in pages], float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(pages), size=(draws, len(pages)))
    rate = k[idx].sum(1) / n[idx].sum(1) * 100
    return k.sum() / n.sum() * 100, np.percentile(rate, 2.5), np.percentile(rate, 97.5), int(k.sum()), int(n.sum()), len(pages), int((k > 0).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result")
    ap.add_argument("--pools", nargs="+", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    result = json.load(open(a.result))
    cases, flips = collect(result, set(a.pools))
    lines = [f"{a.result}: pools {', '.join(a.pools)}; flips = error > 45 deg; 10 000 resamples of whole pages"]
    for label, drop in (("all pages", ()), ("without the sideways source page", (SIDEWAYS,))):
        m, lo, hi, k, n, pages, bad_pages = interval(cases, flips, drop)
        lines.append(f"  {label:34s} {k} flips in {n} cases of {pages} pages ({bad_pages} pages flip): {m:.2f} % [{lo:.2f}, {hi:.2f}]")
    text = "\n".join(lines)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
