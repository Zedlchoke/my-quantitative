"""Build the NQ deep-research cache: contract registry + per-(contract,session)
panel + PIT held-contract maps. Lane DEEP-NQ, FUTURES-DEEPRESEARCH-V2-20261003."""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import NQ_deep_lib as L  # noqa: E402


def main():
    os.makedirs(L.CACHE, exist_ok=True)
    print("loading outright 1m panel ...", flush=True)
    df = L.load_outright_1m()
    print(f"rows={len(df):,} span {df['dt'].min()} .. {df['dt'].max()}")

    print("building contract registry ...", flush=True)
    reg = L.build_contract_registry(df)
    print(f"contracts={len(reg)}")
    multi = reg.groupby("contract").size()
    if (multi > 1).any():
        print("contract keys spanning multiple clusters (stray splits):")
        print(multi[multi > 1].to_string())

    print("annotating panel ...", flush=True)
    df = L.annotate_panel(df, reg)
    n_break = int(df["in_break"].sum())
    n_wknd = int(df["weekend_anomaly"].sum())
    print(f"break bars={n_break} weekend-anomaly bars={n_wknd}")

    print("session table (vectorized) ...", flush=True)
    df.to_parquet(os.path.join(L.CACHE, "nq_annotated_1m.parquet"), index=False)
    df = df[~df["in_break"]].copy()  # maintenance-break bars: none expected; counted above
    df = df.sort_values(["contract", "dt"]).reset_index(drop=True)
    g = df.groupby(["contract", "session_date"], sort=True)
    sess = g.agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), volume=("volume", "sum"), n_bars=("dt", "size"),
        first_min=("minute_of_day", "first"), last_min=("minute_of_day", "last"),
    ).reset_index()
    rth = df[df["in_rth"]]
    rg = rth.groupby(["contract", "session_date"], sort=True)
    rth_agg = rg.agg(
        rth_volume=("volume", "sum"), rth_bars=("dt", "size"),
        rth_first_min=("minute_of_day", "first"),
        rth_last_min=("minute_of_day", "last")).reset_index()
    sess = sess.merge(rth_agg, on=["contract", "session_date"], how="left")
    rthx = df[df["in_rth_ext"]]
    xg = rthx.groupby(["contract", "session_date"], sort=True)
    xagg = xg.agg(rthx_volume=("volume", "sum"),
                  rthx_bars=("dt", "size")).reset_index()
    sess = sess.merge(xagg, on=["contract", "session_date"], how="left")
    segv = df.groupby(["contract", "session_date", "segment"], sort=True)[
        "volume"].sum().unstack(fill_value=0)
    segr = df.groupby(["contract", "session_date", "segment"], sort=True).agg(
        hi=("high", "max"), lo=("low", "min"))
    segr_range = (segr["hi"] - segr["lo"]).unstack()
    mi = pd.MultiIndex.from_frame(sess[["contract", "session_date"]])
    segv = segv.reindex(mi, fill_value=0)
    segr_range = segr_range.reindex(mi)
    for name, _a, _b in L.SEGMENTS:
        sess[f"vol_{name}"] = segv[name].values if name in segv.columns else 0
        if name in segr_range.columns:
            sess[f"rng_{name}"] = segr_range[name].values
        else:
            sess[f"rng_{name}"] = np.nan
    sess = sess.sort_values(["contract", "session_date"]).reset_index(drop=True)
    sess["prev_close"] = sess.groupby("contract")["close"].shift(1)
    tr_hi = (sess["high"] - sess["prev_close"]).clip(lower=0)
    tr_lo = (sess["prev_close"] - sess["low"]).clip(lower=0)
    sess["true_range"] = pd.concat(
        [tr_hi, tr_lo, sess["high"] - sess["low"]], axis=1).max(axis=1)
    # coverage vs expected minutes
    sess["rth_coverage"] = sess["rth_bars"].fillna(0) / L.RTH_MIN
    sess.to_parquet(os.path.join(L.CACHE, "nq_sessions.parquet"), index=False)
    print(f"session rows={len(sess):,} contracts={sess['contract'].nunique()}")

    print("held-contract maps ...", flush=True)
    held_vol = L.front_by_volume_crossover(sess, k=5)
    held_cal = L.front_by_calendar(sess, reg)
    held_vol.to_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"), index=False)
    held_cal.to_parquet(os.path.join(L.CACHE, "held_calendar.parquet"), index=False)
    print(f"volume-rule sessions={len(held_vol):,} "
          f"calendar-rule sessions={len(held_cal):,}")

    # registry json (with cluster strays disclosed)
    reg_out = reg.copy()
    reg_out["first_bar"] = reg_out["first_bar"].astype(str)
    reg_out["last_bar"] = reg_out["last_bar"].astype(str)
    reg_out["expiry_ts"] = reg_out["expiry_ts"].astype(str)
    reg_out.to_json(os.path.join(L.CACHE, "contract_registry.json"),
                    orient="records", indent=1)
    print("cache complete")


if __name__ == "__main__":
    main()
