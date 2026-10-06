"""test_adapter_af1 — pytest proofs for the 6A-AF1 contingency adapter (synthetic).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest af1_rba -q
Exit code recorded in dispatch/handoff_ADAPT-FXJA.json.
"""
from __future__ import annotations

import pytest

import fx_common as fc
from conftest import load_expected, load_fixture
from af1_rba.adapter import (AF1Adapter, CONTROL_IDS, CORE_IDS, DRAFT_IDS,
                             af1_freeze_check, consume_rba_decision_stamp)

AD = AF1Adapter()
PANEL = load_fixture("af1_rba", "af1_panel_rba.json")
CALENDAR = load_fixture("af1_rba", "af1_calendar.json")
EXPECTED = load_expected("af1_rba")["expected"]
UP_DAY = EXPECTED["up_day"]
DN_DAY = EXPECTED["dn_day"]
ERA1_DAY = "2020-06-02"


def test_contingency_identity_counts_match_frozen_table():
    """The FROZEN object is the 26-count table: AF1 = 8 + 3 = 11 (shapes only;
    strings are PROPOSED CONTINGENCY-PB3-PARK and never a denominator)."""
    assert len(CORE_IDS) == 8 and len(CONTROL_IDS) == 3 and len(DRAFT_IDS) == 11
    frozen = fc.frozen_6a_table_citation()
    assert frozen["identities_by_category"]["AF1_minimal_core"] == 8
    assert frozen["identities_by_category"]["AF1_controls"] == 3
    assert frozen["total"] == 0 and frozen["total_if_ever_lifted"] == 26


def test_era_law_boundary_and_ticks():
    assert fc.sixa_era_for_date("2020-11-20") == "era1"
    assert fc.sixa_era_for_date("2020-11-23") == "era2"
    assert fc.sixa_tick("2020-06-02") == 1e-04 and fc.sixa_tick(UP_DAY) == 5e-05
    assert fc.sixa_tick_value_usd("2020-06-02") == 10.0
    assert fc.sixa_tick_value_usd(UP_DAY) == 5.0


def test_era_aware_cost_binding_no_backcast_numbers():
    e1 = fc.cost_per_side_usd("6A", "2020-06-02")
    e2 = fc.cost_per_side_usd("6A", UP_DAY)
    assert e1["era"] == "era1" and e1["cost_rt_usd"] == 104.92
    assert e1["cost_rt_bp_of_notional"] == 15.1794
    assert e2["era"] == "era2" and e2["cost_rt_usd"] == 54.92
    assert e2["cost_rt_bp_of_notional"] == 8.2019   # x1.85-not-x2 law


def test_era1_refusal_is_a_code_not_a_warning():
    with pytest.raises(fc.RefusedEra1NoTradeIntent) as ei:
        AD.order_intent(PANEL, CALENDAR, CORE_IDS[0], ERA1_DAY)
    assert ei.value.code == "REFUSED_ERA1_DESCRIPTIVE_ONLY"
    assert "back-cast" in ei.value.detail
    # and the era-1 stratum is tagged descriptive-only in observables
    obs = AD.build_observables(PANEL, CALENDAR)
    strata = {e["date"]: e for e in obs["events"]}
    assert strata[ERA1_DAY]["stratum"] == "ERA1_DESCRIPTIVE_ONLY"


def test_exclusions_fomc_and_spillover_no_trade():
    excl = AD.apply_exclusions(CALENDAR, PANEL)
    assert excl == EXPECTED["expected_exclusions"]
    for sd in EXPECTED["expected_exclusions"]:
        out = AD.order_intent(PANEL, CALENDAR, CORE_IDS[0], sd)
        assert out["no_trade"] and out["no_trade_reason"].startswith("EXCLUDED: ")


def test_signal_reference_agreement_and_signs():
    assert EXPECTED["up_move"] > 0 and EXPECTED["dn_move"] < 0
    sig = AD.signal(PANEL, CALENDAR, UP_DAY)
    assert sig["tail"] == "UP" and sig["era"] == "era2"
    ref = EXPECTED["cont_up_d1"]
    got = AD.order_intent(PANEL, CALENDAR, "C6A0-CONT-AF1-DRIFT-UP-D1-S2", UP_DAY)
    assert got["no_trade"] is False and got["side"] == "BUY" == ref["side"]
    assert round(got["entry_ref_price"], 10) == round(ref["entry_ref_price"], 10)
    assert round(got["atr20_window"], 12) == round(ref["atr20_window"], 12)
    assert got["exit_reason"] == ref["exit_reason"] == "TP"
    ref2 = EXPECTED["cont_dn_d1"]
    got2 = AD.order_intent(PANEL, CALENDAR, "C6A0-CONT-AF1-DRIFT-DN-D1-S2", DN_DAY)
    assert got2["side"] == "SELL" and got2["exit_reason"] == ref2["exit_reason"]


def test_pit_not_knowable_before_1435():
    early = fc.at_local(UP_DAY, 14, 32, fc.SYD)
    t = early.isoformat()
    tr = {**PANEL, "bars": [b for b in PANEL["bars"] if fc.parse_ts(b["ts"]) <= fc.parse_ts(t)]}
    sig = AD.signal(tr, CALENDAR, UP_DAY, asof=early)
    assert sig["no_trade_reason"] == "SIGNAL_NOT_KNOWABLE_AT_ASOF"
    dt = fc.at_local(UP_DAY, 14, 35, fc.SYD)
    sig2 = AD.signal(tr, CALENDAR, UP_DAY, asof=dt)
    assert sig2["knowable"] is True and sig2["tail"] == "UP"


def test_k0_structure_pre_registered():
    k0 = fc.fold_floor_check(23, 8)
    assert k0["passes"] is False and k0["per_fold_mean"] == 2.88
    it = AD.order_intent(PANEL, CALENDAR, "C6A0-CONT-AF1-DRIFT-UP-D1-S2", UP_DAY)
    assert it["k0_structure"]["passes"] is False


def test_rba_time_not_carried_refusal():
    with pytest.raises(fc.RefusedRbaTimeNotCarried):
        consume_rba_decision_stamp(date=UP_DAY, time="14:30:05 Sydney")


def test_real_data_refusal_p5_fxja_d5_chain():
    real = {**PANEL, "provenance": "REAL_CHAIN"}
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        AD.order_intent(real, CALENDAR, CORE_IDS[0], UP_DAY)
    assert ei.value.slot_id == "P5-FXJA-D5"
    assert "PB3" in ei.value.detail
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei2:
        af1_freeze_check()
    assert ei2.value.slot_id == "P5-FXJA-D5"
    assert all(v is None for v in fc.GUARDS.values())   # nothing self-signed


def test_contract_binding_two_era_rows():
    c = fc.load_fx_contract("6A")
    assert c["era_table"]["era1"] == (1e-04, 10.0, 100_000.0)
    assert c["era_table"]["era2"] == (5e-05, 5.0, 100_000.0)
    assert fc.load_fx_contract("6J")["multiplier"] == 12_500_000   # 6J single-era
