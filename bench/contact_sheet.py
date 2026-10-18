"""Render a grid of simulated photos so a human can judge the realism of the degradation levels."""
import sys
import cv2
import numpy as np
from . import datasets
from .degrade import LEVELS, render, sample_angle


def main(out="reports/contact_sheet.jpg", ds="az"):
    files = datasets.pool(ds)
    rows = []
    for lv in ("scan", "photo_easy", "photo_hard"):
        tiles = []
        for i in range(5):
            rng = np.random.default_rng([7, i])
            page = cv2.imread(files[(i * 17) % len(files)])
            img = render(page, sample_angle("uniform", rng), LEVELS[lv], rng)
            h, w = img.shape[:2]; s = 300 / max(h, w)
            t = cv2.resize(img, (int(w * s), int(h * s)))
            canvas = np.full((300, 300, 3), 128, np.uint8); canvas[:t.shape[0], :t.shape[1]] = t
            tiles.append(canvas)
        rows.append(np.hstack(tiles))
    cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("wrote", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
