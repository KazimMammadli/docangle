# 8. Speed and deployment

Measured on one laptop (AMD Ryzen 9 5980HX, 8 cores / 16 threads, 15 GB RAM, NVIDIA RTX 3060 Laptop GPU with 6 GB, Fedora Linux, a desktop session running, so absolute times are pessimistic), CPU only unless stated, ONNX Runtime with two threads per model. Latency is the wall time of one call including decoding; throughput uses several caller threads on one process. Numbers from other machines will differ in absolute terms; the ratios between profiles are the transferable part.

## 8.1 One page

| input (20 Azerbaijani test pages rescaled, JPEG quality 90, 3 passes) | **total per call, mean** | median | p95 |
|---|---|---|---|
| 1 MP JPEG (about 1000 px) | **35.0 ms** | 35.1 ms | 38.8 ms |
| A4 at 300 dpi JPEG (3508 px) | **43.9 ms** | 43.7 ms | 49.1 ms |
| 12 MP phone JPEG (4032 px) | **44.8 ms** | 44.6 ms | 48.3 ms |

Source: `reports/latency_files_v4_4.txt` (one call to `predict(path)` per file, models warm, 60 calls per row, laptop on mains power, checked before the run; a repeat run gave 35.2, 44.9 and 51.1 ms means, the last with a few slow calls (p95 85.2 ms): `reports/latency_files_v4_4_repeat.txt`). The time split between decoding and analysis was not measured separately this time. A PDF page is rendered first; see 8.3 for 100-page jobs.

Where the time goes (120 simulated photo pages of about 2029 px, one caller thread, median milliseconds, `reports/profile_stages_v4_4.txt`): Fourier tilt 4.5, straightening 0.6, PP-LCNet 10.2 for the 4 views plus 1.6 for views and input blob, own classifier 15.3 for the 2 views plus 3.0 for the views, Hough line count 15.4 in a parallel thread, resize to the 1000 px canvas 1.2 (mean). The two classifiers and the Hough count run concurrently: the classifiers take 18.8 ms and the whole analysis **26.9 ms** of wall time (mean 27.7, p95 34.3). The own classifier is the longest branch.

Start-up (fresh process, median of 3): `import docangle` 80 ms, each ONNX session 70-86 ms (created lazily on first use), the first prediction 105.5 ms and the second 28.5 ms, the CLI for one image 0.27 s.

## 8.2 Many pages

* **Throughput** with 4 caller threads: 46.6 pages/s against 35.7 with one (a factor of 1.30; 2 threads already give 44.8, more threads do not help because the pipeline already uses several cores per page; `reports/profile_stages_v4_4.txt`, in-memory pages).
* **CPU use.** Idle ONNX and OpenCV threads busy-wait by default, so a page costs about 178 ms of process CPU time for 27 ms of wall time (`reports/profile_stages_v4_4.txt`). The CLI therefore switches, for batches, to lean settings (`ort_spinning=False`, OpenCV on one thread): **identical angles, confidences and review flags on all 96 pages tested**. CPU time per page fell from 186 to 86 ms with one caller (−54 %) and from 240 to 157 ms with four (−35 %) on 100 simulated pages (`reports/cpu_knobs.txt`); measured end to end on three batch inputs (3 alternating repeats each; results identical on 100, 100 and 176 pages) the total CPU time fell by 35 % (100-page JPEG scan PDF), 29 % (100 PNG pages) and 33 % (176-page text PDF). End-to-end wall time of the batches was unchanged on this 16-thread machine (`reports/FINAL_REPORT.md` §18), while the throughput of in-memory pages with four callers rose from 38.5 to 45.3 pages/s (`reports/cpu_knobs.txt`); on a machine with few cores, where the pipelines compete for cores, a throughput gain is plausible but was **not measured**. Single-page latency gets slower (28.8 to 35.9 ms) with OpenCV on one thread, so lean mode is for batches only.
* **Memory**: the profiling process (several pipelines, up to 8 caller threads, 120 pages in two passes) peaked at 1576 MB resident; a single pipeline needs less, but it was not measured separately.

## 8.3 PDF

