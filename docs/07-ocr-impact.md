# 7. Effect on OCR

An angle is only useful if it makes text readable. This chapter measures that: first whether ready-made OCR engines already cope with turned pages (they do not), then what putting docangle in front of them gives, then the end-to-end tool that does it in one command. The test pages are 12 born-digital Azerbaijani pages from 5 official documents; the documents are **not redistributable** (origin undocumented), so these tables can be reproduced on your own pages with the same tools but not on the same pages (see [chapter 10](10-limitations.md)). The measurements were made with Tesseract 5.5.3 (`aze`), PaddleOCR 3.7 with the PP-OCRv6 medium models, and EasyOCR 1.7.2.

**Metric.** Word F1 over the multiset of lower-cased, diacritic-folded words, so that it does not depend on reading order; ground truth is the text layer of the born-digital PDFs. Character error rate is also stored but depends on reading order, so only differences between conditions mean anything.

## 7.1 Do OCR engines read turned pages by themselves?

Every page was turned by 0, 5, 15, 30, 45, 90, 135, 180 and 270° (white expanded canvas, counter-clockwise) and read under three conditions per engine: as it is (with each engine's own orientation options, listed below), after docangle straightened it, and after being turned back by the *known* angle (the ceiling for any front end). Word F1 %, mean of the 12 pages:

| condition | 0° | 5° | 15° | 30° | 45° | 90° | 135° | 180° | 270° | mean |
|---|---|---|---|---|---|---|---|---|---|---|
| EasyOCR as is | 98.5 | 84.2 | 96.7 | 91.8 | 70.0 | 5.9 | 4.2 | 2.8 | 6.2 | 51.1 |
| EasyOCR `rotation_info=[90,180,270]` (3.5× slower) | 92.1 | 74.2 | 80.9 | 78.0 | 73.6 | 47.9 | 69.2 | 90.4 | 44.0 | 72.3 |
| **EasyOCR + docangle** | 98.6 | 98.3 | 98.4 | 98.5 | 98.5 | 98.6 | 98.5 | 98.2 | 98.4 | **98.4** (ceiling 98.4) |
| Paddle PP-OCRv6 as is | 99.3 | 99.4 | 99.1 | 99.2 | 99.3 | 6.3 | 6.3 | 6.2 | 99.2 | 68.3 |
| Paddle + its own orientation / unwarping / text-line modules | 98.8 | 97.6 | 93.4 | 56.3 | 45.0 | 98.9 | 33.1 | 98.4 | 98.2 | 79.9 |
| **Paddle + docangle** | 99.3 | 98.9 | 99.1 | 98.9 | 99.0 | 99.3 | 98.9 | 98.8 | 98.7 | **99.0** (ceiling 99.0) |
| Tesseract as is | 96.4 | 95.8 | 1.8 | 0.1 | 0.0 | 2.4 | 0.4 | 2.7 | 97.1 | 33.0 |
| Tesseract + its orientation detection (OSD) | 96.4 | 95.8 | 1.8 | 0.0 | 0.0 | 96.4 | 0.2 | 73.9 | 66.3 | 47.9 |
| Tesseract + the popular recipe (`minAreaRect` deskew + OSD) | 96.4 | 89.9 | 81.7 | 89.6 | 66.0 | 88.6 | 73.6 | 66.1 | 73.5 | 80.6 |
| **Tesseract + docangle** | 96.4 | 97.7 | 97.6 | 97.5 | 97.7 | 96.5 | 97.8 | 97.7 | 97.8 | **97.4** (ceiling 97.4) |

**Findings.** (1) No engine reads every angle. EasyOCR fails on quarter turns and falls to 70 % at 45°. PaddleOCR's text detector reads tilts up to 45° by itself (the claim that modern detectors handle arbitrary angles is *partly* true) but fails at 90°, 135° and 180°, and its built-in orientation modules fix quarter turns but damage tilted pages (56 % at 30°). Tesseract needs the page within a few degrees, and with its OSD (`psm 0`) and the page turned accordingly the word F1 is 73.9 % at 180° and 66.3 % at 270°. (2) With docangle in front **all three engines reach the ceiling at every angle**: the angle was found within 1.5° on 108 of 108 pages and none was sent to review; the step cost 40-44 ms per page. (3) The recipe from popular tutorials (`minAreaRect` + OSD) gives 80.6 % and costs 0.7 s per page more than docangle in front of Tesseract (1.86 s against 1.13 s, `reports/ocr_rotation/all_tables.txt`). (4) Mean seconds per page over the nine angles (`reports/ocr_rotation/all_tables.txt`): Tesseract on one CPU thread 0.92 s as is and 1.86 s with the tutorial recipe, PaddleOCR PP-OCRv6 medium on the GPU 0.69 s, EasyOCR on the GPU 1.96 s (6.88 s with `rotation_info`). (5) PaddleOCR's *mobile* Latin model drops the Azerbaijani letter ə (word F1 48 %); the medium v6 model reads it correctly.

**Limits.** 12 pages from 5 documents, clean (not photographed) rotations, one document family, three engines; no real phone photos; the "as is" modes are the engines' documented or tutorial usage, not an exhaustive tuning effort.

## 7.2 Does the way the page is rotated matter? (v4.3.2)

`correct()` used to rotate with bilinear interpolation everywhere. That kept about half of the page's edge sharpness (one pass: 52-60 % bilinear, 73-77 % bicubic, 77-81 % Lanczos-4; an exact `np.rot90` keeps 100 %) and, worse, re-sampled flat pages whose tilt estimate was ±0.01°. It now turns by multiples of 90° losslessly, leaves tilts under 0.1° alone and resamples larger tilts once with bicubic. The question was whether the OCR cares. Same 12 pages, 9 angles, docangle finds the angle once and the page is straightened with the old and the new rotation; word F1 %:

| engine | untouched page | old rotation | new rotation | new − old, paired over pages [95 % interval] |
|---|---|---|---|---|
| PaddleOCR (GPU), all 9 angles | 99.3 | 99.1 | 99.1 | −0.00 [−0.11, +0.10] |
| Tesseract, all 9 angles | 96.4 | 97.2 | 97.0 | −0.23 [−0.48, −0.05] |

**There is no measurable OCR gain from the sharper image**, and Tesseract reads the new image very slightly worse (−0.2 points, about one word in 400). Tesseract also reads a rotated and resampled page better than the untouched one (+0.6 to +0.8 points): a possible reason is that its input here is 150 dpi while Tesseract's documentation recommends about 300 dpi; this was not tested for OCR (`reports/tesseract_dpi_check.txt` covers only the orientation task). The change is kept as data hygiene (exact quarter turns, flat pages untouched), not as an accuracy gain; `upright(img, angle, interpolation=cv2.INTER_LINEAR, lossless_quarter_turns=False)` restores the old behaviour.

**PDF pages.** For a PDF, `correct()` returns the page as rendered at `pdf_long_side` (1400 px, about 120 dpi for A4). That is enough for the angle (the angle was the same to 0.01° at 1400 and 2480 px on 6 pages, `reports/FINAL_REPORT.md` §20; 3508 px was not checked) but is not an OCR-grade image. For OCR use `PipelineConfig(pdf_long_side=2480)` (about 210 dpi) or `3508` (300 dpi), or take the angle and render the page yourself.

## 7.3 The end-to-end tool

`tools/ocr_pipeline.py` reads a PDF, an image or a folder: docangle finds the angle and the review flag and rotates the page, the OCR reads it. The CPU side (render, angle, rotation) runs up to two pages ahead of the OCR, so the angle step adds no wall time while the OCR is the slower part.

```bash
python -m tools.ocr_pipeline scan.pdf --page all --out out/        # docangle on the GPU + PaddleOCR PP-OCRv6 on the GPU
python -m tools.ocr_pipeline scan.pdf --engine tesseract --docangle-device cpu     # no GPU
python -m tools.ocr_pipeline scan.pdf --no-docangle                # the OCR alone, for comparison
```

It writes `pages.jsonl` (angle, confidence, review flag, text lines, milliseconds per stage), `text.txt` and `summary.json`; pages that need review are read anyway and marked (`--skip-review` leaves them out). The white border that straightening adds is cut before the OCR (`--no-crop` keeps it): a page turned 45° has twice the area afterwards, OCR time follows the area (correlation 0.92 over the 12 pages) and in one uncropped run the 6 GB test GPU ran out of memory.

**Check** (`bench/ocr_pipeline_eval.py`): 12 pages, each turned by a different angle (0, 5, 15, 30, 45, 90, 135, 180, 270, −37, 12 and 200°), written into **one** 150-dpi scanned PDF, read by the tool with and without docangle in front. Word F1 %:

| page angle | 0° | 5° | 15° | 30° | 45° | 90° | 135° | 180° | 270° | −37° | 12° | 200° | mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PaddleOCR alone | 99.4 | 99.9 | 98.7 | 100.0 | 99.5 | 3.1 | 1.9 | 14.3 | 100.0 | 94.9 | 100.0 | 3.3 | **67.9** |
| PaddleOCR + docangle | 99.4 | 99.9 | 99.6 | 100.0 | 98.2 | 100.0 | 98.7 | 99.6 | 100.0 | 94.6 | 100.0 | 100.0 | **99.2** |
| Tesseract alone (CPU) | 97.1 | 96.8 | 9.1 | 0.0 | 0.0 | 1.5 | 0.0 | 8.2 | 100.0 | 0.0 | 0.0 | 0.0 | **26.1** |
| Tesseract + docangle (CPU) | 97.1 | 98.0 | 98.0 | 97.7 | 100.0 | 99.0 | 98.6 | 95.9 | 100.0 | 96.1 | 99.2 | 99.4 | **98.2** |

docangle's angle error: at most 0.02°; no page was sent to review. Timing on the RTX 3060 laptop GPU (PaddleOCR) and one CPU thread (Tesseract): the wall time of every run equals the sum of the OCR times, so the angle step (a median CPU-side time per page of 226 ms with PaddleOCR and 109 ms with Tesseract, including rendering, decoding and rotation, against 55 and 41 ms without docangle: `reports/ocr_pipeline_eval.txt`, `reports/ocr_pipeline_eval_tesseract.txt`) is hidden; one page takes a median 1.1 s of OCR time with PaddleOCR on the GPU and 1.8 s with Tesseract. GPU memory of the whole process: 3.7 GB with the border cropped. Paddle on the CPU took 26 s for one page in this environment: use the GPU, or Tesseract, on machines without one.

**Limits.** Synthetic scan made from 12 clean born-digital pages (not a real scan), one angle per page and no intervals, one machine, no page needed review (the review path was not exercised in this check).
