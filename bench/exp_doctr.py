"""Experiment E3b: docTR page-orientation model (mobilenet_v3_small_page_orientation, Apache-2.0) as a third quadrant voter.

Input: RGB page letterboxed (aspect kept, black symmetric padding) to 512x512, mean (0.694, 0.695, 0.693), std (0.299, 0.296, 0.301).
Output: 4 logits for [0, -90, 180, 90]; the mapping to our clockwise classes is measured, not assumed (`calibrate_mapping`).
"""
from __future__ import annotations

import os

import cv2
import numpy as np
import onnxruntime as ort

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "external", "doctr",
                    "mobilenet_v3_small_page_orientation.onnx")
MEAN = np.array([0.694, 0.695, 0.693], np.float32)
STD = np.array([0.299, 0.296, 0.301], np.float32)


class DocTR:
    def __init__(self, path=PATH, threads=2):
        o = ort.SessionOptions(); o.intra_op_num_threads = threads
        self.s = ort.InferenceSession(path, o, providers=["CPUExecutionProvider"])
        self.name = self.s.get_inputs()[0].name
        self.size = int(self.s.get_inputs()[0].shape[2])
        self.perm = np.arange(4)          # docTR logit index -> our clockwise class index (set by calibrate_mapping)

    def blob(self, gray: np.ndarray) -> np.ndarray:
        S = self.size
        h, w = gray.shape[:2]
        k = S / max(h, w)
        nh, nw = max(1, int(round(h * k))), max(1, int(round(w * k)))
        small = cv2.resize(gray, (nw, nh), interpolation=cv2.INTER_LINEAR if k > 1 else cv2.INTER_AREA)
        canvas = np.zeros((S, S), np.uint8)
        y0, x0 = (S - nh) // 2, (S - nw) // 2
        canvas[y0:y0 + nh, x0:x0 + nw] = small
        x = (canvas.astype(np.float32)[None] / 255.0 - MEAN[:, None, None]) / STD[:, None, None]    # gray -> 3 identical channels
        return x[None]

    def logits(self, gray):
        return self.s.run(None, {self.name: self.blob(gray)})[0][0]

    def log_posterior(self, gray, ks=(0, 2)):
        """Rotation-voted log-posterior over OUR clockwise classes for an axis-aligned page (same convention as OrientationClassifier)."""
        lps = []
        for k in ks:
            g = gray if k == 0 else np.ascontiguousarray(np.rot90(gray, k))
            lg = self.logits(g).astype(np.float64)
            lp = lg - lg.max(); lp -= np.log(np.exp(lp).sum())
            ours = np.empty(4); ours[self.perm] = lp                   # ours[perm[i]] = lp[i]
            lps.append(ours)
        out = np.zeros(4)
        for c in range(4):
            out[c] = np.mean([lps[i][(c - ks[i]) % 4] for i in range(len(ks))])
        return out - (np.log(np.exp(out - out.max()).sum()) + out.max())


def calibrate_mapping(model: DocTR, grays):
    """Find the logit permutation by showing upright pages rotated CCW by 90*k (our class (360-90k)%360/90) and counting argmax votes."""
    votes = np.zeros((4, 4), int)    # [docTR argmax index, our class]
    for g in grays:
        for k in range(4):
            r = g if k == 0 else np.ascontiguousarray(np.rot90(g, k))
            votes[int(np.argmax(model.logits(r))), ((360 - 90 * k) % 360) // 90] += 1
    return votes
