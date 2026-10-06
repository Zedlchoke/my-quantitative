"""gen_fixtures — RMM-6A roll table (synthetic mirror; commit outputs).

The MEASURED 6A chain (fx_ja/6a_roll_measured.json, sha 4172d288...): 27 rolls,
span 2020-03-17..2026-09-14, mode split 21 abrupt / 6 gradual (explicit
cease-guard variant); baseline-code k=5 has 2 CEASE-GUARD VIOLATIONS
(2024-12-17 held dead 6AZ4 while 6AH5 traded 55,675 lots; 2026-06-16 held dead
6AM6 while 6AU6 traded 55,533) — the explicit cease-guard variant is the
MANDATORY chain-builder (law-pending ADOPT-D9).

This fixture carries a 4-row synthetic mirror: two era-2 rolls (one abrupt,
one gradual) + two era-1 rolls (era tick caveat: pre-2020-11-23 descriptive
only) + the two injected violation rows for the mandatory-guard proof.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROLL_ROWS = [
    {"switch_date": "2024-12-17", "old_contract": "6AZ4", "new_contract": "6AH5",
     "held_bars": 0, "session_bars_total": 1440,
     "held_volume": 0, "new_volume": 55675},          # baseline VIOLATION #1 (era-2)
    {"switch_date": "2026-06-16", "old_contract": "6AM6", "new_contract": "6AU6",
     "held_bars": 0, "session_bars_total": 1440,
     "held_volume": 0, "new_volume": 55533},          # baseline VIOLATION #2 (era-2)
    {"switch_date": "2024-06-17", "old_contract": "6AM4", "new_contract": "6AU4",
     "held_bars": 950, "session_bars_total": 1440,
     "held_volume": 92000, "new_volume": 90000},      # era-2 GRADUAL (crossover)
    {"switch_date": "2020-06-16", "old_contract": "6AM0", "new_contract": "6AU0",
     "held_bars": 500, "session_bars_total": 1440,
     "held_volume": 50000, "new_volume": 48000},      # era-1 GRADUAL (era tick caveat)
    {"switch_date": "2020-09-15", "old_contract": "6AU0", "new_contract": "6AZ0",
     "held_bars": 700, "session_bars_total": 1440,
     "held_volume": 68000, "new_volume": 66000},      # era-1 GRADUAL (era caveat)
]


def main() -> None:
    with open(HERE / "rmm6a_roll_rows.json", "w", encoding="utf-8") as fh:
        json.dump({
            "schema": "adapt_fx_ja/rmm_roll_table@1",
            "symbol": "6A",
            "note": "synthetic mirror of the MEASURED 6A chain "
                    "(6a_roll_measured.json sha 4172d288...): 27 rolls, "
                    "explicit-guard 21 abrupt / 6 gradual; baseline k=5 "
                    "violations 2024-12-17 + 2026-06-16",
            "measured_counts": {"rolls": 27, "abrupt_explicit": 21,
                                "gradual_explicit": 6,
                                "baseline_violations": 2},
            "roll_rows": ROLL_ROWS,
        }, fh, indent=1)
    print("roll rows", len(ROLL_ROWS))


if __name__ == "__main__":
    main()
