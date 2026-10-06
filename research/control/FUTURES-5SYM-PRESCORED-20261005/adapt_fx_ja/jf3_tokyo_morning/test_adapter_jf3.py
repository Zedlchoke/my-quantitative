"""test_adapter_jf3 — pytest proofs for the 6J-JF3 Tokyo-morning adapter (synthetic).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest jf3_tokyo_morning -q
Exit code recorded in dispatch/handoff_ADAPT-FXJA.json.
"""
from __future__ import annotations

import pytest

import fx_common as fc
from conftest import load_expected, load_fixture
from jf3_tokyo_morning.adapter import CONTROL_IDS, CORE_IDS, DRAFT_IDS, JF3Adapter

AD = JF3Adapter()
PANEL = load_fixture("jf3_tokyo_morning", "jf3_panel_tokyo.json")
CALENDAR = load_fixture("jf3_tokyo_morning", "jf3_calendar.json")
EXPECTED = load_expected("jf3_tokyo_morning")["expected"]
UP_DAY = EXPECTED["up_day"]
DN_DAY = EXPECTED["dn_day"]


def trunc_t(panel: dict, asof_iso: str) -> dict:
    t = fc.parse_ts(asof_iso)
    return {**panel, "bars": [b for b in panel["bars"] if fc.parse_ts(b["ts"]) <= t]}


def test_identity_enumeration_matches_budget():
    assert CORE_IDS == [
        "FB6J1-JF3-CONT-UP-D1-S2", "FB6J1-JF3-CONT-UP-D30M-S2",
        "FB6J1-JF3-CONT-DN-D1-S2", "FB6J1-JF3-CONT-DN-D30M-S2",
        "FB6J1-JF3-FADE-UP-D1-S2", "FB6J1-JF3-FADE-UP-D30M-S2",
        "FB6J1-JF3-FADE-DN-D1-S2", "FB6J1-JF3-FADE-DN-D30M-S2"]
    assert CONTROL_IDS == ["FB6J1-PLA-JF3", "FB6J1-ALW-JF3", "FB6J1-CLK-JF3"]
    assert len(DRAFT_IDS) == 11


def test_exclusions_no_trade_fail_closed():
    excl = AD.apply_exclusions(CALENDAR, PANEL)
    assert excl == EXPECTED["expected_exclusions"]
    for sd in excl:
        out = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF3-CONT-UP-D1-S2", sd)
        assert out["no_trade"] is True
        assert out["no_trade_reason"].startswith("EXCLUDED: ")


def test_window_coverage_rule_flags_sub80_session():
    cov = AD.tokyo_range(PANEL, EXPECTED["coverage_fail_day"])
    assert cov is not None and round(cov["coverage"], 6) == EXPECTED["coverage_fail_value"]
    assert EXPECTED["coverage_fail_value"] < 0.80
    sig = AD.signal(PANEL, CALENDAR, EXPECTED["coverage_fail_day"])
    assert sig["no_trade_reason"] == "WINDOW_COVERAGE_BELOW_FLOOR"


def test_signal_and_reference_agreement_up_break():
    ref = EXPECTED["up_trigger"]
    sig = AD.signal(PANEL, CALENDAR, UP_DAY)
    assert sig["knowable"] and sig["tail"] == "UP"
    assert sig["trigger_ts"] == ref["ts"]
    assert round(sig["range_hi"], 12) == round(ref["range_hi"], 12)
    assert round(sig["trigger_close"], 12) == round(ref["close"], 12)


def test_order_intent_reference_agreement_and_signs():
    ref = EXPECTED["cont_up_d1"]
    got = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF3-CONT-UP-D1-S2", UP_DAY)
    assert got["no_trade"] is False
    assert got["direction"] == ref["direction"] == 1 and got["side"] == "BUY"
    assert got["event_context"]["trigger_ts"] == ref["trigger_ts"]
    assert got["decision_time"] == ref["decision_time"]
    assert round(got["entry_ref_price"], 12) == round(ref["entry_ref_price"], 12)
    assert round(got["atr20_points"], 12) == round(ref["atr20_points"], 12)
    assert got["exit_reason"] == ref["exit_reason"]
    ref2 = EXPECTED["fade_dn_d30m"]
    got2 = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF3-FADE-DN-D30M-S2", DN_DAY)
    assert got2["direction"] == ref2["direction"] == 1   # fade a DOWN break = BUY
    assert got2["exit_reason"] == ref2["exit_reason"] == "SL"
    cont_dn = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF3-CONT-DN-D1-S2", DN_DAY)
    assert cont_dn["direction"] == -1 and cont_dn["side"] == "SELL"


