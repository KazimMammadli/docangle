"""Experiment: DuarteBarbosa/deep-image-orientation-detection (EfficientNetV2-S, 4 rotation classes, MIT) as a quadrant voter and as a baseline.

Model file: data/external/duarte_orientation/orientation_model_v2_0.9882.onnx (80.6 MB, sha256 cffe911c...91ba, Hugging Face, downloaded with the maintainer's approval, not part of the package).
Preprocessing exactly as its predict_onnx.py: RGB, PIL bilinear resize to 416 x 416 (aspect NOT kept), centre crop 384, ImageNet mean / std.
Output: 4 logits = the rotation that was APPLIED to an upright image (0: none, 1: 90 deg CW, 2: 180, 3: 90 deg CCW); `perm` maps them to our clockwise classes (measured by `calibrate_mapping`).
The model was trained on photographs (COCO, TextOCR, personal photos), not on documents.
"""
from __future__ import annotations

import os

import numpy as np
import onnxruntime as ort
from PIL import Image

from .exp_doctr import calibrate_mapping  # noqa: F401  (same procedure: upright pages turned by 90*k, count the argmax votes)

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "external", "duarte_orientation", "orientation_model_v2_0.9882.onnx")
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


class Duarte:
    def __init__(self, path=PATH, threads=2):
        o = ort.SessionOptions()
        o.intra_op_num_threads = threads
        self.s = ort.InferenceSession(path, o, providers=["CPUExecutionProvider"])
        self.name = self.s.get_inputs()[0].name
        self.perm = np.arange(4)          # model logit index -> our clockwise class index

    def blob(self, gray_or_bgr: np.ndarray) -> np.ndarray:
        a = gray_or_bgr
        rgb = np.repeat(a[:, :, None], 3, 2) if a.ndim == 2 else a[:, :, ::-1]
        im = Image.fromarray(np.ascontiguousarray(rgb)).resize((416, 416), Image.BILINEAR).crop((16, 16, 400, 400))
        x = (np.asarray(im, np.float32) / 255.0 - MEAN) / STD
        return x.transpose(2, 0, 1)[None]

    def logits(self, img):
        return self.s.run(None, {self.name: self.blob(img)})[0][0]

    def log_posterior(self, gray, ks=(0, 2)):
        """Rotation-voted log-posterior over OUR clockwise classes for an axis-aligned page (same convention as OrientationClassifier / DocTR)."""
        lps = []
        for k in ks:
            g = gray if k == 0 else np.ascontiguousarray(np.rot90(gray, k))
            lg = self.logits(g).astype(np.float64)
            lp = lg - lg.max()
            lp -= np.log(np.exp(lp).sum())
            ours = np.empty(4)
            ours[self.perm] = lp
            lps.append(ours)
        out = np.zeros(4)
        for c in range(4):
            out[c] = np.mean([lps[i][(c - ks[i]) % 4] for i in range(len(ks))])
        return out - (np.log(np.exp(out - out.max()).sum()) + out.max())
