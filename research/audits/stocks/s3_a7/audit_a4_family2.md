# A7 audit — A4 Family 2 `A4_F2_OVI_DECOMP_V1` (defensive overnight-capture sleeve)

Sources audited: `research/proposals/stocks/a4_family2.{md,json}` (twin, consistent).

## 1. Dimension findings (PLAN §9)

### Novelty — PASS (moderate-strong)
The overnight/intraday decomposition (French & Roll 1986; Lou, Polk & Skouras
2019; Bogousslavsky 2016) is well documented, but no S2 proposal occupies the
PLAN §9 "defensive overnight/intraday decomposition" space except this one, and
the factory lens is real: "daily-bar pipelines average the overnight and
intraday components into one close-to-close number; DST-correct UTC bounds,
13:00 early closes, holiday-spanning gaps and halt fail-closed semantics are
the difference between measuring and inventing this premium". Frozen
constants: "beta window, tercile cut, sector caps and clocks are frozen here
before any scoring."

### Source quality — PASS (strong)
Four citations, all real and correctly attributed (French & Roll 1986 JFE
17(1); Lou-Polk-Skouras 2019 JFE 134(1); Bogousslavsky 2016 JF 71(6);
Aboody-Even-Tov-Lehavy-Trueman 2018 JFE 127(2)), `MODEL_INTERNAL_UNVERIFIED`,
with regime-dependence and null-legitimacy caveats stated up front.

### Correlation (structural only) — PASS
Observable: session-decomposed close-to-open capture on a low-beta book.
Clock: daily double-auction (closing entry, opening exit), including early
closes and holiday spans. Counterparty: "intraday-horizon traders and
flow-driven institutions whose rebalancing pressure concentrates in
session-boundary auctions". Numeric prewindow rho:
NOT_IMPLEMENTABLE_NO_REAL_DATA. Long-only, no earnings data — informationally
disjoint from A4 F1 by declared construction.

### Data readiness vs as-built factory — PASS
Verified: `session_bounds(day).end_utc` / `next_session(day).start_utc` exist;
`early_close_cutoff_utc` returns 13:00 ET on early closes;
`classify_gap` classifies inter-session intervals `GAP_OK_WITH_REASON` ("the
gap **is** the return" is exactly the as-built semantics) and fails closed on
uncovered in-session gaps; halted-through-exit carry and
`assert_baseline_scoring_phases` (pre/post disabled — this is a close-to-open
strategy between regular sessions, not a pre/post strategy) verified.
Dividend-at-ex-date-open entitlement accrual matches
`CorporateActionEngine`/`IdentityLedger.apply_dividend` semantics ("flat
positions book nothing"). Real inputs (bound prints, PIT beta inputs, 13F,
halt feeds) correctly UNAVAILABLE_PENDING_ENTITLEMENT.

### Cost/borrow feasibility — PASS (the binding risk, honestly priced)
"Full-notional daily round trip at session boundaries (~250 round trips/year) —
the highest-turnover shape in this sprint"; "This family lives or dies on
double-auction costs: the S6 x1.5 commission/spread stress and the declared
auction-cost proxy are gates by construction; the proposal accepts the risk
that auction costs make it infeasible — that is an honest null, not a hidden
grid". Borrow: "No short legs in any arm; borrow treatment is 'not required',
declared explicitly so the SD4 borrow gates trivially but honestly" — no
hidden free-borrow because there are no shorts. A7's arithmetic concurrence:
at even 2–4 bps all-in per round trip, annual drag is 5–10% on notional
against an overnight premium historically of order a few percent — the honest
prior is that Stage-A's after-cost expectancy gate is more likely than not to
fail. That is a predicted research outcome, not an eligibility defect: the
cost model is coherent and no fill is assumed free.

### Hidden crypto-family rescue — NO RESCUE (E6 = 1)
- vs weekly reversal (REVERSE-3D lineage, rejected): different observable
  ("session-decomposed close-to-open capture, not a reversal score"),
  different counterparty (auction-concentrated infrequent rebalancers),
  different clock (daily double-auction on the NYSE calendar "no weekly
  calendar anywhere"), different control (intraday leg of the same book, not
  an inverted signal). The control severs the holding interval while keeping
  names/formation/frequency — genuinely causal for the claimed carrier.
- vs M01: no order-flow/microstructure observable, no L2 inputs.
- vs funding-carry: "no funding cashflows; US cash equities only".

## 2. Rubric scoring

- E1 = 1; E2 = 1; E3 = 1; E4 = 1; E5 = 1 (coherent with declared cost models;
  infeasibility risk is declared and gated, not assumed away); E6 = 1;
  E7 = 1 (0 HIGH/CRITICAL).

**Sum 7/7 — ELIGIBLE.**

## 3. Quality score: 7.5 / 10

Justification: the cleanest negative control in the pool (interval swap on the
identical book) and a factory lens (session-bound print hygiene) that is
exactly where naive pipelines lie; literature small but precisely on point.
Deductions: the cost survival is improbable under the declared cost models
(the proposal itself concedes this), the mechanism is a regime-dependent
average premium rather than a name-selectable edge (drop-one-symbol stresses
will do little), and the 13F neighbour imports a second heavy entitlement with
a quarterly state variable behind a daily clock.

## 4. Objections

| id | severity | objection | resolution required |
|---|---|---|---|
| O1 | MEDIUM | Expected cost drag (~250 full-notional round trips/yr) plausibly exceeds the gross overnight premium under the declared auction-cost proxy; anchor Stage-A expectancy gate likely fails | None for eligibility; if selected, freeze must fix the auction-cost proxy before scoring and accept the honest null |
| O2 | LOW | Low-beta tercile book retains material positive market beta; "market-beta-matched overnight exposure" context is declared but the sleeve is not market-neutral — MDD/expectancy gates inherit market exposure | Report book beta against SPY TR as declared |
| O3 | LOW | Neighbour (13F ownership) cadence is quarterly while the clock is daily; book churn between filings is minimal but the freeze must pin the availability-lag rule | Pin 13F availability-date convention at freeze |

## 5. Verdict

**ELIGIBLE** (7/7). No failed rubric items. Expected rank 5 under the frozen
rubric (quality 7.5; lex after `A4_F1_PEAD_TS_V1`).
