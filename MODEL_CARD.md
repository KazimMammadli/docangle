# Model card — docangle orientation models

`docangle` ships **three ONNX models**. Only the first two take part in every prediction.

| file | role | size | licence / provenance |
|---|---|---|---|
| `models/pp_lcnet_doc_ori.onnx` | 4-way page orientation (0/90/180/270), 4 rotated views + centre crop | 6.8 MB | PaddleOCR / PaddleX `PP-LCNet_x1_0_doc_ori`, **Apache-2.0**, converted to ONNX, unchanged |
| `models/orient_cls_v4.onnx` | 4-way page orientation, our own, 2 views (0° and 180°) | 17 MB | trained here (`src/train_orientation.py`); MobileNetV3-Large (torchvision, ImageNet-pretrained, BSD-3) fine-tuned on the data below |
| `models/document_angle_detector_large.onnx` | global 360° `[sin, cos]` regressor, **fallback only** (its fallback flag was set in 63 of 6300 benchmark cases, 1.0 %) | 12 MB | see `models/README.md`; the training run was not preserved ("Known limits") |

SHA-256 and provenance of every file: `models/manifest.json`. `models/orient_cls_v1.onnx` is the first generation, kept only because `src/label_audit.py` uses it as an independent voter (the
pipeline does not load it when v4 exists). v3 (the intermediate model of the first benchmark round) is not included.

## What the pipeline decides

`docangle.DocumentOrientationPipeline` (see README) returns an angle in [-180°, 180°] (CCW-positive) plus a confidence and a
`needs_review` flag. Two different questions are answered by two different mechanisms:

* **Fine tilt (mod 90°)** — signal processing, not learned (v4.2+): the peak of the radial projection of the 2-D DFT magnitude of a binarised,
  windowed 512-px copy of the page, folded mod 90° (`docangle/fftskew.py`). A Hough line count runs next to the classifiers and only feeds the
  `TOO_FEW_LINES` gate. (v4.1 used Hough pass 1 + pass 2 for the tilt: `fine_estimator="hough"`.)
* **Which of the 4 quadrants (0/90/180/270)** — the only place a mistake produces a flipped page. Decided by the **sum of the
  log-posteriors of PP-LCNet (4 rotated views) and our own classifier (0° and 180° views)**. Rotation voting: a page of class c
  rotated by 90·r looks like class c−r, so every view votes for the same page-level class.

## Our classifier (`orient_cls_v4`)

* Input: grayscale page squashed to 320×320, mean 0.449 / std 0.226. Output: 4 logits (clockwise class).
* Training script: `src/train_orientation.py` (args stored in the checkpoint; epoch history in `models/orient_cls_v4_history.json`).
* **Training samples** are simulated photographs: random tilt in ±45°, desk/background, lighting gradients and shadows, blur, noise, JPEG,
  keystone, partial crop, then straightened with an estimate that is ~0.5° wrong, like the real pipeline (`src/orient_data.py`).
* **Pages used for training** (all grayscale, long side 1000 px, cached under `data/cache/`, git-ignored, rebuildable):

  | pool | what | pages | note |
  |---|---|---|---|
  | `real_train` | Tobacco3482 train split (scanned business docs) | 2587 | of the 2785 train pages: 143 moved to `real_train_dropped` (audit), 55 set aside by the automatic filter (`.dropped`) |
  | `synth_train` | procedural Latin/Azerbaijani-flavoured office pages (`src/synth_docs.py`) | 6000 | |
  | `rvl_inv_train` | RVL-CDIP "invoice" class (HF `rvl_invoice`) | 6022 | after audit, see below |
  | `cord_train` | CORD v2 *train* receipts photographed by phone | 700 | upright by construction; checked visually |
  | `doclaynet_train` | DocLayNet-small pages (financial reports, manuals, patents, …) | 424 | |

* **Label-noise audit (important).** 17.6 to 18.8 % of the audited RVL-CDIP pages labelled "upright invoice" (1290 of 7312, 74 of 400, 282 of 1500) and about 5 % of Tobacco pages are in fact
  sideways or upside down in the source dataset. A first model trained on the raw data memorised those mistakes. Every pool was therefore
  audited out-of-sample (PP-LCNet and an earlier classifier had to agree that the page is upright; contact sheets were inspected), and
  the pages that failed were moved aside (`*_dropped`, never deleted). Counts are in `data/README.md` and `reports/rvl_inv_pools.json`.
  Even after cleaning, a handful of benchmark pages are still wrong in the source (e.g. `certified_invoice_030` is sideways); see
  `reports/FINAL_REPORT.md`, §6 "Failure analysis".
* **Held-out evaluation pools** are never used for training or checkpoint selection: `rvl_heldout`, `tobacco_cert`, `az`, `ext_funsd`,
  `ext_cord` (CORD test + validation receipts), `ext_doclaynet` (300 pages disjoint from the training pages).

## Intended use

Latin-script documents (letters, invoices, contracts, forms, reports) scanned or photographed at any angle. Output is meant to be
used with the `needs_review` flag: route flagged pages to a person instead of trusting a guess.

## Known limits (read before relying on it)

* **No labelled set of real phone photos of the target documents exists yet.** Photo conditions are simulated (`bench/degrade.py`).
  The only real camera footage measured is SmartDoc (30 English documents, low-resolution frames); the CORD receipts are phone photographs too, but they are turned and degraded by the simulator, so they do not test a real camera. Build one with `tools/label_server.py`.
* Narrow receipts, very sparse pages (cover pages, a single heading), logo-only pages and pages with almost no text are the weak
  spot; these are mostly caught by `needs_review`, not all.
* Not tested: Cyrillic, Arabic-script, CJK, handwriting-only pages, A3, ID cards.
* Fine-angle accuracy on real scans is bounded by the skew of the source page itself (a "scanned upright" page is often 0.3–1°
  off); the reported ≤1° rates on scan pools therefore under-state the angle quality. Only the born-digital `az` pool has exact
  ground truth.
* The fallback regressor's training run is not reproducible from this repository.
* Page orientation inside a *photo with a visible desk* relies on the page being the dominant object; heavy occlusion by hands is
  not modelled.

## Licences of the data

Tobacco3482 / RVL-CDIP: research use only (IIT-CDIP). CORD v2: CC-BY-4.0. DocLayNet: CDLA-Permissive-1.0. FUNSD: no licence text in the downloaded copy, treated as research-only (used for evaluation only). The
Azerbaijani test pages have no documented origin (`data/README.md`): internal testing only, do not redistribute. Trained weights
derived from research-only data should be treated as research-only until the maintainer decides otherwise.

## Optional components (not part of the default per-page decision)

* **Multi-page consensus** (`docangle/consensus.py`, v4.3, opt-in): no model, a Bayesian vote over the other pages' quadrant posteriors; see README and `reports/FINAL_REPORT.md` §13.
* **docTR page-orientation model** (OnnxTR v0.6.0, Apache-2.0): evaluated and rejected as a voter (§12); its file is not shipped: `bench/exp_doctr.py` reads it from `data/external/doctr/` (git-ignored) for comparisons on labelled photos of the intended documents.
