"""A4 — NQ event-day anatomy: FOMC 2011-2026 (DEEP-NQ).

DESCRIPTIVE ONLY (laws): volume / volatility / range timing around the
release window on FOMC statement days vs matched non-event control sessions.
NO conditional mean-return tables, no PnL, no signal ranking.

Release times: only statements whose own archived HTML carries
'For release at H:MM a.m./p.m. E[SD]T' (106 of 147; 98 at 2:00 p.m. ET)
enter the release-window analysis; the rest (2011-2013 era) are day-level
only. CPI/NFP release calendars are NOT archived in the nonprice tree
(bls_gate empty) -> NOT_RUN, disclosed, with the 07:30 CT minute-share
descriptive as the only calendar-free evidence of that cluster.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import NQ_deep_lib as L  # noqa: E402

OUT = os.path.join(L.HERE, "NQ_a4_events.json")

WINDOWS = [  # minutes relative to release (CT clock)
    ("m120_60", -120, -60), ("m60_0", -60, 0), ("h0_30", 0, 30),
    ("h30_60", 30, 60), ("h60_120", 60, 120), ("h120_180", 120, 180),
]


def session_minute_stats(bars: pd.DataFrame) -> pd.DataFrame:
    """bars: 1m rows for one held-contract session, minute_of_day present."""
    b = bars.sort_values("dt")
    lc = np.log(b["close"].astype(float))
    r1 = lc.diff()
    mo = b["minute_of_day"].values
    return pd.DataFrame({"m": mo, "vol": b["volume"].values, "r1": r1.values,
                         "hi": b["high"].values / 1e9,
                         "lo": b["low"].values / 1e9})


def main():
    fomc = L.load_fomc()
    held = pd.read_parquet(os.path.join(L.CACHE, "held_volume_k5.parquet"))
    sess = pd.read_parquet(os.path.join(L.CACHE, "nq_sessions.parquet"))
    hs = sess.merge(held.rename(columns={"held": "contract"}),
                    on=["session_date", "contract"], how="inner")
    hs["d"] = pd.to_datetime(hs["session_date"])
    hs = hs.set_index("d")

    df = L.load_annotated_1m()
    dfh = df.merge(held.rename(columns={"held": "contract"}),
                   on=["contract", "session_date"], how="inner")
    del df
    dfh["d"] = pd.to_datetime(dfh["session_date"])
    dfh = dfh.sort_values(["contract", "dt"]).reset_index(drop=True)
    dfh["r1"] = (dfh.groupby("contract")["close"].transform(
        lambda s: np.log(s.astype(float)).diff()))
    dfh.loc[dfh["contract"].ne(dfh["contract"].shift()), "r1"] = np.nan

    res = {"schema": "NQ_a4_events@1",
           "fomc_statements": int(len(fomc)),
           "with_release_time_proof": int(fomc["time_et"].notna().sum()),
           "time_distribution": fomc["time_et"].astype(str).value_counts().to_dict()}

    # ---- day-level: FOMC session vs control (same weekday, +-3wk, no events) ----
    ev_dates = set(fomc["date"].dt.normalize())
    day_rows = []
    for d in sorted(ev_dates):
        if d not in hs.index:
            continue
        row = hs.loc[d]
        lo, hi = d - pd.Timedelta(days=21), d + pd.Timedelta(days=21)
        pool = hs[(hs.index >= lo) & (hs.index <= hi)]
        pool = pool[pool.index.dayofweek == d.dayofweek]
        pool = pool[~pool.index.isin(ev_dates)]
        pool = pool[pool["rth_coverage"].fillna(0) >= 0.6]
        if row["rth_coverage"] is None or pd.isna(row["rth_coverage"]) \
                or row["rth_coverage"] < 0.6 or not len(pool):
            continue
        day_rows.append({
            "date": str(d.date()),
            "vol_ratio": float(row["volume"] / pool["volume"].median()),
            "rthvol_ratio": float(row["rth_volume"] / pool["rth_volume"].median()),
            "tr_ratio": float(row["true_range"] / pool["true_range"].median()),
            "rth_bars": float(row["rth_bars"])})
    dd = pd.DataFrame(day_rows)
    res["fomc_day_level"] = {
        "n": int(len(dd)),
        "session_volume_ratio_median": float(dd["vol_ratio"].median()),
        "rth_volume_ratio_median": float(dd["rthvol_ratio"].median()),
        "true_range_ratio_median": float(dd["tr_ratio"].median()),
        "share_days_vol_above_control": float((dd["vol_ratio"] > 1).mean()),
        "share_days_range_above_control": float((dd["tr_ratio"] > 1).mean()),
        "control": "same weekday within +-21d, non-event, clean sessions"}

    # ---- release-window anatomy (proof-time statements only) ----
    ev2 = fomc[fomc["time_et"].notna() & (fomc["time_et"].astype(str) == "14:00:00")].copy()
    res["n_2pm_events"] = int(len(ev2))
    win_rows = []
    for d, t in zip(ev2["date"], ev2["time_et"]):
        day = d.normalize()
        if day not in hs.index or pd.isna(hs.loc[day, "rth_coverage"]) \
                or hs.loc[day, "rth_coverage"] < 0.6:
            continue
        # release minute in CT: 14:00 ET == 13:00 CT (both DST-standardized)
        rel = 13 * 60
        bars = dfh[dfh["d"] == day]
        if not len(bars):
            continue
        lo, hi = day - pd.Timedelta(days=21), day + pd.Timedelta(days=21)
        pool_dates = hs[(hs.index >= lo) & (hs.index <= hi)
                        & (hs.index.dayofweek == day.dayofweek)
                        & (~hs.index.isin(ev_dates))
                        & (hs["rth_coverage"].fillna(0) >= 0.6)].index
        pbars = dfh[dfh["d"].isin(pool_dates)]
        rec = {"date": str(day.date())}
        for name, a, b in WINDOWS:
            m0, m1 = rel + a, rel + b
            eb = bars[(bars["minute_of_day"] >= m0) & (bars["minute_of_day"] < m1)]
            cb = pbars[(pbars["minute_of_day"] >= m0) & (pbars["minute_of_day"] < m1)]
            ev_vol = float(eb["volume"].sum())
            ev_absr = float(eb["r1"].abs().mean()) if len(eb) > 1 else np.nan
            # control per-session median (|1m ret| too — signed mean ~0)
            cv = cb.groupby(cb["d"])["volume"].sum().median()
            ca = cb.assign(ar1=cb["r1"].abs()).groupby("d")["ar1"].mean().median()
            ev_rng = float(eb["high"].max() / 1e9 - eb["low"].min() / 1e9) if len(eb) else np.nan
            cr = (cb.groupby("d").apply(
                lambda g: g["high"].max() / 1e9 - g["low"].min() / 1e9,
                include_groups=False).median())
            rec[f"vol_ratio_{name}"] = ev_vol / cv if cv else np.nan
            rec[f"absr_ratio_{name}"] = ev_absr / ca if ca and not np.isnan(ev_absr) else np.nan
            rec[f"rng_ratio_{name}"] = ev_rng / cr if cr and not np.isnan(ev_rng) else np.nan
        # the release minute itself
        em = bars[bars["minute_of_day"] == rel]
        cm = pbars[pbars["minute_of_day"] == rel]
        if len(em) and len(cm):
            rec["release_minute_vol_ratio"] = float(
                em["volume"].iloc[0] / cm["volume"].median())
        win_rows.append(rec)
    wd = pd.DataFrame(win_rows)
    out = {"n": int(len(wd))}
    for name, _a, _b in WINDOWS:
        out[name] = {
            "vol_ratio_median": float(wd[f"vol_ratio_{name}"].median()),
            "absr_ratio_median": float(wd[f"absr_ratio_{name}"].median()),
            "rng_ratio_median": float(wd[f"rng_ratio_{name}"].median())}
    out["release_minute_vol_ratio_median"] = float(
        wd["release_minute_vol_ratio"].median())
    res["fomc_2pm_release_windows"] = out

    res["fomc_time_proof_note"] = (
        "'For release at' lines exist on archived statements from 2016 "
        "onward only (2011-2015 archived HTML carries no time line; those "
        "meetings enter the DAY-LEVEL comparison only). 2010 FOMC meetings "
        "are not in the statements archive at all.")

    # era split for the immediate hour (0..+60 = h0_30 + h30_60)
    wd["year"] = pd.to_datetime(wd["date"]).dt.year
    eras = [("2016_2019", 2016, 2019),
            ("2020_2022", 2020, 2022), ("2023_2026", 2023, 2026)]
    era_hour = {}
    for name, a, b in eras:
        w = wd[(wd["year"] >= a) & (wd["year"] <= b)]
        if not len(w):
            continue
        era_hour[name] = {
            "n": int(len(w)),
            "h0_30_vol_ratio": float(w["vol_ratio_h0_30"].median()),
            "h0_30_absr_ratio": float(w["absr_ratio_h0_30"].median()),
            "m60_0_vol_ratio": float(w["vol_ratio_m60_0"].median()),
            "h120_180_vol_ratio": float(w["vol_ratio_h120_180"].median())}
    res["fomc_release_hour_by_era"] = era_hour

    # ---- non-2pm statements (special times) listed for the record ----
    special = fomc[fomc["time_et"].notna()
                   & (fomc["time_et"].astype(str) != "14:00:00")]
    res["special_time_statements"] = [
        {"date": str(d.date()), "time_et": str(t)}
        for d, t in zip(special["date"], special["time_et"])]

    # ---- CPI/NFP: NOT_RUN statement + calendar-free 07:30 CT evidence ----
    a2 = __import__("json").load(open(os.path.join(L.HERE, "NQ_a2_sessions.json")))
    prof = a2["minute_profiles"]["2023-01_2026-09"]["vol_share_by_minute"]
    def s_at(m):
        v = prof.get(str(m)) or prof.get(m)
        return v
    res["cpa_nfp_status"] = {
        "status": "NOT_RUN",
        "reason": "no historical CPI/NFP release calendar archived in the "
                  "nonprice tree (bls_gate empty; FRED released_at null); "
                  "fabricating dates from memory is forbidden",
        "calendar_free_evidence_0730ct": {
            "note": "07:30 CT = 08:30 ET release slot; minute-volume share "
                    "vs neighbors, 2023-2026 era (calendar-free, descriptive)",
            "share_0725": s_at(445), "share_0729": s_at(449),
            "share_0730": s_at(450), "share_0731": s_at(451),
            "share_0735": s_at(455), "share_0750": s_at(470)}}

    L.jdump(res, OUT)
    print("A4 complete ->", OUT)


if __name__ == "__main__":
    main()
