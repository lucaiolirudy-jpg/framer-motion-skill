# Build clean subtitle timeline: chunks with lines/words/centers + per-frame highlighted word
import json, sys, re, itertools, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, sys.argv[1] + "/work"); import subs
S = sys.argv[1]; V = S + "/src/video.mp4"
raw = json.load(open(S + "/work/chunks_raw.json")); yel = json.load(open(S + "/work/yel.json"))
FIX = json.load(open(S + "/work/subfix.json")) if len(sys.argv) > 2 else {}
def norm(t):
    t = t.replace("’", "'").replace("`", "'")
    t = re.sub(r"[^A-ZÀ-Ü0-9'%€\.\,\s]", "", t.upper())
    return t.split()
def mid_frame(c): return (c["f0"] + c["f1"]) // 2
# grab mid frames of each chunk (subtitle band only)
need = sorted(set(mid_frame(c) for c in raw))
Y0, HH = 1300, 200
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', V, '-vf', f'crop=1080:{HH}:0:{Y0}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
frames = {}; i = 0; ns = set(need)
while True:
    b = p.stdout.read(1080 * HH * 3)
    if len(b) < 1080 * HH * 3: break
    if i in ns: frames[i] = np.frombuffer(b, np.uint8).reshape(HH, 1080, 3)
    i += 1
def tmask(a):
    a = a.astype(int); w = (a[..., 0] > 235) & (a[..., 1] > 235) & (a[..., 2] > 235); y = (a[..., 0] > 190) & (a[..., 1] > 190) & (a[..., 2] < 110)
    dark = (a.sum(-1) < 150)
    from scipy.ndimage import binary_dilation
    near = binary_dilation(dark, iterations=5)
    return (w | y) & near
def score(lines, fr):
    ov = np.array(subs.render(lines))[Y0:Y0 + HH]
    m = ov[..., 3] > 128
    m2 = (ov[..., 0] > 200) & m
    xs = np.nonzero(m2.any(0))[0]
    if len(xs) == 0: return 0
    t = tmask(fr)
    inter = (m2 & t).sum(); uni = (m2 | t).sum() + 1
    return inter / uni
out = []
for ci, c in enumerate(raw):
    key = str(c["f0"])
    fr = frames[mid_frame(c)]
    if key in FIX:
        fx = FIX[key]
        if fx == "DROP": continue
        cand_lines = [[(l.split(), y) for l, y in zip(fx["lines"], fx.get("ys", [1399] if len(fx["lines"]) == 1 else [1366, 1432]))]]
    else:
        base = [(norm(l["t"]), l["y"], (l["x0"] + l["x1"]) / 2, l["x1"] - l["x0"]) for l in c["lines"]]
        # candidate token removals of suspicious single chars
        sus = [(li, wi) for li, (ws, *_r) in enumerate(base) for wi, w in enumerate(ws) if len(w) == 1 and w in "IFS$EÈ"]
        cand_lines = []
        for k in range(len(sus) + 1):
            for comb in itertools.combinations(sus, k):
                L = []
                for li, (ws, y, cx, wd) in enumerate(base):
                    nw = [w for wi, w in enumerate(ws) if (li, wi) not in comb]
                    if nw: L.append((nw, y))
                cand_lines.append(L)
            if len(cand_lines) > 32: break
    best = None
    cand_lines = [L for L in cand_lines if L]
    if not cand_lines: continue
    for L in cand_lines:
        # snap y to standard rows
        ys = [1399] if len(L) == 1 else [1366, 1432] if len(L) == 2 else [1333, 1399, 1465]
        L2 = [(ws, ys[i]) for i, (ws, y) in enumerate(L)]
        s = score(L2, fr)
        if best is None or s > best[0]: best = (s, L2)
    s, L = best
    out.append({"f0": c["f0"], "f1": c["f1"], "lines": [[ws, y] for ws, y in L], "score": round(float(s), 3)})
# per frame highlight index
for c in out:
    boxes = subs.word_boxes([(ws, y) for ws, y in c["lines"]])
    hl = []
    for f in range(c["f0"], c["f1"]):
        e = yel[f] if f < len(yel) else None
        if not e: hl.append(-1); continue
        x0, x1, yc = e; xc = (x0 + x1) / 2
        best = min(range(len(boxes)), key=lambda i: abs((boxes[i][1] + boxes[i][2]) / 2 - xc) + 3 * abs(boxes[i][3] - yc))
        hl.append(best)
    # run-length encode
    c["hl"] = [[k, len(list(g))] for k, g in itertools.groupby(hl)]
json.dump(out, open(S + "/work/subtimeline.json", "w"), ensure_ascii=False)
for c in out:
    flag = "  <<<" if c["score"] < 0.8 else ""
    print(f'{c["f0"]:5d} {c["f0"]/30:7.2f}-{c["f1"]/30:7.2f} {c["score"]:.2f} | ' + " / ".join(" ".join(ws) for ws, y in c["lines"]) + flag)
