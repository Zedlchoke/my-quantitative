"""Volatility-compression breakout — H-VOLCOMP-BRKOUT-v1 (long-only).

Sprint-24h research strategy (owner A4). Thesis: sustained low Bollinger
band-width (a volatility squeeze) resolves via expansion legs; entries taken on
the Donchian-upper close breakout that ends the squeeze, confirmed by a volume
burst, capture the expansion while it is still under-traded.

Rules (pre-registered in research/hypotheses/H-VOLCOMP-BRKOUT-v1/candidate.yaml,
frozen before any scored run):

- Compression gate: range-normalized rank of the PREVIOUS closed bar's
  Bollinger bandwidth inside its trailing ``squeeze_lookback`` window must be
  <= ``squeeze_pct_max`` (0 = tightest edge of the window; tie-robust under
  coiled, degenerate windows). Evaluating the state one bar behind keeps the
  trigger bar's own range out of both the reference window and the tested
  condition (no lookahead).
- Trigger: close > highest high of the previous ``donchian_period`` bars.
- Confirm: current bar volume >= ``volume_min_ratio`` x SMA(volume, 20).
- Long-only; S0 seven-symbol universe; 15m bars; warmup >= 200 bars.
- Risk house style: fixed stop = 1.5x ATR (ATR frozen at fill), take-profit =
  2R (= 2 x stop distance), plus a time-style exit when price closes back below
  the Bollinger basis (middle band).

Trial budget: 4 parameter combinations MAX
(squeeze_lookback {96, 192} x volume_ratio {1.5, 2.0}) - declared and frozen.

All signals are computed on closed bars only; the module is deterministic.
Settings live in THIS module (config/settings.py is outside A4 ownership).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

from nautilus_trader.config import PositiveFloat
from nautilus_trader.config import PositiveInt
from nautilus_trader.indicators import AverageTrueRange
from nautilus_trader.indicators import BollingerBands
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.events import PositionOpened

from regime import VolumeSMA
from strategy_base import BaseFuturesStrategy
from strategy_base import BaseFuturesStrategyConfig

HYPOTHESIS_ID = "H-VOLCOMP-BRKOUT-v1"
STRATEGY_TYPE = "vol_compression_breakout"

# Frozen pre-registered trial grid (4 combinations MAX, PLAN.md §7).
SQUEEZE_LOOKBACK_GRID = (96, 192)
VOLUME_RATIO_GRID = (1.5, 2.0)

# Declared warmup for every grid combination (>= 200 bars, covers lookback 192).
DEFAULT_WARMUP_BARS = 320


def bollinger_bandwidth_pct(upper: float, lower: float, middle: float) -> float | None:
    """Normalized band width in percent of the basis; None when undefined."""
    if middle <= 0:
        return None
    return (upper - lower) / middle * 100.0


def bandwidth_range_rank(current: float, history: Iterable[float]) -> float:
    """Range-normalized rank (0..100) of ``current`` inside its trailing window.

    0 = current sits at the tightest edge of the window, 100 = at the widest.
    Chosen over an ordinal percentile because coiled markets produce heavy ties
    at the minimum; min-max ranking stays well-defined under ties and
    degenerate (constant) windows. Empty window -> 100 (never compressed).
    """
    values = list(history)
    if not values:
        return 100.0
    low = min(values)
    high = max(values)
    if high <= low:
        return 0.0
    return (current - low) / (high - low) * 100.0


@dataclass(frozen=True)
class VolCompressionBreakoutSettings:
    """Research-facing settings (module-local by design; config/settings.py untouched).

    Only ``squeeze_lookback`` and ``volume_min_ratio`` are trial knobs. Every
    other value is FIXED for H-VOLCOMP-BRKOUT-v1 and must not be tuned.
    """

    squeeze_lookback: int = 192  # GRID {96, 192}
    volume_min_ratio: float = 2.0  # GRID {1.5, 2.0}
    bb_period: int = 20  # fixed
    bb_k: float = 2.0  # fixed
    squeeze_pct_max: float = 25.0  # fixed compression threshold (percentile)
    donchian_period: int = 96  # fixed breakout reference window (24h of 15m)
    volume_sma_period: int = 20  # fixed
    atr_period: int = 14  # fixed
    atr_stop_multiple: float = 1.5  # fixed house stop
    take_profit_multiple: float = 2.0  # fixed 2R target
    history_days: int = 220

    def validate(self) -> None:
        if self.squeeze_lookback < self.donchian_period:
            raise ValueError("squeeze_lookback must be >= donchian_period")
        if not 0 < self.squeeze_pct_max <= 100:
            raise ValueError("squeeze_pct_max must be in (0, 100]")
        if self.bb_period <= 0 or self.volume_sma_period <= 0 or self.atr_period <= 0:
            raise ValueError("indicator periods must be > 0")
        if self.atr_stop_multiple <= 0 or self.take_profit_multiple <= 0:
            raise ValueError("stop/TP multiples must be > 0")
        if self.volume_min_ratio <= 0:
            raise ValueError("volume_min_ratio must be > 0")
        if self.warmup_bars() < 200:
            raise ValueError("warmup must be >= 200 bars")

    def warmup_bars(self) -> int:
        """Warmup covering the widest trailing window plus indicator ramp-up."""
        needed = max(self.squeeze_lookback, self.donchian_period) + max(
            self.bb_period, self.volume_sma_period, self.atr_period
        )
        return max(200, needed)

    @classmethod
    def parameter_grid(cls) -> list["VolCompressionBreakoutSettings"]:
        """The frozen 4-combination trial grid (order is deterministic)."""
        return [
            cls(squeeze_lookback=lookback, volume_min_ratio=ratio)
            for lookback in SQUEEZE_LOOKBACK_GRID
            for ratio in VOLUME_RATIO_GRID
        ]

    def to_nautilus_config(
        self,
        instrument_id,
        bar_type,
        *,
        enable_trading: bool = False,
        request_historical_bars: bool = True,
        **risk_kwargs,
    ) -> "VolCompressionBreakoutConfig":
        """Build the Nautilus strategy config from these frozen settings."""
        return VolCompressionBreakoutConfig(
            instrument_id=instrument_id,
            bar_type=bar_type,
            squeeze_lookback=self.squeeze_lookback,
            volume_min_ratio=self.volume_min_ratio,
            bb_period=self.bb_period,
            bb_k=self.bb_k,
            squeeze_pct_max=self.squeeze_pct_max,
            donchian_period=self.donchian_period,
            volume_sma_period=self.volume_sma_period,
            atr_stop_multiple=self.atr_stop_multiple,
            take_profit_multiple=self.take_profit_multiple,
            history_days=self.history_days,
            allow_short=False,
            enable_trading=enable_trading,
            request_historical_bars=request_historical_bars,
            **risk_kwargs,
        )


class VolCompressionBreakoutConfig(BaseFuturesStrategyConfig, frozen=True):
    """Nautilus config for the long-only compression-breakout hypothesis."""

    squeeze_lookback: PositiveInt = 192
    volume_min_ratio: PositiveFloat = 2.0
    bb_period: PositiveInt = 20
    bb_k: PositiveFloat = 2.0
    squeeze_pct_max: PositiveFloat = 25.0
    donchian_period: PositiveInt = 96
    volume_sma_period: PositiveInt = 20
    atr_stop_multiple: float = 1.5
    take_profit_multiple: PositiveFloat = 2.0


class VolCompressionBreakoutStrategy(BaseFuturesStrategy):
    """Long-only squeeze-resolution breakout with volume confirmation."""

    config: VolCompressionBreakoutConfig

    def __init__(self, config: VolCompressionBreakoutConfig) -> None:
        if config.allow_short:
            raise ValueError(
                "H-VOLCOMP-BRKOUT-v1 is long-only; construct with allow_short=False"
            )
        if config.squeeze_lookback < config.donchian_period:
            raise ValueError("squeeze_lookback must be >= donchian_period")
        if not 0 < config.squeeze_pct_max <= 100:
            raise ValueError("squeeze_pct_max must be in (0, 100]")
        if config.atr_stop_multiple <= 0 or config.take_profit_multiple <= 0:
            raise ValueError("stop/TP multiples must be positive")
        super().__init__(config)

        self.bb = BollingerBands(config.bb_period, config.bb_k)
        self.atr = AverageTrueRange(config.atr_period)
        self.volume_sma = VolumeSMA(config.volume_sma_period)
        # Trailing structures hold ONLY prior closed bars: they are appended
        # after signal evaluation so the current bar never sees itself.
        self.bandwidths: deque[float] = deque(maxlen=int(config.squeeze_lookback))
        self.prior_highs: deque[float] = deque(maxlen=int(config.donchian_period))
        self.entry_price: float | None = None
        self.stop_distance: float | None = None

    def indicators(self) -> list:
        return [self.bb, self.atr]

    # -- signal helpers ------------------------------------------------------- #

    def _inputs_ready(self) -> bool:
        return (
            self.bb.initialized
            and self.atr.initialized
            and self.volume_sma.initialized
        )

    def _compression_ok(self) -> bool:
        """Compression state of the previous closed bar vs its own past."""
        if len(self.bandwidths) < self.bandwidths.maxlen:
            return False
        history = list(self.bandwidths)
        previous_bandwidth = history[-1]
        earlier = history[:-1]
        rank = bandwidth_range_rank(previous_bandwidth, earlier)
        return rank <= self.config.squeeze_pct_max

    def _breakout_ok(self, close: float) -> bool:
        if len(self.prior_highs) < self.prior_highs.maxlen:
            return False
        return close > max(self.prior_highs)

    def _volume_ok(self, bar: Bar) -> bool:
        return (
            self.volume_sma.value > 0
            and bar.volume.as_double() >= self.volume_sma.value * self.config.volume_min_ratio
        )

    # -- main loop ------------------------------------------------------------ #

    def on_bar(self, bar: Bar) -> None:
        self._roll_trading_day()
        self.daily.tick_cooldown()
        self.volume_sma.update_bar(bar)
        if not self._inputs_ready():
            return

        close = bar.close.as_double()
        atr = self.atr.value

        if self.portfolio.is_net_long(self.config.instrument_id):
            self._manage_long(close)
        elif self.portfolio.is_net_short(self.config.instrument_id):
            # Long-only hypothesis: unwind any unexpected short immediately.
            self._submit_exit("unexpected short exposure", close)
        elif (
            self._can_open_position()
            and not self._has_active_order()
            and self._compression_ok()
            and self._breakout_ok(close)
            and self._volume_ok(bar)
        ):
            self._submit_entry(OrderSide.BUY, close, atr)

        # Bookkeeping AFTER decisions (point-in-time safe).
        self.prior_highs.append(bar.high.as_double())
        bandwidth = bollinger_bandwidth_pct(self.bb.upper, self.bb.lower, self.bb.middle)
        if bandwidth is not None:
            self.bandwidths.append(bandwidth)

    # -- position management --------------------------------------------------- #

    def _manage_long(self, close: float) -> None:
        if self._has_active_order():
            return
        entry = self.entry_price or close
        distance = self.stop_distance or self.atr.value * self.config.atr_stop_multiple
        target = entry + distance * self.config.take_profit_multiple
        if close <= entry - distance:
            self._submit_exit("ATR stop", close)
        elif close >= target:
            self._submit_exit("take-profit", close)
        elif self.bb.initialized and close < self.bb.middle:
            self._submit_exit("band-middle cross", close)

    def _on_position_opened(self, event: PositionOpened) -> None:
        self.entry_price = float(event.avg_px_open)
        self.stop_distance = self.atr.value * self.config.atr_stop_multiple

    def _on_position_closed(self, event: PositionClosed) -> None:
        self.entry_price = None
        self.stop_distance = None

    def _on_reset(self) -> None:
        # Registered indicators (bb, atr) are reset by BaseFuturesStrategy.on_reset.
        self.volume_sma.reset()
        self.bandwidths.clear()
        self.prior_highs.clear()
        self.entry_price = None
        self.stop_distance = None
