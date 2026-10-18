"""End-to-end checks on real pages. Skipped when the benchmark images are not present."""
import cv2
import pytest

from docangle import angular_distance, rotate_image_expanded

pytestmark = pytest.mark.data
ANGLES = [0.0, 90.0, 180.0, -90.0, 33.3, -117.4, 160.2, -44.0]


def test_roundtrip_angle_recovery_no_flips(pipe, az_pages):
    bad = []
    for f in az_pages:
        img = cv2.imread(f)
        for a in ANGLES:
            r = pipe.predict(rotate_image_expanded(img, a))
            err = angular_distance(r.angle, a)
            if err > 1.5:
                bad.append((f.split("/")[-1], a, r.angle, round(err, 2), r.needs_review))
    assert not bad, bad


def test_upright_output_has_horizontal_text(pipe, az_pages):
    img = cv2.imread(az_pages[0])
    out, res = pipe.correct(rotate_image_expanded(img, 27.0))
    g = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
    prof = (g < 128).sum(axis=1).astype(float)
    assert prof.std() > 0 and res.angle is not None
    assert abs(angular_distance(res.angle, 27.0)) < 1.5


def test_speculative_pass2_agrees_with_sequential(az_pages):
    """Running the pass-2 Hough concurrently with the classifiers must not change the answer (beyond Hough noise)."""
    from docangle import DocumentOrientationPipeline, PipelineConfig
    a = DocumentOrientationPipeline(PipelineConfig(fine_estimator="hough", speculative_pass2=True))
    b = DocumentOrientationPipeline(PipelineConfig(fine_estimator="hough", speculative_pass2=False))
    far = []
    for f in az_pages[:3]:
        img = cv2.imread(f)
        for ang in (0.0, 33.3, 120.0, -90.0):
            rot = rotate_image_expanded(img, ang)
            ra, rb = a.predict(rot), b.predict(rot)
            if angular_distance(ra.angle, rb.angle) > 0.6:
                far.append((f.split("/")[-1], ang, ra.angle, rb.angle))
    assert not far, far
