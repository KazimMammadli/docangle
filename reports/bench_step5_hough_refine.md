# Benchmark step5_hough_refine

commit `51ef41c` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| invoices | scan | uniform | docangle | 200 (100) | 0.28 | 94.5 [90.4–96.9] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 47 |
| invoices | scan | uniform | docangle_noreg | 200 (100) | 0.28 | 94.5 [90.4–96.9] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 46 |
| invoices | scan | uniform | docangle_precise | 200 (100) | 0.28 | 95.0 [91.0–97.3] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 56 |
| invoices | photo_hard | uniform | docangle | 200 (100) | 0.27 | 91.5 [86.8–94.6] | 2.5 [1.1–5.7] | 0.5/2.0 | 4.5 | 1.0 | 45 |
| invoices | photo_hard | uniform | docangle_noreg | 200 (100) | 0.27 | 92.5 [88.0–95.4] | 1.5 [0.5–4.3] | 0.0/1.5 | 3.0 | 1.5 | 44 |
| invoices | photo_hard | uniform | docangle_precise | 200 (100) | 0.23 | 89.5 [84.5–93.0] | 2.5 [1.1–5.7] | 0.5/2.0 | 4.5 | 1.0 | 54 |
| rvl_heldout | scan | uniform | docangle | 200 (200) | 0.34 | 88.0 [82.8–91.8] | 0.5 [0.1–2.8] | 0.0/0.5 | 1.5 | 0.0 | 47 |
| rvl_heldout | scan | uniform | docangle_noreg | 200 (200) | 0.34 | 88.0 [82.8–91.8] | 0.5 [0.1–2.8] | 0.5/0.0 | 1.0 | 0.5 | 47 |
| rvl_heldout | scan | uniform | docangle_precise | 200 (200) | 0.32 | 87.5 [82.2–91.4] | 0.5 [0.1–2.8] | 0.0/0.5 | 1.5 | 0.0 | 56 |
| rvl_heldout | photo_hard | uniform | docangle | 200 (200) | 0.32 | 89.0 [83.9–92.6] | 0.5 [0.1–2.8] | 0.5/0.0 | 3.0 | 0.0 | 45 |
| rvl_heldout | photo_hard | uniform | docangle_noreg | 200 (200) | 0.32 | 88.5 [83.3–92.2] | 1.0 [0.3–3.6] | 1.0/0.0 | 3.0 | 0.0 | 45 |
| rvl_heldout | photo_hard | uniform | docangle_precise | 200 (200) | 0.27 | 89.5 [84.5–93.0] | 0.5 [0.1–2.8] | 0.5/0.0 | 3.0 | 0.0 | 54 |
| tobacco_cert | scan | uniform | docangle | 200 (159) | 0.29 | 92.0 [87.4–95.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 48 |
| tobacco_cert | scan | uniform | docangle_noreg | 200 (159) | 0.29 | 92.0 [87.4–95.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 48 |
| tobacco_cert | scan | uniform | docangle_precise | 200 (159) | 0.28 | 91.5 [86.8–94.6] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 58 |
| tobacco_cert | photo_hard | uniform | docangle | 200 (159) | 0.28 | 90.5 [85.6–93.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.5 | 0.0 | 46 |
| tobacco_cert | photo_hard | uniform | docangle_noreg | 200 (159) | 0.28 | 90.5 [85.6–93.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.5 | 0.0 | 46 |
| tobacco_cert | photo_hard | uniform | docangle_precise | 200 (159) | 0.29 | 90.5 [85.6–93.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.5 | 0.0 | 55 |
| az | scan | uniform | docangle | 200 (100) | 0.16 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 52 |
| az | scan | uniform | docangle_noreg | 200 (100) | 0.16 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 52 |
| az | scan | uniform | docangle_precise | 200 (100) | 0.13 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 61 |
| az | photo_hard | uniform | docangle | 200 (100) | 0.17 | 98.5 [95.7–99.5] | 1.0 [0.3–3.6] | 1.0/0.0 | 1.5 | 1.0 | 48 |
| az | photo_hard | uniform | docangle_noreg | 200 (100) | 0.17 | 98.0 [95.0–99.2] | 1.5 [0.5–4.3] | 1.5/0.0 | 1.0 | 1.5 | 48 |
| az | photo_hard | uniform | docangle_precise | 200 (100) | 0.16 | 97.0 [93.6–98.6] | 1.0 [0.3–3.6] | 1.0/0.0 | 1.5 | 1.0 | 56 |
