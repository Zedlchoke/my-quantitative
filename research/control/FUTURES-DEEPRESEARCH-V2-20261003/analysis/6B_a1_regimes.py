"""6B v2 a1 — strict-past regime map 2020-2026: vol regimes, trend
persistence, drawdown anatomy incl. the 2022 GBP turmoil. OBSERVED only;
no PnL, no signal selection. Emits 6B_a1_regimes.json."""
from __future__ import annotations

import importlib.util
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "six_b_deep_lib", os.path.join(HERE, "6B_deep_lib.py"))
lib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lib)

OUT = {}

sess = pd.read_parquet(os.path.join(lib.CACHE, "6b_sessions.parquet"))
held_cal = pd.read_parquet(os.path.join(lib.CACHE, "held_calendar.parquet"))
held_vol = pd.read_parquet(os.path.join(lib.CACHE, "held_volume_crossover.parquet"))


def chain(held):
    m = sess.merge(held, on="session_date")
    m = m[m["contract"] == m["held"]].copy()
    m["d"] = pd.to_datetime(m["session_date"])
    m = m.sort_values("d").reset_index(drop=True)
    m["ret"] = m["close"].pct_change()
    m.loc[m["held"] != m["held"].shift(), "ret"] = np.nan  # roll boundary
    # drop the truncated final session (fetch cut inside the session)
    full = m["n_bars"] >= 600
    m.loc[~full, "ret"] = np.nan
    return m


cal = chain(held_cal)
vol = chain(held_vol)
cal.to_parquet(os.path.join(lib.CACHE, "chain_calendar.parquet"), index=False)
vol.to_parquet(os.path.join(lib.CACHE, "chain_volume.parquet"), index=False)

r = cal["ret"].dropna()
OUT["chain_calendar"] = {
    "n_days": int(len(r)),
    "span": [str(cal["d"].min().date()), str(cal["d"].max().date())],
    "mean": float(r.mean()), "std": float(r.std()),
    "ann_vol_pct": float(r.std() * np.sqrt(252) * 100),
    "skew": float(r.skew()), "kurt": float(r.kurt()),
    "q05": float(r.quantile(.05)), "q95": float(r.quantile(.95)),
    "min": float(r.min()), "max": float(r.max()),
}

# ---- by-year stats (era drift) ------------------------------------------------
by_year = {}
for y, g in cal.dropna(subset=["ret"]).groupby(cal["d"].dt.year):
    rr = g["ret"]
    by_year[int(y)] = {
        "n": int(len(rr)), "std_pct": float(rr.std() * 100),
        "ann_vol_pct": float(rr.std() * np.sqrt(252) * 100),
        "skew": float(rr.skew()), "min_pct": float(rr.min() * 100),
        "max_pct": float(rr.max() * 100),
        "mean_vol_contracts": float(g["volume"].mean()),
        "q95_absret_pct": float(rr.abs().quantile(.95) * 100),
    }
OUT["by_year"] = by_year

# ---- rolling 63d realized vol (strict past window ends each day) --------------
# min_periods=40 (not 63): roll-boundary NaNs (27) + thin-post-roll sessions
#    # would otherwise leave only ~5 all-clean windows in 6.8y (pandas
#    # rolling requires min_periods NON-NaN values; default = window)
cal["rv63"] = cal["ret"].rolling(63, min_periods=40).std() * np.sqrt(252) * 100
rv = cal[["d", "rv63"]].dropna()
OUT["rv63"] = {
    "min": float(rv["rv63"].min()), "q25": float(rv["rv63"].quantile(.25)),
    "median": float(rv["rv63"].median()), "q75": float(rv["rv63"].quantile(.75)),
    "max": float(rv["rv63"].max()),
    "argmax_date": str(rv.loc[rv["rv63"].idxmax(), "d"].date()),
    "argmin_date": str(rv.loc[rv["rv63"].idxmin(), "d"].date()),
}
# top-8 stress episodes (local maxima windows of rv63)
top = rv.nlargest(8, "rv63")
OUT["rv63_top8"] = [{"date": str(t.d.date()), "rv63_pct": float(t.rv63)}
                    for t in top.itertuples()]

# vol regime labels: trailing-1y tercile of rv63 (strict past)
cal["rv63_pctl_1y"] = cal["rv63"].rolling(252, min_periods=126).rank(pct=True)
lab = pd.cut(cal["rv63_pctl_1y"], [-.01, 1/3, 2/3, 1.01],
             labels=["low", "mid", "high"])
cal["vol_regime"] = lab.astype(str).where(cal["rv63_pctl_1y"].notna(), None)
reg_share = cal.groupby(cal["d"].dt.year)["vol_regime"].value_counts(normalize=True)
OUT["vol_regime_share_by_year"] = {
    str(y): {str(k): float(v) for k, v in s.items()}
    for y, s in reg_share.groupby(level=0)}

# ---- trend persistence ---------------------------------------------------------
pers = {}
rr = cal["ret"].dropna()
pers["ret_ac1..10"] = {f"lag{i}": float(rr.autocorr(i)) for i in range(1, 11)}
pers["absret_ac1..5"] = {f"lag{i}": float(rr.abs().autocorr(i)) for i in range(1, 6)}
# variance ratios VR(q) = Var(q-day)/ (q Var(1d)), drift-adjusted per Lo-MacKinlay
def vr(x, q):
    x = x.dropna().values
    mu = x.mean()
    n = len(x) // q * q
    xs = x[:n].reshape(-1, q).sum(axis=1)
    var1 = np.var(x, ddof=1)
    varq = np.var(xs - q * mu, ddof=1)
    return float(varq / (q * var1))
