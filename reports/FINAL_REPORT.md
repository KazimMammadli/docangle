# docangle v4.1 — final report (addenda: §10 v4.2 Fourier tilt, §11 v4.3 review rule, §15 component ablation, §16-17 PDF throughput, §19 OCR front-end study and GPU)

> **v4.2.0 (2026-10-11) replaced the Hough fine-tilt estimate by a Fourier one.** Sections 1–9 describe and measure v4.1 (still available as
> `fine_estimator="hough"`, bench candidate `docangle_hough`). Section 10 has the v4.2 numbers on the same protocol: better ≤ 1° and
> ≤ 0.5° rates, ≈ 10 ms faster, flips unchanged within noise. Section 11 (v4.3.0) replaces the confidence / review rule. Where this report and
> sections 10–11 differ, those describe the shipped default.

Date: 2026-10-10 · Hardware: AMD Ryzen 9 5980HX (16 threads), CPU only, desktop session running (load ≈ 3) · Python 3.14, OpenCV 4.14,
ONNX Runtime 1.31 · All numbers below were measured in this repository; the raw results are in `reports/bench_final_v4_1*.json`
(commit, config, hardware inside), the pooled tables in `reports/FINAL_TABLES.md`.

## 1. Summary

The task was a better replacement for the original **C8+L** pipeline (Hough mod-90 + PP-LCNet + regressor fallback + double pass):
**accuracy first** (wrong / flipped pages < 1 %, ≥ 99 % within 1°, uncertain pages to `needs_review`), **≤ 50–60 ms per page on this
CPU including decoding**, angle-only and angle+upright modes, image and PDF input.

| goal | result | verdict |
|---|---|---|
| wrong (flipped) pages < 1 % | **0.50 %** [0.32–0.79] of 3600 simulated pages on the four primary pools (C8+L: **4.50 %** [3.87–5.23]). **0.25 %** if the one source page that is itself sideways is excluded. **Caution:** those intervals treat the 3600 cases as independent, but they are rotations of only 659 distinct pages and the flips sit on 7 of them; a page-level bootstrap gives **0.11–1.14 %** (0.06–0.50 % without the sideways page) | **met on the point estimate; the page-level upper bound touches 1 %** |
| …of which sent to a human | 1.2 % of pages get `needs_review`; only **11** flips were *accepted*, and **9 of those 11 are that sideways source page** → **2 real accepted flips in 3600 (0.06 %)** | |
| ≥ 99 % within 1° | born-digital Azerbaijani pages (exact ground truth): **99.9 %** [scan 100, photo_easy 100, photo_hard 99.7]. Real-scan pools: 89–94 % against the *nominal* angle, **94.5–99.5 % against each page's own measured skew** (§5) | **met where ground truth is exact; real scans are limited by skew of the source pages** |
| latency ≤ 60 ms incl. decode | mean **41.5 ms** (1 MP JPEG), **51.8 ms** (A4 300-dpi JPEG), **51.9 ms** (12 MP phone JPEG); p95 53 / 61 / 62 ms | **met on average; p95 touches 60 ms** |
| two modes, image + PDF | `predict` / `correct`, `python -m docangle file.pdf` | done |
| honest about data | label-noise audit of every pool (§6); 20 of the 46 large errors on primary pools are caused by wrong source pages | done |

What is **not** shown: accuracy on *real phone photos of the intended documents* — no labelled set exists. Photographs are simulated
(`bench/degrade.py`); the only real photographs measured are CORD receipts, a different document type (§4). Treat the photo numbers as
a well-controlled proxy, not as a field result.

## 2. What was built

* `docangle/` — pipeline (README "How it works"), PDF input, CLI. One frozen `PipelineConfig`.
* **Own 4-way orientation classifier `orient_cls_v4`** (MobileNetV3-Large), trained on audited data (`MODEL_CARD.md`).
* `bench/` — simulator, metrics with 95 % intervals, runner with failure galleries, **accuracy guard** for speed changes, table builder.
* `src/` — data preparation, label audit, training and export.
* Tests: 58 pytest tests (geometry, API, PDF, JPEG decode/EXIF, end-to-end on real pages).

## 3. Protocol

Pages of known orientation are rotated by a random angle (uniform in [-180°, 180°] — harder than "mostly upright"), optionally
photographed by a simulator (`scan` = clean rotation; `photo_easy`; `photo_hard` = desk, keystone, shadows, blur, noise, JPEG, crop) and
given to each candidate. **Flip = error > 45°.** "Accepted" = not sent to `needs_review`. Pools: `az` (100 born-digital Azerbaijani pages),
`invoices` (RVL-CDIP, 100), `tobacco_cert` (159), `rvl_heldout` (200; shares layouts with training invoices: optimistic) — "primary";
`ext_funsd` (199 scanned forms), `ext_doclaynet` (300 report/manual pages), `ext_cord` (200 receipts photographed by phone) — external,
never trained on. 300 cases per pool and level, 3 levels, 7 pools, 4 candidates (≈ 6300 cases each). Pools with fewer unique pages than
cases are wrapped, so intervals are slightly optimistic (the unique-page count is in the per-cell table).

## 4. Results

### 4.1 Primary pools (az, invoices, tobacco_cert, rvl_heldout) — 3600 cases

| candidate | flips % [95% CI] | flips excl. sideways source page | accepted flips | ≤1° % | ≤0.5° % | needs_review % | mean ms (analysis) |
|---|---|---|---|---|---|---|---|
| **docangle (default)** | **0.50** [0.32–0.79] | 0.25 [0.13–0.47] | 11 (0.31 %) — 2 excluding that page | 93.9 | 79.1 | 1.2 | 39 |
| docangle_full (12 classifier views) | 0.47 [0.30–0.75] | 0.22 | 11 | 93.9 | 79.1 | 1.2 | 64 |
| legacy_v1 (C8+L) | 4.50 [3.87–5.23] | 4.25 | 162 (4.5 %) | 89.8 | 76.5 | 0.0 | 38 |

By level (flips %): scan 0.42 / photo_easy 0.58 / photo_hard 0.50 (C8+L: 3.0 / 4.5 / 6.0). The cheap default is statistically
indistinguishable from the 12-view variant at 40 % lower cost. By pool (flips %, all levels; C8+L in brackets): az 0.00 (0.33),
invoices 1.56 (8.89; 0.56 without the sideways source page), tobacco_cert 0.00 (1.56), rvl_heldout 0.44 (7.22).

The **≤ 0.5° rate is not better than C8+L** (79.1 vs 76.5 is within noise; per pool they trade places): the improvement is in
*not flipping pages*, not in sub-degree precision. Median error is 0.14–0.32° (C8+L 0.14–0.37°) in every primary-pool cell.

Quad-tilt mode (a random quadrant plus up to ±25° tilt — closer to "tilted documents"; 2400 cases, `reports/FINAL_TABLES_quadtilt.md`): docangle flips **0.42 %** [0.23–0.77] (0.17 % without the sideways source page; 7 accepted, 2 excluding it) vs C8+L **3.75 %** [3.06–4.59]; ≤1° 93.7 vs 90.7 %; review 1.1 %.


**Page-level uncertainty (not in the tables above).** The 3600 cases are random rotations of 659 distinct pages (az 100, invoices 100, tobacco_cert 159, rvl_heldout 300). Only **7 pages ever flip** (one of them is the sideways source page): `invoice_030` ×9, `019` ×2, `018` ×2, `000786` ×2, `011`, `001128`, `001118` ×1. So flips are not random noise but a small set of hard pages (halftone bands, near-empty pages, logo-dominated pages), and the honest interval is the page-level one: **0.11–1.14 %** (0.06–0.50 % excluding `invoice_030`), from a cluster bootstrap over pages.

### 4.2 External held-out pools — 2700 cases

| pool | docangle flips % [CI] | accepted flips | needs_review % | C8+L flips % |
|---|---|---|---|---|
| ext_funsd (scans) | 0.00 [0.00–0.43] | 0 | 0.7 | 1.67 |
| ext_doclaynet (born-digital report pages) | 3.11 [2.16–4.46] | 9 (1.0 %) | 4.6 | 5.22 |
| ext_cord (receipts photographed by phone) | 4.00 [2.90–5.49] | 3 (0.33 %) | **28.0** | **41.33** |

These are outside the primary use (receipts are narrow, blurred and sparse; many DocLayNet pages are photos/figures/title pages), and
they show where the system is weaker: ~3–4 % flips, mostly caught by review. Before the real-photo data was added to the classifier
(v3), CORD flips were 32.5 % (photo_hard, 14.9 % accepted); after (v4) 4.5 % with **0 %** accepted (`reports/bench_step8_v3_vs_v4.md`).
For such material raise `review_confidence` (at 0.85 the accepted flips on these pools fall from 0.50 % to 0.25 %, coverage 76 %).

### 4.3 Confidence → review (primary pools, pooled over levels)

| `review_confidence` | pages auto-accepted | accepted flips (of accepted) |
|---|---|---|
| 0.50 | 99.8 % | 14 (0.39 %) |
| **0.70 (default)** | **98.8 %** | **11 (0.31 %; 2 without the sideways source page)** |
| 0.85 | 94.5 % | 10 |
| 0.95 | 90.2 % | 9 |

The remaining accepted flips do not go away with a stricter threshold because 9 of them are the sideways source page, predicted
*correctly* at confidence ≈ 1. AUROC of confidence vs "result is good" is 0.62–1.0 per cell (0.88–1.0 on the external pools; lowest on `tobacco_cert` photo_easy and `invoices` photo_easy). The confidence formula was **not
recalibrated** this round; it ignores fine-angle uncertainty (see §7, item 3).

### 4.4 Latency

Measured with `predict(path)` (decode included), 60 JPEGs per class × 3 repeats, warm session, desktop running:

