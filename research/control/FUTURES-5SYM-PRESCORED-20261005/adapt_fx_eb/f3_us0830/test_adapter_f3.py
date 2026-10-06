"""F3 adapter tests — fixture expectations (UP + DN releases), negative-control
strata NO-TRADE, vintage PIT refusal, PIT truncation, PB2 refusal, slots."""
import copy

import fx_common
from fx_common import RefusedPendingOwnerDecision
from conftest import load_panel, load_expected
from f3_us0830 import adapter as f3

import pytest

D = {"cpi": "2026-04-21", "emp": "2026-05-08", "canceled": "2026-04-22",
     "other": "2026-04-23", "double": "2026-04-15", "quiet": "2026-04-24"}


@pytest.fixture(scope="module")
def ctx():
    panels = {sym: load_panel("f3_us0830", sym) for sym in ("6E", "6B")}
    expected = load_expected("f3_us0830")["expected"]
    return panels, expected


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_up_release_expectations(ctx, sym):
    panels, expected = ctx
    panel, exp = panels[sym], expected[sym]["S_cpi"]
    obs = f3.build_observables(panel, panel["calendar"], sym, D["cpi"])
    assert obs["anchor_ct_minute"] == exp["anchor_ct_minute"]
    assert obs["release_sign"] == exp["release_sign"]
    assert obs["release_move"] == pytest.approx(exp["release_move"])
    assert obs["spike_ratio"] == pytest.approx(exp["spike_ratio"])
    assert obs["atr20"] == pytest.approx(expected[sym]["atr"])
    excl = f3.apply_exclusions(panel, panel["calendar"], sym)
    sig = f3.signal(obs, D["cpi"], excl, sym, panel["calendar"], panel)
    assert sig["status"] == "TRIGGERED" and sig["strata"] == exp["strata"]
    for arm in ("SC", "SD"):
        iid = f"FXF3-{sym}-{arm}-UP-D0-S2"
        intent = f3.order_intent(panel, obs, sig, iid, sym)
        assert intent["side"] == exp["sides"][arm]
        assert intent["entry_px_intent"] == pytest.approx(exp["entry"])
        atr = expected[sym]["atr"]
        sl = exp["entry"] + (atr if arm == "SD" else -atr)
        tp = exp["entry"] + (-2 * atr if arm == "SD" else 2 * atr)
        assert intent["sl_level"] == pytest.approx(sl)
        assert intent["tp_level"] == pytest.approx(tp)
        assert intent["exit_px_model"] == pytest.approx(exp["exit"])
        assert intent["exit_rule"] == exp["exit_rule"]


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_dn_release_expectations(ctx, sym):
    panels, expected = ctx
    panel, exp = panels[sym], expected[sym]["S_emp"]
    obs = f3.build_observables(panel, panel["calendar"], sym, D["emp"])
    assert obs["release_sign"] == exp["release_sign"]
    assert obs["release_move"] == pytest.approx(exp["release_move"])
    excl = f3.apply_exclusions(panel, panel["calendar"], sym)
    sig = f3.signal(obs, D["emp"], excl, sym, panel["calendar"], panel)
    assert sig["status"] == "TRIGGERED" and sig["strata"] == exp["strata"]
    for arm in ("SC", "SD"):
        iid = f"FXF3-{sym}-{arm}-DN-D0-S2"
        intent = f3.order_intent(panel, obs, sig, iid, sym)
        assert intent["side"] == exp["sides"][arm]
        assert intent["entry_px_intent"] == pytest.approx(exp["entry"])
        atr = obs["atr20"]                       # rule-derived from shared ATR
        sl = exp["entry"] + (atr if arm == "SC" else -atr)
        tp = exp["entry"] + (-2 * atr if arm == "SC" else 2 * atr)
        assert intent["sl_level"] == pytest.approx(sl)
        assert intent["tp_level"] == pytest.approx(tp)
        assert intent["exit_px_model"] == pytest.approx(exp["exit"])


