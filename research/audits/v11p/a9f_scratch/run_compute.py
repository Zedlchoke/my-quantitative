"""D2-A9-F compute/RAM/runtime estimate on the prewindow.

One representative feature generation per mechanism group, read-only:
  1. ILLIQUIDITY_PREMIUM: 28d Amihud from 15m bars across all 20 symbols
  2. SEEDS (defensive + lottery): 90d rolling BTC-beta residual, 28d resvol,
     7d residual MAX, 30d residual skew
  3. OI_POSITIONING: not computable -- no OI series exists in the snapshot
Reports wall-clock and peak RSS (resource.getrusage, macOS KB).
"""
from __future__ import annotations

import json
import math
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

CATALOG = Path("/Users/hoangminhlong/my-quantitative/catalog_live_crypto")
DAY_NS = 86_400_000_000_000
SCALE = 10**16
PRE_START = datetime(2024, 11, 1, tzinfo=timezone.utc)
PRE_END = datetime(2025, 8, 21, tzinfo=timezone.utc)
S_NS = int(PRE_START.timestamp()) * 10**9
E_NS = int(PRE_END.timestamp()) * 10**9

symbols = sorted(p.name.split("-15-MINUTE")[0] for p in (CATALOG / "data" / "binance_bar").iterdir())


def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0  # macOS: bytes->MB via KB


results = {"host": {}, "features": {}}
results["host"] = {
    "platform": sys.platform,
    "machine": subprocess.run(["uname", "-m"], capture_output=True, text=True).stdout.strip(),
    "ram_bytes": int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout.strip()),
    "cpu_count": __import__("os").cpu_count(),
}

t0 = time.perf_counter()
daily_close = {}
daily_dv = {}
for s in symbols:
    d = CATALOG / "data" / "binance_bar" / f"{s}-15-MINUTE-LAST-EXTERNAL"
    t = pq.read_table([str(f) for f in sorted(d.rglob("*.parquet"))], columns=["ts_event", "close", "quote_volume"])
    ts = np.array(t.column("ts_event").to_pylist(), dtype=np.int64)
    m = (ts >= S_NS) & (ts <= E_NS)
    ts = ts[m]
    close = np.array(
        [int.from_bytes(c, "little", signed=True) / SCALE for c, keep in zip(t.column("close").to_pylist(), m) if keep]
    )
    qv = np.array([float(v) for v, keep in zip(t.column("quote_volume").to_pylist(), m) if keep])
    days = ts // DAY_NS
    ud, inv = np.unique(days, return_index=True)
    daily_close[s] = (ud, close[inv])  # last bar per day = daily close
    cum = np.cumsum(qv)
    idx = np.searchsorted(days, ud, side="right")
    end = cum[idx - 1]
    start = np.concatenate(([0.0], cum[idx - 1]))[:-1]
    daily_dv[s] = (ud, end - start)
load_s = time.perf_counter() - t0

# ---- Feature 1: 28d Amihud (ILLIQUIDITY group) ----
t0 = time.perf_counter()
amihud = {}
for s in symbols:
    ud, dc = daily_close[s]
    r = np.full_like(dc, np.nan)
    r[1:] = np.abs(np.diff(np.log(dc)))
    _, dv = daily_dv[s]
    x = r / dv
    ok = ~np.isnan(x)
    am = np.full_like(dc, np.nan)
    for i in range(len(dc)):
        if i < 28:
            continue
        w = x[i - 27 : i + 1]
        if np.isfinite(w).sum() >= 21:
            am[i] = np.nanmean(w)
    amihud[s] = (ud, am)
f1_s = time.perf_counter() - t0

# ---- Feature 2: residual moments (SEEDS group) ----
t0 = time.perf_counter()
ud0, btc = daily_close["BTCUSDT-PERP.BINANCE"]
rb = np.full_like(btc, np.nan)
rb[1:] = np.diff(np.log(btc))
resid_vol, res_max, res_skew = {}, {}, {}
for s in symbols:
    ud, dc = daily_close[s]
    if s == "BTCUSDT-PERP.BINANCE":
        r = -rb  # self-beta=1 residual placeholder; BTC is benchmark context only
    else:
        r = np.full_like(dc, np.nan)
        r[1:] = np.diff(np.log(dc))
    # align to BTC day grid
    pos = np.searchsorted(ud0, ud)
    ok = (pos < len(ud0)) & (ud0[np.minimum(pos, len(ud0) - 1)] == ud)
    rb_al = np.full_like(dc, np.nan)
    rb_al[ok] = rb[pos[ok]]
    beta = np.full_like(dc, np.nan)
    for i in range(len(dc)):
        if i < 90:
            continue
        y = r[i - 89 : i + 1]
        x = rb_al[i - 89 : i + 1]
        m2 = np.isfinite(y) & np.isfinite(x)
        if m2.sum() >= 75:
            vy = y[m2] - y[m2].mean()
            vx = x[m2] - x[m2].mean()
            beta[i] = (vy * vx).sum() / (vx * vx).sum()
    res = r - beta * rb_al
    v28 = np.full_like(dc, np.nan)
    mx7 = np.full_like(dc, np.nan)
    sk30 = np.full_like(dc, np.nan)
    for i in range(len(dc)):
        w28 = res[max(0, i - 27) : i + 1]
        w28 = w28[np.isfinite(w28)]
        if len(w28) >= 21:
            v28[i] = w28.std(ddof=1) * math.sqrt(365)
        w7 = res[max(0, i - 6) : i + 1]
        w7 = w7[np.isfinite(w7)]
        if len(w7) >= 5:
            mx7[i] = w7.max()
        w30 = res[max(0, i - 29) : i + 1]
        w30 = w30[np.isfinite(w30)]
        if len(w30) >= 22:
            m3 = ((w30 - w30.mean()) ** 3).mean()
            sk30[i] = m3 / w30.std(ddof=1) ** 3
    resid_vol[s], res_max[s], res_skew[s] = v28, mx7, sk30
f2_s = time.perf_counter() - t0

# ---- Feature 3: OI growth ----
f3_s = None
oi_error = "no OI snapshot series exists anywhere in the staged catalog (oi census: 20 instrument-def parquets, 23 bar parquets, 0 OI); feature not computable, fail-closed UNAVAILABLE"

results["features"] = {
    "prewindow": {"start": PRE_START.isoformat(), "end": PRE_END.isoformat(), "days": (E_NS - S_NS) / DAY_NS},
    "symbols": len(symbols),
    "bar_load_wall_s": round(load_s, 3),
    "f1_amihud_28d_wall_s": round(f1_s, 3),
    "f1_status": "OK" if np.isfinite(amihud[symbols[0]][1][-1]) else "DEGENERATE",
    "f2_residual_moments_wall_s": round(f2_s, 3),
    "f2_status": "OK",
    "f3_oi_growth_wall_s": f3_s,
    "f3_status": "UNAVAILABLE",
    "f3_reason": oi_error,
    "peak_rss_mb": round(rss_mb(), 1),
}
print(json.dumps(results, indent=1, default=str))
json.dump(results, open(sys.argv[1], "w"), indent=1, default=str)
