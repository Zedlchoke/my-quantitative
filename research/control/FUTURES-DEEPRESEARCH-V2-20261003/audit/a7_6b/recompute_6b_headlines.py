#!/usr/bin/env python
"""A7-DEEP-6B fresh-context independent recompute of 6B_DEEP_v2 headline numbers.

Read-only audit: loads RAW vendor parquet + nonprice inputs directly (NOT the
lane's 6B_cache derived parquets), rebuilds sessions/chains/rolls with an
independent implementation, and recomputes the dossier's headline claims.

Outputs: audit/a7_6b/recompute_6b_headlines.json (same dir as this script).
"""
from __future__ import annotations

import datetime as dt
import glob
import io
import json
import os
import re
import zipfile
from xml.etree import ElementTree

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
NONPRICE = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
CHI, LON = "America/Chicago", "Europe/London"
PX = 1e9
TICK = 0.0001
OUT: dict = {}

# ---------------------------------------------------------------- load raw panel
files = (sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1B-O1M-6B-BACKFILL2/*.parquet"))
         + sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1R-O1M-6B-BACKFILL/*.parquet"))
         + sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-O1M-6B/*.parquet")))
OUT["input_files"] = [os.path.basename(f) for f in files]
frames = []
for f in files:
    d = pd.read_parquet(f)
    frames.append(d[~d["raw_symbol"].str.contains("-")])  # outrights only
df = pd.concat(frames, ignore_index=True)
df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
df = df.sort_values("dt").reset_index(drop=True)
OUT["panel_rows_outright"] = int(len(df))
OUT["panel_span"] = [str(df["dt"].min()), str(df["dt"].max())]

# ---------------------------------------------------------------- session date
loc = df["dt"].dt.tz_convert(CHI)
sd = loc.dt.normalize()
# calendar-day +1 (pd.offsets.Day, NOT 24h timedelta — fall-back DST trap the
# lane's lib explicitly avoids; first draft of this audit script had that bug)
sd = sd + pd.offsets.Day(0)
sd = sd.where(loc.dt.hour < 17, sd + pd.offsets.Day(1))
df["session_date"] = sd.dt.tz_localize(None).dt.date

# ---------------------------------------------------------------- registry (independent)
MONTH = {"H": 3, "M": 6, "U": 9, "Z": 12}
CODE = {3: "H", 6: "M", 9: "U", 12: "Z"}


def third_wed(y, m):
    d = dt.date(y, m, 1)
    off = (2 - d.weekday()) % 7
    return d + dt.timedelta(days=off + 14)


def approx_ltd(y, m):
    d = third_wed(y, m)
    n = 0
    while n < 2:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return d


reg = {}
panel_max = df["dt"].max()
for sym, g in df.groupby("raw_symbol"):
    m = re.fullmatch(r"6B([HMUZ])(\d)", sym)
    if not m:
        continue  # serials/foreign excluded (counted separately by lane a7)
    g = g.sort_values("dt")
    # cluster on >45d gaps
    newcl = (g["dt"].diff() > pd.Timedelta(days=45)).astype(int).cumsum()
    for cid, gg in g.groupby(newcl.values):
        t1 = gg["dt"].max()
        digit = int(m.group(2))
        mc = MONTH[m.group(1)]
        hits = []
        for y in range(2019, 2029):
            if y % 10 != digit:
                continue
            ltd = approx_ltd(y, mc)
            delta = (t1.tz_localize(None) - pd.Timestamp(ltd)).days
            if -100 <= delta <= 12:
                # cluster dies near its own LTD (expired contract)
                hits.append((y, ltd))
            elif t1 == panel_max and pd.Timestamp(ltd) >= t1.tz_localize(None):
                # cluster straddles the panel cut: still-live contract
                hits.append((y, ltd))
        if len(hits) == 1:
            reg[(sym, cid)] = {"year": hits[0][0], "expiry": hits[0][1],
                               "first": gg["dt"].min(), "last": t1,
                               "bars": len(gg), "vol": int(gg["volume"].sum())}
df["_cl"] = (df.assign(_d=df["dt"])
             .groupby("raw_symbol")["_d"].diff()
             > pd.Timedelta(days=45)).groupby(df["raw_symbol"]).cumsum().fillna(0)
df["_key"] = list(zip(df["raw_symbol"], df["_cl"]))
lut = {k: f"6B{CODE[v['expiry'].month]}{v['year']}" for k, v in reg.items()}
df["contract"] = df["_key"].map(lut)
resolved = sorted({v["year"] * 100 + v["expiry"].month for v in reg.values()})
OUT["n_quarterly_clusters_resolved"] = len(reg)

# ---------------------------------------------------------------- session table
d2 = df[df["contract"].notna()]
sess = (d2.groupby(["session_date", "contract"])
        .agg(close=("close", "last"), high=("high", "max"), low=("low", "min"),
             volume=("volume", "sum"), n_bars=("volume", "size"))
        .reset_index())
for c in ("close", "high", "low"):
    sess[c] = sess[c] / PX
sess["d"] = pd.to_datetime(sess["session_date"])

# calendar-rule held chain: order contracts by expiry month
corder = sorted(sess["contract"].unique(),
                key=lambda c: (int(c[-4:]), "HMUZ".index(c[2])))
fronts = []
for i, c in enumerate(corder):
    exp_m = pd.Timestamp(int(c[-4:]), "HMUZ".index(c[2]) * 3 + 3, 1)
    sub = sess[sess["contract"] == c]
    held_win = sub[sub["d"] < exp_m]
    if i > 0:
        prev_m = pd.Timestamp(int(corder[i - 1][-4:]),
                              "HMUZ".index(corder[i - 1][2]) * 3 + 3, 1)
        held_win = held_win[held_win["d"] >= prev_m]
    if len(held_win):
        fronts.append(held_win[["session_date", "contract"]])
held = (pd.concat(fronts).groupby("session_date")["contract"]
        .last().rename("held").reset_index())
chain = sess.merge(held, on="session_date")
chain = chain[chain["contract"] == chain["held"]].sort_values("d").reset_index(drop=True)
chain["ret"] = chain["close"].pct_change()
chain.loc[chain["held"] != chain["held"].shift(), "ret"] = np.nan
chain.loc[chain["n_bars"] < 600, "ret"] = np.nan  # thin/truncated sessions
r = chain["ret"].dropna()
OUT["chain"] = {"n_days": int(len(r)),
                "ann_vol_pct": float(r.std() * np.sqrt(252) * 100),
                "min_ret_pct": float(r.min() * 100),
                "min_date": str(chain.loc[r.idxmin(), "d"].date()),
                "max_ret_pct": float(r.max() * 100)}

# ---------------------------------------------------------------- VR21
def vr(x, q):
    x = x.dropna().values
    mu = x.mean()
    n = len(x) // q * q
    xs = x[:n].reshape(-1, q).sum(axis=1)
    return float(np.var(xs - q * mu, ddof=1) / (q * np.var(x, ddof=1)))


vr_all = {f"q{q}": vr(r, q) for q in (2, 5, 10, 21, 63)}
OUT["variance_ratio_full"] = vr_all
OUT["vr21_by_year"] = {
    int(y): vr(g["ret"], 21)
    for y, g in chain.dropna(subset=["ret"]).groupby(chain["d"].dt.year)}

# ---------------------------------------------------------------- drawdown
c = chain.dropna(subset=["ret"]).reset_index(drop=True)
cum = (1 + c["ret"]).cumprod()
dd = cum / cum.cummax() - 1
OUT["max_drawdown_pct"] = float(dd.min() * 100)
OUT["max_drawdown_date"] = str(c.loc[dd.idxmin(), "d"].date())

# ---------------------------------------------------------------- 2022 turmoil
tur = chain[(chain["d"] >= "2022-08-25") & (chain["d"] <= "2022-10-21")]
byday = {str(t.d.date()): {"ret_pct": None if pd.isna(t.ret) else round(t.ret * 100, 3),
                           "low": float(t.low), "vol": int(t.volume)}
         for t in tur.itertuples()}
OUT["turmoil_2022"] = {
    "sep23": byday.get("2022-09-23"),
    "sep26": byday.get("2022-09-26"),
    "sep28": byday.get("2022-09-28"),
    "sep29": byday.get("2022-09-29"),
    "max_volume_day": max(byday, key=lambda k: byday[k]["vol"]),
    "max_volume": max(v["vol"] for v in byday.values()),
    "min_low": min(v["low"] for v in byday.values()),
    "ep_ann_vol_pct": float(tur["ret"].dropna().std() * np.sqrt(252) * 100),
    "median_day_volume_all_chain": float(chain["volume"].median()),
}

# ---------------------------------------------------------------- roll table
rolls = []
expmap = {f"6B{CODE[v['expiry'].month]}{v['year']}": pd.Timestamp(v["expiry"])
          for v in reg.values()}
for i in range(len(corder) - 1):
    old, new = corder[i], corder[i + 1]
    exp_old = expmap[old]
    dm0 = exp_old.replace(day=1)
    o = sess[sess["contract"] == old].sort_values("d")
    n = sess[sess["contract"] == new].sort_values("d")
    pre = o[o["d"] < dm0]
    if not len(pre):
        continue
    rd = pre["d"].max()
    orow = o[o["d"] == rd]
    nrow = n[n["d"] == rd]
    if not len(nrow):
        continue
    if int(orow["volume"].iloc[0]) < 1000 or int(orow["n_bars"].iloc[0]) < 300:
        continue  # genuine front-chain rolls only (lane's filter)
    gap = float(nrow["close"].iloc[0] - orow["close"].iloc[0])
    # volume crossover (trailing-5 mean, decided at close)
    ov, nv = o.set_index("d")["volume"], n.set_index("d")["volume"]
    idx = ov.index.union(nv.index)
    wide = pd.DataFrame({"old": ov.reindex(idx), "new": nv.reindex(idx)}).fillna(0)
    r5 = wide.rolling(5, min_periods=1).mean()
    cross = r5[(r5["new"] > r5["old"]) & (r5.index >= dm0 - pd.Timedelta(days=40))]
    xdate = cross.index.min() if len(cross) else None
    safter = (int(o[(o["d"] > rd) & (o["d"] <= xdate)]["d"].nunique())
              if xdate is not None and xdate > rd else 0)
    rolls.append({"old": old, "roll_date": str(rd.date()),
                  "gap_ticks": round(gap / TICK, 1),
                  "gap_pct": gap / float(orow["close"].iloc[0]) * 100,
                  "old_close": float(orow["close"].iloc[0]),
                  "crossover": str(xdate.date()) if xdate is not None else None,
                  "sessions_after": safter,
                  "in_delivery_month": bool(xdate >= dm0) if xdate is not None else None,
                  "old_dm_vol": int(o[o["d"] >= dm0]["volume"].sum()),
                  "old_vol_roll": int(orow["volume"].iloc[0]),
                  "new_vol_roll": int(nrow["volume"].iloc[0])})
OUT["n_rolls"] = len(rolls)
g = np.array([x["gap_ticks"] for x in rolls])
OUT["roll_gap_dist"] = {"mean": float(g.mean()), "median": float(np.median(g)),
                        "n_pos": int((g > 0).sum()), "n_neg": int((g < 0).sum()),
                        "min": float(g.min()), "max": float(g.max())}
sa = [x["sessions_after"] for x in rolls]
OUT["migration"] = {"median_sessions_after": float(np.median(sa)),
                    "min": int(min(sa)), "max": int(max(sa)),
                    "q25": float(np.quantile(sa, .25)), "q75": float(np.quantile(sa, .75)),
                    "all_in_delivery_month": all(x["in_delivery_month"] for x in rolls),
                    "old_dm_vol_median": float(np.median([x["old_dm_vol"] for x in rolls])),
                    "old_over_new_at_roll_median": float(np.median(
                        [x["old_vol_roll"] / max(x["new_vol_roll"], 1) for x in rolls]))}

# ---------------------------------------------------------------- policy differential
boe = pd.read_parquet(f"{NONPRICE}/normalized/boe_bank_rate_tidy.parquet")
boe["date"] = pd.to_datetime(boe["observation_date"])
boe_s = boe.set_index("date")["value"].sort_index()
fred = pd.read_parquet(f"{NONPRICE}/normalized/fred_latest_tidy.parquet")
fr = fred[fred["series_id"] == "FRED_DFEDTARU"].copy()
fr["date"] = pd.to_datetime(fr["observation_period"])
fr_s = fr.set_index("date")["value"].sort_index()
grid = pd.date_range("2019-06-01", "2026-10-05")
b_step = boe_s.reindex(grid, method="ffill")
f_step = fr_s.reindex(grid, method="ffill")
diff = f_step - b_step

for x in rolls:
    dd_ = pd.Timestamp(x["roll_date"])
    x["boe"] = float(b_step.loc[dd_])
    x["fed"] = float(f_step.loc[dd_])
    x["diff"] = float(diff.loc[dd_])

x = np.array([q["diff"] for q in rolls])
gpct = np.array([q["gap_pct"] for q in rolls])
lvl = np.array([q["old_close"] for q in rolls])
OUT["gap_vs_diff"] = {
    "pearson": float(np.corrcoef(x, g)[0, 1]),
    "spearman": float(pd.Series(x).rank().corr(pd.Series(g).rank())),
    "mean_gap_diff_pos": float(g[x > 0].mean()), "n_pos": int((x > 0).sum()),
    "mean_gap_diff_neg": float(g[x < 0].mean()), "n_neg": int((x < 0).sum()),
    "n_zero": int((x == 0).sum()),
    "zero_diff_rolls": [q["roll_date"] for q in rolls if q["diff"] == 0],
}
b, a = np.polyfit(x, gpct, 1)
theory = lvl * (x / 100.0) * (91 / 360) / TICK
OUT["cip"] = {"slope_pct_per_pp": float(b), "theory_pct_per_pp": 100 * 91 / 360 * 0.01,
              "realized_over_theory_slope": float(b / (100 * 91 / 360 * 0.01)),
              "mean_gap_ticks": float(g.mean()), "mean_cip_ticks": float(theory.mean()),
              "corr_realized_vs_cip": float(np.corrcoef(g, theory)[0, 1])}

# ---------------------------------------------------------------- v1 overturn
V1_DATES = ["2025-11-28", "2026-02-27", "2026-05-29", "2026-08-31"]
V1_GAPS_TICKS = {"2025-11-28": -2, "2026-02-27": +5,
                 "2026-05-29": -3, "2026-08-31": +3}  # v1 dossier §1 (IBKR RTH closes)
OUT["v1_window"] = {
    "dates": V1_DATES,
    "v1_gap_ticks": [V1_GAPS_TICKS[d] for d in V1_DATES],
    "v2_gap_ticks": [q["gap_ticks"] for q in rolls if q["roll_date"] in V1_DATES],
    "boe": [float(b_step.loc[pd.Timestamp(d)]) for d in V1_DATES],
    "fed": [float(f_step.loc[pd.Timestamp(d)]) for d in V1_DATES],
    "diff": [float(diff.loc[pd.Timestamp(d)]) for d in V1_DATES],
}
# differential path across v1's whole measurement era (2025-09..2026-09)
era = diff.loc["2025-09-01":"2026-09-30"]
OUT["v1_era_diff"] = {"min": float(era.min()), "max": float(era.max()),
                      "n_days_nonzero": int((era != 0).sum()), "n_days": int(len(era))}

# ---------------------------------------------------------------- OI vs volume crossover
stfiles = sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-statistics-ALL10/*.parquet"))
sts = []
for f_ in stfiles:
    d_ = pd.read_parquet(f_)
    sts.append(d_[d_["raw_symbol"].str.startswith("6B")
                  & ~d_["raw_symbol"].str.contains("-")])
st = pd.concat(sts, ignore_index=True)
st["rd"] = pd.to_datetime(st["ts_ref"], unit="ns", utc=True).dt.date
oi = st[st["stat_type"] == 9]
oi_roll = []
for q in rolls:
    dd_ = pd.Timestamp(q["roll_date"])
    if dd_ < pd.Timestamp("2023-12-01"):
        continue
    # my contract keys are 6B<HMUZ><yyyy>; statistics raw_symbol is 6B<HMUZ><d>
    o_sym = "6B" + q["old"][2] + str(int(q["old"][3:]) % 10)
    n_key = corder[corder.index(q["old"]) + 1]
    n_sym = "6B" + n_key[2] + str(int(n_key[3:]) % 10)
    oo = oi[oi["raw_symbol"] == o_sym].drop_duplicates("rd", keep="last")
    nn = oi[oi["raw_symbol"] == n_sym].drop_duplicates("rd", keep="last")
    if not len(oo) or not len(nn):
        continue
    oi_o = oo.set_index(pd.to_datetime(oo["rd"])).sort_index()["quantity"]
    oi_n = nn.set_index(pd.to_datetime(nn["rd"])).sort_index()["quantity"]
    j = pd.DataFrame({
        "o": oi_o.reindex(pd.date_range(dd_ - pd.Timedelta(days=45),
                                        dd_ + pd.Timedelta(days=30)), method="ffill"),
        "n": oi_n.reindex(pd.date_range(dd_ - pd.Timedelta(days=45),
                                        dd_ + pd.Timedelta(days=30)), method="ffill")
    }).dropna()
    cr = j[j["n"] > j["o"]].index
    oi_roll.append({"roll": q["roll_date"],
                    "oi_cross": str(min(cr).date()) if len(cr) else None,
                    "vol_cross": q["crossover"]})
lags = [(pd.Timestamp(w["oi_cross"]) - pd.Timestamp(w["vol_cross"])).days
        for w in oi_roll if w["oi_cross"] and w["vol_cross"]]
OUT["oi_vs_volume"] = {"n": len(lags), "median_lag_days": float(np.median(lags)),
                       "min": int(min(lags)), "max": int(max(lags)), "table": oi_roll}

# ---------------------------------------------------------------- BoE MPC events
spec = importlib_util = None
import importlib.util
_lp = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/6B_deep_lib.py"
_sp = importlib.util.spec_from_file_location("lane_lib", _lp)
lane = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(lane)
mpc = lane.load_mpc_calendar()
mpc = mpc[mpc["date"] <= pd.Timestamp("2026-09-30")]
mpc_dates = set(mpc["date"].dt.strftime("%Y-%m-%d"))
OUT["n_mpc_days_sched"] = int(len(mpc))
OUT["n_mpc_change"] = int(mpc["changed_rate"].sum())

bars = d2.merge(held, on="session_date")
bars = bars[bars["contract"] == bars["held"]].copy()
bars["sd"] = pd.to_datetime(bars["session_date"]).dt.strftime("%Y-%m-%d")
bars = bars[bars["sd"] != bars["sd"].max()]  # drop truncated final session
lmin = bars["dt"].dt.tz_convert(LON)
bars["lon_min"] = lmin.dt.hour * 60 + lmin.dt.minute
bars["dow"] = pd.to_datetime(bars["session_date"]).dt.dayofweek


def day_window(frame, a, b):
    w = frame[(frame["lon_min"] >= a) & (frame["lon_min"] < b)]
    per = w.groupby("sd").agg(vol=("volume", "sum"))
    return {"n": int(w["sd"].nunique()), "median_vol": float(per["vol"].median())}


bd = bars[bars["sd"].isin(mpc_dates)]
th = bars[(bars["dow"] == 3) & (~bars["sd"].isin(mpc_dates))]
OUT["boe_mpc"] = {
    "n_in_panel": int(bd["sd"].nunique()),
    "first5_mpc": day_window(bd, 720, 725),
    "first5_thursday": day_window(th, 720, 725),
    "m30m30_mpc": day_window(bd, 690, 750),
    "m30m30_thursday": day_window(th, 690, 750),
    "day_vol_mpc": float(bd.groupby("sd")["volume"].sum().median()),
    "day_vol_thursday": float(th.groupby("sd")["volume"].sum().median()),
    "minute_profile_720": float(bd[bd["lon_min"] == 720]["volume"].mean()),
    "minute_profile_721": float(bd[bd["lon_min"] == 721]["volume"].mean()),
    "minute_profile_722": float(bd[bd["lon_min"] == 722]["volume"].mean()),
    "top_minute": int(bd.groupby("lon_min")["volume"].mean().idxmax()),
}

# change vs hold first-5m
chg = set(mpc[mpc["changed_rate"]]["date"].dt.strftime("%Y-%m-%d"))
OUT["boe_mpc"]["first5_change"] = day_window(bd[bd["sd"].isin(chg)], 720, 725)
OUT["boe_mpc"]["first5_hold"] = day_window(bd[~bd["sd"].isin(chg)], 720, 725)

# ---------------------------------------------------------------- FOMC parse
ffiles = sorted(glob.glob(f"{NONPRICE}/fed/statements/monetary*.html"))
rows = []
for f_ in ffiles:
    mm = re.fullmatch(r"monetary(\d{8})a\.html", os.path.basename(f_))
    if not mm:
        continue
    txt = open(f_, encoding="utf-8", errors="replace").read()
    mt = re.search(r"For release at\s*(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(E[SD]T)", txt)
    hh = None
    if mt:
        hh = int(mt.group(1)) % 12 + (12 if mt.group(3) == "p" else 0)
    rows.append({"date": mm.group(1), "hh": hh, "mm": int(mt.group(2)) if mt else None})
fomc = pd.DataFrame(rows)
fomc["date"] = pd.to_datetime(fomc["date"], format="%Y%m%d")
pan = fomc[(fomc["date"] >= "2020-01-01") & (fomc["date"] <= "2026-09-30")]
OUT["fomc"] = {
    "n_statements_in_window": int(len(pan)),
    "n_unique_dates": int(pan["date"].nunique()),
    "n_with_time_proof": int(pan["hh"].notna().sum()),
    "n_at_1400et": int(((pan["hh"] == 14) & (pan["mm"] == 0)).sum()),
    "other_times": sorted({f"{int(a)}:{int(b):02d}" for a, b in
                           zip(pan[pan["hh"] != 14]["hh"].dropna(),
                               pan[pan["hh"] != 14]["mm"].dropna())}),
}
fd = bars[bars["sd"].isin(set(pan["date"].dt.strftime("%Y-%m-%d")))].copy()
cmin = bars["dt"].dt.tz_convert(CHI)
bars["ct_min"] = cmin.dt.hour * 60 + cmin.dt.minute
fd = bars[bars["sd"].isin(set(pan["date"].dt.strftime("%Y-%m-%d")))].copy()
wd = bars[(bars["dow"] == 2) & (~bars["sd"].isin(set(pan["date"].dt.strftime("%Y-%m-%d"))))].copy()


def ct_window(frame, a, b):
    w = frame[(frame["ct_min"] >= a) & (frame["ct_min"] < b)]
    per = w.groupby("sd").agg(vol=("volume", "sum"))
    return {"n": int(w["sd"].nunique()), "median_vol": float(per["vol"].median())}


OUT["fomc"]["first5_fomc"] = ct_window(fd, 780, 785)
OUT["fomc"]["first5_wednesday"] = ct_window(wd, 780, 785)
OUT["fomc"]["m30m30_fomc"] = ct_window(fd, 750, 810)
OUT["fomc"]["m30m30_wednesday"] = ct_window(wd, 750, 810)
OUT["fomc"]["day_vol_fomc"] = float(fd.groupby("sd")["volume"].sum().median())
OUT["fomc"]["day_vol_wednesday"] = float(wd.groupby("sd")["volume"].sum().median())

# ---------------------------------------------------------------- London share drift
era_def = [("2020-2021", 2020, 2021), ("2022", 2022, 2022),
           ("2023-2024", 2023, 2024), ("2025-2026", 2025, 2026)]
lh = lmin.dt.hour
yr = pd.to_datetime(bars["session_date"]).dt.year
sh = {}
for name, y0, y1 in era_def:
    m_ = (yr >= y0) & (yr <= y1)
    tot = bars.loc[m_, "volume"].sum()
    sh[name] = {
        "lon_morning_07_12": float(bars.loc[m_ & lh.between(7, 11), "volume"].sum() / tot),
        "asia_00_07": float(bars.loc[m_ & (lh < 7), "volume"].sum() / tot),
        "h15": float(bars.loc[m_ & (lh == 15), "volume"].sum() / tot),
        "h8": float(bars.loc[m_ & (lh == 8), "volume"].sum() / tot),
        "h12_17": float(bars.loc[m_ & lh.between(12, 16), "volume"].sum() / tot),
        "h17_24": float(bars.loc[m_ & (lh >= 17), "volume"].sum() / tot),
    }
OUT["london_share"] = sh

# ---------------------------------------------------------------- CoT (FIXED tidy)
cot = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet")
c6 = cot[cot["series_id"] == "COT_LEGACY_6B"].copy()
c6["obs"] = pd.to_datetime(c6["observation_period"])
c6 = c6.sort_values("obs").reset_index(drop=True)
c6["nn"] = c6["noncomm_long"] - c6["noncomm_short"]
mu = c6["nn"].div(c6["open_interest_all"]).rolling(156, min_periods=156).mean().shift(1)
sd_ = c6["nn"].div(c6["open_interest_all"]).rolling(156, min_periods=156).std().shift(1)
c6["z"] = (c6["nn"] / c6["open_interest_all"] - mu) / sd_
cc = c.dropna(subset=["ret"]).reset_index(drop=True)
h = 20
cc["fwd_vol20"] = cc["ret"].rolling(h).std().shift(-h) * np.sqrt(252) * 100
pxv = cc["close"].values
fdd = np.full(len(pxv), np.nan)
for i in range(len(pxv) - h):
    w = pxv[i:i + h + 1]
    fdd[i] = (w / np.maximum.accumulate(w) - 1).min()
cc["fdd20"] = fdd
mm = (c6.dropna(subset=["z"])[["obs", "z", "nn"]]
      .merge(cc[["d", "fwd_vol20", "fdd20"]], left_on="obs", right_on="d")
      .dropna(subset=["fwd_vol20"]))
OUT["cot"] = {
    "n_rows": int(len(c6)), "span": [str(c6["obs"].min().date()), str(c6["obs"].max().date())],
    "n_joint": int(len(mm)),
    "corr_absz_fwdvol": float(mm["z"].abs().corr(mm["fwd_vol20"])),
    "corr_z_fwdvol": float(mm["z"].corr(mm["fwd_vol20"])),
    "bucket_med_vol": {k: float(v["fwd_vol20"].median()) for k, v in
                       mm.groupby(pd.cut(mm["z"], [-np.inf, -1.5, -0.5, 0.5, 1.5, np.inf]),
                                  observed=True)},
    "bucket_med_dd": {str(k): float(v["fdd20"].median() * 100) for k, v in
                      mm.groupby(pd.cut(mm["z"], [-np.inf, -1.5, -0.5, 0.5, 1.5, np.inf]),
                                 observed=True)},
    "nn_min": float(c6["nn"].min()), "nn_min_date": str(c6.loc[c6["nn"].idxmin(), "obs"].date()),
    "nn_max": float(c6["nn"].max()), "nn_max_date": str(c6.loc[c6["nn"].idxmax(), "obs"].date()),
    "aug2022": [{"obs": str(t.obs.date()), "z": round(float(t.z), 2), "nn": int(t.nn)}
                for t in c6[(c6["obs"] >= "2022-08-01")
                            & (c6["obs"] <= "2022-08-31")].itertuples()],
}

# ---------------------------------------------------------------- gilts (own parser)
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def col_to_idx(ref):
    s = re.match(r"([A-Z]+)", ref).group(1)
    n = 0
    for ch in s:
        n = n * 26 + ord(ch) - 64
    return n - 1


def parse_gilt(path):
    outer = zipfile.ZipFile(path)
    name = [n for n in outer.namelist() if "2016 to 2024" in n][0]
    inner = zipfile.ZipFile(io.BytesIO(outer.read(name)))
    wb = ElementTree.fromstring(inner.read("xl/workbook.xml"))
    # find sheet index for '4. spot curve'
    sheet_file = None
    for i, sh in enumerate(wb.findall(".//m:sheet", NS)):
        if sh.get("name") == "4. spot curve":
            sheet_file = f"xl/worksheets/sheet{i + 1}.xml"
    if sheet_file is None or sheet_file not in inner.namelist():
        # fall back: scan all sheets for the years: header
        cands = [n for n in inner.namelist() if n.startswith("xl/worksheets/sheet")]
        for n in cands:
            head = inner.read(n)[:4000].decode("utf-8", "ignore")
            if "Years:" in head or "years:" in head:
                sheet_file = n
                break
    sst = []
    if "xl/sharedStrings.xml" in inner.namelist():
        ss = ElementTree.fromstring(inner.read("xl/sharedStrings.xml"))
        for si in ss.findall("m:si", NS):
            sst.append("".join(t.text or "" for t in si.findall(".//m:t", NS)))
    ws = ElementTree.fromstring(inner.read(sheet_file))
    rows_out, tenors = [], None
    for row in ws.findall(".//m:row", NS):
        vals = {}
        for cel in row.findall("m:c", NS):
            ref = cel.get("r", "")
            idx = col_to_idx(ref) if ref else len(vals)
            v = cel.find("m:v", NS)
            if v is None:
                continue
            vals[idx] = sst[int(v.text)] if cel.get("t") == "s" else v.text
        first = vals.get(0)
        if first is None:
            continue
        s0 = str(first).strip().lower()
        if s0.startswith("years:"):
            tenors = []
            for k in sorted(k for k in vals if k > 0):
                try:
                    tenors.append(float(vals[k]))
                except (TypeError, ValueError):
                    tenors.append(None)
            continue
        if tenors is None:
            continue
        try:
            serial = float(first)
        except (TypeError, ValueError):
            continue
        date = (dt.datetime(1899, 12, 30) + dt.timedelta(days=serial)).date()
        for j, t in enumerate(tenors, start=1):
            if t is None or j not in vals or vals[j] is None:
                continue
            try:
                rows_out.append({"date": date, "tenor": t, "yield": float(vals[j])})
            except ValueError:
                pass
    return pd.DataFrame(rows_out)


gcurve = parse_gilt(f"{NONPRICE}/boe/glcnominalddata.zip")
g10 = gcurve[gcurve["tenor"] == 10.0].set_index(pd.to_datetime(gcurve[gcurve["tenor"] == 10.0]["date"]))["yield"].sort_index()
g2 = gcurve[gcurve["tenor"] == 2.0].set_index(pd.to_datetime(gcurve[gcurve["tenor"] == 2.0]["date"]))["yield"].sort_index()
OUT["gilt_coverage"] = {"span": [str(gcurve["date"].min()), str(gcurve["date"].max())],
                        "n_days": int(gcurve["date"].nunique())}
mg = cc[["d", "close", "ret"]].merge(
    pd.DataFrame({"g2": g2, "g10": g10}), left_on="d", right_index=True, how="inner")
mg["dg10"] = mg["g10"].diff()
mg["dg2"] = mg["g2"].diff()
mg = mg.dropna(subset=["dg10"])
OUT["gilts"] = {
    "full_corr_ret_dg10": float(mg["ret"].corr(mg["dg10"])),
    "era_corr": {str(y): float(s["ret"].corr(s["dg10"]))
                 for y, s in mg.groupby(mg["d"].dt.year) if y >= 2020},
    "rc63_min": float(mg["ret"].rolling(63).corr(mg["dg10"]).min()),
    "rc63_min_date": str(mg.loc[mg["ret"].rolling(63).corr(mg["dg10"]).idxmin(), "d"].date()),
    "rc63_max": float(mg["ret"].rolling(63).corr(mg["dg10"]).max()),
    "rc63_max_date": str(mg.loc[mg["ret"].rolling(63).corr(mg["dg10"]).idxmax(), "d"].date()),
    "episode": [{"date": str(t.d.date()), "ret_pct": round(t.ret * 100, 2),
                 "dg2_bp": round(t.dg2 * 100, 1), "dg10_bp": round(t.dg10 * 100, 1),
                 "g2_lvl": round(t.g2, 3)}
                for t in mg[(mg["d"] >= "2022-09-22") & (mg["d"] <= "2022-09-28")].itertuples()],
    "ep_corr_23_28": float(mg[(mg["d"] >= "2022-09-23") & (mg["d"] <= "2022-09-28")]["ret"]
                           .corr(mg[(mg["d"] >= "2022-09-23") & (mg["d"] <= "2022-09-28")]["dg10"])),
}
y22 = mg[mg["d"].dt.year == 2022]
sdg = y22["dg10"].std()
stress = y22[y22["dg10"].abs() > 2 * sdg]
calm = y22[y22["dg10"].abs() < 0.5 * sdg]
OUT["gilts"]["stress_2022"] = {
    "n_stress": int(len(stress)),
    "median_absret_stress_pct": float(stress["ret"].abs().median() * 100),
    "median_absret_calm_pct": float(calm["ret"].abs().median() * 100),
    "dates": [str(x.date()) for x in stress["d"]]}

# ---------------------------------------------------------------- save
def _san(o):
    if isinstance(o, dict):
        return {str(k): _san(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_san(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp, dt.date, dt.datetime)):
        return str(o)
    return o


with open(os.path.join(HERE, "recompute_6b_headlines.json"), "w") as fh:
    json.dump(_san(OUT), fh, indent=1, allow_nan=False)
print("WROTE recompute_6b_headlines.json")
print("n_rolls:", OUT["n_rolls"], "| gap mean/med:", OUT["roll_gap_dist"]["mean"],
      OUT["roll_gap_dist"]["median"])
print("corr gap vs diff:", OUT["gap_vs_diff"]["pearson"],
      "spearman:", OUT["gap_vs_diff"]["spearman"])
print("v1 window:", json.dumps(OUT["v1_window"], indent=1))
