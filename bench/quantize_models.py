"""Experiment: static int8 quantisation (QDQ, per-channel weights) of the two classifiers, calibrated on real pipeline inputs.

  PYTHONPATH=. python -m bench.quantize_models make  [--cases 200]            # writes models/experimental/{orient_cls_v4,pp_lcnet_doc_ori}.int8.onnx
  PYTHONPATH=. python -m bench.quantize_models agree                          # logits of fp32 against int8 on fresh pipeline inputs, and the speed of each session
  # then the accuracy guard on the real pipeline:
  python -m bench.guard --base docangle --variants docangle_int8 --datasets az invoices ext_funsd ext_doclaynet --levels scan photo_hard --n 50

The calibration inputs are the exact tensors the pipeline feeds the models (the straightened page, our views), taken from simulated cases with a seed range that the
benchmarks do not use (seed_start 100), so that the quantised models are not tuned on the cases they are judged on.
"""
from __future__ import annotations

import argparse
import os
import time

import cv2
import numpy as np
import onnxruntime as ort
from onnxruntime.quantization import CalibrationDataReader, CalibrationMethod, QuantFormat, QuantType, quantize_static

from docangle import DocumentOrientationPipeline, PipelineConfig

from .degrade import LEVELS, render, sample_angle
from .run import make_cases

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "models")
OUT = os.path.join(MODELS, "experimental")
NAMES = {"orient": "orient_cls_v4", "lcnet": "pp_lcnet_doc_ori"}


def capture(cases_per_cell, seed_start):
    """Run the real pipeline over simulated cases and record the tensors both classifiers receive."""
    pipe = DocumentOrientationPipeline(PipelineConfig())
    got = {"orient": [], "lcnet": []}
    orient_logits, lcnet_blob = pipe._orient.logits, pipe._lcnet_blob

    def spy_orient(x):
        got["orient"].append(np.array(x))
        return orient_logits(x)

    def spy_blob(views):
        b = lcnet_blob(views)
        got["lcnet"].append(np.array(b))
        return b
    pipe._orient.logits = spy_orient
    pipe._lcnet_blob = spy_blob
    for ds in ("az", "invoices", "tobacco_cert", "ext_funsd", "ext_doclaynet", "ext_cord", "rvl_heldout"):
        for lv in ("scan", "photo_easy", "photo_hard"):
            cases, _, _ = make_cases(ds, lv, "uniform", 1, cases_per_cell, seed_start=seed_start)
            for f, s, i, rng in cases:
                page = cv2.imread(f)
                gt = sample_angle("uniform", rng)
                pipe.predict(render(page, gt, LEVELS[lv], rng))
    return got


STRIDE = 8          # calibration tensors held in memory at a time (ONNX Runtime keeps every activation of every sample of a chunk: about 0.1-0.2 GB each)


class Reader(CalibrationDataReader):
    """Single-view tensors, handed out in chunks (``CalibStridedMinMax``): the histograms of the calibrator accumulate across chunks, memory stays bounded."""

    def __init__(self, name, batches):
        self.name = name
        items = [b[i:i + 1] for b in batches for i in range(len(b))]
        self.items = items[:len(items) // STRIDE * STRIDE]
        self.it = iter(self.items)

    def get_next(self):
        x = next(self.it, None)
        return None if x is None else {self.name: x}

    def __len__(self):
        return len(self.items)

    def set_range(self, start_index, end_index):
        self.it = iter(self.items[start_index:end_index])


def make(a):
    os.makedirs(OUT, exist_ok=True)
    got = capture(a.cases, a.seed_start)
    for key, base in NAMES.items():
        src = os.path.join(MODELS, base + ".onnx")
        dst = os.path.join(OUT, base + ".int8.onnx")
        sess = ort.InferenceSession(src, providers=["CPUExecutionProvider"])
        samples = got[key]
        print(f"{base}: {sum(len(b) for b in samples)} calibration tensors", flush=True)
        t0 = time.time()
        quantize_static(src, dst, Reader(sess.get_inputs()[0].name, samples), quant_format=QuantFormat.QDQ, per_channel=True,
                        weight_type=QuantType.QInt8, activation_type=QuantType.QUInt8, calibrate_method=CalibrationMethod.Percentile,
                        extra_options={"ActivationSymmetric": False, "WeightSymmetric": True, "CalibStridedMinMax": STRIDE})
        print(f"  wrote {dst} ({os.path.getsize(dst) / 1e6:.1f} MB, {time.time() - t0:.0f} s)", flush=True)


def agree(a):
    got = capture(a.cases, a.seed_start)
    for key, base in NAMES.items():
        fp = ort.InferenceSession(os.path.join(MODELS, base + ".onnx"), providers=["CPUExecutionProvider"])
        q = ort.InferenceSession(os.path.join(OUT, base + ".int8.onnx"), providers=["CPUExecutionProvider"])
        name = fp.get_inputs()[0].name
        same, maxd, n = 0, 0.0, 0
        for x in got[key]:
            a_, b_ = fp.run(None, {name: x})[0], q.run(None, {name: x})[0]
            same += int((a_.argmax(1) == b_.argmax(1)).sum())
            n += len(a_)
            maxd = max(maxd, float(np.abs(a_ - b_).max()))
        xs = got[key][:20]

        def speed(s):
            for x in xs[:3]:
                s.run(None, {name: x})
            t = time.perf_counter()
            for x in xs:
                s.run(None, {name: x})
            return (time.perf_counter() - t) / len(xs) * 1000.0
        print(f"{base}: {n} views, same argmax {100 * same / n:.2f} %, max |logit difference| {maxd:.3f}; "
              f"fp32 {speed(fp):.1f} ms, int8 {speed(q):.1f} ms per call of {got[key][0].shape[0]} views")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["make", "agree"])
    ap.add_argument("--cases", type=int, default=10, help="cases per pool and level")
    ap.add_argument("--seed-start", type=int, default=100)
    a = ap.parse_args()
    {"make": make, "agree": agree}[a.cmd](a)


if __name__ == "__main__":
    main()