| input | decode | analysis | **total mean** | p95 | max |
|---|---|---|---|---|---|
| 1 MP JPEG (≈1000 px) | 1.5 ms | 40 ms | **41.5 ms** | 53 ms | 56 ms |
| A4 at 300 dpi JPEG (3508 px) | 11 ms (reduced-scale decode) | 40 ms | **51.8 ms** | 61 ms | 65 ms |
| 12 MP phone JPEG (4032 px) | 11 ms (reduced-scale decode) | 40 ms | **51.9 ms** | 62 ms | 67 ms |
| (before: full-size decode, no speculation) | 1.4 / 15 / 21 ms | 46–50 ms | 51 / 66 / 71 ms | 65 / 81 / 85 ms | 68 / 83 / 88 ms |

**Update, same day (code speed-up, accuracy unchanged):** the classifier preprocessing was rewritten (the page is resized once and
the *small* image is rotated; normalisation by a lookup table that gives bit-identical floats). On 700 fixed cases (7 pools × 2
levels, `bench.equiv`) the angles are **100 % identical**, no review flag changed, flips / ≤1° / >5° counts are identical, confidence
differs by at most 0.002; mean analysis time 40.2 → 37.7 ms. End-to-end including decode (desktop under load ≈ 8, so conservative):
**38.9 ms** (1 MP JPEG), **50.4 ms** (A4 300 dpi), **50.0 ms** (12 MP phone), p95 51.5 / 62 / 60 ms. The table above is the earlier measurement.

Stage costs: Hough ≈ 11–13 ms per pass, PP-LCNet ≈ 18 ms (4 views), own classifier ≈ 21 ms (2 views); the classifiers and the pass-2
Hough run concurrently, so the chain is ≈ 12 + 21 + small. PDF: rendering a 1400-px page is ≈ 25 ms on top (first call includes
library start-up). C8+L measured 33–43 ms in the same harness (analysis only): it is faster, and less accurate.

### 4.5 Fine angle and source skew

`bench/skew_check.py` (output in `reports/skew_check.txt`) measures every source page once *without rotation* and re-scores each case
against `gt + that skew`. It is a **consistency** measure (the reference comes from the same method), not independent accuracy.

| pool | level | ≤1° nominal | ≤1° vs own skew |
|---|---|---|---|
| az | scan / photo_hard | 100.0 / 99.5 | 100.0 / 99.5 |
| invoices | scan / photo_hard | 94.5 / 93.5 | 98.0 / 96.0 |
| tobacco_cert | scan / photo_hard | 93.0 / 92.5 | 99.5 / 99.0 |
| rvl_heldout | scan / photo_hard | 89.5 / 89.0 | 97.0 / 94.5 |
| ext_funsd | scan / photo_hard | 91.5 / 91.5 | 98.5 / 97.0 |
| ext_doclaynet | scan / photo_hard | 98.5 / 91.5 | 98.5 / 91.5 |

(2 of 200 `invoices` cases per level use a source page the pipeline itself calls tilted by more than 8°, and are left out of the
adjusted score.) So most of the gap to 99 % on real scans is the skew of the "upright" pages themselves; what remains is a few
pages on which the line detector fails (§7, item 2).

### 4.6 Seven real phone photos (qualitative, no ground truth)

Seven phone photos of printed pages (private, not published): 6 different shots, hand-held, on a desk, on a wooden floor, one
sideways, two upside down, one at 44°. All 7 were turned upright correctly **by eye**; confidence 0.91–1.00.
This is a sanity check on n = 7, not a measurement.

## 5. Data audit — wrong "upright" labels

Public "upright" scans are not reliable; this has already caused wrong results once. Details and counts: `data/README.md`.

* RVL-CDIP "invoice": a large share sideways/flipped; a model trained on the raw pages memorised the mistakes. Audited (two independent
  models + contact sheets), 1290 / 74 / 282 pages of the train / val / held-out pools moved to `*_dropped`.
* Tobacco3482: 143 of 2785 train and 21 of 348 val pages moved.
* Benchmark pool `invoices` still contains `certified_invoice_030.png`, which is sideways in the source: 9 of the 18 flips on primary
  pools are this one page predicted *correctly*. `certified_invoice_075` and `Letter_1640` are visibly skewed in the source
  (errors 5–20° and 6–7°) and produce 11 of the 28 "5–45° errors". Together **20 of the 46 large errors on primary pools are wrong
  ground truth, not model errors**. (`bench/summarize.py` reports flips with and without that page.)
* CORD / DocLayNet / FUNSD audited by eye (`reports/audit_ext_*.jpg`): the pages flagged by the pipeline were upright — model errors.
* `brno_mobile_test` turned out to be 48-px text-line crops, not pages: unusable (601 MB can be deleted).

## 6. Failure analysis (primary pools, default pipeline, 46 errors > 5° in 3600 cases, 24 pages)

Pictures: `reports/failures/final/` (degraded input | our output | source page; also `source_pages_with_errors_*.jpg`). Looked at all of them.

| class | cases | what it is |
|---|---|---|
| wrong source page | 20 | `invoice_030` sideways (9), `invoice_075` skewed (5), `Letter_1640` skewed (6) |
| sparse / dirty pages, genuine flips | ~9 flips | black halftone bands (`invoice_019`, `000786`), near-empty pages (`001128`), logo-dominated pages (`001032`); 7 of 9 were sent to review |
| fine-angle failures on dense tables | ~15 | page whose long segments are number columns / dotted leaders: Hough locks onto another axis (`001472`: 20–26° off at about half of all tested angles, confidence 0.98 — the worst single page); `018`, `070`, `008`, `011`, `036` |
| other | few | one AZ page (`docA_page_026`, review) |

On **external** pools: 96 of 178 large errors are CORD receipts (narrow, blurred, hand in frame), 34 DocLayNet (title/figure pages).

## 7. Known limits and open items

1. **No labelled real phone photos of the intended documents.** The single most useful next step: label ~300 with `tools/label_server.py`
   and run `bench.eval_labeled`; keep half held out.
2. **Fine-angle failures are confident.** Rare (pass-1 error > 5° in 0.4 % of cases) but they are accepted at confidence ≈ 1 because the
   confidence formula does not look at line agreement. A global projection-profile estimator as a cross-check was tried (below): it was
   *worse* than Hough (54 vs 7 errors > 5° in 1599 cases) and its disagreements were mostly its own mistakes, so it does not help as an arbiter.
3. Confidence is not recalibrated (kept 0.55·posterior + 0.45·lines/80, threshold 0.70).
4. Not tested: Cyrillic, Arabic-script, CJK, handwriting-only pages, A3, ID cards, heavy occlusion, multi-page consensus.
5. Source of the Azerbaijani test pages undocumented (`data/README.md`); the 100 PNGs are the only copy.
6. `rvl_heldout` shares layouts with training invoices (optimistic); `tobacco_cert` was filtered with the same models the pipeline uses.
7. **`predict` and `correct` can differ slightly on the same file**: `predict` decodes a grayscale image directly, `correct` decodes colour and converts, and Hough is sensitive to such pixel-level differences. On one of the seven private phone photos the final angle differed by 0.16° but the pass-2 residual was 3.04° vs 1.22°, which moved the confidence from 0.77 (`LARGE_RESIDUAL`, review) to 0.995. Decisions on borderline pages are therefore not bit-stable across decode paths.
8. Latency p95 is ≈ 61–62 ms for large JPEGs on a desktop under load; set `ort_intra_threads`/affinity if a hard cap is required.
9. The fallback regressor is an unreproducible old artefact; it fired in 8 of 1600 cases. It is kept because removing it raised the
   number of accepted flips (9 vs 6) — a difference of three pages, not statistically significant.
10. No `LICENSE` file; the trained weights inherit the research-only terms of Tobacco/RVL-CDIP until the maintainer decides.

## 8. Decisions and rejected experiments (all on the same simulated cases)

| experiment | result | decision |
|---|---|---|
| 12-view classifier vote vs cheap vote (PP-LCNet 4 views + own 2 views) | quadrant error 0.69 % [0.38–1.23] vs 0.81 % [0.48–1.39] (1599 hard cases); final benchmark flips 0.47 vs 0.50 % | cheap vote adopted: −25 ms |
| run the two classifiers in parallel threads | same output | adopted |
| pass 2 = local projection profile (±2°) instead of Hough | 29 vs 21 errors > 5° in 1599 cases: it cannot repair pass-1 errors larger than 2° | **rejected**; Hough pass 2 kept |
| Hough pass 2 + projection polish ("precise") | better ≤0.5° on scans (79.9 vs 78.3 %), but ≤1° on photos 91.9 vs 93.7 %; az photo_easy 97.3 vs 100 % at +10 ms | **rejected, code removed** |
| ±45° wrap in the line-angle median | pass-1 errors > 5°: 18 (wrapped median) → 7 (circular 4θ mean + median); full pipeline ≤1° 93.0 → 94.0 %, flips 11 → 9 | **adopted** (`axis_angle`) |
| weight lines by length (audit suggestion) | ≤1° fell to 66–89 % on photo cells (long edges of desk/page dominate) — `bench_step6_REJECTED_length_weighted_axis` | **rejected** |
| global projection estimator as pass-1 arbiter | worse than Hough; see §7 item 2 | rejected |
| regressor fallback on/off | 8 triggers / 1600; flips 11 / 11; accepted flips 6 / 9 | kept |
| working canvas 800 px | −6 ms but only 44.6 % of angles within 0.05° of baseline, ≤1° 90.7 vs 91.4 % | **rejected** (accuracy guard) |
| speculative pass 2 (Hough while classifiers run) | −7 ms; 2800 cases: flips 39 / 39; ≤1° 90.2 / 90.5 %; of 61 cases that differ by > 0.25° it is better in 31, worse in 30 | **adopted** (noise-level) |
| reduced-scale JPEG decode for ≥ 2 MP files | −10 ms; 400 phone-size cases ≤1° 93.2 vs 93.8 %, flips 1 / 1; A4: 95.0 vs 94.2 % | adopted, switch `reduced_jpeg_decode` |
| own classifier v4 (+ CORD train receipts, DocLayNet pages) | CORD photo_hard flips 32.5 → 4.5 % (accepted 14.9 → 0 %); DocLayNet photo_hard 8.5 → 5.0 %; az photo_hard 1.0 → 0.0 %; other pools unchanged | **adopted** |
| other open-source solutions | DocOrient (MIT): 7–48 % wrong quadrant on our pools; PP-DocLayoutV3 as a voter: 37–80 % right; Tesseract OSD / docTR: published 49 % / 64 % (not re-run); `reports/exp_docorient.json` | rejected; PP-LCNet is the only third-party model used |
| GPU | the pipeline is ≈ 40 ms of CPU work; no gain | not used (training used the RTX 3060) |

