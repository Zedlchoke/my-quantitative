# SFV3-A6-TOM-SETTLE — Turn-of-month settlement-flow seasonality in sector ETFs

Lane: A6 (blind proposal lane 3), STOCKS-FREE-V3 Phase D1.
Frozen 2026-09-03 from `STOCKS_FREE_V3_BLIND_PACKET_SHA`. Document only —
no returns, PnL, PF, Sharpe, rankings or correlations were computed; no market
data, no scored outcomes, and no other lane's files were opened.

## 1. Family identity, primary source, and ETF-market mechanism

- **family_id:** `SFV3-A6-TOM-SETTLE`
- **Mechanism class:** calendar-conditioned settlement/inflow seasonality
  (priority search space: month-end/quarter-end institutional rebalancing
  seasonality).

**Primary-source claim.** Joseph Ogden (1990), "Turn-of-Month Evaluations of
Liquid Profits and Stock Returns", *Journal of Finance* 45(5). Ogden documents
that a large share of monthly equity returns is concentrated in the
turn-of-the-month (TOM) days and attributes the concentration to a
settlement-cycle liquidity channel: cash from salaries, dividends and interest
arrives around the turn of the month and is reinvested, producing predictable,
non-informational buy pressure concentrated in the last sessions and the first
sessions of each month. Corroborating primary sources: Lakonishok & Smidt
(1988), "Are Seasonal Anomalies Real? A Fifty-Year Perspective", *Review of
Financial Studies* 1(4) (TOM return concentration is a long-run regularity,
not a sample artifact); Lakonishok, Shleifer, Thaler & Vishny (1991), "Window
Dressing by Pension Fund Managers", *American Economic Review* 81(2)
(institutional rebalancing activity is concentrated at period ends). These are
priors on mechanism, not profitability evidence.

**ETF-market mechanism story.** The monthly settlement clock transmits to the
sector-ETF cohort through creation/redemption mechanics: defined-contribution
contributions and model-portfolio / rebalancing programs fund ETF creations
around month turns, and institutional programs rebalance at period ends. This
flow is *scheduled*, not information-motivated: it arrives whether or not it
moves the price. Liquidity providers and authorized participants absorb it and
charge a premium, which in equilibrium shows up as a concentration of the
cohort's total return in a small, pre-declared set of sessions around each
month turn. The family claims the concentration itself, not the market's
average drift.

## 2. Expected counterparty and falsifiable expected sign

- **Counterparty:** month-turn scheduled buyers — retirement-plan contribution
  deployment, model-portfolio and institutional rebalancing programs, and
  settlement-motivated reinvestment. They accept short-term adverse prices
  because their transact clock is set by a settlement/compliance calendar:
  holding idle cash or missing a rebalance date costs them more than the
  price concession. The other active side is the liquidity provider/AP, who
  demands compensation for absorbing one-sided scheduled flow.
- **Falsifiable expected sign:** the equal-weight 11-ETF basket's per-session
  issuer-TR return during pre-declared TOM window sessions exceeds its
  per-session return outside the window; equivalently, the arm's
  **risk-matched incremental alpha is positive** (per fold and on average).
  If TOM sessions carry the same per-session beta compensation as any other
  session, the mechanism is absent and the family must die (see section 11).

## 3. Required fields and PIT availability

Only already-authorized fields are used:

- daily raw OHLCV (closes for marks; nothing else consumed);
- official split factors and official cash distributions (issuer-TR
  accounting path — the accounting authority per packet lesson 6);
- `US_EQUITY_REGULAR_V1` regular-session calendar. Window membership is a
  pure function of the published exchange calendar, which is known in
  advance of every session: **PIT availability is exact** — no estimation,
  no in-sample statistics, no lookahead surface exists.

No earnings, analyst, borrow, flow, quote/spread, options or fundamental
fields are used. Nothing needs a new account, paid data, or network fetch.

## 4. Universe, formation, holding, decision and execution clocks

