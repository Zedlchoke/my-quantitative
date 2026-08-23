"""Behavior/unit tests for H-FUNDCROWD-MR-v2 (funding_crowding).

Drives ``FundingCrowdingMRStrategy`` with a stubbed point-in-time
``FundingPIT`` so gate semantics are exact and deterministic:

* long allowed below the threshold, blocked strictly above it;
* short mirror math EXACT (blocked at percentile <= (100-threshold_p)/100);
* any PIT failure (None value / unavailable PIT / missing decision ts)
  blocks BOTH sides fail-closed and increments ``funding_gate_blocks``;
* no-lookahead: the stub records every queried timestamp and the maximum
  must equal the signal bar's CLOSE timestamp;
* frozen spec: exactly 3 grid combinations {70,75,80}, all other parameters
  identical to the reclaim-MR baseline defaults; config factory keeps
  ``allow_short=True`` in the shared-risk-kwarg path (unlike volcomp).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity

import strategy_funding_crowding_mr as mod
import strategy_reclaim_mr as reclaim_mod
from strategy_base import BaseFuturesStrategyConfig
from strategy_funding_crowding_mr import (
    DEFAULT_FUNDING_BUNDLE_DIR,
    DEFAULT_WARMUP_BARS,
    FUNDING_WINDOW_DAYS,
    THRESHOLD_P_GRID,
    FundingCrowdingMRConfig,
    FundingCrowdingMRSettings,
    FundingCrowdingMRStrategy,
)

BAR_TYPE = BarType.from_str("SOLUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL")
INSTRUMENT_ID = InstrumentId.from_str("SOLUSDT-PERP.BINANCE")
_TS0 = 1767225600000000000  # 2026-01-01T00:00:00Z
_STEP_NS = 900_000_000_000  # 15 minutes


class _StubFundingPIT:
    """Fake PIT: fixed percentile/reason, records every queried ts."""

    def __init__(self, percentile: float = 0.5, reason: str | None = None) -> None:
        self.percentile = percentile
        self.reason = reason
        self.queries_ts_ms: list[int] = []
        self.queries_window_days: list[float] = []

    def percentile_asof(self, ts, window_days=FUNDING_WINDOW_DAYS):
        self.queries_ts_ms.append(int(ts))
        self.queries_window_days.append(float(window_days))
        if self.reason is not None:
            return None, self.reason
        return self.percentile, None


class _RecordingFundingPIT(_StubFundingPIT):
    """Captures constructor args to prove default-resolution wiring."""

    constructed: list[tuple[str, str]] = []

    def __init__(self, symbol: str, bundle_dir: str) -> None:
        type(self).constructed.append((symbol, bundle_dir))
        super().__init__(percentile=0.5, reason=None)


class _StubRSI:
    def __init__(self, value: float) -> None:
        self.value = value
        self.initialized = True


class _StubADX:
    def __init__(self) -> None:
        self.value = 10.0
        self.initialized = True

    def update_bar(self, _bar) -> None:  # deterministic: never changes
        return None

    def reset(self) -> None:
        return None


class _FakePortfolio:
    def __init__(self) -> None:
        self.side = None

    def is_flat(self, _instrument_id) -> bool:
        return self.side is None

    def is_net_long(self, _instrument_id) -> bool:
        return self.side == OrderSide.BUY

    def is_net_short(self, _instrument_id) -> bool:
        return self.side == OrderSide.SELL

    def equity(self, _venue):
        return None


class _FakeCache:
    def orders_open(self, **_kwargs):
        return []

    def orders_inflight(self, **_kwargs):
        return []


class _FakeClock:
    def utc_now(self) -> datetime:
        return datetime(2026, 1, 2, tzinfo=__import__("datetime").timezone.utc)


class _GatedHarness(FundingCrowdingMRStrategy):
    """Shadow framework properties; force reclaim signals deterministically.

    The frozen reclaim predicates are overridden in THIS TEST HARNESS ONLY so
    that a forced entry reaches the real funding gate through the genuine
    ``on_bar -> _submit_entry`` path. Production logic stays untouched.
    """

    def __init__(self, config: FundingCrowdingMRConfig, pit) -> None:
        super().__init__(config, funding_pit=pit)
        self.fake_portfolio = _FakePortfolio()
        self.fake_cache = _FakeCache()
        self.fake_clock = _FakeClock()
        self.rsi = _StubRSI(value=50.0)  # replaced before feeding
        self.adx = _StubADX()
        self.force_signal: str | None = None  # "long" | "short" | None
        self.entries: list[tuple[str, float]] = []
        self.exits: list[tuple[str, float]] = []
        self._blocks_before_submit: int | None = None

    @property
    def portfolio(self):
        return self.fake_portfolio

    @property
    def cache(self):
        return self.fake_cache

    @property
    def clock(self):
        return self.fake_clock

    def indicators_initialized(self) -> bool:  # test shim: real ones fed by hand
        return True

    def _reclaimed_lower(self, _close: float) -> bool:
        return self.force_signal == "long"

    def _reclaimed_upper(self, _close: float) -> bool:
        return self.force_signal == "short"

    def _submit_entry(self, side, close, atr, stop_multiple=None, risk_scale=1.0):
        allowed = super()._submit_entry(side, close, atr, stop_multiple, risk_scale)
        if allowed:
            self.entries.append((str(side), close))
            self.fake_portfolio.side = side
            event = type(
                "_OpenEvent",
                (),
                {
                    "instrument_id": INSTRUMENT_ID,
                    "side": PositionSide.LONG if side == OrderSide.BUY else PositionSide.SHORT,
                    "avg_px_open": close,
                },
            )()
            self.on_position_opened(event)
        return allowed

    def _submit_exit(self, reason: str, close: float) -> None:
        super()._submit_exit(reason, close)
        self.exits.append((reason, close))
        self.fake_portfolio.side = None


def _make_harness(pit=None, *, percentile=0.5, reason=None, **config_overrides):
    overrides: dict = {
        "instrument_id": INSTRUMENT_ID,
        "bar_type": BAR_TYPE,
        "phase_gate": False,  # skip Wyckoff tracker in unit scenarios
        "enable_trading": False,
        "request_historical_bars": False,
    }
    overrides.update(config_overrides)
    pit = pit if pit is not None else _StubFundingPIT(percentile, reason)
    return _GatedHarness(FundingCrowdingMRConfig(**overrides), pit)


class _Feed:
    """Sequential synthetic bar feeder mimicking engine indicator updates."""

    def __init__(self, strategy: FundingCrowdingMRStrategy) -> None:
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
        self.strategy.vhf.handle_bar(bar)
        self.strategy.atr.handle_bar(bar)
        self.strategy.on_bar(bar)
        self.index += 1
        return bar


WARMUP_BARS = 60


def _feed_warmup(feed: _Feed) -> None:
    for k in range(WARMUP_BARS):
        base = [99.90, 100.00, 100.10][k % 3]
        feed.feed(base, round(base + 0.05, 2), round(base - 0.05, 2), base, 10.0)


# -- frozen spec contract ------------------------------------------------------ #


class TestFrozenSpecContract:
    def test_parameter_grid_is_exactly_three_threshold_combinations(self) -> None:
        assert THRESHOLD_P_GRID == (70, 75, 80)
        grid = FundingCrowdingMRSettings.parameter_grid()
        assert len(grid) == 3
        assert [s.threshold_p for s in grid] == [70, 75, 80]

    def test_grid_copies_reclaim_mr_baseline_defaults_exactly(self) -> None:
        for settings in FundingCrowdingMRSettings.parameter_grid():
            settings.validate()
            assert settings.funding_window_days == 30.0
            assert settings.bb_period == 20
            assert settings.bb_k == 2.0
            assert settings.rsi_period == 2
            assert settings.rsi_oversold == 15.0
            assert settings.rsi_overbought == 85.0
            assert settings.vhf_period == 28
            assert settings.vhf_max == 0.25
            assert settings.adx_period == 14
            assert settings.adx_max == 20.0
            assert settings.volume_sma_period == 20
            assert settings.volume_max_ratio == 1.8
            assert settings.atr_period == 14
            assert settings.atr_stop_multiple == 1.5
            assert settings.take_profit_multiple == 2.0
            assert settings.history_days == 220
            assert settings.phase_gate is True

    def test_settings_validate_and_declared_warmup(self) -> None:
        for settings in FundingCrowdingMRSettings.parameter_grid():
            settings.validate()
            assert settings.warmup_bars() >= 200
            assert settings.warmup_bars() == DEFAULT_WARMUP_BARS == 320

    def test_settings_validate_rejects_bad_thresholds(self) -> None:
        for bad in (0, -5, 69, 81, 100, 101):
            try:
                FundingCrowdingMRSettings(threshold_p=bad).validate()
            except ValueError:
                continue
            raise AssertionError(f"threshold_p={bad!r} must be rejected")

    def test_to_nautilus_config_roundtrip_and_allow_short_kwarg(self) -> None:
        settings = FundingCrowdingMRSettings(threshold_p=75)
        config = settings.to_nautilus_config(
            INSTRUMENT_ID,
            BAR_TYPE,
            request_historical_bars=False,
            allow_short=True,
            enable_trading=False,
            risk_per_trade_usdt=Decimal("5"),
            max_notional_usdt=Decimal("100"),
            max_daily_loss_usdt=Decimal("20"),
            max_trades_per_day=4,
            cooldown_bars_after_loss=4,
        )
        assert isinstance(config, BaseFuturesStrategyConfig)
        assert isinstance(config, FundingCrowdingMRConfig)
        assert config.allow_short is True  # kept in risk kwargs (vs volcomp)
        assert config.threshold_p == 75.0
        assert config.funding_window_days == FUNDING_WINDOW_DAYS == 30.0
        assert config.history_days == 220
        assert config.bb_period == 20
        assert config.atr_stop_multiple == 1.5
        assert config.take_profit_multiple == 2.0
        assert config.enable_trading is False
        assert config.request_historical_bars is False

    def test_strategy_rejects_out_of_range_threshold(self) -> None:
        for bad in (0.0, 100.0, -1.0):
            try:
                _make_harness(percentile=0.5, threshold_p=bad)
            except ValueError:
                continue
            raise AssertionError(f"threshold_p={bad!r} must be rejected at construction")


# -- gate semantics (exact math) ------------------------------------------------ #


def _arm_decision_ts(harness: _GatedHarness) -> int:
    """Process one bar via on_bar so last_decision_ts_ms is set organically."""
    feed = _Feed(harness)
    bar = feed.feed(100.0, 100.10, 99.90, 100.0, 10.0)
    return int(bar.ts_event) // 1_000_000


class TestFundingGateSemantics:
    def test_long_blocked_strictly_above_threshold_allowed_at_or_below(self) -> None:
        for threshold in THRESHOLD_P_GRID:
            level = threshold / 100
            # At exactly p/100: ALLOWED (block condition is strict >).
            harness = _make_harness(percentile=level, threshold_p=threshold)
            _arm_decision_ts(harness)
            assert harness._submit_entry(OrderSide.BUY, 100.0, 0.5) is True
            assert harness.funding_gate_blocks == 0
            # Just above p/100: BLOCKED.
            harness = _make_harness(
                percentile=level + 1e-09, threshold_p=threshold
            )
            _arm_decision_ts(harness)
            assert harness._submit_entry(OrderSide.BUY, 100.0, 0.5) is False
            assert harness.funding_gate_blocks == 1
            assert harness.entries == []

    def test_short_mirror_math_exact_inclusive_lower_tail(self) -> None:
        for threshold in THRESHOLD_P_GRID:
            bound = (100 - threshold) / 100
            # At exactly (100-p)/100: BLOCKED (condition is inclusive <=).
            harness = _make_harness(percentile=bound, threshold_p=threshold)
            _arm_decision_ts(harness)
            assert harness._submit_entry(OrderSide.SELL, 100.0, 0.5) is False
            assert harness.funding_gate_blocks == 1
            # Just above the lower-tail bound: ALLOWED.
            harness = _make_harness(percentile=bound + 1e-09, threshold_p=threshold)
            _arm_decision_ts(harness)
            assert harness._submit_entry(OrderSide.SELL, 100.0, 0.5) is True
            # Extreme tails behave per the mirror rule.
            harness = _make_harness(percentile=0.0, threshold_p=threshold)
            _arm_decision_ts(harness)
            assert harness._submit_entry(OrderSide.SELL, 100.0, 0.5) is False
            harness = _make_harness(percentile=1.0, threshold_p=threshold)
            _arm_decision_ts(harness)
            assert harness._submit_entry(OrderSide.SELL, 100.0, 0.5) is True

    def test_fail_closed_pit_failure_blocks_both_sides_and_counts(self) -> None:
        pit = _StubFundingPIT(reason="insufficient_history")
        harness = _make_harness(pit=pit)
        decision_ts_ms = _arm_decision_ts(harness)
        assert harness._submit_entry(OrderSide.BUY, 100.0, 0.5) is False
        assert harness.funding_gate_blocks == 1
        assert harness._submit_entry(OrderSide.SELL, 100.0, 0.5) is False
        assert harness.funding_gate_blocks == 2
        assert harness.entries == []
        assert pit.queries_ts_ms == [decision_ts_ms, decision_ts_ms]

    def test_missing_decision_timestamp_blocks_before_querying(self) -> None:
        pit = _StubFundingPIT(percentile=0.5)
        harness = _make_harness(pit=pit)
        assert harness.last_decision_ts_ms is None
        assert harness._submit_entry(OrderSide.BUY, 100.0, 0.5) is False
        assert harness.funding_gate_blocks == 1
        assert pit.queries_ts_ms == []  # failed closed BEFORE touching data

    def test_counter_accumulates_across_repeated_blocks(self) -> None:
        harness = _make_harness(percentile=0.95)  # crowded-long zone
        _arm_decision_ts(harness)
        for attempt in range(1, 4):
            assert harness._submit_entry(OrderSide.BUY, 100.0, 0.5) is False
            assert harness.funding_gate_blocks == attempt

    def test_window_days_forwarded_to_pit_query(self) -> None:
        pit = _StubFundingPIT(percentile=0.5)
        harness = _make_harness(pit=pit)
        _arm_decision_ts(harness)
        assert harness._submit_entry(OrderSide.BUY, 100.0, 0.5) is True
        assert pit.queries_window_days == [30.0]


class TestPITResolutionAndLookahead:
    def test_default_pit_resolution_uses_symbol_and_scan_bundle_dir(self, monkeypatch) -> None:
        monkeypatch.setattr(mod, "FundingPIT", _RecordingFundingPIT)
        _RecordingFundingPIT.constructed.clear()
        # Explicit pit=None constructor arg -> module must resolve its own PIT.
        config = FundingCrowdingMRConfig(
            instrument_id=INSTRUMENT_ID,
            bar_type=BAR_TYPE,
            phase_gate=False,
            enable_trading=False,
            request_historical_bars=False,
        )
        harness = _GatedHarness(config, None)
        _arm_decision_ts(harness)
        assert harness._submit_entry(OrderSide.BUY, 100.0, 0.5) is True
        assert _RecordingFundingPIT.constructed == [
            ("SOLUSDT", DEFAULT_FUNDING_BUNDLE_DIR)
        ]
        # Resolved once and cached afterwards.
        harness._resolve_funding_pit()
        assert len(_RecordingFundingPIT.constructed) == 1

    def test_no_lookahead_gate_sees_only_signal_bar_close_ts(self, monkeypatch) -> None:
        monkeypatch.setattr(reclaim_mod, "is_ranging", lambda **_kwargs: True)
        harness = _make_harness(percentile=0.5)
        harness.rsi = _StubRSI(value=10.0)  # oversold: long signal qualifies
        feed = _Feed(harness)
        fed_close_ts_ms: list[int] = []
        for _ in range(WARMUP_BARS):
            bar = feed.feed(100.0, 100.05, 99.95, 100.0, 10.0)
            fed_close_ts_ms.append(int(bar.ts_event) // 1_000_000)
        pit = harness._funding_pit
        assert pit.queries_ts_ms == []  # warmup must never touch funding data

        # Forced qualifying reclaim signal on the trigger bar.
        harness.force_signal = "long"
        trigger_bar = feed.feed(100.0, 100.05, 99.95, 100.0, 10.0)
        trigger_close_ts_ms = int(trigger_bar.ts_event) // 1_000_000

        assert len(harness.entries) == 1
        assert harness.entries[-1][0] == str(OrderSide.BUY)
        # Queried EXACTLY once, at the trigger bar's close timestamp — never
        # during warmup, never with any later (future) timestamp.
        assert pit.queries_ts_ms == [trigger_close_ts_ms]
        assert all(ts < trigger_close_ts_ms for ts in fed_close_ts_ms)
        assert harness.funding_gate_blocks == 0

    def test_short_end_to_end_through_real_on_bar_path(self, monkeypatch) -> None:
        monkeypatch.setattr(reclaim_mod, "is_ranging", lambda **_kwargs: True)
        harness = _make_harness(percentile=0.9)  # uncrowded-short zone
        harness.rsi = _StubRSI(value=95.0)  # overbought: short signal qualifies
        feed = _Feed(harness)
        for _ in range(WARMUP_BARS):
            feed.feed(100.0, 100.05, 99.95, 100.0, 10.0)
        harness.force_signal = "short"
        trigger_bar = feed.feed(100.0, 100.05, 99.95, 100.0, 10.0)
        assert len(harness.entries) == 1
        assert harness.entries[-1][0] == str(OrderSide.SELL)
        assert harness._funding_pit.queries_ts_ms == [
            int(trigger_bar.ts_event) // 1_000_000
        ]

    def test_crowded_long_blocked_through_real_on_bar_path(self, monkeypatch) -> None:
        monkeypatch.setattr(reclaim_mod, "is_ranging", lambda **_kwargs: True)
        harness = _make_harness(percentile=0.8, threshold_p=70)  # > 0.70 -> blocked
        harness.rsi = _StubRSI(value=10.0)
        feed = _Feed(harness)
        for _ in range(WARMUP_BARS):
            feed.feed(100.0, 100.05, 99.95, 100.0, 10.0)
        harness.force_signal = "long"
        feed.feed(100.0, 100.05, 99.95, 100.0, 10.0)
        assert harness.entries == []
        assert harness.exits == []
        assert harness.funding_gate_blocks == 1
