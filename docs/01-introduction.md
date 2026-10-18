# 1. Introduction

## 1.1 The problem

Pages reach a document pipeline turned. A sheet-fed scanner feeds a stack with a few pages upside down; a clerk photographs a contract with a phone held sideways; a PDF produced by a copier carries a `/Rotate` flag that disagrees with the pixels. OCR engines are trained on upright text. Fed a page turned by 90° or 180° most of them return nothing useful; fed a page tilted by 10-20° many return text with many errors. The remedy is to find the rotation first and undo it.

The rotation has two parts with different characters:

* **The quadrant**: which of 0°, 90°, 180°, 270° the page is turned by. It is a *recognition* problem (is this text upside down?), solved by looking at the content, and a mistake is catastrophic.
* **The fine tilt**: the remaining angle in [-45°, 45°). It is a *geometry* problem (which way do the text lines run?), solved by signal processing, and a mistake of a degree or two is harmless for OCR.

Every large error in the history of this project was a quadrant error. That shaped everything else: the design spends its effort on the quadrant decision and on knowing when that decision is shaky.

## 1.2 What docangle returns

```python
from docangle import get_pipeline

r = get_pipeline().predict("page.jpg")      # PDFs: predict("scan.pdf", page=0)
r.angle          # float in [-180, 180], counter-clockwise positive; None if undetermined
r.confidence     # 0..1, the posterior probability of the chosen quadrant (minus a penalty when a fallback acted)
r.needs_review   # True: send this page to a person
r.reasons        # specific causes, e.g. ['TOO_FEW_LINES'], ['LOW_LCNET_SCORE'], ['NO_CONTENT'] (a plain low confidence has no reason code: needs_review is simply True; all codes: chapter 9.2)
r.quality        # 'HIGH_CONFIDENCE', 'MEDIUM_CONFIDENCE', 'NEEDS_HUMAN_REVIEW', 'UNDETERMINED'
```

`correct()` additionally returns the page rotated upright; `python -m docangle` does the same from the command line for images, folders and PDFs. The complete schema is in [appendix A](appendix-a-config.md).

## 1.3 Vocabulary

| term | meaning |
|---|---|
| angle | rotation of the page, counter-clockwise positive; rotate by `-angle` to straighten |
| quadrant | the page's rotation rounded to a multiple of 90° |
| fine tilt | `angle` minus the quadrant, in [-45°, 45°) |
| flip | error > 45° (wrong quadrant) |
| review | the page is sent to a human (`needs_review`) |
| accepted flip | a flip that was not reviewed: the dangerous case |
| pool | a set of source pages used to build benchmark cases |
| case | one source page, rotated by a known angle and optionally degraded |

## 1.4 Scope

**In scope**: Latin-script printed documents (letters, invoices, contracts, forms, reports, receipts) scanned or photographed at any angle; images (JPEG, PNG, TIFF...), numpy arrays and PDF pages; CPU use at tens of milliseconds per page, with an optional GPU path.

**Out of scope, deliberately**:

* *Recognising text.* docangle is not an OCR; chapter 7 measures how much it helps three OCRs.
* *Dewarping curved pages* and perspective correction. A page photographed with strong keystone is rotated, not unwarped.
* *Finding the page in a photo.* By default the page is assumed to fill most of the image; an experimental, opt-in detector (`doc_crop`, chapter 2.9) handles pages that lie small on a desk.
* *Non-Latin scripts and handwriting.* They were not part of the training data or the tests; behaviour on them is unknown.

## 1.5 How it came about

The project began as an audit and rebuild of an earlier pipeline ("C8+L": a Hough-transform fine tilt plus PP-LCNet plus a global regressor, twice). That pipeline flipped 4.5 % of simulated pages and never asked for review. The rebuild kept the architecture's shape (a quadrant classifier plus geometry), added an own classifier trained on audited data, replaced Hough by a Fourier estimate, and replaced an uncalibrated confidence by a parameter-free one. Every step was accepted or rejected by a paired benchmark on identical cases; the full history is in [chapter 11](11-decisions.md) and the lab notebook.
