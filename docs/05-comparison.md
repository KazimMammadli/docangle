# 5. Comparison with other open-source tools

This chapter answers one question: **if you need to know how a page is turned, which open-source tool should you use, and what do you get for the price?** It compares docangle with the open-source orientation tools that could be installed and run here without registration or a server (skew-only tools and the ones that were not run are listed in 5.3; the search is in [`reports/METHOD_RESEARCH.md`](../reports/METHOD_RESEARCH.md)), on the same input images, on the same machine, on the same task. The rules are written down in 5.2 so that anyone can run the comparison again or add a tool, and the threats to its validity, including the ones that favour docangle, are in 5.5.

Every table below between a `generated` mark is produced by `python -m bench.compare_report fill-docs` from the stored answers of every tool to every case (`reports/benchmark/raw_*.json.gz`); nothing in them is typed by hand, and a unit test fails if they drift from the stored results.

## 5.1 The result in one table

Wrong-quadrant rate in %, lower is better, tools exactly as their authors ship them (the page reaches each tool as an application would hold it). Intervals, paired counts and every pool are in 5.4.

<!-- generated:summary -->
| tool | exact quarter turns | hand-held photo (quadrant ± 25°) | any angle | real phone frames, page cut out | real phone frames, whole frame | median ms per page, any angle |
|---|---|---|---|---|---|---|
| docangle | 0.0 % | 0.5 % | 0.8 % | 1.4 % | 7.6 % | 28 |
| PP-LCNet | 1.0 % | 23.2 % | 38.7 % | 18.3 % | 27.9 % | 4 |
| docTR | 4.0 % | 6.0 % | 10.1 % | 5.2 % | 14.8 % | 15 |
| DocOrient | 19.4 % | 78.6 % | 82.4 % | 30.2 % | 52.4 % | 62 |
| EfficientNetV2 | 9.3 % | 17.6 % | 25.4 % | 6.4 % | 18.8 % | 121 |
| Tesseract OSD | 35.3 % | 64.2 % | 70.3 % | 95.5 % | 97.4 % | 472 |
<!-- /generated -->

