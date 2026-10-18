"""Where does the time go? Stage profile of docangle on ~120 page canvases, thread scaling, and start-up cost.

  python -m bench.profile_stages --pages 120 --out reports/profile_stages.txt

Stages are timed by wrapping the pipeline's internal methods (the wrappers add ~microseconds). Single caller thread for the stage table;
then pages/s with 1, 2, 4, 6, 8 caller threads; then the cost of importing docangle and of creating each ONNX session (fresh subprocesses).
Run it on an idle machine; nothing else should run at the same time.
"""
from __future__ import annotations

import argparse
import collections
import gc
import os
import resource
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline, PipelineConfig
import docangle.pipeline as P

from .degrade import LEVELS, render, sample_angle
from .run import make_cases


def canvases(n):
    imgs = []
    per = max(1, n // 6)
    for pool in ("az", "invoices", "rvl_heldout", "tobacco_cert", "ext_doclaynet", "ext_cord"):
        cases, _, _ = make_cases(pool, "photo_easy", "uniform", 1, per)
        for f, s, i, rng in cases:
            page = cv2.imread(f)
            img = render(page, sample_angle("uniform", rng), LEVELS["photo_easy"], rng)
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
            imgs.append(g)
    return imgs[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=120)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    L = []

    def emit(s=""):
        print(s, flush=True); L.append(s)

    imgs = canvases(a.pages)
    emit(f"{len(imgs)} simulated photo pages (photo_easy, 6 pools), original sizes median {int(np.median([max(g.shape) for g in imgs]))} px long side")
    pipe = DocumentOrientationPipeline(PipelineConfig())
    for g in imgs[:5]:
        pipe.predict(g)
    T = collections.defaultdict(list)
    lock = threading.Lock()

    def wrap(obj, name, label):
        f = getattr(obj, name)

        def w(*args, **kw):
            t0 = time.perf_counter(); out = f(*args, **kw); dt = (time.perf_counter() - t0) * 1000
            with lock:
                T[label].append(dt)
            return out
        setattr(obj, name, w)
    wrap(pipe._fft, "tilt", "fourier tilt (512 px)")
    wrap(pipe, "_hough_slope", "hough line count (thread)")
    wrap(pipe, "_lcnet_view_set", "pp-lcnet views (resize+rot)")
    wrap(pipe, "_lcnet_blob", "pp-lcnet blob (LUT)")
    sess = pipe._lcnet_session()
    run0 = sess.run

    class S:                                   # wrap the ORT session.run of PP-LCNet
        def __getattr__(self, k):
            return getattr(sess, k)

        def run(self, *x, **k):
            t0 = time.perf_counter(); o = run0(*x, **k); dt = (time.perf_counter() - t0) * 1000
            with lock:
                T["pp-lcnet onnx run (4 views)"].append(dt)
            return o
    pipe._lcnet = S()
    wrap(pipe._orient, "views", "own views (resize 320+rot+norm)")
    wrap(pipe._orient, "logits", "own onnx run (2 views)")
    wrap(pipe, "_coarse", "classifiers total (_coarse)")
    rot0 = P.rotate_image_expanded

    def rot(*x, **k):
        t0 = time.perf_counter(); o = rot0(*x, **k); dt = (time.perf_counter() - t0) * 1000
        with lock:
            T["straighten (rotate_image_expanded)"].append(dt)
        return o
    P.rotate_image_expanded = rot
    tot, cpu = [], []
    for g in imgs:
        t0, c0 = time.perf_counter(), time.process_time()
        pipe.analyze(g)
        tot.append((time.perf_counter() - t0) * 1000); cpu.append((time.process_time() - c0) * 1000)
    P.rotate_image_expanded = rot0
    emit("\nSTAGES (single caller thread; ms per page; median / mean / p95). The two classifiers run concurrently inside _coarse; Hough runs in a thread.")
    for k in ["fourier tilt (512 px)", "straighten (rotate_image_expanded)", "pp-lcnet views (resize+rot)", "pp-lcnet blob (LUT)", "pp-lcnet onnx run (4 views)",
              "own views (resize 320+rot+norm)", "own onnx run (2 views)", "classifiers total (_coarse)", "hough line count (thread)"]:
        x = np.array(T[k])
        if len(x):
            emit(f"  {k:38s} {np.median(x):6.2f} {x.mean():6.2f} {np.percentile(x, 95):6.2f}   (n={len(x)})")
    tot, cpu = np.array(tot), np.array(cpu)
    emit(f"  {'analyze() wall total':38s} {np.median(tot):6.2f} {tot.mean():6.2f} {np.percentile(tot, 95):6.2f}")
    emit(f"  {'analyze() process CPU time (all threads)':38s} {np.median(cpu):6.2f} {cpu.mean():6.2f} {np.percentile(cpu, 95):6.2f}")
    big = [g for g in imgs if max(g.shape) > 1000]
    t0 = time.perf_counter()
    for g in big:
        m = max(g.shape); cv2.resize(g, (int(g.shape[1] * 1000 / m), int(g.shape[0] * 1000 / m)), interpolation=cv2.INTER_AREA)
    emit(f"  {'resize to 1000 px canvas (INTER_AREA)':38s} {(time.perf_counter() - t0) * 1000 / max(1, len(big)):6.2f} mean over {len(big)} larger pages")

    emit("\nTHREAD SCALING (fresh pipeline, predict on in-memory gray pages, 2 passes over all pages):")
    base = None
    del pipe
    gc.collect()
    for w in (1, 2, 4, 6, 8):
        p2 = DocumentOrientationPipeline(PipelineConfig())
        for g in imgs[:3]:
            p2.predict(g)
        work = imgs * 2
        t0, c0 = time.perf_counter(), time.process_time()
        if w == 1:
            for g in work:
                p2.predict(g)
        else:
            with ThreadPoolExecutor(max_workers=w) as ex:
                list(ex.map(p2.predict, work))
        dt, dc = time.perf_counter() - t0, time.process_time() - c0
        pps = len(work) / dt
        base = base or pps
        emit(f"  {w} caller threads: {pps:6.1f} pages/s  (x{pps / base:4.2f})  CPU {dc / len(work) * 1000:6.1f} ms per page, machine cores used ~{dc / dt:4.1f}"
             f"  [peak RSS so far {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024} MB]")
        del p2
        gc.collect()

    emit("\nSTART-UP (fresh python processes, median of 3; the page is the first simulated page of the list above, written as a PNG):")
    tmp = tempfile.TemporaryDirectory()
    page_path = os.path.join(tmp.name, "page.png")
    cv2.imwrite(page_path, imgs[0])
    code = {
        "python + import docangle": "import time;t=time.perf_counter();import docangle;print((time.perf_counter()-t)*1000)",
        "pipeline object (no sessions yet)": "import docangle,time;t=time.perf_counter();p=docangle.DocumentOrientationPipeline();print((time.perf_counter()-t)*1000)",
        "first predict (creates 2-3 sessions) on a page": f"import docangle,time,numpy as np,cv2;g=cv2.imread({page_path!r},0);p=docangle.DocumentOrientationPipeline();t=time.perf_counter();p.predict(g);a=(time.perf_counter()-t)*1000;t=time.perf_counter();p.predict(g);print(a, (time.perf_counter()-t)*1000)",
    }
    for k, c in code.items():
        vals = []
        for _ in range(3):
            out = subprocess.run([sys.executable, "-c", c], capture_output=True, text=True).stdout.split()
            vals.append([float(x) for x in out])
        v = np.median(np.array(vals), axis=0)
        emit(f"  {k:48s} " + " | ".join(f"{x:7.1f} ms" for x in np.atleast_1d(v)) + ("   (first | second predict)" if len(np.atleast_1d(v)) == 2 else ""))
    t0 = time.perf_counter(); subprocess.run([sys.executable, "-m", "docangle", page_path], capture_output=True)
    emit(f"  {'CLI one image, wall (python -m docangle page.png)':48s} {(time.perf_counter() - t0) * 1000:7.1f} ms")
    for name, fn in (("PP-LCNet", "pp_lcnet_doc_ori.onnx"), ("own classifier v4", "orient_cls_v4.onnx"), ("regressor", "document_angle_detector_large.onnx")):
        c = f"import time;from docangle.regressor import make_session;t=time.perf_counter();make_session('models/{fn}',2);print((time.perf_counter()-t)*1000)"
        v = sorted(float(subprocess.run([sys.executable, "-c", c], capture_output=True, text=True).stdout) for _ in range(3))[1]
        emit(f"  {'ONNX session creation: ' + name:48s} {v:7.1f} ms")
    if a.out:
        open(a.out, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
