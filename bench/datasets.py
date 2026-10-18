"""Upright-page pools for benchmarking. Pools are file lists; images are loaded lazily."""
import glob
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _pool(name: str):
    if name == "az":
        return sorted(glob.glob(os.path.join(ROOT, "data", "az_test_pages", "*.png")))
    if name == "invoices":
        return sorted(glob.glob(os.path.join(ROOT, "data", "invoices_rvl_certified", "*.png")))
    if name == "tobacco_cert":
        with open(os.path.join(ROOT, "data", "certified_upright_test.json")) as f:
            return [os.path.join(ROOT, p) for p in json.load(f)]
    if name == "rvl_heldout":  # independent invoices: never used for training or checkpoint selection
        return sorted(glob.glob(os.path.join(ROOT, "data", "cache", "rvl_inv_heldout", "*.png")))
    if name in ("ext_funsd", "ext_cord", "ext_doclaynet"):  # external sets, see src/prep_external.py; never trained on
        return sorted(glob.glob(os.path.join(ROOT, "data", "cache", name, "*.png")))
    raise KeyError(name)


def pool(name: str):
    files = _pool(name)
    if not files:
        raise SystemExit(f"pool {name!r} is empty: the pages are not in this checkout. The private pools (az, invoices) must be replaced by your own pages, "
                         f"the others are recreated by the data scripts: see docs/12-reproduce.md, section 12.2")
    return files


def pick(files, n: int, seed_index: int):
    """Disjoint chunks across seeds while the pool lasts; wraps (and reports it) otherwise."""
    order = np.random.default_rng(12345).permutation(len(files))
    start = (seed_index * n) % len(files)
    idx = [order[(start + i) % len(files)] for i in range(n)]
    return [files[i] for i in idx], (seed_index + 1) * n > len(files)
