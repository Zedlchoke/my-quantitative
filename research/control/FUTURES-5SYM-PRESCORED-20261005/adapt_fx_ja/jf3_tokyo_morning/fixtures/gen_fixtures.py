"""gen_fixtures — JF3 synthetic panels (deterministic; commit outputs).

Engineered calendar [DRAFT-CODE]: 24 weekday sessions 2026-06-01..2026-06-30
(JST calendar-day session labels; synthetic). NOT real data.

Session structure (per session, bars 09:00-17:00 JST = 00:00-08:00 UTC):
  - Tokyo window 09:00-11:30 JST: +1 tick/bar walk from BASE -> range
    [BASE, BASE+149t], 150/150 nominal bars (coverage 1.0)
  - non-event post-window: flat at BASE+148t (below range_hi) -> NO break
  - UP-break day: post-window continues +1t/bar -> first close ABOVE range_hi
  - DN-break day: post-window falls -3t/bar -> close below range_lo
  - coverage-fail day: window carries only 100 of 150 bars (coverage 0.667)
Daily high/low = [BASE, BASE+149t] on every normal session -> daily
ATR(20) = 149 ticks exactly.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import fx_common as fc
import fx_fixture_kit as kit

HERE = Path(__file__).resolve().parent
TICK = fc.SIXJ_TICK
BASE = 0.0065000

SESSION_DATES = []
_d = date(2026, 6, 1)
while len(SESSION_DATES) < 24:
    if _d.weekday() < 5:
        SESSION_DATES.append(_d.isoformat())
    _d += timedelta(days=1)

UP_DAY = SESSION_DATES[22]
DN_DAY = SESSION_DATES[23]
BOJ_DAY = SESSION_DATES[21]
MOF_DAY = SESSION_DATES[20]
COV_DAY = SESSION_DATES[19]


def build_panel() -> dict:
    bars, sessions = [], []
    contract = "6JP6"   # synthetic front label
    for sd in SESSION_DATES:
        wbars = kit.walk_session(sd, kit.at_local(sd, 9, 0, fc.JST),
                                 kit.at_local(sd, 11, 30, fc.JST),
                                 BASE, TICK, 500, contract, tick=TICK)
        if sd == COV_DAY:
            wbars = wbars[:100]            # coverage 100/150 = 0.667 < 0.80
        px_end = float(wbars[-1]["close"]) if wbars else BASE
        if sd == UP_DAY:
            pstep = TICK
        elif sd == DN_DAY:
            pstep = -3 * TICK
        else:
            pstep = 0.0
            px_end = round_to_grid(BASE + 148 * TICK)
        pbars = kit.walk_session(sd, kit.at_local(sd, 11, 30, fc.JST),
                                 kit.at_local(sd, 17, 0, fc.JST),
                                 px_end, pstep, 800, contract, tick=TICK)
        allb = wbars + pbars
        bars.extend(allb)
        sessions.append(kit.session_agg(
            sd, open_=float(allb[0]["open"]), high=max(float(b["high"]) for b in allb),
            low=min(float(b["low"]) for b in allb), close=float(allb[-1]["close"]),
            volume=sum(int(b["volume"]) for b in allb),
            last_bar_utc=allb[-1]["ts"], contract=contract))
    sessions.sort(key=lambda s: s["session_date"])
    bars.sort(key=lambda b: (b["session_date"], b["ts"]))
    return {
        "schema": "adapt_fx_ja/synthetic_panel@1",
        "provenance": "SYNTHETIC",
        "symbol": "6J",
        "family": "JF3",
        "contract": {"tick_size": TICK, "tick_value_usd": fc.SIXJ_TICK_VALUE_USD,
                     "multiplier": fc.SIXJ_MULTIPLIER,
                     "quote_direction": fc.QUOTE_DIRECTION_6J},
        "sessions": sessions,
        "bars": bars,
    }


def round_to_grid(px: float) -> float:
    return round(round(px / TICK) * TICK, 10)


def build_calendar() -> dict:
    return {
        "boj_mpm_dates": [BOJ_DAY],
        "mof_disclosure_dates": [MOF_DAY],
        "mof_op_days": [],
        "quarters_unproven": ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4",
                              "UNIDENTIFIED-A", "UNIDENTIFIED-B"],
        "early_close_times_not_obtained": [],
        "roll_guard_flagged_days": [],
        "fomc_statement_days": [],
    }


def main() -> None:
    panel = build_panel()
    calendar = build_calendar()
    with open(HERE / "jf3_panel_tokyo.json", "w", encoding="utf-8") as fh:
        json.dump(panel, fh, indent=0)
    with open(HERE / "jf3_calendar.json", "w", encoding="utf-8") as fh:
        json.dump(calendar, fh, indent=1)
    with open(HERE / "probe_dates.json", "w", encoding="utf-8") as fh:
        json.dump({"up_day": UP_DAY, "dn_day": DN_DAY, "boj_day": BOJ_DAY,
                   "mof_day": MOF_DAY, "cov_day": COV_DAY}, fh, indent=1)
    print("bars", len(panel["bars"]), "sessions", len(panel["sessions"]),
          "UP_DAY", UP_DAY, "DN_DAY", DN_DAY)


if __name__ == "__main__":
    main()
