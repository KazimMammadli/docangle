"""Fairness check for the Tesseract candidate of bench/compare_open_models.py: does telling Tesseract the resolution change its answers?

  TESSERACT_ROOT=/path/to/tesseract/prefix PYTHONPATH=. python -m bench.tesseract_dpi_check --out reports/tesseract_dpi_check.txt

Images that come from OpenCV carry no resolution, and Tesseract then assumes one and says so on stderr. The comparison runs Tesseract exactly as its documentation
shows (`--psm 0 -l osd`); this check runs the same exact quarter turns again with `--dpi 150` and `--dpi 300` and counts how many answers change. If none did, the
comparison did not handicap Tesseract by leaving the resolution out.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile

import cv2

from bench.compare_open_models import TesseractOSD, cases_quarter


def osd(tool, bgr, dpi=None):
    """(quadrant the page is turned by or None, whether Tesseract complained about the resolution)."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "page.png")
        cv2.imwrite(path, bgr)
        cmd = [tool.bin, path, "stdout", "--psm", "0"] + (["--dpi", str(dpi)] if dpi else []) + ["-l", "osd"]
        out = subprocess.run(cmd, capture_output=True, text=True, env=tool.env)
    q = None
    for line in out.stdout.splitlines() + out.stderr.splitlines():
        if line.startswith("Rotate:"):
            q = (int(line.split(":")[1]) % 360) // 90
    return q, "resolution" in out.stderr.lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8, help="pages per pool (each is turned four times)")
    ap.add_argument("--datasets", nargs="+", default=["az", "invoices", "ext_funsd", "ext_doclaynet", "ext_cord"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    tool = TesseractOSD()
    variants = {"as in the comparison (no --dpi)": None, "--dpi 150": 150, "--dpi 300": 300}
    got = {k: [] for k in variants}
    truth, warned = [], 0
    for meta, img in cases_quarter(a):
        truth.append(meta["gt_q"])
        for k, dpi in variants.items():
            q, w = osd(tool, img, dpi)
            got[k].append(q)
            warned += int(w and dpi is None)
    n = len(truth)
    base = got["as in the comparison (no --dpi)"]
    lines = [f"Tesseract OSD on {n} exact quarter turns ({', '.join(a.datasets)}, {a.n} pages each); the program warned about the missing resolution in {warned} of them", ""]
    lines.append("| variant | right | wrong | no answer | answers different from the default |")
    lines.append("|---|---|---|---|---|")
    for k, v in got.items():
        right = sum(x == t for x, t in zip(v, truth))
        none = sum(x is None for x in v)
        differ = sum(x != b for x, b in zip(v, base))
        lines.append(f"| {k} | {right} | {n - right - none} | {none} | {differ} |")
    text = "\n".join(lines)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")


if __name__ == "__main__":
    main()
