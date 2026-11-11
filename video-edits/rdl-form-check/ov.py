# Pose-driven overlays in the style of the reference (shin line + dots, back line, dumbbell path, depth zone)
import json, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.signal import savgol_filter
import os
D = os.path.dirname(os.path.abspath(__file__))
RED = (235, 40, 45); GREEN = (40, 200, 80); YEL = (255, 222, 0); WHITE = (255, 255, 255)
SS = 2  # supersampling

class Track:
    def __init__(self, f):
        P = json.load(open(f"{D}/pose_{f}.json")); n = len(P)
        arr = np.full((n, 33, 3), np.nan)
        for i, p in enumerate(P):
            if p: arr[i] = np.array(p)[:33]
        idx = np.arange(n)
        for k in range(33):
            for c in range(3):
                v = arr[:, k, c]; ok = ~np.isnan(v)
                if ok.sum() > 10: arr[:, k, c] = savgol_filter(np.interp(idx, idx[ok], v[ok]), 7, 2)
        self.a = arr; self.n = n
        # camera-facing side
        vis = np.nanmean(arr[:, [11, 23, 25, 27], 2]) - np.nanmean(arr[:, [12, 24, 26, 28], 2])
        self.s = 0 if vis >= 0 else 1
        R = json.load(open(f"{D}/reps_{f}.json")); self.ang = np.array(R["ang"]); self.tops = R["tops"]
    def pt(self, i, k): i = min(max(i, 0), self.n - 1); return self.a[i, k + self.s, :2] if k in (11, 13, 15, 23, 25, 27, 29, 31) else self.a[i, k, :2]
    def joints(self, i):
        g = lambda k: self.pt(i, k)
        return dict(sh=g(11), hip=g(23), knee=g(25), ank=g(27), wr=g(15), heel=g(29), toe=g(31), ear=self.a[min(i, self.n - 1), 7 + self.s, :2])

def dot(d, p, col, r=11):
    x, y = p * SS; r *= SS
    d.ellipse((x - r - 4 * SS, y - r - 4 * SS, x + r + 4 * SS, y + r + 4 * SS), fill=WHITE)
    d.ellipse((x - r, y - r, x + r, y + r), fill=col)
def line(d, pts, col, w=9, outline=True):
    pts = [tuple(p * SS) for p in pts]
    if outline: d.line(pts, fill=WHITE, width=(w + 6) * SS, joint="curve")
    d.line(pts, fill=col, width=w * SS, joint="curve")
def bezier(p0, c, p1, n=24):
    t = np.linspace(0, 1, n)[:, None]; return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1

def overlay(tr, i, mode, path_from=None, W=1080, H=1920, show=("shin", "back", "path", "depth")):
    """mode: 'bad' or 'good'. Returns RGBA image W x H in source coordinates."""
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    j = tr.joints(i); col = RED if mode == "bad" else GREEN
    ang = tr.ang[min(i, tr.n - 1)]
    L = np.linalg.norm(j["sh"] - j["hip"]) + 1e-6
    v = (j["sh"] - j["hip"]) / L; nrm = np.array([v[1], -v[0]])
    if nrm[1] > 0: nrm = -nrm  # normal pointing to the back (up)
    if "depth" in show:
        ky = j["knee"][1]
        if mode == "bad" and j["wr"][1] > ky + 25:
            z = Image.new("RGBA", im.size, (0, 0, 0, 0)); zd = ImageDraw.Draw(z)
            x0, x1 = j["knee"][0] - 170, j["knee"][0] + 130
            zd.rectangle((x0 * SS, ky * SS, x1 * SS, (j["wr"][1] + 40) * SS), fill=(235, 40, 45, 70))
            im = Image.alpha_composite(im, z); d = ImageDraw.Draw(im)
        # dashed reference line at knee height
        x0, x1 = j["knee"][0] - 190, j["knee"][0] + 150
        for x in np.arange(x0, x1, 28):
            d.line(((x * SS, ky * SS), (min(x + 16, x1) * SS, ky * SS)), fill=(255, 255, 255, 230), width=4 * SS)
    if "path" in show and path_from is not None:
        pts = [tr.joints(k)["wr"] for k in range(path_from, i + 1)]
        if len(pts) > 1:
            g = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
            gd.line([tuple(p * SS) for p in pts], fill=(255, 222, 0, 255), width=7 * SS, joint="curve")
            im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(6 * SS)))
            d = ImageDraw.Draw(im); line(d, pts, YEL, w=6, outline=False)
    if "back" in show:
        hb = j["hip"] + nrm * 0.11 * L - v * 0.04 * L
        sb = j["sh"] + nrm * 0.15 * L
        if mode == "bad":
            k = np.clip((ang - 35) / 50, 0, 1)
            c = (hb + sb) / 2 + nrm * (0.06 + 0.16 * k) * L
            pts = bezier(hb, c, sb)
        else:
            pts = np.stack([hb, sb])
        line(d, pts, col, w=10); dot(d, hb, col, 10); dot(d, sb, col, 10)
    if "shin" in show:
        line(d, [j["knee"], j["ank"]], col, w=9); dot(d, j["knee"], col); dot(d, j["ank"], col)
    return im.resize((W, H), Image.LANCZOS)

def badge(kind, size=120):
    s = size * 4; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = RED if kind == "x" else GREEN
    d.ellipse((0, 0, s - 1, s - 1), fill=WHITE); m = int(s * 0.045); d.ellipse((m, m, s - 1 - m, s - 1 - m), fill=col)
    w = int(s * 0.11)
    if kind == "x":
        a, b = s * 0.32, s * 0.68
        d.line(((a, a), (b, b)), fill=WHITE, width=w); d.line(((a, b), (b, a)), fill=WHITE, width=w)
        for p in ((a, a), (b, b), (a, b), (b, a)): d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=WHITE)
    else:
        pts = [(s * 0.28, s * 0.52), (s * 0.44, s * 0.68), (s * 0.73, s * 0.36)]
        d.line(pts, fill=WHITE, width=w, joint="curve")
        for p in (pts[0], pts[2]): d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=WHITE)
    return im.resize((size, size), Image.LANCZOS)

_fp = {}
def pill(text, kind, h=78):
    if h not in _fp: _fp[h] = ImageFont.truetype(f"{D}/mont900.woff", int(h * 0.44 * 4))
    f = _fp[h]; s = 4
    tw = f.getlength(text); W = int(tw + h * 4 * 1.35); im = Image.new("RGBA", (W, h * s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = RED if kind == "x" else GREEN
    d.rounded_rectangle((0, 0, W - 1, h * s - 1), radius=h * s // 2, fill=(255, 255, 255, 255))
    m = 3 * s; d.rounded_rectangle((m, m, W - 1 - m, h * s - 1 - m), radius=h * s // 2 - m, fill=col + (255,))
    b = badge(kind, int(h * 0.8 * s)); im.alpha_composite(b, (int(h * 0.1 * s), int(h * 0.1 * s)))
    d.text((h * s * 0.98, h * s / 2), text, font=f, fill=WHITE, anchor="lm")
    return im.resize((W // s, h), Image.LANCZOS)
