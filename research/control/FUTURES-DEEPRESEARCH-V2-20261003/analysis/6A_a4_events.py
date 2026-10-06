#!/usr/bin/env python
"""A4 — event-day anatomy: RBA + FOMC 2020-2026 — lane DEEP-6A.

LAWS (dispatch): release-anchored volume/volatility/range timing descriptives
ONLY. NO conditional mean-return tables — signed event returns are never
computed or conditioned on event type (anything PnL-linked = NOT_RUN).

Events (in-corpus sources only):
  * RBA cash-rate decisions 2020-2026 from the rba.gov.au gate HTML table
    (nonprice corpus). Announcement anchor = 14:30 Sydney on
    effective_date - 1 AU business day (convention disclosed; special
    meetings flagged where effective-minus-1BD is not a Tuesday, e.g. the
    2020-03-18 emergency COVID cut).
  * FOMC statement days from archived federalreserve.gov HTML (nonprice
    corpus), statement time 'For release at' where the page carries it
    (else 13:00 CT convention, flagged).
  * ABS CPI / Labour Force: NOT_RUN — no ABS family in the nonprice corpus
    (erratum vs dispatch packet; abs.gov.au does not expose historical
    release dates on listing pages; future-release time 11:30 AEDT verified
    on the landing page 2026-10-03).

Per event family, per release-anchored minute window (DST-correct, hub clock):
  volume, mean |1m return| (bp), max 1m range (ticks), volume-active share;
  event-day session totals (volume, session range) vs the non-event-session
  distribution (medians) — distributional description only.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python 6A_a4_events.py
Writes: 6A_a4_events.json
"""
from __future__ import annotations

import importlib.util
import os
import zoneinfo

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "sixA_deep_lib", os.path.join(_HERE, "6A_deep_lib.py"))
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)

OUT = os.path.join(_HERE, "6A_a4_events.json")
SYD_TZ = zoneinfo.ZoneInfo("Australia/Sydney")

WINDOWS = [("pre_60_5", -60, -5), ("around_pm5", -5, 5), ("post_5_15", 5, 15),
           ("post_15_60", 15, 60), ("post_60_240", 60, 240)]


def held_bars() -> pd.DataFrame:
    sess = pd.read_parquet(f"{L.CACHE}/session_contract.parquet")
    sess = sess[~sess["contract"].str.startswith("STRAY")]
    sess["session_date"] = pd.to_datetime(sess["session_date"])
    ch = L.calendar_chain(sess, quarterly_only=True)
    ch["session_date"] = pd.to_datetime(ch["session_date"])
    bars = pd.read_parquet(f"{L.CACHE}/outright_1m.parquet",
                           columns=["dt", "contract", "session_date", "open",
                                    "high", "low", "close", "volume",
                                    "ct_minute", "syd_min"])
    bars["session_date"] = pd.to_datetime(bars["session_date"])
    pairs = set(zip(ch["session_date"], ch["held"]))
    mask = [(d, c) in pairs for d, c in zip(bars["session_date"], bars["contract"])]
    fb = bars[pd.Series(mask, index=bars.index)].sort_values("dt").reset_index(drop=True)
    fb["ret1"] = fb["close"] / fb["close"].shift(1) - 1
    fb.loc[fb["contract"] != fb["contract"].shift(1), "ret1"] = np.nan
    fb["range_t"] = (fb["high"] - fb["low"]) / L.TICK
    return fb, sess


def window_stats(fb, t0_utc, a, b):
    """Bars with dt in [t0+a, t0+b) minutes (UTC minutes)."""
    lo = t0_utc + pd.Timedelta(minutes=a)
    hi = t0_utc + pd.Timedelta(minutes=b)
    w = fb[(fb["dt"] >= lo) & (fb["dt"] < hi)]
    if len(w) == 0:
        return {"n": 0}
    return {
        "n": int(len(w)), "volume": int(w["volume"].sum()),
        "mean_abs_ret_bp": float(np.nanmean(np.abs(w["ret1"])) * 1e4
                                 if w["ret1"].notna().any() else None),
        "max_range_ticks": float(w["range_t"].max()),
        "share_minutes_with_volume": float((w["volume"] > 0).mean()),
    }


