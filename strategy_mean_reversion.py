"""Mean-reversion strategy for ranging crypto markets.

Trades the assumption that price tends to revert to its mean when the market is
not trending. Entries are taken only in a **range regime**: VHF low, ADX low,
and volume not elevated vs its SMA (VHF alone was not enough — NOTES.md §4.3).

Entries (Bollinger + RSI):
  - LONG  when close touches the lower band and RSI is oversold, in a range.
  - SHORT when close touches the upper band and RSI is overbought, in a range.

Exits:
  - ATR stop frozen at entry (``atr_stop_multiple`` × ATR_entry), or
  - take-profit at ``take_profit_multiple`` × that stop distance.
"""

from __future__ import annotations

from nautilus_trader.common.enums import LogColor
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
from regime import HtfTrendTracker
from regime import VolumeSMA
from regime import is_ranging
from regime_wyckoff import WyckoffDailyTracker
from regime_wyckoff import WyckoffPhase
from data.tradfi import TradfiSessionGate
from regime_wyckoff import wyckoff_allows_entries
from regime_wyckoff import wyckoff_allows_long
from regime_wyckoff import wyckoff_allows_short
from regime_wyckoff import wyckoff_risk_scale
from strategy_base import BaseFuturesStrategy
from strategy_base import BaseFuturesStrategyConfig


class MeanReversionStrategyConfig(BaseFuturesStrategyConfig, frozen=True):
    bb_period: PositiveInt = 20
    bb_k: PositiveFloat = 2.0
    rsi_period: PositiveInt = 2
    rsi_oversold: float = 10.0
    rsi_overbought: float = 90.0
    vhf_period: PositiveInt = 28
    vhf_max: float = 0.35  # <= this => ranging (with ADX + volume)
    adx_period: PositiveInt = 14
    adx_max: float = 25.0  # <= this => weak trend (range)
    volume_sma_period: PositiveInt = 20
    volume_max_ratio: float = 1.5  # skip if volume > ratio × SMA (breakout)
    take_profit_multiple: float = 1.5  # reward:risk target
    htf_trend_filter: bool = False
    htf_ema_period: PositiveInt = 200
    htf_minutes: PositiveInt = 60
    wyckoff_gate: bool = False
    wyckoff_directional_bias: bool = False
    tradfi_session_filter: bool = False


