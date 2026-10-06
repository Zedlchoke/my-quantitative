"""gen_fixtures — JF1 synthetic panels (deterministic; commit outputs).

Engineered calendar [DRAFT-CODE]: 26 synthetic "MPM dates" (monthly, 15th)
2024-01..2026-02 + 4 non-event control days. NOT the real BoJ calendar —
every number is synthetic; the machinery under test is window math, PIT,
signs and exclusions, never a real-data claim.

Session bars (per session_date, UTC-stamped): JST 12:00-17:00 = 03:00-08:00
UTC (300 1m bars). Window = JST [12:00, 15:30); post-window strip carries the
D1/D30M entries and the exit resolution.

Engineered moves (6J price terms; tick 5e-07):
  - 24 move days: +2 or -2 ticks/bar inside the window (tail UP/DN)
  - 1 flat day (tail undefined -> TRIGGER_FLAT)
  - last event day: post-window +10 ticks/bar -> TP hit on DRIFT-UP
  - one DN day with post-window -10 ticks/bar -> SL hit on DRIFT-DN
Non-event days: flat window, small post-window drift.
"""
from __future__ import annotations

import json
from pathlib import Path

import fx_common as fc
import fx_fixture_kit as kit

HERE = Path(__file__).resolve().parent
TICK = fc.SIXJ_TICK
BASE = 0.0065000

# 26 synthetic MPM dates: 15th of each month 2024-01 .. 2026-02
MPM_DATES = [f"{y}-{m:02d}-15"
             for y, m in ([(2024, m) for m in range(1, 13)]
                          + [(2025, m) for m in range(1, 13)]
                          + [(2026, m) for m in (1, 2, 3)])]
CONTROL_DATES = ["2024-01-16", "2024-06-17", "2025-03-17", "2025-09-16",
                 "2022-09-20",   # the cease-guard law-case date (flagged, never base)
                 "2026-07-30"]   # unverified op-window (price-only label)
# The 2026-02 event day is the TP-hit showcase; the 2026-03 event day is the
# SL-hit showcase (adverse post-window burst after a DOWN window).
TP_HIT_DATE = "2026-02-15"
SL_HIT_DATE = "2026-03-15"
FLAT_DATE = "2026-01-15"
REGIME_CHANGE_DATE = "2025-12-15"    # descriptive-only stratum member


def window_step(date: str) -> float:
    if date == FLAT_DATE:
        return 0.0
    if date == TP_HIT_DATE:
        return 2 * TICK
    if date == SL_HIT_DATE:
        return -2 * TICK
    sign = 1.0 if (MPM_DATES.index(date) % 2 == 0) else -1.0
    return sign * 2 * TICK


def post_step(date: str, in_window_last_close: float) -> float:
    if date == TP_HIT_DATE:
        return 10 * TICK          # favorable burst -> TP hit on DRIFT-UP
    if date == SL_HIT_DATE:
        return 10 * TICK          # adverse burst after a DOWN window -> SL hit
    return 0.0   # post-window strip flat after the window


def build_panel() -> dict:
    bars, sessions = [], []
    contract = "6JM6"   # synthetic front label
    for sd in MPM_DATES + CONTROL_DATES:
        wstep = window_step(sd) if sd in MPM_DATES else 0.0
        wbars = kit.walk_session(sd, kit.at_local(sd, 12, 0, fc.JST),
                                 kit.at_local(sd, 15, 30, fc.JST),
                                 BASE, wstep, 500, contract, tick=TICK)
        px_end = float(wbars[-1]["close"]) if wbars else BASE
        pstep = post_step(sd, px_end)
        pbars = kit.walk_session(sd, kit.at_local(sd, 15, 30, fc.JST),
                                 kit.at_local(sd, 17, 0, fc.JST),
                                 px_end, pstep, 800, contract, tick=TICK)
        allb = wbars + pbars
        bars.extend(allb)
        w_hi = max(float(b["high"]) for b in wbars)
        w_lo = min(float(b["low"]) for b in wbars)
        sessions.append(kit.session_agg(
            sd, open_=float(allb[0]["open"]), high=max(float(b["high"]) for b in allb),
            low=min(float(b["low"]) for b in allb), close=float(allb[-1]["close"]),
            volume=sum(int(b["volume"]) for b in allb),
            last_bar_utc=allb[-1]["ts"], contract=contract,
            extra={"window_ranges": {"mpm": round(w_hi - w_lo, 12)}}))
    sessions.sort(key=lambda s: s["session_date"])
    bars.sort(key=lambda b: (b["session_date"], b["ts"]))
    return {
        "schema": "adapt_fx_ja/synthetic_panel@1",
        "provenance": "SYNTHETIC",
        "symbol": "6J",
        "family": "JF1",
        "contract": {"tick_size": TICK, "tick_value_usd": fc.SIXJ_TICK_VALUE_USD,
                     "multiplier": fc.SIXJ_MULTIPLIER,
                     "quote_direction": fc.QUOTE_DIRECTION_6J},
        "sessions": sessions,
        "bars": bars,
    }


def build_calendar() -> dict:
    return {
        "boj_mpm_dates": list(MPM_DATES),
        "boj_mpm_regime_change_dates": [REGIME_CHANGE_DATE],
        "mof_op_days": [MPM_DATES[21]],            # ex-post universe cut
        "mof_disclosure_dates": [],
        "unverified_op_windows": ["2026-07-30"],   # price-only label, never merged
        "quarters_unproven": ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4",
                              "UNIDENTIFIED-A", "UNIDENTIFIED-B"],
        "early_close_times_not_obtained": [CONTROL_DATES[1]],  # holiday times NOT_OBTAINED
        "roll_guard_flagged_days": ["2022-09-20"],
        "fomc_statement_days": [],
    }


def main() -> None:
    panel = build_panel()
    calendar = build_calendar()
    with open(HERE / "jf1_panel_mpm.json", "w", encoding="utf-8") as fh:
        json.dump(panel, fh, indent=0)
    with open(HERE / "jf1_calendar.json", "w", encoding="utf-8") as fh:
        json.dump(calendar, fh, indent=1)
    print("bars", len(panel["bars"]), "sessions", len(panel["sessions"]))


if __name__ == "__main__":
    main()
