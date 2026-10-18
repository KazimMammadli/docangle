"""Fast path for typical scanner pages: take the page's JPEG image directly instead of rendering the page with PDFium (opt-in).

A scanned PDF page is usually ONE full-page JPEG (DCTDecode). Rendering it with PDFium decodes all pixels (8.7 MP at 300 dpi A4) and scales
them: ~66 ms per page, one page at a time (PDFium is not thread-safe, see ``pdf.py``). Here the raw JPEG bytes are copied out under the PDFium
lock (about 1 ms), then decoded OUTSIDE the lock at reduced size (libjpeg DCT scaling, as ``pipeline._read_gray`` does for JPEG files), turned to
the orientation a viewer shows and resized to the canvas PDFium would have produced, so that ``analyze()`` receives almost the same raster.

It is used ONLY when everything checks out (the page is a single full-page, axis-aligned 8-bit baseline/progressive JPEG with nothing else visible);
any doubt means the normal ``render_pdf_page`` is used and the result is exactly what it was before. Not bit-identical to the render path
(different resampling), judged by angle agreement: ``bench/pdf_equiv.py``, ``reports/FINAL_REPORT.md`` section 17.

What the PDFium API cannot show (``/Decode``, ``/SMask``, ``/Mask``, ``/ImageMask``, ``/Matte``, ``/OC`` ...) is guarded at document level by a byte-token
scan of the file and by a canary (first eligible page of a document rendered small and compared with the fast raster). These guards reduce the
risk but cannot prove a mixed document safe; ``DOCANGLE_PDF_FAST=0`` is a kill switch and ``pdf_fast_stats()`` tells which path every page took.
"""
from __future__ import annotations

import math
import os
import re
import threading
from collections import Counter, OrderedDict
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from .errors import ImageReadError
from .pdf import _PDFIUM_LOCK, _pdfium, render_pdf_page

_OBJ_TEXT, _OBJ_IMAGE = 1, 3
_SOF = (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF)
_GOOD_COLORSPACES = {1, 2, 4, 5, 7}           # DeviceGray, DeviceRGB, CalGray, CalRGB, ICCBased (not CMYK / Lab / Indexed / Separation ...)
_MAX_OBJECTS = 300                            # an OCR text layer is fine, but every text object costs FFI calls under the lock
_MAX_PROGRESSIVE_BYTES = 256 * 1024 * 1024    # coefficient buffer of a progressive JPEG is about w*h*components*2 bytes
_TOKENS = re.compile(rb"/(?:Decode|SMask|Mask|ImageMask|Matte|OCProperties|ColorTransform)(?![A-Za-z])")

_RED = {1: cv2.IMREAD_GRAYSCALE, 2: cv2.IMREAD_REDUCED_GRAYSCALE_2, 4: cv2.IMREAD_REDUCED_GRAYSCALE_4, 8: cv2.IMREAD_REDUCED_GRAYSCALE_8}

_STATS: Counter = Counter()
_STATS_LOCK = threading.Lock()
_VERDICTS: "OrderedDict[tuple, dict]" = OrderedDict()
_VERDICT_LOCK = threading.Lock()
_VERDICT_MAX = 32


def pdf_fast_stats() -> Dict[str, int]:
    """Counts of the path every page took since the last reset: 'fast', 'fallback: <reason>'."""
    with _STATS_LOCK:
        return dict(_STATS)


def reset_pdf_fast_stats() -> None:
    with _STATS_LOCK:
        _STATS.clear()
    with _VERDICT_LOCK:
        _VERDICTS.clear()


def _count(key: str) -> None:
    with _STATS_LOCK:
        _STATS[key] += 1


def enabled(flag: bool) -> bool:
    """The configuration switch, overridden by the environment kill switch DOCANGLE_PDF_FAST=0."""
    return bool(flag) and os.environ.get("DOCANGLE_PDF_FAST", "1") != "0"


