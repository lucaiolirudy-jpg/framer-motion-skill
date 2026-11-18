# One-arm dumbbell row: synced split -> 4 s wrong -> ~4 s correct (foot placement sped up 2x, then real time)
import sys, subprocess, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); import ov_dbrow as R; ov = R.ov
OUT = sys.argv[1]; W, H, FPS = 1080, 1920, 30
TE, TF = R.Track("e"), R.Track("f")   # E = wrong, F = correct
F_k = [5.9, 6.9, 8.0, 9.1, 10.1, 11.2, 12.3]     # bottom/top/bottom... (correct, master, real time)
E_k = [1.9, 2.7, 3.5, 4.3, 5.1, 5.9, 6.7]        # wrong, warped onto F phases (from 60 fps source)
FOOT0 = 0.3                                       # correct: foot starts moving
segs = []
for k in range(int(round((F_k[-1] - F_k[0]) * FPS))):
    tf = F_k[0] + k / FPS; segs.append(("split", float(np.interp(tf, F_k, E_k)), tf, k))
SE0, SE1 = 3.5, 7.5
for k in range(int((SE1 - SE0) * FPS)): segs.append(("E", SE0 + k / FPS, None, k))
# correct single: src 0.3->3.2 at 2x, then 3.2->5.9 real time
RAMP = [(0.3, 3.2, 2.0), (3.2, 5.9, 1.0)]
tf = RAMP[0][0]; k = 0; ramp_out = []
for a, b, sp in RAMP:
    tf = a
    while tf < b - 1e-6: segs.append(("F", None, tf, k)); ramp_out.append(tf); tf += sp / FPS; k += 1
def load(path, fps, times):
    need = sorted(set(int(round(t * fps)) for t in times)); ns = set(need); out = {}; i = 0
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    while i <= need[-1]:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        if i in ns: out[i] = Image.frombytes("RGB", (W, H), b)
        i += 1
    p.kill(); return out
FE60 = load(D + "/e_n60.mp4", 60, [s[1] for s in segs if s[0] == "split"])
FE = load(D + "/e_n.mp4", 30, [s[1] for s in segs if s[0] == "E"])
FF = load(D + "/f_n.mp4", 30, [s[2] for s in segs if s[2] is not None])
def blur_bg(img, size):
    w, h = size; s = max(w / img.width, h / img.height) * 1.15
    b = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)
    x0 = (b.width - w) // 2; y0 = (b.height - h) // 2
    return Image.blend(b.crop((x0, y0, x0 + w, y0 + h)).filter(ImageFilter.GaussianBlur(28)), Image.new("RGB", (w, h), (20, 20, 24)), 0.18)
def half(fr, cx, yoff, scale=0.66, w=540):
    sw, sh = int(W * scale), int(H * scale); s = fr.resize((sw, sh), Image.LANCZOS)
    x0 = max(0, min(sw - w, int(cx * scale - w / 2)))
    out = blur_bg(fr, (w, H)); out.paste(s.crop((x0, 0, x0 + w, sh)), (0, yoff)); return out
def single(fr, toe_y, scale=0.92):
    s = fr.resize((int(W * scale), int(H * scale)), Image.LANCZOS)
    out = blur_bg(fr, (W, H)); out.paste(s, ((W - s.width) // 2, int(1425 - toe_y * scale))); return out
def ease(u): u = min(max(u, 0), 1); return 1 - (1 - u) ** 3
def pop(img, u):
    if u <= 0: return None
    s = max(0.05, 0.6 + 0.4 * ease(u) + 0.08 * np.sin(min(u, 1) * np.pi))
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
BX, BV = ov.badge("x", 112), ov.badge("v", 112)
LAB_E = ["PIEDE TROPPO INDIETRO", "TIRA COL BRACCIO", "BUSTO CHE RUOTA"]
LAB_F = ["PIEDE SOTTO L'ANCA", "GOMITO VERSO L'ANCA", "BUSTO STABILE"]
PILLS = {t: ov.pill(t, "x") for t in LAB_E}; PILLS.update({t: ov.pill(t, "v") for t in LAB_F})
tE = [0.15, 4.3 - SE0 - 0.15, 5.1 - SE0]            # seconds into the wrong single
f_idx = lambda src: next(i for i, t in enumerate(ramp_out) if t >= src) / FPS
tF = [f_idx(2.9), f_idx(3.7), f_idx(4.5)]          # foot settled, first pull, stable torso
print("labels", tE, tF, "correct single", len(ramp_out) / FPS, "s")
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', D + '/video_only.mp4'], stdin=subprocess.PIPE)
for kind, te, tf, k in segs:
    if kind == "split":
        fe = FE60[int(round(te * 60))].convert("RGBA"); fe.alpha_composite(R.overlay(TE, te, "bad"))
        ff = FF[int(round(tf * 30))].convert("RGBA"); ff.alpha_composite(R.overlay(TF, tf, "good", foot_from=None))
        out = Image.new("RGB", (W, H)); out.paste(half(fe.convert("RGB"), 430, 336), (0, 0)); out.paste(half(ff.convert("RGB"), 480, 216), (540, 0))
        ImageDraw.Draw(out).rectangle((538, 0, 541, H), fill=(255, 255, 255)); o = out.convert("RGBA")
        for img, x in ((BX, 270), (BV, 810)):
            p = pop(img, k / 8)
            if p: o.alpha_composite(p, (x - p.width // 2, 350 - p.height // 2))
    else:
        if kind == "E": fr = FE[int(round(te * 30))].convert("RGBA"); fr.alpha_composite(R.overlay(TE, te, "bad")); toe = 1673; labs, times = LAB_E, tE
        else: fr = FF[int(round(tf * 30))].convert("RGBA"); fr.alpha_composite(R.overlay(TF, tf, "good", foot_from=FOOT0)); toe = 1854; labs, times = LAB_F, tF
        o = single(fr.convert("RGB"), toe).convert("RGBA"); y = 300
        for lab, tt in zip(labs, times):
            p = pop(PILLS[lab], (k / 30 - tt) * 30 / 8)
            if p: o.alpha_composite(p, (70 + (PILLS[lab].width - p.width) // 2, y + (PILLS[lab].height - p.height) // 2))
            y += 96
    enc.stdin.write(o.convert("RGB").tobytes())
enc.stdin.close(); enc.wait()
dF = len(ramp_out) / FPS
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', D + '/video_only.mp4', '-i', D + '/e.mp4', '-i', D + '/f.mp4', '-filter_complex',
    f"[2:a:1]atrim={F_k[0]}:{F_k[-1]},asetpts=PTS-STARTPTS[a1];[1:a:1]atrim={SE0}:{SE1},asetpts=PTS-STARTPTS[a2];[2:a:1]atrim=0.3:{0.3 + dF},asetpts=PTS-STARTPTS[a3];[a1][a2][a3]concat=n=3:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11,aformat=sample_rates=44100:channel_layouts=stereo[a]",
    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', OUT, '-vf', 'crop=1080:1350:0:285', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                '-c:a', 'copy', '-movflags', '+faststart', OUT.replace('9x16', '4x5')], check=True)
print("done", len(segs) / FPS, "s")
