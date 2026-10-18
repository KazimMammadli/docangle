"""Do ready-made OCR engines read rotated / skewed pages by themselves? And does docangle in front of them help?

  # run one engine (in the python that has it installed), resumable:
  PYTHONPATH=. python -m bench.ocr_rotation_eval run --engine easyocr --pages 12 --out reports/ocr_rotation/easyocr.json
  # tables from one or more result files:
  python -m bench.ocr_rotation_eval analyze reports/ocr_rotation/*.json

Ground truth = the text layer of the born-digital PDFs behind the Azerbaijani test pages (`data/external/ocr_eval/gt_pages.json`). Every page is rotated
(white expanded canvas, CCW) by 0, 5, 15, 30, 45, 90, 135, 180, 270 degrees and read under three conditions per engine mode:
  native  : the rotated image goes straight into the engine (with whatever orientation handling the engine has: modes listed per engine)
  ours    : docangle.correct() straightens the page first, then the engine's plain mode reads it
  oracle  : the page is rotated back by the KNOWN angle (ceiling of what any front end could give), then the engine's plain mode reads it
Metrics: word F1 (multiset of lower-cased, diacritic-folded words: independent of reading order) and CER (character error rate of the folded,
whitespace-collapsed text; reading-order sensitive, so only differences between conditions are meaningful), plus seconds per page.

The tables in reports/FINAL_REPORT.md section 19 were made before docangle 4.3.2, when straightening was bilinear everywhere. The 'oracle', the Tesseract
OSD turn and the textbook deskew below still use that bilinear rotate_image_expanded on purpose (they reproduce section 19); 'ours' (docangle.correct) now
uses the 4.3.2 rotation. bench/ocr_upright_quality.py (section 20) measured the difference: no effect of practical size.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import unicodedata
from collections import Counter

import cv2
import numpy as np

ANGLES = [0, 5, 15, 30, 45, 90, 135, 180, 270]
GT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "external", "ocr_eval", "gt_pages.json")
_FOLD = str.maketrans({"ə": "e", "Ə": "E", "ı": "i", "İ": "I"})


# ----------------------------- metrics ------------------------------------ #
def norm(s: str) -> str:
    return " ".join(unicodedata.normalize("NFC", s).split())


def fold(s: str) -> str:
    s = unicodedata.normalize("NFD", norm(s).translate(_FOLD))
    return "".join(c for c in s if not unicodedata.combining(c))


def lev(a: str, b: str) -> int:
    """Levenshtein distance by Myers' bit-parallel algorithm (Python big integers)."""
    if not a:
        return len(b)
    m = len(a)
    mask = (1 << m) - 1
    peq = {}
    for i, c in enumerate(a):
        peq[c] = peq.get(c, 0) | (1 << i)
    pv, mv, score, last = mask, 0, m, 1 << (m - 1)
    for c in b:
        eq = peq.get(c, 0)
        xv = eq | mv
        xh = (((eq & pv) + pv) ^ pv) | eq
        ph = mv | (~(xh | pv) & mask)
        mh = pv & xh
        if ph & last:
            score += 1
        elif mh & last:
            score -= 1
        ph = ((ph << 1) | 1) & mask
        mh = (mh << 1) & mask
        pv = (mh | (~(xv | ph) & mask)) & mask
        mv = ph & xv
    return score


def word_f1(gt: str, ocr: str) -> float:
    g, o = Counter(re.findall(r"\w+", fold(gt).lower())), Counter(re.findall(r"\w+", fold(ocr).lower()))
    if not g or not o:
        return 0.0
    tp = sum((g & o).values())
    p, r = tp / sum(o.values()), tp / sum(g.values())
    return 0.0 if tp == 0 else 2 * p * r / (p + r)


def cer(gt: str, ocr: str) -> float:
    g, o = fold(gt), fold(ocr)
    return lev(g, o) / max(1, len(g))


# ----------------------------- engines ------------------------------------ #
class Engine:
    name = ""
    native_modes: list = []        # modes whose behaviour on a rotated page is the question (engine's own handling)
    plain_mode = ""                # mode used after a front end has straightened the page

    def read(self, img, mode) -> str:
        raise NotImplementedError


