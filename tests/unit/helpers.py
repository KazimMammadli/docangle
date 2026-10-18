import numpy as np


def ruled_page(h=1400, w=1000, seed=0):
    """Synthetic page: ruled horizontal text-like lines + a table frame (strong long edges)."""
    import cv2
    rng = np.random.default_rng(seed)
    img = np.full((h, w, 3), 255, np.uint8)
    for y in range(120, h - 120, 34):
        x0 = 100 + int(rng.integers(0, 30))
        cv2.line(img, (x0, y), (w - 100 - int(rng.integers(0, 60)), y), (0, 0, 0), 2)
    cv2.rectangle(img, (80, 80), (w - 80, h - 80), (0, 0, 0), 2)
    return img


def make_scan_pdf(path, pages, rotate=0, dpi=150):
    """Write a PDF with one full-page raster image per entry of ``pages`` (uint8 gray arrays).

    ``rotate`` sets the /Rotate key of every page (what a viewer shows is the image turned clockwise by it).
    No third-party PDF library needed: the file is assembled by hand.
    """
    import zlib

    objs = []   # bytes of each object body, 1-based numbering

    def add(body):
        objs.append(body)
        return len(objs)

    cat = add(b"")          # 1: catalog, filled in below
    pages_obj = add(b"")    # 2: page tree, filled in below
    kids = []
    for g in pages:
        h, w = g.shape
        data = zlib.compress(g.tobytes())
        img = add(b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceGray "
                  b"/BitsPerComponent 8 /Filter /FlateDecode /Length %d >>\nstream\n" % (w, h, len(data)) + data + b"\nendstream")
        wp, hp = w * 72.0 / dpi, h * 72.0 / dpi
        content = b"q %f 0 0 %f 0 0 cm /Im0 Do Q" % (wp, hp)
        cs = add(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        pg = add(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %f %f] /Rotate %d /Contents %d 0 R "
                 b"/Resources << /XObject << /Im0 %d 0 R >> >> >>" % (wp, hp, rotate, cs, img))
        kids.append(pg)
    objs[cat - 1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[pages_obj - 1] = b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % k for k in kids) + b"] /Count %d >>" % len(kids)
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offsets:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    with open(path, "wb") as f:
        f.write(bytes(out))


def jpeg_bytes(gray_or_bgr, quality=85, progressive=False, exif_orientation=None):
    """JPEG bytes of an array; optionally progressive and with an EXIF Orientation tag (which PDFium ignores inside a PDF)."""
    import cv2
    params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    if progressive:
        params += [cv2.IMWRITE_JPEG_PROGRESSIVE, 1]
    data = cv2.imencode(".jpg", gray_or_bgr, params)[1].tobytes()
    if exif_orientation is not None:
        tiff = b"II*\x00\x08\x00\x00\x00" + b"\x01\x00" + b"\x12\x01\x03\x00\x01\x00\x00\x00" + bytes([exif_orientation, 0, 0, 0]) + b"\x00\x00\x00\x00"
        seg = b"Exif\x00\x00" + tiff
        data = data[:2] + b"\xff\xe1" + (len(seg) + 2).to_bytes(2, "big") + seg + data[2:]
    return data


def build_pdf(pages):
    """Hand-built PDF for the PDF fast-path tests. ``pages`` is a list of dicts:
    mediabox=(w, h) points, rotate=int, images=[dict(data, w, h, cs=b'/DeviceGray', filter=b'/DCTDecode', extra=b'', cm=(a,b,c,d,e,f), smask=False)],
    pre=b'' / post=b'' (content-stream operators before / after the images), resources=b'' (extra /Resources entries), annots=bool, page_extra=b''.
    Returns the PDF bytes."""
    objs = []

    def add(body):
        objs.append(body)
        return len(objs)

    cat = add(b"")
    pages_obj = add(b"")
    kids = []
    for pg in pages:
        w_pt, h_pt = pg.get("mediabox", (420.0, 594.0))
        xobj, content = [], [pg.get("pre", b"")]
        for k, im in enumerate(pg["images"]):
            extra = im.get("extra", b"")
            if im.get("smask"):
                sm = add(b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceGray /BitsPerComponent 8 /Length 1 >>\nstream\n\xff\nendstream")
                extra += b" /SMask %d 0 R" % sm
            data = im["data"]
            oid = add(b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace %s /BitsPerComponent 8 /Filter %s %s /Length %d >>\nstream\n"
                      % (im["w"], im["h"], im.get("cs", b"/DeviceGray"), im.get("filter", b"/DCTDecode"), extra, len(data)) + data + b"\nendstream")
            xobj.append(b"/Im%d %d 0 R" % (k, oid))
            a, b, c, d, e, f = im.get("cm", (w_pt, 0, 0, h_pt, 0, 0))
            content.append(b"q %f %f %f %f %f %f cm /Im%d Do Q" % (a, b, c, d, e, f, k))
        content.append(pg.get("post", b""))
        stream = b"\n".join(content)
        cs = add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        extra_page = pg.get("page_extra", b"")
        if pg.get("annots"):
            an = add(b"<< /Type /Annot /Subtype /Square /Rect [10 10 60 60] /C [1 0 0] >>")
            extra_page += b" /Annots [%d 0 R]" % an
        kids.append(add(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %f %f] /Rotate %d /Contents %d 0 R /Resources << /XObject << %s >> %s >> %s >>"
                        % (w_pt, h_pt, pg.get("rotate", 0), cs, b" ".join(xobj), pg.get("resources", b""), extra_page)))
    objs[cat - 1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[pages_obj - 1] = b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % k for k in kids) + b"] /Count %d >>" % len(kids)
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offsets:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)
