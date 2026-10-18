# Benchmark e2_conf_quadtilt

commit `d36cc94` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| az | scan | quad_tilt | docangle | 200 (100) | 0.01 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 29 |
| az | scan | quad_tilt | docangle_conflegacy | 200 (100) | 0.01 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 30 |
| az | photo_hard | quad_tilt | docangle | 200 (100) | 0.01 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 0.5 | 0.0 | 27 |
| az | photo_hard | quad_tilt | docangle_conflegacy | 200 (100) | 0.01 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 0.5 | 0.0 | 28 |
| invoices | scan | quad_tilt | docangle | 200 (100) | 0.24 | 94.5 [90.4–96.9] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.5 | 1.0 | 27 |
| invoices | scan | quad_tilt | docangle_conflegacy | 200 (100) | 0.24 | 94.5 [90.4–96.9] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 28 |
| invoices | photo_hard | quad_tilt | docangle | 200 (100) | 0.11 | 95.5 [91.7–97.6] | 1.0 [0.3–3.6] | 0.0/1.0 | 2.5 | 1.0 | 27 |
| invoices | photo_hard | quad_tilt | docangle_conflegacy | 200 (100) | 0.11 | 95.5 [91.7–97.6] | 1.0 [0.3–3.6] | 0.0/1.0 | 3.0 | 1.0 | 28 |
| tobacco_cert | scan | quad_tilt | docangle | 200 (159) | 0.23 | 92.5 [88.0–95.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 28 |
| tobacco_cert | scan | quad_tilt | docangle_conflegacy | 200 (159) | 0.23 | 92.5 [88.0–95.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 29 |
| tobacco_cert | photo_hard | quad_tilt | docangle | 200 (159) | 0.08 | 98.5 [95.7–99.5] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 28 |
| tobacco_cert | photo_hard | quad_tilt | docangle_conflegacy | 200 (159) | 0.08 | 98.5 [95.7–99.5] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 28 |
| rvl_heldout | scan | quad_tilt | docangle | 200 (200) | 0.27 | 90.0 [85.1–93.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.5 | 0.0 | 28 |
| rvl_heldout | scan | quad_tilt | docangle_conflegacy | 200 (200) | 0.27 | 90.0 [85.1–93.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 29 |
| rvl_heldout | photo_hard | quad_tilt | docangle | 200 (200) | 0.08 | 92.5 [88.0–95.4] | 0.5 [0.1–2.8] | 0.5/0.0 | 2.0 | 0.0 | 27 |
| rvl_heldout | photo_hard | quad_tilt | docangle_conflegacy | 200 (200) | 0.08 | 92.5 [88.0–95.4] | 0.5 [0.1–2.8] | 0.5/0.0 | 2.0 | 0.0 | 28 |
| ext_funsd | scan | quad_tilt | docangle | 200 (199) | 0.25 | 93.0 [88.6–95.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 27 |
| ext_funsd | scan | quad_tilt | docangle_conflegacy | 200 (199) | 0.25 | 93.0 [88.6–95.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 28 |
| ext_funsd | photo_hard | quad_tilt | docangle | 200 (199) | 0.11 | 95.0 [91.0–97.3] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 27 |
| ext_funsd | photo_hard | quad_tilt | docangle_conflegacy | 200 (199) | 0.11 | 95.0 [91.0–97.3] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.5 | 0.0 | 28 |
| ext_doclaynet | scan | quad_tilt | docangle | 200 (200) | 0.01 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 3.0 | 0.0 | 33 |
| ext_doclaynet | scan | quad_tilt | docangle_conflegacy | 200 (200) | 0.01 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 2.5 | 0.0 | 33 |
| ext_doclaynet | photo_hard | quad_tilt | docangle | 200 (200) | 0.01 | 98.0 [95.0–99.2] | 2.0 [0.8–5.0] | 2.0/0.0 | 2.0 | 0.5 | 30 |
| ext_doclaynet | photo_hard | quad_tilt | docangle_conflegacy | 200 (200) | 0.01 | 98.0 [95.0–99.2] | 2.0 [0.8–5.0] | 2.0/0.0 | 2.5 | 2.1 | 31 |
| ext_cord | scan | quad_tilt | docangle | 200 (200) | 0.11 | 84.5 [78.8–88.9] | 2.0 [0.8–5.0] | 1.0/1.0 | 3.0 | 0.5 | 26 |
| ext_cord | scan | quad_tilt | docangle_conflegacy | 200 (200) | 0.11 | 84.5 [78.8–88.9] | 2.0 [0.8–5.0] | 1.0/1.0 | 22.0 | 0.6 | 27 |
| ext_cord | photo_hard | quad_tilt | docangle | 200 (200) | 0.08 | 80.0 [73.9–85.0] | 2.5 [1.1–5.7] | 2.0/0.5 | 7.0 | 0.5 | 26 |
| ext_cord | photo_hard | quad_tilt | docangle_conflegacy | 200 (200) | 0.08 | 80.0 [73.9–85.0] | 2.5 [1.1–5.7] | 2.0/0.5 | 28.5 | 0.0 | 27 |
