# A4 Family 2 — A4_F2_OVI_DECOMP_V1: Defensive overnight-capture sleeve (overnight-vs-intraday decomposition)

- Lane: S2/A4 (calendar/session/corporate-actions perspective)
- Branch: `orca/stocks-s2-prop-a4`, bootstrap SHA `3a00fd7653dd5ff51ca4b9be51b494638bbb6df9`
- Created: 2026-09-02
- Priority space (PLAN §9): defensive overnight/intraday decomposition
- Max trials: **exactly 3 cells** (anchor, neighbour, negative control)

**Outcome-blind attestation.** Written before any scored window exists; no
candidate returns, PF, Sharpe or ranking computed; no other proposal lane's
files read. Citations are model-internal and marked `MODEL_INTERNAL_UNVERIFIED`;
no DOIs or quotes fabricated. Turnover/capacity figures are priors, not results.

## 1. Economic mechanism and expected counterparty

US equity expected returns localize into session components: documented US
evidence finds the average equity premium accrues disproportionately to holding
**overnight** (regular-session close to next regular-session open), with the
average **intraday** (open-to-close) component near zero or negative. The
generating mechanism is **institutional infrequent rebalancing**: investors who
trade occasionally concentrate order flow near session-boundary auctions,
transferring overnight exposure to whoever holds through the close (Bogousslavsky
2016). French & Roll (1986) establish that price discovery concentrates in
sessions, making non-trading intervals structurally distinct return states;
Lou, Polk & Skouras (2019) show premia split into overnight and intraday
components with opposite average signs by ownership/strategy clienteles.

The family holds a **defensive (low-beta) long book only overnight**: entered at
the closing auction, exited at the next opening auction — capturing the
overnight component and refusing the intraday component of the same names.

**Expected counterparty:** intraday-horizon traders and flow-driven institutions
whose rebalancing pressure concentrates in session-boundary auctions; investors
structurally averse to overnight gap risk who must be compensated for it. We are
the overnight-exposure provider on the other side of their intraday-flat
preference.

Literature (all `MODEL_INTERNAL_UNVERIFIED`):

- French & Roll (1986), *Journal of Financial Economics* 17(1) — variance/information concentration in sessions; non-trading intervals are distinct states.
- Lou, Polk & Skouras (2019), *JFE* 134(1) — "tug of war": overnight vs intraday expected returns; overnight positive on average for broad/defensive books.
- Bogousslavsky (2016), *Journal of Finance* 71(6) — infrequent rebalancing → overnight-momentum/intraday-reversal seasonality (the mechanism).
- Aboody, Even-Tov, Lehavy & Trueman (2018), *JFE* 127(2) — cross-sectional clientele variation in overnight asymmetry (grounds the neighbour).

## 2. PIT fields and source authority

| Field | Authority | Status |
| --- | --- | --- |
| Session calendar table (holidays, 13:00 ET early closes, special closures, DST-correct UTC bounds) | `US_EQUITY_REGULAR_V1` frozen table (A4); pinned NYSE hours/calendar reference | factory now; 2027–2030 entries rule-derived (`NEEDS_PROVIDER_VERIFICATION`) |
| Regular-session bound prints (opening/closing auction or first/last regular-session prints) | Owner-authorized provider (PLAN §2 order, e.g. Databento when entitled) | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| PIT beta inputs (252-session rolling vs SPY, TOTAL_RETURN path) | PIT price history via A3/loader | schema in fixture now; real **UNAVAILABLE_PENDING_ENTITLEMENT** |
| PIT institutional ownership (13F snapshots, filing-lag availability dates) | SEC 13F via owner-authorized vendor | **UNAVAILABLE_PENDING_ENTITLEMENT** (neighbour arm only) |
| Corporate actions (splits, cash dividends with ex/effective timestamps) | A4 `CorporateActionEngine` records; provider CA file when entitled | factory contract now; real records **UNAVAILABLE_PENDING_ENTITLEMENT** |
| Halt / no-print intervals | Provider halt feed as declared `HaltInterval` | **UNAVAILABLE_PENDING_ENTITLEMENT**; fail-closed gap classification in factory |

