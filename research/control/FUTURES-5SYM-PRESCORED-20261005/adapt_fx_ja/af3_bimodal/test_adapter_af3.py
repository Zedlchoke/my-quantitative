"""test_adapter_af3 — pytest proofs for the 6A-AF3 contingency adapter (synthetic).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest af3_bimodal -q
Exit code recorded in dispatch/handoff_ADAPT-FXJA.json.
"""
from __future__ import annotations

import pytest

import fx_common as fc
from conftest import load_expected, load_fixture
from af3_bimodal.adapter import (AF3Adapter, CONTROL_IDS, CORE_IDS, DRAFT_IDS,
                                 af3_freeze_check)

AD = AF3Adapter()
PANEL = load_fixture("af3_bimodal", "af3_panel_sydney.json")
CALENDAR = load_fixture("af3_bimodal", "af3_calendar.json")
EXPECTED = load_expected("af3_bimodal")["expected"]
ROT_DAY = EXPECTED["rot_day"]
ABS_DAY = EXPECTED["abs_day"]
K4_DAY = EXPECTED["k4_day"]
COV_DAY = EXPECTED["coverage"]["cov_day"]


def test_contingency_identity_counts_match_frozen_table():
    assert len(CORE_IDS) == 8 and len(CONTROL_IDS) == 3 and len(DRAFT_IDS) == 11
    frozen = fc.frozen_6a_table_citation()
    assert frozen["identities_by_category"]["AF3_minimal_core"] == 8
    assert frozen["identities_by_category"]["RMM_6A_contingency"] == 4
    assert frozen["total"] == 0 and frozen["total_if_ever_lifted"] == 26


def test_exclusions_rba_fomc_coverage():
    excl = AD.apply_exclusions(CALENDAR, PANEL)
    assert excl == EXPECTED["expected_exclusions"]
    out = AD.order_intent(PANEL, CALENDAR, CORE_IDS[0], COV_DAY)
    assert out["no_trade"] and out["no_trade_reason"].startswith("EXCLUDED: ")


def test_coverage_rule_value():
    assert EXPECTED["coverage"]["value"] == 0.75 < 0.80
    rng = AD.sydney_range(PANEL, COV_DAY)
    assert round(rng["coverage"], 6) == 0.75


def test_rot_abs_signs_and_reference_agreement():
    ref = EXPECTED["rot_up_d1"]
    got = AD.order_intent(PANEL, CALENDAR, "C6A0-CONT-AF3-ROT-UP-D1-S2", ROT_DAY)
    assert got["no_trade"] is False and got["side"] == "BUY" == ref["side"]
    assert got["event_context"]["trigger_ts"] == ref["trigger_ts"]
    assert round(got["entry_ref_price"], 10) == round(ref["entry_ref_price"], 10)
    assert round(got["atr20_points"], 12) == round(ref["atr20_points"], 12)
    assert got["exit_reason"] == ref["exit_reason"]
    # ABS on the DN break = BUY (fade); ROT-DN would SELL
    abs_it = AD.order_intent(PANEL, CALENDAR, "C6A0-CONT-AF3-ABS-DN-D30M-S2", ABS_DAY)
    assert abs_it["side"] == "BUY"
    rot_dn = AD.order_intent(PANEL, CALENDAR, "C6A0-CONT-AF3-ROT-DN-D1-S2", ABS_DAY)
    assert rot_dn["side"] == "SELL"
    assert AD.signal(PANEL, CALENDAR, ABS_DAY)["tail"] == "DN"


def test_k4_china_window_contamination_refuses():
    """K4: a trigger inside 09:30-10:00 Shanghai is a contamination boundary —
    fail-closed NO-TRADE in the signal and a refusal CODE on intent."""
    assert EXPECTED["k4_in_china_window"] is True
    sig = AD.signal(PANEL, CALENDAR, K4_DAY)
    assert sig["no_trade_reason"] == "CHINA_WINDOW_CONTAMINATION_K4"
    assert sig["k4_contamination"] is True
    with pytest.raises(fc.RefusedChinaCalendarNotRun) as ei:
        AD.order_intent(PANEL, CALENDAR, CORE_IDS[0], K4_DAY)
    assert ei.value.code == "REFUSED_CHINA_CALENDAR_NOT_RUN"
    assert "NOT_RUN" in ei.value.detail


def test_shanghai_window_mapping_dst_law():
    """The China-window membership is resolved in Asia/Shanghai (DST-correct):
    the ROT trigger (12:11 Syd = 10:11 Shanghai) is OUTSIDE; the K4 trigger
    (11:31 Syd = 09:31 Shanghai) is INSIDE — same clock law, opposite months
    would flip Sydney DST but not Shanghai's (C3'' falsifier substrate)."""
    from datetime import datetime as dt
    rot_trig = fc.parse_ts(EXPECTED["rot_trigger"]["ts"])
    k4_trig = fc.parse_ts(EXPECTED["k4_trigger"]["ts"])
    assert not AD.in_china_window(rot_trig)
    assert AD.in_china_window(k4_trig)
    law = fc.dst_mismatch_falsifier()
    assert law["falsifier"] == "C3p_DST_MISMATCH"


def test_pit_range_not_complete_before_window_close():
    early = fc.at_local(ROT_DAY, 10, 0, fc.SYD)
    tr = {**PANEL, "bars": [b for b in PANEL["bars"]
                            if fc.parse_ts(b["ts"]) <= fc.parse_ts(early.isoformat())]}
    sig = AD.signal(tr, CALENDAR, ROT_DAY, asof=early)
    assert sig["no_trade_reason"] == "RANGE_NOT_COMPLETE_UPTO_ASOF"


def test_pit_no_break_before_trigger():
    # ROT day: window closes 01:30 UTC, trigger 02:10 UTC
    pre = fc.parse_ts("2024-05-06T01:45:00+00:00")
    tr = {**PANEL, "bars": [b for b in PANEL["bars"]
                            if fc.parse_ts(b["ts"]) <= pre]}
    sig = AD.signal(tr, CALENDAR, ROT_DAY, asof=pre)
    assert sig["no_trade_reason"] == "NO_BREAK_UPTO_ASOF"


def test_era1_refusal_and_real_data_refusal():
    with pytest.raises(fc.RefusedEra1NoTradeIntent):
        AD.order_intent(PANEL, CALENDAR, CORE_IDS[0], "2020-06-02")
    real = {**PANEL, "provenance": "REAL_CHAIN"}
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        AD.order_intent(real, CALENDAR, CORE_IDS[0], ROT_DAY)
    assert ei.value.slot_id == "P5-FXJA-D5"
    with pytest.raises(fc.RefusedPendingOwnerDecision):
        af3_freeze_check()
    assert all(v is None for v in fc.GUARDS.values())


def test_era_aware_cost_with_sydney_floor():
    it = AD.order_intent(PANEL, CALENDAR, CORE_IDS[0], ROT_DAY)
    cp = it["cost_preview"]
    assert cp["era"] == "era2" and cp["cost_per_side_usd"] == 27.46
    assert cp["session_floor_entry_usd"] == 5.0   # +1 tick x $5.00 era-2
    assert cp["cost_rt_usd"] == round(2 * 27.46 + 5.0, 6)
