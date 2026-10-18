# 2. Design

## 2.1 Principles

1. **The quadrant is the risk; spend effort there.** A 1° error is invisible to OCR, a 180° error is total. The design has one learned, voted decision for the quadrant and one cheap, geometric estimate for the rest.
2. **Know when you are unsure, and say so.** Every result carries a confidence, the fused posterior of the chosen quadrant (not calibrated: a temperature of 0.5 would lower its log-loss, chapter 11), and a review flag derived from it by one threshold. Nothing in the rule is fitted to a particular data set except that threshold.
3. **Nothing is adopted without a paired benchmark.** Each change was run on the same simulated cases as the version before it and accepted only if accuracy did not drop beyond the intervals (chapter 11).
4. **Accuracy before speed, speed before elegance.** The default keeps every view that measurably helps; faster profiles exist as opt-ins (chapter 8).

## 2.2 Overview

```
 input (image file | PDF page | numpy array)
   │  decode: JPEG at reduced scale when large, PDF page rendered, 16-bit and float arrays scaled
   ▼
 working canvas: grey, long side ≤ 1000 px            ── blank page? → NO_CONTENT   too small? → IMAGE_TOO_SMALL
   │
   ├──────────────► Hough lines (thread) ── counts text lines only
   ▼
 ① FINE TILT, Fourier:  binarise a 512 px copy → Tukey window → 2-D DFT → radial projection of the
   magnitude spectrum → peak, folded modulo 90°                              → tilt ∈ [-45°, 45°)
   ▼
 ② straighten the canvas by −tilt (white expanded canvas); it is now axis-aligned, but still 0/90/180/270 off
   ▼
 ③ QUADRANT, two classifiers in parallel, each voting over rotated views of the page:
     PP-LCNet (Apache-2.0)   4 views (0°, 90°, 180°, 270°)  → log-posterior over the 4 quadrants
     own MobileNetV3         2 views (0°, 180°)             → log-posterior over the 4 quadrants
   sum of the two → posterior → quadrant = argmax
   ▼
 ④ fallback (rare): classifiers unsure → a 360° regressor may override the quadrant (penalty on confidence)
   ▼
 ⑤ angle = quadrant + tilt (normalised to [-180°, 180°])
    confidence = posterior of the chosen quadrant − 0.30 if the regressor overrode
    needs_review = confidence < 0.90   or   fewer than 8 text lines   or   blank / too small / unreadable
```

## 2.3 Input handling

* **Images** are decoded straight to grey. JPEGs with a long side of 2000 px or more are decoded at 1/2 to 1/8 scale as long as the result keeps at least 1000 px (the analysis never needs more), which saves about 10 ms on a 12 MP phone photo; EXIF orientation is applied by the decoder and the angle is relative to the EXIF-corrected image; `correct()` and `render_upright()` decode the original in colour (or grey, 8 or 16 bit as stored; an alpha channel is dropped) with the same EXIF handling, so the raster that is rotated is the one that was analysed. `reduced_jpeg_decode=False` turns the shortcut off.
* **PDF pages** are rendered with PDFium (`pypdfium2`) as a viewer would show them: the page's `/Rotate` flag is applied. PDFium is not thread-safe, so every call is serialised by one lock. An opt-in fast path (`pdf_fast_path`) takes the single JPEG of a scanned page directly instead of rendering it: a synthetic 100-page JPEG-scan PDF goes from 6.9 s to 2.7 s, with guards that fall back to rendering for anything unusual (chapter 8).
* **Arrays**: 8-bit, 16-bit and float images, grey, colour or with alpha, are converted to 8-bit grey.
* **Gates**: an image whose short side is under 64 px is `IMAGE_TOO_SMALL`; a canvas with a grey-level standard deviation below 2 is `NO_CONTENT`. Both return `angle=None` and `needs_review=True`.

## 2.4 The fine tilt (Fourier, stage ①)

Text lines are rows of periodic structure; in the 2-D Fourier magnitude of the page they produce a bright ridge perpendicular to the lines. The estimate follows the radial-projection method of jdeskew (Pham et al., ICIP 2022) and is our own port (`docangle/fftskew.py`):

