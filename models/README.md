# Models

| file | role | size | terms |
|---|---|---|---|
| `pp_lcnet_doc_ori.onnx` | 4-way page orientation (PaddleOCR `PP-LCNet_x1_0_doc_ori`, converted to ONNX, unchanged) | 6.8 MB | Apache-2.0, see `../LICENSES/Apache-2.0-PaddlePaddle.txt` |
| `orient_cls_v4.onnx` | the own 4-way classifier (MobileNetV3-Large, trained here) | 17 MB | **see below** |
| `document_angle_detector_large.onnx` | global 360° regressor, fallback only | 12 MB | **see below** |
| `orient_cls_v1.onnx` | first generation, used only by the data-audit tool | 17 MB | as the own classifier |
| `orient_cls_v4.pt`, `orient_cls_v4_history.json` | training checkpoint (arguments, epoch history) and its history of the own classifier, for retraining and inspection | 17 MB | as the own classifier |

`manifest.json` lists the SHA-256, role and provenance of every weight and history file that is distributed in this folder; `python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" models/FILE` checks one.

## Terms of the own weights

The own classifier and the regressor were trained on pages of Tobacco3482 / RVL-CDIP (derived from IIT-CDIP, **research use only**), CORD v2 (CC-BY-4.0), DocLayNet (CDLA-Permissive-1.0) and procedurally generated pages. Whether the weights are a derivative of research-only data is a legal question this project cannot settle. Until the maintainers state otherwise in the release notes, **use the own weight files (the classifiers `orient_cls_v4` and `orient_cls_v1` and the regressor) for research and evaluation only**; the source code is MIT either way. If you need weights for a commercial purpose, train them on data you may use (`docs/12-reproduce.md`, section 12.7), starting from `src/train_orientation.py`.

The regressor's training run was not preserved (it was trained on synthetic rotations of Tobacco3482 pages in an earlier version of the project); it is a fallback whose flag was set in 63 of 6300 benchmark cases (1.0 %; regressor override or `TOO_FEW_LINES` gate; `reports/bench_final_v4_4.json`) and was found neutral for accepted flips (`docs/11-decisions.md`).

## Using your own copies

`DOCANGLE_MODELS_DIR=/path/to/models` makes docangle read the models from another folder. A missing or unreadable model raises `ModelNotFoundError`; docangle never continues without a model it needs. The 360° regressor is needed only while `PipelineConfig.use_regressor_fallback` is on (the default), with `too_few_lines_angle="regressor"` or with `fine_estimator="hough"`; with `use_regressor_fallback=False` the pipeline runs without that file.
