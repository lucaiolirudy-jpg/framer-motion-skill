# Standing barbell curl overlays: torso line vs vertical from the hip (+ swing arc / degrees / trail),
# upper arm vs vertical from the shoulder (+ elbow trail on wrong form)
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D + "/../v2"); import ov
RED, GREEN, WHITE = ov.RED, ov.GREEN, ov.WHITE; SS = 2
class Track:
    def __init__(self, f, side=1): self.A = np.load(f"{D}/A_{f}.npy"); self.n = len(self.A); self.s = side
    def at(self, t, k):
        k = k + self.s if k in (11, 13, 15, 23, 25, 27) else k
        x = min(max(t * 30, 0), self.n - 1.001); i = int(x); u = x - i
        return self.A[i, k, :2] * (1 - u) + self.A[i + 1, k, :2] * u
    def torso(self, t): sh, hp = self.at(t, 11), self.at(t, 23); return np.degrees(np.arctan2(sh[0] - hp[0], hp[1] - sh[1]))
    def upper(self, t): sh, el = self.at(t, 11), self.at(t, 13); return np.degrees(np.arctan2(el[0] - sh[0], el[1] - sh[1]))
_fn = ImageFont.truetype(D + "/mont900.woff", 42 * SS)
def dashed_v(d, x, y0, y1):
    for y in np.arange(y0, y1, 28): d.line(((x * SS, y * SS), (x * SS, min(y + 16, y1) * SS)), fill=(255, 255, 255, 235), width=4 * SS)
def overlay(tr, t, mode, W=1080, H=1920):
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = RED if mode == "bad" else GREEN
    sh, el, wr, hp = (tr.at(t, k) for k in (11, 13, 15, 23)); L = np.linalg.norm(sh - hp); ta = tr.torso(t)
    dashed_v(d, hp[0], hp[1] - 1.15 * L, hp[1] - 15)                     # torso reference
    dashed_v(d, sh[0], sh[1] + 15, sh[1] + 0.75 * L)                     # upper-arm reference
    r = 0.5 * L; big = abs(ta) > 8; acol = RED if (mode == "bad" and big) else GREEN
    a0, a1 = -90, -90 + ta; lo, hi = min(a0, a1), max(a0, a1)
    if hi - lo > 1:
        arc = Image.new("RGBA", im.size, (0, 0, 0, 0)); ad = ImageDraw.Draw(arc)
        box = ((hp[0] - r) * SS, (hp[1] - r) * SS, (hp[0] + r) * SS, (hp[1] + r) * SS)
        ad.pieslice(box, lo, hi, fill=acol + (85,)); ad.arc(box, lo, hi, fill=acol + (255,), width=5 * SS)
        im = Image.alpha_composite(im, arc); d = ImageDraw.Draw(im)
    if mode == "bad":
        tl = Image.new("RGBA", im.size, (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
        for k in range(14, 0, -2):
            tt = t - k / 30; h2, s2 = tr.at(tt, 23), tr.at(tt, 11)
            td.line((tuple(h2 * SS), tuple(s2 * SS)), fill=(235, 40, 45, int(140 * (1 - k / 15))), width=8 * SS)
        pts = [tr.at(t - k / 30, 13) for k in range(14, -1, -1)]
        for i in range(1, len(pts)):
            td.line((tuple(pts[i - 1] * SS), tuple(pts[i] * SS)), fill=(235, 40, 45, int(40 + 200 * i / len(pts))), width=9 * SS)
        im = Image.alpha_composite(im, tl.filter(ImageFilter.GaussianBlur(2 * SS))); d = ImageDraw.Draw(im)
        if big:
            mid = np.radians(-90 + ta / 2); tp = hp + np.array([np.cos(mid), np.sin(mid)]) * (r + 55)
            d.text((tp[0] * SS, tp[1] * SS), f"{abs(ta):.0f}°", font=_fn, fill=WHITE, anchor="mm", stroke_width=6 * SS, stroke_fill=RED)
    ov.line(d, [hp, sh], col, w=10); ov.line(d, [sh, el], col, w=8); ov.line(d, [el, wr], col, w=6)
    ov.dot(d, hp, col, 12); ov.dot(d, sh, col, 12); ov.dot(d, el, col, 10); ov.dot(d, wr, col, 8)
    return im.resize((W, H), Image.LANCZOS)
