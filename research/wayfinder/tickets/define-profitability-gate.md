# Define the profitability gate and benchmark contract

**Type:** research  
**Status:** closed  
**Blocked by:** none

## Question

What exact metrics and thresholds define “hopefully profitable” after fees,
slippage, funding, latency/session effects, and shared-capital constraints?

## Decision needed

Choose the minimum acceptance contract for every candidate: expectancy, PF,
drawdown, stability across folds, benchmark-relative return, and a minimum number
of trades. Decide whether the candidate must beat flat and fixed-notional
buy-and-hold, and whether BTC beta-hedged performance is required for altcoins.

## Evidence to collect

- Existing `NOTES.md` acceptance rules and baseline artifacts.
- A single canonical PnL definition shared by engine, funding audit and WF.
- Stress ranges for maker/taker fees, one-tick versus multi-tick slippage, and
  delayed fills.

## Resolution

Adopt a two-stage gate. Stage A is a cheap, frozen research screen; Stage B is
the promotion/forward-test gate. Passing Stage A never authorizes live trading.
The thresholds below are operating guardrails, not proof that an edge is real.

### Canonical PnL and reporting

- The canonical result is realized closed-position PnL in USDT after commissions,
  modeled slippage, funding cashflows, and explicitly recorded latency/session
  penalties. The same definition must be used by the engine, funding audit, and
  walk-forward report.
- Report position-PnL expectancy/PF and engine return-series metrics (Sharpe,
  drawdown) as separate views. Never compare a PF computed from one definition
  with a PF computed from the other.
- Keep a cost-free diagnostic, but never use it for promotion. Re-run the final
  candidate with one-tick baseline slippage, a declared multi-tick stress, and a
  one-bar delayed-fill stress; fee/slippage assumptions are frozen before the
  run.

### Stage A — frozen screening

All rules, symbols, and parameters are frozen before inspecting the scored
folds. Use at least three chronological folds with warmup outside each OOS
window and no leakage.

- At least 20 closed trades per symbol in the combined screen. A lower-frequency
  exception must be declared before the run and still show at least 10 trades
  per fold; otherwise the result is inconclusive, not a pass.
- Aggregate after-cost expectancy must be positive, and at least 2/3 folds must
  have positive after-cost expectancy.
- Aggregate position-PnL PF must be at least 1.10. If a fold has at least five
  trades, its PF must not be below 0.80. No single fold may contribute more than
  50% of total PnL.
- For a multi-symbol rule, every required symbol must pass the declared gate;
  an average that hides a failing symbol is not a portfolio pass. A per-symbol
  candidate must be labeled as such.

These rules preserve the existing `research/acceptance.py` 2/3-fold and PF 1.10
screen while adding minimum sample size and concentration checks.

### Stage B — promotion and forward-test

Use an untouched holdout or a new rolling OOS period. The current 15-minute
strategies default to the stricter high-frequency sample requirement; a
low-frequency exception is documented before the test.

- High-frequency candidate: at least 100 closed trades total; low-frequency
  exception: at least 40 trades, evidence across at least six folds, and no
  fold contributing more than 50% of PnL.
- After-cost aggregate PF must be at least 1.15 and expectancy positive. The
  risk report must show maximum drawdown no greater than 10% of starting
  capital (and the configured per-trade/daily loss limits must not be violated).
  Sharpe of at least 0.50 is supporting evidence, never a sole pass condition.
- At least four of six weekly/fold observations must have positive expectancy;
  there must not be three consecutive observations with PF below 0.80.
- A candidate must beat the flat benchmark (zero after-cost PnL). Buy-and-hold
  is a contextual benchmark, not a universal hard gate: a strategy that reduces
  exposure can be valuable even when it does not beat a bull-market buy-and-
  hold return, but the comparison must be shown on the same window and
  notional. For altcoins, also report BTC-beta-neutral alpha; raw altcoin PnL
  alone is insufficient.
- Shared-capital replay must remain positive after funding with PF at least 1.10,
  respect gross/concurrency/cluster limits, and keep any one symbol below 40%
  of portfolio PnL or risk contribution. Re-run with +50% fee/slippage and one
  bar delayed fills; failure is rejection or return to the map.
- Before any testnet order, run 6–8 weeks signal-only with locked parameters,
  at least 20 trades when the strategy can reasonably produce them, realized
  slippage/fill no worse than 1.5x the model, and no circuit-breaker violation.
  Any failed condition blocks promotion and live money.

### Benchmark contract

Every report includes, on the identical OOS window and fixed notional:

1. Flat/zero return after costs (the hard minimum benchmark).
2. Long buy-and-hold for long or long/short candidates, and short
   buy-and-hold for short-only candidates; both are descriptive and carry no
   leverage.
3. BTC beta-neutral return/alpha for altcoin candidates, using a frozen beta
   estimation window and the same costs. The hedge ratio is not tuned on the
   scored fold.

Benchmarks are labeled raw and cost-adjusted. They do not replace the
after-cost gate or shared-capital replay.

### Why the gate is conservative

Repeatedly selecting the best backtest can manufacture apparent skill from
noise; White's Reality Check explicitly tests whether a selected model beats a
benchmark after data-snooping concerns ([White, 2000](https://doi.org/10.1111/1468-0262.00152)).
Standard holdouts can also be unreliable when many variants are tried, which is
why the promotion stage requires frozen rules, multiple chronological folds and
an untouched period ([Bailey et al., 2017](https://escholarship.org/uc/item/4w1110bb)).
When the research log contains many tested variants, report a deflated Sharpe
or comparable multiple-testing adjustment rather than presenting the maximum
Sharpe ([Bailey and López de Prado, 2014](https://doi.org/10.2139/ssrn.2460551)).

**Decision:** flat is the hard benchmark; buy-and-hold and BTC-beta-neutral
benchmarks are mandatory context/relative-alpha checks; all promotion gates
use the canonical after-cost PnL and shared-capital replay. The current ETH
and altcoin baseline results remain screening evidence only until an untouched
Stage B period and signal-only run satisfy this contract.
