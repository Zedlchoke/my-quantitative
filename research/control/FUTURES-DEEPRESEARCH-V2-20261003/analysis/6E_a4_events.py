"""A4 — 6E event-day anatomy: ECB GC decisions + FOMC statements (DEEP-6E).

Release-anchored volume / per-minute range / volatility timing descriptives
from 1m front-quarterly bars, DST-correct release times (Europe/Berlin for
ECB, America/New_York for FOMC). NO conditional mean-return tables: nothing
here ranks or selects signals; PnL-linked selection = NOT_RUN by law.
Event-day vs same-weekday non-event minutes only.
"""
from __future__ import annotations

import importlib
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
L = importlib.import_module("6E_deep_lib")

OUT = os.path.join(L.HERE, "6E_a4_events.json")
BER = "Europe/Berlin"
NY = "America/New_York"


def minute_stats(front: pd.DataFrame, dates: set, lo: int, hi: int):
    """Median volume + median range by CT minute-of-day over given dates."""
    sub = front[(front["session_date"].isin(dates))
                & (front["minute_of_day"] >= lo)
                & (front["minute_of_day"] < hi)]
    if not len(sub):
        return {}, {}
    sub = sub.assign(r=sub["high_px"] - sub["low_px"])
    vol = sub.groupby("minute_of_day")["volume"].median()
    rng = sub.groupby("minute_of_day")["r"].median()
    return ({int(k): float(v) for k, v in vol.items()},
            {int(k): float(v) for k, v in rng.items()})


