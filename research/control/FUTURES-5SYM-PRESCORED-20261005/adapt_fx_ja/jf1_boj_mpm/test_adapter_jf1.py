"""test_adapter_jf1 — pytest proofs for the 6J-JF1 BoJ MPM adapter (synthetic).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest jf1_boj_mpm -q
(from adapt_fx_ja/). Exit code recorded in dispatch/handoff_ADAPT-FXJA.json.
"""
from __future__ import annotations

import copy

import pytest

import fx_common as fc
from conftest import load_expected, load_fixture
from jf1_boj_mpm.adapter import (CONTROL_IDS, CORE_IDS, DRAFT_IDS, DELAY_MINUTES,
                                 JF1Adapter)

AD = JF1Adapter()
PANEL = load_fixture("jf1_boj_mpm", "jf1_panel_mpm.json")
CALENDAR = load_fixture("jf1_boj_mpm", "jf1_calendar.json")
EXPECTED = load_expected("jf1_boj_mpm")["expected"]
TP_DAY = "2026-02-15"
SL_DAY = "2026-03-15"
FLAT_DAY = "2026-01-15"
DECISION_UTC = fc.at_local(TP_DAY, 15, 30, fc.JST)   # 06:30 UTC


def trunc(panel: dict, asof) -> dict:
    a = asof if isinstance(asof, str) else asof.isoformat()
    t = fc.parse_ts(a)
    return {**panel, "bars": [b for b in panel["bars"] if fc.parse_ts(b["ts"]) <= t]}


# ------------------------------------------------------------------ identity
def test_identity_enumeration_matches_budget():
    assert CORE_IDS == [
        "FB6J1-JF1-DRIFT-UP-D1-S2", "FB6J1-JF1-DRIFT-UP-D30M-S2",
        "FB6J1-JF1-DRIFT-DN-D1-S2", "FB6J1-JF1-DRIFT-DN-D30M-S2",
        "FB6J1-JF1-REV-UP-D1-S2", "FB6J1-JF1-REV-UP-D30M-S2",
        "FB6J1-JF1-REV-DN-D1-S2", "FB6J1-JF1-REV-DN-D30M-S2"]
    assert CONTROL_IDS == ["FB6J1-PLA-JF1", "FB6J1-ALW-JF1", "FB6J1-CLK-JF1"]
    assert len(DRAFT_IDS) == 11   # CONV-B minimal JF1 block (IDENTITY_BUDGET_6J s.2)


def test_contract_binding_and_quote_direction():
    c = fc.load_fx_contract("6J")
    assert (c["tick_size"], c["tick_value_usd"], c["multiplier"]) == (5e-07, 6.25, 12_500_000)
    assert c["quote_direction"] == fc.QUOTE_DIRECTION_6J == "USD_PER_JPY__6J_UP__JPY_STRONG"


def test_quote_direction_law_orientation_proof():
    """6J UP = yen STRONG: a FALLING USDJPY inside the window must yield a
    RISING 6J price and tail UP (SPEC_6J s.2 orientation proof transposed to
    the synthetic fixture)."""
    assert fc.usdjpy_to_6j(157.32) > fc.usdjpy_to_6j(160.04)   # yen stronger -> 6J higher
    sig = AD.signal(PANEL, CALENDAR, TP_DAY)
    assert sig["tail"] == EXPECTED["tails"][TP_DAY] == "UP"
    assert sig["window_move"] > 0 and sig["window_close"] > sig["window_open"]
    dn = "2024-02-15"
    assert AD.signal(PANEL, CALENDAR, dn)["tail"] == "DN"


def test_exclusions_no_trade_fail_closed():
    excl = AD.apply_exclusions(CALENDAR, PANEL)
    assert excl == EXPECTED["expected_exclusions"]
    for sd, flags in excl.items():
        for iid in DRAFT_IDS:
            out = AD.order_intent(PANEL, CALENDAR, iid, sd)
            assert out["no_trade"] is True
            assert out["no_trade_reason"].startswith("EXCLUDED: "), (sd, iid)


def test_trigger_flat_no_trade():
    sig = AD.signal(PANEL, CALENDAR, FLAT_DAY)
    assert sig["knowable"] is True and sig["tail"] is None
    assert sig["no_trade_reason"] == "TRIGGER_FLAT"
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-UP-D1-S2", FLAT_DAY)
    assert out["no_trade"] and out["no_trade_reason"] == "TRIGGER_FLAT"


# --------------------------------------------------------------------- PIT
def test_pit_truncation_not_knowable_before_decision_time():
    before = DECISION_UTC.replace(minute=DECISION_UTC.minute - 1)
    sig = AD.signal(trunc(PANEL, before), CALENDAR, TP_DAY, asof=before)
    assert sig["event"] is True and sig["knowable"] is False
    assert sig["no_trade_reason"] == "SIGNAL_NOT_KNOWABLE_AT_ASOF"