- **Universe:** all 11 cohort ETFs `SPY XLK XLE XLF XLV XLI XLP XLY XLU XLB
  XLRE` as one equal-weight basket. Long/cash only; no short leg.
- **Formation:** none — the state variable is the calendar itself.
  **TOM window** for month M = the last 3 regular sessions of M plus the
  first 2 regular sessions of M+1 (5 sessions). Ordinals are counted on the
  regular-session calendar, never on calendar dates, so holiday-thinned
  months are handled without special cases.
- **Decision clock:** at the close of completed session T, the target book for
  the fill at T+1 is fully determined: TOM book if session T+1 is a window
  session, BASE book otherwise. Completed-session PIT; nothing uses session
  T+1's own data.
- **Execution clock:** fills at the **close of session T+1** (the canonical
  V3 factory fill event; the fill day earns no same-day return on the new
  weights). Because the calendar is known a session ahead, the book is
  always pre-positioned exactly one session before each gross transition.
- **Holding:** window membership. The book alternates between exactly two
  books, 24 transitions per year (12 window entries + 12 window exits).
  A window that straddles a fold boundary or purge gap loses those scored
  sessions; no compensation trades are made.

## 5. Long/cash target construction and cash semantics

Two frozen books, no other states:

- **TOM book:** each of the 11 ETFs at weight `0.50/11`; gross `0.50`.
- **BASE book:** each of the 11 ETFs at weight `0.30/11`; gross `0.30`.
- **CASH** is the residual to 1.0, is never a tradable leg, never counts in
  turnover, and costs are charged exactly once per fill (canonical
  `factory.value_book` semantics). No intra-window re-equalization: leg
  weights drift between the 24 scheduled transitions and are never traded.

**Why gross is 0.30–0.50 (reasoned constants):** (i) the turnover ceiling —
a full 1.0/0.0 monthly cycle costs 24.0 two-way per year, 4x over the 6.0x
gate; a 0.20 delta across 24 transitions costs 4.80 two-way per year, inside
the gate with 20% margin; (ii) fold-1 drawdown realism — the cohort's worst
drawdowns are systemic, and a book whose gross exceeds ~0.5 through a
Feb–Mar-2020-class episode cannot plausibly satisfy the frozen max-fold-MDD
<= 15% gate; (iii) the incremental-alpha test matches the arm's own gross
path, so lower gross does not dilute the mechanism test, it only lowers
absolute PnL. The constants are fixed ex ante; no grid, no tuning.

## 6. Turnover, capacity, cost, distribution and split handling

- **Turnover (schedule-only, exact):** 24 transitions/yr x |Δgross| 0.20 =
  **4.80 two-way per year**, inside the 6.0x ceiling measured before any
  scoring. CASH excluded from turnover everywhere.
- **Capacity:** research-scale capital in 11 of the deepest cash-market
  instruments on the exchange; capacity is a non-binding constraint.
- **Cost:** base 10 bps/side on ~4.8 two-way/yr ≈ 0.48%/yr of equity;
  stress 20 bps ≈ 0.96%/yr. The mechanism premium must clear the *stress*
  number in the stress gate — that is precisely what the stress arm tests.
- **Distributions and splits:** legs compound split-adjusted raw returns plus
  distributions on ex-dates in the canonical issuer-TR accounting path; fills
  at raw prices; the 2025-12-05 2:1-split class of conflicts is neutralized
  by issuer-TR authority (packet lesson 6). No adjustment-flag data is read.

## 7. Expected behaviour against the four benchmarks

- **FLAT_HARD (hard floor):** expected positive after-cost over the full S0
  span — average gross ~0.36x a positively-drifting cohort minus ~0.5%/yr
  costs. Expected to beat flat in aggregate; individual folds with negative
  cohort drift can be flat-negative, which the fold gates arbitrate.
- **SPY total return:** expected to *trail* SPY TR in strong-bull folds
  (gross 0.30–0.50 < 1.0) and to outperform in drawdown folds. Trailing SPY
  TR is the *expected* shape of a correctly scaled arm and is not evidence
  against the mechanism.
