"""DT100 family signal builders.

Contract: build_X(df, p) -> pd.Series `pos` aligned to df.index, values in
{-1,0,+1} = position DESIRED as of that bar's CLOSE. The engine fills at the
NEXT bar's open. All windows are backward-looking; any forward reference is a
falsification fixture failure (test_dt100.py mutates for this).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _z(s: pd.Series, win: int) -> pd.Series:
    m = s.rolling(win, min_periods=max(20, win // 4)).mean()
    sd = s.rolling(win, min_periods=max(20, win // 4)).std()
    return (s - m) / sd.replace(0.0, np.nan)


def _day_key(ts: pd.Series) -> pd.Series:
    return ts.dt.floor("D")


def _pct_rank(s: pd.Series, win: int) -> pd.Series:
    return s.rolling(win, min_periods=max(20, win // 2)).rank(pct=True)


# ------------------------------------------------------------------ crypto 1m

def orb(df: pd.DataFrame, p: dict) -> pd.Series:
    """Opening range breakout: first N minutes of UTC day define range; break
    -> hold direction; flat at end-of-day."""
    minutes = p["window_min"]
    ts = df["ts"]
    day = _day_key(ts)
    rng = df.set_index(ts).groupby(day)["h"].transform(lambda s: s.rolling(minutes, min_periods=minutes).max())
    # per-day rolling max/min of highs/lows within first `minutes` bars
    hi, lo = {}, {}
    pos = np.zeros(len(df), dtype=float)
    o, h, l = df["o"].to_numpy(), df["h"].to_numpy(), df["l"].to_numpy()
    cur_day, cur_hi, cur_lo, armed = None, -np.inf, np.inf, False
    mins_into_day = 0
    day_arr = day.to_numpy()
    close_i = df["c"].to_numpy()
    for i in range(len(df)):
        d = day_arr[i]
        if d != cur_day:
            cur_day, cur_hi, cur_lo, armed, mins_into_day = d, -np.inf, np.inf, False, 0
        mins_into_day += 1
        if mins_into_day <= minutes:
            cur_hi = max(cur_hi, h[i]); cur_lo = min(cur_lo, l[i])
            continue
        if not armed:
            if close_i[i] > cur_hi:
                armed = "long"; pos[i] = 1.0
            elif close_i[i] < cur_lo:
                armed = "short"; pos[i] = -1.0
        elif armed == "long":
            pos[i] = 1.0
        elif armed == "short":
            pos[i] = -1.0
    return pd.Series(pos, index=df.index)


def squeeze(df: pd.DataFrame, p: dict) -> pd.Series:
    m, sd = df["c"].rolling(20).mean(), df["c"].rolling(20).std()
    width = (4 * sd) / m
    narrow = _pct_rank(width, p["lookback"]) < p["pct"]
    brk_up = (df["c"] > df["h"].rolling(p["range_win"]).max().shift(1)) & narrow.shift(1)
    brk_dn = (df["c"] < df["l"].rolling(p["range_win"]).min().shift(1)) & narrow.shift(1)
    pos = pd.Series(0.0, index=df.index)
    pos[brk_up] = 1.0
    pos[brk_dn] = -1.0
    return _hold_until(pos, df, p.get("hold", 240))


def _hold_until(pos: pd.Series, df: pd.DataFrame, hold_bars: int) -> pd.Series:
    out = pos.copy()
    idx = np.flatnonzero(pos.to_numpy() != 0)
    for i in idx:
        out.iloc[i + 1:i + 1 + hold_bars] = pos.iloc[i]
    return out


def rsi2(df: pd.DataFrame, p: dict) -> pd.Series:
    delta = df["c"].diff()
    up = delta.clip(lower=0).rolling(2).mean()
    dn = (-delta.clip(upper=0)).rolling(2).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    trend = df["c"] > df["c"].rolling(p["ema"]).mean()
    long = (rsi < p["lo"]) & trend
    short = (rsi > p["hi"]) & (~trend)
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0
    pos[short] = -1.0
    return _hold_until(pos, df, p["hold"])


def hourclock_fade(df: pd.DataFrame, p: dict) -> pd.Series:
    """OVERNIGHTFADE / JPYFADE style: in `hours`, fade the previous hour's
    return when its z-score exceeds band."""
    ts = df["ts"]
    ret1h = df["c"].pct_change(60)
    z = _z(ret1h, p["zwin"])
    hh = ts.dt.hour
    inwin = hh.isin(p["hours"])
    long = inwin & (z.shift(60) < -p["band"])
    short = inwin & (z.shift(60) > p["band"])
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0
    pos[short] = -1.0
    return _hold_until(pos, df, p["hold"])


def weekend(df: pd.DataFrame, p: dict) -> pd.Series:
    """Fade Saturday's accumulated move, entered Sunday 00:00 UTC, flat Monday."""
    ts = df["ts"]
    day = ts.dt.dayofweek  # 5=Sat, 6=Sun
    ret1d = df["c"].pct_change(1440)
    z = _z(ret1d, 30 * 1440)
    sun_open = (day == 6) & (ts.dt.hour == 0)
    long = sun_open & (z.shift(1) < -p["band"])
    short = sun_open & (z.shift(1) > p["band"])
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0
    pos[short] = -1.0
    return _hold_until(pos, df, 24 * 60)


