"""F1 adapter tests — fixture expectations, exclusions NO-TRADE, PIT truncation,
PB2 refusal (P5-FXEB-OD1), slot refusals. Outcome-blind; synthetic only."""
import copy

import fx_common
from fx_common import PanelError, RefusedPendingOwnerDecision
from conftest import load_panel, load_expected
from f1_london_range import adapter as f1

import pytest

S = {"6E": {"trig": "2026-04-15", "notrig": "2026-04-16", "covlow": "2026-04-17",
            "holiday": "2026-04-24", "onfomc": "2026-04-22", "overlay": "2026-04-23",
            "qbad": "2026-07-06"},
     "6B": {"trig": "2026-04-15", "notrig": "2026-04-16", "covlow": "2026-04-17",
            "overlay": "2026-04-23", "onfomc": "2026-04-22", "qbad": "2023-06-15"}}


@pytest.fixture(scope="module")
def ctx():
    panels = {sym: load_panel("f1_london_range", sym) for sym in ("6E", "6B")}
    expected = load_expected("f1_london_range")["expected"]
    return panels, expected


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_fixture_expectations(ctx, sym):
    panels, expected = ctx
    panel, exp = panels[sym], expected[sym]
    s = S[sym]["trig"]
    obs = f1.build_observables(panel, panel["calendar"], sym, s)
    assert obs["rlon"] == exp["S_trig"]["rlon"]
    assert obs["coverage"] == pytest.approx(exp["S_trig"]["coverage"])
    assert obs["trigger"]["sign"] == exp["S_trig"]["trigger"]["sign"]
    assert obs["trigger"]["close"] == pytest.approx(exp["S_trig"]["trigger"]["close"])
    assert obs["trigger"]["bar_ct"] == exp["S_trig"]["trigger"]["bar_ct"]
    assert obs["atr20"] == pytest.approx(exp["atr20"])
    excl = f1.apply_exclusions(panel, panel["calendar"], sym)
    sig = f1.signal(obs, s, excl, sym, panel["calendar"], panel)
    assert sig["status"] == exp["S_trig"]["signal_status"]
    assert sig["tail"] == "UP"
    for iid, o in exp["S_trig"]["orders"].items():
        intent = f1.order_intent(panel, obs, sig, iid, sym, delay_slot="D0")
        assert intent["side"] == o["side"], iid
        assert intent["entry_px_intent"] == pytest.approx(o["entry"]), iid
        assert intent["sl_level"] == pytest.approx(o["sl"]), iid
        assert intent["tp_level"] == pytest.approx(o["tp"]), iid
        assert intent["exit_px_model"] == pytest.approx(o["exit"]), iid
        assert intent["exit_rule"] == o["rule"], iid
        assert intent["cost_model"]["gate_consumable"] is False
        assert intent["cost_model"]["labels"] == fx_common.COST_LABELS
    # D1B fills one bar later, same engineered flat price
    d1b = f1.order_intent(panel, obs, sig, f"FXF1-{sym}-HC-UP-D1B-S2", sym,
                          delay_slot="D1B")
    assert d1b["delay_slot"] == "D1B"
    assert d1b["entry_px_intent"] == pytest.approx(exp["S_trig"]["orders"]
                                                   [f"FXF1-{sym}-HC-UP-D0-S2"]["entry"])


@pytest.mark.parametrize("sym,scenario", [
    ("6E", "notrig"), ("6E", "covlow"), ("6E", "onfomc"), ("6E", "overlay"),
    ("6E", "holiday"), ("6E", "qbad"),
    ("6B", "notrig"), ("6B", "covlow"), ("6B", "onfomc"), ("6B", "overlay"),
    ("6B", "qbad"),
])
def test_exclusion_days_no_trade(ctx, sym, scenario):
    panels, expected = ctx
    panel = panels[sym]
    s = S[sym][scenario]
    obs = f1.build_observables(panel, panel["calendar"], sym, s)
    excl = f1.apply_exclusions(panel, panel["calendar"], sym)
    sig = f1.signal(obs, s, excl, sym, panel["calendar"], panel)
    exp = expected[sym].get(scenario if scenario not in ("overlay",) else "S_overlay",
                            expected[sym].get("S_" + scenario, {}))
    assert sig["status"] == "NO_TRADE"
    for b in exp["blocking"]:
        assert b in sig["blocking"], (sym, scenario, sig["blocking"])
    oid = sig["identity_draft_ids"][0]
    intent = f1.order_intent(panel, obs, sig, oid, sym)
    assert intent["status"] == "NO_TRADE"


def test_6b_holiday_grid_absence_is_declaration_not_exclusion():
    """6B 0/42 grid: the absence is DECLARED on every session but never blocks —
    holiday-adjacent 6B sessions are neither excluded nor certified clean."""
    panel = load_panel("f1_london_range", "6B")
    excl = f1.apply_exclusions(panel, panel["calendar"], "6B")
    every = {f for flags in excl.values() for f in flags}
    assert "HOL_GRID_ABSENT_0OF42_DECLARED" in every
    from fx_common import blocking_flags
    assert "HOL_GRID_ABSENT_0OF42_DECLARED" not in blocking_flags(
        ["HOL_GRID_ABSENT_0OF42_DECLARED"])