def test_tail_mismatch_no_trade():
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF3-CONT-DN-D1-S2", UP_DAY)
    assert out["no_trade"] and out["no_trade_reason"] == "TAIL_MISMATCH"


def test_quote_direction_law_6j_price_terms():
    """Break UP = 6J close ABOVE range high = yen strengthening; the CONT-UP
    side must be BUY (long yen strength), per the orientation proof."""
    sig = AD.signal(PANEL, CALENDAR, UP_DAY)
    assert sig["tail"] == "UP" and sig["trigger_close"] > sig["range_hi"]
    it = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF3-CONT-UP-D1-S2", UP_DAY)
    assert it["side"] == "BUY" and it["quote_direction_law"] == fc.QUOTE_DIRECTION_6J


def test_pit_range_not_knowable_before_window_close():
    early = fc.at_local(UP_DAY, 10, 0, fc.JST)   # 10:00 JST — window incomplete
    sig = AD.signal(trunc_t(PANEL, early.isoformat()), CALENDAR, UP_DAY, asof=early)
    assert sig["knowable"] is False
    assert sig["no_trade_reason"] == "RANGE_NOT_COMPLETE_UPTO_ASOF"


def test_pit_truncation_identical_and_no_lookahead():
    dt = EXPECTED["up_trigger"]["decision_time"]   # trigger close, 13:31 JST
    sig_t = AD.signal(trunc_t(PANEL, dt), CALENDAR, UP_DAY, asof=dt)
    sig_f = AD.signal(PANEL, CALENDAR, UP_DAY, asof=dt)
    for f in ("tail", "trigger_ts", "range_hi", "range_lo", "trigger_close"):
        assert sig_t[f] == sig_f[f], f
    it_t = AD.order_intent(trunc_t(PANEL, dt), CALENDAR,
                           "FB6J1-JF3-CONT-UP-D1-S2", UP_DAY, asof=dt)
    it_f = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF3-CONT-UP-D1-S2", UP_DAY, asof=dt)
    for f in ("direction", "side", "entry_ref_price", "sl_price", "tp_price",
              "exit_resolution"):
        assert it_t[f] == it_f[f], f
    assert it_t["exit_resolution"] == "PENDING_UPTO_ASOF"   # no future read
    # a post-window-close, pre-trigger truncation must NOT know the break
    # (DN day: window closes 02:30 UTC, trigger 03:20 UTC)
    pre = fc.parse_ts("2026-07-02T03:00:00+00:00")
    sig_pre = AD.signal(trunc_t(PANEL, pre.isoformat()), CALENDAR, DN_DAY, asof=pre)
    assert sig_pre["no_trade_reason"] == "NO_BREAK_UPTO_ASOF"


def test_dst_mismatch_falsifier_probe():
    """C3'': bucketing the SAME bars in CT instead of JST must change the
    window (different/no trigger) — the Tokyo anchor is load-bearing."""
    probe = EXPECTED["dst_mismatch_probe"]
    assert probe["different"] is True
    law = fc.dst_mismatch_falsifier()
    assert law["falsifier"] == "C3p_DST_MISMATCH" and "kill" in law["law"]


def test_atr_warmup_insufficient():
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF3-CONT-UP-D1-S2",
                          PANEL["sessions"][0]["session_date"])
    assert out["no_trade"] and out["no_trade_reason"] == "ATR_WARMUP_INSUFFICIENT"


def test_real_data_refusal_6j_ceiling():
    real = {**PANEL, "provenance": "REAL_CHAIN"}
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        AD.order_intent(real, CALENDAR, "FB6J1-JF3-CONT-UP-D1-S2", UP_DAY)
    assert ei.value.slot_id == "P5-FXJA-D1"


def test_identity_grammar_refuses_foreign_shapes():
    with pytest.raises(ValueError):
        AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-UP-D1-S2", UP_DAY)
    with pytest.raises(ValueError):
        _bad_arm()


def _bad_arm():
    from jf3_tokyo_morning.adapter import _parse_identity
    _parse_identity("FB6J1-JF3-DRIFT-UP-D1-S2")


def test_session_close_time_exit_law():
    """CONT-UP-D30M on the UP day enters late (12:01 JST); the remaining
    up-walk cannot reach TP, so the exit must be the measured session last
    bar (no overnight hold)."""
    got = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF3-CONT-UP-D30M-S2", UP_DAY)
    assert got["exit_reason"] == "SESSION_CLOSE"
    last = fc.session_last_dt(PANEL, UP_DAY)
    assert fc.parse_ts(got["exit_ts"]) == last
    # and the D1 variant does reach its TP inside the session
    got_d1 = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF3-CONT-UP-D1-S2", UP_DAY)
    assert got_d1["exit_reason"] == "TP"
    assert fc.parse_ts(got_d1["exit_ts"]) <= last
