Source: `reports/bench_final_v4_1_quadtilt.json` — commit `f4fcb38` (dirty), AMD Ryzen 9 5980HX with Radeon Graphics, 16 cores, opencv 4.14.0, onnxruntime 1.31.0, python 3.14.6.

Simulated photographs of known pages at a random quadrant (0/90/180/270) plus a tilt of up to ±25°; flip = error > 45°. 'accepted' = the page was NOT sent to review.

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — scan

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 800 | 0.25 [0.07–0.91] | 0.00 [0.00–0.48] | 0.25 (2) | 94.0 | 76.0 | 0.4 | 41 |
| legacy_v1 | 800 | 2.75 [1.82–4.13] | 2.50 [1.62–3.83] | 2.75 (22) | 92.5 | 79.2 | 0.0 | 35 |

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — photo_easy

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 800 | 0.62 [0.27–1.45] | 0.38 [0.13–1.10] | 0.38 (3) | 94.0 | 78.0 | 1.1 | 39 |
| legacy_v1 | 800 | 3.75 [2.64–5.30] | 3.62 [2.54–5.16] | 3.75 (30) | 91.2 | 76.2 | 0.0 | 33 |

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — photo_hard

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 800 | 0.38 [0.13–1.10] | 0.12 [0.02–0.70] | 0.25 (2) | 93.0 | 79.6 | 1.8 | 38 |
| legacy_v1 | 800 | 4.75 [3.48–6.45] | 4.50 [3.27–6.17] | 4.75 (38) | 88.4 | 73.8 | 0.0 | 33 |

### Primary pools — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 2400 | 0.42 [0.23–0.77] | 0.17 [0.06–0.43] | 0.29 (7) | 93.7 | 77.9 | 1.1 | 39 |
| legacy_v1 | 2400 | 3.75 [3.06–4.59] | 3.54 [2.87–4.36] | 3.75 (90) | 90.7 | 76.4 | 0.0 | 34 |


### az — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 600 | 0.17 [0.03–0.94] | 0.17 [0.03–0.94] | 0.00 (0) | 99.8 | 98.7 | 0.2 | 42 |
| legacy_v1 | 600 | 0.17 [0.03–0.94] | 0.17 [0.03–0.94] | 0.17 (1) | 99.8 | 98.8 | 0.0 | 35 |

### invoices — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 600 | 1.17 [0.57–2.39] | 0.17 [0.03–0.94] | 1.00 (6) | 94.2 | 75.8 | 2.3 | 37 |
| legacy_v1 | 600 | 8.33 [6.38–10.82] | 7.50 [5.65–9.89] | 8.33 (50) | 87.8 | 73.5 | 0.0 | 32 |

### tobacco_cert — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 600 | 0.00 [0.00–0.64] | 0.00 [0.00–0.64] | 0.00 (0) | 92.0 | 70.2 | 0.3 | 39 |
| legacy_v1 | 600 | 0.83 [0.36–1.94] | 0.83 [0.36–1.94] | 0.83 (5) | 91.5 | 70.2 | 0.0 | 32 |

### rvl_heldout — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 600 | 0.33 [0.09–1.21] | 0.33 [0.09–1.21] | 0.17 (1) | 88.7 | 66.8 | 1.5 | 38 |
| legacy_v1 | 600 | 5.67 [4.08–7.81] | 5.67 [4.08–7.81] | 5.67 (34) | 83.7 | 63.2 | 0.0 | 35 |




### Per cell

| pool | level | candidate | cases (unique pages) | median ° | ≤1° % [95% CI] | flips % [95% CI] | review % | accepted flips % | ms |
|---|---|---|---|---|---|---|---|---|---|
| az | scan | docangle | 200 (100) | 0.12 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 45 |
| az | scan | legacy_v1 | 200 (100) | 0.12 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.0 | 0.5 | 40 |
| az | photo_easy | docangle | 200 (100) | 0.14 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 41 |
| az | photo_easy | legacy_v1 | 200 (100) | 0.15 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 33 |
| az | photo_hard | docangle | 200 (100) | 0.16 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5 | 0.0 | 40 |
| az | photo_hard | legacy_v1 | 200 (100) | 0.16 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 32 |
| invoices | scan | docangle | 200 (100) | 0.30 | 95.0 [91.0–97.3] | 1.0 [0.3–3.6] | 1.0 | 1.0 | 38 |
| invoices | scan | legacy_v1 | 200 (100) | 0.25 | 93.0 [88.6–95.8] | 4.0 [2.0–7.7] | 0.0 | 4.0 | 31 |
| invoices | photo_easy | docangle | 200 (100) | 0.30 | 94.5 [90.4–96.9] | 1.5 [0.5–4.3] | 2.5 | 1.0 | 37 |
| invoices | photo_easy | legacy_v1 | 200 (100) | 0.28 | 86.5 [81.1–90.6] | 10.5 [7.0–15.5] | 0.0 | 10.5 | 32 |
| invoices | photo_hard | docangle | 200 (100) | 0.27 | 93.0 [88.6–95.8] | 1.0 [0.3–3.6] | 3.5 | 1.0 | 36 |
| invoices | photo_hard | legacy_v1 | 200 (100) | 0.30 | 84.0 [78.3–88.4] | 10.5 [7.0–15.5] | 0.0 | 10.5 | 34 |
| tobacco_cert | scan | docangle | 200 (159) | 0.28 | 93.0 [88.6–95.8] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 41 |
| tobacco_cert | scan | legacy_v1 | 200 (159) | 0.26 | 91.5 [86.8–94.6] | 0.0 [0.0–1.9] | 0.0 | 0.0 | 33 |
| tobacco_cert | photo_easy | docangle | 200 (159) | 0.26 | 92.0 [87.4–95.0] | 0.0 [0.0–1.9] | 0.5 | 0.0 | 39 |
| tobacco_cert | photo_easy | legacy_v1 | 200 (159) | 0.27 | 92.0 [87.4–95.0] | 0.5 [0.1–2.8] | 0.0 | 0.5 | 32 |
| tobacco_cert | photo_hard | docangle | 200 (159) | 0.29 | 91.0 [86.2–94.2] | 0.0 [0.0–1.9] | 0.5 | 0.0 | 38 |
| tobacco_cert | photo_hard | legacy_v1 | 200 (159) | 0.31 | 91.0 [86.2–94.2] | 2.0 [0.8–5.0] | 0.0 | 2.0 | 31 |
| rvl_heldout | scan | docangle | 200 (200) | 0.33 | 88.0 [82.8–91.8] | 0.0 [0.0–1.9] | 0.5 | 0.0 | 39 |
| rvl_heldout | scan | legacy_v1 | 200 (200) | 0.31 | 86.0 [80.5–90.1] | 6.5 [3.8–10.8] | 0.0 | 6.5 | 35 |
| rvl_heldout | photo_easy | docangle | 200 (200) | 0.34 | 89.5 [84.5–93.0] | 1.0 [0.3–3.6] | 1.5 | 0.5 | 38 |
| rvl_heldout | photo_easy | legacy_v1 | 200 (200) | 0.35 | 86.5 [81.1–90.6] | 4.0 [2.0–7.7] | 0.0 | 4.0 | 35 |
| rvl_heldout | photo_hard | docangle | 200 (200) | 0.28 | 88.5 [83.3–92.2] | 0.0 [0.0–1.9] | 2.5 | 0.0 | 37 |
| rvl_heldout | photo_hard | legacy_v1 | 200 (200) | 0.38 | 78.5 [72.3–83.6] | 6.5 [3.8–10.8] | 0.0 | 6.5 | 34 |