def test_pit_truncated_panel_byte_identical_at_decision_time():
    """No-future-data law: the resolved intent from a panel truncated at the
    decision time equals the full-panel resolution (asof=None) field-by-field
    for every PIT-bearing field."""
    sig_fields = ["tail", "window_move", "window_open", "window_close"]
    it_fields = ["direction", "side", "entry_ref_price", "sl_price", "tp_price",
                 "atr20_window", "no_trade", "no_trade_reason"]
    sig_t = AD.signal(trunc(PANEL, DECISION_UTC), CALENDAR, TP_DAY, asof=DECISION_UTC)
    sig_f = AD.signal(PANEL, CALENDAR, TP_DAY, asof=None)
    for f in sig_fields:
        assert sig_t[f] == sig_f[f], f
    it_t = AD.order_intent(trunc(PANEL, DECISION_UTC), CALENDAR,
                           "FB6J1-JF1-DRIFT-UP-D1-S2", TP_DAY, asof=DECISION_UTC)
    it_f = AD.order_intent(PANEL, CALENDAR,
                           "FB6J1-JF1-DRIFT-UP-D1-S2", TP_DAY, asof=DECISION_UTC)
    for f in it_fields + ["ts_entry", "exit_resolution"]:
        assert it_t[f] == it_f[f], f
    # at the decision instant the exit is legitimately PENDING (no future read);
    # end-of-session resolution on the full panel must be the TP showcase
    it_full = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-UP-D1-S2", TP_DAY)
    assert it_full["exit_resolution"] == "RESOLVED" and it_full["exit_reason"] == "TP"
    # the D30M entry bar (16:00 JST) does not exist at the decision time:
    # the PIT-correct answer is a NO-TRADE, never a look-ahead fill
    it_d30 = AD.order_intent(trunc(PANEL, DECISION_UTC), CALENDAR,
                             "FB6J1-JF1-DRIFT-UP-D30M-S2", TP_DAY, asof=DECISION_UTC)
    assert it_d30["no_trade"] and it_d30["no_trade_reason"] == "ENTRY_BAR_ABSENT_UPTO_ASOF"


def test_delay_entries_match_law():
    it_d1 = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-UP-D1-S2", TP_DAY)
    it_d30 = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-UP-D30M-S2", TP_DAY)
    assert DELAY_MINUTES == {"D1": 0, "D30M": 30}
    assert fc.local_minutes(fc.parse_ts(it_d1["ts_entry"]), fc.JST) == 930   # 15:30 JST bar
    assert fc.local_minutes(fc.parse_ts(it_d30["ts_entry"]), fc.JST) == 960  # 16:00 JST bar
    assert it_d1["order_type"] == "MARKET_NEXT_BAR_OPEN"


# ------------------------------------------------------- expected-manifest
def test_reference_manifest_agreement():
    assert EXPECTED["n_events"] == 27 and EXPECTED["n_control_days"] == 6
    ref = EXPECTED["tp_hit_intent_drift_up_d1"]
    got = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-UP-D1-S2", TP_DAY)
    assert got["no_trade"] is False

    def eq(a, b):
        return round(a, 12) == round(b, 12) if isinstance(a, float) else a == b

    for a, b in (("direction", "direction"), ("side", "side"),
                 ("entry_ref_price", "entry_ref_price"),
                 ("sl_price", "sl_price"), ("tp_price", "tp_price"),
                 ("atr20_window", "atr20_window"),
                 ("exit_ref_price", "exit_ref_price"),
                 ("exit_reason", "exit_reason"), ("exit_ts", "exit_ts")):
        assert eq(got[a], ref[b]), (a, got[a], ref[b])
    ref2 = EXPECTED["sl_hit_intent_drift_dn_d1"]
    got2 = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-DN-D1-S2", SL_DAY)
    assert got2["exit_reason"] == ref2["exit_reason"] == "SL"
    assert round(got2["exit_ref_price"], 12) == round(ref2["exit_ref_price"], 12)
    assert got2["direction"] == -1 and got2["side"] == "SELL"


def test_tail_mismatch_no_trade():
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-DN-D1-S2", TP_DAY)
    assert out["no_trade"] and out["no_trade_reason"] == "TAIL_MISMATCH"


def test_regime_change_stratum_descriptive_only():
    obs = AD.build_observables(PANEL, CALENDAR)
    strata = {e["date"]: e["stratum"] for e in obs["events"]}
    assert strata["2025-12-15"] == "REGIME_CHANGE_DESCRIPTIVE_ONLY"
    assert fc.fold_floor_check(6)["passes"] is False   # pre-declared fold-floor failure


# -------------------------------------------------------------- warmup law
def test_atr_warmup_insufficient():
    early = "2024-06-15"   # fewer than 20 prior events
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-UP-D1-S2", early)
    assert out["no_trade"] and out["no_trade_reason"] == "ATR_WARMUP_INSUFFICIENT"


