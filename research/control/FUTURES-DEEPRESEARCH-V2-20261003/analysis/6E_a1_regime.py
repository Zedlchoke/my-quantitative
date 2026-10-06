"""A1 — 6E regime map 2020-2026 (DEEP-6E).

Gap-free daily stats from the PIT calendar-rule quarterly chain (within-
contract returns only — no roll gaps), multi-horizon volatility incl the
2022 EUR crisis, trend persistence, drawdown anatomy on the ratio-adjusted
level, and where v1's 13.5-month window sits in the fuller distribution.
Descriptive only: no PnL, no selection; thresholds strict-past/rolling.
"""
from __future__ import annotations

import importlib
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6E_deep_lib")

OUT = os.path.join(L.HERE, "6E_a1_regimes.json")


def main():
    res = {"schema": "6E_a1_regimes@1",
           "window": "2020-01-02..2026-09-30",
           "chain_rule": "quarterly-only, declared calendar roll "
                         "(last session before delivery-month day 1)"}
    sess = pd.read_parquet(os.path.join(L.CACHE, "6e_sessions.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_calendar.parquet"))
    held = held.rename(columns={"held": "held_cal"})

    closes = sess.pivot_table(index="session_date", columns="contract",
                              values="close")
    vols = sess.pivot_table(index="session_date", columns="contract",
                            values="volume")
    # long-form lookup: (session_date_str, contract) -> close, prev_close
    px = closes.stack().rename("close").reset_index()
    px["session_date"] = px["session_date"].astype(str)
    px["prev_close"] = px.groupby("contract")["close"].shift(1)
    lut = px.set_index(["session_date", "contract"])[["close", "prev_close"]]
    vv = vols.stack().rename("volume").reset_index()
    vv["session_date"] = vv["session_date"].astype(str)
    vlut = vv.set_index(["session_date", "contract"])["volume"]

    daily = held.copy()
    daily["session_date"] = daily["session_date"].astype(str)
    daily = daily.join(lut, on=["session_date", "held_cal"])
    daily = daily.join(vlut, on=["session_date", "held_cal"])
    daily.index = pd.to_datetime(daily["session_date"])
    daily = daily.sort_index()
    daily["ret"] = daily["close"] / daily["prev_close"] - 1.0
    daily["logret"] = np.log(daily["close"] / daily["prev_close"])
    n_ret = int(daily["ret"].notna().sum())
    res["n_sessions"] = int(len(daily))
    res["n_returns"] = n_ret

    r = daily["ret"].dropna()
    res["daily_ret"] = {
        "mean_bp": float(r.mean() * 1e4), "std_pct": float(r.std() * 100),
        "min_pct": float(r.min() * 100), "max_pct": float(r.max() * 100),
        "skew": float(r.skew()), "kurt": float(r.kurt()),
        "q05_pct": float(r.quantile(.05) * 100),
        "q95_pct": float(r.quantile(.95) * 100),
        "ann_vol_pct": float(r.std() * np.sqrt(252) * 100),
    }
    # top-10 |ret| days
    top = r.abs().sort_values(ascending=False).head(10)
    res["top10_abs_ret_days"] = {str(d.date()): float(v * 100)
                                 for d, v in top.items()}

    # ---- multi-horizon vol ----
    lr = daily["logret"].dropna()
    horizons = {"1d": 1, "5d": 5, "21d": 21, "63d": 63}
    mv = {}
    for name, h in horizons.items():
        agg = lr.rolling(h).sum()
        mv[name] = {"std_daily_units_pct": float(agg.std() * 100),
                    "ann_from_horizon_pct": float(
                        agg.std() * np.sqrt(252 / h) * 100)}
    res["multi_horizon_vol"] = mv
    roll63 = lr.rolling(63).std() * np.sqrt(252) * 100
    res["rolling63_ann_vol_pct"] = {
        "min": float(roll63.min()), "median": float(roll63.median()),
        "max": float(roll63.max()),
        "min_date": str(roll63.idxmin().date()), "max_date": str(roll63.idxmax().date()),
    }
    roll21 = lr.rolling(21).std() * np.sqrt(252) * 100
    res["rolling21_ann_vol_pct"] = {
        "min": float(roll21.min()), "median": float(roll21.median()),
        "max": float(roll21.max()),
        "min_date": str(roll21.idxmin().date()), "max_date": str(roll21.idxmax().date()),
    }

    # ---- annual regime table ----
    ann = []
    for y, g in daily.groupby(daily.index.year):
        rr = g["ret"].dropna()
        if len(rr) < 30:
            continue
        ann.append({
            "year": int(y), "n": int(len(rr)),
            "first_close": float(g["close"].dropna().iloc[0]),
            "last_close": float(g["close"].dropna().iloc[-1]),
            "drift_pct": float((g["close"].dropna().iloc[-1] /
                                g["close"].dropna().iloc[0] - 1) * 100),
            "ann_vol_pct": float(rr.std() * np.sqrt(252) * 100),
            "min_close": float(g["close"].min()), "max_close": float(g["close"].max()),
            "worst_day_pct": float(rr.min() * 100), "best_day_pct": float(rr.max() * 100),
            "median_front_volume": float(g["volume"].median()),
        })
    res["annual_table"] = ann

    # ---- trend persistence ----
    def vr(lr_series, q):
        a = lr_series.dropna().to_numpy()
        mu = a.mean()
        var1 = np.var(a - mu, ddof=1)
        agg = pd.Series(a - mu).rolling(q).sum().dropna().to_numpy()
        varq = np.var(agg, ddof=1)
        return varq / (q * var1)
    ac = {f"lag{k}": float(lr.autocorr(k)) for k in (1, 2, 3, 5, 10, 21)}
    res["trend_persistence"] = {
        "ret_autocorr": ac,
        "absret_autocorr_lag1": float(lr.abs().autocorr(1)),
        "absret_autocorr_lag5": float(lr.abs().autocorr(5)),
        "variance_ratio": {f"q{q}": float(vr(lr, q)) for q in (2, 5, 10, 21, 63)},
        "note": "VR<1 mean reversion at horizon q; VR>1 trend persistence",
    }

    # ---- drawdown anatomy on ratio-adjusted level ----
    level = (1 + daily["ret"].fillna(0)).cumprod()
    peak = level.cummax()
    dd = level / peak - 1
    res["max_drawdown_pct"] = float(dd.min() * 100)
    # top-5 drawdown episodes (local troughs with distinct recovery points)
    eps = []
    in_dd, start, trough, trough_val = False, None, None, 0.0
    prev = None
    for d, v in dd.items():
        if v < -0.005 and not in_dd:
            in_dd, start, trough, trough_val = True, prev or d, d, v
        elif in_dd and v < trough_val:
            trough, trough_val = d, v
        elif in_dd and v >= -1e-9:
            eps.append({"start": str(start.date()), "trough": str(trough.date()),
                        "recovered": str(d.date()),
                        "depth_pct": float(trough_val * 100),
                        "length_sessions": int(level.index.get_loc(d) - level.index.get_loc(start))})
            in_dd = False
        prev = d
    if in_dd:
        eps.append({"start": str(start.date()), "trough": str(trough.date()),
                    "recovered": None, "depth_pct": float(trough_val * 100),
                    "length_sessions": int(level.index.get_loc(trough) - level.index.get_loc(start))})
    eps = sorted(eps, key=lambda e: e["depth_pct"])[:8]
    res["top_drawdowns"] = eps

    # ---- v1-window placement ----
    # v1 front-scale era 2025-09-09..2026-10-01 (n=247) vs full-sample rolling
    # windows of the same length (strict-past placement percentile)
    win = daily.loc["2025-09-09":"2026-10-01", "ret"].dropna()
    n = len(win)
    vol_series = lr.rolling(n).std() * np.sqrt(252) * 100
    drift_series = lr.rolling(n).sum() * 100
    v1_vol = float(win.std() * np.sqrt(252) * 100)
    v1_drift = float((1 + win).prod() - 1) * 100
    res["v1_window_placement"] = {
        "window": "2025-09-09..2026-10-01", "n": n,
        "v1_ann_vol_pct": v1_vol,
        "v1_vol_percentile_in_2020_2026_rolling": float(
            (vol_series.dropna() <= v1_vol).mean() * 100),
        "v1_total_drift_pct": v1_drift,
        "v1_drift_percentile_in_2020_2026_rolling": float(
            (drift_series.dropna() <= v1_drift).mean() * 100),
        "full_sample_rolling_window_vol_pctiles": {
            "p05": float(vol_series.quantile(.05)), "p50": float(vol_series.quantile(.5)),
            "p95": float(vol_series.quantile(.95))},
    }

    # ---- 2022 EUR crisis sub-window descriptives ----
    crisis = daily.loc["2022-01-01":"2022-12-31", "ret"].dropna()
    pre = daily.loc["2021-01-01":"2021-12-31", "ret"].dropna()
    res["eur_crisis_2022"] = {
        "note": "USD-parity slide: energy shock + Fed-ECB differential",
        "ann_vol_2021_pct": float(pre.std() * np.sqrt(252) * 100),
        "ann_vol_2022_pct": float(crisis.std() * np.sqrt(252) * 100),
        "ratio": float(crisis.std() / pre.std()),
        "drift_2022_pct": float((daily.loc["2022-01-01": "2022-12-31", "close"].dropna().iloc[-1] /
                                 daily.loc["2022-01-01": "2022-12-31", "close"].dropna().iloc[0] - 1) * 100),
    }
    # vol-of-vol and regime sharpe-free descriptors
    res["vol_regime_share"] = {
        "pct_sessions_rolling63_below_7pct": float((roll63 < 7).mean() * 100),
        "pct_sessions_7_to_10pct": float(((roll63 >= 7) & (roll63 < 10)).mean() * 100),
        "pct_sessions_above_10pct": float((roll63 >= 10).mean() * 100),
        "pct_sessions_above_15pct": float((roll63 >= 15).mean() * 100),
    }
    L.jdump(res, OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
