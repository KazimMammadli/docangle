# Third-party notices

docangle's source code is MIT-licensed (see `LICENSE`). It uses, and in places ships or evaluates, the following third-party material. Nothing here changes the licence of the code.

## Models that are part of the package

| item | licence | notes |
|---|---|---|
| `models/pp_lcnet_doc_ori.onnx` | Apache-2.0 | PaddleOCR / PaddleX `PP-LCNet_x1_0_doc_ori` (Baidu, PaddlePaddle Authors), converted to ONNX without changes. The Apache-2.0 text is in `LICENSES/Apache-2.0-PaddlePaddle.txt`. |
| MobileNetV3-Large ImageNet weights (torchvision) | BSD-3-Clause | initialisation of the own classifier before fine-tuning (the regressor's training run was not preserved); not redistributed on their own |
| `models/orient_cls_v4.onnx`, `models/orient_cls_v4.pt` (training checkpoint), `models/orient_cls_v1.onnx` (first generation, used only by the audit tool), `models/document_angle_detector_large.onnx` | see `models/README.md` | trained for this project on the data sets below; the terms of the weights are stated separately from the code's |

## Libraries (installed, not redistributed)

NumPy (BSD-3-Clause), OpenCV (Apache-2.0), ONNX Runtime (MIT), pypdfium2 and PDFium (BSD-3-Clause / Apache-2.0), Pillow (HPND). Development extras: pytest (MIT), ruff (MIT). Training extras: PyTorch and torchvision (BSD-3-Clause).

## Methods

The fine-tilt estimator follows *Adaptive Radial Projection on Fourier Magnitude Spectrum for Document Image Skew Estimation* (Pham et al., ICIP 2022; the reference code `jdeskew` is MIT-licensed). `docangle/fftskew.py` is an independent implementation and contains no code from that project.

## Data sets (not redistributed; scripts download them from their public sources)

| data set | terms |
|---|---|
| Tobacco3482 and RVL-CDIP (derived from IIT-CDIP) | research use only |
| CORD v2 | CC-BY-4.0 |
| DocLayNet | CDLA-Permissive-1.0 |
| FUNSD | no licence text in the downloaded copy; treated as research-only |
| SmartDoc 2015 challenge 1 | CC-BY-4.0 |
| DISE-2021 | see the data set's own page |

## Software compared in `docs/05-comparison.md` (not redistributed)

DocOrient (MIT), docTR / OnnxTR page-orientation model (Apache-2.0), the EfficientNetV2 orientation model of DuarteBarbosa (MIT), Tesseract (Apache-2.0).