Print quality at the session bounds is decisive: consolidated closes
contaminated by after-hours prints silently fake or destroy the overnight return.

## 3. Universe, neutralization, benchmark

- **Universe:** PIT-accepted liquid US common stocks/ETFs from A3 (≥30 eligible
  names per decision), filtered to the low-beta defensive subset.
- **Neutralization:** long-only book over the bottom-beta tercile (252-session
  rolling PIT beta vs SPY), sector-capped so it is not a single-sector
  bond-proxy; no short leg in anchor/control.
- **Benchmark:** flat (cash) and SPY total return; declared factor-neutral
  context is market-beta-matched overnight exposure with sector caps.

## 4. Formation, holding and execution clocks (session-calendar expressible)

- **Formation clock:** calendar-anchored, no signal event. The book is re-derived
  each session from the previous close's PIT beta tercile; decisions use data
  strictly before the entry instant.
- **Holding clock:** overnight interval only — buy at `session_bounds(day).end_utc`
  (closing auction; 13:00 ET on early closes), sell at `next_session(day).start_utc`
  (opening auction). Intervals span weekends, holidays and early-close boundaries
  exactly as the frozen table declares; the ~41h Thanksgiving-eve overnight is a
  structurally longer overnight state, **not** a missing bar.
- **Execution clock:** double-auction (MOC-entry / MOO-exit shape). Intervals
  between bounds classify as `GAP_OK_WITH_REASON` — the gap **is** the return. A
  name halted through the exit open is carried to the first halt-free open; an
  unexplained in-session gap fails closed and stops that name — synthetic fills
  are never authorized. Pre/post phases stay disabled in baseline scoring: this
  is a close-to-open strategy between regular sessions, not a pre/post-market
  strategy (`assert_baseline_scoring_phases`).
- Everything reduces to `session_bounds`, `next_session`,
  `early_close_cutoff_utc` and `HaltInterval`; the calendar manifest digest is
  part of the trial identity.

## 5. Expected turnover and capacity (priors, not computed)

- Full-notional daily round trip at session boundaries (~250 round trips/year) —
  the highest-turnover shape in this sprint; feasibility hinges on auction
  liquidity of the defensive mega-cap subset.
- Capacity: low eight figures USD at ≤5% of closing/opening auction volume in
  low-beta large caps; participation beyond that moves the close against the
  book and consumes the premium.
- Declared cost sensitivity: the family lives or dies on double-auction costs;
  the S6 x1.5 commission/spread stress plus the declared auction-cost proxy are
  gates by construction. An honest cost-infeasible null is acceptable output.

## 6. Arms (anchor, neighbour, causal negative control — three distinct cells)

1. **`A4_F2_OVI_DECOMP_V1:ANCHOR` (`anchor_overnight_lowbeta`)** — long defensive
   book (bottom-beta tercile, sector-capped, PIT), bought at the closing auction,
   sold at the next opening auction, every session day including early closes
   and holiday-spanning intervals.
2. **`A4_F2_OVI_DECOMP_V1:NEIGHBOUR` (`neighbour_overnight_high_own`)** —
   identical overnight clock, book selected by high PIT institutional ownership
   (13F, filing-lag availability) instead of low beta. Theoretically justified:
   Lou-Polk-Skouras attribute overnight localization to ownership clienteles —
   the mechanism's state variable — so the same clock on the ownership book
   should also capture the overnight premium. Supports the anchor if the
   mechanism is clientele-driven overnight compensation rather than low beta per se.