1. take the 1000 px canvas to a 512 px copy and binarise it by an adaptive Gaussian threshold (block 11, offset −10);
2. multiply by a 2-D Tukey window over the real image extent (page borders and desk edges would otherwise draw a bright cross into the spectrum and the estimate collapses on photographs);
3. zero-pad to 512 × 512 and take the DFT; take the magnitude and shift the zero frequency to the centre;
4. resample the magnitude onto 1800 directions (0.1° steps over 180°) and sum along each direction, once over all radii and once without the low-frequency core (the innermost 20 %);
5. add the profile at θ and θ + 90° (text lines, table rules and vertical strokes all vote for the same page axis), take the peak with a parabolic sub-bin refinement, and fold the result into [-45°, 45°);
6. use the core-free profile when it agrees with the full one to within 0.5°, as the paper does.

The method is training-free and takes about 5 ms. It replaced a two-pass Hough estimate in v4.2; the old estimator is still available as `PipelineConfig(fine_estimator="hough")`. A Hough pass still runs in a parallel thread, but only to count text lines for the `TOO_FEW_LINES` gate.

## 2.5 Straightening (stage ②)

The working canvas is rotated by minus the tilt onto an expanded white canvas (bilinear; this copy is only for the classifiers). The page is now axis-aligned and the only unknown left is a multiple of 90°.

## 2.6 The quadrant (stage ③)

Two classifiers look at the straightened page.

**PP-LCNet** (`PP-LCNet_x1_0_doc_ori` from PaddleOCR, ONNX, 6.8 MB): the page is resized to a short side of 256 px and centre-cropped to 224 × 224, grey replicated into three channels.

**Our classifier** (`orient_cls_v4`, MobileNetV3-Large fine-tuned on audited data, ONNX, 17 MB): the page is squashed to 320 × 320 grey.

Both return a distribution over the four *clockwise* classes c ∈ {0, 1, 2, 3} (the page is turned clockwise by 90°·c). **Rotation voting**: if a page has class c, then the same page rotated counter-clockwise by r·90° looks like class (c − r) mod 4. So every rotated view is an independent vote for c, and the page-level log-posterior is the mean of the per-view log-probabilities,

    LP(c) = (1/n) · Σ_i log p_i( (c − r_i) mod 4 )

with r = (0, 1, 2, 3) for PP-LCNet and r = (0, 2) for the own classifier. The two log-posteriors are added (weights 1 and 1), renormalised, and the quadrant is the argmax; the **posterior** of that quadrant is the quantity called the score below. The own classifier's temperature and the voter weights were fitted once, in-sample (3 parameters, `reports/calibrate_e2.txt`): the log-loss improved (0.0170 to 0.0129) but the number of quadrant errors stayed at 25 (chapter 11), so both stay at 1.

Why two models? PP-LCNet alone makes about nine times more quadrant errors than the pair (445 against 51 flips) on our simulated pages (chapter 6, ablation), and our classifier alone has more accepted flips at equal review rate (+7, interval +1..+15). They fail on different pages; the sum fixes most of both.

## 2.7 The fallback (stage ④)

When the score is below 0.60, or the tilt is near ±45° (|tilt| > 25°, where the quadrant boundary lies) and the score is below 0.88, a global regressor (MobileNetV3-Large producing [sin θ, cos θ] of the full 360° angle) is asked about the whole page. If its angle differs from the chosen one by more than 45° it overrides (`reasons` gets `REGRESSOR_OVERRIDE`) and the confidence is lowered by 0.30. In the v4.4 benchmark the fallback flag (set when the regressor overrides the quadrant, or on a `TOO_FEW_LINES` page) was set in 63 of 6300 cases (1.0 %: 14 of 3600 on the primary pools, 49 of 2700 on the external pools; `fallback_triggers` in `reports/bench_final_v4_4.json`); how often the regressor was asked and agreed was not counted. The ablation found it **neutral** for *accepted* flips (every page where it acts is reviewed anyway). Without it the displayed angle is actually better on the simulated pools (51 to 25 flips) and on DISE, but worse on whole SmartDoc frames (59 to 85); it was kept for that reason and because removing it would not save time (chapter 11).

