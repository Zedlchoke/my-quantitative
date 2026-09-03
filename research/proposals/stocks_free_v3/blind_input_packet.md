# STOCKS-FREE-V3 blind input packet (outcome-blind)

Frozen 2026-09-03 by A1. This is the complete permissible input for the three
blind proposal lanes. It contains **no** V2 arm PnL table, **no** per-ETF
performance ranking and **no** winning-period diagnostics — only mechanism-
level lessons, frozen contracts and constraints.

## Market, data, clocks

- Universe: 11 US cash-market ETFs — `SPY XLK XLE XLF XLV XLI XLP XLY XLU XLB
  XLRE` (XLC excluded). Long/cash only; no short leg without separate PIT
  borrow authority. Gross exposure ≤ 1.0, no leverage.
- Available fields: daily raw OHLCV + volume; official split factors; official
  cash distributions; issuer total-return reconstruction inputs;
  `US_EQUITY_REGULAR_V1` regular-session calendar. Provider: the already
  authorized Twelve Data Basic (USD 0) account — no new accounts, no paid
  data, no network fetch during the cycle.
- Forbidden fields: earnings dates/surprise, analyst revisions, borrow/short
  interest, intraday quotes/spreads, fundamentals, institutional flows,
  options/futures.
- PIT clock: features use completed sessions only; a signal from data through
  session T is executable at the **next** session's event.

## Windows

| Window | Range | Notes |
|---|---|---|
| Warmup | 2018-01-02..2018-04-03 | 63 sessions |
| S0 fold 1 | 2018-04-04..2020-09-01 scored (purge 5 sessions) | screening |
| S0 fold 2 | 2020-09-10..2023-02-09 scored (purge 5 sessions) | screening |
| S0 fold 3 | 2023-02-17..2025-07-24 scored (purge 5 sessions) | screening |
| S1 | 2025-08-01..2026-07-31 | **SEALED — never read** |

S0 is a screening window, not untouched OOS.

## Constraints

- Deterministic long/cash target books; explicit CASH leg allowed (CASH never
  counts in tradable-leg turnover; costs charged exactly once).
- Base cost 10 bps/side; stress 2× (20 bps); turnover feasibility ceiling
  6.0× two-way per year, measured schedule-only before any scoring.
- Distributions reinvest via the issuer-TR accounting path; fills at raw
  prices; splits via official factors.

## Benchmarks and incremental alpha

Four benchmarks, frozen before scoring: **flat** (hard), **SPY total return**,
**equal-weight 10-sector ETF total return**, **risk-matched SPY** scaled ex
ante by the arm's frozen gross/vol rule. Incremental mechanism alpha is
strategy after-cost return minus the risk-matched benchmark per fold — raw
PnL alone is never evidence; a family cannot pass merely because long equity
beta rose.

## Stage-A gates (preregistered)

After-cost expectancy > 0 · position PF ≥ 1.10 · ≥ 2/3 folds positive · no
fold PF < 0.80 · max fold MDD ≤ 15% · per-arm largest positive-fold share
≤ 50% · no ETF > 35% of positive PnL · sufficient decisions per fold · stress
PnL > 0 and PF ≥ 1.00 · turnover/capacity inside schedule gate · risk-matched
SPY excess positive in ≥ 2/3 folds · incremental mechanism alpha positive ·
neighbour supports the mechanism · control falsifies (opposite alpha sign, or
|control alpha| < 50% of |anchor alpha|) · drop-one-ETF and drop-one-fold
survival · exact reproduction · zero unresolved HIGH/CRITICAL.

Budget: at most **2 families × 3 arms = 6 scored base cells**. Historical
denominator 6 (all prior Stocks observations); stress/drop-one diagnostics
add no trials.

## Mechanism-level lessons from prior cycles

1. Market/sector beta explained nearly all of a top-ranked momentum anchor in
   this cohort/window — the preregistered bottom-ranked control reproduced the
   anchor's expectancy almost exactly, falsifying the ranking mechanism.
2. A trend/defensive rotation failed drawdown and drop-one robustness; a
   bookkeeping artifact changed its label, not its rejection.
3. Positive raw PnL is not edge: both prior families earned positive PnL with
   no incremental alpha over beta.
4. Fold-concentration must use one consistent per-arm definition.
5. Sidecar accounting must equal the canonical harness; CASH is not a tradable
   leg; costs are charged exactly once.
6. Issuer distributions vs provider adjust=all conflicted on five 2025-12-05
   2:1 splits; issuer-TR reconstruction is the accounting authority.

## Forbidden ancestry (veto list — summary)

Cross-sectional relative momentum over sector ETFs (any variant) ·
time-series trend / SMA / EMA / vol-targeted defensive rotation (any variant)
· selected-ETF rescue · long-SPY/sector-beta-only results · earnings /
fundamentals / borrow / institutional-flow / quote-spread mechanisms without
current PIT data · indicator grids without a distinct economic mechanism ·
anything needing new accounts, paid data or network fetch. Full inventory:
`research/control/stocks_free_v3_run/forbidden_family_inventory.json`.

## What every proposal must specify

Primary-source claim and ETF-market mechanism · expected counterparty and
falsifiable expected sign · required fields and PIT availability · universe,
formation, holding, decision and execution clocks · long/cash target
construction and cash semantics · turnover/capacity/cost/distribution
handling · expected behaviour vs all four benchmarks · anchor + theoretically
justified neighbour + causal negative control · incremental mechanism test
separating alpha from beta · drop-one expectations · exact falsification rule
and implementation estimate · ancestry comparison (not a rescue).

Priority search spaces (not mandatory): month-end/quarter-end rebalancing
seasonality · overnight vs intraday return decomposition · market-adjusted
idiosyncratic shock reversal · sector dispersion/breadth transitions · daily
volume/liquidity seasonality · volatility-event recovery.

**Hard rule:** proposal agents compute no returns, PnL, PF, Sharpe, rankings
or correlations on the scored S0 window. Proposals are documents only.
