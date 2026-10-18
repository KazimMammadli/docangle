"""Turn the external page datasets under data/external into upright-candidate pools under data/cache/ext_*.

    python -m src.prep_external            # funsd (scanned forms), cord_v2 (receipt photos), doclaynet (PDF page renders)

Each pool is gray PNG, long side <= 1000 px, fixed selection (seeded). These pages are only CANDIDATES for
"upright": run `python -m src.audit_external` afterwards and look at the flagged pages (a few are really sideways).
Brno Mobile OCR in data/external is a set of 48-px TEXT-LINE crops, not pages, and is therefore not used.
"""
from __future__ import annotations

import glob
import os
import zipfile

import cv2
import numpy as np
import pyarrow.parquet as pq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, "data", "external")
CACHE = os.path.join(ROOT, "data", "cache")


def _save(name: str, idx: int, g: np.ndarray, long_side: int = 1000, cache_prefix: str = "ext_") -> str:
    d = os.path.join(CACHE, f"{cache_prefix}{name}")
    os.makedirs(d, exist_ok=True)
    s = long_side / max(g.shape)
    if s < 1:
        g = cv2.resize(g, (int(g.shape[1] * s), int(g.shape[0] * s)), interpolation=cv2.INTER_AREA)
    path = os.path.join(d, f"{name}_{idx:04d}.png")
    cv2.imwrite(path, g)
    return path


def _from_parquet(name: str, folder: str, splits=("test", "train", "validation"), limit: int = 400) -> int:
    n = 0
    for sp in splits:
        for f in sorted(glob.glob(os.path.join(EXT, folder, "data", f"{sp}-*.parquet"))):
            pf = pq.ParquetFile(f)
            for rg in range(pf.num_row_groups):
                col = pf.read_row_group(rg, columns=["image"]).column(0).to_pylist()
                for r in col:
                    g = cv2.imdecode(np.frombuffer(r["bytes"], np.uint8), cv2.IMREAD_GRAYSCALE)
                    if g is None:
                        continue
                    _save(name, n, g)
                    n += 1
                    if n >= limit:
                        return n
    return n


def _doclaynet(limit: int = 300) -> int:
    """300 pages for evaluation (ext_doclaynet); the pages NOT chosen feed the training pools (see _training_pools)."""
    z = zipfile.ZipFile(os.path.join(EXT, "doclaynet_small", "data", "dataset_small.zip"))
    names = sorted(m for m in z.namelist() if m.endswith(".png") and "/images/" in m)
    order = np.random.default_rng(7).permutation(len(names))
    for i, k in enumerate(order[:limit]):
        g = cv2.imdecode(np.frombuffer(z.read(names[k]), np.uint8), cv2.IMREAD_GRAYSCALE)
        _save("doclaynet", i, g)
    return limit


def _training_pools(n_doclaynet: int = 424, n_val: int = 100, n_val_dln: int = 80) -> dict:
    """Pools for training the orientation classifier, disjoint from every evaluation pool:
    cord_train/cord_val   - CORD v2 *train* split receipts photographed by phone (800 -> 700/100)
    doclaynet_train/_val  - DocLayNet-small pages not used by ext_doclaynet
    """
    out = {}
    files = sorted(glob.glob(os.path.join(EXT, "cord_v2", "data", "train-*.parquet")))
    total = sum(pq.ParquetFile(f).metadata.num_rows for f in files)
    i = 0
    for f in files:                                  # stream: these files are ~450 MB each
        pf = pq.ParquetFile(f)
        for rg in range(pf.num_row_groups):
            for r in pf.read_row_group(rg, columns=["image"]).column(0).to_pylist():
                g = cv2.imdecode(np.frombuffer(r["bytes"], np.uint8), cv2.IMREAD_GRAYSCALE)
                if g is not None:
                    _save("cord_train" if i < total - n_val else "cord_val", i, g, cache_prefix="")
                i += 1
    out["cord"] = i
    z = zipfile.ZipFile(os.path.join(EXT, "doclaynet_small", "data", "dataset_small.zip"))
    names = sorted(m for m in z.namelist() if m.endswith(".png") and "/images/" in m)
    order = np.random.default_rng(7).permutation(len(names))[300:300 + n_doclaynet + n_val_dln]
    for j, k in enumerate(order):
        g = cv2.imdecode(np.frombuffer(z.read(names[k]), np.uint8), cv2.IMREAD_GRAYSCALE)
        _save("doclaynet_train" if j < n_doclaynet else "doclaynet_val", j, g, cache_prefix="")
    out["doclaynet"] = len(order)
    return out


def main(only=None):
    # FUNSD: 199 scanned forms (test + train); CORD v2: receipts photographed by phone (test + validation)
    if only in (None, "funsd"):
        print("funsd", _from_parquet("funsd", "funsd", splits=("test", "train"), limit=199))
    if only in (None, "cord"):
        print("cord", _from_parquet("cord", "cord_v2", splits=("test", "validation"), limit=200))
    if only in (None, "doclaynet"):
        print("doclaynet", _doclaynet(300))
    if only in (None, "training"):
        print("training pools", _training_pools())


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
