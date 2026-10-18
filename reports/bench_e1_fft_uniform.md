# Benchmark e1_fft_uniform

commit `ce2bf6d` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| az | scan | uniform | docangle | 200 (100) | 0.16 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 41 |
| az | scan | uniform | docangle_fft | 200 (100) | 0.01 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 30 |
| az | photo_hard | uniform | docangle | 200 (100) | 0.17 | 99.5 [97.2–99.9] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.0 | 0.0 | 36 |
| az | photo_hard | uniform | docangle_fft | 200 (100) | 0.01 | 99.5 [97.2–99.9] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.0 | 0.0 | 29 |
| invoices | scan | uniform | docangle | 200 (100) | 0.27 | 94.5 [90.4–96.9] | 1.5 [0.5–4.3] | 0.5/1.0 | 1.5 | 1.0 | 35 |
| invoices | scan | uniform | docangle_fft | 200 (100) | 0.24 | 94.0 [89.8–96.5] | 1.5 [0.5–4.3] | 0.5/1.0 | 2.0 | 1.0 | 28 |
| invoices | photo_hard | uniform | docangle | 200 (100) | 0.26 | 93.5 [89.2–96.2] | 2.0 [0.8–5.0] | 0.5/1.5 | 4.5 | 1.6 | 39 |
| invoices | photo_hard | uniform | docangle_fft | 200 (100) | 0.09 | 94.0 [89.8–96.5] | 2.0 [0.8–5.0] | 0.5/1.5 | 4.0 | 1.6 | 33 |
| tobacco_cert | scan | uniform | docangle | 200 (159) | 0.29 | 93.0 [88.6–95.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 42 |
| tobacco_cert | scan | uniform | docangle_fft | 200 (159) | 0.22 | 92.5 [88.0–95.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 34 |
| tobacco_cert | photo_hard | uniform | docangle | 200 (159) | 0.28 | 92.5 [88.0–95.4] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.0 | 0.0 | 36 |
| tobacco_cert | photo_hard | uniform | docangle_fft | 200 (159) | 0.07 | 97.5 [94.3–98.9] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.0 | 0.0 | 30 |
| rvl_heldout | scan | uniform | docangle | 200 (200) | 0.32 | 89.5 [84.5–93.0] | 0.5 [0.1–2.8] | 0.5/0.0 | 1.0 | 0.0 | 37 |
| rvl_heldout | scan | uniform | docangle_fft | 200 (200) | 0.27 | 89.0 [83.9–92.6] | 1.0 [0.3–3.6] | 0.5/0.5 | 1.5 | 0.0 | 30 |
| rvl_heldout | photo_hard | uniform | docangle | 200 (200) | 0.31 | 89.0 [83.9–92.6] | 0.5 [0.1–2.8] | 0.0/0.5 | 2.0 | 0.5 | 38 |
| rvl_heldout | photo_hard | uniform | docangle_fft | 200 (200) | 0.08 | 92.5 [88.0–95.4] | 1.0 [0.3–3.6] | 0.5/0.5 | 2.0 | 0.5 | 31 |
| ext_cord | scan | uniform | docangle | 200 (200) | 0.30 | 77.5 [71.2–82.7] | 4.5 [2.4–8.3] | 4.0/0.5 | 18.0 | 0.6 | 34 |
| ext_cord | scan | uniform | docangle_fft | 200 (200) | 0.06 | 87.5 [82.2–91.4] | 4.5 [2.4–8.3] | 4.0/0.5 | 19.0 | 0.0 | 32 |
| ext_cord | photo_hard | uniform | docangle | 200 (200) | 0.69 | 61.5 [54.6–68.0] | 4.5 [2.4–8.3] | 3.0/1.5 | 39.0 | 0.0 | 33 |
| ext_cord | photo_hard | uniform | docangle_fft | 200 (200) | 0.05 | 86.0 [80.5–90.1] | 4.5 [2.4–8.3] | 3.0/1.5 | 33.0 | 0.0 | 31 |
| ext_doclaynet | scan | uniform | docangle | 200 (200) | 0.16 | 98.5 [95.7–99.5] | 1.0 [0.3–3.6] | 0.0/1.0 | 3.0 | 0.0 | 46 |
| ext_doclaynet | scan | uniform | docangle_fft | 200 (200) | 0.01 | 99.0 [96.4–99.7] | 0.5 [0.1–2.8] | 0.0/0.5 | 2.5 | 0.0 | 34 |
| ext_doclaynet | photo_hard | uniform | docangle | 200 (200) | 0.18 | 91.5 [86.8–94.6] | 5.0 [2.7–9.0] | 3.0/2.0 | 6.0 | 1.6 | 44 |
| ext_doclaynet | photo_hard | uniform | docangle_fft | 200 (200) | 0.01 | 94.0 [89.8–96.5] | 5.5 [3.1–9.6] | 3.5/2.0 | 6.5 | 1.6 | 34 |
