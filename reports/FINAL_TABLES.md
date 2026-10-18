Source: `reports/bench_final_v4_1.json` — commit `f4fcb38` (dirty), AMD Ryzen 9 5980HX with Radeon Graphics, 16 cores, opencv 4.14.0, onnxruntime 1.31.0, python 3.14.6.

Simulated photographs of known pages at uniformly random angles in [-180°, 180°]; flip = error > 45°. 'accepted' = the page was NOT sent to review.

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — scan

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 1200 | 0.42 [0.18–0.97] | 0.17 [0.05–0.61] | 0.25 (3) | 94.6 | 78.3 | 0.6 | 40 |
| docangle_precise | 1200 | 0.42 [0.18–0.97] | 0.17 [0.05–0.61] | 0.25 (3) | 94.8 | 79.9 | 0.6 | 50 |
| docangle_full | 1200 | 0.42 [0.18–0.97] | 0.17 [0.05–0.61] | 0.25 (3) | 94.6 | 78.3 | 0.7 | 65 |
| legacy_v1 | 1200 | 3.00 [2.17–4.13] | 2.75 [1.96–3.84] | 3.00 (36) | 92.5 | 79.8 | 0.0 | 38 |

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — photo_easy

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 1200 | 0.58 [0.28–1.20] | 0.33 [0.13–0.85] | 0.25 (3) | 93.5 | 78.8 | 1.2 | 39 |
| docangle_precise | 1200 | 0.58 [0.28–1.20] | 0.33 [0.13–0.85] | 0.25 (3) | 92.2 | 78.6 | 1.2 | 49 |
| docangle_full | 1200 | 0.50 [0.23–1.09] | 0.25 [0.09–0.73] | 0.25 (3) | 93.6 | 78.8 | 1.2 | 64 |
| legacy_v1 | 1200 | 4.50 [3.47–5.83] | 4.25 [3.25–5.54] | 4.50 (54) | 89.8 | 75.8 | 0.0 | 38 |

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — photo_hard

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 1200 | 0.50 [0.23–1.09] | 0.25 [0.09–0.73] | 0.42 (5) | 93.7 | 80.2 | 1.8 | 38 |
| docangle_precise | 1200 | 0.50 [0.23–1.09] | 0.25 [0.09–0.73] | 0.42 (5) | 91.9 | 80.6 | 1.8 | 48 |
| docangle_full | 1200 | 0.50 [0.23–1.09] | 0.25 [0.09–0.73] | 0.42 (5) | 93.7 | 80.2 | 1.6 | 63 |
| legacy_v1 | 1200 | 6.00 [4.79–7.49] | 5.75 [4.57–7.21] | 6.00 (72) | 86.9 | 73.8 | 0.0 | 38 |

### Primary pools — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 3600 | 0.50 [0.32–0.79] | 0.25 [0.13–0.47] | 0.31 (11) | 93.9 | 79.1 | 1.2 | 39 |
| docangle_precise | 3600 | 0.50 [0.32–0.79] | 0.25 [0.13–0.47] | 0.31 (11) | 93.0 | 79.7 | 1.2 | 49 |
| docangle_full | 3600 | 0.47 [0.30–0.75] | 0.22 [0.11–0.44] | 0.31 (11) | 93.9 | 79.1 | 1.2 | 64 |
| legacy_v1 | 3600 | 4.50 [3.87–5.23] | 4.25 [3.64–4.96] | 4.50 (162) | 89.8 | 76.5 | 0.0 | 38 |

### External held-out pools (FUNSD scans, DocLayNet pages, CORD receipt photos) — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 2700 | 2.37 [1.86–3.02] | 2.37 [1.86–3.02] | 0.44 (12) | 85.9 | 71.7 | 11.1 | 38 |
| docangle_precise | 2700 | 2.37 [1.86–3.02] | 2.37 [1.86–3.02] | 0.44 (12) | 85.3 | 73.3 | 11.1 | 48 |
| docangle_full | 2700 | 2.19 [1.70–2.81] | 2.19 [1.70–2.81] | 0.26 (7) | 86.0 | 71.8 | 11.3 | 63 |
| legacy_v1 | 2700 | 16.07 [14.74–17.51] | 16.07 [14.74–17.51] | 16.07 (434) | 75.9 | 63.9 | 0.0 | 37 |

