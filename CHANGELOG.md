# Changelog

Format after Keep a Changelog; versions are the package versions. Every entry that changes results names the evidence (`reports/FINAL_REPORT.md` section numbers, §N, or chapters of `docs/`).

## [4.5.0] - unreleased
- `pip install docangle`: the three pipeline models (36.0 MB) are no longer needed in the install. On first use they are downloaded from the GitHub Release `v4.4.0`, checked against a built-in SHA-256 and kept in `~/.cache/docangle/` (`$XDG_CACHE_HOME/docangle/`); a message on stderr names the files, the source and the research-use terms of the own weights (`models/README.md`). Order of lookup: `DOCANGLE_MODELS_DIR` (only that folder, never a download), the repository's `models/`, the cache, the download. Offline or a wrong checksum is a `ModelNotFoundError` that names the URL and the folder to put the file in. Results are unchanged: the files are the same ones.
- Publishing to PyPI through GitHub Actions with Trusted Publishing (`.github/workflows/publish.yml`).

## [4.4.0] - 2026-10-18 (first public release)
First what was added while preparing the public release, then what the internal 4.4.0 build of 2026-10-13 added.

- Fixed: `correct()` and `render_upright()` decoded the file without applying the EXIF orientation tag while `predict()` applied it, so the angle of a rotated phone JPEG described a different image than the one that was turned (90° off, also on the command line with `-o`). Both now read the same raster.
- The 360° regressor file is optional when the configuration does not ask for it (`use_regressor_fallback=False`, `too_few_lines_angle` not `"regressor"`, `fine_estimator` not `"hough"`); a needed file that is missing is still an error with a message that says so.
- A missing own classifier is an error (`ModelNotFoundError`); the pipeline no longer falls back to the first-generation model.
- Clear messages instead of a crash for an empty benchmark pool (`bench/datasets.py`); `python -m src.orient_data` has a command line; `tools/first_look` no longer asks for the predecessor pipeline by default; `bench/profile_stages.py` no longer needs a particular private page.
- New measurements and tools: `bench/page_interval.py` (page-level interval of the flip rate: 0.58 % [0.14, 1.23], `reports/page_interval_v4_4.txt`), `tools/check_links.py`, `bench/latency_files.py` (latency of a call on an image file), `bench/smartdoc_page_size.py`, `reports/profile_stages_v4_4.txt`, `reports/skew_check_v4_4.txt`, `reports/int8_quantization.txt`.
- Documentation: reason-code table (chapter 9.2), complete API table, `-o` and consensus rules, every number re-checked against the stored results in `reports/`.
- The main benchmark of chapter 6.1 was re-run on this code (`reports/bench_final_v4_4.json`, `reports/bench_final_v4_4_quadtilt.json`, tables `reports/FINAL_TABLES_v4_4*.md`): the primary-pool headline numbers are unchanged (0.58 % flips, 0 real accepted), CORD flips fall from 3.67 % to 2.67 % and the external pools from 2.26 % to 1.93 % (the TOO_FEW_LINES angle of v4.3.1 was not yet in the first run, `bench_final_v4_3.*`). Chapter 5 (`reports/benchmark/`) was run with 4.4.0.
- The book `docs/`: design, evaluation protocol, results, decision log, reproduction guide, and **chapter 5, a controlled comparison with other open-source tools** (PP-LCNet, docTR, DocOrient, an EfficientNetV2 photo model, Tesseract OSD): same inputs and hardware, exact quarter turns first, the other tools also behind docangle's straightening, real phone frames, tools allowed to hold pages back, eleven threats to validity.
- `bench/compare_open_models.py` (runs the tools, stores every answer with its score and flag) and `bench/compare_report.py` (Wilson intervals over pages, exact page-level sign tests, selective-prediction and speed tables; `fill-docs` writes the generated tables of chapter 5 and the README, and a unit test keeps them in step).
- `bench/tesseract_dpi_check.py`: telling Tesseract the resolution changes none of its answers.
- SmartDoc comparison truth fixed: one background is filmed with the page turned by 90 degrees; the stored perfect-detector SmartDoc row of chapter 6 measured again with the current code (flips 1.5 %, was 2.7 % before the v4.3.1 line-count fix).
- Release files: `LICENSE`, `NOTICE.md`, `CITATION.cff`, `CONTRIBUTING.md`, `models/README.md`, continuous integration.
- Opt-in document finder for photos where the page lies small on a desk (`PipelineConfig(doc_crop=True)`, `docangle/docrop.py`): SmartDoc whole frames within 1° 42.9 % to 73.1 %, flips 6.4 % to 3.9 % (§22).
- `tools/ocr_pipeline.py --engine tesseract`: the end-to-end OCR tool without a GPU (§21).

## [4.3.3] - 2026-10-13
- `tools/ocr_pipeline.py`: PDF or image to angle to upright page to PaddleOCR to text on the GPU (§21).
- Fixed: onnxruntime-gpu ran the models silently on the CPU when it could not find the pip-installed CUDA libraries; they are now found without `LD_LIBRARY_PATH` and a failed GPU request is an error.

## [4.3.2] - 2026-10-13
- The straightened image is rotated with lossless quarter turns, no resampling for tilts under 0.1° and bicubic interpolation otherwise (`upright(..., min_tilt=0.1)`); the old behaviour is `upright(img, a, interpolation=cv2.INTER_LINEAR, lossless_quarter_turns=False)`. No OCR effect measured (§20).
- Documented: for PDFs `correct()` returns the page at `pdf_long_side` (1400 px by default).

## [4.3.1] - 2026-10-13
- Pages with too few text lines report the classifier's angle instead of the regressor's (§15).
- Fixed: PDFium is not thread-safe; all PDFium calls are serialised by a lock (threaded batches used to crash or return unreadable pages) (§16).
- Opt-in PDF fast path (`pdf_fast_path`, `--pdf-fast`): 100 scanned pages 6.9 s to 2.7 s (§17).
- Lean CPU settings for batches in the CLI: identical results, 29-35 % less CPU (§18).
- Optional GPU provider (`ort_provider="cuda"`), speed profiles, `lcnet_weight=0` (§15, §19).

## [4.3.0] - 2026-10-11
- New confidence and review rule: the posterior of the chosen quadrant minus 0.30 when the regressor overrode, review below 0.90; the line-count term is gone (§11).
- Opt-in multi-page consensus (`predict_job`, `predict_pdf`, `--consensus`) (§13).
- Real camera evaluation on SmartDoc 2015 (§14); `tools/first_look.py` for label-free inspection of real photos.

## [4.2.0] - 2026-10-11
- Fourier radial-projection fine tilt replaces the two Hough passes: within 1° 90.2 % to 93.8 %, errors above 5° 95 to 51 in 2800 paired cases, 7-8 ms faster (§10). The old estimator is `fine_estimator="hough"`.

## [4.1.0] - 2026-10-10
- Final benchmark of the rebuilt pipeline (flips 0.50 % against 4.50 % for the predecessor), own classifier v4 trained with real phone photos (CORD) and DocLayNet pages, PDF input, speculative pass 2, reduced-scale JPEG decode, accuracy-guard tool (§1-§9).

## [4.0.0] - 2026-10-08
- Audit and rebuild of the predecessor pipeline as the `docangle` package: fixes for 20 audit findings (OpenCV 5 crash, silent missing model, EXIF, batch API, packaging), benchmark harness with page-level statistics, labelling tool.
