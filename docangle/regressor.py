"""ONNX wrapper for the global [sin, cos] angle regressor (fallback model)."""

from __future__ import annotations

import math
import os
import threading
from typing import Optional

import cv2
import numpy as np

from .errors import ModelNotFoundError

_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
# (x / 255 - mean) / std  ==  x * SCALE + BIAS
_SCALE = (1.0 / (255.0 * _IMAGENET_STD)).astype(np.float32)
_BIAS = (-_IMAGENET_MEAN / _IMAGENET_STD).astype(np.float32)


_CUDA_LIBS = ("libcudart.so.12", "libcublas.so.12", "libcublasLt.so.12", "libcufft.so.11", "libcurand.so.10", "libcudnn.so.9")
_cuda_lock = threading.Lock()
_cuda_libs_ready = False


def _preload_cuda_libs() -> None:
    """Make the pip-installed CUDA libraries visible to ONNX Runtime GPU (once per process).

    onnxruntime-gpu before 1.21 finds libcudnn, libcublas ... only on the dynamic loader's search path, but the pip packages (nvidia-cudnn-cu12,
    nvidia-cublas-cu12, ...) put them in site-packages/nvidia/*/lib, which is not on it, and the CUDA provider then fails to load. Each library that
    cannot be found on the normal path (LD_LIBRARY_PATH, system CUDA) is loaded from there by its full path; libraries that are already reachable are left alone.
    """
    global _cuda_libs_ready
    with _cuda_lock:
        if _cuda_libs_ready:
            return
        _cuda_libs_ready = True
        import ctypes
        import glob
        try:
            import nvidia
        except ImportError:
            return
        dirs = [d for p in nvidia.__path__ for d in sorted(glob.glob(os.path.join(p, "*", "lib")))]
        for name in _CUDA_LIBS:
            try:
                ctypes.CDLL(name)
                continue
            except OSError:
                pass
            for d in dirs:
                if os.path.isfile(os.path.join(d, name)):
                    try:
                        ctypes.CDLL(os.path.join(d, name), mode=ctypes.RTLD_GLOBAL)
                    except OSError:
                        pass
                    break


def make_session(path: str, intra_threads: int, allow_spinning: bool = True, provider: str = "cpu"):
    """Create an ONNX Runtime session (CPU, or CUDA with ``provider="cuda"``) with the options actually applied."""
    import onnxruntime as ort

    if not os.path.isfile(path):
        raise ModelNotFoundError(f"ONNX model not found: {path}")
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opts.intra_op_num_threads = int(intra_threads)
    opts.inter_op_num_threads = 1
    if not allow_spinning:                   # idle ONNX threads sleep instead of busy-waiting: same results, far less CPU when pages run in parallel
        opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        opts.add_session_config_entry("session.inter_op.allow_spinning", "0")
    if provider == "cuda":
        if "CUDAExecutionProvider" not in ort.get_available_providers():
            raise ModelNotFoundError("ort_provider='cuda' needs the GPU build of ONNX Runtime (pip install onnxruntime-gpu) and the CUDA 12 libraries")
        _preload_cuda_libs()
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    else:
        providers = ["CPUExecutionProvider"]
    session = ort.InferenceSession(path, sess_options=opts, providers=providers)
    if provider == "cuda" and "CUDAExecutionProvider" not in session.get_providers():       # ORT falls back to the CPU silently when a CUDA library is missing
        raise ModelNotFoundError("ort_provider='cuda': ONNX Runtime could not load its CUDA provider (needs CUDA 12 and cuDNN 9 libraries: "
                                 "pip install nvidia-cudnn-cu12 nvidia-cublas-cu12 nvidia-cuda-runtime-cu12 nvidia-cufft-cu12 nvidia-curand-cu12, or put them on LD_LIBRARY_PATH)")
    return session


class AngleRegressor:
    """Global 360-degree regressor: image -> angle in [-180, 180] (CCW positive)."""

    def __init__(self, onnx_path: str, intra_threads: int = 2, allow_spinning: bool = True, provider: str = "cpu"):
        if not os.path.isfile(onnx_path):
            raise ModelNotFoundError(f"ONNX model not found: {onnx_path}")
        self.onnx_path = onnx_path
        self._intra_threads = intra_threads
        self._spin = allow_spinning
        self._provider = provider
        self._session = None
        self._input_name: Optional[str] = None
        self._size = 256
        self._lock = threading.Lock()

    def _ensure(self):
        if self._session is None:
            with self._lock:
                if self._session is None:
                    sess = make_session(self.onnx_path, self._intra_threads, self._spin, self._provider)
                    info = sess.get_inputs()[0]
                    shape = info.shape
                    # shape is [batch, 3, H, W]; H/W are ints for this model
                    self._size = int(shape[2]) if isinstance(shape[2], int) else 256
                    self._input_name = info.name
                    self._session = sess
        return self._session

    @property
    def input_size(self) -> int:
        self._ensure()
        return self._size

    def _blob(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        resized = cv2.resize(img, (self._size, self._size), interpolation=cv2.INTER_LINEAR)
        rgb = resized[:, :, ::-1].astype(np.float32)
        norm = rgb * _SCALE + _BIAS
        return np.ascontiguousarray(norm.transpose(2, 0, 1)[None], dtype=np.float32)

    def predict(self, img: np.ndarray) -> float:
        """Angle in degrees, [-180, 180]. `img` must be uint8 gray/BGR/BGRA."""
        sess = self._ensure()
        out = sess.run(None, {self._input_name: self._blob(img)})[0][0]
        return float(math.degrees(math.atan2(float(out[0]), float(out[1]))))