* **docangle makes the fewest wrong-quadrant errors in every setting, and on the simulated sets the margin grows with tilt.** On exact quarter turns 0.0 % of 700 cases are wrong; on hand-held photographs 0.5 %; when the page may be turned by any angle 0.8 %; on real phone frames with the page cut out 1.4 %. The best other tool makes 1.0 % (PP-LCNet), 6.0 % (docTR), 10.1 % (docTR) and 5.2 % (docTR) in the same four settings. Over pages, each of these differences is significant except the first, the one with PP-LCNet on exact quarter turns.
* **Only on clean, exactly turned pages is the field close.** PP-LCNet, one view, 4 ms, makes 7 errors in 700 such cases against none for docangle, on four pages: not a significant difference. If the pages are exact quarter turns and an unannounced error in 1 % of them is acceptable, PP-LCNet alone is the much cheaper choice ([5.4.10](#5410-which-tool-for-which-job)).
* **Tilt is what breaks the others, and docangle's tilt step explains part of the difference: most of it for PP-LCNet and DocOrient, less than half for EfficientNetV2 and docTR (5.4.3).** PP-LCNet goes from 1.0 % wrong on exact turns to 23.2 % on hand-held photographs and 38.7 % at any angle. Behind docangle's own straightening it makes 9.3 % at any angle, and the best of the others, docTR, 5.9 %: still seven times docangle's rate. On whole phone frames, where the page covers a median 11.7 % of the picture and the tilt step is unreliable, the "straightened" rows are no longer a best case: PP-LCNet and EfficientNetV2 gain a little, docTR collapses (14.8 % to 61.0 %) and DocOrient gets worse (52.4 % to 60.7 %) ([5.4.6](#546-real-camera-footage-smartdoc-2015)).
* **docangle is not the best at everything.** On whole phone frames without its page finder docTR is right on 27 cases where docangle is wrong (docangle 7.6 %, docTR 14.8 %; the other direction: 57 cases). The older Hough estimator measures the tilt of whole frames better than the Fourier one (56 % against 46 % within 1°). And docangle needs 24 to 28 ms per page where PP-LCNet needs 4 and docTR 12 to 15.
* **The review flag is part of what is measured.** docangle sends 1.1 to 2.7 % of the clean and simulated pages (7 % of the cut-out and 23 % of the whole phone frames) to a person and is wrong on 0.0 to 0.3 % of the rest (1.2 % on whole phone frames). The scores of the other tools separate their errors far less well: at the same share docTR is still wrong on 3.5 to 8.9 % of the clean and simulated pages, and to reach docangle's rate it would have to hold back 54 to 69 % of them. DocOrient never flags a page; Tesseract stays silent on 17 to 38 % of the pages, and on 84 to 88 % of low-resolution phone frames.
* **None of the other tools gives a fine angle.** docangle's is within 1° for 96 to 97 % of simulated pages and 77 % of real frames with the page cut out; the textbook `minAreaRect` deskew manages 43 to 45 % and 13 %.

## 5.2 The rules of the comparison

| # | rule | why |
|---|---|---|
| 1 | **Same input.** Each case image is produced once (fixed seeds) and handed, as the same BGR `uint8` array, to every tool in the same process. No tool sees the ground truth, the file name, a crop or another tool's answer. | the only difference left is the tool |
| 2 | **Each tool prepares its own input**, exactly as its authors ship it (resize, crop, normalisation: the code is in `bench/compare_open_models.py`, one class per tool). What each output index means (which logit is which rotation) was *measured* on exact quarter turns before the run, never assumed (`bench/exp_duarte.py`, `bench/docorient_quarter.py`). | a mis-read class order would make a good tool look bad |
| 3 | **Same task.** The *quadrant task*: by which multiple of 90° is the page turned? It is the one question every tool can answer. A tool that gives no answer, or crashes, is counted wrong. Cases within 5° of a quadrant boundary (±45°, ±135°) are left out: the truth is a matter of convention there. The fine angle is compared only among the tools that give one. | one number per question |
| 4 | **Several kinds of page, so that no setting suits only one side.** Exact quarter turns of clean pages: what a four-class model is built for, no tilt and no photographic damage. Hand-held photographs: one quadrant plus a tilt of up to ±25°. Photographs turned by any angle. Real phone frames (SmartDoc), whole and with the page cut out. | the home ground of the others comes first |
| 5 | **Best case for the others.** Every third-party classifier is also run behind docangle's own straightening ("+ straightening"): the page reaches it with the tilt taken out (the estimate is within 1° in about 96 % of cases), the situation a four-class model is designed for. Those rows show how much of docangle's advantage is the tilt step and how much is the classifier. They are not a product you can download. | do not punish a tool for tilt it was never meant to handle |
| 6 | **Same machine, same conditions.** CPU only, two threads for every ONNX session the harness builds (docangle's own default; DocOrient builds its own session with options that the harness does not control), one case at a time, models loaded and warm before timing. The time is the wall time of the whole call including the tool's own preparation; docangle runs three ONNX sessions and a Hough thread at once and uses about 178 ms of CPU time for 27 ms of wall time (`reports/profile_stages_v4_4.txt`), so on a busy machine its share of the CPU is larger than its share of the wall time. Tesseract is a program, not a library: its time includes writing the PNG and starting the process. | comparable times |
| 7 | **Intervals count pages.** 95 % Wilson intervals with the number of pages as sample size ([chapter 4.4](04-evaluation-protocol.md)); paired counts say on how many identical cases docangle was right and the other tool wrong, and the reverse. | the copies of one page are not independent |
| 8 | **Everyone may hold pages back.** docangle's rate counts a page even when its review flag was set. A tool with a score may hold back its least certain pages as well, at the same share of pages as docangle (equal review rate, 5.4.7); DocOrient's own "not reliable" flag and Tesseract's silence are shown at their own operating point. | the review flag is part of docangle, so the others get the same chance |
| 9 | **Versions and hardware are stored.** Every raw file records the Python library versions (DocOrient's as a fixed label), the CPU model and the arguments of the run; the Tesseract version (5.5.3) and the model files are named in 5.3, not in the raw files. | a result can be checked |

**Checks that no tool is handicapped.**

* **Repeatability.** The three simulated modes were run twice (the first runs are in the git history: the quarter turns in commit `d096c99`, the hand-held and any-angle sets in `2e024d7`). Every answer that exists in both runs was identical, compared with a script over the stored files: 5 600 quadrant answers for the quarter turns (8 tools), 10 080 for the hand-held set (12 tools), 6 720 for the any-angle set (8 tools; the straightened variants of this set had no first run); the fine angles of docangle, its Hough variant and the minAreaRect deskew were identical too. The SmartDoc mode was run once for the stored result: its repeatability was not checked. Timings differ between runs.
* **Tesseract and the missing resolution.** Images that come from OpenCV carry no resolution, and Tesseract warns about it in every call. Telling it `--dpi 150` or `--dpi 300` changed none of its 160 answers on a sample of exact quarter turns (`bench/tesseract_dpi_check.py`, [`reports/tesseract_dpi_check.txt`](../reports/tesseract_dpi_check.txt)), so leaving the resolution out does not handicap it.
* **Output conventions** (which index is which rotation, which sign Tesseract's "Rotate" has) were measured on exact quarter turns before the run; the bench scripts that do it are named in rule 2.
* **No help from the ground truth or from docangle.** Every tool gets the same array. The only crops are the SmartDoc "document cut out" set, which every tool receives, and the rows marked "+ straightening", whose names say what was done to the page.

## 5.3 The tools

| tool (name in the tables) | what it is | what it answers | licence | size | what it reads | claim of its authors |
|---|---|---|---|---|---|---|
| **docangle** 4.4 | this repository: Fourier tilt, PP-LCNet on 4 rotated views, an own MobileNetV3 on 2 views, a 360° regressor as rare fallback, a review rule | angle in [-180°, 180°], quadrant, confidence, review flag | MIT (code); weights: [`models/README.md`](../models/README.md) | 36 MB, three ONNX models (24 MB without the fallback regressor) | a grey canvas of at most 1000 px | chapter 6 |
| **PP-LCNet** | `PP-LCNet_x1_0_doc_ori` of PaddleOCR / PaddleX, converted to ONNX unchanged, **one view** | quadrant | Apache-2.0 | 6.8 MB | short side 256 px, centre crop 224 × 224 | 99.06 % on their test set |
| **docTR** | `mobilenet_v3_small_page_orientation` (OnnxTR release v0.6.0) | quadrant | Apache-2.0 | 6.1 MB | letterbox to 512 × 512 | 64 % (a published figure without a named source, recorded in `reports/FINAL_REPORT.md` §8; not re-run) |
| **DocOrient** 0.4.1 | PyPI `docorient`: an energy-axis test plus a MobileNetV2 flip classifier | quadrant, and a `reliable` flag | MIT | 8.9 MB | its own preparation | 98 % (its README) |
| **EfficientNetV2** | `DuarteBarbosa/deep-image-orientation-detection`, EfficientNetV2-S, ONNX, **one view; trained on photographs, not on documents** | quadrant | MIT | 80.6 MB | resized to 416 × 416, centre crop 384 | 98.82 % on photographs (their validation) |
| **Tesseract OSD** 5.5.3 | `tesseract --psm 0 -l osd`, the orientation and script detection of the OCR engine | quadrant ("Rotate: N") and an unnormalised confidence; stays silent when it cannot decide | Apache-2.0 | 10.6 MB `osd.traineddata` (plus the program) | the whole page as a PNG file | 49 % (a published figure without a named source, recorded in `reports/FINAL_REPORT.md` §8; not re-run) |
| minAreaRect | the textbook `cv2.minAreaRect` deskew of OpenCV tutorials | tilt modulo 90° only | Apache-2.0 (OpenCV) | none | the whole page | none |
| docangle Hough | docangle's own earlier fine-tilt estimator (v4.1, Hough lines) | tilt modulo 90° only | MIT | none | grey canvas | none |

The last two are baselines for the *fine angle* only (5.4.8). docangle with `doc_crop` (the opt-in page finder, [chapter 2](02-design.md)) takes part in the real-camera tables only.

**Seen but not measured**, with the reason:

| tool | why not |
|---|---|
| rotdet v2 | GPL-3.0; its own 90 % was measured on 164 pages labelled by a language model; not downloaded |
| olmOCR, other vision-language models | a 7-billion-parameter model that also outputs a rotation; GPU-heavy, quadrant only |
| Seeing Straight (arXiv 2511.04161) | no code or weights found |
| PaddleOCR document pre-processor | its orientation stage *is* PP-LCNet (measured above); its built-in modules (orientation, unwarping, text lines, measured together) damaged tilted pages in an earlier test ([lab notebook](../reports/FINAL_REPORT.md) §19) |
| jdeskew, `deskew`, `hough` | fine skew only; docangle's Fourier tilt follows the method of the jdeskew paper (our own implementation, `docangle/fftskew.py`), so running the original code would check our implementation against theirs (`pip install jdeskew deskew`); not run here |
| Chuckame/deep-image-orientation-angle-detection (ViT, continuous angle) | trained on photographs, no published metrics for documents; not measured |
| neural-deskew | learns a combination of three classical skew estimators; no weights published |
| general photo orientation models other than EfficientNetV2 | trained on photographs; one of them is in the tables as the representative |

## 5.4 Results

Each subsection gives the tables first and what they show after; every table is generated from the stored answers, and `reports/benchmark/RESULTS.md` holds the same tables for every mode in one file. The column "same cases" counts the cases (and the pages) on which only docangle or only the other tool was right, with an exact two-sided sign test over pages.

### 5.4.1 Exact quarter turns of clean pages: the home ground of the four-class models

700 cases: 175 pages from seven pools, each turned by 0°, 90°, 180° and 270° with `np.rot90`, so nothing is resampled and nothing is degraded.

<!-- generated:quarter/main/quadrant -->
| tool | cases | wrong quadrant % [95 % interval] | no answer | median ms | p95 ms | same cases: docangle-only right / this-only right (pages: docangle better / this better, sign test) |
|---|---|---|---|---|---|---|
| docangle | 700 | **0.0** [0.0, 2.1] | 0 | 27 | 40 | — |
| PP-LCNet | 700 | **1.0** [0.3, 3.9] | 0 | 4 | 5 | 7 / 0 (pages 4 / 0, p = 0.125) |
| docTR | 700 | **4.0** [2.0, 8.0] | 0 | 13 | 19 | 28 / 0 (pages 15 / 0, p < 0.001) |
| DocOrient | 700 | **19.4** [14.2, 25.9] | 0 | 26 | 136 | 136 / 0 (pages 36 / 0, p < 0.001) |
| EfficientNetV2 | 700 | **9.3** [5.8, 14.5] | 0 | 112 | 155 | 65 / 0 (pages 35 / 0, p < 0.001) |
| Tesseract OSD | 700 | **35.3** [28.6, 42.6] | 119 | 326 | 766 | 247 / 0 (pages 89 / 0, p < 0.001) |
<!-- /generated -->

<!-- generated:quarter/main/pool -->
| pool (cases) | docangle | PP-LCNet | docTR | DocOrient | EfficientNetV2 | Tesseract OSD |
|---|---|---|---|---|---|---|
| az (100) | 0.0 | 0.0 | 0.0 | 4.0 | 33.0 | 6.0 |
| ext_cord (100) | 0.0 | 4.0 | 8.0 | 72.0 | 13.0 | 68.0 |
| ext_doclaynet (100) | 0.0 | 0.0 | 3.0 | 2.0 | 4.0 | 33.0 |
| ext_funsd (100) | 0.0 | 1.0 | 2.0 | 4.0 | 1.0 | 39.0 |
| invoices (100) | 0.0 | 0.0 | 6.0 | 20.0 | 11.0 | 43.0 |
| rvl_heldout (100) | 0.0 | 2.0 | 7.0 | 18.0 | 3.0 | 58.0 |
| tobacco_cert (100) | 0.0 | 0.0 | 2.0 | 16.0 | 0.0 | 0.0 |
<!-- /generated -->

docangle made no error. PP-LCNet, which docangle itself uses as one of its voters, made seven (1.0 %), on four pages; the sign test over pages gives p = 0.125, so on clean exact quarter turns no difference between a single PP-LCNet view and docangle's six could be shown (four pages against none; that is not a proof of equivalence), and the single view is 6 to 7 times faster. Every other tool is significantly worse: docTR 4.0 %, EfficientNetV2 9.3 %, DocOrient 19.4 %, Tesseract 35.3 % (and silent on 17 % of the pages).

The pools show where each tool is weak. Receipts (`ext_cord`: narrow pages, little text) are the hardest pool for four of the five other tools: DocOrient 72 % wrong, Tesseract 68 %, EfficientNetV2 13 %, docTR 8 %, PP-LCNet 4 %. EfficientNetV2, which was trained on photographs, is the least predictable across pools: 0 % on `tobacco_cert`, 1 % on FUNSD, 33 % on the born-digital Azerbaijani pages. Tesseract is right on all of `tobacco_cert` (text-dense scans) and wrong on 58 % of the held-out invoice pages (`rvl_heldout`).

### 5.4.2 Hand-held photographs: a quadrant plus a tilt of up to 25°

840 cases: 280 pages × the three degradation levels, one of the four quadrants and a random tilt in ±25°.

<!-- generated:handheld/main/quadrant -->
| tool | cases | wrong quadrant % [95 % interval] | no answer | median ms | p95 ms | same cases: docangle-only right / this-only right (pages: docangle better / this better, sign test) |
|---|---|---|---|---|---|---|
| docangle | 840 | **0.5** [0.1, 2.2] | 0 | 27 | 36 | — |
| PP-LCNet | 840 | **23.2** [18.7, 28.5] | 0 | 4 | 5 | 194 / 3 (pages 140 / 1, p < 0.001) |
| docTR | 840 | **6.0** [3.7, 9.4] | 0 | 15 | 18 | 49 / 3 (pages 35 / 2, p < 0.001) |
| DocOrient | 840 | **78.6** [73.4, 83.0] | 0 | 54 | 112 | 657 / 1 (pages 272 / 0, p < 0.001) |
| EfficientNetV2 | 840 | **17.6** [13.6, 22.5] | 0 | 117 | 145 | 147 / 3 (pages 106 / 3, p < 0.001) |
| Tesseract OSD | 840 | **64.2** [58.4, 69.6] | 315 | 441 | 698 | 535 / 0 (pages 264 / 0, p < 0.001) |
| PP-LCNet + straightening | 840 | **9.2** [6.3, 13.1] | 0 | 12 | 14 | 73 / 0 (pages 56 / 0, p < 0.001) |
| docTR + straightening | 840 | **6.7** [4.3, 10.2] | 0 | 20 | 23 | 55 / 3 (pages 38 / 3, p < 0.001) |
| DocOrient + straightening | 840 | **35.6** [30.2, 41.4] | 0 | 38 | 47 | 297 / 2 (pages 166 / 0, p < 0.001) |
| EfficientNetV2 + straightening | 840 | **11.2** [8.0, 15.4] | 0 | 116 | 126 | 91 / 1 (pages 64 / 1, p < 0.001) |
<!-- /generated -->

<!-- generated:handheld/main/level -->
| level (cases) | docangle | PP-LCNet | docTR | DocOrient | EfficientNetV2 | Tesseract OSD | PP-LCNet + straightening | docTR + straightening | DocOrient + straightening | EfficientNetV2 + straightening |
|---|---|---|---|---|---|---|---|---|---|---|
| photo_easy (280) | 0.7 | 23.2 | 5.4 | 80.0 | 17.5 | 66.1 | 10.4 | 5.4 | 37.5 | 10.4 |
| photo_hard (280) | 0.7 | 26.8 | 6.4 | 81.4 | 22.5 | 81.8 | 12.5 | 8.9 | 45.7 | 15.4 |
| scan (280) | 0.0 | 19.6 | 6.1 | 74.3 | 12.9 | 44.6 | 4.6 | 5.7 | 23.6 | 7.9 |
<!-- /generated -->

<!-- generated:handheld/main/pool -->
| pool (cases) | docangle | PP-LCNet | docTR | DocOrient | EfficientNetV2 | Tesseract OSD | PP-LCNet + straightening | docTR + straightening | DocOrient + straightening | EfficientNetV2 + straightening |
|---|---|---|---|---|---|---|---|---|---|---|
| az (120) | 0.0 | 18.3 | 5.8 | 86.7 | 20.8 | 55.0 | 0.0 | 10.0 | 25.8 | 10.8 |
| ext_cord (120) | 0.8 | 37.5 | 11.7 | 91.7 | 17.5 | 83.3 | 28.3 | 10.0 | 95.0 | 11.7 |
| ext_doclaynet (120) | 1.7 | 25.0 | 6.7 | 68.3 | 14.2 | 59.2 | 5.8 | 5.0 | 18.3 | 10.0 |
| ext_funsd (120) | 0.0 | 15.8 | 0.8 | 72.5 | 8.3 | 63.3 | 2.5 | 0.8 | 17.5 | 0.8 |
| invoices (120) | 0.8 | 26.7 | 7.5 | 75.0 | 35.0 | 70.0 | 15.0 | 8.3 | 43.3 | 26.7 |
| rvl_heldout (120) | 0.0 | 23.3 | 5.0 | 70.8 | 22.5 | 68.3 | 12.5 | 5.0 | 30.8 | 17.5 |
| tobacco_cert (120) | 0.0 | 15.8 | 4.2 | 85.0 | 5.0 | 50.0 | 0.0 | 7.5 | 18.3 | 0.8 |
<!-- /generated -->

A tilt of up to 25° (small tilts were not tabulated separately) is enough to break the single-view classifiers: PP-LCNet goes from 1.0 % on exact turns to 23.2 %, DocOrient from 19.4 % to 78.6 %, EfficientNetV2 from 9.3 % to 17.6 %. docTR is the most robust of the others (4.0 % to 6.0 %). docangle made four errors in 840 cases (0.5 %), on four pages, three of them held back for review. The level table shows that photographic damage barely moves docTR (6.1 % on the clean `scan` level, 6.4 % on `photo_hard`) or docangle (0.0 % and 0.7 %), but it does move the others: Tesseract goes from 44.6 % to 81.8 %, EfficientNetV2 from 12.9 % to 22.5 % and PP-LCNet from 19.6 % to 26.8 %. docangle and docTR hardly change with the photographic damage; for the other four (PP-LCNet, DocOrient 74.3 to 81.4 %, EfficientNetV2, Tesseract) it matters as well.

### 5.4.3 Photographs turned by any angle

840 cases, the angle drawn uniformly from [-180°, 180°]; 752 of them are further than 5° from a quadrant boundary and count.

<!-- generated:uniform/main/quadrant -->
| tool | cases | wrong quadrant % [95 % interval] | no answer | median ms | p95 ms | same cases: docangle-only right / this-only right (pages: docangle better / this better, sign test) |
|---|---|---|---|---|---|---|
| docangle | 752 | **0.8** [0.2, 2.7] | 0 | 28 | 34 | — |
| PP-LCNet | 752 | **38.7** [33.2, 44.5] | 0 | 4 | 5 | 286 / 1 (pages 190 / 1, p < 0.001) |
| docTR | 752 | **10.1** [7.1, 14.2] | 0 | 15 | 18 | 75 / 5 (pages 62 / 4, p < 0.001) |
| DocOrient | 752 | **82.4** [77.6, 86.5] | 0 | 62 | 130 | 617 / 3 (pages 272 / 1, p < 0.001) |
| EfficientNetV2 | 752 | **25.4** [20.7, 30.8] | 0 | 121 | 150 | 189 / 4 (pages 142 / 3, p < 0.001) |
| Tesseract OSD | 752 | **70.3** [64.7, 75.4] | 286 | 472 | 784 | 524 / 1 (pages 266 / 0, p < 0.001) |
| PP-LCNet + straightening | 752 | **9.3** [6.4, 13.3] | 0 | 12 | 14 | 67 / 3 (pages 53 / 2, p < 0.001) |
| docTR + straightening | 752 | **5.9** [3.7, 9.2] | 0 | 20 | 23 | 44 / 6 (pages 37 / 4, p < 0.001) |
| DocOrient + straightening | 752 | **37.6** [32.2, 43.4] | 0 | 43 | 54 | 278 / 1 (pages 173 / 1, p < 0.001) |
| EfficientNetV2 + straightening | 752 | **14.2** [10.6, 18.8] | 0 | 119 | 128 | 106 / 5 (pages 74 / 4, p < 0.001) |
<!-- /generated -->

<!-- generated:uniform/main/level -->
| level (cases) | docangle | PP-LCNet | docTR | DocOrient | EfficientNetV2 | Tesseract OSD | PP-LCNet + straightening | docTR + straightening | DocOrient + straightening | EfficientNetV2 + straightening |
|---|---|---|---|---|---|---|---|---|---|---|
| photo_easy (257) | 0.8 | 42.0 | 10.5 | 84.8 | 29.2 | 75.9 | 12.1 | 5.4 | 39.7 | 14.4 |
| photo_hard (242) | 0.8 | 41.7 | 10.7 | 80.6 | 31.0 | 82.6 | 9.9 | 7.0 | 50.4 | 16.9 |
| scan (253) | 0.8 | 32.4 | 9.1 | 81.8 | 16.2 | 53.0 | 5.9 | 5.1 | 23.3 | 11.5 |
<!-- /generated -->

<!-- generated:uniform/main/pool -->
| pool (cases) | docangle | PP-LCNet | docTR | DocOrient | EfficientNetV2 | Tesseract OSD | PP-LCNet + straightening | docTR + straightening | DocOrient + straightening | EfficientNetV2 + straightening |
|---|---|---|---|---|---|---|---|---|---|---|
| az (110) | 0.0 | 30.0 | 3.6 | 85.5 | 30.0 | 64.5 | 0.9 | 5.5 | 28.2 | 21.8 |
| ext_cord (105) | 1.9 | 48.6 | 14.3 | 89.5 | 24.8 | 88.6 | 30.5 | 7.6 | 91.4 | 12.4 |
| ext_doclaynet (107) | 3.7 | 46.7 | 15.0 | 73.8 | 28.0 | 76.6 | 3.7 | 11.2 | 24.3 | 14.0 |
| ext_funsd (109) | 0.0 | 34.9 | 11.9 | 84.4 | 18.3 | 70.6 | 5.5 | 1.8 | 21.1 | 2.8 |
| invoices (104) | 0.0 | 42.3 | 12.5 | 76.9 | 33.7 | 67.3 | 11.5 | 7.7 | 42.3 | 24.0 |
| rvl_heldout (109) | 0.0 | 35.8 | 8.3 | 80.7 | 22.9 | 61.5 | 11.0 | 4.6 | 34.9 | 19.3 |
| tobacco_cert (108) | 0.0 | 33.3 | 5.6 | 86.1 | 20.4 | 63.9 | 2.8 | 2.8 | 23.1 | 5.6 |
<!-- /generated -->

Without a tilt step the one-view classifiers make many more errors than on exact quarter turns: PP-LCNet 38.7 %, EfficientNetV2 25.4 %, DocOrient 82.4 %, Tesseract 70.3 % (silent on 38 %). docTR 10.1 %. docangle made six errors, on four pages, five of them held back for review; they sit on `ext_doclaynet` (3.7 %: title and figure pages) and `ext_cord` (1.9 %: receipts), the two pools that [chapter 6.1](06-results.md) already names as its weak spots; on the other five pools docangle made none. docTR was right on 5 cases where docangle was wrong, docangle on 75 where docTR was wrong (pages: 4 against 62).

### 5.4.4 What docangle's straightening changes for the others

The rows "+ straightening" of the tables above hand each third-party classifier the page after docangle's Fourier tilt step has turned it upright (rule 5). In the simulated sets they are the best case for those tools.

* **The tilt step removes part of the gap between docangle and the single classifiers, more for some tools than for others.** At any angle PP-LCNet goes from 38.7 % to 9.3 % (78 % of its gap to docangle's 0.8 % is gone), DocOrient from 82.4 % to 37.6 % (55 %), EfficientNetV2 from 25.4 % to 14.2 % (46 %), docTR from 10.1 % to 5.9 % (45 %); on hand-held photographs (docangle 0.5 %) from 23.2 % to 9.2 % (62 %), 78.6 % to 35.6 % (55 %), 17.6 % to 11.2 % (37 %), and docTR stays at 6.0 % and 6.7 % (no gain).
* **Not all of it.** Even then the best of them, docTR with 5.9 %, makes seven times docangle's 0.8 % (docangle right on 44 cases where it is wrong, the reverse on 6; 37 pages against 4, p < 0.001). What remains is the classifier side: six views whose log-posteriors are added, and an own classifier trained on exactly this kind of straightened simulated page (threat 2 in 5.5 says why this part cannot be called simply "better").
* **Receipts are a weak spot of PP-LCNet.** Behind straightening it is the best of the other tools on the two pools docangle never saw (1.2 % hand-held, 3.2 % any angle) but makes 28 to 31 % on receipts. Its preparation (short side scaled to 256 px, central 224 × 224 square) is visible in the code; whether that causes the receipt errors was not tested.

### 5.4.5 The pools docangle's classifier never saw

`az` (the private Azerbaijani pages) and `ext_funsd` (scanned forms) were never used to train docangle's classifier (they were part of the dump on which the review threshold was chosen, chapter 4.2); the other five pools come from the same data families as its training pages (disjoint pages, [chapter 4.2](04-evaluation-protocol.md)).

<!-- generated:quarter/main/unseen -->
| tool | cases | wrong quadrant % [95 % interval] | no answer | median ms | p95 ms | same cases: docangle-only right / this-only right (pages: docangle better / this better, sign test) |
|---|---|---|---|---|---|---|
| docangle | 200 | **0.0** [0.0, 7.1] | 0 | 29 | 36 | — |
| PP-LCNet | 200 | **0.5** [0.0, 8.0] | 0 | 4 | 6 | 1 / 0 (pages 1 / 0, p = 1.000) |
| docTR | 200 | **1.0** [0.1, 8.9] | 0 | 13 | 15 | 2 / 0 (pages 2 / 0, p = 0.500) |
| DocOrient | 200 | **4.0** [1.1, 13.5] | 0 | 45 | 59 | 8 / 0 (pages 3 / 0, p = 0.250) |
| EfficientNetV2 | 200 | **17.0** [9.0, 29.7] | 0 | 113 | 123 | 34 / 0 (pages 18 / 0, p < 0.001) |
| Tesseract OSD | 200 | **22.5** [13.1, 35.8] | 13 | 441 | 497 | 45 / 0 (pages 19 / 0, p < 0.001) |
<!-- /generated -->

<!-- generated:handheld/main/unseen -->
| tool | cases | wrong quadrant % [95 % interval] | no answer | median ms | p95 ms | same cases: docangle-only right / this-only right (pages: docangle better / this better, sign test) |
|---|---|---|---|---|---|---|
| docangle | 240 | **0.0** [0.0, 4.6] | 0 | 27 | 34 | — |
| PP-LCNet | 240 | **17.1** [10.4, 26.8] | 0 | 4 | 5 | 41 / 0 (pages 33 / 0, p < 0.001) |
| docTR | 240 | **3.3** [1.1, 9.9] | 0 | 15 | 18 | 8 / 0 (pages 7 / 0, p = 0.016) |
| DocOrient | 240 | **79.6** [69.5, 87.0] | 0 | 55 | 113 | 191 / 0 (pages 80 / 0, p < 0.001) |
| EfficientNetV2 | 240 | **14.6** [8.5, 23.9] | 0 | 118 | 144 | 35 / 0 (pages 28 / 0, p < 0.001) |
| Tesseract OSD | 240 | **59.2** [48.2, 69.3] | 89 | 469 | 696 | 142 / 0 (pages 75 / 0, p < 0.001) |
| PP-LCNet + straightening | 240 | **1.2** [0.2, 6.7] | 0 | 12 | 14 | 3 / 0 (pages 3 / 0, p = 0.250) |
| docTR + straightening | 240 | **5.4** [2.2, 12.7] | 0 | 20 | 22 | 13 / 0 (pages 11 / 0, p < 0.001) |
| DocOrient + straightening | 240 | **21.7** [14.1, 31.9] | 0 | 37 | 46 | 52 / 0 (pages 43 / 0, p < 0.001) |
| EfficientNetV2 + straightening | 240 | **5.8** [2.4, 13.3] | 0 | 116 | 125 | 14 / 0 (pages 13 / 0, p < 0.001) |
<!-- /generated -->

<!-- generated:uniform/main/unseen -->
| tool | cases | wrong quadrant % [95 % interval] | no answer | median ms | p95 ms | same cases: docangle-only right / this-only right (pages: docangle better / this better, sign test) |
|---|---|---|---|---|---|---|
| docangle | 219 | **0.0** [0.0, 4.6] | 0 | 29 | 34 | — |
| PP-LCNet | 219 | **32.4** [23.2, 43.3] | 0 | 4 | 5 | 71 / 0 (pages 53 / 0, p < 0.001) |
| docTR | 219 | **7.8** [3.7, 15.7] | 0 | 14 | 19 | 17 / 0 (pages 15 / 0, p < 0.001) |
| DocOrient | 219 | **84.9** [75.5, 91.2] | 0 | 61 | 123 | 186 / 0 (pages 80 / 0, p < 0.001) |
| EfficientNetV2 | 219 | **24.2** [16.1, 34.6] | 0 | 119 | 148 | 53 / 0 (pages 43 / 0, p < 0.001) |
| Tesseract OSD | 219 | **67.6** [56.7, 76.8] | 78 | 490 | 828 | 148 / 0 (pages 79 / 0, p < 0.001) |
| PP-LCNet + straightening | 219 | **3.2** [1.0, 9.7] | 0 | 12 | 14 | 7 / 0 (pages 7 / 0, p = 0.016) |
| docTR + straightening | 219 | **3.7** [1.2, 10.3] | 0 | 20 | 23 | 8 / 0 (pages 7 / 0, p = 0.016) |
| DocOrient + straightening | 219 | **24.7** [16.5, 35.1] | 0 | 43 | 54 | 54 / 0 (pages 42 / 0, p < 0.001) |
| EfficientNetV2 + straightening | 219 | **12.3** [6.8, 21.3] | 0 | 118 | 127 | 27 / 0 (pages 21 / 0, p < 0.001) |
<!-- /generated -->

The ranking does not change: with the page turned by any angle docangle makes no error in 219 cases (the 95 % limit for no error on 80 pages is 4.6 %), docTR 7.8 %, EfficientNetV2 24.2 %, PP-LCNet 32.4 %, Tesseract 67.6 %, DocOrient 84.9 %. Behind straightening, PP-LCNet (3.2 %) and docTR (3.7 %) come closest, and both are still significantly worse over pages (7 pages against none, p = 0.016). On exact quarter turns of these two pools, with 200 cases, docangle, PP-LCNet and docTR differ by one or two cases. The sample is small and `az` cannot be reproduced by anyone outside the project; FUNSD is public.

### 5.4.6 Real camera footage: SmartDoc 2015

420 frames from 150 video clips of 30 English documents on five backgrounds (1920 × 1080, every 50th frame of each clip), each turned by a random multiple of 90° so that the quadrant is a real question and used twice, whole and cut out: 840 cases. The truth comes from the four page corners. *Document cut out*: the page and a margin of 8 % of its long side, as a perfect page detector would give it (the page's bounding box has a long side of a median 591 px, 5th to 95th percentile 450 to 769, and the cut-out with its margins a median 685 px: `reports/smartdoc_page_size.txt`); *whole frame*: the page covers a median 11.7 % of the picture (5th to 95th percentile 7.2 to 16.2 %). Both sets are made from the same frames.

<!-- generated:smartdoc/cutout/quadrant -->
| tool | cases | wrong quadrant % [95 % interval] | no answer | median ms | p95 ms | same cases: docangle-only right / this-only right (pages: docangle better / this better, sign test) |
|---|---|---|---|---|---|---|
| docangle | 420 | **1.4** [0.4, 4.9] | 0 | 24 | 29 | — |
| PP-LCNet | 420 | **18.3** [13.0, 25.3] | 0 | 4 | 5 | 76 / 5 (pages 59 / 3, p < 0.001) |
| docTR | 420 | **5.2** [2.7, 10.0] | 0 | 12 | 14 | 19 / 3 (pages 14 / 1, p < 0.001) |
| DocOrient | 420 | **30.2** [23.5, 38.0] | 0 | 16 | 24 | 122 / 1 (pages 81 / 1, p < 0.001) |
| EfficientNetV2 | 420 | **6.4** [3.5, 11.5] | 0 | 109 | 114 | 25 / 4 (pages 21 / 4, p < 0.001) |
| Tesseract OSD | 420 | **95.5** [90.9, 97.8] | 353 | 109 | 215 | 395 / 0 (pages 144 / 0, p < 0.001) |
| PP-LCNet + straightening | 420 | **7.9** [4.5, 13.3] | 0 | 8 | 10 | 32 / 5 (pages 24 / 5, p < 0.001) |
| docTR + straightening | 420 | **4.3** [2.0, 8.8] | 0 | 16 | 18 | 15 / 3 (pages 10 / 1, p = 0.012) |
| DocOrient + straightening | 420 | **30.7** [23.9, 38.5] | 0 | 21 | 32 | 124 / 1 (pages 74 / 1, p < 0.001) |
| EfficientNetV2 + straightening | 420 | **9.5** [5.8, 15.3] | 0 | 112 | 118 | 38 / 4 (pages 25 / 4, p < 0.001) |
| docangle + doc_crop | 420 | **1.9** [0.6, 5.6] | 0 | 26 | 30 | 2 / 0 (pages 2 / 0, p = 0.500) |
<!-- /generated -->

<!-- generated:smartdoc/cutout/pool -->
| pool (cases) | docangle | PP-LCNet | docTR | DocOrient | EfficientNetV2 | Tesseract OSD | PP-LCNet + straightening | docTR + straightening | DocOrient + straightening | EfficientNetV2 + straightening | docangle + doc_crop |
|---|---|---|---|---|---|---|---|---|---|---|---|
| datasheet (75) | 0.0 | 6.7 | 0.0 | 36.0 | 0.0 | 97.3 | 2.7 | 1.3 | 28.0 | 1.3 | 0.0 |
| letter (70) | 0.0 | 15.7 | 1.4 | 21.4 | 2.9 | 94.3 | 7.1 | 1.4 | 14.3 | 1.4 | 0.0 |
| magazine (71) | 2.8 | 21.1 | 15.5 | 45.1 | 2.8 | 90.1 | 4.2 | 14.1 | 45.1 | 4.2 | 4.2 |
| paper (68) | 2.9 | 16.2 | 2.9 | 19.1 | 1.5 | 100.0 | 2.9 | 1.5 | 22.1 | 4.4 | 4.4 |
| patent (67) | 1.5 | 23.9 | 7.5 | 31.3 | 7.5 | 95.5 | 10.4 | 6.0 | 34.3 | 14.9 | 1.5 |
| tax (69) | 1.4 | 27.5 | 4.3 | 27.5 | 24.6 | 95.7 | 20.3 | 1.4 | 40.6 | 31.9 | 1.4 |
<!-- /generated -->

<!-- generated:smartdoc/whole/quadrant -->
| tool | cases | wrong quadrant % [95 % interval] | no answer | median ms | p95 ms | same cases: docangle-only right / this-only right (pages: docangle better / this better, sign test) |
|---|---|---|---|---|---|---|
| docangle | 420 | **7.6** [4.4, 13.0] | 0 | 26 | 30 | — |
| PP-LCNet | 420 | **27.9** [21.3, 35.5] | 0 | 4 | 6 | 98 / 13 (pages 66 / 9, p < 0.001) |
| docTR | 420 | **14.8** [10.0, 21.3] | 0 | 13 | 15 | 57 / 27 (pages 37 / 20, p = 0.033) |
| DocOrient | 420 | **52.4** [44.4, 60.2] | 0 | 44 | 52 | 205 / 17 (pages 93 / 11, p < 0.001) |
| EfficientNetV2 | 420 | **18.8** [13.4, 25.8] | 0 | 113 | 124 | 68 / 21 (pages 41 / 16, p = 0.001) |
| Tesseract OSD | 420 | **97.4** [93.4, 99.0] | 370 | 183 | 292 | 377 / 0 (pages 143 / 0, p < 0.001) |
| PP-LCNet + straightening | 420 | **23.1** [17.1, 30.5] | 0 | 11 | 12 | 77 / 12 (pages 54 / 8, p < 0.001) |
| docTR + straightening | 420 | **61.0** [53.0, 68.4] | 0 | 18 | 21 | 236 / 12 (pages 98 / 6, p < 0.001) |
| DocOrient + straightening | 420 | **60.7** [52.7, 68.2] | 0 | 29 | 35 | 231 / 8 (pages 105 / 7, p < 0.001) |
| EfficientNetV2 + straightening | 420 | **16.4** [11.4, 23.2] | 0 | 114 | 121 | 62 / 25 (pages 35 / 17, p = 0.018) |
| docangle + doc_crop | 420 | **3.3** [1.4, 7.6] | 0 | 26 | 31 | 3 / 21 (pages 2 / 14, p = 0.004) |
<!-- /generated -->

<!-- generated:smartdoc/whole/pool -->
| pool (cases) | docangle | PP-LCNet | docTR | DocOrient | EfficientNetV2 | Tesseract OSD | PP-LCNet + straightening | docTR + straightening | DocOrient + straightening | EfficientNetV2 + straightening | docangle + doc_crop |
|---|---|---|---|---|---|---|---|---|---|---|---|
| datasheet (75) | 1.3 | 16.0 | 2.7 | 50.7 | 1.3 | 100.0 | 12.0 | 60.0 | 57.3 | 1.3 | 1.3 |
| letter (70) | 1.4 | 10.0 | 0.0 | 55.7 | 4.3 | 98.6 | 11.4 | 51.4 | 61.4 | 0.0 | 1.4 |
| magazine (71) | 22.5 | 38.0 | 33.8 | 54.9 | 11.3 | 91.5 | 29.6 | 64.8 | 62.0 | 12.7 | 7.0 |
| paper (68) | 4.4 | 20.6 | 16.2 | 45.6 | 17.6 | 98.5 | 10.3 | 69.1 | 55.9 | 7.4 | 1.5 |
| patent (67) | 9.0 | 37.3 | 17.9 | 65.7 | 37.3 | 97.0 | 29.9 | 52.2 | 67.2 | 37.3 | 7.5 |
| tax (69) | 7.2 | 46.4 | 18.8 | 42.0 | 43.5 | 98.6 | 46.4 | 68.1 | 60.9 | 42.0 | 1.4 |
<!-- /generated -->

* **With the page cut out** docangle makes 1.4 %, docTR 5.2 %, EfficientNetV2 6.4 %, PP-LCNet 18.3 %, DocOrient 30.2 %; Tesseract's OSD gave no answer for 353 of the 420 frames (95.5 % wrong or silent); the cause was not investigated. docangle's six errors are on six clips, five of them held back for review.
* **On whole frames** every tool gets worse and the field comes closer: docangle 7.6 %, docTR 14.8 %, EfficientNetV2 18.8 %, PP-LCNet 27.9 %, DocOrient 52.4 %. docTR is right on 27 cases where docangle is wrong, docangle on 57 (over pages: docangle better on 37, docTR on 20): significant (p = 0.033), but not by much. Magazine pages are the hardest (docangle 22.5 %). With the opt-in page finder (`doc_crop=True`) docangle makes 3.3 % and is significantly better than without it (pages 2 against 14, p = 0.004).
* **The "+ straightening" rows do not mean here what they mean in the simulated sets.** The tilt step needs the page to fill the picture; on a whole frame its estimate is within 1° in only 46 % of the cases (5.4.8). Straightening by a wrong estimate helps PP-LCNet (27.9 % to 23.1 %) and EfficientNetV2 (18.8 % to 16.4 %) but ruins docTR (14.8 % to 61.0 %) and makes DocOrient worse (52.4 % to 60.7 %); why was not investigated. On the cut-out frames, where the tilt step works, the rows are mixed: straightening helps PP-LCNet (18.3 % to 7.9 %) and docTR (5.2 % to 4.3 %), leaves DocOrient flat (30.2 % to 30.7 %) and makes EfficientNetV2 worse (6.4 % to 9.5 %); docTR and PP-LCNet behind straightening stay worse than docangle (p = 0.012 and p < 0.001).

### 5.4.7 Holding pages back for a person

docangle's rate in the tables above counts a page even when its review flag was set. Here every tool may hold pages back: docangle by its review rule; a tool with a score, its least certain cases, at the same share of cases as docangle held back; DocOrient by its own `reliable` flag; Tesseract by being silent. The shares count cases; the intervals count pages. The last column asks the opposite question: how many cases would a tool have to hold back to be as reliable as docangle is on the cases it answers?

<!-- generated:quarter/main/selective -->
| tool: which cases it holds back | held back, % of cases | wrong among the cases it answered: n / N | % [95 % interval over pages] | cases it must hold back to match docangle's rate, % |
|---|---|---|---|---|
| docangle: its own review rule | 1.1 | 0 / 692 | **0.0** [0.0, 2.2] | — |
| PP-LCNet: its least certain cases, same share as docangle | 1.1 | 3 / 692 | **0.4** [0.1, 2.9] | 6.0 |
| docTR: its least certain cases, same share as docangle | 1.1 | 24 / 692 | **3.5** [1.6, 7.3] | 54.4 |
| DocOrient: its own 'not reliable' flag | 0.0 | 136 / 700 | **19.4** [14.2, 25.9] | — |
| EfficientNetV2: its least certain cases, same share as docangle | 1.1 | 59 / 692 | **8.5** [5.2, 13.6] | 92.0 |
| Tesseract OSD: its least certain cases, same share as docangle | 1.1 | 239 / 692 | **34.5** [27.9, 41.9] | 83.1 |
| Tesseract OSD: silent when it has no answer | 17.0 | 128 / 581 | **22.0** [16.3, 29.1] | — |
<!-- /generated -->

<!-- generated:handheld/main/selective -->
| tool: which cases it holds back | held back, % of cases | wrong among the cases it answered: n / N | % [95 % interval over pages] | cases it must hold back to match docangle's rate, % |
|---|---|---|---|---|
| docangle: its own review rule | 2.7 | 1 / 817 | **0.1** [0.0, 1.6] | — |
| PP-LCNet: its least certain cases, same share as docangle | 2.7 | 179 / 817 | **21.9** [17.5, 27.1] | 74.9 |
| docTR: its least certain cases, same share as docangle | 2.7 | 37 / 817 | **4.5** [2.6, 7.6] | 64.6 |
| DocOrient: its own 'not reliable' flag | 0.0 | 660 / 840 | **78.6** [73.4, 83.0] | — |
| EfficientNetV2: its least certain cases, same share as docangle | 2.7 | 135 / 817 | **16.5** [12.6, 21.3] | 99.5 |
| Tesseract OSD: its least certain cases, same share as docangle | 2.7 | 516 / 817 | **63.2** [57.4, 68.6] | 99.6 |
| Tesseract OSD: silent when it has no answer | 37.5 | 224 / 525 | **42.7** [36.9, 48.7] | — |
| PP-LCNet + straightening: its least certain cases, same share as docangle | 2.7 | 65 / 817 | **8.0** [5.3, 11.7] | 41.2 |
| docTR + straightening: its least certain cases, same share as docangle | 2.7 | 47 / 817 | **5.8** [3.6, 9.1] | 96.2 |
| DocOrient + straightening: its own 'not reliable' flag | 0.0 | 299 / 840 | **35.6** [30.2, 41.4] | — |
| EfficientNetV2 + straightening: its least certain cases, same share as docangle | 2.7 | 82 / 817 | **10.0** [7.0, 14.1] | 98.8 |
<!-- /generated -->

<!-- generated:uniform/main/selective -->
| tool: which cases it holds back | held back, % of cases | wrong among the cases it answered: n / N | % [95 % interval over pages] | cases it must hold back to match docangle's rate, % |
|---|---|---|---|---|
| docangle: its own review rule | 2.7 | 1 / 732 | **0.1** [0.0, 1.6] | — |
| PP-LCNet: its least certain cases, same share as docangle | 2.7 | 279 / 732 | **38.1** [32.6, 43.9] | 91.1 |
| docTR: its least certain cases, same share as docangle | 2.7 | 65 / 732 | **8.9** [6.1, 12.8] | 68.8 |
| DocOrient: its own 'not reliable' flag | 0.0 | 620 / 752 | **82.4** [77.6, 86.5] | — |
| EfficientNetV2: its least certain cases, same share as docangle | 2.7 | 178 / 732 | **24.3** [19.7, 29.7] | never |
| Tesseract OSD: its least certain cases, same share as docangle | 2.7 | 509 / 732 | **69.5** [63.9, 74.6] | 99.6 |
| Tesseract OSD: silent when it has no answer | 38.0 | 243 / 466 | **52.1** [46.0, 58.2] | — |
| PP-LCNet + straightening: its least certain cases, same share as docangle | 2.7 | 60 / 732 | **8.2** [5.5, 12.0] | 56.9 |
| docTR + straightening: its least certain cases, same share as docangle | 2.7 | 32 / 732 | **4.4** [2.5, 7.4] | 81.9 |
| DocOrient + straightening: its own 'not reliable' flag | 0.0 | 283 / 752 | **37.6** [32.2, 43.4] | — |
| EfficientNetV2 + straightening: its least certain cases, same share as docangle | 2.7 | 96 / 732 | **13.1** [9.7, 17.6] | 93.0 |
<!-- /generated -->

<!-- generated:smartdoc/cutout/selective -->
| tool: which cases it holds back | held back, % of cases | wrong among the cases it answered: n / N | % [95 % interval over pages] | cases it must hold back to match docangle's rate, % |
|---|---|---|---|---|
| docangle: its own review rule | 6.9 | 1 / 391 | **0.3** [0.0, 3.1] | — |
| PP-LCNet: its least certain cases, same share as docangle | 6.9 | 61 / 391 | **15.6** [10.6, 22.3] | 56.2 |
| docTR: its least certain cases, same share as docangle | 6.9 | 9 / 391 | **2.3** [0.8, 6.3] | 98.6 |
| DocOrient: its own 'not reliable' flag | 0.0 | 127 / 420 | **30.2** [23.5, 38.0] | — |
| EfficientNetV2: its least certain cases, same share as docangle | 6.9 | 21 / 391 | **5.4** [2.7, 10.3] | 96.9 |
| Tesseract OSD: its least certain cases, same share as docangle | 6.9 | 372 / 391 | **95.1** [90.4, 97.6] | never |
| Tesseract OSD: silent when it has no answer | 84.0 | 48 / 67 | **71.6** [57.8, 82.3] | — |
| PP-LCNet + straightening: its least certain cases, same share as docangle | 6.9 | 18 / 391 | **4.6** [2.2, 9.3] | 36.9 |
| docTR + straightening: its least certain cases, same share as docangle | 6.9 | 7 / 391 | **1.8** [0.6, 5.6] | 53.8 |
| DocOrient + straightening: its own 'not reliable' flag | 0.0 | 129 / 420 | **30.7** [23.9, 38.5] | — |
| EfficientNetV2 + straightening: its least certain cases, same share as docangle | 6.9 | 22 / 391 | **5.6** [2.9, 10.6] | never |
| docangle + doc_crop: its own review rule | 7.1 | 1 / 390 | **0.3** [0.0, 3.1] | — |
<!-- /generated -->

<!-- generated:smartdoc/whole/selective -->
| tool: which cases it holds back | held back, % of cases | wrong among the cases it answered: n / N | % [95 % interval over pages] | cases it must hold back to match docangle's rate, % |
|---|---|---|---|---|
| docangle: its own review rule | 23.3 | 4 / 322 | **1.2** [0.3, 5.1] | — |
| PP-LCNet: its least certain cases, same share as docangle | 23.3 | 56 / 322 | **17.4** [12.0, 24.5] | 78.8 |
| docTR: its least certain cases, same share as docangle | 23.3 | 26 / 322 | **8.1** [4.6, 13.8] | 80.2 |
| DocOrient: its own 'not reliable' flag | 0.0 | 220 / 420 | **52.4** [44.4, 60.2] | — |
| EfficientNetV2: its least certain cases, same share as docangle | 23.3 | 33 / 322 | **10.2** [6.3, 16.3] | 96.4 |
| Tesseract OSD: its least certain cases, same share as docangle | 23.3 | 311 / 322 | **96.6** [91.8, 98.6] | never |
| Tesseract OSD: silent when it has no answer | 88.1 | 39 / 50 | **78.0** [62.2, 88.4] | — |
| PP-LCNet + straightening: its least certain cases, same share as docangle | 23.3 | 47 / 322 | **14.6** [9.5, 21.8] | 90.2 |
| docTR + straightening: its least certain cases, same share as docangle | 23.3 | 187 / 322 | **58.1** [49.9, 65.8] | never |
| DocOrient + straightening: its own 'not reliable' flag | 0.0 | 255 / 420 | **60.7** [52.7, 68.2] | — |
| EfficientNetV2 + straightening: its least certain cases, same share as docangle | 23.3 | 33 / 322 | **10.2** [6.3, 16.4] | never |
| docangle + doc_crop: its own review rule | 12.1 | 0 / 369 | **0.0** [0.0, 2.9] | — |
<!-- /generated -->

docangle holds back 1.1 % of the pages of the quarter-turn set, 2.7 % of the hand-held and any-angle sets, 6.9 % of the cut-out and 23.3 % of the whole frames, and is wrong on 0.0, 0.1, 0.1, 0.3 and 1.2 % of the pages it answers. (With `doc_crop` the whole frames need only 12.1 % held back and none of the answered pages is wrong.) The scores of the other tools are much less informative: at docangle's share, docTR is still wrong on 3.5 %, 4.5 % and 8.9 % of the quarter-turn, hand-held and any-angle pages, PP-LCNet on 21.9 % of the hand-held and 38.1 % of the any-angle pages; docTR would have to hold back 54 %, 65 % and 69 % of those pages to reach docangle's rate. In these tests the softmax of a four-class model is a weak uncertainty signal. DocOrient never flags a page and Tesseract's silence (17 % of the quarter turns, 38 % of the tilted pages) leaves 22 % to 52 % of its answers wrong.

### 5.4.8 Fine angle

Only docangle and the two baselines give a tilt. The error is the difference to the true tilt modulo 90° (the baselines cannot know the quadrant).

<!-- generated:handheld/main/fine -->
| estimator | cases | median error ° | within 0.5° % | within 1° % | error > 5° % [95 % interval] | median ms |
|---|---|---|---|---|---|---|
| docangle | 840 | 0.06 | 87.3 | 95.8 | 0.0 [0.0, 1.4] | 27 |
| docangle Hough | 840 | 0.22 | 79.4 | 94.0 | 0.0 [0.0, 1.4] | 35 |
| minAreaRect | 840 | 1.89 | 41.4 | 45.4 | 42.0 [36.4, 47.9] | 20 |
<!-- /generated -->

<!-- generated:uniform/main/fine -->
| estimator | cases | median error ° | within 0.5° % | within 1° % | error > 5° % [95 % interval] | median ms |
|---|---|---|---|---|---|---|
| docangle | 840 | 0.05 | 89.9 | 96.9 | 0.0 [0.0, 1.4] | 28 |
| docangle Hough | 840 | 0.22 | 78.7 | 94.0 | 0.1 [0.0, 1.6] | 36 |
| minAreaRect | 840 | 3.23 | 40.1 | 43.5 | 45.4 [39.6, 51.2] | 25 |
<!-- /generated -->

<!-- generated:smartdoc/cutout/fine -->
| estimator | cases | median error ° | within 0.5° % | within 1° % | error > 5° % [95 % interval] | median ms |
|---|---|---|---|---|---|---|
| docangle | 420 | 0.38 | 58.6 | 76.7 | 4.8 [2.3, 9.4] | 24 |
| docangle Hough | 420 | 0.67 | 41.0 | 64.8 | 11.9 [7.7, 18.1] | 29 |
| minAreaRect | 420 | 4.34 | 6.4 | 13.1 | 44.3 [36.6, 52.3] | 4 |
| docangle + doc_crop | 420 | 0.38 | 58.6 | 76.4 | 4.8 [2.3, 9.4] | 26 |
<!-- /generated -->

<!-- generated:smartdoc/whole/fine -->
| estimator | cases | median error ° | within 0.5° % | within 1° % | error > 5° % [95 % interval] | median ms |
|---|---|---|---|---|---|---|
| docangle | 420 | 1.19 | 27.4 | 46.4 | 15.2 [10.4, 21.9] | 26 |
| docangle Hough | 420 | 0.77 | 36.2 | 56.4 | 18.6 [13.2, 25.6] | 28 |
| minAreaRect | 420 | 5.10 | 5.5 | 11.4 | 51.2 [43.3, 59.1] | 32 |
| docangle + doc_crop | 420 | 0.40 | 54.5 | 75.5 | 6.7 [3.7, 11.8] | 26 |
<!-- /generated -->

On simulated pages docangle's Fourier tilt is within 1° in 95.8 % (hand-held) and 96.9 % (any angle) of the cases, the older Hough estimator in 94.0 % in both, and the textbook `minAreaRect` deskew in 45.4 % and 43.5 %. On real frames with the page cut out the Fourier tilt reaches 76.7 % against 64.8 % for Hough and 13.1 % for `minAreaRect`. **On whole frames the order of the first two is reversed** (Fourier 46.4 %, Hough 56.4 %): the Fourier method wants the page to fill the picture, which is what `doc_crop` provides (75.5 %). The truth of the real frames comes from the page edges (perspective moves it from the text lines by a degree or two: the authors' estimate, not measured here), and scans labelled upright are themselves 0.3 to 1° off ([chapter 4.5](04-evaluation-protocol.md)), so the simulated numbers are the cleaner measurement. The skew estimators jdeskew and `deskew` were not run (5.3).

### 5.4.9 Speed and size

Median (95th percentile) milliseconds per page, the whole call including the tool's own preparation, one case at a time, CPU, two threads in every session the harness builds (DocOrient: its own session options).

<!-- generated:speed -->
| tool | exact quarter turns | hand-held photo (quadrant ± 25°) | any angle | real phone frames, page cut out | real phone frames, whole frame |
|---|---|---|---|---|---|
| docangle | 27 (40) | 27 (36) | 28 (34) | 24 (29) | 26 (30) |
| PP-LCNet | 4 (5) | 4 (5) | 4 (5) | 4 (5) | 4 (6) |
| docTR | 13 (19) | 15 (18) | 15 (18) | 12 (14) | 13 (15) |
| DocOrient | 26 (136) | 54 (112) | 62 (130) | 16 (24) | 44 (52) |
| EfficientNetV2 | 112 (155) | 117 (145) | 121 (150) | 109 (114) | 113 (124) |
| Tesseract OSD | 326 (766) | 441 (698) | 472 (784) | 109 (215) | 183 (292) |
<!-- /generated -->

docangle needs 24 to 28 ms per page in every setting: 6 to 7 times as long as one PP-LCNet view, about twice as long as docTR, as fast as DocOrient on exact quarter turns (27 and 26 ms), faster on the tilted simulated pages (27 and 28 ms against 54 and 62) and on whole phone frames (26 against 44), slower on the cut-out phone frames (24 against 16 ms), about a quarter of EfficientNetV2's time, and between a fifth and a seventeenth of Tesseract's. It carries 36 MB of models (24 MB without the fallback regressor) against 6 to 11 MB for PP-LCNet, docTR, DocOrient and Tesseract's OSD data and 81 MB for EfficientNetV2. On a GPU docangle takes less than half the time ([chapter 8](08-performance.md), which also gives the median 35 to 45 ms of a call that includes decoding the image file; the times here are from arrays already in memory); the others were not measured on one. What the extra 20 ms or so buy is in the tables above: the tilt step, the six views and the review flag.

### 5.4.10 Which tool for which job

| if you | use | because |
|---|---|---|
| have clean pages in exact quarter turns, can live with about 1 % unannounced errors, and want the cheapest and fastest | **PP-LCNet alone** (4 ms, 6.8 MB, Apache-2.0) | 1.0 % wrong on 700 such cases, not significantly different from docangle (5.4.1) |
| have photographs or scans with tilt, or pages that can be turned by any angle | **docangle** | 0.5 to 0.8 % wrong against 6 % or more for the best other tool (5.4.2, 5.4.3) |
| also need the fine angle for deskewing | **docangle** | within 1° for 96 to 97 % of simulated pages; none of the orientation tools gives an angle, `minAreaRect` manages 43 to 45 % (5.4.8) |
| need to know which pages not to trust | **docangle** | its flag leaves 0.0 to 0.3 % errors among the answered pages at 1 to 7 % held back; the scores of the other tools separate their errors far less well (5.4.7) |
| photograph a document with a phone and the page is small in the frame | **docangle with `doc_crop=True`** | 7.6 % wrong on whole frames, 3.3 % with the page finder (5.4.6) |
| use Tesseract and want its OSD to say how the page is turned | **do not rely on it** | 35 % wrong or silent on clean exact turns, silent on 84 % of the cut-out and 88 % of the whole phone frames; the cause was not investigated (5.4.1, 5.4.6) |
| need a tool that is a drop-in model rather than a pipeline | **docTR page orientation** | the most accurate single-model tool once the page is tilted or photographed: 5.2 to 14.8 % wrong, 12 to 15 ms (5.4.2, 5.4.3, 5.4.6) |

## 5.5 Threats to validity

| # | threat | direction | what was done | what remains |
|---|---|---|---|---|
| 1 | docangle's own classifier was trained on pages of the same data families as five of the seven pools (RVL-CDIP invoices, Tobacco, CORD, DocLayNet; disjoint pages). The third-party models' training data is unknown or different | favours docangle | the pools are reported one by one, and the two pools it never saw (`az`, FUNSD) are tabled separately (5.4.5); the ranking does not change | only two such pools, one of them private |
| 2 | the simulated photographs resemble what docangle's classifier was trained on: separate code (`src/orient_data.py` against `bench/degrade.py`), the same kinds of effects and the same 20 generated background textures | favours docangle on the photo levels | the `scan` level and the exact quarter turns need no photographic effect, and docangle's rate is as low there (0.0 to 0.8 %); the SmartDoc frames are real. Besides, docTR's rate barely changes with the level (5.4.2, 5.4.3) | no labelled collection of real phone photographs of such documents exists to test with |
| 3 | docangle is a system (a tilt step, six views, a review rule) and the others are single models | not a bias, but a different cost: 24 to 28 ms against 4 ms (PP-LCNet) and 12 to 15 ms (docTR) | the "+ straightening" rows show the part of the gap that is the tilt step; the speed table shows the price | a tool built from PP-LCNet with the same six views would be a new tool; the ablation of [chapter 6.5](06-results.md) measures it: PP-LCNet alone is far worse than docangle |
| 4 | tilt is outside the design range of a four-class model | favours docangle in the hand-held and any-angle settings | exact quarter turns come first; the "+ straightening" rows | on whole phone frames the straightening itself fails (5.4.6) |
| 5 | small samples: 175 pages (quarter turns), 280 pages (simulated sets), 150 clips (SmartDoc) | widens the intervals | intervals count pages; paired counts and exact sign tests over pages | differences of a few cases on a few pages (PP-LCNet on quarter turns) cannot be interpreted |
| 6 | Tesseract is a program, not a model, and its OSD may want more text or a higher resolution than these inputs give | disfavours Tesseract | run as documented; the `--dpi` check changed nothing; the cost of writing the PNG is counted and named | OSD inside a full OCR run, at 300 dpi scans, was not measured |
| 7 | the review threshold 0.90 of docangle was chosen on a dump that overlaps some pages of these pools ([chapter 4.4](04-evaluation-protocol.md)) | slightly favours docangle's rate in 5.4.7 | the quadrant answers do not depend on the threshold; SmartDoc was never used to choose it | the held-back shares are optimistic by an unknown, small amount |
| 8 | the authors' own accuracy claims were measured on other data (photographs, their own test sets) | none | EfficientNetV2 is trained on photographs and included as the representative general model; a different number here is not a contradiction | |
| 9 | timings come from one laptop with a desktop running | numbers vary | the ratios are more stable than the values; the machine is named in every raw file | other CPUs, other thread settings |
| 10 | every tool is as installed in October 2026 | | versions are stored in every raw file | newer versions may be better |
| 11 | SmartDoc informed three decisions of docangle: the `TOO_FEW_LINES` gate, keeping the regressor, and the `doc_crop` parameters, which were tuned on the even-numbered documents | the `doc_crop` rows and the real-frame review shares are partly in-sample | the odd-numbered half, which the parameters never saw, gives 3.9 % flips with `doc_crop` against 5.4 % without ([chapter 6.4](06-results.md)); docangle without `doc_crop` is affected only through the gate and the regressor | the real-frame numbers of docangle are optimistic by an unknown, small amount |

**What would change the conclusion.** If your pages are clean exact quarter turns, no difference between PP-LCNet alone and docangle could be shown on these pages (p = 0.125 over 4 pages) and PP-LCNet is 6 to 7 times faster. If the page is small in the picture and you cannot cut it out, the field is closer (5.4.6). If your documents are very unlike the ones here (other scripts, handwriting, pages without text), none of the numbers apply.

## 5.6 What this comparison does not show

* **Real phone photographs of the intended documents.** The simulated photographs are a model of a camera, and the only real camera footage is 30 English documents at low resolution (SmartDoc; the CORD receipts are turned and degraded by simulation). Nobody has labelled phone photos of Azerbaijani documents yet; [chapter 9](09-usage.md) shows how to measure it on a small sample.
* **Other scripts, handwriting, pages without text.** All pools are Latin-script documents.
* **GPU speed of the other tools.** Only docangle was measured on a GPU ([chapter 8](08-performance.md)).
* **Newer versions.** Every tool is as installed in October 2026; a later version of any of them may do better, and the stored raw files say exactly what was run.
* **OCR outcome.** A wrong quadrant is the costly mistake because OCR then reads nothing; [chapter 7](07-ocr-impact.md) measures what docangle does for three OCR engines. It was not repeated with the other tools in front.

## 5.7 Adding a tool, running it again

A tool is one class in `bench/compare_open_models.py`: a `predict(bgr) -> 0..3 or None` that returns by how many quarter turns counter-clockwise the page is turned (use `bench/docorient_quarter.py` to check a new tool's convention on exact turns first), plus optional `conf` (a score, higher is more certain) and `flag` ("not sure") attributes. Add it to `QUADRANT`, run the four modes of [chapter 12.5](12-reproduce.md), then `python -m bench.compare_report fill-docs ...`. Pull requests with a tool, or with a setting under which one of the tools here is handicapped, are welcome: the rules in 5.2 are the contract.