def main():
    res = {"schema": "6E_a4_events@1",
           "law": "descriptive release-anchored timing only; NO conditional "
                  "mean-return tables; no selection"}
    df = pd.read_parquet(os.path.join(L.CACHE, "6e_annotated_1m.parquet"))
    held = pd.read_parquet(os.path.join(L.CACHE, "held_calendar.parquet"))
    held["session_date"] = held["session_date"].astype(str)
    df["session_date"] = df["session_date"].astype(str)
    df["contract"] = df["raw_symbol"] + "_" + (
        2020 + df["raw_symbol"].str[-1].astype(int)).astype(str)
    front = df.merge(held, left_on=["session_date"], right_on=["session_date"])
    front = front[front["contract"] == front["held"]]
    front["r"] = front["high_px"] - front["low_px"]
    all_sessions = set(held["session_date"])

    ecb = L.load_ecb_gc()
    fomc = L.load_fomc()

    # ---- ECB decision days ----
    # release 14:15 Berlin time (FACT, ECB page fetched 2026-10-02); press
    # conference 14:45 Berlin. Convert per-date to CT minute-of-day.
    ecb_rows = []
    for r in ecb.itertuples():
        d = r.date
        s = d.strftime("%Y-%m-%d")
        if s not in all_sessions:
            ecb_rows.append({"date": s, "in_data": False})
            continue
        ts = pd.Timestamp(d.year, d.month, d.day, 14, 15, tz=BER)
        ct = ts.tz_convert(L.CHI)
        minute = ct.hour * 60 + ct.minute
        ecb_rows.append({"date": s, "in_data": True, "verified_direct":
                         bool(r.verified_direct), "release_ct_minute": minute,
                         "release_ct": str(ct)})
    in_data = [e for e in ecb_rows if e["in_data"]]
    res["ecb"] = {
        "n_meetings_2020_2026": len(ecb_rows),
        "n_in_data": len(in_data),
        "n_verified_direct_fetch": sum(e.get("verified_direct", False) for e in in_data),
        "release_time_facts": "decision press release 14:15 CET/CEST "
                              "(Europe/Berlin), press conference 14:45 "
                              "(ECB pages, fetched 2026-10-02); dates "
                              "assembled from the ECB decisions archive "
                              "(JS-rendered; 10 dates machine-verified by "
                              "direct press-release URL fetch)",
        "release_minutes_ct_distribution": pd.Series(
            [e["release_ct_minute"] for e in in_data]).value_counts().to_dict(),
    }
    ecb_dates = {e["date"] for e in in_data}
    # control: Thursdays without ECB decision
    thurs = {s for s in all_sessions
             if pd.Timestamp(s).dayofweek == 3 and s not in ecb_dates}

    # window 06:30-08:30 CT (contains 14:15 Berlin in both DST states)
    ev_vol, ev_rng = minute_stats(front, ecb_dates, 6 * 60 + 30, 8 * 60 + 30)
    ct_vol, ct_rng = minute_stats(front, thurs, 6 * 60 + 30, 8 * 60 + 30)
    res["ecb"]["median_volume_by_minute"] = {
        "event": {str(k): v for k, v in ev_vol.items()},
        "control_thursdays": {str(k): v for k, v in ct_vol.items()}}
    # ratios at the typical release minutes (06:45 CDT / 07:15 CST -> both)
    def ratio_at(vol_e, vol_c, m):
        if m in vol_e and m in vol_c and vol_c[m] > 0:
            return float(vol_e[m] / vol_c[m])
        return None
    res["ecb"]["volume_ratio_event_vs_control"] = {
        f"m{m}": ratio_at(ev_vol, ct_vol, m) for m in (405, 420, 430, 435, 445)}
    # peak-volume minute distribution on event days (argmax per session)
    sub = front[(front["session_date"].isin(ecb_dates))
                & (front["minute_of_day"] >= 6 * 60)
                & (front["minute_of_day"] < 9 * 60)]
    peak_min = sub.groupby("session_date").apply(
        lambda g: int(g.loc[g["volume"].idxmax(), "minute_of_day"]))
    res["ecb"]["peak_volume_minute_0600_0900ct_distribution"] = (
        peak_min.value_counts().sort_index().to_dict())
    subc = front[(front["session_date"].isin(thurs))
                 & (front["minute_of_day"] >= 6 * 60)
                 & (front["minute_of_day"] < 9 * 60)]
    peak_min_c = subc.groupby("session_date").apply(
        lambda g: int(g.loc[g["volume"].idxmax(), "minute_of_day"]))
    res["ecb"]["peak_volume_minute_control_thursdays"] = (
        peak_min_c.value_counts().sort_index().to_dict())
    # post-release volume share of a fixed CT block
    def share_after(dates, release_m, lo, hi):
        tot = post = 0.0
        for s in dates:
            g = front[(front["session_date"] == s)
                      & (front["minute_of_day"] >= lo)
                      & (front["minute_of_day"] < hi)]
            if not len(g):
                continue
            tot += g["volume"].sum()
            post += g.loc[g["minute_of_day"] >= release_m, "volume"].sum()
        return float(post / tot * 100) if tot else None
    res["ecb"]["share_of_0600_1000_volume_after_0645ct"] = {
        "event_days": share_after(ecb_dates, 405, 360, 600),
        "control_thursdays": share_after(thurs, 405, 360, 600)}

    # ---- FOMC decision days ----
    fomc_rows = []
    for r in fomc.itertuples():
        s = r.date.strftime("%Y-%m-%d")
        if s < "2020-01-01":
            continue
        if s not in all_sessions:
            continue
        # statement time: parsed 'For release at' when present, else 14:00 ET
        if r.time_et is not None:
            ts = pd.Timestamp(r.date.year, r.date.month, r.date.day,
                              r.time_et.hour, r.time_et.minute, tz=NY)
        else:
            ts = pd.Timestamp(r.date.year, r.date.month, r.date.day,
                              14, 0, tz=NY)
        ct = ts.tz_convert(L.CHI)
        fomc_rows.append({"date": s, "time_et_proven": r.time_et is not None,
                          "release_ct_minute": ct.hour * 60 + ct.minute})
    res["fomc"] = {
        "n_in_data_2020_2026": len(fomc_rows),
        "n_with_primary_time_proof": sum(r["time_et_proven"] for r in fomc_rows),
        "release_minutes_ct_distribution": pd.Series(
            [r["release_ct_minute"] for r in fomc_rows]).value_counts().to_dict(),
    }
    fomc_dates = {r["date"] for r in fomc_rows}
    weds = {s for s in all_sessions
            if pd.Timestamp(s).dayofweek == 2 and s not in fomc_dates}
    fv, fr_ = minute_stats(front, fomc_dates, 12 * 60 + 30, 14 * 60 + 30)
    cv, cr = minute_stats(front, weds, 12 * 60 + 30, 14 * 60 + 30)
    res["fomc"]["median_volume_by_minute"] = {
        "event": {str(k): v for k, v in fv.items()},
        "control_wednesdays": {str(k): v for k, v in cv.items()}}
    res["fomc"]["volume_ratio_event_vs_control"] = {
        f"m{m}": ratio_at(fv, cv, m) for m in (780, 785, 790, 795, 800, 810, 820)}
    subf = front[(front["session_date"].isin(fomc_dates))
                 & (front["minute_of_day"] >= 12 * 60)
                 & (front["minute_of_day"] < 15 * 60)]
    peakf = subf.groupby("session_date").apply(
        lambda g: int(g.loc[g["volume"].idxmax(), "minute_of_day"]))
    res["fomc"]["peak_volume_minute_1200_1500ct_distribution"] = (
        peakf.value_counts().sort_index().to_dict())
    subfc = front[(front["session_date"].isin(weds))
                  & (front["minute_of_day"] >= 12 * 60)
                  & (front["minute_of_day"] < 15 * 60)]
    peakfc = subfc.groupby("session_date").apply(
        lambda g: int(g.loc[g["volume"].idxmax(), "minute_of_day"]))
    res["fomc"]["peak_volume_minute_control_wednesdays"] = (
        peakfc.value_counts().sort_index().to_dict())
    res["fomc"]["share_of_1200_1600_volume_after_1300ct"] = {
        "event_days": share_after(fomc_dates, 780, 720, 960),
        "control_wednesdays": share_after(weds, 780, 720, 960)}

    # ---- ECB 2022 unscheduled/extra meetings present? (Mar-2020 pair etc.)
    res["ecb"]["meeting_dates_used"] = sorted(ecb_dates)

    # ---- US 8:30 ET block on all days (release-anchored, not event-list) ----
    d830 = front[(front["minute_of_day"] == 450)]
    nb = front[(front["minute_of_day"] == 449)]
    res["us_830et_block"] = {
        "median_volume_0730": float(d830["volume"].median()),
        "median_volume_0729": float(nb["volume"].median()),
        "median_range_0730": float(d830["r"].median()),
        "median_range_0729": float(nb["r"].median()),
        "note": "8:30 ET releases occur Mon-Fri (CPI/NFP/retail/etc.); "
                "event-type split NOT_RUN (no PIT release calendar on disk "
                "for US data).",
    }
    L.jdump(res, OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
