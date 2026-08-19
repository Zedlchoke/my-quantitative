# my-quantitative

Quantitative crypto-futures trading bot built on [NautilusTrader](https://nautilustrader.io).

**Standardised assumptions**

- Exchange / product: **Binance USD-M perpetual `BTCUSDT-PERP`**
- Position mode: **one-way / netting** (`oms_type: NETTING`)
- Environment: **Testnet / Demo** — **no real money** (LIVE is disabled by a hard guard)
- Strategies (switch with `strategy_type`):
  - `ema_atr` — EMA-ATR trend following (default)
  - `mean_reversion` — Bollinger + RSI mean-reversion with VHF regime filter

The USD-M ↔ COIN-M choice is a single config switch: change `market.account_type`
to `COIN_FUTURES` (and `symbol`/`base_currency` to `BTCUSD`/`BTC`) in the YAML files.

## Project layout

```
main.py                      CLI entry point (download / backtest / live)
strategy_base.py             shared futures-strategy base (risk, orders, daily limits)
strategy.py                  EMA-ATR trend strategy
strategy_mean_reversion.py   Bollinger + RSI mean-reversion strategy
strategy_factory.py          builds the selected strategy from settings
config/
  settings.py                typed settings dataclasses + YAML loaders
  research.yaml              research config — EMA-ATR (default)
  research_mean_reversion.yaml  research config — mean-reversion
  live.yaml                  live config (Testnet/Demo)
data/
  catalog.py                 ParquetDataCatalog wrapper (BinanceBar-aware)
  download.py                historical-data download pipeline
backtest/
  engine.py                  backtest engine builder (fees + slippage)
reports/
  performance.py             performance summary + CSV/JSON reports
risk/
  limits.py                  risk limits + daily risk tracker + position sizing
```

## Quick start

```bash
pip install -r requirements.txt

# 1. Copy and fill in your Binance TESTNET keys (no real money)
cp .env.example .env

# 2. Download historical bars into ./catalog
python main.py download

# 3. Run a backtest (fees + slippage) and write reports to ./results
python main.py backtest

# 3b. Backtest the mean-reversion strategy instead
python main.py backtest --config config/research_mean_reversion.yaml

# 4. Run live on Testnet in signal-only mode (or set enable_trading: true)
python main.py live
```

## Strategies

### `ema_atr` — EMA-ATR trend following (default)

Trend strategy: enters on a fast/slow EMA crossover filtered by a long-term trend
EMA, exits on the opposite crossover or an ATR trailing stop. Strong in trends,
whipsawed in ranges.

### `mean_reversion` — Bollinger + RSI with VHF regime filter

Range strategy: enters **long** when price touches the lower Bollinger band and
RSI is oversold, **short** when it touches the upper band and RSI is overbought,
but only while the **Vertical Horizontal Filter (VHF)** is below `vhf_max`
(i.e. the market is ranging, not trending). Exits on a revert to the middle band
or an ATR stop. Complements `ema_atr` — the two cover both market regimes.

Select the strategy with `strategy_type: ema_atr | mean_reversion` and tune the
`mean_reversion:` block in `config/research_mean_reversion.yaml`.

## Configuration

`config/research.yaml` and `config/live.yaml` are intentionally separated so
backtest/data settings can never leak into a live session (and vice-versa).

- `market` — contract profile (`account_type`, `symbol`, `base_currency`,
  `oms_type`, `leverage`, bar spec). This is where you switch USD-M ↔ COIN-M.
- `risk` — per-trade and daily risk limits (risk-per-trade, max notional, max
  daily loss, max trades/day, cooldown, ATR stop multiple).
- `strategy` — EMA/ATR periods and history depth (used by `ema_atr`).
- `mean_reversion` — Bollinger/RSI/VHF parameters (used by `mean_reversion`).
- `strategy_type` — `ema_atr` (default) or `mean_reversion`.
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
