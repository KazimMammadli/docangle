# Appendix B: glossary and references

## B.1 Glossary

| term | meaning |
|---|---|
| accepted flip | a flip (wrong quadrant) that was not sent to review |
| accuracy guard | `bench/guard.py`: a speed change is accepted only if at least 99 % of angles move by at most 0.05° and no accuracy metric drops |
| ambiguous case | a case within 5° of a quadrant boundary; left out of the quadrant task |
| angle | rotation of the page, counter-clockwise positive, in [-180°, 180°] |
| case | one source page, rotated by a known angle and optionally degraded |
| CER, word F1 | character error rate; F1 over the multiset of folded words (order independent) |
| cluster bootstrap | an interval from resampling whole pages (or clips) instead of cases |
| Wilson interval on pages | a 95 % interval for a rate whose sample size is the number of pages (or clips), each page counted by its share of wrong cases; sensible even when there are few errors or none (chapter 4.4, used in chapter 5) |
| deskew | removing a small tilt (the fine tilt) |
| fine tilt | the angle modulo 90°, in [-45°, 45°) |
| flip | an error larger than 45°: the wrong quadrant |
| OSD | Tesseract's orientation and script detection |
| pool | a set of source pages used to make benchmark cases |
| quadrant | the page's rotation rounded to a multiple of 90° |
| review | `needs_review == True`: the page goes to a person |
| rotation voting | every 90°-rotated view of a page is an independent vote for the page's class; see chapter 2.6 |
| source skew | the page's own tilt in its source scan, before any rotation was applied |

## B.2 References

These are the works the design, the data and the comparison rest on. Check the bibliographic details against the originals before citing them in a paper; they are given here from the projects' own pages.

**Methods**

* Q. L. Pham et al., *Adaptive Radial Projection on Fourier Magnitude Spectrum for Document Image Skew Estimation*, ICIP 2022 (the method behind the fine tilt; code `jdeskew`; the DISE-2021 data set).
* C. Cui et al., *PP-LCNet: A Lightweight CPU Convolutional Neural Network*, 2021, arXiv:2109.15099 (the backbone of `PP-LCNet_x1_0_doc_ori`).
* A. Howard et al., *Searching for MobileNetV3*, ICCV 2019, arXiv:1905.02244 (the backbone of the own classifier and the regressor).
* R. Smith, *An Overview of the Tesseract OCR Engine*, ICDAR 2007 (Tesseract and its OSD).

**Data sets**

* A. W. Harley, A. Ufkes, K. G. Derpanis, *Evaluation of Deep Convolutional Nets for Document Image Classification and Retrieval* (RVL-CDIP), ICDAR 2015, arXiv:1502.07058.
* S. Park et al., *CORD: A Consolidated Receipt Dataset for Post-OCR Parsing*, NeurIPS 2019 workshop on Document Intelligence.
* B. Pfitzmann et al., *DocLayNet: A Large Human-Annotated Dataset for Document-Layout Analysis*, KDD 2022, arXiv:2206.01062.
* G. Jaume, H. K. Ekenel, J.-P. Thiran, *FUNSD: A Dataset for Form Understanding in Noisy Scanned Documents*, 2019, arXiv:1905.13538.
* J.-C. Burie et al., *ICDAR 2015 Competition on Smartphone Document Capture and OCR (SmartDoc)*, ICDAR 2015 (the SmartDoc challenge-1 frames, github.com/jchazalon/smartdoc15-ch1-dataset).

**Other tools compared in chapter 5**

* PaddleOCR / PaddleX `PP-LCNet_x1_0_doc_ori` (Apache-2.0), github.com/PaddlePaddle/PaddleOCR.
* DocOrient, PyPI `docorient` 0.4.1 (MIT).
* docTR / OnnxTR page-orientation model `mobilenet_v3_small_page_orientation` (Apache-2.0), github.com/mindee/doctr and github.com/felixdittrich92/OnnxTR.
* Hugging Face `DuarteBarbosa/deep-image-orientation-detection`, an EfficientNetV2-S 4-class model (MIT).
* Tesseract 5 OSD, github.com/tesseract-ocr/tesseract.
* Other projects surveyed and not run: rotdet v2 (github.com/fcrescio/rotdet, GPL-3.0), neural-deskew (github.com/dito97/neural-deskew), jdeskew, `deskew` and `hough` on PyPI, olmOCR, Seeing Straight (arXiv:2511.04161, OCR-Rotation-Bench). The survey is [`reports/METHOD_RESEARCH.md`](../reports/METHOD_RESEARCH.md).
