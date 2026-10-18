"""Pool several cells of a bench JSON into the tables used by reports/FINAL_REPORT.md.

  python -m bench.summarize reports/bench_final_v4_1.json > reports/FINAL_TABLES.md

Counts are rebuilt from the per-cell rates (rate x n), so the pooled numbers are exact sums, with Wilson 95 % intervals.
Cells of the same page pool share pages (the pool is wrapped when it has fewer unique pages than cases), so the intervals
are slightly optimistic; the per-cell table lists the unique page count.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict

from .metrics import wilson

PRIMARY_POOLS = ("az", "invoices", "tobacco_cert", "rvl_heldout")
EXTERNAL_POOLS = ("ext_funsd", "ext_doclaynet", "ext_cord")
BAD_SOURCE = {"certified_invoice_030.png"}      # source page is itself sideways (looked at it): its "flips" are correct


def _k(rate, n):
    return int(round(rate * n / 100.0))


def pooled(results, pools, levels=None):
    acc = defaultdict(lambda: defaultdict(float))
    for r in results:
        if r["dataset"] not in pools or (levels and r["level"] not in levels):
            continue
        s, c = r["summary"], r["candidate"]
        n = s["n"]
        a = acc[c]
        a["n"] += n
        a["flip"] += _k(s["flip"], n)
        a["le1"] += _k(s["le1"], n)
        a["le05"] += _k(s["le05"], n)
        a["gt5"] += _k(100.0 - s["le2"], n) if "le2" in s else 0
        a["review"] += _k(s["review_rate"], n)
        a["acc_flip"] += s.get("accepted_flip_n", 0)
        a["ms"] += s["ms_mean"] * n
        a["bad_src_flip"] += sum(1 for e in r["errors_gt5"] if e["file"] in BAD_SOURCE and e["pred"] is not None
                                 and abs((e["pred"] - e["gt"] + 180) % 360 - 180) > 45)
    return acc


def fmt_ci(k, n):
    lo, hi = wilson(int(k), int(n))
    return f"{100.0 * k / n:.2f} [{lo:.2f}–{hi:.2f}]"


def table(title, acc, order):
    if not any(c in acc for c in order):
        return ""
    out = [f"### {title}", "", "| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for c in order:
        if c not in acc:
            continue
        a = acc[c]
        n = a["n"]
        out.append(f"| {c} | {int(n)} | {fmt_ci(a['flip'], n)} | {fmt_ci(a['flip'] - a['bad_src_flip'], n)} | "
                   f"{100.0 * a['acc_flip'] / n:.2f} ({int(a['acc_flip'])}) | {100.0 * a['le1'] / n:.1f} | {100.0 * a['le05'] / n:.1f} | "
                   f"{100.0 * a['review'] / n:.1f} | {a['ms'] / n:.0f} |")
    return "\n".join(out) + "\n"


def main(path):
    d = json.load(open(path))
    res = d["results"]
    order = [c for c in dict.fromkeys(r["candidate"] for r in res)]
    m = d["manifest"]
    print(f"Source: `{path}` — commit `{m['git_commit']}`{' (dirty)' if m['git_dirty'] else ''}, {m['cpu']}, {m['cores']} cores, "
          f"opencv {m['opencv']}, onnxruntime {m['onnxruntime']}, python {m['python']}.\n")
    modes = d["args"].get("angle_modes", ["uniform"])
    what = {"uniform": "uniformly random angles in [-180°, 180°]", "quad_tilt": "a random quadrant (0/90/180/270) plus a tilt of up to ±25°"}
    print("Simulated photographs of known pages at " + " and ".join(what.get(m, m) for m in modes) + "; flip = error > 45°. "
          "'accepted' = the page was NOT sent to review.\n")
    for lv in ("scan", "photo_easy", "photo_hard"):
        print(table(f"Primary pools (az, invoices, tobacco_cert, rvl_heldout) — {lv}", pooled(res, PRIMARY_POOLS, {lv}), order))
    print(table("Primary pools — all levels", pooled(res, PRIMARY_POOLS), order))
    print(table("External held-out pools (FUNSD scans, DocLayNet pages, CORD receipt photos) — all levels", pooled(res, EXTERNAL_POOLS), order))
    for pool in PRIMARY_POOLS + EXTERNAL_POOLS:
        print(table(f"{pool} — all levels", pooled(res, (pool,)), order))
    print("### Per cell\n")
    print("| pool | level | candidate | cases (unique pages) | median ° | ≤1° % [95% CI] | flips % [95% CI] | review % | accepted flips % | ms |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in res:
        s = r["summary"]
        if "median" not in s:
            continue
        print(f"| {r['dataset']} | {r['level']} | {r['candidate']} | {s['n']} ({r['unique_pages']}) | {s['median']:.2f} | "
              f"{s['le1']:.1f} [{s['le1_ci'][0]:.1f}–{s['le1_ci'][1]:.1f}] | {s['flip']:.1f} [{s['flip_ci'][0]:.1f}–{s['flip_ci'][1]:.1f}] | "
              f"{s['review_rate']:.1f} | {s.get('accepted_flip', float('nan')):.1f} | {s['ms_mean']:.0f} |")


if __name__ == "__main__":
    main(sys.argv[1])
