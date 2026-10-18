"""DocOrient (PyPI `docorient`, MIT) and the Duarte EfficientNetV2 orientation model (bench/exp_duarte.py, MIT) against docangle on EXACT quarter turns of upright pages.

  PYTHONPATH=. python -m bench.docorient_quarter --out reports/docorient_quarter_turns.txt

The earlier comparison (reports/exp_docorient.json, FINAL_REPORT section 8) used pages turned by arbitrary angles, which DocOrient does not claim to handle. Here every page is turned by 0, 90, 180
and 270 degrees (np.rot90, no resampling). The sign of DocOrient's `angle` is not documented: it is read as the correction (the page was turned CCW by -angle), which is what fits the data. Pages are
assumed upright before turning; RVL-CDIP scans are not always upright (about 12 % of "upright invoice" labels are wrong, FINAL_REPORT section 5), so that pool is a pessimistic proxy for both methods.
"""
from __future__ import annotations

import argparse
import glob
import time

import cv2
import numpy as np
from PIL import Image

from docangle import DocumentOrientationPipeline, angular_distance


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    from docorient import detect_orientation

    from .exp_duarte import Duarte
    duarte = Duarte()
    perm = np.array([0, 3, 2, 1])                         # model logit index -> our clockwise class (measured)
    pipe = DocumentOrientationPipeline()
    sets = {"az (born-digital Azerbaijani pages)": sorted(glob.glob("data/az_test_pages/*.png"))[:a.n],
            "invoices (RVL-CDIP scans)": sorted(glob.glob("data/invoices_rvl_test/*.*"))[:a.n]}
    lines = ["exact quarter turns of upright pages: share of cases with the right quadrant"]
    for name, files in sets.items():
        ok_do = ok_ours = ok_du = n = 0
        t_do = t_ours = t_du = 0.0
        for f in files:
            img = cv2.imread(f)
            if img is None:
                continue
            for k in range(4):
                rot = np.ascontiguousarray(np.rot90(img, k))
                t = time.perf_counter()
                r = detect_orientation(Image.fromarray(cv2.cvtColor(rot, cv2.COLOR_BGR2RGB)))
                t_do += time.perf_counter() - t
                ok_do += (-r.angle) % 360 == 90 * k
                t = time.perf_counter()
                ok_du += perm[int(np.argmax(duarte.logits(rot)))] == ((360 - 90 * k) % 360) // 90
                t_du += time.perf_counter() - t
                t = time.perf_counter()
                ang = pipe.predict(rot).angle
                t_ours += time.perf_counter() - t
                ok_ours += ang is not None and angular_distance(ang, 90 * k) < 45
                n += 1
        lines.append(f"{name}: {n} cases | DocOrient {100 * ok_do / n:.1f} % ({1000 * t_do / n:.0f} ms) | Duarte {100 * ok_du / n:.1f} % ({1000 * t_du / n:.0f} ms, one view) | docangle {100 * ok_ours / n:.1f} % ({1000 * t_ours / n:.0f} ms)")
    text = "\n".join(lines)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
