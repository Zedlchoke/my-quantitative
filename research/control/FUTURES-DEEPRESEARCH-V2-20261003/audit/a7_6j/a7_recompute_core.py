"""A7-DEEP-6J independent audit — FRESH recompute from vendor parquet (read-only).

Lane A7-DEEP-6J, task FUTURES-DEEPRESEARCH-V2-20261003. READ-ONLY on data;
writes only under audit/a7_6j/. This script deliberately does NOT import the
lane's 6J_deep_lib or 6J_cache: everything is rebuilt from the vendor parquet
with independently written logic, then compared to the dossier's claims.

Stages:
  A. vendor panel census (rows, regex filter, 6AV3, tick grid, duplicates)
  B. session map + held-contract chain (k=5 volume crossover, BOTH the coded
     variant held[t]~data-through-t and the disclosed variant held[t+1])
  C. A1 recompute: rolled drawdown, 3% zigzag legs, leg-end vs MOF-op adjacency
  D. A2 recompute: tokyo_am volume/range share, session-high minute shares,
     BoJ decision-window medians, CT hour shares
"""
from __future__ import annotations

import glob
import json
import os
import re

import numpy as np
import pandas as pd

DATA_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "a7_cache")
PX_SCALE = 1e-9
TICK_INT = 500  # int-nano units per 5e-7 tick
MONTH_CODE = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
              "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
OUTRIGHT_RE = re.compile(r"^6J[FGHJKMNQUVXZ]\d$")

MOF_OPS = ["2022-09-22", "2022-10-21", "2022-10-24", "2024-04-29", "2024-05-01",
           "2024-07-11", "2024-07-12", "2026-04-30", "2026-05-04", "2026-05-06"]
PENDING = "2026-07-30"


