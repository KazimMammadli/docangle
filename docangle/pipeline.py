"""Hybrid document orientation pipeline (Fourier tilt mod 90 -> classifiers -> fallback).

Angle convention: CCW-positive degrees in [-180, 180]. A page rotated CCW by
``a`` degrees yields ``angle == a``; ``correct`` rotates by ``-a`` to restore it.

Stages
------
1. Fine tilt mod 90 in [-45, 45]: Fourier radial projection (default) or Hough (v4.1: ``fine_estimator="hough"``).
2. PP-LCNet + own classifier: which of 0/90/180/270 the axis-aligned page is in.
3. Fallback: global regressor when the classifiers are unsure and the tilt is near +-45.
4. Hough mode only: pass 2 (Hough again on the corrected page) removes the residual tilt.
"""

from __future__ import annotations

import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import cv2
import numpy as np

from .errors import ImageReadError, ModelNotFoundError, UndeterminedOrientation
from .docrop import find_document
from .fftskew import FFTSkew
from .orientation import OrientationClassifier
from .regressor import AngleRegressor, make_session

ImageLike = Union[str, "os.PathLike[str]", np.ndarray]

_MODELS_DIR = os.environ.get(
    "DOCANGLE_MODELS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models"),
)

_LCNET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_LCNET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
# (gray / 255 - mean) / std for every gray level and channel: same float32 arithmetic as the direct formula (bit-identical
# result), but one table lookup per pixel instead of five passes over a 4x3x224x224 float array.
_LCNET_LUT = np.stack([(np.arange(256, dtype=np.float32) / 255.0 - m) / s for m, s in zip(_LCNET_MEAN, _LCNET_STD)])
_LCNET_CW_LABELS = (0, 90, 180, 270)  # model classes are clockwise degrees


# --------------------------------------------------------------------------- #
# Config / result types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PipelineConfig:
    """All tunable constants in one hashable place (store it with benchmark results)."""

    working_max_dim: int = 1000
    pass1_strips: int = 1                    # Hough pass 1 in this many parallel horizontal bands (1 = one call; Hough estimator only)
    pass1_max_dim: int = 1000                # Hough pass 1 runs on at most this long side (<= working_max_dim)
    fine_estimator: str = "fft"              # fine tilt: "fft" (Fourier radial projection, no pass 2;
                                             # Hough then runs concurrently only for the line count) or "hough" (v4.1: Hough pass 1 + pass 2)
    fft_size: int = 512                      # canvas of the Fourier estimate
    fft_alarm_deg: float = 0.0               # fft mode: |Hough - Fourier| (mod 90) above this lowers the confidence; 0 = off
    # Fallback rules
    boundary_slope_threshold: float = 25.0   # |hough slope| above this -> near the +-45 ambiguity
    lcnet_score_threshold: float = 0.88      # ... and fused score below this -> ask the regressor
    lcnet_hard_floor: float = 0.60           # fused score (both classifiers) below this always asks the regressor
    disagree_threshold: float = 45.0         # regressor overrides only if it differs by more
    min_lines: int = 8                       # fewer Hough lines -> text-less page path
    axis_estimator: str = "circular"         # pass-1 line-angle estimator: "circular" or "median" (see axis_angle)
    # Hough / edge settings
    adaptive_canny: bool = True
    margin_fraction: float = 0.025           # ignore edges this close to the border
    # Pass 2
    skip_pass2: bool = False                 # speed mode; default favours accuracy
    skip_pass2_min_lines: int = 20
    skip_pass2_min_score: float = 0.85
    skip_pass2_max_slope: float = 32.0
    # Input gates
    min_side: int = 64
    min_std: float = 2.0                     # grey-level std below this = blank page
    # Confidence -> review policy
    confidence_model: str = "posterior"      # "posterior": quadrant posterior minus a fallback penalty (v4.3.0);
                                             # "legacy": 0.55*posterior + 0.45*min(1, lines/80) (v4.1-4.2; use review 0.70 / high 0.85)
    fallback_penalty: float = 0.30           # posterior mode: subtracted when the regressor overrode the classifiers
    high_confidence: float = 0.97
    review_confidence: float = 0.90          # below this -> needs_review
    large_residual_deg: float = 3.0          # pass-2 residual above this is suspicious
    # Coarse classifier
    lcnet_weight: float = 1.0                # weight of PP-LCNet log-posterior in the coarse vote
    orient_weight: float = 1.0               # weight of our own classifier; 0 = run without it (otherwise a missing model is an error)
    orient_temperature: float = 1.0          # calibration temperature of our classifier
    orient_onnx_path: Optional[str] = None
    use_regressor_fallback: bool = True
    ambiguity_flag: bool = False             # model-free: when the fallback TRIGGER fires (low posterior, or tilt near +-45 and posterior < 0.88) but the
                                             # regressor is off, only flag the page (fallback_triggered, penalty, reason AMBIGUOUS_QUADRANT)
    too_few_lines_angle: str = "classifier"  # angle reported for TOO_FEW_LINES pages (always reviewed): "classifier" =
                                             # Fourier tilt + classifier quadrant (v4.3.1), "regressor" = the 360-degree regressor (v4.3)
    lcnet_rots: Tuple[int, ...] = (0, 1, 2, 3)   # which 90-degree rotations PP-LCNet votes over
    lcnet_crops: Tuple[str, ...] = ("center",)   # "center" (PP-LCNet standard crop) and/or "full" (whole page squashed)
    orient_rots: Tuple[int, ...] = (0, 2)        # rotations our classifier votes over (0 and 180 decide flips)
    pdf_long_side: int = 1400                # PDF pages are rendered to this long side (px) before analysis
    reduced_jpeg_decode: bool = True         # decode big JPEG files at 1/2..1/8 scale (analysis uses <= working_max_dim px)
    pdf_fast_path: bool = False              # predict(): take a scanned page's single JPEG directly instead of rendering it (docangle/pdf_fast.py,
                                             # opt-in; DOCANGLE_PDF_FAST=0 disables it; unusual pages always fall back to rendering)
    doc_crop: bool = False                   # photos that show the page small on a desk: find the document first and analyse only that part (docangle/docrop.py,
                                             # model-free, ~3 ms; the angle is the angle of the whole image). Experimental, see reports/FINAL_REPORT.md section 22
    doc_crop_max_area: float = 0.25          # the document region counts only if it covers less than this share of the image (a page that fills the frame is left alone;
                                             # 0.25 = tuned on SmartDoc, where pages cover a median 11.7 % of the frame, 5th-95th percentile 7.2-16.2 %; 0.6 also touches normal pages)
    lcnet_tta: bool = True                   # vote over the rotations in lcnet_rots (default 4 x the centre crop); False = a single view
    # Runtime
    parallel_classifiers: bool = True        # run PP-LCNet and our classifier concurrently (ORT releases the GIL)
    speculative_pass2: bool = True           # run the pass-2 Hough on the straightened page WHILE the classifiers run
    ort_provider: str = "cpu"                # "cpu" (default) or "cuda": run the three ONNX models on the GPU (needs onnxruntime-gpu; the Fourier / Hough / resize
                                             # parts stay on the CPU). Experimental, see reports/FINAL_REPORT.md
    ort_spinning: bool = True                # False: idle ONNX Runtime threads sleep instead of busy-waiting (identical results; together with OpenCV on one
                                             # thread 29-35 % less CPU in batches, reports/cpu_knobs.txt; the CLI uses both for batches)
    ort_intra_threads: int = 2               # ONNX Runtime threads of PP-LCNet and of the regressor
    orient_intra_threads: int = 0            # threads of our classifier (the longest branch); 0 = same as ort_intra_threads
    onnx_path: Optional[str] = None
    lcnet_onnx_path: Optional[str] = None

    def __post_init__(self):
        if self.working_max_dim < 256:
            raise ValueError("working_max_dim must be >= 256")
        if self.fine_estimator not in ("hough", "fft"):
            raise ValueError("fine_estimator must be 'hough' or 'fft'")
        if not 0.0 <= self.review_confidence <= self.high_confidence <= 1.0:
            raise ValueError("need 0 <= review_confidence <= high_confidence <= 1")
        if self.ort_provider not in ("cpu", "cuda"):
            raise ValueError("ort_provider must be 'cpu' or 'cuda'")
        if self.too_few_lines_angle not in ("classifier", "regressor"):
            raise ValueError("too_few_lines_angle must be 'classifier' or 'regressor'")
        if self.confidence_model not in ("posterior", "legacy"):
            raise ValueError("confidence_model must be 'posterior' or 'legacy'")