3. **`A4_F2_OVI_DECOMP_V1:CONTROL` (`control_intraday_lowbeta`)** — the identical
   anchor book held intraday only (open→close of the same session, flat
   overnight). Same names, same formation, same trading frequency; only the
   holding interval differs. The mechanism predicts the overnight premium
   vanishes here (intraday average ≈ zero or negative in US evidence). If
   intraday matches overnight, the edge was plain market beta and the family is
   falsified.

## 7. Corporate-action, earnings, borrow and dividend treatment

- Splits/cash dividends applied exactly once at ex/effective timestamps (default
  ex-date open). When the exit open is an ex-date, the position held through the
  prior close is entitled: `cash_to_position` accrues at the ex/effective moment
  and the raw-vs-total-return reconciliation must close at that boundary.
  Beta/signals on the TOTAL_RETURN path; auction fills on the RAW path.
- **No earnings conditioning** — names are held regardless of announcement
  calendar; earnings-day overnight gaps are simply part of the overnight stream.
  This keeps the information set disjoint from A4 Family 1 (PEAD).
- **Borrow: none required** (no short legs in any arm), declared explicitly so
  no free-borrow assumption hides anywhere.
- Longs receive cash dividends; ex-dates following holds land dividend yield in
  the overnight leg; SPY total-return benchmark keeps dividend treatment symmetric.

## 8. Falsification rule and external-validity caveats

Pre-registered: family survives only if (a) anchor passes §13 gates (after-cost
expectancy > 0, position PF ≥ 1.10, ≥2/3 folds positive, no fold PF < 0.80);
(b) neighbour supports the anchor; (c) the intraday-only control destroys or
materially weakens the effect (intraday expectancy ≤ overnight expectancy by a
declared margin; intraday ≤ 0 is the point prediction); (d) drop-one
-symbol/sector/fold survival and the auction-cost stress hold. A control that
matches the anchor rejects the family.

Caveats:

- The positive overnight average is a recent-decades US large-cap pattern and
  regime-dependent; a null on S0 is legitimate.
- Double-auction costs dominate feasibility; small proxy changes can flip net
  expectancy.
- Session-bound print quality decides the decomposition; provider verification
  at bounds is mandatory before real scoring.
- Early closes and holiday-spanning overnights are structurally different
  intervals; 2027–2030 calendar entries are rule-derived pending verification.
- Beta/ownership inputs are PIT-lagged estimators; window changes are new trial
  identities.

## 9. Exact maximum trial count

**3 cells** — anchor, neighbour, negative control. No grids: beta window, tercile
cut, sector caps and clocks are frozen here before any scoring.

## Novelty defense and readiness

- **Not a crypto rescue:** vs weekly reversal — different observable
  (session-decomposed close-to-open capture, not a reversal score), counterparty
  (auction-concentrated infrequent rebalancers), clock (daily double-auction on
  the NYSE session calendar with early closes and holiday spans; no weekly
  calendar) and control (intraday leg of the same book). Not M01 aggressor-flow
  absorption (no order-flow observable) and not funding-carry (no funding
  cashflows; US cash equities only).
- **Disjoint from A4 Family 1:** return decomposition vs accounting surprise;
  pure calendar clock vs event-anchored timestamps; intraday-leg control vs
  sign-flipped surprise; no earnings data used.
- **Lens note:** the edge lives exactly where naive session handling silently
  fakes or destroys the effect — daily-bar pipelines average the overnight and
  intraday components into one close-to-close number; DST-correct UTC bounds,
  13:00 early closes, holiday-spanning gaps and halt fail-closed semantics are
  the difference between measuring and inventing this premium.
- **Readiness:** implementable now against the synthetic-fixture factory
  (calendar bounds/early closes, CA engine ex-date accrual and reconciliation,
  fixture prices with expected-sign and control-destruction goldens). Real-data
  readiness **BLOCKED pending owner-authorized entitlement** (bound prints, PIT
  beta inputs, 13F, halt feeds); real scored research closes
  `STOCKS_BLOCKED_DATA_AUTHORITY` until then (PLAN §0).
