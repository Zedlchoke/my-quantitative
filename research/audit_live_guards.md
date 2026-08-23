# Audit — Live real-money guard (`enable_trading`) — A3, 2026-08-23

**Scope:** prove that no path leads to real-money live trading while
`enable_trading` is `false`. Production code was **not modified**; this audit
adds only tests (`tests/test_live_guards.py`) and this document.

**Verdict summary:** all shipped entry paths are blocked from real money.
Two weaknesses found (H1, H2) — H1 is a genuine programmatic guard hole,
H2 is a config footgun limited to Testnet/Demo impact.

---

## 1. Guard architecture (defence in depth)

| Layer | Location | Mechanism |
|-------|----------|-----------|
| L1 | `config/settings.py:487-493` (`LiveSettings.__post_init__`) | Raises `ValueError` if `environment == "LIVE"` **and** `enable_trading` — LIVE execution is unconditionally forbidden at object construction |
| L2 | `config/settings.py:749-770` (`load_live_config`) | YAML is the only source of `enable_trading`; default `False`; environment upper-cased before the L1 check |
| L3 | `main.py:150-286` (`_run_live`, `cmd_live`) | Exec client + `BinanceLiveExecClientFactory` wired **only** when `enable_trading`; requires `BINANCE_API_KEY`/`BINANCE_API_SECRET` when trading; prints mode banner |
| L4 | `strategy_factory.py:37-74` | Forwards `enable_trading` into every strategy config |
| L5 | `strategy_base.py:202, 261, 137-141` | `_submit_entry`, `_submit_exit`, `on_stop` cleanup all gated by `config.enable_trading` — even with an exec client attached, signal-only strategies never submit |

## 2. Paths audited — verdict per path

| # | Path | Verdict | Evidence / test |
|---|------|---------|-----------------|
| P1 | `python main.py live` → `cmd_live` → `load_live_config(config/live.yaml)` | **BLOCKED** — ships `enable_trading: false`, TESTNET | `test_shipped_live_configs_have_trading_disabled`, `test_cli_live_defaults_to_signal_only_config` |
| P2 | `config/live_eth_mean_reversion.yaml` | **BLOCKED** — signal-only TESTNET | same parametrized test |
| P3 | `config/live_tradfi_spy_qqq.yaml` (`environment: LIVE`, data-only) | **BLOCKED** — signal-only; flipping `enable_trading: true` raises via L1 | `test_shipped_live_configs_have_trading_disabled`, `test_signal_only_on_live_venue_cannot_be_flipped` |
| P4 | CLI flags on `live` subcommand | **BLOCKED** — only `--config` exists; no flag can flip trading/env | `test_cli_live_subcommand_has_no_trading_flag` |
| P5 | Env-var override (`ENABLE_TRADING`, `TRADING_ENABLED`, `ENVIRONMENT`, `BINANCE_ENVIRONMENT`, …) | **BLOCKED** — no env var feeds settings; only API keys come from env | `test_env_vars_cannot_enable_trading`, `test_api_keys_alone_do_not_enable_trading` |
| P6 | `.env` file via `python-dotenv` (`main.py:280`) | **SAFE** — `.env.example` defines only `BINANCE_API_KEY`/`SECRET`; keys alone never enable trading (see P5). Note: worktree `.env` symlink currently dangling → no keys load at all | grep of `.env.example`; P5 tests |
| P7 | Post-load mutation (`settings.enable_trading = True`) | **BLOCKED** — frozen dataclass raises `FrozenInstanceError` | `test_frozen_settings_block_post_load_mutation` |
| P8 | Config merge after load via `dataclasses.replace(...)` | **BLOCKED for LIVE** — `replace` re-runs `__post_init__`, so `replace(environment="LIVE", enable_trading=True)` raises. (`replace(enable_trading=True)` stays on non-LIVE venue = Testnet by design) | `test_replace_cannot_sneak_live_execution` |
| P9 | YAML with `environment: LIVE` + `enable_trading: true` | **BLOCKED** — load raises | `test_load_live_config_rejects_live_env_with_trading` |
| P10 | Missing/empty YAML keys | **SAFE** — defaults are `TESTNET` / `enable_trading: False` | `test_load_live_config_missing_keys_default_to_safe_values` |
| P11 | Strategy-level bypass (direct order submission) | **BLOCKED** — all 7 strategy modules route through gated `_submit_entry`/`_submit_exit` in `strategy_base.py`; static scan finds zero direct `submit_order`/`close_all_positions` calls outside base | `test_all_strategies_route_orders_through_gated_base_helpers`, `test_strategy_guard_blocks_entry_when_signal_only`, `test_strategy_guard_blocks_exit_and_stop_cleanup_when_signal_only`, contrast: `test_strategy_guard_is_active_when_enabled_contrast_test` |
| P12 | `python main.py backtest` / research configs | **NOT A LIVE PATH** — uses in-process `BacktestEngine` with simulated venue; no network adapters. Research settings structurally have no `enable_trading` field | `test_backtest_engine_is_simulated_only`, `test_research_settings_have_no_trading_switch` |
| P13 | Other modules spinning up a node | **NONE FOUND** — canary test asserts only `main.py` references `TradingNode` / Binance exec client classes repo-wide | `test_only_main_py_references_live_trading_infrastructure` |
| P14 | `scripts/weekly_forward_test.sh` | **SAFE** — download + OOS validation only; never invokes `live` | `test_weekly_forward_script_never_invokes_live_command` |
| P15 | `research/*` modules (`oos_validate`, `scan_matrix`, `optimize`, …) | **SAFE** — backtests/reports only; covered by P12/P13 canary | P13 test |

