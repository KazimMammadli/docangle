# bench/

Scripts that produce the numbers of the [book](../docs/index.md). Run each as `python -m bench.<name>`; the first lines of every script show its command, and [chapter 12](../docs/12-reproduce.md) lists them with run times. Results go to [`reports/`](../reports/README.md).

## Core: the main benchmark

| script | what it does |
|---|---|
| `run` | main benchmark: candidates on simulated rotated and degraded pages of every pool, each number with n and an interval |
| `summarize` | pools a `run` result into the `FINAL_TABLES*.md` tables |
| `page_interval` | page-level interval of the flip rate of a stored `run` result |
| `candidates` | the named pipelines that `run`, `guard` and the other scripts compare |
| `datasets` | file lists of the page pools |
| `degrade` | seeded scanner and phone-photo simulator with exact ground truth |
| `metrics` | shared intervals, angle error and summaries |
| `guard` | accuracy guard for a change: baseline and variants on the same cases |
| `equiv` | case-by-case check that a refactor or speed-up changes no result |

## Comparison with other tools (ch. 5)

| script | what it does |
|---|---|
| `compare_open_models` | runs docangle and the other open-source tools on identical inputs |
| `compare_report` | builds the chapter 5 tables from the stored raw files |
| `exp_duarte` | wrapper of the EfficientNetV2 orientation model, used by the comparison |
| `docorient_quarter` | DocOrient and EfficientNetV2 against docangle on exact quarter turns |
| `tesseract_dpi_check` | fairness check of the Tesseract candidate |

## Real pages and independent checks (ch. 6)

| script | what it does |
|---|---|
| `smartdoc_eval` | SmartDoc 2015 phone frames with page-corner ground truth |
| `smartdoc_page_size` | size of the page inside the SmartDoc frames |
| `dise_eval` | DISE-2021 skew test |
| `skew_check` | fine angle re-scored against each source page's own skew |
| `simple_deskew_baseline` | textbook `minAreaRect` deskew against the Fourier tilt |
| `eval_labeled` | evaluates candidates on your own photos labelled with `tools/label_server.py` |

## Design checks (ch. 6.2, 6.5, 6.6)

| script | what it does |
|---|---|
| `views_dump` | stores every view's model output per case |
| `views_emulate` | rebuilds a pipeline variant's decision from a `views_dump` row |
| `ablate` | switches pipeline components off one at a time on a dump |
| `features`, `calibrate` | decision features dump; fitted voter weights and a learned review score (not adopted) |
| `consensus_eval` | opt-in multi-page consensus |

## OCR (ch. 7)

| script | what it does |
|---|---|
| `ocr_rotation_eval` | do OCR engines read rotated pages by themselves, and does docangle in front help |
| `ocr_upright_quality` | effect of the rotation method of the corrected page on OCR |
| `ocr_pipeline_eval` | end-to-end check of `tools/ocr_pipeline.py` |

## Speed (ch. 8)

| script | what it does |
|---|---|
| `profile_stages` | time per stage, thread scaling and start-up |
| `latency_files` | one call on JPEG files of three sizes |
| `gpu_ab` | CPU against GPU |
| `cpu_knobs` | ONNX Runtime and OpenCV thread settings |
| `timing_ab` | latency and throughput of candidates in interleaved order |
| `pdf_equiv` | opt-in PDF JPEG fast path against full rendering |

## Rejected experiments (ch. 11)

| script | what it does |
|---|---|
| `quantize_models` | static int8 quantisation of the classifiers |
| `exp_doctr`, `exp_doctr_eval`, `exp_doctr_analyze` | docTR (or EfficientNetV2) as a third quadrant voter |
