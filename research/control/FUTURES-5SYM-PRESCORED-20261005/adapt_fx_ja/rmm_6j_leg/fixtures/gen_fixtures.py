"""gen_fixtures — RMM-6J roll/cease-guard week (deterministic; commit outputs).

The 2022-09-20 LAW CASE (SPEC_6J s.5; fx_ja/6j_cease_guard_2022.json), synthetic
reconstruction: exchange OPEN; dying 6JU2 has ZERO bars on the switch date while
receiving 6JZ2 trades a full 1,357-bar day; the baseline k=5 keeps held=U2 for
the 09-20 row (bar-level chain drops the session) while the explicit cease-guard
variant force-switches at that session's close, effective 09-21.

Chain inputs are INJECTED rows (switch tables class); the bars panel proves the
cease-guard anatomy. 10 synthetic sessions around the switch so the switch+K
(K=5) horizon is representable.
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

SESSION_DATES = [ (date(2022, 9, 15) + timedelta(days=i)).isoformat()
                  for i in range(10)
                  if (date(2022, 9, 15) + timedelta(days=i)).weekday() < 5 ]
SWITCH_DATE = "2022-09-20"      # index 3 in SESSION_DATES (Tue)
U2 = "6JU2"
Z2 = "6JZ2"
# Injected switch table (synthetic mirror of the measured 27-roll chain):
ROLL_ROWS = [
    {"switch_date": SWITCH_DATE, "old_contract": U2, "new_contract": Z2,
     "held_bars": 0, "session_bars_total": 1357,
     "held_volume": 0, "new_volume": 125303},
    {"switch_date": "2026-09-14", "old_contract": "6JU6", "new_contract": "6JZ6",
     "held_bars": 900, "session_bars_total": 1357,
     "held_volume": 90000, "new_volume": 88000},
    {"switch_date": "2022-09-21", "old_contract": "6JX0", "new_contract": "6JZ0",
     "held_bars": 900, "session_bars_total": 1357,
     "held_volume": 77000, "new_volume": 76000},
]


def build_panel() -> dict:
    bars, sessions = [], []
    for i, sd in enumerate(SESSION_DATES):
        step = TICK if i % 2 == 0 else -TICK
        if sd == SWITCH_DATE:
            # the law case: U2 prints NOTHING; Z2 trades the full day
            day_bars = kit.walk_session(sd, kit.at_local(sd, 0, 0, fc.JST),
                                        kit.at_local(sd, 23, 0, fc.JST),
                                        BASE, step, 500, Z2, tick=TICK)
        else:
            held = U2 if i < 3 else Z2
            day_bars = kit.walk_session(sd, kit.at_local(sd, 0, 0, fc.JST),
                                        kit.at_local(sd, 23, 0, fc.JST),
                                        BASE, step, 500, held, tick=TICK)
        bars.extend(day_bars)
        sessions.append(kit.session_agg(
            sd, open_=float(day_bars[0]["open"]), high=max(float(b["high"]) for b in day_bars),
            low=min(float(b["low"]) for b in day_bars), close=float(day_bars[-1]["close"]),
            volume=sum(int(b["volume"]) for b in day_bars),
            last_bar_utc=day_bars[-1]["ts"], contract=(U2 if i < 3 else Z2)))
    return {
        "schema": "adapt_fx_ja/synthetic_panel@1",
        "provenance": "SYNTHETIC",
        "symbol": "6J",
        "family": "RMM6J",
        "contract": {"tick_size": TICK, "tick_value_usd": fc.SIXJ_TICK_VALUE_USD,
                     "multiplier": fc.SIXJ_MULTIPLIER,
                     "quote_direction": fc.QUOTE_DIRECTION_6J},
        "sessions": sessions,
        "bars": bars,
    }


def build_calendar() -> dict:
    return {
        "boj_mpm_dates": ["2022-09-21"],   # roll 3's switch stacks on a BoJ day
        "mof_disclosure_dates": [],
        "mof_op_days": [],
        "quarters_unproven": [],
        "early_close_times_not_obtained": [],
        "roll_guard_flagged_days": [SWITCH_DATE],
        "fomc_statement_days": [],
    }


def main() -> None:
    panel = build_panel()
    calendar = build_calendar()
    with open(HERE / "rmm6j_panel_rollweek.json", "w", encoding="utf-8") as fh:
        json.dump(panel, fh, indent=0)
    with open(HERE / "rmm6j_calendar.json", "w", encoding="utf-8") as fh:
        json.dump(calendar, fh, indent=1)
    with open(HERE / "rmm6j_roll_rows.json", "w", encoding="utf-8") as fh:
        json.dump({"schema": "adapt_fx_ja/rmm_roll_table@1", "symbol": "6J",
                   "note": "synthetic mirror of the measured 27-roll chain "
                           "(rmm_mode_ledger.json 19 abrupt / 8 gradual)",
                   "measured_counts": {"abrupt": 19, "gradual": 8, "total": 27},
                   "roll_rows": ROLL_ROWS}, fh, indent=1)
    print("bars", len(panel["bars"]), "sessions", len(panel["sessions"]),
          "switch", SWITCH_DATE)


if __name__ == "__main__":
    main()