def pdhl_sweep(df: pd.DataFrame, p: dict) -> pd.Series:
    """Sweep of PRIOR-day high/low that fails to hold (reclaim) -> fade.

    Prior-day levels are the previous UTC day's completed high/low — no same-day
    information can enter (daily series shifted one day, then mapped to bars).
    """
    ts = df["ts"]
    day = _day_key(ts)
    d_hi = df.set_index(ts)["h"].resample("1D").max()
    d_lo = df.set_index(ts)["l"].resample("1D").min()
    pdh = (d_hi.shift(1)).reindex(day.to_numpy()).to_numpy()   # yesterday's high per bar
    pdl = (d_lo.shift(1)).reindex(day.to_numpy()).to_numpy()   # yesterday's low per bar
    c = df["c"].to_numpy()
    pos = np.zeros(len(df))
    fired = 0
    for i in range(1, len(df)):
        if np.isnan(pdh[i]):
            continue
        if fired and day.iloc[i - 1] == day.iloc[i]:
            pos[i] = pos[i - 1]
            continue
        fired = 0
        # sweep above PDH then close back below it -> short the failed break
        if c[i - 1] <= pdh[i] and c[i] > pdh[i] and c[i] < pdh[i] * (1 + p["reclaim_frac"]):
            pos[i] = -1.0; fired = 1
        elif c[i - 1] >= pdl[i] and c[i] < pdl[i] and c[i] > pdl[i] * (1 - p["reclaim_frac"]):
            pos[i] = 1.0; fired = 1
    return pd.Series(pos, index=df.index)


def delta_div(df: pd.DataFrame, p: dict) -> pd.Series:
    delta = (2 * df["tb"] - df["v"]).rolling(p["dwin"]).sum()
    dz = _z(delta, p["dwin"])
    pz = _z(df["c"], p["dwin"])
    short = (dz < -p["dz"]) & (pz > p["pz"])
    long = (dz > p["dz"]) & (pz < -p["pz"])
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0
    pos[short] = -1.0
    return _hold_until(pos, df, p["hold"])


def fh_mom(df: pd.DataFrame, p: dict) -> pd.Series:
    ts = df["ts"]
    day = _day_key(ts)
    atr_d = (df["h"] - df["l"]).rolling(1440).mean()
    c0 = df["c"].groupby(day).transform("first")
    r = (df["c"] - c0) / atr_d
    hh = ts.dt.hour
    after = hh >= 1
    long = after & (r.shift(1) > p["k"]) & (hh <= 22)
    short = after & (r.shift(1) < -p["k"]) & (hh <= 22)
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0
    pos[short] = -1.0
    return _hold_until(pos, df, 120)


def on_ret(df: pd.DataFrame, p: dict) -> pd.Series:
    """Overnight-return conditioning: at 01:00 UTC fade the extreme first-hour
    return z (prior 90d distribution). No same-day-future information."""
    ts = df["ts"]
    ret1h = df["c"].pct_change(60)
    z = _z(ret1h, 90 * 1440)
    hh = ts.dt.hour
    at_open = hh == 1
    long = at_open & (z.shift(1) < -p["band"])
    short = at_open & (z.shift(1) > p["band"])
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0
    pos[short] = -1.0
    return _hold_until(pos, df, 22 * 60)


def volauto(df: pd.DataFrame, p: dict) -> pd.Series:
    atr = (df["h"] - df["l"]).rolling(60).mean()
    hi_vol = _pct_rank(atr, 1440) > p["volpct"]
    r30 = df["c"].pct_change(30)
    z = _z(r30, 1440)
    short = hi_vol & (z.shift(1) > p["band"])
    long = hi_vol & (z.shift(1) < -p["band"])
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0
    pos[short] = -1.0
    return _hold_until(pos, df, p["hold"])


