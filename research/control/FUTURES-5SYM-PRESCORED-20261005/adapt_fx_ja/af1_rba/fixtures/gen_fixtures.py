"""gen_fixtures — AF1 (6A contingency, PB3 PARK) synthetic panels.

Engineered calendar [DRAFT-CODE]: 22 synthetic RBA decision dates (every 21
days ending 2024-05-07, all era-2) + a FOMC statement day + its spillover day
+ an ERA-1 RBA date (2020-06-02, the refusal fixture). NOT real RBA data.

Session bars: 14:00-17:30 Sydney local (zoneinfo-stamped UTC), 210 bars.
Decision window 14:30-14:35 Syd (DECLARED convention anchor); window move
engineered +-4 ticks/bar (era-2 grid 5e-05); era-1 bars on the 1e-04 grid
($10/tick, NO-BACK-CAST law).
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import fx_common as fc
import fx_fixture_kit as kit

HERE = Path(__file__).resolve().parent
BASE = 0.6700

EVENT_DATES = [(date(2023, 7, 17) + timedelta(days=14 * i)).isoformat()
               for i in range(22)]          # ends 2024-05-07; all in proven quarters
UP_DAY = EVENT_DATES[-1]                     # 2024-05-07, TP-hit showcase
DN_DAY = EVENT_DATES[-2]                     # 2024-04-16, SL-hit showcase
FLAT_DAY = EVENT_DATES[-3]
FOMC_DAY = "2024-05-01"
FOMC_SPILL_DAY = "2024-05-02"
ERA1_DAY = "2020-06-02"                      # the era-1 refusal fixture


def build_panel() -> dict:
    bars, sessions = [], []
    contract = "6AM4"   # synthetic front label
    all_dates = sorted(set(EVENT_DATES) | {FOMC_DAY, FOMC_SPILL_DAY, ERA1_DAY})
    for sd in all_dates:
        tick = fc.sixa_tick(sd)                # ERA-AWARE grid (1e-4 vs 5e-5)
        step = 0.0
        if sd in EVENT_DATES:
            step = (4 * tick if EVENT_DATES.index(sd) % 2 == 0 else -4 * tick)
            if sd == UP_DAY:
                step = 4 * tick
            if sd == DN_DAY:
                step = -4 * tick
            if sd == FLAT_DAY:
                step = 0.0
        # pre-window 14:00-14:30 flat; window 14:30-14:35 engineered;
        # post 14:35-17:30 continues +-1 tick/bar (era-aware tick)
        pre = kit.walk_session(sd, kit.at_local(sd, 14, 0, fc.SYD),
                               kit.at_local(sd, 14, 30, fc.SYD),
                               BASE, 0.0, 400, contract, tick=tick)
        win = kit.walk_session(sd, kit.at_local(sd, 14, 30, fc.SYD),
                               kit.at_local(sd, 14, 35, fc.SYD),
                               BASE, step, 700, contract, tick=tick)
        px_end = float(win[-1]["close"])
        if sd == UP_DAY:
            pstep = 1 * tick      # favorable continuation -> TP hit on CONT-UP
        elif sd == DN_DAY:
            pstep = 1 * tick      # adverse burst after a DOWN window -> SL hit
        else:
            pstep = 0.0
        post = kit.walk_session(sd, kit.at_local(sd, 14, 35, fc.SYD),
                                kit.at_local(sd, 17, 30, fc.SYD),
                                px_end, pstep, 900, contract, tick=tick)
        allb = pre + win + post
        bars.extend(allb)
        w_hi = max(float(b["high"]) for b in win)
        w_lo = min(float(b["low"]) for b in win)
        sessions.append(kit.session_agg(
            sd, open_=float(allb[0]["open"]), high=max(float(b["high"]) for b in allb),
            low=min(float(b["low"]) for b in allb), close=float(allb[-1]["close"]),
            volume=sum(int(b["volume"]) for b in allb),
            last_bar_utc=allb[-1]["ts"], contract=contract,
            extra={"window_ranges": {"rba": round(w_hi - w_lo, 12)}}))
    sessions.sort(key=lambda s: s["session_date"])
    bars.sort(key=lambda b: (b["session_date"], b["ts"]))
    return {
        "schema": "adapt_fx_ja/synthetic_panel@1",
        "provenance": "SYNTHETIC",
        "symbol": "6A",
        "family": "AF1",
        "contingency": "CONTINGENCY-PB3-PARK (SPEC_6A_CONTINGENCY banner)",
        "contract": {"tick_size": fc.SIXA_ERA2_TICK,
                     "tick_value_usd": fc.SIXA_ERA2_TICK_VALUE_USD,
                     "multiplier": fc.SIXA_MULTIPLIER,
                     "era_table": {"era1": [fc.SIXA_ERA1_TICK, fc.SIXA_ERA1_TICK_VALUE_USD],
                                   "era2": [fc.SIXA_ERA2_TICK, fc.SIXA_ERA2_TICK_VALUE_USD]}},
        "sessions": sessions,
        "bars": bars,
    }


def build_calendar() -> dict:
    return {
        "rba_decision_dates": sorted(EVENT_DATES + [ERA1_DAY]),
        "fomc_statement_days": [FOMC_DAY],
        "quarters_unproven": ["2023-Q1", "2023-Q2"],
        "early_close_times_not_obtained": [],
        "roll_guard_flagged_days": [],
        "mof_op_days": [],
        "mof_disclosure_dates": [],
    }


def main() -> None:
    panel = build_panel()
    calendar = build_calendar()
    with open(HERE / "af1_panel_rba.json", "w", encoding="utf-8") as fh:
        json.dump(panel, fh, indent=0)
    with open(HERE / "af1_calendar.json", "w", encoding="utf-8") as fh:
        json.dump(calendar, fh, indent=1)
    print("bars", len(panel["bars"]), "sessions", len(panel["sessions"]),
          "UP", UP_DAY, "DN", DN_DAY, "era1", ERA1_DAY)


if __name__ == "__main__":
    main()
