import cv2
import numpy as np
import pytest

from docangle import angular_distance, normalize_angle, rotate_image_expanded, upright
from docangle.pipeline import axis_angle
from tests.unit.helpers import ruled_page


@pytest.mark.parametrize("a,expected", [(0, 0), (180, -180), (-180, -180), (190, -170), (-190, 170), (540, -180), (359.5, -0.5)])
def test_normalize_angle(a, expected):
    assert normalize_angle(a) == pytest.approx(expected)


@pytest.mark.parametrize("a,b,d", [(179, -179, 2), (0, 180, 180), (10, 20, 10), (-170, 170, 20), (45, 45, 0)])
def test_angular_distance(a, b, d):
    assert angular_distance(a, b) == pytest.approx(d)
    assert angular_distance(b, a) == pytest.approx(d)


def test_expanded_canvas_keeps_all_corners():
    img = np.zeros((300, 500), np.uint8)
    out = rotate_image_expanded(img, 30)
    c, s = np.cos(np.radians(30)), np.sin(np.radians(30))
    assert out.shape[1] >= 300 * s + 500 * c - 1 and out.shape[0] >= 300 * c + 500 * s - 1


@pytest.mark.parametrize("dtype,white", [(np.uint8, 255), (np.uint16, 65535), (np.float32, 1.0)])
def test_upright_border_is_white_for_each_dtype(dtype, white):
    img = np.full((200, 300), white, dtype)
    out = upright(img, 25.0)
    assert out.dtype == dtype
    assert out.min() == white  # border filled white, no black wedges


def test_rotation_sign_convention_ccw_positive():
    # A bright dot on the right edge, rotated +90 (CCW) must end up at the top.
    img = np.zeros((101, 101), np.uint8)
    img[50, 95] = 255
    out = rotate_image_expanded(img, 90, border_val=0)
    y, x = np.unravel_index(out.argmax(), out.shape)
    assert y < 20 and abs(x - out.shape[1] // 2) < 3


@pytest.mark.parametrize("tilt", [-40.0, -20.3, -5.0, 0.7, 13.3, 30.0, 44.0])
def test_hough_slope_recovers_tilt_incl_near_boundary(pipe, tilt):
    gray = cv2.cvtColor(ruled_page(), cv2.COLOR_BGR2GRAY)
    rot = rotate_image_expanded(gray, tilt)
    slope, n = pipe._hough_slope(rot)
    expected = -((tilt + 45.0) % 90.0 - 45.0)  # image y axis points down: CCW page tilt = negative slope
    assert n > 20
    diff = abs((slope - expected + 45.0) % 90.0 - 45.0)  # compare mod 90 (boundary wraps legitimately)
    # HoughLinesP uses 1-degree theta bins, so perfectly straight synthetic lines quantise to <=0.5 deg.
    assert diff < 0.75, (slope, expected)


def _axis_err(a, b):
    return abs((a - b + 45.0) % 90.0 - 45.0)


@pytest.mark.parametrize("true", [0.0, 3.2, -17.0, 30.0, 44.0, 45.0, -44.5])
def test_axis_angle_circular_handles_the_pm45_wrap(true):
    rng = np.random.default_rng(1)
    dirs = true + 90.0 * rng.integers(0, 4, 60) + rng.normal(0, 0.8, 60)   # lines along both page axes
    assert _axis_err(axis_angle(dirs, "circular"), true) < 0.6


def test_axis_angle_legacy_median_fails_at_the_wrap():
    """The wrapped-median estimator returns ~0 for pages tilted ~45 degrees: why 'circular' is the default."""
    dirs = np.array([44.0] * 5 + [46.0] * 5)
    assert _axis_err(axis_angle(dirs, "median"), 45.0) > 40
    assert _axis_err(axis_angle(dirs, "circular"), 45.0) < 1.5


def test_axis_angle_ignores_stray_lines():
    dirs = np.concatenate([np.full(40, 7.0), np.array([30.0, -20.0, 55.0])])
    assert _axis_err(axis_angle(dirs, "circular"), 7.0) < 0.5


@pytest.mark.parametrize("angle", [90, -90, 180, -180, 270])
def test_upright_quarter_turns_are_lossless(angle):
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, (120, 200), dtype=np.uint8)
    out = upright(img, angle)
    assert np.array_equal(out, np.rot90(img, k=int(round(-angle / 90.0)) % 4))        # exact pixels, exact canvas size, no resampling
    assert not np.shares_memory(out, img)


def test_upright_tilt_is_sharper_than_bilinear():
    import cv2
    page = np.full((600, 900), 235, np.uint8)
    for y in range(40, 560, 22):
        cv2.line(page, (50, y), (850, y), 30, 2)
    tilted = rotate_image_expanded(page, 7.0)
    sharp = lambda x: cv2.Laplacian(x, cv2.CV_64F).var()
    new = upright(tilted, 7.0)
    old = upright(tilted, 7.0, interpolation=cv2.INTER_LINEAR, lossless_quarter_turns=False)
    assert new.shape == old.shape or abs(new.shape[0] - old.shape[0]) <= 1
    assert sharp(new) > sharp(old)


def test_upright_with_quarter_plus_tilt_restores_the_page():
    page = np.full((300, 500), 220, np.uint8)
    page[100:200, 150:350] = 40
    a = upright(rotate_image_expanded(page, 100.0), 100.0)
    h, w = page.shape
    y0, x0 = (a.shape[0] - h) // 2, (a.shape[1] - w) // 2
    assert np.abs(a[y0:y0 + h, x0:x0 + w].astype(int) - page).mean() < 5                 # upright again: only the block edges differ (resampled twice)


@pytest.mark.parametrize("angle", [0.0, 0.01, -0.04, 0.099, 90.03, 179.98, -90.05])
def test_upright_leaves_a_tiny_tilt_alone(angle):
    """A correction below min_tilt (the estimate's resolution) is not worth a blurring resample: the pixels stay exactly the same."""
    rng = np.random.default_rng(3)
    img = rng.integers(0, 256, (90, 140), dtype=np.uint8)
    out = upright(img, angle)
    assert np.array_equal(out, np.rot90(img, k=int(round(-angle / 90.0)) % 4))


def test_upright_min_tilt_can_be_switched_off_and_larger_tilts_still_rotate():
    rng = np.random.default_rng(4)
    img = rng.integers(0, 256, (90, 140), dtype=np.uint8)
    assert not np.array_equal(upright(img, 0.3), img)                                     # 0.3 degrees is above the default dead band
    forced = upright(img, 0.05, min_tilt=0.0)
    assert forced.shape != img.shape or not np.array_equal(forced, img)                   # explicitly asked for: resampled
