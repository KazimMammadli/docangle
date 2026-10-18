"""Train the 4-way page-orientation classifier (GPU) and export it to ONNX.

    python -m src.train_orientation --epochs 30 --out models/orient_cls_v1

Validation: fixed samples from the *val* splits only (Tobacco val pages and unseen synthetic pages).
Checkpoint selection uses real-page accuracy. Test-set numbers come from `bench.run` afterwards.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import models

from .orient_data import OrientationDataset, list_pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class OrientNet(nn.Module):
    """MobileNetV3-Large on a 1-channel page image -> 4 logits (clockwise 0/90/180/270)."""

    def __init__(self, pretrained: bool = True):
        super().__init__()
        w = models.MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        self.backbone = models.mobilenet_v3_large(weights=w)
        self.backbone.classifier[-1] = nn.Linear(self.backbone.classifier[-1].in_features, 4)

    def forward(self, x):  # x: (N,1,S,S) normalised
        return self.backbone(x.expand(-1, 3, -1, -1))


def _mem_available_gb() -> float:
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    return 0.0


def _preflight(min_free_gb: float, workers: int):
    """Refuse to start when RAM is short: an OOM on this 15 GB laptop freezes the whole desktop."""
    free = _mem_available_gb()
    need = max(min_free_gb, 1.5 + 0.35 * workers)
    if free < need:
        raise SystemExit(f"only {free:.1f} GB RAM available, need {need:.1f} GB. Close other jobs or lower --workers.")
    print(f"memory preflight ok: {free:.1f} GB available (need {need:.1f})", flush=True)


@torch.no_grad()
def evaluate(model, loader, device, n_pools):
    model.eval()
    correct = [0] * n_pools
    total = [0] * n_pools
    nll = []
    for x, y, src in loader:
        x, y, src = x.to(device), y.to(device), src.to(device)
        with torch.autocast("cuda", dtype=torch.float16):
            lg = model(x)
        pred = lg.argmax(1)
        nll.append(F.cross_entropy(lg.float(), y, reduction="none").cpu())
        for s in range(n_pools):
            m = src == s
            correct[s] += int((pred[m] == y[m]).sum()); total[s] += int(m.sum())
    return {"acc": [c / max(t, 1) for c, t in zip(correct, total)], "n": total, "nll": float(torch.cat(nll).mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--samples", type=int, default=12000)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--size", type=int, default=320)
    ap.add_argument("--train-pools", default="real_train:0.5,synth_train:0.5", help="name:weight,... (names under data/cache)")
    ap.add_argument("--val-pools", default="real_val:0.6,synth_val:0.4")
    ap.add_argument("--init", default=None, help="checkpoint to fine-tune from")
    ap.add_argument("--select", default="real_val", help="comma list of val pool names whose mean accuracy picks the checkpoint")
    ap.add_argument("--workers", type=int, default=4, help="train DataLoader workers (each costs ~250 MB RAM)")
    ap.add_argument("--val-workers", type=int, default=0)
    ap.add_argument("--min-free-gb", type=float, default=6.0, help="refuse to start if less RAM is available")
    ap.add_argument("--out", default="models/orient_cls_v1")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    _preflight(a.min_free_gb, a.workers)
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    dev = torch.device("cuda")
    torch.backends.cudnn.benchmark = True

    tp = [x.split(":") for x in a.train_pools.split(",")]
    vp = [x.split(":") for x in a.val_pools.split(",")]
    tr_pools = [list_pool(n) for n, _ in tp]
    va_pools = [list_pool(n) for n, _ in vp]
    print("train pools:", {n: len(p) for (n, _), p in zip(tp, tr_pools)}, "val pools:", {n: len(p) for (n, _), p in zip(vp, va_pools)}, flush=True)
    sel_idx = [i for i, (n, _) in enumerate(vp) if n in a.select.split(",")]
    train = OrientationDataset(tr_pools, [float(w) for _, w in tp], a.samples, a.size, True)
    val = OrientationDataset(va_pools, [float(w) for _, w in vp], 1800, a.size, True, fixed_seed=777)
    tl = DataLoader(train, a.batch, shuffle=True, num_workers=a.workers, persistent_workers=True, drop_last=True, pin_memory=True)
    vl = DataLoader(val, 128, shuffle=False, num_workers=a.val_workers)

    model = OrientNet(pretrained=a.init is None).to(dev)
    if a.init:
        model.load_state_dict(torch.load(os.path.join(ROOT, a.init), map_location=dev, weights_only=False)["model"])
        print("fine-tuning from", a.init, flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
    steps = a.epochs * len(tl)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=steps, pct_start=0.1)
    scaler = torch.amp.GradScaler("cuda")
    best, hist = -1.0, []
    os.makedirs(os.path.dirname(os.path.join(ROOT, a.out)), exist_ok=True)
    for ep in range(1, a.epochs + 1):
        model.train(); t0 = time.time(); tot = 0.0
        for x, y, _ in tl:
            x, y = x.to(dev, non_blocking=True), y.to(dev, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            with torch.autocast("cuda", dtype=torch.float16):
                loss = F.cross_entropy(model(x), y, label_smoothing=0.05)
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); sched.step()
            tot += float(loss.detach())
        m = evaluate(model, vl, dev, len(vp)); m.update(epoch=ep, train_loss=tot / len(tl), sec=time.time() - t0); hist.append(m)
        accs = " ".join(f"{n} {x*100:.1f}%" for (n, _), x in zip(vp, m["acc"]))
        print(f"ep {ep:02d} loss {m['train_loss']:.3f} | val {accs} nll {m['nll']:.3f} | {m['sec']:.0f}s", flush=True)
        score = float(np.mean([m["acc"][i] for i in sel_idx]))
        if score > best:
            best = score
            torch.save({"model": model.state_dict(), "size": a.size, "epoch": ep, "val": m, "args": vars(a)}, os.path.join(ROOT, a.out + ".pt"))
    json.dump(hist, open(os.path.join(ROOT, a.out + "_history.json"), "w"), indent=1)
    print("best selection acc", best)


if __name__ == "__main__":
    main()
