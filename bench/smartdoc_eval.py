"""Real phone footage: SmartDoc 2015 challenge 1 frames (CC-BY 4.0, data/external/smartdoc/frames).

  python -m bench.smartdoc_eval --every 25 --candidates docangle docangle_hough legacy_v1 [--rot90] --out reports/smartdoc_eval.txt

150 video clips of 30 documents (datasheet, letter, magazine, paper, patent, tax) filmed with a phone on 5 backgrounds; every frame has the
document's four corners. GT angle = direction of the document's top/bottom edges (mean of tl->tr and bl->br), CCW positive in our convention.
Caveats: the GT comes from the page EDGES (perspective moves it by a degree or two from the text-line direction), documents are English, a document
fills only part of a 1920x1080 frame, consecutive frames are near-duplicates (so every K-th frame is used and the 150 clips, not the frames, are the
independent units), `--crop M` cuts out the document (corners + margin M of its long side) as a perfect document detector would,
`--rot90` additionally turns every frame by a random multiple of 90 degrees to test the quadrant on real footage.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import math
import os

import cv2
import numpy as np

from .candidates import REGISTRY
from .metrics import circ_err

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "external", "smartdoc", "frames")


def gt_angle(r):
    f = lambda k: float(r[k])
    vx = (f("tr_x") - f("tl_x")) + (f("br_x") - f("bl_x"))
    vy = (f("tr_y") - f("tl_y")) + (f("br_y") - f("bl_y"))
    return math.degrees(math.atan2(-vy, vx))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, default=25)
    ap.add_argument("--candidates", nargs="+", default=["docangle", "docangle_hough", "legacy_v1"], choices=list(REGISTRY))
    ap.add_argument("--rot90", action="store_true")
    ap.add_argument("--crop", type=float, default=None, help="crop to the document corners + this margin (fraction of the long side), as a perfect document detector would")
    ap.add_argument("--docs", choices=["all", "even", "odd"], default="all", help="only the documents with an even / odd model_id (docangle/docrop.py was tuned on the even ones)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = list(csv.DictReader(gzip.open(os.path.join(ROOT, "metadata.csv.gz"), "rt")))
    rows = [r for r in rows if int(r["frame_index"]) % a.every == 0 and (a.docs == "all" or int(r["model_id"]) % 2 == (a.docs == "odd"))]
    fns = {n: REGISTRY[n]()[0] for n in a.candidates}
    rng = np.random.default_rng(0)
    rec = {n: [] for n in fns}
    meta = []
    for i, r in enumerate(rows):
        img = cv2.imread(os.path.join(ROOT, r["image_path"]))
        gt = gt_angle(r)
        if a.crop is not None:
            pts = np.array([[float(r[k + "_x"]), float(r[k + "_y"])] for k in ("tl", "bl", "br", "tr")])
            x0, y0 = pts.min(0); x1, y1 = pts.max(0)
            m = a.crop * max(x1 - x0, y1 - y0)
            H, W = img.shape[:2]
            img = np.ascontiguousarray(img[max(0, int(y0 - m)):min(H, int(y1 + m)), max(0, int(x0 - m)):min(W, int(x1 + m))])
        if a.rot90:
            k = int(rng.integers(0, 4))
            if k:
                img = np.ascontiguousarray(np.rot90(img, k)); gt = ((gt + 90 * k + 180) % 360) - 180
        meta.append((r["modeltype_name"], r["bg_name"], r["model_name"], gt))
        for n, fn in fns.items():
            import time
            t0 = time.perf_counter(); o = fn(img); ms = (time.perf_counter() - t0) * 1000
            rec[n].append((o["pred"], o.get("review", False), ms))
        if (i + 1) % 100 == 0:
            print(i + 1, "/", len(rows), flush=True)
    gts = np.array([m[3] for m in meta])
    lines = [f"SmartDoc frames: {len(rows)} (every {a.every}th of 150 clips), rot90={a.rot90}, crop={a.crop}; error = circular difference to the page-edge GT"]
    for n in fns:
        p = np.array([np.nan if x[0] is None else x[0] for x in rec[n]]); rev = np.array([x[1] for x in rec[n]], bool)
        e = np.array([180.0 if q != q else circ_err(q, g) for q, g in zip(p, gts)]); flip = e > 45
        lines.append(f"{n:20s} n={len(e)} median {np.median(e):5.2f} deg | <=1 {np.mean(e<=1)*100:5.1f} % <=2 {np.mean(e<=2)*100:5.1f} % <=5 {np.mean(e<=5)*100:5.1f} % | "
                     f"flips(>45) {flip.sum():3d} ({flip.mean()*100:.1f} %) | review {rev.mean()*100:4.1f} % accepted flips {int((flip&~rev).sum())} | ms {np.mean([x[2] for x in rec[n]]):.0f}")
    for typ in sorted({m[0] for m in meta}):
        sel = np.array([m[0] == typ for m in meta])
        for n in fns[:1] if False else list(fns)[:1]:
            p = np.array([np.nan if x[0] is None else x[0] for x in rec[n]])
            e = np.array([180.0 if q != q else circ_err(q, g) for q, g in zip(p, gts)])
            lines.append(f"   {n} by type {typ:9s} n={sel.sum():3d} <=2 {np.mean(e[sel]<=2)*100:5.1f} % flips {int((e[sel]>45).sum())}")
    print("\n".join(lines))
    if a.out:
        open(a.out, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
