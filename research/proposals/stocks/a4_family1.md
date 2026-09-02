# A4 Family 1 — A4_F1_PEAD_TS_V1: Timestamp-safe post-earnings-announcement drift

- Lane: S2/A4 (calendar/session/corporate-actions perspective)
- Branch: `orca/stocks-s2-prop-a4`, bootstrap SHA `3a00fd7653dd5ff51ca4b9be51b494638bbb6df9`
- Created: 2026-09-02
- Priority space (PLAN §9): post-earnings drift with timestamp-safe surprise data
- Max trials: **exactly 3 cells** (anchor, neighbour, negative control)

**Outcome-blind attestation.** This proposal was written before any scored window
exists. No candidate returns, PF, Sharpe or ranking was computed and no other
proposal lane's files were read. All literature items below are cited from model
internal knowledge and marked `MODEL_INTERNAL_UNVERIFIED`; no DOIs or quotes are
fabricated. Turnover/capacity figures are literature-informed priors, not
computed results.

## 1. Economic mechanism and expected counterparty

Quarterly earnings news diffuses slowly into prices because attention-constrained
investors underreact to the *content* of the announcement relative to expectations
(gradual information diffusion, Hong & Stein 1999; conservatism, Barberis,
Shleifer & Vishny 1998). Prices then drift in the direction of the standardized
unexpected earnings (SUE) for roughly one to three months. The family is long
high-SUE, short low-SUE within each PIT sector.

**Expected counterparty:** attention-constrained investors (discretionary retail
and institutions anchored to stale expectations) who trade the news late —
Bartov, Radhakrishnan & Krinsky (2000) localize the drift where individual
investors dominate — plus arbitrageurs rationed by the weeks-long announcement
risk exposure. We take the other side during the diffusion window.

Literature (all `MODEL_INTERNAL_UNVERIFIED`):

- Ball & Brown (1968), *Journal of Accounting Research* 6(2) — origin of the drift observation.
- Bernard & Thomas (1989), *JAR* 27 (Suppl.) — drift persists ~60 trading days; monotone in SUE quintiles.
- Bernard & Thomas (1990), *JAR* 28(2) — prices underreact to implications of current earnings for future earnings.
- Livnat & Mendenhall (2006), *JAR* 44(1) — drift for consensus-based and time-series SUE; revenue surprises also drift (grounds the neighbour).
- Bartov, Radhakrishnan & Krinsky (2000), *The Accounting Review* 75(1) — counterparty identification.
- Hong & Stein (1999), *JF* 54(6); Barberis, Shleifer & Vishny (1998), *JFE* 49(3) — mechanism theory.

## 2. PIT fields and source authority

| Field | Authority | Status |
| --- | --- | --- |
| `earnings_release_timestamp_utc` (tz-aware first-release timestamp) | Owner-authorized PIT provider (IBES/Refinitiv-class report-date file; PLAN §2 provider order) | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| `earnings_timing_classification` (BTO/AMC/UNKNOWN) | `research.assets.stocks.corporate_actions.classify_earnings_timestamp` vs `US_EQUITY_REGULAR_V1` (A4 frozen table) | available in factory |
| Actual quarterly EPS, first-reported/restatement-aware | PIT fundamentals provider | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| Consensus EPS snapshot strictly before release (+ fallback: seasonal-random-walk SUE, declared at freeze) | IBES-class PIT consensus history | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| Actual/consensus quarterly revenue (neighbour arm) | same PIT providers | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| PIT GICS sector at decision date (no backfill) | A3 security master | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| Universe accepted/rejected rows per decision | A3 PIT universe contract (no index-membership backfill) | factory contract now; real data **UNAVAILABLE_PENDING_ENTITLEMENT** |
| Session calendar table + halt intervals | `US_EQUITY_REGULAR_V1` frozen table; provider halt feeds as `HaltInterval` when real | factory synthetic-golden now; 2027-2030 entries rule-derived (`NEEDS_PROVIDER_VERIFICATION`) |