@dataclass
class Result:
    """Outcome for one page. ``angle`` is None only when ``reason`` explains why."""

    angle: Optional[float]
    confidence: float
    quality: str                  # HIGH_CONFIDENCE | MEDIUM_CONFIDENCE | NEEDS_HUMAN_REVIEW | UNDETERMINED
    needs_review: bool
    reasons: List[str] = field(default_factory=list)
    num_lines: int = 0
    lcnet_score: Optional[float] = None
    fine_tilt: Optional[float] = None       # fine tilt used to straighten the page (Fourier; Hough in v4.1 mode), degrees
    fallback_triggered: bool = False
    pass2_skipped: bool = False
    residual: Optional[float] = None        # pass-2 residual slope, degrees
    posterior: Optional[List[float]] = None  # fused posterior over the 4 clockwise classes (0, 90, 180, 270) of the straightened page
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def normalize_angle(angle: float) -> float:
    """Wrap to [-180, 180)."""
    return (angle + 180.0) % 360.0 - 180.0


def angular_distance(a: float, b: float) -> float:
    """Shortest circular distance in [0, 180]."""
    return abs((a - b + 180.0) % 360.0 - 180.0)


def rotate_image_expanded(img: np.ndarray, angle_deg: float, border_val=255, interpolation: int = cv2.INTER_LINEAR) -> np.ndarray:
    """Rotate CCW by ``angle_deg`` on a canvas large enough to keep every corner (bilinear by default: the analysis path)."""
    h, w = img.shape[:2]
    center = (w / 2.0, h / 2.0)
    M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    bound_w = int(math.ceil(h * abs(M[0, 1]) + w * abs(M[0, 0])))
    bound_h = int(math.ceil(h * abs(M[0, 0]) + w * abs(M[0, 1])))
    M[0, 2] += bound_w / 2.0 - center[0]
    M[1, 2] += bound_h / 2.0 - center[1]
    if img.ndim == 2 or img.shape[2] == 1:
        bv = border_val[0] if isinstance(border_val, (tuple, list)) else border_val
    else:
        bv = border_val if isinstance(border_val, (tuple, list)) else (border_val,) * img.shape[2]
    return cv2.warpAffine(img, M, (bound_w, bound_h), flags=interpolation, borderValue=bv)


