# Incline dumbbell curl: synced split (wrong slowed via 60 fps interpolation) -> 4 s wrong -> 4 s correct
import sys, subprocess, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); import ov_bbcurl as R; ov = R.ov
OUT = sys.argv[1]; W, H, FPS = 1080, 1920, 30
TH, TG = R.Track("l"), R.Track("k")      # L = wrong, K = correct
G_k = [5.7, 6.93, 8.37, 9.5, 10.8]
H_k = [3.73, 4.47, 5.37, 6.27, 7.0]
segs = [("split", float(np.interp(G_k[0] + k / FPS, G_k, H_k)), G_k[0] + k / FPS, k) for k in range(int(round((G_k[-1] - G_k[0]) * FPS)))]
SH0, SH1 = 3.0, 7.0; SG0, SG1 = 5.7, 9.7
segs += [("H", SH0 + k / FPS, None, k) for k in range(int((SH1 - SH0) * FPS))]
segs += [("G", None, SG0 + k / FPS, k) for k in range(int((SG1 - SG0) * FPS))]
def load(path, fps, times):
    need = sorted(set(int(round(t * fps)) for t in times)); ns = set(need); out = {}; i = 0
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    while i <= need[-1]:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        if i in ns: out[i] = Image.frombytes("RGB", (W, H), b)
        i += 1
    p.kill(); return out
FH60 = load(D + "/l_n60.mp4", 60, [s[1] for s in segs if s[0] == "split"])
FH = load(D + "/l_n.mp4", 30, [s[1] for s in segs if s[0] == "H"])
FG = load(D + "/k_n.mp4", 30, [s[2] for s in segs if s[2] is not None])
def getH60(t):
    i = int(round(t * 60)); return FH60.get(i) or FH60[min(FH60, key=lambda k: abs(k - i))]
def blur_bg(img, size):
    w, h = size; s = max(w / img.width, h / img.height) * 1.15
    b = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR); x0 = (b.width - w) // 2; y0 = (b.height - h) // 2
    return Image.blend(b.crop((x0, y0, x0 + w, y0 + h)).filter(ImageFilter.GaussianBlur(28)), Image.new("RGB", (w, h), (20, 20, 24)), 0.18)
def half(fr, cx, yoff=269, scale=0.68, w=540):
    sw, sh = int(W * scale), int(H * scale); s = fr.resize((sw, sh), Image.LANCZOS)
    x0 = max(0, min(sw - w, int(cx * scale - w / 2)))
    out = blur_bg(fr, (w, H)); out.paste(s.crop((x0, 0, x0 + w, sh)), (0, yoff)); return out
def ease(u): u = min(max(u, 0), 1); return 1 - (1 - u) ** 3
def pop(img, u):
    if u <= 0: return None
    s = max(0.05, 0.6 + 0.4 * ease(u) + 0.08 * np.sin(min(u, 1) * np.pi))
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
BX, BV = ov.badge("x", 112), ov.badge("v", 112)
LAB_H = ["BUSTO CHE DONDOLA", "USA LO SLANCIO", "GOMITO CHE AVANZA"]
LAB_G = ["BUSTO FERMO", "MOVIMENTO CONTROLLATO", "GOMITO FERMO"]
PILLS = {t: ov.pill(t, "x", h=62) for t in LAB_H}; PILLS.update({t: ov.pill(t, "v", h=62) for t in LAB_G})
first = lambda c, a, b: next((t for t in np.arange(a, b, 1 / 30) if c(t)), a) - a
t1 = max(0.15, first(lambda t: TH.torso(t) < -9, SH0, SH1))
t3 = first(lambda t: TH.upper(t) > 35, SH0 + t1, SH1) + t1
tH = [t1, t1 + 0.4, max(t3, t1 + 0.8)]
tG = [0.15, 0.8, 6.93 - SG0 - 0.2]
print("labels", tH, tG)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', D + '/video_only.mp4'], stdin=subprocess.PIPE)
for kind, th, tg, k in segs:
    if kind == "split":
        fh = getH60(th).convert("RGBA"); fh.alpha_composite(R.overlay(TH, th, "bad"))
        fg = FG[int(round(tg * 30))].convert("RGBA"); fg.alpha_composite(R.overlay(TG, tg, "good"))
        out = Image.new("RGB", (W, H)); out.paste(half(fh.convert("RGB"), 480), (0, 0)); out.paste(half(fg.convert("RGB"), 460), (540, 0))
        ImageDraw.Draw(out).rectangle((538, 0, 541, H), fill=(255, 255, 255)); o = out.convert("RGBA")
        for img, x in ((BX, 270), (BV, 810)):
            p = pop(img, k / 8)
            if p: o.alpha_composite(p, (x - p.width // 2, 345 - p.height // 2))
    else:
        if kind == "H": fr = FH[int(round(th * 30))].convert("RGBA"); fr.alpha_composite(R.overlay(TH, th, "bad")); labs, times = LAB_H, tH
        else: fr = FG[int(round(tg * 30))].convert("RGBA"); fr.alpha_composite(R.overlay(TG, tg, "good")); labs, times = LAB_G, tG
        sc = fr.convert("RGB").resize((int(W * 0.85), int(H * 0.85)), Image.LANCZOS)
        o = blur_bg(fr.convert("RGB"), (W, H)); o.paste(sc, ((W - sc.width) // 2, int(1480 - 1737 * 0.85))); o = o.convert("RGBA"); y = 300
        for lab, tt in zip(labs, times):
            P = PILLS[lab]; p = pop(P, (k / 30 - tt) * 30 / 8)
            if p: o.alpha_composite(p, (1050 - P.width + (P.width - p.width) // 2, y + (P.height - p.height) // 2))
            y += 74
    enc.stdin.write(o.convert("RGB").tobytes())
enc.stdin.close(); enc.wait()
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', D + '/video_only.mp4', '-i', D + '/k.mp4', '-i', D + '/l.mp4', '-filter_complex',
    f"[1:a]atrim={G_k[0]}:{G_k[-1]},asetpts=PTS-STARTPTS[a1];[2:a]atrim={SH0}:{SH1},asetpts=PTS-STARTPTS[a2];[1:a]atrim={SG0}:{SG1},asetpts=PTS-STARTPTS[a3];[a1][a2][a3]concat=n=3:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11,aformat=sample_rates=44100:channel_layouts=stereo[a]",
    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', OUT, '-vf', 'crop=1080:1350:0:285', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                '-c:a', 'copy', '-movflags', '+faststart', OUT.replace('9x16', '4x5')], check=True)
print("done", len(segs) / FPS, "s")
