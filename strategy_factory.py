"""Strategy factory: build a strategy instance from shared settings.

Keeps the strategy-selection logic in one place so the backtest engine and the
live node always instantiate strategies identically.
"""

from __future__ import annotations

from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId

from config.settings import BreakoutSettings
from config.settings import MarketSettings
from config.settings import MeanReversionSettings
from config.settings import RegimeSwitchSettings
from config.settings import RiskSettings
from config.settings import StrategySettings
from strategy import EmaAtrStrategy
from strategy import EmaAtrStrategyConfig
from strategy_mean_reversion import MeanReversionStrategy
from strategy_mean_reversion import MeanReversionStrategyConfig
from strategy_breakout import BreakoutStrategy
from strategy_breakout import BreakoutStrategyConfig
from strategy_regime_switch import RegimeSwitchStrategy
from strategy_regime_switch import RegimeSwitchStrategyConfig


def _risk_kwargs(risk: RiskSettings, *, enable_trading: bool) -> dict:
    return dict(
        risk_per_trade_usdt=risk.risk_per_trade,
        max_notional_usdt=risk.max_notional,
        max_daily_loss_usdt=risk.max_daily_loss,
        max_trades_per_day=risk.max_trades_per_day,
        cooldown_bars_after_loss=risk.cooldown_bars_after_loss,
        risk_pct_per_trade=risk.risk_pct_per_trade,
        max_risk_per_trade_usdt=risk.max_risk_per_trade_usdt,
        max_daily_loss_pct=risk.max_daily_loss_pct,
        circuit_breaker_losses=risk.circuit_breaker_losses,
        circuit_breaker_pause_bars=risk.circuit_breaker_pause_bars,
        allow_short=risk.allow_short,
        enable_trading=enable_trading,
        close_position_on_stop=risk.close_position_on_stop,
    )


def build_strategy(
    market: MarketSettings,
    risk: RiskSettings,
    strategy: StrategySettings,
    *,
    strategy_type: str,
    mean_reversion: MeanReversionSettings | None,
    regime_switch: RegimeSwitchSettings | None,
    breakout: BreakoutSettings | None = None,
    enable_trading: bool,
    request_historical_bars: bool,
    symbol: str,
):
    """Build the requested strategy instance for one ``symbol``."""
    instrument_id = InstrumentId.from_str(market.instrument_id(symbol))
    bar_type = BarType.from_str(market.bar_type(symbol))
    risk_kwargs = _risk_kwargs(risk, enable_trading=enable_trading)

    if strategy_type == "ema_atr":
        return EmaAtrStrategy(
            config=EmaAtrStrategyConfig(
                instrument_id=instrument_id,
                bar_type=bar_type,
                fast_ema_period=strategy.fast_ema_period,
                slow_ema_period=strategy.slow_ema_period,
                trend_ema_period=strategy.trend_ema_period,
                atr_period=strategy.atr_period,
                atr_stop_multiple=risk.atr_stop_multiple,
                history_days=strategy.history_days,
                request_historical_bars=request_historical_bars,
                **risk_kwargs,
            ),
        )

    if strategy_type == "mean_reversion":
        if mean_reversion is None:
            raise ValueError("mean_reversion settings are required for strategy_type=mean_reversion")
        return MeanReversionStrategy(
            config=MeanReversionStrategyConfig(
                instrument_id=instrument_id,
                bar_type=bar_type,
                bb_period=mean_reversion.bb_period,
                bb_k=mean_reversion.bb_k,
                rsi_period=mean_reversion.rsi_period,
                rsi_oversold=mean_reversion.rsi_oversold,
                rsi_overbought=mean_reversion.rsi_overbought,
                vhf_period=mean_reversion.vhf_period,
                vhf_max=mean_reversion.vhf_max,
                adx_period=mean_reversion.adx_period,
                adx_max=mean_reversion.adx_max,
                volume_sma_period=mean_reversion.volume_sma_period,
                volume_max_ratio=mean_reversion.volume_max_ratio,
                atr_period=mean_reversion.atr_period,
                atr_stop_multiple=mean_reversion.atr_stop_multiple,
                take_profit_multiple=mean_reversion.take_profit_multiple,
                history_days=mean_reversion.history_days,
                htf_trend_filter=mean_reversion.htf_trend_filter,
                htf_ema_period=mean_reversion.htf_ema_period,
                htf_minutes=mean_reversion.htf_minutes,
                wyckoff_gate=mean_reversion.wyckoff_gate,
                wyckoff_directional_bias=mean_reversion.wyckoff_directional_bias,
                request_historical_bars=request_historical_bars,
                **risk_kwargs,
            ),
        )

    if strategy_type == "regime_switch":
        if regime_switch is None:
            raise ValueError("regime_switch settings are required for strategy_type=regime_switch")
        return RegimeSwitchStrategy(
            config=RegimeSwitchStrategyConfig(
                instrument_id=instrument_id,
                bar_type=bar_type,
                fast_ema_period=regime_switch.fast_ema_period,
                slow_ema_period=regime_switch.slow_ema_period,
                trend_ema_period=regime_switch.trend_ema_period,
                bb_period=regime_switch.bb_period,
                bb_k=regime_switch.bb_k,
                rsi_period=regime_switch.rsi_period,
                rsi_oversold=regime_switch.rsi_oversold,
                rsi_overbought=regime_switch.rsi_overbought,
                vhf_period=regime_switch.vhf_period,
                vhf_max=regime_switch.vhf_max,
                adx_period=regime_switch.adx_period,
                adx_max=regime_switch.adx_max,
                volume_sma_period=regime_switch.volume_sma_period,
                volume_max_ratio=regime_switch.volume_max_ratio,
                atr_period=regime_switch.atr_period,
                atr_stop_multiple=regime_switch.trend_stop_multiple,
                trend_stop_multiple=regime_switch.trend_stop_multiple,
                mean_reversion_stop_multiple=regime_switch.mean_reversion_stop_multiple,
                take_profit_multiple=regime_switch.take_profit_multiple,
                history_days=regime_switch.history_days,
                request_historical_bars=request_historical_bars,
                **risk_kwargs,
            ),
        )

    if strategy_type == "breakout":
        if breakout is None:
            raise ValueError("breakout settings are required for strategy_type=breakout")
        return BreakoutStrategy(
            config=BreakoutStrategyConfig(
                instrument_id=instrument_id,
                bar_type=bar_type,
                donchian_period=breakout.donchian_period,
                adx_period=breakout.adx_period,
                adx_min=breakout.adx_min,
                volume_sma_period=breakout.volume_sma_period,
                volume_min_ratio=breakout.volume_min_ratio,
                atr_period=breakout.atr_period,
                atr_stop_multiple=breakout.atr_stop_multiple,
                take_profit_multiple=breakout.take_profit_multiple,
                wyckoff_markup_only=breakout.wyckoff_markup_only,
                history_days=breakout.history_days,
                request_historical_bars=request_historical_bars,
                **risk_kwargs,
            ),
        )

    raise ValueError(
        f"Unknown strategy_type {strategy_type!r}; "
        "expected one of (ema_atr, mean_reversion, regime_switch, breakout)",
    )
