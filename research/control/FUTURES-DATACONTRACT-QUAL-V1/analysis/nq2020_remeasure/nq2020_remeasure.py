"""NQ 2020 alias-recovery re-measurement — lane NQ-2020-REMEASURE,
task FUTURES-DATACONTRACT-QUAL-V1 (parent evidence: FUTURES-DEEPRESEARCH-V2-20261003
ERRATUM F1 / A7-NQ F1, read-only).

What this does (descriptive only; no PnL, no signals, no dossier edits):
  1. Loads the two vendor NQ 1m chunks covering 2018-06..2022-06 READ-ONLY and
     trims to 2018-06-01..2021-01-31 (warmup + build window; aggregates use 2020).
  2. Builds TWO panels from the same rows:
       NEW (alias-recovered view, ERRATUM F1 frozen rule):
           instrument_id==16908 AND utc-date < 2020-06-01 -> raw_symbol 'NQM0'
           (the vendor dash-alias 'NQU8-NQM9' IS the June-2020 contract NQM0).
       OLD' (v2 behavior, sensitivity/reproduction): drop every dash symbol
           exactly as NQ_deep_lib.load_outright_1m did (the alias disappears,
           hole 2020-03-23..05-29 -> NaN closes).
  3. Integrity checks (panel-wide + alias-specific).
  4. Sessionizes with the v2 conventions (America/Chicago, session D =
     17:00 CT D-1 -> 16:00 CT D, era-B close everywhere in window; maintenance
     break bars dropped after counting; DST via tz_convert wall-clock),
     builds the time-cluster contract registry (one-digit-year epochs),
     per-(contract,session) table, and the PIT k=5 volume-crossover front rule
     (verbatim v2 logic: trailing-5-session mean volume of next quarterly vs
     current, decided at close of t; held map from v2 code).
  5. Recomputes the dossier's 2020 aggregates on both series and diffs against
     the v2 a1 reference numbers (read from NQ_a1_regimes.json read-only):
     yearly log return, ann vol, worst/best days, max DD, session counts,
     COVID drawdown episode, rvol20/rvol60 maxima.
  6. OLD' must approximately reproduce the v2 numbers (validates that deltas
     come from the alias recovery, not from a different methodology).

Outputs: nq2020_remeasure.json (+ stdout table). Prose in NQ2020_ADDENDUM.md.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re

import numpy as np
import pandas as pd

DATA_ROOT = ("/Users/hoangminhlong/my-quantitative-data/"
             "futures-databento-av1trim")
V2 = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
      "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, "nq2020_remeasure.json")

CHI = "America/Chicago"
MONTH_CODE = {"H": 3, "M": 6, "U": 9, "Z": 12}
CODE_MONTH = {3: "H", 6: "M", 9: "U", 12: "Z"}
RTH_MIN = 6 * 60 + 30  # 08:30-15:00 CT core = 390 minutes

TRIM_END = "2021-02-01"          # exclusive UTC bound of the build window
FRAME_START = "2019-06-03"       # dd/rvol frame start (mission build window)
FRAME_END = "2021-01-31"
ALIAS_ID = 16908
VIEW_RULE_DATE = pd.Timestamp("2020-06-01", tz="UTC")
HOLE_START, HOLE_END = "2020-03-23", "2020-05-29"  # alleged-hole session dates


# --------------------------------------------------------------------------
# loading + views
# --------------------------------------------------------------------------
def load_raw() -> pd.DataFrame:
    files = [
        f"{DATA_ROOT}/parquet/AV1R-O1M-NQ-DELTA/"
        "AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01.parquet",
        f"{DATA_ROOT}/parquet/AV1R-O1M-NQ-DELTA/"
        "AV1R-O1M-NQ-DELTA__2020-06-01_2022-06-01.parquet",
    ]
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    df = df[df["dt"] < pd.Timestamp(TRIM_END, tz="UTC")].reset_index(drop=True)
    return df


def make_views(df: pd.DataFrame):
    new = df.copy()
    m = (new["instrument_id"] == ALIAS_ID) & (new["dt"] < VIEW_RULE_DATE)
    new.loc[m, "raw_symbol"] = "NQM0"
    new = new[~new["raw_symbol"].str.contains("-")].reset_index(drop=True)
    old = df[~df["raw_symbol"].str.contains("-")].reset_index(drop=True)
    return new, old, int(m.sum())


# --------------------------------------------------------------------------
# integrity
# --------------------------------------------------------------------------
def integrity(panel: pd.DataFrame, label: str) -> dict:
    return {
        "label": label,
        "rows": int(len(panel)),
        "dup_instrument_minute": int(panel.duplicated(
            subset=["instrument_id", "ts_event"]).sum()),
        "dup_symbol_minute": int(panel.assign(
            minute=panel["dt"].astype("int64") // 60_000_000_000).duplicated(
            subset=["raw_symbol", "minute"]).sum()),
        "high_lt_low": int((panel["high"] < panel["low"]).sum()),
        "negative_price": int(((panel[["open", "high", "low", "close"]] < 0)
                               .any(axis=1)).sum()),
        "close_outside_range": int(((panel["close"] > panel["high"]) |
                                    (panel["close"] < panel["low"])).sum()),
        "zero_volume_bars": int((panel["volume"] == 0).sum()),
    }


def alias_checks(df: pd.DataFrame, panel_new: pd.DataFrame) -> dict:
    a = df[df["instrument_id"] == ALIAS_ID].copy()
    a["day"] = a["dt"].dt.date
    alias = a[a["dt"] < VIEW_RULE_DATE]
    relab = a[a["dt"] >= VIEW_RULE_DATE]
    hole = alias[(alias["dt"] >= pd.Timestamp(HOLE_START, tz="UTC")) &
                 (alias["dt"] < pd.Timestamp("2020-05-30", tz="UTC"))]
    # price sanity on the hole window (outright scale 1e9; NQ traded ~6.6k-9.7k)
    hole_daily = hole.groupby("day").agg(vol=("volume", "sum"),
                                         close=("close", "last"))
    hole_ret = np.log(hole_daily["close"]).diff().dropna()
    raw_nqm0_ids = sorted(df[(df["raw_symbol"] == "NQM0") &
                             (df["dt"] >= VIEW_RULE_DATE)]
                          ["instrument_id"].unique().tolist())
    small_px = a[a["close"] < 100_000_000_000]  # <10,000 at 1e9 scale
    return {
        "alias_rows_total": int(len(alias)),
        "alias_volume_total": int(alias["volume"].sum()),
        "alias_span": [str(alias["dt"].min()), str(alias["dt"].max())],
        "relabel_rows_2020_06": int(len(relab)),
        "relabel_volume": int(relab["volume"].sum()),
        "relabel_instrument_ids": raw_nqm0_ids,
        "hole_trading_dates": int(hole["day"].nunique()),
        "hole_volume": int(hole["volume"].sum()),
        "hole_max_daily_volume": int(hole_daily["vol"].max()),
        "hole_close_min_max_1e9_scale": [float(hole_daily["close"].min()),
                                         float(hole_daily["close"].max())],
        "hole_max_abs_daily_logret": float(hole_ret.abs().max()),
        "hole_dup_instrument_minute": int(hole.duplicated(
            subset=["instrument_id", "ts_event"]).sum()),
        "hole_high_lt_low": int((hole["high"] < hole["low"]).sum()),
        "hole_negative": int(((hole[["open", "high", "low", "close"]] < 0)
                              .any(axis=1)).sum()),
        "hole_zero_volume_bars": int((hole["volume"] == 0).sum()),
        "pre2020_small_scale_bars": {
            "n": int(len(small_px)),
            "dates": sorted(str(d) for d in small_px["day"].unique()),
            "note": ("bars with close < 1e11 raw (<10,000 at 1e9 scale): "
                     "2018-08 stray prints on the 1e7 fixed-point scale; "
                     "they sit in a <50-bar stray cluster excluded from the "
                     "held path (volume 2 contracts)"),
        },
    }


# --------------------------------------------------------------------------
# sessionize + registry + sessions table (v2 conventions, era-B window)
# --------------------------------------------------------------------------
def sessionize(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    local = df["dt"].dt.tz_convert(CHI)
    hhmm = local.dt.hour * 60 + local.dt.minute
    # naive local wall-clock calendar day + 1 when at/after 17:00 CT: DST-safe
    # day arithmetic (v2 lib used Day offsets on the same wall clock)
    sess = local.dt.normalize().dt.tz_localize(None)
    roll = local.dt.hour >= 17
    sdate = sess + pd.to_timedelta(roll.astype(int), unit="D")
    df["session_date"] = sdate.dt.date
    df["minute_of_day"] = hhmm
    df["in_break"] = (hhmm >= 16 * 60) & (hhmm < 17 * 60)  # era-B close 16:00
    dow = local.dt.dayofweek
    df["weekend_anomaly"] = ((dow == 4) & (hhmm >= 17 * 60)) | (dow == 5)
    df["in_rth"] = (hhmm >= 8 * 60 + 30) & (hhmm < 15 * 60)
    n_break = int(df["in_break"].sum())
    n_wknd = int(df["weekend_anomaly"].sum())
    df = df[~df["in_break"]].copy()
    return df, {"break_bars": n_break, "weekend_anomaly_bars": n_wknd}


def third_friday(year: int, month: int) -> dt.date:
    d = dt.date(year, month, 1)
    offset = (4 - d.weekday()) % 7
    return d + dt.timedelta(days=offset + 14)


def build_registry(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sym, idx in df.groupby("raw_symbol", sort=False).groups.items():
        m = re.fullmatch(r"NQ([HMUZ])(\d)", sym)
        if m is None:
            raise ValueError(f"unexpected outright symbol {sym}")
        code, digit = m.group(1), int(m.group(2))
        sub = df.loc[idx]
        ts = sub["dt"].sort_values().reset_index(drop=True)
        breaks = ts.diff() > pd.Timedelta(days=45)
        sub = sub.assign(_cluster=breaks.cumsum().values)
        for cid, grp in sub.groupby("_cluster"):
            t0, t1 = grp["dt"].min(), grp["dt"].max()
            cands = [third_friday(y, MONTH_CODE[code])
                     for y in range(2010, 2028) if y % 10 == digit]
            ok = [c for c in cands
                  if (pd.Timestamp(c) - pd.Timedelta(days=820)
                      ).tz_localize("UTC") <= t0
                  and t1 <= (pd.Timestamp(c) + pd.Timedelta(days=12)
                             ).tz_localize("UTC")]
            stray = False
            if len(ok) != 1:
                if len(grp) < 50:
                    stray = True
                else:
                    raise ValueError(f"{sym} cluster {cid} {t0}..{t1} "
                                     f"n={len(grp)} cands={ok}")
            exp = ok[0] if ok else None
            rows.append({
                "symbol": sym, "cluster": int(cid),
                "expiry": exp.isoformat() if exp else None,
                "month": MONTH_CODE[code],
                "year": exp.year if exp else None,
                "n_bars": int(len(grp)), "stray": stray})
    reg = pd.DataFrame(rows)
    reg["contract"] = [
        (f"STRAY_{r['symbol']}_{r['cluster']}" if r["stray"] or not r["year"]
         else f"{r['symbol']}_{int(r['year'])}") for _, r in reg.iterrows()]
    return reg


def annotate_contracts(df: pd.DataFrame, reg: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["raw_symbol", "dt"]).reset_index(drop=True)
    brk = df.groupby("raw_symbol")["dt"].diff() > pd.Timedelta(days=45)
    df["_cluster"] = brk.groupby(df["raw_symbol"]).cumsum().fillna(0).astype(int)
    key = df["raw_symbol"] + "|" + df["_cluster"].astype(str)
    rk = reg["symbol"] + "|" + reg["cluster"].astype(str)
    lut = pd.Series(reg["contract"].values, index=rk.values)
    df["contract"] = key.map(lut)
    if df["contract"].isna().any():
        raise ValueError("unmapped rows")
    return df


def sessions_table(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["contract", "session_date"], sort=True)
    sess = g.agg(open=("open", "first"), high=("high", "max"),
                 low=("low", "min"), close=("close", "last"),
                 volume=("volume", "sum"), n_bars=("dt", "size")).reset_index()
    rth = df[df["in_rth"]].groupby(["contract", "session_date"], sort=True)
    ra = rth.agg(rth_bars=("dt", "size")).reset_index()
    sess = sess.merge(ra, on=["contract", "session_date"], how="left")
    sess["rth_coverage"] = sess["rth_bars"].fillna(0) / RTH_MIN
    return sess


# --------------------------------------------------------------------------
# PIT front rule — verbatim v2 logic (k=5 volume crossover)
# --------------------------------------------------------------------------
_QKEY = re.compile(r"^NQ[HMUZ]\d_\d{4}$")


def next_quarter(contract: str) -> str:
    sym, yr = contract.split("_")
    m = MONTH_CODE[sym[2]]
    y = int(yr)
    nm, ny = (m + 3, y) if m < 12 else (3, y + 1)
    return f"NQ{CODE_MONTH[nm]}{ny % 10}_{ny}"


def front_by_volume_crossover(sess: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    sess = sess[sess["contract"].str.match(_QKEY)].copy()
    wide = sess.pivot_table(index="session_date", columns="contract",
                            values="volume", aggfunc="sum").sort_index()
    roll = wide.rolling(k, min_periods=1).mean()
    state = None
    held_contracts = []
    for d in wide.index:
        row = roll.loc[d].dropna()
        row = row[row > 0]
        if state is None:
            state = row.idxmax()
        else:
            nxt = next_quarter(state)
            if nxt in row.index:
                cur_v = row.get(state, np.nan)
                nxt_v = row[nxt]
                if pd.notna(cur_v) and nxt_v > cur_v:
                    state = nxt
                elif pd.isna(cur_v):
                    state = nxt
        held_contracts.append(state)
    return pd.DataFrame({"session_date": wide.index, "held": held_contracts})


def held_daily(sess: pd.DataFrame, held: pd.DataFrame) -> pd.DataFrame:
    m = sess.merge(held.rename(columns={"held": "contract"}),
                   on=["session_date", "contract"], how="right")
    m = m.sort_values("session_date").reset_index(drop=True)
    m["d"] = pd.to_datetime(m["session_date"])
    m["log_close"] = np.log(m["close"].astype(float))
    m["ret"] = m["log_close"].diff()
    m["cov"] = m["rth_coverage"].clip(0, 1).fillna(0.0)
    m["depleted"] = (m["cov"] < 0.25) | m["close"].isna()
    return m


# --------------------------------------------------------------------------
# aggregates (a1 conventions)
# --------------------------------------------------------------------------
def yearly_2020(m: pd.DataFrame) -> dict:
    y = m[(m["d"] >= "2020-01-01") & (m["d"] <= "2020-12-31")]
    rr = y["ret"].dropna()
    lc = y.set_index("d")["log_close"]
    dd_y = lc - lc.cummax()
    iw = rr.idxmin(); ib = rr.idxmax()
    return {
        "n_sessions": int(len(y)),
        "n_data_sessions": int(y["close"].notna().sum()),
        "n_clean_sessions": int((~y["depleted"]).sum()),
        "n_nan_rets": int(y["ret"].isna().sum()),
        "ret_pct": float(100 * y["ret"].sum()),
        "vol_ann_pct": float(100 * rr.std() * np.sqrt(252)),
        "worst_day_pct": float(100 * rr.min()),
        "worst_day_date": str(y.loc[iw, "d"].date()),
        "best_day_pct": float(100 * rr.max()),
        "best_day_date": str(y.loc[ib, "d"].date()),
        "max_dd_pct": float(-100 * dd_y.min()),
        "up_days_pct": float(100 * (rr > 0).mean()),
        "avg_daily_volume_contracts": float(y["volume"].mean()),
    }


def covid_episode(m: pd.DataFrame) -> dict:
    f = m[(m["d"] >= FRAME_START) & (m["d"] <= FRAME_END)].reset_index(drop=True)
    lc = f["log_close"]
    dd = lc - lc.cummax()
    eps = []
    in_dd, start, trough = False, None, None
    for i, v in enumerate(dd):
        if not in_dd and v < -0.10:
            in_dd, start, trough = True, i, i
        elif in_dd:
            if v < dd.iloc[trough]:
                trough = i
            if v >= -1e-9:
                eps.append((start, trough, i))
                in_dd = False
    if in_dd:
        eps.append((start, trough, None))
    out = None
    for s, t, e in eps:
        if f["d"].iloc[t] <= pd.Timestamp("2020-04-01") and \
           f["d"].iloc[t] >= pd.Timestamp("2020-02-01"):
            out = {
                "start": str(f["d"].iloc[s].date()),
                "trough": str(f["d"].iloc[t].date()),
                "end": (str(f["d"].iloc[e].date()) if e is not None
                        else "unrecovered_in_frame"),
                "trough_close_1e9": float(f["close"].iloc[t]),
                "depth_pct": float(-100 * dd.iloc[t]),
                "fall_sessions": int(t - s),
                "recovery_sessions": (int(e - t) if e is not None else None),
                "n_hole_nan_sessions_inside": int(
                    f.iloc[s:(e or len(f) - 1) + 1]["ret"].isna().sum()),
            }
    return out


def rvol(m: pd.DataFrame) -> dict:
    f = m[(m["d"] >= FRAME_START) & (m["d"] <= FRAME_END)].reset_index(drop=True)
    y20 = (f["d"] >= "2020-01-01") & (f["d"] <= "2020-12-31")
    res = {}
    for w in (20, 60):
        v = f["ret"].rolling(w, min_periods=max(2, int(w * 0.75))
                             ).std() * np.sqrt(252)
        vy = v[y20]
        res[f"rvol{w}"] = {
            "max_2020_pct": float(100 * vy.max()),
            "argmax_date": str(f.loc[vy.idxmax(), "d"].date()),
            "value_at_2020_03_27_pct": float(
                100 * v[f["d"] == pd.Timestamp("2020-03-27")].iloc[0]),
            "value_at_2020_04_13_pct": float(
                100 * v[f["d"] == pd.Timestamp("2020-04-13")].iloc[0]),
            "max_frame_pct": float(100 * v.max()),
            "argmax_frame_date": str(f.loc[v.idxmax(), "d"].date()),
        }
    return res


def held_verification(m_new, panel_new, held_new, sess_new) -> dict:
    hz = held_new[(held_new["session_date"] >= dt.date(2020, 3, 23)) &
                  (held_new["session_date"] <= dt.date(2020, 5, 29))]
    hh = hz["held"].value_counts().to_dict()
    # instrument ids behind NQM0_2020 held sessions in the hole window
    ids = panel_new[(panel_new["contract"] == "NQM0_2020") &
                    (panel_new["dt"] >= pd.Timestamp("2020-03-23", tz="UTC")) &
                    (panel_new["dt"] < pd.Timestamp("2020-05-30", tz="UTC"))
                    ]["instrument_id"].unique().tolist()
    june = held_new[(held_new["session_date"] >= dt.date(2020, 6, 1)) &
                    (held_new["session_date"] <= dt.date(2020, 6, 30))]
    chg = june[june["held"] != june["held"].shift()]
    # March roll timing (NQH0 -> NQM0)
    mar = held_new[(held_new["session_date"] >= dt.date(2020, 3, 10)) &
                   (held_new["session_date"] <= dt.date(2020, 3, 31))]
    mchg = mar[mar["held"] != mar["held"].shift()]
    # close continuity at the roll
    s = sess_new[(sess_new["contract"].isin(["NQH0_2020", "NQM0_2020"])) &
                 (sess_new["session_date"] >= dt.date(2020, 3, 16)) &
                 (sess_new["session_date"] <= dt.date(2020, 3, 24))]
    return {
        "hole_held_contracts": {str(k): int(v) for k, v in hh.items()},
        "hole_NQM0_instrument_ids": sorted(int(x) for x in ids),
        "june_rolls": [{"session_date": str(r.session_date),
                        "held": r.held} for r in chg.itertuples()],
        "march_rolls": [{"session_date": str(r.session_date),
                         "held": r.held} for r in mchg.itertuples()],
        "roll_week_closes_1e9": [
            {"session_date": str(r.session_date), "contract": r.contract,
             "close": float(r.close), "volume": int(r.volume)}
            for r in s.itertuples()],
    }


# --------------------------------------------------------------------------
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
    return o


def main():
    print("loading vendor chunks (read-only) ...", flush=True)
    raw = load_raw()
    print(f"rows 2018-06..2021-01: {len(raw):,}")

    new, old, n_relabel = make_views(raw)
    print(f"relabelled rows (id {ALIAS_ID}, <2020-06-01): {n_relabel:,}")

    integ = {
        "raw_cross_chunk_dup_instrument_minute": int(
            raw.duplicated(subset=["instrument_id", "ts_event"]).sum()),
        "panel_new": integrity(new, "alias-recovered view"),
        "panel_old_dashfilter": integrity(old, "v2 dash-filter view"),
        "alias": alias_checks(raw, new),
    }
    print(json.dumps(integ["alias"], indent=1))

    panels, sesses, helds, dailies, extras = {}, {}, {}, {}, {}
    for name, panel in (("new", new), ("old", old)):
        ann, ex = sessionize(panel)
        reg = build_registry(ann)
        ann = annotate_contracts(ann, reg)
        sess = sessions_table(ann)
        held = front_by_volume_crossover(sess, k=5)
        daily = held_daily(sess, held)
        panels[name], sesses[name], helds[name], dailies[name] = ann, sess, held, daily
        extras[name] = {"stray_clusters": int(reg["stray"].sum()),
                        **ex}
        print(f"[{name}] sessions={len(sess):,} held={len(held):,} "
              f"contracts={sess['contract'].nunique()} "
              f"strays={extras[name]['stray_clusters']}")

    # OLD' vs v2 cache: held-map agreement (read-only comparison)
    cache_held = pd.read_parquet(f"{V2}/NQ_cache/held_volume_k5.parquet")
    cache_held["session_date"] = pd.to_datetime(
        cache_held["session_date"]).dt.date
    cmp_win = helds["old"][(helds["old"]["session_date"] >= dt.date(2019, 1, 2)) &
                           (helds["old"]["session_date"] <= dt.date(2021, 1, 31))]
    mg = cmp_win.merge(cache_held, on="session_date", how="left",
                       suffixes=("_mine", "_v2"))
    mism = mg[mg["held_mine"] != mg["held_v2"]]
    held_agree = {
        "window": "2019-01-02..2021-01-31",
        "sessions_compared": int(len(mg)),
        "mismatches": int(len(mism)),
        "mismatch_dates": [
            {"session_date": str(r.session_date), "mine": r.held_mine,
             "v2_cache": (None if pd.isna(r.held_v2) else r.held_v2)}
            for r in mism.itertuples()][:40],
    }
    print("held-map agreement OLD' vs v2 cache:", held_agree["mismatches"],
          "mismatches /", held_agree["sessions_compared"])

    # v2 a1 reference (read-only)
    a1 = json.load(open(f"{V2}/NQ_a1_regimes.json"))
    y20_v2 = [y for y in a1["yearly"] if y["year"] == 2020][0]
    covid_v2 = [e for e in a1["drawdowns_ge10pct"]
                if e["start"] == "2020-02-27"][0]
    rv20_v2 = a1["realized_vol_summary"]["rvol_20d"]
    rv60_v2 = a1["realized_vol_summary"]["rvol_60d"]
    # v2 cache daily (for the worst-day DATE the dossier mislabeled)
    cache_daily = pd.read_parquet(f"{V2}/NQ_cache/nq_held_daily.parquet")
    cache_daily["d"] = pd.to_datetime(cache_daily["d"])
    r20 = cache_daily[(cache_daily["d"] >= "2020-01-01") &
                      (cache_daily["d"] <= "2020-12-31")].set_index("d")[
                          "ret"].dropna()
    v2_ref = {
        "yearly_2020": y20_v2,
        "worst_day_date_from_cache": str(r20.idxmin().date()),
        "best_day_date_from_cache": str(r20.idxmax().date()),
        "covid_episode": covid_v2,
        "rvol20_max": rv20_v2["max"], "rvol20_argmax": rv20_v2["argmax_date"],
        "rvol60_max": rv60_v2["max"], "rvol60_argmax": rv60_v2["argmax_date"],
    }

    agg = {}
    for name in ("new", "old"):
        agg[name] = {"yearly_2020": yearly_2020(dailies[name]),
                     "covid": covid_episode(dailies[name]),
                     "rvol": rvol(dailies[name])}

    verify = held_verification(dailies["new"], panels["new"],
                               helds["new"], sesses["new"])

    # ---- decomposition of the yearly-return delta + roll-week detail ----
    dn, do = dailies["new"].set_index("d"), dailies["old"].set_index("d")

    def _ret(frame, day):
        v = frame.loc[pd.Timestamp(day), "ret"]
        return None if pd.isna(v) else float(100 * v)
    hole_rets = dn.loc[(dn.index >= "2020-03-23") &
                       (dn.index <= "2020-06-01"), "ret"]
    recon_notes = {
        "old_vs_v2_session_count": (
            "v2 map has 260 session rows in 2020, this rebuild 259: the v2 "
            "CACHE splits the 2020-11-01 DST fall-back Sunday-open chunk "
            "(17:00-23:59 CST, first bar 23:00Z) into a phantom session "
            "'2020-11-01'; the CURRENT v2 lib code (replicated here) assigns "
            "it to Monday 2020-11-02. One-row cache artifact; explains the "
            "0.08pp old'-vs-v2 vol gap; yearly ret sum unaffected "
            "(telescoping)."),
        "recovered_hole_returns": {
            "n_sessions": int(hole_rets.notna().sum()),
            "window": "2020-03-23..2020-06-01 (ret from real 05-29 close)",
            "sum_logret_pct": float(100 * hole_rets.sum())},
        "roll_week_2020": {
            "note": ("k=5 crossover fires at close of 2020-03-19 (NQM0 "
                     "trail5 357k > NQH0 229k); held map switches NQH0->NQM0 "
                     "at 03-19, NQM0->NQU0 at 06-18 (same as v2). Old series "
                     "held NQH0 into the hole: its last pre-hole close "
                     "03-20 = 7453.50 is a stale expiry-week print (6,248 "
                     "contracts) vs liquid NQM0 6920.25 / NQU0 6900.00 the "
                     "same session."),
            "ret_0319_new_pct": _ret(dn, "2020-03-19"),
            "ret_0319_old_pct": _ret(do, "2020-03-19"),
            "ret_0320_new_pct": _ret(dn, "2020-03-20"),
            "ret_0320_old_pct": _ret(do, "2020-03-20"),
            "mar_jun_roll_spread_in_0319_ret_pp": float(
                _ret(dn, "2020-03-19") - _ret(do, "2020-03-19"))},
        "covid_recovery_note": (
            "recovery date 2020-06-05 UNCHANGED (old detection landed on the "
            "first post-hole session with dd>=0; the recovered path stays "
            "below the 02-27 peak through 06-04, so the date is now measured, "
            "not hole-bridged). fall sessions 12->16 and recovery 58->54 are "
            "row-count consequences of the trough moving 03-16 -> 03-20."),
    }

    out = {
        "schema": "nq2020_remeasure@1",
        "task": "FUTURES-DATACONTRACT-QUAL-V1 / lane NQ-2020-REMEASURE",
        "provenance": {
            "vendor_files": [
                "AV1R-O1M-NQ-DELTA/AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01.parquet",
                "AV1R-O1M-NQ-DELTA/AV1R-O1M-NQ-DELTA__2020-06-01_2022-06-01.parquet"],
            "view_rule": (f"instrument_id=={ALIAS_ID} AND utc_date < "
                          "2020-06-01 -> raw_symbol 'NQM0' (ERRATUM F1, frozen)"),
            "old_behavior": "raw symbols containing '-' dropped (v2 outright filter)",
            "build_window": "2018-06-01..2021-01-31 (chain warmup from chunk start)",
            "frame": f"{FRAME_START}..{FRAME_END}",
            "front_rule": ("PIT volume-crossover k=5 (v2 code verbatim: "
                           "trailing-5-session mean volume, next quarterly vs "
                           "current, decided at close of t, held map from v2 "
                           "loop); unadjusted held closes (roll spreads "
                           "absorbed in switch-day returns, v2 convention)"),
            "session_convention": ("America/Chicago; session D = 17:00 CT D-1 "
                                   "-> 16:00 CT D (era-B); maintenance break "
                                   "bars dropped; DST wall-clock via tz_convert"),
            "v2_reference": "NQ_a1_regimes.json + NQ_cache (read-only)",
        },
        "integrity": integ,
        "extras": extras,
        "held_map_agreement_old_vs_v2cache": held_agree,
        "v2_reference_numbers": v2_ref,
        "remeasured": agg,
        "front_verification": verify,
        "reconciliation_notes": recon_notes,
    }
    with open(OUT_JSON, "w") as fh:
        json.dump(_san(out), fh, indent=1, default=str, allow_nan=False)

    # ---- console summary ----
    print("\n=== 2020 aggregates: v2 (dossier) vs OLD' repro vs NEW recovered ===")
    yv, yo, yn = v2_ref["yearly_2020"], agg["old"]["yearly_2020"], agg["new"]["yearly_2020"]
    rows = [
        ("sessions with data", f"{yv['n_sessions']-int(v2_ref['yearly_2020']['depleted_sessions'])}+depl",
         f"{yo['n_data_sessions']}", f"{yn['n_data_sessions']}"),
        ("yearly log ret %", f"{yv['ret_pct']:.2f}", f"{yo['ret_pct']:.2f}", f"{yn['ret_pct']:.2f}"),
        ("ann vol %", f"{yv['vol_ann_pct']:.2f}", f"{yo['vol_ann_pct']:.2f}", f"{yn['vol_ann_pct']:.2f}"),
        ("worst day %", f"{yv['worst_day_pct']:.2f}",
         f"{yo['worst_day_pct']:.2f} @{yo['worst_day_date']}",
         f"{yn['worst_day_pct']:.2f} @{yn['worst_day_date']}"),
        ("best day %", f"{yv['best_day_pct']:.2f}",
         f"{yo['best_day_pct']:.2f} @{yo['best_day_date']}",
         f"{yn['best_day_pct']:.2f} @{yn['best_day_date']}"),
        ("max DD %", f"{yv['max_dd_pct']:.2f}", f"{yo['max_dd_pct']:.2f}", f"{yn['max_dd_pct']:.2f}"),
    ]
    for r in rows:
        print(f"  {r[0]:22s} {r[1]:>18s} {r[2]:>22s} {r[3]:>22s}")
    cv = v2_ref["covid_episode"]
    co, cn = agg["old"]["covid"], agg["new"]["covid"]
    print(f"  COVID: v2 {cv['start']}->{cv['trough']}->{cv['end']} "
          f"{cv['depth_pct']:.2f}% fall {cv['peak_to_trough_sessions']} rec {cv['recovery_sessions']}")
    print(f"  COVID OLD' {co}")
    print(f"  COVID NEW  {cn}")
    print(f"  rvol20: v2 max {100*rv20_v2['max']:.2f} @{rv20_v2['argmax_date']} | "
          f"OLD' {agg['old']['rvol']['rvol20']} | NEW {agg['new']['rvol']['rvol20']}")
    print(f"  rvol60: v2 max {100*rv60_v2['max']:.2f} @{rv60_v2['argmax_date']} | "
          f"OLD' {agg['old']['rvol']['rvol60']} | NEW {agg['new']['rvol']['rvol60']}")
    print("\nfront verification:", json.dumps(verify, indent=1, default=str))
    print("\nwrote", OUT_JSON)


if __name__ == "__main__":
    main()
