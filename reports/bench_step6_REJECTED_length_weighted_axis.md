# Benchmark step6_circular_axis

commit `51ef41c` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| invoices | scan | uniform | docangle | 200 (100) | 0.27 | 95.0 [91.0–97.3] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 47 |
| invoices | scan | uniform | docangle_full | 200 (100) | 0.27 | 95.0 [91.0–97.3] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 76 |
| invoices | scan | uniform | docangle_precise | 200 (100) | 0.27 | 95.0 [91.0–97.3] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 56 |
| invoices | photo_hard | uniform | docangle | 200 (100) | 0.42 | 66.5 [59.7–72.7] | 2.5 [1.1–5.7] | 0.5/2.0 | 6.5 | 1.1 | 44 |
| invoices | photo_hard | uniform | docangle_full | 200 (100) | 0.41 | 66.5 [59.7–72.7] | 2.0 [0.8–5.0] | 0.0/2.0 | 5.0 | 1.1 | 74 |
| invoices | photo_hard | uniform | docangle_precise | 200 (100) | 0.31 | 69.0 [62.3–75.0] | 2.5 [1.1–5.7] | 0.5/2.0 | 6.5 | 1.1 | 53 |
| rvl_heldout | scan | uniform | docangle | 200 (200) | 0.32 | 89.0 [83.9–92.6] | 1.0 [0.3–3.6] | 0.5/0.5 | 1.5 | 0.0 | 47 |
| rvl_heldout | scan | uniform | docangle_full | 200 (200) | 0.32 | 89.5 [84.5–93.0] | 0.5 [0.1–2.8] | 0.0/0.5 | 1.0 | 0.0 | 76 |
| rvl_heldout | scan | uniform | docangle_precise | 200 (200) | 0.29 | 89.0 [83.9–92.6] | 1.0 [0.3–3.6] | 0.5/0.5 | 1.5 | 0.0 | 56 |
| rvl_heldout | photo_hard | uniform | docangle | 200 (200) | 0.62 | 66.0 [59.2–72.2] | 0.0 [0.0–1.9] | 0.0/0.0 | 7.5 | 0.0 | 46 |
| rvl_heldout | photo_hard | uniform | docangle_full | 200 (200) | 0.62 | 66.0 [59.2–72.2] | 0.0 [0.0–1.9] | 0.0/0.0 | 7.5 | 0.0 | 73 |
| rvl_heldout | photo_hard | uniform | docangle_precise | 200 (200) | 0.39 | 67.0 [60.2–73.1] | 0.0 [0.0–1.9] | 0.0/0.0 | 7.5 | 0.0 | 54 |
| tobacco_cert | scan | uniform | docangle | 200 (159) | 0.29 | 93.0 [88.6–95.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 48 |
| tobacco_cert | scan | uniform | docangle_full | 200 (159) | 0.29 | 93.0 [88.6–95.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 77 |
| tobacco_cert | scan | uniform | docangle_precise | 200 (159) | 0.28 | 92.5 [88.0–95.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 57 |
| tobacco_cert | photo_hard | uniform | docangle | 200 (159) | 0.38 | 80.0 [73.9–85.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.0 | 0.0 | 46 |
| tobacco_cert | photo_hard | uniform | docangle_full | 200 (159) | 0.38 | 80.0 [73.9–85.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.0 | 0.0 | 74 |
| tobacco_cert | photo_hard | uniform | docangle_precise | 200 (159) | 0.38 | 80.0 [73.9–85.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.0 | 0.0 | 55 |
| az | scan | uniform | docangle | 200 (100) | 0.16 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 52 |
| az | scan | uniform | docangle_full | 200 (100) | 0.16 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 80 |
| az | scan | uniform | docangle_precise | 200 (100) | 0.14 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 61 |
| az | photo_hard | uniform | docangle | 200 (100) | 0.19 | 88.5 [83.3–92.2] | 1.0 [0.3–3.6] | 1.0/0.0 | 2.0 | 1.0 | 48 |
| az | photo_hard | uniform | docangle_full | 200 (100) | 0.19 | 89.0 [83.9–92.6] | 0.5 [0.1–2.8] | 0.5/0.0 | 2.0 | 0.5 | 76 |
| az | photo_hard | uniform | docangle_precise | 200 (100) | 0.16 | 90.0 [85.1–93.4] | 1.0 [0.3–3.6] | 1.0/0.0 | 2.0 | 1.0 | 57 |
