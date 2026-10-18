"""Per-VIEW dump for component ablations (redundancy analysis, "Stage 0"): one pass over the benchmark's simulated cases that records
everything needed to emulate OFFLINE any variant of the voters, the fallback and the review gate (`bench.views_emulate`).

  python -m bench.views_dump --datasets az invoices ... --seeds 3 --n 100 [--seed-start 3] --out /tmp/views.json

For every case the default front end is replayed (decode -> gray canvas -> Fourier tilt -> straighten) and then, on the straightened page:
  lc_probs   (8, 4)  PP-LCNet softmax outputs for rotations 0..3 x crops (center, full) -- row order: rot0 center, rot0 full, rot1 center, ...
  or_logits  (4, 4)  own classifier logits for rotations k = 0..3 (the default votes with k = 0, 2)
  reg_angle          the 360-degree regressor on the working canvas, ALWAYS computed (the default calls it for ~1 % of pages)
  fine_tilt, fft_sharp, lines / h_slope (Hough), ink (dark-pixel fraction of the canvas), std
Nothing here changes the pipeline; `views_emulate` rebuilds the default decision and is checked against `bench.features` (self-check).
"""
from __future__ import annotations

import argparse
import json

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline, PipelineConfig, rotate_image_expanded
from docangle.pipeline import _to_gray

from .degrade import LEVELS, render, sample_angle
from .run import make_cases


class Replay:
    def __init__(self):
        self.cfg = PipelineConfig(lcnet_crops=("center", "full"), lcnet_rots=(0, 1, 2, 3))
        self.pipe = DocumentOrientationPipeline(self.cfg)
        self.pipe._lcnet_session(); self.pipe._orient._ensure(); self.pipe._regressor._ensure()

    def run(self, img):
        p, cfg = self.pipe, self.cfg
        gray = _to_gray(img)
        h, w = gray.shape[:2]
        m = max(h, w)
        work = cv2.resize(gray, (int(w * cfg.working_max_dim / m), int(h * cfg.working_max_dim / m)), interpolation=cv2.INTER_AREA) if m > cfg.working_max_dim else gray
        row = {"std": float(work[::2, ::2].std())}
        if row["std"] < cfg.min_std or min(h, w) < cfg.min_side:
            return None
        tilt, sharp = p._fft.tilt_ex(work)
        h_slope, lines = p._hough_slope(work, None, cfg.pass1_max_dim, cfg.pass1_strips)
        ortho = rotate_image_expanded(work, -tilt)
        views, owner = p._lcnet_view_set(ortho)
        sess = p._lcnet_session()
        probs = sess.run(None, {sess.get_inputs()[0].name: p._lcnet_blob(views)})[0]
        ks = (0, 1, 2, 3)
        lg = p._orient.logits(p._orient.views(ortho, ks))
        row.update(fine_tilt=float(tilt), fft_sharp=float(sharp), h_slope=float(h_slope), lines=int(lines),
                   lc_owner=[int(o) for o in owner], lc_probs=np.asarray(probs, float).round(6).tolist(),
                   or_logits=np.asarray(lg, float).round(5).tolist(), reg_angle=float(p._regressor.predict(work)),
                   ink=float((work < 128).mean()))
        return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", required=True)
    ap.add_argument("--levels", nargs="+", default=["scan", "photo_easy", "photo_hard"])
    ap.add_argument("--angle-mode", default="uniform")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--seed-start", type=int, default=0)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rp = Replay()
    rows = []
    for ds in a.datasets:
        for lv in a.levels:
            cases, _, _ = make_cases(ds, lv, a.angle_mode, a.seeds, a.n, a.seed_start)
            for f, s, i, rng in cases:
                page = cv2.imread(f)
                gt = sample_angle(a.angle_mode, rng)
                img = render(page, gt, LEVELS[lv], rng)
                r = rp.run(img)
                rows.append(dict(ds=ds, lv=lv, seed=s, page=f"{ds}/{f.split('/')[-1]}", gt=gt, **(r if r is not None else {"skipped": True})))
            print("views", ds, lv, flush=True)
    json.dump(rows, open(a.out, "w"))
    print("wrote", a.out, len(rows))


if __name__ == "__main__":
    main()
