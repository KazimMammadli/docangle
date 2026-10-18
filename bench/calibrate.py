"""Review-policy experiments on a `bench.features` dump (experiment E2). Page-grouped cross-validation throughout.

  python -m bench.calibrate /tmp/feat.json

1. voter fusion: weights / temperature of PP-LCNet and the own classifier by NLL of the 4-class decision vs the current 1:1 product.
2. review score: a small logistic model on decision features, fitted on page-disjoint folds, compared with the current confidence
   rule AT THE SAME REVIEW RATE (accepted flips and accepted errors > 5 deg among the pages that are not sent to review).
Cases of the known sideways source page are dropped (its 'flips' are correct answers).
"""
from __future__ import annotations

import argparse
import json

import numpy as np

BAD_SOURCE = {"certified_invoice_030.png"}
PRIMARY = {"az", "invoices", "tobacco_cert", "rvl_heldout"}


def load(path):
    rows = [r for r in json.load(open(path)) if r["angle"] is not None and "lcnet" in r and "orient" in r
            and r["page"].split("/")[-1] not in BAD_SOURCE]
    return rows


def true_idx(gt):
    coarse = int(round(gt / 90.0)) * 90 % 360
    return ((360 - coarse) % 360) // 90


def lse(x):
    m = x.max(-1, keepdims=True)
    return m + np.log(np.exp(x - m).sum(-1, keepdims=True))


def fuse(lc, orr, w1=1.0, w2=1.0, t=1.0):
    z = (w1 * lc + w2 * orr) / t
    return z - lse(z)


def fit_fusion(lc, orr, y):
    best = None
    for w1 in (0.0, 0.25, 0.5, 0.75, 1.0, 1.5):
        for w2 in (0.0, 0.25, 0.5, 0.75, 1.0, 1.5):
            for t in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
                if w1 == 0 and w2 == 0:
                    continue
                lp = fuse(lc, orr, w1, w2, t)
                nll = -lp[np.arange(len(y)), y].mean()
                if best is None or nll < best[0]:
                    best = (nll, w1, w2, t)
    return best


def feats(r_list):
    X = []
    for r in r_list:
        lc, orr = np.array(r["lcnet"]), np.array(r["orient"])
        fz = fuse(lc, orr)
        p = np.exp(fz)
        top = np.sort(p)[::-1]
        pl, po = np.exp(lc - lse(lc)), np.exp(orr - lse(orr))
        eps = 1e-6
        lg = lambda v: np.log((v + eps) / (1 - v + eps))
        X.append([lg(top[0]), lg(top[0] - top[1]) if top[0] - top[1] < 1 else 6.0, lg(pl.max()), lg(po.max()),
                  float(pl.argmax() == po.argmax()), np.log1p(r["lines"]), min(1.0, r["lines"] / 80.0),
                  min(r["h_gap"] if r["h_gap"] is not None else 0.0, 10.0), float(r["fallback"])])
    return np.array(X, float)


def logistic(X, y, l2=1.0, it=50):
    mu, sd = X.mean(0), X.std(0) + 1e-6
    Z = np.hstack([(X - mu) / sd, np.ones((len(X), 1))])
    w = np.zeros(Z.shape[1])
    R = l2 * np.eye(Z.shape[1]); R[-1, -1] = 0
    for _ in range(it):
        p = 1 / (1 + np.exp(-Z @ w))
        g = Z.T @ (p - y) + R @ w
        H = (Z * (p * (1 - p))[:, None]).T @ Z + R + 1e-6 * np.eye(Z.shape[1])
        w -= np.linalg.solve(H, g)
    return lambda Xn: 1 / (1 + np.exp(-np.hstack([(Xn - mu) / sd, np.ones((len(Xn), 1))]) @ w))


def grouped_folds(pages, k=5, seed=0):
    u = sorted(set(pages)); rng = np.random.default_rng(seed); rng.shuffle(u)
    fold = {p: i % k for i, p in enumerate(u)}
    return np.array([fold[p] for p in pages])


