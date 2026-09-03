"""Synthetic causal tests for A8-V11-ILLIQ-AMIHUD (planted illiquidity premium).

A deterministic synthetic frame plants a forward drift increasing in symbol
illiquidity (dollar volume decreases with the symbol index; the premium is
applied only FORWARD of the warmup feature window).  The frozen anchor book
(long illiquid / short liquid quintiles, beta-neutral) must realise a
positive price spread; the sign-inverted causal control must flip the sign
exactly.  No real data and no scored artifact is produced here.
"""

import math

from research.adapter_v10.runner import run_strategy
from research.v11.families.illiq_amihud import IlliqAmihudPlugin
from research.v11.families.illiq_amihud.audits import build_synthetic_frame
from research.v11.families.illiq_amihud.strategy import compute_stamp_features

ANCHOR = "ILLIQ-AMIHUD-28D-W"
NEIGHBOUR = "ILLIQ-AMIHUD-56D-W"
CONTROL = "ILLIQ-AMIHUD-28D-W-INV"


def _make_plugin(arm_id: str, bars=None, settlements=None, weeks: int = 52):
    if bars is None:
        bars, settlements = build_synthetic_frame(weeks=weeks)
    ticks = {sym: 0.01 for sym in bars}
    return IlliqAmihudPlugin(
        bars_by_symbol=bars,
        arm_id=arm_id,
        tick_sizes=ticks,
        settle_points_by_symbol=settlements or {},
    )


def _price_pnl_sum(plugin):
    result = run_strategy(plugin, write_artifact_file=False)
    pnl = math.fsum(float(p["price_pnl_per_unit"]) for p in result["positions"])
    return pnl, result


def test_anchor_realises_positive_planted_illiquidity_premium():
    plugin = _make_plugin(ANCHOR)
    pnl, result = _price_pnl_sum(plugin)
    assert result["scored"] is False
    assert pnl > 0.0, f"anchor must profit from the planted premium, got {pnl}"


def test_sign_inverted_control_flips_the_spread_exactly():
    bars, settlements = build_synthetic_frame(weeks=52)
    anchor_pnl, _ = _price_pnl_sum(_make_plugin(ANCHOR, bars, settlements))
    control_pnl, _ = _price_pnl_sum(_make_plugin(CONTROL, bars, settlements))
    assert anchor_pnl > 0.0
    assert control_pnl < 0.0
    # the inverted book mirrors the anchor weight-for-weight: the realised
    # price spread must flip sign with no residual
    assert abs(anchor_pnl + control_pnl) < 1e-6


def test_books_are_long_illiquid_short_liquid_and_neutral():
    bars, _ = build_synthetic_frame(weeks=52)
    plugin = _make_plugin(ANCHOR, bars)
    universe = plugin.universe(plugin.baseline_stress())
    stamp = plugin.schedule().instants[25]
    book = plugin.targets_at(stamp, universe=universe, stress=plugin.baseline_stress())
    assert book["status"] == "OK"
    diagnostics = book["diagnostics"]
    longs = set(diagnostics["long_leg"])
    shorts = set(diagnostics["short_leg"])
    assert longs and shorts and not (longs & shorts)
    snapshot = compute_stamp_features(
        bars_by_symbol=plugin._bars,
        universe=universe,
        benchmark_symbol="BTCUSDT",
        decision_ns=int(stamp),
        formation_days=28,
    )
    for sym in longs | shorts:
        assert sym in snapshot.features
        assert sym in snapshot.betas
    for sym_long in longs:
        for sym_short in shorts:
            assert snapshot.features[sym_long] >= snapshot.features[sym_short]
    weights = book["weights"]
    assert abs(math.fsum(weights.values())) < 1e-9  # dollar-neutral
    book_beta = math.fsum(
        snapshot.betas[sym] * weights[sym] for sym in weights
    )
    assert abs(book_beta) < 1e-9  # beta-neutral under the frozen 90d beta
    # confound diagnostics ride along as artifacts only
    assert "rho_amihud_vs_reversal_7d" in diagnostics
    assert "rho_amihud_vs_log_size_proxy" in diagnostics


def test_double_generation_determinism():
    """Two independent generations produce byte-identical adapter results."""
    _, first = _price_pnl_sum(_make_plugin(ANCHOR))
    _, second = _price_pnl_sum(_make_plugin(ANCHOR))
    assert first["hashes"]["result_sha256"] == second["hashes"]["result_sha256"]
    # an independently rebuilt frame yields the same artifacts again
    bars, settlements = build_synthetic_frame(weeks=52)
    _, third = _price_pnl_sum(_make_plugin(ANCHOR, bars, settlements))
    assert third["hashes"]["result_sha256"] == first["hashes"]["result_sha256"]


def test_neighbour_arm_runs_through_the_same_pipeline():
    plugin = _make_plugin(NEIGHBOUR)
    pnl, result = _price_pnl_sum(plugin)
    assert result["scored"] is False
    assert math.isfinite(pnl)
