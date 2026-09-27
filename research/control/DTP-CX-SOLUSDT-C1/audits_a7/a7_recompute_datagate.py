#!/usr/bin/env python
"""A7 — B: timestamp-scale scan (L-TRACKB1-1) + 2024-06 cross-granularity spot check."""
import csv, io, json, zipfile

W = ("/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/"
     "integration/research/control/DTP-CX-SOLUSDT-C1")
PWS = ("/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-solusdt-c1/"
       "integration/research/control/PWS-CX-SOLUSDT-C1/data_local")
DAY_LO, DAY_HI = 1718409600000, 1718496000000  # 2024-06-15T00:00Z..2024-06-16T00:00Z
TOL_A, TOL_R = 1e-6, 1e-9


def read(path):
    """ts -> [open, high, low, close, volume, quote_volume]"""
    out = {}
    with zipfile.ZipFile(path) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            for row in csv.reader(io.TextIOWrapper(fh, "utf-8", newline="")):
                if len(row) < 8 or not row[0].isdigit():
                    continue
                t = int(row[0])
                if t >= 10 ** 14:
                    t //= 1000
                out[t] = [float(row[1]), float(row[2]), float(row[3]),
                          float(row[4]), float(row[5]), float(row[7])]
    return out


def scale_scan(tag):
    r = read(f"{W}/data_local/vision/klines_um_SOLUSDT_1m/SOLUSDT-1m-{tag}.zip")
    ks = sorted(r)
    mx = max(ks)
    return {"month": tag, "rows": len(r), "first": ks[0], "last": ks[-1],
            "max_ts": mx, "all_ms": mx < 10 ** 14,
            "gaps": sum(1 for a, b in zip(ks, ks[1:]) if b - a != 60000),
            "dups": len(ks) != len(r)}


def agg(src, step):
    """aggregate 1m bars into step-ms buckets: first open, max high, min low, last close, sum vol, sum qvol"""
    b = {}
    for t in sorted(src):
        k = t - (t % step)
        v = src[t]
        if k not in b:
            b[k] = [v[0], v[1], v[2], v[3], v[4], v[5]]
        else:
            x = b[k]
            x[1] = max(x[1], v[1]); x[2] = min(x[2], v[2])
            x[3] = v[3]; x[4] += v[4]; x[5] += v[5]
    return b


def close_enough(a, b):
    for x, y in zip(a, b):
        if abs(x - y) > TOL_A and abs(x - y) > TOL_R * max(abs(x), abs(y)):
            return False, (x, y)
    return True, None


res = {"scale_scan": [scale_scan(t) for t in ("2020-09", "2023-07", "2026-08")], "xg": {}}
k1 = read(f"{W}/data_local/vision/klines_um_SOLUSDT_1m/SOLUSDT-1m-2024-06.zip")
d1 = {t: v for t, v in k1.items() if DAY_LO <= t < DAY_HI}
a15 = agg(d1, 900000); a60 = agg(d1, 3600000)
f15 = read(f"{W}/data_local/vision/klines_um_SOLUSDT_15m/SOLUSDT-15m-2024-06.zip")
f15 = {t: v for t, v in f15.items() if DAY_LO <= t < DAY_HI}
f60 = read(f"{PWS}/vision/klines_um_SOLUSDT_1h/2024-06.zip")
f60 = {t: v for t, v in f60.items() if DAY_LO <= t < DAY_HI}
for name, agg_d, ref_d in [("15m_vs_1m", a15, f15), ("1h_vs_1m", a60, f60)]:
    ks_a, ks_r = sorted(agg_d), sorted(ref_d)
    mm = []
    if ks_a != ks_r:
        mm.append(f"grid mismatch: agg {len(ks_a)} vs ref {len(ks_r)}")
    for t in ks_a:
        if t in ref_d:
            ok, detail = close_enough(agg_d[t], ref_d[t])
            if not ok:
                mm.append((t, detail))
    res["xg"][name] = {"checked": len(ks_a), "ref_buckets": len(ks_r), "mismatched": len(mm),
                       "detail": mm[:5]}
print(json.dumps(res, indent=1))
with open(W + "/audits_a7/a7_datagate_spot_machine@1.json", "w") as fh:
    json.dump(res, fh, indent=1)
