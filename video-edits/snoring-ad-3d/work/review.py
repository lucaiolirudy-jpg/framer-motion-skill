import json, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, sys.argv[1] + "/work"); import subs
S = sys.argv[1]; t0, t1 = float(sys.argv[2]), float(sys.argv[3]); outp = sys.argv[4]
tl = json.load(open(S + "/work/subtimeline.json"))
sel = [c for c in tl if c["f1"] / 30 > t0 and c["f0"] / 30 < t1]
rows = []
for c in sel:
    # find frame of each highlight state
    f = c["f0"]; 
    for k, n in c["hl"]:
        fm = f + n // 2
        orig = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{fm/30:.3f}', '-i', S + '/src/video.mp4', '-frames:v', '1', '-vf', 'crop=1080:180:0:1310', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        o = Image.frombytes("RGB", (1080, 180), orig)
        bg = Image.new("RGBA", (1080, 1920), (70, 90, 120, 255))
        bg.alpha_composite(subs.render([(ws, y) for ws, y in c["lines"]], k if k >= 0 else None))
        r = bg.crop((0, 1310, 1080, 1490)).convert("RGB")
        row = Image.new("RGB", (1080, 380), (0, 0, 0)); row.paste(o, (0, 0)); row.paste(r, (0, 190))
        ImageDraw.Draw(row).text((5, 362), f'f0={c["f0"]} t={fm/30:.2f}', fill=(255, 80, 80))
        rows.append(row.resize((540, 190)))
        f += n
cols = 3; H = (len(rows) + cols - 1) // cols
sheet = Image.new("RGB", (540 * cols, 190 * H), (30, 30, 30))
for i, r in enumerate(rows): sheet.paste(r, ((i % cols) * 540, (i // cols) * 190))
sheet.save(outp); print(len(rows))
