"""Reclaim mean-reversion baseline for accumulation/transition ranges."""

from __future__ import annotations

from nautilus_trader.config import PositiveFloat
from nautilus_trader.config import PositiveInt
from nautilus_trader.indicators import AverageTrueRange
from nautilus_trader.indicators import BollingerBands
from nautilus_trader.indicators import RelativeStrengthIndex
from nautilus_trader.indicators import VerticalHorizontalFilter
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.events import PositionOpened

from regime import AverageDirectionalIndex
from regime import VolumeSMA
from regime import is_ranging
from regime_wyckoff import WyckoffDailyTracker
from regime_wyckoff import WyckoffPhase
from strategy_base import BaseFuturesStrategy
from strategy_base import BaseFuturesStrategyConfig


class ReclaimMeanReversionStrategyConfig(BaseFuturesStrategyConfig, frozen=True):
    bb_period: PositiveInt = 20
    bb_k: PositiveFloat = 2.0
    rsi_period: PositiveInt = 2
    rsi_oversold: float = 15.0
    rsi_overbought: float = 85.0
    vhf_period: PositiveInt = 28
    vhf_max: float = 0.25
    adx_period: PositiveInt = 14
    adx_max: float = 20.0
    volume_sma_period: PositiveInt = 20
    volume_max_ratio: float = 1.8
    take_profit_multiple: float = 2.0
    phase_gate: bool = True


class ReclaimMeanReversionStrategy(BaseFuturesStrategy):
    """Enter only after a band excursion is reclaimed in a weak-trend regime."""

    def __init__(self, config: ReclaimMeanReversionStrategyConfig) -> None:
        if not 0 <= config.rsi_oversold < config.rsi_overbought <= 100:
            raise ValueError("RSI levels must satisfy 0 <= oversold < overbought <= 100")
        if config.vhf_max <= 0 or config.adx_max <= 0 or config.volume_max_ratio <= 0:
            raise ValueError("range thresholds must be positive")
        if config.atr_stop_multiple <= 0 or config.take_profit_multiple <= 0:
            raise ValueError("stop and take-profit multiples must be positive")
        super().__init__(config)

        self.bb = BollingerBands(config.bb_period, config.bb_k)
        self.rsi = RelativeStrengthIndex(config.rsi_period)
        self.vhf = VerticalHorizontalFilter(config.vhf_period)
        self.atr = AverageTrueRange(config.atr_period)
        self.adx = AverageDirectionalIndex(config.adx_period)
        self.volume_sma = VolumeSMA(config.volume_sma_period)
        self.wyckoff = WyckoffDailyTracker() if config.phase_gate else None
        self.phase = WyckoffPhase.TRANSITION
        self.previous_close: float | None = None
        self.previous_lower: float | None = None
        self.previous_upper: float | None = None
        self.entry_price: float | None = None
        self.stop_distance: float | None = None

    def indicators(self) -> list:
        return [self.bb, self.rsi, self.vhf, self.atr]

    def on_bar(self, bar: Bar) -> None:
        self._roll_trading_day()
        self.daily.tick_cooldown()
        self.adx.update_bar(bar)
        self.volume_sma.update_bar(bar)
        if self.wyckoff is not None:
            self.phase = self.wyckoff.update_bar(bar)

        if not self.indicators_initialized() or not self.adx.initialized:
            return

        close = bar.close.as_double()
        atr = self.atr.value
        if self.portfolio.is_net_long(self.config.instrument_id):
            self._manage_long(close, atr)
        elif self.portfolio.is_net_short(self.config.instrument_id):
            self._manage_short(close, atr)
        elif self._can_open_position() and not self._has_active_order():
            in_range = is_ranging(
                vhf=self.vhf.value,
                vhf_max=self.config.vhf_max,
                adx=self.adx.value,
                adx_max=self.config.adx_max,
                volume=bar.volume.as_double(),
                volume_sma=self.volume_sma.value,
                volume_max_ratio=self.config.volume_max_ratio,
            )
            if in_range and self._phase_allows_long() and self._reclaimed_lower(close):
                if self.rsi.value <= self.config.rsi_oversold:
                    self._submit_entry(OrderSide.BUY, close, atr)
            elif in_range and self._phase_allows_short() and self._reclaimed_upper(close):
                if self.config.allow_short and self.rsi.value >= self.config.rsi_overbought:
                    self._submit_entry(OrderSide.SELL, close, atr)

        self.previous_close = close
        self.previous_lower = self.bb.lower
        self.previous_upper = self.bb.upper

    def _reclaimed_lower(self, close: float) -> bool:
        return (
            self.previous_close is not None
            and self.previous_lower is not None
            and self.previous_close <= self.previous_lower
            and close > self.bb.lower
        )

    def _reclaimed_upper(self, close: float) -> bool:
        return (
            self.previous_close is not None
            and self.previous_upper is not None
            and self.previous_close >= self.previous_upper
            and close < self.bb.upper
        )

    def _phase_allows_long(self) -> bool:
        return self.wyckoff is None or not self.wyckoff.initialized or self.phase in {
            WyckoffPhase.ACCUMULATION,
            WyckoffPhase.TRANSITION,
        }

    def _phase_allows_short(self) -> bool:
        return self.wyckoff is None or not self.wyckoff.initialized or self.phase in {
            WyckoffPhase.DISTRIBUTION,
            WyckoffPhase.TRANSITION,
        }

    def _manage_long(self, close: float, atr: float) -> None:
        if self._has_active_order():
            return
        distance = self.stop_distance or atr * self.config.atr_stop_multiple
        entry = self.entry_price or close
        if close <= entry - distance:
            self._submit_exit("ATR stop", close)
        elif close >= entry + distance * self.config.take_profit_multiple:
            self._submit_exit("take-profit", close)

    def _manage_short(self, close: float, atr: float) -> None:
        if self._has_active_order():
            return
        distance = self.stop_distance or atr * self.config.atr_stop_multiple
        entry = self.entry_price or close
        if close >= entry + distance:
            self._submit_exit("ATR stop", close)
        elif close <= entry - distance * self.config.take_profit_multiple:
            self._submit_exit("take-profit", close)

    def _on_position_opened(self, event: PositionOpened) -> None:
        self.entry_price = float(event.avg_px_open)
        self.stop_distance = self.atr.value * self.config.atr_stop_multiple

    def _on_position_closed(self, event: PositionClosed) -> None:
        self.entry_price = None
        self.stop_distance = None

    def _on_reset(self) -> None:
        self.adx.reset()
        self.volume_sma.reset()
        if self.wyckoff is not None:
            self.wyckoff.reset()
        self.phase = WyckoffPhase.TRANSITION
        self.previous_close = None
        self.previous_lower = None
        self.previous_upper = None
        self.entry_price = None
        self.stop_distance = None
