"""Strategy factory: build a strategy instance from shared settings.

Keeps the strategy-selection logic in one place so the backtest engine and the
live node always instantiate strategies identically.
"""

from __future__ import annotations

from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId

from config.settings import MarketSettings
from config.settings import MeanReversionSettings
from config.settings import RiskSettings
from config.settings import StrategySettings
from strategy import EmaAtrStrategy
from strategy import EmaAtrStrategyConfig
from strategy_mean_reversion import MeanReversionStrategy
from strategy_mean_reversion import MeanReversionStrategyConfig

STRATEGY_TYPES = ("ema_atr", "mean_reversion")


def build_strategy(
    market: MarketSettings,
    risk: RiskSettings,
    strategy: StrategySettings,
    *,
    strategy_type: str,
    mean_reversion: MeanReversionSettings | None,
    enable_trading: bool,
    request_historical_bars: bool,
):
    """Build the requested strategy instance."""
    instrument_id = InstrumentId.from_str(market.instrument_id)
    bar_type = BarType.from_str(market.bar_type)

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
                risk_per_trade_usdt=risk.risk_per_trade,
                max_notional_usdt=risk.max_notional,
                max_daily_loss_usdt=risk.max_daily_loss,
                max_trades_per_day=risk.max_trades_per_day,
                cooldown_bars_after_loss=risk.cooldown_bars_after_loss,
                history_days=strategy.history_days,
                allow_short=risk.allow_short,
                enable_trading=enable_trading,
                request_historical_bars=request_historical_bars,
                close_position_on_stop=risk.close_position_on_stop,
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
                atr_period=mean_reversion.atr_period,
                atr_stop_multiple=risk.atr_stop_multiple,
                risk_per_trade_usdt=risk.risk_per_trade,
                max_notional_usdt=risk.max_notional,
                max_daily_loss_usdt=risk.max_daily_loss,
                max_trades_per_day=risk.max_trades_per_day,
                cooldown_bars_after_loss=risk.cooldown_bars_after_loss,
                history_days=mean_reversion.history_days,
                allow_short=risk.allow_short,
                enable_trading=enable_trading,
                request_historical_bars=request_historical_bars,
                close_position_on_stop=risk.close_position_on_stop,
            ),
        )

    raise ValueError(
        f"Unknown strategy_type {strategy_type!r}; expected one of {STRATEGY_TYPES}",
    )
