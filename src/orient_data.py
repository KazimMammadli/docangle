"""Data for the 4-way page-orientation classifier.

Pools (all grayscale, upright, long side 1000 px, cached as PNG under data/cache/):
  * real  : Tobacco3482 train/val pages (cleaned of pages PP-LCNet is confident are sideways/flipped)
  * synth : procedural Latin/Azerbaijani office pages (src/synth_docs.py)

A training sample imitates what the classifier sees at inference: the page in one of 4 orientations is
tilted by a random angle in [-45, 45], photographed (desk/white background, light, shadow, blur, noise,
JPEG, keystone, crop), then straightened by the estimated tilt (with ~0.5 deg error) on an expanded
white-border canvas, and squashed to SxS. Label = clockwise orientation class index (0, 90, 180, 270).
"""
from __future__ import annotations

import glob
import os
from multiprocessing import Pool
from typing import List, Optional

import cv2

cv2.setNumThreads(1)  # DataLoader workers must not each spawn a thread pool
import numpy as np
import torch
from torch.utils.data import Dataset

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "cache")
LONG = 1000
SIM_LONG = 640


def _resize_long(g: np.ndarray, long_side: int = LONG) -> np.ndarray:
    h, w = g.shape[:2]
    s = long_side / max(h, w)
    return cv2.resize(g, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA) if s < 1 else g


def _cache_real(args):
    src, dst = args
    if os.path.exists(dst):
        return dst
    g = cv2.imread(src, cv2.IMREAD_GRAYSCALE)
    if g is None:
        return None
    cv2.imwrite(dst, _resize_long(g))
    return dst


def _synth_job(args):
    seed, dst = args
    from .synth_docs import make_page
    if not os.path.exists(dst):
        cv2.imwrite(dst, _resize_long(make_page(np.random.default_rng(seed))))
    return dst


def build_caches(n_synth: int = 6000, n_synth_val: int = 600, workers: int = 12, clean_real: bool = True):
    os.makedirs(CACHE, exist_ok=True)
    out = {}
    with Pool(workers) as pool:
        for split in ("train", "val"):
            d = os.path.join(CACHE, f"real_{split}")
            os.makedirs(d, exist_ok=True)
            jobs = [(f, os.path.join(d, os.path.splitext(os.path.basename(f))[0] + ".png"))
                    for f in sorted(glob.glob(os.path.join(ROOT, "data", "splits", split, "*.jpg")))]
            out[f"real_{split}"] = [r for r in pool.map(_cache_real, jobs, chunksize=8) if r]
        for name, n, base in (("synth_train", n_synth, 1_000_000), ("synth_val", n_synth_val, 9_000_000)):
            d = os.path.join(CACHE, name)
            os.makedirs(d, exist_ok=True)
            jobs = [(base + i, os.path.join(d, f"{i:05d}.png")) for i in range(n)]
            out[name] = pool.map(_synth_job, jobs, chunksize=16)
    if clean_real:
        out["real_dropped"] = _clean_real(out)
    return out


def _clean_real(pools) -> List[str]:
    """Drop pages the pretrained PP-LCNet is >90 % sure are NOT upright (sideways/flipped scans)."""
    from docangle import DocumentOrientationPipeline, PipelineConfig
    pipe = DocumentOrientationPipeline(PipelineConfig(lcnet_tta=True))
    dropped = []
    for key in ("real_train", "real_val"):
        for f in pools[key]:
            g = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
            ccw, score = pipe._coarse(g)[:2]
            if ccw != 0 and score > 0.90:
                dropped.append(f)
                os.replace(f, f + ".dropped")
        pools[key] = [f for f in pools[key] if f not in set(dropped)]
    return dropped


def list_pool(name: str) -> List[str]:
    return sorted(glob.glob(os.path.join(CACHE, name, "*.png")))