def at_review_rate(score_risk, flip, big, rate):
    """Send the `rate` fraction with the highest risk to review; return accepted flips / accepted >5deg."""
    n = len(score_risk); k = int(round(rate * n))
    order = np.argsort(-score_risk, kind="stable")
    acc = np.ones(n, bool); acc[order[:k]] = False
    return int((flip & acc).sum()), int((big & acc).sum())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("feat"); a = ap.parse_args()
    rows = load(a.feat)
    ds = np.array([r["ds"] for r in rows]); pages = [r["page"] for r in rows]
    err = np.array([r["err"] for r in rows]); flip, big = err > 45, err > 5
    conf = np.array([r["conf"] for r in rows]); rev = np.array([r["review"] for r in rows])
    lc = np.array([r["lcnet"] for r in rows]); orr = np.array([r["orient"] for r in rows])
    y = np.array([true_idx(r["gt"]) for r in rows])
    amb = np.array([abs(((r["gt"] + 45) % 90) - 45) > 40 for r in rows])
    print(f"cases {len(rows)} (primary {np.isin(ds, list(PRIMARY)).sum()}), pages {len(set(pages))}, flips {flip.sum()}, errors>5deg {big.sum()}, current review {rev.sum()} ({rev.mean()*100:.1f} %)")

    print("\n== 1. fusion of the two voters (NLL of the true quadrant; argmax flips among non-ambiguous cases)")
    ok = ~amb
    for name, w in (("1:1 (current)", (1, 1, 1)), ("lcnet only", (1, 0, 1)), ("own only", (0, 1, 1))):
        lp = fuse(lc[ok], orr[ok], *w); pred = lp.argmax(1)
        print(f"  {name:14s} NLL {-lp[np.arange(ok.sum()), y[ok]].mean():.4f}  quadrant errors {(pred != y[ok]).sum()}")
    nll, w1, w2, t = fit_fusion(lc[ok], orr[ok], y[ok])
    lp = fuse(lc[ok], orr[ok], w1, w2, t)
    print(f"  best grid     NLL {nll:.4f}  w_lcnet {w1} w_own {w2} T {t}  quadrant errors {(lp.argmax(1) != y[ok]).sum()}  (in-sample, 3 parameters)")

    print("\n== 2. review score (5-fold, page-disjoint): accepted flips / accepted errors>5deg at the SAME review rate as the current rule")
    X = feats(rows)
    fold = grouped_folds(pages)
    for label, target in (("flip", flip), ("error>5deg", big)):
        oof = np.zeros(len(rows))
        for k in range(5):
            tr, te = fold != k, fold == k
            oof[te] = logistic(X[tr], target[tr].astype(float))(X[te])
        for group, m in (("primary pools", np.isin(ds, list(PRIMARY))), ("external pools", ~np.isin(ds, list(PRIMARY))), ("all", np.ones(len(rows), bool))):
            rate = rev[m].mean()
            cur = at_review_rate(1 - conf[m], flip[m], big[m], rate)
            new = at_review_rate(oof[m], flip[m], big[m], rate)
            print(f"  model target={label:10s} {group:14s} review {rate*100:4.1f} %  current rule: acc.flips {cur[0]:3d} acc.>5deg {cur[1]:3d} | learned: acc.flips {new[0]:3d} acc.>5deg {new[1]:3d}   (n={m.sum()}, flips {flip[m].sum()}, >5deg {big[m].sum()})")
        print("  risk-coverage (all pools): review rate -> accepted flips, current vs learned[" + label + "]")
        for rate in (0.01, 0.02, 0.05, 0.10, 0.20):
            cur = at_review_rate(1 - conf, flip, big, rate); new = at_review_rate(oof, flip, big, rate)
            print(f"     {rate*100:4.0f} %   current {cur[0]:3d}/{cur[1]:3d}   learned {new[0]:3d}/{new[1]:3d}   (accepted flips / accepted >5deg)")

    print("\n== 3. leave-one-POOL-out (train on the other pools, score the held-out pool; target = flip) at the pool's current review rate")
    names = ["lcnet_top_logit", "margin_logit", "lcnet_max_logit", "own_max_logit", "voters_agree", "log1p_lines", "lines_term", "hough_fft_gap", "fallback"]
    tot_cur = tot_new = 0
    for d in sorted(set(ds)):
        m = ds == d
        if flip[m].sum() == 0 and big[m].sum() == 0:
            continue
        risk = logistic(X[~m], flip[~m].astype(float))(X[m])
        rate = rev[m].mean()
        cur = at_review_rate(1 - conf[m], flip[m], big[m], rate); new = at_review_rate(risk, flip[m], big[m], rate)
        tot_cur += cur[0]; tot_new += new[0]
        print(f"  {d:14s} n={m.sum():4d} flips {flip[m].sum():2d} review {rate*100:4.1f} %  acc.flips current {cur[0]:2d} learned {new[0]:2d} | acc.>5deg current {cur[1]:2d} learned {new[1]:2d}")
    print(f"  total accepted flips over pools with errors: current {tot_cur}, learned {tot_new}")
    print("\n== 4. coefficients (standardised features, fitted on all cases; target = flip)")
    mu, sd = X.mean(0), X.std(0) + 1e-6
    f = logistic(X, flip.astype(float))
    for j, nme in enumerate(names):
        Xp = X.copy(); Xp[:, j] = mu[j] + sd[j]
        print(f"  {nme:16s} +1 sd -> mean risk x{(f(Xp).mean() / f(X).mean()):.2f}")


if __name__ == "__main__":
    main()
