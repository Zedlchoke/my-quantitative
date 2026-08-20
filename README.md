# my-quantitative

Quantitative crypto-futures trading bot built on [NautilusTrader](https://nautilustrader.io).

**Standardised assumptions**

- Exchange / product: **Binance USD-M perpetuals** (multi-symbol, default `BTCUSDT`, `ETHUSDT`)
- Position mode: **one-way / netting** (`oms_type: NETTING`)
- Environment: **Testnet / Demo** — **no real money** (LIVE is disabled by a hard guard)
- Strategies (switch with `strategy_type`):
  - `ema_atr` — EMA-ATR trend following (default)
  - `mean_reversion` — Bollinger + RSI mean-reversion, tight stop + 1.5R take-profit
  - `regime_switch` — trend in trends, mean-reversion in ranges (VHF-selected)

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
risk/
  limits.py                  risk limits + daily risk tracker + position sizing
```

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
```

## Parameter optimisation

```bash
# Grid-search strategy parameters, ranked by expectancy (not win rate).
# Bars are cached per symbol and combos run in parallel across CPU cores.
python -m research.optimize --config config/research_mean_reversion.yaml --grid quick
python -m research.optimize --config config/research_regime_switch.yaml --grid quick

# Walk-forward robustness (split the data into N windows)
python -m research.optimize --config config/research_mean_reversion.yaml --grid quick --folds 3

# Control parallelism / noise floor
python -m research.optimize ... --workers 2 --min-trades 20 --top 15
```

Output: `results/optimize/ranking.csv` + `ranking.json`, sorted by
trade-weighted **expectancy** across symbols/windows, with profit factor and a
`positive_cells` robustness count. A combo is only useful if it has enough
trades AND positive expectancy across several symbols/windows — not merely a
high win rate.

## Strategies

### `ema_atr` — EMA-ATR trend following (default)

Enters on a fast/slow EMA crossover filtered by a long-term trend EMA, exits on
the opposite crossover or an ATR trailing stop. Strong in trends, whipsawed in
ranges.

### `mean_reversion` — Bollinger + RSI, tight stop + 1.5R take-profit

Enters **long** when price touches the lower Bollinger band and RSI is oversold,
**short** on the upper band + overbought, only while the **VHF** is below
`vhf_max` (ranging market). Exits on a tight ATR stop (1R) or a take-profit at
`take_profit_multiple` x stop distance (reward:risk).

### `regime_switch` — trend in trends, mean-reversion in ranges

Uses **VHF** to pick the active leg each bar: `VHF <= vhf_max` → mean-reversion
leg (Bollinger + RSI, tight stop + 1.5R TP); otherwise → trend leg (EMA-ATR with
trailing stop). The leg that opens a position manages its own exit, so a regime
flip never orphans a position.

## Configuration

`config/research*.yaml` and `config/live.yaml` are intentionally separated so
backtest/data settings can never leak into a live session.

- `market.symbols` — list of traded symbols, e.g. `[BTCUSDT, ETHUSDT, SOLUSDT]`.
- `market` — contract profile (`account_type`, `base_currency`, `oms_type`,
  `leverage`, bar spec). Switch USD-M ↔ COIN-M here.
- `risk` — per-trade and daily risk limits (risk-per-trade, max notional, max
  daily loss, max trades/day, cooldown, ATR stop multiple).
- `strategy` — EMA/ATR periods (used by `ema_atr`).
- `mean_reversion` — Bollinger/RSI/VHF + stop + take-profit (used by `mean_reversion`).
- `regime_switch` — trend + mean-reversion legs + VHF + stops (used by `regime_switch`).
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
- The API keys in `.env` are **testnet** keys. Never put live keys here.
