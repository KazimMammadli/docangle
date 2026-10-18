import cv2
import numpy as np
import pytest

from docangle import DocumentOrientationPipeline, PipelineConfig, rotate_image_expanded
from docangle.fftskew import FFTSkew
from tests.unit.helpers import ruled_page


def _text_page(seed=0):
    img = ruled_page(seed=seed)
    rng = np.random.default_rng(seed)
    for y in range(125, 1280, 34):                      # word-like dashes make the spectrum less artificial
        x = 110
        while x < 880:
            n = int(rng.integers(20, 70))
            cv2.line(img, (x, y - 5), (x + n, y - 5), (0, 0, 0), 5)
            x += n + int(rng.integers(8, 20))
    return img[:, :, 0]


@pytest.mark.parametrize("tilt", [0.0, 3.0, -7.5, 20.0, -31.0, 44.0])
def test_tilt_matches_rotation_ccw_positive(tilt):
    page = rotate_image_expanded(_text_page(), tilt)    # CCW rotation by `tilt`
    est = FFTSkew(512).tilt(page)
    assert abs((est - tilt + 45.0) % 90.0 - 45.0) < 1.0


def test_tilt_is_folded_modulo_90():
    page = rotate_image_expanded(_text_page(), 90.0 + 4.0)
    assert FFTSkew(512).tilt(page) == pytest.approx(4.0, abs=1.0)


def test_pipeline_fft_mode_runs_and_reports_angle():
    pipe = DocumentOrientationPipeline(PipelineConfig(fine_estimator="fft", fft_alarm_deg=3.0))
    r = pipe.predict(rotate_image_expanded(_text_page(), 12.0))
    assert r.angle is not None
    assert r.fine_tilt == pytest.approx(12.0, abs=1.0)      # the Fourier tilt, whatever the classifiers decide


def test_bad_fine_estimator_rejected():
    with pytest.raises(ValueError):
        PipelineConfig(fine_estimator="radon")
