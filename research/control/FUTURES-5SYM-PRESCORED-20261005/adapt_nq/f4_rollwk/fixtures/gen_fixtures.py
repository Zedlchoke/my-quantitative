"""gen_fixtures + reference_expected — F4 ROLLWK machinery fixtures.

Volumes: old NQU3_2023 flat 200,000; new NQZ3_2023 50,000 (idx 0..7) then
260,000 (idx 8..13). Trailing-5 mean ending t-1 first exceeds the incumbent at
i=12 (window idx 7..11: mean 218,000 > 200,000) -> switch at 2023-09-13,
decided from data through 2023-09-12 (PIT), dte = 2 (expiry 2023-09-15).

Run: PYTHONPATH=. ../../.venv/bin/python f4_rollwk/fixtures/gen_fixtures.py
"""
from __future__ import annotations

import json
from pathlib import Path

from fixture_kit import session_agg

HERE = Path(__file__).resolve().parent

SESSIONS = ["2023-08-28", "2023-08-29", "2023-08-30", "2023-08-31", "2023-09-01",
            "2023-09-04", "2023-09-05", "2023-09-06", "2023-09-07", "2023-09-08",
            "2023-09-11", "2023-09-12", "2023-09-13", "2023-09-14"]
OLD, NEW = "NQU3_2023", "NQZ3_2023"
EXPIRY = "2023-09-15"          # quarterly expiry (authority-calendar class)
SWITCH_EXPECTED = "2023-09-13"  # asserted by the independent walker below


def volumes(i: int) -> dict:
    return {OLD: 200_000.0, NEW: 50_000.0 if i < 8 else 260_000.0}


def independent_rolls() -> list[str]:
    """Literal walker (independent of the adapter) for the manifest."""
    switch, held = [], OLD
    for i in range(len(SESSIONS)):
        if i >= 5:
            w = range(i - 5, i)
            m_old = sum(volumes(j)[OLD] for j in w) / 5
            m_new = sum(volumes(j)[NEW] for j in w) / 5
            cand = NEW if m_new > m_old else OLD
        else:
            cand = held
        if cand != held:
            switch.append(SESSIONS[i])
            held = cand
    return switch


def main() -> None:
    got = independent_rolls()
    assert got == [SWITCH_EXPECTED], got
    sessions = []
    for i, d in enumerate(SESSIONS):
        v = volumes(i)
        agg = session_agg(
            d, open_=15000.0, high=15030.0, low=14970.0, close=15000.0,
            volume=int(v[OLD]),  # headline volume = held incumbent until switch
            rth_core_coverage=1.0, last_bar_ct="15:59",
            contract=OLD if d < SWITCH_EXPECTED else NEW)
        agg["cand_volumes"] = v
        if d == SWITCH_EXPECTED:
            agg["spread_adjustment_factor"] = 1.012
        sessions.append(agg)
    panel = {
        "schema": "adapt_nq/synthetic_panel@1", "provenance": "SYNTHETIC",
        "symbol": "NQ", "contract": OLD, "held_contract": OLD,
        "expiry_date": EXPIRY, "family": "NQ-F4",
        "note": "synthetic roll-window fixture; engineered volumes; not market data",
        "sessions": sessions, "bars": [],
        "cease_guard_violations": 0,
        "calendar": {
            "fomc_statements": [
                {"date": "2023-09-12", "time_et": "14:00",
                 "statement_file": "monetary20230912a.html"}],
            "bls_vintage": [], "early_close_not_transcribed": [],
            "quarters_unproven": []},
    }
    (HERE / "f4_panel_roll.json").write_text(json.dumps(panel, indent=1),
                                             encoding="utf-8")

    switch = SWITCH_EXPECTED
    idx = SESSIONS.index(switch)
    window = SESSIONS[max(0, idx - 4): idx + 1]
    manifest = {
        "schema": "adapt_nq/expected_manifest@1",
        "family": "NQ-F4",
        "status": "PROPOSED-DRAFT (machinery-only; Role-B gate NOT EVIDENCED)",
        "identity_counts": {"core": 4, "controls": 3, "minimal": 7,
                            "role_a_identities": 0},
        "expected": {
            "switch_date": switch,
            "decided_from_data_through": SESSIONS[idx - 1],
            "dte": 2,
            "roll_week_membership": window,
            "event_stacking": {"2023-09-12": ["FOMC_STANDING_OUTSIDE"]},
            "audit_pass": {"pass": True, "n_failures": 0, "n_rolls": 1},
            "audit_fail_when_factor_stripped": {
                "pass": False,
                "failure_code": "MISSING_SPREAD_ADJUSTMENT",
                "binding": "kills the RUN, never the hypothesis"},
        },
    }
    (HERE / "EXPECTED_MANIFEST.json").write_text(json.dumps(manifest, indent=1),
                                                 encoding="utf-8")
    print("F4 fixtures written; switch =", got)


if __name__ == "__main__":
    main()
