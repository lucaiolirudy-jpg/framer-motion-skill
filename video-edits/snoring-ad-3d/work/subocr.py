import subprocess, numpy as np, json, sys
from rapidocr_onnxruntime import RapidOCR
V, SEGS, OUT = sys.argv[1:4]
ocr = RapidOCR()
segs = json.load(open(SEGS))["segs"]
starts = sorted(set(a for a, b in segs))
Y0, HH = 1250, 360
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', V, '-vf', f'crop=1080:{HH}:0:{Y0}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
FS = 1080 * HH * 3
res = {}
si = set(starts); i = 0
while True:
    buf = p.stdout.read(FS)
    if len(buf) < FS: break
    if i in si:
        f = np.frombuffer(buf, np.uint8).reshape(HH, 1080, 3)
        r = f[..., 0].astype(int); g = f[..., 1].astype(int); b = f[..., 2].astype(int)
        yel = (r > 190) & (g > 190) & (b < 110)
        white = (r > 235) & (g > 235) & (b > 235)
        txt = np.full((HH, 1080), 255, np.uint8); txt[yel | white] = 0
        lines = []
        out, _ = ocr(np.stack([txt]*3, -1))
        for box, t, conf in (out or []):
            ys = [pt[1] for pt in box]; xs = [pt[0] for pt in box]
            lines.append({"t": t, "y": (min(ys)+max(ys))/2 + Y0, "x0": min(xs), "x1": max(xs), "h": max(ys)-min(ys), "c": conf})
        ytxt = np.full((HH, 1080), 255, np.uint8); ytxt[yel] = 0
        yw = []
        if yel.sum() > 150:
            out2, _ = ocr(np.stack([ytxt]*3, -1))
            for box, t, conf in (out2 or []):
                xs = [pt[0] for pt in box]; ys = [pt[1] for pt in box]
                yw.append({"t": t, "y": (min(ys)+max(ys))/2 + Y0, "x0": min(xs), "x1": max(xs)})
        res[i] = {"lines": sorted(lines, key=lambda l: l["y"]), "yel": yw}
    i += 1
json.dump(res, open(OUT, 'w'), ensure_ascii=False)
print(len(res))
