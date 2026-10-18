# Benchmark final_v4_2

commit `f9d09c6` · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| az | scan | uniform | docangle | 300 (100) | 0.01 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0/0.0 | 0.0 | 0.0 | 31 |
| az | photo_easy | uniform | docangle | 300 (100) | 0.01 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0/0.0 | 0.0 | 0.0 | 28 |
| az | photo_hard | uniform | docangle | 300 (100) | 0.01 | 99.7 [98.1–99.9] | 0.0 [0.0–1.3] | 0.0/0.0 | 0.7 | 0.0 | 28 |
| invoices | scan | uniform | docangle | 300 (100) | 0.23 | 94.3 [91.1–96.4] | 1.3 [0.5–3.4] | 0.3/1.0 | 1.3 | 1.0 | 28 |
| invoices | photo_easy | uniform | docangle | 300 (100) | 0.13 | 94.7 [91.5–96.7] | 2.0 [0.9–4.3] | 0.7/1.3 | 2.3 | 1.4 | 28 |
| invoices | photo_hard | uniform | docangle | 300 (100) | 0.09 | 95.0 [91.9–96.9] | 1.7 [0.7–3.8] | 0.3/1.3 | 3.3 | 1.4 | 29 |
| tobacco_cert | scan | uniform | docangle | 300 (159) | 0.20 | 92.7 [89.1–95.1] | 0.0 [0.0–1.3] | 0.0/0.0 | 0.3 | 0.0 | 28 |
| tobacco_cert | photo_easy | uniform | docangle | 300 (159) | 0.10 | 98.7 [96.6–99.5] | 0.0 [0.0–1.3] | 0.0/0.0 | 0.3 | 0.0 | 29 |
| tobacco_cert | photo_hard | uniform | docangle | 300 (159) | 0.08 | 97.3 [94.8–98.6] | 0.0 [0.0–1.3] | 0.0/0.0 | 0.7 | 0.0 | 29 |
| rvl_heldout | scan | uniform | docangle | 300 (300) | 0.22 | 90.0 [86.1–92.9] | 0.7 [0.2–2.4] | 0.3/0.3 | 1.3 | 0.0 | 28 |
| rvl_heldout | photo_easy | uniform | docangle | 300 (300) | 0.12 | 91.0 [87.2–93.7] | 0.7 [0.2–2.4] | 0.3/0.3 | 2.0 | 0.0 | 29 |
| rvl_heldout | photo_hard | uniform | docangle | 300 (300) | 0.08 | 94.3 [91.1–96.4] | 0.7 [0.2–2.4] | 0.3/0.3 | 2.0 | 0.3 | 28 |
| ext_funsd | scan | uniform | docangle | 300 (199) | 0.25 | 93.0 [89.5–95.4] | 0.0 [0.0–1.3] | 0.0/0.0 | 0.0 | 0.0 | 28 |
| ext_funsd | photo_easy | uniform | docangle | 300 (199) | 0.11 | 95.3 [92.3–97.2] | 0.0 [0.0–1.3] | 0.0/0.0 | 0.3 | 0.0 | 28 |
| ext_funsd | photo_hard | uniform | docangle | 300 (199) | 0.08 | 95.7 [92.7–97.5] | 0.0 [0.0–1.3] | 0.0/0.0 | 1.7 | 0.0 | 29 |
| ext_doclaynet | scan | uniform | docangle | 300 (300) | 0.01 | 98.7 [96.6–99.5] | 1.0 [0.3–2.9] | 0.7/0.3 | 2.7 | 0.0 | 32 |
| ext_doclaynet | photo_easy | uniform | docangle | 300 (300) | 0.01 | 96.0 [93.1–97.7] | 3.7 [2.1–6.4] | 3.0/0.7 | 4.7 | 1.7 | 31 |
| ext_doclaynet | photo_hard | uniform | docangle | 300 (300) | 0.01 | 95.0 [91.9–96.9] | 4.7 [2.8–7.7] | 3.0/1.7 | 6.0 | 1.1 | 32 |
| ext_cord | scan | uniform | docangle | 300 (200) | 0.06 | 85.0 [80.5–88.6] | 4.7 [2.8–7.7] | 4.0/0.7 | 19.3 | 0.0 | 27 |
| ext_cord | photo_easy | uniform | docangle | 300 (200) | 0.07 | 92.3 [88.8–94.8] | 2.7 [1.4–5.2] | 2.3/0.3 | 19.0 | 0.8 | 28 |
| ext_cord | photo_hard | uniform | docangle | 300 (200) | 0.05 | 85.0 [80.5–88.6] | 3.7 [2.1–6.4] | 2.3/1.3 | 33.3 | 0.0 | 28 |
