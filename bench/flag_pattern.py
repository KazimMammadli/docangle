"""What sets the pages that docangle sends to review apart from the others?

  python -m bench.flag_pattern collect --out flags.json      # main-benchmark cases (uniform angles) of the pools that have flags, one row per case
  python -m bench.flag_pattern analyze --out flags.json      # flag rate per pool and level; per feature the AUROC (flagged vs not) inside each pool

One row per case: the pool, level and exact truth (angle, fine tilt, true quadrant), features of the SOURCE page (size, shape, ink share, sharpness,
contrast) and of the degraded INPUT frame (sharpness, contrast), and docangle's answer (confidence, number of text lines, flag, reasons).
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline

from . import run as bench_run
from .degrade import LEVELS, render, sample_angle
from .metrics import auroc

POOLS = ["ext_cord", "ext_doclaynet", "invoices", "rvl_heldout"]
LEVEL_NAMES = ["scan", "photo_easy", "photo_hard"]
FEATURES = ["abs_tilt", "src_long", "src_aspect", "src_ink", "src_sharp", "src_contrast", "frame_sharp", "frame_contrast", "is_180", "is_90", "num_lines"]


def _save(path, rows):
    with (gzip.open if path.endswith(".gz") else open)(path, "wt") as fh:
        json.dump(rows, fh)


def _sharp(gray):
    h, w = gray.shape[:2]
    g = cv2.resize(gray, (int(w * 1000 / max(h, w)), int(h * 1000 / max(h, w))), interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


def collect(a):
    pipe = DocumentOrientationPipeline()
    rows = []
    for ds in a.datasets:
        for lv in a.levels:
            cases, _, _ = bench_run.make_cases(ds, lv, "uniform", a.seeds, a.n)
            for f, s, i, rng in cases:
                page = cv2.imread(f)
                gt = sample_angle("uniform", rng)
                img = render(page, gt, LEVELS[lv], rng)
                r = pipe.predict(img)
                g = cv2.cvtColor(page, cv2.COLOR_BGR2GRAY) if page.ndim == 3 else page
                fg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
                tilt = (gt + 45.0) % 90.0 - 45.0
                quad = int(round((gt - tilt) / 90.0)) % 4        # 0 upright, 2 upside down, 1 / 3 quarter turns
                h, w = g.shape[:2]
                rows.append(dict(ds=ds, lv=lv, file=f.split("/")[-1], gt=gt, review=bool(r.needs_review), conf=r.confidence, reasons=r.reasons,
                                 abs_tilt=abs(tilt), is_180=float(quad == 2), is_90=float(quad in (1, 3)), num_lines=r.num_lines,
                                 src_long=float(max(h, w)), src_aspect=float(max(h, w) / min(h, w)), src_ink=float((g < 128).mean()),
                                 src_sharp=_sharp(g), src_contrast=float(g.std()), frame_sharp=_sharp(fg), frame_contrast=float(fg.std())))
            print(f"{ds}/{lv}: {len(cases)} cases, flagged {sum(x['review'] for x in rows if x['ds'] == ds and x['lv'] == lv)}", flush=True)
            _save(a.out, rows)


def analyze(a):
    with (gzip.open if a.out.endswith(".gz") else open)(a.out, "rt") as fh:
        rows = json.load(fh)
    print("## Flag rate by pool and level\n\n| pool | scan | photo_easy | photo_hard |\n|---|---|---|---|")
    for ds in POOLS:
        cells = []
        for lv in LEVEL_NAMES:
            r = [x for x in rows if x["ds"] == ds and x["lv"] == lv]
            cells.append(f"{100 * np.mean([x['review'] for x in r]):.1f} % ({sum(x['review'] for x in r)}/{len(r)})" if r else "-")
        print(f"| {ds} | " + " | ".join(cells) + " |")
    fl = [x for x in rows if x["review"]]
    print(f"\n## First reason of the {len(fl)} flagged pages (of {len(rows)} cases); a page can carry several codes, none = plain low confidence\n")
    for k, v in collections.Counter(x["reasons"][0] if x["reasons"] else "none" for x in fl).most_common():
        print(f"- {k}: {v}")
    print(f"median text lines: flagged {np.median([x['num_lines'] for x in fl]):.0f}, not flagged {np.median([x['num_lines'] for x in rows if not x['review']]):.0f}; "
          f"flagged pages with fewer than 8 lines: {sum(x['num_lines'] < 8 for x in fl)}")
    print("\n## What separates flagged from not flagged, inside each pool (AUROC: 0.5 = nothing, 1.0 = perfect; + = flagged pages have the higher value)\n")
    print("| feature | " + " | ".join(POOLS) + " | all four |\n|---|" + "---|" * (len(POOLS) + 1))
    for f in FEATURES:
        cells = []
        for ds in POOLS + [None]:
            r = [x for x in rows if ds is None or x["ds"] == ds]
            y = np.array([x["review"] for x in r])
            if y.sum() < 5 or (~y).sum() < 5:
                cells.append("-")
                continue
            auc = auroc(np.array([x[f] for x in r], dtype=float), y)
            cells.append(f"{auc:.2f}{'+' if auc >= 0.5 else '-'}")
        print(f"| {f} | " + " | ".join(cells) + " |")
    print("\n## Flag rate by feature third (all four pools, pool-balanced: thirds are cut inside each pool)\n")
    for f in ("abs_tilt", "src_sharp", "src_contrast", "src_ink", "src_aspect", "frame_sharp", "num_lines"):
        out = []
        for t in range(3):
            fl = tot = 0
            for ds in POOLS:
                r = [x for x in rows if x["ds"] == ds]
                v = np.array([x[f] for x in r])
                lo, hi = np.quantile(v, [t / 3, (t + 1) / 3])
                sel = [x for x in r if (x[f] >= lo and (x[f] < hi or t == 2))]
                fl += sum(x["review"] for x in sel)
                tot += len(sel)
            out.append(f"{100 * fl / tot:.1f} %")
        print(f"- {f}: lowest third {out[0]}, middle {out[1]}, highest {out[2]}")
    print(f"\nflag rate when the page is upside down (180): {100 * np.mean([x['review'] for x in rows if x['is_180']]):.1f} %, quarter turn: "
          f"{100 * np.mean([x['review'] for x in rows if x['is_90']]):.1f} %, upright: {100 * np.mean([x['review'] for x in rows if not x['is_180'] and not x['is_90']]):.1f} %")
    t45 = [x for x in rows if x["abs_tilt"] >= 30]
    print(f"flag rate when the tilt is within 15 degrees of the 45-degree boundary: {100 * np.mean([x['review'] for x in t45]):.1f} % ({len(t45)} cases), otherwise "
          f"{100 * np.mean([x['review'] for x in rows if x['abs_tilt'] < 30]):.1f} %")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["collect", "analyze"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--datasets", nargs="+", default=POOLS)
    ap.add_argument("--levels", nargs="+", default=LEVEL_NAMES)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--n", type=int, default=100)
    a = ap.parse_args()
    {"collect": collect, "analyze": analyze}[a.step](a)


if __name__ == "__main__":
    main()
