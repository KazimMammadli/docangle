# 11. Decision log

Every idea that was tried, how it was judged and what was decided. "Adopted" means it is in the default pipeline; "opt-in" means it exists behind a switch and is off by default; "rejected" means the code was removed or never merged. Evidence is a section of the [lab notebook](../reports/FINAL_REPORT.md) (§N) unless a file is named. All comparisons use the paired protocol of [chapter 4](04-evaluation-protocol.md). Versions are the package versions in [`CHANGELOG.md`](../CHANGELOG.md).

## 11.1 Quadrant decision

| idea | result | decision |
|---|---|---|
| PP-LCNet plus an own classifier, summed log-posteriors (v3/v4) | quadrant errors on 5603 non-ambiguous cases: PP-LCNet alone 382, own v4 alone 36, both 25 (§12) | **adopted** |
| the own classifier retrained with real phone photos (CORD train) and DocLayNet pages (v4) | CORD hard-photo flips 32.5 % to 4.5 %, accepted 14.9 % to 0 %; other pools unchanged (§8) | **adopted** |
| 12 views (PP-LCNet centre + full crops × 4 rotations, own × 4) instead of 6 | 46 against 51 flips, no gain for +25 ms (§8, §15) | rejected |
| the two classifiers run in parallel threads | same output, faster (the saving was not stored) | **adopted** |
| fit voter weights and temperature | log-loss 0.0170 to 0.0129, quadrant errors unchanged at 25 (§11) | rejected (weights stay at 1) |
| docTR page-orientation model as a third voter | alone 295 errors against 36 for the own classifier; fusing never reduces errors; +17 ms (§12) | rejected |
| EfficientNetV2 orientation model (Hugging Face, MIT) as a third voter | alone 47 errors in 447 cases against 2 for the own classifier and 0 for the pair; fusing at weight 0.25 raises errors 0 to 1; +191 ms (`reports/exp_duarte_voter.txt`; the tool alone is compared in [chapter 5](05-comparison.md)) | rejected |
| removing PP-LCNet | accepted flips +7 [+1, +15] at equal review rate; saves 3 ms (§15) | rejected |
| the 360° regressor fallback | neutral for accepted flips; without it the displayed angle is better on the simulated pools (51 to 25 flips) and worse on whole SmartDoc frames (59 to 85) (§15) | kept (neutral) |
| TOO_FEW_LINES pages report the classifier's angle instead of the regressor's | the gate changes only 6 of 900 cases (regressor flips 5 to 0, confidence and review identical); the dev dump has 59 flips with the regressor's angle against 51; SmartDoc cropped flips 25 to 14 (§15) | **adopted** (v4.3.1) |

## 11.2 Fine tilt

| idea | result | decision |
|---|---|---|
| ±45° wrap in the line-angle estimator (circular mean of 4θ) | pass-1 errors > 5° 18 to 7; ≤ 1° 93.0 to 94.0 % (§8) | **adopted** |
| weight Hough lines by length | ≤ 1° fell to 66-89 % on photo cells: long desk and page edges dominate (§8) | rejected |
| global projection-profile estimator as arbiter or as pass 2 | worse than Hough (54 against 7 errors > 5°; 29 against 21) (§7, §8) | rejected |
| Hough pass 2 plus projection polish | ≤ 0.5° better on scans, ≤ 1° worse on photos, +10 ms | rejected |
| **Fourier radial projection replaces both Hough passes** | ≤ 1° 90.2 to 93.8 %, errors > 5° 95 to 51 in 2800 paired cases, 7-8 ms faster; DISE-2021 ≤ 1° 89.3 to 94.3 % (§10) | **adopted** (v4.2.0) |
| Hough-versus-Fourier disagreement as a confidence alarm | fired 6 times in 1260 cases, 5 on correct pages | opt-in, off (`fft_alarm_deg`) |
| 800 px instead of 1000 px working canvas | −6 ms, only 44.6 % of angles within 0.05° of the baseline | rejected by the accuracy guard (§8) |
| Hough pass 1 in strips | a small saving (not stored) but the line set changes; Hough estimator only | opt-in (`pass1_strips`) |
| speculative pass 2 (Hough while the classifiers run) | −7 ms, flips 39 against 39 | adopted for v4.1; made obsolete by the Fourier tilt |

## 11.3 Confidence and review

| idea | result | decision |
|---|---|---|
| the original confidence `0.55·posterior + 0.45·min(1, lines/80)` | structurally unable to review a page with 80 or more lines; never calibrated (§11) | replaced |
| learned review score (logistic regression, nine features) | accepted flips 13 to 3-5 at the old review rate (`reports/calibrate_e2.txt`); not compared with the new rule at an equal review rate, and the parameter-free rule needs no fitting | not adopted |
| **posterior of the chosen quadrant minus 0.30 if the regressor acted; review below 0.90** | external pools: review 9.7 % to 3.8 %, accepted flips 10 to 6; primary pools: small, unproven gain (§11) | **adopted** (v4.3.0) |
| line count as a review signal | no signal for fine-angle errors in any line-count bucket | dropped (`TOO_FEW_LINES` stays as a separate gate) |

## 11.4 Optional features

