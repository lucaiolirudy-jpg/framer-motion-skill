# Overlays for the seated cable row comparison (torso line, vertical reference, lean angle arc, swing trail, elbow arrow)
import json, os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.signal import savgol_filter
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D + "/../v2")
import ov  # badge / pill / colours
RED, GREEN, WHITE = ov.RED, ov.GREEN, ov.WHITE
SS = 2
class Track:
    def __init__(self, f):
        P = json.load(open(f"{D}/pose_{f}.json")); A = np.array([np.array(p)[:33] for p in P], dtype=float)
        for k in range(33):
            for c in range(2): A[:, k, c] = savgol_filter(A[:, k, c], 9, 2)
        self.A = A; self.n = len(A); R = json.load(open(f"{D}/reps_{f}.json")); self.ang = np.array(R["ang"])
    def at(self, t, k):  # t in seconds, linear interpolation between 30 fps samples
        x = min(max(t * 30, 0), self.n - 1.001); i = int(x); u = x - i
        return self.A[i, k, :2] * (1 - u) + self.A[i + 1, k, :2] * u
    def angle(self, t):
        x = min(max(t * 30, 0), self.n - 1.001); i = int(x); u = x - i; return self.ang[i] * (1 - u) + self.ang[i + 1] * u
_fn = ImageFont.truetype(D + "/mont900.woff", 46 * SS)
def dot(d, p, col, r=12): ov.dot(d, p, col, r)
def overlay(tr, t, mode, W=1080, H=1920):
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = RED if mode == "bad" else GREEN
    hip, sh = tr.at(t, 23), tr.at(t, 11); L = np.linalg.norm(sh - hip)
    ang = tr.angle(t)
    # vertical dashed reference through the hip
    for y in np.arange(hip[1] - 1.15 * L, hip[1] - 10, 30):
        d.line(((hip[0] * SS, y * SS), (hip[0] * SS, min(y + 17, hip[1]) * SS)), fill=(255, 255, 255, 235), width=4 * SS)
    # swing trail (wrong form): previous torso positions fading out
    if mode == "bad":
        tr_img = Image.new("RGBA", im.size, (0, 0, 0, 0)); td = ImageDraw.Draw(tr_img)
        for k in range(14, 0, -2):
            tt = t - k / 30; h2, s2 = tr.at(tt, 23), tr.at(tt, 11); e2 = s2 + (s2 - h2) * 0.18
            td.line((tuple(h2 * SS), tuple(e2 * SS)), fill=(235, 40, 45, int(150 * (1 - k / 15))), width=8 * SS)
        im = Image.alpha_composite(im, tr_img.filter(ImageFilter.GaussianBlur(2 * SS))); d = ImageDraw.Draw(im)
    # lean angle arc at the hip
    r = 0.42 * L; big = abs(ang) > 15
    acol = (RED if (mode == "bad" and big) else GREEN)
    a0, a1 = -90, -90 + ang  # PIL angles: 0 = +x, clockwise
    lo, hi = min(a0, a1), max(a0, a1)
    if hi - lo > 1:
        arc = Image.new("RGBA", im.size, (0, 0, 0, 0)); ad = ImageDraw.Draw(arc)
        box = ((hip[0] - r) * SS, (hip[1] - r) * SS, (hip[0] + r) * SS, (hip[1] + r) * SS)
        ad.pieslice(box, lo, hi, fill=acol + (90,)); ad.arc(box, lo, hi, fill=acol + (255,), width=5 * SS)
        im = Image.alpha_composite(im, arc); d = ImageDraw.Draw(im)
    if mode == "bad" and big:
        mid = np.radians(-90 + ang / 2); tp = hip + np.array([np.cos(mid), np.sin(mid)]) * (r + 60)
        txt = f"{abs(ang):.0f}°"
        d.text((tp[0] * SS, tp[1] * SS), txt, font=_fn, fill=WHITE, anchor="mm", stroke_width=6 * SS, stroke_fill=RED)
    # torso line hip -> shoulder (extended a little towards the head)
    end = sh + (sh - hip) * 0.18
    ov.line(d, [hip, end], col, w=10); dot(d, hip, col); dot(d, sh, col)
    # elbow arrow (correct form): elbow driving back while pulling
    if False:
        el = tr.at(t, 13); v = tr.at(t + 2 / 30, 13) - tr.at(t - 2 / 30, 13)
        if v[0] > 6:
            a = min(1, (v[0] - 6) / 10); p0 = el + np.array([30, 0]); p1 = el + np.array([30 + 110 * a, 0])
            ov.line(d, [p0, p1], GREEN, w=9)
            hd = [tuple((p1 + np.array([26, 0])) * SS), tuple((p1 + np.array([-6, -22])) * SS), tuple((p1 + np.array([-6, 22])) * SS)]
            d.polygon(hd, fill=GREEN, outline=WHITE)
    return im.resize((W, H), Image.LANCZOS)
