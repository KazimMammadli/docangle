# 6. Results

All numbers in this chapter come from the protocol of [chapter 4](04-evaluation-protocol.md) and from the version named in each heading; the raw result files are in [`reports/`](../reports/) and the day-by-day derivations in the [lab notebook](../reports/FINAL_REPORT.md) (section numbers are given as §N). Simulated photographs unless stated. The comparison with *other open-source tools* is chapter 5; this chapter is about docangle itself.

## 6.1 Quadrant accuracy and review behaviour (v4.4 code, 3600 + 2700 simulated cases)

Pages turned by any angle in [-180°, 180°], three degradation levels (`reports/bench_final_v4_4.json`, tables in `reports/FINAL_TABLES_v4_4.md`; run on mains power on the working tree that became this release, so the recorded commit is the last private one plus uncommitted changes). The first run of this benchmark, with the v4.3.0 code (`reports/bench_final_v4_3.json`), differs in the CORD pool (flips 3.67 %, ≤ 1° 87.4 %) and by at most 0.3 points in the ≤ 1° rate elsewhere; flips, accepted flips and review shares of every other pool are identical. "Known-bad source page" is the one RVL-CDIP invoice that is itself sideways in its source; its correct predictions count as flips against the raw label.

| pool group | cases | flips % (case-level 95 % interval) | flips without the known-bad page | accepted flips | ≤ 1° % | ≤ 0.5° % | sent to review % |
|---|---|---|---|---|---|---|---|
| primary pools (az, invoices, tobacco_cert, rvl_heldout) | 3600 | **0.58** [0.38, 0.89] | 0.33 | 9 (all on the known-bad page: **0 real**) | 95.7 | 87.4 | 1.1 |
| ... of which `az` (exact ground truth) | 900 | **0.00** [0.00, 0.43] | 0.00 | 0 | 100.0 | 100.0 | 0.1 |
| external pools (FUNSD, DocLayNet, CORD) | 2700 | 1.93 [1.47, 2.52] | 1.93 | 6 | 93.3 | 87.0 | 3.8 |
| ... `ext_funsd` (scanned forms) | 900 | 0.00 [0.00, 0.43] | 0.00 | 0 | 94.7 | 82.7 | 0.1 |
| ... `ext_doclaynet` (report and manual pages) | 900 | 3.11 [2.16, 4.46] | 3.11 | 5 | 96.9 | 96.7 | 3.8 |
| ... `ext_cord` (receipts photographed by phone) | 900 | 2.67 [1.80, 3.94] | 2.67 | 1 | 88.2 | 81.7 | 7.6 |

Hand-held mode (`quad_tilt`, a quadrant plus up to ±25°, 2400 primary-pool cases): flips 0.42 % [0.23, 0.77] (case-level interval), 6 accepted, ≤ 1° 95.5 %, review 1.2 % (`reports/FINAL_TABLES_v4_4_quadtilt.md`; the v4.3.0 code gave 0.46 %).

**Page-level honesty.** The 3600 cases are rotations of 659 distinct pages and the flips sit on very few of them (here 21 flips on 9 pages, 8 of them without the sideways source page: `reports/page_interval_v4_4.txt`). The honest interval for the primary-pool flip rate is therefore the page-cluster one, not the case-level interval above (§4.1): **0.58 % [0.14, 1.23]** with 10 000 resamples of whole pages, and 0.33 % [0.11, 0.61] without the sideways source page (`python -m bench.page_interval`). For v4.1 the same kind of interval was 0.50 % [0.11, 1.14] (`reports/FINAL_REPORT.md`). The pages that flip are hard in recognisable ways: black halftone bands, near-empty pages, logo-dominated pages and, before the Fourier tilt, number tables whose long segments mislead a line detector (§6).

**Where it is weakest.** Receipts photographed by phone (narrow, blurred, a hand in the frame) flip in 2.7 % of cases (24 of 900; 23 of them go to review, one is accepted), and 7.6 % of all receipt cases are reviewed; DocLayNet's title and figure pages flip in 3.1 %. For such material raise `review_confidence`: on the 6291-case dump of §11, at 0.95 the external pools send 7.2 % of pages to review and accept 2 flips in 2700, at 0.98 14.6 % and none (in the v4.4 run the review share at 0.95 is 7.1 %).

