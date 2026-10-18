"""DISE-2021 (+-45 degree skew, GT angle in the file name) evaluation: python -m bench.dise_eval 600 [candidate]

Needs data/external/dise2021/dise2021_45.zip (HF phamquiluan/DISE-2021). Pages are skewed only (no 90/180 flips in the
ground truth) and include many non-Latin, graphics-only and noisy binarised pages: an out-of-domain stress test.
"""
import sys, re, zipfile, numpy as np, cv2
from docangle import DocumentOrientationPipeline
from .candidates import REGISTRY, legacy
z = zipfile.ZipFile('data/external/dise2021/dise2021_45.zip')
names = sorted(n for n in z.namelist() if '/test/' in n and n.endswith('.png'))
print('test images', len(names))
rng = np.random.default_rng(0); pick = [names[i] for i in rng.permutation(len(names))[:int(sys.argv[1])]]
pipe = DocumentOrientationPipeline(REGISTRY[sys.argv[2]]()[1] if len(sys.argv) > 2 else None)
try:
    leg, _ = legacy()
except SystemExit:                                   # the predecessor is not part of the public repository: its column becomes empty
    leg = lambda img: {'pred': None}  # noqa: E731
rows = []
for n in pick:
    gt = float(re.search(r'\[(-?[\d.]+)\]\.png$', n).group(1))
    img = cv2.imdecode(np.frombuffer(z.read(n), np.uint8), cv2.IMREAD_COLOR)
    r = pipe.predict(img); l = leg(img)['pred']
    rows.append((gt, r.angle, r.needs_review, l, img.shape[1]))
a = np.array([(g, p if p is not None else np.nan, rv, lp if lp is not None else np.nan) for g, p, rv, lp, _ in rows], float)
def err(p, g): return np.abs((p - g + 180) % 360 - 180)
for sign in (1, -1):
    print(f"sign {sign:+d}: ours median err {np.nanmedian(err(a[:,1], sign*a[:,0])):.2f}  C8+L {np.nanmedian(err(a[:,3], sign*a[:,0])):.2f}")
sign = 1 if np.nanmedian(err(a[:,1], a[:,0])) < np.nanmedian(err(a[:,1], -a[:,0])) else -1
print("using sign", sign, "| median image width", np.median([r[4] for r in rows]))
for name, col in (("docangle", 1), ("C8+L", 3)):
    e = err(a[:, col], sign * a[:, 0]); ok = ~np.isnan(e)
    print(f"{name:9s} n={ok.sum()} median {np.nanmedian(e):.2f}  <=1deg {np.mean(e[ok]<=1)*100:.1f}%  <=2deg {np.mean(e[ok]<=2)*100:.1f}%  >5deg {int((e[ok]>5).sum())}  flips(>45) {int((e[ok]>45).sum())}")
e = err(a[:, 1], sign * a[:, 0]); print("ours: review flagged", int(a[:,2].sum()), "| >5deg among flagged", int(((e>5)&(a[:,2]==1)).sum()), "| >5deg accepted", int(((e>5)&(a[:,2]==0)).sum()))
bins = [(0,5),(5,15),(15,30),(30,46)]
for lo, hi in bins:
    m = (np.abs(a[:,0])>=lo)&(np.abs(a[:,0])<hi); print(f" |skew| {lo}-{hi}: n={m.sum()} ours <=1deg {np.mean(e[m]<=1)*100:.1f}% >5deg {int((e[m]>5).sum())}")
