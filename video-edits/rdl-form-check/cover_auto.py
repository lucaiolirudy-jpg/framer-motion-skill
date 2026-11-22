# Cover from a split-screen screenshot: removes old badges, crops to 9:16 around the divider, adds title + ERRORE vs CORRETTO
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
V2 = sys.argv[1]; sys.path.insert(0, V2); import ov
src, out, l1, l2 = sys.argv[2:6]
im = Image.open(src).convert("RGB"); a = np.array(im).astype(float); H0, W0, _ = a.shape
ai = a.astype(int)
colmean = ai.mean((0, 2)); right = W0
while right > 0 and colmean[right - 1] < 6: right -= 1
div = int(np.mean([x for x in range(int(W0 * .4), int(W0 * .6)) if ai[:, x].mean() > 190]))
top = int(H0 * 0.3)
red = (ai[..., 0] > 170) & (ai[..., 1] < 90) & (ai[..., 2] < 90)
grn = (ai[..., 1] > 130) & (ai[..., 0] < 120) & (ai[..., 2] < 120) & (ai[..., 1] - ai[..., 0] > 50)
boxes = []
for m in (red, grn):
    ys, xs = np.nonzero(m[:top]); boxes.append((xs.min() - 9, xs.max() + 9, ys.min() - 9, ys.max() + 9))
rng = np.random.default_rng(0)
for x0, x1, y0, y1 in boxes:
    t, b = a[y0 - 1, x0:x1 + 1], a[y1 + 1, x0:x1 + 1]
    for y in range(y0, y1 + 1):
        u = (y - y0) / (y1 - y0); a[y, x0:x1 + 1] = t * (1 - u) + b * u + rng.normal(0, 2.5, t.shape)
img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
for x0, x1, y0, y1 in boxes:
    bx = (x0 - 10, y0 - 10, x1 + 10, y1 + 10); img.paste(img.crop(bx).filter(ImageFilter.GaussianBlur(6)), bx[:2])
# crop to 9:16
Wc, Hc = right, H0
FIT = len(sys.argv) > 7 and sys.argv[7] == 'fit'
if FIT:
    img = img.crop((0, 0, Wc, Hc)); nh = int(Wc * 16 / 9); ext = Image.new('RGB', (Wc, nh)); ext.paste(img, (0, 0))
    band = img.crop((0, Hc - 200, Wc, Hc)).resize((Wc, nh - Hc + 200)).filter(ImageFilter.GaussianBlur(20)); ext.paste(band, (0, Hc - 100)); ext.paste(img.crop((0, 0, Wc, Hc - 100)), (0, 0)); img = ext
elif Wc / Hc > 9 / 16:
    cw = int(Hc * 9 / 16); x0 = max(0, min(Wc - cw, div - cw // 2)); img = img.crop((x0, 0, x0 + cw, Hc)); div -= x0
else:
    ch = int(Wc * 16 / 9); y0 = max(0, Hc - ch) if Hc - ch < 60 else 0; img = img.crop((0, y0, Wc, y0 + ch))
s = 1080 / img.width; img = img.resize((1080, 1920), Image.LANCZOS); DIV = int(div * s)
SHIFT = int(sys.argv[6]) if len(sys.argv) > 6 else 0
if SHIFT:  # move the content down; fill the top with a blurred stretch of the top band
    band = img.crop((0, 0, 1080, 260)).resize((1080, 260 + SHIFT)).filter(ImageFilter.GaussianBlur(25))
    moved = Image.new("RGB", (1080, 1920)); moved.paste(img, (0, SHIFT)); moved.paste(band, (0, 0))
    moved.paste(img.crop((0, 260, 1080, 300)).filter(ImageFilter.GaussianBlur(8)), (0, 260 + SHIFT - 20)); img = moved
W, H = 1080, 1920; o = img.convert("RGBA")
g = Image.new("L", (1, H)); [g.putpixel((0, y), int(235 * max(0, min(1, (760 - y) / 520)))) for y in range(H)]
o.alpha_composite(Image.merge("RGBA", [Image.new("L", (W, H), 0)] * 3 + [g.resize((W, H))]))
d = ImageDraw.Draw(o); F = lambda z: ImageFont.truetype(os.path.join(V2, "mont900.woff"), z)
def ctext(y, txt, size, fill, stroke):
    f = F(size)
    while f.getlength(txt) > 1000: size -= 4; f = F(size)
    d.text((W / 2, y), txt, font=f, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))
ctext(370, l1, 190, (255, 222, 0), 8); ctext(510, l2, 104, (255, 255, 255), 6)
px = ov.pill("ERRORE", "x", h=86); pv = ov.pill("CORRETTO", "v", h=86)
o.alpha_composite(px, (max(10, DIV // 2 - px.width // 2), 640)); o.alpha_composite(pv, (min(W - 10 - pv.width, (DIV + W) // 2 - pv.width // 2), 640))
d.text((DIV, 683), "VS", font=F(60), fill=(255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
o.convert("RGB").save(out, quality=95); print(out, "div", DIV)