# --------------------------------------------------------------------------- #
def _rotate_expanded(img, angle, border=255, interp=cv2.INTER_LINEAR):
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)
    nw = int(np.ceil(h * abs(M[0, 1]) + w * abs(M[0, 0])))
    nh = int(np.ceil(h * abs(M[0, 0]) + w * abs(M[0, 1])))
    M[0, 2] += nw / 2.0 - w / 2.0
    M[1, 2] += nh / 2.0 - h / 2.0
    return cv2.warpAffine(img, M, (nw, nh), flags=interp, borderValue=border)


def make_sample(page: np.ndarray, quadrant_ccw: int, rng: np.random.Generator, bgs: List[np.ndarray],
                size: int = 320, augment: bool = True) -> np.ndarray:
    """Return an SxS uint8 gray image of ``page`` (upright) in orientation ``quadrant_ccw`` (0..3)."""
    g = np.ascontiguousarray(np.rot90(page, quadrant_ccw))
    if max(g.shape) > SIM_LONG:  # simulate at 640 px: the classifier sees a 320 px squash anyway (3x cheaper)
        k = SIM_LONG / max(g.shape)
        g = cv2.resize(g, (int(g.shape[1] * k), int(g.shape[0] * k)), interpolation=cv2.INTER_AREA)
    if not augment:
        return cv2.resize(g, (size, size), interpolation=cv2.INTER_AREA)
    tilt = float(rng.uniform(-45, 45))
    # --- photograph it
    if rng.random() < 0.3:  # mild keystone
        h, w = g.shape
        d = float(rng.uniform(0, 0.05)) * w
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        g = cv2.warpPerspective(g, cv2.getPerspectiveTransform(src, np.float32([[d, 0], [w - d, 0], [w, h], [0, h]])), (w, h), borderValue=255)
    h, w = g.shape
    alpha = np.full((h, w), 255, np.uint8)
    rg = _rotate_expanded(g, tilt, 0)
    ra = _rotate_expanded(alpha, tilt, 0)
    nh, nw = rg.shape
    if rng.random() < 0.65:  # desk / dark background
        m = float(rng.uniform(1.05, 1.4)); ch, cw = int(nh * m), int(nw * m)
        if bgs and rng.random() < 0.7:
            bg = bgs[int(rng.integers(len(bgs)))]
            bh, bw = bg.shape
            if bh < ch or bw < cw:
                bg = cv2.resize(bg, (max(cw, bw), max(ch, bh)))
                bh, bw = bg.shape
            y, x = int(rng.integers(0, bh - ch + 1)), int(rng.integers(0, bw - cw + 1))
            canvas = bg[y:y + ch, x:x + cw].copy()
        else:
            canvas = np.full((ch, cw), int(rng.integers(20, 200)), np.uint8)
        oy, ox = (ch - nh) // 2 + int(rng.integers(-10, 11)), (cw - nw) // 2 + int(rng.integers(-10, 11))
        oy, ox = max(0, min(ch - nh, oy)), max(0, min(cw - nw, ox))
        reg = canvas[oy:oy + nh, ox:ox + nw].astype(np.float32)
        a = ra.astype(np.float32) / 255.0
        canvas[oy:oy + nh, ox:ox + nw] = np.clip(reg * (1 - a) + rg.astype(np.float32) * a * float(rng.uniform(0.85, 1.0)), 0, 255).astype(np.uint8)
        img = canvas
    else:
        img = np.where(ra > 127, rg, 255).astype(np.uint8)
    # lighting gradient / vignette / shadow band: built at 1/8 resolution, upsampled, applied in one multiply
    hh, ww = img.shape
    if rng.random() < 0.7:
        sh_, sw_ = max(4, hh // 8), max(4, ww // 8)
        gx = np.linspace(-0.5, 0.5, sw_, dtype=np.float32)[None, :]
        gy = np.linspace(-0.5, 0.5, sh_, dtype=np.float32)[:, None]
        fac = np.ones((sh_, sw_), np.float32)
        if rng.random() < 0.85:
            ang = float(rng.uniform(0, 6.28))
            fac -= float(rng.uniform(0.05, 0.35)) * (gx * np.cos(ang) + gy * np.sin(ang) + 0.7)
        if rng.random() < 0.4:
            yy, xx = np.mgrid[0:sh_, 0:sw_].astype(np.float32)
            a = float(rng.uniform(0, np.pi)); c0 = float(rng.uniform(0.2, 0.8)) * (sw_ * np.cos(a) + sh_ * np.sin(a))
            dd = (xx * np.cos(a) + yy * np.sin(a) - c0) / (0.08 * max(sh_, sw_))
            fac *= 1.0 - float(rng.uniform(0.1, 0.35)) * np.exp(-dd * dd)
        fac = cv2.resize(fac, (ww, hh), interpolation=cv2.INTER_LINEAR)
        img = np.clip(img * fac, 0, 255).astype(np.uint8)
    if rng.random() < 0.35:
        img = cv2.GaussianBlur(img, (0, 0), float(rng.uniform(0.5, 1.8)))
    if rng.random() < 0.4:
        img = np.clip(img + rng.standard_normal(img.shape, dtype=np.float32) * float(rng.uniform(1, 9)), 0, 255).astype(np.uint8)
    if rng.random() < 0.5:
        img = cv2.imdecode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(30, 95))])[1], cv2.IMREAD_GRAYSCALE)
    # --- straighten with the (slightly wrong) tilt estimate, white border like the pipeline
    img = _rotate_expanded(img, -(tilt + float(rng.normal(0, 0.5))), 255)
    if rng.random() < 0.15:  # a bit of the page cut off
        hh, ww = img.shape
        f_ = float(rng.uniform(0.03, 0.1))
        side = int(rng.integers(4))
        img = [img[int(hh * f_):], img[:hh - int(hh * f_)], img[:, int(ww * f_):], img[:, :ww - int(ww * f_)]][side]
    return cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)