## 6.2 The review threshold

Confidence is the posterior of the chosen quadrant, and the rule is one threshold on it (chapter 2.8). On the 6291-case dump that chose the threshold:

| `review_confidence` | primary pools: review % / accepted flips | external pools: review % / accepted flips |
|---|---|---|
| 0.90 (default) | 1.1 / 0 | 3.8 / 6 |
| 0.95 | 2.6 / 0 | 7.2 / 2 |
| 0.98 | 6.4 / 0 | 14.6 / 0 |

The dump leaves out the one source page that is itself sideways (`certified_invoice_030`); in the full benchmark that page adds 9 accepted flips, which are correct predictions of a sideways page (`reports/FINAL_TABLES_v4_4.md`). The rule replaced one that added a line-count term and let every page with 80 or more lines skip review; on out-of-domain pages the new rule accepts 6 flips where the old accepted 10, with 3.8 % review instead of 9.7 %. On the primary pools the gain is small and not proven (a hand-held check showed no change). A learned review score (logistic regression on nine features) cut the accepted flips from 13 to 3 at the old rule's review rate in page-grouped cross-validation (`reports/calibrate_e2.txt`); it was not adopted because the parameter-free rule needs no fitting, and the two were not compared at an equal review rate. The threshold was fitted on the same cases that appear in one table; independent checks are in the next sections (§11).

## 6.3 Fine angle

* **Against the nominal angle**, ≤ 1° in 88.2-100.0 % of cases over the seven pools (az 100.0, ext_doclaynet 96.9, tobacco_cert 96.2, invoices 94.8, ext_funsd 94.7, rvl_heldout 91.9, ext_cord 88.2); ≤ 0.5° in 77.4-100.0 % (`reports/FINAL_TABLES_v4_4.md`, all levels of each pool). Scans labelled upright are themselves 0.3-1° off, which caps the measurable rate: against each page's *own* measured skew (a consistency check: that reference is measured with the same Fourier method) the rate is 93.5-100.0 % per pool and level (12 cells of 200 cases: the four primary pools, FUNSD and DocLayNet, levels `scan` and `photo_hard`; `reports/skew_check_v4_4.txt`, §4.5).
* **Fourier against Hough** (§10, same cases, paired): ≤ 1° rose from 90.2 % to 93.8 % and errors > 5° fell from 95 to 51 in 2800 cases; the Fourier estimate was better by more than 0.25° in 668 cases and worse in 117; the analysis got 7-8 ms faster.
* **DISE-2021** (an independent public skew data set; 600 of its pages with skew up to ±45°; `reports/dise_eval_v4_3.txt`): median error 0.07°, ≤ 1° in 94.3 %, errors > 5° in 34 pages, all of them wrong quadrants; the predecessor C8+L reached 84.0 % and 70 errors.
* **Textbook deskew** (`cv2.minAreaRect`, as in tutorials) reaches 83.5 % within 1° on clean simulated scans, 11 % on simulated hard photos, and 12 % with a median error of 4.4° on real SmartDoc frames; it cannot tell 0° from 90°, 180° or 270° at all (§19).

## 6.4 Real camera footage: SmartDoc 2015 (§14, §22)

150 clips of 30 English documents filmed on 5 backgrounds (926 frames, every 25th of each clip); ground truth from the four page corners, so the angle is that of the page edges (perspective can move it by 1-2° from the text lines).

| 926 frames | median error | ≤ 1° | flips | review | accepted flips |
|---|---|---|---|---|---|
| whole frame (the page covers a median 12 % of the frame), docangle | 1.37° | 42.9 % | 6.4 % | 23.9 % | 1 |
| whole frame, `doc_crop=True` | **0.44°** | **73.1 %** | **3.9 %** | 13.5 % | **0** |
| page cut out with the true corners (a perfect detector) | 0.40° | 76.3 % | 1.5 % | 6.7 % | 1 |
| ... same, v4.1 Hough fine tilt | 0.72° | 61.0 % | 2.9 % | 13.7 % | 2 |
| ... same, predecessor C8+L | 0.80° | 57.2 % | 7.9 % | 0 % | 73 |

