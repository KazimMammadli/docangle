# docangle: finding how a document page is turned

*A design, evaluation and comparison record of an open-source page-orientation and skew estimator. Version 4.4.0, October 2026.*

`docangle` answers one question about a scanned or photographed page of Latin-script text: **by how many degrees is it rotated**, anywhere between -180° and +180°? It answers with an angle, a confidence and a `needs_review` flag, so that the pages it is unsure about go to a person instead of being guessed. It is a *pre-processing* step for OCR and archiving pipelines, not an OCR.

This book is the complete record behind the code: what the system does and why it is built that way (chapters 1-3), how it was measured and what the numbers say (4-8), how to use and reproduce it (9, 12), where it is weak (10) and which ideas were tried and thrown away (11). Chapter 5 compares it with the other open-source tools that solve parts of the same problem, under identical conditions. Every table names the command that produces it; the inputs can be regenerated from public sources except the private Azerbaijani pages (`az`, also used by the speed measurements and the OCR study) and the `invoices` snapshot (chapter 12).

## Contents

| chapter | what is in it | read it if you want to |
|---|---|---|
| [1. Introduction](01-introduction.md) | the problem, the vocabulary, what is and is not in scope | know whether docangle fits your documents |
| [2. Design](02-design.md) | the pipeline stage by stage, with the formulas and the reasons | understand or change the algorithm |
| [3. Models and data](03-models-and-data.md) | the three models, the training data, the label audit, licences | trust, retrain or redistribute the models |
| [4. Evaluation protocol](04-evaluation-protocol.md) | cases, metrics, statistics, known traps | judge whether the numbers mean what they say |
| [5. Comparison with other open-source tools](05-comparison.md) | a controlled benchmark against 5 orientation tools, with two skew estimators as fine-angle baselines | choose a tool |
| [6. Results](06-results.md) | accuracy, review behaviour, real camera footage, ablations | see the evidence |
| [7. Effect on OCR](07-ocr-impact.md) | three OCR engines with and without docangle; the end-to-end tool | decide whether you need an angle step at all |
| [8. Speed and deployment](08-performance.md) | latency, throughput, CPU and GPU, PDF paths, memory | size a deployment |
| [9. Using docangle](09-usage.md) | install, Python and command-line use, recipes | start |
| [10. Limitations](10-limitations.md) | failure modes, what was never measured, data and licence statement | avoid surprises |
| [11. Decision log](11-decisions.md) | every adopted and rejected experiment, with its evidence | not repeat a failed idea |
| [12. Reproducing the results](12-reproduce.md) | environment, data, commands, run times | verify any claim |
| [Appendix A: configuration](appendix-a-config.md) | every `PipelineConfig` field (generated) | tune |
| [Appendix B: glossary and references](appendix-b-glossary-references.md) | terms and sources | look something up |

The raw lab notebook, written day by day while the work was done, is [`reports/FINAL_REPORT.md`](../reports/FINAL_REPORT.md); this book is the organised version of it, and where the two differ the notebook records the history and this book the final state.

## What is proven and what is not

| claim | evidence | status |
|---|---|---|
| picks the right quadrant on simulated pages of any angle: 0.6 % wrong in 3600 cases, 0 of them accepted by the review rule on pages whose source is itself upright | chapter 6 | measured, simulated photographs |
| the fine tilt is within 1° for 88.2-100.0 % of cases, depending on the pool (seven pools; the ground truth of simulated pages is exact up to the skew of the source scan) | chapter 6 | measured, simulated |
| a real phone camera (SmartDoc, 30 English documents): on the cut-out page the Fourier tilt beats Hough (within 1°: 76.7 % against 64.8 %), on whole frames Hough is ahead (56.4 % against 46.4 %); review flags catch almost all flips | chapter 6 | measured, **small real data set** |
| docangle in front of Tesseract, PaddleOCR or EasyOCR brings each engine to the level of a perfectly straightened page | chapter 7 | measured on **12 clean pages** from 5 documents (not redistributable) |
| fairly compared with the open-source orientation models we could run, docangle is the most accurate on arbitrary angles | chapter 5 | measured, same inputs and hardware |
| works on real phone photos of *your* documents | — | **not measured: no labelled real photos of the target documents exist**; [chapter 9](09-usage.md) shows how to measure it |
| Cyrillic, Arabic-script, CJK, handwriting, A3, ID cards | — | not tested |

## How to cite

See [`CITATION.cff`](../CITATION.cff). If you use the comparison tables, cite the version of the book and the commit of the repository: the raw result files of the main benchmark store the commit and configuration they were produced with, those of the comparison their library versions, CPU model and arguments.

## Conventions used throughout

* **Angle**: counter-clockwise positive, in degrees, in [-180, 180]. A page that was rotated counter-clockwise by *a* has angle *a*; to straighten it, rotate it by *-a*.
* **Quadrant**: which multiple of 90° the page is turned by (0, 90, 180, 270).
* **Flip**: an error larger than 45°, i.e. the wrong quadrant. A flipped page is the costly mistake: OCR reads nothing.
* **Accepted flip**: a flip that was *not* sent to review.
* **Review**: `needs_review == True`.
* Intervals are 95 % intervals over *pages* (a bootstrap, or in chapter 5 a Wilson interval on pages) except where a table says "case-level"; see [chapter 4](04-evaluation-protocol.md).
