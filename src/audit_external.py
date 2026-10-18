"""Audit the external pools for pages that are NOT upright (sideways / upside down / strongly skewed).

    python -m src.audit_external ext_funsd ext_cord ext_doclaynet

Runs the pipeline on every page as it is. A page the pipeline calls rotated by more than --thr degrees is only
a CANDIDATE (the pipeline may be wrong): the script writes contact sheets (reports/audit_ext_<pool>_<k>.jpg, tile
caption = index, predicted angle, confidence) so a human can look, then `--move 3 17 ...` moves confirmed pages
to data/cache/<pool>_dropped/ (never deleted).
"""
from __future__ import annotations

import argparse
import glob
import json
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "cache")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pools", nargs="+")
    ap.add_argument("--thr", type=float, default=8.0, help="flag pages the pipeline calls rotated by more than this")
    ap.add_argument("--move", nargs="*", type=int, help="indices (from the sheets) to move to <pool>_dropped (one pool only)")
    a = ap.parse_args()
    if a.move is not None:
        assert len(a.pools) == 1
        files = json.load(open(os.path.join(ROOT, "reports", f"audit_{a.pools[0]}.json")))["flagged"]
        dst = os.path.join(CACHE, a.pools[0] + "_dropped")
        os.makedirs(dst, exist_ok=True)
        for i in a.move:
            f = os.path.join(CACHE, a.pools[0], files[i]["file"])
            os.replace(f, os.path.join(dst, files[i]["file"]))
            print("moved", files[i]["file"])
        return
    from docangle import get_pipeline
    pipe = get_pipeline()
    for pool in a.pools:
        files = sorted(glob.glob(os.path.join(CACHE, pool, "*.png")))
        rows, flagged = [], []
        for f in files:
            g = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
            r = pipe.analyze(g)
            rec = {"file": os.path.basename(f), "angle": r.angle, "conf": r.confidence, "review": r.needs_review}
            rows.append(rec)
            if r.angle is None or abs(r.angle) > a.thr:
                flagged.append(rec)
        json.dump({"pool": pool, "n": len(files), "flagged": flagged, "all": rows},
                  open(os.path.join(ROOT, "reports", f"audit_{pool}.json"), "w"), indent=1)
        print(f"{pool}: {len(files)} pages, {len(flagged)} flagged (|angle| > {a.thr})")
        tiles = []
        for i, rec in enumerate(flagged):
            g = cv2.imread(os.path.join(CACHE, pool, rec["file"]), cv2.IMREAD_GRAYSCALE)
            H = 300
            t = cv2.cvtColor(cv2.resize(g, (max(8, int(g.shape[1] * H / g.shape[0])), H), interpolation=cv2.INTER_AREA), cv2.COLOR_GRAY2BGR)
            ang = "None" if rec["angle"] is None else f"{rec['angle']:+.0f}"
            cv2.putText(t, f"#{i} {ang} c{rec['conf']:.2f}", (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            tiles.append(cv2.copyMakeBorder(t, 0, 0, 0, 4, cv2.BORDER_CONSTANT, value=(255, 0, 0)))
        rowsimg, cur, w = [], [], 0
        for t in tiles:
            if w + t.shape[1] > 1800:
                rowsimg.append(cur); cur, w = [], 0
            cur.append(t); w += t.shape[1]
        if cur:
            rowsimg.append(cur)
        sheets = [rowsimg[i:i + 4] for i in range(0, len(rowsimg), 4)]
        for k, sh in enumerate(sheets):
            ims = []
            for r in sh:
                row = np.hstack(r)
                ims.append(np.hstack([row, np.full((300, 1800 - row.shape[1], 3), 255, np.uint8)]) if row.shape[1] < 1800 else row)
            cv2.imwrite(os.path.join(ROOT, "reports", f"audit_{pool}_{k}.jpg"), np.vstack(ims), [cv2.IMWRITE_JPEG_QUALITY, 75])


if __name__ == "__main__":
    main()
