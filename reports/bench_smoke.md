# Benchmark smoke

commit `9a75ecb` (dirty) · AMD Ryzen 9 5980HX with Radeon Graphics · 16 cores · opencv 4.14.0 · ort 1.30.0 · python 3.14.6

| dataset | level | angles | candidate | n (pages) | median ° | ≤1° % [95% CI] | flip % [95% CI] | 180°/90° | review % | accepted flip % | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| az | scan | uniform | docangle | 60 (60) | 0.16 | 100.0 [94.0–100.0] | 0.0 [0.0–6.0] | 0.0/0.0 | 0.0 | 0.0 | 36 |
| az | scan | uniform | legacy_v1 | 60 (60) | 0.13 | 100.0 [94.0–100.0] | 0.0 [0.0–6.0] | 0.0/0.0 | 0.0 | 0.0 | 36 |
| az | photo_easy | uniform | docangle | 60 (60) | 0.14 | 100.0 [94.0–100.0] | 0.0 [0.0–6.0] | 0.0/0.0 | 1.7 | 0.0 | 33 |
| az | photo_easy | uniform | legacy_v1 | 60 (60) | 0.16 | 100.0 [94.0–100.0] | 0.0 [0.0–6.0] | 0.0/0.0 | 0.0 | 0.0 | 33 |
| az | photo_hard | uniform | docangle | 60 (60) | 0.19 | 100.0 [94.0–100.0] | 0.0 [0.0–6.0] | 0.0/0.0 | 0.0 | 0.0 | 32 |
| az | photo_hard | uniform | legacy_v1 | 60 (60) | 0.19 | 100.0 [94.0–100.0] | 0.0 [0.0–6.0] | 0.0/0.0 | 0.0 | 0.0 | 34 |
