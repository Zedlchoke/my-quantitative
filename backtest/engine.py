"""Backtest engine builder with fee + slippage modelling and multi-symbol runs."""

from __future__ import annotations

from dataclasses import dataclass
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
from config.settings import BreakoutSettings
from config.settings import MarkdownBreakdownSettings
from config.settings import MarketSettings
from config.settings import MeanReversionSettings
from config.settings import PortfolioRiskSettings
from config.settings import ReclaimMeanReversionSettings
from config.settings import RegimeSwitchSettings
from config.settings import RiskSettings
from config.settings import StrategySettings
from config.settings import TrendPullbackSettings
from data.catalog import Catalog
from risk.limits import RiskLimits
from risk.portfolio import PortfolioRiskLimits
from risk.portfolio import PortfolioRiskManager
from strategy_factory import build_strategy


@dataclass
class SymbolBacktest:
    """Result of backtesting one symbol."""

    symbol: str
    engine: BacktestEngine
    result: BacktestResult


@dataclass
class PortfolioBacktest:
    """One shared-capital run containing all configured symbols."""

    symbols: tuple[str, ...]
    engine: BacktestEngine
    result: BacktestResult


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


def _logging_config(log_level: str) -> LoggingConfig:
    """Build a logger config which is safe for repeated Nautilus 1.230 runs.

    In 1.230, ``log_level='OFF'`` still initializes the process-global Rust
    logger.  A second BacktestEngine in the same research process then panics.
    ``bypass_logging`` is the supported way to prevent that initialization.
    """
    disabled = log_level.upper() == "OFF"
    return LoggingConfig(
        log_level=log_level,
        bypass_logging=disabled,
        print_config=False,
    )


def _attach_risk_limits(result: BacktestResult, risk: RiskSettings, leverage: int) -> None:
    result.risk_limits = RiskLimits(  # type: ignore[attr-defined]
        risk_per_trade=risk.risk_per_trade,
        max_notional=risk.max_notional,
        max_daily_loss=risk.max_daily_loss,
        max_trades_per_day=risk.max_trades_per_day,
        cooldown_bars_after_loss=risk.cooldown_bars_after_loss,
        atr_stop_multiple=risk.atr_stop_multiple,
        leverage=leverage,
        risk_pct_per_trade=risk.risk_pct_per_trade,
        max_risk_per_trade_usdt=risk.max_risk_per_trade_usdt,
        max_daily_loss_pct=risk.max_daily_loss_pct,
        circuit_breaker_losses=risk.circuit_breaker_losses,
        circuit_breaker_pause_bars=risk.circuit_breaker_pause_bars,
    )


def run_backtest_for_symbol(
    market: MarketSettings,
    risk: RiskSettings,
    strategy: StrategySettings,
    backtest: BacktestSettings,
    catalog: Catalog,
    *,
    symbol: str,
    strategy_type: str,
    mean_reversion: MeanReversionSettings | None,
    regime_switch: RegimeSwitchSettings | None,
    breakout: BreakoutSettings | None = None,
    reclaim_mr: ReclaimMeanReversionSettings | None = None,
    trend_pullback: TrendPullbackSettings | None = None,
    markdown_breakdown: MarkdownBreakdownSettings | None = None,
    vol_compression=None,
    trader_id: str = "BACKTESTER-001",
    log_level: str = "INFO",
    instrument=None,
    bars: list[BinanceBar] | None = None,
) -> SymbolBacktest:
    """Run a single-symbol backtest and return the (still-open) engine + result.

    ``instrument`` / ``bars`` may be supplied to reuse pre-loaded data across many
    runs (e.g. in a grid search), skipping the catalog read + volume normalisation.
    """
    instrument_id = InstrumentId.from_str(market.instrument_id(symbol))
    bar_type = BarType.from_str(market.bar_type(symbol))

    if instrument is None:
        instrument = catalog.instrument(instrument_id)
        if instrument is None:
            raise ValueError(
                f"Instrument {instrument_id} not found in catalog at {catalog.path}. "
                "Run the download pipeline first.",
            )

    if bars is None:
        bars = catalog.bars(bar_type)
        if not bars:
            raise ValueError(f"No bars for {bar_type} in catalog at {catalog.path}")

    base_currency = Currency.from_str(market.base_currency)
    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id=f"{trader_id}-{symbol}",
            logging=_logging_config(log_level),
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
            regime_switch=regime_switch,
            breakout=breakout,
            reclaim_mr=reclaim_mr,
            trend_pullback=trend_pullback,
            markdown_breakdown=markdown_breakdown,
            vol_compression=vol_compression,
            enable_trading=True,
            request_historical_bars=False,
            symbol=symbol,
        ),
    )

    engine.run(start=backtest.start, end=backtest.end)
    result = engine.get_result()
    _attach_risk_limits(result, risk, market.leverage)

    return SymbolBacktest(symbol=symbol, engine=engine, result=result)


