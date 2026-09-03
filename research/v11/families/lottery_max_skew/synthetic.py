"""Deterministic synthetic fixtures for the LOT family tests.

No randomness anywhere: every series is a closed-form function of integers,
so two constructions are byte-identical by design and the planted
lottery premium is exact.

The planted mechanism mirrors the frozen hypothesis: a large POSITIVE
idiosyncratic (BTC-residual) spike raises a symbol's trailing-7d residual
MAX, and the spike mean-reverts over the following week (negative lottery /
MAX premium).  The frozen anchor book (long LOW-MAX, short HIGH-MAX) must
therefore earn a positive forward residual spread and the sign-inverted
causal control must flip.
"""

from __future__ import annotations

import math
from typing import Mapping

from research.adapter_v10.protocol import SettlementPoint
from research.v11.families.lottery_max_skew.plugin import BarEvent, MarketInputs
from research.v11.families.lottery_max_skew.strategy import DailyFrame, aggregate_daily

DAY_NS = 86_400_000_000_000
BAR_NS = 900_000_000_000
BARS_PER_DAY = 96
#: close-stamp shave before the nominal grid line (mirrors staged bars)
BAR_SHAVE_NS = 999_936

SYNTH_BENCHMARK = "BTCUSDT-PERP.BINANCE"
SYNTH_SYMBOLS = tuple(f"SYMSYN{i:02d}-PERP.BINANCE" for i in range(15))

#: planted parameters (frozen fixture constants, NOT strategy parameters)
SPIKE_SIZE = 0.05          # one-day idiosyncratic lottery spike (+5%)
SPIKE_REVERSION = 0.008    # per-day residual give-back over the next 7 days
SPIKE_PERIOD_DAYS = 11     # symbol i spikes when (day - i) % 11 == 0
MARKET_AMP = 0.010
IDIO_AMP = 0.001           # small residual noise so the premium dominates
BASE_PRICE = 100.0


def daily_symbol_return(symbol_index: int, day: int) -> float:
    """Deterministic daily return with the planted lottery mechanism.

    ``r = beta_i * m_t + e_{i,t}`` where ``m_t`` is the shared BTC market
    factor, ``e`` the idiosyncratic residual carrying the spike/reversion
    pair: a ``+SPIKE_SIZE`` residual up-move on the symbol's spike day is
    repaid by ``SPIKE_REVERSION`` per day over the following week.
    """
    beta = 0.8 + 0.04 * symbol_index
    market = MARKET_AMP * math.sin(2.0 * math.pi * day / 40.0)
    idio = IDIO_AMP * math.sin(2.0 * math.pi * day / (17.0 + 3.0 * symbol_index) + symbol_index)
    if (day - symbol_index) % SPIKE_PERIOD_DAYS == 0:
        idio += SPIKE_SIZE
    for k in range(1, 8):
        if (day - symbol_index - k) % SPIKE_PERIOD_DAYS == 0:
            # a spike happened k days ago: the lottery spike mean-reverts
            idio -= SPIKE_REVERSION
            break
    return beta * market + idio


def benchmark_daily_return(day: int) -> float:
    return MARKET_AMP * math.sin(2.0 * math.pi * day / 40.0)


def build_synthetic_bars(
    *, start_day: int, n_days: int
) -> tuple[MarketInputs, Mapping[str, DailyFrame]]:
    """Build the synthetic ``MarketInputs`` (and daily frames) deterministically.

    Day ``start_day`` is the FIRST day with a complete 96-bar UTC day; the
    caller picks ``start_day`` so the warmup + window stamps are covered.
    """
    daily_by_symbol: dict[str, DailyFrame] = {}
    bars_by_symbol: dict[str, list[BarEvent]] = {}
    settlements_by_symbol: dict[str, tuple[SettlementPoint, ...]] = {}
    tick_sizes: dict[str, float] = {}

    benchmark_closes: dict[int, float] = {}
    previous = BASE_PRICE
    for offset in range(n_days):
        day = start_day + offset
        previous = previous * (1.0 + benchmark_daily_return(day))
        benchmark_closes[day] = previous
    daily_by_symbol[SYNTH_BENCHMARK] = _frame_from_closes(benchmark_closes)
    bars_by_symbol[SYNTH_BENCHMARK] = _bars_from_closes(benchmark_closes)
    settlements_by_symbol[SYNTH_BENCHMARK] = _funding_series(start_day, n_days)
    tick_sizes[SYNTH_BENCHMARK] = 0.1

    for index, symbol in enumerate(SYNTH_SYMBOLS):
        closes: dict[int, float] = {}
        previous = BASE_PRICE * (1.0 + 0.1 * index)
        for offset in range(n_days):
            day = start_day + offset
            previous = previous * (1.0 + daily_symbol_return(index, day))
            closes[day] = previous
        daily_by_symbol[symbol] = _frame_from_closes(closes)
        bars_by_symbol[symbol] = _bars_from_closes(closes)
        settlements_by_symbol[symbol] = _funding_series(start_day, n_days)
        tick_sizes[symbol] = 0.01

    inputs = MarketInputs(
        daily_by_symbol=daily_by_symbol,
        bars_by_symbol=bars_by_symbol,
        settlements_by_symbol=settlements_by_symbol,
        tick_sizes=tick_sizes,
        symbols=[SYNTH_BENCHMARK, *SYNTH_SYMBOLS],
    )
    return inputs, daily_by_symbol


def _frame_from_closes(closes: Mapping[int, float]) -> DailyFrame:
    enriched = []
    for day in sorted(closes):
        day_ns = day * DAY_NS
        for j in range(BARS_PER_DAY):
            enriched.append(
                {
                    "ts_event_ns": day_ns + (j + 1) * BAR_NS - BAR_SHAVE_NS,
                    "close": closes[day],
                    "quote_volume": 1_000_000.0,
                }
            )
    return aggregate_daily(enriched)


def _bars_from_closes(closes: Mapping[int, float]) -> list[BarEvent]:
    bars: list[BarEvent] = []
    for day in sorted(closes):
        day_ns = day * DAY_NS
        for j in range(BARS_PER_DAY):
            ts = day_ns + (j + 1) * BAR_NS - BAR_SHAVE_NS
            bars.append(BarEvent(ts_event_ns=ts, open=closes[day], close=closes[day]))
    return bars


def _funding_series(start_day: int, n_days: int, rate: float = 0.0001) -> tuple[SettlementPoint, ...]:
    """Three 8h funding settlements per UTC day (native cadence)."""
    points = []
    for offset in range(n_days):
        day_ns = (start_day + offset) * DAY_NS
        for hour in (8, 16, 24):
            points.append(
                SettlementPoint(publish_ts_ns=day_ns + hour * 3600 * 1_000_000_000, value=rate)
            )
    return tuple(points)


__all__ = [
    "BAR_NS",
    "BARS_PER_DAY",
    "IDIO_AMP",
    "MARKET_AMP",
    "SPIKE_PERIOD_DAYS",
    "SPIKE_REVERSION",
    "SPIKE_SIZE",
    "SYNTH_BENCHMARK",
    "SYNTH_SYMBOLS",
    "build_synthetic_bars",
    "daily_symbol_return",
]
