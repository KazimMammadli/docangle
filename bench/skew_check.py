"""How much of the missing <= 1 degree rate is the SOURCE page's own skew?

  python -m bench.skew_check --datasets az invoices tobacco_cert rvl_heldout --levels scan photo_hard --n 100 --seeds 2

Public "upright" scans are usually 0.3-1 degree off, so ground truth gt = (applied rotation) is only nominal. This tool
measures every source page once WITHOUT rotation (s0 = pipeline angle of the page as it is) and re-scores every simulated
case against gt + s0. The reference s0 comes from the same method, so this is a consistency measure (does the estimate
survive rotation, blur, shadows, JPEG?), NOT an independent accuracy number; pages the pipeline itself calls tilted by more
than 8 degrees (or sideways) are left out of the adjusted score and counted separately.
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np

from .candidates import REGISTRY
from .degrade import LEVELS, render, sample_angle
from .metrics import circ_err, wilson
from .run import make_cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default="docangle")
    ap.add_argument("--datasets", nargs="+", default=["az", "invoices", "tobacco_cert", "rvl_heldout"])
    ap.add_argument("--levels", nargs="+", default=["scan", "photo_hard"])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seeds", type=int, default=2)
    a = ap.parse_args()
    fn = REGISTRY[a.candidate]()[0]
    print(f"{'pool':14s} {'level':10s} {'cases':>5s} {'skewed>8':>8s} {'median|s0|':>10s} | {'<=1deg raw %':>12s} {'<=1deg adj %':>12s} {'<=0.5 adj %':>11s} {'>2deg adj':>9s} {'>5deg adj':>9s}")
    for ds in a.datasets:
        s0_cache = {}
        for lv in a.levels:
            cases, _, _ = make_cases(ds, lv, "uniform", a.seeds, a.n)
            raw, adj, skewed, s0s = [], [], 0, []
            for f, s, i, rng in cases:
                if f not in s0_cache:
                    r0 = fn(cv2.imread(f))
                    s0_cache[f] = r0["pred"]
                s0 = s0_cache[f]
                page = cv2.imread(f)
                gt = sample_angle("uniform", rng)
                img = render(page, gt, LEVELS[lv], rng)
                p = fn(img)["pred"]
                if p is None or s0 is None:
                    continue
                raw.append(circ_err(p, gt))
                if abs(s0) > 8.0:
                    skewed += 1
                    continue
                adj.append(circ_err(p, gt + s0))
                s0s.append(abs(s0))
            raw, adj = np.array(raw), np.array(adj)
            lo, hi = wilson(int(np.sum(adj <= 1)), len(adj))
            print(f"{ds:14s} {lv:10s} {len(raw):5d} {skewed:8d} {np.median(s0s):10.2f} | {np.mean(raw <= 1) * 100:12.1f} {np.mean(adj <= 1) * 100:12.1f} "
                  f"{np.mean(adj <= .5) * 100:11.1f} {int(np.sum(adj > 2)):9d} {int(np.sum(adj > 5)):9d}   (adj <=1 deg 95% CI {lo:.1f}-{hi:.1f})", flush=True)


if __name__ == "__main__":
    main()