@pytest.mark.parametrize("sym,scenario", [
    ("6E", "canceled"), ("6E", "other"), ("6E", "double"), ("6E", "quiet"),
    ("6E", "qbad"), ("6B", "canceled"), ("6B", "other"), ("6B", "double"),
    ("6B", "quiet"), ("6B", "qbad"),
])
def test_negative_control_days_no_trade(ctx, sym, scenario):
    panels, expected = ctx
    panel = panels[sym]
    s = D[scenario] if scenario != "qbad" else \
        ("2026-07-06" if sym == "6E" else "2023-06-15")
    obs = f3.build_observables(panel, panel["calendar"], sym, s)
    excl = f3.apply_exclusions(panel, panel["calendar"], sym)
    sig = f3.signal(obs, s, excl, sym, panel["calendar"], panel)
    exp = expected[sym]["S_" + scenario]
    assert sig["status"] == "NO_TRADE"
    for b in exp["blocking"]:
        assert b in sig["blocking"], (sym, scenario, sig["blocking"])
    intent = f3.order_intent(panel, obs, sig, sig["identity_draft_ids"][0], sym)
    assert intent["status"] == "NO_TRADE"


def test_vintage_pit_refusal_is_a_blocking_flag(ctx):
    """A stamp whose vintage_asof postdates the decision date refuses (the
    current-calendar inference ban, encoded)."""
    panels, _ = ctx
    panel = panels["6E"]
    row = [r for r in panel["calendar"]["bls_vintage"]
           if r["date"] == D["quiet"]][0]
    assert row["vintage_asof"] > D["quiet"]
    cls = f3.event_class("6E", panel["calendar"], D["quiet"])
    assert "PIT_VINTAGE_POSTDATED" in cls["blocking"]


def test_pit_truncation_identical_decision_instant_outputs(ctx):
    panels, _ = ctx
    for sym in ("6E", "6B"):
        panel = panels[sym]
        obs = f3.build_observables(panel, panel["calendar"], sym, D["cpi"])
        excl = f3.apply_exclusions(panel, panel["calendar"], sym)
        sig = f3.signal(obs, D["cpi"], excl, sym, panel["calendar"], panel)
        intent = f3.order_intent(panel, obs, sig, f"FXF3-{sym}-SC-UP-D0-S2", sym)
        asof = fx_common.parse_ts(intent["entry_ts_intent"])
        truncated = copy.deepcopy(panel)
        truncated["bars"] = [b for b in panel["bars"]
                             if fx_common.parse_ts(b["ts"]) <= asof]
        obs2 = f3.build_observables(truncated, panel["calendar"], sym, D["cpi"])
        excl2 = f3.apply_exclusions(truncated, panel["calendar"], sym)
        sig2 = f3.signal(obs2, D["cpi"], excl2, sym, panel["calendar"], truncated)
        intent2 = f3.order_intent(truncated, obs2, sig2,
                                  f"FXF3-{sym}-SC-UP-D0-S2", sym,
                                  resolve_exit=False)
        assert obs2["release_sign"] == obs["release_sign"]
        assert obs2["release_move"] == pytest.approx(obs["release_move"])
        assert sig2["tail"] == sig["tail"] and sig2["status"] == sig["status"]
        assert intent2["entry_px_intent"] == pytest.approx(intent["entry_px_intent"])
        assert intent2["sl_level"] == pytest.approx(intent["sl_level"])


def test_pb2_refusal_real_data_path(ctx):
    panels, _ = ctx
    panel = copy.deepcopy(panels["6E"])
    panel["provenance"] = "REAL_6E_CACHE"
    with pytest.raises(RefusedPendingOwnerDecision) as ei:
        f3.build_observables(panel, panel["calendar"], "6E", D["cpi"])
    assert ei.value.slot_id == "P5-FXEB-OD1"


def test_slot_refusals_and_identity_enumeration():
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.bind_option("FX-A")
    assert e.value.slot_id == "P5-FXEB-OD2"
    for sym in ("6E", "6B"):
        core = fx_common.core_ids("FX-F3", sym)
        assert len(core) == 8
        assert f"FXF3-{sym}-SC-UP-D0-S2" in core
        assert f"FXF3-{sym}-SD-DN-D1B-S2" in core
        assert fx_common.family_identity_counts("FX-F3", sym) == \
            {"core": 8, "controls": 3, "conv_d_minimal": 11}
