# 9. Using docangle

## 9.1 Install

```bash
git clone <repository-url> docangle && cd docangle
pip install -e .             # numpy, opencv-python-headless, onnxruntime
pip install -e ".[pdf]"      # + pypdfium2 for PDF input
pip install -e ".[dev]"      # + pytest, ruff
```

Python 3.10 or newer, CPU only (a GPU path exists, [section 9.6](#96-gpu)). Install from the repository: the models are read from `models/` (checksums and provenance in `models/manifest.json`; see [`models/README.md`](../models/README.md) for how to obtain them if your copy does not contain the weights); set `DOCANGLE_MODELS_DIR` to use another folder. A missing model is an error (`ModelNotFoundError`), never a silent guess. The 360° regressor is optional: it is needed only while `use_regressor_fallback` is on (the default), or with `too_few_lines_angle="regressor"` or `fine_estimator="hough"`; with `PipelineConfig(use_regressor_fallback=False)` the pipeline runs without it (its effect is chapter 6.5). The own classifier can be switched off knowingly with `orient_weight=0` (far less accurate, chapter 6.5).

## 9.2 Python

```python
from docangle import get_pipeline

pipe = get_pipeline()                       # created once, thread-safe, models load on first use
r = pipe.predict("page.jpg")                # a path, a numpy array (any dtype, grey / BGR / BGRA) or a PDF
print(r.angle, r.confidence, r.needs_review, r.reasons)

upright, r = pipe.correct("page.jpg")       # the original image rotated upright; None if the page is undetermined
```

| call | what it does |
|---|---|
| `predict(image, page=0)` | angle, confidence, review flag, reasons; for PDFs `page` is 0-based |
| `predict_angle(image, page=0)` | the angle only; raises `UndeterminedOrientation` for blank or too small pages |
| `correct(image, expand=True, page=0)` | `(upright image, result)`; for PDFs the page is rendered at `pdf_long_side` (see 9.5) |
| `predict_batch(images, max_workers=4)` | paths or arrays (no `page`), results in input order; an unreadable input becomes `UNREADABLE`, never aborts the batch |
| `predict_job(items, max_workers=4, consensus=True, eps=0.05)` / `predict_pdf(path, consensus=True, eps=0.05, max_workers=4)` | pages of one scan job together (`items` are paths, arrays or `(pdf_path, page)` pairs), with multi-page consensus (9.7) |
| `apply_job_consensus(results, config=None, eps=0.05, min_pages=3)` | the consensus step alone, on results you already hold |
| `correct_image(image, expand=True)` | compatibility helper: `(upright image, angle)`; raises if the page is undetermined |
| `render_upright(image, angle, expand=True, page=0)` | loads the image as `correct` does and rotates it by `-angle`: for results that were adjusted afterwards (consensus) |
| `upright(img, angle, min_tilt=0.1)` | the rotation used by `correct`, usable on any image you hold |

Angles are counter-clockwise positive in [-180, 180]; to straighten a page rotate it by `-angle` (that is what `upright` does). `angle is None` means undetermined (blank, too small, unreadable) and always comes with `needs_review=True`.

**Reason codes** (`Result.reasons`; a plain low confidence has no code, `needs_review` is simply True):

| code | when | effect |
|---|---|---|
| `IMAGE_TOO_SMALL` | the short side is under 64 px | `angle=None`, review |
| `NO_CONTENT` | the grey-level standard deviation of the analysis canvas is below 2 (blank page) | `angle=None`, review |
| `UNREADABLE` | the input could not be read (batch, job and command line) | `angle=None`, review |
| `TOO_FEW_LINES` | fewer than 8 Hough lines: a page without text | confidence 0.40, always reviewed; the angle is the classifier's (`too_few_lines_angle`; with `fine_estimator="hough"` it is the regressor's) |
| `LOW_LCNET_SCORE` | the fused posterior of the quadrant (both classifiers together, not PP-LCNet alone) is below 0.60 | no penalty of its own; the page is reviewed because the confidence is below 0.60 |
| `REGRESSOR_OVERRIDE` | the 360° regressor was asked, differed by more than 45° and overrode the quadrant | confidence −0.30 |
| `AMBIGUOUS_QUADRANT` | only with `ambiguity_flag=True` and the regressor off: the fallback trigger fired, the page is only flagged | confidence −0.30 |
| `LARGE_RESIDUAL` | the second-pass Hough residual is above 3° (that pass runs rarely in the default mode) | confidence −0.15 |
| `LARGE_FINE_DISAGREEMENT` | only with `fft_alarm_deg > 0` (default 0, off) and the Fourier estimator: Hough and Fourier tilt differ by more than that | confidence −0.15 |
| `JOB_CONSENSUS` | multi-page consensus changed the quadrant of a page whose own posterior did not outweigh the other pages | angle changed |
| `JOB_DISAGREE` | a confident page contradicts a nearly unanimous job | kept, reviewed |

## 9.3 Command line

```bash
python -m docangle page.jpg                         # one line per page: file, angle, confidence, quality, reasons
python -m docangle scans/ --json                    # JSON lines for a folder (images; PDFs only page 0 unless --page all); --threads defaults to min(4, CPUs)
python -m docangle page.jpg -o upright.jpg          # also write the straightened image
python -m docangle job.pdf --page all --json        # every PDF page (0-based number or 'all')
python -m docangle job.pdf --page all --consensus   # pages of one PDF are one job (see 9.7)
python -m docangle job.pdf --pdf-fast               # JPEG fast path for scanned PDFs (opt-in, see chapter 8)
```

With `-o`, one page writes the file you name; several pages (a folder, `--page all`) write into a directory of that name, which is created: images keep their file names and a PDF page becomes `<stem>_p<N>.png`. Output is streamed in input order. For batches the CLI switches to lean CPU settings automatically (`--no-lean` turns that off).

## 9.4 The review workflow

docangle's contract is: *trust `needs_review == False`, look at the rest.* A practical set-up:

1. Run the pipeline over the incoming pages.
2. Pages with `needs_review == False` go straight on. In the simulated benchmark these contain 0 real flips in 3600 cases on the main pools and 6 in 2700 on the external pools (chapter 6).
3. Pages with `needs_review == True` (0.7 % of simulated clean scans of the primary pools, 1.1 % over scan and both photo levels; 7.6 % of simulated receipt photographs, mean over three levels) go to a person with the suggested angle pre-applied; `reasons` says why.
4. Tune `PipelineConfig(review_confidence=...)`: 0.90 is the default; 0.95 doubles the review rate and removes most remaining accepted flips on out-of-domain material.
5. **Measure on your own pages before trusting any of this.** Without labels: `python -m tools.first_look photos/ --out out/` compares candidates, turns every photo by three known angles to check that the answer moves by exactly that, and writes numbered contact sheets of the straightened results, so a person can list the pages that are not upright in seconds. With labels (drag along one text line per photo in a browser): `python tools/label_server.py photos/ --out labels.jsonl`, then `python -m bench.eval_labeled photos/ labels.jsonl`. Keep half of the labelled pages untouched; never tune on the photos you report.

## 9.5 PDFs and the straightened image

A PDF page is rendered as a viewer shows it (`/Rotate` applied). `predict` renders at `pdf_long_side` = 1400 px, which is plenty for the angle. `correct()` returns **that** raster rotated upright, which is about 120 dpi for A4 and not an OCR-grade image. For OCR input either raise `PipelineConfig(pdf_long_side=2480)` (about 210 dpi; the angle is unchanged to 0.01° on 6 pages) or `3508` (300 dpi), or take the angle and render the page yourself with the resolution your OCR likes and rotate it with `docangle.upright`. For image files `correct()` rotates the original full-resolution decode.

## 9.6 GPU

```python
from docangle import PipelineConfig, get_pipeline
pipe = get_pipeline(PipelineConfig(ort_provider="cuda"))      # needs onnxruntime-gpu and CUDA 12 / cuDNN 9
```

Identical results, about twice as fast per page and half the CPU (chapter 8). If the CUDA libraries cannot be loaded you get a `ModelNotFoundError` with instructions, not a silent CPU run.

## 9.7 Options worth knowing

| option | what for | where measured |
|---|---|---|
| `review_confidence` (0.90) | stricter or looser review | chapter 6.2 |
| `doc_crop=True` | photos where the page lies small on a desk | chapter 6.4 |
| `predict_pdf(path)` / CLI `--consensus` | the pages of one scan job share their orientation: unsure pages follow the others, a confident outlier is reviewed. It needs at least 3 pages that have a quadrant posterior (blank, `TOO_FEW_LINES` and unreadable pages do not count); with fewer the results are returned unchanged. `eps` (0.05) is the assumed chance that one page's vote is wrong | chapter 6.6 |
| `pdf_fast_path=True` / `--pdf-fast` | faster scanned PDFs | chapter 8.3 |
| `ort_provider="cuda"` | GPU | chapter 8.4 |
| `orient_rots=(0,)`, `lcnet_rots=(0, 2)` | faster profiles | chapter 8.5 |
| `fine_estimator="hough"` | the v4.1 fine tilt | chapter 6.3 |

The complete list is [appendix A](appendix-a-config.md).

## 9.8 Putting an OCR behind it

```bash
python -m tools.ocr_pipeline scan.pdf --page all --out out/           # PaddleOCR on the GPU
python -m tools.ocr_pipeline scan.pdf --engine tesseract --docangle-device cpu      # Tesseract, no GPU
```

Chapter 7 describes what it does and what it gained on the test pages. To use your own OCR, take `r = pipe.predict(path)` and `img = docangle.upright(your_full_resolution_image, r.angle)`, and read `img`; skip or queue the page when `r.needs_review`.

## 9.9 Troubleshooting

| symptom | cause and remedy |
|---|---|
| `ModelNotFoundError` | the weights are not in `models/`; see `models/README.md` or set `DOCANGLE_MODELS_DIR` |
| `ImageReadError` on a PDF | PDFium could not open or render the page; the batch calls return `UNREADABLE` for that page and continue |
| angle is off by exactly 90° or 180° on a page | the page is probably in the review queue; check `needs_review` and `reasons` |
| the angle differs slightly between `predict` and `correct` | decoding differs (grey decode against colour decode and conversion); borderline pages are not bit-stable across decode paths. Both apply the EXIF orientation, so a difference of 90° or more is a bug: please report it |
| 6 GB GPU out of memory with an OCR | the straightened canvas of a 45° page doubles in area; crop the white border before the OCR (`tools/ocr_pipeline.py` does) |
