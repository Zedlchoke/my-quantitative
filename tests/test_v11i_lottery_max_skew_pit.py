"""PIT / no-leak tests for V11-SEED-LOTTERY-MAX-SKEW.

A bar (or funding settlement row) stamped AFTER a decision stamp must never
be able to change that stamp's features, eligibility or target book.  This
family consumes completed 15m bars and native funding settlements only (the
staged snapshot has no OI inputs for this family; the OI row clause of the
lane contract therefore reduces to the same after-stamp test on the funding
settlement series, the only other stamped input).

The test mutates the post-stamp tail of the data (append/alter) and asserts
the pre-stamp computation is BIT-identical; it also verifies the mirror
sanity check that mutating PRE-stamp data DOES move the stamp's book.
"""

from __future__ import annotations

import copy
import json

from research.adapter_v10.protocol import SettlementPoint
from research.v11.families.lottery_max_skew.plugin import (
    ANCHOR_ARM,
    NEIGHBOUR_ARM,
    build_arm_plugin,
)
from research.v11.families.lottery_max_skew.strategy import (
    DAY_NS,
    day_index,
    build_schedule_instants,
)
from research.v11.families.lottery_max_skew.synthetic import (
    SYNTH_BENCHMARK,
    SYNTH_SYMBOLS,
    build_synthetic_bars,
)

START_DAY = 20_200
N_DAYS = 185


def _inputs():
    inputs, _frames = build_synthetic_bars(start_day=START_DAY, n_days=N_DAYS)
    return inputs


def _canon(payload) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _stamp_payload(plugin, instant: int, universe) -> dict:
    """The PIT-relevant part of one stamp: features -> target book.

    Deliberately EXCLUDES fills/marks: the declared execution lag fills at
    the covering bar whose close stamp is (by design) after the decision
    instant, so execution prices are allowed -- required -- to depend on
    post-stamp-stamped bars.  The SIGNAL side must not.
    """
    baseline = plugin.baseline_stress()
    return {
        "book": plugin.targets_at(int(instant), universe=universe, stress=baseline),
    }


def _first_instant_with_book(plugin, universe) -> int:
    baseline = plugin.baseline_stress()
    for instant in build_schedule_instants()[:-1]:
        book = plugin.targets_at(int(instant), universe=universe, stress=baseline)
        if book["weights"]:
            return int(instant)
    raise AssertionError("no synthetic stamp produced a book")


def _mutate_after(inputs, cutoff: int, *, wild: bool) -> None:
    """Corrupt every observation completing at/after ``cutoff`` in place.

    BOTH injected views are corrupted: the 15m ``bars_by_symbol`` (execution
    side) and the daily frames ``daily_by_symbol`` (feature side) -- the
    feature engine reads the daily aggregates, so a bars-only mutation could
    never reach the signal and the sanity mirror below would be vacuous.
    A day's last bar completes at ``(day+1)*DAY_NS - BAR_SHAVE_NS >= cutoff``
    exactly when ``day >= cutoff // DAY_NS``, so whole UTC days are the
    correct corruption granularity.
    """
    from research.v11.families.lottery_max_skew.strategy import DailyFrame

    cutoff_day = int(cutoff) // DAY_NS
    for symbol in list(inputs.daily_by_symbol):
        frame = inputs.daily_by_symbol[symbol]
        closes = dict(frame.closes)
        for day in sorted(closes):
            if day >= cutoff_day:
                closes[day] = closes[day] * (11.0 if wild else 1.0)
        inputs.daily_by_symbol[symbol] = DailyFrame(
            closes=closes, dollar_volume=dict(frame.dollar_volume)
        )
    for symbol in list(inputs.bars_by_symbol):
        bars = inputs.bars_by_symbol[symbol]
        kept = [b for b in bars if b.ts_event_ns < cutoff]
        extra = [
            type(b)(
                ts_event_ns=b.ts_event_ns,
                open=(b.open * 7.5 if wild else b.open),
                close=(b.close * 11.0 if wild else b.close),
            )
            for b in bars
            if b.ts_event_ns >= cutoff
        ]
        inputs.bars_by_symbol[symbol] = kept + extra


