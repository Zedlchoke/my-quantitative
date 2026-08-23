"""Typed settings for the crypto-futures trading system.

The system is standardised on **Binance USD-M perpetuals** in **one-way / netting
mode**, running on **Testnet / Demo** (no real money).

``research`` and ``live`` configurations are intentionally split into two YAML
files so that backtest/data settings can never accidentally leak into a live
session and vice-versa. ``MarketSettings`` keeps the USD-M vs COIN-M choice and
the traded symbols in one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml


# --------------------------------------------------------------------------- #
# Market / contract profile
# --------------------------------------------------------------------------- #
# Binance account type -> default perpetual symbols. USD-M uses USDT as the
# shared base currency; COIN-M is per-symbol margin (BTC for BTCUSD, etc.).
_ACCOUNT_PROFILES: dict[str, dict[str, str]] = {
    "USDT_FUTURES": {"base_currency": "USDT", "default_symbol": "BTCUSDT"},
    "COIN_FUTURES": {"base_currency": "BTC", "default_symbol": "BTCUSD"},
}


@dataclass(frozen=True)
class MarketSettings:
    """Market / contract assumptions shared by research and live."""

    venue: str = "BINANCE"
    account_type: str = "USDT_FUTURES"  # USDT_FUTURES | COIN_FUTURES
    symbols: tuple[str, ...] = ("BTCUSDT",)  # e.g. BTCUSDT, ETHUSDT, SOLUSDT
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
            "symbols": (profile["default_symbol"],),
            "base_currency": profile["base_currency"],
        }
        values.update(overrides)
        return cls(**values)

    def instrument_id(self, symbol: str) -> str:
        """Nautilus instrument ID, e.g. ``BTCUSDT-PERP.BINANCE``."""
        return f"{symbol}-{self.contract_type}.{self.venue}"

    def bar_type(self, symbol: str) -> str:
        """Standard external bar type, e.g. ``BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL``."""
        return (
            f"{self.instrument_id(symbol)}-{self.bar_step}-{self.bar_aggregation}-"
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
    risk_pct_per_trade: float | None = None
    max_risk_per_trade_usdt: Decimal | None = None
    max_daily_loss_pct: float | None = None
    circuit_breaker_losses: int = 0
    circuit_breaker_pause_bars: int = 96

    def validate(self) -> None:
        if self.risk_per_trade <= 0 or self.max_notional <= 0 or self.max_daily_loss <= 0:
            raise ValueError("risk_per_trade, max_notional and max_daily_loss must be > 0")
        if self.max_trades_per_day <= 0:
            raise ValueError("max_trades_per_day must be > 0")
        if self.atr_stop_multiple <= 0:
            raise ValueError("atr_stop_multiple must be > 0")
        if self.risk_pct_per_trade is not None and self.risk_pct_per_trade <= 0:
            raise ValueError("risk_pct_per_trade must be > 0 when set")
        if self.max_daily_loss_pct is not None and self.max_daily_loss_pct <= 0:
            raise ValueError("max_daily_loss_pct must be > 0 when set")
        if self.circuit_breaker_losses < 0:
            raise ValueError("circuit_breaker_losses must be >= 0")


@dataclass(frozen=True)
class PortfolioRiskSettings:
    """Account-wide limits shared by every symbol strategy."""

    enabled: bool = False
    max_gross_notional: Decimal = Decimal("1200")
    max_portfolio_risk_pct: float = 3.0
    max_concurrent_positions: int = 4
    max_positions_per_cluster: int = 2
    max_daily_loss_pct: float = 2.0
    circuit_breaker_losses: int = 6
    clusters: dict[str, str] = field(default_factory=dict)
    asset_classes: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.enabled:
            return
        from risk.portfolio import PortfolioRiskLimits

        PortfolioRiskLimits(
            max_gross_notional=self.max_gross_notional,
            max_portfolio_risk_pct=self.max_portfolio_risk_pct,
            max_concurrent_positions=self.max_concurrent_positions,
            max_positions_per_cluster=self.max_positions_per_cluster,
            max_daily_loss_pct=self.max_daily_loss_pct,
            circuit_breaker_losses=self.circuit_breaker_losses,
        ).validate()


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
    adx_period: int = 14
    adx_max: float = 25.0
    volume_sma_period: int = 20
    volume_max_ratio: float = 1.5
    atr_period: int = 14
    atr_stop_multiple: float = 1.0  # stop distance frozen at entry
    take_profit_multiple: float = 1.5  # reward:risk target
    history_days: int = 10
    htf_trend_filter: bool = False
    htf_ema_period: int = 200
    htf_minutes: int = 60
    wyckoff_gate: bool = False
    wyckoff_directional_bias: bool = False
    tradfi_session_filter: bool = False
    tradfi_market_type: str = "EQUITY"
    tradfi_allowed_sessions: tuple[str, ...] = ("REGULAR",)

    def validate(self) -> None:
        if self.wyckoff_directional_bias and not self.wyckoff_gate:
            raise ValueError("wyckoff_directional_bias requires wyckoff_gate=true")
        if self.bb_period <= 0 or self.rsi_period <= 0 or self.vhf_period <= 0:
            raise ValueError("indicator periods must be > 0")
        if self.adx_period <= 0 or self.volume_sma_period <= 0:
            raise ValueError("adx_period and volume_sma_period must be > 0")
        if not 0 <= self.rsi_oversold < self.rsi_overbought <= 100:
            raise ValueError("RSI levels must satisfy 0 <= oversold < overbought <= 100")
        if self.atr_stop_multiple <= 0:
            raise ValueError("atr_stop_multiple must be > 0")
        if self.take_profit_multiple <= 0:
            raise ValueError("take_profit_multiple must be > 0")
        if self.adx_max <= 0 or self.volume_max_ratio <= 0:
            raise ValueError("adx_max and volume_max_ratio must be > 0")


@dataclass(frozen=True)
class RegimeSwitchSettings:
    """Regime-switch strategy: trend (EMA-ATR) in trends, mean-reversion in ranges."""

    # Trend leg (EMA-ATR)
    fast_ema_period: int = 20
    slow_ema_period: int = 50
    trend_ema_period: int = 200
    # Mean-reversion leg (Bollinger + RSI)
    bb_period: int = 20
    bb_k: float = 2.0
    rsi_period: int = 2
    rsi_oversold: float = 10.0
    rsi_overbought: float = 90.0
    # Regime filter (VHF): <= vhf_max => ranging, else trending
    vhf_period: int = 28
    vhf_max: float = 0.35
    adx_period: int = 14
    adx_max: float = 25.0
    volume_sma_period: int = 20
    volume_max_ratio: float = 1.5
    # Stops / target
    atr_period: int = 14
    trend_stop_multiple: float = 2.0
    mean_reversion_stop_multiple: float = 1.0
    take_profit_multiple: float = 1.5
    history_days: int = 10

    def validate(self) -> None:
        if not self.fast_ema_period < self.slow_ema_period < self.trend_ema_period:
            raise ValueError("EMA periods must satisfy fast < slow < trend")
        if self.bb_period <= 0 or self.rsi_period <= 0 or self.vhf_period <= 0:
            raise ValueError("indicator periods must be > 0")
        if self.adx_period <= 0 or self.volume_sma_period <= 0:
            raise ValueError("adx_period and volume_sma_period must be > 0")
        if not 0 <= self.rsi_oversold < self.rsi_overbought <= 100:
            raise ValueError("RSI levels must satisfy 0 <= oversold < overbought <= 100")
        if self.trend_stop_multiple <= 0 or self.mean_reversion_stop_multiple <= 0:
            raise ValueError("stop multiples must be > 0")
        if self.take_profit_multiple <= 0:
            raise ValueError("take_profit_multiple must be > 0")
        if self.adx_max <= 0 or self.volume_max_ratio <= 0:
            raise ValueError("adx_max and volume_max_ratio must be > 0")


@dataclass(frozen=True)
class BreakoutSettings:
    """Volatility breakout (markup-only research leg) — fixed TA thresholds."""

    donchian_period: int = 20
    adx_period: int = 14
    adx_min: float = 25.0
    volume_sma_period: int = 20
    volume_min_ratio: float = 1.3
    atr_period: int = 14
    atr_stop_multiple: float = 2.0
    take_profit_multiple: float = 2.0
    wyckoff_markup_only: bool = True
    history_days: int = 220

    def validate(self) -> None:
        if self.donchian_period <= 0 or self.adx_period <= 0:
            raise ValueError("donchian_period and adx_period must be > 0")
        if self.volume_sma_period <= 0:
            raise ValueError("volume_sma_period must be > 0")
        if self.adx_min <= 0 or self.volume_min_ratio <= 0:
            raise ValueError("adx_min and volume_min_ratio must be > 0")
        if self.atr_stop_multiple <= 0 or self.take_profit_multiple <= 0:
            raise ValueError("stop/TP multiples must be > 0")


@dataclass(frozen=True)
class ReclaimMeanReversionSettings:
    """Fixed reclaim-MR baseline for weak-trend accumulation/transition ranges."""

    bb_period: int = 20
    bb_k: float = 2.0
    rsi_period: int = 2
    rsi_oversold: float = 15.0
    rsi_overbought: float = 85.0
    vhf_period: int = 28
    vhf_max: float = 0.25
    adx_period: int = 14
    adx_max: float = 20.0
    volume_sma_period: int = 20
    volume_max_ratio: float = 1.8
    atr_period: int = 14
    atr_stop_multiple: float = 1.5
    take_profit_multiple: float = 2.0
    history_days: int = 220
    phase_gate: bool = True

    def validate(self) -> None:
        if self.bb_period <= 0 or self.rsi_period <= 0 or self.vhf_period <= 0:
            raise ValueError("reclaim-MR indicator periods must be > 0")
        if not 0 <= self.rsi_oversold < self.rsi_overbought <= 100:
            raise ValueError("RSI levels must satisfy 0 <= oversold < overbought <= 100")
        if self.adx_period <= 0 or self.volume_sma_period <= 0:
            raise ValueError("reclaim-MR periods must be > 0")
        if self.vhf_max <= 0 or self.adx_max <= 0 or self.volume_max_ratio <= 0:
            raise ValueError("reclaim-MR thresholds must be > 0")
        if self.atr_stop_multiple <= 0 or self.take_profit_multiple <= 0:
            raise ValueError("reclaim-MR stop/TP must be > 0")


@dataclass(frozen=True)
class TrendPullbackSettings:
    """Fixed fast-EMA reclaim baseline for directional pullbacks."""

    fast_ema_period: int = 20
    slow_ema_period: int = 50
    trend_ema_period: int = 200
    adx_period: int = 14
    adx_min: float = 20.0
    volume_sma_period: int = 20
    volume_min_ratio: float = 0.8
    atr_period: int = 14
    atr_stop_multiple: float = 2.0
    history_days: int = 220
    phase_gate: bool = True

    def validate(self) -> None:
        if not self.fast_ema_period < self.slow_ema_period < self.trend_ema_period:
            raise ValueError("pullback EMA periods must satisfy fast < slow < trend")
        if self.adx_period <= 0 or self.volume_sma_period <= 0 or self.atr_period <= 0:
            raise ValueError("pullback periods must be > 0")
        if self.adx_min <= 0 or self.volume_min_ratio <= 0 or self.atr_stop_multiple <= 0:
            raise ValueError("pullback thresholds must be > 0")


@dataclass(frozen=True)
class MarkdownBreakdownSettings:
    """Fixed short-only lower-Donchian breakdown baseline."""

    donchian_period: int = 20
    trend_ema_period: int = 200
    adx_period: int = 14
    adx_min: float = 20.0
    volume_sma_period: int = 20
    volume_min_ratio: float = 1.3
    atr_period: int = 14
    atr_stop_multiple: float = 2.0
    take_profit_multiple: float = 1.5
    history_days: int = 220
    phase_gate: bool = True

    def validate(self) -> None:
        if self.donchian_period <= 0 or self.trend_ema_period <= 0:
            raise ValueError("breakdown periods must be > 0")
        if self.adx_period <= 0 or self.volume_sma_period <= 0 or self.atr_period <= 0:
            raise ValueError("breakdown periods must be > 0")
        if self.adx_min <= 0 or self.volume_min_ratio <= 0:
            raise ValueError("breakdown thresholds must be > 0")
        if self.atr_stop_multiple <= 0 or self.take_profit_multiple <= 0:
            raise ValueError("breakdown stop/TP must be > 0")


STRATEGY_TYPES = (
    "ema_atr",
    "mean_reversion",
    "regime_switch",
    "breakout",
    "reclaim_mr",
    "trend_pullback",
    "markdown_breakdown",
)


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
    mode: str = "per_symbol"  # per_symbol | portfolio
    start: str | None = None
    end: str | None = None
    starting_balance: str = "100000 USDT"
    fee_model: str = "maker_taker"  # maker_taker | fixed
    fixed_fee: str = "1 USDT"  # used when fee_model == fixed
    fill_model: str = "one_tick_slippage"  # best_price | one_tick_slippage | probabilistic
    prob_fill_on_limit: float = 1.0
    prob_slippage: float = 0.0
    random_seed: int | None = 42

    def validate(self) -> None:
        if self.mode not in {"per_symbol", "portfolio"}:
            raise ValueError("backtest.mode must be per_symbol or portfolio")


@dataclass(frozen=True)
class ReportSettings:
    output_dir: str = "./results"
    include_csv: bool = True
    include_json: bool = True
    funding_data_path: str | None = None


@dataclass(frozen=True)
class ResearchSettings:
    market: MarketSettings
    risk: RiskSettings
    strategy: StrategySettings
    data: DataDownloadSettings
    backtest: BacktestSettings
    report: ReportSettings
    portfolio_risk: PortfolioRiskSettings = field(default_factory=PortfolioRiskSettings)
    strategy_type: str = "ema_atr"  # ema_atr | mean_reversion | regime_switch | breakout
    mean_reversion: MeanReversionSettings = None  # type: ignore[assignment]
    regime_switch: RegimeSwitchSettings = None  # type: ignore[assignment]
    breakout: BreakoutSettings = None  # type: ignore[assignment]
    reclaim_mr: ReclaimMeanReversionSettings = None  # type: ignore[assignment]
    trend_pullback: TrendPullbackSettings = None  # type: ignore[assignment]
    markdown_breakdown: MarkdownBreakdownSettings = None  # type: ignore[assignment]

    def validate(self) -> None:
        self.risk.validate()
        self.strategy.validate()
        self.backtest.validate()
        self.portfolio_risk.validate()
        if self.strategy_type == "mean_reversion":
            if self.mean_reversion is None:
                raise ValueError("mean_reversion settings are required")
            self.mean_reversion.validate()
        elif self.strategy_type == "regime_switch":
            if self.regime_switch is None:
                raise ValueError("regime_switch settings are required")
            self.regime_switch.validate()
        elif self.strategy_type == "breakout":
            if self.breakout is None:
                raise ValueError("breakout settings are required")
            self.breakout.validate()
        elif self.strategy_type == "reclaim_mr":
            if self.reclaim_mr is None:
                raise ValueError("reclaim_mr settings are required")
            self.reclaim_mr.validate()
        elif self.strategy_type == "trend_pullback":
            if self.trend_pullback is None:
                raise ValueError("trend_pullback settings are required")
            self.trend_pullback.validate()
        elif self.strategy_type == "markdown_breakdown":
            if self.markdown_breakdown is None:
                raise ValueError("markdown_breakdown settings are required")
            self.markdown_breakdown.validate()
        elif self.strategy_type not in STRATEGY_TYPES:
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
    strategy_type: str = "ema_atr"  # ema_atr | mean_reversion | regime_switch
    mean_reversion: MeanReversionSettings = None  # type: ignore[assignment]
    regime_switch: RegimeSwitchSettings = None  # type: ignore[assignment]
    breakout: BreakoutSettings = None  # type: ignore[assignment]
    reclaim_mr: ReclaimMeanReversionSettings = None  # type: ignore[assignment]
    trend_pullback: TrendPullbackSettings = None  # type: ignore[assignment]
    markdown_breakdown: MarkdownBreakdownSettings = None  # type: ignore[assignment]
    portfolio_risk: PortfolioRiskSettings = field(default_factory=PortfolioRiskSettings)

    def __post_init__(self) -> None:
        if self.environment == "LIVE" and self.enable_trading:
            # Public production data is allowed in signal-only mode; execution is not.
            raise ValueError(
                "LIVE execution is disabled (no real money). Use LIVE only with "
                "enable_trading=false, or use TESTNET/DEMO for execution tests.",
            )

    def validate(self) -> None:
        self.risk.validate()
        self.strategy.validate()
        self.portfolio_risk.validate()
        if self.strategy_type == "mean_reversion":
            if self.mean_reversion is None:
                raise ValueError("mean_reversion settings are required")
            self.mean_reversion.validate()
        elif self.strategy_type == "regime_switch":
            if self.regime_switch is None:
                raise ValueError("regime_switch settings are required")
            self.regime_switch.validate()
        elif self.strategy_type == "breakout":
            if self.breakout is None:
                raise ValueError("breakout settings are required")
            self.breakout.validate()
        elif self.strategy_type == "reclaim_mr":
            if self.reclaim_mr is None:
                raise ValueError("reclaim_mr settings are required")
            self.reclaim_mr.validate()
        elif self.strategy_type == "trend_pullback":
            if self.trend_pullback is None:
                raise ValueError("trend_pullback settings are required")
            self.trend_pullback.validate()
        elif self.strategy_type == "markdown_breakdown":
            if self.markdown_breakdown is None:
                raise ValueError("markdown_breakdown settings are required")
            self.markdown_breakdown.validate()
        elif self.strategy_type not in STRATEGY_TYPES:
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

    raw_symbols = data.get("symbols", [data.get("symbol") or profile["default_symbol"]])
    if isinstance(raw_symbols, str):
        raw_symbols = [raw_symbols]
    symbols = tuple(str(s) for s in raw_symbols)

    return MarketSettings(
        venue=data.get("venue", "BINANCE"),
        account_type=account_type,
        symbols=symbols,
        base_currency=data.get("base_currency") or profile["base_currency"],
        contract_type=data.get("contract_type", "PERP"),
        oms_type=data.get("oms_type", "NETTING"),
        bar_step=int(data.get("bar_step", 15)),
        bar_aggregation=data.get("bar_aggregation", "MINUTE"),
        price_type=data.get("price_type", "LAST"),
        leverage=int(data.get("leverage", 3)),
    )


def _build_risk(data: dict[str, Any]) -> RiskSettings:
    max_risk = data.get("max_risk_per_trade_usdt")
    return RiskSettings(
        risk_per_trade=Decimal(str(data.get("risk_per_trade", "5"))),
        max_notional=Decimal(str(data.get("max_notional", "300"))),
        max_daily_loss=Decimal(str(data.get("max_daily_loss", "20"))),
        max_trades_per_day=int(data.get("max_trades_per_day", 4)),
        cooldown_bars_after_loss=int(data.get("cooldown_bars_after_loss", 4)),
        atr_stop_multiple=float(data.get("atr_stop_multiple", 2.0)),
        allow_short=bool(data.get("allow_short", True)),
        close_position_on_stop=bool(data.get("close_position_on_stop", True)),
        risk_pct_per_trade=data.get("risk_pct_per_trade"),
        max_risk_per_trade_usdt=Decimal(str(max_risk)) if max_risk is not None else None,
        max_daily_loss_pct=data.get("max_daily_loss_pct"),
        circuit_breaker_losses=int(data.get("circuit_breaker_losses", 0)),
        circuit_breaker_pause_bars=int(data.get("circuit_breaker_pause_bars", 96)),
    )


def _build_portfolio_risk(data: dict[str, Any]) -> PortfolioRiskSettings:
    return PortfolioRiskSettings(
        enabled=bool(data.get("enabled", False)),
        max_gross_notional=Decimal(str(data.get("max_gross_notional", "1200"))),
        max_portfolio_risk_pct=float(data.get("max_portfolio_risk_pct", 3.0)),
        max_concurrent_positions=int(data.get("max_concurrent_positions", 4)),
        max_positions_per_cluster=int(data.get("max_positions_per_cluster", 2)),
        max_daily_loss_pct=float(data.get("max_daily_loss_pct", 2.0)),
        circuit_breaker_losses=int(data.get("circuit_breaker_losses", 6)),
        clusters={str(k): str(v) for k, v in data.get("clusters", {}).items()},
        asset_classes={str(k): str(v) for k, v in data.get("asset_classes", {}).items()},
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
        adx_period=int(data.get("adx_period", 14)),
        adx_max=float(data.get("adx_max", 25.0)),
        volume_sma_period=int(data.get("volume_sma_period", 20)),
        volume_max_ratio=float(data.get("volume_max_ratio", 1.5)),
        atr_period=int(data.get("atr_period", 14)),
        atr_stop_multiple=float(data.get("atr_stop_multiple", 1.0)),
        take_profit_multiple=float(data.get("take_profit_multiple", 1.5)),
        history_days=int(data.get("history_days", 10)),
        htf_trend_filter=bool(data.get("htf_trend_filter", False)),
        htf_ema_period=int(data.get("htf_ema_period", 200)),
        htf_minutes=int(data.get("htf_minutes", 60)),
        wyckoff_gate=bool(data.get("wyckoff_gate", False)),
        wyckoff_directional_bias=bool(data.get("wyckoff_directional_bias", False)),
        tradfi_session_filter=bool(data.get("tradfi_session_filter", False)),
        tradfi_market_type=str(data.get("tradfi_market_type", "EQUITY")),
        tradfi_allowed_sessions=tuple(data.get("tradfi_allowed_sessions", ["REGULAR"])),
    )


def _build_regime_switch(data: dict[str, Any]) -> RegimeSwitchSettings:
    return RegimeSwitchSettings(
        fast_ema_period=int(data.get("fast_ema_period", 20)),
        slow_ema_period=int(data.get("slow_ema_period", 50)),
        trend_ema_period=int(data.get("trend_ema_period", 200)),
        bb_period=int(data.get("bb_period", 20)),
        bb_k=float(data.get("bb_k", 2.0)),
        rsi_period=int(data.get("rsi_period", 2)),
        rsi_oversold=float(data.get("rsi_oversold", 10.0)),
        rsi_overbought=float(data.get("rsi_overbought", 90.0)),
        vhf_period=int(data.get("vhf_period", 28)),
        vhf_max=float(data.get("vhf_max", 0.35)),
        adx_period=int(data.get("adx_period", 14)),
        adx_max=float(data.get("adx_max", 25.0)),
        volume_sma_period=int(data.get("volume_sma_period", 20)),
        volume_max_ratio=float(data.get("volume_max_ratio", 1.5)),
        atr_period=int(data.get("atr_period", 14)),
        trend_stop_multiple=float(data.get("trend_stop_multiple", 2.0)),
        mean_reversion_stop_multiple=float(data.get("mean_reversion_stop_multiple", 1.0)),
        take_profit_multiple=float(data.get("take_profit_multiple", 1.5)),
        history_days=int(data.get("history_days", 10)),
    )


def _build_breakout(data: dict[str, Any]) -> BreakoutSettings:
    return BreakoutSettings(
        donchian_period=int(data.get("donchian_period", 20)),
        adx_period=int(data.get("adx_period", 14)),
        adx_min=float(data.get("adx_min", 25.0)),
        volume_sma_period=int(data.get("volume_sma_period", 20)),
        volume_min_ratio=float(data.get("volume_min_ratio", 1.3)),
        atr_period=int(data.get("atr_period", 14)),
        atr_stop_multiple=float(data.get("atr_stop_multiple", 2.0)),
        take_profit_multiple=float(data.get("take_profit_multiple", 2.0)),
        wyckoff_markup_only=bool(data.get("wyckoff_markup_only", True)),
        history_days=int(data.get("history_days", 220)),
    )


def _build_reclaim_mr(data: dict[str, Any]) -> ReclaimMeanReversionSettings:
    return ReclaimMeanReversionSettings(
        bb_period=int(data.get("bb_period", 20)),
        bb_k=float(data.get("bb_k", 2.0)),
        rsi_period=int(data.get("rsi_period", 2)),
        rsi_oversold=float(data.get("rsi_oversold", 15.0)),
        rsi_overbought=float(data.get("rsi_overbought", 85.0)),
        vhf_period=int(data.get("vhf_period", 28)),
        vhf_max=float(data.get("vhf_max", 0.25)),
        adx_period=int(data.get("adx_period", 14)),
        adx_max=float(data.get("adx_max", 20.0)),
        volume_sma_period=int(data.get("volume_sma_period", 20)),
        volume_max_ratio=float(data.get("volume_max_ratio", 1.8)),
        atr_period=int(data.get("atr_period", 14)),
        atr_stop_multiple=float(data.get("atr_stop_multiple", 1.5)),
        take_profit_multiple=float(data.get("take_profit_multiple", 2.0)),
        history_days=int(data.get("history_days", 220)),
        phase_gate=bool(data.get("phase_gate", True)),
    )


def _build_trend_pullback(data: dict[str, Any]) -> TrendPullbackSettings:
    return TrendPullbackSettings(
        fast_ema_period=int(data.get("fast_ema_period", 20)),
        slow_ema_period=int(data.get("slow_ema_period", 50)),
        trend_ema_period=int(data.get("trend_ema_period", 200)),
        adx_period=int(data.get("adx_period", 14)),
        adx_min=float(data.get("adx_min", 20.0)),
        volume_sma_period=int(data.get("volume_sma_period", 20)),
        volume_min_ratio=float(data.get("volume_min_ratio", 0.8)),
        atr_period=int(data.get("atr_period", 14)),
        atr_stop_multiple=float(data.get("atr_stop_multiple", 2.0)),
        history_days=int(data.get("history_days", 220)),
        phase_gate=bool(data.get("phase_gate", True)),
    )


def _build_markdown_breakdown(data: dict[str, Any]) -> MarkdownBreakdownSettings:
    return MarkdownBreakdownSettings(
        donchian_period=int(data.get("donchian_period", 20)),
        trend_ema_period=int(data.get("trend_ema_period", 200)),
        adx_period=int(data.get("adx_period", 14)),
        adx_min=float(data.get("adx_min", 20.0)),
        volume_sma_period=int(data.get("volume_sma_period", 20)),
        volume_min_ratio=float(data.get("volume_min_ratio", 1.3)),
        atr_period=int(data.get("atr_period", 14)),
        atr_stop_multiple=float(data.get("atr_stop_multiple", 2.0)),
        take_profit_multiple=float(data.get("take_profit_multiple", 1.5)),
        history_days=int(data.get("history_days", 220)),
        phase_gate=bool(data.get("phase_gate", True)),
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
        portfolio_risk=_build_portfolio_risk(data.get("portfolio_risk", {})),
        strategy_type=data.get("strategy_type", "ema_atr"),
        mean_reversion=_build_mean_reversion(data.get("mean_reversion", {})),
        regime_switch=_build_regime_switch(data.get("regime_switch", {})),
        breakout=_build_breakout(data.get("breakout", {})),
        reclaim_mr=_build_reclaim_mr(data.get("reclaim_mr", {})),
        trend_pullback=_build_trend_pullback(data.get("trend_pullback", {})),
        markdown_breakdown=_build_markdown_breakdown(data.get("markdown_breakdown", {})),
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
        regime_switch=_build_regime_switch(data.get("regime_switch", {})),
        breakout=_build_breakout(data.get("breakout", {})),
        reclaim_mr=_build_reclaim_mr(data.get("reclaim_mr", {})),
        trend_pullback=_build_trend_pullback(data.get("trend_pullback", {})),
        markdown_breakdown=_build_markdown_breakdown(data.get("markdown_breakdown", {})),
        portfolio_risk=_build_portfolio_risk(data.get("portfolio_risk", {})),
    )
    settings.validate()
    return settings