### az — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 99.9 | 99.3 | 0.2 | 41 |
| docangle_precise | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 98.3 | 96.8 | 0.2 | 51 |
| docangle_full | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 99.9 | 99.3 | 0.2 | 66 |
| legacy_v1 | 900 | 0.33 [0.11–0.98] | 0.33 [0.11–0.98] | 0.33 (3) | 99.7 | 99.1 | 0.0 | 35 |

### invoices — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 1.56 [0.93–2.59] | 0.56 [0.24–1.29] | 1.11 (10) | 94.3 | 75.2 | 2.3 | 38 |
| docangle_precise | 900 | 1.56 [0.93–2.59] | 0.56 [0.24–1.29] | 1.11 (10) | 93.2 | 77.8 | 2.3 | 48 |
| docangle_full | 900 | 1.44 [0.85–2.46] | 0.44 [0.17–1.14] | 1.11 (10) | 94.4 | 75.3 | 1.9 | 63 |
| legacy_v1 | 900 | 8.89 [7.20–10.93] | 7.89 [6.30–9.83] | 8.89 (80) | 87.2 | 71.3 | 0.0 | 40 |

### tobacco_cert — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 92.2 | 74.1 | 0.6 | 39 |
| docangle_precise | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 90.8 | 73.6 | 0.6 | 49 |
| docangle_full | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 92.2 | 74.1 | 0.6 | 64 |
| legacy_v1 | 900 | 1.56 [0.93–2.59] | 1.56 [0.93–2.59] | 1.56 (14) | 89.3 | 72.7 | 0.0 | 36 |

### rvl_heldout — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 0.44 [0.17–1.14] | 0.44 [0.17–1.14] | 0.11 (1) | 89.2 | 67.7 | 1.7 | 38 |
| docangle_precise | 900 | 0.44 [0.17–1.14] | 0.44 [0.17–1.14] | 0.11 (1) | 89.6 | 70.7 | 1.7 | 48 |
| docangle_full | 900 | 0.44 [0.17–1.14] | 0.44 [0.17–1.14] | 0.11 (1) | 89.2 | 67.6 | 2.0 | 63 |
| legacy_v1 | 900 | 7.22 [5.71–9.10] | 7.22 [5.71–9.10] | 7.22 (65) | 82.8 | 62.9 | 0.0 | 42 |

### ext_funsd — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 91.1 | 68.2 | 0.7 | 38 |
| docangle_precise | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 90.8 | 69.8 | 0.7 | 48 |
| docangle_full | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 91.1 | 68.2 | 0.7 | 63 |
| legacy_v1 | 900 | 1.67 [1.01–2.73] | 1.67 [1.01–2.73] | 1.67 (15) | 89.8 | 67.2 | 0.0 | 36 |

### ext_doclaynet — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 3.11 [2.16–4.46] | 3.11 [2.16–4.46] | 1.00 (9) | 95.6 | 93.6 | 4.6 | 44 |
| docangle_precise | 900 | 3.11 [2.16–4.46] | 3.11 [2.16–4.46] | 1.00 (9) | 94.4 | 91.3 | 4.6 | 54 |
| docangle_full | 900 | 2.78 [1.89–4.07] | 2.78 [1.89–4.07] | 0.56 (5) | 95.8 | 93.9 | 5.0 | 68 |
| legacy_v1 | 900 | 5.22 [3.95–6.88] | 5.22 [3.95–6.88] | 5.22 (47) | 93.2 | 91.1 | 0.0 | 40 |

