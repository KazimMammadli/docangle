"""PDF / image -> angle (docangle) -> upright page -> OCR -> text, in one command: the angle step in front of an OCR, end to end.

  python -m tools.ocr_pipeline scan.pdf --page all --out reports/ocr_run          # docangle on the GPU + PaddleOCR PP-OCRv6 on the GPU
  python -m tools.ocr_pipeline scans_dir/ --engine tesseract --docangle-device cpu   # no GPU: Tesseract (needs the tesseract program and its aze model)
  python -m tools.ocr_pipeline scan.pdf --page all --no-docangle                  # the OCR alone, nothing rotated: the comparison

Needs ONE python environment with docangle's requirements plus `paddleocr` and `paddlepaddle-gpu` (or, for --engine tesseract, only the tesseract program) (for the GPU: also `onnxruntime-gpu`; the CUDA
libraries of the pip packages are found without LD_LIBRARY_PATH). Per page: docangle finds the angle and the review flag and rotates the page upright
(lossless quarter turns, reports/FINAL_REPORT.md section 20; a PDF page is rendered at --long-side px: 2480 is about 210 dpi for A4, 3508 is 300 dpi), the
OCR reads it. The next page is prepared on the CPU while the GPU reads the current one. The white border that straightening adds is cut before the OCR (--no-crop keeps it). Pages that need review are read anyway, with the best-guess angle,
and marked; --skip-review leaves them out. Writes to --out: pages.jsonl (per page: label, angle, confidence, needs_review, reasons, lines, ocr_score,
milliseconds per stage), text.txt (all pages, review pages marked), summary.json (timings, GPU memory) and, with --save-images, the upright pages the OCR saw.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline, ImageReadError, ModelNotFoundError, PipelineConfig
from docangle.pdf import pdf_page_count, render_pdf_page

EXT = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".pdf")


def list_jobs(inputs, page):
    """(label, path, page_index) for every page to read; a PDF yields one job per requested page."""
    paths = []
    for p in inputs:
        paths += sorted(q for q in glob.glob(os.path.join(p, "*")) if q.lower().endswith(EXT)) if os.path.isdir(p) else [p]
    jobs = []
    for p in paths:
        if p.lower().endswith(".pdf"):
            try:
                pages = range(pdf_page_count(p)) if page == "all" else [int(page)]
            except ImageReadError:                      # a damaged PDF becomes one unreadable row, the others still run
                pages = [0]
            jobs += [(f"{p}#{k + 1}", p, k) for k in pages]
        else:
            jobs.append((p, p, 0))
    return jobs


def warm_up_image():
    """A small page of text lines: forces every ONNX session / OCR model to load and run once before anything is timed."""
    img = np.full((600, 800, 3), 255, np.uint8)
    for k in range(12):
        cv2.putText(img, "docangle warm up line %d 0123456789" % k, (40, 50 + 40 * k), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    return img


def make_pipeline(device, long_side):
    """docangle pipeline; device 'auto' uses the GPU when ONNX Runtime can load its CUDA provider and says so when it falls back to the CPU."""
    warm = warm_up_image()
    if device in ("auto", "cuda"):
        try:
            pipe = DocumentOrientationPipeline(PipelineConfig(pdf_long_side=long_side, ort_provider="cuda"))
            pipe.predict(warm)
            return pipe, "cuda"
        except ModelNotFoundError as e:
            if device == "cuda":
                raise
            print(f"note: docangle runs on the CPU ({e})", file=sys.stderr)
    pipe = DocumentOrientationPipeline(PipelineConfig(pdf_long_side=long_side))
    pipe.predict(warm)
    return pipe, "cpu"


def make_reader(device):
    """PaddleOCR PP-OCRv6 (the default models: they read the Azerbaijani letter ə), its own orientation / unwarping modules off: docangle does that."""
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(device=device, enable_mkldnn=False, use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False)

    def read(img):
        r = ocr.predict(img)[0]
        scores = [float(s) for s in r["rec_scores"]]
        return [str(t) for t in r["rec_texts"]], (float(np.mean(scores)) if scores else 0.0)

    read(warm_up_image())
    return read


def crop_white(img, margin=0.02, white=245):
    """Cut the white border that straightening adds (a page turned 45 degrees has twice the area): the OCR time and its GPU memory follow the image area."""
    g = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ink = g < white
    rows, cols = np.flatnonzero(ink.any(1)), np.flatnonzero(ink.any(0))
    if rows.size == 0:
        return img
    m = int(margin * max(img.shape[:2]))
    y0, y1 = max(0, rows[0] - m), min(img.shape[0], rows[-1] + m + 1)
    x0, x1 = max(0, cols[0] - m), min(img.shape[1], cols[-1] + m + 1)
    return img[y0:y1, x0:x1]


def make_tesseract_reader(binary, tessdata, lang):
    """Tesseract 5 as a command-line program (one OpenMP thread, page segmentation mode 3): the OCR for machines without a GPU."""
    binary = binary or shutil.which("tesseract")
    if not binary:
        raise SystemExit("error: tesseract not found: install it or give --tesseract-bin")
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    if tessdata:
        env["TESSDATA_PREFIX"] = tessdata

    def read(img):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "page.png")
            cv2.imwrite(path, img)
            out = subprocess.run([binary, path, "stdout", "-l", lang, "--psm", "3"], capture_output=True, text=True, env=env)
        return [ln for ln in out.stdout.splitlines() if ln.strip()], None

    return read


def front(pipe, long_side, crop, job):
    """CPU side of one page: decode / render, find the angle, rotate. Runs up to two pages ahead of the OCR."""
    label, path, page = job
    t0 = time.perf_counter()
    try:
        if pipe is not None:
            img, res = pipe.correct(path, page=page)
            if crop and img is not None:
                img = crop_white(img)
        else:
            img = render_pdf_page(path, page, long_side, color=True) if path.lower().endswith(".pdf") else cv2.imread(path)
            res = None
            if img is None:
                raise ImageReadError(f"cannot read {path}")
        return dict(job=job, img=img, res=res, error=None, front_ms=(time.perf_counter() - t0) * 1000.0)
    except ImageReadError as e:
        return dict(job=job, img=None, res=None, error=str(e) or "UNREADABLE", front_ms=(time.perf_counter() - t0) * 1000.0)


def gpu_mem_mb():
    try:
        out = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
    except OSError:
        return None
    for line in out.splitlines():
        pid, mem = [x.strip() for x in line.split(",")]
        if int(pid) == os.getpid():
            return int(mem)
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="angle -> upright -> OCR in one command")
    ap.add_argument("inputs", nargs="+", help="image files, PDF files, or directories of them")
    ap.add_argument("--page", default="0", help="PDF page, 0-based, or 'all' (default 0)")
    ap.add_argument("--out", default="reports/ocr_run")
    ap.add_argument("--engine", choices=["paddle", "tesseract"], default="paddle", help="paddle = PaddleOCR PP-OCRv6 (GPU recommended), tesseract = Tesseract 5 on the CPU")
    ap.add_argument("--device", default="gpu:0", help="PaddleOCR device: gpu:0 (default) or cpu")
    ap.add_argument("--tesseract-bin", default=None, help="path of the tesseract program (default: from PATH)")
    ap.add_argument("--tessdata", default=None, help="folder with the .traineddata files (TESSDATA_PREFIX)")
    ap.add_argument("--lang", default="aze", help="Tesseract language model (default aze)")
    ap.add_argument("--docangle-device", choices=["auto", "cuda", "cpu"], default="auto", help="auto = GPU if ONNX Runtime can use it")
    ap.add_argument("--long-side", type=int, default=2480, help="PDF pages are rendered to this long side in px (default 2480, about 210 dpi for A4)")
    ap.add_argument("--no-docangle", action="store_true", help="read the page as it is (no angle step), for comparison")
    ap.add_argument("--no-crop", action="store_true", help="keep the white border that straightening adds (default: cut it before the OCR)")
    ap.add_argument("--skip-review", action="store_true", help="do not read pages that need review")
    ap.add_argument("--save-images", action="store_true", help="also write the upright page images the OCR read")
    a = ap.parse_args(argv)
    if a.page != "all" and not a.page.isdigit():
        print("error: --page must be a number or 'all'", file=sys.stderr)
        return 2
    missing = [p for p in a.inputs if not os.path.exists(p)]
    if missing:
        print(f"error: not found: {missing[0]}", file=sys.stderr)
        return 2
    jobs = list_jobs(a.inputs, a.page)
    if not jobs:
        print("error: no images or PDFs found", file=sys.stderr)
        return 2
    os.makedirs(os.path.join(a.out, "pages") if a.save_images else a.out, exist_ok=True)

    t0 = time.perf_counter()
    pipe, dev = (None, "none") if a.no_docangle else make_pipeline(a.docangle_device, a.long_side)
    t1 = time.perf_counter()
    read = make_reader(a.device) if a.engine == "paddle" else make_tesseract_reader(a.tesseract_bin, a.tessdata, a.lang)
    ocr_name = f"PaddleOCR PP-OCRv6 on {a.device}" if a.engine == "paddle" else f"Tesseract ({a.lang}) on the CPU"
    t2 = time.perf_counter()
    print(f"docangle: {dev} ({t1 - t0:.1f} s to load) | OCR: {ocr_name} ({t2 - t1:.1f} s to load) | {len(jobs)} page(s)", file=sys.stderr)

    rows, text_parts = [], []
    wall0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=1) as ex:
        todo, window = iter(jobs), deque()
        for _ in range(2):                                  # the CPU side runs up to two pages ahead of the OCR
            j = next(todo, None)
            if j is not None:
                window.append(ex.submit(front, pipe, a.long_side, not a.no_crop, j))
        while window:
            f = window.popleft().result()
            j = next(todo, None)
            if j is not None:
                window.append(ex.submit(front, pipe, a.long_side, not a.no_crop, j))
            label, path, page = f["job"]
            res, img = f["res"], f["img"]
            row = dict(label=label, file=path, page=page, front_ms=round(f["front_ms"], 1), ocr_ms=0.0, lines=[], ocr_score=None, skipped=None)
            if res is not None:
                row.update(angle=res.angle, confidence=res.confidence, needs_review=res.needs_review, reasons=res.reasons, quality=res.quality)
            if f["error"]:
                row["skipped"] = "UNREADABLE"
            elif img is None:
                row["skipped"] = "UNDETERMINED"             # blank / too small: no angle, nothing to read
            elif a.skip_review and res is not None and res.needs_review:
                row["skipped"] = "NEEDS_REVIEW"
            else:
                t = time.perf_counter()
                row["lines"], row["ocr_score"] = read(img)
                row["ocr_ms"] = round((time.perf_counter() - t) * 1000.0, 1)
                row["size"] = [int(img.shape[1]), int(img.shape[0])]
                if a.save_images:
                    stem = os.path.splitext(os.path.basename(path))[0]
                    cv2.imwrite(os.path.join(a.out, "pages", f"{stem}_p{page + 1:03d}.png"), img)
            rows.append(row)
            flag = "  [REVIEW %s]" % ",".join(row.get("reasons") or []) if row.get("needs_review") else ""
            ang = row.get("angle")
            info = "  (no angle step)" if res is None else f"  angle={'-' if ang is None else format(ang, '+.2f')}  conf={res.confidence:.2f}"
            head = f"=== {label}{info}{flag}{'  [SKIPPED ' + row['skipped'] + ']' if row['skipped'] else ''} ==="
            text_parts.append(head + "\n" + "\n".join(row["lines"]))
            print(f"{label}\t{'-' if ang is None else format(ang, '+.2f')}\tfront {row['front_ms']:.0f} ms\tOCR {row['ocr_ms']:.0f} ms\t{len(row['lines'])} lines{flag}", flush=True)
    wall = time.perf_counter() - wall0

    with open(os.path.join(a.out, "pages.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(a.out, "text.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(text_parts) + "\n")

    med = lambda k: float(np.median([r[k] for r in rows if r[k]] or [0.0]))
    summary = dict(pages=len(rows), wall_s=round(wall, 2), pages_per_s=round(len(rows) / wall, 3), front_ms_median=round(med("front_ms"), 1), ocr_ms_median=round(med("ocr_ms"), 1),
                   needs_review=sum(1 for r in rows if r.get("needs_review")), skipped=sum(1 for r in rows if r["skipped"]), docangle_device=dev, ocr_device=ocr_name,
                   long_side=a.long_side, load_s=dict(docangle=round(t1 - t0, 1), ocr=round(t2 - t1, 1)), gpu_memory_mb=gpu_mem_mb())
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    print(f"\n{summary['pages']} page(s) in {wall:.1f} s = {summary['pages_per_s']:.2f} pages/s (model loading and warm-up not counted); "
          f"median per page: CPU side {summary['front_ms_median']:.0f} ms (decode/render + angle + rotate), OCR {summary['ocr_ms_median']:.0f} ms; "
          f"{summary['needs_review']} need review, {summary['skipped']} skipped; GPU memory of this process: {summary['gpu_memory_mb']} MB", file=sys.stderr)
    print(f"written: {a.out}/pages.jsonl, {a.out}/text.txt, {a.out}/summary.json", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
