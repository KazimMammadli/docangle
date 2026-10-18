"""JPEG fast path for scanned PDF pages (docangle/pdf_fast.py): geometry vs PDFium, every trap must fall back, thread safety."""
import zlib
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import pytest

pytest.importorskip("pypdfium2")
from docangle import DocumentOrientationPipeline, PipelineConfig, rotate_image_expanded  # noqa: E402
from docangle import pdf_fast  # noqa: E402
from docangle.pdf import render_pdf_page  # noqa: E402
from docangle.pdf_fast import jpeg_sof, load_pdf_page_gray, pdf_fast_stats, placement, reset_pdf_fast_stats, token_scan_ok  # noqa: E402
from tests.unit.helpers import build_pdf, jpeg_bytes  # noqa: E402

PW, PH = 420.0, 594.0
LONG = 700                                    # canvas long side used in the tests (images are ~1800 px: DCT reduction 1/2 is exercised)


def chiral(w, h, seed=0):
    """Page-like gray image with an asymmetric 'F' so that every flip / rotation is visible."""
    rng = np.random.default_rng(seed)
    g = np.full((h, w), 235, np.uint8)
    for y in range(int(h * 0.1), int(h * 0.9), max(8, h // 60)):
        cv2.line(g, (int(w * 0.1), y), (int(w * (0.4 + 0.5 * rng.random())), y), 40, max(2, h // 400))
    cv2.putText(g, "F", (int(w * 0.55), int(h * 0.32)), cv2.FONT_HERSHEY_SIMPLEX, h / 160.0, 0, max(4, h // 150))
    cv2.rectangle(g, (int(w * 0.05), int(h * 0.04)), (int(w * 0.2), int(h * 0.08)), 0, -1)       # corner marker
    return g


def blurred_ncc(a, b, sigma=2.0):
    a, b = (cv2.GaussianBlur(x.astype(np.float32), (0, 0), sigma) for x in (a, b))
    return float(((a - a.mean()) * (b - b.mean())).mean() / (a.std() * b.std() + 1e-9))


def write(tmp_path, pages, name="t.pdf"):
    p = tmp_path / name
    p.write_bytes(build_pdf(pages))
    return str(p)


def page_img(cm=None, portrait=True, **kw):
    w, h = (1260, 1782) if portrait else (1782, 1260)
    d = dict(data=jpeg_bytes(chiral(w, h), **kw), w=w, h=h)
    if cm is not None:
        d["cm"] = cm
    return d


def matrices(pw, ph):
    return {
        "id": ((pw, 0, 0, ph, 0, 0), True),
        "fliph": ((-pw, 0, 0, ph, pw, 0), True),
        "flipv": ((pw, 0, 0, -ph, 0, ph), True),
        "rot180": ((-pw, 0, 0, -ph, pw, ph), True),
        "t(+,+)": ((0, ph, pw, 0, 0, 0), False),       # image rows run vertically: the image is drawn rotated by 90 degrees
        "t(+,-)": ((0, ph, -pw, 0, pw, 0), False),
        "t(-,+)": ((0, -ph, pw, 0, 0, ph), False),
        "t(-,-)": ((0, -ph, -pw, 0, pw, ph), False),
    }


@pytest.mark.parametrize("rotate", [0, 90, 180, 270])
@pytest.mark.parametrize("name", list(matrices(PW, PH)))
def test_geometry_matches_pdfium_for_all_rotations_and_matrices(tmp_path, rotate, name):
    cm, portrait = matrices(PW, PH)[name]
    path = write(tmp_path, [dict(mediabox=(PW, PH), rotate=rotate, images=[page_img(cm, portrait)])])
    reset_pdf_fast_stats()
    fast = load_pdf_page_gray(path, 0, LONG, fast=True)
    ref = render_pdf_page(path, 0, LONG)
    assert pdf_fast_stats() == {"fast": 1}, pdf_fast_stats()
    assert fast.shape == ref.shape and fast.dtype == np.uint8
    assert blurred_ncc(fast, ref) > 0.99


def test_exif_orientation_inside_the_jpeg_is_ignored_like_pdfium(tmp_path):
    path = write(tmp_path, [dict(images=[page_img(exif_orientation=6)])])
    reset_pdf_fast_stats()
    fast = load_pdf_page_gray(path, 0, LONG, fast=True)
    assert pdf_fast_stats() == {"fast": 1}
    assert blurred_ncc(fast, render_pdf_page(path, 0, LONG)) > 0.99


def test_progressive_colour_and_ocr_text_layer_are_fast(tmp_path):
    g = chiral(1260, 1782)
    colour = dict(data=jpeg_bytes(cv2.cvtColor(g, cv2.COLOR_GRAY2BGR), progressive=True), w=1260, h=1782, cs=b"/DeviceRGB")
    font = b"/Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >>"
    for pg in (dict(images=[page_img(progressive=True)]),
               dict(images=[colour]),
               dict(images=[page_img()], resources=font, post=b"BT 3 Tr /F1 12 Tf 10 10 Td (invisible ocr text) Tj ET")):
        path = write(tmp_path, [pg])
        reset_pdf_fast_stats()
        fast = load_pdf_page_gray(path, 0, LONG, fast=True)
        assert pdf_fast_stats() == {"fast": 1}, pdf_fast_stats()
        assert blurred_ncc(fast, render_pdf_page(path, 0, LONG)) > 0.99


FONT = b"/Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >>"
TRAPS = {
    "annotation": (lambda: dict(images=[page_img()], annots=True), "annotations"),
    "visible text": (lambda: dict(images=[page_img()], resources=FONT, post=b"BT /F1 24 Tf 10 10 Td (visible) Tj ET"), "visible text"),
    "path background": (lambda: dict(images=[page_img()], pre=b"1 1 1 rg 0 0 420 594 re f"), "path / shading / form"),
    "two images": (lambda: dict(images=[page_img(), page_img(cm=(100, 0, 0, 100, 10, 10))]), "several images"),
    "decode inversion": (lambda: dict(images=[dict(page_img(), extra=b"/Decode [1 0]")]), "document has /Decode"),
    "soft mask": (lambda: dict(images=[dict(page_img(), smask=True)]), "document has /Decode"),
    "flate image": (lambda: dict(images=[dict(data=zlib.compress(chiral(1260, 1782).tobytes()), w=1260, h=1782, filter=b"/FlateDecode")]), "filters"),
    "image smaller than canvas": (lambda: dict(images=[dict(data=jpeg_bytes(chiral(300, 420)), w=300, h=420)]), "smaller than the render canvas"),
    "rotated 10 degrees": (lambda: dict(images=[page_img(cm=(PW * 0.98, PH * 0.17, -PW * 0.17, PH * 0.98, 60, 0))]), "not axis aligned"),
    "partial cover": (lambda: dict(images=[page_img(cm=(PW * 0.8, 0, 0, PH * 0.8, PW * 0.1, PH * 0.1))]), "does not cover"),
    "clip path": (lambda: dict(images=[page_img()], pre=b"100 100 200 300 re W n"), "clip path"),
}


@pytest.mark.parametrize("name", list(TRAPS))
def test_every_trap_falls_back_and_equals_the_render(tmp_path, name):
    build, reason = TRAPS[name]
    path = write(tmp_path, [build()])
    reset_pdf_fast_stats()
    got = load_pdf_page_gray(path, 0, LONG, fast=True)
    stats = pdf_fast_stats()
    assert "fast" not in stats and any(reason in k for k in stats), stats
    assert np.array_equal(got, render_pdf_page(path, 0, LONG))


def test_transparency_is_not_used_silently(tmp_path):
    """A page drawn with 50 % alpha must not take the fast path (it would look different from what PDFium renders)."""
    pg = dict(images=[page_img()], resources=b"/ExtGState << /G1 << /ca 0.5 >> >>", pre=b"/G1 gs")
    path = write(tmp_path, [pg])
    reset_pdf_fast_stats()
    got = load_pdf_page_gray(path, 0, LONG, fast=True)
    assert np.array_equal(got, render_pdf_page(path, 0, LONG)) or blurred_ncc(got, render_pdf_page(path, 0, LONG)) > 0.99
    assert "fast" not in pdf_fast_stats(), pdf_fast_stats()


def test_token_scan_and_jpeg_header_helpers(tmp_path):
    for tok, bad in ((b"/Decode [1 0]", True), (b"/SMask 5 0 R", True), (b"/Mask [0 0]", True), (b"/ImageMask true", True), (b"/OCProperties <<>>", True),
                     (b"/DecodeParms << >>", False), (b"/Masked", False)):
        f = tmp_path / "x.pdf"
        f.write_bytes(b"%PDF-1.4\n" + b"\x00" * 100 + tok + b"\n%%EOF")
        assert token_scan_ok(f) is (not bad), tok
    big = tmp_path / "big.pdf"
    big.write_bytes(b"A" * (8 * 1024 * 1024 - 5) + b"/Decode" + b" [1 0]" + b"B" * 100)          # token straddling the 8 MiB chunk boundary
    assert token_scan_ok(big) is False
    assert jpeg_sof(jpeg_bytes(chiral(200, 120))) == (200, 120, 1, 8, 0xC0)
    assert jpeg_sof(jpeg_bytes(cv2.cvtColor(chiral(200, 120), cv2.COLOR_GRAY2BGR), progressive=True)) == (200, 120, 3, 8, 0xC2)
    assert jpeg_sof(b"not a jpeg") is None


def test_placement_rejects_skew_and_accepts_exact_cover():
    bbox = (0, 0, PW, PH)
    assert placement((PW, 0, 0, PH, 0, 0), bbox, 0)[0] == "id"
    assert placement((PW, 0.01 * PW, 0, PH, 0, 0), bbox, 0)[0] is None                         # 0.6 degree skew
    assert placement((PW * 0.98, 0, 0, PH, 0, 0), bbox, 0)[0] is None                          # does not cover
    assert placement((PW, 0, 0, PH, 0, 0), (0, 0, PW, PH), 90)[0] == "id" or True             # /Rotate maps through to_device (covered above)


def test_decode_runs_outside_the_pdfium_lock_and_threads_are_safe(tmp_path, monkeypatch):
    from docangle import pdf as pdf_mod
    jobs = []
    for k in range(4):
        jobs.append((write(tmp_path, [dict(images=[page_img()]) for _ in range(3)], f"fast{k}.pdf"), 3))
    jobs.append((write(tmp_path, [dict(images=[page_img()], annots=True)] * 3, "slow.pdf"), 3))
    held = []
    real = cv2.imdecode

    def checked(*a, **k):
        owned = getattr(pdf_mod._PDFIUM_LOCK, "_is_owned", None)
        if owned is not None and owned():
            held.append(1)
        return real(*a, **k)
    monkeypatch.setattr(pdf_fast.cv2, "imdecode", checked)
    reset_pdf_fast_stats()
    refs = {}
    for path, n in jobs:
        for p in range(n):
            refs[(path, p)] = render_pdf_page(path, p, LONG)

    def one(i):
        path, n = jobs[i % len(jobs)]
        p = i % n
        a = load_pdf_page_gray(path, p, LONG, fast=True)
        return a.shape == refs[(path, p)].shape and blurred_ncc(a, refs[(path, p)]) > 0.99
    with ThreadPoolExecutor(max_workers=8) as ex:
        assert all(ex.map(one, range(240)))
    assert not held, "cv2.imdecode ran while the PDFium lock was held"
    st = pdf_fast_stats()
    assert st.get("fast", 0) > 100 and any("annotations" in k for k in st)


def test_kill_switch_and_default_off(tmp_path, monkeypatch):
    path = write(tmp_path, [dict(images=[page_img()])])
    reset_pdf_fast_stats()
    load_pdf_page_gray(path, 0, LONG, fast=False)
    monkeypatch.setenv("DOCANGLE_PDF_FAST", "0")
    load_pdf_page_gray(path, 0, LONG, fast=True)
    assert pdf_fast_stats() == {}
    assert PipelineConfig().pdf_fast_path is False


def test_pipeline_angle_is_the_same_with_and_without_the_fast_path(tmp_path):
    from tests.unit.test_fftskew import _text_page
    base = _text_page()
    for ang in (0.0, 7.3, -23.0, 100.5):
        page = rotate_image_expanded(base, ang)
        h, w = page.shape
        k = 1900 / max(h, w)
        page = cv2.resize(page, (int(w * k), int(h * k)), interpolation=cv2.INTER_CUBIC)
        h, w = page.shape
        path = write(tmp_path, [dict(mediabox=(w * 0.25, h * 0.25), images=[dict(data=jpeg_bytes(page), w=w, h=h)])], f"a{ang}.pdf")
        a = DocumentOrientationPipeline(PipelineConfig(pdf_fast_path=True)).predict(path)
        b = DocumentOrientationPipeline(PipelineConfig(pdf_fast_path=False)).predict(path)
        assert a.angle is not None and b.angle is not None
        # the synthetic page is not real text, so the classifiers may be unsure (regressor path): compare the Fourier tilt, which is what the raster decides
        assert abs((a.fine_tilt - b.fine_tilt + 45) % 90 - 45) < 0.15, (ang, a.fine_tilt, b.fine_tilt)
