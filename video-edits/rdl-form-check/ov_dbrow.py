# One-arm dumbbell row overlays: torso line (+ rotation trail), arm line, hip->foot leg line with vertical reference,
# footprint + foot-movement arrow (correct form), elbow-to-hip arrow
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D + "/../v2"); import ov
RED, GREEN, WHITE = ov.RED, ov.GREEN, ov.WHITE; SS = 2
class Track:
    def __init__(self, f, side=1):
        self.A = np.load(f"{D}/A_{f}.npy"); self.n = len(self.A); self.s = side
    def at(self, t, k):
        k = k + self.s if k in (11, 13, 15, 23, 25, 27, 29, 31) else k
        x = min(max(t * 30, 0), self.n - 1.001); i = int(x); u = x - i
        return self.A[i, k, :2] * (1 - u) + self.A[i + 1, k, :2] * u
def arrow(d, p0, p1, col, w=9, head=26):
    ov.line(d, [p0, p1], col, w=w)
    v = p1 - p0; L = np.linalg.norm(v) + 1e-6; u = v / L; nrm = np.array([-u[1], u[0]])
    tip = p1 + u * head * 0.9; a = p1 - u * 4 + nrm * head * 0.85; b = p1 - u * 4 - nrm * head * 0.85
    d.polygon([tuple(tip * SS), tuple(a * SS), tuple(b * SS)], fill=col, outline=WHITE, width=3 * SS)
def footprint(img, heel, toe, col, alpha=150):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    c = (heel + toe) / 2 + np.array([0, 18]); v = toe - heel; L = max(np.linalg.norm(v), 120) * 1.15
    ang = np.degrees(np.arctan2(v[1], v[0]))
    w, h = int(L * SS), int(L * 0.42 * SS)
    e = Image.new("RGBA", (w + 12 * SS, h + 12 * SS), (0, 0, 0, 0)); ed = ImageDraw.Draw(e)
    ed.ellipse((6 * SS, 6 * SS, w + 6 * SS, h + 6 * SS), fill=col + (alpha,), outline=WHITE + (255,), width=4 * SS)
    e = e.rotate(-ang, expand=True, resample=Image.BICUBIC)
    lay.alpha_composite(e, (int(c[0] * SS - e.width / 2), int(c[1] * SS - e.height / 2)))
    return Image.alpha_composite(img, lay)
def overlay(tr, t, mode, foot_from=None, W=1080, H=1920):
    im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = RED if mode == "bad" else GREEN
    hip, sh, el, wr, ank = (tr.at(t, k) for k in (23, 11, 13, 15, 27))
    heel, toe = tr.at(t, 29), tr.at(t, 31); floor = max(heel[1], toe[1]) + 10
    # vertical reference from the hip to the floor
    for y in np.arange(hip[1] + 20, floor, 30):
        d.line(((hip[0] * SS, y * SS), (hip[0] * SS, min(y + 17, floor) * SS)), fill=(255, 255, 255, 235), width=4 * SS)
    if mode == "good":
        # foot movement: arrow following the foot from where it started to where it is now
        if foot_from is not None and t > foot_from + 0.1:
            pts = [tr.at(x, 27) for x in np.arange(foot_from, t, 1 / 30)]
            if np.linalg.norm(pts[-1] - pts[0]) > 40:
                g = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
                p0, p1 = pts[0] + np.array([0, 60]), pts[-1] + np.array([0, 60])
                gd.line([tuple(p0 * SS), tuple(p1 * SS)], fill=GREEN + (255,), width=10 * SS)
                im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(5 * SS))); d = ImageDraw.Draw(im)
                arrow(d, p0, p1, GREEN)
        im = footprint(im, heel, toe, GREEN); d = ImageDraw.Draw(im)
    else:
        # gap between the hip vertical and the foot (foot too far back)
        y = floor + 30; arrow(d, np.array([hip[0], y]), np.array([ank[0] + 20, y]), RED, w=7, head=20)
        im = footprint(im, heel, toe, RED, 120); d = ImageDraw.Draw(im)
        # torso rotation trail
        tl = Image.new("RGBA", im.size, (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
        for k in range(14, 0, -2):
            tt = t - k / 30; h2, s2 = tr.at(tt, 23), tr.at(tt, 11)
            td.line((tuple(h2 * SS), tuple(s2 * SS)), fill=(235, 40, 45, int(150 * (1 - k / 15))), width=8 * SS)
        im = Image.alpha_composite(im, tl.filter(ImageFilter.GaussianBlur(2 * SS))); d = ImageDraw.Draw(im)
    # leg: hip -> ankle
    ov.line(d, [hip, ank], col, w=9); ov.dot(d, ank, col, 11)
    # torso: hip -> shoulder
    ov.line(d, [hip, sh], col, w=10); ov.dot(d, hip, col, 12); ov.dot(d, sh, col, 12)
    # arm: shoulder -> elbow -> wrist
    ov.line(d, [sh, el, wr], col, w=8); ov.dot(d, el, col, 10); ov.dot(d, wr, col, 10)
    if mode == "good":
        v = tr.at(t + 2 / 30, 13) - tr.at(t - 2 / 30, 13)
        if v[1] < -4:  # elbow rising = pulling: show direction elbow -> hip
            u = (hip - el) / (np.linalg.norm(hip - el) + 1e-6); a = min(1, (-v[1] - 4) / 10)
            arrow(d, el + u * 30, el + u * (30 + 120 * a), GREEN, w=8, head=22)
    return im.resize((W, H), Image.LANCZOS)
