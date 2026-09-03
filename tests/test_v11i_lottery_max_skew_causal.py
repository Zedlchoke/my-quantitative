"""Synthetic causal tests for V11-SEED-LOTTERY-MAX-SKEW (frozen sign).

The seed brief freezes the expected sign: ``anchor net spread > 0; inverted
control <= 0``.  On synthetic data with a planted lottery premium (a +5%
idiosyncratic spike that mean-reverts over the following week, so a high
trailing-7d residual MAX predicts negative forward residual returns), the
frozen anchor book (long LOW-MAX / short HIGH-MAX quintiles) must earn a
positive forward residual spread and the sign-inverted causal control must
flip the sign.
"""

from __future__ import annotations

import math

from research.v11.families.lottery_max_skew.plugin import (
    ANCHOR_ARM,
    CONTROL_ARM,
    NEIGHBOUR_ARM,
    build_arm_plugin,
)
from research.v11.families.lottery_max_skew.strategy import (
    DAY_NS,
    build_schedule_instants,
    day_index,
)
from research.v11.families.lottery_max_skew.synthetic import (
    SPIKE_REVERSION,
    build_synthetic_bars,
)

#: synthetic calendar: complete days covering >=120 warmup returns before the
#: frozen Monday stamps of Aug-Oct 2025 plus the forward spread horizon.
#: (day 20200 = 2025-05-20 UTC; day 20384 = 2025-11-21 UTC)
START_DAY = 20_200
N_DAYS = 185
N_STAMPS = 8


def _plugin(arm: str):
    inputs, _frames = build_synthetic_bars(start_day=START_DAY, n_days=N_DAYS)
    return build_arm_plugin(arm, inputs), inputs


def _monday_stamps(count: int) -> list[int]:
    instants = [i for i in build_schedule_instants()[:-1]]
    assert len(instants) >= count
    return instants[:count]


def _book_weights(plugin, instant: int, universe) -> dict[str, float]:
    book = plugin.targets_at(instant, universe=universe, stress=plugin.baseline_stress())
    assert book["status"] == "OK", book
    assert book.get("reason_code") is None
    return {sym: w for sym, w in book["weights"]}


def _forward_residual_spread(
    weights: dict[str, float], inputs, instant: int, horizon_days: int = 7
) -> float:
    """Capital-weighted residual forward return of the book (signal only).

    The holding week of a book formed at Monday 00:00Z is the daily returns
    of days ``D .. D+6`` (day ``D``'s return completes Monday 23:59:59Z,
    inside the holding span).
    """
    first_day = day_index(instant)
    spread = 0.0
    for symbol, weight in weights.items():
        frame = inputs.daily_by_symbol[symbol]
        benchmark = inputs.daily_by_symbol["BTCUSDT-PERP.BINANCE"]
        leg = 0.0
        for day in range(first_day, first_day + horizon_days):
            r_i = frame.daily_return(day)
            r_m = benchmark.daily_return(day)
            assert r_i is not None and r_m is not None
            leg += r_i - r_m
        spread += weight * leg
    return spread


def test_anchor_book_has_frozen_positive_spread_control_flips() -> None:
    anchor, inputs = _plugin(ANCHOR_ARM)
    control, _ = _plugin(CONTROL_ARM)
    universe = anchor.tradeable_universe()
    stamps = _monday_stamps(N_STAMPS)
    anchor_spreads: list[float] = []
    control_spreads: list[float] = []
    for instant in stamps:
        anchor_w = _book_weights(anchor, instant, universe)
        control_w = _book_weights(control, instant, universe)
        # the causal control is the sign-inverted anchor book
        flipped = {sym: -w for sym, w in anchor_w.items()}
        assert set(flipped) == set(control_w)
        for sym in sorted(flipped):
            assert abs(flipped[sym] - control_w[sym]) < 1e-12, sym
        anchor_spreads.append(_forward_residual_spread(anchor_w, inputs, instant))
        control_spreads.append(_forward_residual_spread(control_w, inputs, instant))
    mean_anchor = math.fsum(anchor_spreads) / len(anchor_spreads)
    mean_control = math.fsum(control_spreads) / len(control_spreads)
    assert mean_anchor > 0.0, anchor_spreads
    assert mean_control < 0.0, control_spreads
    # the flip is exact: control spread == -anchor spread
    for a, c in zip(anchor_spreads, control_spreads):
        assert abs(a + c) < 1e-12
    # the planted premium bounds the per-week spread from below
    assert mean_anchor >= SPIKE_REVERSION, mean_anchor


def test_anchor_book_breadth_weights_and_gross() -> None:
    anchor, _ = _plugin(ANCHOR_ARM)
    universe = anchor.tradeable_universe()
    instant = _monday_stamps(1)[0]
    weights = _book_weights(anchor, instant, universe)
    longs = {s: w for s, w in weights.items() if w > 0}
    shorts = {s: w for s, w in weights.items() if w < 0}
    assert len(longs) >= 2 and len(shorts) >= 2
    assert math.fsum(abs(w) for w in weights.values()) - 1.0 < 1e-9
    assert all(abs(w) <= 0.30 + 1e-9 for w in weights.values())
    # low-minus-high: long leg holds the LOW residual-MAX quintile
    stamp = anchor._engine.features_at(
        instant_ns=instant,
        arm=ANCHOR_ARM,
        symbols=sorted(universe),
        last_completed_bar=anchor._last_completed_bar_map(universe, instant),
    )
    assert max(stamp.features[s] for s in longs) <= min(stamp.features[s] for s in shorts) + 1e-15


def test_books_are_gross_one_and_beta_neutral_ish() -> None:
    anchor, _ = _plugin(ANCHOR_ARM)
    universe = anchor.tradeable_universe()
    for instant in _monday_stamps(4):
        book = anchor.targets_at(instant, universe=universe, stress=anchor.baseline_stress())
        weights = {s: w for s, w in book["weights"]}
        gross = math.fsum(abs(w) for w in weights.values())
        assert abs(gross - 1.0) < 1e-9
        diagnostics = book["diagnostics"]
        if diagnostics.get("beta_split") == "btc_beta_neutral":
            b_l = diagnostics["beta_long_leg_mean"]
            b_s = diagnostics["beta_short_leg_mean"]
            leg_gross_long = len(
                [1 for s, w in weights.items() if w > 0]
            ) and math.fsum(w for w in weights.values() if w > 0)
            leg_gross_short = -math.fsum(w for w in weights.values() if w < 0)
            assert abs(leg_gross_long * b_l - leg_gross_short * b_s) < 1e-6


def test_fold_boundary_stamps_force_flat_on_synthetic() -> None:
    anchor, _ = _plugin(ANCHOR_ARM)
    universe = anchor.tradeable_universe()
    instants = build_schedule_instants()
    force_flat = sorted(
        i for i in instants[:-1]
        if anchor.targets_at(i, universe=universe, stress=anchor.baseline_stress())[
            "reason_code"
        ] == "fold_boundary_force_flat"
    )
    assert len(force_flat) == 3  # one per frozen fold F0/F1/F2
    terminal = anchor.targets_at(
        instants[-1], universe=universe, stress=anchor.baseline_stress()
    )
    assert terminal["reason_code"] == "terminal_force_flat"
    assert terminal["weights"] == []
