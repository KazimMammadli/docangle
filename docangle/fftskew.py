"""Fine page tilt from the Fourier spectrum (radial projection of the 2-D DFT magnitude, after jdeskew / ICIP 2022).

Text lines and ruling make bright ridges in the magnitude spectrum; the direction with the largest radial sum is the page
axis. The profile is folded modulo 90 degrees (text lines, table rules and vertical strokes all vote for the same axis), so the
result is a tilt in [-45, 45) with no 0/90 ambiguity, like the Hough estimate it is compared with. A 2-D Tukey window over the real
image extent keeps the page border and the desk edges out of the spectrum (without it photos collapse).
"""
from __future__ import annotations

import threading
from typing import Dict, Tuple

import cv2
import numpy as np


class FFTSkew:
    """Thread-safe (the polar maps and windows are built once under a lock, ``angle`` keeps no state)."""

    def __init__(self, size: int = 512, n_angles: int = 1800, low_cut: float = 0.2, agree_deg: float = 0.5,
                 block: int = 11, offset: int = -10, tukey: float = 0.5):
        self.size, self.n_angles, self.agree_deg, self.block, self.offset, self.tukey = size, n_angles, agree_deg, block, offset, tukey
        c, radius = size // 2, size // 2 - 1
        theta = np.arange(n_angles) * np.pi / n_angles
        s = np.arange(1, radius, dtype=np.float64)
        self._mx = (c + s[None, :] * np.cos(theta)[:, None]).astype(np.float32)
        self._my = (c - s[None, :] * np.sin(theta)[:, None]).astype(np.float32)
        self._low = int(low_cut * radius)
        self._windows: Dict[Tuple[int, int], np.ndarray] = {}
        self._lock = threading.Lock()

    def _window(self, h: int, w: int) -> np.ndarray:
        key = (h, w)
        win = self._windows.get(key)
        if win is None:
            def taper(n: int) -> np.ndarray:
                x = np.ones(n)
                m = max(1, int(self.tukey * n / 2))
                r = 0.5 * (1 - np.cos(np.pi * np.arange(m) / m))
                x[:m], x[-m:] = r, r[::-1]
                return x
            win = (taper(h)[:, None] * taper(w)[None, :]).astype(np.float32)
            with self._lock:
                self._windows[key] = win
        return win

    @staticmethod
    def _peak(p: np.ndarray) -> float:
        n = len(p)
        i = int(np.argmax(p))
        y0, y1, y2 = p[(i - 1) % n], p[i], p[(i + 1) % n]
        d = y0 - 2 * y1 + y2
        return i + (0.5 * (y0 - y2) / d if d < 0 else 0.0)

    def tilt(self, gray: np.ndarray) -> float:
        """CCW tilt of the page axes in degrees, in [-45, 45): rotate the page by minus this to straighten it."""
        return self.tilt_ex(gray)[0]

    def tilt_ex(self, gray: np.ndarray):
        """``(tilt, sharpness)``: sharpness = peak / mean of the DC-free folded profile (1 = flat spectrum, no dominant direction)."""
        s = self.size
        h, w = gray.shape[:2]
        if max(h, w) != s:
            k = s / max(h, w)
            gray = cv2.resize(gray, (max(1, int(round(w * k))), max(1, int(round(h * k)))), interpolation=cv2.INTER_AREA)
        x = cv2.adaptiveThreshold(255 - gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                  self.block, self.offset).astype(np.float32)
        x *= self._window(*x.shape)
        padded = np.zeros((s, s), np.float32)
        padded[:x.shape[0], :x.shape[1]] = x
        f = cv2.dft(padded, flags=cv2.DFT_COMPLEX_OUTPUT)
        mag = np.fft.fftshift(cv2.magnitude(f[..., 0], f[..., 1]))
        polar = cv2.remap(mag, self._mx, self._my, cv2.INTER_LINEAR)
        full = polar.sum(1, dtype=np.float64)                    # all radii
        no_dc = polar[:, self._low:].sum(1, dtype=np.float64)    # without the low-frequency core
        half = self.n_angles // 2
        step = 180.0 / self.n_angles

        def to_deg(profile: np.ndarray) -> float:
            return ((self._peak(profile[:half] + profile[half:]) * step + 45.0) % 90.0) - 45.0

        a, b = to_deg(full), to_deg(no_dc)
        folded = no_dc[:half] + no_dc[half:]
        sharp = float(folded.max() / (folded.mean() + 1e-9))
        # the paper's rule: trust the DC-free profile when it agrees with the full one
        return (b if abs((a - b + 45.0) % 90.0 - 45.0) <= self.agree_deg else a), sharp
