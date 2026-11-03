"""Can an OCR engine settle the pages docangle flags `needs_review`? (the idea: turn the page the 4 ways, read each, keep the one that reads best)

  python -m bench.ocr_judge_eval collect --out DIR          # docangle on the main-benchmark cases; keeps every flagged page and a random control sample
  python -m bench.ocr_judge_eval judge   --out DIR --tesseract /path/to/tesseract   # Tesseract (or `--engine paddle --paddle-model mobile --device gpu:0`) reads each kept page in the 4 quadrants
  python -m bench.ocr_judge_eval analyze --out DIR          # how often the reading picks the true quadrant, against docangle's own answer

Cases are the ones of `bench.run` (same pools, levels, seeds, n and `uniform` angles). The four candidate pages of a case are the
input turned by tilt + k * 90 degrees, k = 0..3, where tilt is docangle's fine tilt (its angle modulo 90), so the judge decides the quadrant only.
Judges (scores of one reading; higher is better): n_good = words of 3+ letters read with confidence >= 70, sum_conf = sum of word confidences,
mean_conf = mean word confidence, n_words = number of words. Tesseract language: eng for every pool, page segmentation mode 4 (mode 3 turns 90-degree pages on its own).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

from docangle import upright

from . import run as bench_run
from .candidates import REGISTRY
from .degrade import LEVELS, render, sample_angle
from .metrics import circ_err, wilson

POOLS = ["az", "invoices", "tobacco_cert", "rvl_heldout", "ext_funsd", "ext_doclaynet", "ext_cord"]
LEVEL_NAMES = ["scan", "photo_easy", "photo_hard"]
JUDGES = ("n_good", "sum_conf", "mean_conf", "n_words")


def _tilt(pred: float) -> float:
    return (pred + 45.0) % 90.0 - 45.0


def _cand_angles(pred: float):
    t = _tilt(pred)
    return [float((t + 90.0 * k + 180.0) % 360.0 - 180.0) for k in range(4)]


def _truth_k(pred: float, gt: float) -> int:
    return int(np.argmin([circ_err(a, gt) for a in _cand_angles(pred)]))


# ------------------------------ collect ----------------------------------- #
def collect(a):
    os.makedirs(os.path.join(a.out, "img"), exist_ok=True)
    fn, _ = REGISTRY["docangle"]()
    rng_ctl = np.random.default_rng(777)
    rows = []
    for ds in a.datasets:
        for lv in a.levels:
            cases, _, _ = bench_run.make_cases(ds, lv, "uniform", a.seeds, a.n)
            kept = flagged = 0
            for f, s, i, rng in cases:
                page = cv2.imread(f)
                gt = sample_angle("uniform", rng)
                img = render(page, gt, LEVELS[lv], rng)
                r = fn(img)
                ctl = (not r["review"]) and rng_ctl.random() < a.control_rate
                if r["review"] or ctl:
                    cid = f"{ds}__{lv}__{s}_{i}"
                    cv2.imwrite(os.path.join(a.out, "img", cid + ".png"), img)
                    rows.append(dict(id=cid, ds=ds, lv=lv, file=os.path.basename(f), gt=gt, pred=r["pred"], conf=r["conf"], review=bool(r["review"])))
                    kept += 1
                    flagged += bool(r["review"])
            print(f"{ds}/{lv}: {len(cases)} cases, flagged {flagged}, control kept {kept - flagged}", flush=True)
            json.dump(rows, open(os.path.join(a.out, "cases.json"), "w"))
    print("kept", len(rows), "flagged", sum(r["review"] for r in rows))


# ------------------------------- judge ------------------------------------ #
def _read(tess, png, lang, psm):
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    t0 = time.perf_counter()
    out = subprocess.run([tess, png, "stdout", "-l", lang, "--psm", str(psm), "tsv"], capture_output=True, text=True, env=env, timeout=300).stdout
    sec = time.perf_counter() - t0
    words = []
    for row in csv.DictReader(io.StringIO(out), delimiter="\t", quoting=csv.QUOTE_NONE):
        try:
            conf, text = float(row["conf"]), (row["text"] or "").strip()
        except (KeyError, ValueError):
            continue
        if conf >= 0 and text:
            words.append((conf, text))
    confs = [c for c, _ in words]
    good = [c for c, t in words if c >= 70 and sum(ch.isalpha() for ch in t) >= 3]
    return dict(n_words=len(words), n_good=len(good), sum_conf=float(sum(confs)), mean_conf=float(np.mean(confs)) if confs else 0.0, sec=sec)


def _paddle_reader(model, device):
    """PaddleOCR (run this step in the interpreter that has it); the same four scores as Tesseract's, lines instead of words."""
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    from paddleocr import PaddleOCR
    names = dict(text_detection_model_name="PP-OCRv5_mobile_det", text_recognition_model_name="latin_PP-OCRv5_mobile_rec") if model == "mobile" else {}
    ocr = PaddleOCR(device=device, use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False, **names)

    def read(png):
        t0 = time.perf_counter()
        r = ocr.predict(png)[0]
        sec = time.perf_counter() - t0
        lines = [(float(c) * 100.0, t) for t, c in zip(r["rec_texts"], r["rec_scores"]) if t.strip()]
        confs = [c for c, _ in lines]
        good = [c for c, t in lines if c >= 70 and sum(ch.isalpha() for ch in t) >= 3]
        return dict(n_words=len(lines), n_good=len(good), sum_conf=float(sum(confs)), mean_conf=float(np.mean(confs)) if confs else 0.0, sec=sec)
    return read


