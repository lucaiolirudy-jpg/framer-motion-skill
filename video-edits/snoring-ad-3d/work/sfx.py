import json, sys, wave, numpy as np
from scipy.signal import butter, sosfilt
S = sys.argv[1]; plan = json.load(open(S + "/work/plan_full.json"))
SR = 44100; DUR = 336.4
rng = np.random.default_rng(1)
def whoosh(dur=0.5, peak=0.22, rise=True):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    bands = [(300, 600), (500, 1000), (800, 1600), (1300, 2600), (2000, 4000), (3000, 6000)]
    for k, (lo, hi) in enumerate(bands):
        sos = butter(2, [lo, hi], btype="band", fs=SR, output="sos")
        x = sosfilt(sos, rng.standard_normal(n + 2000))[2000:]
        c = (k / (len(bands) - 1)) * 0.6 * dur + 0.12 * dur if rise else (1 - k / (len(bands) - 1)) * 0.6 * dur + 0.12 * dur
        env = np.exp(-((t - c) / (0.16 * dur)) ** 2)
        out += x * env / (k + 1) ** 0.3
    env = np.minimum(1, t / (peak * dur)) * np.exp(-np.maximum(0, t - peak * dur) / (0.25 * dur))
    out *= env; out /= np.abs(out).max() + 1e-9
    return out
track = np.zeros(int(DUR * SR) + SR)
prev_e = -10
for c in plan:
    if c["s"] - prev_e < 0.05 and c["kind"] == "photo": prev_e = c["e"]; continue  # back-to-back photo montage: one whoosh only
    w = whoosh(0.45 if c["kind"] == "3d" else 0.38, rise=c["kind"] == "3d")
    gain = 10 ** (-17 / 20) if c["kind"] == "3d" else 10 ** (-20 / 20)
    st = int((c["s"] - 0.14) * SR); st = max(0, st)
    track[st:st + len(w)] += w * gain
    prev_e = c["e"]
pcm = (np.clip(track, -1, 1) * 32767).astype(np.int16)
st = np.stack([pcm, pcm], -1)
with wave.open(S + "/work/sfx.wav", "wb") as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes(st.tobytes())
print("ok")
