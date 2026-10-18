# Benchmark step4_default_vs_full_vs_c8l

commit `515fae7` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| invoices | scan | uniform | docangle | 200 (100) | 0.29 | 94.5 [90.4–96.9] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 46 |
| invoices | scan | uniform | docangle_full | 200 (100) | 0.28 | 94.5 [90.4–96.9] | 1.0 [0.3–3.6] | 0.0/1.0 | 1.0 | 1.0 | 75 |
| invoices | scan | uniform | legacy_v1 | 200 (100) | 0.27 | 92.0 [87.4–95.0] | 6.5 [3.8–10.8] | 4.0/2.5 | 0.0 | 6.5 | 40 |
| invoices | photo_hard | uniform | docangle | 200 (100) | 0.23 | 90.0 [85.1–93.4] | 2.5 [1.1–5.7] | 0.5/2.0 | 3.5 | 1.6 | 44 |
| invoices | photo_hard | uniform | docangle_full | 200 (100) | 0.27 | 92.0 [87.4–95.0] | 2.0 [0.8–5.0] | 0.0/2.0 | 2.5 | 1.0 | 72 |
| invoices | photo_hard | uniform | legacy_v1 | 200 (100) | 0.30 | 82.5 [76.6–87.1] | 11.0 [7.4–16.1] | 5.0/6.0 | 0.0 | 11.0 | 42 |
| rvl_heldout | scan | uniform | docangle | 200 (200) | 0.32 | 87.0 [81.6–91.0] | 0.5 [0.1–2.8] | 0.0/0.5 | 1.0 | 0.0 | 47 |
| rvl_heldout | scan | uniform | docangle_full | 200 (200) | 0.34 | 88.0 [82.8–91.8] | 0.5 [0.1–2.8] | 0.0/0.5 | 2.5 | 0.0 | 78 |
| rvl_heldout | scan | uniform | legacy_v1 | 200 (200) | 0.28 | 85.5 [80.0–89.7] | 4.5 [2.4–8.3] | 2.5/2.0 | 0.0 | 4.5 | 43 |
| rvl_heldout | photo_hard | uniform | docangle | 200 (200) | 0.25 | 90.0 [85.1–93.4] | 0.5 [0.1–2.8] | 0.5/0.0 | 2.0 | 0.0 | 44 |
| rvl_heldout | photo_hard | uniform | docangle_full | 200 (200) | 0.32 | 89.0 [83.9–92.6] | 0.5 [0.1–2.8] | 0.5/0.0 | 3.0 | 0.0 | 73 |
| rvl_heldout | photo_hard | uniform | legacy_v1 | 200 (200) | 0.40 | 78.0 [71.8–83.2] | 9.5 [6.2–14.4] | 7.0/2.5 | 0.0 | 9.5 | 42 |
| tobacco_cert | scan | uniform | docangle | 200 (159) | 0.28 | 89.5 [84.5–93.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 47 |
| tobacco_cert | scan | uniform | docangle_full | 200 (159) | 0.29 | 92.0 [87.4–95.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.5 | 0.0 | 79 |
| tobacco_cert | scan | uniform | legacy_v1 | 200 (159) | 0.23 | 92.0 [87.4–95.0] | 0.5 [0.1–2.8] | 0.5/0.0 | 0.0 | 0.5 | 37 |
| tobacco_cert | photo_hard | uniform | docangle | 200 (159) | 0.30 | 89.5 [84.5–93.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.0 | 0.0 | 46 |
| tobacco_cert | photo_hard | uniform | docangle_full | 200 (159) | 0.28 | 90.5 [85.6–93.8] | 0.0 [0.0–1.9] | 0.0/0.0 | 1.5 | 0.0 | 75 |
| tobacco_cert | photo_hard | uniform | legacy_v1 | 200 (159) | 0.31 | 88.5 [83.3–92.2] | 2.0 [0.8–5.0] | 1.0/1.0 | 0.0 | 2.0 | 37 |
| az | scan | uniform | docangle | 200 (100) | 0.13 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 49 |
| az | scan | uniform | docangle_full | 200 (100) | 0.16 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 82 |
| az | scan | uniform | legacy_v1 | 200 (100) | 0.14 | 100.0 [98.1–100.0] | 0.0 [0.0–1.9] | 0.0/0.0 | 0.0 | 0.0 | 36 |
| az | photo_hard | uniform | docangle | 200 (100) | 0.16 | 96.0 [92.3–98.0] | 1.0 [0.3–3.6] | 1.0/0.0 | 1.5 | 1.0 | 47 |
| az | photo_hard | uniform | docangle_full | 200 (100) | 0.16 | 99.0 [96.4–99.7] | 0.5 [0.1–2.8] | 0.5/0.0 | 1.5 | 0.5 | 76 |
| az | photo_hard | uniform | legacy_v1 | 200 (100) | 0.15 | 99.5 [97.2–99.9] | 0.5 [0.1–2.8] | 0.5/0.0 | 0.0 | 0.5 | 35 |
