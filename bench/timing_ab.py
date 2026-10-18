"""Latency / throughput A-B of registry candidates on an IDLE machine.

  python -m bench.timing_ab --candidates docangle docangle_noreg2 ... --pages 300 --reps 3 [--workers 4]

Pages are sampled from the benchmark pools, resized to the 1000-px working canvas and kept in memory (decode time is excluded: only analyze()).
Candidates are interleaved in rotating order on every page so that load drift hits all of them equally. Reports mean / median / p95 ms per page
(one caller thread) and, with --workers, pages per second of `predict_batch`-style threading. Run nothing else at the same time.
"""
from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline

from . import datasets
from .candidates import REGISTRY


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", nargs="+", required=True)
    ap.add_argument("--pages", type=int, default=300)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    files = []
    for pool in ("az", "invoices", "rvl_heldout", "tobacco_cert", "ext_doclaynet", "ext_cord"):
        files += datasets.pick(datasets.pool(pool), max(1, a.pages // 6), 0)[0]
    imgs = []
    for f in files[:a.pages]:
        g = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
        if g is None:
            continue
        k = 1000.0 / max(g.shape)
        imgs.append(cv2.resize(g, None, fx=k, fy=k, interpolation=cv2.INTER_AREA) if k < 1 else g)
    pipes = {n: DocumentOrientationPipeline(REGISTRY[n]()[1]) for n in a.candidates}
    for p in pipes.values():                                   # warm: create all sessions
        for g in imgs[:5]:
            p.predict(g)
    ms = {n: [] for n in pipes}
    names = list(pipes)
    for rep in range(a.reps):
        for i, g in enumerate(imgs):
            order = names[(i + rep) % len(names):] + names[:(i + rep) % len(names)]
            for n in order:
                t0 = time.perf_counter(); pipes[n].predict(g); ms[n].append((time.perf_counter() - t0) * 1000.0)
    lines = [f"{len(imgs)} pages x {a.reps} reps, 1000-px gray canvases, single caller thread, analyze() only"]
    for n in names:
        x = np.array(ms[n])
        lines.append(f"{n:24s} mean {x.mean():6.2f} ms  median {np.median(x):6.2f}  p95 {np.percentile(x, 95):6.2f}")
    if a.workers > 1:
        for n in names:
            t0 = time.perf_counter()
            with ThreadPoolExecutor(max_workers=a.workers) as ex:
                list(ex.map(pipes[n].predict, imgs * 2))
            dt = time.perf_counter() - t0
            lines.append(f"{n:24s} throughput with {a.workers} workers: {2 * len(imgs) / dt:5.1f} pages/s")
    print("\n".join(lines))
    if a.out:
        open(a.out, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
