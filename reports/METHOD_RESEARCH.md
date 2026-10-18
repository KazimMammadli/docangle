# New-method research (2026-10-10): what was found, what to test, in which order

*Working notes of 2026-10-10 to 2026-10-13; a few statements were corrected later. Where they give a number for another tool, the controlled measurement in [docs/05-comparison.md](../docs/05-comparison.md) supersedes it; what was implemented or rejected is in [docs/11-decisions.md](../docs/11-decisions.md).*

Status: **survey done, nothing implemented yet.** Five research agents surveyed open-source models, papers, classical cues, skew
estimators and reliability tricks (the raw data, 50 items with licences, speed, and how to test
them here, are not part of the public repository). The design / adversarial-critique / synthesis stage of the workflow did not run (session usage limit), so **the ranking
below is mine, made from the survey numbers.** The real adversarial check is our own benchmark: nothing here is adopted until
`bench.equiv` / `bench.guard` say so.

**How far to trust the numbers below.** They were measured by the research agents on small samples (360–720 simulated photos,
one seed; DISE 600 pages), with scratch code that monkey-patches the pipeline (`research/agent_scratch/`, unreviewed). The agents
did not agree with each other on one point (windowing, see E1). Treat every figure as a hypothesis to reproduce, not a result.

## Ranked experiments

### E1. Fourier radial-projection fine angle instead of Hough pass 1 (best evidence, also faster) — **DONE, adopted in v4.2.0 (FINAL_REPORT §10)**
Idea (jdeskew / ICIP 2022): threshold the page, 2-D DFT magnitude, sum along radial lines, take the best angle, fold mod 90.
Training-free, 256–512 px, about 3–5 ms, errors independent of Hough (it fails on photos only through the page border and the desk).

Agent measurements (`research/agent_scratch/exp3.py`, pipeline with pass 1 = FFT, pass 2 skipped, Hough kept only for line count):

| set | metric | current | FFT pass 1 |
|---|---|---|---|
| DISE-2021, 600 pages | ≤ 1° | 89.3 % | 94.3 % |
| | errors > 5° | 51 | 34 (all quadrant flips; no fine-angle blunders left) |
| simulated photo_hard, 360 cases | ≤ 1° | 87.5 % | 96.1 % |
| | errors > 5° | 22 | 5 |
| CORD receipts photo_hard | ≤ 1° | 53 % | 88 % |

Why it matters here: the Hough blunders on DISE were dense pages with 97–1845 lines, which is the "dense number tables, confident
fine-angle error" weak spot of our final report, and our confidence term `min(1, lines/80)` is maximal exactly there.

Cautions (do not skip):
* **Windowing is essential.** One agent got 71.6 % ≤ 1° (no window) / ~94 % (Hann) on raw simulated photos, the other 86 % (no
  window) / 97.8 % (Tukey). Border and desk edges leak a cross into the spectrum. Test window and crop explicitly.
* **The agent's latency claim (−18…−20 ms) is wrong for this machine.** It assumed Hough pass 1 = 24 ms (measured under load); we
  measured 11.1 ms. Realistic: Hough 1 (11) → FFT (≈4): about **−5…−8 ms wall-clock**, plus about 10 ms less CPU (pass 2 disappears),
  which helps batch throughput. If Hough stays in a parallel thread for the line count, latency = FFT + max(classifiers, Hough).
* Replacing pass 2 with FFT was worse on photos (21 errors > 5°): drop pass 2, do not replace it.
* Receipts: slanted paper edges can pull the folded estimate by 4–5°. A "family-split" arbiter exists (`famskew.py`) but is a
  hypothesis from 4 hand-inspected receipts; needs asymmetric-perspective simulation or real photos.
* The review policy was tuned with the Hough line count; re-tune. Keep `NO_CONTENT` / min-lines gates (FFT always returns a number).

Test plan: registry candidates `docangle_fft` (pass 1 FFT, no pass 2, Hough thread for lines) and `docangle_fft_alarm` (plus a
`LARGE_FINE_DISAGREEMENT` reason when |Hough − FFT| mod 90 > 3°, confidence −0.15). `bench.guard` on the 4 primary pools × 3 levels ×
2 angle modes, then CORD / DocLayNet / FUNSD, then DISE 600. Accept if: ≤ 1° up beyond noise, errors > 5° not higher, flips not
higher, review rate not materially higher, paired better/worse counts not worse. Page-level (cluster) CIs for the final claim.

