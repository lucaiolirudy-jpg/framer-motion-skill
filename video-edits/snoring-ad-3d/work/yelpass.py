import subprocess, numpy as np, json, sys
V, OUT = sys.argv[1:3]
Y0, HH = 1300, 200
p = subprocess.Popen(['ffmpeg','-v','error','-i',V,'-vf',f'crop=1080:{HH}:0:{Y0}','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
FS = 1080*HH*3; res = []
while True:
    buf = p.stdout.read(FS)
    if len(buf) < FS: break
    f = np.frombuffer(buf, np.uint8).reshape(HH,1080,3).astype(np.int16)
    yel = (f[...,0]>190)&(f[...,1]>190)&(f[...,2]<110)
    if yel.sum() < 120: res.append(None); continue
    ys, xs = np.nonzero(yel)
    # robust extents
    x0, x1 = np.percentile(xs, [1, 99]); yc = ys.mean() + Y0
    res.append([int(x0), int(x1), round(float(yc),1)])
json.dump(res, open(OUT,'w'))
print(len(res))
