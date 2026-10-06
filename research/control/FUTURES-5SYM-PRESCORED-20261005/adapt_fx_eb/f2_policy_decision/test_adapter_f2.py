"""F2 adapter tests — 6E FOMC leg / 6B MPC leg. Fixture expectations (incl. the
6B minute-720 London anchor DST-proof), exclusions NO-TRADE, PIT truncation,
PB2 refusal, slot refusals. Outcome-blind; synthetic only."""
import copy

import fx_common
from fx_common import RefusedPendingOwnerDecision
from conftest import load_panel, load_expected
from f2_policy_decision import adapter as f2

import pytest

D_6E = {"fomc": "2026-04-15", "emerg": "2026-04-21", "ecb": "2026-04-16",
        "quiet": "2026-04-23", "qbad": "2026-07-06"}
D_6B = {"mpc": "2026-04-16", "mpc_hold": "2026-03-12", "fomc": "2026-04-15",
        "double": "2026-04-22", "quiet": "2026-04-23", "qbad": "2023-06-15"}


@pytest.fixture(scope="module")
def ctx():
    panels = {sym: load_panel("f2_policy_decision", sym) for sym in ("6E", "6B")}
    expected = load_expected("f2_policy_decision")["expected"]
    return panels, expected


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_fixture_expectations(ctx, sym):
    panels, expected = ctx
    panel, exp = panels[sym], expected[sym]
    s = D_6E["fomc"] if sym == "6E" else D_6B["mpc"]
    key = "S_fomc" if sym == "6E" else "S_mpc_change"
    e = exp[key]
    obs = f2.build_observables(panel, panel["calendar"], sym, s)
    assert obs["anchor_ct_minute"] == e["anchor_ct_minute"]
    assert obs["window_sign"] == e["window_sign"]
    assert obs["window_move"] == pytest.approx(e["window_move"])
    assert obs["spike_ratio"] == pytest.approx(e["spike_ratio"])
    assert obs["atr20"] == pytest.approx(e["atr20"])
    excl = f2.apply_exclusions(panel, panel["calendar"], sym)
    sig = f2.signal(obs, s, excl, sym, panel["calendar"], panel)
    assert sig["status"] == "TRIGGERED"
    assert sig["strata"] == e["strata"]
    for iid, o in e["orders"].items():
        intent = f2.order_intent(panel, obs, sig, iid, sym, delay_slot="D0")
        assert intent["side"] == o["side"], iid
        assert intent["entry_px_intent"] == pytest.approx(o["entry"]), iid
        assert intent["sl_level"] == pytest.approx(o["sl"]), iid
        assert intent["tp_level"] == pytest.approx(o["tp"]), iid
        assert intent["exit_px_model"] == pytest.approx(o["exit"]), iid
        assert intent["exit_rule"] == o["rule"], iid
    # D1B fills one bar later on the same engineered flat post-block
    d1b = f2.order_intent(panel, obs, sig, f"FXF2-{sym}-RC-UP-D1B-S2", sym,
                          delay_slot="D1B")
    assert d1b["entry_px_intent"] == pytest.approx(
        e["orders"][f"FXF2-{sym}-RC-UP-D0-S2"]["entry"])
    # D30M is the declared full-grid extension: enumerable under the ALT slot
    # set (binding the ALT set as THE core law requires P5-FXEB-OD3)
    sig30 = f2.signal(obs, s, excl, sym, panel["calendar"], panel,
                      delay_slots=fx_common.DELAY_SLOTS_ALT)
    d30 = f2.order_intent(panel, obs, sig30, f"FXF2-{sym}-RC-UP-D30M-S2", sym,
                          delay_slot="D30M")
    assert d30["entry_px_intent"] == pytest.approx(
        e["orders"][f"FXF2-{sym}-RC-UP-D0-S2"]["entry"])


def test_6b_mpc_minute720_london_anchor_dst_proof(ctx):
    """The 6B anchor is LONDON wall 12:00 (minute 720), never a CT clock: on
    2026-04-16 it resolves to 06:00 CT, on the DST-mismatch date 2026-03-12
    (US DST on, UK GMT) to 07:00 CT. Same London minute, shifted CT — the
    measured DST-stability law encoded as a fixture pair."""
    panels, expected = ctx
    panel = panels["6B"]
    obs_change = f2.build_observables(panel, panel["calendar"], "6B", D_6B["mpc"])
    obs_hold = f2.build_observables(panel, panel["calendar"], "6B",
                                    D_6B["mpc_hold"])
    assert obs_change["anchor_ct_minute"] == 360
    assert obs_hold["anchor_ct_minute"] == 420
    assert obs_change["window_sign"] == obs_hold["window_sign"] == "UP"
    excl = f2.apply_exclusions(panel, panel["calendar"], "6B")
    sig = f2.signal(obs_hold, D_6B["mpc_hold"], excl, "6B", panel["calendar"],
                    panel)
    assert sig["status"] == "TRIGGERED" and sig["strata"] == ["MPC_HOLD"]


