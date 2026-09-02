# A7 audit — A5 Family 2 `A5-S2-F2-EXDATE-TAX-CLIENTELE-CAPTURE` (ex-date dividend capture, honest liability accounting)

Sources audited: `research/proposals/stocks/a5_family2.{md,json}` (twin, consistent).

## 1. Dimension findings (PLAN §9)

### Novelty — PASS (moderate)
Ex-date drop-ratio capture (Elton & Gruber 1970) is old and, as the proposal
admits, "a crowded dealer trade". The novel element is the accounting-honesty
design: "On adjusted (total-return) series the entire effect is invisible by
construction; on naive hedged backtests built from TR series the hedge leg's
ex-date liability silently vanishes" — capture is booked as an explicit
`cash_dividends` receipt on a raw-price identity with
`short_dividend_liability` named for the hedge. Falsification condition (iv)
converts the classic adjusted-series artifact into a golden construction
assertion. Honest thinness disclosure: "the post-2003 qualified-dividend
regime compresses the shortfall (honest prior: thin)".

### Source quality — PASS (strong)
Six citations, all real and correctly characterized (Elton & Gruber 1970 JF;
Kalay 1982 JF; Michaely 1991 JF; Boyd & Jagannathan 1994 JF; Green & Rydqvist
1999 JFE; Frank & Jagannathan 1998 JFE), `MODEL_INTERNAL_UNVERIFIED`, with the
Frank–Jagannathan microstructure alternative explicitly kept alive as the
reason the control is mandatory — exemplary adversarial self-treatment.
Drop-ratio priors declared "honestly uncertain... r ∈ [0.6, 0.95]" with the
thin post-2003 evidence "stated, not cited".

### Correlation (structural only) — PASS with note
Observable: PIT declared-dividend/ex-date calendar with tax character.
Clock: event-driven T−5 signal → entry → ex-date → T+1 close exit (~6–7
sessions). Counterparty: "taxable investors... selling into cum-dividend
dates" plus ex-date dealers. Numeric prewindow rho:
NOT_IMPLEMENTABLE_NO_REAL_DATA. Note: this is the pool's only carry-shaped
family (collect a declared payment around a known date); all four rescue axes
still differ from funding-carry (see below).

### Data readiness vs as-built factory — PASS with finding
Verified: `DividendEvent` booking into `cash_dividends` / 
`short_dividend_liability` with flat positions booking nothing (as-built
`IdentityLedger.apply_dividend` semantics match the proposal's claims
verbatim); raw-price fills via `attempt_fill` with the exact fail-closed order
quoted; one-event delay and last-executable-event terminal policy present.
**Objection O1 (MEDIUM):** the pit_fields table declares "declared cash
dividend per share with PIT ex-date and declaration timestamp —
AVAILABLE_IN_SYNTHETIC_FIXTURE_NOW (DividendEvent fixture)", but as-built
`DividendEvent` has exactly three fields (`symbol`, `dividend_per_share`,
`ex_date_utc`) and **cannot carry a declaration timestamp**. The no-leakage
rule "Only dividends declared before the formation signal enter the event
calendar" therefore cannot be enforced on the declared record type; it needs an
auxiliary fixture record (precedent: `BorrowLocate`), or a DividendEvent
extension. Booking remains expressible today, so E4 stands, but the stated
binding overstates the as-built factory. Tax character (qualified/ordinary) is
correctly declared UNAVAILABLE_PENDING_ENTITLEMENT with a declared fixture
boolean.

### Cost/borrow feasibility — PASS (marginal by its own honest arithmetic)
"all-in round trip of order 4–20 bps"; "a 0.5%-of-price quarterly event
captures roughly 2.5–20 bps, which the liquid-name friction can fully consume
at the high-r end; a 1.0–1.5%-of-price REIT event... comfortably above
friction, while at r near 0.95 it collapses below friction". Anchor core is
long-only, needs no locate; the hedged variant inherits full locate discipline
with "unavailable locate falls back to the unhedged variant (fail closed,
never a free short)". Entry NO_FILL skips the event entirely — no one-legged
capture. No free-fill, no halt-fill; earnings-window exclusion declared.

### Hidden crypto-family rescue — NO RESCUE (E6 = 1)
- vs funding-carry (closest shape in the pool, checked adversarially):
  observable (declared dividend + PIT ex-date + tax character vs perpetual
  funding rate), counterparty (taxable cum-date sellers and ex-date dealers vs
  perp counterparties), clock (event-driven ~6–7-session holds keyed to ex-dates
  vs funding-interval carry), control (qualified low-yield placebo with r ≈ 1
  prediction — no analog in the rejected funding-carry lineages, whose placebo
  was a reversed funding sign). All four differ: not a rescue.
- vs M01: no order-flow observable; multi-day event clock.
- vs weekly reversal: keyed to ex-dates, not a periodic reversal score.

## 2. Rubric scoring

- E1 = 1; E2 = 1; E3 = 1 (REIT neighbour is theory-ranked; qualified low-yield
  control plausibly destroys the tax-penalty channel); E4 = 1 (booking
  expressible; O1 must be fixed in the fixture spec at freeze); E5 = 1;
  E6 = 1; E7 = 1 (0 HIGH/CRITICAL).

**Sum 7/7 — ELIGIBLE.**

## 3. Quality score: 7.0 / 10

Justification: the most honest self-assessment in the pool (thin post-2003
prior stated before any outcome; the Frank–Jagannathan alternative used to
justify the control), and the raw-price/liable-hedge design is exactly the A5
lens. Deductions: the base trade is old, crowded and probably post-2003 thin
by the proposal's own arithmetic; anchor and neighbour (top-yield tail vs
REITs) likely overlap heavily, weakening neighbour independence (O2); O1
binding discrepancy; endogenous-r capacity self-limit is declared but caps the
family's interest.

## 4. Objections

| id | severity | objection | resolution required |
|---|---|---|---|
| O1 | MEDIUM | `DividendEvent` as-built cannot carry the declaration timestamp the no-leakage rule requires; the pit_fields claim "AVAILABLE_IN_SYNTHETIC_FIXTURE_NOW (DividendEvent fixture)" overstates the factory | Freeze must declare the auxiliary declaration-record schema (or a DividendEvent extension) before S4 |
| O2 | MEDIUM | Anchor (non-qualified/top-yield-quintile) and neighbour (REITs) books substantially overlap; the neighbour's independent support is weaker than in the other families | Declare the overlap expectation at freeze; treat neighbour failure with coverage attribution |
| O3 | LOW | Ordinary-payer events are friction-consumed by the proposal's own arithmetic; realized family reduces to REIT/high-yield events | Report capture by liquidity/yield tier as declared |
| O4 | LOW | Carry-shaped analogy to funding-carry documented; no rescue (all four axes differ) | None |

## 5. Verdict

**ELIGIBLE** (7/7). No failed rubric items. Expected rank 6 under the frozen
rubric (quality 7.0).
