"""A fair comparison of docangle with other open-source page-orientation / skew estimators, on identical inputs and identical hardware.

  PYTHONPATH=. python -m bench.compare_open_models run --mode uniform  --out reports/benchmark/raw_uniform.json.gz     # simulated pages, every angle
  PYTHONPATH=. python -m bench.compare_open_models run --mode quarter  --out reports/benchmark/raw_quarter.json.gz     # clean pages, exact 0/90/180/270 turns
  PYTHONPATH=. python -m bench.compare_open_models run --mode handheld --out reports/benchmark/raw_handheld.json.gz    # one of the 4 quadrants + tilt up to 25 degrees
  PYTHONPATH=. python -m bench.compare_open_models run --mode smartdoc --out reports/benchmark/raw_smartdoc.json.gz    # real phone frames, whole and cut out
  PYTHONPATH=. python -m bench.compare_report summarize reports/benchmark/raw_*.json.gz --out reports/benchmark/RESULTS.md      # the tables

Rules that make it fair (the full text is docs/05-comparison.md):
  * ONE input per case. Every case image is made once (fixed seeds) and handed, as the same BGR uint8 array, to every candidate in the same process.
    Each candidate does its own pre-processing, exactly as its authors ship it. No candidate sees the ground truth, a crop, or the other candidates' answers.
  * ONE task per table. Quadrant task: which of 0/90/180/270 degrees is the page turned by (the answer a 4-class model can give). Cases within 5 degrees of a
    quadrant boundary are left out (the truth is ambiguous there). A candidate that gives no answer counts as wrong. Fine-angle task: the tilt modulo 90 degrees.
  * ONE machine, CPU only, 2 threads per ONNX session (the library default of docangle; DocOrient sets its own), one case at a time, models loaded and warm
    before timing, wall time of the whole call including the candidate's own pre-processing, median and 95th percentile.
  * Uncertainty: 95 % Wilson intervals whose sample size is the number of PAGES (or video clips), not of cases: the cases that are turned copies of one page are not
    independent. Paired counts against docangle (right/wrong on the same case) are given as well; tools may hold pages back for a person (equal review rate).
  * Disclosure (docs/05-comparison.md 5.5, not printed by this script): docangle's own classifier was trained on other pages of RVL-CDIP / Tobacco / CORD / DocLayNet;
    for third-party models the training data is, at best, partly documented).
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
EXT = os.path.join(ROOT, "data", "external")
TESS_ROOT = os.environ.get("TESSERACT_ROOT")      # a conda-style prefix (bin/tesseract, share/tessdata); default: `tesseract` on PATH
THREADS = 2
STRAIGHT = " after Fourier straightening"        # suffix of the name of a candidate that runs behind docangle's straightening

# ------------------------------------------------------------------------------------------------ candidates #
# Every candidate returns the rotation of the PAGE in 90-degree steps counter-clockwise, as an integer 0..3 (the quadrant), or None for "no answer".
# The class conventions below were measured (bench/exp_duarte.py calibrate_mapping, bench/docorient_quarter.py), not assumed.


def softmax(v):
    e = np.exp(np.asarray(v, np.float64) - np.max(v))
    return e / e.sum()


class DocAngle:
    name = "docangle 4.4 (default, CPU)"
    task = "both"

    def __init__(self):
        from docangle import DocumentOrientationPipeline, PipelineConfig
        self.pipe = DocumentOrientationPipeline(PipelineConfig())
        self.last = None

    def predict(self, bgr):
        r = self.last = self.pipe.predict(bgr)
        self.conf, self.flag = (None if r.angle is None else float(r.confidence)), bool(r.needs_review)
        return None if r.angle is None else int(round(r.angle / 90.0)) % 4

    def fine_tilt(self):
        return None if self.last is None else self.last.fine_tilt


class DocAngleHough(DocAngle):
    name = "docangle fine tilt by Hough (v4.1 estimator)"
    task = "fine"

    def __init__(self):
        from docangle import DocumentOrientationPipeline, PipelineConfig
        self.pipe = DocumentOrientationPipeline(PipelineConfig(fine_estimator="hough"))
        self.last = None


class DocAngleCrop(DocAngle):
    name = "docangle 4.4 + doc_crop"
    task = "quadrant"

    def __init__(self):
        from docangle import DocumentOrientationPipeline, PipelineConfig
        self.pipe = DocumentOrientationPipeline(PipelineConfig(doc_crop=True))
        self.last = None


class PPLCNet:
    name = "PP-LCNet_x1_0_doc_ori (PaddleOCR), one view"
    task = "quadrant"

    def __init__(self):
        import onnxruntime as ort
        o = ort.SessionOptions()
        o.intra_op_num_threads = THREADS
        self.s = ort.InferenceSession(os.path.join(ROOT, "models", "pp_lcnet_doc_ori.onnx"), o, providers=["CPUExecutionProvider"])
        self.mean = np.array([0.485, 0.456, 0.406], np.float32)
        self.std = np.array([0.229, 0.224, 0.225], np.float32)

    def predict(self, bgr):
        h, w = bgr.shape[:2]
        k = 256.0 / min(h, w)
        im = cv2.resize(bgr, (max(224, round(w * k)), max(224, round(h * k))), interpolation=cv2.INTER_LINEAR)
        y0, x0 = (im.shape[0] - 224) // 2, (im.shape[1] - 224) // 2
        im = im[y0:y0 + 224, x0:x0 + 224, ::-1].astype(np.float32) / 255.0
        x = ((im - self.mean) / self.std).transpose(2, 0, 1)[None]
        p = self.s.run(None, {self.s.get_inputs()[0].name: x})[0][0]          # softmax output of the exported model
        c = int(np.argmax(p))                                                  # clockwise class
        self.conf = float(np.max(p))
        return (4 - c) % 4


class DocTRPage:
    name = "docTR page orientation (OnnxTR mobilenet_v3_small)"
    task = "quadrant"
    PERM = (0, 3, 2, 1)                                  # model logit index -> clockwise class (measured)

    def __init__(self):
        import onnxruntime as ort
        o = ort.SessionOptions()
        o.intra_op_num_threads = THREADS
        self.s = ort.InferenceSession(os.path.join(EXT, "doctr", "mobilenet_v3_small_page_orientation.onnx"), o, providers=["CPUExecutionProvider"])
        self.name_in = self.s.get_inputs()[0].name
        self.size = int(self.s.get_inputs()[0].shape[2])
        self.mean = np.array([0.694, 0.695, 0.693], np.float32)
        self.std = np.array([0.299, 0.296, 0.301], np.float32)

    def predict(self, bgr):
        S = self.size
        h, w = bgr.shape[:2]
        k = S / max(h, w)
        nh, nw = max(1, int(round(h * k))), max(1, int(round(w * k)))
        small = cv2.resize(bgr, (nw, nh), interpolation=cv2.INTER_LINEAR if k > 1 else cv2.INTER_AREA)[:, :, ::-1]
        canvas = np.zeros((S, S, 3), np.uint8)
        y0, x0 = (S - nh) // 2, (S - nw) // 2
        canvas[y0:y0 + nh, x0:x0 + nw] = small
        x = ((canvas.astype(np.float32) / 255.0 - self.mean) / self.std).transpose(2, 0, 1)[None]
        z = self.s.run(None, {self.name_in: x})[0][0]
        self.conf = float(np.max(softmax(z)))
        c = self.PERM[int(np.argmax(z))]
        return (4 - c) % 4


class DocOrient:
    name = "DocOrient 0.4.1 (PyPI docorient)"
    task = "quadrant"

    def predict(self, bgr):
        from docorient import detect_orientation
        from PIL import Image
        r = detect_orientation(Image.fromarray(np.ascontiguousarray(bgr[:, :, ::-1])))
        self.flag = not r.reliable                       # the library's own "not sure" signal; it gives no score
        return ((-r.angle) % 360) // 90                  # its angle is the correction: the page was turned CCW by -angle


class DuarteNet:
    name = "EfficientNetV2-S orientation model (DuarteBarbosa, one view)"
    task = "quadrant"

    def __init__(self):
        from bench.exp_duarte import Duarte
        self.m = Duarte(threads=THREADS)
        self.perm = (0, 3, 2, 1)

    def predict(self, bgr):
        z = np.asarray(self.m.logits(bgr)).reshape(-1)
        self.conf = float(np.max(softmax(z)))
        c = self.perm[int(np.argmax(z))]
        return (4 - c) % 4


class TesseractOSD:
    name = "Tesseract 5 OSD (--psm 0)"
    task = "quadrant"

    def __init__(self):
        self.bin = os.path.join(TESS_ROOT, "bin", "tesseract") if TESS_ROOT else shutil.which("tesseract")
        if not self.bin or not os.path.isfile(self.bin):
            raise FileNotFoundError("tesseract not found: put it on PATH or set TESSERACT_ROOT")
        self.env = dict(os.environ, OMP_THREAD_LIMIT="1")
        if TESS_ROOT:
            self.env["TESSDATA_PREFIX"] = os.path.join(TESS_ROOT, "share", "tessdata")

    def predict(self, bgr):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "page.png")
            cv2.imwrite(p, bgr)                           # the program reads files: writing the PNG is part of its cost
            o = subprocess.run([self.bin, p, "stdout", "--psm", "0", "-l", "osd"], capture_output=True, text=True, env=self.env)
        got = None
        for line in (o.stdout + o.stderr).splitlines():
            if line.startswith("Rotate:"):
                got = (int(line.split(":")[1]) % 360) // 90       # "Rotate: N" = turn clockwise by N to fix = the page is turned CCW by N
            elif line.startswith("Orientation confidence:"):
                self.conf = float(line.split(":")[1])             # not a probability (a ratio of scores); only its order is used
        return got


class MinAreaRect:
    name = "textbook cv2.minAreaRect deskew"
    task = "fine"

    def __init__(self):
        from bench.simple_deskew_baseline import minarea_tutorial
        self.f = minarea_tutorial
        self.last = None

    def predict(self, bgr):
        self.last = float(self.f(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)))
        return None

    def fine_tilt(self):
        return self.last


class Straightened:
    """Another candidate behind docangle's Fourier straightening: the page is turned upright by minus the estimated tilt first (as docangle does
    before its own classifiers), so that a model built for axis-aligned pages is not penalised for the tilt. Only the quadrant is judged."""
    task = "quadrant"

    def __init__(self, inner):
        from docangle.fftskew import FFTSkew
        self.inner, self.fft = inner, FFTSkew(512)
        self.name = inner.name.split(" (")[0] + STRAIGHT

    conf = property(lambda self: getattr(self.inner, "conf", None))
    flag = property(lambda self: getattr(self.inner, "flag", None))

    def predict(self, bgr):
        from docangle import rotate_image_expanded
        h, w = bgr.shape[:2]
        m = max(h, w)
        small = cv2.resize(bgr, (int(w * 1000 / m), int(h * 1000 / m)), interpolation=cv2.INTER_AREA) if m > 1000 else bgr
        tilt = self.fft.tilt(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
        return self.inner.predict(rotate_image_expanded(small, -tilt, border_val=255))


QUADRANT = [DocAngle, PPLCNet, DocTRPage, DocOrient, DuarteNet, TesseractOSD]
STRAIGHTENED = [PPLCNet, DocTRPage, DocOrient, DuarteNet]
FINE = [DocAngle, DocAngleHough, MinAreaRect]


def build(classes, only=None):
    out = []
    for c in classes:
        if only and c.__name__ not in only and c.name not in only:
            continue
        try:
            out.append(c())
        except Exception as e:                                  # a missing model must not stop the others; it is reported
            print(f"skipped {c.name}: {e}", file=sys.stderr)
    return out


# ---------------------------------------------------------------------------------------------------- cases #
def warm_page():
    img = np.full((700, 500, 3), 255, np.uint8)
    for y in range(40, 660, 18):
        cv2.line(img, (40, y), (460, y), (30, 30, 30), 2)
    return img


def cases_simulated(a, angle_mode, label):
    from bench.degrade import LEVELS, render, sample_angle
    from bench.run import make_cases
    for ds in a.datasets:
        for lv in a.levels:
            cases, _, _ = make_cases(ds, lv, angle_mode, a.seeds, a.n)
            for f, s, i, rng in cases:
                page = cv2.imread(f)
                gt = sample_angle(angle_mode, rng)
                yield dict(set=label, pool=ds, level=lv, page=f"{ds}/{os.path.basename(f)}", gt=gt, gt_q=int(round(gt / 90.0)) % 4,
                           ambiguous=abs(((gt + 45.0) % 90.0) - 45.0) > 40.0), render(page, gt, LEVELS[lv], rng)


def cases_uniform(a):
    return cases_simulated(a, "uniform", "simulated, any angle in [-180, 180]")


def cases_handheld(a):
    return cases_simulated(a, "quad_tilt", "simulated, one of the 4 quadrants + tilt up to 25 degrees")


def cases_quarter(a):
    from bench import datasets
    for ds in a.datasets:
        files = datasets.pool(ds)
        chosen, _ = datasets.pick(files, a.n, 0)
        for f in chosen:
            page = cv2.imread(f)
            for k in range(4):
                yield dict(set="quarter turns", pool=ds, level="clean", page=f"{ds}/{os.path.basename(f)}", gt=90.0 * k, gt_q=k, ambiguous=False), np.ascontiguousarray(np.rot90(page, k))


def cases_smartdoc(a):
    from bench.smartdoc_eval import ROOT as SD, gt_angle
    rows = [r for r in csv.DictReader(gzip.open(os.path.join(SD, "metadata.csv.gz"), "rt")) if int(r["frame_index"]) % a.every == 0]
    rng = np.random.default_rng(0)
    for r in rows:
        img = cv2.imread(os.path.join(SD, r["image_path"]))
        k = int(rng.integers(0, 4))
        pts = np.array([[float(r[q + "_x"]), float(r[q + "_y"])] for q in ("tl", "bl", "br", "tr")])
        x0, y0 = pts.min(0)
        x1, y1 = pts.max(0)
        m = 0.08 * max(x1 - x0, y1 - y0)
        H, W = img.shape[:2]
        cut = img[max(0, int(y0 - m)):min(H, int(y1 + m)), max(0, int(x0 - m)):min(W, int(x1 + m))]
        clip = f"{r['bg_name']}/{r['model_name']}/{r['model_subid']}"
        gt = gt_angle(r) + 90.0 * k           # the page is NOT always upright in the original frame (one background is filmed with the page turned by +-90 degrees): the truth is the corner-derived angle plus the turn
        for name, im in (("whole frame", img), ("document cut out", cut)):
            yield dict(set=f"SmartDoc {name}", pool=r["modeltype_name"], level="real camera", page=clip, gt=gt, gt_q=int(round(gt / 90.0)) % 4,
                       ambiguous=abs(((gt + 45.0) % 90.0) - 45.0) > 40.0), np.ascontiguousarray(np.rot90(im, k))


# --------------------------------------------------------------------------------------------------- running #
def run(a):
    quad = build(QUADRANT, a.candidates)
    fine = build(FINE, a.candidates)
    cands = {c.name: c for c in quad + fine}
    if a.straightened:
        for cls in STRAIGHTENED:
            w_ = Straightened(cls())
            cands[w_.name] = w_
    if a.mode == "smartdoc" and (not a.candidates or "DocAngleCrop" in a.candidates):
        cands[DocAngleCrop.name] = DocAngleCrop()
    w = warm_page()
    for c in cands.values():                                      # load and warm everything before the first timed case
        c.predict(w)
    gen = {"uniform": cases_uniform, "handheld": cases_handheld, "quarter": cases_quarter, "smartdoc": cases_smartdoc}[a.mode](a)
    rows, t0 = [], time.time()
    for meta, img in gen:
        row = dict(meta)
        for name, c in cands.items():
            if not isinstance(c, Straightened):
                c.conf = c.flag = None                            # whatever a candidate does not provide stays empty
            t = time.perf_counter()
            try:
                q = c.predict(img)
            except Exception as e:                                # a crash is "no answer", counted against the candidate
                q = None
                row.setdefault("errors", {})[name] = repr(e)[:80]
            ms = (time.perf_counter() - t) * 1000.0
            ft = c.fine_tilt() if hasattr(c, "fine_tilt") else None
            extra = {} if ft is None else dict(tilt=round(float(ft), 3))
            if getattr(c, "conf", None) is not None:
                extra["conf"] = round(float(c.conf), 4)
            if getattr(c, "flag", None) is not None:
                extra["flag"] = bool(c.flag)
            row[name] = dict(q=q, ms=round(ms, 1), **extra)
        rows.append(row)
        if len(rows) % 50 == 0:
            print(f"{len(rows)} cases, {time.time() - t0:.0f} s", flush=True)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with gzip.open(a.out, "wt") as fh:
        json.dump(dict(mode=a.mode, args=vars(a), versions=versions(), candidates=list(cands), rows=rows), fh)
    print("wrote", a.out, len(rows), "cases")


def versions():
    import onnxruntime
    v = dict(python=sys.version.split()[0], numpy=np.__version__, opencv=cv2.__version__, onnxruntime=onnxruntime.__version__)
    try:
        import docorient
        v["docorient"] = getattr(docorient, "__version__", "0.4.1")
    except Exception:
        pass
    import docangle
    v["docangle"] = docangle.__version__
    v["cpu"] = next((ln.split(":")[1].strip() for ln in open("/proc/cpuinfo") if ln.startswith("model name")), "?")
    try:
        v["commit"] = subprocess.run(["git", "describe", "--always", "--dirty"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        pass                                                          # not a git checkout
    return v


def main():
    ap = argparse.ArgumentParser(description="run the candidates over the cases of one mode and store every answer (tables: bench/compare_report.py)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--mode", choices=["uniform", "handheld", "quarter", "smartdoc"], required=True)
    r.add_argument("--datasets", nargs="+", default=["az", "invoices", "tobacco_cert", "rvl_heldout", "ext_funsd", "ext_doclaynet", "ext_cord"])
    r.add_argument("--levels", nargs="+", default=["scan", "photo_easy", "photo_hard"])
    r.add_argument("--n", type=int, default=40, help="pages per pool and level")
    r.add_argument("--seeds", type=int, default=1)
    r.add_argument("--every", type=int, default=50, help="smartdoc: every K-th frame of each clip")
    r.add_argument("--candidates", nargs="*", default=None, help="class names to run (default all)")
    r.add_argument("--straightened", action="store_true", help="also run PPLCNet, DocTRPage, DocOrient and DuarteNet behind docangle's Fourier straightening")
    r.add_argument("--out", required=True)
    run(ap.parse_args())


if __name__ == "__main__":
    main()
