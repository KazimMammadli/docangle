"""Does the way the corrected page is rotated matter for the OCR? (old: bilinear everywhere; new: lossless quarter turns, no resample for tiny tilts, bicubic)

  PYTHONPATH=. python -m bench.ocr_upright_quality run --engine paddle_v6 --pages 12 --out reports/ocr_rotation/quality_paddle_v6_gpu.json
  python -m bench.ocr_upright_quality analyze reports/ocr_rotation/quality_*.json
  python -m bench.ocr_upright_quality sweep              # no OCR: sharpness kept by ONE resampling pass, versus the rotation angle

The rotated test inputs are made like a camera would (exact quarter turns lossless, other angles with Lanczos), so the correction is the ONLY resampling
a real photo would get. docangle finds the angle once; the page is then straightened two ways and read by the same engine:
  linear : upright(..., interpolation=INTER_LINEAR, lossless_quarter_turns=False)   (behaviour before 4.3.2)
  hq     : upright(...)                                                              (4.3.2: lossless quarter turns, tilts < 0.1 degree untouched, bicubic)
  asis   : the original upright page, untouched (the ceiling)
Also stored: sharpness kept = Laplacian variance of the corrected page (centre window of the original size, so the white corners of the larger canvas do not
dilute it) divided by that of the original page.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bench.ocr_rotation_eval import ANGLES, GT, cer, make_engine, pick_pages, word_f1  # noqa: E402


def lapvar(x):
    return cv2.Laplacian(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY) if x.ndim == 3 else x, cv2.CV_64F).var()


def centre(x, h, w):
    H, W = x.shape[:2]
    y0, x0 = max(0, (H - h) // 2), max(0, (W - w) // 2)
    return x[y0:y0 + h, x0:x0 + w]


def sharp_kept(img, page):
    """Edge sharpness of ``img`` (the page, corrected) relative to ``page`` (the upright original): 1.0 = nothing lost."""
    return lapvar(centre(img, *page.shape[:2])) / lapvar(page)


def camera_rotate(page, ang):
    from docangle import rotate_image_expanded
    if ang % 90 == 0:
        return np.ascontiguousarray(np.rot90(page, ang // 90))
    return rotate_image_expanded(page, float(ang), border_val=255, interpolation=cv2.INTER_LANCZOS4)


def run(a):
    from docangle import DocumentOrientationPipeline, upright
    pipe, eng = DocumentOrientationPipeline(), make_engine(a.engine)
    rows = json.load(open(a.out)) if os.path.exists(a.out) else []
    done = {(r["png"], r["angle"], r["cond"]) for r in rows}
    for pi, pg in enumerate(pick_pages(a.pages)):
        page = cv2.imread(pg["png"])
        if (pg["png"], 0, "asis") not in done:
            t0 = time.perf_counter(); txt = eng.read(page, eng.plain_mode)
            rows.append(dict(engine=eng.name, png=pg["png"], doc=pg["doc"], angle=0, cond="asis", sec=time.perf_counter() - t0, text=txt, sharp=1.0))
        for ang in a.angles:
            rot = camera_rotate(page, ang)
            res = pipe.predict(rot)
            for cond, kw in (("linear", dict(interpolation=cv2.INTER_LINEAR, lossless_quarter_turns=False)), ("hq", {})):
                if (pg["png"], ang, cond) in done:
                    continue
                img = upright(rot, res.angle, **kw)
                t0 = time.perf_counter(); txt = eng.read(img, eng.plain_mode)
                rows.append(dict(engine=eng.name, png=pg["png"], doc=pg["doc"], angle=ang, cond=cond, sec=time.perf_counter() - t0, text=txt,
                                 sharp=sharp_kept(img, page), found=res.angle))
        json.dump(rows, open(a.out, "w"), ensure_ascii=False)
        print(f"page {pi + 1} done", flush=True)


def _boot(d, rng):
    d = np.asarray(d, float)
    b = rng.choice(d, (4000, len(d))).mean(1)
    return d.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5), int((d > 0.05).sum()), int((d < -0.05).sum())


def analyze(a):
    gt = {p["png"]: p["text"] for p in json.load(open(GT))}
    rng = np.random.default_rng(0)
    for f in a.files:
        R = json.load(open(f))
        eng = R[0]["engine"]
        print(f"\n=== {eng} ===")
        angles = sorted({r["angle"] for r in R if r["cond"] != "asis"})
        pages = sorted({r["png"] for r in R})
        f1 = {(r["png"], r["angle"], r["cond"]): word_f1(gt[r["png"]], r["text"]) * 100 for r in R}
        print(f"{'condition':26s} " + " ".join(f"{x:>6d}" for x in angles) + "    mean")
        for c in ("linear", "hq"):
            vals = [np.mean([f1[(p, x, c)] for p in pages]) for x in angles]
            print(f"{c + ' (word F1 %)':26s} " + " ".join(f"{v:6.1f}" for v in vals) + f"   {np.mean(vals):5.1f}")
        for c in ("linear", "hq"):
            vals = [np.mean([min(cer(gt[r["png"]], r["text"]), 3) * 100 for r in R if r["cond"] == c and r["angle"] == x]) for x in angles]
            print(f"{c + ' (CER %)':26s} " + " ".join(f"{v:6.1f}" for v in vals) + f"   {np.mean(vals):5.1f}")
        for c in ("linear", "hq"):
            vals = [np.mean([r["sharp"] for r in R if r["cond"] == c and r["angle"] == x]) * 100 for x in angles]
            print(f"{c + ' (sharpness kept %)':26s} " + " ".join(f"{v:6.0f}" for v in vals) + f"   {np.mean(vals):5.0f}")
        base = {r["png"]: word_f1(gt[r["png"]], r["text"]) * 100 for r in R if r["cond"] == "asis"}
        print(f"{'original page, untouched':26s} word F1 {np.mean(list(base.values())):.1f} %  "
              f"CER {np.mean([min(cer(gt[r['png']], r['text']), 3) * 100 for r in R if r['cond'] == 'asis']):.1f} %")
        print("paired over pages (page-bootstrap 95 % interval), word F1 points:")
        groups = (("page already upright (0)", [0]), ("quarter turns 90/180/270", [90, 180, 270]), ("tilts 5/15/30/45", [5, 15, 30, 45]),
                  ("quarter turn + 45 (135)", [135]), ("all angles", angles))
        for name, grp in groups:
            m, lo, hi, better, worse = _boot([np.mean([f1[(p, x, "hq")] - f1[(p, x, "linear")] for x in grp]) for p in pages], rng)
            print(f"  hq - linear   {name:26s} {m:+6.2f}  [{lo:+5.2f}, {hi:+5.2f}]   pages better/worse {better}/{worse} of {len(pages)}")
        for c in ("linear", "hq"):
            m, lo, hi, better, worse = _boot([np.mean([f1[(p, x, c)] for x in angles]) - base[p] for p in pages], rng)
            print(f"  {c:6s} - untouched page, all angles  {m:+6.2f}  [{lo:+5.2f}, {hi:+5.2f}]   pages better/worse {better}/{worse} of {len(pages)}")


def sweep(a):
    from docangle import rotate_image_expanded
    pages = [cv2.imread(p["png"]) for p in pick_pages(a.pages)]
    print(f"{len(pages)} pages; edge sharpness kept after ONE rotation pass (centre window / original, mean and worst page)")
    print(f"{'angle':>7} | {'bilinear':>13} {'bicubic':>13} {'Lanczos-4':>13}")
    for ang in a.tilts:
        cells = []
        for ip in (cv2.INTER_LINEAR, cv2.INTER_CUBIC, cv2.INTER_LANCZOS4):
            v = [sharp_kept(rotate_image_expanded(p, -ang, border_val=255, interpolation=ip), p) * 100 for p in pages]
            cells.append(f"{np.mean(v):5.0f}% ({np.min(v):3.0f}%)")
        print(f"{ang:7.2f} | " + " ".join(cells))
    print("exact quarter turn (np.rot90): 100 % (same pixels)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--engine", required=True, choices=["easyocr", "paddle_mobile", "paddle_v6", "tesseract"])
    r.add_argument("--pages", type=int, default=12)
    r.add_argument("--angles", type=int, nargs="+", default=ANGLES)
    r.add_argument("--out", required=True)
    an = sub.add_parser("analyze")
    an.add_argument("files", nargs="+")
    sw = sub.add_parser("sweep")
    sw.add_argument("--pages", type=int, default=12)
    sw.add_argument("--tilts", type=float, nargs="+", default=[0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 5, 15, 30, 45])
    a = ap.parse_args()
    {"run": run, "analyze": analyze, "sweep": sweep}[a.cmd](a)


if __name__ == "__main__":
    main()