### E2. Disagreement alarm and calibrated review (0 ms at inference; offline replay) — **DONE, v4.3.0 (FINAL_REPORT §11)**
After E1, because it needs its features. Per-case dumps → (1) temperature/weight per voter on page-disjoint data, (2) tiny logistic
"quadrant wrong" predictor on ≈ 8 features (max posterior, margin, voter agreement, lines, residual, Hough-vs-FFT gap, fallback flag),
(3) review threshold from a risk-coverage curve with a Clopper-Pearson / Learn-then-Test bound, **page-grouped** (flips sit on 5–7
source pages, case-level CV leaks). Report risk–coverage per pool and per external domain, compare at equal review rate. Calibration
cannot fix confident errors: expect a gain on review cost, not on flips.

### E3. Independent quadrant evidence (cheap cues first, training only if needed)
a. **Ascender/descender and mark-above/below cues as a veto to review, not as a voter** (own cv2 code; Leptonica's `pixUpDownDetect`
   idea). Agent measurement on DISE 600: never confidently disagreed with a correct page; at diff ≤ −4 it flagged 3.6 % extra
   review and caught 9 of 18 180° flips (7 of the 12 that had been accepted); at ≤ −16, 0 false reviews, 2 of 18 caught. Weaknesses: blind at the 1000-px canvas for A4 (needs ≈ 150 ppi,
   x-height ≥ 10 px, so use a half-scale ROI crop, only on low-margin or disagreement pages), fails on number tables / all caps /
   receipts / covers (abstains), no signal for the 19 sideways errors (Chinese vertical text). Only ~5 source documents behind the DISE flips.
b. **(measured, REJECTED — FINAL_REPORT §12)** **docTR `mobilenet_v3_small_page_orientation`** as a third voter (Apache-2.0, 6 MB fp32 / 1.7 MB int8, ONNX, letterboxed 512²).
   Never measured by anyone. **Needs approval to download** (OnnxTR v0.6.0 release asset). First measure it alone against
   PP-LCNet and v4 on the same cases and check that errors are not correlated.
c. **Native-resolution glyph/patch voter** (Rashid et al.: per-connected-component 4-way CNN, page = vote over hundreds of CCs;
   or 12–16 text patches of 96² from the canvas). Labels are free (rotate audited upright pages). ~50–100k parameters, +3–10 ms.
   Highest ceiling and the most work (data + training on the RTX 3060, ≤ 1–2 GB dataset, memory rules). Only if a/b leave the flips.
   Its low vote count / margin doubles as a "no Latin text here" review trigger.

### E4. Training data aimed at the known failures
Synthetic binarised / dithered / typewriter scans (Kanungo noise, halftone), synthetic covers and big-lettering pages, hard-page
mining; then a v5 classifier (≈ 40 min GPU, recipe in README). Targets DISE-type failures. DISE is out of domain, so first decide
whether the intended documents contain such pages at all.

### E5. Job-level (multi-page) consensus, opt-in — **DONE as optional feature (FINAL_REPORT §13)**
Pages of one PDF / folder usually share their orientation; leave-one-out vote over the 4-class posteriors, low-confidence pages adopt a
strong consensus (`JOB_CONSENSUS`), confident disagreeing pages go to review (`JOB_DISAGREE`), never share the fine angle for
photos. ~0.1 ms/page. Probably the most useful thing for real multi-page PDFs, but it is not a per-page accuracy
gain and must be judged separately (data: `az_test_pages`, 5 real documents; mixed jobs must be simulated).

## Looked at and not worth it
Seeing Straight (304 M params, GPU), Tesseract OSD (hundreds of ms), PP-OCR / RD-POD recognition-driven orientation (15–40 ms+,
useful only as an offline label-audit oracle), Kiril2206 EfficientNet API (claims unverified), rotdet (tiny, unmeasured), KNN+Fourier,
FHT / gradient-histogram skew (no better than the Fourier method already measured), text-line 0/180 PP-LCNet voter on classically
found lines (measured alone: 18/72 invoice and 24/78 CORD page-level errors; errors fairly uncorrelated with the ensemble, fused gain
not established, keep as a fallback idea).

