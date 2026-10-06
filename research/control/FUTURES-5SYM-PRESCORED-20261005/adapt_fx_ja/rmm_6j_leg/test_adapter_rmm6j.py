"""test_adapter_rmm6j — pytest proofs for the RMM-6J leg machinery (synthetic).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest rmm_6j_leg -q
Exit code recorded in dispatch/handoff_ADAPT-FXJA.json.
"""
from __future__ import annotations

import pytest

import fx_common as fc
from conftest import load_fixture
from rmm_6j_leg.adapter import DRAFT_IDS, RMM6JAdapter

AD = RMM6JAdapter()
PANEL = load_fixture("rmm_6j_leg", "rmm6j_panel_rollweek.json")
CALENDAR = load_fixture("rmm_6j_leg", "rmm6j_calendar.json")
ROLL_TABLE = load_fixture("rmm_6j_leg", "rmm6j_roll_rows.json")
ROLL_ROWS = ROLL_TABLE["roll_rows"]
SWITCH = "2022-09-20"


def test_identity_enumeration_exact_four_ids():
    assert DRAFT_IDS == ["FB6J1-RMM-MCOMPRESS-REV-D1", "FB6J1-RMM-MCOMPRESS-REV-D30M",
                         "FB6J1-RMM-MCOMPRESS-CONT-D1", "FB6J1-RMM-MCOMPRESS-CONT-D30M"]


def test_chain_law_2022_09_20_baseline_vs_explicit_guard():
    """The law case, element by element (SPEC_6J s.5): baseline keeps held=U2
    on the dead session (bar-level chain drops it); the explicit cease-guard
    variant force-switches at that close, effective t+1."""
    chain = fc.build_roll_chain(ROLL_ROWS)
    base = {b["switch_date"]: b for b in chain["baseline_k5"]}
    expl = {e["switch_date"]: e for e in chain["explicit_cease_guard"]}
    b, e = base[SWITCH], expl[SWITCH]
    assert b["mode"] == e["mode"] == "ABRUPT"
    assert b["trigger"] == e["trigger"] == "cease_guard_no_bars"
    assert b["held_contract_effective"] == "6JU2"
    assert b["held_dead_session_dropped"] is True
    assert e["cease_guard_forced_switch"] is True
    assert e["held_contract_effective"] == "6JZ2"
    assert "decided at close t, effective t+1" == b["timing_law"] == e["timing_law"]
    # sign-non-flip law (RMM K6(a)): the old->new order is identical in both
    assert chain["sign_flip_check"]["old_to_new_order_identical"] is True
    # gradual roll classification
    assert base["2026-09-14"]["mode"] == "GRADUAL"
    assert base["2026-09-14"]["trigger"] == "k5_crossover"
    assert chain["baseline_violations"] == [SWITCH]
    assert chain["mode_counts"] == {"abrupt": 1, "gradual": 2}


def test_guard_disclosure_law_pending_d9():
    d = fc.measure_and_disclose_guard_violations(fc.build_roll_chain(ROLL_ROWS))
    assert d["n_violations"] == 1 and d["violations"] == [SWITCH]
    assert d["chain_sign_flip"] is True
    assert "mandatory" in d["mandatory_law"].lower()
    # the 6A law: >=2 violations make the explicit guard the MANDATORY builder
    d2 = fc.measure_and_disclose_guard_violations(fc.build_roll_chain(
        ROLL_ROWS + [{"switch_date": "2026-06-16", "old_contract": "6AM6",
                      "new_contract": "6AU6", "held_bars": 0,
                      "session_bars_total": 1357, "held_volume": 0,
                      "new_volume": 55533}]))
    assert d2["n_violations"] == 2 and d2["explicit_guard_mandatory"] is True


def test_panel_proves_the_cease_guard_anatomy():
    """Exchange OPEN on the switch date: dying U2 prints ZERO bars; receiving
    Z2 trades the full day (synthetic mirror of 125,303 lots / 1,357 bars)."""
    sw_bars = fc.session_bars(PANEL, SWITCH)
    assert all(b["contract"] == "6JZ2" for b in sw_bars)
    assert len(sw_bars) == 1380   # 23h synthetic full day
    prev = fc.session_bars(PANEL, "2022-09-19")
    assert all(b["contract"] == "6JU2" for b in prev)   # U2's final prior session


def test_observables_event_stacking_and_extremal_stratum():
    obs = AD.build_observables(PANEL, CALENDAR, ROLL_ROWS)
    # roll 3's switch (2022-09-21) stacks on an injected BoJ MPM day
    assert "X_EVENT_STACKING_CENTRAL_BANK" in obs["exclusions"]["2022-09-21"]
    assert obs["extremal_dates"] == [SWITCH]
    assert obs["extremal_stratum_law"]["passes"] is False   # n=3 fails the floor
    assert obs["guard_disclosure"]["n_violations"] == 1
    assert obs["event_clock_law"] == "switch session t; decided at close t, effective t+1"


def test_signal_is_descriptive_only_switch_move():
    sig = AD.signal(PANEL, CALENDAR, SWITCH, receiving_contract="6JZ2")
    assert sig["knowable"] is True and sig["tail"] == "DN"
    assert sig["switch_move"] < 0   # engineered walk: switch-day index 3 -> -1 tick/bar
    assert "descriptive only" in sig["machinery_note"]
    # PIT: truncated at midday, the switch-session move is partial but lawful
    half = fc.at_local(SWITCH, 12, 0, fc.JST)
    sig_h = AD.signal(PANEL, CALENDAR, SWITCH, "6JZ2", asof=half)
    assert sig_h["knowable"] is True and sig_h["switch_move"] != sig["switch_move"]


def test_role_b_intent_refuses_even_synthetic_d2_then_d1():
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        AD.order_intent(PANEL, CALENDAR, "FB6J1-RMM-MCOMPRESS-REV-D1", SWITCH)
    assert ei.value.slot_id == "P5-FXJA-D1"   # ceiling gate fires FIRST
    # with the ceiling hypothetically signed, D2 still refuses (never self-ratified)
    fc.GUARDS["P5-FXJA-D1"] = {"signed_by": "TEST-ONLY-NOT-A-SIGNATURE"}
    try:
        with pytest.raises(fc.RefusedPendingOwnerDecision) as ei2:
            AD.order_intent(PANEL, CALENDAR, "FB6J1-RMM-MCOMPRESS-REV-D1", SWITCH)
        assert ei2.value.slot_id == "P5-FXJA-D2"
    finally:
        fc.GUARDS["P5-FXJA-D1"] = None   # restore the unsigned law
    assert all(v is None for v in fc.GUARDS.values())


def test_real_data_refusal_and_foreign_identity():
    real = {**PANEL, "provenance": "REAL_CHAIN"}
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        AD.signal(real, CALENDAR, SWITCH, "6JZ2")
    assert ei.value.slot_id == "P5-FXJA-D1"
    with pytest.raises(ValueError):
        AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-UP-D1-S2", SWITCH)


def test_bind_option_jc_refusal_chain():
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        fc.bind_option_6j("J-C")
    assert ei.value.slot_id == "P5-FXJA-D1"
    assert fc.frozen_6a_table_citation()["sha256"].startswith("1a96b8ea")
