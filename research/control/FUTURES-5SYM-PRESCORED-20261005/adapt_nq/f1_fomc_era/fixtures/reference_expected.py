"""reference_expected — INDEPENDENT expected-value computation for F1 fixtures.

This is the manifest generator required by the lane task ("each fixture carries
its EXPECTED signal/intent outcomes in a manifest you compute independently").
It does NOT import the adapter: every number below is a literal formula over
the engineered fixture constants, computed straight from the generator's
documented price paths. Run after gen_fixtures.py:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python reference_expected.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
MULT = 20.0          # $/pt (spec arithmetic chain; symbol_contracts.json NQ)
ATR = 60.0           # engineered: every prior session ranges exactly 60.00


def gross(entry: float, exit_: float, direction: int) -> float:
    """SYNTHETIC-ARITHMETIC sanity number only — never a PnL claim."""
    return round((exit_ - entry) * direction * MULT, 6)


def sl_tp_by_id(entries: dict, tails: dict) -> tuple[dict, dict]:
    """SL = entry -/+ 1.0*ATR; TP = entry +/- 2*SL_dist, per identity."""
    sl, tp = {}, {}
    for iid, e in entries.items():
        d = tails[iid]
        s = e - ATR if d == 1 else e + ATR
        sl[iid] = s
        tp[iid] = e + 2 * ATR if d == 1 else e - 2 * ATR
    return sl, tp


def main() -> None:
    ord_wed = date(2023, 6, 21).toordinal()
    shdw_dir = 1 if (20261002 + ord_wed) % 2 == 0 else -1

    up_entries = {"FBNQ1-F1-CONT-UP-D0-S2": 15006.25, "FBNQ1-F1-CONT-UP-D30-S2": 15010.00,
                  "FBNQ1-F1-REV-UP-D0-S2": 15006.25, "FBNQ1-F1-REV-UP-D30-S2": 15010.00,
                  "FBNQ1-F1-ALW-D0-S2": 15006.25}
    up_dirs = {"FBNQ1-F1-CONT-UP-D0-S2": 1, "FBNQ1-F1-CONT-UP-D30-S2": 1,
               "FBNQ1-F1-REV-UP-D0-S2": -1, "FBNQ1-F1-REV-UP-D30-S2": -1,
               "FBNQ1-F1-ALW-D0-S2": 1}
    up_sl, up_tp = sl_tp_by_id(up_entries, up_dirs)
    up = {
        "session_date": "2023-06-14",
        "trigger_move_points": 15006.00 - 15000.00,
        "tail": "UP",
        "atr20_points": ATR,
        "entries": {"D0": 15006.25, "D30": 15010.00},
        "exit_price": 15050.00, "exit_reason": "SESSION_CLOSE",
        "sl_by_id": up_sl, "tp_by_id": up_tp,
        "gross_synthetic_usd": {
            "FBNQ1-F1-CONT-UP-D0-S2": gross(15006.25, 15050.00, +1),
            "FBNQ1-F1-CONT-UP-D30-S2": gross(15010.00, 15050.00, +1),
            "FBNQ1-F1-REV-UP-D0-S2": gross(15006.25, 15050.00, -1),
            "FBNQ1-F1-REV-UP-D30-S2": gross(15010.00, 15050.00, -1),
            "FBNQ1-F1-ALW-D0-S2": gross(15006.25, 15050.00, +1),
        },
        "tail_mismatch_ids": ["FBNQ1-F1-CONT-DN-D0-S2", "FBNQ1-F1-CONT-DN-D30-S2",
                              "FBNQ1-F1-REV-DN-D0-S2", "FBNQ1-F1-REV-DN-D30-S2"],
    }
    dn_entries = {"FBNQ1-F1-CONT-DN-D0-S2": 15091.75, "FBNQ1-F1-CONT-DN-D30-S2": 15088.00,
                  "FBNQ1-F1-REV-DN-D0-S2": 15091.75, "FBNQ1-F1-REV-DN-D30-S2": 15088.00}
    dn_dirs = {"FBNQ1-F1-CONT-DN-D0-S2": -1, "FBNQ1-F1-CONT-DN-D30-S2": -1,
               "FBNQ1-F1-REV-DN-D0-S2": 1, "FBNQ1-F1-REV-DN-D30-S2": 1}
    dn_sl, dn_tp = sl_tp_by_id(dn_entries, dn_dirs)
    dn = {
        "session_date": "2023-07-26",
        "trigger_move_points": 15092.00 - 15100.00,
        "tail": "DN",
        "atr20_points": ATR,
        "entries": {"D0": 15091.75, "D30": 15088.00},
        "exit_price": 15040.00, "exit_reason": "SESSION_CLOSE",
        "sl_by_id": dn_sl, "tp_by_id": dn_tp,
        "gross_synthetic_usd": {
            "FBNQ1-F1-CONT-DN-D0-S2": gross(15091.75, 15040.00, -1),
            "FBNQ1-F1-CONT-DN-D30-S2": gross(15088.00, 15040.00, -1),
            "FBNQ1-F1-REV-DN-D0-S2": gross(15091.75, 15040.00, +1),
            "FBNQ1-F1-REV-DN-D30-S2": gross(15088.00, 15040.00, +1),
        },
        "tail_mismatch_ids": ["FBNQ1-F1-CONT-UP-D0-S2", "FBNQ1-F1-CONT-UP-D30-S2",
                              "FBNQ1-F1-REV-UP-D0-S2", "FBNQ1-F1-REV-UP-D30-S2"],
    }
    era_entries = {"FBNQ1-F1-CONT-UP-D0-S2": 14576.25, "FBNQ1-F1-CONT-UP-D30-S2": 14576.25,
                   "FBNQ1-F1-REV-UP-D0-S2": 14576.25, "FBNQ1-F1-REV-UP-D30-S2": 14576.25}
    era_dirs = {"FBNQ1-F1-CONT-UP-D0-S2": 1, "FBNQ1-F1-CONT-UP-D30-S2": 1,
                "FBNQ1-F1-REV-UP-D0-S2": -1, "FBNQ1-F1-REV-UP-D30-S2": -1}
    era_sl, era_tp = sl_tp_by_id(era_entries, era_dirs)
    era_a = {
        "session_date": "2015-09-17",
        "trigger_move_points": 14576.00 - 14570.00,
        "tail": "UP",
        "era": "A",
        "era_close_ct": 16 * 60 + 15,
        "last_bar_ct": "16:14",
        "atr20_points": ATR,
        "entries": {"D0": 14576.25, "D30": 14576.25},
        "exit_price": 14580.00, "exit_reason": "SESSION_CLOSE",
        "sl_by_id": era_sl, "tp_by_id": era_tp,
        "gross_synthetic_usd": {
            "FBNQ1-F1-CONT-UP-D0-S2": gross(14576.25, 14580.00, +1),
            "FBNQ1-F1-CONT-UP-D30-S2": gross(14576.25, 14580.00, +1),
            "FBNQ1-F1-REV-UP-D0-S2": gross(14576.25, 14580.00, -1),
            "FBNQ1-F1-REV-UP-D30-S2": gross(14576.25, 14580.00, -1),
        },
    }
    shdw = {
        "session_date": "2023-06-21",
        "weekday": "Wednesday", "is_fomc_day": False,
        "seed": 20261002, "ordinal": ord_wed, "shadow_direction": shdw_dir,
        "entry_price_D0": 14900.25, "exit_price": 14930.00,
        "exit_reason": "SESSION_CLOSE",
        "gross_synthetic_usd": {"FBNQ1-F1-SHDW-D0-S2": gross(14900.25, 14930.00, shdw_dir)},
    }
    no_trade = {
        "2023-06-16": "EXCLUDED: H1_RTH_COVERAGE_LT_060",
        "2026-01-19": "EXCLUDED: H1_RTH_COVERAGE_LT_060,H2_H3_2026_DUBIOUS",
        "2023-11-24": "EXCLUDED: H1_RTH_COVERAGE_LT_060,H4_EARLY_CLOSE_NOT_TRANSCRIBED",
        "NOT_EVENT_MEMBER_example": {"session_date": "2023-06-21",
                                     "identity": "FBNQ1-F1-CONT-UP-D0-S2",
                                     "reason": "NOT_EVENT_MEMBER"},
        "SHDW_NOT_WEDNESDAY_example": {"session_date": "2023-06-15",
                                       "identity": "FBNQ1-F1-SHDW-D0-S2",
                                       "reason": "SHDW_NOT_WEDNESDAY"},
        "SHDW_FOMC_DAY_MATCH_example": {"session_date": "2023-06-14",
                                        "identity": "FBNQ1-F1-SHDW-D0-S2",
                                        "reason": "SHDW_FOMC_DAY_MATCH"},
        "FLAT_anchor_example": {"identity": "FBNQ1-F1-FLAT",
                                "reason": "FLAT_ANCHOR_ZERO_TRADES"},
    }
    pit = {
        "asof_points": ["2023-06-14T13:01:00-05:00", "2023-06-14T14:00:00-05:00",
                        "2023-06-14T15:59:00-05:00"],
        "law": "truncated panels (rows > asof removed) must give identical outputs",
    }
    costs = {
        "default_variant": "A (P5-NQ3 unsigned, basis-only default)",
        "per_side_usd": {"S1": 23.50, "S2": 28.50, "S3": 33.50},
        "rt_usd_S2_x1.0": 57.00,
    }
    manifest = {
        "schema": "adapt_nq/expected_manifest@1",
        "family": "NQ-F1",
        "status": "PROPOSED-DRAFT (synthetic fixtures; outcome-blind)",
        "identity_counts": {"core": 8, "controls": 3, "minimal": 11},
        "expected": {"up_day": up, "dn_day": dn, "era_a_day": era_a,
                     "shdw_wednesday": shdw, "no_trade": no_trade,
                     "pit": pit, "costs": costs},
    }
    (HERE / "EXPECTED_MANIFEST.json").write_text(json.dumps(manifest, indent=1),
                                                 encoding="utf-8")
    print("F1 EXPECTED_MANIFEST.json written; shadow_direction(2023-06-21) =", shdw_dir)


if __name__ == "__main__":
    main()