def run_backtest(
    market: MarketSettings,
    risk: RiskSettings,
    strategy: StrategySettings,
    backtest: BacktestSettings,
    catalog: Catalog,
    *,
    strategy_type: str = "ema_atr",
    mean_reversion: MeanReversionSettings | None = None,
    regime_switch: RegimeSwitchSettings | None = None,
    breakout: BreakoutSettings | None = None,
    reclaim_mr: ReclaimMeanReversionSettings | None = None,
    trend_pullback: TrendPullbackSettings | None = None,
    markdown_breakdown: MarkdownBreakdownSettings | None = None,
    trader_id: str = "BACKTESTER-001",
    log_level: str = "INFO",
) -> list[SymbolBacktest]:
    """Run a backtest for every symbol in ``market.symbols``."""
    runs: list[SymbolBacktest] = []
    for symbol in market.symbols:
        runs.append(
            run_backtest_for_symbol(
                market,
                risk,
                strategy,
                backtest,
                catalog,
                symbol=symbol,
                strategy_type=strategy_type,
                mean_reversion=mean_reversion,
                regime_switch=regime_switch,
                breakout=breakout,
                reclaim_mr=reclaim_mr,
                trend_pullback=trend_pullback,
                markdown_breakdown=markdown_breakdown,
                trader_id=trader_id,
                log_level=log_level,
            ),
        )
    return runs


def run_portfolio_backtest(
    market: MarketSettings,
    risk: RiskSettings,
    strategy: StrategySettings,
    backtest: BacktestSettings,
    catalog: Catalog,
    *,
    strategy_type: str = "ema_atr",
    mean_reversion: MeanReversionSettings | None = None,
    regime_switch: RegimeSwitchSettings | None = None,
    breakout: BreakoutSettings | None = None,
    reclaim_mr: ReclaimMeanReversionSettings | None = None,
    trend_pullback: TrendPullbackSettings | None = None,
    markdown_breakdown: MarkdownBreakdownSettings | None = None,
    trader_id: str = "PORTFOLIO-BACKTESTER-001",
    log_level: str = "INFO",
    portfolio_risk: PortfolioRiskSettings | None = None,
) -> PortfolioBacktest:
    """Backtest all symbols concurrently against one balance and venue account."""
    base_currency = Currency.from_str(market.base_currency)
    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id=trader_id,
            logging=_logging_config(log_level),
        ),
    )

    instrument_ids = {
        symbol: InstrumentId.from_str(market.instrument_id(symbol))
        for symbol in market.symbols
    }
    engine.add_venue(
        venue=Venue(market.venue),
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=base_currency,
        starting_balances=[Money.from_str(backtest.starting_balance)],
        default_leverage=Decimal("1"),
        leverages={iid: Decimal(market.leverage) for iid in instrument_ids.values()},
        fee_model=build_fee_model(backtest),
        fill_model=build_fill_model(backtest),
    )

    manager = None
    if portfolio_risk is not None and portfolio_risk.enabled:
        manager = PortfolioRiskManager(
            PortfolioRiskLimits(
                max_gross_notional=portfolio_risk.max_gross_notional,
                max_portfolio_risk_pct=portfolio_risk.max_portfolio_risk_pct,
                max_concurrent_positions=portfolio_risk.max_concurrent_positions,
                max_positions_per_cluster=portfolio_risk.max_positions_per_cluster,
                max_daily_loss_pct=portfolio_risk.max_daily_loss_pct,
                circuit_breaker_losses=portfolio_risk.circuit_breaker_losses,
            ),
            clusters=portfolio_risk.clusters,
            asset_classes=portfolio_risk.asset_classes,
        )

    all_bars: list[BinanceBar] = []
    for symbol, instrument_id in instrument_ids.items():
        instrument = catalog.instrument(instrument_id)
        if instrument is None:
            raise ValueError(
                f"Instrument {instrument_id} not found in catalog at {catalog.path}. "
                "Run the production public-data download first.",
            )
        bar_type = BarType.from_str(market.bar_type(symbol))
        bars = catalog.bars(bar_type)
        if not bars:
            raise ValueError(f"No bars for {bar_type} in catalog at {catalog.path}")
        engine.add_instrument(instrument)
        all_bars.extend(bars)
        built_strategy = build_strategy(
            market,
            risk,
            strategy,
            strategy_type=strategy_type,
            mean_reversion=mean_reversion,
            regime_switch=regime_switch,
            breakout=breakout,
            reclaim_mr=reclaim_mr,
            trend_pullback=trend_pullback,
            markdown_breakdown=markdown_breakdown,
            enable_trading=True,
            request_historical_bars=False,
            symbol=symbol,
        )
        built_strategy.set_portfolio_risk_manager(manager)
        engine.add_strategy(built_strategy)

    # One globally ordered stream is required for simultaneous positions and
    # shared cash/margin to be represented correctly.
    all_bars.sort(key=lambda bar: (bar.ts_event, str(bar.bar_type)))
    engine.add_data(all_bars)
    engine.run(start=backtest.start, end=backtest.end)
    result = engine.get_result()
    _attach_risk_limits(result, risk, market.leverage)
    result.portfolio_symbols = tuple(market.symbols)  # type: ignore[attr-defined]
    return PortfolioBacktest(tuple(market.symbols), engine, result)
