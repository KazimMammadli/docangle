"""CLI: python -m docangle IMAGE_PDF_OR_DIR [-o OUT] [--json] [--threads N] [--page N|all] [--consensus]"""

import argparse
import dataclasses
import glob
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

from .consensus import apply_job_consensus
from .errors import DocAngleError, ImageReadError
from .pipeline import PipelineConfig, Result, get_pipeline

_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".pdf")


def _jobs(paths, page):
    """Expand inputs to (label, path, page_index); a PDF yields one job per requested page."""
    jobs = []
    for p in paths:
        if p.lower().endswith(".pdf"):
            from .pdf import pdf_page_count
            try:
                pages = range(pdf_page_count(p)) if page == "all" else [int(page)]
            except ImageReadError:                      # a damaged PDF becomes one UNREADABLE row, the others still run
                pages = [0]
            jobs += [(f"{p}#{k + 1}", p, k) for k in pages]
        else:
            jobs.append((p, p, 0))
    return jobs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="docangle", description="Document rotation angle detector")
    ap.add_argument("input", help="image file, PDF file, or a directory of them")
    ap.add_argument("-o", "--output", help="write the upright image (file) or a directory (several pages)")
    ap.add_argument("--json", action="store_true", help="print one JSON object per page")
    ap.add_argument("--threads", type=int, default=0,
                    help="parallel pages (default 0 = automatic: min(4, CPU count); 1 = sequential). PDF pages are rendered one at a time (PDFium is not thread-safe), the analysis runs in parallel")
    ap.add_argument("--page", default="0", help="PDF page, 0-based, or 'all' (default 0)")
    ap.add_argument("--no-lean", action="store_true", help="batch mode: keep ONNX Runtime thread spinning and OpenCV's own threads (default for batches: lean)")
    ap.add_argument("--pdf-fast", action="store_true",
                    help="scanned PDF pages: take the page's single JPEG directly instead of rendering it (faster; unusual pages fall back to rendering; "
                         "experimental, see reports/FINAL_REPORT.md section 17)")
    ap.add_argument("--consensus", action="store_true",
                    help="treat the pages of one PDF, and the images of one directory, as one scan job: unsure pages follow the "
                         "others, odd pages are sent to review (do not use for unrelated photos)")
    args = ap.parse_args(argv)
    if args.page != "all" and not args.page.isdigit():
        print("error: --page must be a number or 'all'", file=sys.stderr)
        return 2

    cfg = PipelineConfig(pdf_fast_path=args.pdf_fast)
    if args.threads <= 0:
        args.threads = max(1, min(4, os.cpu_count() or 1))
    try:
        if os.path.isdir(args.input):
            paths = sorted(p for p in glob.glob(os.path.join(args.input, "*")) if p.lower().endswith(_EXT))
        elif os.path.isfile(args.input):
            paths = [args.input]
        else:
            print(f"error: not found: {args.input}", file=sys.stderr)
            return 2
        if not paths:
            print("error: no images found", file=sys.stderr)
            return 2
        jobs = _jobs(paths, args.page)
        to_dir = len(jobs) > 1 or args.page == "all" or os.path.isdir(args.input)     # several pages possible: -o is a directory
        if args.output and to_dir:
            os.makedirs(args.output, exist_ok=True)
        parallel = args.threads > 1 and len(jobs) > 1
        if parallel and not args.no_lean:
            # Pages run in parallel: idle ONNX / OpenCV threads should not busy-wait or oversubscribe the cores (identical results,
            # about a third less CPU per page, more pages/s; reports/cpu_knobs.txt). A single page keeps the fastest latency settings.
            cfg = dataclasses.replace(cfg, ort_spinning=False)
            cv2.setNumThreads(1)
        pipe = get_pipeline(cfg)

        def one(job):
            _, path, page = job
            try:
                if args.output and not args.consensus:
                    img, res = pipe.correct(path, page=page)
                    return res, img
                return pipe.predict(path, page=page), None
            except ImageReadError:
                return Result(angle=None, confidence=0.0, quality="UNDETERMINED", needs_review=True,
                              reasons=["UNREADABLE"]), None

        def emit(job, r, img) -> int:
            label, path, page = job
            if args.json:
                print(json.dumps({"file": label, **r.to_dict()}, ensure_ascii=False), flush=True)
            else:
                a = "undetermined" if r.angle is None else f"{r.angle:+.2f}"
                flag = "  [REVIEW]" if r.needs_review else ""
                print(f"{label}\t{a}\tconf={r.confidence:.2f}\t{r.quality}{flag}\t{','.join(r.reasons)}", flush=True)
            if args.output and img is not None:
                if not to_dir:
                    dst = args.output
                else:
                    stem, ext = os.path.splitext(os.path.basename(path))
                    dst = os.path.join(args.output, f"{stem}_p{page + 1}.png" if ext.lower() == ".pdf"
                                       else os.path.basename(path))
                if img.dtype == np.uint16 and not dst.lower().endswith((".png", ".tif", ".tiff")):
                    img = (img >> 8).astype(np.uint8)          # JPEG and most formats are 8-bit; OpenCV would saturate, not scale
                try:
                    ok = cv2.imwrite(dst, img)
                except cv2.error:
                    ok = False
                if not ok:
                    print(f"error: could not write {dst}", file=sys.stderr)
                    return 1
            return 0

        if not args.consensus:
            # Streaming: every result is printed (and its upright image written and dropped) as soon as it is ready, in input order,
            # so a long PDF shows progress at once and no page image is kept in memory.
            if parallel:
                with ThreadPoolExecutor(max_workers=args.threads) as ex:
                    for job, (r, img) in zip(jobs, ex.map(one, jobs)):
                        if emit(job, r, img):
                            return 1
            else:
                for job in jobs:
                    r, img = one(job)
                    if emit(job, r, img):
                        return 1
            return 0

        # --consensus needs every page of a job before any result can be final
        if parallel:
            with ThreadPoolExecutor(max_workers=args.threads) as ex:
                outs = list(ex.map(one, jobs))
        else:
            outs = [one(j) for j in jobs]
        groups = {}
        for k, (_, path, _) in enumerate(jobs):
            groups.setdefault(path if path.lower().endswith(".pdf") else os.path.dirname(os.path.abspath(path)), []).append(k)
        for ks in groups.values():
            for k, r in zip(ks, apply_job_consensus([outs[k][0] for k in ks], cfg)):
                outs[k] = (r, None)
        for k, job in enumerate(jobs):
            r, img = outs[k]
            if args.output and r.angle is not None:
                img = pipe.render_upright(job[1], r.angle, page=job[2])
            if emit(job, r, img):
                return 1
        return 0
    except DocAngleError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