## 9. Reproduce

```bash
pip install -e ".[dev,pdf]"                      # models are read from ./models
pytest -q                                        # 125 tests
export PYTHONPATH=.
python -m bench.run --datasets az invoices tobacco_cert rvl_heldout ext_funsd ext_doclaynet ext_cord \
    --levels scan photo_easy photo_hard --angle-modes uniform \
    --candidates docangle docangle_full legacy_v1 --seeds 3 --n 100 --tag final --gallery reports/failures/final
python -m bench.summarize reports/bench_final.json > reports/FINAL_TABLES.md
python -m bench.skew_check --datasets az invoices tobacco_cert rvl_heldout ext_funsd ext_doclaynet --levels scan photo_hard
```

(`data/cache` and `data/external` are rebuilt by `src/prep_rvl_invoices.py`, `src/orient_data.py`, `src/prep_external.py`; see
`data/README.md`. The benchmark uses ≈ 4 GB RAM; run it under a memory cap on a 15 GB machine.)

## 10. v4.2 addendum — Fourier fine tilt (2026-10-11)

**Change.** The fine tilt (angle modulo 90°) is no longer the circular mean of Hough line angles (pass 1) corrected by a second Hough pass
on the straightened page. It is the peak of the radial projection of the 2-D DFT magnitude of a binarised, Tukey-windowed 512-px copy
of the page, folded modulo 90° (`docangle/fftskew.py`; idea: jdeskew, Pham et al., ICIP 2022; own port, no new dependency). Hough still runs, in a
parallel thread, only to count text lines (confidence term, `TOO_FEW_LINES`). The classifiers, the regressor fallback and the review
policy are unchanged. Found by the method survey (`reports/METHOD_RESEARCH.md`, experiment E1).

**Same protocol as §3–4** (`bench_final_v4_2.json`, `bench_final_v4_2_quadtilt.json`, tables `FINAL_TABLES_v4_2*.md`; seeds and cases are
identical to the v4.1 run, so the numbers are directly comparable; C8+L was not re-run, its v4.1 row is unchanged):

| primary pools, 3600 simulated pages | v4.1 (Hough) | **v4.2 (Fourier)** |
|---|---|---|
| flips % [95 % CI] | 0.50 [0.32–0.79] (18) | 0.58 [0.38–0.89] (21) |
| flips excluding the sideways source page | 0.25 (9) | 0.33 (12) |
| accepted flips, of which the sideways page | 11 (9) | 12 (9) → 2 vs **3** real accepted flips |
| ≤ 1° / ≤ 0.5° | 93.9 % / 79.1 % | **95.6 % / 87.3 %** |
| ≤ 1°, photo_hard | 93.7 % | **96.6 %** |
| needs_review | 1.2 % | 1.2 % |
| mean analysis time | 39 ms | **29 ms** |
| external pools (FUNSD, DocLayNet, CORD), 2700 cases: flips / ≤ 1° / review | 2.37 % / 85.9 % / 11.1 % | 2.26 % / **92.9 %** / 9.7 % |
| quad_tilt, primary pools, 2400 cases: flips / ≤ 1° | 0.42 % / 93.7 % | 0.46 % / **95.5 %** |
| DISE-2021, 600 pages (`dise_eval_v4_2.txt`): ≤ 1° / errors > 5° | 89.3 % / 51 | **94.3 % / 34** (all 34 are quadrant errors) |

**What it did not change, honestly.** The 90°/180° decision is made by the classifiers, which the new tilt estimate does not touch. The
flip counts differ by +3 cases on primary pools (spread over three different source pages: invoice_018 3 vs 2, plus one new flip on each of two
other pages), inside the confidence intervals; in the 2800-case paired guard (`guard_e1_fft_vs_hough.txt`) flips were 39 (Hough) vs 41
(Fourier) and in a 1260-case paired dump 19 vs 17. Read this as "no systematic change", not as an improvement. The real accepted flips on primary pools went from 2 to 3 cases (0.06 → 0.08 %).
The quadrant problem (receipts 2.3 % flips, DISE covers / vertical text / noisy scans) is the next target (`METHOD_RESEARCH.md` E2–E4).

**Paired guard, 2800 cases (7 pools × scan/photo_hard × 2 seeds, same cases)**: ≤ 1° 90.2 → 93.8 %, ≤ 0.5° 74.9 → 86.3 %, errors > 5° 95 → 51, the
Fourier estimate better by > 0.25° in 668 cases and worse in 117, mean analysis 37.1 → 29.9 ms. In the 1260-case paired dump no pool got worse by more than one case in
errors > 5° (invoices 2 → 3); CORD receipts 26 → 9.

**Latency (JPEG decode included, same session, desktop under load, 36 pages × 3 repeats; Hough/Fourier measured back to back):**

| input | v4.1 (Hough) mean / p95 | **v4.2 (Fourier)** mean / p95 |
|---|---|---|
| ≈ 1 MP JPEG | 56.2 / 65.0 ms | **35.3 / 41.3 ms** |
| A4 300 dpi JPEG | 62.5 / 72.5 ms | **41.7 / 47.4 ms** |
| 12 MP phone JPEG | 62.6 / 74.2 ms | **40.7 / 45.6 ms** |

(The machine was busier than when §4.4 was measured, so the v4.1 row is higher than the 39–50 ms quoted there; the *difference* is the
valid comparison. The Hough pass-1 on the critical path is replaced by a ≈ 4 ms Fourier step, and pass 2 is gone; Hough only runs next to the classifiers.)

**Skew check (`skew_check_v4_2.txt`, same method as §4.5).** Against the nominal angle ≤ 1° rose in most pools (Tobacco photo_hard 92.5 → 97.5 %,
RVL photo_hard 89.0 → 92.5 %, FUNSD photo_hard 91.5 → 95.0 %, DocLayNet photo_hard 91.5 → 94.0 %; RVL scan 89.5 → 89.0 % is flat). Against each page's *own* measured skew the
picture is mixed, and this measure is only a consistency check, because the reference now comes from the Fourier method too (median |source skew| 0.26–0.32° on the real-scan
pools instead of 0.00° with Hough): invoices 98.0 / 96.0 → 98.5 / 99.0 %, Tobacco scan 99.5 → 100 % but **Tobacco photo_hard 99.0 → 95.5 %**, RVL scan 97.0 → 99.0 %,
RVL photo_hard 94.5 → 93.5 %. So on blurred, shadowed Tobacco photos the Fourier estimate is less repeatable than Hough (7 of 200 cases), elsewhere equal or more repeatable. Only labelled real photos can settle this.

**Tried in the same step and rejected:** `fft_alarm_deg` (confidence −0.15 when |Hough − Fourier| > 3°): on 1260 cases it fired 6 times, 5 of them on
correct pages, no accepted flip avoided; kept as an opt-in config field, off by default. Replacing pass 2 by a second Fourier estimate was worse on photos in the survey
(agent measurement), so pass 2 was dropped, not replaced.

**Known weaknesses of the Fourier tilt** (from the survey, not yet reproduced here): receipts with strongly slanted paper edges can pull the folded
estimate by 4–5° (a text-line vs vertical-line family split is a hypothesis in `METHOD_RESEARCH.md`); asymmetric perspective is not simulated; and
all of this is on simulated photographs of known pages — real labelled phone photos are still the missing number.

## 11. v4.3 addendum — review rule (2026-10-11)

**Finding.** The confidence `0.55·posterior + 0.45·min(1, lines/80)` (never calibrated, audit F-10) had a structural flaw: with ≥ 80 text lines the
second term is 0.45, so any quadrant posterior above 0.45 gives confidence ≥ 0.70 and the page is **never** sent to review (only the regressor fallback,
−0.20, could still trigger it). Dense pages — exactly where classifiers are most often confidently wrong about the quadrant — were therefore not reviewable. On
6291 cases (`bench.features` dump, 1357 pages) the 73 flips had 41–498 lines (13 of them accepted); 51 of the 73 flips were fallback cases.

**Experiment** (`bench/features.py`, `bench/calibrate.py`, output `calibrate_e2.txt`; all analyses page-disjoint):
* *Voter fusion* (weights, temperature of the two voters): better NLL (0.0170 → 0.0129) but the same 25 quadrant errors. No change made.
* *Learned review score* (logistic regression on 9 features, 5-fold page-grouped and leave-one-pool-out): at the old review rate accepted flips 13 → 3 (5-fold) / 13 → 5 (leave-one-pool-out).
* *Parameter-free rule* `confidence = fused posterior − 0.30·fallback`, review < 0.90: better than the learned model (primary pools: 1.1 % review and 0 accepted flips at the same
  review rate where the old rule accepted 3; external: 3.8 % review instead of 9.7 %, 6 accepted instead of 10). Line count has no signal for fine-angle errors either
  (accepted errors > 5° are 0.1–1.1 % in every line-count bucket). The line term was dropped; `TOO_FEW_LINES` (< 8 lines) stays a separate gate.

