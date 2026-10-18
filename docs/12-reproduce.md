# 12. Reproducing the results

Every table in this book names the command that produced it. This chapter collects them, with what each needs and how long it takes on the measurement machine (Ryzen 9 5980HX; the training step used an RTX 3060 Laptop GPU). Run everything from the repository root with `PYTHONPATH=.`. The benchmark uses about 4 GB of RAM; on a machine with 16 GB or less run it under a memory limit, for example `systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 nice -n 5 <command>`, and run heavy jobs one at a time.

## 12.1 Environment

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,pdf]"            # add ".[train]" for data preparation and training (12.2, 12.7) and ".[bench]" for the comparison (12.5)
pytest -q                                   # the unit tests; tests that need benchmark data skip themselves when it is absent
python -m tools.gen_config_doc --check      # the configuration appendix matches the code
```

Measured with Python 3.14, NumPy 2.3, OpenCV 4.14 (headless), ONNX Runtime 1.31, pypdfium2 5.14; docangle requires Python 3.10 or newer (continuous integration runs 3.10 and 3.12); the tests and the accuracy, comparison and CPU speed measurements used 3.14; the OCR study (chapter 7) and the GPU measurements ran in separate environments (`reports/environments_ocr_gpu.txt`) with Python 3.11.16, onnxruntime-gpu 1.19.2, PaddleOCR 3.7, EasyOCR 1.7.2 and Tesseract 5.5.3. The comparison harness additionally uses `docorient` (PyPI), `onnxruntime` models of docTR and of the EfficientNetV2 orientation model, and a Tesseract 5 installation with the `osd` model (see 12.5).

## 12.2 Which data can be recreated

| pool or data set | recreated by | status |
|---|---|---|
| `tobacco_cert` (159 pages), Tobacco training pools | `python data/download_samples.py`, then `python -m src.orient_data`; the page list is `data/certified_upright_test.json` | recreatable (about 3 GB download) |
| `rvl_heldout`, RVL-CDIP training pools | `python -m src.prep_rvl_invoices` (Hugging Face `rvl_invoice`; split by page, seeded) | recreatable, but its de-duplication step used the original 200-page invoice test pools, so the page set can differ slightly |
| `invoices` (100 certified + 100 test RVL-CDIP pages) | — | **snapshot only**: the images were kept, their source identifiers were not; not redistributed |
| `ext_funsd`, `ext_cord`, `ext_doclaynet` | `python -m src.prep_external`, then `python -m src.audit_external ext_funsd ext_cord ext_doclaynet` | recreatable |
| SmartDoc 2015 challenge 1 | the `frames.tar.gz` of release v2.0.0 of github.com/jchazalon/smartdoc15-ch1-dataset (972 MB, CC-BY-4.0), unpacked to `data/external/smartdoc/` | recreatable; sha256 of the archive `3acb8be1...9eae` |
| DISE-2021 | `dise2021_45.zip` from Hugging Face `phamquiluan/DISE-2021`, in `data/external/dise2021/` | recreatable |
| `az` (100 Azerbaijani pages), the OCR study pages | — | **private, never published** (origin not documented). Use your own born-digital pages: put them as PNG files in `data/az_test_pages/` (the folder name is fixed in `bench/datasets.py`; the speed tools `bench.latency_files`, `bench.timing_ab` and `bench.docorient_quarter` read it too), or generate pages with `src/synth_docs.py` |

## 12.3 Our own evaluation

The commands below name the pools of the original runs. `az` and `invoices` are private (12.2): drop them from `--datasets` or fill `data/az_test_pages/` with your own pages; a pool that is empty stops the command with a message that says so.

| table | command | time |
|---|---|---|
| main benchmark (6.1) | `python -m bench.run --datasets az invoices tobacco_cert rvl_heldout ext_funsd ext_doclaynet ext_cord --levels scan photo_easy photo_hard --angle-modes uniform --candidates docangle --seeds 3 --n 100 --tag mytag`, then `python -m bench.summarize reports/bench_mytag.json` | 25-40 min |
| hand-held mode (6.1) | the same with `--angle-modes quad_tilt --seeds 2` | 15-25 min |
| page-level interval of the flip rate (6.1, 4.4) | `python -m bench.page_interval reports/bench_mytag.json --pools az invoices tobacco_cert rvl_heldout` | seconds |
| fine angle against source skew (6.3) | `python -m bench.skew_check --datasets az invoices tobacco_cert rvl_heldout ext_funsd ext_doclaynet --levels scan photo_hard --n 100 --seeds 2` | 10 min |
| DISE-2021 (6.3) | `python -m bench.dise_eval 600` | 1 min |
| SmartDoc (6.4) | `python -m bench.smartdoc_eval --every 25 --candidates docangle docangle_crop` (add `--crop 0.08` for the perfect-detector reference, `--docs odd` for the held-out half; `reports/smartdoc_eval_crop_v4_4.txt` is the perfect-detector run of this version) | 2-4 min |
| ablation (6.5) | `python -m bench.views_dump ...`, then `python -m bench.ablate views.json` | 30 min dump, seconds to ablate |
| multi-page consensus (6.6) | `python -m bench.consensus_eval --out reports/consensus_eval.txt` | 3 min |
| accuracy guard for any change | `python -m bench.guard --base docangle --variants <candidate> --datasets tobacco_cert rvl_heldout ext_funsd --levels scan photo_hard --n 100` | 5-15 min |
| per-case equivalence of a code change | `python -m bench.equiv dump ... ; python -m bench.equiv compare before.json after.json` | 5 min |

Candidates are named in `bench/candidates.py`. The stored raw results of the runs reported here are in [`reports/`](../reports/) (`bench_*.json`, `reports/data/*.json.gz`, `reports/benchmark/`); each stores the library versions and the CPU model it was produced with, and the main-benchmark files also the commit and configuration.

## 12.4 Speed

| table | command |
|---|---|
| stage costs, thread scaling, start-up (8.1, 8.2) | `python -m bench.profile_stages --pages 120 --out reports/profile_stages_v4_4.txt` |
| latency of one call on a JPEG file (8.1) | `python -m bench.latency_files > reports/latency_files_v4_4.txt` |
| CPU settings (8.2) | `python -m bench.cpu_knobs --pages 100 --out reports/cpu_knobs.txt` |
| speed profiles (8.5) | `python -m bench.timing_ab --candidates docangle docangle_or1 docangle_lc2or1 docangle_ownonly docangle_min --pages 300 --reps 3 --workers 4` |
| GPU (8.4) | `python -m bench.gpu_ab --pages 120 --out reports/gpu_ab.txt` in an environment with `onnxruntime-gpu` |
| PDF fast path (8.3) | `python -m bench.pdf_equiv --pools az invoices --levels scan photo_hard --n 40 --out reports/pdf_equiv.txt` |

Time such things on an otherwise idle machine and on mains power: a laptop on battery power-saves the CPU and its timings are not comparable. The speed numbers of chapters 5 and 8 were taken with a desktop session running, the files named `_v4_4` (`profile_stages`, `latency_files`) on mains power with the machine otherwise idle.

## 12.5 The comparison with other open-source tools (chapter 5)

```bash
pip install -e ".[bench]"                 # DocOrient (MIT; 0.4.1 was used) and Pillow
# docTR page orientation: OnnxTR v0.6.0 release asset mobilenet_v3_small_page_orientation.onnx -> data/external/doctr/
# EfficientNetV2 orientation model: orientation_model_v2_0.9882.onnx (Hugging Face DuarteBarbosa/deep-image-orientation-detection)
#     -> data/external/duarte_orientation/   (sha256 cffe911c1dff47fbfbbd90110aaab9c07134645c460d35b3ae8832079bea91ba)
# Tesseract 5 with the osd model: set TESSERACT_ROOT to the installation (bin/tesseract, share/tessdata/osd.traineddata)
python -m bench.compare_open_models run --mode quarter  --n 25 --out reports/benchmark/raw_quarter.json.gz
python -m bench.compare_open_models run --mode handheld --n 40 --straightened --out reports/benchmark/raw_handheld.json.gz
python -m bench.compare_open_models run --mode uniform  --n 40 --straightened --out reports/benchmark/raw_uniform.json.gz
python -m bench.compare_open_models run --mode smartdoc --every 50 --straightened --out reports/benchmark/raw_smartdoc.json.gz
python -m bench.compare_report summarize reports/benchmark/raw_*.json.gz --out reports/benchmark/RESULTS.md      # every table, from the stored answers
python -m bench.compare_report fill-docs reports/benchmark/raw_*.json.gz --docs README.md docs/05-comparison.md   # rewrite the generated tables of chapter 5 and the README
python -m bench.tesseract_dpi_check --out reports/tesseract_dpi_check.txt                                          # does telling Tesseract the resolution change its answers? (5.1)
```

Without the private pools add `--datasets tobacco_cert rvl_heldout ext_funsd ext_doclaynet ext_cord` to the `run` commands; the tables then differ from chapter 5, which includes `az` and `invoices`. A candidate whose model file is missing is skipped with a message; the others still run. About 1 s per case in total, so the four runs take about an hour. The tables of chapter 5 and the comparison table of the README are *generated* between `<!-- generated:KEY -->` marks; `fill-docs --check` (and a unit test) fails when they no longer match the stored results.

## 12.6 The OCR experiments (chapter 7)

```bash
python -m bench.ocr_rotation_eval run --engine paddle_v6 --pages 12 --out reports/ocr_rotation/paddle_v6_gpu.json     # also: easyocr, tesseract
python -m bench.ocr_rotation_eval analyze reports/ocr_rotation/*.json
python -m bench.ocr_upright_quality run --engine paddle_v6 --pages 12 --out reports/ocr_rotation/quality_paddle_v6_gpu.json
python -m bench.ocr_upright_quality analyze reports/ocr_rotation/quality_*.json
python -m bench.ocr_pipeline_eval --out out/ocr_eval                                # the end-to-end check (needs paddleocr + paddlepaddle-gpu); writes out/ocr_eval/summary.txt
python -m bench.ocr_pipeline_eval --out out/ocr_eval_tess --engine tesseract --docangle-device cpu   # the same with Tesseract (needs tesseract with the aze model)
```

They read the 12 private Azerbaijani pages; substitute your own pages and ground-truth texts (`data/external/ocr_eval/gt_pages.json`: a list of `{"png", "doc", "text", "chars"}`).

## 12.7 Retraining the own classifier

```bash
python -m src.prep_external training          # CORD and DocLayNet training pools (about 4 GB peak)
python -m src.train_orientation --epochs 12 --samples 12000 --lr 3e-4 --init models/orient_cls_v3.pt \
    --train-pools real_train:0.15,synth_train:0.15,rvl_inv_train:0.25,cord_train:0.25,doclaynet_train:0.20 \
    --val-pools real_val:0.2,synth_val:0.1,rvl_inv_val:0.3,cord_val:0.25,doclaynet_val:0.15 \
    --select real_val,rvl_inv_val,cord_val,doclaynet_val --workers 4 --out models/orient_cls_v5
python -m src.export_orientation models/orient_cls_v5.pt        # then compare with `docangle` using bench.run before adopting
```

About 40 minutes on an RTX 3060 Laptop GPU. **Audit every pool for sideways pages first** (`src/label_audit.py`, `src/audit_external.py`; chapter 3.3). The recipe starts from an intermediate checkpoint (`orient_cls_v3.pt`) that is not part of the repository; start from `orient_cls_v4.pt` or from ImageNet weights and expect different numbers.

## 12.8 Checking a claim

1. Find the table; read its caption for the command.
2. If the raw result is stored (`reports/*.json`, `reports/data/`, `reports/benchmark/`), re-aggregate it (`bench.summarize`, `bench.compare_report summarize`): this needs no images.
3. To rerun, recreate the pool (12.2), run the command, and compare. Expect identical angles for identical inputs and library versions; timings vary with the machine and its load.
4. If a number does not reproduce, that is a bug in this book: please open an issue with the command, the versions and the output.
