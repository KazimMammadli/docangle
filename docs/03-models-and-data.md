# 3. Models and data

## 3.1 The models

`docangle` uses three ONNX models. The first two take part in every prediction; the third is consulted rarely. SHA-256 and provenance of every file are in [`models/manifest.json`](../models/manifest.json).

| file | role | size | origin | licence |
|---|---|---|---|---|
| `pp_lcnet_doc_ori.onnx` | 4-way page orientation, 4 rotated views | 6.8 MB | PaddleOCR / PaddleX `PP-LCNet_x1_0_doc_ori` converted to ONNX, unchanged | Apache-2.0 |
| `orient_cls_v4.onnx` | 4-way page orientation, our own, 2 views | 17 MB | trained with `src/train_orientation.py` (MobileNetV3-Large, torchvision ImageNet weights, fine-tuned) | see 3.4 |
| `document_angle_detector_large.onnx` | global 360° `[sin, cos]` regressor, fallback only | 12 MB | trained on synthetic rotations of Tobacco3482 pages in an earlier project run; the training log was not preserved | see 3.4 |

An earlier generation (`orient_cls_v1`) is kept only because the audit tool `src/label_audit.py` uses it as an independent voter.

## 3.2 The own classifier

* **Architecture**: MobileNetV3-Large (torchvision), grey input squashed to 320 × 320, mean 0.449, std 0.226, four logits for the clockwise classes. 17 MB, 15.3 ms median for the ONNX run of two views on this CPU (`reports/profile_stages_v4_4.txt`).
* **Training samples are simulated photographs of audited pages**: a random tilt of up to ±45°, a desk or background, lighting gradients and shadows, blur, noise, JPEG compression, keystone and partial crops, then straightened with an estimate that is about 0.5° wrong, as the real pipeline would do (`src/orient_data.py`). The benchmark's own simulator (`bench/degrade.py`) is separate code that models the same kinds of effects and draws on the same 20 generated background textures (`data/backgrounds/`): the simulated photo levels of every benchmark in this book are therefore *familiar* to docangle's classifier and unfamiliar to third-party models (chapter 5.5 says what that means for the comparison).
* **Recipe** (v4): fine-tuned from v3 (itself from v1) for 12 epochs, 12 000 samples per epoch, learning rate 3e-4, about 40 minutes on an RTX 3060 laptop GPU. The exact command is in [chapter 12](12-reproduce.md); the arguments and the epoch history are stored with the checkpoint (`models/orient_cls_v4.pt`, `orient_cls_v4_history.json`).

| training pool | what | pages |
|---|---|---|
| `real_train` | Tobacco3482 train split: scanned business documents | 2587 pages kept; of the 2785 train pages of the split, 143 sit in `cache/real_train_dropped` (sideways or flipped, audit) and 55 carry the suffix `.dropped` (set aside by the automatic filter in `src/orient_data.py`): 2587 + 143 + 55 = 2785 |
| `synth_train` | procedural Latin / Azerbaijani-flavoured office pages (`src/synth_docs.py`) | 6000 |
| `rvl_inv_train` | the "invoice" class of RVL-CDIP | 6022 (after audit) |
| `cord_train` | CORD v2 *train* receipts photographed by phone | 700 |
| `doclaynet_train` | DocLayNet-small pages (reports, manuals, patents...) | 424 |

## 3.3 Label noise: the first thing to check in any orientation data set

"Upright" labels in public document collections are not reliable. A first classifier trained on the raw data memorised the mistakes. An out-of-sample audit (PP-LCNet and an earlier classifier had to agree that a page is upright; contact sheets were inspected by eye) found:

| data set | pages that were sideways or upside down in the source |
|---|---|
| RVL-CDIP "invoice" | 17.6 % of the train pages (1290 of 7312), 18.5 % of val (74 of 400), 18.8 % of the held-out pool (282 of 1500) |
| Tobacco3482 | 143 of 2785 train and 21 of 348 val pages (5-6 %) |
| CORD, DocLayNet, FUNSD | none found to be label errors; the 46 flagged receipts and 2 DocLayNet pages were upright or ambiguous: the model's mistakes, kept |

Dropped pages were moved aside, never deleted, and a handful of benchmark pages are still sideways in their source (one invoice is the best-known case: its "flips" in the benchmark are correct predictions; the tables say so). The consequence for every evaluation: **a result computed against raw labels punishes a correct model.** Scans also carry *source skew*: a page counted as upright is often 0.3-1° off, which caps the fine-angle accuracy that can be measured on scan pools.

## 3.4 Licences, and what the public repository contains

| item | terms | consequence |
|---|---|---|
| code | MIT (this repository) | free to use, change and redistribute with the notice |
| `pp_lcnet_doc_ori.onnx` | Apache-2.0 (PaddlePaddle) | redistributable with the licence text and notice ([NOTICE.md](../NOTICE.md)) |
| RVL-CDIP / Tobacco3482 (IIT-CDIP) | research use only | the pages are **not** redistributed; scripts download them from their public sources |
| CORD v2 | CC-BY-4.0 | not redistributed (downloaded by script) |
| DocLayNet | CDLA-Permissive-1.0 | not redistributed (downloaded by script) |
| FUNSD | no licence text in the downloaded copy; treated as research-only | evaluation only; not redistributed |
| SmartDoc 2015 challenge 1 | CC-BY-4.0 | not redistributed (downloaded by script) |
| `orient_cls_v4` and the regressor | trained on data of the types above | **the weights' terms are the maintainers' decision** and are stated in [`models/README.md`](../models/README.md) and the release notes; until then they are research-use weights |
| a private set of 100 Azerbaijani test pages | source documents not documented | **never published**; every result computed on it is marked *not reproducible by outsiders* |

Raw benchmark inputs (pages, failure galleries, OCR transcripts of those pages) are therefore absent from the repository; per-case answers are stored for the comparison of chapter 5 (`reports/benchmark/raw_*.json.gz`) and the ablation dumps (`reports/data/`); the main benchmark files keep per-pool summaries and the per-case rows of errors above 5° only ([chapter 12](12-reproduce.md) says how to regenerate the inputs from the public sources).