def _to_uint8(arr: np.ndarray) -> np.ndarray:
    if arr.dtype == np.uint8:
        return arr
    if arr.dtype == np.uint16:
        return (arr >> 8).astype(np.uint8)
    if arr.dtype == np.bool_:
        return arr.astype(np.uint8) * 255
    if np.issubdtype(arr.dtype, np.floating):
        a = np.nan_to_num(arr.astype(np.float32))
        if a.size and float(a.max()) <= 1.0:
            a = a * 255.0
        return np.clip(a, 0, 255).astype(np.uint8)
    if np.issubdtype(arr.dtype, np.integer):
        return np.clip(arr, 0, 255).astype(np.uint8)
    raise ImageReadError(f"unsupported dtype: {arr.dtype}")


def _to_gray(arr: np.ndarray) -> np.ndarray:
    a = _to_uint8(arr)
    if a.ndim == 2:
        return a
    if a.ndim == 3:
        c = a.shape[2]
        if c == 1:
            return a[:, :, 0]
        if c == 3:
            return cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
        if c == 4:
            return cv2.cvtColor(a, cv2.COLOR_BGRA2GRAY)
    raise ImageReadError(f"unsupported image shape: {arr.shape}")


def _white_for(img: np.ndarray) -> float:
    if img.dtype == np.uint16:
        return 65535
    if np.issubdtype(img.dtype, np.floating):              # same range rule as _to_uint8: 0..1 or 0..255
        return 1.0 if not img.size or float(np.nanmax(img)) <= 1.0 else 255.0
    return 255


def upright(img: np.ndarray, angle: float, expand: bool = True, interpolation: int = cv2.INTER_CUBIC,
            lossless_quarter_turns: bool = True, min_tilt: float = 0.1) -> np.ndarray:
    """Rotate ``img`` by ``-angle`` (white border). Works on uint8/uint16/float, gray or colour.

    This is the image that goes on to an OCR, so it is resampled as little as possible (reports/FINAL_REPORT.md section 20):
      * the part of the correction that is a multiple of 90 degrees is done losslessly (``np.rot90``: same pixels, no resampling);
      * a remaining tilt below ``min_tilt`` degrees (0.1 = the resolution of the angle estimate) is left alone: any resampling blurs the page, and a
        correction smaller than the estimate's own error cannot make it better (the estimate of a flat page is often +-0.01 degrees);
      * a larger remaining tilt (at most 45 degrees) is resampled once, bicubic (one pass keeps about three quarters of the edge sharpness of a
        page, bilinear about half).
    ``lossless_quarter_turns=False, interpolation=cv2.INTER_LINEAR`` reproduces the behaviour of versions before 4.3.2.
    """
    white = _white_for(img)
    if expand and lossless_quarter_turns:
        a = -float(angle)                                  # counter-clockwise rotation to apply
        k = int(round(a / 90.0))
        rest = a - 90.0 * k                                # in [-45, 45]
        out = np.ascontiguousarray(np.rot90(img, k % 4)) if k % 4 else img
        if abs(rest) < max(float(min_tilt), 0.005):        # exact quarter turn, or a tilt too small to correct: no resampling
            return out if k % 4 else np.array(img, copy=True)
        res = rotate_image_expanded(out, rest, border_val=white, interpolation=interpolation)
        if np.issubdtype(res.dtype, np.floating):          # bicubic can overshoot; integer types saturate by themselves
            res = np.clip(res, min(float(img.min()), float(white)), max(float(img.max()), float(white)))
        return res
    if expand:
        return rotate_image_expanded(img, -angle, border_val=white, interpolation=interpolation)
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), -angle, 1.0)
    bv = (white,) * img.shape[2] if img.ndim == 3 else white
    return cv2.warpAffine(img, M, (w, h), flags=interpolation, borderValue=bv)


def _is_pdf(path) -> bool:
    return os.fspath(path).lower().endswith(".pdf")


def _jpeg_size(path) -> Optional[Tuple[int, int]]:
    """(width, height) from the JPEG header without decoding, or None if ``path`` is not a readable JPEG."""
    try:
        with open(path, "rb") as f:
            head = f.read(2)
            if head != b"\xff\xd8":
                return None
            while True:
                b = f.read(1)
                while b and b != b"\xff":
                    b = f.read(1)
                while b == b"\xff":
                    b = f.read(1)
                if not b:
                    return None
                marker = b[0]
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    continue
                seg = f.read(2)
                if len(seg) < 2:
                    return None
                length = int.from_bytes(seg, "big")
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    data = f.read(5)
                    return (int.from_bytes(data[3:5], "big"), int.from_bytes(data[1:3], "big")) if len(data) == 5 else None
                f.seek(length - 2, 1)
    except OSError:
        return None


_REDUCED = {2: cv2.IMREAD_REDUCED_GRAYSCALE_2, 4: cv2.IMREAD_REDUCED_GRAYSCALE_4, 8: cv2.IMREAD_REDUCED_GRAYSCALE_8}


