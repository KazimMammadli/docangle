# Benchmark baseline_step1

commit `9a75ecb` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.30.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| invoices | scan | uniform | docangle | 300 (100) | 0.33 | 91.0 [87.2–93.7] | 5.3 [3.3–8.5] | 3.7/1.7 | 12.3 | 3.8 | 34 |
| invoices | scan | uniform | docangle_fast | 300 (100) | 0.33 | 89.7 [85.7–92.6] | 6.0 [3.8–9.3] | 4.7/1.3 | 14.3 | 5.1 | 24 |
| invoices | scan | uniform | legacy_v1 | 300 (100) | 0.26 | 92.0 [88.4–94.6] | 5.0 [3.1–8.1] | 3.3/1.7 | 0.0 | 5.0 | 42 |
| invoices | scan | quad_tilt | docangle | 300 (100) | 0.33 | 92.0 [88.4–94.6] | 4.0 [2.3–6.9] | 2.7/1.3 | 4.7 | 3.8 | 31 |
| invoices | scan | quad_tilt | docangle_fast | 300 (100) | 0.32 | 92.3 [88.8–94.8] | 4.0 [2.3–6.9] | 2.0/2.0 | 6.3 | 2.8 | 19 |
| invoices | scan | quad_tilt | legacy_v1 | 300 (100) | 0.28 | 93.7 [90.3–95.9] | 4.7 [2.8–7.7] | 3.3/1.3 | 0.0 | 4.7 | 34 |
| invoices | photo_easy | uniform | docangle | 300 (100) | 0.29 | 85.7 [81.2–89.2] | 9.7 [6.8–13.5] | 6.0/3.7 | 20.0 | 5.8 | 32 |
| invoices | photo_easy | uniform | docangle_fast | 300 (100) | 0.32 | 83.3 [78.7–87.1] | 10.0 [7.1–13.9] | 8.0/2.0 | 25.0 | 5.3 | 25 |
| invoices | photo_easy | uniform | legacy_v1 | 300 (100) | 0.28 | 85.3 [80.9–88.9] | 9.7 [6.8–13.5] | 6.7/3.0 | 0.0 | 9.7 | 40 |
| invoices | photo_easy | quad_tilt | docangle | 300 (100) | 0.28 | 91.3 [87.6–94.0] | 6.3 [4.1–9.7] | 3.3/3.0 | 11.7 | 5.3 | 30 |
| invoices | photo_easy | quad_tilt | docangle_fast | 300 (100) | 0.32 | 89.3 [85.3–92.3] | 6.0 [3.8–9.3] | 3.7/2.3 | 15.3 | 5.1 | 21 |
| invoices | photo_easy | quad_tilt | legacy_v1 | 300 (100) | 0.28 | 91.0 [87.2–93.7] | 6.0 [3.8–9.3] | 3.3/2.7 | 0.0 | 6.0 | 33 |
| invoices | photo_hard | uniform | docangle | 300 (100) | 0.34 | 82.3 [77.6–86.2] | 12.3 [9.1–16.5] | 7.0/5.3 | 26.7 | 8.6 | 32 |
| invoices | photo_hard | uniform | docangle_fast | 300 (100) | 0.32 | 80.7 [75.8–84.7] | 13.0 [9.7–17.3] | 8.0/5.0 | 30.0 | 8.1 | 26 |
| invoices | photo_hard | uniform | legacy_v1 | 300 (100) | 0.30 | 82.7 [78.0–86.5] | 13.0 [9.7–17.3] | 7.0/6.0 | 0.0 | 13.0 | 43 |
| invoices | photo_hard | quad_tilt | docangle | 300 (100) | 0.27 | 87.3 [83.1–90.6] | 7.7 [5.2–11.2] | 5.7/2.0 | 18.3 | 6.5 | 29 |
| invoices | photo_hard | quad_tilt | docangle_fast | 300 (100) | 0.33 | 84.7 [80.2–88.3] | 7.3 [4.9–10.9] | 5.0/2.3 | 20.0 | 5.4 | 21 |
| invoices | photo_hard | quad_tilt | legacy_v1 | 300 (100) | 0.31 | 86.3 [82.0–89.8] | 7.7 [5.2–11.2] | 6.0/1.7 | 0.0 | 7.7 | 33 |
| tobacco_cert | scan | uniform | docangle | 300 (159) | 0.31 | 91.3 [87.6–94.0] | 1.0 [0.3–2.9] | 0.7/0.3 | 5.0 | 0.4 | 33 |
| tobacco_cert | scan | uniform | docangle_fast | 300 (159) | 0.31 | 89.0 [85.0–92.1] | 0.7 [0.2–2.4] | 0.3/0.3 | 6.0 | 0.4 | 21 |
| tobacco_cert | scan | uniform | legacy_v1 | 300 (159) | 0.25 | 91.3 [87.6–94.0] | 1.3 [0.5–3.4] | 0.7/0.7 | 0.0 | 1.3 | 38 |
| tobacco_cert | scan | quad_tilt | docangle | 300 (159) | 0.31 | 91.0 [87.2–93.7] | 0.3 [0.1–1.9] | 0.3/0.0 | 0.7 | 0.3 | 34 |
| tobacco_cert | scan | quad_tilt | docangle_fast | 300 (159) | 0.31 | 89.0 [85.0–92.1] | 0.0 [0.0–1.3] | 0.0/0.0 | 2.3 | 0.0 | 17 |
| tobacco_cert | scan | quad_tilt | legacy_v1 | 300 (159) | 0.25 | 93.0 [89.5–95.4] | 0.3 [0.1–1.9] | 0.3/0.0 | 0.0 | 0.3 | 35 |
| tobacco_cert | photo_easy | uniform | docangle | 300 (159) | 0.27 | 90.3 [86.5–93.2] | 1.0 [0.3–2.9] | 1.0/0.0 | 10.0 | 0.7 | 33 |
| tobacco_cert | photo_easy | uniform | docangle_fast | 300 (159) | 0.29 | 87.3 [83.1–90.6] | 1.3 [0.5–3.4] | 1.0/0.3 | 10.3 | 1.1 | 22 |
| tobacco_cert | photo_easy | uniform | legacy_v1 | 300 (159) | 0.30 | 89.3 [85.3–92.3] | 0.7 [0.2–2.4] | 0.7/0.0 | 0.0 | 0.7 | 37 |
| tobacco_cert | photo_easy | quad_tilt | docangle | 300 (159) | 0.31 | 89.3 [85.3–92.3] | 2.3 [1.1–4.7] | 1.0/1.3 | 4.7 | 2.1 | 33 |
| tobacco_cert | photo_easy | quad_tilt | docangle_fast | 300 (159) | 0.34 | 86.3 [82.0–89.8] | 2.0 [0.9–4.3] | 0.7/1.3 | 5.3 | 1.4 | 19 |
| tobacco_cert | photo_easy | quad_tilt | legacy_v1 | 300 (159) | 0.27 | 89.7 [85.7–92.6] | 2.0 [0.9–4.3] | 0.7/1.3 | 0.0 | 2.0 | 35 |
| tobacco_cert | photo_hard | uniform | docangle | 300 (159) | 0.33 | 86.0 [81.6–89.5] | 2.7 [1.4–5.2] | 1.3/1.3 | 12.0 | 1.5 | 33 |
| tobacco_cert | photo_hard | uniform | docangle_fast | 300 (159) | 0.33 | 83.7 [79.1–87.4] | 2.3 [1.1–4.7] | 1.0/1.3 | 15.7 | 1.2 | 23 |
| tobacco_cert | photo_hard | uniform | legacy_v1 | 300 (159) | 0.33 | 86.7 [82.4–90.1] | 3.0 [1.6–5.6] | 1.0/2.0 | 0.0 | 3.0 | 40 |
| tobacco_cert | photo_hard | quad_tilt | docangle | 300 (159) | 0.30 | 87.7 [83.5–90.9] | 2.3 [1.1–4.7] | 1.0/1.3 | 7.7 | 1.8 | 31 |
| tobacco_cert | photo_hard | quad_tilt | docangle_fast | 300 (159) | 0.34 | 86.3 [82.0–89.8] | 2.7 [1.4–5.2] | 1.7/1.0 | 9.7 | 2.2 | 19 |
| tobacco_cert | photo_hard | quad_tilt | legacy_v1 | 300 (159) | 0.30 | 86.7 [82.4–90.1] | 3.7 [2.1–6.4] | 1.3/2.3 | 0.0 | 3.7 | 32 |