def test_post_stamp_bars_cannot_enter_stamp_features() -> None:
    inputs = _inputs()
    plugin = build_arm_plugin(ANCHOR_ARM, inputs)
    universe = plugin.tradeable_universe()
    instant = _first_instant_with_book(plugin, universe)
    before = _stamp_payload(plugin, instant, universe)

    # Mutate EVERY bar completing at/after the decision instant: wild prices
    # on every symbol (incl. the benchmark) from Monday's first bar onward.
    # The stamp's features may only use days strictly before the stamp, so
    # even the decision day's own (mutated) daily close must not matter.
    mutated = _inputs()
    cutoff = day_index(instant) * DAY_NS
    _mutate_after(mutated, cutoff, wild=True)
    plugin_mutated = build_arm_plugin(ANCHOR_ARM, mutated)
    after = _stamp_payload(plugin_mutated, instant, universe)
    assert _canon(before) == _canon(after)


def test_post_stamp_mutations_do_move_later_stamps_sanity() -> None:
    """Mirror check: post-stamp data must matter for LATER stamps, proving
    the invariance above is not vacuous."""
    inputs = _inputs()
    plugin = build_arm_plugin(ANCHOR_ARM, inputs)
    universe = plugin.tradeable_universe()
    instants = [i for i in build_schedule_instants()[:-1]]
    instant = _first_instant_with_book(plugin, universe)
    later = next(i for i in instants if i > instant + 14 * DAY_NS)
    before = _stamp_payload(plugin, later, universe)

    mutated = _inputs()
    cutoff = day_index(instant) * DAY_NS
    _mutate_after(mutated, cutoff, wild=True)
    after = _stamp_payload(build_arm_plugin(ANCHOR_ARM, mutated), later, universe)
    assert _canon(before) != _canon(after)


def test_funding_rows_after_a_stamp_cannot_enter_earlier_spans() -> None:
    """A settlement row published after a decision stamp cannot accrue to a
    holding span that closed before it (LONG_PAYS_POSITIVE_RATE accrual)."""
    from research.adapter_v10.protocol import PositionSpan
    from research.v11.families.lottery_max_skew.plugin import MarketInputs
    import math

    inputs = _inputs()
    plugin = build_arm_plugin(NEIGHBOUR_ARM, inputs)
    symbol = sorted(plugin.tradeable_universe())[0]
    span = PositionSpan(
        symbol=symbol,
        signed_weight=-0.25,
        start_ns=(START_DAY + 160) * DAY_NS,
        end_ns=(START_DAY + 167) * DAY_NS,
    )
    base_flows = plugin.funding_cashflows_for_spans([span])

    # duplicate inputs, then append wild funding rows far after the span
    settled = dict(inputs.settlements_by_symbol)
    settled[symbol] = tuple(settled[symbol]) + tuple(
        SettlementPoint(
            publish_ts_ns=(START_DAY + 200) * DAY_NS + k * 3600 * 1_000_000_000,
            value=9.99,
        )
        for k in range(10)
    )
    mutated = MarketInputs(
        daily_by_symbol=inputs.daily_by_symbol,
        bars_by_symbol=inputs.bars_by_symbol,
        settlements_by_symbol=settled,
        tick_sizes=inputs.tick_sizes,
        symbols=inputs.symbols,
    )
    plugin_mutated = build_arm_plugin(NEIGHBOUR_ARM, mutated)
    mutated_flows = plugin_mutated.funding_cashflows_for_spans([span])
    assert base_flows and mutated_flows
    assert _canon(base_flows) == _canon(mutated_flows)
    # every flow stays strictly inside the span with the frozen sign
    for flow in mutated_flows:
        assert span.start_ns < int(flow["publish_ts_ns"]) <= span.end_ns
        expected = -float(flow["signed_weight"]) * float(flow["rate"])
        assert abs(float(flow["cashflow_per_unit_capital"]) - expected) < 1e-12


def test_daily_aggregation_never_uses_incomplete_days() -> None:
    """A day missing any of its 96 bars is UNAVAILABLE (never forward
    filled), so a partial final day can never masquerade as signal."""
    from research.v11.families.lottery_max_skew.strategy import aggregate_daily

    bars = []
    for j in range(95):  # one bar short
        bars.append(
            {
                "ts_event_ns": 100 * DAY_NS + (j + 1) * 900_000_000_000 - 999_936,
                "close": 100.0 + j,
                "quote_volume": 1.0,
            }
        )
    frame = aggregate_daily(bars)
    assert frame.closes == {}
    assert frame.daily_return(100) is None
