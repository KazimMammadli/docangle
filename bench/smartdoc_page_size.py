"""How big is the page in the SmartDoc frames? (the numbers quoted in docs/05 5.4.6 and docs/06 6.4)

  python -m bench.smartdoc_page_size --out reports/smartdoc_page_size.txt

From the corner coordinates of ``data/external/smartdoc/frames/metadata.csv.gz``, for every K-th frame of each clip (K = 50: the 420 frames of chapter 5;
K = 25: the 926 frames of chapter 6): the long side of the bounding box of the page corners, the same with the 8 % margin of the "cut out" set,
and the share of the 1920 x 1080 frame that the page polygon covers.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "data", "external", "smartdoc", "frames", "metadata.csv.gz")
FRAME_AREA = 1920 * 1080
MARGIN = 0.08


def stats(rows):
    side, cut, share = [], [], []
    for r in rows:
        pts = np.array([[float(r[k + "_x"]), float(r[k + "_y"])] for k in ("tl", "bl", "br", "tr")])
        w, h = np.ptp(pts[:, 0]), np.ptp(pts[:, 1])
        side.append(max(w, h))
        cut.append(max(w, h) * (1 + 2 * MARGIN))
        x, y = pts[:, 0], pts[:, 1]
        share.append(0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / FRAME_AREA * 100)
    return np.array(side), np.array(cut), np.array(share)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = list(csv.DictReader(gzip.open(META, "rt")))
    lines = []
    for k in (50, 25):
        sub = [r for r in rows if int(r["frame_index"]) % k == 0]
        side, cut, share = stats(sub)
        lines.append(f"every {k}th frame: {len(sub)} frames")
        for name, v, unit in (("page bounding box, long side", side, "px"), ("cut-out (page + 8 % margin each side), long side", cut, "px"), ("share of the 1920 x 1080 frame covered by the page", share, "%")):
            lines.append(f"  {name:55s} median {np.median(v):7.1f} {unit} | 5th-95th percentile {np.percentile(v, 5):7.1f} - {np.percentile(v, 95):7.1f} | min {v.min():7.1f} max {v.max():7.1f}")
    text = "\n".join(lines)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")


if __name__ == "__main__":
    main()
