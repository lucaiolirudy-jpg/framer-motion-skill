import json, sys, subprocess, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ov
D = os.path.dirname(os.path.abspath(__file__)); R3D = sys.argv[1]; OUT = sys.argv[2]
W, H, FPS = 1080, 1920, 30
TA, TB = ov.Track("a"), ov.Track("b")
def knee_flex(tr, i):
    j = tr.joints(i); u = j["hip"] - j["knee"]; v = j["ank"] - j["knee"]
    c = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-6); return 180 - np.degrees(np.arccos(np.clip(c, -1, 1)))
def top_before(tr, i): t = [k for k in tr.tops if k <= i]; return t[-1] if t else max(0, i - 90)

# ---------------- timeline ----------------
A_top0, A_top2 = 23.97, 31.53
A_bots = [26.5, 30.13]; A_tops = [23.97, 27.9, 31.53]
B_tops = [27.2, 32.17, 36.93]; B_bots = [30.53, 35.27]
def mapB(ta):  # piecewise-linear phase mapping A -> B
    ka = [A_tops[0], A_bots[0], A_tops[1], A_bots[1], A_tops[2]]; kb = [B_tops[0], B_bots[0], B_tops[1], B_bots[1], B_tops[2]]
    return float(np.interp(ta, ka, kb))
segs = []
nsplit = int(round((A_top2 - A_top0) * FPS))
for k in range(nsplit): ta = A_top0 + k / FPS; segs.append(("split", int(round(ta * FPS)), int(round(mapB(ta) * FPS)), k))
SA0, SA1 = 28.0, 32.0; SB0, SB1 = 32.6, 36.6
for k in range(int((SA1 - SA0) * FPS)): segs.append(("A", int(round((SA0 + k / FPS) * FPS)), None, k))
for k in range(int((SB1 - SB0) * FPS)): segs.append(("B", None, int(round((SB0 + k / FPS) * FPS)), k))

# ---------------- mannequin frames (correct form) ----------------
mjobs = []
for kind, fa, fb, k in segs:
    if kind == "A": th = float(np.clip(TA.ang[fa], -5, 72)); mjobs.append([th, 16 + 4 * th / 72, 0.55])
    if kind == "B": mjobs.append([float(np.clip(TB.ang[fb], -5, 78)), float(np.clip(knee_flex(TB, fb), 8, 30)), 0.55])
MDIR = D + "/mframes"
json.dump(mjobs, open(D + "/mjobs.json", "w"))
if False:
    subprocess.run(["rm", "-rf", MDIR]); subprocess.run(["node", R3D + "/mannequin_render.js", D + "/mjobs.json", MDIR], check=True)

# ---------------- source frame access ----------------
def load(path, idxs):
    need = set(idxs); out = {}; i = 0
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    mx = max(need)
    while i <= mx:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        if i in need: out[i] = Image.frombytes("RGB", (W, H), b)
        i += 1
    p.kill(); return out
FA = load(D + "/a_n.mp4", [s[1] for s in segs if s[1] is not None])
FB = load(D + "/b_n.mp4", [s[2] for s in segs if s[2] is not None])

def blur_bg(img, size):
    w, h = size; s = max(w / img.width, h / img.height) * 1.15
    b = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)
    x0 = (b.width - w) // 2; y0 = (b.height - h) // 2
    b = b.crop((x0, y0, x0 + w, y0 + h)).filter(ImageFilter.GaussianBlur(28))
    return Image.blend(b, Image.new("RGB", (w, h), (20, 20, 24)), 0.18)

def half(src, ovl, cx, scale=0.74, yoff=280, w=540):
    fr = src.convert("RGBA"); fr.alpha_composite(ovl); fr = fr.convert("RGB")
    sw, sh = int(W * scale), int(H * scale); s = fr.resize((sw, sh), Image.LANCZOS)
    x0 = int(cx * scale - w / 2); x0 = max(0, min(sw - w, x0))
    out = blur_bg(fr, (w, H)); out.paste(s.crop((x0, 0, x0 + w, sh)), (0, yoff)); return out

BX, BV = ov.badge("x", 112), ov.badge("v", 112)
def ease(u): u = min(max(u, 0), 1); return 1 - (1 - u) ** 3
def pop(img, u):
    if u <= 0: return None
    s = 0.6 + 0.4 * ease(u) + 0.08 * np.sin(min(u, 1) * np.pi) ; s = max(0.05, s)
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)

