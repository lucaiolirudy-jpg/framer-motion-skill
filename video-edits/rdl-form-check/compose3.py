# Seated cable row: synced split (wrong slowed from 60 fps) -> 4 s wrong -> 4 s correct
import json, sys, subprocess, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); import ov_row as R; ov = R.ov
OUT = sys.argv[1]; W, H, FPS = 1080, 1920, 30
TC, TD = R.Track("c"), R.Track("d")   # C = correct, D = wrong
# rep keyframes (extended -> contracted -> extended ...)
C_k = [5.23, 6.87, 8.5, 9.67, 11.17]
D_k = [3.17, 4.03, 5.03, 5.93, 6.9]
segs = []
n = int(round((C_k[-1] - C_k[0]) * FPS))
for k in range(n): tc = C_k[0] + k / FPS; segs.append(("split", tc, float(np.interp(tc, C_k, D_k)), k))
SD0, SD1 = 6.9, 10.9   # wrong single
SC0, SC1 = 5.0, 9.0    # correct single
for k in range(int((SD1 - SD0) * FPS)): segs.append(("D", None, SD0 + k / FPS, k))
for k in range(int((SC1 - SC0) * FPS)): segs.append(("C", SC0 + k / FPS, None, k))

def load(path, fps, times):
    need = sorted(set(int(round(t * fps)) for t in times)); ns = set(need); out = {}; i = 0
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    while i <= need[-1]:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        if i in ns: out[i] = Image.frombytes("RGB", (W, H), b)
        i += 1
    p.kill(); return out
FC = load(D + "/c_n.mp4", 30, [s[1] for s in segs if s[1] is not None])
FD60 = load(D + "/d_n60.mp4", 60, [s[2] for s in segs if s[0] == "split"])
FD30 = load(D + "/d_n.mp4", 30, [s[2] for s in segs if s[0] == "D"])
def getC(t): return FC[int(round(t * 30))]
def getD(t, split): return FD60[int(round(t * 60))] if split else FD30[int(round(t * 30))]

def blur_bg(img, size):
    w, h = size; s = max(w / img.width, h / img.height) * 1.15
    b = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)
    x0 = (b.width - w) // 2; y0 = (b.height - h) // 2
    b = b.crop((x0, y0, x0 + w, y0 + h)).filter(ImageFilter.GaussianBlur(28))
    return Image.blend(b, Image.new("RGB", (w, h), (20, 20, 24)), 0.18)
def half(fr, cx, scale=0.72, yoff=200, w=540):
    sw, sh = int(W * scale), int(H * scale); s = fr.resize((sw, sh), Image.LANCZOS)
    x0 = max(0, min(sw - w, int(cx * scale - w / 2)))
    out = blur_bg(fr, (w, H)); out.paste(s.crop((x0, 0, x0 + w, sh)), (0, yoff)); return out
def ease(u): u = min(max(u, 0), 1); return 1 - (1 - u) ** 3
def pop(img, u):
    if u <= 0: return None
    s = max(0.05, 0.6 + 0.4 * ease(u) + 0.08 * np.sin(min(u, 1) * np.pi))
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
BX, BV = ov.badge("x", 112), ov.badge("v", 112)
LAB_D = ["BUSTO CHE OSCILLA", "TROPPO INDIETRO", "USA LO SLANCIO"]
LAB_C = ["BUSTO FERMO", "BUSTO DRITTO", "TIRA CON LA SCHIENA"]
PILLS = {t: ov.pill(t, "x") for t in LAB_D}; PILLS.update({t: ov.pill(t, "v") for t in LAB_C})
# label timing (seconds from single start), tied to what happens on screen
first = lambda cond, t0, t1: next((t for t in np.arange(t0, t1, 1 / 30) if cond(t)), t0) - t0
tD = [0.15, first(lambda t: TD.angle(t) > 22, SD0, SD1), first(lambda t: TD.angle(t) < -22, SD0 + 0.5, SD1)]
tC = [0.15, first(lambda t: abs(TC.at(t, 15)[0] - TC.at(t, 11)[0]) < 230, SC0, SC1), 1.4]
tD = [max(tD[0], 0.15), max(tD[1], 0.45), max(tD[2], tD[1] + 0.35)]
print("label times", tD, tC)

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', D + '/video_only.mp4'], stdin=subprocess.PIPE)
for kind, tc, td, k in segs:
    if kind == "split":
        fd = getD(td, True).convert("RGBA"); fd.alpha_composite(R.overlay(TD, td, "bad"))
        fc = getC(tc).convert("RGBA"); fc.alpha_composite(R.overlay(TC, tc, "good"))
        out = Image.new("RGB", (W, H)); out.paste(half(fd.convert("RGB"), 690), (0, 0)); out.paste(half(fc.convert("RGB"), 720), (540, 0))
        ImageDraw.Draw(out).rectangle((538, 0, 541, H), fill=(255, 255, 255))
        o = out.convert("RGBA")
        for img, x in ((BX, 270), (BV, 810)):
            p = pop(img, k / 8)
            if p: o.alpha_composite(p, (x - p.width // 2, 350 - p.height // 2))
    else:
        t, tr, mode, labs, times, t0 = (td, TD, "bad", LAB_D, tD, SD0) if kind == "D" else (tc, TC, "good", LAB_C, tC, SC0)
        fr = (getD(t, False) if kind == "D" else getC(t)).convert("RGBA"); fr.alpha_composite(R.overlay(tr, t, mode))
        o = Image.new("RGBA", (W, H)); o.paste(fr, (0, -80))
        o.paste(blur_bg(fr.convert("RGB"), (W, 80)).convert("RGBA"), (0, H - 80))
        y = 300
        for lab, tt in zip(labs, times):
            p = pop(PILLS[lab], (k / 30 - tt) * 30 / 8)
            if p: o.alpha_composite(p, (70 + (PILLS[lab].width - p.width) // 2, y + (PILLS[lab].height - p.height) // 2))
            y += 96
    enc.stdin.write(o.convert("RGB").tobytes())
enc.stdin.close(); enc.wait()
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', D + '/video_only.mp4', '-i', D + '/c.mp4', '-i', D + '/d.mp4', '-filter_complex',
    f"[1:a:1]atrim={C_k[0]}:{C_k[-1]},asetpts=PTS-STARTPTS[a1];[2:a:1]atrim={SD0}:{SD1},asetpts=PTS-STARTPTS[a2];[1:a:1]atrim={SC0}:{SC1},asetpts=PTS-STARTPTS[a3];[a1][a2][a3]concat=n=3:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11,aformat=sample_rates=44100:channel_layouts=stereo[a]",
    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', OUT, '-vf', 'crop=1080:1350:0:285', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                '-c:a', 'copy', '-movflags', '+faststart', OUT.replace('9x16', '4x5')], check=True)
print("done", len(segs) / FPS, "s")
