"""LIVE hard-guard regression tests (A3, sprint 24h).

Proves that with ``enable_trading=False`` (the shipped default in
``config/live.yaml`` and ``config/live_eth_mean_reversion.yaml``) every
reachable order-submission path is blocked, that env-var bypass vectors have
no effect on settings loading, and documents the two known P0 holes from the
audit (see research/protocol/live_guard_audit.md) as strict xfail markers.
"""

from __future__ import annotations

import pytest

from config.settings import LiveSettings, load_live_config, load_research_config
from strategy_factory import build_strategy


LIVE_CONFIGS = ("config/live.yaml", "config/live_eth_mean_reversion.yaml")

STRATEGY_CASES = (
    ("ema_atr", {}),
    ("mean_reversion", {"mean_reversion": None}),
    ("regime_switch", {"regime_switch": None}),
    ("breakout", {"breakout": None}),
    ("reclaim_mr", {"reclaim_mr": None}),
    ("trend_pullback", {"trend_pullback": None}),
    ("markdown_breakdown", {"markdown_breakdown": None}),
)


def _build(strategy_type: str, required):
    from config.settings import (
        BreakoutSettings,
        MarkdownBreakdownSettings,
        MeanReversionSettings,
        MarketSettings,
        ReclaimMeanReversionSettings,
        RegimeSwitchSettings,
        RiskSettings,
        StrategySettings,
        TrendPullbackSettings,
    )

    settings = {
        "mean_reversion": None,
        "regime_switch": None,
        "breakout": None,
        "reclaim_mr": None,
        "trend_pullback": None,
        "markdown_breakdown": None,
    }
    if strategy_type == "mean_reversion":
        settings["mean_reversion"] = MeanReversionSettings()
    elif strategy_type == "regime_switch":
        settings["regime_switch"] = RegimeSwitchSettings()
    elif strategy_type == "breakout":
        settings["breakout"] = BreakoutSettings()
    elif strategy_type == "reclaim_mr":
        settings["reclaim_mr"] = ReclaimMeanReversionSettings()
    elif strategy_type == "trend_pullback":
        settings["trend_pullback"] = TrendPullbackSettings()
    elif strategy_type == "markdown_breakdown":
        settings["markdown_breakdown"] = MarkdownBreakdownSettings()

    return build_strategy(
        MarketSettings(),
        RiskSettings(),
        StrategySettings(),
        strategy_type=strategy_type,
        enable_trading=False,
        request_historical_bars=False,
        symbol="BTCUSDT",
        **settings,
    )


@pytest.mark.parametrize(("strategy_type", "required"), STRATEGY_CASES)
def test_all_strategies_built_signal_only_and_submission_blocked(
    strategy_type, required, monkeypatch
):
    strategy = _build(strategy_type, required)
    assert strategy.config.enable_trading is False

    def _no_order(*args, **kwargs):
        raise AssertionError("submit_order must never be reached when signal-only")

    def _no_close(*args, **kwargs):
        raise AssertionError("close_all_positions must never be reached when signal-only")

    monkeypatch.setattr(strategy, "submit_order", _no_order)
    monkeypatch.setattr(strategy, "close_all_positions", _no_close)

    from nautilus_trader.model.enums import OrderSide

    strategy._submit_entry(OrderSide.BUY, close=100.0, atr=1.0)
    strategy._submit_exit(reason="test", close=100.0)


@pytest.mark.parametrize("config_path", LIVE_CONFIGS)
def test_shipped_live_configs_are_signal_only_testnet(config_path):
    settings = load_live_config(config_path)
    assert settings.enable_trading is False
    assert settings.environment == "TESTNET"
    assert isinstance(settings.run_seconds, int)


def test_env_var_overrides_have_no_effect_on_settings_load(tmp_path, monkeypatch):
    hostile = {
        "BINANCE_ENABLE_TRADING": "true",
        "ENABLE_TRADING": "1",
        "TRADING_MODE": "LIVE",
        "ENVIRONMENT": "LIVE",
        "BINANCE_ENVIRONMENT": "LIVE",
        "BINANCE_API_KEY": "attacker-key",
        "BINANCE_API_SECRET": "attacker-secret",
        "NAUTILUS_ENABLE_TRADING": "true",
    }
    for key, value in hostile.items():
        monkeypatch.setenv(key, value)

    live = load_live_config("config/live.yaml")
    assert live.enable_trading is False
    assert live.environment == "TESTNET"

    eth = load_live_config("config/live_eth_mean_reversion.yaml")
    assert eth.enable_trading is False

    research = load_research_config("config/research_baseline_eth.yaml")
    assert hasattr(research, "market") and research.market.symbols


def test_direct_live_settings_default_is_safe():
    settings = LiveSettings()
    assert settings.environment == "TESTNET"
    assert settings.enable_trading is False


# --------------------------- known P0 holes -------------------------------- #
# Both holes are documented in research/protocol/live_guard_audit.md and are
# NOT fixed here (production files are outside A3 ownership).  xfail(strict)
# means: today they fail; the day production fixes them they XPASS and break
# the suite until these tests are flipped to hard assertions.


@pytest.mark.xfail(strict=True, reason="P0 HOLE-1: case-sensitive 'LIVE' compare")
def test_hole1_lowercase_live_environment_bypasses_guard():
    with pytest.raises(ValueError):
        LiveSettings(environment="live", enable_trading=True)


@pytest.mark.xfail(strict=True, reason="P0 HOLE-2: quoted YAML \"false\" is truthy")
def test_hole2_quoted_yaml_false_is_truthy(tmp_path):
    config = tmp_path / "live_quoted.yaml"
    config.write_text('environment: TESTNET\nenable_trading: "false"\n')
    settings = load_live_config(config)
    assert settings.enable_trading is False
