"""First look at a folder of real (unlabeled) photos: no ground truth needed.

  python -m tools.first_look PHOTO_DIR --out reports/first_look

Writes to --out:
  summary.txt        what the checks found (below)
  results.csv        per photo: angle / confidence / review of every candidate, agreement, rotation-consistency errors
  sheet_XX.jpg       contact sheets of the UPRIGHT result of the default pipeline (20 photos each, numbered; review pages marked red)
  index.csv          sheet number -> file name, so a person can note the wrong ones in seconds

Checks without labels:
  * agreement between candidates (docangle, docangle_hough): same quadrant? angles within 1 degree?
  * rotation consistency of docangle: every photo is turned by three known angles; the angle must change by exactly that
    (a stability test: it does not say the first answer is right, but a method that fails it cannot be right)
  * needs_review rate and reasons
The person then looks at the sheets and lists the numbers that are NOT upright: that is the quadrant ground truth for the whole folder.
"""
from __future__ import annotations

import argparse
import csv
import glob
import os

import cv2
import numpy as np

from bench.candidates import REGISTRY
from bench.metrics import circ_err
from docangle import DocumentOrientationPipeline, PipelineConfig, normalize_angle, rotate_image_expanded

EXT = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp")
TURNS = (37.3, -112.5, 180.0)


def sheet(tiles, labels, flags, path, cols=5, h=300):
    cells = []
    for t, lab, bad in zip(tiles, labels, flags):
        k = h / t.shape[0]
        t = cv2.resize(t, (max(8, int(t.shape[1] * k)), h), interpolation=cv2.INTER_AREA)
        t = cv2.copyMakeBorder(t, 0, 0, 0, 0, cv2.BORDER_CONSTANT)
        cv2.putText(t, lab, (4, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255) if bad else (0, 140, 0), 2)
        cells.append(cv2.copyMakeBorder(t, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=(120, 120, 120)))
    w = max(c.shape[1] for c in cells)
    rows = []
    for i in range(0, len(cells), cols):
        row = cells[i:i + cols]
        row = [cv2.copyMakeBorder(c, 0, 0, 0, w - c.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for c in row]
        row += [np.full_like(row[0], 255)] * (cols - len(row))
        rows.append(np.hstack(row))
    cv2.imwrite(path, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo_dir")
    ap.add_argument("--out", default="reports/first_look")
    ap.add_argument("--candidates", nargs="+", default=["docangle", "docangle_hough"], choices=list(REGISTRY), help="legacy_v1 needs the predecessor pipeline, which is not part of this repository")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    files = sorted(p for p in glob.glob(os.path.join(a.photo_dir, "*")) if p.lower().endswith(EXT))
    fns = {n: REGISTRY[n]()[0] for n in a.candidates}
    pipe = DocumentOrientationPipeline(PipelineConfig())
    rows, tiles, labels, flags = [], [], [], []
    for i, f in enumerate(files, 1):
        img = cv2.imread(f)
        if img is None:
            continue
        outs = {n: fn(img) for n, fn in fns.items()}
        r0 = pipe.predict(img)
        cons = []
        for t in TURNS:
            r = pipe.predict(rotate_image_expanded(img, t))
            cons.append(float("nan") if (r.angle is None or r0.angle is None) else circ_err(normalize_angle(r.angle - t), r0.angle))
        row = {"n": i, "file": os.path.basename(f), "review": r0.needs_review, "reasons": "|".join(r0.reasons), "cons_max_err": float(np.nanmax(cons)) if not np.all(np.isnan(cons)) else float("nan")}
        for n, o in outs.items():
            row[f"{n}_angle"] = o["pred"]; row[f"{n}_conf"] = o.get("conf")
        rows.append(row)
        up = pipe.render_upright(img, r0.angle) if r0.angle is not None else img
        tiles.append(up if up.ndim == 3 else cv2.cvtColor(up, cv2.COLOR_GRAY2BGR))
        labels.append(f"{i}" + (" REVIEW" if r0.needs_review else "")); flags.append(r0.needs_review)
        if i % 10 == 0:
            print(f"{i}/{len(files)}", flush=True)
    for k in range(0, len(tiles), 20):
        sheet(tiles[k:k + 20], labels[k:k + 20], flags[k:k + 20], os.path.join(a.out, f"sheet_{k // 20 + 1:02d}.jpg"))
    with open(os.path.join(a.out, "results.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(os.path.join(a.out, "index.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["n", "sheet", "file"])
        for r in rows:
            w.writerow([r["n"], (r["n"] - 1) // 20 + 1, r["file"]])
    n = len(rows)
    L = [f"{n} photos from {a.photo_dir}"]
    L.append(f"needs_review ({a.candidates[0]}): {sum(r['review'] for r in rows)} ({100 * np.mean([r['review'] for r in rows]):.1f} %)")
    ok = [r["cons_max_err"] for r in rows if r["cons_max_err"] == r["cons_max_err"]]
    L.append(f"rotation consistency (3 known turns each, same photo): within 1 deg {100 * np.mean(np.array(ok) <= 1):.1f} %, within 5 deg {100 * np.mean(np.array(ok) <= 5):.1f} %, "
             f"quadrant-level inconsistencies (> 45 deg) {int(np.sum(np.array(ok) > 45))} of {len(ok)}")
    if len(a.candidates) > 1:
        base = a.candidates[0]
        for other in a.candidates[1:]:
            d = [circ_err(r[f'{base}_angle'], r[f'{other}_angle']) for r in rows if r[f'{base}_angle'] is not None and r[f'{other}_angle'] is not None]
            L.append(f"agreement {base} vs {other}: within 1 deg {100 * np.mean(np.array(d) <= 1):.1f} %, different quadrant (> 45 deg) {int(np.sum(np.array(d) > 45))} of {len(d)}")
    L.append("NEXT: open sheet_*.jpg and write down the numbers that are NOT upright (index.csv maps number -> file).")
    open(os.path.join(a.out, "summary.txt"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
