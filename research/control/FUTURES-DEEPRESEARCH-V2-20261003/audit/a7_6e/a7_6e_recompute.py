"""A7-DEEP-6E independent audit recompute — lane A7-DEEP-6E, task
FUTURES-DEEPRESEARCH-V2-20261003.

Fresh, independent recomputation of the DEEP-6E dossier headline numbers
from RAW vendor parquet (no DEEP-6E cache/lib imports; every step rebuilt
from scratch). READ-ONLY on data. Writes only under audit/a7_6e/.

Recompute targets (dossier 6E_DEEP_v2.md):
  1  expiry-rule model 80/80 (holiday-extended IMM rule)
  2  v1-window vol percentile (6.8th pct) + rolling p05/p50/p95
  3  front volume outside 08:30-16:00 CT (55.3%)
  4  ECB/US-data block 06:30-08:00 CT: RV share 15.6% / vol share 12.5%
  5  serial share of outright volume 0.34%
  6  27 rolls: sign 27/27, corr gap vs CIP r=0.91, residual +6.2 ticks
     (BOTH latest-vintage rates AND ALFRED year-end SOFR vintages, PIT-as-of)
  7  migration crossover Thursday d-4 30.7% -> Friday d-3 87.1%
  8  FOMC statement minute 13:00 CT volume x17.2
  9  venue-OI (GLBX stat_type 9) vs CFTC CoT OI: ratio on ALL overlap weeks
 10  CoT EURO FX claims on the FIXED tidy (era flips, extremes, 2022 path,
     crowded-short forward vol)
 11  misc cross-checks (quietest hours, rolling-63 min date, FOMC/ECB peak
     counts, era bar counts, contaminant rows)
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re

import numpy as np
import pandas as pd

DATA = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
NONPRICE = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "a7_6e_recompute.json")

CHI = "America/Chicago"
PX = 1e9
TICK = 5e-05
MONTH = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
         "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
QUARTERLY = {"H", "M", "U", "Z"}
OUTr = re.compile(r"^6E([FGHJKMNQUVXZ])(\d)$")

FILES = [
    ("B2", f"{DATA}/parquet/AV1B-O1M-6E-BACKFILL2/AV1B-O1M-6E-BACKFILL2__2020-01-01_2022-01-01.parquet"),
    ("R1", f"{DATA}/parquet/AV1R-O1M-6E-BACKFILL/AV1R-O1M-6E-BACKFILL__2022-01-01_2024-01-01.parquet"),
    ("R2", f"{DATA}/parquet/AV1R-O1M-6E-BACKFILL/AV1R-O1M-6E-BACKFILL__2024-01-01_2026-01-01.parquet"),
    ("T1", f"{DATA}/parquet/AV1T-O1M-6E/AV1T-O1M-6E__2026-01-01_2026-07-01.parquet"),
    ("T2", f"{DATA}/parquet/AV1T-O1M-6E/AV1T-O1M-6E__2026-07-01_2026-10-01.parquet"),
]


def jdump(obj, path):
    def san(o):
        if isinstance(o, dict):
            return {str(k): san(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [san(v) for v in o]
        if isinstance(o, (float, np.floating)):
            return float(o) if np.isfinite(o) else None
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, (pd.Timestamp, dt.date, dt.datetime)):
            return str(o)
        return o
    with open(path, "w") as fh:
        json.dump(san(obj), fh, indent=1, allow_nan=False)


# ---------------------------------------------------------------- expiry rule
def third_wd(y, m, wd):
    d = dt.date(y, m, 1)
    off = (wd - d.weekday()) % 7
    return d + dt.timedelta(days=off + 14)


def nth_wd(y, m, wd, n):
    d = dt.date(y, m, 1)
    off = (wd - d.weekday()) % 7
    return d + dt.timedelta(days=off + 7 * (n - 1))


def good_friday(y):
    a = y % 19
    b, c = y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mo = (h + l - 7 * m + 114) // 31
    da = ((h + l - 7 * m + 114) % 31) + 1
    return dt.date(y, mo, da) - dt.timedelta(days=2)


def holidays(y):
    h = {third_wd(y, 1, 0), third_wd(y, 2, 0), nth_wd(y, 10, 0, 2),
         good_friday(y), dt.date(y, 11, 11)}
    if y >= 2022:
        h.add(dt.date(y, 6, 19))
    out = set()
    for d in h:
        if d.weekday() == 5:
            out.add(d - dt.timedelta(days=1))
        elif d.weekday() == 6:
            out.add(d + dt.timedelta(days=1))
        else:
            out.add(d)
    return out


def last_trade(y, m):
    tw = third_wd(y, m, 2)
    hol = holidays(y)
    d, n = tw, 0
    while n < 2:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5 and d not in hol:
            n += 1
    return d


def main():
    res = {"schema": "a7_6e_recompute@1", "generated": dt.datetime.utcnow().isoformat()}

    # ---- load raw vendor files (READ-ONLY) ----
    frames = []
    era_counts = {}
    for tag, f in FILES:
        d = pd.read_parquet(f, columns=["raw_symbol", "ts_event", "close", "volume"])
        sy = d["raw_symbol"].astype(str)
        ou = sy.str.fullmatch(OUTr)
        era_counts[tag] = {
            "rows_total": int(len(d)),
            "rows_outright": int(ou.sum()),
            "rows_dash_spread": int(sy.str.contains("-").sum()),
            "stray_other": {k: int(v) for k, v in
                            sy[~sy.str.contains("-") & ~ou].value_counts().items()},
        }
        g = d[ou].copy()
        g["era"] = tag
        frames.append(g)
    df = pd.concat(frames, ignore_index=True)
    res["raw_load"] = {
        "era_counts": era_counts,
        "total_outright_bars": int(len(df)),
        "contracts": int(df["raw_symbol"].nunique()),
    }

    # ---- annotate: CT wall clock, session date, RTH flag ----
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    loc = df["dt"].dt.tz_convert(CHI)
    hhmm = loc.dt.hour * 60 + loc.dt.minute
    wall = loc.dt.tz_localize(None).dt.normalize()
    df["session_date"] = (wall + pd.to_timedelta(
        (hhmm >= 17 * 60).astype(int), unit="D")).dt.date
    df["minute_of_day"] = hhmm
    df["in_rth"] = (hhmm >= 8 * 60 + 30) & (hhmm < 16 * 60)
    df["close_px"] = df["close"] / PX
    df["contract"] = df["raw_symbol"] + "_" + (2020 + df["raw_symbol"].str[-1].astype(int)).astype(str)

    # ---- expiry rule check (1) ----
    last_sess = df.groupby("raw_symbol")["session_date"].max()
    rule_rows = []
    for sym, ls in last_sess.items():
        m = OUTr.fullmatch(sym)
        y, mo = 2020 + int(m.group(2)), MONTH[m.group(1)]
        rule_rows.append({"symbol": sym, "expiry_rule": last_trade(y, mo).isoformat(),
                          "expiry_obs": str(ls), "quarterly": m.group(1) in QUARTERLY})
    rrd = pd.DataFrame(rule_rows)
    rrd["dow_obs"] = pd.to_datetime(rrd["expiry_obs"]).dt.dayofweek
    # expired (authoritative last session) iff both last session and rule
    # date lie inside the data window; future contracts use the rule date
    data_end = pd.Timestamp(df["session_date"].max())
    rrd["exp_rule_ts"] = pd.to_datetime(rrd["expiry_rule"])
    rrd["last_ts"] = pd.to_datetime(rrd["expiry_obs"])
    rrd["expired_ok"] = (rrd["last_ts"] <= data_end) & (rrd["exp_rule_ts"] <= data_end)
    rrd["delivery"] = pd.to_datetime(
        np.where(rrd["expired_ok"], rrd["last_ts"], rrd["exp_rule_ts"]))
    q = rrd[rrd["quarterly"]]
    expd = rrd[rrd["exp_rule_ts"] <= pd.Timestamp("2026-09-30")]
    res["expiry_rule"] = {
        "n_contracts_total": int(len(rrd)),
        "n_expired_by_rule": int(len(expd)),
        "n_match_among_expired": int((expd["expiry_rule"] == expd["expiry_obs"]).sum()),
        "quarterly_effective_expiry_dow_monday": f"{int((pd.to_datetime(q['delivery']).dt.dayofweek == 0).sum())}/{len(q)}",
        "non_monday_quarteral_expiries": [
            {"symbol": r.symbol, "expiry": str(pd.Timestamp(r.delivery).date())}
            for r in q.itertuples()
            if pd.Timestamp(r.delivery).dayofweek != 0],
    }

    # ---- held calendar rule (quarterly front until last session before
    #      delivery-month day 1) — independent implementation ----
    qs = rrd[rrd["quarterly"]].sort_values("delivery").reset_index(drop=True)
    sessions = sorted(df["session_date"].unique())
    held_map = {}
    for i in range(len(qs) - 1):
        c, exp = qs.loc[i, "symbol"], qs.loc[i, "delivery"]
        nxt_first = (exp.replace(day=1) + pd.DateOffset(months=1))
        if i == 0:
            lo = pd.Timestamp("1900-01-01")
        else:
            lo = pd.Timestamp(qs.loc[i - 1, "delivery"]).replace(day=1)
        for s in sessions:
            ts = pd.Timestamp(s)
            if lo <= ts < nxt_first and s not in held_map:
                # only assign if this contract trades that session
                held_map[s] = c
    # rebuild sequentially: contract holds from prior delivery-month day-1
    # (the simple loop above assigns the EARLIEST contract in [lo, nxt) — fix:
    # walk sessions forward, contract = last one whose window contains s)
    held_map = {}
    ci = 0
    for s in sessions:
        ts = pd.Timestamp(s)
        # latest contract i whose holding window [lo_i, first_i) contains ts
        cand = None
        for i in range(len(qs) - 1):
            exp = qs.loc[i, "delivery"]
            lo = pd.Timestamp("1900-01-01") if i == 0 else pd.Timestamp(
                qs.loc[i - 1, "delivery"]).replace(day=1)
            hi = exp.replace(day=1) + pd.DateOffset(months=1)
            # rule: hold until LAST session BEFORE delivery-month day 1
            if lo <= ts < exp.replace(day=1):
                cand = qs.loc[i, "symbol"]
        if cand is not None:
            held_map[s] = cand + "_" + str(2020 + int(cand[-1]))
    held = pd.DataFrame({"session_date": list(held_map.keys()),
                         "held": list(held_map.values())}).sort_values("session_date")
    held["session_date"] = held["session_date"].astype(str)
    res["held_map"] = {"n_sessions": int(len(held)),
                       "first": held["session_date"].iloc[0],
                       "last": held["session_date"].iloc[-1]}

    # per-(session, contract) aggregates
    sess = df.groupby(["session_date", "contract"]).agg(
        close=("close_px", "last"), volume=("volume", "sum")).reset_index()
    sess["session_date"] = sess["session_date"].astype(str)

    # ---- front panel (held contract bars) ----
    front_keys = set(zip(held["session_date"], held["held"]))
    df["session_date"] = df["session_date"].astype(str)
    fk = list(zip(df["session_date"], df["contract"]))
    f = df[pd.Series([k in front_keys for k in fk], index=df.index)].copy()
    res["front"] = {"bars": int(len(f)), "sessions": int(f["session_date"].nunique())}

    # (3) RTH split
    res["rth_split"] = {
        "vol_outside_pct": float(f.loc[~f["in_rth"], "volume"].sum() / f["volume"].sum() * 100),
        "vol_inside_pct": float(f.loc[f["in_rth"], "volume"].sum() / f["volume"].sum() * 100),
        "bars_outside": int((~f["in_rth"]).sum()),
    }

    # (4) segment RV / volume shares
    SEG = {"ecb_usdata": (390, 480), "london_morning": (120, 300),
           "us_morning_8_12": (480, 720), "asia": (-300, 120)}
    f = f.sort_values(["raw_symbol", "dt"])
    f["lret"] = np.log(f["close_px"] / f.groupby("raw_symbol")["close_px"].shift(1))
    f.loc[(f["session_date"] != f.groupby("raw_symbol")["session_date"].shift(1))
          | ((f["dt"] - f.groupby("raw_symbol")["dt"].shift(1)).dt.total_seconds() > 120),
          "lret"] = np.nan
    # session-relative minute for evening hours (17:00-24:00 of D-1)
    srmin = np.where(f["minute_of_day"] >= 17 * 60,
                     f["minute_of_day"] - 24 * 60, f["minute_of_day"])
    f = f.assign(srmin=srmin)
    tot_rv = float(np.nansum(f["lret"] ** 2))
    tot_v = float(f["volume"].sum())
    segs = {}
    for name, (a, b) in SEG.items():
        m = (f["srmin"] >= a) & (f["srmin"] < b)
        segs[name] = {"rv_share_pct": float(np.nansum(f.loc[m, "lret"] ** 2) / tot_rv * 100),
                      "vol_share_pct": float(f.loc[m, "volume"].sum() / tot_v * 100)}
    res["segments"] = segs
    # quietest CT hours by volume share (wall-clock hours)
    hv = f.assign(h=f["srmin"] // 60).groupby("h")["volume"].sum() / tot_v * 100
    res["quietest_session_hours"] = {f"h{int(h):+03d}": float(v)
                                     for h, v in hv.nsmallest(3).items()}
    res["h078910_share_pct"] = float(hv[[7, 8, 9, 10]].sum())

    # (5) serial vs quarterly volume
    qvol = sess[sess["contract"].str[2].isin(list(QUARTERLY))]["volume"].sum()
    sym_quarterly = set(rrd.loc[rrd["quarterly"], "symbol"])
    qvol = df[df["raw_symbol"].isin(sym_quarterly)]["volume"].sum()
    svol = df[~df["raw_symbol"].isin(sym_quarterly)]["volume"].sum()
    res["serial_vs_quarterly"] = {
        "n_quarterly": int(len(sym_quarterly)),
        "n_serial": int(rrd["symbol"].nunique() - len(sym_quarterly)),
        "serial_share_pct": float(svol / (svol + qvol) * 100),
    }

    # ---- daily chain returns (held closes, within-contract) ----
    closes = sess.pivot_table(index="session_date", columns="contract", values="close")
    px = closes.stack().rename("close").reset_index()
    px["prev_close"] = px.groupby("contract")["close"].shift(1)
    lut = px.set_index(["session_date", "contract"])[["close", "prev_close"]]
    daily = held.copy().set_index("session_date")
    daily = daily.join(lut, on=["session_date", "held"])
    daily.index = pd.to_datetime(daily.index)
    daily = daily.sort_index()
    daily["ret"] = daily["close"] / daily["prev_close"] - 1
    daily["logret"] = np.log(daily["close"] / daily["prev_close"])
    lr = daily["logret"].dropna()

    # (2) v1 window placement
    win = daily.loc["2025-09-09":"2026-10-01", "ret"].dropna()
    n = len(win)
    vol_s = lr.rolling(n).std() * np.sqrt(252) * 100
    drift_s = lr.rolling(n).sum() * 100
    v1v = float(win.std() * np.sqrt(252) * 100)
    res["v1_window"] = {
        "n_returns": int(n),
        "ann_vol_pct": v1v,
        "vol_percentile": float((vol_s.dropna() <= v1v).mean() * 100),
        "drift_pct": float((1 + win).prod() - 1) * 100,
        "drift_percentile": float((drift_s.dropna() <= float((1 + win).prod() - 1) * 100).mean() * 100),
        "roll_p05": float(vol_s.quantile(.05)), "roll_p50": float(vol_s.quantile(.5)),
        "roll_p95": float(vol_s.quantile(.95)),
    }
    roll63 = lr.rolling(63).std() * np.sqrt(252) * 100
    res["rolling63"] = {"min": float(roll63.min()), "min_date": str(roll63.idxmin().date()),
                        "max": float(roll63.max()), "max_date": str(roll63.idxmax().date())}
    res["daily_ret"] = {"std_pct": float(daily["ret"].std() * 100),
                        "n": int(daily["ret"].notna().sum())}

    # ---- (6) rolls + CIP ----
    hc = held.copy()
    hc["prev"] = hc["held"].shift()
    rolls = hc[hc["held"].ne(hc["prev"]) & hc["prev"].notna()]
    exp_lut = {r.symbol + "_" + str(2020 + int(r.symbol[-1])): r.delivery
               for r in rrd.itertuples()}
    # rates
    sofr_l = pd.read_csv(f"{NONPRICE}/fred_alfred/latest/SOFR_latest.csv")
    sofr_l["date"] = pd.to_datetime(sofr_l["observation_date"])
    sofr_l = sofr_l.set_index("date")["SOFR"].sort_index()
    estr = pd.read_parquet(f"{NONPRICE}/normalized/ecb_tidy.parquet")
    estr = estr[estr["series_id"] == "ECB_ESTR"].copy()
    estr["date"] = pd.to_datetime(estr["observation_period"])
    estr = estr.set_index("date")["value"].sort_index()
    diff_l = (sofr_l / 100 - estr / 100).dropna()

    # ALFRED year-end SOFR vintages (PIT-as-of): for roll date d use the latest
    # vintage whose as-of date <= d; observation = nearest <= that cutoff
    vint = {}
    for p in sorted(glob.glob(f"{NONPRICE}/fred_alfred/vintage_attempts/SOFR_*.csv")):
        asof = pd.Timestamp(re.search(r"SOFR_(\d{4}-\d{2}-\d{2})\.csv", p).group(1))
        d = pd.read_csv(p)
        d["date"] = pd.to_datetime(d["observation_date"])
        vint[asof] = d.set_index("date")[d.columns[1]].sort_index()

    def sofr_vintage_at(rd):
        elig = [a for a in sorted(vint) if a <= rd]
        if not elig:
            return np.nan
        s = vint[elig[-1]]
        idx = s.index.asof(rd)
        if idx is None:
            return np.nan
        v = s.loc[idx]
        return float(v) if pd.notna(v) else np.nan

    vols_w = sess.pivot_table(index="session_date", columns="contract", values="volume")
    rows = []
    for r in rolls.itertuples():
        old, new, dstr = r.prev, r.held, r.session_date
        if old not in closes.columns or new not in closes.columns:
            continue
        eo, en = exp_lut[old], exp_lut[new]
        d_exp = (en - eo).days
        co, cn = closes.at[dstr, old], closes.at[dstr, new]
        gap_px = cn - co
        gap_pct = gap_px / co * 100
        rd = pd.Timestamp(dstr)
        near = diff_l.index.asof(rd)
        rd_diff = float(diff_l.loc[near])
        cip = rd_diff * (d_exp / 360.0) * 100
        sv = sofr_vintage_at(rd)
        near_e = estr.index.asof(rd)
        ev = float(estr.loc[near_e]) if near_e is not None else np.nan
        cip_v = (sv / 100 - ev / 100) * (d_exp / 360.0) * 100
        rows.append({"roll": dstr, "old": old, "days": d_exp,
                     "gap_ticks": gap_px / TICK, "gap_pct": gap_pct,
                     "cip_latest_pct": cip, "cip_vintage_pct": cip_v,
                     "rate_diff_latest_pct": rd_diff * 100,
                     "sofr_vintage": sv, "estr_latest": ev})
    rd_f = pd.DataFrame(rows)
    rd_f["gap_minus_cip_latest_ticks"] = (rd_f["gap_pct"] - rd_f["cip_latest_pct"]) / 0.005
    rd_f["gap_minus_cip_vintage_ticks"] = (rd_f["gap_pct"] - rd_f["cip_vintage_pct"]) / 0.005
    sign_l = ((rd_f["gap_pct"] > 0) & (rd_f["rate_diff_latest_pct"] > 0))
    sign_v = ((rd_f["gap_pct"] > 0) & (rd_f["cip_vintage_pct"] > 0))
    res["rolls_cip"] = {
        "n": int(len(rd_f)),
        "n_positive_gaps": int((rd_f["gap_ticks"] > 0).sum()),
        "median_gap_ticks": float(rd_f["gap_ticks"].median()),
        "min_max_ticks": [float(rd_f["gap_ticks"].min()), float(rd_f["gap_ticks"].max())],
        "sign_agreement_vs_ratediff_latest": f"{int(sign_l.sum())}/{len(rd_f)}",
        "sign_agreement_gap_vs_cip_vintage": f"{int(sign_v.sum())}/{len(rd_f)}",
        "corr_gap_vs_cip_latest": float(rd_f[["gap_pct", "cip_latest_pct"]].corr().iloc[0, 1]),
        "corr_gap_vs_cip_vintage": float(rd_f[["gap_pct", "cip_vintage_pct"]].corr().iloc[0, 1]),
        "median_gap_minus_cip_latest_ticks": float(rd_f["gap_minus_cip_latest_ticks"].median()),
        "median_gap_minus_cip_vintage_ticks": float(rd_f["gap_minus_cip_vintage_ticks"].median()),
        "vintage_note": "ALFRED year-end SOFR vintages on disk: 2019/2020/2021/2022/2023/"
                        "2024-12-31 + 2026-09-30 (NO 2025-12-31 vintage -> 2025-2026 rolls "
                        "use the 2024-12-31 vintage, stale up to ~21 months vs roll date); "
                        "ESTR latest-only (ECB SDW), no vintage set on disk",
        "rows": rd_f.to_dict("records"),
    }

    # (7) migration path
    path_rows = []
    for r in rolls.itertuples():
        old, new = r.prev, r.held
        if old not in vols_w.columns or new not in vols_w.columns:
            continue
        eo = exp_lut[old]
        idx = pd.DatetimeIndex(pd.to_datetime(vols_w.index))
        m = (idx <= eo) & (idx >= eo - pd.Timedelta(days=25))
        w = vols_w.loc[m, [old, new]]
        for d, row in w.iterrows():
            o, nn = row[old], row[new]
            if pd.isna(o) and pd.isna(nn):
                continue
            path_rows.append({"old": old, "dte": int((eo - pd.Timestamp(d)).days),
                              "new_share": float(nn / (nn + o) * 100) if (nn + o) > 0 else None})
    pdf_ = pd.DataFrame(path_rows)
    med = pdf_.groupby("dte")["new_share"].median()
    res["migration"] = {str(int(k)): round(float(v), 2) for k, v in med.items()
                        if 0 <= k <= 10}

    # ---- (8) FOMC x17.2 ----
    ev_dates, fomc_rows = set(held["session_date"]), []
    for p in sorted(glob.glob(f"{NONPRICE}/fed/statements/monetary*.html")):
        m = re.fullmatch(r"monetary(\d{8})a\.html", os.path.basename(p))
        if not m:
            continue
        d = pd.Timestamp(m.group(1))
        s = d.strftime("%Y-%m-%d")
        if s < "2020-01-01" or s not in ev_dates:
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
        mt = re.search(r"For release at\s*(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(E[SD]T)", txt)
        if mt:
            hh = int(mt.group(1)) % 12 + (12 if mt.group(3) == "p" else 0)
            ts = pd.Timestamp(d.year, d.month, d.day, hh, int(mt.group(2)), tz="America/New_York")
        else:
            ts = pd.Timestamp(d.year, d.month, d.day, 14, 0, tz="America/New_York")
        ct = ts.tz_convert(CHI)
        fomc_rows.append({"date": s, "minute": ct.hour * 60 + ct.minute,
                          "time_proven": mt is not None})
    fds = {r["date"] for r in fomc_rows}
    weds = {s for s in ev_dates if pd.Timestamp(s).dayofweek == 2 and s not in fds}
    sub_e = f[(f["session_date"].isin(fds)) & (f["minute_of_day"].between(770, 830))]
    sub_c = f[(f["session_date"].isin(weds)) & (f["minute_of_day"].between(770, 830))]
    me = sub_e.groupby("minute_of_day")["volume"].median()
    mc = sub_c.groupby("minute_of_day")["volume"].median()
    res["fomc"] = {
        "n_events": len(fomc_rows), "n_time_proven": sum(r["time_proven"] for r in fomc_rows),
        "ratio_m780": float(me.get(780) / mc.get(780)),
        "ratio_m785": float(me.get(785) / mc.get(785)),
        "ratio_m790": float(me.get(790) / mc.get(790)),
        "median_vol_780_event": float(me.get(780)),
        "median_vol_780_control": float(mc.get(780)),
    }

    # ---- (9) venue OI vs CoT OI ----
    stats = []
    for p in sorted(glob.glob(f"{DATA}/parquet/AV1T-statistics-ALL10/*.parquet")):
        d = pd.read_parquet(p, columns=["raw_symbol", "ts_event", "ts_ref",
                                        "stat_type", "quantity"])
        d = d[(d["stat_type"] == 9) & d["raw_symbol"].astype(str).str.fullmatch(OUTr)]
        stats.append(d)
    st = pd.concat(stats, ignore_index=True)
    st["ref_date"] = pd.to_datetime(st["ts_ref"], unit="ns", utc=True).dt.date
    st["pub"] = pd.to_datetime(st["ts_event"], unit="ns", utc=True)
    st = st.sort_values("pub")
    oi_daily = st.groupby(["raw_symbol", "ref_date"]).agg(
        oi=("quantity", "last")).reset_index()
    oi_sum = oi_daily.groupby("ref_date")["oi"].sum()
    oi_sum.index = pd.to_datetime(oi_sum.index)

    cot = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet")
    cot = cot[cot["series_id"] == "COT_LEGACY_6E"].copy()
    cot["obs_date"] = pd.to_datetime(cot["observation_period"])
    cot = cot.sort_values("obs_date").reset_index(drop=True)
    cot["net_noncomm"] = cot["noncomm_long"] - cot["noncomm_short"]
    c3 = cot[cot["obs_date"] >= "2023-10-01"].copy()
    raw_ratios, dedup_ratios, dedup_rows = [], [], []
    for r in c3.itertuples():
        sub = st[st["ref_date"] == r.obs_date.date()]
        if not len(sub):
            continue
        dedup = sub.sort_values("pub").groupby("raw_symbol")["quantity"].last().sum()
        raw_ratios.append(float(sub["quantity"].sum()) / float(r.open_interest_all))
        dedup_ratios.append(float(dedup) / float(r.open_interest_all))
        dedup_rows.append({"date": str(r.obs_date.date()),
                           "ratio": float(dedup) / float(r.open_interest_all)})
    rr = pd.Series(raw_ratios)
    dr = pd.Series(dedup_ratios)
    res["venue_oi_vs_cot"] = {
        "n_matched": int(len(rr)),
        "raw_sum_method": {
            "median": float(rr.median()), "p05": float(rr.quantile(.05)),
            "p95": float(rr.quantile(.95)), "min": float(rr.min()), "max": float(rr.max()),
            "note": "reproduces DEEP-6E a5 method: sums ALL stat_type-9 rows per "
                    "ref_date; vendor publishes 2 rows per contract-day "
                    "(duplicate publication events; 3-4 on ~115 days)"},
        "dedup_latest_pub_method": {
            "median": float(dr.median()), "p05": float(dr.quantile(.05)),
            "p95": float(dr.quantile(.95)), "min": float(dr.min()), "max": float(dr.max()),
            "n_within_0p2pct_of_1": int((dr.sub(1).abs() <= 0.002).sum()),
            "note": "one row per (contract, ref_date), latest publication wins"},
        "n_cot_tuesdays_since_2023_10": int(len(c3)),
        "worst_dedup_weeks": sorted(dedup_rows, key=lambda x: -x["ratio"])[:4],
        "n_distinct_stat_ref_dates": int(st.groupby("ref_date").size().__len__()),
    }
    # rows-per-pair duplication census
    pairn = st.groupby(["raw_symbol", "ref_date"]).size()
    res["venue_oi_vs_cot"]["rows_per_contract_day"] = {
        str(int(k)): int(v) for k, v in pairn.value_counts().items()}
    # per-contract probe for one clean week (mechanism adjudication)
    probe_date = pd.Timestamp("2024-06-04")
    pc = oi_daily[pd.to_datetime(oi_daily["ref_date"]) == probe_date].sort_values(
        "oi", ascending=False)
    cw = cot[cot["obs_date"] == probe_date]["open_interest_all"]
    if len(cw) and len(pc):
        cot_that_week = float(cw.iloc[0])
        res["venue_oi_vs_cot"]["per_contract_probe_2024_06_04"] = {
            "contracts": {r.raw_symbol: int(r.oi) for r in pc.itertuples()},
            "sum": int(pc["oi"].sum()), "cot_oi": cot_that_week,
            "ratio": float(pc["oi"].sum() / cot_that_week),
            "n_contracts": int(len(pc))}
    else:
        res["venue_oi_vs_cot"]["per_contract_probe_2024_06_04"] = "probe date missing"

    # ---- (10) CoT claims on the FIXED tidy ----
    cot["pct_oi"] = cot["net_noncomm"] / cot["open_interest_all"] * 100
    eras = {"2010-2014": ("2010-01-01", "2014-12-31"),
            "2015-2019": ("2015-01-01", "2019-12-31"),
            "2020-2022": ("2020-01-01", "2022-12-31"),
            "2023-2026": ("2023-01-01", "2026-12-31")}
    era_out = {}
    for k, (a, b) in eras.items():
        m = cot[(cot["obs_date"] >= a) & (cot["obs_date"] <= b)]
        era_out[k] = {"n": int(len(m)), "mean_net_noncomm": float(m["net_noncomm"].mean()),
                      "mean_oi": float(m["open_interest_all"].mean())}
    # strict-past 3y percentile (rolling 156w INCLUDING current, as the lane
    # did; plus a strictly-past variant excluding current)
    roll_min = cot["net_noncomm"].rolling(156, min_periods=104).min()
    roll_max = cot["net_noncomm"].rolling(156, min_periods=104).max()
    cot["pctile"] = (cot["net_noncomm"] - roll_min) / (roll_max - roll_min) * 100
    rmin_p = cot["net_noncomm"].rolling(156, min_periods=104).apply(
        lambda s: s.iloc[:-1].min(), raw=False)
    rmax_p = cot["net_noncomm"].rolling(156, min_periods=104).apply(
        lambda s: s.iloc[:-1].max(), raw=False)
    cot["pctile_strict"] = (cot["net_noncomm"] - rmin_p) / (rmax_p - rmin_p) * 100
    latest = cot.iloc[-1]
    res["cot_fixed"] = {
        "n_weeks": int(len(cot)), "first": str(cot["obs_date"].min().date()),
        "last": str(cot["obs_date"].max().date()),
        "min_net": float(cot["net_noncomm"].min()),
        "min_date": str(cot.loc[cot["net_noncomm"].idxmin(), "obs_date"].date()),
        "max_net": float(cot["net_noncomm"].max()),
        "max_date": str(cot.loc[cot["net_noncomm"].idxmax(), "obs_date"].date()),
        "latest_net": float(latest["net_noncomm"]),
        "latest_date": str(latest["obs_date"].date()),
        "latest_pctile_incl_current": float(latest["pctile"]),
        "latest_pctile_strict_past": float(latest["pctile_strict"]),
        "eras": era_out,
        "dup_obs_dates": int(cot["obs_date"].duplicated().sum()),
    }
    # 2022 crisis summary
    c22 = cot[(cot["obs_date"] >= "2022-01-01") & (cot["obs_date"] <= "2022-12-31")]
    res["cot_fixed"]["crisis_2022"] = {
        "start_net": float(c22["net_noncomm"].iloc[0]),
        "min_net": float(c22["net_noncomm"].min()),
        "min_date": str(c22.loc[c22["net_noncomm"].idxmin(), "obs_date"].date()),
        "end_net": float(c22["net_noncomm"].iloc[-1]),
        "oi_start": float(c22["open_interest_all"].iloc[0]),
        "oi_max": float(c22["open_interest_all"].max()),
    }
    # crowded-short forward vol (join pctile -> fwd 21d vol at obs+3 sessions)
    fwd = daily["ret"].rolling(21).std().shift(-21) * np.sqrt(252) * 100
    rows = []
    for r in cot.dropna(subset=["pctile"]).itertuples():
        if not (pd.Timestamp("2020-01-01") <= r.obs_date <= pd.Timestamp("2026-09-01")):
            continue
        start = daily.index.asof(r.obs_date + pd.Timedelta(days=3))
        if start is None or pd.isna(fwd.get(start)):
            continue
        rows.append({"p": float(r.pctile), "ps": float(r.pctile_strict),
                     "v": float(fwd.loc[start])})
    j = pd.DataFrame(rows)
    res["cot_fixed"]["fwd_vol_by_percentile"] = {
        "n": int(len(j)),
        "ge80": {"n": int((j["p"] >= 80).sum()), "mean": float(j.loc[j["p"] >= 80, "v"].mean())},
        "le20": {"n": int((j["p"] <= 20).sum()), "mean": float(j.loc[j["p"] <= 20, "v"].mean()),
                 "median": float(j.loc[j["p"] <= 20, "v"].median())},
        "ge80_median": float(j.loc[j["p"] >= 80, "v"].median()),
        "mid_mean": float(j.loc[(j["p"] > 20) & (j["p"] < 80), "v"].mean()),
        "le20_strict_mean": float(j.loc[j["ps"] <= 20, "v"].mean()),
        "ge80_strict_mean": float(j.loc[j["ps"] >= 80, "v"].mean()),
    }
    # old-vs-new tidy diff for the 6E series specifically (value-level)
    old = pd.read_parquet(f"{NONPRICE}/normalized/cftc_legacy_tidy.parquet.bak_prefix_mixed_20261003")
    old6 = old[old["series_id"].astype(str).str.startswith("COT_LEGACY_6E")].copy()
    old6["obs_date"] = pd.to_datetime(old6["observation_period"])
    old6["net_noncomm"] = old6["noncomm_long"] - old6["noncomm_short"]
    m = old6.merge(cot[["obs_date", "net_noncomm", "open_interest_all"]],
                   on="obs_date", suffixes=("_old", "_new"))
    res["cot_fixed"]["bak_comparison"] = {
        "bak_6e_series_rows": {str(s): int((old6["series_id"] == s).sum())
                               for s in old6["series_id"].unique()},
        "new_rows": int(len(cot)),
        "joined": int(len(m)),
        "net_noncomm_mismatches": int((m["net_noncomm_old"] != m["net_noncomm_new"]).sum()),
        "oi_mismatches": int((m["open_interest_all_old"] != m["open_interest_all_new"]).sum()),
    }

    # ---- (11) misc: era bar counts on my own era tagging ----
    era_of = np.where(df["dt"] < pd.Timestamp("2022-01-01", tz="UTC"), "B2",
                      np.where(df["dt"] < pd.Timestamp("2026-01-01", tz="UTC"), "R", "T"))
    df["era3"] = era_of
    res["era_bars"] = {e: {"bars": int(len(g)), "sessions": int(g["session_date"].nunique())}
                       for e, g in df.groupby("era3")}

    jdump(res, OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
