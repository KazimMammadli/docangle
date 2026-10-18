"""Analyse the E3b dump: docTR alone, three-voter fusion, and the effect on the v4.3 review rule.  python -m bench.exp_doctr_analyze /tmp/e3/feat_doctr.json [duarte]   (the optional word is the voter key in the dump)"""
import json
import sys

import numpy as np

from .calibrate import BAD_SOURCE, PRIMARY, fuse, true_idx

V = sys.argv[2] if len(sys.argv) > 2 else "doctr"
rows = [r for r in json.load(open(sys.argv[1])) if r["angle"] is not None and V in r and "orient" in r
        and r["page"].split("/")[-1] not in BAD_SOURCE]
ds = np.array([r["ds"] for r in rows]); pages = [r["page"] for r in rows]
lc, orr, dt = (np.array([r[k] for r in rows]) for k in ("lcnet", "orient", V))
y = np.array([true_idx(r["gt"]) for r in rows])
amb = np.array([abs(((r["gt"] + 45) % 90) - 45) > 40 for r in rows]); ok = ~amb
fb = np.array([r["fallback"] for r in rows]); err = np.array([r["err"] for r in rows]); flip = err > 45; big = err > 5
rev_now = np.array([r["review"] for r in rows])
own = np.isin(ds, list(PRIMARY))
print(f"cases {len(rows)} (non-ambiguous {ok.sum()}), pages {len(set(pages))}; {V} time per page (2 views) mean {np.mean([r[V + '_ms'] for r in rows]):.1f} ms")


def qerr(lp, m=ok):
    return int((lp.argmax(1)[m] != y[m]).sum())


print("\nquadrant errors (non-ambiguous cases)   all | primary | external | per pool")
def line(name, lp):
    pools = " ".join(f"{d[:9]}:{qerr(lp, ok & (ds == d))}" for d in sorted(set(ds)))
    print(f"  {name:28s} {qerr(lp):4d} | {qerr(lp, ok & own):3d} | {qerr(lp, ok & ~own):3d} | {pools}")
line("PP-LCNet", lc); line("own v4", orr); line(V, dt)
base = fuse(lc, orr); line("current (LCNet + own)", base)
for w in (0.25, 0.5, 0.75, 1.0, 1.5):
    z = base + w * dt
    line(f"+ {V} x{w}", z - np.log(np.exp(z).sum(1, keepdims=True)))
wl = (base.argmax(1) != y) & ok; wd = (dt.argmax(1) != y) & ok
print(f"\nerror overlap: current wrong {wl.sum()}, {V} wrong {wd.sum()}, both wrong {(wl & wd).sum()}, current wrong but {V} right {(wl & ~wd).sum()}, {V} wrong but current right {(~wl & wd).sum()}")

print("\nreview rule v4.3 (conf = fused posterior - 0.30*fallback, review < 0.90): review % / accepted flips (primary | external)")
for w in (0.0, 0.25, 0.5, 0.75, 1.0):
    z = base + w * dt; lp = z - np.log(np.exp(z).sum(1, keepdims=True))
    conf = np.exp(lp).max(1) - 0.3 * fb
    wrong = (lp.argmax(1) != y) & ok            # quadrant wrong under this fusion
    out = []
    for g, m in (("primary", own), ("external", ~own)):
        for t in (0.90, 0.95):
            r = conf[m] < t
            out.append(f"{g} t{t}: {r.mean()*100:4.1f}% / {int((wrong[m] & ~r).sum()):2d}")
    print(f"  {V} weight {w:4.2f}: " + " | ".join(out))