def baseline_stats(fb, events, t_local_col, center, a, b, exclude_dates):
    """Same hub-clock window on all non-event sessions (median across sessions)."""
    col = fb[t_local_col]
    lo, hi = center + a, center + b
    w = fb[(col >= lo) & (col < hi) & (~fb["session_date"].isin(exclude_dates))]
    per = w.groupby("session_date").agg(
        vol=("volume", "sum"), rng=("range_t", "max"),
        absr=("ret1", lambda s: float(np.nanmean(np.abs(s))) if s.notna().any() else np.nan))
    return {
        "n_sessions": int(len(per)),
        "median_volume": float(per["vol"].median()) if len(per) else None,
        "median_max_range_ticks": float(per["rng"].median()) if len(per) else None,
        "median_mean_abs_ret_bp": float(per["absr"].median() * 1e4)
        if len(per) and per["absr"].notna().any() else None,
    }


def main():
    fb, sess = held_bars()

    # ---------------- RBA events -------------------------------------------
    rba = L.load_rba_decisions()
    rba = rba[(rba["announcement_date"] >= "2020-01-01") &
              (rba["announcement_date"] <= "2026-10-01")].copy()
    rba["is_special"] = rba["announcement_date"].dt.dayofweek != 1  # Tue regular
    rba_events = []
    for r in rba.itertuples():
        day = pd.Timestamp(r.announcement_date)
        t0_utc = (pd.Timestamp(day, tz=SYD_TZ) +
                  pd.Timedelta(hours=14, minutes=30)).tz_convert("UTC")
        row = {"announcement_date": str(day.date()),
               "effective_date": str(r.effective_date.date()),
               "change_pp": r.change_pp, "cash_rate_pct": r.cash_rate_pct,
               "special_flag": bool(r.is_special),
               "t0_utc": str(t0_utc)}
        for wname, a, b in WINDOWS:
            row[wname] = window_stats(fb, t0_utc, a, b)
        rba_events.append(row)
    rba_dates = set(pd.to_datetime(rba["announcement_date"]).dt.normalize())
    rba_base = {wname: baseline_stats(fb, rba_events, "syd_min", 14 * 60 + 30,
                                      a, b, rba_dates)
                for wname, a, b in WINDOWS}

    # event-day session totals vs non-event sessions (distributional)
    daily = fb.groupby("session_date").agg(
        vol=("volume", "sum"), rng_ticks=("range_t", "max")).reset_index()
    syd_vol = fb.assign(
        s=fb["volume"].where(fb["dt"].dt.tz_convert(L.SYD).dt.hour.between(7, 16))
    ).groupby("session_date")["s"].sum()
    daily["syd_share"] = daily["session_date"].map(syd_vol).fillna(0) / daily["vol"]
    non_ev = daily[~daily["session_date"].isin(rba_dates)]
    ev = daily[daily["session_date"].isin(rba_dates)]
    rba_day = {
        "n_event_sessions": int(len(ev)),
        "event_median_volume": float(ev["vol"].median()) if len(ev) else None,
        "non_event_median_volume": float(non_ev["vol"].median()),
        "event_median_session_range_ticks": float(ev["rng_ticks"].median()) if len(ev) else None,
        "non_event_median_session_range_ticks": float(non_ev["rng_ticks"].median()),
        "event_median_syd_share_pct": float(ev["syd_share"].median() * 100) if len(ev) else None,
        "non_event_median_syd_share_pct": float(non_ev["syd_share"].median() * 100),
        "note": "descriptive distribution comparison only; NO mean-return conditioning (law)",
    }

    # split by decision type: change vs hold (volume/vol only — no returns)
    change_dates = set(pd.to_datetime(
        rba[rba["change_pp"] != 0]["announcement_date"]).dt.normalize())
    hold_dates = rba_dates - change_dates
    ch_ev = daily[daily["session_date"].isin(change_dates)]
    ho_ev = daily[daily["session_date"].isin(hold_dates)]
    rba_day["change_days"] = {
        "n": int(len(ch_ev)),
        "median_volume": float(ch_ev["vol"].median()) if len(ch_ev) else None,
        "median_range_ticks": float(ch_ev["rng_ticks"].median()) if len(ch_ev) else None,
    }
    rba_day["hold_days"] = {
        "n": int(len(ho_ev)),
        "median_volume": float(ho_ev["vol"].median()) if len(ho_ev) else None,
        "median_range_ticks": float(ho_ev["rng_ticks"].median()) if len(ho_ev) else None,
    }

    # ---------------- FOMC events ------------------------------------------
    fomc = L.load_fomc()
    fomc = fomc[(fomc["date"] >= "2020-01-01") & (fomc["date"] <= "2026-10-01")]
    fomc_events = []
    for r in fomc.itertuples():
        tm = r.time_et or pd.Timestamp("13:00").time()
        flagged = r.time_et is None
        t0_utc = (pd.Timestamp(r.date) +
                  pd.Timedelta(hours=tm.hour, minutes=tm.minute)).tz_localize(
            "America/New_York").tz_convert("UTC")
        row = {"date": str(r.date), "time_et": str(tm),
               "time_flagged_convention": flagged,
               "t0_utc": str(t0_utc)}
        for wname, a, b in WINDOWS:
            row[wname] = window_stats(fb, t0_utc, a, b)
        fomc_events.append(row)
    fomc_dates = set(pd.to_datetime(fomc["date"]).dt.normalize())
    fomc_base = {wname: baseline_stats(fb, fomc_events, "ct_minute", 13 * 60,
                                       a, b, fomc_dates)
                 for wname, a, b in WINDOWS}
    ev = daily[daily["session_date"].isin(fomc_dates)]
    non_ev = daily[~daily["session_date"].isin(fomc_dates)]
    fomc_day = {
        "n_event_sessions": int(len(ev)),
        "event_median_volume": float(ev["vol"].median()) if len(ev) else None,
        "non_event_median_volume": float(non_ev["vol"].median()),
        "event_median_session_range_ticks": float(ev["rng_ticks"].median()) if len(ev) else None,
        "non_event_median_session_range_ticks": float(non_ev["rng_ticks"].median()),
        "note": "FOMC lands 13:00 CT INSIDE the measured session (v1: only event family visible in RTH)",
    }

    out = {
        "meta": {
            "lane": "DEEP-6A", "analysis": "A4 event-day anatomy",
            "window": ["2020-01-02", "2026-09-30"],
            "laws": ("descriptive timing anatomy only; NO conditional mean-return "
                     "tables; no surprise classification (none in corpus)"),
            "abs_cpi_labour_force": "NOT_RUN — no ABS family in nonprice corpus (erratum vs dispatch packet); abs.gov.au historical release dates not exposed on listing pages (landing-page future-release time 11:30 AEDT verified 2026-10-03)",
            "us_cpi_nfp": "NOT_RUN — bls_gate empty in nonprice corpus",
        },
        "rba": {
            "n_events": len(rba_events),
            "n_change_meetings": int((rba["change_pp"] != 0).sum()),
            "n_hold_meetings": int((rba["change_pp"] == 0).sum()),
            "special_meetings_flagged": [e["announcement_date"] for e in rba_events
                                         if e["special_flag"]],
            "announcement_convention": "14:30 Sydney on effective_date - 1 AU business day; specials (non-Tuesday announcements) flagged — anchor uncertainty disclosed",
            "windows_median_across_events": {
                wname: {
                    "median_volume": float(np.median([e[wname]["volume"]
                                                      for e in rba_events
                                                      if e[wname]["n"] > 0])),
                    "median_mean_abs_ret_bp": float(np.median(
                        [e[wname]["mean_abs_ret_bp"] for e in rba_events
                         if e[wname].get("mean_abs_ret_bp") is not None])),
                } for wname, _, _ in WINDOWS},
            "baseline_non_event_sessions_same_clock": rba_base,
            "event_day_vs_non_event_day": rba_day,
            "events": rba_events,
        },
        "fomc": {
            "n_events": len(fomc_events),
            "windows_median_across_events": {
                wname: {
                    "median_volume": float(np.median([e[wname]["volume"]
                                                      for e in fomc_events
                                                      if e[wname]["n"] > 0])),
                    "median_mean_abs_ret_bp": float(np.median(
                        [e[wname]["mean_abs_ret_bp"] for e in fomc_events
                         if e[wname].get("mean_abs_ret_bp") is not None])),
                } for wname, _, _ in WINDOWS},
            "baseline_non_event_sessions_same_clock": fomc_base,
            "event_day_vs_non_event_day": fomc_day,
            "events": fomc_events,
        },
    }
    L.jdump(out, OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
