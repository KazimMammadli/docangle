# reports/

Stored results behind every number in the [README](../README.md) and the [book](../docs/index.md). Each row names the script that wrote the file; [chapter 12](../docs/12-reproduce.md) has the commands.

## Start here

| file | what it is |
|---|---|
| [FINAL_TABLES_v4_4.md](FINAL_TABLES_v4_4.md) | main benchmark of the current version: pooled tables with intervals (ch. 6.1-6.3) |
| [FINAL_TABLES_v4_4_quadtilt.md](FINAL_TABLES_v4_4_quadtilt.md) | the same for hand-held pages: random quarter turn plus tilt (ch. 6.1) |
| [page_interval_v4_4.txt](page_interval_v4_4.txt) | page-level interval of the main flip rate (ch. 6.1) |
| [benchmark/RESULTS.md](benchmark/RESULTS.md) | comparison with other open-source tools (ch. 5) |
| [FINAL_REPORT.md](FINAL_REPORT.md) | lab notebook: how each version was derived, decisions and rejected ideas |
| [METHOD_RESEARCH.md](METHOD_RESEARCH.md) | survey notes on other methods and tools |

`bench_*.json` files hold the raw per-cell results of `bench.run`. The runner also writes a Markdown twin; the twins are not stored because the JSON rebuilds them byte for byte:

```
python -c "import json,sys; from bench.run import to_markdown; print(to_markdown(json.load(open(sys.argv[1]))), end='')" reports/bench_final_v4_4.json
```

## Main benchmark (ch. 6)

| file | what it is | written by |
|---|---|---|
| [bench_final_v4_4.json](bench_final_v4_4.json), [bench_final_v4_4_quadtilt.json](bench_final_v4_4_quadtilt.json) | raw results of the current main benchmark | `bench.run` |
| [skew_check_v4_4.txt](skew_check_v4_4.txt) | fine angle re-scored against each source page's own skew (consistency check, ch. 6.3) | `bench.skew_check` |
| [dise_eval_v4_3.txt](dise_eval_v4_3.txt) | DISE-2021 out-of-domain skew test (ch. 6.3) | `bench.dise_eval` |
| [smartdoc_eval_crop_v4_4.txt](smartdoc_eval_crop_v4_4.txt) | SmartDoc 2015 real phone frames, page cut out with the true corners (ch. 6.4) | `bench.smartdoc_eval` |
| [smartdoc_eval.txt](smartdoc_eval.txt), [smartdoc_eval_rot90.txt](smartdoc_eval_rot90.txt), [smartdoc_eval_crop_rot90.txt](smartdoc_eval_crop_rot90.txt) | SmartDoc whole frames, and whole or cut-out frames with random quarter turns (ch. 6.4) | `bench.smartdoc_eval` |
| [smartdoc_eval_doccrop_even.txt](smartdoc_eval_doccrop_even.txt), [smartdoc_eval_doccrop_odd.txt](smartdoc_eval_doccrop_odd.txt), [smartdoc_eval_doccrop_whole.txt](smartdoc_eval_doccrop_whole.txt) | opt-in document finder on SmartDoc: parameters chosen on the documents with an even `model_id`, checked on the odd ones, then all frames | `bench.smartdoc_eval` |
| [smartdoc_page_size.txt](smartdoc_page_size.txt) | size of the page inside the SmartDoc frames | `bench.smartdoc_page_size` |
| [simple_deskew_baseline.txt](simple_deskew_baseline.txt) | textbook `minAreaRect` deskew against the Fourier tilt, simulated pages | `bench.simple_deskew_baseline` |
| [simple_deskew_smartdoc.txt](simple_deskew_smartdoc.txt) | the same on SmartDoc frames with the page cut out | |
| [consensus_eval.txt](consensus_eval.txt) | opt-in multi-page consensus (ch. 6.6) | `bench.consensus_eval` |

## Comparison with other tools (ch. 5)

