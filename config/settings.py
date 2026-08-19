"""Typed settings for the crypto-futures trading system.

The system is standardised on **Binance USD-M perpetual BTCUSDT-PERP** in
**one-way / netting mode**, running on **Testnet / Demo** (no real money).

``research`` and ``live`` configurations are intentionally split into two YAML
files so that backtest/data settings can never accidentally leak into a live
session and vice-versa. The shared ``MarketSettings`` keeps the USD-M vs COIN-M
choice in one place: switch ``account_type`` to ``COIN_FUTURES`` (and update
``symbol``/``base_currency`` accordingly) when moving to COIN-M.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml


# --------------------------------------------------------------------------- #
# Market / contract profile
# --------------------------------------------------------------------------- #
# Binance account type -> (base currency, default perpetual symbol). Keeping the
# mapping here means switching USD-M <-> COIN-M is a config-only change.
_ACCOUNT_PROFILES: dict[str, dict[str, str]] = {
    "USDT_FUTURES": {"base_currency": "USDT", "symbol": "BTCUSDT"},
    "COIN_FUTURES": {"base_currency": "BTC", "symbol": "BTCUSD"},
}


@dataclass(frozen=True)
class MarketSettings:
    """Market / contract assumptions shared by research and live."""

    venue: str = "BINANCE"
    account_type: str = "USDT_FUTURES"  # USDT_FUTURES | COIN_FUTURES
    symbol: str = "BTCUSDT"  # BTCUSDT (USD-M) | BTCUSD (COIN-M)
    base_currency: str = "USDT"  # USDT (USD-M) | BTC (COIN-M)
    contract_type: str = "PERP"
    oms_type: str = "NETTING"  # one-way mode (netting, not hedging)
    bar_step: int = 15
    bar_aggregation: str = "MINUTE"
    price_type: str = "LAST"
    leverage: int = 3

    @classmethod
    def for_account_type(cls, account_type: str, **overrides: Any) -> "MarketSettings":
        """Build market settings for a Binance account type with sane defaults."""
        profile = _ACCOUNT_PROFILES.get(account_type)
        if profile is None:
            raise ValueError(
                f"Unknown account_type {account_type!r}; "
                f"expected one of {sorted(_ACCOUNT_PROFILES)}",
            )
        values: dict[str, Any] = {
            "account_type": account_type,
            "symbol": profile["symbol"],
            "base_currency": profile["base_currency"],
        }
        values.update(overrides)
        return cls(**values)

    @property
    def instrument_id(self) -> str:
        """Nautilus instrument ID, e.g. ``BTCUSDT-PERP.BINANCE``."""
        return f"{self.symbol}-{self.contract_type}.{self.venue}"

    @property
    def bar_type(self) -> str:
        """Standard external bar type, e.g. ``BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL``."""
        return (
            f"{self.instrument_id}-{self.bar_step}-{self.bar_aggregation}-"
            f"{self.price_type}-EXTERNAL"
        )


# --------------------------------------------------------------------------- #
# Risk management
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RiskSettings:
    """Per-trade and daily risk limits (denominated in ``base_currency``)."""

    risk_per_trade: Decimal = Decimal("5")
    max_notional: Decimal = Decimal("300")
    max_daily_loss: Decimal = Decimal("20")
    max_trades_per_day: int = 4
    cooldown_bars_after_loss: int = 4
    atr_stop_multiple: float = 2.0
    allow_short: bool = True
    close_position_on_stop: bool = True

    def validate(self) -> None:
        if self.risk_per_trade <= 0 or self.max_notional <= 0 or self.max_daily_loss <= 0:
            raise ValueError("risk_per_trade, max_notional and max_daily_loss must be > 0")
        if self.max_trades_per_day <= 0:
            raise ValueError("max_trades_per_day must be > 0")
        if self.atr_stop_multiple <= 0:
            raise ValueError("atr_stop_multiple must be > 0")


# --------------------------------------------------------------------------- #
# Strategy parameters
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StrategySettings:
    """EMA-ATR trend strategy parameters."""

    fast_ema_period: int = 20
    slow_ema_period: int = 50
    trend_ema_period: int = 200
    atr_period: int = 14
    history_days: int = 10

    def validate(self) -> None:
        if not self.fast_ema_period < self.slow_ema_period < self.trend_ema_period:
            raise ValueError("EMA periods must satisfy fast < slow < trend")
        if self.atr_period <= 0:
            raise ValueError("atr_period must be > 0")


@dataclass(frozen=True)
class MeanReversionSettings:
    """Bollinger + RSI mean-reversion strategy parameters."""

    bb_period: int = 20
    bb_k: float = 2.0
    rsi_period: int = 2
    rsi_oversold: float = 10.0
    rsi_overbought: float = 90.0
    vhf_period: int = 28
    vhf_max: float = 0.35
    atr_period: int = 14
    history_days: int = 10

    def validate(self) -> None:
        if self.bb_period <= 0 or self.rsi_period <= 0 or self.vhf_period <= 0:
            raise ValueError("indicator periods must be > 0")
        if not 0 <= self.rsi_oversold < self.rsi_overbought <= 100:
            raise ValueError("RSI levels must satisfy 0 <= oversold < overbought <= 100")


# --------------------------------------------------------------------------- #
# Research (data download + backtest + report)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DataDownloadSettings:
    catalog_path: str = "./catalog"
    environment: str = "TESTNET"  # BinanceEnvironment: TESTNET | DEMO | LIVE
    start: str | None = None  # ISO datetime or None
    end: str | None = None  # ISO datetime or None
    lookback_days: int = 30  # used when start is None


@dataclass(frozen=True)
class BacktestSettings:
    start: str | None = None
    end: str | None = None
    starting_balance: str = "100000 USDT"
    fee_model: str = "maker_taker"  # maker_taker | fixed
    fixed_fee: str = "1 USDT"  # used when fee_model == fixed
    fill_model: str = "one_tick_slippage"  # best_price | one_tick_slippage | probabilistic
    prob_fill_on_limit: float = 1.0
    prob_slippage: float = 0.0
    random_seed: int | None = 42


@dataclass(frozen=True)
class ReportSettings:
    output_dir: str = "./results"
    include_csv: bool = True
    include_json: bool = True


@dataclass(frozen=True)
class ResearchSettings:
    market: MarketSettings
    risk: RiskSettings
    strategy: StrategySettings
    data: DataDownloadSettings
    backtest: BacktestSettings
    report: ReportSettings
    strategy_type: str = "ema_atr"  # ema_atr | mean_reversion
    mean_reversion: MeanReversionSettings = None  # type: ignore[assignment]

    def validate(self) -> None:
        self.risk.validate()
        self.strategy.validate()
        if self.strategy_type == "mean_reversion" and self.mean_reversion is not None:
            self.mean_reversion.validate()
        elif self.strategy_type not in ("ema_atr", "mean_reversion"):
            raise ValueError(f"Unknown strategy_type: {self.strategy_type!r}")
        if not (1 <= self.market.leverage <= 125):
            raise ValueError("leverage must be between 1 and 125")


# --------------------------------------------------------------------------- #
# Live
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LiveSettings:
    environment: str = "TESTNET"  # TESTNET | DEMO (never LIVE without explicit opt-in)
    enable_trading: bool = False
    run_seconds: int = 0  # 0 = run until Ctrl+C
    log_level: str = "INFO"
    market: MarketSettings = None  # type: ignore[assignment]
    risk: RiskSettings = None  # type: ignore[assignment]
    strategy: StrategySettings = None  # type: ignore[assignment]
    strategy_type: str = "ema_atr"  # ema_atr | mean_reversion
    mean_reversion: MeanReversionSettings = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.environment == "LIVE":
            # Hard safety guard: the system is standardised on Testnet/Demo.
            raise ValueError(
                "LIVE environment is disabled by default (no real money). "
                "Use TESTNET or DEMO.",
            )

    def validate(self) -> None:
        self.risk.validate()
        self.strategy.validate()
        if self.strategy_type == "mean_reversion" and self.mean_reversion is not None:
            self.mean_reversion.validate()
        elif self.strategy_type not in ("ema_atr", "mean_reversion"):
            raise ValueError(f"Unknown strategy_type: {self.strategy_type!r}")


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def _load_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _build_market(data: dict[str, Any]) -> MarketSettings:
    account_type = data.get("account_type", "USDT_FUTURES")
    profile = _ACCOUNT_PROFILES.get(account_type)
    if profile is None:
        raise ValueError(
            f"Unknown account_type {account_type!r}; "
            f"expected one of {sorted(_ACCOUNT_PROFILES)}",
        )
    return MarketSettings(
        venue=data.get("venue", "BINANCE"),
        account_type=account_type,
        symbol=data.get("symbol") or profile["symbol"],
        base_currency=data.get("base_currency") or profile["base_currency"],
        contract_type=data.get("contract_type", "PERP"),
        oms_type=data.get("oms_type", "NETTING"),
        bar_step=int(data.get("bar_step", 15)),
        bar_aggregation=data.get("bar_aggregation", "MINUTE"),
        price_type=data.get("price_type", "LAST"),
        leverage=int(data.get("leverage", 3)),
    )


def _build_risk(data: dict[str, Any]) -> RiskSettings:
    return RiskSettings(
        risk_per_trade=Decimal(str(data.get("risk_per_trade", "5"))),
        max_notional=Decimal(str(data.get("max_notional", "300"))),
        max_daily_loss=Decimal(str(data.get("max_daily_loss", "20"))),
        max_trades_per_day=int(data.get("max_trades_per_day", 4)),
        cooldown_bars_after_loss=int(data.get("cooldown_bars_after_loss", 4)),
        atr_stop_multiple=float(data.get("atr_stop_multiple", 2.0)),
        allow_short=bool(data.get("allow_short", True)),
        close_position_on_stop=bool(data.get("close_position_on_stop", True)),
    )


def _build_strategy(data: dict[str, Any]) -> StrategySettings:
    return StrategySettings(
        fast_ema_period=int(data.get("fast_ema_period", 20)),
        slow_ema_period=int(data.get("slow_ema_period", 50)),
        trend_ema_period=int(data.get("trend_ema_period", 200)),
        atr_period=int(data.get("atr_period", 14)),
        history_days=int(data.get("history_days", 10)),
    )


def _build_mean_reversion(data: dict[str, Any]) -> MeanReversionSettings:
    return MeanReversionSettings(
        bb_period=int(data.get("bb_period", 20)),
        bb_k=float(data.get("bb_k", 2.0)),
        rsi_period=int(data.get("rsi_period", 2)),
        rsi_oversold=float(data.get("rsi_oversold", 10.0)),
        rsi_overbought=float(data.get("rsi_overbought", 90.0)),
        vhf_period=int(data.get("vhf_period", 28)),
        vhf_max=float(data.get("vhf_max", 0.35)),
        atr_period=int(data.get("atr_period", 14)),
        history_days=int(data.get("history_days", 10)),
    )


def load_research_config(path: str | Path) -> ResearchSettings:
    """Load a research (data + backtest + report) configuration from YAML."""
    data = _load_mapping(Path(path))
    settings = ResearchSettings(
        market=_build_market(data.get("market", {})),
        risk=_build_risk(data.get("risk", {})),
        strategy=_build_strategy(data.get("strategy", {})),
        data=DataDownloadSettings(**data.get("data", {})),
        backtest=BacktestSettings(**data.get("backtest", {})),
        report=ReportSettings(**data.get("report", {})),
        strategy_type=data.get("strategy_type", "ema_atr"),
        mean_reversion=_build_mean_reversion(data.get("mean_reversion", {})),
    )
    settings.validate()
    return settings


def load_live_config(path: str | Path) -> LiveSettings:
    """Load a live-trading configuration from YAML."""
    data = _load_mapping(Path(path))
    settings = LiveSettings(
        environment=data.get("environment", "TESTNET").upper(),
        enable_trading=bool(data.get("enable_trading", False)),
        run_seconds=int(data.get("run_seconds", 0)),
        log_level=data.get("log_level", "INFO"),
        market=_build_market(data.get("market", {})),
        risk=_build_risk(data.get("risk", {})),
        strategy=_build_strategy(data.get("strategy", {})),
        strategy_type=data.get("strategy_type", "ema_atr"),
        mean_reversion=_build_mean_reversion(data.get("mean_reversion", {})),
    )
    settings.validate()
    return settings
