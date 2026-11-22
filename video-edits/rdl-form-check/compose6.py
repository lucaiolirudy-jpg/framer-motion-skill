# Hanging knee raise: synced split -> 4 s wrong -> 4 s correct (scaled down so bar/hands/feet stay in the safe area)
import sys, subprocess, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); import ov_hang as R; ov = R.ov
OUT = sys.argv[1]; W, H, FPS = 1080, 1920, 30
TJ, TI = R.Track("j"), R.Track("i")       # J = wrong, I = correct
I_k = [3.1, 4.13, 5.9, 7.07, 8.6]; J_k = [3.0, 4.03, 5.6, 6.73, 8.0]
segs = [("split", float(np.interp(I_k[0] + k / FPS, I_k, J_k)), I_k[0] + k / FPS, k) for k in range(int(round((I_k[-1] - I_k[0]) * FPS)))]
SJ0, SJ1 = 5.6, 9.6; SI0, SI1 = 5.9, 9.9
segs += [("J", SJ0 + k / FPS, None, k) for k in range(int((SJ1 - SJ0) * FPS))]
segs += [("I", None, SI0 + k / FPS, k) for k in range(int((SI1 - SI0) * FPS))]
def load(path, times):
    need = sorted(set(int(round(t * 30)) for t in times)); ns = set(need); out = {}; i = 0
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    while i <= need[-1]:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        if i in ns: out[i] = Image.frombytes("RGB", (W, H), b)
        i += 1
    p.kill(); return out
FJ = load(D + "/j_n.mp4", [s[1] for s in segs if s[1] is not None]); FI = load(D + "/i_n.mp4", [s[2] for s in segs if s[2] is not None])
get = lambda F, t: F[min(F, key=lambda k: abs(k - t * 30))]
def blur_bg(img, size):
    w, h = size; s = max(w / img.width, h / img.height) * 1.15
    b = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR); x0 = (b.width - w) // 2; y0 = (b.height - h) // 2
    return Image.blend(b.crop((x0, y0, x0 + w, y0 + h)).filter(ImageFilter.GaussianBlur(28)), Image.new("RGB", (w, h), (20, 20, 24)), 0.18)
def half(fr, cx, scale=0.62, yoff=400, w=540):
    sw, sh = int(W * scale), int(H * scale); s = fr.resize((sw, sh), Image.LANCZOS)
    x0 = max(0, min(sw - w, int(cx * scale - w / 2))); out = blur_bg(fr, (w, H)); out.paste(s.crop((x0, 0, x0 + w, sh)), (0, yoff)); return out
def single(fr, scale=0.8, yoff=300):
    s = fr.resize((int(W * scale), int(H * scale)), Image.LANCZOS); out = blur_bg(fr, (W, H)); out.paste(s, ((W - s.width) // 2, yoff)); return out
def ease(u): u = min(max(u, 0), 1); return 1 - (1 - u) ** 3
def pop(img, u):
    if u <= 0: return None
    s = max(0.05, 0.6 + 0.4 * ease(u) + 0.08 * np.sin(min(u, 1) * np.pi))
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
BX, BV = ov.badge("x", 112), ov.badge("v", 112)
LAB_J = ["CORPO CHE DONDOLA", "USA LO SLANCIO"]; LAB_I = ["CORPO FERMO", "MOVIMENTO CONTROLLATO"]
PILLS = {t: ov.pill(t, "x") for t in LAB_J}; PILLS.update({t: ov.pill(t, "v") for t in LAB_I})
first = lambda c, a, b: next((t for t in np.arange(a, b, 1 / 30) if c(t)), a) - a
tJ = [max(0.15, first(lambda t: abs(TJ.torso(t)) > 20, SJ0, SJ1)), 0]; tJ[1] = tJ[0] + 0.6
tI = [0.15, 1.0]
print("labels", tJ, tI)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', D + '/video_only.mp4'], stdin=subprocess.PIPE)
for kind, tj, ti, k in segs:
    if kind == "split":
        fj = get(FJ, tj).convert("RGBA"); fj.alpha_composite(R.overlay(TJ, tj, "bad"))
        fi = get(FI, ti).convert("RGBA"); fi.alpha_composite(R.overlay(TI, ti, "good"))
        out = Image.new("RGB", (W, H)); out.paste(half(fj.convert("RGB"), 410), (0, 0)); out.paste(half(fi.convert("RGB"), 400), (540, 0))
        ImageDraw.Draw(out).rectangle((538, 0, 541, H), fill=(255, 255, 255)); o = out.convert("RGBA")
        for img, x in ((BX, 270), (BV, 810)):
            p = pop(img, k / 8)
            if p: o.alpha_composite(p, (x - p.width // 2, 340 - p.height // 2))
    else:
        if kind == "J": fr = get(FJ, tj).convert("RGBA"); fr.alpha_composite(R.overlay(TJ, tj, "bad")); labs, times = LAB_J, tJ
        else: fr = get(FI, ti).convert("RGBA"); fr.alpha_composite(R.overlay(TI, ti, "good")); labs, times = LAB_I, tI
        o = single(fr.convert("RGB")).convert("RGBA"); y = 1290
        for lab, tt in zip(labs, times):
            P = PILLS[lab]; p = pop(P, (k / 30 - tt) * 30 / 8)
            if p: o.alpha_composite(p, (70 + (P.width - p.width) // 2, y + (P.height - p.height) // 2))
            y += 92
    enc.stdin.write(o.convert("RGB").tobytes())
enc.stdin.close(); enc.wait()
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', D + '/video_only.mp4', '-i', D + '/i.mp4', '-i', D + '/j.mp4', '-filter_complex',
    f"[1:a]atrim={I_k[0]}:{I_k[-1]},asetpts=PTS-STARTPTS[a1];[2:a]atrim={SJ0}:{SJ1},asetpts=PTS-STARTPTS[a2];[1:a]atrim={SI0}:{SI1},asetpts=PTS-STARTPTS[a3];[a1][a2][a3]concat=n=3:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11,aformat=sample_rates=44100:channel_layouts=stereo[a]",
    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', OUT, '-vf', 'crop=1080:1350:0:285', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                '-c:a', 'copy', '-movflags', '+faststart', OUT.replace('9x16', '4x5')], check=True)
print("done", len(segs) / FPS, "s")
