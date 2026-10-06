"""reference_expected — INDEPENDENT expected values for F3 fixtures.

No adapter import: run lengths and trigger dates are recomputed by a literal
walk over the engineered close table in gen_fixtures.py (duplicated here on
purpose, as an independent check).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
MULT = 20.0
K = 5
HORIZON = 5

CLOSES = [
    ("2023-08-01", 15000.00), ("2023-08-02", 15010.00), ("2023-08-03", 15005.00),
    ("2023-08-07", 15015.00), ("2023-08-08", 15010.00), ("2023-08-09", 15020.00),
    ("2023-08-10", 15010.00), ("2023-08-11", 14990.00), ("2023-08-14", 14970.00),
    ("2023-08-15", 14950.00), ("2023-08-16", 14930.00), ("2023-08-17", 14905.00),
    ("2023-08-18", 14925.00), ("2023-08-21", 14945.00), ("2023-08-22", 14965.00),
    ("2023-08-23", 14985.00), ("2023-08-24", 15005.00), ("2023-08-25", 15015.00),
    ("2023-08-28", 15005.00), ("2023-08-29", 15015.00), ("2023-08-30", 14995.00),
    ("2023-08-31", 15000.00), ("2023-09-01", 14990.00), ("2023-09-05", 14970.00),
    ("2023-09-06", 14950.00), ("2023-09-07", 14930.00), ("2023-09-08", 14910.00),
    ("2023-09-11", 14900.00), ("2023-09-12", 14920.00), ("2023-09-13", 14900.00),
]
OPENS = {"2023-08-17": 14935.00, "2023-08-25": 15010.00, "2023-09-11": 14905.00}
SWITCH = "2023-08-18"
FOMC_ENTRY = "2023-09-11"


def gross(entry: float, exit_: float, direction: int) -> float:
    return round((exit_ - entry) * direction * MULT, 6)


def main() -> None:
    # independent run-length walk
    runs, triggers, prev_sign, run, last = {}, [], 0, 0, None
    for d, c in CLOSES:
        if last is None:
            runs[d] = 0
            last = c
            continue
        ret = c - last
        s = 1 if ret > 0 else (-1 if ret < 0 else 0)
        run = run + 1 if s != 0 and s == prev_sign else (1 if s != 0 else 0)
        prev_sign = s if s != 0 else prev_sign
        runs[d] = run
        last = c
    dates = [d for d, _ in CLOSES]
    for i, (d, _) in enumerate(CLOSES):
        if runs[d] >= K and (i == 0 or runs[dates[i - 1]] < K):
            triggers.append(d)

    assert triggers == ["2023-08-16", "2023-08-24", "2023-09-08"], triggers

    def entry_exit(trig: str):
        i = dates.index(trig)
        return dates[i + 1], dates[i + HORIZON]

    e1, x1 = entry_exit("2023-08-16")   # 08-17 .. 08-23 (crosses the switch 08-18)
    e2, x2 = entry_exit("2023-08-24")   # 08-25 .. 08-31 (clean)
    close = dict(CLOSES)
    run1 = {"trigger_session": "2023-08-16", "tail": "DN", "run_len": runs["2023-08-16"],
            "entry_session": e1, "exit_session": x1,
            "no_trade_reason": "ROLL_CROSS_UNADJUSTED",
            "law": "holding window crosses the 2023-08-18 roll switch; spread-adjusted "
                   "switch-day returns are chain data"}
    entry2 = OPENS[e2]
    exit2 = close[x2]
    run2 = {
        "trigger_session": "2023-08-24", "tail": "UP", "run_len": runs["2023-08-24"],
        "entry_session": e2, "exit_session": x2,
        "entry_ref_price": entry2, "exit_ref_price": exit2,
        "exit_reason": "HORIZON_CLOSE", "holding_held_sessions": HORIZON,
        "gross_synthetic_usd": {
            "FBNQ1-F3-CONT-UP-D0-S2": gross(entry2, exit2, +1),
            "FBNQ1-F3-REV-UP-D0-S2": gross(entry2, exit2, -1),
            "FBNQ1-F3-ALW-D0-S2": gross(entry2, exit2, +1),
        },
        "tail_mismatch_ids": ["FBNQ1-F3-CONT-DN-D0-S2", "FBNQ1-F3-REV-DN-D0-S2"],
    }
    no_trigger = {"session_date": "2023-08-15", "run_len": runs["2023-08-15"],
                  "reason": "NO_TRIGGER", "law": "k=4 run does not trigger (k=5 law)"}
    ord_shdw = date.fromisoformat("2023-08-01").toordinal()
    shdw_dir = 1 if (20261002 + ord_shdw) % 2 == 0 else -1
    shdw = {"session_date": "2023-08-01", "shadow_direction": shdw_dir,
            "entry_session": "2023-08-02", "exit_session": "2023-08-09",
            "entry_ref_price": 15007.50, "exit_ref_price": close["2023-08-09"],
            "exit_reason": "HORIZON_CLOSE",
            "gross_synthetic_usd": {"FBNQ1-F3-SHDW-D0-S2":
                                    gross(15007.50, close["2023-08-09"], shdw_dir)}}
    no_trade = {
        "run3_fomc_entry": {"trigger_session": "2023-09-08",
                            "entry_session": FOMC_ENTRY,
                            "reason": "EXCLUDED: FOMC_STANDING_OUTSIDE"},
        "flat_anchor": {"identity": "FBNQ1-F3-FLAT",
                        "reason": "FLAT_ANCHOR_ZERO_TRADES"},
    }
    pit = {"asof_points": ["2023-08-24T16:00:00-05:00", "2023-08-28T20:00:00-05:00",
                           "2023-09-01T20:00:00-05:00"],
           "law": "truncated held series (sessions after asof removed) must give "
                  "identical outputs; entry open/exit close are knowable only from "
                  "the following day; pre-entry asof refuses uniformly"}
    manifest = {
        "schema": "adapt_nq/expected_manifest@1",
        "family": "NQ-F3",
        "status": "PROPOSED-DRAFT (synthetic fixtures; outcome-blind)",
        "identity_counts": {"core": 4, "controls": 3, "minimal": 7},
        "expected": {"triggers": triggers, "run1_roll_cross": run1, "run2_clean": run2,
                     "no_trigger_k4": no_trigger, "shdw": shdw, "no_trade": no_trade,
                     "pit": pit},
    }
    (HERE / "EXPECTED_MANIFEST.json").write_text(json.dumps(manifest, indent=1),
                                                 encoding="utf-8")
    print("F3 EXPECTED_MANIFEST.json written; triggers =", triggers,
          "; shdw_dir =", shdw_dir)


if __name__ == "__main__":
    main()
