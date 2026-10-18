"""PDF-level A/B of the JPEG fast path against PDFium rendering on pages with KNOWN angles.

  python -m bench.pdf_equiv --pools az invoices ... --levels scan photo_hard --n 40 --out reports/pdf_equiv.txt

Every benchmark case (a degraded, rotated page with a known angle) is wrapped into a one-page scanner-style PDF (JPEG, alternating 150 dpi gray,
300 dpi gray and 200 dpi colour variants, q = 75) and analysed twice by the same pipeline settings: pages rendered by PDFium (``pdf_fast_path=False``)
and through the fast path. Reports the share of pages that took the fast path, angle / quadrant / review differences between the two paths, and
accuracy against the truth (flips, <= 1 deg, paired better / worse by more than 0.25 deg).
"""
from __future__ import annotations

import argparse
import os
import tempfile

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline, PipelineConfig
from docangle.pdf_fast import pdf_fast_stats, reset_pdf_fast_stats
from tests.unit.helpers import build_pdf, jpeg_bytes

from .degrade import LEVELS, render, sample_angle
from .metrics import circ_err
from .run import make_cases

VARIANTS = [("gray 150 dpi", 150, 2000, False), ("gray 300 dpi", 300, 3500, False), ("colour 200 dpi", 200, 2600, True)]


def wrap(img, dpi, long_px, colour, path):
    g = img if colour else (cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img)
    if colour and g.ndim == 2:
        g = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    k = long_px / max(g.shape[:2])
    g = cv2.resize(g, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC if k > 1 else cv2.INTER_AREA)
    h, w = g.shape[:2]
    im = dict(data=jpeg_bytes(g, quality=75), w=w, h=h, cs=b"/DeviceRGB" if colour else b"/DeviceGray")
    with open(path, "wb") as f:
        f.write(build_pdf([dict(mediabox=(w * 72.0 / dpi, h * 72.0 / dpi), images=[im])]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pools", nargs="+", default=["az", "invoices", "tobacco_cert", "rvl_heldout", "ext_funsd", "ext_doclaynet", "ext_cord"])
    ap.add_argument("--levels", nargs="+", default=["scan", "photo_hard"])
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    off = DocumentOrientationPipeline(PipelineConfig(pdf_fast_path=False))
    on = DocumentOrientationPipeline(PipelineConfig(pdf_fast_path=True))
    tmp = tempfile.mkdtemp(prefix="pdfeq_")
    rows = []
    reset_pdf_fast_stats()
    for pool in a.pools:
        for lv in a.levels:
            cases, _, _ = make_cases(pool, lv, "uniform", 1, a.n)
            for i, (f, s, ci, rng) in enumerate(cases):
                page = cv2.imread(f)
                gt = sample_angle("uniform", rng)
                img = render(page, gt, LEVELS[lv], rng)
                v = VARIANTS[i % len(VARIANTS)]
                path = os.path.join(tmp, "p.pdf")
                wrap(img, v[1], v[2], v[3], path)
                ro, rf = off.predict(path), on.predict(path)
                rows.append(dict(pool=pool, lv=lv, variant=v[0], gt=gt, file=os.path.basename(f), a_off=ro.angle, a_on=rf.angle, rev_off=ro.needs_review, rev_on=rf.needs_review,
                                 conf_off=ro.confidence, conf_on=rf.confidence))
            print("done", pool, lv, flush=True)
    L = [f"{len(rows)} pages (one-page JPEG scanner-style PDFs), fast-path usage: {pdf_fast_stats()}"]

    def err(x, g):
        return 180.0 if x is None else circ_err(x, g)
    e_off = np.array([err(r["a_off"], r["gt"]) for r in rows]); e_on = np.array([err(r["a_on"], r["gt"]) for r in rows])
    d = np.array([180.0 if (r["a_off"] is None or r["a_on"] is None) else circ_err(r["a_off"], r["a_on"]) for r in rows])
    L.append(f"angle difference fast vs render: max {d.max():.3f} deg, mean {d.mean():.4f}; > 0.05 deg: {int((d > .05).sum())}, > 0.25 deg: {int((d > .25).sum())}, > 45 deg (quadrant): {int((d > 45).sum())}")
    L.append(f"review flag differs: {sum(r['rev_off'] != r['rev_on'] for r in rows)}; confidence differs by > 0.01: {sum(abs(r['conf_off'] - r['conf_on']) > .01 for r in rows)}")
    for name, e in (("render (PDFium)", e_off), ("fast path", e_on)):
        L.append(f"{name:16s} flips {int((e > 45).sum()):3d} | <=1deg {np.mean(e <= 1) * 100:5.1f} % | <=0.5deg {np.mean(e <= .5) * 100:5.1f} % | >5deg {int((e > 5).sum())}")
    L.append(f"paired vs truth (threshold 0.25 deg): fast better in {int((e_on < e_off - .25).sum())}, worse in {int((e_on > e_off + .25).sum())}")
    L.append("cases where the two paths differ by more than 0.25 deg:")
    for r, dd in zip(rows, d):
        if dd > 0.25:
            L.append(f"  {r['pool']}/{r['lv']} {r['file']} [{r['variant']}] gt {r['gt']:+.1f}: render {r['a_off']} (conf {r['conf_off']}, review {r['rev_off']}) | fast {r['a_on']} (conf {r['conf_on']}, review {r['rev_on']})")
    for v in VARIANTS:
        m = np.array([r["variant"] == v[0] for r in rows])
        L.append(f"  {v[0]:15s} n={int(m.sum()):3d} max diff {d[m].max():.3f} deg, flips render {int((e_off[m] > 45).sum())} / fast {int((e_on[m] > 45).sum())}")
    print("\n".join(L))
    if a.out:
        open(a.out, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
