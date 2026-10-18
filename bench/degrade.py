"""Seeded phone-photo / scanner degradation simulator with exact ground truth.

Ground truth is the CCW rotation angle applied to an upright page (same convention as docangle).
Keystone perspective is applied *before* rotation and is left/right symmetric, so it does not bias
the mean text direction; the label stays well defined.
"""
from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from typing import Dict

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BG_CACHE: Dict[str, np.ndarray] = {}


@dataclass(frozen=True)
class Level:
    name: str
    desk_prob: float          # page on a desk texture (else scanner bed)
    keystone_max: float       # fraction of width the top edge may shrink per side
    crop_prob: float          # part of the page cut off by the frame
    light_prob: float         # gradient / vignette / tint
    shadow_prob: float        # soft shadow band across the page
    blur_prob: float
    noise_max: float
    jpeg_min: int
    lowres_prob: float        # simulate a small/old phone image
    black_border_prob: float  # scanner lid / dark frame


LEVELS = {
    # Clean rotation of a scan on white: what the old benchmarks measured.
    "scan": Level("scan", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 95, 0.0, 0.0),
    "photo_easy": Level("photo_easy", 0.6, 0.02, 0.0, 0.5, 0.2, 0.2, 4.0, 70, 0.1, 0.1),
    "photo_hard": Level("photo_hard", 0.85, 0.06, 0.35, 0.9, 0.5, 0.5, 10.0, 35, 0.35, 0.25),
}


def _backgrounds():
    if not _BG_CACHE:
        for f in sorted(glob.glob(os.path.join(ROOT, "data", "backgrounds", "*.jpg"))):
            im = cv2.imread(f)
            if im is not None:
                _BG_CACHE[f] = im
    return list(_BG_CACHE.values())


def _desk(h: int, w: int, rng: np.random.Generator) -> np.ndarray:
    bgs = _backgrounds()
    if bgs and rng.random() < 0.8:
        bg = bgs[int(rng.integers(len(bgs)))]
        bh, bw = bg.shape[:2]
        s = max(h / bh, w / bw, 1.0)
        if s > 1.0:
            bg = cv2.resize(bg, (int(bw * s) + 1, int(bh * s) + 1))
            bh, bw = bg.shape[:2]
        y = int(rng.integers(0, bh - h + 1)); x = int(rng.integers(0, bw - w + 1))
        out = bg[y:y + h, x:x + w].copy()
        if rng.random() < 0.5:
            out = out[:, ::-1].copy()
        return out
    color = rng.integers(40, 200, size=3)
    noise = rng.normal(0, 5, (h, w, 3))
    return np.clip(color + noise, 0, 255).astype(np.uint8)


def _keystone(img: np.ndarray, frac: float) -> np.ndarray:
    h, w = img.shape[:2]
    d = frac * w
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[d, 0], [w - d, 0], [w, h], [0, h]])
    return cv2.warpPerspective(img, cv2.getPerspectiveTransform(src, dst), (w, h),
                               borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))


