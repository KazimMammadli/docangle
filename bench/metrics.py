"""Metrics with confidence intervals for angle benchmarks."""
from __future__ import annotations

import math
from typing import Dict, List

import numpy as np


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - r) / d) * 100, min(1.0, (c + r) / d) * 100)


def boot_ci(x: np.ndarray, fn, n_boot: int = 1000, seed: int = 0):
    if len(x) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    vals = [fn(x[rng.integers(0, len(x), len(x))]) for _ in range(n_boot)]
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def circ_err(pred: float, gt: float) -> float:
    return abs((pred - gt + 180.0) % 360.0 - 180.0)


def auroc(score: np.ndarray, positive: np.ndarray) -> float:
    """P(score of a random positive > score of a random negative); ties count half."""
    pos, neg = score[positive], score[~positive]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    allv = np.concatenate([pos, neg])
    ranks = allv.argsort().argsort().astype(float) + 1
    # average ranks for ties
    _, inv, cnt = np.unique(allv, return_inverse=True, return_counts=True)
    sums = np.bincount(inv, weights=ranks)
    ranks = (sums / cnt)[inv]
    return float((ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def summarize(records: List[Dict]) -> Dict:
    """records: dict(gt, pred|None, conf, review, ms)."""
    n = len(records)
    und = [r for r in records if r["pred"] is None]
    ok = [r for r in records if r["pred"] is not None]
    err = np.array([circ_err(r["pred"], r["gt"]) for r in ok]) if ok else np.zeros(0)
    ms = np.array([r["ms"] for r in records])
    out: Dict = {"n": n, "undetermined": len(und)}
    if len(err):
        flip = err > 45.0
        f180 = err > 135.0
        f90 = flip & ~f180
        out.update(
            mae=float(err.mean()), mae_ci=boot_ci(err, np.mean),
            median=float(np.median(err)), median_ci=boot_ci(err, np.median),
            p90=float(np.percentile(err, 90)), p95=float(np.percentile(err, 95)), p99=float(np.percentile(err, 99)),
            max=float(err.max()),
            le05=float((err <= 0.5).mean() * 100), le1=float((err <= 1.0).mean() * 100),
            le1_ci=wilson(int((err <= 1.0).sum()), len(err)),
            le2=float((err <= 2.0).mean() * 100),
            flip=float(flip.mean() * 100), flip_ci=wilson(int(flip.sum()), len(err)),
            flip180=float(f180.mean() * 100), flip90=float(f90.mean() * 100),
        )
        rev = np.array([r["review"] for r in ok], dtype=bool)
        acc = ~rev
        out["review_rate"] = float(rev.mean() * 100)
        out["coverage"] = float(acc.mean() * 100)
        if acc.any():
            out["accepted_flip"] = float(flip[acc].mean() * 100)
            out["accepted_flip_n"] = int(flip[acc].sum())
            out["accepted_flip_ci"] = wilson(int(flip[acc].sum()), int(acc.sum()))
            out["accepted_le1"] = float((err[acc] <= 1.0).mean() * 100)
        out["flips_caught_by_review"] = int((flip & rev).sum())
        conf = np.array([r["conf"] for r in ok])
        out["auroc_conf_vs_good"] = auroc(conf, err <= 5.0)
    if len(ms):
        out.update(ms_mean=float(ms.mean()), ms_p50=float(np.percentile(ms, 50)), ms_p95=float(np.percentile(ms, 95)))
    return out


def risk_coverage(records: List[Dict], thresholds=(0.0, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95)):
    ok = [r for r in records if r["pred"] is not None]
    err = np.array([circ_err(r["pred"], r["gt"]) for r in ok])
    conf = np.array([r["conf"] for r in ok])
    rows = []
    for t in thresholds:
        m = conf >= t
        if not m.any():
            rows.append({"t": t, "coverage": 0.0}); continue
        rows.append({"t": t, "coverage": float(m.mean() * 100), "flip": float((err[m] > 45).mean() * 100),
                     "flip_n": int((err[m] > 45).sum()), "le1": float((err[m] <= 1.0).mean() * 100),
                     "mae": float(err[m].mean())})
    return rows