def rv_regime(df: pd.DataFrame, p: dict) -> pd.Series:
    rv = df["c"].pct_change().rolling(1440).std()
    hi = _pct_rank(rv, 30 * 1440) > p["hi"]
    lo = _pct_rank(rv, 30 * 1440) < p["lo"]
    r60 = df["c"].pct_change(60)
    z = _z(r60, 1440)
    mr_short = hi & (z.shift(1) > 2.0)
    mr_long = hi & (z.shift(1) < -2.0)
    mom_long = lo & (df["c"] > df["h"].rolling(240).max().shift(1))
    mom_short = lo & (df["c"] < df["l"].rolling(240).min().shift(1))
    pos = pd.Series(0.0, index=df.index)
    pos[mr_long] = 1.0; pos[mom_long] = 1.0
    pos[mr_short] = -1.0; pos[mom_short] = -1.0
    return _hold_until(pos, df, 120)


def vol_target_mom(df: pd.DataFrame, p: dict) -> pd.Series:
    ret = df["c"] - df["c"].shift(p["lookback"])
    atr = (df["h"] - df["l"]).rolling(60).mean()
    ok_vol = _pct_rank(atr, 1440) <= p["volcap"]
    long = (ret.shift(1) > 0) & ok_vol
    short = (ret.shift(1) < 0) & ok_vol
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0; pos[short] = -1.0
    return _hold_until(pos, df, p["lookback"])


def fail_breakout(df: pd.DataFrame, p: dict) -> pd.Series:
    rh = df["h"].rolling(p["rwin"]).max().shift(1)
    rl = df["l"].rolling(p["rwin"]).min().shift(1)
    broke_up = (df["c"] > rh).astype(float)
    back_in = df["c"] < rh
    trigger_up = broke_up.rolling(p["confirm"]).max() > 0
    short = trigger_up & back_in
    broke_dn = (df["c"] < rl).astype(float)
    back_in_dn = df["c"] > rl
    trigger_dn = broke_dn.rolling(p["confirm"]).max() > 0
    long = trigger_dn & back_in_dn
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0; pos[short] = -1.0
    return _hold_until(pos, df, p["hold"])


def fvg(df: pd.DataFrame, p: dict) -> pd.Series:
    gap_up = df["l"] > df["h"].shift(2)
    gap_dn = df["h"] < df["l"].shift(2)
    lvl_up = df["h"].shift(2)
    lvl_dn = df["l"].shift(2)
    unfilled_up = (df["l"].rolling(p["fill_win"]).min() > lvl_up).shift(1)
    unfilled_dn = (df["h"].rolling(p["fill_win"]).max() < lvl_dn).shift(1)
    short = gap_up & unfilled_up
    long = gap_dn & unfilled_dn
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0; pos[short] = -1.0
    return _hold_until(pos, df, 30)


def forecast_fund(df: pd.DataFrame, p: dict, settle_hours=(0, 8, 16)) -> pd.Series:
    """premiumIndex z beyond band inside pre-settlement window -> fade premium."""
    z = _z(df["c"], p["zwin"])
    ts = df["ts"]
    hh = ts.dt.hour
    mins = ts.dt.hour * 60 + ts.dt.minute
    pre = pd.Series(False, index=df.index)
    for sh in settle_hours:
        lo = max(0, sh * 60 - p["pre_window"])
        pre = pre | ((mins >= lo) & (mins < sh * 60))
    long = pre & (z.shift(1) < -p["band"])
    short = pre & (z.shift(1) > p["band"])
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0; pos[short] = -1.0
    return _hold_until(pos, df, p["pre_window"])


# ------------------------------------------------------------------ 1h / pair

def tsmom_h(df: pd.DataFrame, p: dict) -> pd.Series:
    ret = df["c"] - df["c"].shift(p["lookback"])
    sd = df["c"].pct_change().rolling(p["lookback"]).std() * np.sqrt(p["lookback"])
    strong = ret.abs() > 0.2 * sd
    pos = pd.Series(0.0, index=df.index)
    pos[(ret.shift(1) > 0) & strong.shift(1)] = 1.0
    pos[(ret.shift(1) < 0) & strong.shift(1)] = -1.0
    return _hold_until(pos, df, p["lookback"])


