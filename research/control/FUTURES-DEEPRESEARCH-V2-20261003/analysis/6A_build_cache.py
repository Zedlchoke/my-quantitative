#!/usr/bin/env python
"""Build the DEEP-6A caches — lane DEEP-6A, task FUTURES-DEEPRESEARCH-V2-20261003.

Read-only over the vendor parquet; writes only inside 6A_cache/:
  outright_1m.parquet        annotated outright 1m panel (contract keys, session
                             dates, CT-clock minute/segment, hub-local minutes)
  spreads_1m.parquet         calendar-spread instrument bars (SEPARATE — negative
                             prices live here; never mixed into price stats)
  registry.parquet           per-contract identity + QA flags
  session_contract.parquet   per (session_date, contract): OHLC, volumes by
                             exchange-clock segment and hub-local window
  build_report.json          data-quality numbers (era ledger raw inputs)

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python 6A_build_cache.py
"""
from __future__ import annotations

import importlib.util
import os

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "sixA_deep_lib", os.path.join(_HERE, "6A_deep_lib.py"))
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)


def era_of(d) -> str:
    d = pd.Timestamp(d)
    if d <= pd.Timestamp("2021-12-31"):
        return "ERA_BF2_2020_2021"
    if d <= pd.Timestamp("2023-12-31"):
        return "ERA_BF1A_2022_2023"
    if d <= pd.Timestamp("2025-12-31"):
        return "ERA_BF1B_2024_2025"
    if d <= pd.Timestamp("2026-03-31"):
        return "ERA_BF1C_2026Q1"
    return "ERA_TRIM_2026Q2Q3"