_MEAN, _STD = 0.449, 0.226


class OrientationDataset(Dataset):
    """Infinite-style dataset: each index draws a random page/orientation (seeded per index if ``fixed``)."""

    def __init__(self, pools: List[List[str]], weights: List[float], n: int, size: int = 320,
                 augment: bool = True, fixed_seed: Optional[int] = None, bg_dir: Optional[str] = None):
        self.pools, self.n, self.size, self.augment, self.fixed_seed = pools, n, size, augment, fixed_seed
        w = np.array(weights, float)
        self.weights = w / w.sum()
        bg_dir = bg_dir or os.path.join(ROOT, "data", "backgrounds")
        self.bgs = [b for b in (cv2.imread(f, cv2.IMREAD_GRAYSCALE) for f in sorted(glob.glob(os.path.join(bg_dir, "*.jpg")))) if b is not None]

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        rng = np.random.default_rng([self.fixed_seed, i]) if self.fixed_seed is not None else np.random.default_rng()
        pi = int(rng.choice(len(self.pools), p=self.weights))
        page = cv2.imread(self.pools[pi][int(rng.integers(len(self.pools[pi])))], cv2.IMREAD_GRAYSCALE)
        q = int(rng.integers(4))                 # CCW quadrant applied
        x = make_sample(page, q, rng, self.bgs, self.size, self.augment)
        t = torch.from_numpy(x).float().div_(255.0).sub_(_MEAN).div_(_STD)[None]
        return t, (-q) % 4, pi                   # label: clockwise class index


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Build the cached pools under data/cache/ (real Tobacco3482 pages, synthetic pages); needs data/splits and, for the cleaning step, the PP-LCNet model")
    ap.add_argument("--n-synth", type=int, default=6000, help="synthetic training pages")
    ap.add_argument("--n-synth-val", type=int, default=600, help="synthetic validation pages")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--no-clean", action="store_true", help="skip moving aside the pages PP-LCNet is more than 90 %% sure are not upright")
    a = ap.parse_args()
    out = build_caches(a.n_synth, a.n_synth_val, a.workers, clean_real=not a.no_clean)
    for k, v in out.items():
        print(f"{k}: {len(v)}")


if __name__ == "__main__":
    main()
