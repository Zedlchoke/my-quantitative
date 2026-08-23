"""Live-guard regression tests (A3, sprint 24h).

Mission: prove that no path — YAML config, CLI flag, env var, post-load
mutation, or strategy-level shortcut — can lead to real-money live trading
while ``enable_trading`` is false everywhere.

Guard layers audited (see research/audit_live_guards.md):
  L1  LiveSettings.__post_init__      -> LIVE + enable_trading raises
  L2  load_live_config                -> YAML default enable_trading=False,
                                         environment uppercased
  L3  main.cmd_live / _run_live       -> exec client wired only when trading;
                                         API keys required when trading
  L4  strategy_factory.build_strategy -> forwards enable_trading to config
  L5  BaseFuturesStrategy             -> _submit_entry/_submit_exit/on_stop
                                         all gated by config.enable_trading

Known holes are documented loudly at the bottom of this module and in
research/audit_live_guards.md. Production code was NOT modified.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from config.settings import LiveSettings
from config.settings import ResearchSettings
from config.settings import load_live_config

REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_CONFIGS = sorted((REPO_ROOT / "config").glob("live*.yaml"))


# --------------------------------------------------------------------------- #
# L1/L2: shipped configs + settings construction
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("config_path", LIVE_CONFIGS, ids=lambda p: p.name)
def test_shipped_live_configs_have_trading_disabled(config_path):
    """Every shipped live*.yaml must load clean and be signal-only."""
    settings = load_live_config(config_path)
    assert settings.enable_trading is False


def test_signal_only_on_live_venue_cannot_be_flipped(tmp_path):
    """live_tradfi_spy_qqq.yaml ships environment=LIVE (data-only).

    Prove the guard catches any attempt to enable execution on that config.
    """
    src = (REPO_ROOT / "config" / "live_tradfi_spy_qqq.yaml").read_text("utf-8")
    flipped = re.sub(r"enable_trading:\s*false", "enable_trading: true", src)
    assert flipped != src
    cfg = tmp_path / "flipped.yaml"
    cfg.write_text(flipped)
    with pytest.raises(ValueError, match="LIVE execution is disabled"):
        load_live_config(cfg)


def test_live_environment_with_trading_raises_at_construction():
    """L1: the hard guard blocks LIVE execution outright."""
    with pytest.raises(ValueError, match="LIVE execution is disabled"):
        LiveSettings(environment="LIVE", enable_trading=True)


@pytest.mark.parametrize(
    ("raw_yaml", "expected"),
    [("enable_trading: true\n", True), ("enable_trading: false\n", False),
     ("enable_trading: null\n", False), ("environment: TESTNET\n", False)],
)
def test_load_live_config_bool_coercion_for_real_booleans(tmp_path, raw_yaml, expected):
    """Real YAML boolean/null values parse as expected; missing key => False.

    NOTE: quoted string scalars like ``"false"`` are a known footgun — see
    HOLE H2 at the bottom of this file and research/audit_live_guards.md.
    """
    cfg = tmp_path / "c.yaml"
    cfg.write_text(raw_yaml)
    assert load_live_config(cfg).enable_trading is expected


def test_load_live_config_rejects_live_env_with_trading(tmp_path):
    """End-to-end: a user-edited YAML asking for LIVE execution cannot load."""
    cfg = tmp_path / "live_danger.yaml"
    cfg.write_text("environment: LIVE\nenable_trading: true\n")
    with pytest.raises(ValueError, match="LIVE execution is disabled"):
        load_live_config(cfg)


def test_load_live_config_missing_keys_default_to_safe_values(tmp_path):
    """An empty/minimal YAML must land on signal-only TESTNET."""
    cfg = tmp_path / "empty.yaml"
    cfg.write_text("{}\n")
    settings = load_live_config(cfg)
    assert settings.enable_trading is False
    assert settings.environment == "TESTNET"


# --------------------------------------------------------------------------- #
# Bypass attempt 1: environment variables
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "env_name",
    [
        "ENABLE_TRADING",
        "TRADING_ENABLED",
        "ENABLE_LIVE_TRADING",
        "ENVIRONMENT",
        "BINANCE_ENVIRONMENT",
        "NAUTILUS_ENVIRONMENT",
        "LIVE",
    ],
)
def test_env_vars_cannot_enable_trading(tmp_path, monkeypatch, env_name):
    """No env var feeds into load_live_config; flipping them changes nothing."""
    monkeypatch.setenv(env_name, "true")
    monkeypatch.setenv("BINANCE_API_KEY", "fake-key")
    monkeypatch.setenv("BINANCE_API_SECRET", "fake-secret")
    cfg = tmp_path / "c.yaml"
    cfg.write_text(yaml.safe_dump({"environment": "TESTNET"}))
    settings = load_live_config(cfg)
    assert settings.enable_trading is False
    assert settings.environment == "TESTNET"


def test_api_keys_alone_do_not_enable_trading(tmp_path, monkeypatch):
    """Presence of API keys must not flip the switch (only YAML can)."""
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_API_SECRET", "s")
    cfg = tmp_path / "c.yaml"
    cfg.write_text("{}\n")
    assert load_live_config(cfg).enable_trading is False


# --------------------------------------------------------------------------- #
# Bypass attempt 2: post-load mutation of the frozen settings object
# --------------------------------------------------------------------------- #
def test_frozen_settings_block_post_load_mutation():
    settings = load_live_config(REPO_ROOT / "config" / "live.yaml")
    with pytest.raises(dataclasses.FrozenInstanceError):
        settings.enable_trading = True


def test_replace_cannot_sneak_live_execution():
    """dataclasses.replace re-runs __post_init__, so LIVE+trading still raises."""
    base = load_live_config(REPO_ROOT / "config" / "live.yaml")
    with pytest.raises(ValueError, match="LIVE execution is disabled"):
        dataclasses.replace(base, environment="LIVE", enable_trading=True)
    # replace(enable_trading=True) alone stays on the loaded (non-LIVE) venue.
    mutated = dataclasses.replace(base, enable_trading=True)
    assert mutated.environment != "LIVE"


# --------------------------------------------------------------------------- #
# Bypass attempt 3: CLI flags
# --------------------------------------------------------------------------- #
def _live_parser_options():
    from main import build_parser

    parser = build_parser()
    live_action = next(a for a in parser._actions if a.dest == "command")
    live_subparser = live_action.choices["live"]
    return {opt for action in live_subparser._actions for opt in action.option_strings}


def test_cli_live_subcommand_has_no_trading_flag():
    """The live subcommand exposes only --config; no flag can enable trading."""
    options = _live_parser_options()
    assert "--config" in options
    dangerous = [o for o in options if re.search(r"trad|live|exec|env|real|money", o)]
    assert not dangerous, f"CLI flags capable of bypassing guards: {dangerous}"


def test_cli_live_defaults_to_signal_only_config():
    from main import build_parser

    args = build_parser().parse_args(["live"])
    assert args.config == "config/live.yaml"
    settings = load_live_config(Path(args.config))
    assert settings.enable_trading is False


# --------------------------------------------------------------------------- #
# L3: _run_live wiring — exec clients exist iff enable_trading
# --------------------------------------------------------------------------- #
class _FakeTrader:
    def __init__(self):
        self.strategies = []

    def add_strategy(self, strategy):
        self.strategies.append(strategy)


class _FakeTradingNode:
    instances: list["_FakeTradingNode"] = []

    def __init__(self, *, config):
        self.config = config
        self.trader = _FakeTrader()
        self.data_factories: list = []
        self.exec_factories: list = []
        self.built = False
        _FakeTradingNode.instances.append(self)

    def add_data_client_factory(self, name, factory):
        self.data_factories.append((name, factory))

    def add_exec_client_factory(self, name, factory):
        self.exec_factories.append((name, factory))

    def build(self):
        self.built = True

    async def run_async(self):
        return None

    async def stop_async(self):
        return None


@pytest.fixture()
def fake_node(monkeypatch):
    _FakeTradingNode.instances = []
    import main as main_module

    monkeypatch.setattr(main_module, "TradingNode", _FakeTradingNode)
    return _FakeTradingNode


def _signal_only_settings() -> LiveSettings:
    settings = load_live_config(REPO_ROOT / "config" / "live.yaml")
    return dataclasses.replace(settings, run_seconds=1)


async def _drive(settings: LiveSettings) -> None:
    from main import _run_live

    await _run_live(settings)


def test_signal_only_run_wires_no_exec_clients(fake_node, capsys):
    """Entry path proof: enable_trading=false => zero exec clients/factories."""
    import asyncio

    asyncio.run(_drive(_signal_only_settings()))

    assert len(fake_node.instances) == 1
    node = fake_node.instances[0]
    assert dict(node.config.exec_clients or {}) == {}
    assert node.exec_factories == [], "exec client factory leaked into signal-only mode"
    assert node.data_factories, "data clients should still be configured"
    assert node.trader.strategies, "strategies should still be added"
    for strategy in node.trader.strategies:
        assert strategy.config.enable_trading is False
    out = capsys.readouterr().out
    assert "SIGNAL-ONLY" in out
    assert "TRADING" not in out.replace("SIGNAL-ONLY", "")


def test_trading_mode_without_api_keys_raises_before_node_build(fake_node, monkeypatch):
    """L3 key gate: enable_trading=true without keys aborts before any wiring."""
    import asyncio

    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_API_SECRET", raising=False)
    settings = dataclasses.replace(
        load_live_config(REPO_ROOT / "config" / "live.yaml"),
        enable_trading=True,
        run_seconds=1,
    )
    with pytest.raises(ValueError, match="BINANCE_API_KEY"):
        asyncio.run(_drive(settings))
    assert fake_node.instances == [], "node must not be built when keys are missing"


def test_trading_mode_exec_client_only_on_non_live_venues(fake_node, monkeypatch):
    """The switch itself works — but only ever reaches TESTNET/DEMO venues."""
    import asyncio

    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_API_SECRET", "s")
    settings = dataclasses.replace(
        load_live_config(REPO_ROOT / "config" / "live.yaml"),
        enable_trading=True,
        run_seconds=1,
    )
    assert settings.environment == "TESTNET"

    asyncio.run(_drive(settings))
    node = fake_node.instances[0]
    exec_names = [name for name, _ in node.exec_factories]
    assert exec_names, "sanity: enable_trading=true must wire the exec factory"
    assert node.config.exec_clients.keys(), "exec client config present"
    for name, _cfg in node.config.exec_clients.items():
        env_name = getattr(_cfg.environment, "name", str(_cfg.environment))
        assert env_name in {"TESTNET", "DEMO"}, (
            f"exec client {name} points at {env_name}; real money possible!"
        )


# --------------------------------------------------------------------------- #
# L4/L5: strategy level — the last line of defence
# --------------------------------------------------------------------------- #
def _build_strategy(enable_trading: bool):
    from strategy_base import BaseFuturesStrategyConfig  # noqa: F401
    from strategy_factory import build_strategy

    settings = load_live_config(REPO_ROOT / "config" / "live_eth_mean_reversion.yaml")
    return build_strategy(
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
        enable_trading=enable_trading,
        request_historical_bars=False,
        symbol=settings.market.symbols[0],
    )


def _isolate_strategy(monkeypatch, strategy) -> MagicMock:
    """Patch order-submission surface at the subclass level.

    Nautilus Actor attributes are read-only, so we shadow the inherited
    methods on the concrete (Python-level) strategy class and observe calls.
    """
    calls = {
        "submit_order": MagicMock(),
        "close_all_positions": MagicMock(),
        "cancel_all_orders": MagicMock(),
        "unsubscribe_bars": MagicMock(),
    }
    cls = type(strategy)
    for name, mock in calls.items():
        monkeypatch.setattr(cls, name, mock, raising=True)
    monkeypatch.setattr(cls, "order_factory", MagicMock(), raising=True)
    strategy.portfolio_risk = None
    strategy.instrument = MagicMock(min_quantity=None, min_notional=None)
    strategy.instrument.make_qty.return_value = MagicMock(as_double=lambda: 0.001)
    return calls


def test_strategy_guard_blocks_entry_when_signal_only(monkeypatch):
    from nautilus_trader.model.enums import OrderSide

    strategy = _build_strategy(enable_trading=False)
    calls = _isolate_strategy(monkeypatch, strategy)
    strategy._submit_entry(OrderSide.BUY, close=3000.0, atr=10.0)
    calls["submit_order"].assert_not_called()


def test_strategy_guard_blocks_exit_and_stop_cleanup_when_signal_only(monkeypatch):
    strategy = _build_strategy(enable_trading=False)
    calls = _isolate_strategy(monkeypatch, strategy)
    strategy._submit_exit("test-exit", close=3000.0)
    calls["close_all_positions"].assert_not_called()
    strategy.on_stop()
    calls["close_all_positions"].assert_not_called()
    calls["submit_order"].assert_not_called()


def test_strategy_guard_is_active_when_enabled_contrast_test(monkeypatch):
    """Contrast proof: the same call submits exactly once when trading is on.

    This shows the guard above is the real mechanism (not a broken stub).
    Trading here targets TESTNET/DEMO per settings; real money requires
    environment=LIVE which L1 forbids.
    """
    from nautilus_trader.model.enums import OrderSide

    strategy = _build_strategy(enable_trading=True)
    calls = _isolate_strategy(monkeypatch, strategy)
    strategy._submit_entry(OrderSide.BUY, close=3000.0, atr=10.0)
    assert calls["submit_order"].call_count == 1


def test_all_strategies_route_orders_through_gated_base_helpers():
    """Static proof: no strategy file bypasses the gated submit helpers."""
    gated_files = {"strategy_base.py"}
    offenders: list[str] = []
    for path in sorted(REPO_ROOT.glob("strategy*.py")):
        if path.name in gated_files:
            continue
        src = path.read_text(encoding="utf-8")
        if re.search(r"\b(submit_order|close_all_positions)\s*\(", src):
            offenders.append(path.name)
    assert not offenders, (
        f"{offenders} submit orders directly, bypassing the enable_trading "
        "gate in strategy_base.py — this breaks the last-line guard."
    )


# --------------------------------------------------------------------------- #
# Other entry points: backtests, scripts, research modules
# --------------------------------------------------------------------------- #
def test_backtest_engine_is_simulated_only():
    """backtest/engine.py must never touch live adapters/nodes."""
    src = (REPO_ROOT / "backtest" / "engine.py").read_text(encoding="utf-8")
    assert "BacktestEngine" in src
    for forbidden in ("TradingNode", "BinanceLiveExecClientFactory",
                      "BinanceExecClientConfig", "load_dotenv"):
        assert forbidden not in src, f"live adapter leak in backtest/engine.py: {forbidden}"


def test_only_main_py_references_live_trading_infrastructure():
    """Canary: main.py is the sole module allowed to reference live infra."""
    forbidden_tokens = ("TradingNode", "BinanceExecClientConfig",
                        "BinanceLiveExecClientFactory")
    offenders: list[str] = []
    for path in sorted(REPO_ROOT.rglob("*.py")):
        rel = path.relative_to(REPO_ROOT)
        if rel.parts[0] in {"tests", "__pycache__"} or "__pycache__" in rel.parts:
            continue
        if path.name == "main.py":
            continue
        src = path.read_text(encoding="utf-8", errors="ignore")
        if any(tok in src for tok in forbidden_tokens):
            offenders.append(str(rel))
    assert not offenders, (
        f"New live-trading entry point appeared outside main.py: {offenders}"
    )


def test_weekly_forward_script_never_invokes_live_command():
    src = (REPO_ROOT / "scripts" / "weekly_forward_test.sh").read_text(encoding="utf-8")
    assert "main.py live" not in src
    assert "enable_trading" not in src.lower().replace("#", "")


def test_research_settings_have_no_trading_switch():
    """Research configs structurally cannot carry an enable_trading field."""
    names = {f.name for f in dataclasses.fields(ResearchSettings)}
    assert "enable_trading" not in names
    assert "environment" not in names


# --------------------------------------------------------------------------- #
# KNOWN HOLES — documented loudly, NOT fixed (production code untouched).
# See research/audit_live_guards.md for full reproduction steps.
# --------------------------------------------------------------------------- #
@pytest.mark.xfail(
    reason=(
        "HOLE H1 (audit_live_guards.md): LiveSettings.__post_init__ compares "
        "environment == 'LIVE' exactly, so LiveSettings(environment='live', "
        "enable_trading=True) constructs fine and reaches the real-money path "
        "(main._binance_environment uppercases later). All shipped loaders "
        "upper-case the value first, so YAML/CLI paths are safe today; the hole "
        "only opens for future programmatic construction. DO NOT rely on direct "
        "construction; fix belongs in production code (normalize case in "
        "__post_init__), which A3 is forbidden to touch."
    ),
    strict=False,
)
def test_hole_h1_lowercase_live_bypasses_hard_guard():
    with pytest.raises(ValueError, match="LIVE execution is disabled"):
        LiveSettings(environment="live", enable_trading=True)


@pytest.mark.xfail(
    reason=(
        "HOLE H2 (audit_live_guards.md): load_live_config uses bool(...) on the "
        "YAML value, so a quoted string enable_trading: \"false\" becomes True "
        "and silently enables TESTNET/DEMO execution. Real money stays blocked "
        "because environment=LIVE plus a truthy enable_trading raises in L1, so "
        "impact is limited to unintended paper-trading. Fix belongs in "
        "production code (strict isinstance check), out of A3 scope."
    ),
    strict=False,
)
def test_hole_h2_quoted_string_false_enables_execution(tmp_path):
    cfg = tmp_path / "footgun.yaml"
    cfg.write_text('environment: TESTNET\nenable_trading: "false"\n')
    assert load_live_config(cfg).enable_trading is False  # actually True today


def test_hole_h2_string_false_still_blocked_from_real_money(tmp_path):
    """Damage control for H2: the footgun cannot reach the LIVE venue."""
    cfg = tmp_path / "footgun_live.yaml"
    cfg.write_text('environment: LIVE\nenable_trading: "false"\n')
    with pytest.raises(ValueError, match="LIVE execution is disabled"):
        load_live_config(cfg)
