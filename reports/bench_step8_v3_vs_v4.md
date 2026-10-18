# Benchmark step8_v3_vs_v4

commit `51ef41c` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ext_funsd | scan | uniform | docangle_v3 | 200 (199) | 0.31 | 91.5 [86.8–94.6] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 47 |
| ext_funsd | scan | uniform | docangle_v4 | 200 (199) | 0.31 | 91.5 [86.8–94.6] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 48 |
| ext_funsd | photo_hard | uniform | docangle_v3 | 200 (199) | 0.31 | 92.0 [87.4–95.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.5 | 0.0 | 46 |
| ext_funsd | photo_hard | uniform | docangle_v4 | 200 (199) | 0.31 | 92.0 [87.4–95.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.5 | 0.0 | 46 |
| ext_cord | scan | uniform | docangle_v3 | 200 (200) | 0.75 | 55.5 [48.6–62.2] | 30.5 [24.5–37.2] | 26.5/4.0 | 35.0 | 10.8 | 40 |
| ext_cord | scan | uniform | docangle_v4 | 200 (200) | 0.31 | 79.0 [72.8–84.1] | 4.5 [2.4–8.3] | 4.0/0.5 | 18.0 | 0.6 | 38 |
| ext_cord | photo_hard | uniform | docangle_v3 | 200 (200) | 1.55 | 45.5 [38.7–52.4] | 32.5 [26.4–39.3] | 28.0/4.5 | 49.5 | 14.9 | 41 |
| ext_cord | photo_hard | uniform | docangle_v4 | 200 (200) | 0.65 | 61.0 [54.1–67.5] | 4.5 [2.4–8.3] | 3.0/1.5 | 40.0 | 0.0 | 38 |
| ext_doclaynet | scan | uniform | docangle_v3 | 200 (200) | 0.15 | 99.0 [96.4–99.7] | 0.5 [0.1–2.8] | 0.5/0.0 | 4.0 | 0.0 | 57 |
| ext_doclaynet | scan | uniform | docangle_v4 | 200 (200) | 0.16 | 98.5 [95.7–99.5] | 1.0 [0.3–3.6] | 0.0/1.0 | 3.0 | 0.0 | 57 |
| ext_doclaynet | photo_hard | uniform | docangle_v3 | 200 (200) | 0.19 | 89.5 [84.5–93.0] | 8.5 [5.4–13.2] | 5.0/3.5 | 6.0 | 4.8 | 53 |
| ext_doclaynet | photo_hard | uniform | docangle_v4 | 200 (200) | 0.18 | 92.5 [88.0–95.4] | 5.0 [2.7–9.0] | 3.0/2.0 | 6.0 | 1.6 | 52 |
| invoices | scan | uniform | docangle_v3 | 200 (100) | 0.27 | 95.5 [91.7–97.6] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 46 |
| invoices | scan | uniform | docangle_v4 | 200 (100) | 0.27 | 95.0 [91.0–97.3] | 1.5 [0.5–4.3] | 0.5/1.0 | 1.5 | 1.0 | 47 |
| invoices | photo_hard | uniform | docangle_v3 | 200 (100) | 0.26 | 93.0 [88.6–95.8] | 2.5 [1.1–5.7] | 0.5/2.0 | 4.5 | 1.0 | 45 |
| invoices | photo_hard | uniform | docangle_v4 | 200 (100) | 0.26 | 93.5 [89.2–96.2] | 2.0 [0.8–5.0] | 0.5/1.5 | 4.5 | 1.6 | 45 |
| rvl_heldout | scan | uniform | docangle_v3 | 200 (200) | 0.33 | 89.5 [84.5–93.0] | 1.0 [0.3–3.6] | 0.5/0.5 | 1.5 | 0.0 | 48 |
| rvl_heldout | scan | uniform | docangle_v4 | 200 (200) | 0.33 | 90.0 [85.1–93.4] | 0.5 [0.1–2.8] | 0.5/0.0 | 1.0 | 0.0 | 48 |
| rvl_heldout | photo_hard | uniform | docangle_v3 | 200 (200) | 0.32 | 88.5 [83.3–92.2] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.0 | 0.0 | 46 |
| rvl_heldout | photo_hard | uniform | docangle_v4 | 200 (200) | 0.32 | 88.5 [83.3–92.2] | 0.5 [0.1–2.8] | 0.0/0.5 | 2.0 | 0.5 | 46 |
| tobacco_cert | scan | uniform | docangle_v3 | 200 (159) | 0.29 | 93.0 [88.6–95.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 49 |
| tobacco_cert | scan | uniform | docangle_v4 | 200 (159) | 0.29 | 93.0 [88.6–95.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 50 |
| tobacco_cert | photo_hard | uniform | docangle_v3 | 200 (159) | 0.29 | 92.5 [88.0–95.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.0 | 0.0 | 47 |
| tobacco_cert | photo_hard | uniform | docangle_v4 | 200 (159) | 0.29 | 92.5 [88.0–95.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.0 | 0.0 | 48 |
| az | scan | uniform | docangle_v3 | 200 (100) | 0.16 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 53 |
| az | scan | uniform | docangle_v4 | 200 (100) | 0.16 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 54 |
| az | photo_hard | uniform | docangle_v3 | 200 (100) | 0.17 | 98.5 [95.7–99.5] | 1.0 [0.3–3.6] | 1.0/0.0 | 1.5 | 1.0 | 48 |
| az | photo_hard | uniform | docangle_v4 | 200 (100) | 0.17 | 99.5 [97.2–99.9] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.0 | 0.0 | 49 |