pers["variance_ratio"] = {f"q{q}": vr(rr, q) for q in (2, 5, 10, 21, 63)}
pers_by_year = {}
for y, g in cal.dropna(subset=["ret"]).groupby(cal["d"].dt.year):
    pers_by_year[int(y)] = {
        "ac1": float(g["ret"].autocorr(1)),
        "ac5": float(g["ret"].autocorr(5)),
        "absret_ac1": float(g["ret"].abs().autocorr(1)),
        "vr5": vr(g["ret"], 5), "vr21": vr(g["ret"], 21),
    }
pers["by_year"] = pers_by_year
OUT["persistence"] = pers

# ---- drawdown anatomy (roll-gap-excluded cumulative index) ---------------------
c = cal.dropna(subset=["ret"]).reset_index(drop=True)
c["cum"] = (1 + c["ret"]).cumprod()
c["peak"] = c["cum"].cummax()
c["dd"] = c["cum"] / c["peak"] - 1
OUT["max_drawdown"] = float(c["dd"].min())
OUT["max_drawdown_date"] = str(c.loc[c["dd"].idxmin(), "d"].date())
# top drawdown episodes: distinct troughs below -3%
eps, cur = [], None
for t in c.itertuples():
    if t.dd < -0.03:
        if cur is None:
            cur = {"start": t.d, "trough": t.d, "depth": float(t.dd), "peak_before": float(t.peak)}
        elif t.dd < cur["depth"]:
            cur["trough"], cur["depth"] = t.d, float(t.dd)
    else:
        if cur is not None and cur["depth"] < -0.03:
            cur["end"] = t.d
            cur["recovered_to"] = float(t.cum)
            eps.append(cur)
        cur = None
if cur is not None and cur["depth"] < -0.03:
    cur["end"] = None  # still open at data end
    eps.append(cur)
OUT["drawdown_episodes_below_3pct"] = [
    {"start": str(e["start"].date()), "trough": str(e["trough"].date()),
     "end": str(e.get("end").date()) if e.get("end") else None,
     "depth_pct": round(e["depth"] * 100, 2), "peak_before": round(e["peak_before"], 4)}
    for e in eps]

# ---- 2022 GBP turmoil day anatomy (mini-budget era, settlement-free) ----------
tur = cal[(cal["d"] >= "2022-08-25") & (cal["d"] <= "2022-10-21")]
turmo = []
for t in tur.itertuples():
    turmo.append({
        "date": str(t.d.date()), "close": float(t.close),
        "ret_pct": None if pd.isna(t.ret) else round(float(t.ret) * 100, 3),
        "range_pct": round(float((t.high - t.low) / t.close) * 100, 3),
        "low": float(t.low), "volume": int(t.volume),
        "held": t.held,
    })
OUT["turmoil_2022_daily"] = turmo
seg = tur.dropna(subset=["ret"])
OUT["turmoil_2022_summary"] = {
    "n_days": int(len(seg)),
    "cum_ret_pct": float(((1 + seg["ret"]).prod() - 1) * 100),
    "ann_vol_pct": float(seg["ret"].std() * np.sqrt(252) * 100),
    "worst_day_pct": float(seg["ret"].min() * 100),
    "worst_day_date": str(seg.loc[seg["ret"].idxmin(), "d"].date()),
    "best_day_pct": float(seg["ret"].max() * 100),
    "best_day_date": str(seg.loc[seg["ret"].idxmax(), "d"].date()),
    "max_volume_day": str(tur.loc[tur["volume"].idxmax(), "d"].date()),
    "max_volume": int(tur["volume"].max()),
    "min_low": float(tur["low"].min()),
    "min_low_date": str(tur.loc[tur["low"].idxmin(), "d"].date()),
}

# pre-turmoil peak to trough
pre = cal[cal["d"] <= "2022-09-22"]
peak_close = float(pre["close"].max())
peak_date = str(pre.loc[pre["close"].idxmax(), "d"].date())
trough = cal[(cal["d"] >= "2022-09-23") & (cal["d"] <= "2022-10-01")]
tr_date = str(trough.loc[trough["low"].idxmin(), "d"].date())
OUT["turmoil_peak_to_trough"] = {
    "peak_close": peak_close, "peak_date": peak_date,
    "min_low": float(trough["low"].min()), "min_low_date": tr_date,
    "close_to_close_drop_pct": float(
        (trough["close"].min() / peak_close - 1) * 100),
}

# ---- volume-rule chain robustness ---------------------------------------------
rv2 = vol.dropna(subset=["ret"])
OUT["chain_volume_rule"] = {
    "n_days": int(len(rv2)),
    "ann_vol_pct": float(rv2["ret"].std() * np.sqrt(252) * 100),
    "corr_daily_rets_vs_calendar": float(
        cal.set_index("d")["ret"].corr(vol.set_index("d")["ret"])),
}

lib.jdump(OUT, os.path.join(HERE, "6B_a1_regimes.json"))
print("a1 done:", OUT["rv63"], "| maxDD", OUT["max_drawdown"], OUT["max_drawdown_date"])