class EasyOCR(Engine):
    name = "easyocr"
    native_modes = ["plain", "rotation_info"]
    plain_mode = "plain"

    def __init__(self):
        import easyocr
        self.rd = easyocr.Reader(["az"], gpu=True, verbose=False)

    def read(self, img, mode):
        kw = {"rotation_info": [90, 180, 270]} if mode == "rotation_info" else {}
        return " ".join(r[1] for r in self.rd.readtext(img, **kw))


class Paddle(Engine):
    native_modes = ["builtin_orientation", "plain"]
    plain_mode = "plain"

    def __init__(self, mobile: bool):
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        from paddleocr import PaddleOCR
        models = (dict(text_detection_model_name="PP-OCRv5_mobile_det", text_recognition_model_name="latin_PP-OCRv5_mobile_rec") if mobile else {})
        self.name = "paddle_mobile_v5" if mobile else "paddle_v6_medium"
        device = os.environ.get("OCR_DEVICE", "cpu")                                   # "gpu:0" with the GPU build of paddlepaddle
        common = dict(device=device, enable_mkldnn=os.environ.get("OCR_MKLDNN", "0") == "1", **models)
        if device != "cpu":
            self.name += "_gpu"
        self.engines = {"builtin_orientation": PaddleOCR(**common),                       # defaults: document orientation + unwarping + text-line orientation
                        "plain": PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False, **common)}

    def read(self, img, mode):
        r = self.engines[mode].predict(img)[0]
        return " ".join(r["rec_texts"])


class Tesseract(Engine):
    """Tesseract 5, Azerbaijani model 'aze', one OpenMP thread (typical server setting). Uses `tesseract` from PATH, or the conda-style install in $TESSERACT_ROOT (bin/tesseract, share/tessdata)."""
    name = "tesseract"
    native_modes = ["plain", "osd_fix", "tutorial_deskew_osd"]   # plain = psm 3; osd_fix = psm 0 (OSD) -> turn by the quarter turn it reports -> psm 3;
                                                                 # tutorial_deskew_osd = the whole popular recipe: minAreaRect deskew, then OSD, then psm 3
    plain_mode = "plain"
    ROOT = os.environ.get("TESSERACT_ROOT")

    def __init__(self):
        import shutil
        self.bin = os.path.join(self.ROOT, "bin", "tesseract") if self.ROOT else (shutil.which("tesseract") or "tesseract")
        self.env = dict(os.environ, OMP_THREAD_LIMIT="1")
        if self.ROOT:
            self.env["TESSDATA_PREFIX"] = os.path.join(self.ROOT, "share", "tessdata")

    def _run(self, img, args):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.png")
            cv2.imwrite(p, img)
            o = subprocess.run([self.bin, p, "stdout"] + args, capture_output=True, text=True, env=self.env)
            return o.stdout + o.stderr

    def read(self, img, mode):
        if mode == "tutorial_deskew_osd":
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from bench.simple_deskew_baseline import minarea_tutorial
            from docangle import rotate_image_expanded
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
            tilt = minarea_tutorial(g)                                    # the tutorial's skew estimate (what it believes the page tilt is, CCW)
            img = rotate_image_expanded(img, -float(tilt), border_val=255)  # deskew
            mode = "osd_fix"
        if mode == "osd_fix":
            m = re.search(r"Rotate: (\d+)", self._run(img, ["--psm", "0", "-l", "osd"]))
            rot = int(m.group(1)) if m else 0
            if rot:
                import sys
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from docangle import rotate_image_expanded
                img = rotate_image_expanded(img, -float(rot), border_val=255)       # "Rotate: N" = turn clockwise by N (checked on known rotations)
        return self._run(img, ["-l", "aze", "--psm", "3"])


def make_engine(name):
    return {"easyocr": EasyOCR, "paddle_mobile": lambda: Paddle(True), "paddle_v6": lambda: Paddle(False), "tesseract": Tesseract}[name]()


