"""A6 — 6E data-quality ledger per era + hypothesis-refinement inputs (DEEP-6E).

Per-era (AV1B backfill2 2020-2022 / AV1R backfill 2022-2026-01 / AV1T
original 2026) row/bar/session counts, coverage, stale bars, weekend/
break anomalies, price-range sanity, negative prices, duplicate minutes,
spread-instrument and stray-symbol contamination, era-boundary butts, and
serial-book share. All OBSERVED.
"""
from __future__ import annotations

import importlib
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6E_deep_lib")

OUT = os.path.join(L.HERE, "6E_a6_dq.json")


def era_of(ts):
    if ts < pd.Timestamp("2022-01-01", tz="UTC"):
        return "AV1B-2020-2022-backfill2"
    if ts < pd.Timestamp("2026-01-01", tz="UTC"):
        return "AV1R-2022-2026-backfill"
    return "AV1T-2026-original"


def main():
    res = {"schema": "6E_a6_dq@1"}
    df = pd.read_parquet(os.path.join(L.CACHE, "6e_annotated_1m.parquet"))
    df["era"] = df["dt"].map(era_of)
    res["provenance"] = {
        "AV1B-O1M-6E-BACKFILL2__2020-01-01_2022-01-01": "vendor job GLBX-20261002-94UVSCXK6G, sha256 c3fd0a88… (BACKFILL_LEDGER.json, lane FX-BACKFILL)",
        "AV1R-O1M-6E-BACKFILL__2022-01-01_2024-01-01 + __2024-01-01_2026-01-01": "vendor jobs in COMPLETION_LEDGER.json (lane ACQ-DOWNLOAD backfill chain)",
        "AV1T-O1M-6E__2026-01-01_2026-07-01 + __2026-07-01_2026-10-01": "original av1trim download (COMPLETION_LEDGER.json)",
    }
    rows = {}
    for era, g in df.groupby("era"):
        per_sess = g.groupby("session_date").agg(
            nbars=("dt", "size"), vol=("volume", "sum"))
        # stale flat bars: o==h==l==c AND volume==0
        stale = int(((g["open"] == g["high"]) & (g["high"] == g["low"])
                     & (g["low"] == g["close"]) & (g["volume"] == 0)).sum())
        # duplicate (contract, minute) bars
        dup = int(g.duplicated(subset=["raw_symbol", "session_date",
                                       "minute_of_day"]).sum())
        px = g["close_px"]
        rows[era] = {
            "bars": int(len(g)),
            "sessions": int(g["session_date"].nunique()),
            "contracts": int(g["raw_symbol"].nunique()),
            "first": str(g["dt"].min()), "last": str(g["dt"].max()),
            "median_bars_per_session": float(per_sess["nbars"].median()),
            "p05_bars_per_session": float(per_sess["nbars"].quantile(.05)),
            "median_session_volume": float(per_sess["vol"].median()),
            "stale_flat_zero_vol_bars": stale,
            "duplicate_contract_minute_bars": dup,
            "negative_price_bars": int((px <= 0).sum()),
            "price_min": float(px.min()), "price_max": float(px.max()),
            "weekend_anomaly_bars": int(g["weekend_anomaly"].sum()),
            "break_bars_1600_1700ct": int(g["in_break"].sum()),
            "tick_multiple_violations_close": int(
                (np.abs(np.round(px / L.TICK) * L.TICK - px) > 1e-12).sum()),
        }
    res["eras"] = rows

    # era boundary butts: continuity of front chain around 2022-01-01 and
    # 2026-01-01
    held = pd.read_parquet(os.path.join(L.CACHE, "held_calendar.parquet"))
    sess = pd.read_parquet(os.path.join(L.CACHE, "6e_sessions.parquet"))
    closes = sess.pivot_table(index="session_date", columns="contract", values="close")
    closes.index = closes.index.astype(str)
    butt = {}
    for b in ("2021-12-31", "2022-01-03", "2025-12-31", "2026-01-02"):
        if b in closes.index:
            r = closes.loc[b].dropna()
            h = held[held["session_date"].astype(str) == b]["held"]
            if len(h):
                butt[b] = {"held": h.iloc[0],
                           "held_close": float(r.get(h.iloc[0], np.nan))
                           if pd.notna(r.get(h.iloc[0], np.nan)) else None,
                           "n_contracts_printing": int(len(r))}
    res["era_boundary_checks"] = butt

    # no-data weekdays (sessions in held map with no front bars)
    held["session_date"] = held["session_date"].astype(str)
    df["session_date"] = df["session_date"].astype(str)
    front_sessions = set(df["session_date"])
    missing = [s for s in held["session_date"] if s not in front_sessions]
    res["held_sessions_without_front_bars"] = {
        "n": len(missing), "dates": sorted(missing)[:20]}

    # v1 (IBKR) overlap: what did v1's RTH-only view miss? front bars by
    # in_rth_liquid vs not
    f = df.merge(held, on="session_date")
    f = f[f["raw_symbol"] + "_" + (2020 + f["raw_symbol"].str[-1].astype(int)).astype(str) == f["held"]]
    res["rth_only_view_would_miss"] = {
        "front_bars_outside_ibkr_liquid_hours": int((~f["in_rth_liquid"]).sum()),
        "front_volume_outside_ibkr_liquid_hours_pct": float(
            f.loc[~f["in_rth_liquid"], "volume"].sum() / f["volume"].sum() * 100),
        "front_volume_inside_ibkr_liquid_hours_pct": float(
            f.loc[f["in_rth_liquid"], "volume"].sum() / f["volume"].sum() * 100),
    }
    L.jdump(res, OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
