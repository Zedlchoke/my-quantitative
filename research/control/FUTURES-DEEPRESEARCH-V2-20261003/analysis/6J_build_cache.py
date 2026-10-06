"""Build the 6J deep-research cache: contract registry + per-(contract,session)
panel + PIT held-contract maps. Lane DEEP-6J, FUTURES-DEEPRESEARCH-V2-20261003."""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib

L = importlib.import_module("6J_deep_lib")


def main():
    os.makedirs(L.CACHE, exist_ok=True)
    print("loading outright 1m panel ...", flush=True)
    df = L.load_outright_1m()
    print(f"rows={len(df):,} span {df['dt'].min()} .. {df['dt'].max()}")

    print("building contract registry ...", flush=True)
    reg = L.build_contract_registry(df)
    n_stray = int(reg["stray"].sum())
    n_q = int((~reg["stray"] & reg["symbol"].str.contains(r"[HMUZ]")).sum())
    n_serial = int((~reg["stray"] & ~reg["symbol"].str.contains(r"[HMUZ]")).sum())
    print(f"contracts={len(reg)} quarterly={n_q} serial={n_serial} stray={n_stray}")
    dup = reg.groupby("contract").size()
    if (dup > 1).any():
        print("WARN contract keys spanning multiple clusters:")
        print(dup[dup > 1].to_string())

    print("annotating panel ...", flush=True)
    df = L.annotate_panel(df, reg)
    n_break = int(df["in_break"].sum())
    n_wknd = int(df["weekend_anomaly"].sum())
    print(f"break bars={n_break} weekend-anomaly bars={n_wknd}")
    df = L.assign_center_windows(df)
    df = L.assign_ct_buckets(df)
    df = df.drop(columns=["_cluster"])
    df.to_parquet(os.path.join(L.CACHE, "6j_annotated_1m.parquet"), index=False)

    # ---- per-(contract, session) aggregates ----
    d = df[~df["in_break"]].copy()
    for c in ("open", "high", "low", "close"):
        d[c + "_px"] = d[c].astype(float) * L.PX_SCALE
    d["range_px"] = d["high_px"] - d["low_px"]
    g = d.groupby(["contract", "session_date"], sort=True)
    sess = g.agg(
        open=("open_px", "first"), high=("high_px", "max"), low=("low_px", "min"),
        close=("close_px", "last"), volume=("volume", "sum"), n_bars=("dt", "size"),
        first_smin=("session_min", "first"), last_smin=("session_min", "last"),
    ).reset_index()
    sess["coverage"] = sess["n_bars"] / L.SESSION_FULL_MIN
    # center-window volumes + ranges (overlap disclosed)
    for name in L.CENTER_WINDOWS:
        w = d[d[f"w_{name}"]]
        wv = w.groupby(["contract", "session_date"])["volume"].sum()
        wr = w.groupby(["contract", "session_date"])["range_px"].sum()
        mi = pd.MultiIndex.from_frame(sess[["contract", "session_date"]])
        sess[f"vol_{name}"] = wv.reindex(mi, fill_value=0).values
        sess[f"rng_{name}"] = wr.reindex(mi, fill_value=0.0).values
    # CT-bucket volumes (disjoint partition)
    for name, _a, _b in L.CT_BUCKETS[:-1]:
        w = d[d["ct_bucket"] == name]
        wv = w.groupby(["contract", "session_date"])["volume"].sum()
        mi = pd.MultiIndex.from_frame(sess[["contract", "session_date"]])
        sess[f"volb_{name}"] = wv.reindex(mi, fill_value=0).values
    sess = sess.sort_values(["contract", "session_date"]).reset_index(drop=True)
    sess["prev_close"] = sess.groupby("contract")["close"].shift(1)
    tr_hi = (sess["high"] - sess["prev_close"]).clip(lower=0)
    tr_lo = (sess["prev_close"] - sess["low"]).clip(lower=0)
    sess["true_range"] = pd.concat(
        [tr_hi, tr_lo, sess["high"] - sess["low"]], axis=1).max(axis=1)
    sess.to_parquet(os.path.join(L.CACHE, "6j_sessions.parquet"), index=False)
    print(f"session rows={len(sess):,} contracts={sess['contract'].nunique()}")

    print("held-contract maps ...", flush=True)
    held_vol = L.front_by_volume_crossover(sess, k=5)
    held_cal = L.front_by_calendar_quarterly(sess, reg)
    held_vol.to_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"), index=False)
    held_cal.to_parquet(os.path.join(L.CACHE, "held_calendar_q.parquet"), index=False)
    n_rolls_vol = int((held_vol["held"] != held_vol["held"].shift()).sum() - 1)
    print(f"volume-rule sessions={len(held_vol):,} rolls={n_rolls_vol} "
          f"calendar-rule sessions={len(held_cal):,}")

    reg_out = reg.copy()
    for c in ("first_bar", "last_bar"):
        reg_out[c] = reg_out[c].astype(str)
    reg_out.to_json(os.path.join(L.CACHE, "contract_registry.json"),
                    orient="records", indent=1)
    print("cache complete")


if __name__ == "__main__":
    main()
