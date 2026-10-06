"""gen_fixtures — builds the committed F3 synthetic panel (deterministic).

Engineered held-daily closes (all 0.25-grid):
  s1..s6   alternating (no run)
  s7..s11  DOWN run  (-10,-20,-20,-20,-20)  -> trigger at s11
  s12..s16 holding window for run 1; s14 = ROLL SWITCH -> ROLL_CROSS_UNADJUSTED
  s13..s17 UP run (+20 x5, fresh after s12's -25) -> trigger at s17
  s18..s22 holding window for run 2 (no switch)   -> full intents
  s23..s27 DOWN run 2 -> trigger at s27; entry s28 = FOMC day -> EXCLUDED
Run: PYTHONPATH=. ../../.venv/bin/python f3_run_rev/fixtures/gen_fixtures.py
"""
from __future__ import annotations

import json
from pathlib import Path

from fixture_kit import session_agg

HERE = Path(__file__).resolve().parent

CLOSES = {
    # s1..s6 alternating, no run
    "2023-08-01": 15000.00, "2023-08-02": 15010.00, "2023-08-03": 15005.00,
    "2023-08-07": 15015.00, "2023-08-08": 15010.00, "2023-08-09": 15020.00,
    # DOWN run 1: rets -10,-20,-20,-20,-20 ending 2023-08-16 (5 consecutive)
    "2023-08-10": 15010.00, "2023-08-11": 14990.00, "2023-08-14": 14970.00,
    "2023-08-15": 14950.00,
    "2023-08-16": 14930.00,   # TRIGGER day run 1 (5th consecutive down ret)
    "2023-08-17": 14905.00,   # run-1 entry session (ret -25 extends the run; no new trigger)
    "2023-08-18": 14925.00,   # +20 UP run starts (ROLL SWITCH session)
    "2023-08-21": 14945.00, "2023-08-22": 14965.00, "2023-08-23": 14985.00,
    "2023-08-24": 15005.00,   # TRIGGER day run 2 (5 consecutive up rets)
    "2023-08-25": 15015.00,   # run-2 entry session
    "2023-08-28": 15005.00,   # s19 (-10)
    "2023-08-29": 15015.00,   # s20 (+10)
    "2023-08-30": 14995.00,   # s21 (-20; keeps 08-31's ret positive)
    "2023-08-31": 15000.00,   # s22: exit session run 2 (close; ret +5 breaks the down run)
    # DOWN run 3: rets -10,-20,-20,-20,-20 ending 2023-09-08 (5 consecutive)
    "2023-09-01": 14990.00,
    "2023-09-05": 14970.00, "2023-09-06": 14950.00, "2023-09-07": 14930.00,
    "2023-09-08": 14910.00,   # TRIGGER day run 3
    "2023-09-11": 14900.00,   # run-3 entry session = FOMC day (excluded)
    "2023-09-12": 14920.00, "2023-09-13": 14900.00,  # tail sessions (alternating)
}
OPENS = {
    "2023-08-17": 14935.00,   # run-1 entry open
    "2023-08-25": 15010.00,   # run-2 entry open
    "2023-09-11": 14905.00,   # run-3 entry open (excluded anyway)
}
LAST_BAR = {d: "15:59" for d in CLOSES}

SESSIONS = sorted(CLOSES)


def main() -> None:
    switch = "2023-08-18"
    sessions = []
    for d in SESSIONS:
        contract = "NQU3_2023" if d < switch else "NQZ3_2023"
        o = OPENS.get(d, round(CLOSES[d] - 2.50, 2))
        sessions.append(session_agg(
            d, open_=o, high=max(o, CLOSES[d]) + 5.00, low=min(o, CLOSES[d]) - 5.00,
            close=CLOSES[d], volume=250_000, rth_core_coverage=1.0,
            last_bar_ct=LAST_BAR[d], contract=contract))
    panel = {
        "schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
        "symbol": "NQ", "contract": "NQU3_2023/NQZ3_2023", "family": "NQ-F3",
        "note": "synthetic held-daily fixture; engineered closes; not market data",
        "sessions": sessions,
        "bars": [],
        "rolls": [{"switch_date": switch, "old_contract": "NQU3_2023",
                   "new_contract": "NQZ3_2023", "k": 5,
                   "spread_adjustment_factor": 1.015,
                   "note": "k=5 volume-crossover, decided t-1, held from t"}],
        "calendar": {
            "fomc_statements": [
                {"date": "2023-09-11", "time_et": "14:00",
                 "statement_file": "monetary20230911a.html"}],
            "bls_vintage": [], "early_close_not_transcribed": [],
            "quarters_unproven": []},
    }
    (HERE / "f3_panel_daily.json").write_text(json.dumps(panel, indent=1),
                                              encoding="utf-8")
    print("F3 fixtures written to", HERE)


if __name__ == "__main__":
    main()
