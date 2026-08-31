# my-quantitative

Quantitative crypto-futures trading bot built on [NautilusTrader](https://nautilustrader.io).

**Standardised assumptions**

- Exchange / product: **Binance USD-M perpetuals** (multi-symbol, right now, `BTCUSDT`, `ETHUSDT`)
- Position mode: **one-way / netting** (`oms_type: NETTING`)
- Environment: **Testnet / Demo** — **no real money** (LIVE is disabled by a hard guard)
- Strategies (switch with `strategy_type`):
  - `ema_atr` — EMA-ATR trend following (default — do not replace until NOTES.md acceptance)
  - `mean_reversion` — Bollinger + RSI, range filter = VHF + ADX + volume
  - `regime_switch` — trend in trends, mean-reversion in ranges (same range filter)

The USD-M ↔ COIN-M choice is a config switch: change `market.account_type` to
`COIN_FUTURES` (and set `symbols`/`base_currency` accordingly).

## Project layout

```
main.py                      CLI entry point (download / backtest / live)
strategy_base.py             shared futures-strategy base (risk, orders, daily limits)
strategy.py                  EMA-ATR trend strategy
strategy_mean_reversion.py   Bollinger + RSI mean-reversion strategy
strategy_regime_switch.py    regime-switch strategy (trend / mean-reversion)
strategy_factory.py          builds the selected strategy from settings
config/
  settings.py                typed settings dataclasses + YAML loaders
  research.yaml              research config — EMA-ATR (default)
  research_mean_reversion.yaml  research config — mean-reversion
  research_regime_switch.yaml   research config — regime-switch
  live.yaml                  live config (Testnet/Demo)
data/
  catalog.py                 ParquetDataCatalog wrapper (BinanceBar-aware)
  download.py                historical-data download pipeline (multi-symbol)
backtest/
  engine.py                  backtest engine builder (fees + slippage, multi-symbol)
reports/
  performance.py             performance summary + CSV/JSON reports (per symbol)
research/
  optimize.py                parameter grid-search optimizer (parallel, multi-symbol)
  acceptance.py              NOTES.md walk-forward acceptance criteria
regime.py                    VHF + ADX + volume range filter
risk/
  limits.py                  risk limits + daily risk tracker + position sizing
tests/                       unit tests (risk, regime, acceptance)
```

## Research-agent plans and model effort

The governed research roadmaps are:

- `PLAN.md` — V11 crypto-perpetual research;
- `PLAN_stocks.md` — US cash-equity/ETF research;
- `PLAN_forex.md` — G10 spot-FX research.

When **GLM-5.3 Flash** is used for these agents, the project default is:

| Role/task | Reasoning effort |
|---|---|
| A1 controller, worktrees, integration and gates | `high` |
| A7 independent prelaunch/terminal audit | `high` |
| Shared core, PIT/accounting/rollover correctness | `high` |
| Normal isolated implementation lane | `medium` |
| Mechanical manifest/test/status checks | `low` or `medium` |
| `xhigh`/`max`, if the provider exposes it | incident analysis or difficult terminal audit only |

Do not set every agent to `high`: use it where reasoning errors can corrupt
lineage, accounting or authorization. A1 records the requested model and effort
in the worktree manifest. Because GLM is a third-party model, the provider's
actual mapping of `effort` must be measured; an unsupported or unverified
mapping is reported explicitly, never assumed.

Worktree and machine-wide concurrency rules remain authoritative in the three
PLAN files. Model effort does not relax scientific gates, ownership, trial
budgets, S1 isolation or the prohibition on unapproved live/paper execution.

### Claude Code project toolkit

The repository includes eight project skills, three bounded agents and a
destructive-command guard under `.claude/`. `CLAUDE.md` is the always-on
operating contract.

Validate the setup:

```bash
.venv/bin/python .claude/scripts/validate_claude_setup.py
```

Start a controller only from its already verified integration worktree:

```bash
cd /Users/hoangminhlong/my-quantitative/.worktrees/stocks/integration
claude --agent a1-controller --effort high

cd /Users/hoangminhlong/my-quantitative/.worktrees/forex/integration
claude --agent a1-controller --effort high
```

Use `implementation-agent` at `medium` in a manifest-assigned lane and
`a7-auditor` at `high` in the assigned audit worktree. Inside Claude Code, the
workflow skills are available as `/repo-intake`, `/worktree-dispatch`,
`/test-router`, `/gate-evidence`, `/pit-data-audit`, `/trial-freeze`,
`/reproduce-reconcile`, and `/agent-handoff`.

Do not launch either A1 until the owner checkout is clean and its PLAN-approved
full bootstrap SHA has been frozen. If a running Claude Code session does not
show newly added agents/skills, restart it once so the new project directories
are discovered.

## Quick start

```bash
pip install -r requirements.txt

# 1. Copy and fill in your Binance TESTNET keys (no real money)
cp .env.example .env

# 2. Download historical bars (all market.symbols) into ./catalog
python main.py download

# 3. Run backtests (fees + slippage) and write reports to ./results/<SYMBOL>/
python main.py backtest
python main.py backtest --config config/research_mean_reversion.yaml
python main.py backtest --config config/research_regime_switch.yaml

# 4. Run live on Testnet in signal-only mode (or set enable_trading: true)
python main.py live

# ETH mean-reversion demo (validated params, conservative risk — see NOTES.md bước 6)
python -m research.oos_validate --config config/research_mean_reversion_eth.yaml
python main.py live --config config/live_eth_mean_reversion.yaml
```

## Parameter optimisation

```bash
# Grid-search strategy parameters, ranked by expectancy (not win rate).
# Bars are cached per symbol and combos run in parallel across CPU cores.
# Cell results are written to results/optimize/cells*.jsonl so you can resume.
python -m research.optimize --config config/research.yaml --grid quick
python -m research.optimize --config config/research_mean_reversion.yaml --grid quick
python -m research.optimize --config config/research_regime_switch.yaml --grid quick

# Walk-forward robustness (split the data into N windows)
python -m research.optimize --config config/research_mean_reversion.yaml --grid quick --folds 3

# Control parallelism / noise floor
python -m research.optimize ... --workers 2 --min-trades 20 --top 15
```

Output: `results/optimize/ranking.csv` + `ranking.json`, sorted by
trade-weighted **expectancy**, with profit factor, Sharpe, max drawdown,
`positive_folds`, and `meets_acceptance` (NOTES.md §7). A combo is only
promoted if it has enough trades **and** passes acceptance — not merely a
high win rate. Default configs stay on `ema_atr` until that happens.

## Strategies

### `ema_atr` — EMA-ATR trend following (default)

Enters on a fast/slow EMA crossover filtered by a long-term trend EMA, exits on
the opposite crossover or an ATR trailing stop. Strong in trends, whipsawed in
ranges.

### `mean_reversion` — Bollinger + RSI, frozen stop + take-profit

Enters **long** when price touches the lower Bollinger band and RSI is oversold,
**short** on the upper band + overbought, only in a **range**: VHF ≤ `vhf_max`,
ADX ≤ `adx_max`, and volume ≤ `volume_max_ratio` × volume SMA. Exits on an ATR
stop frozen at entry, or a take-profit at `take_profit_multiple` × that stop.

### `regime_switch` — trend in trends, mean-reversion in ranges

Uses the same VHF + ADX + volume rule to pick the active leg each bar: range →
mean-reversion; otherwise → EMA-ATR trend. The leg that opens a position
manages its own exit, so a regime flip never orphans a position.

## Configuration

`config/research*.yaml` and `config/live.yaml` are intentionally separated so
backtest/data settings can never leak into a live session.

- `market.symbols` — list of traded symbols, e.g. `[BTCUSDT, ETHUSDT, SOLUSDT]`.
- `market` — contract profile (`account_type`, `base_currency`, `oms_type`,
  `leverage`, bar spec). Switch USD-M ↔ COIN-M here.
- `risk` — per-trade and daily risk limits (risk-per-trade, max notional, max
  daily loss, max trades/day, cooldown, ATR stop multiple).
- `strategy` — EMA/ATR periods (used by `ema_atr`).
- `mean_reversion` — Bollinger/RSI + VHF/ADX/volume + stop + take-profit.
- `regime_switch` — trend + mean-reversion legs + the same range filter + stops.
- `strategy_type` — `ema_atr` (default) | `mean_reversion` | `regime_switch`.
- `data` (research) — catalog path, environment, lookback/start/end.
- `backtest` (research) — starting balance, fee model, fill/slippage model.
- `report` (research) — output directory and artifact formats.

### Fees and slippage

Backtests use a **maker/taker fee model** (Binance tier-0: maker 0.02%, taker
0.05%, read from the instrument) plus a configurable **fill model** for slippage:

| `backtest.fee_model` | behaviour                                   |
|----------------------|---------------------------------------------|
| `maker_taker`        | instrument maker/taker rates (default)      |
| `fixed`              | fixed commission (`backtest.fixed_fee`)     |

| `backtest.fill_model`      | behaviour                                        |
|----------------------------|--------------------------------------------------|
| `one_tick_slippage`        | deterministic one-tick adverse fill (default)    |
| `probabilistic`            | probabilistic slippage (`prob_slippage`)         |
| `best_price`               | no slippage                                      |

### Risk management

`risk.limits.RiskLimits` + `risk.limits.DailyRiskTracker` are the single source of
truth for position sizing and daily limits, shared by every strategy, the
backtest report and the live node:

- position quantity = `min(risk_per_trade / ATR_stop_distance, max_notional / price)`
- daily loss, max trades/day and post-loss cooldown are enforced per UTC day

## Notes

- Historical bars are stored as `BinanceBar` in the catalog; `data/catalog.py`
  handles that type directly.
- On Windows, the download pipeline registers the catalog directly to avoid a
  path-encoding issue with spaces in `DataCatalogConfig`.
- Run unit tests: `python -m unittest discover -s tests`