**Shipped** (`PipelineConfig.confidence_model="posterior"`, `fallback_penalty=0.30`, `review_confidence=0.90`, `high_confidence=0.97`; the old rule stays as `confidence_model="legacy"`, bench
candidate `docangle_conflegacy`). Angles do not change, only `confidence` and `needs_review`. **The threshold 0.90 was picked on the same 6291 cases that
the first rows of the table below use (the benchmark cases are identical), so those rows are partly in-sample.** Independent checks, run after the change with the old rule alongside:

| check | old rule | **new rule** |
|---|---|---|
| final protocol, primary pools (3600): review % / accepted flips | 1.2 % / 12 (9 are the sideways page) | **1.1 % / 9 (all 9 are the sideways page → 0 real)** |
| final protocol, external pools (2700): review % / accepted flips | 9.7 % / 10 | **3.8 % / 6** |
| …CORD receipts (900): review % / accepted flips | 23.9 % / 2 | **7.6 % / 1** |
| quad_tilt, primary pools (1600, not used for fitting): review % / accepted flips | 0.9 % / 4 | 1.1 % / 4 (**no gain**) |
| quad_tilt, external pools (1200): review % / accepted flips | 9.5 % / 5 | **2.5 % / 3** |
| DISE-2021, 600 pages (different data): review flagged / accepted errors > 5° | 22 / 18 | **42 / 6** (more reviews: +3.3 points) |

Result in one line: on out-of-domain pages accepted flips drop and receipts need far fewer reviews; on the primary pools the benefit is small and not proven (the
quad_tilt check on the primary pools shows no change; the uniform protocol shows 3 → 0 real accepted flips but on data that tuned the threshold). A stricter threshold is a one-line change
(on the 6291 cases 0.95 gives 2.6 % review on primary pools, 0 accepted flips; external 7.2 % review, 2 accepted flips; 0.98: 6.4 % / 14.6 % review, 0 / 0).
`high_confidence` (0.97) only labels `quality`; it does not change what is reviewed.

Final tables: `FINAL_TABLES_v4_3.md`, `FINAL_TABLES_v4_3_quadtilt.md` (raw `bench_final_v4_3*.json`, `bench_e2_conf_quadtilt.json`, `dise_eval_v4_3.txt`).

## 12. E3b — docTR page-orientation model as a third voter: rejected (2026-10-11)

Model: `mobilenet_v3_small_page_orientation` from OnnxTR v0.6.0 (Apache-2.0, 6.1 MB, 512² letterboxed input; downloaded with the maintainer's approval to
`data/external/doctr/`, sha256 `60606ce4…aa67`, not part of the package). Class mapping measured on 48 upright pages × 4 rotations (docTR logit index → our clockwise
class: 0→0, 1→3, 2→2, 3→1). Evaluated on the 6291 cases of the §11 dump (`bench/exp_doctr.py`, `bench/exp_doctr_eval.py`, `bench/exp_doctr_analyze.py`, raw output `reports/exp_doctr_e3b.txt`):

| quadrant errors, 5603 non-ambiguous cases | all | primary pools | external |
|---|---|---|---|
| PP-LCNet alone | 382 | 157 | 225 |
| own classifier v4 alone | 36 | 7 | 29 |
| **docTR alone** | **295** | 138 | 157 |
| current fusion (PP-LCNet + own) | **25** | 6 | 19 |
| + docTR, weight 0.25 / 0.5 / 1.0 | 25 / 26 / 32 | 6 / 7 / 7 | 19 / 19 / 25 |

docTR alone is far weaker than our classifier (295 vs 36 errors; 25 errors even on born-digital Azerbaijani pages where ours makes 0). Of the 25 errors of the current fusion it
would fix 9 but is wrong on 279 pages the current fusion gets right, so fusing it never reduces quadrant errors (25 → 25 at weight 0.25, worse above). With weight 0.25 the review rate at
threshold 0.95 falls (primary pools 2.6 → 1.8 %, external 7.2 → 4.5 %) at equal accepted flips, but that costs **+17 ms per page** (2 views at 512²) and a third-party model whose training data
is undocumented, so it is not adopted. The model file is kept locally in case it is wanted for labelled photos of the intended documents (it can be compared with `bench.exp_doctr_eval` there).

## 13. E5 — multi-page consensus (optional feature, 2026-10-11)

`docangle/consensus.py`, API `predict_job` / `predict_pdf` / `apply_job_consensus`, CLI `--consensus` (opt-in, default behaviour unchanged). Each page's fused
quadrant posterior (`Result.posterior`) is combined with a leave-one-out vote of the other pages that tolerates 5 % odd pages (formula in the module docstring); the page
takes the combined argmax, confidence = combined posterior (− fallback penalty), review < 0.90. A confident page against a nearly unanimous job keeps its answer and is reviewed
(`JOB_DISAGREE`). No new model, ≈ 0.1 ms per page, the fine angle is never shared.

Evaluation (`bench/consensus_eval.py`, output `reports/consensus_eval.txt`): 1000 pages in 100+ jobs, photo_easy and photo_hard; the 5 real Azerbaijani documents (100 pages) plus pseudo-jobs of
10 random pages from invoices, RVL, DocLayNet and CORD.

| scenario | flips | accepted flips | reviews |
|---|---|---|---|
| all pages of a job share the orientation | 6 → **2** | 3 → **0** | 23 → **6** |
| one page in ten has another orientation (90 odd pages) | 6 → 5 | 3 → 0 | 24 → 96 (all 90 odd pages are reviewed) |

In the mixed scenario 87 of the 90 odd pages kept their correct answer and 3 were turned wrong by the job; all 90 were sent to review, so none was accepted silently. **Limits:** on the real
Azerbaijani documents there was nothing to repair (0 flips before and after); the gains come from pseudo-jobs whose pages are independent, which overstates the benefit (hard pages cluster inside real
documents); n is small (6 flips before). Only meaningful for scan jobs: phone photos of unrelated pages turned differently must not be one job.

## 14. Real phone footage: SmartDoc 2015 (2026-10-11)

First *real* camera data with ground truth (downloaded with the maintainer's approval: SmartDoc-CH1 `frames.tar.gz`, 972 MB, GitHub release v2.0.0, sha256 verified, CC-BY 4.0,
`data/external/smartdoc/`, not in git; tool `bench/smartdoc_eval.py`, outputs `reports/smartdoc_eval*.txt`). 150 video clips, 30 English documents (datasheet, letter, magazine, paper,
patent, tax) filmed on 5 backgrounds; GT angle comes from the four document corners (page-edge direction, so perspective can shift it by 1–2° from the text-line direction).
926 frames (every 25th of each clip; the 150 clips, not the frames, are the independent units); `--rot90` additionally turns each frame by a random multiple of 90°.

**Whole frame (document is only 10–25 % of a 1920×1080 frame; desk, mouse and cables around it): outside the design of this pipeline** (it assumes the page fills the image):
docangle v4.3 median error 1.4°, ≤ 2° 57.6 %, flips 8.9 % (82 of 926) of which 81 were sent to review (review 23.9 %, 1 accepted flip); legacy C8+L flips 16.7 %, none reviewed.
Contact sheet of the failures: the text in the frame is tiny and the background dominates; the GT is correct.

**Document cropped out (corners + 8 % margin, as a perfect document detector would):**

| 926 frames | median error | ≤ 1° | ≤ 2° | ≤ 5° | flips > 45° | review | accepted flips |
|---|---|---|---|---|---|---|---|
| **docangle v4.3** (Fourier tilt + posterior review) | **0.40°** | **75.7 %** | **84.6 %** | **92.1 %** | **2.7 %** (25) | 6.7 % | **1** |
| docangle_hough (v4.1 fine tilt, old review) | 0.72° | 61.0 % | 74.7 % | 85.3 % | 2.9 % (27) | 13.7 % | 2 |
| docangle_conflegacy (Fourier tilt, old review rule) | 0.40° | 75.7 % | 84.6 % | 92.1 % | 2.7 % (25) | 12.2 % | 2 |
| legacy C8+L | 0.80° | 57.2 % | 70.3 % | 81.3 % | 7.9 % (73) | 0 % | 73 |

With random 90° turns on top the picture is the same (docangle flips 2.3 %, review 7.2 %, 2 accepted; C8+L 7.1 %, 66 accepted). Flips by type (docangle, crop): magazine 7, patent 8, paper 6, letter 2, tax 2, datasheet 0 of ≈ 150 each: pages dominated by photographs and drawings.

**What this says.** (1) On real footage the Fourier fine tilt is clearly better than Hough (≤ 1° 75.7 vs 61.0 %, median 0.40 vs 0.72°) — the simulated gain is confirmed on a real camera. (2) The new review rule
keeps the reviewed share half that of the old rule at the same number of accepted flips. (3) docangle beats C8+L on every metric; its flips are almost all caught by review, C8+L's never. (4) **If the photos of the intended documents
contain much background (a page lying on a desk), a document-detection / crop step in front is the biggest missing piece**: without it flips are 9 % instead of 2.7 %, almost all sent to review. SmartDoc's corner
annotations would allow testing such a step. (5) Limits: these are low-resolution preview frames of English pages (≈ 400 px page height), page-edge GT, only 30 distinct documents.

## 15. Component ablation: is anything in the pipeline redundant? (2026-10-13, v4.3.1)