## 3. HOLES FOUND (documented loudly — production code NOT touched)

### H1 — Lowercase `"live"` environment string bypasses the hard guard (programmatic)

- **Where:** `config/settings.py:488` — `if self.environment == "LIVE" and self.enable_trading:` compares the exact uppercase string.
- **Reproduction:**
  ```python
  from config.settings import LiveSettings
  s = LiveSettings(environment="live", enable_trading=True)   # NO ValueError!
  # main._run_live then uppercases via _binance_environment() ->
  # BinanceEnvironment.LIVE + exec client + trading-enabled strategies
  ```
- **Impact:** real-money path reachable **only via direct programmatic construction**. All shipped loaders are safe because `load_live_config` does `.upper()` *before* construction (P2–P9). CLI/YAML cannot trigger it today.
- **Risk:** any future code that builds `LiveSettings` directly with a mixed-case env string silently re-opens real-money trading.
- **Suggested fix (for A1/owner):** normalize case inside `__post_init__` (e.g. compare `self.environment.upper()`), or validate via enum.
- **Test:** `test_hole_h1_lowercase_live_bypasses_hard_guard` (marked `xfail`).

### H2 — Quoted-string YAML values enable execution instead of disabling it (footgun)

- **Where:** `config/settings.py:754` — `enable_trading=bool(data.get("enable_trading", False))`.
- **Reproduction:**
  ```yaml
  environment: TESTNET
  enable_trading: "false"     # quoted string
  ```
  → `bool("false") == True` → execution enabled unintentionally.
- **Impact:** limited to **Testnet/Demo paper-trading** — real money still blocked because `environment: LIVE` combined with any truthy value raises in L1 (verified: `test_hole_h2_string_false_still_blocked_from_real_money`).
- **Risk:** an operator who "quotes to be safe" gets the opposite of what they wrote.
- **Suggested fix (for A1/owner):** strict type check (`isinstance(value, bool)`) or reject non-bool scalars.
- **Tests:** `test_hole_h2_quoted_string_false_enables_execution` (xfail), `test_hole_h2_string_false_still_blocked_from_real_money` (passing damage-control).

## 4. Additional observations

1. **Worktree `.env` symlink is dangling** (target `/Users/hoangminhlong/my-quantitative/.env` missing). Effect: `load_dotenv()` loads nothing → even a hand-edited `enable_trading: true` run aborts at the L3 key check (`ValueError: ... BINANCE_API_KEY ...`). Accidentally safe here, but restore the symlink for intended Testnet workflows.
2. `backtest/engine.py:194,332` sets `enable_trading=True` for strategies — intentional and safe: venue is an in-process simulated `BacktestEngine`, no network client exists there.
3. The single source of truth for "may submit orders" is `BaseFuturesStrategyConfig.enable_trading`; everything upstream funnels into it. Keeping the static-scan canary tests (P11/P13) in CI prevents new ungated submission sites or second node constructors.

## 5. How to re-run

```bash
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests/test_live_guards.py -v
```

Expected: all green, exactly 2 xfailed (H1, H2).
