"""PDF input (needs the optional pypdfium2 package; skipped without it)."""
import cv2
import numpy as np
import pytest

from docangle import ImageReadError, angular_distance, rotate_image_expanded
from tests.unit.helpers import make_scan_pdf, ruled_page

pytest.importorskip("pypdfium2")
from docangle.pdf import pdf_page_count, render_pdf_page  # noqa: E402


@pytest.fixture
def two_page_pdf(tmp_path):
    g = cv2.cvtColor(ruled_page(), cv2.COLOR_BGR2GRAY)
    p = tmp_path / "two.pdf"
    make_scan_pdf(p, [g, g[:700]])
    return p


def test_page_count_and_render_size(two_page_pdf):
    assert pdf_page_count(two_page_pdf) == 2
    a = render_pdf_page(two_page_pdf, 0, long_side=1000)
    assert a.dtype == np.uint8 and a.ndim == 2 and 990 <= max(a.shape) <= 1010
    c = render_pdf_page(two_page_pdf, 1, long_side=800, color=True)
    assert c.ndim == 3 and c.shape[2] == 3
    assert c.shape[0] < c.shape[1] * 1.6       # second page is the shorter one


def test_bad_page_and_bad_file(two_page_pdf, tmp_path):
    with pytest.raises(ImageReadError):
        render_pdf_page(two_page_pdf, 5)
    bad = tmp_path / "broken.pdf"
    bad.write_bytes(b"this is not a pdf")
    with pytest.raises(ImageReadError):
        pdf_page_count(bad)


@pytest.mark.data
def test_predict_pdf_recovers_tilt_and_viewer_rotation(pipe, az_pages, tmp_path):
    page = cv2.imread(az_pages[0], cv2.IMREAD_GRAYSCALE)
    tilted = rotate_image_expanded(page, 12.0)
    p = tmp_path / "tilted.pdf"
    make_scan_pdf(p, [tilted])
    assert angular_distance(pipe.predict(str(p)).angle, 12.0) < 1.5

    q = tmp_path / "viewer_rotated.pdf"      # /Rotate 90: a viewer shows the page turned 90 degrees clockwise
    make_scan_pdf(q, [page], rotate=90)
    assert angular_distance(pipe.predict(str(q)).angle, -90.0) < 1.5
    out, res = pipe.correct(str(q))
    assert out.ndim == 3 and out.shape[0] > out.shape[1]       # upright portrait page again


def test_correct_returns_the_pdf_page_at_pdf_long_side(two_page_pdf):
    """For a PDF, correct() returns the raster it analysed: raise pdf_long_side for an OCR-grade image (the angle does not depend on it)."""
    from docangle import DocumentOrientationPipeline, PipelineConfig
    small, rs = DocumentOrientationPipeline(PipelineConfig(pdf_long_side=900)).correct(str(two_page_pdf))
    big, rb = DocumentOrientationPipeline(PipelineConfig(pdf_long_side=1800)).correct(str(two_page_pdf))
    assert 890 <= max(small.shape[:2]) <= 915 and 1780 <= max(big.shape[:2]) <= 1830
    assert angular_distance(rs.fine_tilt, rb.fine_tilt) < 0.5        # the fine tilt: the quadrant of a synthetic non-text page is arbitrary


def test_threaded_rendering_is_safe(tmp_path):
    """PDFium is not thread-safe; without the module lock a threaded batch crashed ('double free') or returned unreadable pages."""
    from concurrent.futures import ThreadPoolExecutor
    pages = [cv2.cvtColor(ruled_page(seed=s), cv2.COLOR_BGR2GRAY) for s in range(6)]
    p = tmp_path / "six.pdf"
    make_scan_pdf(p, pages)
    with ThreadPoolExecutor(max_workers=8) as ex:
        out = list(ex.map(lambda k: render_pdf_page(p, k % 6, long_side=1200), range(48)))
    assert all(a.dtype == np.uint8 and 1190 <= max(a.shape) <= 1210 for a in out)


def test_pdfium_error_on_a_page_becomes_image_read_error(two_page_pdf, monkeypatch):
    """A damaged page must give UNREADABLE for that page in a job (ImageReadError), not abort the run with a PdfiumError."""
    import pypdfium2 as pdfium
    import docangle.pdf as P

    def boom(self, *a, **k):
        raise pdfium.PdfiumError("simulated damaged page object")
    monkeypatch.setattr(pdfium.PdfPage, "render", boom)
    with pytest.raises(ImageReadError):
        P.render_pdf_page(two_page_pdf, 0)
    from docangle import get_pipeline
    res = get_pipeline().predict_job([(str(two_page_pdf), 0), (str(two_page_pdf), 1)], consensus=False)
    assert [r.reasons for r in res] == [["UNREADABLE"], ["UNREADABLE"]]
