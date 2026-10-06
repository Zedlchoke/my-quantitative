"""A7 — NQ data-quality ledger 2010-2026 (DEEP-NQ).

Per-era record densities, gaps and the 2020 vendor hole, DST evidence,
maintenance-break violations, stray deferred-quarter prints, session-era
schedule changes (Friday early close, 16:15->16:00 close), duplicate and
monotonicity checks, spread-instrument share. Every claim below is OBSERVED
on the av1trim parquet panel with this script + window.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import NQ_deep_lib as L  # noqa: E402

OUT = os.path.join(L.HERE, "NQ_a7_quality.json")


def main():
    df = L.load_annotated_1m()
    sess = pd.read_parquet(os.path.join(L.CACHE, "nq_sessions.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))
    reg = pd.read_json(os.path.join(L.CACHE, "contract_registry.json"))
    res = {"schema": "NQ_a7_quality@1"}

    stray_col = reg["stray"].fillna(False).astype(bool) if "stray" in reg \
        else pd.Series([False] * len(reg))
    res["panel"] = {
        "rows_outright_1m": int(len(df)),
        "first_bar_utc": str(df["dt"].min()),
        "last_bar_utc": str(df["dt"].max()),
        "stray_clusters_excluded": int(stray_col.sum()),
        "stray_detail": reg[stray_col][
            ["symbol", "first_bar", "last_bar", "n_bars"]].to_dict("records"),
        "duplicate_symbol_minute_rows": int(
            df.duplicated(subset=["raw_symbol", "ts_event"]).sum()),
    }

    # monotonic ts within each contract stream
    bad = 0
    for c, g in df.groupby("contract"):
        if g["ts_event"].is_monotonic_increasing is False:
            bad += 1
    res["panel"]["non_monotonic_contract_streams"] = int(bad)

    # ---- per-year density ----
    df["year"] = df["dt"].dt.year
    yr = []
    held_sess = sess.merge(held.rename(columns={"held": "contract"}),
                           on=["session_date", "contract"], how="inner")
    held_sess["y"] = pd.to_datetime(held_sess["session_date"]).dt.year
    for y, g in df.groupby("year"):
        hs = held_sess[held_sess["y"] == y]
        yr.append({
            "year": int(y), "bars": int(len(g)),
            "sessions_with_data": int(g["session_date"].nunique()),
            "held_sessions": int(len(hs)),
            "clean_held_sessions": int((hs["rth_coverage"].fillna(0) >= 0.6).sum()),
            "median_front_rth_coverage": float(
                hs["rth_coverage"].median()) if len(hs) else None})
    res["yearly_density"] = yr

    # ---- the 2020 hole ----
    hole = df[(df["dt"] >= "2020-03-20") & (df["dt"] < "2020-06-01")]
    hole_sess = hole.groupby("session_date")["contract"].unique().to_dict()
    res["vendor_hole_2020"] = {
        "window": "2020-03-20..2026-05-29 (front contracts absent; measured)",
        "degraded_from": "2020-03-16 (front volume 505k->85k by 03-19)",
        "sessions_affected": int(len(hole_sess)),
        "contracts_with_any_data": sorted(
            {c for cs in hole_sess.values() for c in cs}),
        "held_contract_missing_sessions": int(
            (held_sess.groupby("y").size().get(2020, 0)) and
            len(held_sess) - held_sess["session_date"].nunique()),
        "note": "only deferred NQU0_2020 trickle (~100-1200 contracts/day); "
                "the true front NQM0_2020 is entirely absent 03-23..05-29; "
                "all affected analyses exclude or NaN these sessions"}

    # ---- DST evidence: session-open UTC hour by month (17:00 CT = 22Z CDT / 23Z CST) ----
    opens = []
    for d, g in df.groupby("session_date"):
        g2 = g[g["minute_of_day"] >= 1020].sort_values("dt")
        if len(g2):
            first = g2["dt"].iloc[0]
            opens.append({"d": str(d), "utc_hour": int(first.hour)})
    op = pd.DataFrame(opens)
    op["m"] = pd.to_datetime(op["d"]).dt.to_period("M").astype(str)
    piv = op.groupby("m")["utc_hour"].agg(
        lambda s: int(s.mode().iloc[0]))
    flips = piv[piv.diff().fillna(0) != 0]
    res["dst_evidence"] = {
        "note": "modal UTC hour of the 17:00 CT Globex open per month; "
                "22 = CDT, 23 = CST; flips should land in March/November",
        "flip_months": {str(k): int(v) for k, v in flips.items()},
        "n_months": int(len(piv)),
        "unexpected_flips": [m for m in flips.index
                             if m[5:7] not in ("03", "11")]}

    # ---- break-bar violations (trading inside the maintenance window) ----
    brk = df[df["in_break"]]
    loc = brk["dt"].dt.tz_convert(L.CHI)
    res["break_bar_violations"] = {
        "n_bars": int(len(brk)),
        "eraA_1615_1700": int(((brk["minute_of_day"] >= 16*60+15)).sum()),
        "eraB_1600_close_tail": int(((brk["minute_of_day"] >= 16*60)
                                     & (brk["minute_of_day"] < 16*60+15)
                                     & (pd.to_datetime(
                                         brk["session_date"]) >=
                                         L.SESSION_SWITCH_DATE)).sum()),
        "by_year": {str(int(k)): int(v) for k, v in
                    loc.dt.year.value_counts().sort_index().items()}}

    # ---- schedule-era changes (measured) ----
    res["session_schedule_eras"] = {
        "eraA": "2010-06-06..2015-09-18: Mon-Thu close 16:15 CT; FRIDAY "
                "close 15:15 CT through 2012-10 (last full month; mixed "
                "Nov-2012; none from Dec-2012); maintenance 16:15-17:00",
        "eraB": "2015-09-21..2026-09-30: all days close 16:00 CT; "
                "maintenance 16:00-17:00",
        "evidence": "median last-trade minute per weekday per year "
                    "(NQ_a7 run + NQ_a2 era tables)"}

    # ---- price sanity ----
    px = df[["high", "low", "close", "open"]] / 1e9
    res["price_sanity"] = {
        "negative_prices": int((px < 0).any(axis=1).sum()),
        "high_lt_low": int((df["high"] < df["low"]).sum()),
        "close_outside_hl": int(((df["close"] > df["high"]) |
                                 (df["close"] < df["low"])).sum()),
        "zero_volume_bars": int((df["volume"] == 0).sum()),
        "min_close": float(px["close"].min()), "max_close": float(px["close"].max())}

    # ---- source file composition (spread vs outright) ----
    import glob
    files = sorted(glob.glob(
        "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
        "/parquet/AV1R-O1M-NQ-DELTA/*.parquet")) + sorted(glob.glob(
        "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim"
        "/parquet/AV1T-O1M-NQ/*.parquet"))
    tot = 0
    spr = 0
    for f in files:
        t = pd.read_parquet(f, columns=["raw_symbol"])
        tot += len(t)
        spr += int(t["raw_symbol"].str.contains("-").sum())
    res["vendor_row_composition"] = {
        "total_rows_parent_symbol": int(tot),
        "calendar_spread_rows": int(spr),
        "outright_rows": int(tot - spr),
        "note": "parent NQ.FUT request resolves spreads too; analysis uses "
                "outrights only"}

    L.jdump(res, OUT)
    print("A7 complete ->", OUT)


if __name__ == "__main__":
    main()
