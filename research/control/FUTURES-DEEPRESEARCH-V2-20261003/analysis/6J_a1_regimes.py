"""A1 — 6J regime map 2020-2026 (DEEP-6J).

Held-contract daily series from the PIT volume-crossover rule (k=5, next HMUZ
quarterly; decided at t-1 close, new contract held from t — no vendor
stitching). Two return series:
  * ret_within — within-contract daily log returns (27 roll dates carry the NEW
    contract's within-contract return; NO roll-gap jump anywhere);
  * ret_rolled — consecutive held-contract closes INCLUDING the cross-contract
    carry gap on roll dates (economic PnL of a rolled position at close, no
    spread/cost; the gap is a real carry cost for longs).
Descriptive only: rolling realized vol, trend persistence, drawdown anatomy,
strict-past regime labels, v1-window context. Prices are USD-per-JPY; USDJPY
= 1/price (quote-orientation trap disclosed).
"""
from __future__ import annotations

import os
import sys

import importlib

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6J_deep_lib")

OUT = os.path.join(L.HERE, "6J_a1_regimes.json")


def held_daily(sess: pd.DataFrame, held: pd.DataFrame) -> pd.DataFrame:
    m = sess.merge(held.rename(columns={"held": "contract"}),
                   on=["session_date", "contract"], how="inner")
    m = m.sort_values("session_date").reset_index(drop=True)
    m["d"] = pd.to_datetime(m["session_date"])
    m["log_close"] = np.log(m["close"].astype(float))
    m["ret_rolled"] = m["log_close"].diff()
    # within-contract return: diff vs previous session ONLY if same contract
    prev_log = m.groupby("contract")["log_close"].shift(1)
    m["ret_within"] = m["log_close"] - prev_log
    m["is_roll"] = m["contract"] != m["contract"].shift()
    m["depleted"] = m["coverage"] < 0.25
    return m


def zigzag_legs(cum: pd.Series, dates: pd.Series, swing: float = 0.03):
    """Zigzag swing decomposition of the cumulative log series: pivots reverse
    after a >=swing move. Returns down-legs (peak->trough) and up-legs with
    depths/durations. Lets the 2021-2026 structural yen-weak path decompose
    into its intervention-bounce-separated legs (running-peak drawdown cannot:
    no post-2021 bounce returned within 2% of the 2020-03 peak)."""
    vals = cum.fillna(0).values  # first ret is NaN; anchor at 0
    piv = []  # (idx, kind)
    last_i = 0
    ext_i = 0  # index of pending extremum
    direction = 0  # 1 up-leg in progress, -1 down, 0 unset
    for i in range(1, len(vals)):
        if direction >= 0:
            if vals[i] > vals[ext_i]:
                ext_i = i
            elif vals[ext_i] - vals[i] >= swing:
                if direction == 1 or True:
                    piv.append((ext_i, "peak"))
                direction = -1
                ext_i = i
        if direction <= 0:
            if vals[i] < vals[ext_i]:
                ext_i = i
            elif vals[i] - vals[ext_i] >= swing:
                piv.append((ext_i, "trough"))
                direction = 1
                ext_i = i
    piv.append((ext_i, "trough" if direction == -1 else "peak"))
    legs = []
    for (i0, k0), (i1, k1) in zip(piv[:-1], piv[1:]):
        depth = float(100 * (vals[i1] - vals[i0]))
        legs.append({"kind": "down" if k0 == "peak" else "up",
                     "from": str(dates.iloc[i0].date()),
                     "to": str(dates.iloc[i1].date()),
                     "move_pct": depth, "sessions": int(i1 - i0)})
    return legs


