Source: `reports/bench_final_v4_3_quadtilt.json` — commit `c2ef759` (dirty), AMD Ryzen 9 5980HX with Radeon Graphics, 16 cores, opencv 4.14.0, onnxruntime 1.31.0, python 3.14.6.

Simulated photographs of known pages at a random quadrant (0/90/180/270) plus a tilt of up to ±25°; flip = error > 45°. 'accepted' = the page was NOT sent to review.

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — scan

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 800 | 0.25 [0.07–0.91] | 0.00 [0.00–0.48] | 0.25 (2) | 94.2 | 81.0 | 1.0 | 28 |

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — photo_easy

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 800 | 0.62 [0.27–1.45] | 0.38 [0.13–1.10] | 0.25 (2) | 95.6 | 87.4 | 1.4 | 28 |

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — photo_hard

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 800 | 0.50 [0.19–1.28] | 0.25 [0.07–0.91] | 0.25 (2) | 96.5 | 89.0 | 1.2 | 28 |

### Primary pools — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 2400 | 0.46 [0.26–0.82] | 0.21 [0.09–0.49] | 0.25 (6) | 95.5 | 85.8 | 1.2 | 28 |


### az — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 600 | 0.17 [0.03–0.94] | 0.17 [0.03–0.94] | 0.00 (0) | 99.8 | 99.8 | 0.2 | 28 |

### invoices — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 600 | 1.17 [0.57–2.39] | 0.17 [0.03–0.94] | 1.00 (6) | 95.2 | 84.2 | 2.7 | 27 |

### tobacco_cert — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 600 | 0.00 [0.00–0.64] | 0.00 [0.00–0.64] | 0.00 (0) | 95.8 | 85.8 | 0.0 | 28 |

### rvl_heldout — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 600 | 0.50 [0.17–1.46] | 0.50 [0.17–1.46] | 0.00 (0) | 91.0 | 73.3 | 2.0 | 28 |




### Per cell

| pool | level | candidate | cases (unique pages) | median ° | ≤1° % [95% CI] | flips % [95% CI] | review % | accepted flips % | ms |
|---|---|---|---|---|---|---|---|---|---|
| az | scan | docangle | 200 (100) | 0.01 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 29 |
| az | photo_easy | docangle | 200 (100) | 0.01 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 28 |
| az | photo_hard | docangle | 200 (100) | 0.01 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5 | 0.0 | 28 |
| invoices | scan | docangle | 200 (100) | 0.24 | 94.5 [90.4–96.9] | 1.0 [0.3–3.6] | 1.5 | 1.0 | 27 |
| invoices | photo_easy | docangle | 200 (100) | 0.14 | 95.5 [91.7–97.6] | 1.5 [0.5–4.3] | 4.0 | 1.0 | 28 |
| invoices | photo_hard | docangle | 200 (100) | 0.11 | 95.5 [91.7–97.6] | 1.0 [0.3–3.6] | 2.5 | 1.0 | 28 |
| tobacco_cert | scan | docangle | 200 (159) | 0.23 | 92.5 [88.0–95.4] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 28 |
| tobacco_cert | photo_easy | docangle | 200 (159) | 0.11 | 96.5 [93.0–98.3] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 28 |
| tobacco_cert | photo_hard | docangle | 200 (159) | 0.08 | 98.5 [95.7–99.5] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 28 |
| rvl_heldout | scan | docangle | 200 (200) | 0.27 | 90.0 [85.1–93.4] | 0.0 [0.0–1.9] | 2.5 | 0.0 | 28 |
| rvl_heldout | photo_easy | docangle | 200 (200) | 0.13 | 90.5 [85.6–93.8] | 1.0 [0.3–3.6] | 1.5 | 0.0 | 28 |
| rvl_heldout | photo_hard | docangle | 200 (200) | 0.08 | 92.5 [88.0–95.4] | 0.5 [0.1–2.8] | 2.0 | 0.0 | 27 |