# --------------------------------------------------------------------------- #
# Pure helpers (unit-tested without a PDF)
# --------------------------------------------------------------------------- #
def jpeg_sof(buf) -> Optional[Tuple[int, int, int, int, int]]:
    """(width, height, components, precision, SOF marker) from a JPEG header held in memory, or None."""
    mv = memoryview(buf).cast("B")
    n = len(mv)
    if n < 4 or mv[0] != 0xFF or mv[1] != 0xD8:
        return None
    i = 2
    while i + 4 <= n:
        if mv[i] != 0xFF:
            i += 1
            continue
        m = mv[i + 1]
        if m == 0xFF:
            i += 1
            continue
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        if m == 0xDA:                          # start of scan before any frame header
            return None
        length = (mv[i + 2] << 8) | mv[i + 3]
        if m in _SOF:
            if i + 10 > n:
                return None
            return ((mv[i + 7] << 8) | mv[i + 8], (mv[i + 5] << 8) | mv[i + 6], mv[i + 9], mv[i + 4], m)
        i += 2 + length
    return None


def to_device(x: float, y: float, bbox, rot: int) -> Tuple[float, float]:
    """User-space point -> displayed-page coordinates (origin top-left, y down, points) with /Rotate applied clockwise."""
    l, b, r, t = bbox
    if rot == 0:
        return (x - l, t - y)
    if rot == 90:
        return (y - b, x - l)
    if rot == 180:
        return (r - x, y - b)
    return (t - y, r - x)                     # 270


def placement(cm, bbox, rot: int, skew_tol: float = 1.5e-4, cover_tol: float = 0.01):
    """How the image's pixel grid lies on the displayed page.

    Returns ``(op, (Wd, Hd))`` or ``(None, reason)``. ``op`` turns the decoded array (rows = image rows) into the viewer's orientation.
    The image must be axis aligned (skew <= ``skew_tol``) and cover the page box on all four sides within ``cover_tol`` of its size.
    """
    a, b, c, d, e, f = cm

    def dev(u, v):
        return to_device(a * u + c * v + e, b * u + d * v + f, bbox, rot)
    tl, tr, bl, br = dev(0, 1), dev(1, 1), dev(0, 0), dev(1, 0)
    ex = (tr[0] - tl[0], tr[1] - tl[1])       # device direction of image +x (along a row)
    ey = (bl[0] - tl[0], bl[1] - tl[1])       # device direction of image +y (down a column)
    nx, ny = math.hypot(*ex), math.hypot(*ey)
    if nx < 1e-6 or ny < 1e-6:
        return None, "degenerate matrix"
    if min(abs(ex[0]), abs(ex[1])) > skew_tol * nx or min(abs(ey[0]), abs(ey[1])) > skew_tol * ny:
        return None, "not axis aligned"
    l, bt, r, t = bbox
    wd, hd = (r - l, t - bt) if rot in (0, 180) else (t - bt, r - l)
    if abs(ex[0]) >= abs(ex[1]):              # image rows run horizontally
        sx, sy = ex[0] > 0, ey[1] > 0
        op = {(True, True): "id", (False, True): "fliph", (True, False): "flipv", (False, False): "rot180"}[(sx, sy)]
    else:                                     # rows run vertically
        sx, sy = ex[1] > 0, ey[0] > 0
        op = {(True, False): "cw", (False, True): "ccw", (True, True): "transpose", (False, False): "antitranspose"}[(sx, sy)]
    xs = [p[0] for p in (tl, tr, bl, br)]
    ys = [p[1] for p in (tl, tr, bl, br)]
    tx, ty = max(0.5, cover_tol * wd), max(0.5, cover_tol * hd)
    if not (abs(min(xs)) <= tx and abs(min(ys)) <= ty and abs(max(xs) - wd) <= tx and abs(max(ys) - hd) <= ty):
        return None, "image does not cover the page"
    return op, (wd, hd)


