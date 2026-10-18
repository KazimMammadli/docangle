"""Component ablation on a `bench.views_dump` file, OFFLINE (no model runs), with page-cluster bootstrap.

  python -m bench.ablate /tmp/views_dev.json --selfcheck reports/data/features_v4_3.json.gz [--out reports/ablation_dev.txt]

Every variant of `VARIANTS` is rebuilt with `bench.views_emulate.decide`. Reported per group (primary pools / external pools / all), and for the PAIRED
difference to the default with a 95 % interval from resampling PAGES (the 6300 cases are rotations of ~1350 pages, so rows are not independent):
  flips (final angle error > 45 deg), accepted flips and accepted errors > 5 deg AT THE DEFAULT'S REVIEW RATE (each variant's lowest-confidence rows are reviewed until the number
  of reviewed cases equals the default's, so a variant is not rewarded for reviewing more), ordinary review rate at the shipped threshold, <=1 deg rate.
Cases of the sideways source page certified_invoice_030.png and the +-45 ambiguity zone (|((gt+45)%90)-45| > 40) are excluded from the error counts.
"""
from __future__ import annotations

import argparse
import gzip
import json

import numpy as np

from .metrics import circ_err
from .views_emulate import decide

PRIMARY = {"az", "invoices", "tobacco_cert", "rvl_heldout"}
BAD_SOURCE = "certified_invoice_030.png"

VARIANTS = {
    "default (v4.3.1)": {},
    "lcnet 2 views (rot 0,2)": dict(lc_rots=(0, 2)),
    "lcnet 1 view": dict(lc_rots=(0,)),
    "own 1 view (0 only)": dict(own_ks=(0,)),
    "lcnet 2 + own 1 view": dict(lc_rots=(0, 2), own_ks=(0,)),
    "12-view (lcnet centre+full x4, own x4)": dict(lc_crops=("center", "full"), own_ks=(0, 1, 2, 3)),
    "own classifier only": dict(w_lc=0.0),
    "PP-LCNet only": dict(w_own=0.0),
    "regressor off (flag kept, no override)": dict(ambiguity_flag_only=True, use_reg=False),
    "regressor off, no flag": dict(use_reg=False),
    "TOO_FEW_LINES angle = regressor (v4.3)": dict(tfl_mode="regressor"),
    "no TOO_FEW_LINES gate": dict(min_lines=0),
    "no gate, regressor off (flag kept)": dict(min_lines=0, ambiguity_flag_only=True, use_reg=False),
}


def load(path):
    op = gzip.open if path.endswith(".gz") else open
    return json.load(op(path, "rt"))


def usable(rows):
    return [r for r in rows if not r.get("skipped") and r["page"].split("/")[-1] != BAD_SOURCE]


def evaluate(rows, kw):
    out = [decide(r, **kw) for r in rows]
    err = np.array([circ_err(o["angle"], r["gt"]) for o, r in zip(out, rows)])
    return err, np.array([o["conf"] for o in out]), np.array([o["review"] for o in out]), np.array([o["fallback"] for o in out])


