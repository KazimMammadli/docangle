"""Latency of one call on an image FILE (decode + analysis) for three input sizes.

  python -m bench.latency_files > reports/latency_files_v4_4.txt

Twenty pages of the private pool are rescaled to 1000, 3508 and 4032 px (long side), written as JPEG (quality 90) and timed with
``DocumentOrientationPipeline().predict(path)``: 3 warm-up calls, then 3 passes over the 20 files. Run it on mains power and an idle desktop.
"""
from __future__ import annotations

import glob
import os
import tempfile
import time

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES = (("1 MP JPEG (about 1000 px)", 1000), ("A4 at 300 dpi JPEG (3508 px)", 3508), ("12 MP phone JPEG (4032 px)", 4032))
PAGES, PASSES, WARMUP, JPEG_QUALITY = 20, 3, 3, 90


def write_jpegs(files, long_side, folder):
    paths = []
    for i, f in enumerate(files):
        im = cv2.imread(f)
        h, w = im.shape[:2]
        k = long_side / max(h, w)
        im = cv2.resize(im, (round(w * k), round(h * k)), interpolation=cv2.INTER_CUBIC if k > 1 else cv2.INTER_AREA)
        path = os.path.join(folder, f"{long_side}_{i}.jpg")
        cv2.imwrite(path, im, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        paths.append(path)
    return paths


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "az_test_pages", "*.png")))[:PAGES]
    if not files:
        raise SystemExit("data/az_test_pages is not available: put any set of page images there (see docs/12-reproduce.md)")
    pipe = DocumentOrientationPipeline()
    with tempfile.TemporaryDirectory() as folder:
        for label, long_side in SIZES:
            paths = write_jpegs(files, long_side, folder)
            for p in paths[:WARMUP]:
                pipe.predict(p)
            ms = []
            for _ in range(PASSES):
                for p in paths:
                    t0 = time.perf_counter()
                    pipe.predict(p)
                    ms.append((time.perf_counter() - t0) * 1000)
            ms = np.array(ms)
            print(f"{label:32s} n={len(ms)} mean {ms.mean():.1f} median {np.median(ms):.1f} p95 {np.percentile(ms, 95):.1f} ms", flush=True)


if __name__ == "__main__":
    main()
