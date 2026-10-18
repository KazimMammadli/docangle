"""Benchmark runner.

  python -m bench.run --datasets az invoices tobacco_cert --levels scan photo_easy photo_hard \
        --angle-modes uniform quad_tilt --seeds 3 --n 100 --candidates docangle legacy_v1

Writes reports/bench_<timestamp>.json and a Markdown summary. Every number in the summary carries n
and a 95 % interval; the file records git commit, versions, hardware and config.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import platform
import subprocess
import time
import zlib
from datetime import datetime

import cv2
import numpy as np

from . import datasets
from .candidates import REGISTRY
from .degrade import LEVELS, render, sample_angle
from .metrics import circ_err, risk_coverage, summarize
from docangle import upright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def manifest():
    def sh(*a):
        try:
            return subprocess.check_output(a, cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            return None
    import onnxruntime
    cpu = None
    try:
        cpu = next(l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
    except Exception:
        pass
    return {"git_commit": sh("git", "rev-parse", "--short", "HEAD"), "git_dirty": bool(sh("git", "status", "--porcelain")),
            "python": platform.python_version(), "opencv": cv2.__version__, "onnxruntime": onnxruntime.__version__,
            "numpy": np.__version__, "cpu": cpu, "cores": os.cpu_count(), "os": platform.platform()}


def make_cases(dataset, level, angle_mode, seeds, n, seed_start=0):
    files = datasets.pool(dataset)
    cases, wrapped = [], False
    for s in range(seed_start, seed_start + seeds):
        chosen, w = datasets.pick(files, n, s)
        wrapped |= w
        for i, f in enumerate(chosen):
            rng = np.random.default_rng([zlib.crc32(f"{dataset}/{level}/{angle_mode}".encode()) & 0xFFFFFF, s, i])  # stable across processes
            cases.append((f, s, i, rng))
    return cases, len(set(f for f, *_ in cases)), wrapped


def save_failure(root, cand, ds, lv, idx, page, img, gt, r):
    """Contact tile for one large error: degraded input | our output | source page (what GT claims is upright)."""
    H = 360

    def tile(a, text):
        a = cv2.cvtColor(a, cv2.COLOR_GRAY2BGR) if a.ndim == 2 else a
        k = H / a.shape[0]
        t = cv2.resize(a, (max(8, int(a.shape[1] * k)), H), interpolation=cv2.INTER_AREA)
        cv2.putText(t, text, (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
        return cv2.copyMakeBorder(t, 0, 0, 0, 3, cv2.BORDER_CONSTANT, value=(0, 0, 255))
    try:
        out = upright(img, r["pred"])
    except Exception:
        out = img
    cap = f"{r['file'][:24]} gt {gt:+.1f} pred {r['pred']:+.1f} conf {r['conf']:.2f}{' REVIEW' if r['review'] else ''}"
    row = np.hstack([tile(img, "input"), tile(out, cap), tile(page, "source page (GT: upright)")])
    os.makedirs(root, exist_ok=True)
    cv2.imwrite(os.path.join(root, f"{cand}_{ds}_{lv}_{idx:03d}.jpg"), row, [cv2.IMWRITE_JPEG_QUALITY, 70])


def run(args):
    out = {"manifest": manifest(), "args": vars(args), "results": []}
    gal_n = {}
    cands = {}
    for name in args.candidates:
        fn, cfg = REGISTRY[name]()
        cands[name] = (fn, dataclasses.asdict(cfg) if dataclasses.is_dataclass(cfg) else cfg)
    for ds in args.datasets:
        for lv in args.levels:
            for am in args.angle_modes:
                cases, uniq, wrapped = make_cases(ds, lv, am, args.seeds, args.n)
                print(f"== {ds} / {lv} / {am}: {len(cases)} cases, {uniq} unique pages{' (pool wrapped)' if wrapped else ''}", flush=True)
                recs = {c: [] for c in cands}
                for f, s, i, rng in cases:
                    page = cv2.imread(f)
                    gt = sample_angle(am, rng)
                    img = render(page, gt, LEVELS[lv], rng)
                    for c, (fn, _) in cands.items():
                        t0 = time.perf_counter()
                        try:
                            r = fn(img)
                        except Exception as e:  # a crash is a result, not an excuse to stop
                            r = {"pred": None, "conf": 0.0, "review": True, "error": repr(e)[:80]}
                        r.update(gt=gt, ms=(time.perf_counter() - t0) * 1000.0, file=os.path.basename(f), seed=s)
                        recs[c].append(r)
                        if args.gallery and c == args.candidates[0] and r["pred"] is not None and circ_err(r["pred"], gt) > 5.0 and gal_n.get((c, ds, lv), 0) < 25:
                            gal_n[(c, ds, lv)] = gal_n.get((c, ds, lv), 0) + 1
                            save_failure(os.path.join(ROOT, args.gallery), c, ds, lv, gal_n[(c, ds, lv)], page, img, gt, r)
                for c, rs in recs.items():
                    summ = summarize(rs)
                    bad = [dict(file=r["file"], gt=r["gt"], pred=r["pred"], conf=round(r["conf"], 3), review=r["review"])
                           for r in rs if r["pred"] is not None and circ_err(r["pred"], r["gt"]) > 5.0][:40]
                    out["results"].append({"dataset": ds, "level": lv, "angle_mode": am, "candidate": c,
                                           "unique_pages": uniq, "pool_wrapped": wrapped, "summary": summ,
                                           "fallback_triggers": sum(1 for r in rs if r.get("fallback")),
                                           "risk_coverage": risk_coverage(rs), "config": cands[c][1], "errors_gt5": bad})
                    s_ = summ
                    print(f"  {c:14s} n={s_['n']} med={s_.get('median', float('nan')):.2f} le1={s_.get('le1', float('nan')):.1f}% "
                          f"flip={s_.get('flip', float('nan')):.1f}% (acc.flip={s_.get('accepted_flip', float('nan')):.1f}% "
                          f"review={s_.get('review_rate', float('nan')):.1f}%) ms={s_.get('ms_mean', float('nan')):.0f}", flush=True)
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(ROOT, "reports", f"bench_{args.tag or stamp}.json")
    json.dump(out, open(path, "w"), indent=1, default=lambda o: None if o != o else o)
    md = to_markdown(out)
    open(path.replace(".json", ".md"), "w").write(md)
    print("wrote", path)
    return out


def to_markdown(out):
    m = out["manifest"]
    lines = [f"# Benchmark {out['args'].get('tag') or ''}", "",
             f"commit `{m['git_commit']}`{' (dirty)' if m['git_dirty'] else ''} · {m['cpu']} · {m['cores']} cores · "
             f"opencv {m['opencv']} · ort {m['onnxruntime']} · python {m['python']}", "",
             "| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in out["results"]:
        s = r["summary"]
        if "median" not in s:
            continue
        ci = lambda k: f"[{s[k][0]:.1f}–{s[k][1]:.1f}]"
        lines.append(f"| {r['dataset']} | {r['level']} | {r['angle_mode']} | {r['candidate']} | {s['n']} ({r['unique_pages']}) | "
                     f"{s['median']:.2f} | {s['le1']:.1f} {ci('le1_ci')} | {s['flip']:.1f} {ci('flip_ci')} | "
                     f"{s['flip180']:.1f}/{s['flip90']:.1f} | {s['review_rate']:.1f} | "
                     f"{s.get('accepted_flip', float('nan')):.1f} | {s['ms_mean']:.0f} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["az"])
    ap.add_argument("--levels", nargs="+", default=["scan"], choices=list(LEVELS))
    ap.add_argument("--angle-modes", nargs="+", default=["uniform"])
    ap.add_argument("--candidates", nargs="+", default=["docangle"], choices=list(REGISTRY))
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--gallery", default=None, help="directory (relative to repo) for failure tiles of errors > 5 deg")
    run(ap.parse_args())
