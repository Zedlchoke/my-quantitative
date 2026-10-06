# 00 — Master Research Framework for Futures Contracts

## Objective
Use this framework to research any futures contract from market mechanics to causal drivers, regime behavior, signal hypotheses, execution constraints, and point-in-time (PIT) backtest design. The goal is not to collect facts; it is to build a chain from **economic cause → observable data → market reaction → testable signal → executable strategy**.

## 1. Foundation: understand what is actually being traded
Answer before any strategy work:

1. What is the underlying economic exposure?
2. Who are the natural hedgers, speculators, market makers, and arbitrageurs?
3. What exchange lists the contract and what are the trading hours?
4. What are contract size, tick size, tick value, currency denomination, margin mechanics, and settlement type?
5. What months are listed? Which expiries are normally liquid?
6. When does liquidity migrate from front month to next month?
7. Is price behavior dominated by cash-market arbitrage, storage/carry, macro expectations, seasonality, or order flow?
8. Which session matters most: Asia, Europe, US cash open, settlement, or overnight?
9. Which contract should be considered "tradeable" at each timestamp based on PIT volume/open interest?
10. Which vendor symbols correspond to individual expiries, and how will continuous series be reconstructed reproducibly?

## 2. Causal map
For every proposed driver, force a complete causal chain:

> Source variable → economic mechanism → positioning/liquidity channel → expected price direction → expected horizon → conditions where relation breaks.

Required fields for each driver:
- **Driver**
- **Why it should matter**
- **Expected sign**
- **Lag / horizon**
- **Regime dependency**
- **Observable PIT data source**
- **Confounders**
- **Falsification test**

Never accept "X is correlated with Y" as a complete explanation.

## 3. Driver taxonomy
Research each contract through these buckets:

### Macro
Rates, inflation, growth, labor market, central-bank policy, liquidity, USD, risk appetite.

### Fundamental / physical
Production, inventories, storage, imports/exports, weather, demand, supply disruptions, refinery/industrial usage, harvest cycles where relevant.

### Cross-asset
Related futures, cash indexes, FX, rates, volatility indexes, credit, commodities, sector equities.

### Positioning
CFTC CoT, open interest, dealer positioning where available, options skew/IV, ETF/fund flows, CTA proxies.

### Term structure
Calendar spreads, contango/backwardation, roll yield, basis, convenience yield, carry, curve curvature.

### Microstructure
Spread, depth, volume, order-flow imbalance, session effects, settlement effects, roll-window effects.

### Event-driven
Scheduled reports, macro releases, exchange notices, policy announcements, inventories, earnings/sector data, geopolitical shocks.

## 4. Regime framework
Tag history into regimes before interpreting a signal:

- High vs low realized volatility
- Inflationary vs disinflationary
- Growth expansion vs slowdown/recession
- Tightening vs easing monetary policy
- Strong vs weak USD
- Risk-on vs risk-off
- High vs low inventory/storage
- Contango vs backwardation
- Trending vs mean-reverting
- Crisis vs normal liquidity

For each signal, ask whether edge is stable across regimes or comes from one exceptional period.

## 5. Hypothesis template
Every strategy idea must be written as:

**Hypothesis**  
When [observable PIT condition] occurs, [contract/spread] should [move/revert/trend] over [horizon], because [economic mechanism]. The effect should be strongest when [regime], weakest or reversed when [failure regime].

Then specify:
- Entry condition
- Exit condition
- Holding period
- Direction
- Universe / expiry selection rule
- Roll handling
- Position sizing
- Transaction-cost model
- Invalidation rule

## 6. Required tests
At minimum:

1. Full-sample result
2. Walk-forward / rolling OOS
3. Regime split
4. Year-by-year stability
5. Long vs short contribution
6. Event vs non-event periods
7. Front-month vs deferred contracts
8. Parameter perturbation
9. Entry-delay sensitivity
10. Cost/slippage stress test
11. Alternative roll rule
12. Alternative data source / cross-check where possible
13. Look-ahead audit
14. Survivorship / symbol mapping audit
15. Capacity and turnover review

## 7. PIT data rules
Every external series must record:
- Historical value as known then
- Release timestamp
- Time zone
- Revision/vintage if applicable
- Source
- Earliest timestamp strategy could legally observe it

If only a revised history is available today, treat it as unsuitable for strict PIT backtests unless the strategy explicitly does not depend on revision-sensitive information.

## 8. Futures-specific data rules
Store raw individual contracts and build continuous series yourself.

Minimum fields:
- timestamp
- raw_symbol
- instrument_id
- expiry
- activation/listing timestamp
- OHLCV
- volume
- open interest where available
- settlement where available
- best bid/ask if used
- tick size / multiplier

Maintain explicit roll tables:
- old contract
- new contract
- decision timestamp
- reason for roll
- old/new volume and OI
- raw price gap
- adjustment factor

## 9. Research output standard
Each contract research file should ultimately contain:
1. Market thesis
2. Participant map
3. Driver map
4. Regime map
5. Event calendar
6. Term-structure logic
7. Cross-asset relationships
8. Candidate signals
9. Required datasets
10. Backtest plan
11. Execution/cost model
12. Failure modes
13. Open questions
14. Ranked next experiments

## 10. Stop conditions
Reject or pause a strategy when:
- Edge disappears with realistic costs
- Result is driven by one year/event
- Signal requires revised/non-PIT data
- Roll method materially determines profitability
- Entry timing is unrealistically precise
- Strategy cannot survive reasonable slippage
- Economic mechanism is contradicted by the data
- Out-of-sample behavior is structurally different without a defensible explanation