| file | what it is | written by |
|---|---|---|
| [benchmark/raw_handheld.json.gz](benchmark/raw_handheld.json.gz), [raw_quarter](benchmark/raw_quarter.json.gz), [raw_uniform](benchmark/raw_uniform.json.gz), [raw_smartdoc](benchmark/raw_smartdoc.json.gz) | every tool's answer to every case, one file per mode | `bench.compare_open_models run` |
| [tesseract_dpi_check.txt](tesseract_dpi_check.txt) | fairness check: does `--dpi` change Tesseract's answers | `bench.tesseract_dpi_check` |
| [docorient_quarter_turns.txt](docorient_quarter_turns.txt) | DocOrient against docangle on exact quarter turns (earlier version of the script) | `bench.docorient_quarter` |

## Design checks: ablation, review rule, data (ch. 3, 6.2, 6.5)

| file | what it is | written by |
|---|---|---|
| [ablation_dev.txt](ablation_dev.txt), [ablation_heldout.txt](ablation_heldout.txt) | every pipeline component switched off in turn, paired intervals | `bench.ablate` |
| [smartdoc_ablation_crop.txt](smartdoc_ablation_crop.txt), [smartdoc_ablation_crop_rot90.txt](smartdoc_ablation_crop_rot90.txt), [smartdoc_ablation_full.txt](smartdoc_ablation_full.txt), [dise_ablation.txt](dise_ablation.txt) | the same ablation checked on real frames and on DISE-2021 | `bench.smartdoc_eval`, `bench.dise_eval` |
| [ablate_views_confirm.json](ablate_views_confirm.json) | quadrant error of the 12-view classifier vote against the cheap vote | |
| [data/views_v4_3_dev.json.gz](data/views_v4_3_dev.json.gz), [data/views_v4_3_heldout_rvl.json.gz](data/views_v4_3_heldout_rvl.json.gz) | per-view dumps the ablation reads | `bench.views_dump` |
| [calibrate_e2.txt](calibrate_e2.txt), [data/features_v4_3.json.gz](data/features_v4_3.json.gz) | fitted voter weights and a learned review score against the confidence rule (not adopted) | `bench.calibrate`, `bench.features` |
| [bench_e2_conf_quadtilt.json](bench_e2_conf_quadtilt.json) | hand-held check of the v4.3 review rule against the old one | `bench.run` |
| [audit_rvl.json](audit_rvl.json), [audit_tobacco_lcnet.json](audit_tobacco_lcnet.json) | label-noise audit of the RVL-CDIP and Tobacco3482 pools | `src.label_audit` |
| [audit_ext_cord.json](audit_ext_cord.json), [audit_ext_doclaynet.json](audit_ext_doclaynet.json), [audit_ext_funsd.json](audit_ext_funsd.json) | pages flagged in the external pools (ch. 3) | `src.audit_external` |
| [rvl_inv_pools.json](rvl_inv_pools.json) | pool sizes of the RVL-CDIP invoice preparation | `src.prep_rvl_invoices` |

## OCR (ch. 7)

| file | what it is | written by |
|---|---|---|
| [ocr_rotation/all_tables.txt](ocr_rotation/all_tables.txt) | OCR engines on rotated pages: native, oracle and corrected by docangle (7.1) | `bench.ocr_rotation_eval` |
| [ocr_rotation/quality_tables.txt](ocr_rotation/quality_tables.txt), [ocr_rotation/upright_sharpness_sweep.txt](ocr_rotation/upright_sharpness_sweep.txt) | effect of the rotation method of the corrected page (7.2) | `bench.ocr_upright_quality` |
| [ocr_pipeline_eval.txt](ocr_pipeline_eval.txt), [ocr_pipeline_eval_tesseract.txt](ocr_pipeline_eval_tesseract.txt) | end-to-end check of `tools/ocr_pipeline.py` | `bench.ocr_pipeline_eval` |
| [environments_ocr_gpu.txt](environments_ocr_gpu.txt) | library versions of the separate OCR and GPU environments | |

## Speed (ch. 8)

