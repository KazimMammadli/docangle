Source: `reports/bench_final_v4_2.json` — commit `f9d09c6`, AMD Ryzen 9 5980HX with Radeon Graphics, 16 cores, opencv 4.14.0, onnxruntime 1.31.0, python 3.14.6.

Simulated photographs of known pages at uniformly random angles in [-180°, 180°]; flip = error > 45°. 'accepted' = the page was NOT sent to review.

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — scan

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 1200 | 0.50 [0.23–1.09] | 0.25 [0.09–0.73] | 0.25 (3) | 94.2 | 81.8 | 0.8 | 29 |

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — photo_easy

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 1200 | 0.67 [0.34–1.31] | 0.42 [0.18–0.97] | 0.33 (4) | 96.1 | 87.9 | 1.2 | 29 |

### Primary pools (az, invoices, tobacco_cert, rvl_heldout) — photo_hard

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 1200 | 0.58 [0.28–1.20] | 0.33 [0.13–0.85] | 0.42 (5) | 96.6 | 92.2 | 1.7 | 28 |

### Primary pools — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 3600 | 0.58 [0.38–0.89] | 0.33 [0.19–0.58] | 0.33 (12) | 95.6 | 87.3 | 1.2 | 29 |

### External held-out pools (FUNSD scans, DocLayNet pages, CORD receipt photos) — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 2700 | 2.26 [1.76–2.89] | 2.26 [1.76–2.89] | 0.37 (10) | 92.9 | 86.7 | 9.7 | 29 |

### az — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 99.9 | 99.9 | 0.2 | 29 |

### invoices — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 1.67 [1.01–2.73] | 0.67 [0.31–1.45] | 1.22 (11) | 94.7 | 84.6 | 2.3 | 28 |

### tobacco_cert — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 96.2 | 87.4 | 0.4 | 29 |

### rvl_heldout — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 0.67 [0.31–1.45] | 0.67 [0.31–1.45] | 0.11 (1) | 91.8 | 77.3 | 1.8 | 29 |

### ext_funsd — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 0.00 [0.00–0.43] | 0.00 [0.00–0.43] | 0.00 (0) | 94.7 | 82.7 | 0.7 | 28 |

### ext_doclaynet — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 3.11 [2.16–4.46] | 3.11 [2.16–4.46] | 0.89 (8) | 96.6 | 96.3 | 4.4 | 32 |

### ext_cord — all levels

| candidate | cases | flips % [95% CI] | flips excl. known-bad source page | accepted flips (conf ≥ review thr.) % | ≤1° % | ≤0.5° % | needs_review % | mean ms (analyse) |
|---|---|---|---|---|---|---|---|---|
| docangle | 900 | 3.67 [2.62–5.10] | 3.67 [2.62–5.10] | 0.22 (2) | 87.4 | 81.2 | 23.9 | 28 |

### Per cell

| pool | level | candidate | cases (unique pages) | median ° | ≤1° % [95% CI] | flips % [95% CI] | review % | accepted flips % | ms |
|---|---|---|---|---|---|---|---|---|---|
| az | scan | docangle | 300 (100) | 0.01 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 31 |
| az | photo_easy | docangle | 300 (100) | 0.01 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 28 |
| az | photo_hard | docangle | 300 (100) | 0.01 | 99.7 [98.1–99.9] | 0.0 [0.0–1.3] | 0.7 | 0.0 | 28 |
| invoices | scan | docangle | 300 (100) | 0.23 | 94.3 [91.1–96.4] | 1.3 [0.5–3.4] | 1.3 | 1.0 | 28 |
| invoices | photo_easy | docangle | 300 (100) | 0.13 | 94.7 [91.5–96.7] | 2.0 [0.9–4.3] | 2.3 | 1.4 | 28 |
| invoices | photo_hard | docangle | 300 (100) | 0.09 | 95.0 [91.9–96.9] | 1.7 [0.7–3.8] | 3.3 | 1.4 | 29 |
| tobacco_cert | scan | docangle | 300 (159) | 0.20 | 92.7 [89.1–95.1] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 28 |
| tobacco_cert | photo_easy | docangle | 300 (159) | 0.10 | 98.7 [96.6–99.5] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 29 |
| tobacco_cert | photo_hard | docangle | 300 (159) | 0.08 | 97.3 [94.8–98.6] | 0.0 [0.0–1.3] | 0.7 | 0.0 | 29 |
| rvl_heldout | scan | docangle | 300 (300) | 0.22 | 90.0 [86.1–92.9] | 0.7 [0.2–2.4] | 1.3 | 0.0 | 28 |
| rvl_heldout | photo_easy | docangle | 300 (300) | 0.12 | 91.0 [87.2–93.7] | 0.7 [0.2–2.4] | 2.0 | 0.0 | 29 |
| rvl_heldout | photo_hard | docangle | 300 (300) | 0.08 | 94.3 [91.1–96.4] | 0.7 [0.2–2.4] | 2.0 | 0.3 | 28 |
| ext_funsd | scan | docangle | 300 (199) | 0.25 | 93.0 [89.5–95.4] | 0.0 [0.0–1.3] | 0.0 | 0.0 | 28 |
| ext_funsd | photo_easy | docangle | 300 (199) | 0.11 | 95.3 [92.3–97.2] | 0.0 [0.0–1.3] | 0.3 | 0.0 | 28 |
| ext_funsd | photo_hard | docangle | 300 (199) | 0.08 | 95.7 [92.7–97.5] | 0.0 [0.0–1.3] | 1.7 | 0.0 | 29 |
| ext_doclaynet | scan | docangle | 300 (300) | 0.01 | 98.7 [96.6–99.5] | 1.0 [0.3–2.9] | 2.7 | 0.0 | 32 |
| ext_doclaynet | photo_easy | docangle | 300 (300) | 0.01 | 96.0 [93.1–97.7] | 3.7 [2.1–6.4] | 4.7 | 1.7 | 31 |
| ext_doclaynet | photo_hard | docangle | 300 (300) | 0.01 | 95.0 [91.9–96.9] | 4.7 [2.8–7.7] | 6.0 | 1.1 | 32 |
| ext_cord | scan | docangle | 300 (200) | 0.06 | 85.0 [80.5–88.6] | 4.7 [2.8–7.7] | 19.3 | 0.0 | 27 |
| ext_cord | photo_easy | docangle | 300 (200) | 0.07 | 92.3 [88.8–94.8] | 2.7 [1.4–5.2] | 19.0 | 0.8 | 28 |
| ext_cord | photo_hard | docangle | 300 (200) | 0.05 | 85.0 [80.5–88.6] | 3.7 [2.1–6.4] | 33.3 | 0.0 | 28 |