def pair_mr(df_a: pd.DataFrame, df_b: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Spread = log(a) - beta*log(b), beta rolling. Returns frame with ts,spread."""
    a = df_a.set_index("ts")["c"].rename("a")
    b = df_b.set_index("ts")["c"].rename("b")
    m = pd.concat([a, b], axis=1).dropna()
    la, lb = np.log(m["a"]), np.log(m["b"])
    var = lb.rolling(p["beta_win"]).var()
    cov = la.rolling(p["beta_win"]).cov(lb)
    beta = (cov / var).clip(0.2, 3.0)
    spread = la - beta * lb
    z = _z(spread, p["zwin"])
    return pd.DataFrame({"ts": m.index, "spread": spread, "z": z}).reset_index(drop=True)


def corr_break(df_alt: pd.DataFrame, df_btc: pd.DataFrame, p: dict) -> pd.Series:
    a = df_alt.set_index("ts")["c"].pct_change().rename("a")
    b = df_btc.set_index("ts")["c"].pct_change().rename("b")
    m = pd.concat([a, b], axis=1).dropna()
    corr = m["a"].rolling(p["corr_win"]).corr(m["b"])
    low_corr = corr < np.nanpercentile(corr.dropna(), p["corr_pct"])
    r6 = m["b"].rolling(6).sum()
    z = _z(r6, p["corr_win"])
    pos = pd.Series(0.0, index=m.index)
    pos[low_corr.shift(1) & (z.shift(1) > p["band"])] = 1.0
    pos[low_corr.shift(1) & (z.shift(1) < -p["band"])] = -1.0
    out = pd.DataFrame({"ts": m.index, "pos": pos}).reset_index(drop=True)
    return out


def leadlag(df_btc: pd.DataFrame, df_sol: pd.DataFrame, p: dict) -> pd.Series:
    rb = df_btc.set_index("ts")["c"].pct_change(p["lag"]).rename("rb")
    m = df_sol.set_index("ts").join(rb, how="left").ffill()
    z = _z(m["rb"], 1440)
    pos = pd.Series(0.0, index=m.index)
    pos[z.shift(1) > p["band"]] = 1.0
    pos[z.shift(1) < -p["band"]] = -1.0
    return _hold_until_df(pos, p["hold"])


def _hold_until_df(pos: pd.Series, hold: int) -> pd.Series:
    out = pos.copy()
    idx = np.flatnonzero(pos.to_numpy() != 0)
    for i in idx:
        out.iloc[i + 1:i + 1 + hold] = pos.iloc[i]
    return out


# ------------------------------------------------------------------ FX 1m

def asian_range(df: pd.DataFrame, p: dict) -> pd.Series:
    ts = df["ts"]
    day = _day_key(ts)
    hhmm = ts.dt.hour * 60 + ts.dt.minute
    asian = (hhmm >= 0) & (hhmm < 7 * 60)
    rh = df["c"].where(asian).groupby(day).transform("max")
    rl = df["c"].where(asian).groupby(day).transform("min")
    london = (hhmm >= 7 * 60) & (hhmm < 11 * 60)
    c = df["c"]
    long = london & (c > rh.shift(1) + p["edge_frac"] * (rh - rl).shift(1))
    short = london & (c < rl.shift(1) - p["edge_frac"] * (rh - rl).shift(1))
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0; pos[short] = -1.0
    return _hold_until(pos, df, 4 * 60)


def london_mom(df: pd.DataFrame, p: dict) -> pd.Series:
    return asian_range(df, {**p, "edge_frac": 0.0})


def vwap_mr(df: pd.DataFrame, p: dict) -> pd.Series:
    ts = df["ts"]
    day = _day_key(ts)
    tp = df["c"]
    vwap = tp.groupby(day).cumsum() / (pd.Series(range(1, len(df) + 1), index=df.index).groupby(day).cumsum())
    sd = tp.rolling(60).std()
    dev = (df["c"] - vwap) / sd
    hhmm = ts.dt.hour * 60 + ts.dt.minute
    tradable = (hhmm >= 7 * 60) & (hhmm < 20 * 60)
    long = tradable & (dev.shift(1) < -p["band"])
    short = tradable & (dev.shift(1) > p["band"])
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0; pos[short] = -1.0
    return _hold_until(pos, df, p["hold"])


def boll_fade(df: pd.DataFrame, p: dict) -> pd.Series:
    m = df["c"].rolling(p["win"]).mean()
    sd = df["c"].rolling(p["win"]).std()
    long = df["c"] < (m - p["k"] * sd).shift(1)
    short = df["c"] > (m + p["k"] * sd).shift(1)
    pos = pd.Series(0.0, index=df.index)
    pos[long] = 1.0; pos[short] = -1.0
    return _hold_until(pos, df, p["hold"])
