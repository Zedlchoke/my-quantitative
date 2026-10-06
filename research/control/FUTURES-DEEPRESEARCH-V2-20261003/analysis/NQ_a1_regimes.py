"""A1 — NQ regime map 2010-2026 (DEEP-NQ).

Held-contract daily series from the PIT volume-crossover rule (k=5, decided at
t-1 close, new contract held from t — no vendor stitching). Descriptive only:
rolling realized vol at multiple horizons, trend persistence (variance ratios,
autocorrelations), drawdown anatomy, strict-past regime labels, and where the
v1 window (2025-05-30+) sits inside the full-era distribution.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import NQ_deep_lib as L  # noqa: E402

OUT = os.path.join(L.HERE, "NQ_a1_regimes.json")


def held_daily(sess: pd.DataFrame, held: pd.DataFrame) -> pd.DataFrame:
    """Outer merge: sessions where the held contract has no bars (the
    2020-03-23..2020-05-29 vendor hole: only a deferred-contract trickle
    exists) keep NaN closes so diff() yields NaN, never a synthetic jump."""
    m = sess.merge(held.rename(columns={"held": "contract"}),
                   on=["session_date", "contract"], how="right")
    m = m.sort_values("session_date").reset_index(drop=True)
    m["d"] = pd.to_datetime(m["session_date"])
    m["log_close"] = np.log(m["close"].astype(float))
    m["ret"] = m["log_close"].diff()
    m["cov"] = m["rth_coverage"].clip(0, 1).fillna(0.0)
    m["depleted"] = (m["cov"] < 0.25) | m["close"].isna()
    return m


def main():
    sess = pd.read_parquet(os.path.join(L.CACHE, "nq_sessions.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))
    held_cal = pd.read_parquet(os.path.join(L.CACHE, "held_calendar.parquet"))
    d = held_daily(sess, held)
    dc = held_daily(sess, held_cal)

    r = d["ret"].dropna()
    res = {"schema": "NQ_a1_regimes@1",
           "panel": {"n_sessions": int(len(d)),
                     "first": str(d["d"].iloc[0].date()),
                     "last": str(d["d"].iloc[-1].date()),
                     "roll_rule": "PIT volume-crossover k=5, decide t-1, hold from t",
                     "n_rolls": int((held["held"] != held["held"].shift()).sum() - 1),
                     "depleted_sessions": int(d["depleted"].sum())}}

    # ---- multi-horizon realized vol (trailing, past-only windows) ----
    ann = 252.0
    volz = {}
    for w in (5, 10, 20, 60, 120, 252):
        v = d["ret"].rolling(w, min_periods=max(2, int(w * 0.75))).std() * np.sqrt(ann)
        volz[f"rvol_{w}d"] = v
    vdf = pd.DataFrame(volz)
    vol_summary = {}
    for c in vdf:
        s = vdf[c].dropna()
        vol_summary[c] = {
            "min": float(s.min()), "p5": float(s.quantile(.05)),
            "p25": float(s.quantile(.25)), "median": float(s.median()),
            "p75": float(s.quantile(.75)), "p95": float(s.quantile(.95)),
            "max": float(s.max()),
            "argmin_date": str(d["d"][s.idxmin()].date()),
            "argmax_date": str(d["d"][s.idxmax()].date()),
            "last": float(s.iloc[-1])}
    res["realized_vol_summary"] = vol_summary

    # vol-of-vol and vol clustering
    rv20 = vdf["rvol_20d"]
    res["vol_clustering"] = {
        "acf1_abs_ret_252d_median": float(
            d["ret"].abs().rolling(252).apply(
                lambda x: np.corrcoef(x[:-1], x[1:])[0, 1], raw=True)
            .dropna().median()),
        "vol20_of_vol20": float(rv20.diff().abs().rolling(252).median()
                                .dropna().median())}

    # ---- trend persistence ----
    def variance_ratio(ret: pd.Series, q: int) -> pd.Series:
        var1 = ret.rolling(252, min_periods=189).var()
        varq = ret.rolling(q, min_periods=q).sum().rolling(252, min_periods=189).var()
        return varq / (q * var1)

    vr = {f"vr_{q}": variance_ratio(d["ret"], q) for q in (5, 20, 60)}
    vrdf = pd.DataFrame(vr)
    res["trend_persistence"] = {
        "acf1_ret_full": float(r.autocorr(1)),
        "acf1_ret_rolling252_median": float(
            d["ret"].rolling(252).apply(
                lambda x: np.corrcoef(x[:-1], x[1:])[0, 1], raw=True)
            .dropna().median()),
        "acf1_ret_rolling252_p10_p90": [
            float(x) for x in d["ret"].rolling(252).apply(
                lambda x: np.corrcoef(x[:-1], x[1:])[0, 1], raw=True)
            .dropna().quantile([.1, .9])],
        "variance_ratios_full": {k: float(v.dropna().iloc[-252:].mean())
                                 for k, v in vrdf.items()},
        "variance_ratio_20_median": float(vrdf["vr_20"].dropna().median()),
        "variance_ratio_20_p10_p90": [float(x) for x in
                                      vrdf["vr_20"].dropna().quantile([.1, .9])]}

    # ---- drawdown anatomy ----
    d["cum"] = d["log_close"] - d["log_close"].iloc[0]
    d["peak"] = d["cum"].cummax()
    d["dd"] = d["cum"] - d["peak"]

    def drawdown_episodes(dd: pd.Series, min_depth: float = 0.10):
        eps = []
        in_dd = False
        start = None
        trough = None
        for i, (dt_, v) in enumerate(dd.items()):
            if not in_dd and v < -min_depth:
                in_dd, start, trough = True, i, i
            elif in_dd:
                if v < dd.iloc[trough]:
                    trough = i
                if v >= -1e-9:
                    eps.append((start, trough, i))
                    in_dd = False
        if in_dd:
            eps.append((start, trough, None))
        return eps

    eps = drawdown_episodes(d["dd"], 0.10)
    ep_list = []
    for s, t, e in eps:
        ep_list.append({
            "start": str(d["d"].iloc[s].date()),
            "trough": str(d["d"].iloc[t].date()),
            "end": (str(d["d"].iloc[e].date()) if e is not None else "unrecovered"),
            "depth_pct": float(-100 * d["dd"].iloc[t]),
            "peak_to_trough_sessions": int(t - s),
            "recovery_sessions": (int(e - t) if e is not None else None),
            "trough_is_depleted_window": bool(d["depleted"].iloc[t])})
    ep_list.sort(key=lambda x: -x["depth_pct"])
    res["drawdowns_ge10pct"] = ep_list

    # per-year anatomy
    d["year"] = d["d"].dt.year
    yearly = []
    for y, g in d.groupby("year"):
        rr = g["ret"].dropna()
        cum = g.set_index("d")["cum"]
        dd_y = (cum - cum.cummax())
        yearly.append({
            "year": int(y), "n_sessions": int(len(g)),
            "ret_pct": float(100 * g["ret"].sum()),
            "vol_ann_pct": float(100 * rr.std() * np.sqrt(252)) if len(rr) > 2 else None,
            "skew": float(rr.skew()) if len(rr) > 10 else None,
            "ex_kurt": float(rr.kurt()) if len(rr) > 10 else None,
            "up_days_pct": float(100 * (rr > 0).mean()),
            "worst_day_pct": float(100 * rr.min()), "best_day_pct": float(100 * rr.max()),
            "max_dd_pct": float(-100 * dd_y.min()) if len(dd_y) else None,
            "avg_daily_vol_contracts": float(g["volume"].mean()),
            "median_true_range_pts": float(g["true_range"].median()),
            "depleted_sessions": int(g["depleted"].sum()),
            "med_rvol20": float((g["ret"].rolling(20, min_periods=15).std() * np.sqrt(252)).median()),
        })
    res["yearly"] = yearly

    # ---- strict-past regime labels ----
    # vol tercile: rvol60 vs its trailing-756d own distribution
    rv60 = vdf["rvol_60d"]
    def past_tercile(x):
        w = x.dropna()
        return np.nan if len(w) < 500 else (w.iloc[-1] -
                                            w.iloc[:-1].quantile(2/3) > 0) * 0 + \
               (1 if w.iloc[-1] <= w.iloc[:-1].quantile(1/3) else
                (2 if w.iloc[-1] <= w.iloc[:-1].quantile(2/3) else 3))
    lab_vol = []
    v60 = rv60.copy()
    win = 756
    for i in range(len(v60)):
        lo = max(0, i - win)
        seg = v60.iloc[lo:i + 1].dropna()
        if len(seg) < 300:
            lab_vol.append(None)
        else:
            hist = seg.iloc[:-1]
            q1, q2 = hist.quantile(1/3), hist.quantile(2/3)
            lab_vol.append(1 if seg.iloc[-1] <= q1 else
                           (2 if seg.iloc[-1] <= q2 else 3))
    d["regime_vol"] = lab_vol  # 1 low / 2 med / 3 high, strict-past terciles
    counts = pd.Series([x for x in lab_vol if x is not None]).value_counts()
    res["regime_vol_tercile_counts"] = {str(k): int(v) for k, v in counts.items()}
    ct = pd.crosstab(d["year"], d["regime_vol"])
    res["regime_vol_by_year"] = {str(int(y)): {str(int(k)): int(v) for k, v in
                                               row.items() if pd.notna(k)}
                                 for y, row in ct.iterrows()}

    # trend regime: trailing 120d |t-stat| of mean daily ret
    mu = d["ret"].rolling(120, min_periods=90).mean()
    se = d["ret"].rolling(120, min_periods=90).std() / np.sqrt(120)
    tstat = (mu / se).where(se > 0)
    d["trend_t"] = tstat
    d["regime_trend"] = np.where(tstat > 1, "trend_up",
                         np.where(tstat < -1, "trend_down", "range"))
    tr_counts = d["regime_trend"][d["regime_trend"].notna() &
                                  d["ret"].notna()].value_counts()
    res["regime_trend_counts"] = {k: int(v) for k, v in tr_counts.items()}
    ct2 = pd.crosstab(d["year"], d["regime_trend"])
    res["regime_trend_by_year"] = {str(int(y)): {k: int(v) for k, v in row.items()
                                                 if pd.notna(k)}
                                   for y, row in ct2.iterrows()}
    # joint: high-vol + trending share by year
    d["hi_vol"] = d["regime_vol"] == 3
    res["share_high_vol_by_year"] = {
        str(int(y)): float(g["hi_vol"].mean()) for y, g in d.groupby("year")}

    # ---- where does 2025-26 (and v1's window) sit? ----
    full = vdf["rvol_20d"].dropna()
    full_hist = full[full.index < d.index[d["d"] >= "2025-01-01"][0]]
    v1w = d["d"] >= pd.Timestamp("2025-05-30")
    v1_rvol = vdf["rvol_20d"][v1w].dropna()
    prior = d["d"] < pd.Timestamp("2025-01-01")
    prior_rvol = vdf["rvol_20d"][prior].dropna()
    res["v1_window_context"] = {
        "v1_window": "2025-05-30..2026-10-01 (true-front, v1 dossier W2)",
        "rvol20_median_v1window_pct": float(100 * v1_rvol.median()),
        "rvol20_median_2010_2024_pct": float(100 * prior_rvol.median()),
        "rvol20_percentile_of_v1window_median_within_2010_2024": float(
            (prior_rvol < v1_rvol.median()).mean()),
        "rvol20_p10_p90_2010_2024_pct": [float(100 * prior_rvol.quantile(.1)),
                                          float(100 * prior_rvol.quantile(.9))],
        "v1_rvol20_range_pct": [float(100 * v1_rvol.min()),
                                float(100 * v1_rvol.max())],
        "v1_window_max_dd_pct": float(-100 * d[d.index.isin(v1w[v1w].index)]
                                      ["dd"].min())}

    # calendar-rule sensitivity: same headline stats on calendar-rule series
    rc = dc["ret"].dropna()
    res["calendar_rule_sensitivity"] = {
        "vol_ann_pct": float(100 * rc.std() * np.sqrt(252)),
        "n_sessions": int(len(dc)),
        "note": "v1 rule; thin first ~2 weeks of each quarter"}

    # save rolling series for other analyses/dossier plots
    pd.DataFrame({
        "d": d["d"], "close": d["close"], "ret": d["ret"],
        "rvol20": vdf["rvol_20d"], "rvol60": vdf["rvol_60d"],
        "dd": d["dd"], "regime_vol": d["regime_vol"],
        "regime_trend": d["regime_trend"], "depleted": d["depleted"],
        "rth_coverage": d["cov"],
    }).to_parquet(os.path.join(L.CACHE, "nq_held_daily.parquet"), index=False)

    L.jdump(res, OUT)
    print("A1 complete ->", OUT)


if __name__ == "__main__":
    main()