def at_rate(conf, k):
    """Review the k lowest-confidence rows (stable order); returns the boolean 'accepted' mask."""
    acc = np.ones(len(conf), bool)
    acc[np.argsort(conf, kind="stable")[:k]] = False
    return acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("views"); ap.add_argument("--selfcheck", default=None); ap.add_argument("--out", default=None)
    ap.add_argument("--boot", type=int, default=3000)
    a = ap.parse_args()
    raw = load(a.views)
    rows = usable(raw)
    amb = np.array([abs(((r["gt"] + 45) % 90) - 45) > 40 for r in rows]); ok = ~amb
    ds = np.array([r["ds"] for r in rows]); page = np.array([r["page"] for r in rows])
    groups = {"primary": np.isin(ds, list(PRIMARY)) & ok, "external": ~np.isin(ds, list(PRIMARY)) & ok, "all": ok}
    L = [f"{a.views}: {len(raw)} cases, {len(rows)} usable, {int(ok.sum())} outside the +-45 zone, {len(set(page))} pages"]

    if a.selfcheck:
        ref = [r for r in load(a.selfcheck)]
        assert len(ref) == len(raw), "self-check reference has a different case set"
        keep = [i for i, r in enumerate(raw) if not r.get("skipped") and r["page"].split("/")[-1] != BAD_SOURCE]
        d_same = d_rev = d_conf = nfb = 0
        for i in keep:
            e, r = decide(raw[i]), ref[i]
            fb = r["fallback"]
            nfb += fb
            if not fb and circ_err(e["angle"], r["angle"]) > 0.05:
                d_same += 1
            if e["review"] != r["review"]:
                d_rev += 1
            if abs(e["conf"] - r["conf"]) > 1e-3:
                d_conf += 1
        L.append(f"SELF-CHECK vs bench.features dump: {len(keep)} cases; angle differs (non-fallback rows) {d_same}, review differs {d_rev}, confidence differs {d_conf} (fallback rows {nfb} differ only by the real pipeline's Hough residual)")

    res = {n: evaluate(rows, kw) for n, kw in VARIANTS.items()}
    base = res["default (v4.3.1)"]
    pages = sorted(set(page)); pidx = {p: i for i, p in enumerate(pages)}
    pid = np.array([pidx[p] for p in page])
    rng = np.random.default_rng(0)
    boots = rng.integers(0, len(pages), size=(a.boot, len(pages)))

    def per_page(x):
        return np.bincount(pid, weights=x.astype(float), minlength=len(pages))

    def row_metrics(r, k_by_group):
        err, conf, rev, fb = r
        m = {}
        for g, mask in groups.items():
            acc = at_rate(np.where(mask, conf, np.inf), k_by_group[g])      # rows outside the group are never reviewed here
            flip = (err > 45) & mask
            m[g] = dict(flips=flip, accf=flip & acc, acc5=((err > 5) & mask) & acc, big=(err > 5) & mask, le1=(err <= 1) & mask, rev=rev & mask)
        return m

    k_by = {g: int(base[2][mask].sum()) for g, mask in groups.items()}
    bm = row_metrics(base, k_by)
    for g in groups:
        L.append(f"\n=== group: {g} (cases {int(groups[g].sum())}, pages {len(set(page[groups[g]]))}; default reviews {k_by[g]}, flips {int(bm[g]['flips'].sum())}, accepted flips {int(bm[g]['accf'].sum())}) ===")
        L.append(f"{'variant':44s} {'flips':>6s} {'acc.flips':>9s} {'acc>5':>6s} {'>5deg':>6s} {'<=1deg%':>8s} {'review%':>8s} | paired vs default (pages): d.flips [95% CI] | d.acc.flips [CI] | d.acc>5 [CI] | pages changed")
        for n, r in res.items():
            m = row_metrics(r, k_by)[g]
            line = f"{n:44s} {int(m['flips'].sum()):6d} {int(m['accf'].sum()):9d} {int(m['acc5'].sum()):6d} {int(m['big'].sum()):6d} {m['le1'][groups[g]].mean()*100:8.1f} {m['rev'][groups[g]].mean()*100:8.2f} |"
            if n != "default (v4.3.1)":
                cells = []
                for key in ("flips", "accf", "acc5"):
                    d = per_page(m[key]) - per_page(bm[g][key])
                    bs = d[boots].sum(axis=1)
                    cells.append(f"{d.sum():+5.0f} [{np.percentile(bs, 2.5):+4.0f},{np.percentile(bs, 97.5):+4.0f}]")
                changed = int(((per_page(m['flips']) != per_page(bm[g]['flips'])) | (per_page(m['accf']) != per_page(bm[g]['accf']))).sum())
                line += " " + " | ".join(cells) + f" | {changed}"
            L.append(line)
    txt = "\n".join(L)
    print(txt)
    if a.out:
        open(a.out, "w").write(txt + "\n")


if __name__ == "__main__":
    main()