(1) On a real camera the Fourier tilt is better than Hough only when the page is cut out (420 cases, `reports/benchmark/RESULTS.md`: within 1° 76.7 % against 64.8 %, error above 5° 4.8 % against 11.9 %); on the whole frame the within-1° rate and the median error reverse (46.4 % against 56.4 %; 1.19° against 0.77°) while the share of errors above 5° stays lower for Fourier (15.2 % against 18.6 %). On simulated photos the Fourier tilt was better (paragraph above). (2) With the same angles the new review rule reviewed 6.7 % of the cut-out frames and 23.9 % of the whole frames against 12.2 % and 33.0 % for the old rule, and accepted 1 flip against 2 and 17 (`reports/smartdoc_eval_crop.txt` and `reports/smartdoc_eval.txt`; both taken before the v4.3.1 line-count fix, the angles of the old and the new rule are identical in them). (3) docangle's flips are almost all caught by review; the predecessor's never. (4) A page that lies small on a desk costs accuracy; the opt-in `doc_crop` finder recovers about 90 % of the within-1° gain a perfect finder would give but only about half of the reduction in flips (6.4 % to 3.9 % against 1.5 % for a perfect finder), and on documents that were held out when its parameters were chosen (the odd-numbered half: ≤ 1° 44.3 % to 73.3 %, flips 5.4 % to 3.9 %). It moves a few angles of pages that fill the whole image, so it stays off by default (accuracy guard on 400 photo cases: worse by more than 0.25° in 4 cases, better in 1).

The perfect-detector rows were measured again with the code of this version (`reports/smartdoc_eval_crop_v4_4.txt`); the earlier file `reports/smartdoc_eval_crop.txt` was taken before the line-count fix of v4.3.1 and showed 2.7 % flips for docangle. The predecessor row is the old measurement (its code did not change).

Caveat: 30 English documents at low resolution (the long side of the page is a median 597 px, 5th to 95th percentile 453 to 781, in the frames used: `reports/smartdoc_page_size.txt`); page-edge ground truth.

## 6.5 Which parts are needed (ablation, §15)

The stages listed in the table were removed or reduced in turn, offline, from a per-view dump of 6300 cases (the flip counts below are over the 5603 cases outside the ±45° ambiguity zone, 1357 pages; `reports/ablation_dev.txt`), with paired page-cluster intervals and at the default's review rate:

| variant | flips | accepted flips (equal review rate) | verdict |
|---|---|---|---|
| default | 51 | 5 | |
| PP-LCNet alone | 445 | 364 | far worse: needs the own classifier |
| own classifier alone | 54 | 12 (+7, interval +1..+15) | PP-LCNet is not redundant |
| 12 views instead of 6 | 46 | 4 | no gain for +25 ms |
| own classifier, 1 view | 47 | 4 | non-inferior (a speed option) |
| PP-LCNet, 2 views | 50 | 5 | non-inferior (a speed option) |
| regressor override off | 25 | 5 | neutral for accepted flips (kept) |

The regressor is kept only because it is neutral; without it the displayed angle is better on the simulated pools and worse on whole SmartDoc frames.

## 6.6 Multi-page consensus (opt-in, §13)

On 1000 pages in 100+ jobs (pseudo-jobs of independent pages overstate the benefit; the five real documents had nothing to repair): when all pages of a job share one orientation, flips fall from 6 to 2, accepted flips from 3 to 0 and reviews from 23 to 6; with one odd page in ten, all 90 odd pages are sent to review and 3 of 90 correct odd pages are turned wrong by the job, none of them accepted. Meant for scan jobs, not for unrelated photos (not measured on them).

## 6.7 Predecessor

For reference, the earlier predecessor C8+L (Hough fine tilt, PP-LCNet, regressor, two passes, no review) on the same 3600 primary-pool cases flipped 4.50 % (162 accepted, since it never asks for review) against docangle's 0.58 % (0 real accepted); on the three external pools 16.1 % (FUNSD 1.7, DocLayNet 5.2, CORD 41.3) against 1.9 % (v4.4; the C8+L row is from the v4.1 run on the same cases). It is not an open-source tool you can install, so it appears here only as the starting point.