def _judge_case(a, row, tmp, reader):
    img = cv2.imread(os.path.join(a.out, "img", row["id"] + ".png"))
    scores = []
    for k, ang in enumerate(_cand_angles(row["pred"])):
        page = upright(img, ang)
        h, w = page.shape[:2]
        sc = a.target_side / max(h, w)          # small pages (receipts) are enlarged: Tesseract wants letters of about 20 px
        page = cv2.resize(page, (int(w * sc), int(h * sc)), interpolation=cv2.INTER_CUBIC if sc > 1 else cv2.INTER_AREA)
        path = os.path.join(tmp, f"{row['id']}_{k}.png")
        cv2.imwrite(path, page)
        scores.append(reader(path))
        os.remove(path)
    return row["id"], scores


def judge(a):
    rows = json.load(open(os.path.join(a.out, "cases.json")))
    path = os.path.join(a.out, "judge.json")
    done = json.load(open(path)) if os.path.exists(path) else {}
    todo = [r for r in rows if r["id"] not in done]
    print(f"{len(done)} done, {len(todo)} to read ({a.workers} Tesseract workers)", flush=True)
    t0 = time.time()
    reader = _paddle_reader(a.paddle_model, a.device) if a.engine == "paddle" else (lambda png: _read(a.tesseract, png, a.lang, a.psm))
    with tempfile.TemporaryDirectory(dir=a.out) as tmp, ThreadPoolExecutor(1 if a.engine == "paddle" else a.workers) as ex:
        for n, (cid, scores) in enumerate(ex.map(lambda r: _judge_case(a, r, tmp, reader), todo), 1):
            done[cid] = scores
            if n % 10 == 0 or n == len(todo):
                json.dump(done, open(path, "w"))
                el = time.time() - t0
                print(f"  {n}/{len(todo)} pages, {el / 60:.1f} min, eta {el / n * (len(todo) - n) / 60:.1f} min", flush=True)


# ------------------------------ analyze ----------------------------------- #
def _fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.1f} % [{lo:.1f}, {hi:.1f}]" if n else "n/a"


def _pick(scores, judge):
    v = np.array([s[judge] for s in scores], dtype=float)
    order = np.argsort(-v)
    best = int(order[0]) if v[order[0]] > v[order[1]] else -1        # a tie (nothing read) settles nothing
    return best, float(v[order[0]] / (v[order[1]] + 1.0))


