"""Find the document in a photo that shows it small, on a desk or another background (opt-in: ``PipelineConfig(doc_crop=True)``).

The pipeline assumes the page fills the image. On a phone photo of a page lying on a desk the text is tiny and the background dominates, so the angle
is less reliable (SmartDoc whole frames: 8.9 % flips against 2.7 % when the document is cut out, reports/FINAL_REPORT.md section 14). This detector
needs no model: Canny edges of a 640 px copy are thickened and joined, the connected region with the most edge pixels is the document, its bounding
box (plus a margin) is returned. A box is returned only when the region is clearly smaller than the image, so a page that fills the frame is left alone.
The angle of the crop is the angle of the image (the box is axis-aligned).
"""
from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np


def find_document(gray: np.ndarray, side: int = 640, kernel: float = 0.01, canny_lo: int = 20, canny_hi: int = 60, margin: float = 0.04,
                  min_area: float = 0.04, max_area: float = 0.25) -> Optional[Tuple[int, int, int, int]]:
    """``(x0, y0, x1, y1)`` of the document in ``gray`` (uint8, pixels of ``gray``), or None if no region is clearly smaller than the image.

    ``kernel`` is the edge-thickening size as a fraction of the 640 px copy's long side; ``min_area`` / ``max_area`` bound the region's share of the
    image (smaller: noise; larger: the page already fills the frame); ``margin`` is added around the box as a fraction of its long side.
    """
    h, w = gray.shape[:2]
    s = side / max(h, w)
    g = cv2.resize(gray, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA) if s < 1.0 else gray
    s = g.shape[1] / w
    edges = cv2.Canny(cv2.GaussianBlur(g, (3, 3), 0), canny_lo, canny_hi)
    k = max(3, int(kernel * max(g.shape)) | 1)
    mask = cv2.dilate(edges, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (2 * k + 1, 2 * k + 1)))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n < 2:
        return None
    on = edges > 0
    counts = np.bincount(labels[on], minlength=n)
    counts[0] = 0
    best = int(np.argmax(counts))
    x, y, bw, bh = (int(v) for v in stats[best, :4])
    if not min_area <= bw * bh / float(g.shape[0] * g.shape[1]) <= max_area:
        return None
    m = margin * max(bw, bh)
    x0, y0 = max(0, int((x - m) / s)), max(0, int((y - m) / s))
    x1, y1 = min(w, int((x + bw + m) / s)), min(h, int((y + bh + m) / s))
    return x0, y0, x1, y1
