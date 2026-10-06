"""reference_expected — INDEPENDENT expected-value computation for F2 fixtures.

No adapter import: every number is a literal formula over the engineered
fixture constants. Run after gen_fixtures.py (from adapt_nq/, PYTHONPATH=.):
  ../../.venv/bin/python f2_macro_0730/fixtures/reference_expected.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
MULT = 20.0
ATR = 60.0


def gross(entry: float, exit_: float, direction: int) -> float:
    return round((exit_ - entry) * direction * MULT, 6)


def sl_tp(entries: dict, dirs: dict) -> tuple[dict, dict]:
    sl, tp = {}, {}
    for iid, e in entries.items():
        d = dirs[iid]
        sl[iid] = e - ATR if d == 1 else e + ATR
        tp[iid] = e + 2 * ATR if d == 1 else e - 2 * ATR
    return sl, tp


def main() -> None:
    up_entries = {"FBNQ1-F2-CONT-UP-D0-S2": 15006.25, "FBNQ1-F2-CONT-UP-D30-S2": 15130.00,
                  "FBNQ1-F2-REV-UP-D0-S2": 15006.25, "FBNQ1-F2-REV-UP-D30-S2": 15130.00,
                  "FBNQ1-F2-ALW-D0-S2": 15006.25}
    up_dirs = {"FBNQ1-F2-CONT-UP-D0-S2": 1, "FBNQ1-F2-CONT-UP-D30-S2": 1,
               "FBNQ1-F2-REV-UP-D0-S2": -1, "FBNQ1-F2-REV-UP-D30-S2": -1,
               "FBNQ1-F2-ALW-D0-S2": 1}
    up_sl, up_tp = sl_tp(up_entries, up_dirs)
    up_exits = {"FBNQ1-F2-CONT-UP-D0-S2": (15126.25, "TP"),
                "FBNQ1-F2-CONT-UP-D30-S2": (15150.00, "SESSION_CLOSE"),
                # 07:37 bar [15006.25, 15126.50] contains BOTH the short's SL
                # (15066.25) and the long's TP (15126.25): same-bar TP/SL =>
                # SL PRIORITY fires for the short (conservative fill law).
                "FBNQ1-F2-REV-UP-D0-S2": (15066.25, "SL"),
                "FBNQ1-F2-REV-UP-D30-S2": (15150.00, "SESSION_CLOSE"),
                "FBNQ1-F2-ALW-D0-S2": (15126.25, "TP")}
    up = {
        "session_date": "2023-06-13", "series": "CPI",
        "trigger_move_points": 15006.00 - 15000.00, "tail": "UP", "atr20_points": ATR,
        "entries": {"D0": 15006.25, "D30": 15130.00},
        "sl_by_id": up_sl, "tp_by_id": up_tp,
        "exits_by_id": {k: {"price": v[0], "reason": v[1]} for k, v in up_exits.items()},
        "ts_exit_TP": "2023-06-13T07:37:00-05:00",
        "gross_synthetic_usd": {iid: gross(up_entries[iid], up_exits[iid][0], up_dirs[iid])
                                for iid in up_entries},
        "tail_mismatch_ids": ["FBNQ1-F2-CONT-DN-D0-S2", "FBNQ1-F2-CONT-DN-D30-S2",
                              "FBNQ1-F2-REV-DN-D0-S2", "FBNQ1-F2-REV-DN-D30-S2"],
    }

    dn_entries = {"FBNQ1-F2-CONT-DN-D0-S2": 15091.75, "FBNQ1-F2-CONT-DN-D30-S2": 15091.75,
                  "FBNQ1-F2-REV-DN-D0-S2": 15091.75, "FBNQ1-F2-REV-DN-D30-S2": 15091.75}
    dn_dirs = {"FBNQ1-F2-CONT-DN-D0-S2": -1, "FBNQ1-F2-CONT-DN-D30-S2": -1,
               "FBNQ1-F2-REV-DN-D0-S2": 1, "FBNQ1-F2-REV-DN-D30-S2": 1}
    dn_sl, dn_tp = sl_tp(dn_entries, dn_dirs)
    dn = {
        "session_date": "2023-07-12", "series": "CPI",
        "trigger_move_points": 15092.00 - 15100.00, "tail": "DN", "atr20_points": ATR,
        "entries": {"D0": 15091.75, "D30": 15091.75},
        "sl_by_id": dn_sl, "tp_by_id": dn_tp,
        "exit_price": 15040.00, "exit_reason": "SESSION_CLOSE",
        "gross_synthetic_usd": {iid: gross(dn_entries[iid], 15040.00, dn_dirs[iid])
                                for iid in dn_entries},
        "tail_mismatch_ids": ["FBNQ1-F2-CONT-UP-D0-S2", "FBNQ1-F2-CONT-UP-D30-S2",
                              "FBNQ1-F2-REV-UP-D0-S2", "FBNQ1-F2-REV-UP-D30-S2"],
    }

    ord_shdw = date(2023, 6, 15).toordinal()
    shdw_dir = 1 if (20261002 + ord_shdw) % 2 == 0 else -1
    shdw = {
        "session_date": "2023-06-15", "is_release_day": False,
        "seed": 20261002, "ordinal": ord_shdw, "shadow_direction": shdw_dir,
        "entry_price_D0": 15000.25, "exit_price": 15030.00,
        "exit_reason": "SESSION_CLOSE",
        "gross_synthetic_usd": {"FBNQ1-F2-SHDW-D0-S2": gross(15000.25, 15030.00, shdw_dir)},
    }

    no_trade = {
        "fomc_overlap_2023-09-13": "EXCLUDED: FOMC_STANDING_OUTSIDE",
        "canceled_2025-10-15": "CANCELED_CONTROL_STRATUM",
        "era_gated_2019-06-12": "ERA_GATED",
        "shdw_on_release_day": {"session_date": "2023-06-13",
                                "identity": "FBNQ1-F2-SHDW-D0-S2",
                                "reason": "SHDW_ON_RELEASE_DAY"},
        "vintage_unknown_at_decision_date": {
            "session_date": "2023-06-13", "doctored_known_by": "2023-06-14",
            "reason": "NOT_EVENT_MEMBER",
            "law": "current-calendar inference forbidden (known_by > D does not exist)"},
        "flat_anchor": {"identity": "FBNQ1-F2-FLAT",
                        "reason": "FLAT_ANCHOR_ZERO_TRADES"},
    }

    d5 = {
        "pin_date": "2026-02-13",
        "with_pin": "build_observables succeeds; 2026-02-13 routes as a scheduled "
                    "release day (aggregate-only fixture: the anchor bar is absent, "
                    "so a core arm resolves SIGNAL_NOT_KNOWABLE_AT_ASOF)",
        "with_pin_no_trade_reason": "SIGNAL_NOT_KNOWABLE_AT_ASOF",
        "pin_stripped": "REFUSED_D5_PIN_MISSING (RC-3.4 hard refusal)",
    }

    pit = {
        "asof_points": ["2023-06-13T07:31:00-05:00", "2023-06-13T09:00:00-05:00",
                        "2023-06-13T15:59:00-05:00"],
        "law": "truncated panels (rows > asof removed) must give identical outputs",
    }

    manifest = {
        "schema": "adapt_nq/expected_manifest@1",
        "family": "NQ-F2",
        "status": "PROPOSED-DRAFT (synthetic fixtures; outcome-blind)",
        "identity_counts": {"core": 8, "controls": 3, "minimal": 11},
        "expected": {"cpi_up_day": up, "cpi_dn_day": dn, "shdw_day": shdw,
                     "no_trade": no_trade, "d5_pin": d5, "pit": pit},
    }
    (HERE / "EXPECTED_MANIFEST.json").write_text(json.dumps(manifest, indent=1),
                                                 encoding="utf-8")
    print("F2 EXPECTED_MANIFEST.json written; shadow_direction(2023-06-15) =", shdw_dir)


if __name__ == "__main__":
    main()
