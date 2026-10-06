"""F4 adapter tests — M2c dual-window expectations, threshold law, roll
exclusions, Sunday stratum, PB2 + slot refusals. Outcome-blind; synthetic only."""
import copy

import fx_common
from fx_common import RefusedPendingOwnerDecision
from conftest import load_panel, load_expected
from f4_reopen_gap import adapter as f4

import pytest

D = {"reopen": "2026-04-17", "sunday": "2026-04-20", "roll": "2026-04-22",
     "after": "2026-04-23", "below": "2026-04-24"}


@pytest.fixture(scope="module")
def ctx():
    panels = {sym: load_panel("f4_reopen_gap", sym) for sym in ("6E", "6B")}
    expected = load_expected("f4_reopen_gap")["expected"]
    return panels, expected


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_m2c_dual_window_expectations(ctx, sym):
    """Both windows computed and distinctly labeled; WINDOW_A is the signal
    source; the engineered gap_B > gap_A echoes the erratum's direction."""
    panels, expected = ctx
    panel, exp = panels[sym], expected[sym]
    obs = f4.build_observables(panel, panel["calendar"], sym, D["reopen"])
    assert obs["gap_a"] == pytest.approx(exp["S_reopen"]["gap_a"])
    assert obs["gap_b"] == pytest.approx(exp["S_reopen"]["gap_b"])
    assert obs["gap_ratio_b_over_a"] == pytest.approx(exp["S_reopen"]["ratio"])
    assert obs["gap_b"] > obs["gap_a"] > 0
    assert set(obs["m2c_labels"]) == {"WINDOW_A_REOPEN_1700_PRIMARY",
                                      "WINDOW_B_RTH_OPEN_0830_ERRATUM_BASELINE"}
    assert obs["atr20"] == pytest.approx(exp["atr"])
    assert "SUNDAY_REOPEN_STRATUM" not in obs["flags"]
    excl = f4.apply_exclusions(panel, panel["calendar"], sym)
    thr = exp["threshold"]
    sig = f4.signal(obs, D["reopen"], excl, sym, panel["calendar"], panel,
                    min_gap_threshold=thr)
    assert sig["status"] == "TRIGGERED"
    assert sig["tail"] == exp["S_reopen"]["tail"]
    assert sig["strata"] == exp["S_reopen"]["strata"]
    assert sig["threshold_label"] == "SYNTHETIC-PARAMETER-NOT-REGISTERED"
    for arm in ("GC", "GD"):
        iid = f"FXF4-{sym}-{arm}-UP-D0-S2"
        intent = f4.order_intent(panel, obs, sig, iid, sym)
        assert intent["side"] == exp["S_reopen"]["sides"][arm]
        assert intent["entry_px_intent"] == pytest.approx(exp["S_reopen"]["entry"])
        assert intent["sl_level"] == pytest.approx(exp["S_reopen"]["sl"][arm])
        assert intent["tp_level"] == pytest.approx(exp["S_reopen"]["tp"][arm])
        assert intent["exit_px_model"] == pytest.approx(exp["S_reopen"]["exit"])
        assert intent["exit_rule"] == exp["S_reopen"]["exit_rule"]
        assert intent["window"] == "WINDOW_A_REOPEN_1700_PRIMARY"


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_threshold_law_refusal_and_below_threshold(ctx, sym):
    panels, expected = ctx
    panel = panels[sym]
    obs = f4.build_observables(panel, panel["calendar"], sym, D["reopen"])
    excl = f4.apply_exclusions(panel, panel["calendar"], sym)
    # no threshold -> NO-TRADE with the NOT_RUN grounds (registered-cycle decision)
    sig0 = f4.signal(obs, D["reopen"], excl, sym, panel["calendar"], panel,
                     min_gap_threshold=None)
    assert sig0["status"] == "NO_TRADE"
    assert sig0["blocking"] == ["THRESHOLD_NOT_REGISTERED"]
    assert "never tuned in PREP" in sig0["not_run_grounds"]
    # below-threshold gap -> the zero/minimum-gap-day placebo class
    obs_b = f4.build_observables(panel, panel["calendar"], sym, D["below"])
    sig_b = f4.signal(obs_b, D["below"], excl, sym, panel["calendar"], panel,
                      min_gap_threshold=expected[sym]["threshold"])
    assert sig_b["status"] == "NO_TRADE"
    assert sig_b["blocking"] == ["GAP_BELOW_THRESHOLD"]
    assert sig_b["gap_a"] == pytest.approx(expected[sym]["S_below"]["gap_a"])


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_sunday_stratum_and_dual_windows(ctx, sym):
    """Sunday reopen: observables computed on BOTH windows (ratio echoes the
    erratum's 2.3-5x band direction) but the session never trades the base."""
    panels, expected = ctx
    panel = panels[sym]
    obs = f4.build_observables(panel, panel["calendar"], sym, D["sunday"])
    exp = expected[sym]["S_sunday"]
    assert obs["gap_a"] == pytest.approx(exp["gap_a"])
    assert obs["gap_b"] == pytest.approx(exp["gap_b"])
    assert obs["gap_ratio_b_over_a"] == pytest.approx(exp["ratio"])
    assert obs["gap_b"] > obs["gap_a"] > 0
    assert "SUNDAY_REOPEN_STRATUM" in obs["flags"]
    excl = f4.apply_exclusions(panel, panel["calendar"], sym)
    sig = f4.signal(obs, D["sunday"], excl, sym, panel["calendar"], panel,
                    min_gap_threshold=expected[sym]["threshold"])
    assert sig["status"] == "NO_TRADE"
    assert "SUNDAY_REOPEN_STRATUM" in sig["blocking"]