def load_panel() -> pd.DataFrame:
    os.makedirs(CACHE, exist_ok=True)
    c = os.path.join(CACHE, "panel.parquet")
    if os.path.exists(c):
        return pd.read_parquet(c)
    files = (sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1B-O1M-6J-BACKFILL2/*.parquet"))
             + sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1R-O1M-6J-BACKFILL/*.parquet"))
             + sorted(glob.glob(f"{DATA_ROOT}/parquet/AV1T-O1M-6J/*.parquet")))
    dfs, census = [], []
    for f in files:
        d = pd.read_parquet(f)
        keep = d["raw_symbol"].str.fullmatch(OUTRIGHT_RE)
        nonj = d.loc[~keep & ~d["raw_symbol"].str.contains("-"), "raw_symbol"]
        census.append({
            "file": os.path.basename(f), "rows_total": int(len(d)),
            "rows_outright": int(keep.sum()),
            "spread_rows": int(d["raw_symbol"].str.contains("-").sum()),
            "foreign_rows": int(len(nonj)),
            "foreign_syms": sorted(nonj.astype(str).unique().tolist())})
        dfs.append(d[keep])
    df = pd.concat(dfs, ignore_index=True).sort_values("ts_event").reset_index(drop=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    df.to_parquet(c, index=False)
    with open(os.path.join(CACHE, "census.json"), "w") as fh:
        json.dump(census, fh, indent=1)
    return df


def third_wed(y, m):
    d = pd.Timestamp(y, m, 1)
    off = (2 - d.dayofweek) % 7
    return d + pd.Timedelta(days=off + 14)


def build_registry(df: pd.DataFrame) -> pd.DataFrame:
    """Independent contract registry: split each symbol into >60d clusters,
    resolve one-digit year to the candidate 3rd-Wednesday expiry in 2010..2028."""
    rows = []
    for sym, sub in df.groupby("raw_symbol", sort=False):
        code, digit = sym[2], int(sym[3])
        sub = sub.sort_values("dt")
        brk = sub["dt"].diff() > pd.Timedelta(days=60)
        for cid, g in sub.groupby(brk.cumsum()):
            t0, t1 = g["dt"].min(), g["dt"].max()
            cands = [third_wed(y, MONTH_CODE[code]) for y in range(2010, 2029)
                     if y % 10 == digit]
            ok = [x for x in cands
                  if x - pd.Timedelta(days=820) <= t0.tz_localize(None)
                  and t1.tz_localize(None) <= x + pd.Timedelta(days=10)]
            rows.append({"symbol": sym, "cluster": int(cid),
                         "expiry": ok[0] if len(ok) == 1 else None,
                         "n_bars": len(g), "stray": len(ok) != 1})
    reg = pd.DataFrame(rows)
    reg["year"] = reg["expiry"].dt.year
    reg["contract"] = reg["symbol"] + "_" + reg["year"].astype("Int64").astype(str)
    return reg


def annotate(df, reg):
    chi = df["dt"].dt.tz_convert("America/Chicago")
    hhmm = chi.dt.hour * 60 + chi.dt.minute
    naive = chi.dt.tz_localize(None)
    sdate = naive.dt.normalize() + pd.to_timedelta((naive.dt.hour >= 17).astype(int), "D")
    df["session_date"] = sdate.dt.date
    df["minute_ct"] = hhmm
    df["in_break"] = (hhmm >= 960) & (hhmm < 1020)
    df["weekend_anom"] = ((chi.dt.dayofweek == 4) & (hhmm >= 1020)) | (chi.dt.dayofweek == 5)
    for nm, tz in (("tokyo", "Asia/Tokyo"), ("london", "Europe/London"),
                   ("ny", "America/New_York")):
        cc = df["dt"].dt.tz_convert(tz)
        df[f"minute_{nm}"] = cc.dt.hour * 60 + cc.dt.minute
    # contract key
    df = df.sort_values(["raw_symbol", "dt"]).reset_index(drop=True)
    brk = df.groupby("raw_symbol")["dt"].diff() > pd.Timedelta(days=60)
    df["_cl"] = brk.groupby(df["raw_symbol"]).cumsum().fillna(0).astype(int)
    key = df["raw_symbol"] + "|" + df["_cl"].astype(str)
    rk = reg["symbol"] + "|" + reg["cluster"].astype(str)
    lut = pd.Series(reg["contract"].values, index=rk.values)
    elut = pd.Series(reg["expiry"].values, index=rk.values)
    df["contract"] = key.map(lut)
    df["expiry"] = key.map(elut)
    return df.drop(columns=["_cl"])


def sessions_of(df):
    d = df[~df["in_break"]].copy()
    for c in ("open", "high", "low", "close"):
        d[c + "_px"] = d[c].astype(float) * PX_SCALE
    d["range_px"] = d["high_px"] - d["low_px"]
    g = d.groupby(["contract", "session_date"], sort=True)
    sess = g.agg(close=("close_px", "last"), high=("high_px", "max"),
                 low=("low_px", "min"), volume=("volume", "sum"),
                 n_bars=("dt", "size")).reset_index()
    sess["coverage"] = sess["n_bars"] / 1380.0
    return d, sess


def held_map(sess: pd.DataFrame, k: int = 5, lag: int = 0):
    """HMUZ volume-crossover chain. lag=0 replicates the lane's CODE
    (held[t] decided with data through t); lag=1 replicates the DISCLOSED rule
    (decide at t close, hold from t+1)."""
    q = sess[sess["contract"].str.match(r"^6J[HMUZ]\d_\d{4}$")].copy()
    wide = q.pivot_table(index="session_date", columns="contract",
                         values="volume", aggfunc="sum").sort_index()
    roll = wide.rolling(k, min_periods=1).mean()
    state, out = None, []
    for d in roll.index:
        row = roll.loc[d].dropna()
        row = row[row > 0]
        if state is None:
            state = row.idxmax()
        else:
            m = MONTH_CODE[state[2]]
            y = int(state.split("_")[1])
            nm, ny = (m + 3, y) if m < 12 else (3, y + 1)
            nxt = f"6J{ {v:k_ for k_,v in MONTH_CODE.items()}[nm] }{ny % 10}_{ny}"
            if nxt in row.index:
                cur = row.get(state, np.nan)
                if pd.isna(cur) or row[nxt] > cur:
                    state = nxt
        out.append((d, state))
    o = pd.DataFrame(out, columns=["session_date", "held"])
    if lag:
        o["held"] = o["held"].shift(lag).fillna(o["held"].iloc[0])
    return o


def zigzag(cum: pd.Series, swing=0.03):
    v = cum.fillna(0).values
    piv, ext_i, direction = [], 0, 0
    for i in range(1, len(v)):
        if direction >= 0:
            if v[i] > v[ext_i]:
                ext_i = i
            elif v[ext_i] - v[i] >= swing:
                piv.append((ext_i, "peak"))
                direction, ext_i = -1, i
        if direction <= 0:
            if v[i] < v[ext_i]:
                ext_i = i
            elif v[i] - v[ext_i] >= swing:
                piv.append((ext_i, "trough"))
                direction, ext_i = 1, i
    piv.append((ext_i, "trough" if direction == -1 else "peak"))
    return piv


def main():
    res = {}
    df = load_panel()
    cen = json.load(open(os.path.join(CACHE, "census.json")))
    res["census"] = cen

    # ---------- A: global panel checks ----------
    g = {
        "outright_rows": int(len(df)),
        "tick_grid_violations": int(sum((df[c] % TICK_INT != 0).sum()
                                        for c in ("open", "high", "low", "close"))),
        "dup_instrument_ts": int(df.duplicated(subset=["instrument_id", "ts_event"]).sum()),
        "close_min": float(df["close"].min() * PX_SCALE),
        "close_max": float(df["close"].max() * PX_SCALE),
        "bar_low_min": float(df["low"].min() * PX_SCALE),
        "bar_high_max": float(df["high"].max() * PX_SCALE),
    }
    lo_row = df.loc[df["low"].idxmin()]
    hi_row = df.loc[df["high"].idxmax()]
    g["bar_low_min_ts"] = str(lo_row["dt"])
    g["bar_low_min_sym"] = lo_row["raw_symbol"]
    g["bar_high_max_ts"] = str(hi_row["dt"])
    g["bar_high_max_sym"] = hi_row["raw_symbol"]
    g["grid_step_observed"] = float(np.gcd.reduce(df["close"].values.astype(np.int64)))
    res["A_global"] = g

    reg = build_registry(df)
    res["A_registry"] = {
        "contracts": int(len(reg)), "stray": int(reg["stray"].sum()),
        "quarterly": int((~reg["stray"] & reg["symbol"].str[2].isin(list("HMUZ"))).sum()),
        "serial": int((~reg["stray"] & ~reg["symbol"].str[2].isin(list("HMUZ"))).sum())}

    ann = annotate(df, reg)
    res["A_break_weekend"] = {"break_bars": int(ann["in_break"].sum()),
                              "weekend_bars": int(ann["weekend_anom"].sum())}

    # 2022-09-20 probe (QA claims 16 missing weekdays are holidays only)
    for day in ("2022-09-16", "2022-09-19", "2022-09-20", "2022-09-21"):
        sub = ann[ann["session_date"].astype(str) == day]
        res.setdefault("A_day_probes", {})[day] = {
            "bars": int(len(sub)), "contracts": sub["contract"].nunique(),
            "symbols": sorted(sub["raw_symbol"].unique().tolist())}

    d1m, sess = sessions_of(ann)
    d1m.to_parquet(os.path.join(CACHE, "annotated.parquet"), index=False)
    sess.to_parquet(os.path.join(CACHE, "sessions.parquet"), index=False)

    # ---------- B: held chains ----------
    hv0 = held_map(sess, 5, lag=0)   # as coded
    hv1 = held_map(sess, 5, lag=1)   # as disclosed
    for nm, hv in (("coded", hv0), ("disclosed_lag1", hv1)):
        m = sess.merge(hv.rename(columns={"held": "contract"}),
                       on=["session_date", "contract"])
        m = m.sort_values("session_date").reset_index(drop=True)
        res[f"B_held_{nm}"] = {
            "sessions": int(len(m)),
            "first": str(m["session_date"].iloc[0]),
            "last": str(m["session_date"].iloc[-1]),
            "rolls": int((m["contract"] != m["contract"].shift()).sum() - 1),
            "median_bars": float(m["n_bars"].median()),
            "p5_bars": float(m["n_bars"].quantile(.05)),
            "n_depleted_lt345": int((m["n_bars"] < 345).sum()),
            "depleted_dates": [str(x) for x in
                               m.loc[m["n_bars"] < 345, "session_date"]],
            "switch_dates": [str(x) for x in m.loc[
                (m["contract"] != m["contract"].shift()) & m["contract"].notna(),
                "session_date"]][1:]}
        m.to_parquet(os.path.join(CACHE, f"held_daily_{nm}.parquet"), index=False)
    # missing weekdays
    hh = sess.merge(hv0.rename(columns={"held": "contract"}),
                    on=["session_date", "contract"])
    sd = pd.to_datetime(hh["session_date"])
    cal = pd.date_range(sd.min(), sd.max(), freq="B")
    res["B_missing_weekdays"] = [str(x.date()) for x in cal
                                 if x not in set(sd)]

    # ---------- C: A1 recompute on the CODED chain ----------
    m = pd.read_parquet(os.path.join(CACHE, "held_daily_coded.parquet"))
    m["d"] = pd.to_datetime(m["session_date"])
    m["log_close"] = np.log(m["close"].astype(float))
    m["ret_rolled"] = m["log_close"].diff()
    prev = m.groupby("contract")["log_close"].shift(1)
    m["ret_within"] = m["log_close"] - prev
    m["cum"] = m["ret_rolled"].cumsum()
    m["dd"] = m["cum"] - m["cum"].cummax()
    r = m["ret_within"].dropna()
    res["C_a1"] = {
        "max_dd_rolled_pct": float(-100 * m["dd"].min()),
        "peak_date": str(m.loc[m["cum"].idxmax(), "d"].date()),
        "trough_date": str(m.loc[m["dd"].idxmin(), "d"].date()),
        "cum_within_pct": float(100 * r.sum()),
        "cum_rolled_pct": float(100 * m["ret_rolled"].sum()),
        "up_days_pct": float(100 * (r > 0).mean()),
        "median_ret_bp": float(1e4 * r.median()),
        "price_first": float(m["close"].iloc[0]),
        "price_last": float(m["close"].iloc[-1]),
        "close_min": float(m["close"].min()),
        "close_min_date": str(m.loc[m["close"].idxmin(), "d"].date()),
        "close_max": float(m["close"].max()),
        "close_max_date": str(m.loc[m["close"].idxmax(), "d"].date()),
        "vol_within_ann_pct": float(100 * r.std() * np.sqrt(252))}
    # same on the disclosed (lag1) chain for sensitivity
    m1 = pd.read_parquet(os.path.join(CACHE, "held_daily_disclosed_lag1.parquet"))
    m1["d"] = pd.to_datetime(m1["session_date"])
    m1["log_close"] = np.log(m1["close"].astype(float))
    m1["ret_rolled"] = m1["log_close"].diff()
    m1["cum"] = m1["ret_rolled"].cumsum()
    m1["dd"] = m1["cum"] - m1["cum"].cummax()
    r1 = m1.groupby("contract")["log_close"].diff().dropna()
    res["C_a1_lag1_sensitivity"] = {
        "max_dd_rolled_pct": float(-100 * m1["dd"].min()),
        "peak_date": str(m1.loc[m1["cum"].idxmax(), "d"].date()),
        "trough_date": str(m1.loc[m1["dd"].idxmin(), "d"].date()),
        "cum_within_pct": float(100 * r1.sum()),
        "cum_rolled_pct": float(100 * m1["ret_rolled"].sum())}

    # zigzag legs (coded chain)
    piv = zigzag(m["cum"])
    dates = m["d"].reset_index(drop=True)
    legs = []
    for (i0, k0), (i1, k1) in zip(piv[:-1], piv[1:]):
        legs.append({"kind": "down" if k0 == "peak" else "up",
                     "from": str(dates.iloc[i0].date()),
                     "to": str(dates.iloc[i1].date()),
                     "move_pct": float(100 * (m["cum"].iloc[i1] - m["cum"].iloc[i0])),
                     "sessions": int(i1 - i0)})
    res["C_zigzag_down_3pct"] = sorted([x for x in legs if x["kind"] == "down"],
                                        key=lambda x: x["move_pct"])
    res["C_zigzag_up_3pct"] = sorted([x for x in legs if x["kind"] == "up"],
                                      key=lambda x: -x["move_pct"])[:8]
    # leg-end adjacency to MOF ops / pending window
    sdates = list(m["session_date"].astype(str))
    adj = []
    for leg in [x for x in legs if x["kind"] == "down"]:
        end_i = sdates.index(leg["to"])
        near = []
        for op in MOF_OPS + [PENDING]:
            if op in sdates:
                oi_ = sdates.index(op)
                delta = oi_ - end_i
                if 0 <= delta <= 2:
                    near.append({op: f"+{delta} sessions"})
        adj.append({"to": leg["to"], "move_pct": leg["move_pct"], "near_op": near})
    res["C_downleg_op_adjacency"] = adj

    # ---------- D: A2 recompute ----------
    held0 = hv0
    hmap = dict(zip(held0["session_date"], held0["held"]))
    h = d1m[d1m["session_date"].map(hmap).notna()]
    h = h[h["contract"] == h["session_date"].map(hmap)]
    tot_v = h["volume"].sum()
    res["D_a2"] = {"bars": int(len(h)), "sessions": int(h["session_date"].nunique())}
    # center windows (fresh definitions)
    wins = {
        "tokyo_am": (h["minute_tokyo"] >= 540) & (h["minute_tokyo"] < 690),
        "tokyo_lunch": (h["minute_tokyo"] >= 690) & (h["minute_tokyo"] < 750),
        "tokyo_pm": (h["minute_tokyo"] >= 750) & (h["minute_tokyo"] < 900),
        "tokyo_fix": (h["minute_tokyo"] >= 900) & (h["minute_tokyo"] < 945),
        "london_am": (h["minute_london"] >= 480) & (h["minute_london"] < 720),
        "london_pm": (h["minute_london"] >= 720) & (h["minute_london"] < 990),
        "ny_am": (h["minute_ny"] >= 500) & (h["minute_ny"] < 720),
        "ny_pm": (h["minute_ny"] >= 720) & (h["minute_ny"] < 960),
        "ny_post": (h["minute_ny"] >= 960) & (h["minute_ny"] < 1020),
    }
    cw = {}
    for nm, msk in wins.items():
        w = h[msk]
        cw[nm] = {"vol_share_pct": float(100 * w["volume"].sum() / tot_v),
                  "range_share_pct": float(100 * w["range_px"].sum() / h["range_px"].sum()),
                  "median_1m_vol": float(w["volume"].median())}
    res["D_a2"]["center_windows"] = cw
    res["D_a2"]["full_day_median_1m_vol"] = float(h["volume"].median())
    # session extrema minutes
    d2 = h.sort_values(["session_date", "dt"])
    hi_idx = d2.groupby("session_date")["high"].idxmax()
    lo_idx = d2.groupby("session_date")["low"].idxmin()
    hi_rows, lo_rows = d2.loc[hi_idx], d2.loc[lo_idx]
    res["D_a2"]["high_minute_share_pct"] = {
        nm: float(100 * msk[hi_rows.index].mean()) for nm, msk in wins.items()}
    res["D_a2"]["low_minute_share_pct"] = {
        nm: float(100 * msk[lo_rows.index].mean()) for nm, msk in wins.items()}
    # BoJ decision window
    bw = h[(h["minute_tokyo"] >= 720) & (h["minute_tokyo"] <= 930)]
    res["D_a2"]["boj_window"] = {
        "vol_share_pct": float(100 * bw["volume"].sum() / tot_v),
        "median_1m_vol": float(bw["volume"].median())}
    # CT hour shares
    hv_ = h.groupby(h["minute_ct"] // 60)["volume"].sum()
    res["D_a2"]["ct_hour_vol_share"] = {f"{int(k):02d}": float(v)
                                        for k, v in (hv_ / tot_v).items()}
    # evening/overnight/day buckets
    mm = h["minute_ct"]
    res["D_a2"]["buckets"] = {
        "evening_17_24_pct": float(100 * h.loc[(mm >= 1020), "volume"].sum() / tot_v),
        "overnight_00_07_pct": float(100 * h.loc[mm < 420, "volume"].sum() / tot_v),
        "usday_07_16_pct": float(100 * h.loc[(mm >= 420) & (mm < 960), "volume"].sum() / tot_v)}
    # gaps
    sg = h.groupby("session_date").agg(open=("open_px", "first"), close=("close_px", "last"))
    gap = sg["open"] / sg["close"].shift(1) - 1
    mon = pd.to_datetime(sg.index).dayofweek == 0
    res["D_a2"]["gaps_bp"] = {
        "overnight_median": float(1e4 * gap.median()),
        "overnight_p95_abs": float(1e4 * gap.abs().quantile(.95)),
        "weekend_p95_abs": float(1e4 * gap[mon].abs().quantile(.95))}

    with open(os.path.join(HERE, "a7_core_results.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(json.dumps(res, indent=1, default=str)[:8000])
    print("CORE COMPLETE")


if __name__ == "__main__":
    main()