| idea | result | decision |
|---|---|---|
| multi-page consensus | flips 6 to 2, accepted flips 3 to 0, reviews 23 to 6 when pages share an orientation; an odd page in ten is always reviewed (§13) | opt-in |
| document finder for photos with much background | SmartDoc whole frames ≤ 1° 42.9 to 73.1 %, flips 6.4 to 3.9 % (926 frames, every 25th; chapter 5 uses every 50th, 420 frames: 46.4 to 75.5 %, 7.6 to 3.3 %), but a few angles of normal pages move (§22) | opt-in (`doc_crop`) |
| faster profiles (fewer views) | one own view instead of two: −12 % time, +31 % throughput, non-inferior on the dev dump; profiles that also drop PP-LCNet views (−17 to −20 % time, +49 to +63 % throughput) are riskier, and removing PP-LCNet costs +7 accepted flips [+1, +15]; all unproven on real photos (§15, chapter 8.5) | opt-in |
| GPU for the three ONNX models | identical results, 2× faster, half the CPU (§19) | opt-in (`ort_provider="cuda"`) |
| PDF JPEG fast path | 6.9 s to 2.7 s for a synthetic 100-page JPEG-scan PDF; angles within 0.05° on 98 % | opt-in (`pdf_fast_path`) |

## 11.5 Robustness, speed and output quality

| change | evidence | decision |
|---|---|---|
| lock around every PDFium call | threaded batches crashed or returned unreadable pages (90 of 300 renders failed without it) (§16) | **fixed** (v4.3.1) |
| lean batch settings (ONNX threads do not spin, OpenCV on one thread) | identical results on 96 pages, 30-35 % less CPU (§18) | adopted in the CLI for batches |
| classifier pre-processing: resize once, rotate the small image, table-lookup normalisation | 700 cases: angles 100 % identical, confidence within 0.002, 40.2 to 37.7 ms (§4.4) | **adopted** |
| decode large JPEGs at reduced scale | −10 ms, accuracy equal within noise (§8) | adopted |
| straightened image: lossless quarter turns, no resampling for tilts < 0.1°, bicubic otherwise | sharpness kept 53 % to 73-77 % per pass; no OCR effect (PaddleOCR 99.1 against 99.1, Tesseract 97.2 against 97.0) (§20) | **adopted** as data hygiene (v4.3.2) |
| load pip-installed CUDA libraries without `LD_LIBRARY_PATH`; refuse to run silently on the CPU | ONNX Runtime used to fall back silently (§21) | **fixed** (v4.3.3) |
| crop the white border added by straightening before the OCR | 45° pages double in area, OCR time follows (r = 0.92), a 6 GB GPU ran out of memory once (§21) | adopted in the OCR tool |
| static int8 quantisation of both classifiers (QDQ, per-channel weights, percentile calibration on 420 and 840 tensors taken from the real pipeline; `bench/quantize_models.py`) | files 16.8 to 4.7 MB and 6.8 to 1.9 MB, but the class changed for 9.5 % (own classifier) and 18.7 % (PP-LCNet) of fresh views, and on this CPU (AVX2, no int8 dot-product instructions) int8 was slower: 7.1 to 8.0 ms and 4.2 to 19.1 ms per call (`reports/int8_quantization.txt`, re-measured on mains power). Accuracy guard on 400 cases: flips 4 to 11, ≤ 1° 98.2 to 96.5 %, only 98.0 % of angles within 0.05° (99 % required), worse by more than 0.25° in 7 cases and better in none, 29.7 to 40.3 ms (`reports/guard_int8.txt`) | rejected (this setting on this CPU; other settings and int8 hardware not tried) |

## 11.6 Other open-source tools

DocOrient, PP-DocLayoutV3 as a voter, docTR, the EfficientNetV2 model, Tesseract OSD and the textbook `minAreaRect` deskew were each measured; none was adopted. The controlled comparison is [chapter 5](05-comparison.md); the survey of estimators and reliability tricks that preceded the experiments is [`reports/METHOD_RESEARCH.md`](../reports/METHOD_RESEARCH.md).

## 11.7 Ideas not tried

| idea | why not yet |
|---|---|
| ascender/descender and mark-above/below cues as a veto to review | a survey measurement (not reproduced here) caught 9 of 18 upside-down flips on DISE-2021 at a cost of 3.6 % extra review; it needs a half-scale crop and was judged second to getting real data first |
| native-resolution glyph or patch voter, attention-based pooling | highest ceiling, most work; only worthwhile if flips remain on real photos |
| hard-case training data (binarised, dithered, typewriter scans, covers) | depends on whether the target documents contain such pages |
| a Tesseract engine run in parallel processes in the OCR tool | not needed for correctness |
| calibration of the confidence against fine-angle uncertainty | no data with real fine-angle ground truth |

## 11.8 Audit trail

The first step of the project was an audit of the predecessor (20 findings, F-01 to F-20: among them an OpenCV 5 crash, 180° flips under-reported, a silent missing model, an unvalidated confidence, training data of unknown certification, irreproducible models and test data, circular evaluation); each was either fixed in `docangle` or recorded as a known limit in [chapter 10](10-limitations.md). Behaviour-preserving clean-ups proposed by the redundancy analysis but not done (each would need an equivalence proof): split `analyze()` into a Fourier and a Hough path, one image loader instead of three, (the error instead of a silent `orient_cls_v1` fallback was done: a missing own classifier raises `ModelNotFoundError`).
