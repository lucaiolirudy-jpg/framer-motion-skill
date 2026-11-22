# Hanging knee raise overlays: torso line vs vertical from the shoulder, swing angle arc, hip swing trail, thigh line
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D + "/../v2"); import ov
RED, GREEN, WHITE = ov.RED, ov.GREEN, ov.WHITE; SS = 2
class Track:
    def __init__(self, f, side=0): self.A = np.load(f"{D}/A_{f}.npy"); self.n = len(self.A); self.s = side
    def at(self, t, k):
        k = k + self.s if k in (11, 13, 15, 23, 25, 27) else k
        x = min(max(t * 30, 0), self.n - 1.001); i = int(x); u = x - i
        return self.A[i, k, :2] * (1 - u) + self.A[i + 1, k, :2] * u
    def torso(self, t):
        sh, hp = self.at(t, 11), self.at(t, 23); return np.degrees(np.arctan2(hp[0] - sh[0], hp[1] - sh[1]))
_fn = ImageFont.truetype(D + "/mont900.woff", 44 * SS)
def overlay(tr, t, mode, W=1080, H=1920):
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = RED if mode == "bad" else GREEN
    sh, hp, kn = tr.at(t, 11), tr.at(t, 23), tr.at(t, 25); L = np.linalg.norm(hp - sh); ta = tr.torso(t)
    for y in np.arange(sh[1] + 20, sh[1] + 1.3 * L, 28):
        d.line(((sh[0] * SS, y * SS), (sh[0] * SS, min(y + 16, sh[1] + 1.3 * L) * SS)), fill=(255, 255, 255, 235), width=4 * SS)
    r = 0.5 * L; big = abs(ta) > 18; acol = RED if (mode == "bad" and big) else GREEN
    a0, a1 = 90, 90 - ta; lo, hi = min(a0, a1), max(a0, a1)
    if hi - lo > 1:
        arc = Image.new("RGBA", im.size, (0, 0, 0, 0)); ad = ImageDraw.Draw(arc)
        box = ((sh[0] - r) * SS, (sh[1] - r) * SS, (sh[0] + r) * SS, (sh[1] + r) * SS)
        ad.pieslice(box, lo, hi, fill=acol + (85,)); ad.arc(box, lo, hi, fill=acol + (255,), width=5 * SS)
        im = Image.alpha_composite(im, arc); d = ImageDraw.Draw(im)
    if mode == "bad":
        tl = Image.new("RGBA", im.size, (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
        for k in range(16, 0, -2):
            tt = t - k / 30; s2, h2 = tr.at(tt, 11), tr.at(tt, 23)
            td.line((tuple(s2 * SS), tuple(h2 * SS)), fill=(235, 40, 45, int(150 * (1 - k / 17))), width=8 * SS)
        im = Image.alpha_composite(im, tl.filter(ImageFilter.GaussianBlur(2 * SS))); d = ImageDraw.Draw(im)
        if big:
            mid = np.radians(90 - ta / 2); tp = sh + np.array([np.cos(mid), np.sin(mid)]) * (r + 58)
            d.text((tp[0] * SS, tp[1] * SS), f"{abs(ta):.0f}°", font=_fn, fill=WHITE, anchor="mm", stroke_width=6 * SS, stroke_fill=RED)
    ov.line(d, [hp, kn], col, w=7); ov.dot(d, kn, col, 9)
    ov.line(d, [sh, hp], col, w=10); ov.dot(d, sh, col, 12); ov.dot(d, hp, col, 12)
    return im.resize((W, H), Image.LANCZOS)
