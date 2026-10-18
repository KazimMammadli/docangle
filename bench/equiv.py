"""Case-by-case equivalence check for code changes (refactors, speed-ups).

  python -m bench.equiv dump --candidate docangle --out /tmp/before.json      # on the code BEFORE the change
  ... edit the code ...
  python -m bench.equiv dump --candidate docangle --out /tmp/after.json       # on the code AFTER the change
  python -m bench.equiv compare /tmp/before.json /tmp/after.json

`dump` runs the candidate on a fixed, seeded set of simulated cases (all pools x levels) and stores, per case, the angle,
confidence, review flag and reasons. `compare` reports how many cases are IDENTICAL, the largest differences, how many
review flags changed, and the paired accuracy against the known angle (better / worse by more than 0.25 degrees), so a
pure refactor can be shown to change nothing and a numerical change can be shown to be neutral.
"""
from __future__ import annotations

import argparse
import json
import time

import cv2
import numpy as np

from .candidates import REGISTRY
from .degrade import LEVELS, render, sample_angle
from .metrics import circ_err
from .run import make_cases

POOLS = ["az", "invoices", "tobacco_cert", "rvl_heldout", "ext_funsd", "ext_doclaynet", "ext_cord"]


def dump(a):
    # the registry callable returns only (angle, conf, review); we also want the reasons, so build the pipeline from its config
    from docangle import DocumentOrientationPipeline
    cfg = REGISTRY[a.candidate]()[1]
    pipe = DocumentOrientationPipeline(cfg)
    recs = []
    for ds in a.datasets:
        for lv in a.levels:
            cases, _, _ = make_cases(ds, lv, "uniform", 1, a.n)
            for f, s, i, rng in cases:
                page = cv2.imread(f)
                gt = sample_angle("uniform", rng)
                img = render(page, gt, LEVELS[lv], rng)
                t0 = time.perf_counter()
                r = pipe.predict(img)
                ms = (time.perf_counter() - t0) * 1000.0
                recs.append(dict(ds=ds, lv=lv, file=f.split("/")[-1], gt=gt, angle=r.angle, conf=r.confidence,
                                 review=r.needs_review, reasons=r.reasons, resid=r.residual, lines=r.num_lines, ms=ms))
            print("dumped", ds, lv, flush=True)
    json.dump(recs, open(a.out, "w"))
    print("wrote", a.out, len(recs), "cases")


def _err(r):
    return 180.0 if r["angle"] is None else circ_err(r["angle"], r["gt"])


def compare(a):
    A, B = json.load(open(a.before)), json.load(open(a.after))
    assert len(A) == len(B) and all(x["file"] == y["file"] and x["gt"] == y["gt"] for x, y in zip(A, B)), "different case sets"
    n = len(A)
    same = np.array([x["angle"] == y["angle"] for x, y in zip(A, B)])
    d = np.array([180.0 if (x["angle"] is None or y["angle"] is None) else circ_err(x["angle"], y["angle"]) for x, y in zip(A, B)])
    dc = np.array([abs(x["conf"] - y["conf"]) for x, y in zip(A, B)])
    rev = sum(x["review"] != y["review"] for x, y in zip(A, B))
    rea = sum(sorted(x["reasons"]) != sorted(y["reasons"]) for x, y in zip(A, B))
    ea, eb = np.array([_err(x) for x in A]), np.array([_err(y) for y in B])
    print(f"cases {n}")
    print(f"identical angle (to 0.01 deg): {same.mean() * 100:.2f}%   max |dangle| {d.max():.3f} deg   cases with |dangle| > 0.05: {int((d > 0.05).sum())}   > 0.5: {int((d > 0.5).sum())}")
    print(f"confidence: max |dconf| {dc.max():.4f}   cases > 0.01: {int((dc > 0.01).sum())}   review flag changed: {rev}   reasons changed: {rea}")
    for name, e in (("before", ea), ("after", eb)):
        print(f"{name:7s} flips {int((e > 45).sum()):3d}  >5deg {int((e > 5).sum()):3d}  <=1deg {np.mean(e <= 1) * 100:5.1f}%  <=0.5deg {np.mean(e <= .5) * 100:5.1f}%")
    print(f"paired: after better by >0.25deg in {int((eb < ea - 0.25).sum())} cases, worse in {int((eb > ea + 0.25).sum())}")
    ta, tb = np.array([x["ms"] for x in A]), np.array([y["ms"] for y in B])
    print(f"time per page (analysis, ms): before mean {ta.mean():.1f} p50 {np.percentile(ta, 50):.1f} p95 {np.percentile(ta, 95):.1f} | "
          f"after mean {tb.mean():.1f} p50 {np.percentile(tb, 50):.1f} p95 {np.percentile(tb, 95):.1f}")
    if (d > 0.05).any():
        print("largest differences:")
        for i in np.argsort(-d)[:6]:
            print(f"   {A[i]['ds']}/{A[i]['lv']} {A[i]['file']} gt {A[i]['gt']:+.1f}: before {A[i]['angle']} (c{A[i]['conf']}) after {B[i]['angle']} (c{B[i]['conf']})")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dump")
    d.add_argument("--candidate", default="docangle")
    d.add_argument("--datasets", nargs="+", default=POOLS)
    d.add_argument("--levels", nargs="+", default=["scan", "photo_hard"])
    d.add_argument("--n", type=int, default=50)
    d.add_argument("--out", required=True)
    c = sub.add_parser("compare")
    c.add_argument("before")
    c.add_argument("after")
    a = ap.parse_args()
    dump(a) if a.cmd == "dump" else compare(a)


if __name__ == "__main__":
    main()
