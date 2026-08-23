"""Behavior/unit tests for H-VOLCOMP-BRKOUT-v1 (vol_compression_breakout).

Drives ``VolCompressionBreakoutStrategy.on_bar`` directly with synthetic,
fully deterministic 15m bars. Registered indicators (BollingerBands, ATR) are
fed explicitly to mimic engine auto-registration; lifecycle events are
simulated through the real ``on_position_opened``/``on_position_closed``
handlers so cooldown/daily-risk accounting runs unmodified.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from decimal import Decimal

from nautilus_trader.indicators import AverageTrueRange
from nautilus_trader.indicators import BollingerBands
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity

import strategy_vol_compression_breakout as mod
from strategy_vol_compression_breakout import (
    DEFAULT_WARMUP_BARS,
    SQUEEZE_LOOKBACK_GRID,
    VOLUME_RATIO_GRID,
    VolCompressionBreakoutConfig,
    VolCompressionBreakoutSettings,
    VolCompressionBreakoutStrategy,
    bollinger_bandwidth_pct,
    bandwidth_range_rank,
)

BAR_TYPE = BarType.from_str("SOLUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL")
INSTRUMENT_ID = InstrumentId.from_str("SOLUSDT-PERP.BINANCE")
_TS0 = 1767225600000000000  # 2026-01-01T00:00:00Z
_STEP_NS = 900_000_000_000  # 15 minutes


class _FakePortfolio:
    def __init__(self) -> None:
        self.net_long = False

    def is_flat(self, _instrument_id) -> bool:
        return not self.net_long

    def is_net_long(self, _instrument_id) -> bool:
        return self.net_long

    def is_net_short(self, _instrument_id) -> bool:
        return False

    def equity(self, _venue):
        return None


class _FakeCache:
    def orders_open(self, **_kwargs):
        return []

    def orders_inflight(self, **_kwargs):
        return []


class _FakeClock:
    def utc_now(self) -> datetime:
        # Fixed UTC instant: the trading day never rolls inside a scenario,
        # so cooldown/daily-loss counters accumulate exactly as fed.
        return datetime(2026, 1, 2, tzinfo=timezone.utc)


class _Harness(VolCompressionBreakoutStrategy):
    """Shadow read-only framework properties and simulate fill lifecycle."""

    def __init__(self, config: VolCompressionBreakoutConfig) -> None:
        super().__init__(config)
        self.fake_portfolio = _FakePortfolio()
        self.fake_cache = _FakeCache()
        self.fake_clock = _FakeClock()
        self.entries: list[tuple[str, float]] = []
        self.exits: list[tuple[str, float]] = []
        self.next_close_pnl: float | None = None

    @property
    def portfolio(self):
        return self.fake_portfolio

    @property
    def cache(self):
        return self.fake_cache

    @property
    def clock(self):
        return self.fake_clock

    def _submit_entry(
        self,
        side,
        close: float,
        atr: float,
        stop_multiple: float | None = None,
        risk_scale: float = 1.0,
    ) -> None:
        # Exercise the real gating path (signal-only mode returns early).
        super()._submit_entry(side, close, atr, stop_multiple, risk_scale)
        self.entries.append((str(side), close))
        self.fake_portfolio.net_long = True
        event = type(
            "_OpenEvent",
            (),
            {
                "instrument_id": INSTRUMENT_ID,
                "side": PositionSide.LONG,
                "avg_px_open": close,
            },
        )()
        self.on_position_opened(event)

    def _submit_exit(self, reason: str, close: float) -> None:
        super()._submit_exit(reason, close)
        self.exits.append((reason, close))
        entry = self.entry_price or close
        pnl = self.next_close_pnl if self.next_close_pnl is not None else close - entry
        self.next_close_pnl = None
        self.fake_portfolio.net_long = False
        money = type("_Money", (), {"as_double": lambda self: pnl})()
        event = type(
            "_CloseEvent",
            (),
            {"instrument_id": INSTRUMENT_ID, "realized_pnl": money},
        )()
        self.on_position_closed(event)


def _make_harness(**config_overrides) -> _Harness:
    overrides: dict = {
        "instrument_id": INSTRUMENT_ID,
        "bar_type": BAR_TYPE,
        "allow_short": False,
        "enable_trading": False,
        "request_historical_bars": False,
    }
    overrides.update(config_overrides)
    return _Harness(VolCompressionBreakoutConfig(**overrides))


class _Feed:
    """Sequential synthetic bar feeder mimicking engine indicator updates."""

    def __init__(self, strategy: VolCompressionBreakoutStrategy) -> None:
        self.strategy = strategy
        self.index = 0

    def bar(self, o: float, h: float, l: float, c: float, v: float) -> Bar:
        ts = _TS0 + self.index * _STEP_NS
        return Bar(
            BAR_TYPE,
            Price(o, 2),
            Price(h, 2),
            Price(l, 2),
            Price(c, 2),
            Quantity(v, 1),
            ts,
            ts,
        )

    def feed(self, o: float, h: float, l: float, c: float, v: float) -> Bar:
        bar = self.bar(o, h, l, c, v)
        self.strategy.bb.handle_bar(bar)
        self.strategy.atr.handle_bar(bar)
        self.strategy.on_bar(bar)
        self.index += 1
        return bar


# -- deterministic market phases --------------------------------------------- #

WARMUP_BARS = 30
COIL_MODERATE = 60  # wider dispersion seeds high-bandwidth history
COIL_TIGHT = 150  # ultra-tight plateau builds the compressed distribution
BREAKOUT = dict(o=100.10, h=102.60, l=100.05, c=102.40, v=60.0)


def _feed_warmup(feed: _Feed) -> None:
    for k in range(WARMUP_BARS):
        base = 100.0 + 0.1 * k
        feed.feed(base, base + 0.35, base - 0.35, base + 0.1, 10.0)


def _feed_coil(feed: _Feed) -> None:
    """Moderate coil (dispersion seed) then tight plateau (squeeze state)."""
    i = 0
    for k in range(COIL_MODERATE):
        close = 103.0 + (0.30 if k % 2 else -0.30) + 0.01 * (k % 4)
        feed.feed(round(close - 0.01, 2), round(close + 0.04, 2), round(close - 0.06, 2),
                  round(close, 2), 10.0)
        i += 1
    del i
    for k in range(COIL_TIGHT):
        close = [99.99, 100.0, 100.01][k % 3]
        feed.feed(close, round(close + 0.01, 2), round(close - 0.01, 2), close, 10.0)


def _feed_squeeze_breakout(feed: _Feed) -> tuple[float, float]:
    """Fire one qualifying breakout; return (entry_price, stop_distance)."""
    before = len(feed.strategy.entries)
    feed.feed(**BREAKOUT)
    assert len(feed.strategy.entries) == before + 1
    assert feed.strategy.entry_price is not None
    assert feed.strategy.stop_distance is not None
    return feed.strategy.entry_price, feed.strategy.stop_distance


class TestCompressionMathHelpers:
    def test_bollinger_bandwidth_math_and_guard(self) -> None:
        assert bollinger_bandwidth_pct(110.0, 90.0, 100.0) == 20.0
        assert bollinger_bandwidth_pct(101.0, 99.0, 0.0) is None
        assert bollinger_bandwidth_pct(101.0, 99.0, -5.0) is None

    def test_range_rank_edges(self) -> None:
        window = [1.0, 2.0, 3.0, 4.0]
        assert bandwidth_range_rank(1.0, window) == 0.0
        assert bandwidth_range_rank(4.0, window) == 100.0
        assert bandwidth_range_rank(2.5, window) == 50.0

    def test_range_rank_tie_and_degenerate_windows(self) -> None:
        # Heavy ties at the minimum (coiled markets) stay well-defined.
        window = [0.0] * 150 + [5.0] * 42
        assert bandwidth_range_rank(0.0, window) == 0.0
        # Constant window: nothing expands, treat as fully compressed.
        assert bandwidth_range_rank(7.0, [3.0, 3.0, 3.0]) == 0.0
        # Empty history never signals compression.
        assert bandwidth_range_rank(1.0, []) == 100.0


class TestFrozenSpecContract:
    def test_parameter_grid_is_exactly_four_combinations(self) -> None:
        grid = VolCompressionBreakoutSettings.parameter_grid()
        expected = [
            (lookback, ratio)
            for lookback in SQUEEZE_LOOKBACK_GRID
            for ratio in VOLUME_RATIO_GRID
        ]
        assert SQUEEZE_LOOKBACK_GRID == (96, 192)
        assert VOLUME_RATIO_GRID == (1.5, 2.0)
        assert len(grid) == 4
        assert [(s.squeeze_lookback, s.volume_min_ratio) for s in grid] == expected

    def test_warmup_declared_above_floor_for_every_combo(self) -> None:
        assert DEFAULT_WARMUP_BARS >= 200
        for settings in VolCompressionBreakoutSettings.parameter_grid():
            settings.validate()
            assert settings.warmup_bars() >= 200

    def test_settings_validate_rejects_bad_params(self) -> None:
        cases = [
            dict(squeeze_lookback=48),  # < donchian_period 96
            dict(squeeze_pct_max=0.0),
            dict(squeeze_pct_max=101.0),
            dict(atr_stop_multiple=0.0),
            dict(take_profit_multiple=-1.0),
            dict(volume_min_ratio=0.0),
        ]
        for overrides in cases:
            try:
                VolCompressionBreakoutSettings(**overrides).validate()
            except ValueError:
                continue
            raise AssertionError(f"expected ValueError for {overrides}")

    def test_strategy_is_long_only_by_contract(self) -> None:
        # Rejection happens at strategy construction, not config construction.
        try:
            _make_harness(allow_short=True)
        except ValueError:
            pass
        else:
            raise AssertionError("allow_short=True must be rejected")

    def test_strategy_rejects_lookback_below_donchian(self) -> None:
        try:
            _make_harness(squeeze_lookback=48)
        except ValueError:
            pass
        else:
            raise AssertionError("squeeze_lookback < donchian_period must be rejected")


class TestVolCompressionBreakoutBehavior:
    def test_no_entry_when_compression_absent_despite_breakouts(self) -> None:
        strategy = _make_harness()
        feed = _Feed(strategy)
        _feed_warmup(feed)
        # Alternating expansion/flat cycles with an uptrend: closes repeatedly
        # break 96-bar highs and volume spikes accompany cycle peaks, but the
        # bandwidth state is never at the bottom of its window.
        base = 106.0
        for cycle in range(6):
            expanded = cycle % 2 == 0
            for j in range(48):
                if expanded:
                    close = base + 2.0 * __import__("math").sin(3.141592653589793 * j / 24)
                    volume = 60.0 if j == 12 else 10.0
                else:
                    close = base
                    volume = 10.0
                feed.feed(round(close, 2), round(close + 0.03, 2), round(close - 0.03, 2),
                          round(close, 2), volume)
            base += 3.0
        assert strategy.entries == []
        assert strategy.exits == []
        assert strategy.fake_portfolio.net_long is False

    def test_entry_fires_on_qualifying_squeeze_breakout(self) -> None:
        strategy = _make_harness()
        feed = _Feed(strategy)
        _feed_warmup(feed)
        _feed_coil(feed)
        entry_price, stop_distance = _feed_squeeze_breakout(feed)
        assert strategy.entries[-1][0] == str(OrderSide.BUY)
        assert strategy.entries[-1][1] == entry_price == 102.40
        assert strategy.fake_portfolio.net_long is True
        assert stop_distance > 0
        assert strategy.daily.trade_count == 1

    def test_stop_loss_exit_path_starts_cooldown(self) -> None:
        strategy = _make_harness()
        feed = _Feed(strategy)
        _feed_warmup(feed)
        _feed_coil(feed)
        entry_price, stop_distance = _feed_squeeze_breakout(feed)
        stop_close = round(entry_price - stop_distance * 1.2, 2)
        feed.feed(round(stop_close + 0.31, 2), round(stop_close + 0.33, 2),
                  round(stop_close - 0.02, 2), stop_close, 10.0)
        assert [reason for reason, _ in strategy.exits] == ["ATR stop"]
        assert strategy.fake_portfolio.net_long is False
        assert strategy.daily.trade_count == 1
        assert strategy.daily.cooldown_remaining == 4

    def test_take_profit_exit_path_at_two_r(self) -> None:
        strategy = _make_harness()
        feed = _Feed(strategy)
        _feed_warmup(feed)
        _feed_coil(feed)
        entry_price, stop_distance = _feed_squeeze_breakout(feed)
        target_close = round(entry_price + stop_distance * 2.5, 2)
        assert target_close >= entry_price + stop_distance * 2.0  # beyond 2R
        feed.feed(round(target_close - 0.05, 2), round(target_close + 0.05, 2),
                  round(entry_price + stop_distance, 2), target_close, 10.0)
        assert [reason for reason, _ in strategy.exits] == ["take-profit"]
        assert strategy.fake_portfolio.net_long is False
        assert strategy.daily.cooldown_remaining == 0  # winner: no cooldown

    def test_cooldown_blocks_immediate_reentry_then_allows(self) -> None:
        strategy = _make_harness()
        feed = _Feed(strategy)
        _feed_warmup(feed)
        _feed_coil(feed)
        entry_price, stop_distance = _feed_squeeze_breakout(feed)
        stop_close = round(entry_price - stop_distance * 1.2, 2)
        feed.feed(round(stop_close + 0.31, 2), round(stop_close + 0.33, 2),
                  round(stop_close - 0.02, 2), stop_close, 10.0)
        assert len(strategy.entries) == 1

        # Qualifying breakout one bar after the loss: must stay blocked while
        # the post-loss cooldown is active.
        assert strategy.daily.cooldown_remaining > 0
        feed.feed(103.40, 103.70, 103.35, 103.50, 60.0)
        assert len(strategy.entries) == 1

        # Flush the bandwidth window back to a squeeze state (constant closes
        # collapse band-width to the window minimum) far beyond cooldown length.
        for _ in range(mod.VolCompressionBreakoutSettings().squeeze_lookback + 20):
            feed.feed(103.20, 103.21, 103.19, 103.20, 10.0)
        assert strategy.daily.cooldown_remaining == 0
        feed.feed(103.80, 104.30, 103.70, 104.00, 60.0)
        assert len(strategy.entries) == 2
        assert strategy.entries[-1][1] == 104.00

    def test_daily_loss_limit_blocks_new_entries(self) -> None:
        strategy = _make_harness(max_daily_loss_usdt=Decimal("5"))
        feed = _Feed(strategy)
        _feed_warmup(feed)
        _feed_coil(feed)
        entry_price, stop_distance = _feed_squeeze_breakout(feed)
        stop_close = round(entry_price - stop_distance * 1.2, 2)
        strategy.next_close_pnl = -10.0  # breach max_daily_loss_usdt=5
        feed.feed(round(stop_close + 0.31, 2), round(stop_close + 0.33, 2),
                  round(stop_close - 0.02, 2), stop_close, 10.0)
        assert strategy.daily.realized_pnl <= -5.0
        assert len(strategy.entries) == 1

        # Wait out the cooldown entirely; the daily-loss cap must still block.
        for _ in range(VolCompressionBreakoutSettings().squeeze_lookback + 20):
            feed.feed(103.20, 103.21, 103.19, 103.20, 10.0)
        assert strategy.daily.cooldown_remaining == 0
        feed.feed(103.80, 104.30, 103.70, 104.00, 60.0)
        assert len(strategy.entries) == 1
