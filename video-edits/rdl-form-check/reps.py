import json, sys, numpy as np
from scipy.signal import find_peaks, savgol_filter
for f in "ab":
    P = json.load(open(f"{sys.argv[1]}/pose_{f}.json"))
    n = len(P); ang = np.full(n, np.nan); wy = np.full(n, np.nan)
    for i, p in enumerate(P):
        if not p: continue
        side = 0 if sum(p[k][2] for k in (11, 23, 25)) >= sum(p[k][2] for k in (12, 24, 26)) else 1
        sh, hp, wr = p[11 + side], p[23 + side], p[15 + side]
        ang[i] = np.degrees(np.arctan2(sh[0] - hp[0], hp[1] - sh[1]))  # 0 = upright, +90 = horizontal (facing right)
        wy[i] = wr[1]
    ok = ~np.isnan(ang); idx = np.arange(n)
    a = np.interp(idx, idx[ok], ang[ok]); a = savgol_filter(a, 9, 2)
    pk, _ = find_peaks(a, prominence=25, distance=30)
    va, _ = find_peaks(-a, prominence=25, distance=30)
    print(f, "frames", n, "bottoms(t,angle):", [(round(k / 30, 2), round(a[k])) for k in pk])
    print(f, "tops:", [(round(k / 30, 2), round(a[k])) for k in va])
    json.dump({"ang": a.tolist(), "bottoms": pk.tolist(), "tops": va.tolist()}, open(f"{sys.argv[1]}/reps_{f}.json", "w"))
