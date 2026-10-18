import cv2
import numpy as np

from docangle import DocumentOrientationPipeline, PipelineConfig
from docangle.docrop import find_document


def _page(h, w, rng):
    img = np.full((h, w), 240, np.uint8)
    for y in range(20, h - 20, 14):
        x0 = 20 + int(rng.integers(0, 15))
        cv2.line(img, (x0, y), (w - 20 - int(rng.integers(0, 40)), y), 30, 2)
    return img


def _iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    return i / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i)


def _desk_photo(seed=0):
    rng = np.random.default_rng(seed)
    bg = np.full((720, 1280), 90, np.uint8)
    page = _page(400, 300, rng)
    bg[150:550, 480:780] = page
    return bg, (480, 150, 780, 550)


def test_find_document_locates_a_small_page_on_a_plain_desk():
    img, truth = _desk_photo()
    box = find_document(img)
    assert box is not None and _iou(box, truth) > 0.7


def test_find_document_leaves_a_full_page_and_empty_images_alone():
    rng = np.random.default_rng(1)
    assert find_document(_page(1000, 760, rng)) is None
    assert find_document(np.full((600, 800), 128, np.uint8)) is None


def test_doc_crop_pipeline_keeps_the_angle_of_the_whole_image():
    img, _ = _desk_photo(2)
    tilted = cv2.warpAffine(img, cv2.getRotationMatrix2D((640, 360), 6.0, 1.0), (1280, 720), borderValue=90)
    on = DocumentOrientationPipeline(PipelineConfig(doc_crop=True)).predict(tilted)
    off = DocumentOrientationPipeline().predict(tilted)
    assert on.angle is not None and off.angle is not None
    assert abs(((on.fine_tilt - 6.0 + 45) % 90) - 45) < 2.0                 # the crop is axis-aligned: the tilt is the tilt of the image
