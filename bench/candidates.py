"""Candidate pipelines under test. Each is a callable: BGR uint8 -> dict(pred, conf, review)."""
import importlib.util
import os
import subprocess
import sys
import tempfile

from docangle import DocumentOrientationPipeline, PipelineConfig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def docangle(**cfg):
    pipe = DocumentOrientationPipeline(PipelineConfig(**cfg))

    def run(img):
        r = pipe.predict(img)
        return {"pred": r.angle, "conf": r.confidence, "review": r.needs_review, "fallback": r.fallback_triggered}
    return run, PipelineConfig(**cfg)


def legacy(tag="archive-production-versions", path="production_versions/v1_c8_large"):
    """Load an archived pipeline from git so refactors can be regression-checked against it."""
    tmp = tempfile.mkdtemp(prefix="legacy_")
    for f in ("pipeline.py", "predict.py"):
        try:
            src = subprocess.check_output(["git", "-C", ROOT, "show", f"{tag}:{path}/{f}"], stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            raise SystemExit(f"the predecessor pipeline (C8+L) is not part of this repository (git tag {tag!r} not found): its stored results are in reports/") from e
        open(os.path.join(tmp, f), "wb").write(src)
    for m in ("document_angle_detector_large.onnx", "pp_lcnet_doc_ori.onnx"):
        os.symlink(os.path.join(ROOT, "models", m), os.path.join(tmp, m))
    sys.path.insert(0, tmp)
    spec = importlib.util.spec_from_file_location("legacy_pipeline", os.path.join(tmp, "pipeline.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pipe = mod.DocumentOrientationPipeline()

    def run(img):
        d = pipe.predict_angle_detailed(img) if hasattr(pipe, "predict_angle_detailed") else None
        if d is not None:
            return {"pred": d["angle"], "conf": d.get("confidence", 1.0), "review": False}
        return {"pred": pipe.predict_angle(img), "conf": 1.0, "review": False}
    return run, {"legacy": "predecessor C8+L (kept outside this repository)"}


REGISTRY = {
    "docangle": lambda: docangle(),
    "docangle_full": lambda: docangle(lcnet_crops=("center", "full"), orient_rots=(0, 1, 2, 3)),
    "docangle_legacyaxis": lambda: docangle(fine_estimator="hough", axis_estimator="median"),
    "docangle_nospec": lambda: docangle(fine_estimator="hough", speculative_pass2=False),
    "docangle_s3": lambda: docangle(fine_estimator="hough", pass1_strips=3),
    "docangle_w800": lambda: docangle(working_max_dim=800),
    "docangle_p1_800": lambda: docangle(fine_estimator="hough", pass1_max_dim=800),
    "docangle_conflegacy": lambda: docangle(confidence_model="legacy", review_confidence=0.70, high_confidence=0.85),   # v4.2.0 confidence rule
    "docangle_tflreg": lambda: docangle(too_few_lines_angle="regressor"),     # v4.3 behaviour for TOO_FEW_LINES pages
    "docangle_hough": lambda: docangle(fine_estimator="hough", confidence_model="legacy", review_confidence=0.70, high_confidence=0.85),       # v4.1.0 default (Hough pass 1 + pass 2)
    "docangle_fft": lambda: docangle(fine_estimator="fft"),           # same as the default since v4.2
    "docangle_fft_alarm": lambda: docangle(fine_estimator="fft", fft_alarm_deg=3.0),   # rejected: fires on correct pages
    "docangle_noreg_flag": lambda: docangle(use_regressor_fallback=False, ambiguity_flag=True),   # no regressor, model-free ambiguity flag
    "docangle_ownonly": lambda: docangle(lcnet_weight=0.0),                          # PP-LCNet not run (our classifier decides the quadrant)
    "docangle_min": lambda: docangle(lcnet_weight=0.0, orient_rots=(0,)),            # minimal: Fourier + our classifier, 1 view
    "docangle_lean": lambda: docangle(ort_spinning=False),                           # batch mode: ONNX threads do not spin
    "docangle_int8": lambda: docangle(orient_onnx_path=os.path.join(ROOT, "models", "experimental", "orient_cls_v4.int8.onnx"),
                                      lcnet_onnx_path=os.path.join(ROOT, "models", "experimental", "pp_lcnet_doc_ori.int8.onnx")),   # static int8 classifiers (bench/quantize_models.py)
    "docangle_crop": lambda: docangle(doc_crop=True),                                # find the document in a photo with much background first (docangle/docrop.py)
    "docangle_crop35": lambda: docangle(doc_crop=True, doc_crop_max_area=0.35),
    "docangle_crop60": lambda: docangle(doc_crop=True, doc_crop_max_area=0.60),
    "docangle_cuda": lambda: docangle(ort_provider="cuda"),                          # the three ONNX models on the GPU (needs onnxruntime-gpu)
    "docangle_or1": lambda: docangle(orient_rots=(0,)),
    "docangle_lc2": lambda: docangle(lcnet_rots=(0, 2)),
    "docangle_lc2or1": lambda: docangle(lcnet_rots=(0, 2), orient_rots=(0,)),
    "docangle_noreg": lambda: docangle(use_regressor_fallback=False),
    "docangle_notta": lambda: docangle(lcnet_tta=False),
    "docangle_fast": lambda: docangle(fine_estimator="hough", skip_pass2=True, working_max_dim=800, lcnet_tta=False),
    "legacy_v1": lambda: legacy(),
}
