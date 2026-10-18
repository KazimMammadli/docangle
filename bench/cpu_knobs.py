"""A/B of CPU-usage knobs (ONNX Runtime spinning, ORT threads, OpenCV threads), each variant in a fresh process.

  python -m bench.cpu_knobs --pages 100 --out reports/cpu_knobs.txt

Per variant: wall and CPU ms per page with one caller thread, pages/s with 4 caller threads, and whether every angle / confidence is
IDENTICAL to the default variant (these knobs change scheduling, they must not change results).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

VARIANTS = {
    "default": {},
    "ORT no spinning": {"spin": "0"},
    "OpenCV 1 thread": {"cv": 1},
    "ORT no spinning + OpenCV 1 thread": {"spin": "0", "cv": 1},
    "no spinning + OpenCV 1 + ORT 1 thread/session": {"spin": "0", "cv": 1, "ort": 1},
}


def child(spec, pages, out):
    import cv2
    if "cv" in spec:
        cv2.setNumThreads(spec["cv"])
    import onnxruntime as ort
    import docangle.orientation as O
    import docangle.pipeline as P
    import docangle.regressor as R

    def make_session(path, threads=2):
        so = ort.SessionOptions()
        so.intra_op_num_threads = spec.get("ort", threads)
        so.inter_op_num_threads = 1
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        if "spin" in spec:
            so.add_session_config_entry("session.intra_op.allow_spinning", spec["spin"])
            so.add_session_config_entry("session.inter_op.allow_spinning", spec["spin"])
        return ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])
    if spec:
        R.make_session = O.make_session = P.make_session = make_session
    from concurrent.futures import ThreadPoolExecutor
    from bench.profile_stages import canvases
    imgs = canvases(pages)
    pipe = P.DocumentOrientationPipeline(P.PipelineConfig())
    for g in imgs[:3]:
        pipe.predict(g)
    res, wall, cpu = [], [], []
    for g in imgs:
        t0, c0 = time.perf_counter(), time.process_time()
        r = pipe.predict(g)
        wall.append((time.perf_counter() - t0) * 1000); cpu.append((time.process_time() - c0) * 1000)
        res.append([r.angle, r.confidence, r.needs_review])
    work = imgs * 2
    t0, c0 = time.perf_counter(), time.process_time()
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(pipe.predict, work))
    dt, dc = time.perf_counter() - t0, time.process_time() - c0
    import numpy as np
    json.dump(dict(wall=float(np.median(wall)), wall_mean=float(np.mean(wall)), cpu=float(np.median(cpu)), pps4=len(work) / dt,
                   cpu4=dc / len(work) * 1000, cores4=dc / dt, res=res), open(out, "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=100)
    ap.add_argument("--out", default=None)
    ap.add_argument("--child", default=None)
    ap.add_argument("--spec", default="{}")
    ap.add_argument("--res", default=None)
    a = ap.parse_args()
    if a.child:
        child(json.loads(a.spec), a.pages, a.res)
        return
    import tempfile, os
    tmp = tempfile.mkdtemp()
    got = {}
    for name, spec in VARIANTS.items():
        path = os.path.join(tmp, "r.json")
        subprocess.run([sys.executable, "-m", "bench.cpu_knobs", "--child", "1", "--spec", json.dumps(spec), "--pages", str(a.pages), "--res", path], check=True)
        got[name] = json.load(open(path))
        print(name, "done", flush=True)
    base = got["default"]["res"]
    L = [f"{a.pages} simulated photo pages; single caller thread: median wall / CPU ms per page; 4 caller threads: pages/s, CPU ms per page, cores busy",
         f"{'variant':48s} {'wall':>6s} {'CPU':>7s} | {'4 thr p/s':>9s} {'CPU/page':>8s} {'cores':>5s} | identical results"]
    for name, g in got.items():
        same = sum(x == y for x, y in zip(g["res"], base))
        L.append(f"{name:48s} {g['wall']:6.1f} {g['cpu']:7.1f} | {g['pps4']:9.1f} {g['cpu4']:8.1f} {g['cores4']:5.1f} | {same}/{len(base)}")
    print("\n".join(L))
    if a.out:
        open(a.out, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