* PDFium is not thread-safe: all PDFium calls are serialised by one lock (a bug found by timing a 100-page PDF with four threads: without the lock the process crashed or returned unreadable pages). The analysis of the pages still runs in parallel.
* 100-page PDFs, end to end, 4 workers: born-digital text PDF **2.5 s** (25 ms per page); scanned A4 at 300 dpi **8.3 s** (a synthetic zlib-compressed scan PDF, in-process, an earlier run; 83 ms per page, render-bound: decoding and scaling a 2480 × 3508 image takes 100-160 ms in PDFium, one at a time).
* **JPEG fast path** (`pdf_fast_path=True` or `--pdf-fast`, opt-in): a scanned page that is one full-page JPEG is decoded directly at reduced scale outside the lock instead of rendered. A synthetic 100-page 300-dpi JPEG-scan PDF: CLI **6.9 s to 2.7 s** including start-up (a Flate-compressed scan PDF of 100 pages, not eligible, takes 6.62 s without and 6.65 s with the switch: `reports/FINAL_REPORT.md` §17). Pages that are not a plain full-page JPEG (text PDFs, Flate or 1-bit scans, annotations, masks, soft edges, `/Decode` tricks) fall back to rendering, guarded by a byte-token scan of the file and a one-page canary. On 560 benchmark pages with known angles the angles differ by at most 0.05° on 98 % of pages and no new accepted flip appeared. It stays off by default until `python -m bench.pdf_equiv` has been run on your own scanned PDFs; `DOCANGLE_PDF_FAST=0` switches it off globally.

## 8.4 GPU

`PipelineConfig(ort_provider="cuda")` runs the three ONNX models on the GPU (needs `onnxruntime-gpu` and the CUDA 12 / cuDNN 9 libraries; the pip packages `nvidia-cudnn-cu12`, `nvidia-cublas-cu12` and so on are found without `LD_LIBRARY_PATH`). Results are identical: on 120 pages the angle is the same to 0.01° on all of them, the review flags identical, the largest confidence difference 0.0000. One page: median **38.6 to 16.8 ms**, process CPU time per page **226 to 102 ms**, throughput with one / four caller threads **24 to 55 / 18 to 97 pages/s**, 286 MB of GPU memory. The Fourier tilt, the Hough count and the resizing stay on the CPU. The GPU matters when something else (an OCR on the same card) is much faster than about one page per second per process, or when CPU is the scarce resource; for a single page the CPU path is already fast. Default: CPU.

## 8.5 Speed profiles (opt-in)

The default keeps every view that measurably helps accuracy. Faster profiles exist; their accuracy cost was measured on simulated pools and is within noise there but is **not proven on real photos**, so none is the default (times and throughput from `reports/FINAL_REPORT.md` §15, measured earlier on a busy desktop, load average about 7.5, so they are not comparable with 8.1):

| profile | config | mean ms | pages/s (4 workers) | accepted flips at equal review rate |
|---|---|---|---|---|
| default | | 34.2 | 47.1 | 5 |
| own classifier 1 view | `orient_rots=(0,)` | 30.1 (−12 %) | 61.7 (+31 %) | 4 (non-inferior) |
| PP-LCNet 2 views + own 1 view | `lcnet_rots=(0, 2), orient_rots=(0,)` | 27.9 (−17 %) | 70.7 (+49 %) | 7 (+2, borderline) |
| PP-LCNet removed | `lcnet_weight=0` | 31.0 (−9 %) | 56.1 (+19 %) | 12 (**+7**, interval +1..+15: not recommended) |
| minimal: PP-LCNet removed + own 1 view | | 27.5 (−20 %) | 76.6 (+63 %) | not measured separately |

The percentages of the third row are relative to the default of the run that measured its two values (33.6 ms, 47.3 pages/s; `reports/FINAL_REPORT.md` §15); the other rows use the default row of the table.

Removing PP-LCNet saves little per page because it runs in parallel with the longer own classifier, and it costs safety. Static int8 quantisation of the two classifiers made the pipeline slower on this CPU (29.7 to 40.3 ms) and less accurate (flips 4 to 11 in 400 cases), so it is not offered; the decision log ([11.5](11-decisions.md)) has the numbers. Other quantisation settings (7-bit activation ranges, signed activations) and CPUs with int8 dot-product instructions (AVX-512 VNNI or newer) were not tried, and could change both results. An 800-px working canvas would save 6 ms and was rejected by the accuracy guard (only 44.6 % of angles stayed within 0.05°).

## 8.6 Sizing a deployment

* One process analyses 36 pages per second with one caller thread and 44 to 47 with two or more (in-memory pages, `reports/profile_stages_v4_4.txt`), far more than any OCR downstream consumes: PaddleOCR on a GPU reads about one page per second, Tesseract one page per 1.8 s with one thread (`reports/ocr_pipeline_eval_tesseract.txt`: 1778 ms of OCR per page). Run docangle on the CPU, up to two pages ahead of the OCR (`tools/ocr_pipeline.py` does this); move it to the GPU only if the CPU is the bottleneck.
* For a folder of scans use `python -m docangle folder/ --json --threads 4`; for a PDF `--page all`; add `--consensus` when the pages of one file share their orientation.
* Plan for the *review queue*, not the speed: 0.7 % of simulated clean scans of the primary pools (1.1 % over scan and both photo levels, `reports/FINAL_TABLES_v4_4.md`) and 7.6 % of simulated receipt photographs (mean over three levels) go to review.
