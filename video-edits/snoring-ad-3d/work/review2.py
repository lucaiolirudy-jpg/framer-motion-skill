import json, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, sys.argv[1] + "/work"); import subs
S = sys.argv[1]; plan = json.load(open(S + "/work/plan_full.json"))
tl = json.load(open(S + "/work/subtimeline.json"))
sel = [c for c in tl if any(c["f1"] / 30 > p["s"] and c["f0"] / 30 < p["e"] for p in plan) and c["f0"] / 30 > float(sys.argv[2])]
# decode needed frames in one pass
need = {(c["f0"] + c["f1"]) // 2: c for c in sel}
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', S + '/src/video.mp4', '-vf', 'crop=1080:180:0:1310', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
fr = {}; i = 0
while True:
    b = p.stdout.read(1080 * 180 * 3)
    if len(b) < 1080 * 180 * 3: break
    if i in need: fr[i] = Image.frombytes("RGB", (1080, 180), b)
    i += 1
rows = []
for fm, c in sorted(need.items()):
    bg = Image.new("RGBA", (1080, 1920), (70, 90, 120, 255)); bg.alpha_composite(subs.render([(ws, y) for ws, y in c["lines"]]))
    r = bg.crop((0, 1310, 1080, 1490)).convert("RGB")
    row = Image.new("RGB", (1080, 360)); row.paste(fr[fm], (0, 0)); row.paste(r, (0, 180))
    ImageDraw.Draw(row).text((5, 340), str(c["f0"]), fill=(255, 60, 60))
    rows.append(row.resize((432, 144)))
per = 45; cols = 5
for k in range(0, len(rows), per):
    chunk = rows[k:k + per]; H = (len(chunk) + cols - 1) // cols
    sh = Image.new("RGB", (432 * cols, 144 * H), (20, 20, 20))
    for j, r in enumerate(chunk): sh.paste(r, ((j % cols) * 432, (j // cols) * 144))
    sh.save(f"{S}/frames/rev2_{k // per}.jpg", quality=88)
print(len(rows))