@pytest.mark.parametrize("sym,scenario", [("6E", "roll"), ("6E", "after"),
                                          ("6B", "roll"), ("6B", "after")])
def test_roll_exclusions_no_trade(ctx, sym, scenario):
    panels, expected = ctx
    panel = panels[sym]
    s = D[scenario]
    obs = f4.build_observables(panel, panel["calendar"], sym, s)
    excl = f4.apply_exclusions(panel, panel["calendar"], sym)
    sig = f4.signal(obs, s, excl, sym, panel["calendar"], panel,
                    min_gap_threshold=expected[sym]["threshold"])
    assert sig["status"] == "NO_TRADE"
    assert expected[sym]["S_" + scenario]["blocking"][0] in sig["blocking"]


def test_pit_truncation_identical_decision_instant_outputs(ctx):
    panels, expected = ctx
    for sym in ("6E", "6B"):
        panel = panels[sym]
        obs = f4.build_observables(panel, panel["calendar"], sym, D["reopen"])
        excl = f4.apply_exclusions(panel, panel["calendar"], sym)
        sig = f4.signal(obs, D["reopen"], excl, sym, panel["calendar"], panel,
                        min_gap_threshold=expected[sym]["threshold"])
        intent = f4.order_intent(panel, obs, sig, f"FXF4-{sym}-GC-UP-D0-S2", sym)
        asof = fx_common.parse_ts(intent["entry_ts_intent"])
        truncated = copy.deepcopy(panel)
        truncated["bars"] = [b for b in panel["bars"]
                             if fx_common.parse_ts(b["ts"]) <= asof]
        obs2 = f4.build_observables(truncated, panel["calendar"], sym, D["reopen"])
        excl2 = f4.apply_exclusions(truncated, panel["calendar"], sym)
        sig2 = f4.signal(obs2, D["reopen"], excl2, sym, panel["calendar"],
                         truncated, min_gap_threshold=expected[sym]["threshold"])
        intent2 = f4.order_intent(truncated, obs2, sig2,
                                  f"FXF4-{sym}-GC-UP-D0-S2", sym,
                                  resolve_exit=False)
        assert obs2["gap_a"] == pytest.approx(obs["gap_a"])
        # gap_b prints at 08:30 the NEXT morning — later than the 17:05 decision
        # instant by construction, so it is asserted only on the full panel
        assert obs["gap_b"] == pytest.approx(expected[sym]["S_reopen"]["gap_b"])
        assert sig2["tail"] == sig["tail"] and sig2["status"] == sig["status"]
        assert intent2["entry_px_intent"] == pytest.approx(intent["entry_px_intent"])
        assert intent2["sl_level"] == pytest.approx(intent["sl_level"])


def test_pb2_refusal_real_data_path(ctx):
    panels, _ = ctx
    panel = copy.deepcopy(panels["6E"])
    panel["provenance"] = "REAL_6E_CACHE"
    with pytest.raises(RefusedPendingOwnerDecision) as ei:
        f4.build_observables(panel, panel["calendar"], "6E", D["reopen"])
    assert ei.value.slot_id == "P5-FXEB-OD1"


def test_slot_refusals_and_identity_enumeration():
    with pytest.raises(RefusedPendingOwnerDecision) as e:
        fx_common.bind_option("FX-C")
    assert e.value.slot_id == "P5-FXEB-OD2"
    for sym in ("6E", "6B"):
        core = fx_common.core_ids("FX-F4", sym)
        assert len(core) == 8
        assert f"FXF4-{sym}-GC-UP-D0-S2" in core
        assert f"FXF4-{sym}-GD-DN-D1B-S2" in core
        rmm = [f"FXRMM-{sym}-RB{k}" for k in (1, 2, 3, 4)]
        assert all(i not in core for i in rmm)   # RMM IDs live in their own package
