"""test_adapter_jf2 — pytest proofs for the 6J-JF2 MOF regime adapter (synthetic).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest jf2_mof_regime -q
Exit code recorded in dispatch/handoff_ADAPT-FXJA.json.
"""
from __future__ import annotations

import pytest

import fx_common as fc
from conftest import load_fixture
from jf2_mof_regime.adapter import (CONTROL_IDS, CORE_IDS, DRAFT_IDS, JF2Adapter,
                                    jf2_freeze_check, shuffle_disclosure_labels)

AD = JF2Adapter()
PANEL = load_fixture("jf2_mof_regime", "jf2_panel_host.json")
CALENDAR = load_fixture("jf2_mof_regime", "jf2_calendar.json")
OPS = CALENDAR["mof_ops"]
OP_DAY = OPS[0]["op_date"]              # 2026-02-15 (an MPM day, tail UP)
DISCLOSURE_DAY = OPS[0]["disclosure_date"]  # 2026-03-15
HELD = [s["session_date"] for s in PANEL["sessions"]]


def test_identity_enumeration_matches_budget():
    assert CORE_IDS == ["FB6J1-JF2-DRIFT-UP-REG-S2", "FB6J1-JF2-DRIFT-DN-REG-S2",
                        "FB6J1-JF2-REV-UP-REG-S2", "FB6J1-JF2-REV-DN-REG-S2"]
    assert CONTROL_IDS == ["FB6J1-PLA-JF2", "FB6J1-ALW-JF2", "FB6J1-CLK-JF2"]
    assert len(DRAFT_IDS) == 7   # per host (IDENTITY_BUDGET_6J s.2 JF2 block)


def test_lag_law_label_invisible_before_disclosure():
    """THE PIT boundary this family exists to enforce: on the op day itself —
    BEFORE the ~1-month disclosure — the regime label must read NON_REGIME.
    A signal at asof T must not use the intervention label known only later."""
    reg = AD.regime_at(CALENDAR, PANEL, OP_DAY,
                       asof=f"{OP_DAY}T23:59:59+00:00")
    assert reg["regime_label"] == "NON_REGIME"
    assert reg["visible_ops"] == []            # nothing disclosed yet
    assert OP_DAY not in reg["in_window_op_dates"]


def test_lag_law_label_visible_from_disclosure():
    reg = AD.regime_at(CALENDAR, PANEL, DISCLOSURE_DAY,
                       asof=f"{DISCLOSURE_DAY}T23:59:59+00:00")
    assert reg["regime_label"] == "REGIME"
    assert OP_DAY in reg["visible_ops"]


def test_same_day_op_knowledge_refuses():
    with pytest.raises(fc.RefusedMofLagLawViolation):
        fc.require_same_day_op_visibility(op_date=OP_DAY, asof=OP_DAY)


def test_reg_conditioned_intent_gates_on_label():
    # before disclosure -> NON_REGIME -> NO-TRADE
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF2-DRIFT-UP-REG-S2", OP_DAY)
    assert out["no_trade"] and out["no_trade_reason"] == "REGIME_CONDITION_NOT_MET"
    # after disclosure -> REGIME -> the host arm resolves.
    # DISCLOSURE_DAY (2026-03-15) is the SL-hit MPM fixture day (window DN):
    # DRIFT-DN routes to the host and resolves SELL (6J price terms).
    out2 = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF2-DRIFT-DN-REG-S2",
                           DISCLOSURE_DAY)
    assert out2["no_trade"] is False
    assert out2["identity_id"] == "FB6J1-JF2-DRIFT-DN-REG-S2"
    assert out2["regime_context"]["regime_label"] == "REGIME"
    assert out2["direction"] == -1 and out2["side"] == "SELL"


def test_reg_tail_mismatch_routes_through_host():
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF2-DRIFT-UP-REG-S2",
                          DISCLOSURE_DAY)   # disclosure day tail is DN
    assert out["no_trade"] and out["no_trade_reason"] == "TAIL_MISMATCH"


def test_zone_threshold_refuses_p5_hypo_od4():
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        fc.jf2_zone_threshold()
    assert ei.value.slot_id == "P5-HYPO-OD4"
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei2:
        jf2_freeze_check()
    assert ei2.value.slot_id == "P5-HYPO-OD4"


def test_null_era_check_clean():
    audit = fc.jf2_null_era_check(OPS)
    assert audit["clean"] is True and audit["ops_in_era"] == []
    contam = fc.jf2_null_era_check(OPS + [{"op_date": "2021-05-10",
                                           "disclosure_date": "2021-06-10"}])
    assert contam["clean"] is False and contam["ops_in_era"] == ["2021-05-10"]


def test_clk_negative_control_never_trades():
    # CLK demands a null-era session (non-regime) and still never trades
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-CLK-JF2", "2024-01-15")
    assert out["no_trade"] and out["regime_context"]["regime_label"] == "NON_REGIME"


def test_pla_shuffle_deterministic_single_seed():
    s1 = shuffle_disclosure_labels(OPS, seed=fc.C1_SEED)
    s2 = shuffle_disclosure_labels(OPS, seed=fc.C1_SEED)
    assert s1 == s2 and s1 != OPS
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-PLA-JF2", DISCLOSURE_DAY)
    assert out["regime_context"]["shuffled"] is True
    assert out["regime_context"]["seed"] == fc.C1_SEED


def test_real_data_refusal_and_slot_dependencies():
    real = {**PANEL, "provenance": "REAL_CHAIN"}
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        AD.signal(real, CALENDAR, OP_DAY)
    assert ei.value.slot_id == "P5-FXJA-D1"
    it = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF2-DRIFT-UP-REG-S2",
                         DISCLOSURE_DAY)
    assert set(fc.SLOT_DEPENDENCIES) <= set(it["decision_slot_dependencies"])


def test_host_gates_inherit_exclusions():
    excl = AD.apply_exclusions(CALENDAR, PANEL)
    assert excl.get("2025-10-15") == ["X_MOF_OP_DAY"]
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF2-DRIFT-UP-REG-S2", "2025-10-15")
    assert out["no_trade"] and out["no_trade_reason"].startswith("EXCLUDED: ")


def test_no_own_signal_law():
    sig = AD.signal(PANEL, CALENDAR, OP_DAY)
    assert sig["own_signal_law"].startswith("NONE")
    assert "host_signal" in sig and "regime" in sig
