# Benchmark step3_v3_vs_c8l

commit `73c44c5` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| invoices | scan | uniform | docangle | 200 (100) | 0.33 | 95.5 [91.7–97.6] | 1.0 [0.3–3.6] | 0.0/1.0 | 0.5 | 1.0 | 94 |
| invoices | scan | uniform | legacy_v1 | 200 (100) | 0.27 | 92.5 [88.0–95.4] | 5.5 [3.1–9.6] | 3.5/2.0 | 0.0 | 5.5 | 36 |
| invoices | photo_hard | uniform | docangle | 200 (100) | 0.26 | 91.0 [86.2–94.2] | 2.0 [0.8–5.0] | 0.5/1.5 | 5.5 | 1.1 | 92 |
| invoices | photo_hard | uniform | legacy_v1 | 200 (100) | 0.27 | 86.5 [81.1–90.6] | 7.5 [4.6–12.0] | 3.5/4.0 | 0.0 | 7.5 | 39 |
| rvl_heldout | scan | uniform | docangle | 200 (200) | 0.33 | 87.0 [81.6–91.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.0 | 0.0 | 94 |
| rvl_heldout | scan | uniform | legacy_v1 | 200 (200) | 0.33 | 81.5 [75.5–86.3] | 5.5 [3.1–9.6] | 4.5/1.0 | 0.0 | 5.5 | 38 |
| rvl_heldout | photo_hard | uniform | docangle | 200 (200) | 0.33 | 85.5 [80.0–89.7] | 1.5 [0.5–4.3] | 1.0/0.5 | 5.0 | 0.0 | 92 |
| rvl_heldout | photo_hard | uniform | legacy_v1 | 200 (200) | 0.36 | 79.5 [73.4–84.5] | 9.5 [6.2–14.4] | 7.5/2.0 | 0.0 | 9.5 | 40 |
| tobacco_cert | scan | uniform | docangle | 200 (159) | 0.28 | 89.0 [83.9–92.6] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 96 |
| tobacco_cert | scan | uniform | legacy_v1 | 200 (159) | 0.28 | 90.0 [85.1–93.4] | 0.5 [0.1–2.8] | 0.5/0.0 | 0.0 | 0.5 | 35 |
| tobacco_cert | photo_hard | uniform | docangle | 200 (159) | 0.33 | 90.5 [85.6–93.8] | 0.5 [0.1–2.8] | 0.5/0.0 | 2.0 | 0.5 | 93 |
| tobacco_cert | photo_hard | uniform | legacy_v1 | 200 (159) | 0.32 | 87.5 [82.2–91.4] | 2.0 [0.8–5.0] | 0.5/1.5 | 0.0 | 2.0 | 35 |
| az | scan | uniform | docangle | 200 (100) | 0.14 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 98 |
| az | scan | uniform | legacy_v1 | 200 (100) | 0.13 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 34 |
| az | photo_hard | uniform | docangle | 200 (100) | 0.16 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 1.5 | 0.5 | 96 |
| az | photo_hard | uniform | legacy_v1 | 200 (100) | 0.17 | 98.5 [95.7–99.5] | 1.0 [0.3–3.6] | 1.0/0.0 | 0.0 | 1.0 | 32 |
