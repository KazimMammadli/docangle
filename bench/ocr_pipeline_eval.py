"""End-to-end check of tools/ocr_pipeline.py on a synthetic scanned PDF, scored against the text layer of the born-digital originals.

  python -m bench.ocr_pipeline_eval --out reports/ocr_pipeline_eval            (a python with docangle + paddleocr + paddlepaddle-gpu; add --device cpu for no GPU)

12 Azerbaijani pages (the section 19 test pages), each turned by a different angle the way a scanner or a camera would (exact quarter turns, other
angles with Lanczos), are written into ONE PDF (one raster per page, 150 dpi). tools.ocr_pipeline reads that PDF twice, with the same engine (PaddleOCR PP-OCRv6 or Tesseract):
alone (the pages as a viewer shows them) and with docangle in front. Metric: word F1 (order independent, diacritics folded) per page, mean, and the time per stage.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bench.ocr_rotation_eval import ANGLES, pick_pages, word_f1  # noqa: E402
from bench.ocr_upright_quality import camera_rotate  # noqa: E402
from tests.unit.helpers import make_scan_pdf  # noqa: E402

PAGE_ANGLES = ANGLES + [-37, 12, 200]


def build_pdf(path, n):
    pages = pick_pages(n)
    scans = [cv2.cvtColor(camera_rotate(cv2.imread(pg["png"]), ang), cv2.COLOR_BGR2GRAY) for pg, ang in zip(pages, PAGE_ANGLES)]
    make_scan_pdf(path, scans, dpi=150)
    return pages


def read_rows(out):
    return [json.loads(line) for line in open(os.path.join(out, "pages.jsonl"), encoding="utf-8")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/ocr_pipeline_eval")
    ap.add_argument("--pdf", default=None, help="where to write the synthetic PDF (default: <out>/scan.pdf, not for git)")
    ap.add_argument("--engine", default="paddle")
    ap.add_argument("--device", default="gpu:0")
    ap.add_argument("--tesseract-bin", default=None)
    ap.add_argument("--tessdata", default=None)
    ap.add_argument("--docangle-device", default="auto")
    ap.add_argument("--long-side", type=int, default=2480)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    pdf = a.pdf or os.path.join(a.out, "scan.pdf")
    pages = build_pdf(pdf, len(PAGE_ANGLES))
    gt = [p["text"] for p in pages]
    common = [pdf, "--page", "all", "--engine", a.engine, "--device", a.device, "--long-side", str(a.long_side)]
    if a.tesseract_bin:
        common += ["--tesseract-bin", a.tesseract_bin]
    if a.tessdata:
        common += ["--tessdata", a.tessdata]
    runs = {"alone": ["--no-docangle"], "docangle": ["--docangle-device", a.docangle_device]}
    result = {}
    for name, extra in runs.items():
        out = os.path.join(a.out, name)
        subprocess.run([sys.executable, "-m", "tools.ocr_pipeline", *common, "--out", out, *extra], check=True)
        result[name] = read_rows(out)

    lines = [f"{len(pages)} pages in one scanned PDF (150 dpi rasters), rendered at {a.long_side} px long side, engine {a.engine}; word F1 %, per page",
             f"{'page':>4} {'true angle':>10} {'found':>8} {'review':>6} | {'OCR alone':>9} {'+ docangle':>10}"]
    f1 = {k: [word_f1(g, " ".join(r["lines"])) * 100 for g, r in zip(gt, rows)] for k, rows in result.items()}
    for i, (ang, r) in enumerate(zip(PAGE_ANGLES, result["docangle"])):
        found = r.get("angle")
        lines.append(f"{i + 1:4d} {ang:10d} {'-' if found is None else format(found, '+.2f'):>8} {'yes' if r.get('needs_review') else '':>6} | {f1['alone'][i]:9.1f} {f1['docangle'][i]:10.1f}")
    lines.append(f"{'mean':>4} {'':>10} {'':>8} {'':>6} | {np.mean(f1['alone']):9.1f} {np.mean(f1['docangle']):10.1f}")
    err = [min(abs(((r['angle'] - ang + 180) % 360) - 180), 999) for ang, r in zip(PAGE_ANGLES, result["docangle"]) if r.get("angle") is not None]
    lines.append(f"docangle angle error: max {max(err):.2f} deg, mean {np.mean(err):.2f} deg over {len(err)} pages; "
                 f"{sum(1 for r in result['docangle'] if r.get('needs_review'))} of {len(pages)} sent to review")
    for name, rows in result.items():
        med = lambda k: float(np.median([r[k] for r in rows if r[k]] or [0.0]))
        sm = json.load(open(os.path.join(a.out, name, "summary.json")))
        lines.append(f"{name:9s} median per page: CPU side {med('front_ms'):.0f} ms, OCR {med('ocr_ms'):.0f} ms; {sm['pages']} pages in {sm['wall_s']} s = {sm['pages_per_s']} pages/s; "
                     f"sum of OCR times {sum(r['ocr_ms'] for r in rows) / 1000:.1f} s; GPU memory {sm['gpu_memory_mb']} MB")
    text = "\n".join(lines)
    print("\n" + text)
    with open(os.path.join(a.out, "summary.txt"), "w", encoding="utf-8") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    main()