| file | what it is | written by |
|---|---|---|
| [profile_stages_v4_4.txt](profile_stages_v4_4.txt) | time per stage, thread scaling, start-up | `bench.profile_stages` |
| [latency_files_v4_4.txt](latency_files_v4_4.txt), [latency_files_v4_4_repeat.txt](latency_files_v4_4_repeat.txt) | one call on a JPEG file at three sizes, two runs | `bench.latency_files` |
| [gpu_ab.txt](gpu_ab.txt) | CPU against GPU | `bench.gpu_ab` |
| [cpu_knobs.txt](cpu_knobs.txt) | ONNX Runtime and OpenCV thread settings | `bench.cpu_knobs` |
| [pdf_equiv.txt](pdf_equiv.txt) | opt-in PDF JPEG fast path against full rendering | `bench.pdf_equiv` |
| [timing_ablation.txt](timing_ablation.txt), [timing_pplcnet_removal.txt](timing_pplcnet_removal.txt) | speed of reduced pipelines | `bench.timing_ab` |
| [guard_doccrop.txt](guard_doccrop.txt), [guard_e1_fft_vs_hough.txt](guard_e1_fft_vs_hough.txt) | accuracy guard of the document finder and of the Fourier tilt | `bench.guard` |

## Rejected experiments (ch. 11)

| file | what it is | written by |
|---|---|---|
| [int8_quantization.txt](int8_quantization.txt), [guard_int8.txt](guard_int8.txt) | int8 models: slower and less accurate | `bench.quantize_models`, `bench.guard` |
| [exp_doctr_e3b.txt](exp_doctr_e3b.txt), [exp_duarte_voter.txt](exp_duarte_voter.txt) | docTR and EfficientNetV2 as a third quadrant voter | `bench.exp_doctr_analyze` |
| [exp_docorient.json](exp_docorient.json) | early DocOrient comparison at arbitrary angles | |
| [bench_step6_REJECTED_length_weighted_axis.json](bench_step6_REJECTED_length_weighted_axis.json) | length-weighted line axis | `bench.run` |

## Earlier versions (kept as sources of the lab notebook)

| file | version |
|---|---|
| [FINAL_TABLES.md](FINAL_TABLES.md), [FINAL_TABLES_quadtilt.md](FINAL_TABLES_quadtilt.md), [bench_final_v4_1.json](bench_final_v4_1.json), [bench_final_v4_1_quadtilt.json](bench_final_v4_1_quadtilt.json), [dise_eval_v4_1.txt](dise_eval_v4_1.txt) | 4.1 |
| [FINAL_TABLES_v4_2.md](FINAL_TABLES_v4_2.md), [FINAL_TABLES_v4_2_quadtilt.md](FINAL_TABLES_v4_2_quadtilt.md), [bench_final_v4_2.json](bench_final_v4_2.json), [bench_final_v4_2_quadtilt.json](bench_final_v4_2_quadtilt.json), [dise_eval_v4_2.txt](dise_eval_v4_2.txt), [skew_check_v4_2.txt](skew_check_v4_2.txt) | 4.2 |
| [FINAL_TABLES_v4_3.md](FINAL_TABLES_v4_3.md), [FINAL_TABLES_v4_3_quadtilt.md](FINAL_TABLES_v4_3_quadtilt.md), [bench_final_v4_3.json](bench_final_v4_3.json), [bench_final_v4_3_quadtilt.json](bench_final_v4_3_quadtilt.json), [smartdoc_eval_crop.txt](smartdoc_eval_crop.txt) | 4.3 |
| [bench_baseline_step1.json](bench_baseline_step1.json), [bench_step4_default_vs_full_vs_c8l.json](bench_step4_default_vs_full_vs_c8l.json), [bench_step5_hough_refine.json](bench_step5_hough_refine.json), [bench_step8_v3_vs_v4.json](bench_step8_v3_vs_v4.json) | development steps of 4.1 in the lab notebook |
| [profile_stages.txt](profile_stages.txt), [skew_check.txt](skew_check.txt) | first runs, replaced by the `_v4_4` files |
