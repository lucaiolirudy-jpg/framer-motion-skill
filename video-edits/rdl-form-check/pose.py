import sys, json, subprocess, numpy as np, mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
V, OUT, MODEL = sys.argv[1:4]
W, H = 1080, 1920
opts = vision.PoseLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.VIDEO, num_poses=1,
                                    min_pose_detection_confidence=0.5, min_tracking_confidence=0.5)
lm = vision.PoseLandmarker.create_from_options(opts)
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', V, '-vf', 'scale=540:960', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
res = []; i = 0
while True:
    b = p.stdout.read(540 * 960 * 3)
    if len(b) < 540 * 960 * 3: break
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.frombuffer(b, np.uint8).reshape(960, 540, 3).copy())
    r = lm.detect_for_video(img, int(i * 1000 / 30))
    if r.pose_landmarks:
        res.append([[round(l.x * W, 1), round(l.y * H, 1), round(l.visibility, 2)] for l in r.pose_landmarks[0]])
    else: res.append(None)
    i += 1
json.dump(res, open(OUT, 'w'))
print(OUT, i, sum(r is not None for r in res))