- **Equal-weight sector TR:** same relationship as SPY TR — the arm is a
  partially-invested basket; raw comparison against fully-invested TR is a
  beta comparison, not a mechanism test.
- **Risk-matched SPY (the only hurdle):** the benchmark replicates the arm's
  own ex-ante gross path, so **positive incremental alpha is the entire
  claim**: it can only arise if returns genuinely concentrate in TOM window
  sessions. Expected: positive per-session excess inside windows, alpha > 0
  in >= 2/3 folds. Alpha ≈ 0 falsifies the family.

## 8. Anchor, neighbour, causal negative control

| Arm | ID | Definition |
|---|---|---|
| Anchor | `SFV3-A6-TOM-SETTLE-A` | TOM window = last 3 + first 2 regular sessions of each month; books per section 5; clocks per section 4. |
| Neighbour | `SFV3-A6-TOM-SETTLE-N` | **Month-start settlement-channel window** = first 3 regular sessions of each month only (Ogden's channel, isolated); identical books, gross values, and fill machinery (24 transitions/yr, 4.80 two-way). |
| Control | `SFV3-A6-TOM-SETTLE-C` | **Time-shifted window** = regular-session ordinals 8–12 of each month (mid-month). Identical books, gross values, fill machinery, and costs. Mid-month has no settlement or rebalancing clock. Ordinals 8–12 are disjoint from the anchor window for every possible month length. |

- **Neighbour identity and role:** distinct stable identity (different window,
  same everything else). Theoretically justified: Ogden's channel predicts
  the premium specifically in the *first* sessions of the month. Support
  rule: neighbour incremental alpha > 0 overall and same sign as the anchor
  in >= 2/3 folds. Attribution note (predeclared): if the neighbour's alpha
  is < 50% of the anchor's, the premium is dominated by the month-END leg
  (window-dressing channel, Lakonishok et al. 1991) — the family's combined
  claim survives only if the anchor remains positive and the control fails
  to reproduce it.
- **Control falsification semantics (packet wording):** the control
  *falsifies the no-mechanism null* when its alpha is opposite-signed vs the
  anchor, or |control alpha| < 50% of |anchor alpha|. Mechanism truth
  predicts alpha ≈ 0 for the mid-month window: nothing in the settlement or
  rebalancing calendar happens at ordinals 8–12, so the same gross schedule
  applied there should earn exactly beta.

## 9. Incremental mechanism test (alpha vs equity beta)

Per scored fold f, using the frozen
`research.stocks_free_v3.incremental.compute_fold_alpha` contract:

```
incremental_alpha(f) = R_strategy_after_cost(f) − R_risk_matched_SPY(f)
```

- The arm declares a **frozen ex-ante gross/vol rule** for the
  `RISK_MATCHED_SPY_CONTEXT` builder: `target_daily_vol = 0.005`
  (reasoned: half of SPY's long-run ~1% daily volatility, a literature-level
  constant, not a data measurement), `lookback_sessions = 63`,
  `min_gross = 0.30`, `max_gross = 0.50` — the clip band equals the arm's own
  designed gross range, so the benchmark can never sit outside the arm's
  exposure envelope. All inputs to the scale are SPY returns strictly before
  session d.
- A pure-beta arm mechanically yields alpha ≈ 0 under this construction;
  therefore **positive alpha in >= 2/3 folds is positive evidence of the TOM
  concentration itself** and cannot be manufactured by equity beta. Raw PnL,
  PF, and benchmark comparisons against SPY TR / EW sector TR are
  diagnostics only and never pass-eligible (packet contract).

## 10. Drop-one-ETF and drop-one-fold expectations

- **Drop-one-ETF:** the book is a uniform 11-leg basket, so no single leg
  carries the schedule. Expected: overall incremental alpha remains positive
  after removing SPY (proves the effect is not a SPY-only artifact) and
  after removing any single sector ETF; per-arm positive-PnL concentration
  per ETF should be near 1/11 in the absence of artifacts (gate: no ETF
  > 35% of positive PnL). Dividend-calendar differences (e.g. XLU/XLP) are
  absorbed by issuer-TR reinvestment, not by trading.
- **Drop-one-fold:** the premium is claimed in every month of every fold
  (~24 windows/fold, ~70+ windows over S0). Expected: no fold supplies
  > 50% of positive PnL (gate), and the sign of incremental alpha should not
  flip when any single fold is removed. A premium visible only in one fold
  is indistinguishable from period luck and the family should die.

## 11. Exact falsification rule

The family is **killed** if ANY of the following is observed after scoring:

1. Anchor mean incremental alpha <= 0, or positive in fewer than 2/3 folds
   (beta-only / no concentration).
2. Control `...-C` does not falsify: its incremental alpha has the same sign
   as the anchor's AND |control alpha| >= 50% of |anchor alpha| — i.e. the
   same gross schedule earns the same "premium" mid-month, so the calendar
   mechanism is not the cause.
3. Neighbour `...-N` alpha is opposite-signed to the anchor in >= 2/3 folds
   (the settlement-channel logic is wrong, not merely weak).
4. Stress PnL <= 0 or stress PF < 1.00 (premium does not survive 20 bps).
5. Schedule-only turnover > 6.0 two-way/yr, or max fold MDD > 15%, or any
   fold PF < 0.80, or drop-one-ETF/drop-one-fold survival fails.
6. A zero-decision fold (24 scheduled transitions/fold make this a
   bookkeeping failure, not an evidentiary one).

No repair, re-threshold, window re-shape, or ETF substitution is permitted
after the first scored metric (PLAN section 12).

## 12. Ancestry comparison — why this is not a rescue

- **Not A4 / ordinary cross-sectional momentum:** there is no ranking, no
  lookback return sort, no top-K selection, no relative-strength anywhere.
  All 11 ETFs are held identically at all times; only gross varies on a
  calendar clock.
- **Not A5 / time-series trend, SMA/EMA, or vol-target defensive rotation:**
  the state variable is the exchange calendar, not any price-derived trend
  or volatility statistic; the arm never de-risks in response to falling
  prices and never holds a trend filter.
- **Not a selected-ETF rescue:** no ETF is chosen after any outcome; the
  cohort is the full mandated 11, always.
- **Not long-SPY-beta dressed up:** a fixed-gross basket is by construction
  beta, and the frozen risk-matched benchmark *removes exactly that beta*;
  the family's only pass path is the window-concentration premium. Scaled
  beta alone produces alpha ≈ 0 — the design makes the ineligible outcome
  the expected failure mode, measured directly.
- **Not an indicator grid:** one pre-declared window rule, zero free
  parameters beyond the fixed constants in sections 4–5, each reasoned above.

## 13. Implementation estimate

Reuse: `research.assets.stocks.loader.BarLoader` (bars + checksum), the
issuer-TR builders and `VolScalingRule` in `research.stocks_free_v3.benchmarks`,
the canonical accounting `research.assets.stocks.factory` (value_book,
etf_leg_turnover, fill_cost, normalize_entry_targets — CASH semantics and
once-only costs already frozen), and `compute_fold_alpha` /
`FoldAlphaReport` in `research.stocks_free_v3.incremental`.

New code: one schedule/target module (~150–250 LOC): regular-session month
ordinals, window membership, the two frozen books, the T -> T+1 fill
schedule, and per-arm config digests; golden tests on synthetic calendars
(~150 LOC). Effort: **2–3 engineer-days including tests**. Risk: LOW —
no estimation, no state machine; the only subtle pieces are month ordinals
under holidays and windows straddling purge gaps (both handled by scoring
calendar sessions only).

## 14. Blinding statement

This document was written without reading any scored outcome, any V2 arm
PnL, any file under `research/control/stocks_free_v2_run/`, `research/audits/`,
`tests/` numeric fixtures or `results/`, without reading the A4/A5 lanes, and
without computing any return, PnL, PF, Sharpe, ranking or correlation on any
data. All constants above are reasoned ex ante from the packet's constraints
and from the cited literature, not from any measurement of the cohort.
