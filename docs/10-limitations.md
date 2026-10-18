# 10. Limitations

Read this chapter before relying on docangle. It lists what is weak, what was never measured and what the data and licence situation is.

## 10.1 What the evidence does not cover

| gap | consequence |
|---|---|
| **No labelled real phone photos of the intended documents.** Photographic conditions are simulated (`bench/degrade.py`). The only real camera footage measured is SmartDoc (30 English documents, low-resolution frames, page-edge ground truth); the CORD receipts are phone photographs too, but they are turned and degraded by the simulator, so they do not test a real camera. | Treat photo numbers as a well-controlled proxy, not a field result. [Chapter 9.4](09-usage.md) shows how to measure on your own pages. |
| **The OCR study has 12 pages** from 5 documents, clean rotations, three engines. | It shows that the angle step works and what it gains; it does not show how large the gain is on your scans. |
| **Pools overlap in kind with the training data** (invoices, Tobacco, CORD, DocLayNet pages are the same families the own classifier learned from, on disjoint pages). | The in-domain pools flatter docangle against third-party models; chapter 5 therefore reports the pools nobody trained on separately. |
| **The review threshold was chosen on a 6291-case dump** that overlaps one table. | Independent checks (hand-held mode, SmartDoc, DISE-2021) were run afterwards; on the primary pools the benefit of the new rule over the old one is small and not proven. |
| **Ground truth of scans is itself skewed** by 0.3-1°. | Fine-angle rates on scan pools under-state the angle quality; only the born-digital pool has exact ground truth. |

## 10.2 Inputs the system is not designed for

* Scripts other than Latin (Cyrillic, Arabic-script, CJK, Indic), handwriting-only pages: not trained, not tested. Pages with too few text lines are caught by the `TOO_FEW_LINES` gate (always reviewed) and fall back to the classifier, but the gate was never exercised on such pages because none exist in the test pools.
* Curved or crumpled pages (no dewarping), strong perspective (a page photographed at a steep angle is rotated, not unwarped), heavy occlusion by hands.
* A3 sheets, ID cards, passports, forms with large coloured regions: not tested.
* Pages that are mostly one photograph or drawing (magazine covers, patents with figures) are a weak spot: DocLayNet's title and figure pages flip in 3.1 % of the simulated cases, SmartDoc magazines in 2.8 % (cut out) and 22.5 % (whole frame) of the real frames (chapters 5 and 6).

## 10.3 Known weak spots

| weak spot | evidence | handled by |
|---|---|---|
| receipts photographed by phone (narrow, blurred, hand in the frame) | 2.7 % flips, 7.6 % review, 1 of 900 accepted | review; raise `review_confidence` |
| title, figure and very sparse pages | DocLayNet 3.1 % flips; near-empty and logo-dominated pages in the failure gallery | review (most flips are caught) |
| black halftone bands | two benchmark pages flip repeatedly | review |
| dense number tables | before v4.2 (Hough), a few pages were off by 20° at confidence 0.98; the Fourier tilt roughly halved the errors above 5° overall (95 to 51 in 2800 paired cases) | the remaining ones are confident errors (rare) |
| receipts with strongly slanted paper edges | a survey claim that the folded Fourier estimate can be pulled by 4-5°; not reproduced here | |
| blurred, shadowed Tobacco photos | the Fourier estimate was less repeatable than Hough on 7 of 200 cases against each page's own skew | only labelled real photos can settle it |
| whole camera frames where the page is small (a median 12 % of the picture) | 6.4 % flips on 926 SmartDoc frames, 7.6 % on the 420 of [chapter 5](05-comparison.md); the Fourier tilt is within 1° for only 46 % of them (the Hough estimator 56 %), and docTR is right on 27 of the 420 where docangle is wrong | `doc_crop` (opt-in) recovers about 90 % of the within-1° gain a perfect page finder would give and about half of the reduction in flips; review catches most of the rest |

**Confident fine-angle errors exist.** The confidence is the quadrant posterior; it does not see fine-angle uncertainty. A fine-tilt error between 5° and 45° is rare on simulated pages (15 of 6300 cases, 0.2 %, `reports/bench_final_v4_4.json`), but 14 of those 15 were accepted; on real frames it is more frequent (5.2 % of the 926 cut-out SmartDoc frames are 5° to 45° off, `reports/smartdoc_eval_crop_v4_4.txt`). For a hard guarantee on the fine angle, check the straightened page, not the flag.

**Borderline decode differences.** `predict` and `correct` decode differently (grey directly against colour and conversion) and a page near the review threshold can fall on either side.

## 10.4 Operational limits

* PDF: the JPEG fast path is opt-in and guarded, not proven on real scanned PDFs; the byte-token scan can miss a feature that only some pages carry (a kill switch exists).
* GPU memory with an OCR on the same card: the OCR's pool grows with image area; crop white borders (the bundled tool does).
* Determinism: bit-identical for a given input, model files and ONNX Runtime version; a different thread count can change the last digits of a logit.
* Privacy: docangle runs entirely locally and makes no network calls. (`tools/ocr_pipeline.py` uses PaddleOCR, which downloads its models on first use.)

## 10.5 Data, licences and what is published

See [section 3.4](03-models-and-data.md#34-licences-and-what-the-public-repository-contains). In short: the code is MIT; the third-party model is Apache-2.0; the benchmark images of RVL-CDIP, Tobacco, CORD, DocLayNet, FUNSD and SmartDoc are **not** redistributed (scripts download them from their public sources); a private set of 100 Azerbaijani test pages and everything derived from its text (transcripts, ground-truth texts, failure galleries) is **not published**, because the documents' origin is not documented. Results computed on that set (the `az` pool, the OCR study of chapter 7 and the speed measurements, which read its pages) are reported as numbers only and cannot be reproduced by outsiders on the same pages; a synthetic Azerbaijani page generator (`src/synth_docs.py`) is included for experiments of the same shape.

**Weights.** The own classifier and the regressor were trained on data of the kinds listed above, some of it research-use only (Tobacco3482 / RVL-CDIP). Until the maintainer decides otherwise, treat those weights as research-use weights; see [`models/README.md`](../models/README.md).

## 10.6 Responsible use

An orientation estimate is a low-stakes output, but it feeds pipelines that read contracts, invoices and forms. Use `needs_review`; do not rely on the angle alone where a missed page has legal or financial consequences; keep a person in the loop for the pages the system doubts; and measure on your own documents.
