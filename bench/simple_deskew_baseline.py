"""How good is the textbook deskew (cv2.minAreaRect, as in popular answers/tutorials) compared with docangle's fine tilt?

  python -m bench.simple_deskew_baseline --n 50 --out reports/simple_deskew_baseline.txt

Cases = the benchmark's simulated pages at uniformly random angles; only the tilt modulo 90 degrees can be judged (such methods cannot tell
0 from 90 / 180 / 270). minAreaRect code is the tutorial version, verbatim (invert, Otsu, coordinates of ink pixels, minAreaRect, angle conversion).
"""
from __future__ import annotations

import argparse

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline

from .degrade import LEVELS, render, sample_angle
from .run import make_cases


def minarea_tutorial(gray):
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 10:
        return 0.0
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle        # the tutorial's conversion: this is the rotation it APPLIES (CCW positive)
    return -angle                                           # = the tilt it believes the page has


def err90(est, gt):
    return abs(((est - gt) + 45.0) % 90.0 - 45.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pools", nargs="+", default=["az", "invoices", "tobacco_cert", "rvl_heldout"])
    ap.add_argument("--levels", nargs="+", default=["scan", "photo_hard"])
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    pipe = DocumentOrientationPipeline()
    rows = []
    for pool in a.pools:
        for lv in a.levels:
            cases, _, _ = make_cases(pool, lv, "uniform", 1, a.n)
            for f, s, i, rng in cases:
                page = cv2.imread(f)
                gt = sample_angle("uniform", rng)
                img = render(page, gt, LEVELS[lv], rng)
                g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
                r = pipe.predict(g)
                gt_mod = ((gt + 45.0) % 90.0) - 45.0
                rows.append((pool, lv, err90(minarea_tutorial(g), gt_mod), err90(r.fine_tilt if r.fine_tilt is not None else 0.0, gt_mod)))
    L = [f"{len(rows)} simulated pages, any angle in [-180,180]; error of the tilt modulo 90 degrees (quarter turns cannot be judged by these methods)"]
    L.append(f"{'level / method':34s} {'n':>4s} {'<=1 deg':>8s} {'<=2 deg':>8s} {'>5 deg':>7s} {'>10 deg':>8s} {'median':>7s}")
    for lv in a.levels + ["all"]:
        sel = [r for r in rows if lv == "all" or r[1] == lv]
        for name, k in (("textbook minAreaRect", 2), ("docangle Fourier tilt", 3)):
            e = np.array([r[k] for r in sel])
            L.append(f"{lv + ' / ' + name:34s} {len(e):4d} {np.mean(e <= 1) * 100:7.1f}% {np.mean(e <= 2) * 100:7.1f}% {np.mean(e > 5) * 100:6.1f}% {np.mean(e > 10) * 100:7.1f}% {np.median(e):6.2f}")
    for pool in a.pools:
        sel = [r for r in rows if r[0] == pool]
        L.append(f"  {pool:14s} minAreaRect <=1deg {np.mean([r[2] <= 1 for r in sel]) * 100:5.1f}% | docangle {np.mean([r[3] <= 1 for r in sel]) * 100:5.1f}%")
    print("\n".join(L))
    if a.out:
        open(a.out, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
