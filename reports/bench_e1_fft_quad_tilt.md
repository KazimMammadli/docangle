# Benchmark e1_fft_quad_tilt

commit `ce2bf6d` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| az | scan | quad_tilt | docangle | 200 (100) | 0.12 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 50 |
| az | scan | quad_tilt | docangle_fft | 200 (100) | 0.01 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 37 |
| az | photo_hard | quad_tilt | docangle | 200 (100) | 0.16 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 0.5 | 0.0 | 39 |
| az | photo_hard | quad_tilt | docangle_fft | 200 (100) | 0.01 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 0.5 | 0.0 | 30 |
| invoices | scan | quad_tilt | docangle | 200 (100) | 0.30 | 95.0 [91.0–97.3] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 39 |
| invoices | scan | quad_tilt | docangle_fft | 200 (100) | 0.24 | 94.5 [90.4–96.9] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 31 |
| invoices | photo_hard | quad_tilt | docangle | 200 (100) | 0.27 | 93.0 [88.6–95.8] | 1.0 [0.3–3.6] | 0.0/1.0 | 3.5 | 1.0 | 35 |
| invoices | photo_hard | quad_tilt | docangle_fft | 200 (100) | 0.11 | 95.5 [91.7–97.6] | 1.0 [0.3–3.6] | 0.0/1.0 | 3.0 | 1.0 | 29 |
| tobacco_cert | scan | quad_tilt | docangle | 200 (159) | 0.28 | 93.0 [88.6–95.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 40 |
| tobacco_cert | scan | quad_tilt | docangle_fft | 200 (159) | 0.23 | 92.5 [88.0–95.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 30 |
| tobacco_cert | photo_hard | quad_tilt | docangle | 200 (159) | 0.29 | 91.0 [86.2–94.2] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 38 |
| tobacco_cert | photo_hard | quad_tilt | docangle_fft | 200 (159) | 0.08 | 98.5 [95.7–99.5] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 30 |
| rvl_heldout | scan | quad_tilt | docangle | 200 (200) | 0.33 | 88.0 [82.8–91.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 37 |
| rvl_heldout | scan | quad_tilt | docangle_fft | 200 (200) | 0.27 | 90.0 [85.1–93.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 29 |
| rvl_heldout | photo_hard | quad_tilt | docangle | 200 (200) | 0.28 | 88.5 [83.3–92.2] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.5 | 0.0 | 36 |
| rvl_heldout | photo_hard | quad_tilt | docangle_fft | 200 (200) | 0.08 | 92.5 [88.0–95.4] | 0.5 [0.1–2.8] | 0.5/0.0 | 2.0 | 0.0 | 29 |
| ext_cord | scan | quad_tilt | docangle | 200 (200) | 0.32 | 80.5 [74.5–85.4] | 2.0 [0.8–5.0] | 1.0/1.0 | 21.5 | 0.6 | 29 |
| ext_cord | scan | quad_tilt | docangle_fft | 200 (200) | 0.11 | 84.5 [78.8–88.9] | 2.0 [0.8–5.0] | 1.0/1.0 | 22.0 | 0.6 | 27 |
| ext_cord | photo_hard | quad_tilt | docangle | 200 (200) | 0.51 | 68.0 [61.2–74.1] | 2.0 [0.8–5.0] | 1.5/0.5 | 30.0 | 0.0 | 29 |
| ext_cord | photo_hard | quad_tilt | docangle_fft | 200 (200) | 0.08 | 80.0 [73.9–85.0] | 2.5 [1.1–5.7] | 2.0/0.5 | 28.5 | 0.0 | 28 |
| ext_doclaynet | scan | quad_tilt | docangle | 200 (200) | 0.14 | 98.5 [95.7–99.5] | 0.5 [0.1–2.8] | 0.5/0.0 | 2.5 | 0.0 | 49 |
| ext_doclaynet | scan | quad_tilt | docangle_fft | 200 (200) | 0.01 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 2.5 | 0.0 | 36 |
| ext_doclaynet | photo_hard | quad_tilt | docangle | 200 (200) | 0.16 | 96.5 [93.0–98.3] | 2.0 [0.8–5.0] | 2.0/0.0 | 2.5 | 2.1 | 44 |
| ext_doclaynet | photo_hard | quad_tilt | docangle_fft | 200 (200) | 0.01 | 98.0 [95.0–99.2] | 2.0 [0.8–5.0] | 2.0/0.0 | 2.5 | 2.1 | 34 |
