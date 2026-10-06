"""QA — 6J data-quality ledger per era (DEEP-6J).

Census of the four chained 6J ohlcv-1m windows (AV1B BACKFILL2 2020-22,
AV1R BACKFILL 2022-24 + 2024-26, AV1T 2026) + statistics/definitions coverage
+ nonprice dataset windows. Read-only; every item OBSERVED unless marked.
"""
from __future__ import annotations

import os
import sys

import importlib

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6J_deep_lib")

OUT = os.path.join(L.HERE, "6J_qa_ledger.json")


def main():
    raw = pd.read_parquet(os.path.join(L.CACHE, "6j_outright_1m.parquet"))
    ann = pd.read_parquet(os.path.join(L.CACHE, "6j_annotated_1m.parquet"))
    sess = pd.read_parquet(os.path.join(L.CACHE, "6j_sessions.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))
    reg = pd.read_json(os.path.join(L.CACHE, "contract_registry.json"))

    res = {"schema": "6J_qa_ledger@1"}

    # ---- per-file / per-era census ----
    eras = []
    for f, a, b, name in [
        ("AV1B-O1M-6J-BACKFILL2__2020-01-01_2022-01-01.parquet", "2020-01-01", "2022-01-01", "era_backfill2_2020_22"),
        ("AV1R-O1M-6J-BACKFILL__2022-01-01_2024-01-01.parquet", "2022-01-01", "2024-01-01", "era_backfill_2022_24"),
        ("AV1R-O1M-6J-BACKFILL__2024-01-01_2026-01-01.parquet", "2024-01-01", "2026-01-01", "era_backfill_2024_26"),
        ("AV1T-O1M-6J__2026-01-01_2026-07-01.parquet", "2026-01-01", "2026-07-01", "era_av1t_2026H1"),
        ("AV1T-O1M-6J__2026-07-01_2026-10-01.parquet", "2026-07-01", "2026-10-01", "era_av1t_2026Q3"),
    ]:
        d = pd.read_parquet(f"{L.DATA_ROOT}/parquet/{f.split('__')[0].split('AV')[0]}"
                            if False else None) if False else None
        import glob
        fp = glob.glob(f"{L.DATA_ROOT}/parquet/*/{f}")[0]
        d = pd.read_parquet(fp)
        outright = d[d["raw_symbol"].str.fullmatch(r"^6J[FGHJKMNQUVXZ]\d$")]
        spread = d[d["raw_symbol"].str.contains("-")]
        nonj = d[~d["raw_symbol"].str.startswith("6J")]
        eras.append({
            "file": f, "window": f"{a}..{b}",
            "rows_total": int(len(d)),
            "rows_outright": int(len(outright)),
            "rows_spread_instrument": int(len(spread)),
            "rows_non_6J_symbols": int(len(nonj)),
            "non_6J_symbols": sorted(nonj["raw_symbol"].astype(str).unique().tolist()),
            "first_bar_utc": str(pd.to_datetime(d["ts_event"].min(), unit="ns", utc=True)),
            "last_bar_utc": str(pd.to_datetime(d["ts_event"].max(), unit="ns", utc=True)),
            "n_contracts": int(outright["raw_symbol"].nunique())})
    res["eras"] = eras

    # ---- global checks ----
    res["global"] = {
        "outright_rows": int(len(raw)),
        "first": str(raw["dt"].min()), "last": str(raw["dt"].max()),
        "tick_grid_violations": int(sum((raw[c] % L.TICK != 0).sum()
                                        for c in ("open", "high", "low", "close"))),
        "negative_or_zero_closes": int((raw["close"] <= 0).sum()),
        "duplicate_instrument_ts_rows": int(
            raw.duplicated(subset=["instrument_id", "ts_event"]).sum()),
        "price_min_usdjpy_quote": float(raw["close"].min() * 1e-9),
        "price_max_usdjpy_quote": float(raw["close"].max() * 1e-9),
        "contracts_total": int(len(reg)),
        "contracts_quarterly": int((~reg["stray"] & reg["symbol"].str[2].isin(list("HMUZ"))).sum()),
        "contracts_serial": int((~reg["stray"] & ~reg["symbol"].str[2].isin(list("HMUZ"))).sum()),
        "stray_clusters": int(reg["stray"].sum()),
        "multi_cluster_contracts": int((reg.groupby("contract").size() > 1).sum()),
        "multi_cluster_note": "same contract split by >60d bar gap (deferred trickle "
                              "then roll-window activity); mapped to one contract key",
        "break_window_bars_16_17_ct": int(ann["in_break"].sum()),
        "weekend_anomaly_bars": int(ann["weekend_anomaly"].sum())}

    # ---- session coverage ----
    hh = sess.merge(held.rename(columns={"held": "contract"}))
    hh["sd"] = pd.to_datetime(hh["session_date"])
    hh = hh.sort_values("sd")
    dep = hh[hh["n_bars"] < 0.25 * L.SESSION_FULL_MIN]
    res["session_coverage"] = {
        "held_sessions": int(len(hh)),
        "median_bars_per_session": float(hh["n_bars"].median()),
        "p5_bars_per_session": float(hh["n_bars"].quantile(.05)),
        "depleted_sessions_lt25pct": [
            {"date": str(r["sd"].date()), "bars": int(r["n_bars"])}
            for _, r in dep.iterrows()],
        "session_full_minutes": L.SESSION_FULL_MIN,
        "note": "CME FX trades 23h continuously 17:00->16:00 CT; no maintenance "
                "break observed (1 stray bar in 2.84M inside 16:00-17:00 CT)"}

    # holiday census: weekday sessions missing from held chain
    cal = pd.date_range(hh["sd"].min(), hh["sd"].max(), freq="B")
    missing = [str(d.date()) for d in cal if d not in set(hh["sd"])]
    res["session_coverage"]["missing_weekday_sessions"] = missing
    res["session_coverage"]["n_missing_weekdays"] = len(missing)

    # ---- volume scale cross-check vs GLBX cleared volume (2023-10+) ----
    stats = L.load_statistics_6j()
    cv = stats[stats["stat_type"] == 6].copy()
    cv["d"] = pd.to_datetime(cv["ref_date"])
    cv = cv[~cv["raw_symbol"].str.contains("-")]
    cvd = cv.groupby("d")["quantity"].sum()
    hv = hh.groupby("sd")["volume"].sum()
    jn = pd.DataFrame({"v1m": hv, "vcleared": cvd}).dropna()
    jn = jn[jn["v1m"] > 1000]
    ratio = (jn["v1m"] / jn["vcleared"])
    res["volume_scale_check_2023plus"] = {
        "n_days": int(len(jn)),
        "median_ratio_1m_summed_vs_cleared": float(ratio.median()),
        "p10_p90_ratio": [float(ratio.quantile(.1)), float(ratio.quantile(.9))],
        "note": "1m summed over ALL outright contracts incl deferred trickle vs "
                "exchange cleared-volume statistic"}

    oi = stats[stats["stat_type"] == 9]
    res["statistics_coverage"] = {
        "first": str(pd.to_datetime(stats["ts_ref"], unit="ns", utc=True).min().date()),
        "last": str(pd.to_datetime(stats["ts_ref"], unit="ns", utc=True).max().date()),
        "oi_rows": int(len(oi)),
        "note": "GLBX statistics (OI stat_type 9) exist ONLY from 2023-10-01; "
                "all OI-based statements are 2023+ only"}

    # ---- nonprice dataset windows ----
    mof = L.load_mof_intervention()
    cot = L.load_cot_6j()
    mpm = L.load_boj_mpm()
    res["nonprice_windows"] = {
        "mof_intervention": {
            "span": f"{mof['op_date'].min().date()}..{mof['op_date'].max().date()}",
            "n_ops": int(len(mof)),
            "latest_verified_op": str(mof["op_date"].max().date()),
            "gap_note": "2026 Q3 daily detail (incl. press-cited Jul 30-Aug 26 window) "
                        "NOT published at fetch (2026-10-02); publish lag ~1 month"},
        "cot_legacy_6j": {
            "span": f"{cot['obs_date'].min().date()}..{cot['obs_date'].max().date()}",
            "n_weeks": int(len(cot)),
            "release": "Friday 15:30 ET, positions as-of prior Tuesday, not revised"},
        "boj_mpm_statements": {
            "span": f"{min(mpm['date'])}..{max(mpm['date'])}",
            "n_decisions": int(len(mpm)),
            "regime_change_titled": [str(d) for d in
                                     mpm.loc[mpm["is_regime_change"] == True, "date"]],
            "gap_note": "mpmdeci index snapshots cover 2018..2026-01 only; 2026 "
                        "statement titles are archive PDFs -> 2026-06-16 / 2026-09-18 "
                        "'Change in Guideline' claims carry v1-dossier FACT only"}}

    L.jdump(res, OUT)
    print("QA complete ->", OUT)


if __name__ == "__main__":
    main()