## 2.8 Confidence and review (stage ⑤)

    confidence = posterior(quadrant) − 0.30 · [regressor overrode]
    needs_review = confidence < 0.90   or   text lines < 8   or   blank / too small / unreadable

There is no learned calibrator and no line-count term. An earlier formula, `0.55·posterior + 0.45·min(1, lines/80)`, was found to be structurally wrong: on a page with 80 or more lines the second term alone lifts any posterior above the review threshold, so dense pages, exactly where confident quadrant mistakes live, could never be reviewed (chapter 11). `quality` is `HIGH_CONFIDENCE` at ≥ 0.97, `MEDIUM_CONFIDENCE` between the review threshold and that, `NEEDS_HUMAN_REVIEW` below, and `UNDETERMINED` when there is no angle. Pages with fewer than 8 Hough lines (cover pages, a single heading, logos) get the classifier's quadrant, confidence 0.40 and the reason `TOO_FEW_LINES`; they are always reviewed.

## 2.9 Optional parts

* **Multi-page consensus** (`predict_job`, `predict_pdf`, CLI `--consensus`): pages of one scan job usually share their orientation. A leave-one-out Bayesian combination of the other pages' posteriors lets an unsure page follow a strong consensus (`JOB_CONSENSUS`) and sends a confident page that contradicts a nearly unanimous job to review (`JOB_DISAGREE`). It never shares the fine tilt, and it does nothing for fewer than 3 pages that have a posterior (blank, `TOO_FEW_LINES` and unreadable pages do not count). Not meant for unrelated photos (not measured on them).
* **Document finder** (`doc_crop=True`): for photos where the page lies small on a desk, a model-free detector (Canny edges of a 640 px copy, thickened and joined; the region with most edge pixels) crops the analysis to the page. It takes 2-5 ms; the angle is the angle of the whole image. Off by default because it changes a few angles of pages that fill the image (chapter 6).
* **GPU** (`ort_provider="cuda"`): the three ONNX models run on the GPU through onnxruntime-gpu; results are identical to the CPU's and a page takes half the time and half the CPU. The pip-installed CUDA libraries are found without `LD_LIBRARY_PATH`, and a GPU request that cannot be honoured is an error, not a silent CPU run.
* **Lean batch mode** (`ort_spinning=False`, set automatically by the CLI for batches): idle ONNX threads sleep instead of spinning; results are identical and about a third less CPU per page.

## 2.10 Producing the straightened image

`correct()` rotates the **original** decoded image, not the 1000 px canvas used for the analysis, with as little resampling as possible: the multiple-of-90° part is a lossless `np.rot90`; a remaining tilt under 0.1° (the resolution of the estimate) is not resampled at all; a larger tilt is resampled once with bicubic interpolation onto an expanded white canvas. (An earlier bilinear rotation kept about half of the edge sharpness of the page and re-sampled flat pages whose estimate was ±0.01°; chapter 7.2 measured two OCR engines on the old and the new image: PaddleOCR read them equally well, Tesseract very slightly worse with the new one (−0.23 word-F1 points, interval [−0.48, −0.05]); EasyOCR was not run in that study. So this is data hygiene, not an accuracy gain.) For PDFs the page is rendered at `pdf_long_side` (default 1400 px, about 120 dpi for A4, enough for the angle but not an OCR-grade image; 3508 px is 300 dpi).

## 2.11 Threading and determinism

A pipeline object is thread-safe: ONNX sessions are created lazily under a lock, PP-LCNet and the own classifier run on separate threads (ONNX Runtime releases the GIL), the Hough line count runs on a third, and PDFium calls are serialised. The analysis is deterministic for a given input, model files and ONNX Runtime version (a different number of ONNX threads can change the last bits of a logit; the default of two threads per model is the setting used for every measurement in this book).

## 2.12 What the design does not do

It does not look at the text itself (no OCR in the loop), does not model curved pages, does not fit a calibrator to your data, and does not claim anything about scripts it was not trained on. Its blind spots are listed in [chapter 10](10-limitations.md).
