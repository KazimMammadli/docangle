"""Out-of-sample orientation audit of 'upright' pools.

Scores every page with models that never trained on it (PP-LCNet + our v1 classifier, which saw only
Tobacco + synthetic pages) and records the posterior over clockwise classes. Pages whose posterior says
'not upright' are label-noise candidates (sideways / upside-down source scans).
"""
import glob
import json
import os
import sys

import cv2
import numpy as np

from docangle import DocumentOrientationPipeline, PipelineConfig
from docangle.orientation import OrientationClassifier

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cv2.setNumThreads(2)


def main(pools, out):
    pipe = DocumentOrientationPipeline(PipelineConfig(lcnet_tta=True, orient_weight=0))
    v1 = OrientationClassifier(os.path.join(ROOT, "models", "orient_cls_v1.onnx"), 2)
    res = {}
    for pool in pools:
        files = sorted(glob.glob(os.path.join(ROOT, pool)))
        for i, f in enumerate(files):
            g = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
            lp = pipe._lcnet_logpost(g) + v1.log_posterior(g)
            p = np.exp(lp - lp.max()); p /= p.sum()
            res[os.path.relpath(f, ROOT)] = [round(float(x), 4) for x in p]
            if i % 500 == 0:
                print(pool, i, len(files), flush=True)
    json.dump(res, open(out, "w"))
    arr = np.array(list(res.values()))
    print("pages", len(arr), "P(upright)<0.5:", int((arr[:, 0] < 0.5).sum()), "<0.9:", int((arr[:, 0] < 0.9).sum()))


if __name__ == "__main__":
    main(sys.argv[2:], sys.argv[1])
