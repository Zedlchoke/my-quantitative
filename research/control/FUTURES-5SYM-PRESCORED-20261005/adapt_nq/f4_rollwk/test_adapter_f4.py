"""test_adapter_f4 — pytest proofs for the NQ-F4 ROLLWK machinery (synthetic).

MACHINERY-ONLY: Role-B intents must refuse; Role-A audit + roll calendar +
event stacking are the deliverables under test.
"""
from __future__ import annotations

import copy
import json

import pytest

import nq_common as nc
from conftest import load_expected, load_fixture
from expwitch_refusal import ExpwitchDeadAtGate
from f4_rollwk.adapter import (CONTROL_IDS, CORE_IDS, DRAFT_IDS, RoleBInteractionGateNotFormed,
                               RollWkAdapter)

AD = RollWkAdapter()


def panel() -> dict:
    return load_fixture("f4", "f4_panel_roll.json")


def test_identity_enumeration_matches_budget():
    assert CORE_IDS == ["FBNQ1-F4-CONT-UP-D0-S2", "FBNQ1-F4-CONT-DN-D0-S2",
                        "FBNQ1-F4-REV-UP-D0-S2", "FBNQ1-F4-REV-DN-D0-S2"]
    assert CONTROL_IDS == ["FBNQ1-F4-SHDW-D0-S2", "FBNQ1-F4-ALW-D0-S2",
                           "FBNQ1-F4-FLAT"]
    assert len(DRAFT_IDS) == 7
    assert nc.family_identity_counts()["NQ-F4"] == {
        "core": 4, "controls": 3, "minimal_total": 7}


def test_roll_calendar_matches_manifest():
    exp = load_expected("f4")["expected"]
    p = panel()
    rolls = AD.roll_calendar(p)
    assert len(rolls) == 1
    r = rolls[0]
    assert r["switch_date"] == exp["switch_date"]
    assert r["decided_from_data_through"] == exp["decided_from_data_through"]
    assert r["dte"] == exp["dte"]
    assert r["from_contract"] == "NQU3_2023" and r["to_contract"] == "NQZ3_2023"
    # PIT: the decision consumed data through t-1 only
    assert r["decided_from_data_through"] < r["switch_date"]


def test_pit_switch_decision_uses_only_past_volumes():
    """Deciding with volumes beyond t-1 must not be possible: mutate the switch
    session's own volumes wildly — the switch date must not move."""
    p = panel()
    bad = copy.deepcopy(p)
    for s in bad["sessions"]:
        if s["session_date"] == load_expected("f4")["expected"]["switch_date"]:
            s["cand_volumes"]["NQZ3_2023"] = 99_999_999.0
    assert [r["switch_date"] for r in AD.roll_calendar(bad)] == \
        [r["switch_date"] for r in AD.roll_calendar(p)]


def test_roll_week_membership_and_event_stacking():
    exp = load_expected("f4")["expected"]
    p = panel()
    obs = AD.build_observables(p, p["calendar"])
    assert obs["roll_week_membership"] == exp["roll_week_membership"]
    assert obs["event_stacking_flags"] == exp["event_stacking"]
    assert obs["role_b_gate"].startswith("NEEDS_EVIDENCE")


def test_role_a_audit_pass_and_fail():
    exp = load_expected("f4")["expected"]
    p = panel()
    audit = AD.role_a_audit(p)
    assert audit["pass"] is True and audit["failures"] == []
    assert audit["n_rolls"] == exp["audit_pass"]["n_rolls"]
    # strip the spread adjustment factor -> construction failure (RUN-killer)
    bad = copy.deepcopy(p)
    for s in bad["sessions"]:
        s.pop("spread_adjustment_factor", None)
    audit2 = AD.role_a_audit(bad)
    assert audit2["pass"] is False
    assert audit2["failures"][0]["code"] == \
        exp["audit_fail_when_factor_stripped"]["failure_code"]
    assert "kills the RUN" in audit2["binding"]


def test_role_b_intent_gate_refuses_every_identity():
    p = panel()
    for iid in DRAFT_IDS:
        with pytest.raises(RoleBInteractionGateNotFormed) as ei:
            AD.order_intent(p, p["calendar"], iid, exp_session())
        assert ei.value.code == "ROLE_B_INTERACTION_GATE_NOT_EVIDENCED"


def exp_session() -> str:
    return load_expected("f4")["expected"]["switch_date"]


def test_signal_is_observables_only():
    p = panel()
    sig = AD.signal(p, p["calendar"], exp_session(), None)
    assert sig["in_roll_week"] is True and sig["role_b_signal"] is None


def test_gates():
    p = panel()
    with pytest.raises(nc.RefusedPendingOwnerDecision) as ei:
        AD.build_observables({**p, "provenance": "held_volume_k5_v3"}, p["calendar"])
    assert ei.value.slot_id == "P5-NQ1"
    with pytest.raises(nc.RefusedPendingOwnerDecision):
        nc.bind_option("NQ-C")
    with pytest.raises(ExpwitchDeadAtGate):
        nc.bind_option("NQ-D")
    obs = AD.build_observables(p, p["calendar"])
    a = json.dumps(obs, sort_keys=True)
    b = json.dumps(AD.build_observables(p, p["calendar"]), sort_keys=True)
    assert a == b
