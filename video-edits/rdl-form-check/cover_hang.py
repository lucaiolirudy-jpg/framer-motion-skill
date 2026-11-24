import sys, os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); import ov_hang as R; ov = R.ov
W, H = 1080, 1920
def frame(p, t):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', p, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return Image.frombytes("RGB", (W, H), b).convert("RGBA")
TJ, TI = R.Track("j"), R.Track("i")
fj = frame(D + "/j_n.mp4", 1.6); fj.alpha_composite(R.overlay(TJ, 1.6, "bad"))
fi = frame(D + "/i_n.mp4", 1.07); fi.alpha_composite(R.overlay(TI, 1.07, "good"))
def half(fr, cx, scale=0.72, yoff=770, w=540):
    fr = fr.convert("RGB"); sw, sh = int(W * scale), int(H * scale); s = fr.resize((sw, sh), Image.LANCZOS)
    x0 = max(0, min(sw - w, int(cx * scale - w / 2)))
    bg = fr.resize((int(W * 1.9), int(H * 1.9))).crop((0, 0, w, H)).filter(ImageFilter.GaussianBlur(30))
    out = Image.blend(bg, Image.new("RGB", (w, H), (15, 15, 18)), 0.4); out.paste(s.crop((x0, 0, x0 + w, sh)), (0, yoff)); return out
img = Image.new("RGB", (W, H)); img.paste(half(fj, 440), (0, 0)); img.paste(half(fi, 400), (540, 0))
o = img.convert("RGBA")
g = Image.new("L", (1, H)); [g.putpixel((0, y), int(235 * max(0, min(1, (800 - y) / 520)))) for y in range(H)]
o.alpha_composite(Image.merge("RGBA", [Image.new("L", (W, H), 0)] * 3 + [g.resize((W, H))]))
d = ImageDraw.Draw(o); d.rectangle((538, 640, 541, H), fill=(255, 255, 255))
F = lambda s: ImageFont.truetype(D + "/mont900.woff", s)
def ctext(y, txt, size, fill, stroke):
    f = F(size)
    while f.getlength(txt) > 1000: size -= 4; f = F(size)
    d.text((W / 2, y), txt, font=f, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))
ctext(370, sys.argv[2], 190, (255, 222, 0), 8); ctext(510, sys.argv[3], 104, (255, 255, 255), 6)
px = ov.pill("ERRORE", "x", h=86); pv = ov.pill("CORRETTO", "v", h=86)
o.alpha_composite(px, (270 - px.width // 2, 640)); o.alpha_composite(pv, (810 - pv.width // 2, 640))
d.text((540, 683), "VS", font=F(60), fill=(255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
o.convert("RGB").save(sys.argv[1], quality=95)