class MeanReversionStrategy(BaseFuturesStrategy):
    """Bollinger + RSI mean-reversion with a VHF ranging-regime filter."""

    def __init__(self, config: MeanReversionStrategyConfig) -> None:
        if not 0 <= config.rsi_oversold < config.rsi_overbought <= 100:
            raise ValueError("RSI levels must satisfy 0 <= oversold < overbought <= 100")
        if config.atr_stop_multiple <= 0:
            raise ValueError("atr_stop_multiple must be positive")
        if config.take_profit_multiple <= 0:
            raise ValueError("take_profit_multiple must be positive")

        super().__init__(config)

        self.bb = BollingerBands(config.bb_period, config.bb_k)
        self.rsi = RelativeStrengthIndex(config.rsi_period)
        self.vhf = VerticalHorizontalFilter(config.vhf_period)
        self.atr = AverageTrueRange(config.atr_period)
        self.adx = AverageDirectionalIndex(config.adx_period)
        self.volume_sma = VolumeSMA(config.volume_sma_period)
        self.htf = (
            HtfTrendTracker(
                base_minutes=15,
                htf_minutes=config.htf_minutes,
                ema_period=config.htf_ema_period,
            )
            if config.htf_trend_filter
            else None
        )
        self.wyckoff = WyckoffDailyTracker() if config.wyckoff_gate else None
        self._wyckoff_phase = WyckoffPhase.TRANSITION
        self.tradfi_session_gate: TradfiSessionGate | None = None

        self.entry_price: float | None = None
        self.stop_distance: float | None = None

    def indicators(self) -> list:
        return [self.bb, self.rsi, self.vhf, self.atr]

    def set_tradfi_session_gate(self, gate: TradfiSessionGate | None) -> None:
        self.tradfi_session_gate = gate

    def on_bar(self, bar: Bar) -> None:
        self._roll_trading_day()
        self.daily.tick_cooldown()
        self.adx.update_bar(bar)
        self.volume_sma.update_bar(bar)
        if self.htf is not None:
            self.htf.update(bar.close.as_double())
        if self.wyckoff is not None:
            prev = self._wyckoff_phase
            self._wyckoff_phase = self.wyckoff.update_bar(bar)
            if self.wyckoff.initialized and prev != self._wyckoff_phase:
                self.log.info(
                    f"Wyckoff phase → {self._wyckoff_phase.value}",
                    color=LogColor.CYAN,
                )

        if not self.indicators_initialized() or not self.adx.initialized:
            return

        close = bar.close.as_double()
        atr = self.atr.value
        stop_distance = self.stop_distance or (atr * self.config.atr_stop_multiple)
        in_range = is_ranging(
            vhf=self.vhf.value,
            vhf_max=self.config.vhf_max,
            adx=self.adx.value,
            adx_max=self.config.adx_max,
            volume=bar.volume.as_double(),
            volume_sma=self.volume_sma.value,
            volume_max_ratio=self.config.volume_max_ratio,
        )

        if self.portfolio.is_net_long(self.config.instrument_id):
            stop = (self.entry_price or close) - stop_distance
            target = (self.entry_price or close) + (
                stop_distance * self.config.take_profit_multiple
            )
            if close >= target and not self._has_active_order():
                self._submit_exit("take-profit", close)
            elif close <= stop and not self._has_active_order():
                self._submit_exit("ATR stop", close)

        elif self.portfolio.is_net_short(self.config.instrument_id):
            stop = (self.entry_price or close) + stop_distance
            target = (self.entry_price or close) - (
                stop_distance * self.config.take_profit_multiple
            )
            if close <= target and not self._has_active_order():
                self._submit_exit("take-profit", close)
            elif close >= stop and not self._has_active_order():
                self._submit_exit("ATR stop", close)

        elif self._can_open_position() and not self._has_active_order() and in_range:
            if self.config.tradfi_session_filter:
                if self.tradfi_session_gate is None or not self.tradfi_session_gate.allows(bar.ts_event):
                    return
            risk_scale = 1.0
            allow_long = True
            allow_short = True
            if self.wyckoff is not None and self.wyckoff.initialized:
                if not wyckoff_allows_entries(self._wyckoff_phase):
                    return
                risk_scale = wyckoff_risk_scale(self._wyckoff_phase)
                if risk_scale <= 0:
                    return
                if self.config.wyckoff_directional_bias:
                    allow_long = wyckoff_allows_long(self._wyckoff_phase)
                    allow_short = wyckoff_allows_short(self._wyckoff_phase)

            if (
                allow_long
                and close <= self.bb.lower
                and self.rsi.value <= self.config.rsi_oversold
            ):
                if self.htf is None or self.htf.allows_long():
                    self._submit_entry(OrderSide.BUY, close, atr, risk_scale=risk_scale)
            elif (
                allow_short
                and self.config.allow_short
                and close >= self.bb.upper
                and self.rsi.value >= self.config.rsi_overbought
            ):
                if self.htf is None or self.htf.allows_short():
                    self._submit_entry(OrderSide.SELL, close, atr, risk_scale=risk_scale)

    def _on_position_opened(self, event: PositionOpened) -> None:
        self.entry_price = float(event.avg_px_open)
        self.stop_distance = self.atr.value * self.config.atr_stop_multiple

    def _on_position_closed(self, event: PositionClosed) -> None:
        self.entry_price = None
        self.stop_distance = None

    def _on_reset(self) -> None:
        self.entry_price = None
        self.stop_distance = None
        self.adx.reset()
        self.volume_sma.reset()
        if self.htf is not None:
            self.htf.reset()
        if self.wyckoff is not None:
            self.wyckoff.reset()
            self._wyckoff_phase = WyckoffPhase.TRANSITION