def test_fold_warmup_law_252_sessions():
    assert fc.WARMUP_HELD_SESSIONS == 252
    # structural law: the fold-head warmup drops exactly the first 252 sessions
    from datetime import date as _d, timedelta as _td
    law_list = [(_d(2024, 1, 1) + _td(days=i)).isoformat() for i in range(300)]
    got = fc.scoreable_sessions(law_list, "F3")
    assert len(law_list) - len(got) == 252
    assert got[0] == law_list[252]
    # and on the fixture scale the fold map itself must classify correctly
    f3 = [f"2024-{m:02d}-01" for m in range(1, 13)] + \
         [f"2025-{m:02d}-01" for m in range(1, 13)]
    assert all(fc.fold_for_date(d) == "F3" for d in f3)
    assert fc.fold_for_date("2026-06-01") == "F4"   # F4 = 2026-01..2026-09
    assert fc.fold_for_date("2026-10-01") is None   # partial tail outside every fold


# ------------------------------------------------------------ slot refusals
def test_real_data_refusal_6j_ceiling_p5_fxja_d1():
    real = {**PANEL, "provenance": "REAL_CHAIN"}
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        AD.signal(real, CALENDAR, TP_DAY)
    assert ei.value.slot_id == "P5-FXJA-D1"
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei2:
        fc.require_synthetic(real, "6J")
    assert ei2.value.slot_id == "P5-FXJA-D1"


def test_option_binding_refuses_while_unsigned():
    for opt in ("J-A", "J-B", "J-C"):
        with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
            fc.bind_option_6j(opt)
        assert ei.value.slot_id == "P5-FXJA-D1"
    assert fc.GUARDS["P5-FXJA-D2"] is None
    # even if D1 were ruled, J-C still requires D2 — checked at the guard layer


def test_boj_stamp_consumption_refuses():
    with pytest.raises(fc.RefusedBojStampNotInCorpus):
        fc.consume_boj_intraday_stamp(date=TP_DAY, minute="14:47 JST")
    with pytest.raises(fc.RefusedPendingOwnerDecision):
        fc.jf2_zone_threshold()   # P5-HYPO-OD4 fails closed too


def test_non_conservative_fill_and_verified_cost_refuse():
    with pytest.raises(fc.RefusedPendingOwnerDecision) as e1:
        fc.non_conservative_fill_model()
    assert e1.value.slot_id == "P5-FXJA-D3"
    with pytest.raises(fc.RefusedPendingOwnerDecision) as e2:
        fc.verified_cost_label()
    assert e2.value.slot_id == "P5-FXJA-D4"


def test_cost_preview_matches_cost_contract():
    it = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-DRIFT-UP-D1-S2", TP_DAY)
    cp = it["cost_preview"]
    # per-side = 2.46 + 1.0*(25.00+6.25) = 33.71; +6.25 entry-side session floor
    assert cp["cost_per_side_usd"] == 33.71
    assert cp["cost_rt_usd"] == round(2 * 33.71 + 6.25, 6)
    assert cp["cost_rt_bp_of_notional"] == round(cp["cost_rt_usd"] / 79_787.50 * 1e4, 4)
    assert cp["labels"] == fc.COST_LABELS


def test_controls_semantics():
    late_ctl = "2025-09-16"   # 20 prior events -> ATR warmup OK
    alw = AD.order_intent(PANEL, CALENDAR, "FB6J1-ALW-JF1", late_ctl)
    assert alw["no_trade"] is False and alw["direction"] == 1
    alw_event = AD.order_intent(PANEL, CALENDAR, "FB6J1-ALW-JF1", TP_DAY)
    assert alw_event["no_trade"] and alw_event["no_trade_reason"] == "ALW_NOT_NON_EVENT_DAY"
    clk = AD.order_intent(PANEL, CALENDAR, "FB6J1-CLK-JF1", late_ctl)
    assert clk["no_trade_reason"] == "CLK_WINDOW_FLAT"   # control window is flat
    pla = AD.order_intent(PANEL, CALENDAR, "FB6J1-PLA-JF1", late_ctl)
    assert pla["no_trade"] is False
    assert pla["direction"] == fc.shadow_direction(late_ctl)


def test_clock_control_flat_window_refuses():
    # the fixture control window is flat -> CLK (clock-conditioned) has no sign
    out = AD.order_intent(PANEL, CALENDAR, "FB6J1-CLK-JF1", "2025-09-16")
    assert out["no_trade"] and out["no_trade_reason"] == "CLK_WINDOW_FLAT"


def test_every_core_intent_carries_slot_dependencies():
    it = AD.order_intent(PANEL, CALENDAR, "FB6J1-JF1-REV-UP-D30M-S2", TP_DAY)
    assert set(fc.SLOT_DEPENDENCIES) <= set(it["decision_slot_dependencies"])
    assert it["labels"] == ["SYNTHETIC FIXTURE", "PROPOSED DRAFT", "NO EXECUTION"]
