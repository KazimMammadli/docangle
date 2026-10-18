"""Turn the downloaded RVL-CDIP invoice parquet files into upright-page PNG pools.

  train  : fine-tuning pool           data/cache/rvl_inv_train
  val    : checkpoint selection       data/cache/rvl_inv_val
  heldout: NEW independent benchmark  data/cache/rvl_inv_heldout   (never used for training/tuning)

Images that are near-duplicates (dHash Hamming <= 6) of the project's older invoice test pages are dropped,
and pages PP-LCNet is >90 % sure are sideways/flipped are dropped (label noise). Streams row groups, so RAM
stays small.
"""
import glob
import json
import os

import cv2
import numpy as np
import pyarrow.parquet as pq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "cache")
cv2.setNumThreads(2)


def dhash(g: np.ndarray) -> int:
    s = cv2.resize(g, (9, 8), interpolation=cv2.INTER_AREA).astype(np.int16)
    bits = (s[:, 1:] > s[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def ham(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def main(sample_frac=0.5, n_val=400, n_held=1500, seed=0):
    rng = np.random.default_rng(seed)
    test_hashes = []
    for pat in ("data/invoices_rvl_certified/*.png", "data/invoices_rvl_test/*.png"):
        for f in glob.glob(os.path.join(ROOT, pat)):
            g = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
            if g is not None:
                test_hashes.append(dhash(g))
    print("older invoice test pages hashed:", len(test_hashes), flush=True)

    tmp = os.path.join(OUT, "rvl_inv_all")
    os.makedirs(tmp, exist_ok=True)
    meta, dup = [], 0
    from docangle import DocumentOrientationPipeline, PipelineConfig
    pipe = DocumentOrientationPipeline(PipelineConfig(lcnet_tta=True, orient_weight=0))
    dropped_orient = 0
    idx = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "data/external/rvl_invoice/data/*.parquet"))):
        pf = pq.ParquetFile(f)
        for rg in range(pf.num_row_groups):
            t = pf.read_row_group(rg, columns=["image"]).to_pydict()["image"]
            for item in t:
                if rng.random() > sample_frac:
                    continue
                g = cv2.imdecode(np.frombuffer(item["bytes"], np.uint8), cv2.IMREAD_GRAYSCALE)
                if g is None or min(g.shape) < 200:
                    continue
                h = dhash(g)
                if any(ham(h, x) <= 6 for x in test_hashes):
                    dup += 1
                    continue
                s = 1000.0 / max(g.shape)
                if s < 1:
                    g = cv2.resize(g, (int(g.shape[1] * s), int(g.shape[0] * s)), interpolation=cv2.INTER_AREA)
                ccw, score = pipe._coarse(g)[:2]
                if ccw != 0 and score > 0.90:
                    dropped_orient += 1
                    continue
                p = os.path.join(tmp, f"{idx:06d}.png")
                cv2.imwrite(p, g)
                meta.append({"path": p, "hash": h})
                idx += 1
            print(f"{os.path.basename(f)} rg {rg + 1}/{pf.num_row_groups} kept={idx} dup_of_old_test={dup} dropped_nonupright={dropped_orient}", flush=True)
    order = rng.permutation(len(meta))
    split = {"val": order[:n_val], "heldout": order[n_val:n_val + n_held], "train": order[n_val + n_held:]}
    for name, ids in split.items():
        d = os.path.join(OUT, f"rvl_inv_{name}")
        os.makedirs(d, exist_ok=True)
        for k, i in enumerate(ids):
            os.replace(meta[i]["path"], os.path.join(d, f"{k:06d}.png"))
    os.rmdir(tmp)
    json.dump({k: len(v) for k, v in split.items()} | {"dup_of_old_test": dup, "dropped_nonupright": dropped_orient},
              open(os.path.join(ROOT, "reports", "rvl_inv_pools.json"), "w"), indent=1)
    print({k: len(v) for k, v in split.items()}, dup, dropped_orient)


if __name__ == "__main__":
    main()