PILLS = {k: ov.pill(*k) for k in [("SCHIENA CURVA", "x"), ("SCENDE TROPPO", "x"), ("SCHIENA PIATTA", "v"), ("SCENDI A METÀ", "v")]}
fcard = ImageFont.truetype(D + "/mont900.woff", 30)
def card(mimg):
    cw, ch = 380, 500; c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=36, fill=(18, 22, 30, 170), outline=(255, 255, 255, 90), width=2)
    m = mimg.resize((375, 500), Image.LANCZOS); c.alpha_composite(m, (2, 18))
    tag = ov.pill("FORMA CORRETTA", "v", h=52); c.alpha_composite(tag, ((cw - tag.width) // 2, 16))
    return c

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', D + '/video_only.mp4'], stdin=subprocess.PIPE)
mi = 0
for kind, fa, fb, k in segs:
    if kind == "split":
        la = half(FA[fa], ov.overlay(TA, fa, "bad", show=("shin", "back", "depth")), cx=600)
        lb = half(FB[fb], ov.overlay(TB, fb, "good", show=("shin", "back", "depth")), cx=640)
        out = Image.new("RGB", (W, H)); out.paste(la, (0, 0)); out.paste(lb, (540, 0))
        d = ImageDraw.Draw(out); d.rectangle((538, 0, 541, H), fill=(255, 255, 255))
        o = out.convert("RGBA")
        for img, x in ((BX, 270), (BV, 810)):
            p = pop(img, k / 8)
            if p: o.alpha_composite(p, (x - p.width // 2, 350 - p.height // 2))
        out = o.convert("RGB")
    else:
        tr, fi, mode, cx, yo = (TA, fa, "bad", 600, 60) if kind == "A" else (TB, fb, "good", 640, 91)
        fr = (FA[fa] if kind == "A" else FB[fb]).convert("RGBA")
        fr.alpha_composite(ov.overlay(tr, fi, mode, show=("shin", "back", "depth")))
        out = Image.new("RGB", (W, H)); out.paste(blur_bg(fr.convert("RGB"), (W, H)))
        SC = 0.9; feet = 1576 if kind == "A" else 1509
        fs = fr.convert("RGB").resize((int(W * SC), int(H * SC)), Image.LANCZOS)
        out.paste(fs, (int(540 - cx * SC), int(1490 - feet * SC)))
        o = out.convert("RGBA")
        j = tr.joints(fi); ang = tr.ang[fi]
        if kind == "A":
            t1 = next((q for q in range(int(SA0 * 30), int(SA1 * 30)) if TA.ang[q] > 50), 0)
            t2 = next((q for q in range(int(SA0 * 30), int(SA1 * 30)) if TA.joints(q)["wr"][1] > TA.joints(q)["knee"][1] + 25), 0)
            items = [(("SCHIENA CURVA", "x"), fi - t1), (("SCENDE TROPPO", "x"), fi - t2)]
        else:
            t1 = next((q for q in range(int(SB0 * 30), int(SB1 * 30)) if TB.ang[q] > 40), 0)
            t2 = next((q for q in range(int(SB0 * 30), int(SB1 * 30)) if TB.ang[q] > 65), 0)
            items = [(("SCHIENA PIATTA", "v"), fi - t1), (("SCENDI A METÀ", "v"), fi - t2)]
        y = 300
        for key, age in items:
            p = pop(PILLS[key], age / 8)
            if p: o.alpha_composite(p, (70 + (PILLS[key].width - p.width) // 2, y + (PILLS[key].height - p.height) // 2))
            y += 96
        out = o.convert("RGB")
    enc.stdin.write(out.tobytes())
enc.stdin.close(); enc.wait()
# audio: A ambience for split + single A, B ambience for single B
dur_split = nsplit / FPS
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', D + '/video_only.mp4', '-i', D + '/a.mp4', '-i', D + '/b.mp4', '-filter_complex',
    f"[1:a]atrim={A_top0}:{A_top2},asetpts=PTS-STARTPTS[a1];[1:a]atrim={SA0}:{SA1},asetpts=PTS-STARTPTS[a2];[2:a]atrim={SB0}:{SB1},asetpts=PTS-STARTPTS[a3];[a1][a2][a3]concat=n=3:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11,aformat=sample_rates=44100:channel_layouts=stereo[a]",
    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], check=True)
print("done", OUT, len(segs) / FPS, "s")
