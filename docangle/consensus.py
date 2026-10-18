"""Job-level (multi-page) consensus: pages of one scan job usually share their orientation (opt-in).

Each page keeps its own fused quadrant posterior ``p_i`` (``Result.posterior``). The other pages vote on it with a leave-one-out
evidence that tolerates a fraction ``eps`` of odd pages::

    L_-i(c) = sum_{j != i} log((1 - eps) * p_j(c) + eps / 4)          q_i = softmax(L_-i)
    r_i(c)  proportional to  p_i(c) * ((1 - eps) * q_i(c) + eps / 4)

The page takes ``argmax r_i`` and ``confidence = max r_i`` (minus the fallback penalty if the regressor overrode the classifiers),
reviewed below the usual threshold. So an unsure page next to confident neighbours adopts their orientation and may leave the review
queue, while a confident page that disagrees with a unanimous job stays as it is but is sent to review (the consensus can raise a
rare odd page's odds at most 1 : 77 for eps = 0.05). The fine angle of a page is never shared. Pages without a posterior (blank,
too small, too few lines, unreadable) neither vote nor change.
"""
from __future__ import annotations

import dataclasses
from typing import List, Optional, Sequence

import numpy as np

from .pipeline import PipelineConfig, Result, normalize_angle

_CW = (0, 90, 180, 270)      # class index -> clockwise degrees of the straightened page


def _quadrant_index(result: Result) -> Optional[int]:
    """Class index (of ``Result.posterior``) of the quadrant the page's current angle was built from."""
    if result.angle is None or result.fine_tilt is None:
        return None
    coarse = int(round(normalize_angle(result.angle - result.fine_tilt) / 90.0)) * 90 % 360
    return ((360 - coarse) % 360) // 90


def apply_job_consensus(results: Sequence[Result], config: Optional[PipelineConfig] = None, eps: float = 0.05,
                        min_pages: int = 3) -> List[Result]:
    """Return new Results for one job (input order); the input Results are not modified."""
    cfg = config or PipelineConfig()
    out = list(results)
    if cfg.confidence_model == "legacy":                    # that confidence is not a posterior, so it cannot be recomputed here
        return out
    idx = [i for i, r in enumerate(results) if r.posterior is not None and r.angle is not None and r.fine_tilt is not None]
    if len(idx) < max(2, min_pages):
        return out
    P = np.array([results[i].posterior for i in idx], float)
    P = P / P.sum(axis=1, keepdims=True)
    logv = np.log((1.0 - eps) * P + eps / 4.0)              # vote of every page
    total = logv.sum(axis=0)
    for row, i in enumerate(idx):
        r = results[i]
        loo = total - logv[row]                              # leave-one-out evidence
        q = np.exp(loo - loo.max()); q /= q.sum()
        post = P[row] * ((1.0 - eps) * q + eps / 4.0)
        post /= post.sum()
        cur, new = _quadrant_index(r), int(np.argmax(post))
        conf = float(post[new]) - (cfg.fallback_penalty if r.fallback_triggered else 0.0) \
            - 0.15 * sum(c in r.reasons for c in ("LARGE_RESIDUAL", "LARGE_FINE_DISAGREEMENT"))     # the page's own penalties (pipeline.analyze)
        conf = round(max(0.0, min(1.0, conf)), 3)
        reasons = list(r.reasons)
        angle = r.angle
        if new != cur:
            angle = round(float(normalize_angle(r.fine_tilt + (360 - _CW[new]) % 360)), 2)
            reasons.append("JOB_CONSENSUS")
        disagree = new == cur and int(np.argmax(q)) != new and q.max() >= 0.95
        if disagree:
            reasons.append("JOB_DISAGREE")                  # confident page against a (nearly) unanimous job: kept, but reviewed
        needs_review = disagree or conf < cfg.review_confidence
        quality = ("NEEDS_HUMAN_REVIEW" if needs_review else "HIGH_CONFIDENCE" if conf >= cfg.high_confidence else "MEDIUM_CONFIDENCE")
        out[i] = dataclasses.replace(r, angle=angle, confidence=conf, needs_review=needs_review, quality=quality,
                                     reasons=reasons, posterior=[round(float(x), 5) for x in post])
    return out