def analyze(a):
    rows = json.load(open(os.path.join(a.out, "cases.json")))
    sc = json.load(open(a.judge or os.path.join(a.out, "judge.json")))
    rows = [r for r in rows if r["id"] in sc]
    for r in rows:
        r["ktrue"] = _truth_k(r["pred"], r["gt"])
        r["kdoc"] = int(np.argmin([circ_err(x, r["pred"]) for x in _cand_angles(r["pred"])]))
    flagged, control = [r for r in rows if r["review"]], [r for r in rows if not r["review"]]
    out = [f"pages read: {len(rows)} (flagged {len(flagged)}, control {len(control)}); seconds of reading per page (4 readings): median "
           f"{np.median([sum(s['sec'] for s in sc[r['id']]) for r in rows]):.1f}"]
    out.append(f"\nflagged pages where docangle's quadrant is wrong: {_fmt(sum(r['kdoc'] != r['ktrue'] for r in flagged), len(flagged))}")
    out.append(f"control pages (not flagged) where docangle's quadrant is wrong: {_fmt(sum(r['kdoc'] != r['ktrue'] for r in control), len(control))}")
    out.append("\n## Judge picks the best of the 4 readings, flagged pages (accuracy of the quadrant)\n")
    out.append("| judge | judge right on flagged | judge right on control (the pages docangle accepted) | docangle right on flagged |")
    out.append("|---|---|---|---|")
    for j in JUDGES:
        fr = sum(_pick(sc[r["id"]], j)[0] == r["ktrue"] for r in flagged)
        cr = sum(_pick(sc[r["id"]], j)[0] == r["ktrue"] for r in control)
        out.append(f"| {j} | {_fmt(fr, len(flagged))} | {_fmt(cr, len(control))} | {_fmt(sum(r['kdoc'] == r['ktrue'] for r in flagged), len(flagged))} |")
    out.append("\n## Only trust the judge when its best reading beats the second best by a ratio (flagged pages)\n")
    out.append("| judge | ratio | pages settled | right among the settled | wrong among the settled | still for a person |")
    out.append("|---|---|---|---|---|---|")
    for j in ("n_good", "sum_conf"):
        for ratio in (1.0, 1.5, 2.0, 3.0, 5.0):
            picks = [(_pick(sc[r["id"]], j), r) for r in flagged]
            ok = [(p, r) for p, r in picks if p[1] >= ratio]
            right = sum(p[0] == r["ktrue"] for p, r in ok)
            out.append(f"| {j} | {ratio} | {len(ok)}/{len(flagged)} | {_fmt(right, len(ok))} | {len(ok) - right} | {len(flagged) - len(ok)} |")
    wrong = [r for r in flagged if r["kdoc"] != r["ktrue"]]
    half = sum((r["ktrue"] - r["kdoc"]) % 4 == 2 for r in wrong)
    out.append(f"\ndocangle's wrong flagged pages: {len(wrong)}; the true quadrant is a half turn (180 deg) from its answer on {half}, a quarter turn on {len(wrong) - half}")
    nothing = sum(sc[r["id"]][r["ktrue"]]["n_good"] == 0 for r in flagged)
    out.append(f"flagged pages where the CORRECTLY turned page has no confident word for this engine: {_fmt(nothing, len(flagged))}")
    out.append("\n## Settling rule `n_good` ratio >= 1.5: all 4 readings, or only 2 (docangle's answer and its half turn)\n")
    out.append("| readings | settled | wrong among the settled | still for a person | median seconds of reading per page |")
    out.append("|---|---|---|---|---|")
    for ways in (4, 2):
        settled = bad = 0
        secs = []
        for r in flagged:
            ks = range(4) if ways == 4 else (r["kdoc"], (r["kdoc"] + 2) % 4)
            v = np.array([sc[r["id"]][k]["n_good"] for k in ks], dtype=float)
            o = np.argsort(-v)
            secs.append(sum(sc[r["id"]][k]["sec"] for k in ks))
            if v[o[0]] > v[o[1]] and v[o[0]] / (v[o[1]] + 1.0) >= 1.5:
                settled += 1
                bad += list(ks)[int(o[0])] != r["ktrue"]
        out.append(f"| {ways} | {settled}/{len(flagged)} | {bad} | {len(flagged) - settled} | {np.median(secs):.1f} |")
    out.append("\n## By pool (flagged pages; judge n_good)\n")
    out.append("| pool | flagged | docangle right | judge right |")
    out.append("|---|---|---|---|")
    for ds in POOLS:
        f = [r for r in flagged if r["ds"] == ds]
        if f:
            out.append(f"| {ds} | {len(f)} | {sum(r['kdoc'] == r['ktrue'] for r in f)} | {sum(_pick(sc[r['id']], 'n_good')[0] == r['ktrue'] for r in f)} |")
    text = "\n".join(out)
    print(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["collect", "judge", "analyze"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--datasets", nargs="+", default=POOLS)
    ap.add_argument("--levels", nargs="+", default=LEVEL_NAMES)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--control-rate", type=float, default=0.016, help="share of the unflagged cases kept as a control sample")
    ap.add_argument("--judge", help="analyze: a judge.json other than OUT/judge.json (the readings of one engine)")
    ap.add_argument("--engine", choices=["tesseract", "paddle"], default="tesseract")
    ap.add_argument("--paddle-model", choices=["mobile", "medium"], default="mobile")
    ap.add_argument("--device", default="cpu", help="PaddleOCR device, e.g. gpu:0")
    ap.add_argument("--tesseract", default="tesseract")
    ap.add_argument("--lang", default="eng")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--target-side", type=int, default=2000, help="longest side of a page given to Tesseract (pages are scaled to it)")
    ap.add_argument("--psm", type=int, default=4, help="Tesseract page segmentation mode; 3 turns 90-degree pages itself, so it cannot judge the quadrant")
    a = ap.parse_args()
    {"collect": collect, "judge": judge, "analyze": analyze}[a.step](a)


if __name__ == "__main__":
    main()