## Order of work
E1 → E2 (uses E1's features) → E3a → E3b (after approval to download) → E3c / E4 only if flips remain → E5 as a separate small feature.
One change per commit, one heavy job at a time under memory caps, baseline dump before every edit.

## Update 2026-10-13: redundancy analysis
See FINAL_REPORT §15 (ablation of PP-LCNet, regressor, views, Hough gate).

## Update 2026-10-16: second search for open-source projects that do what docangle does

Question: is there an open-source project on the internet that already does this (page orientation + skew angle + review flag)? Web searches (orientation / skew / rotation + OCR preprocessing, GitHub, PyPI, Hugging Face, arXiv) plus a look at each README or model card. **Nothing found does the whole job**; the closest ones each cover part of it. Claims below are the projects' own unless a measurement is named.

| project | what it does | licence | their claim | our measurement / status |
|---|---|---|---|---|
| PaddleOCR `PP-LCNet_x1_0_doc_ori` | 4 orientations, no fine angle | Apache-2.0 | 99.06 % | **already used** as a voter in docangle |
| PaddleOCR doc preprocessor, PP-DocLayoutV3 / PaddleOCR-VL 1.5 | orientation + unwarping; layout for skewed / curved pages | Apache-2.0 | strong on skew / curve | built-in modules damage tilted pages (§19: 56 % at 30°); PP-DocLayoutV3 as a voter 37-80 % right (§8) |
| DocOrient 0.4.1 (PyPI `docorient`) | 4 orientations (energy axis + MobileNetV2), ≈ 20 ms CPU | MIT | 98 % | arbitrary angles: 7-48 % wrong quadrant (§8); **exact quarter turns: 96.0 % on Azerbaijani pages, 59.5 % on RVL invoices, against 100 % and 86.0 % for docangle** (`bench/docorient_quarter.py`, `reports/docorient_quarter_turns.txt`) |
| docTR page orientation (+ `Filiphw/doctr-page-orientation` fine-tune) | 4 orientations | Apache-2.0 | published 64 % | measured and rejected (§12) |
| jdeskew (ICIP 2022), `ocrd_jdeskew` | fine skew only | MIT | beats other estimators on DISE-2021 | **ported** as docangle's fine tilt (§10) |
| `deskew` (sbrunner), `hough` (PyPI) | fine skew only, classical (Hough / Radon) | MIT | | the Hough part is our baseline; textbook `minAreaRect` 12 % within 1° on SmartDoc (§19) |
| neural-deskew (dito97) | MLP on top of three classical skew estimators | MIT | none yet, no weights | not usable as is; idea (learned stacking) listed in the survey |
| Tesseract OSD, OCRmyPDF `--rotate-pages` | 4 orientations from OSD + deskew | Apache-2.0 / MPL-2.0 | | with OSD the word F1 is 73.9 % at 180° and 66.3 % at 270° (§19) |
| Seeing Straight (arXiv 2511.04161, Krutrim) | 4 orientations, Phi-3.5-Vision encoder | paper CC-BY | 96 / 92 % on its benchmark | no code or weights found; ≈ 300 M parameters; not usable |
| olmOCR (Allen AI) | a 7 B VLM that also outputs `rotation_correction` (0/90/180/270) | Apache-2.0 | | GPU-heavy, quadrant only, no fine angle; not measured |
| rotdet v2 (fcrescio) | 4 orientations, 1.56 MB C4-equivariant CNN, 29-49 ms CPU | **GPL-3.0** | 90 % on 164 LLM-labelled pages | GPL-3.0 (copyleft); its own accuracy figure is below ours |
| DuarteBarbosa/deep-image-orientation-detection (Hugging Face) | 4 orientations, EfficientNetV2, ONNX | MIT | 98.82 % validation on COCO / TextOCR photos | **new, never measured here**; trained mostly on photos, document accuracy unknown |
| Chuckame/deep-image-orientation-angle-detection (Hugging Face) | continuous angle, ViT-base 224, ONNX | MIT | none given | photo-oriented, no metrics; not measured |
| arXiv 2603.25351 (circular-aware rotation regression) | 360° angle of natural images | paper | 3.7° MAE on COCO | not for documents |
| Surya 2, Docling, MinerU | layout / OCR toolkits | various | | no dedicated orientation model found in their documentation |

**Conclusion.** The open-source landscape is: 4-class orientation classifiers (PP-LCNet, DocOrient, docTR, rotdet, generic photo models) and separate skew estimators (jdeskew, deskew, hough). None combines the quadrant, the fine angle and a calibrated `needs_review` flag, none reports Azerbaijani documents or PDF input, and on exact quarter turns the best other tool measured in the book's chapter 5 (PP-LCNet, which docangle itself uses as a voter) is wrong in 1.0 % of 700 cases against 0.0 %, and the other tools are far behind on tilted pages. docangle's contribution is exactly that combination and its evaluation. Only one untested candidate seems worth a measurement: the EfficientNetV2 model of DuarteBarbosa (MIT, ONNX), as an extra voter or a baseline on our pools; it needs approval to download.
