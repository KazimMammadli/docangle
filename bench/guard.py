"""Accuracy guard for speed changes: run a baseline and variants on the SAME simulated cases and compare.

  python -m bench.guard --base docangle --variants docangle_w800 --datasets az invoices tobacco_cert --levels scan photo_hard --n 100

A speed change is accepted only if (see CONTRIBUTING.md): predicted angles differ by <= 0.05 degrees from the baseline for
>= 99 % of cases, flips (error > 45 deg) are not higher beyond the CI overlap, and the <= 1 degree rate is not lower.
"""
from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from .candidates import REGISTRY
from .degrade import LEVELS, render, sample_angle
from .metrics import circ_err
from .run import make_cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="docangle")
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--datasets", nargs="+", default=["az", "invoices", "tobacco_cert", "rvl_heldout"])
    ap.add_argument("--levels", nargs="+", default=["scan", "photo_hard"])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seeds", type=int, default=1)
    a = ap.parse_args()
    names = [a.base] + a.variants
    fns = {n: REGISTRY[n]()[0] for n in names}
    pred = {n: [] for n in names}
    ms = {n: [] for n in names}
    gts = []
    for ds in a.datasets:
        for lv in a.levels:
            cases, _, _ = make_cases(ds, lv, "uniform", a.seeds, a.n)
            for f, s, i, rng in cases:
                page = cv2.imread(f)
                gt = sample_angle("uniform", rng)
                img = render(page, gt, LEVELS[lv], rng)
                gts.append(gt)
                for n in names:
                    t0 = time.perf_counter()
                    r = fns[n](img)
                    ms[n].append((time.perf_counter() - t0) * 1000)
                    pred[n].append(np.nan if r["pred"] is None else r["pred"])
            print("done", ds, lv, flush=True)
    gts = np.array(gts)
    err = {n: np.array([circ_err(p, g) if p == p else 180.0 for p, g in zip(pred[n], gts)]) for n in names}
    b = err[a.base]
    print(f"\ncases {len(gts)}")
    print(f"{'candidate':18s} {'ms':>6s} {'flips':>6s} {'<=1deg%':>8s} {'<=0.5%':>7s} {'>5deg':>6s} {'same<=0.05deg%':>15s} {'same<=0.5deg%':>14s} {'better/worse by>0.25deg':>24s}")
    for n in names:
        d = np.array([circ_err(p, q) if (p == p and q == q) else 180.0 for p, q in zip(pred[n], pred[a.base])])
        e = err[n]
        print(f"{n:18s} {np.mean(ms[n]):6.1f} {int(np.sum(e > 45)):6d} {np.mean(e <= 1) * 100:8.1f} {np.mean(e <= .5) * 100:7.1f} {int(np.sum(e > 5)):6d} "
              f"{np.mean(d <= 0.05) * 100:15.1f} {np.mean(d <= 0.5) * 100:14.1f} {int(np.sum(e < b - 0.25)):>12d}/{int(np.sum(e > b + 0.25))}")


if __name__ == "__main__":
    main()
