"""Evaluate candidates on a directory of real photos labeled with tools/label_server.py.

  python -m bench.eval_labeled PHOTO_DIR labels.jsonl --candidates docangle legacy_v1
"""
import argparse
import json
import os

import cv2

from .candidates import REGISTRY
from .metrics import circ_err, risk_coverage, summarize
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo_dir"); ap.add_argument("labels")
    ap.add_argument("--candidates", nargs="+", default=["docangle"], choices=list(REGISTRY))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    lab = {}
    for line in open(a.labels, encoding="utf-8"):
        r = json.loads(line)
        if r.get("deleted"): lab.pop(r["file"], None)
        else: lab[r["file"]] = r
    items = [(f, r["angle"]) for f, r in lab.items() if r.get("status") == "ok"]
    print(f"{len(items)} labeled photos ({len(lab) - len(items)} skipped/no-text)")
    res = {}
    for name in a.candidates:
        fn, _ = REGISTRY[name]()
        recs = []
        for f, gt in items:
            img = cv2.imread(os.path.join(a.photo_dir, f))
            t0 = time.perf_counter(); r = fn(img); r.update(gt=gt, ms=(time.perf_counter() - t0) * 1000, file=f); recs.append(r)
        s = summarize(recs); res[name] = {"summary": s, "risk_coverage": risk_coverage(recs),
                                          "errors_gt2": [(r["file"], r["gt"], r["pred"], round(r["conf"], 2), r["review"]) for r in recs
                                                         if r["pred"] is None or circ_err(r["pred"], r["gt"]) > 2.0]}
        print(name, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items() if k in
                     ("n", "median", "le1", "flip", "flip_ci", "review_rate", "accepted_flip", "ms_mean")})
    if a.out: json.dump(res, open(a.out, "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
