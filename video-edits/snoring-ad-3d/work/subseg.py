import subprocess, numpy as np, json, sys
V=sys.argv[1]; OUT=sys.argv[2]
W,H=540,140  # crop y 1290..1570 full-res, half scale
p=subprocess.Popen(['ffmpeg','-v','error','-i',V,'-vf','crop=1080:280:0:1290,scale=540:140','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
prev=None; segs=[]; i=0; start=0
def mask(f):
    f=f.astype(np.int16); r,g,b=f[...,0],f[...,1],f[...,2]
    white=(r>238)&(g>238)&(b>238)
    yel=(r>200)&(g>200)&(b<90)
    return white|yel, yel
masks=[]
while True:
    buf=p.stdout.read(W*H*3)
    if len(buf)<W*H*3: break
    m,y=mask(np.frombuffer(buf,np.uint8).reshape(H,W,3))
    masks.append((int(m.sum()), int(y.sum())))
    if prev is not None:
        inter=(m&prev).sum(); uni=(m|prev).sum()+1
        iou=inter/uni
        if iou<0.55:
            segs.append([start,i]); start=i
    prev=m; i+=1
segs.append([start,i])
json.dump({"n":i,"segs":segs,"stats":masks},open(OUT,'w'))
print(i,len(segs))
