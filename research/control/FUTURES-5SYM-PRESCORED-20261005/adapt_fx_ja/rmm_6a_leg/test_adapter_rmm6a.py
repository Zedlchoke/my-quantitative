"""test_adapter_rmm6a — pytest proofs for the RMM-6A contingency machinery (synthetic).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest rmm_6a_leg -q
Exit code recorded in dispatch/handoff_ADAPT-FXJA.json.
"""
from __future__ import annotations

import pytest

import fx_common as fc
from conftest import load_fixture
from rmm_6a_leg.adapter import (DRAFT_IDS, RMM6AAdapter, MEASURED,
                                rmm6a_freeze_check)

AD = RMM6AAdapter()
TABLE = load_fixture("rmm_6a_leg", "rmm6a_roll_rows.json")
ROLL_ROWS = TABLE["roll_rows"]


def test_contingency_identity_counts_match_frozen_table():
    assert len(DRAFT_IDS) == 4
    assert DRAFT_IDS == ["C6A0-CONT-RMM-MCOMPRESS-REV-D1",
                         "C6A0-CONT-RMM-MCOMPRESS-REV-D30M",
                         "C6A0-CONT-RMM-MCOMPRESS-CONT-D1",
                         "C6A0-CONT-RMM-MCOMPRESS-CONT-D30M"]
    frozen = fc.frozen_6a_table_citation()
    assert frozen["identities_by_category"]["RMM_6A_contingency"] == 4
    assert frozen["total"] == 0 and frozen["total_if_ever_lifted"] == 26


def test_measured_mode_split_and_mandatory_explicit_guard():
    assert MEASURED == {"rolls": 27, "abrupt_explicit": 21,
                        "gradual_explicit": 6, "baseline_violations": 2}
    obs = AD.build_observables(ROLL_ROWS)
    d = obs["guard_disclosure"]
    assert d["n_violations"] == 2
    assert d["violations"] == ["2024-12-17", "2026-06-16"]
    assert d["explicit_guard_mandatory"] is True
    assert d["chain_sign_flip"] is True   # RMM K6(a): chain choice flips no sign


def test_chain_classifications_and_era_caveat():
    obs = AD.build_observables(ROLL_ROWS)
    by_date = {r["switch_date"]: r for r in obs["fixture_chain"]["explicit_cease_guard"]}
    assert by_date["2024-12-17"]["mode"] == "ABRUPT"
    assert by_date["2024-06-17"]["mode"] == "GRADUAL"
    assert by_date["2020-06-16"]["era"] == "era1"
    assert "descriptive-only" in by_date["2020-06-16"]["era_law"]
    assert by_date["2024-06-17"]["era_law"] == "era2"
    # the extremal abrupt stratum (n=3) fails any fold floor, pre-declared
    assert obs["extremal_abrupt_stratum"]["fold_floor"]["passes"] is False


def test_intent_refusal_chain_d5_then_d2():
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        AD.order_intent(None, {}, "C6A0-CONT-RMM-MCOMPRESS-REV-D1",
                        session_date="2024-06-17")
    assert ei.value.slot_id == "P5-FXJA-D5"
    fc.GUARDS["P5-FXJA-D5"] = {"signed_by": "TEST-ONLY-NOT-A-SIGNATURE"}
    try:
        with pytest.raises(fc.RefusedPendingOwnerDecision) as ei2:
            AD.order_intent(None, {}, "C6A0-CONT-RMM-MCOMPRESS-REV-D1",
                            session_date="2024-06-17")
        assert ei2.value.slot_id == "P5-FXJA-D2"
    finally:
        fc.GUARDS["P5-FXJA-D5"] = None
    assert all(v is None for v in fc.GUARDS.values())


def test_era1_switch_session_refusal():
    with pytest.raises(fc.RefusedEra1NoTradeIntent):
        AD.order_intent(None, {}, "C6A0-CONT-RMM-MCOMPRESS-CONT-D1",
                        session_date="2020-06-16")


def test_freeze_check_refuses():
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        rmm6a_freeze_check()
    assert ei.value.slot_id == "P5-FXJA-D5"
