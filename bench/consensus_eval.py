"""E5 evaluation: multi-page consensus on simulated jobs.  python -m bench.consensus_eval --out reports/consensus_eval.txt

Jobs: (a) the Azerbaijani PDFs' pages grouped by document (REAL multi-page documents), (b) PSEUDO-jobs of 10 random pages of one pool
(pages of a pseudo-job are independent, which overstates how much a neighbour can help: hard pages cluster inside real documents).
Every page is rendered at its job's quadrant + a random tilt (+-25 deg) through the benchmark's degradations. Scenarios: `clean`
(all pages of a job share the quadrant) and `mixed` (one page in ten has another quadrant: the cost of a wrong assumption).
"""
from __future__ import annotations

import argparse
import re
import zlib

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline, PipelineConfig, apply_job_consensus

from . import datasets
from .degrade import LEVELS, render
from .metrics import circ_err


def groups(pool, n):
    files, _ = datasets.pick(datasets.pool(pool), n, 0)
    if pool == "az":
        by = {}
        for f in files:
            by.setdefault(re.sub(r"_page_\d+.*", "", f.split("/")[-1]), []).append(f)
        return list(by.values()), "real documents"
    return [files[i:i + 10] for i in range(0, len(files) - 9, 10)], "pseudo-jobs of 10"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pools", nargs="+", default=["az", "invoices", "rvl_heldout", "ext_doclaynet", "ext_cord"])
    ap.add_argument("--levels", nargs="+", default=["photo_easy", "photo_hard"])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--eps", type=float, default=0.05)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    pipe = DocumentOrientationPipeline(PipelineConfig())
    lines = []

    def emit(s=""):
        print(s, flush=True); lines.append(s)

    emit(f"consensus eps={a.eps}; flip = error > 45 deg; accepted = not needs_review")
    tot = {}
    for pool in a.pools:
        gs, kind = groups(pool, a.n)
        for lv in a.levels:
            rec = {"clean": [], "mixed": []}      # (job index, page index, gt, own result, odd result or None, is_odd)
            for jn, files in enumerate(gs):
                rng = np.random.default_rng([zlib.crc32(f"{pool}/{lv}/{jn}".encode()) & 0xFFFFFF, 7])
                q = int(rng.integers(0, 4))
                odd_idx = int(rng.integers(0, len(files)))
                clean, mixed = [], []
                for pi, f in enumerate(files):
                    page = cv2.imread(f)
                    tilt = float(rng.uniform(-25, 25))
                    gt = ((q * 90 + tilt + 180) % 360) - 180
                    r = pipe.predict(render(page, gt, LEVELS[lv], rng))
                    clean.append((gt, r)); mixed.append((gt, r, False))
                    if pi == odd_idx:
                        q2 = (q + int(rng.integers(1, 4))) % 4
                        gt2 = ((q2 * 90 + tilt + 180) % 360) - 180
                        mixed[-1] = (gt2, pipe.predict(render(page, gt2, LEVELS[lv], rng)), True)
                rec["clean"].append(clean); rec["mixed"].append(mixed)
            for scen in ("clean", "mixed"):
                st = dict(n=0, fb=0, fa=0, afb=0, afa=0, rb=0, ra=0, odd=0, odd_kept=0, odd_flipped_by_job=0, odd_rev=0)
                for job in rec[scen]:
                    items = [(x[0], x[1]) for x in job]
                    odds = [(len(x) > 2 and x[2]) for x in job]
                    after = apply_job_consensus([r for _, r in items], pipe.config, a.eps)
                    for (gt, rb), ra, odd in zip(items, after, odds):
                        eb = 180.0 if rb.angle is None else circ_err(rb.angle, gt)
                        ea = 180.0 if ra.angle is None else circ_err(ra.angle, gt)
                        st["n"] += 1; st["fb"] += eb > 45; st["fa"] += ea > 45
                        st["afb"] += (eb > 45) and not rb.needs_review; st["afa"] += (ea > 45) and not ra.needs_review
                        st["rb"] += rb.needs_review; st["ra"] += ra.needs_review
                        if odd:
                            st["odd"] += 1; st["odd_kept"] += ea <= 45; st["odd_flipped_by_job"] += (eb <= 45) and (ea > 45); st["odd_rev"] += ra.needs_review
                emit(f"{pool:14s} {lv:10s} {scen:6s} ({kind}, {len(rec[scen])} jobs, {st['n']} pages): flips {st['fb']:3d} -> {st['fa']:3d} | accepted flips {st['afb']:3d} -> {st['afa']:3d} | review {st['rb']:3d} -> {st['ra']:3d}"
                     + (f" | odd pages {st['odd']}: still correct {st['odd_kept']}, flipped BY the consensus {st['odd_flipped_by_job']}, sent to review {st['odd_rev']}" if scen == "mixed" else ""))
                for k, v in st.items():
                    tot[(scen, k)] = tot.get((scen, k), 0) + v
    for scen in ("clean", "mixed"):
        g = lambda k: tot[(scen, k)]
        emit(f"TOTAL {scen:6s} pages {g('n')}: flips {g('fb')} -> {g('fa')} | accepted flips {g('afb')} -> {g('afa')} | review {g('rb')} -> {g('ra')}"
             + (f" | odd {g('odd')}: correct after {g('odd_kept')}, flipped by consensus {g('odd_flipped_by_job')}, reviewed {g('odd_rev')}" if scen == "mixed" else ""))
    if a.out:
        open(a.out, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