def test_pit_truncation_identical_outputs():
    """Feeding a panel truncated at the D0 fill instant yields identical
    observables/signal/ENTRY intent (no future data consumed). The EXIT fill is
    a future event by construction and is asserted only on the full panel."""
    for sym in ("6E", "6B"):
        panel = load_panel("f1_london_range", sym)
        s = S[sym]["trig"]
        obs = f1.build_observables(panel, panel["calendar"], sym, s)
        excl = f1.apply_exclusions(panel, panel["calendar"], sym)
        sig = f1.signal(obs, s, excl, sym, panel["calendar"], panel)
        intent = f1.order_intent(panel, obs, sig,
                                 f"FXF1-{sym}-HC-UP-D0-S2", sym)
        asof = fx_common.parse_ts(intent["entry_ts_intent"])
        truncated = copy.deepcopy(panel)
        truncated["bars"] = [b for b in panel["bars"]
                             if fx_common.parse_ts(b["ts"]) <= asof]
        obs2 = f1.build_observables(truncated, panel["calendar"], sym, s)
        excl2 = f1.apply_exclusions(truncated, panel["calendar"], sym)
        sig2 = f1.signal(obs2, s, excl2, sym, panel["calendar"], truncated)
        intent2 = f1.order_intent(truncated, obs2, sig2,
                                  f"FXF1-{sym}-HC-UP-D0-S2", sym,
                                  resolve_exit=False)
        assert obs2["rlon"] == obs["rlon"] and obs2["trigger"] == obs["trigger"]
        assert sig2["tail"] == sig["tail"] and sig2["status"] == sig["status"]
        assert intent2["entry_px_intent"] == pytest.approx(intent["entry_px_intent"])
        assert intent2["entry_ts_intent"] == intent["entry_ts_intent"]
        assert intent2["sl_level"] == pytest.approx(intent["sl_level"])
        assert intent2["tp_level"] == pytest.approx(intent["tp_level"])


def test_pb2_refusal_real_data_path():
    """Any non-SYNTHETIC provenance raises P5-FXEB-OD1 (real-data NOT_RUN)."""
    panel = copy.deepcopy(load_panel("f1_london_range", "6E"))
    panel["provenance"] = "REAL_6E_CACHE"
    with pytest.raises(RefusedPendingOwnerDecision) as ei:
        f1.build_observables(panel, panel["calendar"], "6E", S["6E"]["trig"])
    assert ei.value.slot_id == "P5-FXEB-OD1"


def test_slot_refusals():
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.bind_option("FX-B")
    assert e.value.slot_id == "P5-FXEB-OD2"
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.bind_delay_slots(("D0", "D30M"))
    assert e.value.slot_id == "P5-FXEB-OD3"
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.consumable_rt_cost("6E", "S2")
    assert e.value.slot_id == "P5-FXEB-OD6"
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.consumable_rt_cost("6B", "S2", basis="A")
    assert e.value.slot_id == "P5-FXEB-OD6" and "DERIVED" in e.value.detail
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.override_d12_posture()
    assert e.value.slot_id == "P5-FXEB-OD9"
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.bind_warmup_law("ES_252")
    assert e.value.slot_id == "P5-FXEB-OD10"
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.request_f1_scored_spec("6E")
    assert e.value.slot_id == "P5-FXEB-OD11"


def test_identity_enumeration_quotes_budget_draft():
    for sym in ("6E", "6B"):
        core = fx_common.core_ids("FX-F1", sym)
        ctl = fx_common.control_ids("FX-F1", sym)
        assert len(core) == 8 and len(ctl) == 3
        assert f"FXF1-{sym}-HC-UP-D0-S2" in core
        assert f"FXF1-{sym}-HD-DN-D1B-S2" in core
        assert f"FXF1-{sym}-C1-SHADOW" in ctl
        assert f"FXF1-{sym}-C3-ANCHOR" in ctl
        counts = fx_common.family_identity_counts("FX-F1", sym)
        assert counts == {"core": 8, "controls": 3, "conv_d_minimal": 11}


def test_contract_binding_and_tick_grid():
    for sym, tick in (("6E", 0.00005), ("6B", 0.0001)):
        c = fx_common.load_fx_contract(sym)
        assert (c["tick_size"], c["tick_value_usd"], c["multiplier"]) == \
            (tick, 6.25, fx_common.SYMBOL_LAW[sym]["multiplier"])
        assert c["long_base_sign"] == 1
        assert c["session_mask_placeholder_disclosed"] == "07:20-14:00"  # disclosed only
    assert fx_common.on_tick_grid(1.10100, "6E") and not fx_common.on_tick_grid(1.10101, "6E")
    assert fx_common.on_tick_grid(1.30190, "6B") and not fx_common.on_tick_grid(1.30005, "6B")
