# Subtitle replica renderer (calibrated on the original video's captions)
from PIL import Image, ImageDraw, ImageFont
import os
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts", "pop700.woff")
SIZE, STROKE, GAP, CX, SX = 71, 3, 34, 540, 0.93   # SX: horizontal squeeze
YEL = (252, 254, 0); WHITE = (255, 255, 255)
_f = ImageFont.truetype(FONT, SIZE)
def line_width(words):
    return (sum(_f.getlength(w) for w in words) + GAP * (len(words) - 1)) * SX
def layout(lines):
    """lines: [(words, y) or (words, y, cx)] ; returns [(word, x_unscaled, y, w_unscaled)]"""
    out = []
    n = len(lines)
    for li, L in enumerate(lines):
        words, y = L[0], L[1]
        cx = L[2] if len(L) > 2 and L[2] is not None else (CX - (GAP * SX / 2 if li < n - 1 else 0))
        ws = [_f.getlength(w) for w in words]
        tot = sum(ws) + GAP * (len(words) - 1)
        x = cx / SX - tot / 2
        for w, wl in zip(words, ws):
            out.append((w, x, y, wl)); x += wl + GAP
    return out
def word_boxes(lines):
    return [(w, x * SX, (x + wl) * SX, y) for (w, x, y, wl) in layout(lines)]
def render(lines, yel_idx=None, W=1080, H=1920):
    Wb = int(W / SX) + 2
    im = Image.new("RGBA", (Wb, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, (w, x, y, wl) in enumerate(layout(lines)):
        if i == yel_idx and w.endswith("'") and len(w) > 1:
            # original keeps the trailing apostrophe white on the highlighted word
            d.text((x, y), w, font=_f, anchor="lm", fill=WHITE, stroke_width=STROKE, stroke_fill=(0, 0, 0))
            d.text((x, y), w[:-1], font=_f, anchor="lm", fill=YEL, stroke_width=STROKE, stroke_fill=(0, 0, 0))
        else:
            d.text((x, y), w, font=_f, anchor="lm", fill=YEL if i == yel_idx else WHITE, stroke_width=STROKE, stroke_fill=(0, 0, 0))
    ys = [L[1] for L in lines]; y0 = max(0, int(min(ys)) - 70); y1 = min(H, int(max(ys)) + 70)
    band = im.crop((0, y0, Wb, y1)).resize((W, y1 - y0), Image.LANCZOS)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); out.paste(band, (0, y0)); return out