def _read_gray(path, target_long_side: int) -> np.ndarray:
    """Grayscale read; large JPEGs are decoded at 1/2, 1/4 or 1/8 scale (JPEG DCT scaling) as long as the result is
    still >= ``target_long_side`` px, which is all the analysis uses. Saves ~10 ms on a 12 MP phone photo."""
    size = _jpeg_size(path)
    if size is not None:
        f = 1
        while f < 8 and max(size) // (f * 2) >= target_long_side:
            f *= 2
        if f > 1:
            img = cv2.imread(os.fspath(path), _REDUCED[f])
            if img is not None:
                return img
    return _read(path, cv2.IMREAD_GRAYSCALE)


def _read(path, flags) -> np.ndarray:
    img = cv2.imread(os.fspath(path), flags)
    if img is None:
        raise ImageReadError(f"could not read image: {path}")
    return img


# The raster that correct() / render_upright() rotate. IMREAD_UNCHANGED would ignore the EXIF orientation tag, while the grayscale
# read used for the analysis applies it: the angle would then describe a different image than the one that is rotated.
# Colour or grey as stored, 8 or 16 bit, EXIF orientation applied (an alpha channel is dropped).
_READ_RASTER = cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH


def axis_angle(degs: np.ndarray, method: str = "circular") -> float:
    """Dominant orientation of line directions modulo 90 degrees, in [-45, 45).

    "median": median of the values wrapped to [-45, 45): exact and robust while the page is near upright, but it
    breaks when the lines straddle the +-45 wrap (pages tilted about 45 degrees: 18 vs 4-7 errors > 5 degrees
    in 1599 benchmark cases).
    "circular": axial mean on the 90-degree circle (angles multiplied by 4), then a median over the lines within
    10 degrees of it, so the +-45 wrap is harmless. Lines are NOT weighted by length: long edges (page border,
    desk, shadows) are not text lines, and length weighting cost 10-25 points of <=1 degree rate on photos.
    """
    if method == "median":
        return float(np.median((degs + 45.0) % 90.0 - 45.0))
    a = np.radians(4.0 * degs)
    mean = float(np.degrees(np.arctan2(np.sin(a).sum(), np.cos(a).sum())) / 4.0)
    dev = (degs - mean + 45.0) % 90.0 - 45.0
    near = np.abs(dev) <= 10.0
    if near.any():
        mean += float(np.median(dev[near]))
    return float((mean + 45.0) % 90.0 - 45.0)


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #
class DocumentOrientationPipeline:
    """Thread-safe: sessions are created once under a lock; analysis is stateless."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self._onnx_path = self.config.onnx_path or os.path.join(_MODELS_DIR, "document_angle_detector_large.onnx")
        self._lcnet_path = self.config.lcnet_onnx_path or os.path.join(_MODELS_DIR, "pp_lcnet_doc_ori.onnx")
        # The regressor is needed only when the configuration can ask it (fallback on, its angle for TOO_FEW_LINES, or the Hough estimator's early exit);
        # switch all of them off (`use_regressor_fallback=False`) to run without its file. A file that IS needed and is missing is an error.
        cfg = self.config
        needs_regressor = cfg.use_regressor_fallback or cfg.too_few_lines_angle == "regressor" or cfg.fine_estimator != "fft"
        for p in ((self._onnx_path,) if needs_regressor else ()) + (self._lcnet_path,):
            if not os.path.isfile(p):
                raise ModelNotFoundError(
                    f"required model file not found: {p}. Models live in the repository's models/ folder: install with "
                    f"`pip install -e .` from the repository, or point DOCANGLE_MODELS_DIR at a folder containing them."
                    + (" The 360-degree regressor is optional: PipelineConfig(use_regressor_fallback=False) runs without it." if p == self._onnx_path else ""))
        self._regressor = (AngleRegressor(self._onnx_path, self.config.ort_intra_threads, self.config.ort_spinning, self.config.ort_provider)
                           if needs_regressor else None)
        self._lcnet = None
        self._lock = threading.Lock()
        self._pool: Optional[ThreadPoolExecutor] = None
        self._fft = FFTSkew(self.config.fft_size) if self.config.fine_estimator == "fft" else None
        op = self.config.orient_onnx_path or os.path.join(_MODELS_DIR, "orient_cls_v4.onnx")
        if self.config.orient_weight > 0 and not os.path.isfile(op):                  # never continue silently on PP-LCNet alone: it is far less accurate (docs/06 6.5)
            raise ModelNotFoundError(
                f"required model file not found: {op}. The own classifier is part of the default pipeline; see models/README.md, or set "
                f"PipelineConfig(orient_weight=0) to run without it knowingly.")
        self._orient = OrientationClassifier(op, self.config.orient_intra_threads or self.config.ort_intra_threads, self.config.ort_spinning, self.config.ort_provider) if self.config.orient_weight > 0 else None

    # ---- models ---------------------------------------------------------- #
    def _lcnet_session(self):
        if self._lcnet is None:
            with self._lock:
                if self._lcnet is None:
                    sess = make_session(self._lcnet_path, self.config.ort_intra_threads, self.config.ort_spinning, self.config.ort_provider)
                    shp = sess.get_outputs()[0].shape
                    if len(shp) != 2 or shp[1] != 4:
                        raise ModelNotFoundError(f"unexpected PP-LCNet output shape {shp}; expected [N, 4]")
                    self._lcnet = sess
        return self._lcnet

    def _lcnet_view_set(self, gray: np.ndarray) -> Tuple[List[np.ndarray], List[int]]:
        """224x224 uint8 views for every configured rotation x crop, and the rotation each one shows.

        The page is resized once per crop and the small image is rotated (resizing commutes with 90-degree rotation
        up to one gray level on ~1.5 % of the pixels), instead of rotating and resizing the full-size canvas 4 times.
        """
        cfg = self.config
        rots = cfg.lcnet_rots if cfg.lcnet_tta else (0,)
        center = full = None
        if "center" in cfg.lcnet_crops:      # PP-LCNet standard preprocessing: short side 256, centre crop 224
            h, w = gray.shape[:2]
            scale = 256.0 / min(h, w)
            center = cv2.resize(gray, (max(224, round(w * scale)), max(224, round(h * scale))), interpolation=cv2.INTER_LINEAR)
        if "full" in cfg.lcnet_crops:        # whole page squashed
            full = cv2.resize(gray, (224, 224), interpolation=cv2.INTER_AREA)
        views, owner = [], []
        for r in rots:
            if center is not None:
                c = np.rot90(center, r)
                y0, x0 = (c.shape[0] - 224) // 2, (c.shape[1] - 224) // 2
                views.append(c[y0:y0 + 224, x0:x0 + 224])
                owner.append(r)
            if full is not None:
                views.append(np.rot90(full, r))
                owner.append(r)
        return views, owner

    @staticmethod
    def _lcnet_blob(views: List[np.ndarray]) -> np.ndarray:
        """(N, 3, 224, 224) float32 network input from N gray uint8 views."""
        g = np.stack(views)
        return np.ascontiguousarray(np.take(_LCNET_LUT, g, axis=1).transpose(1, 0, 2, 3))

    def _lcnet_logpost(self, gray: np.ndarray) -> np.ndarray:
        """Log-posterior over clockwise classes (0, 90, 180, 270) from PP-LCNet.

        The page is shown in the configured 90-degree rotations and crops. A page of clockwise class c
        looks like class (c - r) when rotated CCW by 90*r, so every view is a vote for c; the mean
        log-probability over views is renormalised.
        """
        sess = self._lcnet_session()
        name = sess.get_inputs()[0].name
        views, owner = self._lcnet_view_set(gray)
        probs = sess.run(None, {name: self._lcnet_blob(views)})[0]
        lp = np.array([np.mean([np.log(probs[i][(c - owner[i]) % 4] + 1e-6) for i in range(len(views))]) for c in range(4)])
        return lp - (lp.max() + np.log(np.exp(lp - lp.max()).sum()))

    def _executor(self) -> ThreadPoolExecutor:
        if self._pool is None:
            with self._lock:
                if self._pool is None:
                    self._pool = ThreadPoolExecutor(max_workers=3)
        return self._pool

    def _coarse(self, gray: np.ndarray) -> Tuple[float, float, np.ndarray]:
        """(CCW degrees in {0,90,180,270}, posterior of that class, posterior vector over CW classes)."""
        cfg = self.config
        if self._orient is not None and cfg.parallel_classifiers:
            fut = self._executor().submit(self._orient.log_posterior, gray, cfg.orient_rots, cfg.orient_temperature)
            lp = cfg.lcnet_weight * self._lcnet_logpost(gray) if cfg.lcnet_weight else 0.0     # weight 0: PP-LCNet is not even run
            lp = lp + cfg.orient_weight * fut.result()
        else:
            lp = cfg.lcnet_weight * self._lcnet_logpost(gray) if cfg.lcnet_weight else 0.0
            if self._orient is not None:
                lp = lp + cfg.orient_weight * self._orient.log_posterior(gray, cfg.orient_rots, cfg.orient_temperature)
        post = np.exp(lp - lp.max())
        post /= post.sum()
        idx = int(np.argmax(post))
        return float((360 - _LCNET_CW_LABELS[idx]) % 360), float(post[idx]), post

    # ---- geometry -------------------------------------------------------- #
    def _hough_lines(self, gray: np.ndarray, max_dim: Optional[int] = None, strips: int = 1) -> np.ndarray:
        """Directions (degrees, any sign) of the straight segments found on ``gray``."""
        cfg = self.config
        max_dim = max_dim or cfg.working_max_dim
        h, w = gray.shape[:2]
        m = max(h, w)
        if m > max_dim:
            s = max_dim / m
            gray = cv2.resize(gray, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)

        if cfg.adaptive_canny:
            v = float(np.median(gray[::8, ::8]))
            lower = int(max(20, min(100, 0.67 * v)))
            upper = int(max(60, min(220, 1.33 * v)))
            if lower >= upper:
                lower, upper = 50, 150
        else:
            lower, upper = 50, 150
        edges = cv2.Canny(gray, lower, upper, apertureSize=3)

        if cfg.margin_fraction > 0:
            sh, sw = edges.shape[:2]
            my = max(4, int(sh * cfg.margin_fraction))
            mx = max(4, int(sw * cfg.margin_fraction))
            edges[:my, :] = 0
            edges[-my:, :] = 0
            edges[:, :mx] = 0
            edges[:, -mx:] = 0

        dim = max(edges.shape[:2])
        full = dim >= 1000
        args = (65 if full else 60, max(30, int(40 * min(dim, 1000) / 1000.0)), 6 if full else 5)
        k = max(1, int(strips))
        if k == 1:
            pts = self._hough_segments(edges, *args)
        else:
            # Parallel horizontal bands (HoughLinesP is single-threaded and the biggest cost; only the angles of the
            # segments are used, so band offsets don't matter). Bands overlap so that a line near a border is whole in one.
            h = edges.shape[0]
            step = -(-h // k)
            ov = 40
            bands = [edges[max(0, i * step - ov):min(h, (i + 1) * step + ov)] for i in range(k)]
            futs = [self._executor().submit(self._hough_segments, np.ascontiguousarray(b), *args) for b in bands[1:]]
            parts = [self._hough_segments(np.ascontiguousarray(bands[0]), *args)] + [f.result() for f in futs]
            pts = np.concatenate(parts)
        if len(pts) == 0:
            return np.empty(0)
        degs = np.degrees(np.arctan2(pts[:, 3] - pts[:, 1], pts[:, 2] - pts[:, 0]))
        return degs[np.abs(np.abs(degs) - 45.0) >= 0.5]  # exact 45 = scanner aliasing artefact

    @staticmethod
    def _hough_segments(edges: np.ndarray, threshold: int, min_len: int, max_gap: int) -> np.ndarray:
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=threshold, minLineLength=min_len, maxLineGap=max_gap)
        if lines is None or len(lines) == 0:
            return np.empty((0, 4))
        return lines.reshape(-1, 4)    # OpenCV 4 returns (N,1,4); OpenCV 5 returns (N,4)

    def _hough_slope(self, gray: np.ndarray, method: Optional[str] = None, max_dim: Optional[int] = None,
                     strips: int = 1) -> Tuple[float, int]:
        """Dominant tilt of the page axes in [-45, 45) (image y-down convention) and the number of lines."""
        degs = self._hough_lines(gray, max_dim, strips)
        if degs.size == 0:
            return 0.0, 0
        return axis_angle(degs, method or self.config.axis_estimator), int(degs.size)

    # ---- core ------------------------------------------------------------ #
    def analyze(self, gray: np.ndarray) -> Result:
        """Analyse an 8-bit single-channel image."""
        t0 = time.perf_counter()
        cfg = self.config
        h, w = gray.shape[:2]
        if min(h, w) < cfg.min_side:
            return self._undetermined("IMAGE_TOO_SMALL", t0)
        if cfg.doc_crop:
            box = find_document(gray, max_area=cfg.doc_crop_max_area)
            if box is not None and min(box[3] - box[1], box[2] - box[0]) >= cfg.min_side:
                gray = gray[box[1]:box[3], box[0]:box[2]]
                h, w = gray.shape[:2]

        m = max(h, w)
        work = cv2.resize(gray, (int(w * cfg.working_max_dim / m), int(h * cfg.working_max_dim / m)),
                          interpolation=cv2.INTER_AREA) if m > cfg.working_max_dim else gray
        if float(work[::2, ::2].std()) < cfg.min_std:
            return self._undetermined("NO_CONTENT", t0)

        reasons: List[str] = []
        hough = None
        if self._fft is not None:
            # Fourier tilt on the critical path; the Hough pass only supplies the line count (and the disagreement alarm),
            # so it runs next to the classifiers.
            # strips=1: band jobs queued on the pool this job runs on could wait for each other forever (3 workers, several pages)
            hough = self._executor().submit(self._hough_slope, work, None, cfg.pass1_max_dim, 1)
            fine_tilt = self._fft.tilt(work)
            slope, n_lines = -fine_tilt, cfg.min_lines
        else:
            slope, n_lines = self._hough_slope(work, max_dim=cfg.pass1_max_dim, strips=cfg.pass1_strips)
            fine_tilt = -slope

        if hough is None and n_lines < cfg.min_lines:
            angle = normalize_angle(self._regressor.predict(work))
            reasons.append("TOO_FEW_LINES")
            return Result(angle=round(angle, 2), confidence=0.40, quality="NEEDS_HUMAN_REVIEW",
                          needs_review=True, reasons=reasons, num_lines=n_lines, fine_tilt=fine_tilt,
                          fallback_triggered=True, pass2_skipped=True,
                          elapsed_ms=(time.perf_counter() - t0) * 1000.0)

        ortho = rotate_image_expanded(work, slope)           # == rotate by -fine_tilt
        # The straightened page differs from `ortho` only by a multiple of 90 degrees, and the Hough residual is
        # taken modulo 90, so it can be measured now, concurrently with the classifiers (saves ~13 ms).
        spec = (self._executor().submit(self._hough_slope, ortho, "median")
                if cfg.speculative_pass2 and not cfg.skip_pass2 and hough is None else None)
        coarse, score, post = self._coarse(ortho)
        chosen = normalize_angle(fine_tilt + coarse)
        gap = 0.0
        if hough is not None:
            h_slope, n_lines = hough.result()
            gap = abs((h_slope - slope + 45.0) % 90.0 - 45.0) if n_lines else 0.0
            if n_lines < cfg.min_lines:
                # Reviewed anyway. The classifier's angle changes only the 6 of 900 benchmark cases that hit this gate: the regressor's
                # angle was a flip in 5 of them, the classifier's in none (reports/FINAL_REPORT.md section 15); the classifiers have already run here.
                angle = chosen if cfg.too_few_lines_angle == "classifier" else normalize_angle(self._regressor.predict(work))
                return Result(angle=round(angle, 2), confidence=0.40, quality="NEEDS_HUMAN_REVIEW",
                              needs_review=True, reasons=["TOO_FEW_LINES"], num_lines=n_lines, fine_tilt=fine_tilt,
                              fallback_triggered=True, pass2_skipped=True,
                              elapsed_ms=(time.perf_counter() - t0) * 1000.0)

        fallback = overridden = False
        ambiguous = score < cfg.lcnet_hard_floor or (abs(slope) > cfg.boundary_slope_threshold and score < cfg.lcnet_score_threshold)
        if cfg.use_regressor_fallback and ambiguous:
            alt = normalize_angle(self._regressor.predict(work))
            if angular_distance(chosen, alt) > cfg.disagree_threshold:
                chosen, fallback, overridden = alt, True, True
                reasons.append("REGRESSOR_OVERRIDE")
        elif cfg.ambiguity_flag and ambiguous:
            fallback = True
            reasons.append("AMBIGUOUS_QUADRANT")

        residual: Optional[float] = None
        skipped = False
        if hough is not None and not overridden:
            final, skipped = chosen, True            # the Fourier estimate is the only fine angle (no pass 2)
        elif (cfg.skip_pass2 and not fallback and n_lines >= cfg.skip_pass2_min_lines
                and score >= cfg.skip_pass2_min_score and abs(slope) <= cfg.skip_pass2_max_slope):
            final, skipped = chosen, True
        else:
            # Hough on the straightened page also repairs pass-1 mistakes larger than 2 degrees. A projection-profile
            # polish was tried and removed: it lost accuracy on photos (reports/FINAL_REPORT.md, "Decisions").
            if spec is not None and not overridden:
                residual, _ = spec.result()          # Hough's (image y-down) sign convention
            else:                                    # regressor override: the frame changed, measure again
                residual, _ = self._hough_slope(rotate_image_expanded(work, -chosen), "median")
            tilt = -residual
            final = normalize_angle(chosen + tilt)

        if cfg.confidence_model == "legacy":
            conf = 0.55 * score + 0.45 * min(1.0, n_lines / 80.0)
            if fallback:
                conf -= 0.20
        else:
            # The line count is NOT part of the confidence: with >= 80 lines it lifted any posterior above the review
            # threshold (reports/FINAL_REPORT.md section 11). Too few lines is handled by the TOO_FEW_LINES gate.
            conf = score - (cfg.fallback_penalty if fallback else 0.0)
        if cfg.fft_alarm_deg > 0 and gap > cfg.fft_alarm_deg:
            conf -= 0.15
            reasons.append("LARGE_FINE_DISAGREEMENT")
        if residual is not None and abs(residual) > cfg.large_residual_deg:
            conf -= 0.15
            reasons.append("LARGE_RESIDUAL")
        if score < cfg.lcnet_hard_floor:
            reasons.append("LOW_LCNET_SCORE")
        conf = round(max(0.0, min(1.0, conf)), 3)

        needs_review = conf < cfg.review_confidence
        quality = ("HIGH_CONFIDENCE" if conf >= cfg.high_confidence
                   else "MEDIUM_CONFIDENCE" if not needs_review else "NEEDS_HUMAN_REVIEW")
        return Result(angle=round(float(final), 2), confidence=conf, quality=quality,
                      needs_review=needs_review, reasons=reasons, num_lines=n_lines,
                      lcnet_score=round(score, 3), fine_tilt=fine_tilt, fallback_triggered=fallback,
                      pass2_skipped=skipped, residual=residual, posterior=[round(float(x), 5) for x in post],
                      elapsed_ms=(time.perf_counter() - t0) * 1000.0)

    @staticmethod
    def _undetermined(reason: str, t0: float) -> Result:
        return Result(angle=None, confidence=0.0, quality="UNDETERMINED", needs_review=True,
                      reasons=[reason], elapsed_ms=(time.perf_counter() - t0) * 1000.0)

    # ---- public API ------------------------------------------------------ #
    def predict(self, image: ImageLike, page: int = 0) -> Result:
        """Full result. Raises ImageReadError for unreadable input.

        ``image`` may be a path (image file, or a ``.pdf`` whose 0-based ``page`` is rendered; needs pypdfium2),
        or a numpy array.
        """
        if isinstance(image, (str, os.PathLike)):
            if _is_pdf(image):
                from .pdf_fast import load_pdf_page_gray
                gray = load_pdf_page_gray(image, page, self.config.pdf_long_side, fast=self.config.pdf_fast_path)
            else:
                gray = (_read_gray(image, self.config.working_max_dim) if self.config.reduced_jpeg_decode
                        else _read(image, cv2.IMREAD_GRAYSCALE))
        elif isinstance(image, np.ndarray):
            gray = _to_gray(image)
        else:
            raise ImageReadError("image must be a path or a numpy array")
        return self.analyze(gray)

    def predict_angle(self, image: ImageLike, page: int = 0) -> float:
        """Angle only. Raises UndeterminedOrientation for blank/too-small pages."""
        res = self.predict(image, page)
        if res.angle is None:
            raise UndeterminedOrientation(res.reasons[0] if res.reasons else "UNKNOWN")
        return res.angle

    def correct(self, image: ImageLike, expand: bool = True, page: int = 0) -> Tuple[Optional[np.ndarray], Result]:
        """Return ``(upright_image, result)``; image is None when the result is UNDETERMINED.

        For a ``.pdf`` path the page is rendered in colour (BGR) at ``pdf_long_side`` px and that raster is returned upright.
        """
        if isinstance(image, (str, os.PathLike)):
            if _is_pdf(image):
                from .pdf import render_pdf_page
                img = render_pdf_page(image, page, self.config.pdf_long_side, color=True)
            else:
                img = _read(image, _READ_RASTER)
        elif isinstance(image, np.ndarray):
            img = image
        else:
            raise ImageReadError("image must be a path or a numpy array")
        res = self.analyze(_to_gray(img))
        if res.angle is None:
            return None, res
        return upright(img, res.angle, expand=expand), res

    def render_upright(self, image: ImageLike, angle: float, expand: bool = True, page: int = 0) -> np.ndarray:
        """Load ``image`` (as ``correct`` does) and rotate it by ``-angle``: for results that were adjusted afterwards (job consensus)."""
        if isinstance(image, (str, os.PathLike)):
            if _is_pdf(image):
                from .pdf import render_pdf_page
                img = render_pdf_page(image, page, self.config.pdf_long_side, color=True)
            else:
                img = _read(image, _READ_RASTER)
        elif isinstance(image, np.ndarray):
            img = image
        else:
            raise ImageReadError("image must be a path or a numpy array")
        return upright(img, angle, expand=expand)

    def correct_image(self, image: ImageLike, expand: bool = True) -> Tuple[np.ndarray, float]:
        """Compatibility helper: ``(upright_image, angle)``; raises if undetermined."""
        out, res = self.correct(image, expand=expand)
        if out is None:
            raise UndeterminedOrientation(res.reasons[0] if res.reasons else "UNKNOWN")
        return out, res.angle

    # ---- batch ----------------------------------------------------------- #
    def predict_batch(self, images: Sequence[ImageLike], max_workers: int = 4) -> List[Result]:
        """Results in input order. Unreadable inputs become UNDETERMINED/UNREADABLE (never abort the batch)."""
        def one(x):
            try:
                return self.predict(x)
            except ImageReadError:          # a missing model or library still raises: it is not a property of one input
                return Result(angle=None, confidence=0.0, quality="UNDETERMINED", needs_review=True,
                              reasons=["UNREADABLE"])
        if len(images) <= 1 or max_workers <= 1:
            return [one(x) for x in images]
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            return list(ex.map(one, images))


    # ---- jobs (multi-page consensus, opt-in) ------------------------------ #
    def predict_job(self, items: Sequence[Any], max_workers: int = 4, consensus: bool = True, eps: float = 0.05) -> List[Result]:
        """Results for the pages of ONE scan job (same document / same pile): ``items`` are paths, arrays or ``(pdf_path, page)`` pairs.

        With ``consensus`` the other pages' orientation is used to settle unsure pages and to flag odd ones
        (``docangle.consensus``). Do not mix unrelated pages in one job (e.g. phone photos turned differently).
        """
        from .consensus import apply_job_consensus

        def one(x):
            try:
                return self.predict(*x) if isinstance(x, tuple) else self.predict(x)
            except ImageReadError:          # a missing model or library still raises: it is not a property of one input
                return Result(angle=None, confidence=0.0, quality="UNDETERMINED", needs_review=True, reasons=["UNREADABLE"])
        if len(items) <= 1 or max_workers <= 1:
            res = [one(x) for x in items]
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                res = list(ex.map(one, items))
        return apply_job_consensus(res, self.config, eps) if consensus else res

    def predict_pdf(self, path: Union[str, "os.PathLike[str]"], consensus: bool = True, eps: float = 0.05,
                    max_workers: int = 4) -> List[Result]:
        """Every page of a PDF as one job (needs pypdfium2)."""
        from .pdf import pdf_page_count
        return self.predict_job([(path, k) for k in range(pdf_page_count(path))], max_workers, consensus, eps)


# --------------------------------------------------------------------------- #
# Module-level convenience (cache keyed by config, not first-call-wins)
# --------------------------------------------------------------------------- #
_CACHE: Dict[PipelineConfig, DocumentOrientationPipeline] = {}
_CACHE_LOCK = threading.Lock()


def get_pipeline(config: Optional[PipelineConfig] = None) -> DocumentOrientationPipeline:
    cfg = config or PipelineConfig()
    with _CACHE_LOCK:
        if cfg not in _CACHE:
            _CACHE[cfg] = DocumentOrientationPipeline(cfg)
        return _CACHE[cfg]


def predict_document(image: ImageLike, config: Optional[PipelineConfig] = None) -> Result:
    return get_pipeline(config).predict(image)


def predict_document_angle(image: ImageLike, config: Optional[PipelineConfig] = None) -> float:
    return get_pipeline(config).predict_angle(image)


def correct_document(image: ImageLike, expand: bool = True, config: Optional[PipelineConfig] = None):
    return get_pipeline(config).correct_image(image, expand=expand)
