"""Build the 6E deep-research cache: outright panel annotation, contract
registry (expiry-rule validation), per-(contract,session) table, PIT
held-contract maps (declared calendar / expiry-week / volume crossover).
Lane DEEP-6E, FUTURES-DEEPRESEARCH-V2-20261003."""
from __future__ import annotations

import importlib
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6E_deep_lib")  # digit-leading module name

def main():
    os.makedirs(L.CACHE, exist_ok=True)
    print("loading outright 1m panel ...", flush=True)
    df = L.load_outright_1m()
    print(f"rows={len(df):,} span {df['dt'].min()} .. {df['dt'].max()}")

    print("annotating panel ...", flush=True)
    df = L.annotate_panel(df)
    n_break = int(df["in_break"].sum())
    n_wknd = int(df["weekend_anomaly"].sum())
    n_mism = int(df["dst_mismatch"].sum())
    print(f"break bars={n_break} weekend-anomaly bars={n_wknd} "
          f"dst-mismatch bars={n_mism}")
    df.to_parquet(os.path.join(L.CACHE, "6e_annotated_1m.parquet"), index=False)

    print("contract registry ...", flush=True)
    reg = L.build_contract_registry(df)
    # validate expiry rule vs last observed session for EXPIRED contracts
    chk = reg[reg["expired"]].copy()
    chk["rule_minus_obs_days"] = (
        pd.to_datetime(chk["expiry_rule"]) - pd.to_datetime(chk["expiry_obs"])).dt.days
    n_ok = int((chk["rule_minus_obs_days"] == 0).sum())
    print(f"expiry rule vs observed last session (expired contracts): "
          f"{n_ok}/{len(chk)} exact; residuals disclosed in expiry_rule_check.json")
    out_chk = chk[["symbol", "quarterly", "expiry_rule", "expiry_obs",
                   "rule_minus_obs_days"]]
    for c in ("first_bar", "last_bar"):
        reg[c] = reg[c].astype(str)
    reg.to_json(os.path.join(L.CACHE, "contract_registry.json"),
                orient="records", indent=1)
    out_chk.to_json(os.path.join(L.CACHE, "expiry_rule_check.json"),
                    orient="records", indent=1)

    print("session table (vectorized) ...", flush=True)
    d2 = df[~df["in_break"]].copy()
    d2 = d2.sort_values(["raw_symbol", "dt"]).reset_index(drop=True)
    # map symbol -> contract key via registry (unique per symbol in this window)
    sym2c = reg.set_index("symbol")["contract"].to_dict()
    d2["contract"] = d2["raw_symbol"].map(sym2c)
    if d2["contract"].isna().any():
        raise ValueError("unmapped symbols")
    # within-(contract, session, segment) 1m log returns for realized-variance
    # decomposition; NaN at segment/session boundaries and gaps > 2 minutes.
    d2["prev_close_px"] = d2.groupby("contract")["close_px"].shift(1)
    d2["prev_session"] = d2.groupby("contract")["session_date"].shift(1)
    d2["prev_segment"] = d2.groupby("contract")["segment"].shift(1)
    d2["prev_dt"] = d2.groupby("contract")["dt"].shift(1)
    d2["logret1m"] = np.log(d2["close_px"] / d2["prev_close_px"])
    _ok = ((d2["session_date"] == d2["prev_session"])
           & (d2["segment"] == d2["prev_segment"])
           & ((d2["dt"] - d2["prev_dt"]).dt.total_seconds() <= 120))
    d2.loc[~_ok, "logret1m"] = np.nan
    g = d2.groupby(["contract", "session_date"], sort=True)
    sess = g.agg(
        open=("open_px", "first"), high=("high_px", "max"),
        low=("low_px", "min"), close=("close_px", "last"),
        volume=("volume", "sum"), n_bars=("dt", "size"),
        first_min=("minute_of_day", "first"), last_min=("minute_of_day", "last"),
    ).reset_index()
    liq = d2[d2["in_rth_liquid"]]
    lg = liq.groupby(["contract", "session_date"], sort=True)
    liq_agg = lg.agg(rthliq_volume=("volume", "sum"),
                     rthliq_bars=("dt", "size")).reset_index()
    sess = sess.merge(liq_agg, on=["contract", "session_date"], how="left")
    segv = d2.groupby(["contract", "session_date", "segment"], sort=True)[
        "volume"].sum().unstack(fill_value=0)
    # per-segment close for gap decomposition (last close in segment)
    segc = d2.groupby(["contract", "session_date", "segment"], sort=True)[
        "close_px"].last().unstack()
    segr = d2.groupby(["contract", "session_date", "segment"], sort=True).agg(
        hi=("high_px", "max"), lo=("low_px", "min"))
    segr_range = (segr["hi"] - segr["lo"]).unstack()
    mi = pd.MultiIndex.from_frame(sess[["contract", "session_date"]])
    segv = segv.reindex(mi, fill_value=0)
    segc = segc.reindex(mi)
    segr_range = segr_range.reindex(mi)
    for name, _a, _b in L.SEGMENTS:
        sess[f"vol_{name}"] = segv[name].values if name in segv.columns else 0
        sess[f"close_{name}"] = segc[name].values if name in segc.columns else np.nan
        sess[f"rng_{name}"] = (segr_range[name].values
                               if name in segr_range.columns else np.nan)
    # realized variance per segment: sum of squared 1m log rets within segment
    rv = d2.groupby(["contract", "session_date", "segment"])["logret1m"].apply(
        lambda s: float(np.nansum(np.square(s.to_numpy())))).unstack()
    rv = rv.reindex(mi)
    for name, _a, _b in L.SEGMENTS:
        sess[f"rv_{name}"] = rv[name].values if name in rv.columns else np.nan
    sess = sess.sort_values(["contract", "session_date"]).reset_index(drop=True)
    sess["prev_close"] = sess.groupby("contract")["close"].shift(1)
    tr_hi = (sess["high"] - sess["prev_close"]).clip(lower=0)
    tr_lo = (sess["prev_close"] - sess["low"]).clip(lower=0)
    sess["true_range"] = pd.concat(
        [tr_hi, tr_lo, sess["high"] - sess["low"]], axis=1).max(axis=1)
    sess["rthliq_coverage"] = sess["rthliq_bars"].fillna(0) / L.RTH_MIN
    sess.to_parquet(os.path.join(L.CACHE, "6e_sessions.parquet"), index=False)
    print(f"session rows={len(sess):,} contracts={sess['contract'].nunique()}")

    print("held-contract maps ...", flush=True)
    held_cal = L.front_by_calendar(sess, reg)
    held_expwk = L.front_by_expiry_week(sess, reg, t_minus=2)
    held_vol = L.front_by_volume_crossover(sess, k=5)
    held_cal.to_parquet(os.path.join(L.CACHE, "held_calendar.parquet"), index=False)
    held_expwk.to_parquet(os.path.join(L.CACHE, "held_expiry_week.parquet"), index=False)
    held_vol.to_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"), index=False)
    print(f"calendar={len(held_cal):,} expiry_week={len(held_expwk):,} "
          f"volume={len(held_vol):,}")
    print("cache complete")


if __name__ == "__main__":
    main()
