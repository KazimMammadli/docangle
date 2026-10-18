# Benchmark step7_external_baseline

commit `51ef41c` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ext_funsd | scan | uniform | docangle | 200 (199) | 0.31 | 91.5 [86.8–94.6] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 46 |
| ext_funsd | scan | uniform | legacy_v1 | 200 (199) | 0.28 | 91.0 [86.2–94.2] | 2.0 [0.8–5.0] | 2.0/0.0 | 0.0 | 2.0 | 34 |
| ext_funsd | photo_hard | uniform | docangle | 200 (199) | 0.31 | 92.0 [87.4–95.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 2.5 | 0.0 | 45 |
| ext_funsd | photo_hard | uniform | legacy_v1 | 200 (199) | 0.34 | 87.5 [82.2–91.4] | 3.0 [1.4–6.4] | 0.0/3.0 | 0.0 | 3.0 | 35 |
| ext_cord | scan | uniform | docangle | 200 (200) | 0.75 | 55.5 [48.6–62.2] | 30.5 [24.5–37.2] | 26.5/4.0 | 35.0 | 10.8 | 39 |
| ext_cord | scan | uniform | legacy_v1 | 200 (200) | 1.03 | 49.5 [42.6–56.4] | 40.5 [33.9–47.4] | 31.5/9.0 | 0.0 | 40.5 | 33 |
| ext_cord | photo_hard | uniform | docangle | 200 (200) | 1.55 | 45.5 [38.7–52.4] | 32.5 [26.4–39.3] | 28.0/4.5 | 49.5 | 14.9 | 40 |
| ext_cord | photo_hard | uniform | legacy_v1 | 200 (200) | 3.67 | 38.0 [31.6–44.9] | 43.5 [36.8–50.4] | 27.0/16.5 | 0.0 | 43.5 | 34 |
| ext_doclaynet | scan | uniform | docangle | 200 (200) | 0.15 | 99.0 [96.4–99.7] | 0.5 [0.1–2.8] | 0.5/0.0 | 4.0 | 0.0 | 54 |
| ext_doclaynet | scan | uniform | legacy_v1 | 200 (200) | 0.18 | 97.5 [94.3–98.9] | 1.5 [0.5–4.3] | 0.5/1.0 | 0.0 | 1.5 | 39 |
| ext_doclaynet | photo_hard | uniform | docangle | 200 (200) | 0.19 | 89.5 [84.5–93.0] | 8.5 [5.4–13.2] | 5.0/3.5 | 6.0 | 4.8 | 50 |
| ext_doclaynet | photo_hard | uniform | legacy_v1 | 200 (200) | 0.18 | 89.0 [83.9–92.6] | 8.5 [5.4–13.2] | 4.5/4.0 | 0.0 | 8.5 | 38 |
