import cv2
import numpy as np
import pytest

from docangle.pipeline import _jpeg_size, _read_gray


def _jpeg(path, w, h, orientation=None):
    pil = pytest.importorskip("PIL.Image")
    rng = np.random.default_rng(0)
    a = (rng.random((h, w)) * 60 + 150).astype(np.uint8)
    a[h // 3, :] = 0                                   # one dark row so the page has structure
    im = pil.fromarray(a)
    exif = im.getexif()
    if orientation:
        exif[0x0112] = orientation
    im.save(path, quality=90, exif=exif)


def test_jpeg_size_header_parse(tmp_path):
    p = tmp_path / "a.jpg"
    _jpeg(p, 3000, 2000)
    assert _jpeg_size(p) == (3000, 2000)
    q = tmp_path / "x.png"
    cv2.imwrite(str(q), np.zeros((10, 10), np.uint8))
    assert _jpeg_size(q) is None
    assert _jpeg_size(tmp_path / "missing.jpg") is None


def test_reduced_decode_keeps_orientation_and_scale(tmp_path):
    p = tmp_path / "big.jpg"
    _jpeg(p, 4000, 3000)
    g = _read_gray(p, 1000)
    assert g.ndim == 2 and max(g.shape) >= 1000 and abs(g.shape[1] / g.shape[0] - 4 / 3) < 0.02
    small = tmp_path / "small.jpg"
    _jpeg(small, 900, 700)
    assert _read_gray(small, 1000).shape == (700, 900)            # never reduced below the target


def test_exif_rotation_is_applied_in_reduced_mode_too(tmp_path):
    p = tmp_path / "rot.jpg"
    _jpeg(p, 4000, 3000, orientation=6)                           # stored landscape, shown portrait
    assert cv2.imread(str(p), cv2.IMREAD_GRAYSCALE).shape[0] > cv2.imread(str(p), cv2.IMREAD_GRAYSCALE).shape[1]
    g = _read_gray(p, 1000)
    assert g.shape[0] > g.shape[1]
