"""Backtest engine builder with fee + slippage modelling."""

from __future__ import annotations

from decimal import Decimal

from nautilus_trader.adapters.binance.common.types import BinanceBar
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from nautilus_trader.backtest.engine import BacktestResult
from nautilus_trader.backtest.models.fee import FeeModel
from nautilus_trader.backtest.models.fee import FixedFeeModel
from nautilus_trader.backtest.models.fee import MakerTakerFeeModel
from nautilus_trader.backtest.models.fill import BestPriceFillModel
from nautilus_trader.backtest.models.fill import FillModel
from nautilus_trader.backtest.models.fill import OneTickSlippageFillModel
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Currency
from nautilus_trader.model.objects import Money

from config.settings import BacktestSettings
from config.settings import MarketSettings
from config.settings import MeanReversionSettings
from config.settings import RiskSettings
from config.settings import StrategySettings
from data.catalog import Catalog
from risk.limits import RiskLimits
from strategy_factory import build_strategy


def build_fee_model(settings: BacktestSettings) -> FeeModel:
    if settings.fee_model == "maker_taker":
        # Uses the maker/taker fee rates embedded in the instrument definition
        # (Binance tier-0: maker 0.02%, taker 0.05%).
        return MakerTakerFeeModel()
    if settings.fee_model == "fixed":
        return FixedFeeModel(commission=Money.from_str(settings.fixed_fee))
    raise ValueError(f"Unknown fee_model: {settings.fee_model!r}")


def build_fill_model(settings: BacktestSettings):
    if settings.fill_model == "best_price":
        return BestPriceFillModel()
    if settings.fill_model == "one_tick_slippage":
        return OneTickSlippageFillModel()
    if settings.fill_model == "probabilistic":
        return FillModel(
            prob_fill_on_limit=settings.prob_fill_on_limit,
            prob_slippage=settings.prob_slippage,
            random_seed=settings.random_seed,
        )
    raise ValueError(f"Unknown fill_model: {settings.fill_model!r}")


def run_backtest(
    market: MarketSettings,
    risk: RiskSettings,
    strategy: StrategySettings,
    backtest: BacktestSettings,
    catalog: Catalog,
    *,
    strategy_type: str = "ema_atr",
    mean_reversion: MeanReversionSettings | None = None,
    trader_id: str = "BACKTESTER-001",
) -> tuple[BacktestEngine, BacktestResult]:
    """Run a single backtest and return the (still-open) engine and result."""
    instrument_id = InstrumentId.from_str(market.instrument_id)
    bar_type = BarType.from_str(market.bar_type)

    instrument = catalog.instrument(instrument_id)
    if instrument is None:
        raise ValueError(
            f"Instrument {instrument_id} not found in catalog at {catalog.path}. "
            "Run the download pipeline first.",
        )

    bars: list[BinanceBar] = catalog.bars(bar_type)
    if not bars:
        raise ValueError(f"No bars for {bar_type} in catalog at {catalog.path}")

    base_currency = Currency.from_str(market.base_currency)
    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id=trader_id,
            logging=LoggingConfig(log_level="INFO", print_config=False),
        ),
    )

    engine.add_venue(
        venue=Venue(market.venue),
        oms_type=OmsType.NETTING,  # one-way mode
        account_type=AccountType.MARGIN,
        base_currency=base_currency,
        starting_balances=[Money.from_str(backtest.starting_balance)],
        default_leverage=Decimal("1"),
        leverages={instrument_id: Decimal(market.leverage)},
        fee_model=build_fee_model(backtest),
        fill_model=build_fill_model(backtest),
    )

    engine.add_instrument(instrument)
    engine.add_data(bars)
    engine.add_strategy(
        build_strategy(
            market,
            risk,
            strategy,
            strategy_type=strategy_type,
            mean_reversion=mean_reversion,
            enable_trading=True,
            request_historical_bars=False,
        ),
    )

    engine.run(start=backtest.start, end=backtest.end)
    result = engine.get_result()

    # Re-export the strategy's realised risk profile for the report layer.
    limits = RiskLimits(
        risk_per_trade=risk.risk_per_trade,
        max_notional=risk.max_notional,
        max_daily_loss=risk.max_daily_loss,
        max_trades_per_day=risk.max_trades_per_day,
        cooldown_bars_after_loss=risk.cooldown_bars_after_loss,
        atr_stop_multiple=risk.atr_stop_multiple,
        leverage=market.leverage,
    )
    result.risk_limits = limits  # type: ignore[attr-defined]

    return engine, result
