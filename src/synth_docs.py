"""Procedural Latin-script (Azerbaijani-flavoured) office documents for orientation training.

Pages are upright A4 at ~150 dpi, grayscale uint8. Content is pseudo-text: real Azerbaijani business
words mixed with syllable-built words, so letter shapes (ə ı ö ü ç ş ğ İ, ascenders/descenders) and
typical office layout priors (letterhead on top, signature/total/page number at the bottom, ragged-right
text) are present. It is NOT real language; it is used together with real scans, never alone.
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1240, 1754

_FONT_SETS = [
    ("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf", "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf"),
    ("/usr/share/fonts/liberation-serif-fonts/LiberationSerif-Regular.ttf", "/usr/share/fonts/liberation-serif-fonts/LiberationSerif-Bold.ttf"),
    ("/usr/share/fonts/google-carlito-fonts/Carlito-Regular.ttf", "/usr/share/fonts/google-carlito-fonts/Carlito-Bold.ttf"),
    ("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf", "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-Regular.otf", "/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-Regular.otf"),
    ("/usr/share/fonts/abattis-cantarell-fonts/Cantarell-Regular.otf", "/usr/share/fonts/abattis-cantarell-fonts/Cantarell-Regular.otf"),
]


def _matplotlib_dejavu():
    """DejaVu Sans ships with matplotlib: a font set that exists on every machine that has it."""
    try:
        import matplotlib
        d = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
        return [(os.path.join(d, "DejaVuSans.ttf"), os.path.join(d, "DejaVuSans-Bold.ttf"))]
    except ImportError:
        return []


FONT_SETS = [fs for fs in _FONT_SETS + _matplotlib_dejavu() if all(os.path.exists(p) for p in fs)]
_FONT_CACHE = {}

WORDS = ("Azərbaycan Respublikası Nazirliyi əmr qərar müqavilə işçi əmək haqqı tarix səhifə məbləğ ödəniş hesab faktura "
         "məhsul xidmət miqdar qiymət cəmi ƏDV təsdiq imza möhür direktor mühasib şirkət ünvan telefon Bakı şəhəri küçəsi "
         "rayon maddə bənd qanun təlimat icra hazırlanmış əsasında müəssisə əməkdaş vəzifə maaş məzuniyyət göndərilmişdir "
         "təqdim edilir müvafiq olaraq nəzərə alınmaqla tərəflər öhdəlik məsuliyyət razılaşma qüvvəyə minir müddət ərzində "
         "məlumat sənəd şəxs ödənilməlidir bank hesabı VÖEN kod şöbə rəis müavini komissiya iclas protokol qeyd mövzu "
         "müraciət cavab əlavə nömrə il ay gün saat dəqiqə İdarə Heyəti Təşkilat İşçi Qrupu layihə büdcə xərc gəlir "
         "mədaxil məxaric anbar təhvil təslim alıcı satıcı sifariş çatdırılma ödəmə şərtləri yekun").split()
SYL = ["ba", "da", "qa", "la", "ma", "na", "ra", "sa", "ta", "ya", "za", "ər", "ıq", "ın", "ən", "li", "ci", "çi", "şı", "ğa",
       "mə", "tə", "rə", "nə", "kə", "gə", "və", "yə", "zə", "ol", "ul", "öz", "üz", "ça", "şa", "ho", "bu", "du", "ku", "ri"]
FIRST = ["Əli", "Vüsal", "Günel", "Səbinə", "Rəşad", "Nigar", "Elçin", "Aygün", "Tural", "Leyla", "Orxan", "Şəhla", "Cavid", "Ülviyyə"]
LAST = ["Məmmədov", "Əliyev", "Hüseynov", "Quliyeva", "Həsənov", "Abbasov", "İsmayılova", "Rzayev", "Qasımov", "Nəbiyev"]


def _font(rng, bold=False, size=24, fs=None):
    fs = fs or FONT_SETS[int(rng.integers(len(FONT_SETS)))]
    path = fs[1 if bold else 0]
    key = (path, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(path, size)
    return _FONT_CACHE[key]


def _word(rng):
    if rng.random() < 0.7:
        w = WORDS[int(rng.integers(len(WORDS)))]
    else:
        w = "".join(SYL[int(rng.integers(len(SYL)))] for _ in range(int(rng.integers(2, 5))))
    r = rng.random()
    if r < 0.08:
        w = w.upper().replace("I", "İ") if rng.random() < 0.5 else w.capitalize()
    elif r < 0.2:
        w = w.capitalize()
    return w


def _sentence(rng, n=None):
    n = n or int(rng.integers(5, 14))
    s = " ".join(_word(rng) for _ in range(n))
    return s + ("." if rng.random() < 0.8 else ";")


def _num(rng, lo=1, hi=9999):
    v = float(rng.uniform(lo, hi))
    return f"{v:,.2f}".replace(",", " ")


def _date(rng):
    return f"{int(rng.integers(1, 29)):02d}.{int(rng.integers(1, 13)):02d}.{int(rng.integers(2015, 2027))}"


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _paragraphs(draw, rng, x, y, w, y_max, font, line_h, indent=True, numbered=False, justify=False):
    k = 1
    while y < y_max - line_h:
        text = _sentence(rng, int(rng.integers(12, 60)))
        if numbered:
            text = f"{k}. " + text
            k += 1
        lines = _wrap(draw, text, font, w - (40 if indent else 0))
        for i, ln in enumerate(lines):
            if y > y_max - line_h:
                return y
            xx = x + (40 if (indent and i == 0) else 0)
            draw.text((xx, y), ln, fill=int(rng.integers(0, 50)), font=font)
            y += line_h
        y += int(line_h * rng.uniform(0.2, 0.8))
    return y


def _scribble(draw, rng, x, y, w, h):
    pts = [(x + i * w / 12, y + h / 2 + rng.normal(0, h / 3)) for i in range(13)]
    draw.line(pts, fill=int(rng.integers(0, 60)), width=int(rng.integers(2, 4)), joint="curve")


def _stamp(draw, rng, cx, cy, r):
    g = int(rng.integers(60, 140))
    for rr in (r, r - 6, r // 2):
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=g, width=3)
    f = _font(rng, True, 16)
    for i, ang in enumerate(np.linspace(-1.2, 1.2, 8)):
        draw.text((cx + (r - 24) * np.sin(ang) - 5, cy - (r - 24) * np.cos(ang) - 8), _word(rng)[0].upper(), fill=g, font=f)


def _footer(draw, rng, fs):
    f = _font(rng, False, int(rng.integers(18, 22)), fs)
    r = rng.random()
    if r < 0.5:
        t = f"{int(rng.integers(1, 12))}"
        draw.text((W // 2 - 6, H - 90), t, fill=40, font=f)
    elif r < 0.75:
        draw.text((W - 200, H - 90), f"Səhifə {int(rng.integers(1, 9))}/{int(rng.integers(1, 12))}", fill=40, font=f)


def _letter(rng, fs):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    m = int(rng.integers(100, 170))
    fb = _font(rng, True, int(rng.integers(30, 40)), fs)
    fm = _font(rng, False, int(rng.integers(21, 27)), fs)
    y = int(rng.integers(70, 140))
    org = _sentence(rng, 3).rstrip(".").upper()
    d.text((W // 2 - d.textlength(org, font=fb) / 2, y), org, fill=20, font=fb)
    y += 70
    d.line([(m, y), (W - m, y)], fill=30, width=int(rng.integers(2, 5)))
    y += 40
    d.text((m, y), f"№ {int(rng.integers(1, 999))}/{int(rng.integers(1, 99))}", fill=30, font=fm)
    d.text((W - m - 220, y), _date(rng), fill=30, font=fm)
    y += 100
    t = ["ƏMR", "QƏRAR", "MÜQAVİLƏ", "TƏLİMAT", "MƏLUMAT VƏRƏQƏSİ"][int(rng.integers(5))]
    d.text((W // 2 - d.textlength(t, font=fb) / 2, y), t, fill=20, font=fb)
    y += 90
    y = _paragraphs(d, rng, m, y, W - 2 * m, H - 420, fm, int(fm.size * 1.45), numbered=rng.random() < 0.5)
    y = max(y + 40, H - 380)
    d.text((m, y), _word(rng).capitalize() + " " + _word(rng), fill=20, font=_font(rng, True, 24, fs))
    d.text((W - m - 260, y), f"{rng.choice(FIRST)} {rng.choice(LAST)}", fill=20, font=fm)
    _scribble(d, rng, W - m - 420, y - 30, 220, 60)
    if rng.random() < 0.6:
        _stamp(d, rng, int(W - m - 150), int(y + 20), 70)
    _footer(d, rng, fs)
    return img


def _invoice(rng, fs):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    m = int(rng.integers(70, 130))
    fb = _font(rng, True, int(rng.integers(28, 38)), fs)
    fm = _font(rng, False, int(rng.integers(19, 24)), fs)
    y = int(rng.integers(60, 120))
    d.text((m, y), _sentence(rng, 2).rstrip(".").upper(), fill=20, font=fb)
    d.text((W - m - 380, y), f"HESAB-FAKTURA № {int(rng.integers(1, 99999))}", fill=20, font=_font(rng, True, 26, fs))
    d.text((W - m - 380, y + 40), _date(rng), fill=30, font=fm)
    y += 140
    for lab in ("Satıcı", "Alıcı", "VÖEN", "Ünvan"):
        d.text((m, y), f"{lab}: {_sentence(rng, int(rng.integers(2, 6))).rstrip('.')}", fill=30, font=fm)
        y += int(fm.size * 1.5)
    y += 40
    cols = [60, 380, 130, 160, 200]
    scale = (W - 2 * m) / sum(cols)
    xs = [m]
    for c in cols:
        xs.append(xs[-1] + int(c * scale))
    heads = ["№", "Məhsul / xidmət", "Say", "Qiymət", "Məbləğ"]
    rows = int(rng.integers(6, 22))
    rh = int(fm.size * 1.9)
    grid = rng.random() < 0.85
    for r in range(rows + 1):
        yy = y + r * rh
        if grid:
            d.line([(m, yy), (xs[-1], yy)], fill=40, width=2)
        for ci in range(5):
            txt = heads[ci] if r == 0 else [str(r), _sentence(rng, int(rng.integers(1, 4))).rstrip('.'), str(int(rng.integers(1, 99))), _num(rng, 1, 500), _num(rng, 1, 9000)][ci]
            ff = _font(rng, True, fm.size, fs) if r == 0 else fm
            if ci >= 2 and r > 0:
                d.text((xs[ci + 1] - 12 - d.textlength(txt, font=ff), yy + 8), txt, fill=20, font=ff)
            else:
                d.text((xs[ci] + 10, yy + 8), txt, fill=20, font=ff)
    yb = y + (rows + 1) * rh
    if grid:
        d.line([(m, yb), (xs[-1], yb)], fill=40, width=2)
        for x in xs:
            d.line([(x, y), (x, yb)], fill=40, width=2)
    y = yb + 40
    for lab in ("Cəmi", "ƏDV 18%", "Yekun məbləğ"):
        d.text((xs[3] - 80, y), lab, fill=20, font=_font(rng, True, fm.size, fs))
        t = _num(rng, 100, 99999) + " AZN"
        d.text((xs[-1] - d.textlength(t, font=fm), y), t, fill=20, font=fm)
        y += int(fm.size * 1.6)
    y = max(y + 60, H - 330)
    d.text((m, y), "Direktor: " + f"{rng.choice(FIRST)} {rng.choice(LAST)}", fill=20, font=fm)
    d.text((m, y + 70), "Mühasib: " + f"{rng.choice(FIRST)} {rng.choice(LAST)}", fill=20, font=fm)
    _scribble(d, rng, m + 330, y - 15, 180, 50)
    _scribble(d, rng, m + 330, y + 55, 180, 50)
    if rng.random() < 0.6:
        _stamp(d, rng, W - m - 140, y + 30, 75)
    _footer(d, rng, fs)
    return img


def _form(rng, fs):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    m = int(rng.integers(90, 150))
    fb = _font(rng, True, int(rng.integers(28, 36)), fs)
    fm = _font(rng, False, int(rng.integers(20, 26)), fs)
    y = int(rng.integers(70, 130))
    d.text((m, y), _sentence(rng, 4).rstrip(".").upper(), fill=20, font=fb)
    y += 90
    cols = int(rng.integers(1, 3))
    cw = (W - 2 * m) // cols
    while y < H - 260:
        for c in range(cols):
            x = m + c * cw
            lab = _word(rng).capitalize() + ":"
            d.text((x, y), lab, fill=30, font=_font(rng, True, fm.size, fs))
            lx = x + d.textlength(lab, font=fm) + 14
            d.line([(lx, y + fm.size + 6), (x + cw - 30, y + fm.size + 6)], fill=60, width=2)
            if rng.random() < 0.6:
                d.text((lx + 6, y), _sentence(rng, int(rng.integers(1, 4))).rstrip(".;"), fill=15, font=fm)
        y += int(fm.size * 2.2)
        if rng.random() < 0.12:
            y = _paragraphs(d, rng, m, y, W - 2 * m, min(H - 260, y + 200), fm, int(fm.size * 1.4))
    _scribble(d, rng, m, H - 230, 220, 60)
    _footer(d, rng, fs)
    return img


def _report(rng, fs):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    m = int(rng.integers(90, 150))
    fb = _font(rng, True, int(rng.integers(26, 34)), fs)
    fm = _font(rng, False, int(rng.integers(20, 25)), fs)
    y = int(rng.integers(90, 160))
    if rng.random() < 0.7:
        d.text((m, y), _sentence(rng, 5).rstrip("."), fill=20, font=fb)
        y += 90
    ncol = int(rng.integers(1, 3))
    gap = 50
    cw = (W - 2 * m - gap * (ncol - 1)) // ncol
    for c in range(ncol):
        _paragraphs(d, rng, m + c * (cw + gap), y, cw, H - 150, fm, int(fm.size * 1.4), indent=rng.random() < 0.6)
    _footer(d, rng, fs)
    return img


def make_page(rng: np.random.Generator) -> np.ndarray:
    """One random upright synthetic page (H x W uint8, grayscale)."""
    fs = FONT_SETS[int(rng.integers(len(FONT_SETS)))]
    kind = rng.random()
    img = _letter(rng, fs) if kind < 0.3 else _invoice(rng, fs) if kind < 0.6 else _form(rng, fs) if kind < 0.8 else _report(rng, fs)
    return np.asarray(img)
