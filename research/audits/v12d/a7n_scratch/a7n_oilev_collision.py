"""A7-N scratch: reserved-OILEV collision diagnostic.

Computes the OILEV-V2-style features (28d OI flow, OI stock level) cross-
sectional ranks at each S0 Monday stamp from the read-only consolidated OI
parquets and reports Spearman rank correlation against every proposal anchor
feature. Diagnostics only; no PnL, no strategy returns.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

OI_ROOT = "/Users/hoangminhlong/my-quantitative/oi_data/consolidated"
SYMBOLS = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT", "BCHUSDT",
    "BNBUSDT", "BOMEUSDT", "DOGEUSDT", "ENAUSDT", "ETHUSDT",
    "LINKUSDT", "NEARUSDT", "ONGUSDT", "SOLUSDT", "SUIUSDT", "WLDUSDT",
    "XRPUSDT", "ZECUSDT",
]
DAY = 86_400 * 10**9
WEEK = 7 * DAY

oi = {}
for s in SYMBOLS:
    t = pq.read_table(os.path.join(OI_ROOT, f"{s}_oi.parquet")).to_pandas()
    t["d"] = pd.to_datetime(t["create_time"]).map(lambda x: int(x.timestamp()))  # epoch seconds
    t["dn"] = t["d"].astype("int64")  # seconds
    oi[s] = t.sort_values("d").reset_index(drop=True)


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if len(a) < 3 or ra.std() == 0 or rb.std() == 0:
        return np.nan
    return float(np.corrcoef(ra, rb)[0, 1])


def oi_features(sym: str, T: int) -> dict:
    t = oi[sym]
    T_s = T // 10**9
    d28 = t[(t["dn"] > T_s - 28 * 86400) & (t["dn"] <= T_s)]
    d56 = t[(t["dn"] > T_s - 56 * 86400) & (t["dn"] <= T_s)]
    out = {}
    if len(d28) >= 24:
        flow = d28["sum_open_interest"].diff().dropna().sum()
        base = d28["sum_open_interest"].mean()
        if base > 0:
            out["oi_flow28"] = float(flow / base)
    if len(d56) >= 48:
        out["oi_stock"] = float(d56["sum_open_interest"].iloc[-1])
    return out


def monday_stamps(start_ns, end_ns):
    off = 4 * DAY
    r = start_ns % WEEK
    delta = off - r
    if delta < 0:
        delta += WEEK
    t = start_ns + delta
    out = []
    while t <= end_ns:
        out.append(t)
        t += WEEK
    return out


WINDOW_START = int(datetime(2025, 8, 22, tzinfo=timezone.utc).timestamp() * 1e9)
WINDOW_END = int(datetime(2026, 8, 21, tzinfo=timezone.utc).timestamp() * 1e9)
stamps = monday_stamps(WINDOW_START, WINDOW_END)

# proposal anchor features recomputed cheaply here is out of scope; load from
# the similarity run's per-stamp values via a re-run of features_at is avoided.
# Instead: correlation of OILEV features with the PROPOSAL features is computed
# in the companion script; here we record OI feature availability + the
# OI-vs-ticket/beta correlations using the persisted per-stamp rank vectors is
# not possible, so we correlate OI ranks against ticket/beta ranks computed
# inline via the same loader used in a7n_feature_similarity.
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "a7nfeat", os.path.join(os.path.dirname(os.path.abspath(__file__)), "a7n_feature_similarity.py"))
# Do not execute the module (it runs the full job); instead replicate minimal parts.
# --- minimal replication ---
BARS_ROOT = "/Users/hoangminhlong/my-quantitative/catalog_live_crypto/data/binance_bar"
ALL_SYMBOLS = SYMBOLS[:8] + ["BTCUSDT"] + SYMBOLS[8:]
TRADED = SYMBOLS
NS_PER_15M = 900 * 10**9


def snap_to_slot(ts):
    r = ts % NS_PER_15M
    d = (NS_PER_15M - r) % NS_PER_15M
    return np.where(d < NS_PER_15M // 2, ts + d, ts)


def load_symbol(sym):
    d = os.path.join(BARS_ROOT, f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL")
    closes, qvs, counts, tss = [], [], [], []
    prec = None
    for fn in sorted(os.listdir(d)):
        t = pq.read_table(os.path.join(d, fn))
        md = t.schema.metadata or {}
        if prec is None:
            for k, v in md.items():
                if k == b"price_precision":
                    prec = int(v.decode())
        df = t.select(["close", "quote_volume", "count", "ts_event"]).to_pandas()
        raw = np.array([int.from_bytes(b, "big") for b in df["close"].values], dtype=np.float64)
        closes.append(raw / (10**prec))
        qvs.append(df["quote_volume"].astype(float).values)
        counts.append(df["count"].astype(np.int64).values)
        tss.append(df["ts_event"].values.astype(np.int64))
    rows = sorted(zip(np.concatenate(tss).tolist(), np.concatenate(closes).tolist(),
                      np.concatenate(qvs).tolist(), np.concatenate(counts).tolist()))
    ts = snap_to_slot(np.array([r[0] for r in rows], dtype=np.int64))
    return ts, np.array([r[1] for r in rows]), np.array([r[2] for r in rows]), np.array([r[3] for r in rows], dtype=np.int64), prec


bars = {}
for s in ALL_SYMBOLS:
    ts, close, qv, cnt, prec = load_symbol(s)
    day_idx = ts // DAY
    days = np.unique(day_idx)
    dc = np.array([close[day_idx == d][-1] for d in days])
    bars[s] = {"ts": ts, "qv": qv, "cnt": cnt, "days": days, "dc": dc}

btc_map = dict(zip(bars["BTCUSDT"]["days"].tolist(),
                   np.log(bars["BTCUSDT"]["dc"][1:] / bars["BTCUSDT"]["dc"][:-1]).tolist(),
                   ))
btc_ret = {}
bd = bars["BTCUSDT"]["days"]; bdc = bars["BTCUSDT"]["dc"]
for i in range(1, len(bd)):
    btc_ret[int(bd[i])] = float(np.log(bdc[i] / bdc[i - 1]))

res = {"beta90_vs_oi_flow28": [], "beta90_vs_oi_stock": [],
       "ticket_a6p1_vs_oi_flow28": [], "ticket_a8p2_vs_oi_flow28": [],
       "ticket_a5p2_vs_oi_flow28": [], "amihud28_vs_oi_flow28": []}
for T in stamps:
    dayT = int(T // DAY)
    betas, flows, stocks, t61, t82, t52, amh = {}, {}, {}, {}, {}, {}, {}
    for s in TRADED:
        b = bars[s]
        dmap = dict(zip(b["days"].tolist(), b["dc"].tolist()))
        blk = b["days"][(b["days"] > dayT - 90) & (b["days"] <= dayT)]
        rs, rb = [], []
        for dd in blk[1:]:
            p = int(dd) - 1
            if p in dmap and np.isfinite(dmap[p]) and np.isfinite(dmap[dd]) and int(dd) in btc_ret:
                rs.append(np.log(dmap[dd] / dmap[p])); rb.append(btc_ret[int(dd)])
        if len(rs) >= 60:
            rs = np.array(rs); rb = np.array(rb)
            betas[s] = float(np.cov(rs, rb)[0, 1] / rb.var())
        f = oi_features(s, T)
        if "oi_flow28" in f:
            flows[s] = f["oi_flow28"]
        if "oi_stock" in f:
            stocks[s] = f["oi_stock"]
        ts, qv, cnt = b["ts"], b["qv"], b["cnt"]
        m28 = (ts > T - 28 * DAY) & (ts <= T)
        v = cnt[m28] > 0
        if m28.sum():
            t61[s] = float(qv[m28][v].sum() / max(cnt[m28][v].sum(), 1))
        m30 = (ts > T - 30 * DAY) & (ts <= T)
        m60 = (ts > T - 90 * DAY) & (ts <= T - 30 * DAY)
        if m30.sum() and m60.sum() and (cnt[m30] > 0).mean() >= 0.8 and (cnt[m60] > 0).mean() >= 0.8:
            rec = qv[m30][cnt[m30] > 0].sum() / cnt[m30][cnt[m30] > 0].sum()
            base = qv[m60][cnt[m60] > 0].sum() / cnt[m60][cnt[m60] > 0].sum()
            if base > 0:
                t52[s] = float(rec / base)
        wk = []
        ok = True
        for k in range(12, 0, -1):
            m = (ts > T - k * WEEK) & (ts <= T - (k - 1) * WEEK)
            csum = cnt[m].sum()
            if csum > 0 and m.sum():
                wk.append(qv[m].sum() / csum)
            else:
                ok = False; break
        if ok and len(wk) == 12:
            med = float(np.median(wk))
            if med > 0:
                t82[s] = float(wk[-1] / med)
        dq = []
        for dd in blk[1:]:
            p = int(dd) - 1
            if p in dmap and np.isfinite(dmap[p]) and np.isfinite(dmap[dd]):
                md_ = (ts > p * DAY) & (ts <= dd * DAY)
                qsum = qv[md_].sum()
                if qsum > 0:
                    dq.append(abs(np.log(dmap[dd] / dmap[p])) / qsum)
        if len(dq) >= 60:
            amh[s] = float(np.mean(dq))

    def rho(d1, d2):
        common = sorted(set(d1) & set(d2))
        if len(common) < 10:
            return None
        return spearman([d1[s] for s in common], [d2[s] for s in common])

    for key, (d1, d2) in {
        "beta90_vs_oi_flow28": (betas, flows),
        "beta90_vs_oi_stock": (betas, stocks),
        "ticket_a6p1_vs_oi_flow28": (t61, flows),
        "ticket_a8p2_vs_oi_flow28": (t82, flows),
        "ticket_a5p2_vs_oi_flow28": (t52, flows),
        "amihud28_vs_oi_flow28": (amh, flows),
    }.items():
        r = rho(d1, d2)
        if r is not None and np.isfinite(r):
            res[key].append(r)

summary = {}
for k, v in res.items():
    v = np.abs(np.array(v))
    summary[k] = {
        "n_stamps": int(len(v)),
        "mean_abs_rho": round(float(v.mean()), 4),
        "median_abs_rho": round(float(np.median(v)), 4),
        "max_abs_rho": round(float(v.max()), 4),
        "share_ge_0.50": round(float((v >= 0.50).mean()), 4) if len(v) else None,
        "share_ge_0.70": round(float((v >= 0.70).mean()), 4) if len(v) else None,
    }

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "a7n_oilev_collision_raw.json"), "w") as fh:
    json.dump({"generated_utc": datetime.now(timezone.utc).isoformat(),
               "scope": "S0 Monday stamps, OILEV-style 28d OI flow vs proposal features",
               "summary": summary}, fh, indent=1, sort_keys=True)
print(json.dumps(summary, indent=1))
