# Benchmark final_v4_1_quadtilt

commit `f4fcb38` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| az | scan | quad_tilt | docangle | 200 (100) | 0.12 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 45 |
| az | scan | quad_tilt | legacy_v1 | 200 (100) | 0.12 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 0.0 | 0.5 | 40 |
| az | photo_easy | quad_tilt | docangle | 200 (100) | 0.14 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 41 |
| az | photo_easy | quad_tilt | legacy_v1 | 200 (100) | 0.15 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 33 |
| az | photo_hard | quad_tilt | docangle | 200 (100) | 0.16 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 0.5 | 0.0 | 40 |
| az | photo_hard | quad_tilt | legacy_v1 | 200 (100) | 0.16 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 32 |
| invoices | scan | quad_tilt | docangle | 200 (100) | 0.30 | 95.0 [91.0–97.3] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 38 |
| invoices | scan | quad_tilt | legacy_v1 | 200 (100) | 0.25 | 93.0 [88.6–95.8] | 4.0 [2.0–7.7] | 2.5/1.5 | 0.0 | 4.0 | 31 |
| invoices | photo_easy | quad_tilt | docangle | 200 (100) | 0.30 | 94.5 [90.4–96.9] | 1.5 [0.5–4.3] | 0.0/1.5 | 2.5 | 1.0 | 37 |
| invoices | photo_easy | quad_tilt | legacy_v1 | 200 (100) | 0.28 | 86.5 [81.1–90.6] | 10.5 [7.0–15.5] | 8.5/2.0 | 0.0 | 10.5 | 32 |
| invoices | photo_hard | quad_tilt | docangle | 200 (100) | 0.27 | 93.0 [88.6–95.8] | 1.0 [0.3–3.6] | 0.0/1.0 | 3.5 | 1.0 | 36 |
| invoices | photo_hard | quad_tilt | legacy_v1 | 200 (100) | 0.30 | 84.0 [78.3–88.4] | 10.5 [7.0–15.5] | 8.0/2.5 | 0.0 | 10.5 | 34 |
| tobacco_cert | scan | quad_tilt | docangle | 200 (159) | 0.28 | 93.0 [88.6–95.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 41 |
| tobacco_cert | scan | quad_tilt | legacy_v1 | 200 (159) | 0.26 | 91.5 [86.8–94.6] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 33 |
| tobacco_cert | photo_easy | quad_tilt | docangle | 200 (159) | 0.26 | 92.0 [87.4–95.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 39 |
| tobacco_cert | photo_easy | quad_tilt | legacy_v1 | 200 (159) | 0.27 | 92.0 [87.4–95.0] | 0.5 [0.1–2.8] | 0.0/0.5 | 0.0 | 0.5 | 32 |
| tobacco_cert | photo_hard | quad_tilt | docangle | 200 (159) | 0.29 | 91.0 [86.2–94.2] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 38 |
| tobacco_cert | photo_hard | quad_tilt | legacy_v1 | 200 (159) | 0.31 | 91.0 [86.2–94.2] | 2.0 [0.8–5.0] | 1.5/0.5 | 0.0 | 2.0 | 31 |
| rvl_heldout | scan | quad_tilt | docangle | 200 (200) | 0.33 | 88.0 [82.8–91.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 39 |
| rvl_heldout | scan | quad_tilt | legacy_v1 | 200 (200) | 0.31 | 86.0 [80.5–90.1] | 6.5 [3.8–10.8] | 5.0/1.5 | 0.0 | 6.5 | 35 |
| rvl_heldout | photo_easy | quad_tilt | docangle | 200 (200) | 0.34 | 89.5 [84.5–93.0] | 1.0 [0.3–3.6] | 1.0/0.0 | 1.5 | 0.5 | 38 |
| rvl_heldout | photo_easy | quad_tilt | legacy_v1 | 200 (200) | 0.35 | 86.5 [81.1–90.6] | 4.0 [2.0–7.7] | 3.0/1.0 | 0.0 | 4.0 | 35 |
| rvl_heldout | photo_hard | quad_tilt | docangle | 200 (200) | 0.28 | 88.5 [83.3–92.2] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.5 | 0.0 | 37 |
| rvl_heldout | photo_hard | quad_tilt | legacy_v1 | 200 (200) | 0.38 | 78.5 [72.3–83.6] | 6.5 [3.8–10.8] | 3.5/3.0 | 0.0 | 6.5 | 34 |
