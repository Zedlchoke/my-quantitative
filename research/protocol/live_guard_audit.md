# LIVE hard-guard audit — A3 (sprint 24h)

Status: **audit only**. Production code (`config/settings.py`, `strategy_*.py`,
`main.py`) was NOT modified per ownership rules. Both P0 holes below are
documented with `xfail(strict=True)` regression tests in
`tests/test_live_guards_sprint.py` so that any production fix flips them to
XPASS and forces removal/update of the xfail marker.

## Audited submission paths (signal-only, `enable_trading=False`)

| # | Path | Gate | Location | Verdict |
|---|------|------|----------|---------|
| 1 | Entry submission `_submit_entry` | early `return` after logging when `not config.enable_trading` | `strategy_base.py:202-203` | BLOCKED (before sizing, order factory, portfolio reservation, `submit_order`) |
| 2 | Exit submission `_submit_exit` | `close_all_positions` only under `if self.config.enable_trading:` | `strategy_base.py:261-266` | BLOCKED |
| 3 | Stop-time flatten `on_stop` | `enable_trading and close_position_on_stop` condition | `strategy_base.py:137-145` | BLOCKED when signal-only |
| 4 | Factory wiring `build_strategy(..., enable_trading=...)` | explicit required kwarg; engine passes `True` for backtests only | `strategy_factory.py:55`, `backtest/engine.py:194` | OK — live node must pass `False` from `LiveSettings` |
| 5 | YAML load `load_live_config` | reads only the YAML file; no `os.environ` access anywhere in `config/settings.py` | `config/settings.py:749-770` | OK — env-var override vectors have no effect (proven by tests) |

## P0 holes confirmed (do NOT ship a "live" session before fixing)

### HOLE-1: case-sensitive environment compare in `LiveSettings.__post_init__`

`config/settings.py:488`: `if self.environment == "LIVE" and self.enable_trading:`
A direct construction `LiveSettings(environment='live', enable_trading=True)`
passes the guard because `'live' != 'LIVE'`. `load_live_config` upper-cases
the YAML value (line 753), so the hole is reachable via direct instantiation
or any code path that builds `LiveSettings` programmatically.

Test: `test_hole1_lowercase_live_environment_bypasses_guard` (xfail strict).

Fix sketch (production owner): compare `self.environment.upper() == "LIVE"`.

### HOLE-2: quoted YAML `enable_trading:"false"` becomes truthy

`config/settings.py:754`: `bool(data.get("enable_trading", False))`.
YAML double-quoted `"false"` loads as Python string `"false"`, and
`bool("false") is True`. A hand-edited live.yaml therefore silently enables
trading on Testnet/Demo.

Test: `test_hole2_quoted_yaml_false_is_truthy` (xfail strict).

Fix sketch (production owner): parse with an explicit bool coercion helper
accepting only real booleans / `{"true","false","1","0","yes","no"}` and
rejecting anything else instead of `bool(...)`.

## Env-var bypass vectors checked (all ineffective today)

`BINANCE_API_KEY`, `BINANCE_API_SECRET`, `BINANCE_ENABLE_TRADING`,
`ENABLE_TRADING`, `TRADING_MODE`, `ENVIRONMENT`, `NAUTILUS_*` were set to
hostile values in tests; both loaders (`load_live_config`,
`load_research_config`) re-read the YAML deterministically and ignore the
environment entirely — settings objects are unchanged. There is no
`os.environ`/`os.getenv` usage in `config/`, `strategy_base.py`,
`strategy_factory.py`.

## Backlog

* **P0** fix HOLE-1 + HOLE-2 in `config/settings.py` (owner: production
  owner via A1 handoff), then flip the two xfail tests to strict passing
  assertions.
* **P1** add a defence-in-depth assertion in the live node startup path
  (`main.py`) refusing `LiveSettings` instances whose resolved
  `enable_trading=True` while `environment.upper() != "TESTNET"` and
  `!= "DEMO"`.
* **P2** property test fuzzing `enable_trading` YAML scalar types
  (`bool`, int, quoted strings) against the loader.
