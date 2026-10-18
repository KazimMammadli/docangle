"""Our own 4-way page-orientation classifier (ONNX) with rotation voting."""
from __future__ import annotations

import os
import threading
from typing import Sequence

import cv2
import numpy as np

from .errors import ModelNotFoundError
from .regressor import make_session

_MEAN, _STD = 0.449, 0.226


class OrientationClassifier:
    """Input: straightened grayscale page. Output: log-posterior over clockwise classes (0, 90, 180, 270).

    The page is shown in 90-degree rotations (a page of class c rotated CCW by r looks like class c - r), so each
    call is several independent votes; their mean log-probabilities form the score.
    """

    def __init__(self, onnx_path: str, intra_threads: int = 2, allow_spinning: bool = True, provider: str = "cpu"):
        if not os.path.isfile(onnx_path):
            raise ModelNotFoundError(f"orientation model not found: {onnx_path}")
        self.path, self._threads, self._sess, self._lock = onnx_path, intra_threads, None, threading.Lock()
        self._spin = allow_spinning
        self._provider = provider
        self.size = 320

    def _ensure(self):
        if self._sess is None:
            with self._lock:
                if self._sess is None:
                    s = make_session(self.path, self._threads, self._spin, self._provider)
                    shp = s.get_inputs()[0].shape
                    self.size = int(shp[2]) if isinstance(shp[2], int) else 320
                    self._sess = s
        return self._sess

    # ---- the three steps of a call (split so the pipeline can run views on different threads) ------------ #
    def views(self, gray: np.ndarray, ks: Sequence[int]) -> np.ndarray:
        """(len(ks), 1, S, S) float32 network input: the page squashed to SxS, shown rotated CCW by 90*k for each k.

        The page is squashed once and the small image is rotated (not the other way round): same view up to one gray
        level on ~1 % of the pixels, and no rotated copy of the full-size canvas.
        """
        self._ensure()
        g = np.ascontiguousarray(gray)
        small = cv2.resize(g, (self.size, self.size), interpolation=cv2.INTER_AREA)
        x = np.stack([small if k == 0 else np.rot90(small, k) for k in ks])
        return np.ascontiguousarray(((x.astype(np.float32) / 255.0 - _MEAN) / _STD)[:, None])

    def logits(self, x: np.ndarray) -> np.ndarray:
        s = self._ensure()
        return s.run(None, {s.get_inputs()[0].name: x})[0]

    def view_logits(self, gray: np.ndarray, k: int) -> np.ndarray:
        """Logits (1, 4) of the single view rotated by 90*k (one task per view for parallel execution)."""
        return self.logits(self.views(gray, (k,)))

    @staticmethod
    def vote(lg: np.ndarray, ks: Sequence[int], temperature: float = 1.0) -> np.ndarray:
        """Per-view log-softmax, rotation voting and renormalisation -> log-posterior over the 4 clockwise classes."""
        lg = lg / temperature
        lg = lg - lg.max(axis=1, keepdims=True)
        lp = lg - np.log(np.exp(lg).sum(axis=1, keepdims=True))      # per-view log-softmax
        out = np.zeros(4)
        for c in range(4):
            out[c] = np.mean([lp[i][(c - ks[i]) % 4] for i in range(len(ks))])
        out -= np.log(np.exp(out - out.max()).sum()) + out.max()      # renormalise
        return out

    def log_posterior(self, gray: np.ndarray, rots=(0, 1, 2, 3), temperature: float = 1.0) -> np.ndarray:
        if rots is True:
            rots = (0, 1, 2, 3)
        elif rots is False:
            rots = (0,)
        ks = tuple(rots)
        return self.vote(self.logits(self.views(gray, ks)), ks, temperature)