def main():
    sess = pd.read_parquet(os.path.join(L.CACHE, "6j_sessions.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))
    held_cal = pd.read_parquet(os.path.join(L.CACHE, "held_calendar_q.parquet"))
    d = held_daily(sess, held)
    dc = held_daily(sess, held_cal)

    res = {"schema": "6J_a1_regimes@1",
           "panel": {
               "n_sessions": int(len(d)),
               "first": str(d["d"].iloc[0].date()), "last": str(d["d"].iloc[-1].date()),
               "roll_rule": "PIT volume-crossover k=5 over HMUZ chain, decide t-1 close, hold from t",
               "n_roll_dates": int(d["is_roll"].sum() - 1),
               "depleted_sessions": int(d["depleted"].sum()),
               "quote_note": "price = USD per JPY; USDJPY = 1/price; long 6J = long JPY"}}

    # ---- realized vol (multi-horizon, trailing past-only) ----
    ann = 252.0
    volz = {}
    for w in (5, 10, 21, 60, 126, 252):
        volz[f"rvol_{w}d"] = d["ret_within"].rolling(w, min_periods=max(2, int(w * .75))).std() * np.sqrt(ann)
    vdf = pd.DataFrame(volz)
    res["realized_vol_summary"] = {}
    for c in vdf:
        s = vdf[c].dropna()
        res["realized_vol_summary"][c] = {
            "min_pct": float(100 * s.min()), "p5_pct": float(100 * s.quantile(.05)),
            "median_pct": float(100 * s.median()), "p95_pct": float(100 * s.quantile(.95)),
            "max_pct": float(100 * s.max()),
            "argmax_date": str(d["d"][s.idxmax()].date()),
            "argmin_date": str(d["d"][s.idxmin()].date()),
            "last_pct": float(100 * s.iloc[-1])}

    # ---- trend persistence ----
    # ret_within has NaN on the 27 roll dates (first session of each contract):
    # for rolling-window stats those dates contribute 0 (disclosed; 27/1745).
    rf = d["ret_within"].fillna(0.0)
    r = d["ret_within"].dropna()
    vr = {}
    for q in (5, 20, 60):
        var1 = rf.rolling(252, min_periods=189).var()
        varq = rf.rolling(q, min_periods=q).sum().rolling(252, min_periods=189).var()
        vr[f"vr_{q}"] = varq / (q * var1)
    vrdf = pd.DataFrame(vr)
    sign50 = np.sign(rf.rolling(50, min_periods=40).mean())
    match = (np.sign(rf) == sign50) & sign50.notna() & rf.notna()
    res["trend_persistence"] = {
        "acf1_full": float(r.autocorr(1)), "acf2_full": float(r.autocorr(2)),
        "acf5_full": float(r.autocorr(5)),
        "acf1_rolling252_median": float(
            rf.rolling(252).apply(
                lambda x: np.corrcoef(x[:-1], x[1:])[0, 1], raw=True).dropna().median()),
        "acf1_rolling252_p10_p90": [float(x) for x in rf.rolling(252).apply(
            lambda x: np.corrcoef(x[:-1], x[1:])[0, 1], raw=True).dropna().quantile([.1, .9])],
        "variance_ratio_medians": {k: float(v.dropna().median()) for k, v in vrdf.items()},
        "vr20_p10_p90": [float(x) for x in vrdf["vr_20"].dropna().quantile([.1, .9])],
        "sign_match_trailing50d_share": float(match.mean()),
        "abs_ret_acf1": float(r.abs().autocorr(1)),
        "note": "rolling windows use ret_within.fillna(0) on the 27 roll dates"}

    # ---- drift / depreciation regime ----
    res["drift"] = {
        "mean_ret_within_bp_day": float(1e4 * r.mean()),
        "median_ret_within_bp_day": float(1e4 * r.median()),
        "up_days_pct": float(100 * (r > 0).mean()),
        "cum_ret_within_pct": float(100 * r.sum()),
        "cum_ret_rolled_pct": float(100 * d["ret_rolled"].sum()),
        "price_first": float(d["close"].iloc[0]), "price_last": float(d["close"].iloc[-1]),
        "usdjpy_implied_first": float(1 / d["close"].iloc[0]),
        "usdjpy_implied_last": float(1 / d["close"].iloc[-1]),
        "price_min": float(d["close"].min()), "price_min_date": str(d["d"][d["close"].idxmin()].date()),
        "price_max": float(d["close"].max()), "price_max_date": str(d["d"][d["close"].idxmax()].date()),
        "usdjpy_implied_max": float(1 / d["close"].min()),
        "usdjpy_implied_min": float(1 / d["close"].max())}

    # ---- drawdown anatomy (rolled economic series) ----
    d["cum"] = d["ret_rolled"].cumsum()
    d["peak"] = d["cum"].cummax()
    d["dd"] = d["cum"] - d["peak"]
    res["structural_note"] = {
        "single_peak_to_final_trough": {
            "peak_date": str(d["d"][d["cum"].idxmax()].date()),
            "trough_date": str(d["d"][d["dd"].idxmin()].date()),
            "depth_pct": float(-100 * d["dd"].min())},
        "note": "the 2021-2026 yen-weak super-cycle is ONE unrecovered drawdown "
                "from the 2020-03 running peak (no bounce returned within 2% of "
                "it); zigzag_legs below decomposes it at >=3% swings"}
    legs = zigzag_legs(d["cum"], d["d"], swing=0.03)
    down = [x for x in legs if x["kind"] == "down"]
    down.sort(key=lambda x: x["move_pct"])
    res["zigzag_down_legs_3pct"] = down
    res["zigzag_up_legs_3pct"] = sorted(
        [x for x in legs if x["kind"] == "up"], key=lambda x: -x["move_pct"])
    res["max_dd_rolled_pct"] = float(-100 * d["dd"].min())
    # within-window drawdowns (peak re-anchored inside each calendar year) are
    # in the yearly table as max_dd_pct

    # ---- yearly anatomy ----
    d["year"] = d["d"].dt.year
    yearly = []
    for y, g in d.groupby("year"):
        rr = g["ret_within"].dropna()
        cum = g.set_index(g.index)["cum"]
        dd_y = cum - cum.cummax()
        yearly.append({
            "year": int(y), "n_sessions": int(len(g)),
            "ret_within_pct": float(100 * rr.sum()),
            "ret_rolled_pct": float(100 * g["ret_rolled"].sum()),
            "roll_carry_drag_pct": float(100 * (g["ret_rolled"].sum() - rr.sum())),
            "vol_ann_pct": float(100 * rr.std() * np.sqrt(252)) if len(rr) > 2 else None,
            "skew": float(rr.skew()) if len(rr) > 10 else None,
            "ex_kurt": float(rr.kurt()) if len(rr) > 10 else None,
            "up_days_pct": float(100 * (rr > 0).mean()),
            "worst_day_pct": float(100 * rr.min()), "best_day_pct": float(100 * rr.max()),
            "worst_day_date": str(g["d"][rr.idxmin()].date()) if len(rr) else None,
            "best_day_date": str(g["d"][rr.idxmax()].date()) if len(rr) else None,
            "max_dd_pct": float(-100 * dd_y.min()),
            "avg_daily_vol_contracts": float(g["volume"].mean()),
            "med_true_range_bp": float(1e4 * (g["true_range"] / g["close"]).median()),
            "close_last": float(g["close"].iloc[-1]),
            "usdjpy_implied_close": float(1 / g["close"].iloc[-1])})
    res["yearly"] = yearly

    # ---- strict-past regime labels ----
    rv60 = vdf["rvol_60d"]
    lab = []
    for i in range(len(rv60)):
        seg = rv60.iloc[max(0, i - 756):i + 1].dropna()
        if len(seg) < 200:
            lab.append(None)
        else:
            hist = seg.iloc[:-1]
            q1, q2 = hist.quantile(1 / 3), hist.quantile(2 / 3)
            lab.append(1 if seg.iloc[-1] <= q1 else (2 if seg.iloc[-1] <= q2 else 3))
    d["regime_vol"] = lab
    counts = pd.Series([x for x in lab if x is not None]).value_counts()
    res["regime_vol_tercile_counts"] = {str(k): int(v) for k, v in counts.items()}
    ct = pd.crosstab(d["year"], d["regime_vol"])
    res["regime_vol_by_year"] = {str(int(y)): {str(int(k)): int(v) for k, v in row.items()
                                               if pd.notna(k)} for y, row in ct.iterrows()}

    mu = d["ret_within"].rolling(120, min_periods=90).mean()
    se = d["ret_within"].rolling(120, min_periods=90).std() / np.sqrt(120)
    tstat = (mu / se).where(se > 0)
    # price = USD/JPY: positive 6J return = JPY appreciation => trend_jpy_up
    d["regime_trend"] = np.where(tstat > 1, "trend_jpy_up",
                        np.where(tstat < -1, "trend_jpy_down", "range"))
    tr = d["regime_trend"][d["ret_within"].notna()]
    res["regime_trend_counts"] = {k: int(v) for k, v in
                                  pd.Series(tr).value_counts().items()}
    ct2 = pd.crosstab(d["year"], d["regime_trend"])
    res["regime_trend_by_year"] = {str(int(y)): {k: int(v) for k, v in row.items()
                                                 if pd.notna(k)} for y, row in ct2.iterrows()}

    # ---- v1 window context (v1 true-front era started 2025-05-20) ----
    v1w = d["d"] >= pd.Timestamp("2025-05-20")
    prior = d["d"] < pd.Timestamp("2025-01-01")
    cumw = d["ret_rolled"][v1w].cumsum()
    dd_v1 = cumw - cumw.cummax()
    res["v1_window_context"] = {
        "v1_window": "2025-05-20..2026-10-01",
        "rvol21_median_v1window_pct": float(100 * vdf["rvol_21d"][v1w].dropna().median()),
        "rvol21_median_2020_2024_pct": float(100 * vdf["rvol_21d"][prior].dropna().median()),
        "rvol21_pctile_of_v1window_median_in_2020_24": float(
            (vdf["rvol_21d"][prior].dropna() < vdf["rvol_21d"][v1w].dropna().median()).mean()),
        "v1_window_max_dd_rolled_pct_within_window": float(-100 * dd_v1.min())}

    # calendar-rule sensitivity
    rc = dc["ret_within"].dropna()
    res["calendar_rule_sensitivity"] = {
        "vol_ann_pct": float(100 * rc.std() * np.sqrt(252)),
        "n_sessions": int(len(dc)),
        "cum_ret_within_pct": float(100 * rc.sum()),
        "note": "v1-style roll at last session before delivery month; first ~1-2 weeks of each quarter on thinner new-front book"}

    pd.DataFrame({
        "d": d["d"], "close": d["close"], "ret_within": d["ret_within"],
        "ret_rolled": d["ret_rolled"], "rvol21": vdf["rvol_21d"],
        "rvol60": vdf["rvol_60d"], "dd": d["dd"], "regime_vol": d["regime_vol"],
        "regime_trend": d["regime_trend"], "volume": d["volume"],
        "coverage": d["coverage"], "contract": d["contract"],
    }).to_parquet(os.path.join(L.CACHE, "6j_held_daily.parquet"), index=False)

    L.jdump(res, OUT)
    print("A1 complete ->", OUT)


if __name__ == "__main__":
    main()