def apply_op(a: np.ndarray, op: str) -> np.ndarray:
    if op == "id":
        return a
    if op == "fliph":
        return cv2.flip(a, 1)
    if op == "flipv":
        return cv2.flip(a, 0)
    if op == "rot180":
        return cv2.rotate(a, cv2.ROTATE_180)
    if op == "cw":
        return cv2.rotate(a, cv2.ROTATE_90_CLOCKWISE)
    if op == "ccw":
        return cv2.rotate(a, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if op == "transpose":
        return cv2.transpose(a)
    if op == "antitranspose":
        return cv2.flip(cv2.transpose(a), -1)
    raise ValueError(op)


def reduction_factor(w: int, h: int, long_side: int) -> int:
    """Largest DCT scale 1/2/4/8 whose result is still at least ``long_side`` px on its long side (never upsamples relative to a render)."""
    f = 1
    while f < 8 and max(w, h) // (f * 2) >= long_side:
        f *= 2
    return f


def pdfium_canvas(w_pt: float, h_pt: float, long_side: int) -> Tuple[int, int]:
    """(width, height) in px of ``PdfPage.render(scale=long_side / max(w_pt, h_pt))``: PDFium's ceil rule."""
    scale = long_side / max(w_pt, h_pt, 1.0)
    return math.ceil(w_pt * scale), math.ceil(h_pt * scale)


# --------------------------------------------------------------------------- #
# Document guards
# --------------------------------------------------------------------------- #
def _doc_key(path) -> tuple:
    p = os.path.abspath(os.fspath(path))
    st = os.stat(p)
    return (p, st.st_size, st.st_mtime_ns)


def token_scan_ok(path, chunk: int = 8 * 1024 * 1024) -> bool:
    """False when the file contains a feature that changes how an image is drawn but is invisible through the PDFium API."""
    tail = b""
    with open(os.fspath(path), "rb") as fh:
        while True:
            buf = fh.read(chunk)
            if not buf:
                return True
            if _TOKENS.search(tail + buf[:32]) or _TOKENS.search(buf):
                return False
            tail = buf[-32:]


def _verdict(path) -> dict:
    key = _doc_key(path)
    with _VERDICT_LOCK:
        v = _VERDICTS.get(key)
        if v is None:
            v = {"lock": threading.Lock(), "tokens": None, "canary": None}
            _VERDICTS[key] = v
            while len(_VERDICTS) > _VERDICT_MAX:
                _VERDICTS.popitem(last=False)
        else:
            _VERDICTS.move_to_end(key)
        return v


# --------------------------------------------------------------------------- #
# Phase A (under the PDFium lock) and phase B (no lock)
# --------------------------------------------------------------------------- #
def _plan_page(pg, long_side: int) -> Tuple[Optional[dict], str]:
    """Eligibility test and raw data of one page; needs the PDFium lock. Returns ``(plan, "")`` or ``(None, reason)``."""
    import pypdfium2 as pdfium
    import pypdfium2.raw as C

    if C.FPDFPage_GetAnnotCount(pg) > 0:
        return None, "annotations"
    n = C.FPDFPage_CountObjects(pg)
    if n > _MAX_OBJECTS:
        return None, "too many objects"
    img = None
    for i in range(n):
        o = C.FPDFPage_GetObject(pg, i)
        t = C.FPDFPageObj_GetType(o)
        if t == _OBJ_IMAGE:
            if img is not None:
                return None, "several images"
            img = o
        elif t == _OBJ_TEXT:
            if C.FPDFTextObj_GetTextRenderMode(o) != 3:       # 3 = invisible text (an OCR layer)
                return None, "visible text"
        else:
            return None, "path / shading / form object"
    if img is None:
        return None, "no image"
    if C.FPDFPageObj_CountMarks(img) > 0:                      # e.g. optional-content (hidden layer) marks
        return None, "marked content on the image"
    if C.FPDFPageObj_HasTransparency(img):
        return None, "transparency"
    clip = C.FPDFPageObj_GetClipPath(img)
    if clip and C.FPDFClipPath_CountPaths(clip) > 0:
        return None, "clip path"
    obj = pdfium.PdfObject(img, page=pg, pdf=pg.pdf)
    if obj.get_filters() != ["DCTDecode"]:
        return None, "filters %s" % (obj.get_filters(),)
    w, h = obj.get_px_size()
    bbox, rot = pg.get_bbox(), pg.get_rotation()
    if rot not in (0, 90, 180, 270):
        return None, "unusual /Rotate"
    op, info = placement(obj.get_matrix().get(), bbox, rot)
    if op is None:
        return None, info
    raw = obj.get_data(decode_simple=False)
    sof = jpeg_sof(raw)
    if sof is None or sof[3] != 8 or sof[2] not in (1, 3) or sof[4] not in (0xC0, 0xC1, 0xC2) or (sof[0], sof[1]) != (w, h):
        return None, "jpeg header %s" % (sof,)
    if sof[4] == 0xC2 and w * h * sof[2] * 2 > _MAX_PROGRESSIVE_BYTES:
        return None, "huge progressive jpeg"
    meta = obj.get_metadata()
    if meta.colorspace not in _GOOD_COLORSPACES or meta.bits_per_pixel != 8 * sof[2]:
        return None, "colour space %s / %s bpp" % (meta.colorspace, meta.bits_per_pixel)
    if max(w, h) < long_side:
        return None, "image smaller than the render canvas"
    w_pt, h_pt = pg.get_size()
    return dict(raw=raw, w=w, h=h, op=op, dims=info, canvas=pdfium_canvas(w_pt, h_pt, long_side)), ""


def _decode(plan: dict, long_side: int) -> Optional[np.ndarray]:
    """Phase B, outside the lock: reduced-size DCT decode, viewer orientation, PDFium's canvas size. None on any surprise."""
    w, h = plan["w"], plan["h"]
    f = reduction_factor(w, h, long_side)
    a = cv2.imdecode(np.frombuffer(plan["raw"], np.uint8), _RED[f] | cv2.IMREAD_IGNORE_ORIENTATION)
    if a is None or a.ndim != 2 or a.shape != (-(-h // f), -(-w // f)):
        return None
    a = apply_op(a, plan["op"])
    cw, ch = plan["canvas"]
    if a.shape != (ch, cw):
        a = cv2.resize(a, (cw, ch), interpolation=cv2.INTER_AREA if a.size > cw * ch else cv2.INTER_LINEAR)
    return np.ascontiguousarray(a)


def _canary_ok(path, page: int, plan: dict, long_side: int) -> bool:
    """Render the page small and compare with the fast raster at the same size (catches /Decode inversions, soft masks, wrong geometry)."""
    small = 256
    fast = _decode(plan, long_side)
    if fast is None:
        return False
    ref = render_pdf_page(path, page, small)                   # takes the PDFium lock itself (we do NOT hold it here)
    h, w = ref.shape
    f = cv2.resize(fast, (w, h), interpolation=cv2.INTER_AREA)
    f, r = (cv2.GaussianBlur(x.astype(np.float32), (0, 0), 1.5) for x in (f, ref))
    mae = float(np.abs(f - r).mean())
    sd = float(r.std())
    ncc = 1.0 if sd < 3.0 else float(((f - f.mean()) * (r - r.mean())).mean() / (f.std() * sd + 1e-9))
    return mae <= 8.0 and (sd < 3.0 or ncc >= 0.97)


def load_pdf_page_gray(path, page: int = 0, long_side: int = 1400, fast: bool = True) -> np.ndarray:
    """Gray raster (long side ~``long_side`` px, as ``render_pdf_page``) of one PDF page, via the JPEG fast path when it is safe."""
    if not enabled(fast):
        return render_pdf_page(path, page, long_side)
    try:
        v = _verdict(path)
    except OSError as e:
        raise ImageReadError(f"could not read PDF: {path}") from e
    with v["lock"]:                                            # one token scan per document (cheap, cached)
        if v["tokens"] is None:
            try:
                v["tokens"] = token_scan_ok(path)
            except OSError as e:
                raise ImageReadError(f"could not read PDF: {path}") from e
    if not v["tokens"]:
        _count("fallback: document has /Decode, /SMask, /Mask or similar")
        return render_pdf_page(path, page, long_side)
    if v["canary"] is False:
        _count("fallback: canary failed for this document")
        return render_pdf_page(path, page, long_side)

    plan, reason = None, "pdf error"
    with _PDFIUM_LOCK:
        pdfium = _pdfium()
        try:
            doc = pdfium.PdfDocument(os.fspath(path))
        except Exception as e:
            raise ImageReadError(f"could not read PDF: {path}") from e
        try:
            if not 0 <= page < len(doc):
                raise ImageReadError(f"PDF {path} has {len(doc)} page(s); page {page} requested")
            pg = doc[page]
            try:
                plan, reason = _plan_page(pg, long_side)
            except ImageReadError:
                raise
            except Exception as e:                             # anything unexpected in the object API: render instead
                plan, reason = None, "plan error: %s" % type(e).__name__
            finally:
                pg.close()
        finally:
            doc.close()
    if plan is None:
        _count("fallback: " + reason)
        return render_pdf_page(path, page, long_side)

    if v["canary"] is None:                                    # first eligible page of the document decides for the whole document
        with v["lock"]:
            if v["canary"] is None:
                v["canary"] = _canary_ok(path, page, plan, long_side)
    if not v["canary"]:
        _count("fallback: canary failed for this document")
        return render_pdf_page(path, page, long_side)
    try:
        arr = _decode(plan, long_side)
    except Exception:
        arr = None
    if arr is None:
        _count("fallback: decode failed")
        return render_pdf_page(path, page, long_side)
    _count("fast")
    return arr
