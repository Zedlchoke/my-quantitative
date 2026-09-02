# S2 A5 — outcome-blind family discovery notes (accounting / costs / borrow lens)

Owner: A5 proposal lane, worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/stocks/s2-prop-a5`,
branch `orca/stocks-s2-prop-a5`, bootstrapped at
`3a00fd7653dd5ff51ca4b9be51b494638bbb6df9` (identity verified before any read:
pwd, HEAD, branch and empty porcelain all matched; re-verified before commit).

## Deliverables

| File | Family | One line |
|---|---|---|
| `research/proposals/stocks/a5_family1.json` / `.md` | `A5-S2-F1-LENDING-CONSTRAINT-PREMIUM` | sector/size-neutral L/S ranked by PIT securities-lending scarcity (fee / utilization), locate-gated, honest borrow + short-dividend-liability ledger |
| `research/proposals/stocks/a5_family2.json` / `.md` | `A5-S2-F2-EXDATE-TAX-CLIENTELE-CAPTURE` | long through ex-date on tax-penalized (ordinary-income / high-yield) payers earning the Elton-Gruber drop shortfall, booked as explicit cash receipt on a raw-price identity with an explicitly liable hedge leg |

Each family: exactly 3 cells (anchor, neighbour, negative_control). Total 6,
matching the A7 audit population of six proposals.

## Discovery rationale (why these two, from the A5 lens)

The A5 module trio (`accounting.py`, `execution.py`, `portfolio.py`) has
exactly the buckets most engines default to zero: `short_borrow_fees`,
`short_dividend_liability`, `cash_dividends`, `rejection_costs`, plus a
fail-closed locate gate and a quote-or-proxy spread with a sqrt-impact cap.
Per the diversity mandate, both families are placed where naive accounting
silently fakes or destroys the effect:

- F1: the ranking observable (borrow fee) IS the dominant cost; a zero-borrow
  replay of the identical ranking is expected to "earn" several points/yr more
  than the honest ledger, so the family carries its own artifact detector
  (falsification condition iv).
- F2: the entire effect is invisible-by-construction on adjusted series and
  naive TR-based hedges drop the short-leg liability; the factory's explicit
  dividend buckets are what make capture a real, cost-burdened cashflow.

Both sit in PLAN §9 priority-space territory (F1 adjacent to sector-neutral
quality-risk via constrained names; F2 is an event-driven defensive
construction) while remaining in the A5 cost/borrow specialty, as directed.

## Literature basis (MODEL_INTERNAL_UNVERIFIED — no network this sprint)

F1: Miller (1977, JF); D'Avolio (2002, JFE 66); Geczy, Musto & Reed (2002,
JFE 66); Nagel (2005, JF); Stambaugh, Yu & Yuan (2012, JFE); Kaplan,
Moskowitz & Sensoy (2013, JF); Blocher, Reed & Van Wesep (2013, JFE);
Drechsler & Drechsler (shorting premium; working paper, venue unverified).
F2: Elton & Gruber (1970, JF); Black & Scholes (1974, JF, clientele);
Kalay (1982, JF); Michaely (1991, JF); Boyd & Jagannathan (1994, JF);
Green & Rydqvist (1999, JFE); Frank & Jagannathan (1998, JFE, no-tax
counterpoint). No DOIs, no verbatim quotes. The post-2003 US drop-ratio
evidence is honestly flagged as thin in the proposals rather than backed by
a possibly-misremembered citation.

## Outcome-blind compliance

- No scored-window PnL, PF, Sharpe, ranking or candidate returns were
  computed anywhere in this sprint; the factory was only read, never driven.
- All cost-drag numbers are analytic consequences of the frozen cost models
  (commission schedule, quote/proxy half-spread, declared slippage, sqrt
  impact with participation cap, `rate*days/360` borrow accrual) applied to
  published magnitudes.
- No files from other proposal lanes (other branches) were read. Only this
  worktree's checked-out A5-relevant assets, PLAN_stocks.md and the lane's
  own S1 audit notes (`research/audits/stocks/s1_a5/notes.md`) were read.

## Eligibility check vs PLAN §9 ineligibility

- Neither family is an indicator/lookback/threshold grid: each has one
  mechanism and three theory-linked arms; F2's yield floor is a fixed
  universe-definition parameter, not a searched threshold.
- Neither is a rescue of the rejected crypto families (M01 aggressor-flow
  absorption, funding-carry, weekly reversal): each differs on all four
  required axes — observable, counterparty, clock, causal control — as
  tabulated in the `eligibility` blocks of both JSONs.

## Data readiness (honest)

- Synthetic-fixture factory: both families are implementable NOW — locate/
  fee records, `DividendEvent`, quotes, halt/session flags, ADV, splits are
  first-class fixture inputs of the existing modules.
- Real data: BLOCKED pending owner-authorized entitlement. F1 needs a
  securities-finance feed (PIT fee/utilization/locates, recalls), FINRA
  short interest, PIT earnings calendar. F2 needs PIT declared dividends with
  tax character, PIT earnings calendar, ETF borrow. Neither proposal
  authorizes any purchase. Gate posture if entitlement never arrives:
  scored research stays closed per `STOCKS_BLOCKED_DATA_AUTHORITY`.

## Blockers / assumptions passed to A7 / A1

1. F1 is untestable on real data without the securities-finance entitlement;
   if A1 prioritizes families by data readiness alone, F2's fixture path is
   the stronger of the two.
2. F1 recall events are declared as unmodeled (external-validity caveat), not
   silently assumed absent — flagged so A7 can hold the family to that
   declaration.
3. F2's hedged variant depends on ETF borrow entitlement; the unhedged
   fallback is the declared fail-closed behavior, and A7 should check that
   any implementation preserves it.
4. Both falsification rules reference scored outcomes prospectively only;
   computing them before the S3/S4 freeze would violate the outcome-blind
   contract and must be treated as a gate breach.
