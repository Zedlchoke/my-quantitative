# A7 audit — A5 Family 1 `A5-S2-F1-LENDING-CONSTRAINT-PREMIUM` (borrow-fee short premium, honest carry accounting)

Sources audited: `research/proposals/stocks/a5_family1.{md,json}` (twin, consistent).

## 1. Dimension findings (PLAN §9)

### Novelty — PASS (strong)
The short-sale-constraint anomaly (Miller 1977; D'Avolio 2002; Nagel 2005;
Stambaugh-Yu-Yuan 2012) is documented, but the proposal's object is not the
anomaly — it is the honest-residue spread: "the fee that ranks the names is the
fee the canonical identity charges (`short_borrow_fees`)... Engines that book
shorts at zero borrow and ignore the liability inflate this spread by roughly
the full fee plus dividend yield of the short notional". The zero-borrow
counterfactual is declared as a built-in falsification diagnostic ("that delta
is this family's own falsification diagnostic, not its edge") — an
accounting-honesty design no other proposal in the pool duplicates. No grid:
"one mechanism, three theory-linked arms".

### Source quality — PASS (strong)
Eight citations, all real (Miller 1977 JF; D'Avolio 2002 JFE 66; Nagel 2005 JF;
Stambaugh-Yu-Yuan 2012 JFE; Kaplan-Moskowitz-Sensoy 2013 JF;
Blocher-Reed-Van Wesep 2013 JFE; Geczy-Musto-Reed 2002 JFE 66; Drechsler &
Drechsler shorting premium — venue honestly marked unverified working paper).
`MODEL_INTERNAL_UNVERIFIED` declared; recall/squeeze and regime-break caveats
stated.

### Correlation (structural only) — PASS
Observable: PIT securities-lending fee/utilization. Clock: month-end formation,
~21-session holds, daily fee accrual. Counterparty: "securities-lending desks
(beneficial owners / prime brokers)... plus sentiment-driven retail longs".
Numeric prewindow rho: NOT_IMPLEMENTABLE_NO_REAL_DATA.

### Data readiness vs as-built factory — PASS (heaviest data dependency of the six, correctly declared)
Verified against source: `BorrowLocate` (available ⇒ PIT `annual_rate`
mandatory; unavailable ⇒ reject), `SharedCapitalReplay.submit_intent` locate
gate BEFORE fill with `MISSING_LOCATE`/`NO_LOCATE` zero-cost rejections,
`compute_borrow_fee` at `BORROW_DAY_COUNT_BASIS = 360`,
`IdentityLedger.accrue_borrow_fee` fail-closed on open short,
`attempt_fill` rejection order HALTED → SESSION_CLOSED → MISSING_QUOTE →
MISSING_ADV → PARTICIPATION_CAP exactly as quoted, `next_executable_event_index`
/ `deferred_entry_timestamp` present, terminal valuation on last executable
event via `finalize_terminal`. Real data (securities-finance feed, FINRA short
interest, PIT earnings calendar) correctly UNAVAILABLE_PENDING_ENTITLEMENT;
recalls declared unmodeled rather than silently assumed.

### Cost/borrow feasibility — PASS (best-in-pool treatment)
The dominant drag is modeled as carry, not trading: "special-name fees of order
3-10%/yr... plus short dividend liability of order 1-2%/yr... The honest bar:
the gross sector-neutral spread must exceed roughly 5-12%/yr on short notional
plus trading friction". Feasibility conditional is explicit: "a constrained
name is traded only if the expected fee over the holding period does not exceed
its expected overpricing contribution — the ledger never books a short whose
carry the mechanism cannot afford". No free-borrow anywhere; participation cap
forces multi-day entry; capacity honestly bounded by the short leg.

### Hidden crypto-family rescue — NO RESCUE (E6 = 1)
- vs funding-carry (V6 CARRY-1D/3D/7D rejected): adversarially the closest
  cousin — both are "collect/short against a periodic rate" shapes — but every
  rescue axis differs: observable (equity securities-lending fee/utilization vs
  perpetual funding rate), counterparty (lending desks and sentiment longs vs
  perp long/short counterparties), clock (monthly formation vs funding-interval
  carry), and crucially the sign structure: here the fee is a COST paid to
  harvest overpricing, there the funding payment was the harvested object. The
  causal control (GC-placebo within top lending-supply tercile) has no analog
  in any rejected crypto family and severs the constraint channel: "The
  constraint cause is absent there, so the mechanism predicts a spread
  indistinguishable from zero after costs".
- vs M01: no order-flow observable, no intraday absorption clock.
- vs weekly reversal: monthly, not periodic-reversal; not conditioned on past
  returns.

## 2. Rubric scoring

- E1 = 1; E2 = 1; E3 = 1 (utilization neighbour is the price/quantity twin of
  the fee — strong; GC placebo severs the constraint channel); E4 = 1;
  E5 = 1; E6 = 1; E7 = 1 (0 HIGH/CRITICAL).

**Sum 7/7 — ELIGIBLE.**

## 3. Quality score: 8.0 / 10

Justification: edge and cost are the same object — the cleanest treatment of
borrow economics in the pool and exactly the A5 lane's declared mandate; the
GC-placebo control and zero-borrow counterfactual are genuinely causal and
cheap to run. Deductions: the binding entitlement (PIT securities-finance
data) is the hardest of the six and the family is untestable on real data
without it (declared); realized-book conditioning on locate availability (O2);
recall/squeeze episodes unmodeled (O1).

## 4. Objections

| id | severity | objection | resolution required |
|---|---|---|---|
| O1 | MEDIUM | Recall/forced-cover episodes are UNAVAILABLE_PENDING_ENTITLEMENT and unmodeled; squeezes "can erase months of premium in days". Borrow x2 stress partially but incompletely covers this | Keep declared caveat; freeze must require the borrow x2/unavailable stress and report squeeze-window attribution |
| O2 | MEDIUM | The tradeable book conditions on locate availability — exactly where some arbitrage capital can already act; the harvested set may be the least-constrained tail of the constrained set. The proposal's feasibility conditional acknowledges but does not resolve this selection endogeneity | Freeze must mandate short-leg coverage and traded-vs-dropped constrained-name attribution |
| O3 | LOW | GC-placebo power: fee dispersion inside the top lending-supply tercile is compressed; a ≈0 spread may be hard to distinguish from a weak positive | Declare placebo power diagnostics at freeze |

## 5. Verdict

**ELIGIBLE** (7/7). No failed rubric items. Expected rank 2 under the frozen
rubric (quality 8.0; wins the 8.0 lex tie-break vs `EQ_S2_A3_F2_LISTING_AGE`).
