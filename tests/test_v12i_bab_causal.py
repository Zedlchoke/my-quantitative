"""Hand-computed causal tests for A12-V12-BAB-LOWBETA (golden fixtures).

Fixtures are closed-form synthetic constructions (see ``audits.py`` and the
committed ``golden/`` files):

* the beta-ranking frame plants a forward drift DECREASING in the designed
  beta, so low-beta names are constructed to outperform high-beta names;
* the anchor book must long the 4 lowest / short the 4 highest designed
  betas exactly, realise a positive spread, and the INV control must negate
  the spread EXACTLY (weight-for-weight mirror at identical fills);
* the downcorr frame's closed-form correlations must separate the neighbour
  book from the anchor book (exact mirror on that frame);
* an 8-eligible frame fails closed.

No real data and no scored artifact is produced here.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from research.adapter_v10.runner import run_strategy
from research.v12.families.bab_lowbeta.audits import (
    build_beta_ranking_frame,
    build_downcorr_frame,
    make_plugin,
)
from research.v12.families.bab_lowbeta.plugin import BabLowBetaPlugin
from research.v12.families.bab_lowbeta.strategy import (
    BENCHMARK_SYMBOL_EXCLUDED,
    build_bab_book,
    weekly_monday_stamps,
)

GOLDEN = Path(__file__).resolve().parents[1] / "research" / "v12" / "families" / "bab_lowbeta" / "golden"
ANCHOR = "BAB-90D-W"
NEIGHBOUR = "BAB-DOWNCORR-90D-W"
CONTROL = "BAB-90D-W-INV"


@pytest.fixture(scope="module")
def beta_frame():
    bars, design = build_beta_ranking_frame()
    return bars, design


@pytest.fixture(scope="module")
def downcorr_frame():
    bars, design = build_downcorr_frame()
    return bars, design


# --------------------------------------------------------------------------- #
# Golden micro case (pure book construction, hand-computed weights)
# --------------------------------------------------------------------------- #
def test_micro_weights_case_matches_hand_computation():
    golden = json.loads((GOLDEN / "micro_weights_case.json").read_text())["hand_computation"]
    features = dict(golden["betas"])
    book = build_bab_book(features=features, betas=features, arm_sign=1)
    assert book["status"] == "OK"
    assert sorted(book["diagnostics"]["long_leg"]) == sorted(golden["expected_long_leg"])
    assert sorted(book["diagnostics"]["short_leg"]) == sorted(golden["expected_short_leg"])
    assert book["diagnostics"]["hedge_ratio"] == pytest.approx(
        golden["hedge_ratio"], abs=1e-12
    )
    for sym, want in golden["expected_weights"].items():
        assert book["weights"][sym] == pytest.approx(want, abs=1e-12)
    assert book["diagnostics"]["gross"] == pytest.approx(golden["expected_gross"], abs=1e-12)
    assert book["diagnostics"]["book_beta_post_hedge"] == pytest.approx(
        golden["expected_book_beta"], abs=1e-9
    )
    assert book["diagnostics"]["uniform_cap_scale"] == pytest.approx(
        golden["expected_uniform_cap_scale"], abs=1e-15
    )
    inv = build_bab_book(features=features, betas=features, arm_sign=-1)
    for sym, weight in book["weights"].items():
        assert inv["weights"][sym] + weight == pytest.approx(0.0, abs=1e-15)


def test_below_min_eligible_fails_closed():
    golden = json.loads((GOLDEN / "below_min_case.json").read_text())["hand_computation"]
    eight = {f"S{i}": 1.0 + 0.1 * i for i in range(8)}
    book = build_bab_book(features=eight, betas=dict(eight), arm_sign=1)
    assert book["status"] == golden["expected_status"]
    assert book["reason_code"] == golden["expected_reason_code"]
    assert book["weights"] == golden["expected_weights"]


# --------------------------------------------------------------------------- #
# Beta-ranking fixture: legs match the hand-computed ranking exactly
# --------------------------------------------------------------------------- #
def test_anchor_book_matches_hand_computed_ranking(beta_frame):
    bars, design = beta_frame
    golden = json.loads((GOLDEN / "beta_ranking_fixture.json").read_text())["hand_computation"]
    plugin = make_plugin(ANCHOR, bars)
    universe = plugin.universe(plugin.baseline_stress())
    stamps = plugin.schedule().instants
    book = plugin.targets_at(int(stamps[0]), universe=universe, stress=plugin.baseline_stress())
    assert book["status"] == "OK"
    assert sorted(book["diagnostics"]["long_leg"]) == sorted(golden["expected_long_leg"])
    assert sorted(book["diagnostics"]["short_leg"]) == sorted(golden["expected_short_leg"])
    for sym in book["diagnostics"]["long_leg"]:
        assert book["weights"][sym] == pytest.approx(
            golden["expected_long_weight_each"], abs=1e-12
        )
    for sym in book["diagnostics"]["short_leg"]:
        assert book["weights"][sym] == pytest.approx(
            golden["expected_short_weight_each"], abs=1e-12
        )
    assert book["diagnostics"]["book_beta_post_hedge"] == pytest.approx(0.0, abs=1e-9)


def test_ranking_preserved_at_every_stamp(beta_frame):
    """Long legs are always the 4 lowest designed betas, shorts the 4 highest."""
    bars, design = beta_frame
    plugin = make_plugin(ANCHOR, bars)
    universe = plugin.universe(plugin.baseline_stress())
    ranked = sorted(design["betas"], key=lambda s: design["betas"][s])
    for stamp in plugin.schedule().instants:
        book = plugin.targets_at(int(stamp), universe=universe, stress=plugin.baseline_stress())
        if not book["weights"]:
            assert book["reason_code"] == "FOLD_BOUNDARY_FORCE_FLAT"
            continue
        assert sorted(book["diagnostics"]["long_leg"]) == sorted(ranked[:4])
        assert sorted(book["diagnostics"]["short_leg"]) == sorted(ranked[-4:])


# --------------------------------------------------------------------------- #
# Causal spread: low betas outperform; INV negates exactly
# --------------------------------------------------------------------------- #
def _price_pnl_sum(plugin):
    result = run_strategy(plugin, write_artifact_file=False)
    pnl = math.fsum(float(p["price_pnl_per_unit"]) for p in result["positions"])
    return pnl, result


def test_anchor_realises_positive_planted_low_beta_spread(beta_frame):
    bars, _ = beta_frame
    pnl, result = _price_pnl_sum(make_plugin(ANCHOR, bars))
    assert result["scored"] is False
    assert pnl > 0.0, f"anchor must profit from the planted low-beta drift, got {pnl}"


def test_sign_inverted_control_negates_the_spread_exactly(beta_frame):
    bars, _ = beta_frame
    anchor_pnl, _ = _price_pnl_sum(make_plugin(ANCHOR, bars))
    control_pnl, _ = _price_pnl_sum(make_plugin(CONTROL, bars))
    assert anchor_pnl > 0.0
    assert control_pnl < 0.0
    # the inverted book mirrors the anchor weight-for-weight at identical
    # fills: the realised price spread must negate with no residual
    assert abs(anchor_pnl + control_pnl) < 1e-9


def test_anchor_and_control_books_are_exact_mirrors(beta_frame):
    bars, _ = beta_frame
    anchor = make_plugin(ANCHOR, bars)
    control = make_plugin(CONTROL, bars)
    universe = anchor.universe(anchor.baseline_stress())
    for stamp in anchor.schedule().instants:
        a = anchor.targets_at(int(stamp), universe=universe, stress=anchor.baseline_stress())
        c = control.targets_at(int(stamp), universe=universe, stress=control.baseline_stress())
        assert sorted(a["weights"]) == sorted(c["weights"])
        for sym, weight in a["weights"].items():
            assert c["weights"][sym] + weight == pytest.approx(0.0, abs=1e-12)


# --------------------------------------------------------------------------- #
# Downside-correlation fixture: neighbour distinguished from anchor
# --------------------------------------------------------------------------- #
def test_neighbour_book_differs_from_anchor_on_downcorr_fixture(downcorr_frame):
    bars, _ = downcorr_frame
    golden = json.loads((GOLDEN / "downcorr_fixture.json").read_text())["hand_computation"]
    anchor = make_plugin(ANCHOR, bars)
    neighbour = make_plugin(NEIGHBOUR, bars)
    universe = anchor.universe(anchor.baseline_stress())
    stamps = anchor.schedule().instants
    a = anchor.targets_at(int(stamps[0]), universe=universe, stress=anchor.baseline_stress())
    n = neighbour.targets_at(int(stamps[0]), universe=universe, stress=neighbour.baseline_stress())
    assert sorted(a["diagnostics"]["long_leg"]) == sorted(golden["expected_anchor_long_leg"])
    assert sorted(a["diagnostics"]["short_leg"]) == sorted(golden["expected_anchor_short_leg"])
    assert sorted(n["diagnostics"]["long_leg"]) == sorted(golden["expected_neighbour_long_leg"])
    assert sorted(n["diagnostics"]["short_leg"]) == sorted(golden["expected_neighbour_short_leg"])
    # the neighbour book is the exact mirror of the anchor book on this frame
    assert sorted(n["diagnostics"]["long_leg"]) == sorted(a["diagnostics"]["short_leg"])
    assert sorted(n["diagnostics"]["short_leg"]) == sorted(a["diagnostics"]["long_leg"])


def test_downcorr_feature_matches_closed_form_at_every_sampled_stamp(downcorr_frame):
    bars, design = downcorr_frame
    golden = json.loads((GOLDEN / "downcorr_fixture.json").read_text())["hand_computation"]
    from research.v12.families.bab_lowbeta.strategy import compute_stamp_features

    plugin = make_plugin(NEIGHBOUR, bars)
    universe = plugin.universe(plugin.baseline_stress())
    stamps = plugin.schedule().instants
    for stamp in (stamps[0], stamps[7], stamps[26], stamps[-2]):
        snapshot = compute_stamp_features(
            bars_by_symbol=plugin._bars,
            universe=universe,
            benchmark_symbol=BENCHMARK_SYMBOL_EXCLUDED,
            decision_ns=int(stamp),
            feature="btc_downside_correlation_90d_daily",
        )
        for sym, want in golden["expected_downcorr"].items():
            assert snapshot.features[sym] == pytest.approx(want, abs=1e-9)


def test_invalid_arm_sign_refused():
    with pytest.raises(Exception):
        build_bab_book(features={}, betas={}, arm_sign=0)
