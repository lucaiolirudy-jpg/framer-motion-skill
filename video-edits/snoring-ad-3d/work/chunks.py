import json, re, sys
S = sys.argv[1]
d = json.load(open(S + "/work/subocr.json")); segs = json.load(open(S + "/work/subsegs.json"))
N = segs["n"]
keys = sorted(map(int, d))
def lines_of(e):
    bs = [l for l in e["lines"] if float(l["c"]) > 0.5 and l["t"].strip()]
    rows = []
    for b in sorted(bs, key=lambda b: b["y"]):
        for r in rows:
            if abs(r["y"] - b["y"]) < 20: r["b"].append(b); break
        else: rows.append({"y": b["y"], "b": [b]})
    out = []
    for r in rows:
        bb = sorted(r["b"], key=lambda b: b["x0"])
        txt = " ".join(b["t"].strip() for b in bb).upper()
        txt = re.sub(r"\s+", " ", txt)
        out.append({"y": round(sum(b["y"] for b in bb) / len(bb)), "x0": round(min(b["x0"] for b in bb)), "x1": round(max(b["x1"] for b in bb)), "t": txt})
    return out
chunks = []
for i, k in enumerate(keys):
    e = d[str(k)]; ls = lines_of(e)
    end = keys[i + 1] if i + 1 < len(keys) else N
    sig = " / ".join(l["t"] for l in ls)
    if chunks and chunks[-1]["sig"] == sig and chunks[-1]["f1"] == k:
        chunks[-1]["f1"] = end; continue
    chunks.append({"f0": k, "f1": end, "sig": sig, "lines": ls})
chunks = [c for c in chunks if c["sig"]]
json.dump(chunks, open(S + "/work/chunks_raw.json", "w"), ensure_ascii=False, indent=0)
for c in chunks: print(f'{c["f0"]/30:7.2f}-{c["f1"]/30:7.2f} | {c["sig"]}')
