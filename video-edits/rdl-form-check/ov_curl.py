# Incline dumbbell curl overlays: upper-arm line vs fixed vertical reference, angle arc, elbow trail, "too high" marker
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.signal import savgol_filter
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D + "/../v2"); import ov
RED, GREEN, WHITE = ov.RED, ov.GREEN, ov.WHITE; SS = 2
class Track:
    def __init__(self, f, side=1):
        A = np.load(f"{D}/A_{f}.npy")
        for k in range(33):
            for c in range(2): A[:, k, c] = savgol_filter(A[:, k, c], 9, 2)
        self.A = A; self.n = len(A); self.s = side
    def at(self, t, k):
        k = k + self.s if k in (11, 13, 15, 23, 25, 27) else k
        x = min(max(t * 30, 0), self.n - 1.001); i = int(x); u = x - i
        return self.A[i, k, :2] * (1 - u) + self.A[i + 1, k, :2] * u
    def upper(self, t):
        sh, el = self.at(t, 11), self.at(t, 13); return np.degrees(np.arctan2(el[0] - sh[0], el[1] - sh[1]))
    def elbow(self, t):
        sh, el, wr = self.at(t, 11), self.at(t, 13), self.at(t, 15); u, v = sh - el, wr - el
        return np.degrees(np.arccos(np.clip(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-6), -1, 1)))
_fn = ImageFont.truetype(D + "/mont900.woff", 44 * SS)
def overlay(tr, t, mode, W=1080, H=1920):
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = RED if mode == "bad" else GREEN
    sh, el, wr = tr.at(t, 11), tr.at(t, 13), tr.at(t, 15); L = np.linalg.norm(el - sh); ua = tr.upper(t)
    # fixed reference: straight down from the shoulder
    for y in np.arange(sh[1] + 20, sh[1] + 1.25 * L, 28):
        d.line(((sh[0] * SS, y * SS), (sh[0] * SS, min(y + 16, sh[1] + 1.25 * L) * SS)), fill=(255, 255, 255, 235), width=4 * SS)
    # angle arc between reference and upper arm
    r = 0.55 * L; big = abs(ua) > 22; acol = RED if (mode == "bad" and big) else GREEN
    a0, a1 = 90, 90 - ua; lo, hi = min(a0, a1), max(a0, a1)
    if hi - lo > 1:
        arc = Image.new("RGBA", im.size, (0, 0, 0, 0)); ad = ImageDraw.Draw(arc)
        box = ((sh[0] - r) * SS, (sh[1] - r) * SS, (sh[0] + r) * SS, (sh[1] + r) * SS)
        ad.pieslice(box, lo, hi, fill=acol + (85,)); ad.arc(box, lo, hi, fill=acol + (255,), width=5 * SS)
        im = Image.alpha_composite(im, arc); d = ImageDraw.Draw(im)
    if mode == "bad":
        # elbow trail (elbow drifting forward)
        tl = Image.new("RGBA", im.size, (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
        pts = [tr.at(t - k / 30, 13) for k in range(16, -1, -1)]
        for i in range(1, len(pts)):
            td.line((tuple(pts[i - 1] * SS), tuple(pts[i] * SS)), fill=(235, 40, 45, int(40 + 200 * i / len(pts))), width=10 * SS)
        im = Image.alpha_composite(im, tl.filter(ImageFilter.GaussianBlur(2 * SS))); d = ImageDraw.Draw(im)
        if big:
            mid = np.radians(90 - ua / 2); tp = sh + np.array([np.cos(mid), np.sin(mid)]) * (r + 58)
            d.text((tp[0] * SS, tp[1] * SS), f"{abs(ua):.0f}°", font=_fn, fill=WHITE, anchor="mm", stroke_width=6 * SS, stroke_fill=RED)
        # dumbbell going too high (up to the shoulder)
        if tr.elbow(t) < 70 and ua > 35:
            z = Image.new("RGBA", im.size, (0, 0, 0, 0)); zd = ImageDraw.Draw(z); R0 = 95
            zd.ellipse(((wr[0] - R0) * SS, (wr[1] - R0) * SS, (wr[0] + R0) * SS, (wr[1] + R0) * SS), fill=(235, 40, 45, 70), outline=(235, 40, 45, 255), width=6 * SS)
            im = Image.alpha_composite(im, z); d = ImageDraw.Draw(im)
    ov.line(d, [sh, el], col, w=10); ov.line(d, [el, wr], col, w=7)
    ov.dot(d, sh, col, 12); ov.dot(d, el, col, 12); ov.dot(d, wr, col, 9)
    return im.resize((W, H), Image.LANCZOS)