# ----------------------------- run ---------------------------------------- #
def pick_pages(n):
    pages = [p for p in json.load(open(GT)) if p["chars"] >= 600]
    by = {}
    for p in pages:
        by.setdefault(p["doc"], []).append(p)
    order = sorted(by)
    out, k = [], 0
    while len(out) < n:
        d = order[k % len(order)]
        lst = by[d]
        j = (k // len(order)) * max(1, len(lst) // 4) % len(lst)
        if lst[j] not in out:
            out.append(lst[j])
        k += 1
        if k > 10 * n + 50:
            break
    return out[:n]


def run(a):
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from docangle import DocumentOrientationPipeline, rotate_image_expanded
    pipe = DocumentOrientationPipeline()
    eng = make_engine(a.engine)
    done, rows = set(), []
    if os.path.exists(a.out):
        rows = json.load(open(a.out))
        done = {(r["png"], r["angle"], r["cond"]) for r in rows}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    pages = pick_pages(a.pages)
    print(f"{eng.name}: {len(pages)} pages x {len(a.angles)} angles", flush=True)

    def save():
        json.dump(rows, open(a.out, "w"), ensure_ascii=False)

    for pi, pg in enumerate(pages):
        page = cv2.imread(pg["png"])
        for ang in a.angles:
            rot = rotate_image_expanded(page, float(ang), border_val=255) if ang else page
            todo = []
            for m in eng.native_modes:
                todo.append((f"native:{m}", m, lambda m=m: (rot, None)))
            todo.append((f"ours:{eng.plain_mode}", eng.plain_mode, None))
            todo.append((f"oracle:{eng.plain_mode}", eng.plain_mode, None))
            for cond, mode, _ in todo:
                if (pg["png"], ang, cond) in done:
                    continue
                meta = {}
                if cond.startswith("native"):
                    img = rot
                elif cond.startswith("ours"):
                    t0 = time.perf_counter()
                    up, res = pipe.correct(rot)
                    meta = dict(front_end_ms=(time.perf_counter() - t0) * 1000.0, ours_angle=None if res.angle is None else res.angle, ours_review=res.needs_review)
                    img = up if up is not None else rot
                else:
                    img = rotate_image_expanded(rot, -float(ang), border_val=255) if ang else rot
                t0 = time.perf_counter()
                text = eng.read(img, mode)
                sec = time.perf_counter() - t0
                rows.append(dict(engine=eng.name, png=pg["png"], doc=pg["doc"], angle=ang, cond=cond, sec=sec, text=text, **meta))
            save()
        print(f"page {pi + 1}/{len(pages)} done ({pg['doc']})", flush=True)


# ----------------------------- analyze ------------------------------------ #
def analyze(a):
    gt = {p["png"]: p["text"] for p in json.load(open(GT))}
    rows = []
    for f in a.files:
        rows += json.load(open(f))
    for eng in sorted({r["engine"] for r in rows}):
        R = [r for r in rows if r["engine"] == eng]
        angles = sorted({r["angle"] for r in R})
        conds = sorted({r["cond"] for r in R})
        pages = sorted({r["png"] for r in R})
        print(f"\n=== {eng}: {len(pages)} pages x {len(angles)} angles; word-F1 % (mean over pages) | CER % | seconds per page ===")
        print(f"{'condition':28s} " + " ".join(f"{x:>6d}" for x in angles) + "   mean")
        for metric, fn, fmt in (("word F1", lambda r: word_f1(gt[r["png"]], r["text"]) * 100, "{:6.1f}"),
                                ("CER", lambda r: min(cer(gt[r["png"]], r["text"]), 3.0) * 100, "{:6.1f}")):
            print(f"-- {metric}")
            for c in conds:
                vals = []
                for ang in angles:
                    v = [fn(r) for r in R if r["cond"] == c and r["angle"] == ang]
                    vals.append(np.mean(v) if v else float("nan"))
                print(f"{c:28s} " + " ".join(fmt.format(v) for v in vals) + f"   {np.nanmean(vals):6.1f}")
        print("-- seconds per page (mean)")
        for c in conds:
            print(f"{c:28s} {np.mean([r['sec'] for r in R if r['cond'] == c]):6.2f} s")
        ours = [r for r in R if r["cond"].startswith("ours")]
        if ours:
            ok = sum(1 for r in ours if r.get("ours_angle") is not None and abs((r["ours_angle"] - r["angle"] + 180) % 360 - 180) <= 1.5)
            rev = sum(1 for r in ours if r.get("ours_review"))
            print(f"-- docangle front end in this test: angle within 1.5 deg on {ok}/{len(ours)} pages, sent to review {rev}, mean {np.mean([r['front_end_ms'] for r in ours]):.0f} ms per page")


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
    a = ap.parse_args()
    run(a) if a.cmd == "run" else analyze(a)


if __name__ == "__main__":
    main()
