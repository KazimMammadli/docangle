"""Per-case decision features for review-policy work (experiment E2).

  python -m bench.features --datasets az invoices ... --levels scan photo_hard --seeds 3 --n 100 --out /tmp/feat.json

Runs the default pipeline on the benchmark's simulated cases (same cases as bench.run) and stores, per case, what the review decision
could be based on: the log-posteriors of the two quadrant voters, the Hough line count, the Hough/Fourier tilt gap, fallback flag,
the pipeline's own confidence / review flag, and the truth (angle error). `page` identifies the source page: cases of one page are
rotations of the same document and must stay in one fold when a policy is fitted (`bench.calibrate`).
"""
from __future__ import annotations

import argparse
import json

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline, PipelineConfig

from .degrade import LEVELS, render, sample_angle
from .metrics import circ_err
from .run import make_cases


class Probe:
    """Wraps one pipeline and records the voter outputs of the last predict() call (call it from one thread at a time)."""

    def __init__(self, cfg: PipelineConfig):
        self.pipe = DocumentOrientationPipeline(cfg)
        self.rec = {}
        p = self.pipe
        lc, hs = p._lcnet_logpost, p._hough_slope

        def lcnet(gray):
            out = lc(gray)
            self.rec["lcnet"] = np.asarray(out, float).tolist()
            return out

        def hough(gray, method=None, max_dim=None, strips=1):
            out = hs(gray, method, max_dim, strips)
            if method is None:
                self.rec["h_slope"], self.rec["lines"] = float(out[0]), int(out[1])
            return out
        p._lcnet_logpost, p._hough_slope = lcnet, hough
        reg = p._regressor.predict

        def regressor(gray):
            out = reg(gray)
            self.rec["reg_angle"] = float(out)
            return out
        p._regressor.predict = regressor
        if p._fft is not None:
            fx = p._fft.tilt_ex

            def tilt(gray):
                t, sharp = fx(gray)
                self.rec["fft_sharp"] = sharp
                return t
            p._fft.tilt = tilt
        if p._orient is not None:
            lp = p._orient.log_posterior

            def orient(gray, rots=(0, 1, 2, 3), temperature=1.0):
                out = lp(gray, rots, temperature)
                self.rec["orient"] = np.asarray(out, float).tolist()
                return out
            p._orient.log_posterior = orient

    def run(self, img):
        self.rec = {}
        r = self.pipe.predict(img)
        return r, dict(self.rec)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", required=True)
    ap.add_argument("--levels", nargs="+", default=["scan", "photo_easy", "photo_hard"])
    ap.add_argument("--angle-mode", default="uniform")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    probe = Probe(PipelineConfig())
    rows = []
    for ds in a.datasets:
        for lv in a.levels:
            cases, _, _ = make_cases(ds, lv, a.angle_mode, a.seeds, a.n)
            for f, s, i, rng in cases:
                page = cv2.imread(f)
                gt = sample_angle(a.angle_mode, rng)
                img = render(page, gt, LEVELS[lv], rng)
                r, rec = probe.run(img)
                h_gap = None
                if r.fine_tilt is not None and "h_slope" in rec:
                    h_gap = abs((rec["h_slope"] + r.fine_tilt + 45.0) % 90.0 - 45.0)    # slope = -fine tilt for the Fourier estimate
                rows.append(dict(ds=ds, lv=lv, page=f"{ds}/{f.split('/')[-1]}", gt=gt, angle=r.angle, conf=r.confidence,
                                 review=r.needs_review, reasons=r.reasons, fallback=r.fallback_triggered, score=r.lcnet_score, fine_tilt=r.fine_tilt,
                                 err=(180.0 if r.angle is None else circ_err(r.angle, gt)), h_gap=h_gap, **rec))
            print("features", ds, lv, flush=True)
    json.dump(rows, open(a.out, "w"))
    print("wrote", a.out, len(rows))


if __name__ == "__main__":
    main()
