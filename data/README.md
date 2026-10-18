# data/

Everything under `data/cache/`, `data/external/` and `data/splits/` is git-ignored and rebuildable (scripts named below).

## Benchmark and training pools

| Folder / pool | What | Provenance | Role |
|---|---|---|---|
| `splits/{train,val,test}` | Tobacco3482 (HF `maveriq/tobacco3482`), stratified 80/10/10, seed 42 | public research dataset; `python data/download_samples.py` (~3 GB) | source of `real_train/val` and of `tobacco_cert` |
| `certified_upright_test.json` | 159 Tobacco test pages believed upright | filtered with Hough + PP-LCNet — the **same models the pipeline uses**, so biased toward easy pages; not independent ground truth | benchmark pool `tobacco_cert` |
| `az_test_pages/` | 100 PNG pages (150 dpi) of born-digital Azerbaijani documents | **private: the origin and licence of the source documents are not documented, so these pages are never published and cannot be recreated** | benchmark pool `az`; born-digital, exact ground truth for the angle; results on it are numbers only |
| `invoices_rvl_certified/`, `invoices_rvl_test/` | 100 + 100 RVL-CDIP invoice images | public research dataset | benchmark pool `invoices` (**contains at least one source page that is itself sideways**: `certified_invoice_030`) |
| `cache/rvl_inv_{train,val,heldout}` | RVL-CDIP invoices (HF `rvl_invoice`), de-duplicated (dHash) against the old test pools and audited, split by page | `src/prep_rvl_invoices.py`, `src/label_audit.py` | training / validation / **held-out** benchmark pool `rvl_heldout` (shares layouts with the training pool: optimistic) |
| `cache/real_{train,val}`, `cache/synth_{train,val}` | Tobacco train/val pages (cleaned), procedural Azerbaijani-flavoured pages | `src/orient_data.py`, `src/synth_docs.py` | classifier training / validation |
| `cache/cord_{train,val}` | CORD v2 *train* split receipts photographed by phone (700 / 100) | `src/prep_external.py training` | classifier training / validation |
| `cache/doclaynet_{train,val}` | DocLayNet-small pages (424 / 80) | same | classifier training / validation |
| `cache/ext_funsd` (199), `cache/ext_cord` (200), `cache/ext_doclaynet` (300) | FUNSD scanned forms, CORD v2 test+validation receipts, DocLayNet-small pages | `src/prep_external.py`, audited with `src/audit_external.py` | **held-out** benchmark pools, never trained on |
| `raw_documents/`, `backgrounds/` | 65 sample docs, 20 background textures | generated / RVL demo | synthetic data generator |
| `external/` | the raw downloads (funsd, cord_v2, doclaynet_small, rvl_invoice, brno_mobile_test) | Hugging Face | **`brno_mobile_test` was a set of 48-px text-line crops, not pages: unusable, deleted 2026-10-11** |

## Label-noise audit — what was found

"Upright" labels in public document datasets are not reliable:

* **RVL-CDIP "invoice"** (a public collection of invoices): a large share of pages are sideways or upside down in the
  source. A model trained on the raw data memorised them. The audit (PP-LCNet and an earlier classifier posteriors, contact sheets
  inspected) moved to `cache/rvl_inv_*_dropped`: 1290 / 74 / 282 pages of the train / val / held-out pools (of 7312 / 400 / 1500).
  The first prep step had already removed 356 near-duplicates of the old test pools and 330 pages PP-LCNet was confident were not upright
  (`reports/rvl_inv_pools.json`).
* **Tobacco3482**: of 2785 train pages 143 were moved to `cache/real_train_dropped` and 55 more carry the suffix `.dropped` (automatic filter in `src/orient_data.py`), 2587 remain; of 348 val pages 21 were moved to `cache/real_val_dropped`, 7 carry the suffix, 320 remain.
* **Benchmark pool `invoices`** still contains a sideways page (`certified_invoice_030`); it appears as 4 "flips" in the step-5 benchmark
  that are actually correct predictions (see `reports/FINAL_REPORT.md`).
* **CORD / DocLayNet / FUNSD**: audited with `src/audit_external.py` (the pipeline is run on the unrotated page; every page called
  rotated by > 8° is inspected by eye). All 46 flagged CORD receipts, and 2 flagged DocLayNet pages, are upright or ambiguous: those are
  model errors, not label errors, and were kept (nothing was dropped). Contact sheets: `reports/audit_ext_*.jpg`.
* Scans have **source skew**: a page counted as "upright" is often 0.3–1° off, which caps the measurable fine-angle accuracy on scan pools.

Dropped files are moved, never deleted.

## Missing and needed

A **real, labelled set of phone photos of the documents you care about** (see [docs/09-usage.md](../docs/09-usage.md), section 9.4). Until it exists, photo accuracy is
only known from simulation (and, for the quadrant, the SmartDoc frames).

**SmartDoc 2015 challenge 1 (`external/smartdoc/`, added 2026-10-11):** real phone video frames with document-corner ground truth. Source: https://github.com/jchazalon/smartdoc15-ch1-dataset (release v2.0.0, `frames.tar.gz` 972 MB, sha256 3acb8be1…ae), CC-BY 4.0 (cite Burie et al., ICDAR 2015). Used only by `bench/smartdoc_eval.py` (FINAL_REPORT §14); not in git.
