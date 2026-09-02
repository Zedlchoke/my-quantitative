# A7 audit — A4 Family 1 `A4_F1_PEAD_TS_V1` (timestamp-safe post-earnings-announcement drift)

Sources audited: `research/proposals/stocks/a4_family1.{md,json}` (twin, consistent).

## 1. Dimension findings (PLAN §9)

### Novelty — PASS (moderate)
PEAD is the most heavily documented anomaly in the pool and the proposal says
so ("Drift is documented mostly on 1970–2005 US data and weakens
post-publication (McLean & Pontiff 2016...)"). The additive contribution is the
timestamp-safety lens: "The date-only earnings field is explicitly rejected: it
silently mis-times AMC releases by one session", implemented via
`classify_earnings_timestamp` BTO/AMC with fail-closed UNKNOWN. This is the
PLAN §9 priority space "post-earnings drift with timestamp-safe surprise data"
executed exactly as specified. Grid prohibition: "No grid over horizons,
quintile counts or rebalance frequencies: those are frozen here before any
scoring."

### Source quality — PASS (strong)
Seven citations, all real with volume/issue detail (Ball & Brown 1968 JAR;
Bernard & Thomas 1989 JAR Suppl. and 1990 JAR; Livnat & Mendenhall 2006 JAR;
Bartov-Radhakrishnan-Krinsky 2000 TAR; Hong & Stein 1999 JF; BSV 1998 JFE;
McLean & Pontiff 2016 JF), all `MODEL_INTERNAL_UNVERIFIED`. The revenue-SUE
neighbour justification via Livnat & Mendenhall is the correct use of that
paper. Honest null risk declared.

### Correlation (structural only) — PASS
Observable: accounting surprise vs PIT consensus (SUE). Clock: event-anchored,
"first regular-session open strictly after the release instant", 60-session
cohort holds aggregated weekly. Counterparty: "attention-constrained investors...
who trade the news late". Numeric prewindow rho: NOT_IMPLEMENTABLE_NO_REAL_DATA.
Note: informationally disjoint from A4 F2 by construction ("names are held
regardless of announcement calendar" there; here earnings events are the
signal) — see matrix.

### Data readiness vs as-built factory — PASS
Verified: `classify_earnings_timestamp(ts_utc, calendar)` returns BTO (< session
open of the ET date), AMC (>= session close), UNKNOWN fail-closed with reason —
exactly the proposal's declared semantics. `session_bounds`/`next_session`/
`early_close_cutoff_utc`/`HaltInterval`/`assert_baseline_scoring_phases` all
exist; halt-skip at formation open is expressible; weekly cohort aggregation of
session counts is arithmetic, not a calendar. Calendar table coverage
(2010–2026 published-consistent; 2027–2030 rule-derived) matches the
proposal's own flag. Real data (release timestamps, actual/consensus EPS and
revenue, PIT GICS, halt feeds) correctly UNAVAILABLE_PENDING_ENTITLEMENT,
including the seasonal-random-walk fallback, which the JSON correctly declares
"a distinct arm config at freeze time, never swapped after inspection".

### Cost/borrow feasibility — PASS
"Short legs require PIT locate and borrow rate at formation; unavailable borrow
rejects the leg, never fills free"; short dividend liability and long cash
dividends per the identity; "must clear the S6 stress (x1.5 commission/spread)
with auction costs and short borrow loaded; drift is a known thin-margin family
after costs". Turnover 6–10x/yr with 60-session holds in weekly cohorts is
arithmetically coherent. No free-borrow/free-fill/halt-fill; announcement-day
prints explicitly barred from formation fills.

### Hidden crypto-family rescue — NO RESCUE (E6 = 1)
- vs M01: observable is an accounting surprise, not order-flow imbalance;
  counterparty attention-constrained earnings traders, not momentum aggressors;
  clock event-anchored next-open on the NYSE session calendar, not intraday
  absorption; control is the sign-flipped surprise, not a flow placebo.
- vs funding-carry: no funding observable or cashflow anywhere.
- vs weekly reversal: "no reversal signal, no weekly-calendar clock; the weekly
  cadence here is only a cohort aggregation of event-anchored 60-session
  holds" — verified: the aggregate book touches weekly but the mechanism clock
  is event-anchored.

## 2. Rubric scoring

- E1 = 1; E2 = 1; E3 = 1 (neighbour justified; sign-flip control plausibly
  destroys the stated mechanism — see O1 for its discriminating limit);
  E4 = 1; E5 = 1; E6 = 1; E7 = 1 (0 HIGH/CRITICAL).

**Sum 7/7 — ELIGIBLE.**

## 3. Quality score: 7.5 / 10

Justification: the cleanest PIT-discipline treatment of earnings timing in the
pool and the exact execution of a named priority space, with honest decay and
consensus-quality caveats. Deductions: the base effect is the most crowded and
most post-publication-decayed of the six (a real null risk, honestly declared),
and the negative control is the least discriminating of the six (O1) — it tests
direction, not mechanism class.

## 4. Objections

| id | severity | objection | resolution required |
|---|---|---|---|
| O1 | MEDIUM | The sign-flipped control cannot distinguish underreaction from any signed SUE-correlated characteristic/risk-premium story: a risk-premium anchor and its sign-flip produce (+, −), which already satisfies "(d) destroys or materially weakens". A placebo-surprise control (event calendar fixed, surprise shuffled within sector-quarter) would separate news content from signed characteristics | Advisory: consider declaring the placebo as an additional diagnostic at freeze (does not consume a cell unless promoted; max_trials=3 must be respected) |
| O2 | LOW | Within-sector top/bottom quintile books can starve small PIT sectors; quintile-vs-sector-cap interaction unspecified | Freeze must define minimum sector membership / pooling rule |
| O3 | LOW | Consensus snapshot misalignment is declared "the single largest data risk"; the SARW fallback is itself entitlement-blocked (PIT actuals) | No action beyond the declared freeze-time arm-config pin |

## 5. Verdict

**ELIGIBLE** (7/7). No failed rubric items. Expected rank 4 under the frozen
rubric (quality 7.5; lex before `A4_F2_OVI_DECOMP_V1`).
