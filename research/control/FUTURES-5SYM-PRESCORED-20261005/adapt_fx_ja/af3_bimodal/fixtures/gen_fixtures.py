"""gen_fixtures — AF3 (6A contingency, PB3 PARK) synthetic panels.

Engineered calendar [DRAFT-CODE]: 22 era-2 sessions (14-day spacing,
2023-07-17..2024-05-06, all proven quarters) + a K4 contamination day +
a coverage-fail day. NOT real data.

Session bars (Sydney calendar-day session labels): Sydney window 09:30-11:30
(120 nominal bars, +1 tick/bar walk -> range [BASE, BASE+119t]); post-window:
flat at range_hi - 1t for 40 bars, then the engineered break:
  ROT day: +2 ticks/bar from 12:10 Syd (10:10 Shanghai — OUTSIDE the China window)
  ABS day: -2 ticks/bar from 12:10 Syd
  K4 day : +2 ticks/bar from 11:31 Syd (09:31 Shanghai — INSIDE the China window)
  coverage-fail day: only 90 of 120 window bars (0.75 < 0.80)
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
               for i in range(22)]
ROT_DAY = EVENT_DATES[-1]
ABS_DAY = EVENT_DATES[-2]
RBA_DAY = EVENT_DATES[-3]          # excluded (RBA adjacency)
FOMC_DAY = "2024-04-24"
K4_DAY = "2024-05-20"              # trigger INSIDE the Shanghai data window
COV_DAY = "2024-05-21"


def build_panel() -> dict:
    bars, sessions = [], []
    contract = "6AM4"
    all_dates = sorted(set(EVENT_DATES) | {K4_DAY, COV_DAY, FOMC_DAY})
    for sd in all_dates:
        tick = fc.sixa_tick(sd)
        wbars = kit.walk_session(sd, kit.at_local(sd, 9, 30, fc.SYD),
                                 kit.at_local(sd, 11, 30, fc.SYD),
                                 BASE, tick, 500, contract, tick=tick)
        if sd == COV_DAY:
            wbars = wbars[:90]      # coverage 90/120 = 0.75 < 0.80
        hi = float(wbars[-1]["close"])
        if sd == K4_DAY:
            flat_end = (11, 31)     # break at 11:31 Syd = 09:31 Shanghai (IN window)
        else:
            flat_end = (12, 10)     # break at 12:10 Syd = 10:10 Shanghai (OUT)
        flat = kit.walk_session(sd, kit.at_local(sd, 11, 30, fc.SYD),
                                kit.at_local(sd, flat_end[0], flat_end[1], fc.SYD),
                                round(hi - 1 * tick, 10), 0.0, 700, contract, tick=tick)
        px = float(flat[-1]["close"])
        if sd == ROT_DAY or sd == K4_DAY:
            bstep = 2 * tick
        elif sd == ABS_DAY:
            bstep = -2 * tick
        else:
            bstep = 0.0
        post = kit.walk_session(sd, kit.at_local(sd, flat_end[0], flat_end[1], fc.SYD),
                                kit.at_local(sd, 14, 30, fc.SYD),
                                px, bstep, 900, contract, tick=tick)
        allb = wbars + flat + post
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
        "symbol": "6A",
        "family": "AF3",
        "contingency": "CONTINGENCY-PB3-PARK (SPEC_6A_CONTINGENCY banner)",
        "contract": {"tick_size": fc.SIXA_ERA2_TICK,
                     "tick_value_usd": fc.SIXA_ERA2_TICK_VALUE_USD,
                     "multiplier": fc.SIXA_MULTIPLIER},
        "sessions": sessions,
        "bars": bars,
    }


def build_calendar() -> dict:
    return {
        "rba_decision_dates": [RBA_DAY],
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
    with open(HERE / "af3_panel_sydney.json", "w", encoding="utf-8") as fh:
        json.dump(panel, fh, indent=0)
    with open(HERE / "af3_calendar.json", "w", encoding="utf-8") as fh:
        json.dump(calendar, fh, indent=1)
    with open(HERE / "probe_dates.json", "w", encoding="utf-8") as fh:
        json.dump({"rot_day": ROT_DAY, "abs_day": ABS_DAY, "rba_day": RBA_DAY,
                   "fomc_day": FOMC_DAY, "k4_day": K4_DAY, "cov_day": COV_DAY},
                  fh, indent=1)
    print("bars", len(panel["bars"]), "sessions", len(panel["sessions"]),
          "ROT", ROT_DAY, "ABS", ABS_DAY)


if __name__ == "__main__":
    main()