def _motion_kernel(k: int, ang: float) -> np.ndarray:
    ker = np.zeros((k, k), np.float32)
    ker[k // 2, :] = 1.0
    m = cv2.getRotationMatrix2D((k / 2 - 0.5, k / 2 - 0.5), ang, 1.0)
    ker = cv2.warpAffine(ker, m, (k, k))
    return ker / max(ker.sum(), 1e-6)


def render(page: np.ndarray, angle: float, level: Level, rng: np.random.Generator) -> np.ndarray:
    """Return a degraded BGR uint8 image of ``page`` rotated CCW by ``angle`` degrees."""
    page = page if page.ndim == 3 else cv2.cvtColor(page, cv2.COLOR_GRAY2BGR)
    long_side = int(rng.integers(900, 2000))
    h0, w0 = page.shape[:2]
    s = long_side / max(h0, w0)
    page = cv2.resize(page, (max(64, int(w0 * s)), max(64, int(h0 * s))),
                      interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)

    if level.keystone_max > 0 and rng.random() < 0.7:
        page = _keystone(page, float(rng.uniform(0.0, level.keystone_max)))

    h, w = page.shape[:2]
    rgba = np.dstack([page, np.full((h, w), 255, np.uint8)])
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)
    nw = int(np.ceil(h * abs(M[0, 1]) + w * abs(M[0, 0])))
    nh = int(np.ceil(h * abs(M[0, 0]) + w * abs(M[0, 1])))
    M[0, 2] += nw / 2.0 - w / 2.0
    M[1, 2] += nh / 2.0 - h / 2.0
    rot = cv2.warpAffine(rgba, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    rgb, alpha = rot[:, :, :3].astype(np.float32), rot[:, :, 3:4].astype(np.float32) / 255.0

    desk = rng.random() < level.desk_prob
    if desk:
        m = float(rng.uniform(1.08, 1.45))
        ch, cw = int(nh * m), int(nw * m)
        canvas = _desk(ch, cw, rng).astype(np.float32)
        oy = int(rng.integers(int((ch - nh) * 0.3), int((ch - nh) * 0.7) + 1))
        ox = int(rng.integers(int((cw - nw) * 0.3), int((cw - nw) * 0.7) + 1))
        sh = cv2.GaussianBlur(alpha[:, :, 0], (0, 0), 6)
        dy, dx = int(rng.integers(4, 12)), int(rng.integers(4, 12))
        y1, y2, x1, x2 = oy + dy, min(ch, oy + nh + dy), ox + dx, min(cw, ox + nw + dx)
        canvas[y1:y2, x1:x2] *= (1.0 - 0.45 * sh[:y2 - y1, :x2 - x1])[:, :, None]
        reg = canvas[oy:oy + nh, ox:ox + nw]
        canvas[oy:oy + nh, ox:ox + nw] = reg * (1 - alpha) + rgb * alpha
    else:
        canvas = np.full((nh, nw, 3), 245.0, np.float32)
        canvas = canvas * (1 - alpha) + rgb * alpha
        ch, cw = nh, nw
    img = canvas

    if rng.random() < level.shadow_prob:
        yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
        a = float(rng.uniform(0, np.pi)); c0 = float(rng.uniform(0.2, 0.8)) * (cw * np.cos(a) + ch * np.sin(a))
        d = (xx * np.cos(a) + yy * np.sin(a) - c0) / (0.08 * max(ch, cw))
        img = img * (1.0 - float(rng.uniform(0.15, 0.4)) * np.exp(-d * d))[:, :, None]

    if rng.random() < level.light_prob:
        yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
        a = float(rng.uniform(0, 2 * np.pi))
        g = (xx / cw - 0.5) * np.cos(a) + (yy / ch - 0.5) * np.sin(a)
        img = img * (1.0 - float(rng.uniform(0.1, 0.4)) * (g + 0.7))[:, :, None]
        r2 = ((xx / cw - 0.5) ** 2 + (yy / ch - 0.5) ** 2)
        img = img * (1.0 - float(rng.uniform(0.0, 0.5)) * r2)[:, :, None]
        img = img * rng.uniform(0.92, 1.08, size=3)[None, None, :]
    img = np.clip(img, 0, 255).astype(np.uint8)

    if rng.random() < level.crop_prob:
        for _ in range(int(rng.integers(1, 3))):
            side = int(rng.integers(4)); f = float(rng.uniform(0.03, 0.12))
            hh, ww = img.shape[:2]
            if side == 0: img = img[int(hh * f):]
            elif side == 1: img = img[:hh - int(hh * f)]
            elif side == 2: img = img[:, int(ww * f):]
            else: img = img[:, :ww - int(ww * f)]

    if rng.random() < level.black_border_prob:
        t = int(rng.integers(6, 30)); img = cv2.copyMakeBorder(img, t, t, t, t, cv2.BORDER_CONSTANT, value=(15, 15, 15))

    if rng.random() < level.lowres_prob:
        f = float(rng.uniform(0.3, 0.6)); hh, ww = img.shape[:2]
        img = cv2.resize(cv2.resize(img, (int(ww * f), int(hh * f)), interpolation=cv2.INTER_AREA),
                         (ww, hh), interpolation=cv2.INTER_LINEAR)

    if rng.random() < level.blur_prob:
        if rng.random() < 0.5:
            img = cv2.GaussianBlur(img, (0, 0), float(rng.uniform(0.5, 1.6)))
        else:
            img = cv2.filter2D(img, -1, _motion_kernel(int(rng.integers(3, 10)), float(rng.uniform(0, 180))))

    if level.noise_max > 0 and rng.random() < 0.7:
        img = np.clip(img + rng.normal(0, rng.uniform(1, level.noise_max), img.shape), 0, 255).astype(np.uint8)

    if level.jpeg_min < 95:
        q = int(rng.integers(level.jpeg_min, 96))
        img = cv2.imdecode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])[1], cv2.IMREAD_COLOR)
    return img


def sample_angle(mode: str, rng: np.random.Generator) -> float:
    if mode == "uniform":
        return float(np.round(rng.uniform(-180, 180), 2))
    if mode == "quad_tilt":  # a hand-held photo: any of the 4 quadrants, plus a modest tilt
        q = int(rng.integers(4)) * 90.0
        a = q + float(rng.uniform(-25, 25))
        return float(np.round((a + 180.0) % 360.0 - 180.0, 2))
    raise ValueError(mode)
