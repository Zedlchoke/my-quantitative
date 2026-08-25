# V8X novelty and independence memo — H-XSECT-REVERSAL-BREADTH-{CRYPTO,EQUITY}-v1

Author: A6 (spec/preregistration owner). Drafted 2026-08-25, blind to all V8
core results (no `results/portfolio_v8`, partial logs, metrics, or verdicts
read). Frozen with `research/audits/v8x/v8x_spec_freeze.json` per PLAN §8:
specs/selection rules/hashes must freeze **before the first scored V8 core
artifact**, else `V8X_PREREG_WINDOW_MISSED`.

Question under test: do the two NEW breadth cohorts — top-10 Binance USD-M
crypto by a deterministic pre-performance volume rule (`CRYPTO_USDM_1Y_10`)
and a frozen ten-stock US large-cap basket (`US_EQUITY_SPOT_1Y_10`) — show
weekly cross-sectional reversal over one year of data, each under its own
clock/cost/accounting contract?

## Distinctness vs H-XSECT-REVERSAL-v2 (the V8 core prereg)

| Dimension | H-XSECT-REVERSAL-v2 (V8 core) | V8X breadth cohorts | Verdict |
|---|---|---|---|
| Universe | Fixed six alts (SOL/BNB/XRP/DOGE/LINK/ADA), frozen by hand before performance | Crypto: exactly 10 by rule-based top-10 median-quote-volume ranking (accepted AND rejected sets recorded); Equity: frozen 10-stock basket + SPY benchmark | **DISTINCT** |
| Data span | ~2 years common intersection (2024-08→2026-08) | One-year common intersection ending ≤2026-08-21 | **DISTINCT** |
| Asset class / clock | Crypto only, Monday 00:00 UTC, next completed 15m fill | Cohort E uses official US regular-session calendar, close-signal → next-open fill; explicitly NOT the crypto clock | **DISTINCT** |
| Accounting | Native crypto funding | Equity cohort: NO funding; dividends/splits/borrow accounted separately with raw-vs-adjusted reconciliation | **DISTINCT** |
| Trial namespace | `XSECT-WREV-*` / `XSECT-WMOM-7D-CONTROL` | `V8X-C-WREV-*` / `V8X-C-WMOM-7D-CONTROL` and `V8X-E-*` twins | **DISTINCT** |
| Outcome ceiling | Up to `V8_LOCK_FOR_FUTURE_S1` under full hard/statistical gates | Hard-capped at `*_EXPLORATORY` / `MECHANISM_SCREEN_NON_EXECUTABLE`; never S1/live | **DISTINCT** |

What is shared is protocol scaffolding only (rank mechanics family,
3D/7D/14D lookbacks, bottom-2/top-2 legs, gross 0.80 net 0, fee 0.0005,
3-fold chronological split, 7-day purge/embargo, negative control) — copied
verbatim from PLAN §5.1/§9/§10 as required, not invented here. The PLAN
itself forbids "adding symbols to `H-XSECT-REVERSAL-v2`": nothing in these
cohorts modifies the v2 candidate/hypothesis/status bytes, its universe, or
its verdict surface. No symbol from either breadth cohort migrates into the
frozen six-alt core.

## Distinctness vs V6/V7 families

- **H-XSECT-FUNDING-CARRY-v1 (V6):** ranks purely on trailing settled
  funding; no past-return formation term. Breadth cohorts rank purely on
  multi-session price returns. Different ordering variable ⇒ different
  portfolios on the same dates.
- **H-XSECT-FUND-PRICE-DIVERGENCE-v1 (V7):** two-term spread score
  (price-return percentile minus funding percentile) on a daily clock.
  Breadth cohorts use a single-term pure-reversal rank on weekly/session
  clocks. Categorically different signal construction.

## Statistical separation commitments (PLAN §11.2)

Separate initial capitals, ledgers, cost models, calendars and scorecards
per cohort; DSR counts global search history but estimates within comparable
return cohorts; PBO for crypto excludes equities and vice versa; no
crypto+equity PnL aggregation presented as diversification; side-by-side
reporting is descriptive only and never creates a combined PASS. One-year
breadth outcomes are exploratory and are not pooled with the V8 two-year
six-alt PBO cohort.

## Independence declaration

The six preregistered files hashed in `v8x_spec_freeze.json`
(`candidate.yaml`, `hypothesis.md`, `status.yaml` × both cohorts) were
authored by A6 in worktree `a6-contract-golden` BEFORE any scored V8 core
artifact existed. No V6/V7/V8 performance output was read or used to choose
universes, lookbacks, costs, folds, or outcome caps; universe selection is
deferred to A8/A9 executing the frozen rules performance-blind. Any
post-freeze diff to those files invalidates this window
(`V8X_PREREG_WINDOW_MISSED`).

```text
NOVEL_MATERIAL_DISTINCT_AND_INDEPENDENT
```
