# Composite: original video + full-screen cutaways (3D clips / photo Ken Burns) + replicated subtitles on cutaways.
# usage: python3 compose.py SCRATCH plan.json out.mp4 [t0 t1]
import json, sys, subprocess, bisect, os
import numpy as np
from PIL import Image
S = sys.argv[1]; sys.path.insert(0, S + "/work"); import subs
plan = json.load(open(sys.argv[2])); OUT = sys.argv[3]
T0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
T1 = float(sys.argv[5]) if len(sys.argv) > 5 else 336.33
W, H, FPS = 1080, 1920, 30
V = S + "/src/video.mp4"
tl = json.load(open(S + "/work/subtimeline.json"))
starts = [c["f0"] for c in tl]

def sub_state(f):
    i = bisect.bisect_right(starts, f) - 1
    if i < 0: return None
    c = tl[i]
    if f >= c["f1"]: return None
    k = f - c["f0"]; acc = 0
    for idx, n in c["hl"]:
        if k < acc + n: return (i, idx)
        acc += n
    return (i, -1)

_ov = {}
def overlay(state):
    if state not in _ov:
        i, idx = state; c = tl[i]
        im = subs.render([(ws, y) for ws, y in c["lines"]], idx if idx >= 0 else None)
        a = np.asarray(im)
        ys = np.nonzero(a[..., 3].any(1))[0]
        y0, y1 = (ys.min(), ys.max() + 1) if len(ys) else (0, 1)
        band = a[y0:y1].astype(np.float32)
        _ov[state] = (y0, y1, band[..., :3], band[..., 3:4] / 255.0)
    return _ov[state]

# --- cutaway sources
class Clip:
    def __init__(self, path, nframes):
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
        self.last = None
    def frame(self, k):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3: self.last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        return self.last
    def close(self): self.p.kill()

class Photo:
    def __init__(self, path, n, cfg):
        im = Image.open(path).convert("RGB")
        z1 = cfg.get("zoom", [1.0, 1.10])
        self.n = max(1, n); self.z = z1; self.pan = cfg.get("pan", [0, 0, 0, 0]); self.focus = cfg.get("focus", [0.5, 0.5])
        # base canvas covering 1080x1920 at max zoom
        zmax = max(z1)
        sc = max(W / im.width, H / im.height) * zmax
        self.base = np.asarray(im.resize((int(im.width * sc + 0.5), int(im.height * sc + 0.5)), Image.LANCZOS))
        self.sc = sc / zmax
        self.pil = Image.fromarray(self.base)
    def frame(self, k):
        u = k / max(1, self.n - 1); u = u * u * (3 - 2 * u) * 0.6 + u * 0.4
        z = self.z[0] + (self.z[1] - self.z[0]) * u
        bh, bw = self.base.shape[:2]
        cw, ch = W * max(self.z) / z, H * max(self.z) / z  # crop size in base pixels
        fx = self.focus[0] + (self.pan[2] - self.pan[0]) * u + self.pan[0]
        fy = self.focus[1] + (self.pan[3] - self.pan[1]) * u + self.pan[1]
        cw = min(cw, bw); ch = min(ch, bh)
        x0 = max(0, min(max(0, fx * bw - cw / 2), bw - cw)); y0 = max(0, min(max(0, fy * bh - ch / 2), bh - ch))
        crop = self.pil.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
        return np.asarray(crop)
    def close(self): pass

cuts = []
for c in plan:
    f0, f1 = round(c["s"] * FPS), round(c["e"] * FPS)
    cuts.append((f0, f1, c))
cuts.sort(key=lambda x: x[0])

F0, F1 = round(T0 * FPS), round(T1 * FPS)
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{T0:.3f}', '-i', V, '-t', f'{T1 - T0:.3f}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-ss', f'{T0:.3f}', '-t', f'{T1 - T0:.3f}', '-i', V, '-ss', f'{T0:.3f}', '-t', f'{T1 - T0:.3f}', '-i', S + '/work/sfx.wav',
                        '-filter_complex', '[1:a]aformat=sample_rates=44100:channel_layouts=stereo[v];[2:a]aformat=sample_rates=44100:channel_layouts=stereo[s];[v][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.97:level=false[a]',
                        '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', OUT], stdin=subprocess.PIPE)
active = None; ci = 0
for f in range(F0, F1):
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    fr = np.frombuffer(b, np.uint8).reshape(H, W, 3)
    # find cutaway
    cut = next((x for x in cuts if x[0] <= f < x[1]), None)
    if cut is None:
        if active: active[1].close(); active = None
        enc.stdin.write(fr.tobytes()); continue
    if active is None or active[0] is not cut:
        if active: active[1].close()
        f0, f1, c = cut
        if c["kind"] == "photo": src = Photo(S + "/broll/" + c["src"], f1 - f0, c)
        else: src = Clip(S + "/out3d/" + c["src"], f1 - f0)
        # skip ahead if preview starts in middle of cut
        for k in range(0, f - f0):
            if c["kind"] != "photo": src.frame(k)
        active = (cut, src)
    k = f - cut[0]
    img = active[1].frame(k).astype(np.float32)
    st = sub_state(f)
    if st is not None:
        y0, y1, rgb, a = overlay(st)
        img[y0:y1] = img[y0:y1] * (1 - a) + rgb * a
    enc.stdin.write(img.clip(0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()
print("done", OUT)
