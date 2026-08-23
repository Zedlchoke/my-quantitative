"""Command-line entry points for the crypto-futures trading system.

Subcommands
-----------
download   Download historical bars into the local Parquet catalog.
backtest   Run backtests with fee + slippage modelling and write reports.
live       Run the live Binance USD-M perpetual node (Testnet/Demo only).
status     Print a compact markdown status of latest result artifacts.

Examples
--------
    python main.py download
    python main.py backtest
    python main.py backtest --config config/research_mean_reversion.yaml
    python main.py live
    python main.py status
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import os
import sys

from dotenv import load_dotenv

from nautilus_trader.adapters.binance.common.constants import BINANCE
from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
from nautilus_trader.adapters.binance.common.enums import BinanceEnvironment
from nautilus_trader.adapters.binance.common.symbol import BinanceSymbol
from nautilus_trader.adapters.binance.config import BinanceDataClientConfig
from nautilus_trader.adapters.binance.config import BinanceExecClientConfig
from nautilus_trader.adapters.binance.config import BinanceInstrumentProviderConfig
from nautilus_trader.adapters.binance.factories import BinanceLiveDataClientFactory
from nautilus_trader.adapters.binance.factories import BinanceLiveExecClientFactory
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.identifiers import InstrumentId

from backtest.engine import run_backtest
from backtest.engine import run_portfolio_backtest
from config.settings import LiveSettings
from config.settings import load_live_config
from config.settings import load_research_config
from config.settings import STRATEGY_TYPES
from data.catalog import Catalog
from data.download import download_historical_data
from reports.performance import performance_report
from scripts.status_report import build_status_table
from strategy_factory import build_strategy


def _binance_account_type(value: str) -> BinanceAccountType:
    try:
        return BinanceAccountType[value]
    except KeyError as exc:
        raise ValueError(f"Invalid Binance account type: {value}") from exc


def _binance_environment(value: str) -> BinanceEnvironment:
    try:
        return BinanceEnvironment[value.upper()]
    except KeyError as exc:
        raise ValueError(f"Invalid Binance environment: {value}") from exc


def cmd_download(args: argparse.Namespace) -> int:
    settings = load_research_config(args.config)
    summary = download_historical_data(settings.market, settings.data)
    print(f"Downloaded data for {len(summary['symbols'])} symbols")
    for symbol, info in summary["per_symbol"].items():  # type: ignore[union-attr]
        print(f"  {symbol}: {info['bars_written']} bars")
    print(f"Catalog path: {settings.data.catalog_path}")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    settings = load_research_config(args.config)
    if args.strategy_type:
        settings = dataclasses.replace(settings, strategy_type=args.strategy_type)
        settings.validate()
    if args.output_dir:
        settings = dataclasses.replace(
            settings,
            report=dataclasses.replace(settings.report, output_dir=args.output_dir),
        )
    catalog = Catalog(settings.data.catalog_path)

    common_kwargs = dict(
        strategy_type=settings.strategy_type,
        mean_reversion=settings.mean_reversion,
        regime_switch=settings.regime_switch,
        breakout=settings.breakout,
        reclaim_mr=settings.reclaim_mr,
        trend_pullback=settings.trend_pullback,
        markdown_breakdown=settings.markdown_breakdown,
        trader_id=args.trader_id,
        log_level="OFF",
    )
    if settings.backtest.mode == "portfolio":
        run = run_portfolio_backtest(
            settings.market,
            settings.risk,
            settings.strategy,
            settings.backtest,
            catalog,
            portfolio_risk=settings.portfolio_risk,
            **common_kwargs,
        )
        print(f"\n===== PORTFOLIO: {','.join(run.symbols)} =====")
        try:
            written = performance_report(
                run.engine,
                run.result,
                settings.report,
                subdir="portfolio",
            )
        finally:
            run.engine.dispose()
        print(f"\nReport artifacts: {[str(p) for p in written]}")
        return 0

    runs = run_backtest(
        settings.market,
        settings.risk,
        settings.strategy,
        settings.backtest,
        catalog,
        **common_kwargs,
    )

    written_all: list[str] = []
    for run in runs:
        print(f"\n===== {run.symbol} =====")
        try:
            written = performance_report(
                run.engine,
                run.result,
                settings.report,
                subdir=run.symbol,
            )
            written_all.extend(str(p) for p in written)
        finally:
            run.engine.dispose()

    print(f"\nReport artifacts: {written_all}")
    return 0


async def _run_live(settings: LiveSettings) -> None:
    instrument_ids = [
        InstrumentId.from_str(settings.market.instrument_id(symbol))
        for symbol in settings.market.symbols
    ]

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if settings.enable_trading and (not api_key or not api_secret):
        raise ValueError(
            "enable_trading=true but BINANCE_API_KEY / BINANCE_API_SECRET "
            "are missing from the environment",
        )

    environment = _binance_environment(settings.environment)
    account_type = _binance_account_type(settings.market.account_type)

    instrument_provider = BinanceInstrumentProviderConfig(
        load_all=False,
        load_ids=frozenset(instrument_ids),
    )
    data_client = BinanceDataClientConfig(
        api_key=api_key,
        api_secret=api_secret,
        account_type=account_type,
        environment=environment,
        instrument_provider=instrument_provider,
    )

    exec_clients = {}
    if settings.enable_trading:
        exec_clients[BINANCE] = BinanceExecClientConfig(
            api_key=api_key,
            api_secret=api_secret,
            account_type=account_type,
            environment=environment,
            instrument_provider=instrument_provider,
            futures_leverages={
                BinanceSymbol(symbol): settings.market.leverage
                for symbol in settings.market.symbols
            },
        )

    node = TradingNode(
        config=TradingNodeConfig(
            logging=LoggingConfig(log_level=settings.log_level, print_config=False),
            data_clients={BINANCE: data_client},
            exec_clients=exec_clients,
        ),
    )

    tradfi_gate = None
    if settings.mean_reversion.tradfi_session_filter:
        from data.tradfi import TradfiSessionGate
        from data.tradfi import fetch_trading_schedule

        schedule = fetch_trading_schedule()
        tradfi_gate = TradfiSessionGate.from_payload(
            schedule,
            market_type=settings.mean_reversion.tradfi_market_type,
            allowed_sessions=settings.mean_reversion.tradfi_allowed_sessions,
        )

    portfolio_manager = None
    if settings.portfolio_risk.enabled:
        from risk.portfolio import PortfolioRiskLimits
        from risk.portfolio import PortfolioRiskManager

        portfolio_manager = PortfolioRiskManager(
            PortfolioRiskLimits(
                max_gross_notional=settings.portfolio_risk.max_gross_notional,
                max_portfolio_risk_pct=settings.portfolio_risk.max_portfolio_risk_pct,
                max_concurrent_positions=settings.portfolio_risk.max_concurrent_positions,
                max_positions_per_cluster=settings.portfolio_risk.max_positions_per_cluster,
                max_daily_loss_pct=settings.portfolio_risk.max_daily_loss_pct,
                circuit_breaker_losses=settings.portfolio_risk.circuit_breaker_losses,
            ),
            clusters=settings.portfolio_risk.clusters,
            asset_classes=settings.portfolio_risk.asset_classes,
        )

    # One strategy instance per symbol, sharing the account-wide risk manager.
    for symbol in settings.market.symbols:
        strategy = build_strategy(
            settings.market,
            settings.risk,
            settings.strategy,
            strategy_type=settings.strategy_type,
            mean_reversion=settings.mean_reversion,
            regime_switch=settings.regime_switch,
            breakout=settings.breakout,
            reclaim_mr=settings.reclaim_mr,
            trend_pullback=settings.trend_pullback,
            markdown_breakdown=settings.markdown_breakdown,
            enable_trading=settings.enable_trading,
            request_historical_bars=True,
            symbol=symbol,
        )
        strategy.set_portfolio_risk_manager(portfolio_manager)
        if hasattr(strategy, "set_tradfi_session_gate"):
            strategy.set_tradfi_session_gate(tradfi_gate)
        node.trader.add_strategy(strategy)

    node.add_data_client_factory(BINANCE, BinanceLiveDataClientFactory)
    if settings.enable_trading:
        node.add_exec_client_factory(BINANCE, BinanceLiveExecClientFactory)
    node.build()

    mode = (
        f"{environment.value} FUTURES TRADING"
        if settings.enable_trading
        else "SIGNAL-ONLY"
    )
    symbols = ",".join(settings.market.symbols)
    print(
        f"Starting NautilusTrader in {mode} mode | {symbols} | "
        f"strategy={settings.strategy_type} | "
        f"leverage={settings.market.leverage}x. Press Ctrl+C to stop.",
    )

    if settings.run_seconds > 0:
        run_task = asyncio.create_task(node.run_async())
        await asyncio.sleep(settings.run_seconds)
        await node.stop_async()
        await run_task
    else:
        await node.run_async()


def cmd_live(args: argparse.Namespace) -> int:
    load_dotenv()
    settings = load_live_config(args.config)
    try:
        asyncio.run(_run_live(settings))
    except (KeyboardInterrupt, SystemExit):
        print("\nStopping NautilusTrader...")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    print(build_status_table(args.results_root, args.snapshots_root))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crypto-futures trading system (Binance USD-M perpetual).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_down = sub.add_parser("download", help="Download historical data to catalog")
    p_down.add_argument("--config", default="config/research.yaml")
    p_down.set_defaults(func=cmd_download)

    p_back = sub.add_parser("backtest", help="Run backtests with fees/slippage")
    p_back.add_argument("--config", default="config/research.yaml")
    p_back.add_argument("--trader-id", default="BACKTESTER-001")
    p_back.add_argument("--strategy-type", choices=STRATEGY_TYPES)
    p_back.add_argument("--output-dir")
    p_back.set_defaults(func=cmd_backtest)

    p_live = sub.add_parser("live", help="Run live trading (Testnet/Demo)")
    p_live.add_argument("--config", default="config/live.yaml")
    p_live.set_defaults(func=cmd_live)

    p_status = sub.add_parser(
        "status",
        help="Print compact markdown status of latest result artifacts",
    )
    p_status.add_argument("--results-root", default=None)
    p_status.add_argument("--snapshots-root", default=None)
    p_status.set_defaults(func=cmd_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
