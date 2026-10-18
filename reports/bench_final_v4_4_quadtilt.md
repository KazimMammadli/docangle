# Benchmark final_v4_4_quadtilt

commit `a844f52` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| az | scan | quad_tilt | docangle | 200 (100) | 0.01 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 30 |
| az | photo_easy | quad_tilt | docangle | 200 (100) | 0.01 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 28 |
| az | photo_hard | quad_tilt | docangle | 200 (100) | 0.01 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 28 |
| invoices | scan | quad_tilt | docangle | 200 (100) | 0.24 | 94.5 [90.4–96.9] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.5 | 1.0 | 27 |
| invoices | photo_easy | quad_tilt | docangle | 200 (100) | 0.14 | 95.5 [91.7–97.6] | 1.5 [0.5–4.3] | 0.0/1.5 | 4.0 | 1.0 | 28 |
| invoices | photo_hard | quad_tilt | docangle | 200 (100) | 0.11 | 95.5 [91.7–97.6] | 1.0 [0.3–3.6] | 0.0/1.0 | 2.5 | 1.0 | 28 |
| tobacco_cert | scan | quad_tilt | docangle | 200 (159) | 0.23 | 92.5 [88.0–95.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 28 |
| tobacco_cert | photo_easy | quad_tilt | docangle | 200 (159) | 0.11 | 96.5 [93.0–98.3] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 28 |
| tobacco_cert | photo_hard | quad_tilt | docangle | 200 (159) | 0.08 | 98.5 [95.7–99.5] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 28 |
| rvl_heldout | scan | quad_tilt | docangle | 200 (200) | 0.27 | 90.0 [85.1–93.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.5 | 0.0 | 28 |
| rvl_heldout | photo_easy | quad_tilt | docangle | 200 (200) | 0.13 | 90.5 [85.6–93.8] | 1.0 [0.3–3.6] | 1.0/0.0 | 1.5 | 0.0 | 28 |
| rvl_heldout | photo_hard | quad_tilt | docangle | 200 (200) | 0.08 | 92.5 [88.0–95.4] | 0.5 [0.1–2.8] | 0.5/0.0 | 2.0 | 0.0 | 28 |