### ext_cord — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 4.00 [2.90–5.49] | 4.00 [2.90–5.49] | 0.33 (3) | 70.9 | 53.2 | 28.0 | 33 |
| docangle_precise | 900 | 4.00 [2.90–5.49] | 4.00 [2.90–5.49] | 0.33 (3) | 70.6 | 58.9 | 28.0 | 42 |
| docangle_full | 900 | 3.78 [2.72–5.23] | 3.78 [2.72–5.23] | 0.22 (2) | 71.1 | 53.3 | 28.3 | 58 |
| legacy_v1 | 900 | 41.33 [38.16–44.58] | 41.33 [38.16–44.58] | 41.33 (372) | 44.7 | 33.2 | 0.0 | 37 |

### Per cell

| pool | level | candidate | cases (unique pages) | median ° | ≤1° % [95% CI] | flips % [95% CI] | review % | accepted flips % | ms |
|---|---|---|---|---|---|---|---|---|---|
| az | scan | docangle | 300 (100) | 0.14 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 44 |
| az | scan | docangle_precise | 300 (100) | 0.13 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 53 |
| az | scan | docangle_full | 300 (100) | 0.14 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 68 |
| az | scan | legacy_v1 | 300 (100) | 0.14 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 36 |
| az | photo_easy | docangle | 300 (100) | 0.14 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 41 |
| az | photo_easy | docangle_precise | 300 (100) | 0.14 | 97.3 [94.8–98.6] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 50 |
| az | photo_easy | docangle_full | 300 (100) | 0.14 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 65 |
| az | photo_easy | legacy_v1 | 300 (100) | 0.14 | 99.7 [98.1–99.9] | 0.3 [0.1–1.9] | 0.0 | 0.3 | 33 |
| az | photo_hard | docangle | 300 (100) | 0.17 | 99.7 [98.1–99.9] | 0.0 [0.0–1.3] | 0.7 | 0.0 | 39 |
| az | photo_hard | docangle_precise | 300 (100) | 0.16 | 97.7 [95.3–98.9] | 0.0 [0.0–1.3] | 0.7 | 0.0 | 49 |
| az | photo_hard | docangle_full | 300 (100) | 0.17 | 99.7 [98.1–99.9] | 0.0 [0.0–1.3] | 0.7 | 0.0 | 64 |
| az | photo_hard | legacy_v1 | 300 (100) | 0.15 | 99.3 [97.6–99.8] | 0.7 [0.2–2.4] | 0.0 | 0.7 | 34 |
| invoices | scan | docangle | 300 (100) | 0.28 | 95.0 [91.9–96.9] | 1.3 [0.5–3.4] | 1.0 | 1.0 | 38 |
| invoices | scan | docangle_precise | 300 (100) | 0.27 | 94.7 [91.5–96.7] | 1.3 [0.5–3.4] | 1.0 | 1.0 | 48 |
| invoices | scan | docangle_full | 300 (100) | 0.28 | 95.3 [92.3–97.2] | 1.0 [0.3–2.9] | 1.0 | 1.0 | 63 |
| invoices | scan | legacy_v1 | 300 (100) | 0.25 | 92.3 [88.8–94.8] | 6.3 [4.1–9.7] | 0.0 | 6.3 | 39 |
| invoices | photo_easy | docangle | 300 (100) | 0.27 | 94.3 [91.1–96.4] | 1.7 [0.7–3.8] | 2.3 | 1.0 | 38 |
| invoices | photo_easy | docangle_precise | 300 (100) | 0.25 | 93.3 [89.9–95.6] | 1.7 [0.7–3.8] | 2.3 | 1.0 | 48 |
| invoices | photo_easy | docangle_full | 300 (100) | 0.27 | 94.3 [91.1–96.4] | 1.7 [0.7–3.8] | 2.0 | 1.0 | 63 |
| invoices | photo_easy | legacy_v1 | 300 (100) | 0.30 | 87.0 [82.7–90.3] | 9.3 [6.5–13.2] | 0.0 | 9.3 | 40 |
| invoices | photo_hard | docangle | 300 (100) | 0.26 | 93.7 [90.3–95.9] | 1.7 [0.7–3.8] | 3.7 | 1.4 | 37 |
| invoices | photo_hard | docangle_precise | 300 (100) | 0.21 | 91.7 [88.0–94.3] | 1.7 [0.7–3.8] | 3.7 | 1.4 | 47 |
| invoices | photo_hard | docangle_full | 300 (100) | 0.26 | 93.7 [90.3–95.9] | 1.7 [0.7–3.8] | 2.7 | 1.4 | 62 |
| invoices | photo_hard | legacy_v1 | 300 (100) | 0.31 | 82.3 [77.6–86.2] | 11.0 [7.9–15.0] | 0.0 | 11.0 | 42 |
| tobacco_cert | scan | docangle | 300 (159) | 0.29 | 93.0 [89.5–95.4] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 40 |
| tobacco_cert | scan | docangle_precise | 300 (159) | 0.28 | 92.7 [89.1–95.1] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 50 |
| tobacco_cert | scan | docangle_full | 300 (159) | 0.29 | 93.0 [89.5–95.4] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 65 |
| tobacco_cert | scan | legacy_v1 | 300 (159) | 0.25 | 91.0 [87.2–93.7] | 0.7 [0.2–2.4] | 0.0 | 0.7 | 36 |
| tobacco_cert | photo_easy | docangle | 300 (159) | 0.29 | 91.7 [88.0–94.3] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 39 |
| tobacco_cert | photo_easy | docangle_precise | 300 (159) | 0.28 | 89.3 [85.3–92.3] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 49 |
| tobacco_cert | photo_easy | docangle_full | 300 (159) | 0.29 | 91.7 [88.0–94.3] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 64 |
| tobacco_cert | photo_easy | legacy_v1 | 300 (159) | 0.29 | 88.7 [84.6–91.8] | 1.7 [0.7–3.8] | 0.0 | 1.7 | 37 |
| tobacco_cert | photo_hard | docangle | 300 (159) | 0.26 | 92.0 [88.4–94.6] | 0.0 [0.0–1.3] | 1.0 | 0.0 | 38 |
| tobacco_cert | photo_hard | docangle_precise | 300 (159) | 0.27 | 90.3 [86.5–93.2] | 0.0 [0.0–1.3] | 1.0 | 0.0 | 48 |
| tobacco_cert | photo_hard | docangle_full | 300 (159) | 0.26 | 92.0 [88.4–94.6] | 0.0 [0.0–1.3] | 1.0 | 0.0 | 63 |
| tobacco_cert | photo_hard | legacy_v1 | 300 (159) | 0.31 | 88.3 [84.2–91.5] | 2.3 [1.1–4.7] | 0.0 | 2.3 | 36 |
| rvl_heldout | scan | docangle | 300 (300) | 0.32 | 90.3 [86.5–93.2] | 0.3 [0.1–1.9] | 1.0 | 0.0 | 39 |
| rvl_heldout | scan | docangle_precise | 300 (300) | 0.29 | 91.7 [88.0–94.3] | 0.3 [0.1–1.9] | 1.0 | 0.0 | 49 |
| rvl_heldout | scan | docangle_full | 300 (300) | 0.32 | 90.0 [86.1–92.9] | 0.7 [0.2–2.4] | 1.3 | 0.0 | 64 |
| rvl_heldout | scan | legacy_v1 | 300 (300) | 0.29 | 86.7 [82.4–90.1] | 5.0 [3.1–8.1] | 0.0 | 5.0 | 42 |
| rvl_heldout | photo_easy | docangle | 300 (300) | 0.28 | 88.0 [83.8–91.2] | 0.7 [0.2–2.4] | 2.0 | 0.0 | 38 |
| rvl_heldout | photo_easy | docangle_precise | 300 (300) | 0.26 | 89.0 [85.0–92.1] | 0.7 [0.2–2.4] | 2.0 | 0.0 | 48 |
| rvl_heldout | photo_easy | docangle_full | 300 (300) | 0.28 | 88.3 [84.2–91.5] | 0.3 [0.1–1.9] | 2.7 | 0.0 | 63 |
| rvl_heldout | photo_easy | legacy_v1 | 300 (300) | 0.30 | 84.0 [79.4–87.7] | 6.7 [4.4–10.1] | 0.0 | 6.7 | 41 |
| rvl_heldout | photo_hard | docangle | 300 (300) | 0.30 | 89.3 [85.3–92.3] | 0.3 [0.1–1.9] | 2.0 | 0.3 | 38 |
| rvl_heldout | photo_hard | docangle_precise | 300 (300) | 0.25 | 88.0 [83.8–91.2] | 0.3 [0.1–1.9] | 2.0 | 0.3 | 47 |
| rvl_heldout | photo_hard | docangle_full | 300 (300) | 0.30 | 89.3 [85.3–92.3] | 0.3 [0.1–1.9] | 2.0 | 0.3 | 62 |
| rvl_heldout | photo_hard | legacy_v1 | 300 (300) | 0.37 | 77.7 [72.6–82.0] | 10.0 [7.1–13.9] | 0.0 | 10.0 | 42 |
| ext_funsd | scan | docangle | 300 (199) | 0.31 | 92.0 [88.4–94.6] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 39 |
| ext_funsd | scan | docangle_precise | 300 (199) | 0.29 | 92.7 [89.1–95.1] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 49 |
| ext_funsd | scan | docangle_full | 300 (199) | 0.31 | 92.0 [88.4–94.6] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 65 |
| ext_funsd | scan | legacy_v1 | 300 (199) | 0.27 | 91.7 [88.0–94.3] | 1.7 [0.7–3.8] | 0.0 | 1.7 | 36 |
| ext_funsd | photo_easy | docangle | 300 (199) | 0.30 | 90.3 [86.5–93.2] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 38 |
| ext_funsd | photo_easy | docangle_precise | 300 (199) | 0.26 | 90.0 [86.1–92.9] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 48 |
| ext_funsd | photo_easy | docangle_full | 300 (199) | 0.30 | 90.3 [86.5–93.2] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 63 |
| ext_funsd | photo_easy | legacy_v1 | 300 (199) | 0.30 | 90.0 [86.1–92.9] | 1.0 [0.3–2.9] | 0.0 | 1.0 | 34 |
| ext_funsd | photo_hard | docangle | 300 (199) | 0.31 | 91.0 [87.2–93.7] | 0.0 [0.0–1.3] | 1.7 | 0.0 | 38 |
| ext_funsd | photo_hard | docangle_precise | 300 (199) | 0.30 | 89.7 [85.7–92.6] | 0.0 [0.0–1.3] | 1.7 | 0.0 | 48 |
| ext_funsd | photo_hard | docangle_full | 300 (199) | 0.31 | 91.0 [87.2–93.7] | 0.0 [0.0–1.3] | 1.7 | 0.0 | 62 |
| ext_funsd | photo_hard | legacy_v1 | 300 (199) | 0.32 | 87.7 [83.5–90.9] | 2.3 [1.1–4.7] | 0.0 | 2.3 | 37 |
| ext_doclaynet | scan | docangle | 300 (300) | 0.16 | 98.3 [96.2–99.3] | 1.3 [0.5–3.4] | 3.0 | 0.0 | 46 |
| ext_doclaynet | scan | docangle_precise | 300 (300) | 0.12 | 98.3 [96.2–99.3] | 1.3 [0.5–3.4] | 3.0 | 0.0 | 56 |
| ext_doclaynet | scan | docangle_full | 300 (300) | 0.16 | 99.0 [97.1–99.7] | 0.7 [0.2–2.4] | 2.7 | 0.0 | 69 |
| ext_doclaynet | scan | legacy_v1 | 300 (300) | 0.17 | 97.7 [95.3–98.9] | 1.7 [0.7–3.8] | 0.0 | 1.7 | 39 |
| ext_doclaynet | photo_easy | docangle | 300 (300) | 0.16 | 95.7 [92.7–97.5] | 3.7 [2.1–6.4] | 5.0 | 2.1 | 44 |
| ext_doclaynet | photo_easy | docangle_precise | 300 (300) | 0.15 | 94.7 [91.5–96.7] | 3.7 [2.1–6.4] | 5.0 | 2.1 | 54 |
| ext_doclaynet | photo_easy | docangle_full | 300 (300) | 0.16 | 95.3 [92.3–97.2] | 3.7 [2.1–6.4] | 6.7 | 0.7 | 68 |
| ext_doclaynet | photo_easy | legacy_v1 | 300 (300) | 0.17 | 91.7 [88.0–94.3] | 6.3 [4.1–9.7] | 0.0 | 6.3 | 39 |
| ext_doclaynet | photo_hard | docangle | 300 (300) | 0.18 | 92.7 [89.1–95.1] | 4.3 [2.5–7.3] | 5.7 | 1.1 | 43 |
| ext_doclaynet | photo_hard | docangle_precise | 300 (300) | 0.16 | 90.3 [86.5–93.2] | 4.3 [2.5–7.3] | 5.7 | 1.1 | 52 |
| ext_doclaynet | photo_hard | docangle_full | 300 (300) | 0.18 | 93.0 [89.5–95.4] | 4.0 [2.3–6.9] | 5.7 | 1.1 | 67 |
| ext_doclaynet | photo_hard | legacy_v1 | 300 (300) | 0.18 | 90.3 [86.5–93.2] | 7.7 [5.2–11.2] | 0.0 | 7.7 | 40 |
| ext_cord | scan | docangle | 300 (200) | 0.30 | 79.7 [74.8–83.8] | 5.0 [3.1–8.1] | 19.0 | 0.4 | 32 |
| ext_cord | scan | docangle_precise | 300 (200) | 0.16 | 85.0 [80.5–88.6] | 5.0 [3.1–8.1] | 19.0 | 0.4 | 42 |
| ext_cord | scan | docangle_full | 300 (200) | 0.30 | 80.0 [75.1–84.1] | 4.7 [2.8–7.7] | 19.3 | 0.0 | 57 |
| ext_cord | scan | legacy_v1 | 300 (200) | 0.93 | 52.7 [47.0–58.2] | 37.7 [32.4–43.3] | 0.0 | 37.7 | 35 |
| ext_cord | photo_easy | docangle | 300 (200) | 0.42 | 72.7 [67.4–77.4] | 3.3 [1.8–6.0] | 25.0 | 0.9 | 33 |
| ext_cord | photo_easy | docangle_precise | 300 (200) | 0.31 | 72.3 [67.0–77.1] | 3.3 [1.8–6.0] | 25.0 | 0.9 | 42 |
| ext_cord | photo_easy | docangle_full | 300 (200) | 0.42 | 73.3 [68.1–78.0] | 2.3 [1.1–4.7] | 24.7 | 0.9 | 58 |
| ext_cord | photo_easy | legacy_v1 | 300 (200) | 1.92 | 44.0 [38.5–49.7] | 41.7 [36.2–47.3] | 0.0 | 41.7 | 38 |
| ext_cord | photo_hard | docangle | 300 (200) | 0.69 | 60.3 [54.7–65.7] | 3.7 [2.1–6.4] | 40.0 | 0.0 | 33 |
| ext_cord | photo_hard | docangle_precise | 300 (200) | 0.88 | 54.3 [48.7–59.9] | 3.7 [2.1–6.4] | 40.0 | 0.0 | 42 |
| ext_cord | photo_hard | docangle_full | 300 (200) | 0.69 | 60.0 [54.4–65.4] | 4.3 [2.5–7.3] | 41.0 | 0.0 | 58 |
| ext_cord | photo_hard | legacy_v1 | 300 (200) | 5.41 | 37.3 [32.1–42.9] | 44.7 [39.1–50.3] | 0.0 | 44.7 | 38 |