**Method.** A multi-agent analysis (5 analysts, 8 independent skeptics who re-derived the numbers; the plan itself is not published) proposed which stages could be
removed; the proposals were then tested here. A per-view dump (`bench/views_dump.py`: PP-LCNet softmax of all 8 views, own-classifier logits of all 4 rotations, regressor output always, Fourier tilt,
Hough line count; 6300 cases = 1357 pages, `reports/data/views_v4_3_dev.json.gz`) lets `bench/ablate.py` rebuild every variant OFFLINE (`bench/views_emulate.py`); the emulation of the default reproduces the
real pipeline exactly (self-check on 6291 cases: 0 angle differences outside regressor-override rows, 1 review flag differs). All comparisons are paired, resample PAGES (cases of one page are rotations of the same
document), and compare accepted flips **at the default's review rate**. Dev results: `reports/ablation_dev.txt`. Independent checks: `smartdoc_ablation_*.txt`, `dise_ablation.txt`; idle-machine timing: `timing_ablation.txt`.
**Limits:** the in-sample dump chose the 0.90 threshold; the "held-out" file holds only 300 new pages (RVL; the other pools are exhausted by seeds 0-2) and is uninformative (`ablation_heldout.txt`); no text-less pages exist in the simulated pools; real labelled photos of the intended documents are still missing.

**Dev results, all pools (5603 cases outside the ±45° zone, 1357 pages), paired difference to the default [95 % page-cluster CI]:**

| variant | flips | accepted flips (equal review rate) | verdict |
|---|---|---|---|
| default v4.3.1 | 51 | 5 | |
| PP-LCNet alone | 445 (+394 [+330,+460]) | 364 | needs our classifier |
| **our classifier alone** (PP-LCNet removed) | 54 (+3 [−11,+17]) | 12 (**+7 [+1,+15]**) | **keep PP-LCNet** |
| 12 views (centre+full ×4, own ×4) | 46 (−5 [−15,+4]) | 4 (−1 [−4,+2]) | no gain for +25 ms |
| PP-LCNet 1 view | 73 (+22 [+10,+34]) | 11 (+6 [+2,+11]) | worse |
| PP-LCNet 2 views (rot 0, 2) | 50 (−1 [−7,+5]) | 5 (0) | non-inferior |
| own classifier 1 view (0° only) | 47 (−4 [−13,+5]) | 4 (−1 [−3,0]) | non-inferior |
| PP-LCNet 2 + own 1 view | 51 (0 [−10,+9]) | 7 (+2 [0,+5]) | borderline |
| TOO_FEW_LINES angle = regressor (v4.3) | 59 (+8 [+1,+17]) | 5 | **adopted the classifier angle (v4.3.1)** |
| no TOO_FEW_LINES gate | 51 (0) | 5 | no effect on this data (no text-less pages) |
| regressor override off (all rows) | **25 (−26 [−38,−15])** | 5 (0) | see below |

**Decisions.**
1. **TOO_FEW_LINES angle from the classifier instead of the regressor — adopted (v4.3.1).** Changes only the 6 of 900 cases that hit the gate (equiv test; regressor flips 5 → 0; confidence and review identical); on SmartDoc cropped footage flips fall 25 → 14.
2. **PP-LCNet — keep.** Not redundant: without it accepted flips rise by 7 [+1,+15] at equal review.
3. **Regressor override — neutral, kept.** Without it the *displayed* angle is better in the dev dump (51 → 25 flips), on DISE (34 → 29) and on cropped SmartDoc (14 → 12), but **worse on whole SmartDoc frames (59 → 85)**; the number of *accepted* flips never changes (5/5; SmartDoc 1/1; DISE 6/6), because every page where the regressor acts is reviewed anyway. No saving in time (mean 33.64 vs 33.68 ms). Candidate `docangle_noreg_flag` (no model, `ambiguity_flag=True`) is kept for photos of the intended documents.
4. **12 views, Hough thread / TOO_FEW_LINES gate — keep as is.** The gate's real job (blank, graphic, non-Latin pages) is not covered by any test set; the skeptics refuted "the Hough thread is vestigial" (inconclusive).
5. **View reduction — a speed option, not a new default.** Idle-machine timing (300 pages ×3, interleaved, `analyze()` only; machine load average ≈ 7.5 from the desktop, so absolute values are pessimistic but the order is valid): default 33.6 ms mean / 47.3 pages/s with 4 workers; own 1 view (`orient_rots=(0,)`, candidate `docangle_or1`) **29.5 ms / 60.4 pages/s (−12 % / +28 %)**; PP-LCNet 2 views 32.1 ms / 52.7; both (`docangle_lc2or1`) **27.9 ms / 70.7 pages/s (−17 % / +49 %)**; p95 unchanged (≈ 50 ms). Accuracy: non-inferior on the dev dump for `or1`; on real footage `or1` shows 14 vs 14 flips (SmartDoc crop), 19 vs 16 with random 90° turns, accepted 2 vs 1-2; `lc2or1` accepted 5 vs 1 on whole frames and +2 [0,+5] on the dev dump, so it is the riskier one. **The default stays at full views (accuracy first: the ≤ 50-60 ms goal is already met); `docangle_or1` and `docangle_lc2or1` are documented speed profiles to be judged on photos of the intended documents.**

**Cleanups proposed by the analysis but not done** (behaviour-preserving, would need `bench.equiv` proof each): split `analyze()` into a Fourier and a Hough path, one image loader instead of three, silent `orient_cls_v1` fallback → error, `gap` only when the alarm is on. Documentation inconsistencies it found (MODEL_CARD fine-tilt description, README layout, config comments) are fixed.

**Addendum (2026-10-13): what removing PP-LCNet would save.** `lcnet_weight=0` now skips the model entirely (`docangle_ownonly`); same timing protocol as above (300 pages ×3, interleaved, `analyze()` only; `reports/timing_pplcnet_removal.txt`):

| profile | mean | median | p95 | pages/s, 4 workers |
|---|---|---|---|---|
| default (PP-LCNet 4 views + own 2 views) | 34.2 ms | 29.9 | 52.3 | 47.1 |
| PP-LCNet removed (`docangle_ownonly`) | 31.0 ms (−3.2, −9 %) | 25.8 | 50.2 | 56.1 (+19 %) |
| own classifier 1 view (`docangle_or1`) | 30.1 ms (−4.1, −12 %) | 26.4 | 51.0 | 61.7 (+31 %) |
| minimal: PP-LCNet removed + own 1 view (`docangle_min`) | 27.5 ms (−6.7, −20 %) | 24.5 | 49.1 | 76.6 (+63 %) |

The gain is small per page because PP-LCNet runs in parallel with our classifier (which is the longer branch) and the p95 tail hardly moves; the larger effect is on throughput (CPU saved). The price is safety: in the dev dump
(§15) accepted flips at equal review rate rise by +7 [+1,+15] without PP-LCNet. Default unchanged.

## 16. PDF throughput and a thread-safety bug (2026-10-13)

**Bug found by timing a 100-page PDF with 4 threads:** PDFium (the PDF renderer behind `pypdfium2`) is not thread-safe. `predict_pdf`, `predict_job` and the CLI with `--threads N` rendered pages concurrently,
which crashed the process (`double free or corruption`) or returned unreadable pages (18 of 100 pages undetermined in one run; with the lock removed in an isolated test 90 of 300 renders failed). Single-thread use and all
image input were never affected. **Fixed:** all PDFium calls are serialised by a module lock (`docangle/pdf.py`); the analysis of the pages still runs in parallel. Regression test `test_threaded_rendering_is_safe`.

**Measured throughput after the fix** (this laptop, desktop running; end to end = PDF render at 1400 px + analysis; `predict_job`, no consensus):

| 100-page PDF | 1 worker | 4 workers |
|---|---|---|
| born-digital (Labour Code, text layer) | 7.9 s (79 ms/page) | **2.5 s (25 ms/page)** |
| scanned, A4 300 dpi gray, 87 MB (synthetic, zlib-compressed pages) | 11.5 s (115 ms/page) | 8.3 s (83 ms/page) |

Scanned pages are render-bound: decoding and down-scaling a 2480×3508 image takes ≈ 100-160 ms in PDFium and, because of the lock, renders run one at a time. Faster options not yet done: render in several processes
(each with its own PDFium and pipeline; estimated 3-4 s per 100 scanned pages), or `no_smoothimage` rendering (−37 % render time, but nearest-neighbour down-scaling would have to be validated for accuracy). Real scanned PDFs with JPEG pages may behave differently from this synthetic file.

## 17. Faster scanned PDFs: JPEG fast path (2026-10-13; opt-in)

**Why.** A scanned PDF page is one big image; PDFium decodes all 8.7 MP of a 300-dpi A4 page and scales it (≈ 66 ms for JPEG, ≈ 130 ms for zlib), one page at a time (§16), while our analysis needs only a ≤ 1000-px gray canvas (≈ 30-45 ms).
**What was done.** A 13-agent analysis (5 analysts, 8 skeptics; the plan itself is not published) designed the options; the answers of the intended user (only the angle is needed, no corrected output; no hard time target; scan format unknown, hardware unknown) selected the low-risk ones:
1. `docangle/pdf_fast.py`, switch `PipelineConfig(pdf_fast_path=True)` / CLI `--pdf-fast` (**default off**; kill switch `DOCANGLE_PDF_FAST=0`; `pdf_fast_stats()` shows which path each page took): when the page is exactly one full-page 8-bit JPEG (axis-aligned, covering the page box within 1 %, nothing else visible except an invisible OCR text layer), its raw JPEG bytes are copied out under the PDFium lock (≈ 1 ms), decoded at reduced size (DCT scaling 1/2…1/8) **outside** the lock, turned to the viewer's orientation (/Rotate and the image matrix: 4 × 8 combinations checked pixel-for-pixel against PDFium) and resized to the canvas PDFium would produce. Anything else (annotations, visible text, paths/forms, several images, clip paths, transparency, Flate/CCITT/JBIG2/JPX, CMYK, images smaller than the canvas, skewed placement, `/Decode` `/SMask` `/Mask` `/OCProperties` anywhere in the file, a failed canary comparison on the document's first page) falls back to the normal rendering, which then gives exactly the previous result. EXIF orientation inside the JPEG is ignored like PDFium does.
2. Always on (not opt-in): CLI `--threads` defaults to automatic (min(4, CPUs)) instead of 1; a PDFium error on one page now gives UNREADABLE for that page instead of aborting the whole job.

