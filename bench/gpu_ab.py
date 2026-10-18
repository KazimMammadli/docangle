"""docangle on CPU vs on the GPU (the three ONNX models via onnxruntime-gpu): speed, CPU use, GPU memory and whether the results change.

  LD_LIBRARY_PATH=<nvidia/*/lib dirs> python -m bench.gpu_ab --pages 120 --out reports/gpu_ab.txt      (python with onnxruntime-gpu installed)

Only the ONNX models move to the GPU (`PipelineConfig(ort_provider="cuda")`); the Fourier tilt, Hough, resizing and straightening stay on the CPU.
"""
from __future__ import annotations

import argparse
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from docangle import DocumentOrientationPipeline, PipelineConfig

from .profile_stages import canvases


def gpu_mem_mb():
    import os
    out = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        pid, mem = [x.strip() for x in line.split(",")]
        if int(pid) == os.getpid():
            return int(mem)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=120)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    imgs = canvases(a.pages)
    L = [f"{len(imgs)} simulated photo pages (original sizes ~{int(np.median([max(g.shape) for g in imgs]))} px long side), predict() on in-memory gray images"]
    pipes = {"CPU (default)": DocumentOrientationPipeline(PipelineConfig()), "GPU (ort_provider='cuda')": DocumentOrientationPipeline(PipelineConfig(ort_provider="cuda"))}
    for p in pipes.values():
        for g in imgs[:5]:
            p.predict(g)
    L.append(f"GPU memory held by this process after loading the models: {gpu_mem_mb()} MB")
    res, wall, cpu = {}, {}, {}
    for rep in range(2):                                              # interleaved single-thread pass, second pass counted
        for name, p in pipes.items():
            w, c, r = [], [], []
            for g in imgs:
                t0, c0 = time.perf_counter(), time.process_time()
                x = p.predict(g)
                w.append((time.perf_counter() - t0) * 1000); c.append((time.process_time() - c0) * 1000)
                r.append((x.angle, x.confidence, x.needs_review))
            if rep == 1:
                wall[name], cpu[name], res[name] = np.array(w), np.array(c), r
    L.append("\nSINGLE CALLER THREAD (ms per page)               median    mean     p95   process CPU ms/page")
    for name in pipes:
        L.append(f"  {name:28s} {np.median(wall[name]):10.1f} {wall[name].mean():8.1f} {np.percentile(wall[name], 95):7.1f} {np.median(cpu[name]):14.1f}")
    a0, a1 = res["CPU (default)"], res["GPU (ort_provider='cuda')"]
    d = np.array([0.0 if (x[0] is None and y[0] is None) else (180.0 if (x[0] is None or y[0] is None) else abs((x[0] - y[0] + 180) % 360 - 180)) for x, y in zip(a0, a1)])
    L.append(f"\nRESULTS CPU vs GPU on {len(d)} pages: identical angle (to 0.01 deg) {int((d <= 0.01).sum())}, differ > 0.05 deg: {int((d > 0.05).sum())}, > 0.5 deg: {int((d > 0.5).sum())}, "
             f"> 45 deg (quadrant): {int((d > 45).sum())}; review flag differs {sum(x[2] != y[2] for x, y in zip(a0, a1))}; max |dconf| {max(abs(x[1] - y[1]) for x, y in zip(a0, a1)):.4f}")
    L.append("\nTHROUGHPUT (pages/s, all pages x2, caller threads)  and CPU cost")
    for w in (1, 4):
        for name, p in pipes.items():
            work = imgs * 2
            t0, c0 = time.perf_counter(), time.process_time()
            if w == 1:
                for g in work:
                    p.predict(g)
            else:
                with ThreadPoolExecutor(max_workers=w) as ex:
                    list(ex.map(p.predict, work))
            dt, dc = time.perf_counter() - t0, time.process_time() - c0
            L.append(f"  {w} thread(s) {name:28s} {len(work) / dt:6.1f} pages/s   CPU {dc / len(work) * 1000:6.1f} ms/page")
    print("\n".join(L))
    if a.out:
        open(a.out, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
