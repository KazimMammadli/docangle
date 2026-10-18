"""PDF input: render one page to a grayscale array (needs the optional ``pypdfium2`` package).

    from docangle.pdf import render_pdf_page, pdf_page_count
    gray = render_pdf_page("scan.pdf", page=0)        # uint8 HxW, long side ~ ``long_side`` px
    res = get_pipeline().predict(gray)

Pages of scanned PDFs are usually one embedded raster image; rendering at ~150 dpi equivalent keeps the
decode cost small and gives the pipeline the same kind of input as an image file.
"""
from __future__ import annotations

import os
import threading
from typing import Union

import cv2
import numpy as np

from .errors import DocAngleError, ImageReadError

PathLike = Union[str, "os.PathLike[str]"]

# PDFium is not thread-safe: concurrent open/render calls from several threads corrupt its heap (observed: "double free or corruption" and
# unreadable pages in a 4-thread run over a 100-page PDF). All PDFium work is serialised; the analysis that follows still runs in parallel.
_PDFIUM_LOCK = threading.RLock()


def _pdfium():
    try:
        import pypdfium2 as pdfium  # noqa: WPS433 (optional dependency)
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise DocAngleError("PDF input needs pypdfium2: pip install 'docangle[pdf]'") from e
    return pdfium


def pdf_page_count(path: PathLike) -> int:
    with _PDFIUM_LOCK:
        return _pdf_page_count(path)


def _pdf_page_count(path: PathLike) -> int:
    pdfium = _pdfium()
    try:
        doc = pdfium.PdfDocument(os.fspath(path))
    except Exception as e:  # pypdfium2 raises PdfiumError for unreadable files
        raise ImageReadError(f"could not read PDF: {path}") from e
    try:
        return len(doc)
    finally:
        doc.close()


def render_pdf_page(path: PathLike, page: int = 0, long_side: int = 1400, color: bool = False) -> np.ndarray:
    """Render ``page`` (0-based) as a uint8 array whose longer side is about ``long_side`` px.

    Grayscale (HxW) by default; ``color=True`` returns BGR (HxWx3) for producing an upright colour image.

    The page's /Rotate flag is applied by the renderer, i.e. the result is what a PDF viewer shows.
    That is the right thing to analyse: a scan that is sideways *in the viewer* is what needs fixing.
    """
    with _PDFIUM_LOCK:
        return _render_pdf_page(path, page, long_side, color)


def _render_pdf_page(path: PathLike, page: int, long_side: int, color: bool) -> np.ndarray:
    pdfium = _pdfium()
    try:
        doc = pdfium.PdfDocument(os.fspath(path))
    except Exception as e:
        raise ImageReadError(f"could not read PDF: {path}") from e
    try:
        if not 0 <= page < len(doc):
            raise ImageReadError(f"PDF {path} has {len(doc)} page(s); page {page} requested")
        try:
            pg = doc[page]
            try:
                w_pt, h_pt = pg.get_size()  # points (1/72 in), already rotated by /Rotate
                scale = long_side / max(w_pt, h_pt, 1.0)
                bmp = pg.render(scale=scale, grayscale=not color)
                arr = np.ascontiguousarray(bmp.to_numpy())
            finally:
                pg.close()
        except ImageReadError:
            raise
        except Exception as e:              # PdfiumError: damaged page object, unsupported stream ...: this page only, not the whole job
            raise ImageReadError(f"could not render page {page} of {path}: {e}") from e
    finally:
        doc.close()
    if color:
        return arr[:, :, :3] if arr.ndim == 3 else cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    return arr[:, :, 0] if arr.ndim == 3 else arr