def main():
    os.makedirs(L.CACHE, exist_ok=True)
    raw = L.load_raw_6a()
    print(f"raw rows {len(raw)}; symbols {raw['raw_symbol'].nunique()}; "
          f"{raw['dt'].min()} -> {raw['dt'].max()}")

    is_spread = raw["raw_symbol"].str.contains("-")
    spr = raw[is_spread].copy()
    outr = raw[~is_spread].copy()
    # vendor contamination guard: keep ONLY symbols matching the 6A month-code
    # convention (measured: 1,584 bars of '6BU5' — a 6B-family symbol — ride
    # inside the 6A parent request, instrument 1318, 2020-05-12..2020-08-17)
    good = outr["raw_symbol"].str.fullmatch(r"6A[FGHJKMNQUVXZ]\d")
    contaminants = outr[~good]
    outr = outr[good].copy()
    print(f"outright rows {len(outr)} ({outr['raw_symbol'].nunique()} symbols); "
          f"spread rows {len(spr)} ({spr['raw_symbol'].nunique()} symbols); "
          f"non-6A-family rows excluded {len(contaminants)} "
          f"({contaminants['raw_symbol'].unique().tolist()})")

    # ---- negative-price ledger (dispatch claim re-measured) ----------------
    def negcount(df):
        if len(df) == 0:
            return 0
        return int((df[["open", "high", "low", "close"]] < 0).any(axis=1).sum())
    neg = {
        "outright_negative_bars": negcount(outr),
        "spread_negative_bars": negcount(spr),
        "spread_bars_total": int(len(spr)),
    }

    # ---- registry ----------------------------------------------------------
    defs = L.load_definitions_6a()
    reg = L.build_registry(outr, defs)
    reg.to_parquet(f"{L.CACHE}/registry.parquet", index=False)
    iid2c = dict(zip(reg["instrument_id"], reg["contract"]))
    print(f"registry contracts {len(reg)} "
          f"(quarterly {(~reg['stray'] & reg['is_quarterly']).sum()}, "
          f"serial {(~reg['stray'] & ~reg['is_quarterly']).sum()}, "
          f"stray {int(reg['stray'].sum())}); "
          f"def-window cross-check mismatches "
          f"{len(reg.attrs.get('def_mismatches', []))}; "
          f"stray-cluster instruments {int((reg['n_stray_clusters'] > 0).sum())}")

    # ---- annotate ----------------------------------------------------------
    outr = L.annotate(outr)
    outr["contract"] = outr["instrument_id"].map(iid2c)
    unmapped = int(outr["contract"].isna().sum())
    if unmapped:
        raise ValueError(f"{unmapped} outright rows unmapped to contracts")
    for tz, col in [(L.SYD, "syd_min"), (L.TYO, "tyo_min"),
                    (L.SHA, "sha_min"), (L.LON, "lon_min")]:
        outr[col] = L.hub_local(outr, tz)
    outr["w_sydney_day"] = (outr["syd_min"] >= 7 * 60) & (outr["syd_min"] < 17 * 60)
    outr["w_tokyo"] = (outr["tyo_min"] >= 9 * 60) & (outr["tyo_min"] < 15 * 60)
    outr["w_shanghai_data"] = ((outr["sha_min"] >= 9 * 60 + 30)
                               & (outr["sha_min"] < 10 * 60))
    outr["w_london"] = (outr["lon_min"] >= 8 * 60) & (outr["lon_min"] < 16 * 60 + 30)
    outr["w_us_data"] = (outr["ct_minute"] >= 7 * 60) & (outr["ct_minute"] < 8 * 60 + 30)
    outr["era"] = pd.to_datetime(outr["session_date"]).map(era_of)
    cols = ["instrument_id", "raw_symbol", "ts_event", "dt", "open", "high",
            "low", "close", "volume", "contract", "session_date", "ct_minute",
            "segment", "in_rth", "in_break", "weekend_anomaly", "syd_min",
            "tyo_min", "sha_min", "lon_min", "w_sydney_day", "w_tokyo",
            "w_shanghai_data", "w_london", "w_us_data", "era"]
    outr[cols].to_parquet(f"{L.CACHE}/outright_1m.parquet", index=False)

    spr = L.annotate(spr)
    spr["era"] = pd.to_datetime(spr["session_date"]).map(era_of)
    spr["is_negative_bar"] = (spr[["open", "high", "low", "close"]] < 0).any(axis=1)
    spr[["instrument_id", "raw_symbol", "ts_event", "dt", "open", "high", "low",
         "close", "volume", "session_date", "ct_minute", "era",
         "is_negative_bar"]].to_parquet(f"{L.CACHE}/spreads_1m.parquet", index=False)

    # ---- session x contract daily table ------------------------------------
    o = outr.sort_values("dt")
    daily = o.groupby(["session_date", "contract"], sort=False).agg(
        open_px=("open", "first"), high_px=("high", "max"),
        low_px=("low", "min"), close_px=("close", "last"),
        volume=("volume", "sum"), n_bars=("volume", "size"),
        n_zero_vol=("volume", lambda s: int((s == 0).sum())),
        first_bar=("dt", "min"), last_bar=("dt", "max"),
    ).reset_index()
    rth = o[o["in_rth"]]
    daily = daily.merge(
        rth.groupby(["session_date", "contract"], sort=False).agg(
            rth_open=("open", "first"), rth_close=("close", "last"),
            rth_volume=("volume", "sum")).reset_index(),
        on=["session_date", "contract"], how="left")
    for w in ["w_sydney_day", "w_tokyo", "w_shanghai_data", "w_london", "w_us_data"]:
        vol = o[o[w]].groupby(["session_date", "contract"], sort=False)["volume"].sum()
        daily = daily.merge(vol.rename("vol_" + w).reset_index(),
                            on=["session_date", "contract"], how="left")
    ev = o[o["ct_minute"] >= 17 * 60].groupby(
        ["session_date", "contract"], sort=False)["volume"].sum()
    daily = daily.merge(ev.rename("vol_ev_apac_open").reset_index(),
                        on=["session_date", "contract"], how="left")
    onn = o[o["ct_minute"] < 6 * 60].groupby(
        ["session_date", "contract"], sort=False)["volume"].sum()
    daily = daily.merge(onn.rename("vol_on_asia").reset_index(),
                        on=["session_date", "contract"], how="left")
    st = o[(o["ct_minute"] >= 15 * 60) & (o["ct_minute"] < 16 * 60)].groupby(
        ["session_date", "contract"], sort=False)["volume"].sum()
    daily = daily.merge(st.rename("vol_settle_tail").reset_index(),
                        on=["session_date", "contract"], how="left")
    daily["era"] = pd.to_datetime(daily["session_date"]).map(era_of)
    daily.to_parquet(f"{L.CACHE}/session_contract.parquet", index=False)

    # ---- build report -------------------------------------------------------
    rep = {
        "raw_rows": int(len(raw)),
        "outright_rows": int(len(outr)),
        "spread_rows": int(len(spr)),
        "first_bar_utc": str(raw["dt"].min()), "last_bar_utc": str(raw["dt"].max()),
        "negative_price_bars": neg,
        "vendor_contamination_excluded": {
            "n_rows": int(len(contaminants)),
            "symbols": contaminants["raw_symbol"].unique().tolist(),
            "instrument_ids": sorted(contaminants["instrument_id"].unique().tolist()),
            "span_utc": [str(contaminants["dt"].min()), str(contaminants["dt"].max())],
            "total_volume": int(contaminants["volume"].sum()),
            "note": "non-6A-family outright symbols inside the 6A parent request; excluded from every 6A stat",
        },
        "registry": {
            "n_contracts": int(len(reg)),
            "n_quarterly": int(((~reg["stray"]) & reg["is_quarterly"]).sum()),
            "n_serial": int(((~reg["stray"]) & (~reg["is_quarterly"])).sum()),
            "n_stray": int(reg["stray"].sum()),
            "strays": reg[reg["stray"]][["symbol", "instrument_id", "first_bar",
                                          "last_bar", "n_bars"]].to_dict("records"),
            "instruments_with_stray_clusters": int((reg["n_stray_clusters"] > 0).sum()),
            "stray_cluster_examples": (
                reg[reg["n_stray_clusters"] > 0][["contract", "stray_clusters"]]
                .head(12).to_dict("records")),
            "def_window_mismatches": reg.attrs.get("def_mismatches", []),
            "identity_source_counts": reg["identity_source"].value_counts().to_dict(),
        },
        "qa": {
            "break_violation_bars": int(outr["in_break"].sum()),
            "break_violation_detail": outr[outr["in_break"]][
                ["raw_symbol", "dt", "close", "volume"]].head(10).to_dict("records"),
            "weekend_anomaly_bars": int(outr["weekend_anomaly"].sum()),
            "sessions_total": int(daily["session_date"].nunique()),
            "contracts_in_daily": int(daily["contract"].nunique()),
        },
        "eras": {},
    }
    for era, grp in daily.groupby("era"):
        rep["eras"][era] = {
            "sessions": int(grp["session_date"].nunique()),
            "session_contract_rows": int(len(grp)),
            "zero_vol_bar_share": float(grp["n_zero_vol"].sum()
                                        / max(grp["n_bars"].sum(), 1)),
        }
    L.jdump(rep, f"{L.CACHE}/build_report.json")
    print("caches written to", L.CACHE)
    print("negative-price ledger:", neg)
    print("break violations:", rep["qa"]["break_violation_bars"],
          "weekend anomalies:", rep["qa"]["weekend_anomaly_bars"])


if __name__ == "__main__":
    main()
