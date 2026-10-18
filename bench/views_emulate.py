"""Offline emulation of pipeline variants from a `bench.views_dump` file (no model is run).

`decide(row, **variant)` rebuilds docangle's decision for one case: PP-LCNet vote over a chosen set of views, own-classifier vote over
a chosen set of rotations, weights/temperature, regressor fallback (or none), TOO_FEW_LINES gate and its angle source, confidence and
review rule. The default variant reproduces v4.3 (self-check in `bench.ablate --selfcheck`): it is exact except for the final Hough residual
that the real pipeline adds after a regressor override (that residual is < 5 degrees, so flip decisions are unaffected).
"""
from __future__ import annotations

import math

import numpy as np

CW = (0, 90, 180, 270)


def norm(a):
    a = (a + 180.0) % 360.0 - 180.0
    return 180.0 if a == -180.0 else a


def dist(a, b):
    return abs(norm(a - b))


def lc_post(row, rots=(0, 1, 2, 3), crops=("center",)):
    owner, probs = row["lc_owner"], np.asarray(row["lc_probs"])
    sel = [i for i, r in enumerate(owner) if r in rots and (("center" in crops and i % 2 == 0) or ("full" in crops and i % 2 == 1))]
    lp = np.array([np.mean([math.log(probs[i][(c - owner[i]) % 4] + 1e-6) for i in sel]) for c in range(4)])
    return lp - (lp.max() + math.log(np.exp(lp - lp.max()).sum()))


def own_post(row, ks=(0, 2), temperature=1.0):
    lg = np.asarray(row["or_logits"])[list(ks)] / temperature
    lg = lg - lg.max(axis=1, keepdims=True)
    lp = lg - np.log(np.exp(lg).sum(axis=1, keepdims=True))
    out = np.array([np.mean([lp[i][(c - ks[i]) % 4] for i in range(len(ks))]) for c in range(4)])
    return out - (np.log(np.exp(out - out.max()).sum()) + out.max())


def decide(row, lc_rots=(0, 1, 2, 3), lc_crops=("center",), own_ks=(0, 2), w_lc=1.0, w_own=1.0, temperature=1.0, use_reg=True,
           tfl_mode="classifier", min_lines=8, review_thr=0.90, fb_penalty=0.30, floor=0.60, boundary=25.0, thr_score=0.88,
           disagree=45.0, tfl_review=True, ambiguity_flag_only=False):
    """-> dict(angle, conf, review, fallback, score, tfl). `ambiguity_flag_only`: keep the fallback TRIGGER (flag + penalty) but never use the regressor angle."""
    tilt = row["fine_tilt"]
    lp = 0.0
    if w_lc:
        lp = lp + w_lc * lc_post(row, lc_rots, lc_crops)
    if w_own:
        lp = lp + w_own * own_post(row, own_ks, temperature)
    post = np.exp(lp - np.max(lp)); post /= post.sum()
    idx = int(np.argmax(post)); score = float(post[idx])
    chosen = norm(tilt + (360 - CW[idx]) % 360)
    reg = norm(row["reg_angle"])
    if row["lines"] < min_lines:
        angle = chosen if tfl_mode == "classifier" else reg
        return dict(angle=angle, conf=0.40, review=bool(tfl_review), fallback=True, score=score, tfl=True)
    fallback = False
    if (use_reg or ambiguity_flag_only) and (score < floor or (abs(tilt) > boundary and score < thr_score)):
        if dist(chosen, reg) > disagree:
            fallback = True
            if use_reg and not ambiguity_flag_only:
                chosen = reg
    conf = score - (fb_penalty if fallback else 0.0)
    return dict(angle=chosen, conf=conf, review=conf < review_thr, fallback=fallback, score=score, tfl=False)
