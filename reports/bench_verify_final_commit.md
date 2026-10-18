# Benchmark verify_final_commit

commit `1d12687` · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.31.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| az | scan | uniform | docangle | 300 (100) | 0.14 | 100.0 [98.7–100.0] | 0.0 [0.0–1.3] | 0.0/0.0 | 0.0 | 0.0 | 44 |
| az | photo_hard | uniform | docangle | 300 (100) | 0.17 | 99.7 [98.1–99.9] | 0.0 [0.0–1.3] | 0.0/0.0 | 0.7 | 0.0 | 41 |
| invoices | scan | uniform | docangle | 300 (100) | 0.28 | 95.0 [91.9–96.9] | 1.3 [0.5–3.4] | 0.3/1.0 | 1.0 | 1.0 | 38 |
| invoices | photo_hard | uniform | docangle | 300 (100) | 0.26 | 93.7 [90.3–95.9] | 1.7 [0.7–3.8] | 0.3/1.3 | 3.7 | 1.4 | 38 |