**Accuracy** (`bench/pdf_equiv.py`, `reports/pdf_equiv.txt`): 560 benchmark pages with known angles (7 pools × scan/photo_hard), wrapped into scanner-style one-page JPEG PDFs (150 dpi gray, 300 dpi gray, 200 dpi colour, q 75) and analysed both ways: all 560 took the fast path; 551 differ by ≤ 0.05° (9 differ more; 7 by > 0.25°); every one of the 7 is a page that is sent to review by both paths (confidence < 0.9), including the single quadrant difference (render 0.894, fast 0.555); the only confident page that differs moves by 0.26°; flips against truth 5 (render) vs 6 (fast), ≤ 1° 95.2 % vs 94.8 %, paired better/worse 2/5: the same noise level as the other resampling changes accepted earlier (reduced-size JPEG decode, Fourier tilt). No new silently accepted flip. Unit tests: 51 in `tests/unit/test_pdf_fast.py` (geometry for 4 /Rotate × 8 matrices, EXIF, progressive/colour/OCR-layer pages, 11 trap PDFs that must fall back and then equal the render exactly, token scan across a chunk boundary, threaded stress with a check that no decode runs while the PDFium lock is held).

**Speed** (this laptop, desktop running, 3 repeats alternating, medians):

| job | render (before) | fast path |
|---|---|---|
| CLI, 100-page JPEG scan (300 dpi A4, 63 MB), start-up included | 6.9 s | **2.7 s** (peak RSS +30 MB) |
| in-process, 100 pages, 4 workers (earlier run) | 6.8 s | 2.3 s (1 worker: 9.4 → 4.2 s) |
| 20 pages / 3 pages JPEG scan | 1.37 s / 0.23 s | 0.57 s / 0.16 s |
| zlib scan PDF, 100 pages (not eligible) | 6.62 s | 6.65 s (falls back, no loss) |
| born-digital text PDF, 100 pages | 2.35 s | 2.46 s (+5 %: the eligibility check that finds text / annotations) |

(The CLI default of 4 threads is already included in the 6.9 s; with the old default of 1 thread it was 9-12 s.)

**Limits, honestly.** (1) Everything above uses synthetic scanner-style PDFs built from our own test pages (clean, bicubic-upsampled, one JPEG per page); no real scanner or phone-app PDF has been seen, so the share of real files that are eligible is unknown, and the default therefore stays OFF until `bench/pdf_equiv.py` has been run on real pages. (2) What PDFium's API cannot show is guarded only by a file-level byte-token scan and a one-page canary; a document where only some pages carry such a feature could slip through (documented, kill switch exists). (3) Not bit-identical to rendering. (4) The upright output (`-o`, `correct()`) still renders through PDFium. (5) Not done from the plan: multi-process render farm, Flate / 1-bit / JBIG2 / JPX fast paths, no_smoothimage, `predict`-only 1000-px render; zlib and 1-bit scans keep the old speed (≈ 6.6 s per 100 pages here).

## 18. Batch CLI: lean threads and streaming output (2026-10-13)

**Profile first** (`bench/profile_stages.py`, `reports/profile_stages.txt`, ~100 pages, median ms): Fourier tilt 5.0, straighten 0.7, PP-LCNet ONNX (4 views) 11.4, our classifier ONNX (2 views) 17.3 + views 3.1, both classifiers together 20.8
(the longer branch is ours), Hough thread 19 (parallel), whole page 30 ms wall but **≈ 190 ms of process CPU time**: OpenCV and ONNX Runtime threads busy-wait and oversubscribe the cores. Thread scaling with 1/2/4/6/8 caller threads gives only ×1.0/1.24/1.34/1.29/1.23.
Start-up (fresh process): `import docangle` 105 ms, 3 ONNX sessions 75-94 ms each (created lazily on first use), CLI for one image 0.30 s.

**CPU knobs** (`bench/cpu_knobs.py`, `reports/cpu_knobs.txt`; fresh process per variant; results compared case by case): ONNX Runtime without spinning plus OpenCV on 1 thread cut CPU per page from 186 to 86 ms (1 caller) and 240 to 157 ms (4 callers) with **identical angle, confidence and review flag on all 96 pages**.
(Single-page latency gets slower with OpenCV on 1 thread: 28.8 → 35.9 ms, so this is for batches only. Forcing 1 ONNX thread per session was left out: it changed ≈ 1 % of angles in an older test.)

**Adopted in the CLI** (always for batches, i.e. `--threads > 1` with more than one page; `--no-lean` switches it off; `PipelineConfig(ort_spinning=False)` is the library switch, candidate `docangle_lean`): measured end to end on three batch inputs, 3 alternating repeats each, **results identical in all 100/100/176 pages**, total CPU (user+sys) **−35 % (100-page JPEG scan PDF), −29 % (100 PNG pages), −33 % (176-page text PDF)**; wall time unchanged on this 16-thread laptop (the machine had a busy desktop). The expected benefit on a machine with few cores (less contention, more pages/s) is plausible but **not measured**.
Also: CLI output is now **streamed** (each result is printed, and its upright image written and dropped, as soon as it is ready, in input order): the first result of a 100-page PDF appears after 0.5-0.8 s, and `-o` no longer holds all page images in memory. `--consensus` still waits for the whole job. No speed regression against the previous CLI under identical load (8.8 vs 8.9 s).

## 19. Do ready-made OCR engines make the angle step unnecessary? (OCR study, 2026-10-13) and docangle on the GPU

