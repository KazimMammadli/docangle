# 4. Evaluation protocol

A number is only as good as the way it was produced. This chapter states the protocol once; every later table refers to it.

## 4.1 Cases

A **case** is one source page, turned by a known angle and optionally degraded like a photograph, handed to a candidate with no other information. The truth is the angle that was applied.

* **Angle modes.** `uniform`: any angle in [-180°, 180°] (harder than "mostly upright"). `quad_tilt`: a random quadrant plus a tilt of up to ±25° (a hand-held photo, closer to everyday use). Exact quarter turns (`np.rot90`, no resampling) are used for the clean four-class comparison of chapter 5.
* **Degradation levels** (`bench/degrade.py`). `scan`: a clean rotation onto a white canvas. `photo_easy` and `photo_hard`: a desk or textured background, lighting gradients and shadows, keystone, blur, noise, JPEG compression and partial crop; `photo_hard` is the aggressive setting.
* **Ambiguity.** In chapter 5 and in the ablation, cases within 5° of a quadrant boundary (±45°, ±135°) are left out of the quadrant task: there the truth is a matter of convention. The main benchmark of chapter 6.1 counts all cases.
* **Seeds** are derived from the pool, level and case index, so cases are identical across runs and candidates (checked on one machine; not checked across machines).

## 4.2 Pools and what each one can and cannot show

| pool | pages | what | trained on by docangle's own classifier? |
|---|---|---|---|
| `az` | 100 | born-digital Azerbaijani pages (exact ground truth) | not trained on (private, not redistributable); part of the dump on which the review threshold 0.90 was chosen |
| `invoices` | 100 | RVL-CDIP invoices (contains one source page that is itself sideways) | same data family, other pages |
| `tobacco_cert` | 159 | Tobacco test pages believed upright, filtered with models the pipeline uses (biased to easy pages) | same data family, other pages |
| `rvl_heldout` | 300 | RVL-CDIP invoices, audited, split by page; shares layouts with training invoices (optimistic) | same data family, other pages |
| `ext_funsd` | 199 | scanned forms | not trained on; part of the dump on which the review threshold 0.90 was chosen |
| `ext_doclaynet` | 300 | born-digital report and manual pages | same data family (DocLayNet pages), disjoint pages |
| `ext_cord` | 200 | receipts photographed by phone (CORD test + validation) | same data family (CORD train), disjoint pages |
| SmartDoc 2015 CH1 | 926 frames from 150 clips | **real** phone video frames of 30 English documents on 5 backgrounds, with the page corners | not trained on; it informed three decisions: the `TOO_FEW_LINES` gate, keeping the regressor, and the `doc_crop` area limit (chapter 11) |

The rows marked "same data family" are in-domain for docangle's classifier and out-of-domain for third-party models whose training data is unknown: they flatter docangle. Chapter 5 therefore reports the pools nobody trained on (`ext_funsd`, SmartDoc, `az`) separately from the rest.

## 4.3 Metrics

* **Wrong quadrant / flip rate**: share of cases with an error larger than 45°.
* **Accepted flip**: a flip that was not sent to review. This is the number that matters operationally.
* **Within 1° / 0.5°, median error, errors > 5°**: the fine-angle metrics, computed modulo 90° where a method cannot know the quadrant.
* **Review rate** and a **risk-coverage** table (accepted flips against share of pages accepted, as the threshold moves).
* **Latency**: wall time of the whole call, including the candidate's own pre-processing, one case at a time on a warm process; median and 95th percentile in chapters 5 and 8, the mean in the tables of chapter 6; CPU only unless stated.

## 4.4 Statistics

* **Intervals resample pages (or video clips), not cases.** The 3600 simulated cases of the main benchmark are rotations of only 659 distinct pages; the 21 flips of the v4.4 run sat on 9 of them (`reports/page_interval_v4_4.txt`). Treating cases as independent makes the interval much narrower than it should be (0.38-0.89 % at case level against 0.14-1.23 % over pages for the same flip rate); the honest interval is the page-cluster bootstrap (whole pages resampled, 95 %).
* **The comparison of chapter 5 uses a Wilson interval on pages instead.** Its error rates are close to zero, where a bootstrap over pages misbehaves: with no error it collapses to [0, 0], and with one error it is narrower than the honest bound for no error. The interval is the 95 % Wilson interval whose sample size is the number of *pages* (or video clips), each page counted by its share of wrong cases; this is conservative, because the turned or degraded copies of a page are more alike than independent cases would be.
* **Comparisons are paired.** Two candidates are compared on the same cases; the table lists how many cases only one of them got right, and a paired difference with a page-cluster interval is used for decisions.
* **Equal review rate.** Accepted flips are compared at the review rate of the default, because a method that sends more pages to a human trivially has fewer accepted flips.
* **No tuning on reported data.** The single threshold of the review rule (0.90) was chosen on a dump of 6291 cases that overlaps the first rows of one table; the text of every affected table says so. Independent checks (quad_tilt, SmartDoc, DISE-2021) were run after the choice.

## 4.5 Traps found on the way (and handled)

| trap | what happened | what is done |
|---|---|---|
| wrong "upright" labels | a model memorised sideways source pages; a correct prediction counted as a flip | audit every pool; report numbers with and without the known sideways page |
| few distinct pages | intervals over cases were too tight | intervals over pages for the headline rates: a page bootstrap, and a Wilson interval on pages where error rates are near zero (chapter 5); tables that show case-level intervals say so |
| in-sample threshold | the review threshold was tuned on cases that also appear in a table | say so; verify on independent data |
| source skew | scans labelled "upright" are 0.3-1° off | measure each source page unrotated and score against nominal and own skew; report both |
| label-less real data | no labelled phone photos of the target documents | `tools/first_look.py` (label-free checks, contact sheets), `tools/label_server.py` (labelling in a browser) |
| speed changes that move accuracy | a faster variant changed 1 % of angles | `bench/guard.py`: accepted only if ≥ 99 % of angles move by ≤ 0.05°, flips are not higher beyond the interval overlap and the ≤ 1° rate is not lower |

## 4.6 What this protocol cannot show

* How the system behaves on **real phone photos of your documents**: the photographic conditions are simulated, and the only real camera footage is SmartDoc (30 English documents, low-resolution frames); the CORD receipts are phone photographs too, but they are turned and degraded by the simulator.
* Behaviour on scripts other than Latin, on handwriting, on pages with no text.
* Any claim about OCR outcomes beyond the 12-page study of [chapter 7](07-ocr-impact.md).

## 4.7 Reproducibility of a result file

The raw result files of `bench/run.py` store the commit, the configuration, the library versions and the CPU model (`manifest()`); those of the comparison (`reports/benchmark/`) store the library versions, the CPU model and the arguments of the run (`bench/compare_open_models.py versions()`). The case generator is deterministic. The commands that produce each table are in [chapter 12](12-reproduce.md).