@pytest.mark.parametrize("sym,scenario", [
    ("6E", "emerg"), ("6E", "ecb"), ("6E", "quiet"), ("6E", "qbad"),
    ("6B", "fomc"), ("6B", "double"), ("6B", "quiet"), ("6B", "qbad"),
])
def test_exclusion_and_stratum_days_no_trade(ctx, sym, scenario):
    panels, expected = ctx
    panel = panels[sym]
    s = (D_6E if sym == "6E" else D_6B)[scenario]
    obs = f2.build_observables(panel, panel["calendar"], sym, s)
    excl = f2.apply_exclusions(panel, panel["calendar"], sym)
    sig = f2.signal(obs, s, excl, sym, panel["calendar"], panel)
    exp = expected[sym][
        {"emerg": "S_emerg", "ecb": "S_ecb", "quiet": "S_quiet", "qbad": "S_qbad",
         "fomc": "S_fomc_6B", "double": "S_double"}[scenario]]
    assert sig["status"] == "NO_TRADE"
    for b in exp["blocking"]:
        assert b in sig["blocking"], (sym, scenario, sig["blocking"])
    intent = f2.order_intent(panel, obs, sig, sig["identity_draft_ids"][0], sym)
    assert intent["status"] == "NO_TRADE"


def test_emergency_timing_stamp_is_sensitivity_only(ctx):
    """A non-13:00 FOMC stamp never trades the base (2020 emergency-timing law)."""
    panels, _ = ctx
    panel = panels["6E"]
    obs = f2.build_observables(panel, panel["calendar"], "6E", D_6E["emerg"])
    excl = f2.apply_exclusions(panel, panel["calendar"], "6E")
    sig = f2.signal(obs, D_6E["emerg"], excl, "6E", panel["calendar"], panel)
    assert "EMERGENCY_TIMING" in sig["strata"]
    assert sig["status"] == "NO_TRADE"


def test_pit_truncation_identical_decision_instant_outputs(ctx):
    panels, _ = ctx
    for sym, s in (("6E", D_6E["fomc"]), ("6B", D_6B["mpc"])):
        panel = panels[sym]
        obs = f2.build_observables(panel, panel["calendar"], sym, s)
        excl = f2.apply_exclusions(panel, panel["calendar"], sym)
        sig = f2.signal(obs, s, excl, sym, panel["calendar"], panel)
        intent = f2.order_intent(panel, obs, sig, f"FXF2-{sym}-RC-UP-D0-S2", sym)
        asof = fx_common.parse_ts(intent["entry_ts_intent"])
        truncated = copy.deepcopy(panel)
        truncated["bars"] = [b for b in panel["bars"]
                             if fx_common.parse_ts(b["ts"]) <= asof]
        obs2 = f2.build_observables(truncated, panel["calendar"], sym, s)
        excl2 = f2.apply_exclusions(truncated, panel["calendar"], sym)
        sig2 = f2.signal(obs2, s, excl2, sym, panel["calendar"], truncated)
        intent2 = f2.order_intent(truncated, obs2, sig2,
                                  f"FXF2-{sym}-RC-UP-D0-S2", sym,
                                  resolve_exit=False)
        assert obs2["anchor_ct_minute"] == obs["anchor_ct_minute"]
        assert obs2["window_sign"] == obs["window_sign"]
        assert obs2["window_move"] == pytest.approx(obs["window_move"])
        assert sig2["tail"] == sig["tail"] and sig2["status"] == sig["status"]
        assert intent2["entry_px_intent"] == pytest.approx(intent["entry_px_intent"])
        assert intent2["sl_level"] == pytest.approx(intent["sl_level"])
        assert intent2["tp_level"] == pytest.approx(intent["tp_level"])


def test_pb2_refusal_real_data_path(ctx):
    panels, _ = ctx
    panel = copy.deepcopy(panels["6B"])
    panel["provenance"] = "REAL_6B_CACHE"
    with pytest.raises(RefusedPendingOwnerDecision) as ei:
        f2.build_observables(panel, panel["calendar"], "6B", D_6B["mpc"])
    assert ei.value.slot_id == "P5-FXEB-OD1"


def test_slot_refusals_and_identity_enumeration():
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.bind_option("FX-A")
    assert e.value.slot_id == "P5-FXEB-OD2"
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.bind_delay_slots(("D0", "D1B"))
    assert e.value.slot_id == "P5-FXEB-OD3"
    for sym in ("6E", "6B"):
        core = fx_common.core_ids("FX-F2", sym)
        assert len(core) == 8
        assert f"FXF2-{sym}-RC-UP-D0-S2" in core
        assert f"FXF2-{sym}-RD-DN-D1B-S2" in core
        ctl = fx_common.control_ids("FX-F2", sym)
        assert ctl == [f"FXF2-{sym}-C1-SHADOW", f"FXF2-{sym}-C2-ALW",
                       f"FXF2-{sym}-C3-ANCHOR"]
