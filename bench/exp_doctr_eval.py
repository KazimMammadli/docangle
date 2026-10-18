"""E3b data: the benchmark's simulated cases with the two production voters AND docTR recorded per case (see exp_doctr.py).

  python -m bench.exp_doctr_eval --datasets az invoices ... --seeds 3 --n 100 --out /tmp/e3/feat_doctr.json [--voter duarte]

`--voter duarte` records bench/exp_duarte.py (EfficientNetV2 orientation model) under the key "duarte" instead of docTR under "doctr".
"""
from __future__ import annotations

import argparse
import json
import time

import cv2
import numpy as np

from docangle import PipelineConfig

from .degrade import LEVELS, render, sample_angle
from .exp_doctr import DocTR
from .exp_duarte import Duarte
from .features import Probe
from .metrics import circ_err
from .run import make_cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", required=True)
    ap.add_argument("--levels", nargs="+", default=["scan", "photo_easy", "photo_hard"])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voter", choices=["doctr", "duarte"], default="doctr")
    a = ap.parse_args()
    probe, doctr = Probe(PipelineConfig()), (DocTR() if a.voter == "doctr" else Duarte())
    doctr.perm = np.array([0, 3, 2, 1])          # measured for both models (calibrate_mapping)
    pipe = probe.pipe
    lc_wrapped = pipe._lcnet_logpost
    seen = {}

    def spy(gray):                       # the straightened page that the voters see
        seen["g"] = gray
        return lc_wrapped(gray)
    pipe._lcnet_logpost = spy
    rows = []
    for ds in a.datasets:
        for lv in a.levels:
            cases, _, _ = make_cases(ds, lv, "uniform", a.seeds, a.n)
            for f, s, i, rng in cases:
                page = cv2.imread(f)
                gt = sample_angle("uniform", rng)
                img = render(page, gt, LEVELS[lv], rng)
                seen.clear()
                r, rec = probe.run(img)
                dt = None
                if "g" in seen:
                    t0 = time.perf_counter()
                    rec[a.voter] = doctr.log_posterior(seen["g"]).tolist()
                    dt = (time.perf_counter() - t0) * 1000.0
                rows.append(dict(ds=ds, lv=lv, page=f"{ds}/{f.split('/')[-1]}", gt=gt, angle=r.angle, conf=r.confidence,
                                 review=r.needs_review, fallback=r.fallback_triggered, score=r.lcnet_score,
                                 err=(180.0 if r.angle is None else circ_err(r.angle, gt)), **{f"{a.voter}_ms": dt}, **rec))
            print("done", ds, lv, flush=True)
    json.dump(rows, open(a.out, "w"))
    print("wrote", a.out, len(rows))


if __name__ == "__main__":
    main()