The date-only earnings field is explicitly rejected: it silently mis-times AMC
releases by one session, which is exactly the failure the A4 lane's BTO/AMC
machinery exists to prevent (PLAN §7 A4: "earnings timestamps are PIT and
classified before/after market").

## 3. Universe, neutralization, benchmark

- **Universe:** PIT-accepted liquid common stocks/ETFs from A3 at each formation
  date (§7 A3 floors: ≥30 eligible names per decision; delisted names retained
  through their final valid event).
- **Neutralization:** sector-neutral — within each PIT GICS sector, long top SUE
  quintile, short bottom quintile, dollar-neutral legs, equal sector caps.
- **Benchmark:** flat (cash) and SPY total return, with sector-neutral long/short
  as the declared factor-neutral context.

## 4. Formation, holding and execution clocks (session-calendar expressible)

- **Formation clock:** event-anchored. At each release with a classified timing,
  SUE is computed from PIT snapshots and the cohort decision is taken at the first
  regular-session open strictly after the release instant. BTO releases enter that
  same date's session open (news public before 09:30 ET; `session_bounds`).
  AMC releases enter `next_session(date)` open. UNKNOWN timings (in-session or
  non-session ET dates) are excluded with a recorded reason — fail closed, never
  reclassified.
- **Holding clock:** 60 regular sessions (Bernard-Thomas horizon), implemented as
  12 weekly cohorts; the aggregate book is rebalanced weekly only by replacing the
  expired cohort. Session boundaries come from `session_bounds`/`next_session`;
  early closes end at 13:00 ET and are never silently extended to 16:00
  (`early_close_cutoff_utc`).
- **Execution clock:** entries/exits at the opening auction of the relevant
  session. If a name is halted at the formation open (declared `HaltInterval`),
  it skips to the first session whose open is not halt-covered; unexplained gaps
  raise via `classify_gap` — `GAP_UNEXPLAINED` never fills and synthetic fills are
  always rejected. Baseline scoring keeps pre/post phases disabled
  (`assert_baseline_scoring_phases`).
- Every clock reduces to `session_bounds`, `next_session`, `early_close_cutoff_utc`
  and halt declarations; the calendar manifest digest is part of the trial
  identity. No synthetic or weekly calendar is used anywhere.

## 5. Expected turnover and capacity (priors, not computed)

- One-sided turnover of order 6–10x/year: ~a quarter of the liquid universe
  announces per quarter with classified surprises, held 60 sessions in weekly
  cohorts.
- Capacity: mid eight-figure USD notional at ≤5% ADV participation, bounded by
  the small-cap quintile tail; execution clusters on post-announcement days where
  liquidity is typically above average.
- Declared cost sensitivity: the family must clear the S6 stress (x1.5
  commission/spread) with auction costs and short borrow loaded; drift is a known
  thin-margin family after costs.

## 6. Arms (anchor, neighbour, causal negative control — three distinct cells)

1. **`A4_F1_PEAD_TS_V1:ANCHOR` (`anchor_eps_sue_ls`)** — sector-neutral EPS-SUE
   quintile long/short, PIT consensus (frozen fallback: seasonal-random-walk
   SUE), timestamp-safe formation, 60-session cohort hold.
2. **`A4_F1_PEAD_TS_V1:NEIGHBOUR` (`neighbour_revenue_sue_ls`)** — identical
   pipeline/clock/neutralization with revenue SUE instead of EPS SUE.
   Theoretically justified by Livnat & Mendenhall (2006): revenue surprises
   carry the same underreaction content, so this arm tests that the mechanism is
   news-content diffusion rather than the EPS accounting construct.
3. **`A4_F1_PEAD_TS_V1:CONTROL` (`control_sign_flipped_sue_ls`)** — identical
   pipeline, cohorts, clocks, holdings and costs with the SUE sign flipped (long
   bottom, short top). It removes only the news-content direction while keeping
   the entire event calendar and construction; underreaction predicts it
   destroys or inverts the effect. If the anchor's edge survives sign-flipping,
   the family is falsified as mechanism-mistitled.

## 7. Corporate-action, earnings, borrow and dividend treatment

- Splits and cash dividends applied exactly once at ex/effective timestamps by
  the A4 `CorporateActionEngine`; signals on the declared TOTAL_RETURN research
  path, fills on the RAW path; raw-vs-total-return reconciliation records
  required at every action boundary a holding crosses.
- A new release for a held name refreshes its SUE at the next cohort boundary
  only; the name's announcement-session prints are never used for formation fills.
- Short legs require PIT locate and borrow rate at formation; unavailable borrow
  rejects the leg, never fills free (§7 A5). Shorts accrue dividend liability;
  longs receive cash dividends (`cash_to_position`); SPY total-return benchmark
  keeps dividend treatment symmetric.

## 8. Falsification rule and external-validity caveats

Pre-registered: family survives only if (a) anchor passes the §13 gates
(after-cost expectancy > 0, position PF ≥ 1.10, ≥2/3 folds positive, no fold PF
< 0.80); (b) neighbour supports the anchor (same sign, similar magnitude);
(c) the sign-flipped control destroys or materially weakens the anchor effect;
(d) drop-one-symbol/sector/fold survival. SUE-quintile monotonicity is a
declared diagnostic, not a gate. Failure of (c) with (a) passing rejects the
family as calendar exposure, not news content.

Caveats:

- Drift is documented mostly on 1970–2005 US data and weakens post-publication
  (McLean & Pontiff 2016, *JF* 71(1); `MODEL_INTERNAL_UNVERIFIED`); a null is a
  legitimate outcome.
- Consensus PIT quality is the largest data risk; snapshot misalignment can
  manufacture or destroy surprises, and any snapshot change is a new trial identity.
- Costs and borrow consume a large fraction of gross drift in the illiquid tail.
- Returns are lumpy around announcement seasons (Jan/Apr/Jul/Oct).
- 2027–2030 calendar entries are rule-derived pending provider verification.

## 9. Exact maximum trial count

**3 cells** — anchor, neighbour, negative control. No grid over horizons,
quintile counts or rebalance frequencies: those are frozen here before any
scoring.

## Novelty defense and readiness

- **Not a crypto rescue:** observable is an accounting surprise vs expectations
  (not order-flow imbalance, funding cashflows or a weekly reversal score);
  counterparty is attention-constrained earnings traders; clock is
  event-anchored next-open formation on the NYSE session calendar; control is
  the sign-flipped surprise. All four dimensions differ from M01
  aggressor-flow absorption, funding-carry and weekly reversal.
- **Lane-dependent capability:** inexpressible without PIT BTO/AMC
  classification, which is A4-owned machinery.
- **Readiness:** implementable now against the synthetic-fixture factory
  (calendar, CA engine, fixture SUE rows, expected-sign and control-destruction
  goldens). Real-data readiness **BLOCKED pending owner-authorized
  entitlement**; real scored research closes `STOCKS_BLOCKED_DATA_AUTHORITY`
  until then (PLAN §0).
