import pytest

from docangle import Result, apply_job_consensus, normalize_angle

CW = (0, 90, 180, 270)


def page(cls, post_cls, conf=0.99, tilt=2.0, **kw):
    """Result of a page whose classifiers say class `cls` with posterior mass `post_cls` (rest spread evenly)."""
    post = [(1 - post_cls) / 3] * 4
    post[cls] = post_cls
    angle = normalize_angle(tilt + (360 - CW[cls]) % 360)
    return Result(angle=round(angle, 2), confidence=conf, quality="HIGH_CONFIDENCE", needs_review=conf < 0.9,
                  fine_tilt=tilt, posterior=post, **kw)


def test_unsure_page_adopts_consensus_and_leaves_review():
    pages = [page(0, 0.99) for _ in range(4)] + [Result(**{**vars(page(1, 0.5, conf=0.5, tilt=-1.0)), "posterior": [0.44, 0.5, 0.03, 0.03]})]
    out = apply_job_consensus(pages)
    assert out[4].angle == pytest.approx(-1.0, abs=0.01)                 # class 0 + its own fine tilt
    assert "JOB_CONSENSUS" in out[4].reasons and not out[4].needs_review
    assert [r.angle for r in out[:4]] == [r.angle for r in pages[:4]]    # unanimous pages unchanged
    assert pages[4].angle != out[4].angle                                # input not modified


def test_confident_odd_page_is_kept_but_reviewed():
    pages = [page(0, 0.99) for _ in range(6)] + [page(2, 0.999)]
    out = apply_job_consensus(pages)
    assert out[6].angle == pages[6].angle
    assert out[6].needs_review and "JOB_DISAGREE" in out[6].reasons


def test_small_job_and_pages_without_posterior_unchanged():
    two = [page(0, 0.5, conf=0.5), page(0, 0.99)]
    assert apply_job_consensus(two) == two
    blank = Result(angle=None, confidence=0.0, quality="UNDETERMINED", needs_review=True, reasons=["NO_CONTENT"])
    job = [page(0, 0.99) for _ in range(4)] + [blank]
    assert apply_job_consensus(job)[4] is blank


def test_unanimous_job_unchanged_angles():
    pages = [page(1, 0.97, tilt=t) for t in (0.0, 3.0, -4.0, 1.5)]
    assert [r.angle for r in apply_job_consensus(pages)] == [r.angle for r in pages]


def test_cli_consensus_on_pdf_and_predict_pdf(tmp_path):
    pytest.importorskip("pypdfium2")
    import cv2
    from docangle import get_pipeline
    from docangle.__main__ import main
    from tests.unit.helpers import make_scan_pdf, ruled_page
    pages = [cv2.cvtColor(ruled_page(seed=s), cv2.COLOR_BGR2GRAY) for s in range(4)]
    pdf = tmp_path / "job.pdf"
    make_scan_pdf(str(pdf), pages)
    res = get_pipeline().predict_pdf(str(pdf))
    assert len(res) == 4 and all(r.posterior is not None or r.angle is None for r in res)
    out = tmp_path / "up"
    assert main([str(pdf), "--page", "all", "--consensus", "-o", str(out)]) == 0
    assert len(list(out.glob("*.png"))) == 4