**Question.** If the aim is to read the text, perhaps an OCR that reads rotated / skewed pages by itself is enough. **Method** (`bench/ocr_rotation_eval.py`, raw outputs `reports/ocr_rotation/*.json`, tables `all_tables.txt`): 12 Azerbaijani pages (official orders, Labour Code; ground truth = the text layer of the born-digital PDFs), each rotated by 0, 5, 15, 30, 45, 90, 135, 180, 270° (white expanded canvas), read by three engines under: the engine as it is ("native", incl. each engine's own orientation options), **docangle first** ("ours"), and the page turned back by the known angle ("oracle", the ceiling). Metric: word F1 (order independent, diacritic-folded), CER, seconds per page.
Engines: EasyOCR 1.7.2 (`az`, GPU), PaddleOCR 3.7 PP-OCRv6 medium (GPU, paddlepaddle-gpu 3.2.2), Tesseract 5.5.3 (`aze`, 1 thread, CPU).

**Word F1 %, mean of 12 pages:**

| condition | 0° | 5° | 15° | 30° | 45° | 90° | 135° | 180° | 270° | mean |
|---|---|---|---|---|---|---|---|---|---|---|
| EasyOCR as is | 98.5 | 84.2 | 96.7 | 91.8 | 70.0 | 5.9 | 4.2 | 2.8 | 6.2 | 51.1 |
| EasyOCR `rotation_info=[90,180,270]` (3.5× slower) | 92.1 | 74.2 | 80.9 | 78.0 | 73.6 | 47.9 | 69.2 | 90.4 | 44.0 | 72.3 |
| **EasyOCR + docangle** | 98.6 | 98.3 | 98.4 | 98.5 | 98.5 | 98.6 | 98.5 | 98.2 | 98.4 | **98.4** (oracle 98.4) |
| Paddle v6 as is (no orientation modules) | 99.3 | 99.4 | 99.1 | 99.2 | 99.3 | 6.3 | 6.3 | 6.2 | 99.2 | 68.3 |
| Paddle v6 + its own doc-orientation / unwarping / text-line modules | 98.8 | 97.6 | 93.4 | 56.3 | 45.0 | 98.9 | 33.1 | 98.4 | 98.2 | 79.9 |
| **Paddle v6 + docangle** | 99.3 | 98.9 | 99.1 | 98.9 | 99.0 | 99.3 | 98.9 | 98.8 | 98.7 | **99.0** (oracle 99.0) |
| Tesseract as is | 96.4 | 95.8 | 1.8 | 0.1 | 0.0 | 2.4 | 0.4 | 2.7 | 97.1 | 33.0 |
| Tesseract + OSD (psm 0) + turn | 96.4 | 95.8 | 1.8 | 0.0 | 0.0 | 96.4 | 0.2 | 73.9 | 66.3 | 47.9 |
| Tesseract + popular recipe (minAreaRect deskew + OSD) | 96.4 | 89.9 | 81.7 | 89.6 | 66.0 | 88.6 | 73.6 | 66.1 | 73.5 | 80.6 |
| **Tesseract + docangle** | 96.4 | 97.7 | 97.6 | 97.5 | 97.7 | 96.5 | 97.8 | 97.7 | 97.8 | **97.4** (oracle 97.4) |

**Findings.** (1) No engine reads all angles by itself. EasyOCR fails on quarter turns and drops to 70 % at 45°; Paddle's text detector reads tilts up to 45° by itself (so the claim that modern detectors handle arbitrary angles is **partly true**) but fails at 90/135/180°, and its built-in orientation modules fix quarter turns but damage tilted pages (56 % at 30°); Tesseract needs the page within a few degrees, and with its OSD the word F1 is only 73.9 % at 180° and 66.3 % at 270°. (2) With docangle in front, **all three engines reach the oracle level at every angle**: the front end found the angle within 1.5° on 108/108 pages and sent none to review, costing 40-44 ms per page. (3) The recipe from popular tutorials (minAreaRect + OSD) gives 80.6 % and costs 0.7 s more per page than docangle. (4) Same-page speed at 0° (A4, 150 dpi, 45 lines): Tesseract 1.2-1.7 s (CPU), Paddle v6 medium **1.05 s on the GPU** / 9.5 s on a healthy CPU build (paddle 3.2.2; the installed 3.3.1 has a oneDNN regression: 21-52 s) / 99.9 % word F1 on this page, EasyOCR 1.9 s (GPU) / 10.5 s (CPU). **Paddle's mobile PP-OCRv5 latin model drops the Azerbaijani letter ə (word F1 48 %): do not use it; the v6 medium model reads ə correctly.** The "100-250 ms per page on CPU" claim for PaddleOCR mobile does not hold for a full page here.
(5) Textbook deskew (cv2.minAreaRect as in tutorials, `bench/simple_deskew_baseline.py`): 83.5 % within 1° on clean simulated scans, 11 % on simulated hard photos, **12 % within 1° (median error 4.4°) on real SmartDoc phone frames** against 77 % (0.4°) for docangle's Fourier tilt; it also cannot tell 0 from 90 / 180 / 270°.
**Recommendation:** docangle (CPU) in front of the OCR. With a GPU: PaddleOCR PP-OCRv6 medium (best accuracy); CPU-only: Tesseract `aze`. **Limits:** 12 pages from 5 documents, clean (not photo-degraded) rotations, one document family, three engines; no real phone photos; the "native" modes are the engines' documented / tutorial usage, not exhaustive tuning. The page straightening ("ours" and "oracle") was bilinear in these runs, as in versions before 4.3.2; §20 shows that the newer rotation reads the same (differences ≤ 0.5 word-F1 points).

**docangle on the GPU** (`PipelineConfig(ort_provider="cuda")`, needs `onnxruntime-gpu` and CUDA 12 / cuDNN 9; `bench/gpu_ab.py`, `reports/gpu_ab.txt`, RTX 3060 laptop GPU, same python environment for both columns): only the three ONNX models move (the Fourier tilt, Hough and resizing stay on the CPU).
120 pages: **angle identical to 0.01° on 120/120, review flags identical, max confidence difference 0.0000**; one page: median **38.6 → 16.8 ms** (p95 44.6 → 28.5), process CPU time per page **226 → 102 ms**; throughput with 1 / 4 caller threads **24 → 55 / 18 → 97 pages/s** (the CPU column of this environment is slower than the project's own venv, where the lean CPU mode reaches 45 pages/s with 4 threads); GPU memory held by docangle **286 MB**. In a full OCR job (≈ 1 s per page on the GPU) this saves ≈ 20 ms per page and, more importantly, halves the CPU the angle step uses; it matters when OCR is much faster than ~1 page/s per process (A100, batching). Default stays CPU.


## 20. What the OCR receives: quality of the straightened image (2026-10-13, v4.3.2)

**Question.** "Let our model find the angle and rotate the real original image and send that to the OCR. Why would we send the OCR a reduced-quality image?"

**What was already true.** The angle is found on a ≤ 1000 px grey copy, but `correct()` rotates the ORIGINAL decoded image (full resolution, original colour and bit depth). **One exception, PDFs:** `correct()` rotates the page as rendered at `pdf_long_side` = 1400 px (≈ 120 dpi for A4), which is enough for the angle but not an OCR-grade image. `PipelineConfig(pdf_long_side=2480)` (≈ 210 dpi for A4; the long side of A4 at 300 dpi is 3508) returns a 2480 × 1755 page; checked on 6 pages (0, 3.5, −7, 12, 90, 180°): the angle is the same to 0.01° at 1400 and 2480 (rendering takes longer; not timed; 3508 not checked). Documented in the README.

**What was wrong: the rotation itself.** Before 4.3.2 `upright()` used bilinear interpolation for everything, including exact quarter turns, and it also resampled flat pages, because the estimate of a flat page is often ±0.01° and any non-zero angle triggered a full warp. `bench/ocr_upright_quality.py sweep` (12 pages, Laplacian variance of the centre window relative to the original page; `reports/ocr_rotation/upright_sharpness_sweep.txt`): ONE pass keeps **52-60 % (bilinear), 73-77 % (bicubic), 77-81 % (Lanczos-4)** of the edge sharpness for any angle from 0.05° to 45°, and only 35 % / 57 % / 63 % at 0.01° (there the canvas grows by one pixel, which shifts the whole page by half a pixel; a pure (0.5, 0.5) px shift measured separately keeps 34 % bilinear / 56 % bicubic, the same numbers). An exact quarter turn with `np.rot90` keeps 100 % (same pixels). The old `upright(img, 180)` kept 34 %.

**Change (4.3.2, `docangle.upright`).** (1) the multiple-of-90° part of the correction is `np.rot90` (lossless, exact canvas size); (2) a remaining tilt under `min_tilt` = 0.1° (the resolution of the estimate) is not resampled at all; (3) a larger tilt is resampled once with bicubic (Lanczos-4 would keep ~5 points more but costs more and can ring; not adopted). `upright(img, a, interpolation=cv2.INTER_LINEAR, lossless_quarter_turns=False)` is the old behaviour. The angle, confidence and review flag are untouched (they are decided before the rotation). A first run of the experiment below (before rule 2) showed 2 of 12 pages whose estimate was ±0.01° being resampled in full (sharpness 29 % old / 51 % new): that is why rule 2 exists.

**Does the OCR care?** Same 12 pages and 9 angles as §19; the rotated inputs are made like a camera would (exact quarter turns, other angles with Lanczos-4), so the correction is the only resampling; docangle finds the angle (largest error 0.05°, mean 0.01°, over the 108 page-angle cases) and the page is straightened with the old and with the new rotation; the same engine reads both. Engines: PaddleOCR PP-OCRv6 medium (GPU) and Tesseract 5.5.3 `aze`; EasyOCR was not run. Raw rows `reports/ocr_rotation/quality_*.json`, tables `quality_tables.txt`.

| word F1 %, mean of 12 pages | untouched page | old rotation | new rotation | new − old, paired over pages (95 % page-bootstrap interval) |
|---|---|---|---|---|
| Paddle v6, all 9 angles | 99.3 | 99.1 | 99.1 | −0.00 [−0.11, +0.10] |
| Paddle v6, quarter turns 90/180/270 | | | | +0.16 [+0.01, +0.30] (6 pages better, 1 worse) |
| Paddle v6, tilts 5/15/30/45 | | | | −0.17 [−0.37, +0.03] (3 better, 8 worse) |
| Tesseract, all 9 angles | 96.4 | 97.2 | 97.0 | −0.23 [−0.48, −0.05] (1 better, 8 worse) |
| Tesseract, quarter turns 90/180/270 | | | | −0.46 [−1.13, −0.06] (0 better, 6 worse) |
| Tesseract, tilts 5/15/30/45 | | | | −0.20 [−0.43, −0.00] (3 better, 7 worse) |

Sharpness kept after the whole chain (camera rotation + correction, same for both engines): old **59 %** on average (34 % at 180°, 43-48 % for tilts, 88 % at 0/90/270° because of the ±0.01° pages), new **81 %** (100 % at 0/90/180/270°, 62-68 % for tilts). Mean CER, old / new: Paddle 2.0 / 2.0 %, Tesseract 12.1 / 12.2 % (reading-order sensitive; per angle the difference is at most 0.1 for Paddle and 0.4 for Tesseract, at 180°).

**Findings.** (1) **No measurable OCR gain from the sharper image.** Paddle reads both the same. Tesseract reads the new image slightly WORSE (−0.2 points, about one word in 400; the interval just excludes 0). At 180°, where the old rotation blurred most (34 % sharpness), Tesseract read it best (97.7 against 96.4 for the lossless turn). (2) Tesseract reads a rotated and resampled page better than the untouched one (old +0.81 [+0.10, +1.94], new +0.58 [+0.05, +1.48] points, 7 pages better and 1 worse): its input here is 150 dpi (x-height ≈ 10 px) and it prefers about 300 dpi, so on these pages the limit is resolution, not sharpness (untested guess: upscaling would help it more than keeping sharpness). Paddle loses 0.17 points against the untouched page with either rotation. (3) So the change is **kept as data hygiene, not as an accuracy gain**: quarter turns are now exact, flat pages are no longer resampled, tilted pages keep more detail for human review or other consumers, and the OCR results did not get meaningfully worse. If an OCR ever turns out to prefer the softer image, `lossless_quarter_turns=False, interpolation=cv2.INTER_LINEAR` brings the old behaviour back.

**Limits.** 12 clean born-digital pages at 150 dpi (the easy case for blur), simulated rotations, two engines, wide intervals (a few differences barely exclude 0 among many comparisons, so read them as "no effect of practical size"); no real photo or scan (JPEG artefacts, small print, low contrast may react differently); sharpness is a Laplacian-variance proxy. In `bench/ocr_rotation_eval.py` (§19) the "oracle", the Tesseract OSD turn and the textbook deskew still use the old bilinear `rotate_image_expanded`, on purpose (they reproduce §19); only "ours" (`correct()`) changed, by at most the amounts above. Reproduce: `python -m bench.ocr_upright_quality run --engine paddle_v6 --out ...`, `analyze quality_*.json`, `sweep`.

## 21. End to end on the GPU: PDF → angle → upright → PaddleOCR → text (2026-10-13, v4.3.3)

**What it is.** `tools/ocr_pipeline.py` (one command, one python environment with docangle + `paddleocr` + `paddlepaddle-gpu` + `onnxruntime-gpu`): for every page docangle finds the angle and the review flag and rotates the page upright (lossless quarter turns, §20), PaddleOCR PP-OCRv6 medium reads it, and the CPU side (render, angle, rotation) runs one page ahead of the GPU. Output: `pages.jsonl` (label, angle, confidence, needs_review, reasons, text lines, OCR score, ms per stage), `text.txt`, optionally the upright images. `--no-docangle` reads the page as it is (for comparison), `--skip-review`, `--long-side` (PDF render size), `--device cpu` / `--docangle-device cpu` for machines without a GPU.

**Check** (`bench/ocr_pipeline_eval.py`, `reports/ocr_pipeline_eval.txt`; RTX 3060 laptop GPU, docangle on CUDA, PaddleOCR on `gpu:0`, one process). 12 Azerbaijani pages (the §19 pages), each turned by a different angle like a scanner or camera would (exact quarter turns, other angles with Lanczos-4), written into ONE 150-dpi scanned PDF, rendered at 2480 px long side, read twice by the tool: OCR alone (the page as a viewer shows it) and with docangle in front. Word F1 against the text layer of the born-digital originals:

| page angle | 0° | 5° | 15° | 30° | 45° | 90° | 135° | 180° | 270° | −37° | 12° | 200° | mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OCR alone | 99.4 | 99.9 | 98.7 | 100.0 | 99.5 | 3.1 | 1.9 | 14.3 | 100.0 | 94.9 | 100.0 | 3.3 | **67.9** |
| + docangle | 99.4 | 99.9 | 99.6 | 100.0 | 98.2 | 100.0 | 98.7 | 99.6 | 100.0 | 94.6 | 100.0 | 100.0 | **99.2** |

**Findings.** (1) The angle step is what lets the OCR read the pages turned by 90, 135, 180 and 200° (2-14 % alone, 98.7-100 % with docangle); PaddleOCR reads 270° and tilts up to 45° by itself (as in §19), and on those pages docangle changes a score by at most 1.3 points in either direction (single pages, no intervals: same level). docangle's angle error: max 0.02°, mean 0.01°, no page was sent to review. (2) **Time:** the wall time of both runs equals the sum of the OCR times (14.9 s alone, 12.7 s with docangle for 12 pages; runs of the same job differ by ±15 % on this laptop, so do not read the difference), so the angle step, a median 226 ms of CPU-side time per page (55 ms is rendering alone), is completely hidden behind the GPU. (3) **The white border that straightening adds mattered:** a page turned 45° has twice the area after straightening (6.2 → 12.3 MP), the OCR time followed the area (correlation 0.92 over the 12 pages, +5-18 % for quarter turns and up to +70 % for big tilts), and in one run the 6 GB GPU **ran out of memory** (peak 4.9 GB, Paddle failed to allocate 1.5 GB more). The tool now cuts the white border before the OCR (`--no-crop` keeps it): peak GPU memory 3740 MB with docangle (3802 MB for the OCR alone), same mean word F1. Loading takes 2-4 s (docangle) and 9-13 s (PaddleOCR) once per process; docangle's three ONNX models cost only ≈ 0.3 GB. (4) The CPU mode works (one page checked) but Paddle on the CPU took 26 s for that page here: use the GPU, or another OCR on CPU-only machines (a Tesseract engine is not in this tool).

**Library fix found on the way.** onnxruntime-gpu 1.19 (like all versions before 1.21) finds the pip-installed CUDA libraries (`nvidia-cudnn-cu12`, ...) only through `LD_LIBRARY_PATH`; when it cannot, it runs the model **silently on the CPU**, so `ort_provider="cuda"` could be set while the CPU did the work. `make_session` now loads those libraries from `site-packages/nvidia/*/lib` by full path when the normal search path lacks them, and raises a clear error if the CUDA provider still cannot load. Checked in the Paddle GPU environment without `LD_LIBRARY_PATH`: sessions report `CUDAExecutionProvider`, and for 5 angles CPU and GPU give the same angle and confidence. `tests/unit/test_api.py::test_gpu_pipeline_matches_cpu_when_a_gpu_is_available` needs `onnxruntime-gpu` (skipped in the project's CPU venv; pytest is not installed in the GPU environment, so the same check was run as a script there).

**Limits.** A synthetic scan made from 12 clean born-digital pages (not a real scan), one angle per page and no intervals, 150-dpi rasters rendered up to 2480 px, one OCR engine, no page needed review (the review path was not exercised), the cropping rule (anything darker than 245 plus a 2 % margin) was only tried on white-background pages, laptop GPU shared with a desktop session. The numbers say the chain works and what it costs; they do not say how it behaves on real scans of the intended documents.

**Addendum (v4.4.0): Tesseract on the CPU.** `tools/ocr_pipeline.py --engine tesseract` (Tesseract 5.5.3 `aze`, page segmentation mode 3, one thread; `--tesseract-bin`, `--tessdata`, `--lang`) is the option for machines without a GPU; the same synthetic 12-page scanned PDF, docangle on the CPU (`reports/ocr_pipeline_eval_tesseract.txt`): mean word F1 **26.1 % (OCR alone) → 98.2 % (docangle in front)**, angle error ≤ 0.02°; Tesseract alone reads only the pages that are upright (97 %) or at 270° (100 %). Time: the whole job took 20.6 s for 12 pages (0.58 pages/s, OCR median 1.8 s per page, one Tesseract process; docangle's CPU side 109 ms per page, hidden behind it); alone 17.7 s. Pages could be read by several Tesseract processes at once on a many-core machine; not implemented.

## 22. Finding the document in photos with much background (opt-in `doc_crop`, v4.4.0, 2026-10-13)

**Problem** (§14): when a page lies on a desk and fills 10-25 % of the frame, the text is tiny and the background dominates; SmartDoc whole frames gave 42.9 % within 1° and 6.4 % flips. **Method** (`docangle/docrop.py`, `PipelineConfig(doc_crop=True)`, candidate `docangle_crop`): no model. Canny edges (20/60) of a 640 px copy are thickened (kernel 1 % of the long side) and joined, the connected region with the most edge pixels is the document; its box plus a 4 % margin is cropped (axis-aligned, so the angle of the crop is the angle of the image) when it covers 4-25 % of the image, otherwise the image is left alone. The parameters were chosen on the documents with an even `model_id` of SmartDoc (grid: kernel 0.6-2 %, three Canny pairs) and then checked on the odd ones (box IoU > 0.7 with the true page: 89.6 % tuning half, 87.7 % held-out, mean IoU 0.83; 2-3 ms per frame).

**SmartDoc whole frames, docangle against docangle + `doc_crop`** (§14 gave 8.9 % flips for the whole-frame baseline of v4.3; the current code, which since v4.3.1 takes the angle of too-few-lines pages from the classifier, gives 6.4 % on the same frames) (`bench/smartdoc_eval.py --docs ...`, `reports/smartdoc_eval_doccrop_*.txt`; the perfect-detector reference crops with the true corners + 8 %):

| frames | | median error | ≤ 1° | ≤ 5° | flips > 45° | review | accepted flips |
|---|---|---|---|---|---|---|---|
| all 926 | docangle | 1.37° | 42.9 % | 80.8 % | 6.4 % | 23.9 % | 1 |
| | **+ doc_crop** | **0.44°** | **73.1 %** | 90.1 % | **3.9 %** | **13.5 %** | **0** |
| held-out documents (465) | docangle | 1.31° | 44.3 % | 78.7 % | 5.4 % | 21.9 % | 0 |
| | **+ doc_crop** | 0.42° | **73.3 %** | 88.2 % | 3.9 % | 12.0 % | 0 |
| | perfect crop (reference) | 0.39° | 76.8 % | 91.4 % | 2.2 % | 5.8 % | 1 |
| tuning documents (461) | docangle → + doc_crop | 1.52° → 0.48° | 41.4 → 72.9 % | 82.9 → 92.0 % | 7.4 → 3.9 % | 25.8 → 15.0 % | 1 → 0 |

The cheap detector gets about 90 % of the possible gain in the ≤ 1° rate (29 of 32.5 points on the held-out documents) but less of the gain in flips and review (3.9 against 2.2 %, 12 against 5.8 %): where it misses the page, the pipeline is back at the whole-frame behaviour.

**Does it hurt normal pages?** A little, so it stays **opt-in** (default off). `bench.guard` on pages that fill the image (first run, 1500 cases: az, invoices, tobacco, CORD, FUNSD × scan / photo_easy / photo_hard, limit 0.60): flips 15 / 15, ≤ 1° 95.1 against 94.9 %, but 13 % of the angles moved by more than 0.05° and a change above 0.25° was worse in 43 cases and better in 4. Tightening the limit fixed most of it (second run, 400 photo cases, `reports/guard_doccrop.txt`): limit 0.60 / 0.35 / **0.25** → same angle within 0.05° on 87.5 / 95.2 / 97.0 %, worse / better 11 / 7 / **4** against 1, ≤ 1° 96.8 / 97.0 / 97.0 % (baseline 97.0 %), flips 2 in every column; the SmartDoc gains are the same for all three limits (73.0-73.2 % within 1°). The default limit is therefore 0.25 (`doc_crop_max_area`), candidates `docangle_crop` (0.25), `docangle_crop35`, `docangle_crop60`. Cost: about 2-5 ms per page when it is on.

**Limits.** One real data set (SmartDoc: 30 English documents, 5 backgrounds, low-resolution frames), parameters tuned on half of its documents; an edge-density cue will be fooled by busy backgrounds (many objects, patterned cloth), which SmartDoc has little of; pages that cover 25-60 % of the frame were not tested for a gain (the crop does nothing there with the default limit); the angle is still the angle of the page edges against the text lines for GT purposes (§14). Decide the default on photos of the intended documents: if they show the page small on a desk, switch it on.
