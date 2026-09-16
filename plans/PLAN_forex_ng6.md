# PLAN FOREX-NG6 — XAUUSD real-yield / USD dislocation

> Status: `PLANNED_NOT_STARTED` (2026-09-16). Authority: explicit owner
> directive 2026-09-16 (A1 dispatch: "FOREX-NG6, XAUUSD REAL-YIELD / USD
> DISLOCATION", budget 3 scored cells / 1 family, M0 methodology gate
> before D1, plan audit by fresh-context A7 before registration).
> Pre-cycle frontier evidence is committed under
> `research/control/ng5_ng6_frontier_2026-09/`: outcome-blind researcher
> dossier (construction-B direction preregistered outcome-blind BEFORE
> any measurement), cross-ancestry critique (verdict: CONDITIONAL,
> leaning hostile — the kill stack is named and priced in), bounded
> probes (TD XAU/USD live 1day, depth measured to 1979-12-26 via
> `/earliest_timestamp`; weekend bars exist and are non-flat; DFII10/
> DFII5 confirmed in the granted set; DTWEXBGS CANDIDATE_NOT_AUTHORIZED).
> A P0 close with zero scored cells is a valid result. Nothing in this
> plan is evidence of profitability.

## 0. Cycle identity

```text
cycle_id          FOREX-NG6
asset             forex
subtype           metal_fx_quote
plan              plans/PLAN_forex_ng6.md
branch            orca/forex-ng6-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/forex-ng6/integration
budget            3 scored cells max / 1 family max
go_phrase         GO FOREX NG6 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders
```

Family name (frozen): `XAUUSD REAL-YIELD / USD DISLOCATION`.

Classification disclosure (frozen): the broker convention is a forex/CFD-
style quote; the economic underlying is gold, a commodity. D2 ancestry
pools FOREX + COMMODITIES + RATES + gold-price families. The asset label
exists for data-plane routing only and must never be used to dodge
ancestry.

`PROSPECTIVE-SHADOW-V1` remains independent and `ACTIVE_LIGHT`. This
cycle must not read its PnL, trades, marks or verdicts. No budget, GO or
rescue is shared with STOCKS-NG5.

## 1. Question, in simple language

Gold is supposed to respond to real interest rates and the dollar: higher
real yields or a stronger dollar make holding gold relatively less
attractive. We ask one narrow question:

> Using only macro information available by a frozen decision time, does
> XAUUSD sometimes sit materially away from the response those real-yield
> and USD shocks imply — and does the direction of that dislocation, once
> preregistered, contain repeatable information about subsequent XAUUSD
> returns after price momentum, calendar, rates and commodity-positioning
> controls?

Owner-frozen falsifiable hypothesis (verbatim):

> After using only macro information available by the frozen decision
> time, XAUUSD occasionally deviates materially from the response implied
> by real-yield and USD shocks. A preregistered residual state may
> condition subsequent XAUUSD returns after price momentum, calendar,
> rates and commodity-positioning controls.

Forbidden claims (a proposal using them is invalid, not repairable by
wording): "real yield up always hurts gold"; "strong USD always hurts
gold"; "central banks are buying" (no data in evidence); "gold is a safe
haven" (unverified assumption).

## 2. Why this is a new cycle — honest ancestry disclosure

- **The instrument is new to the program.** Zero XAU references exist in
  any pin, plan or control artifact at the opening SHA (verified by the
  cross-ancestry critic). No scored XAUUSD family exists. XAUUSDT and
  generic gold indices are not this instrument; substitution is forbidden
  anywhere in the spec.
- **Gold price history has been consumed before, on a different plane:**
  COMMODITIES-NG1 `COMMNG1-A4-P2` scored the CFTC 088691 (GOLD/CMX)
  positioning pair against IAU-class ETP legs and was killed by the
  release-clock control (#17, P-24). That closure transfers as a
  mandatory control template, never an automatic veto.
- **The macro information set is NOT new to the program, and this plan
  does not pretend otherwise.** DFII10/DFII5 are already granted control
  series on both planes (RATES-NG1 §3 granted set, CADS pin), and the
  DGS10-LEVEL shadow is the program's most lethal control (falsification
  #14: 4.01x out-earn; #15: CTL-DGS10LEVEL +4.13/trade). The NG3/NG5
  "new evidenced information source" reopening law is therefore NOT
  satisfied by the macro side; this cycle is opened by explicit owner
  directive instead, and it accepts **prior-priced-kill status**: the
  named kill stack (§7) runs in full, and a measured death by it closes
  the cycle honestly at 0 cells.
- Prior kill stack named up front (critic-verified): DGS10-level
  #14/#15; FXFV9-A5-P1 real-rate-deviation frozen-representation veto
  0.3034; V4 carry closure rho 0.997-1.000; clock kills #16/#17;
  FOREX-NG5 E1 financing ceiling 18.07 bps (weekly-hold class); the
  unmeasured XAUUSD cost channel (§4 X-cost gate).

## 3. M0 — methodology contract gate (before D1; owner-mandated)

Shared contract with STOCKS-NG5 (identical law; see
`plans/PLAN_stocks_ng5.md` §3 for the full G1-G10 text): G1 same-family
detection; G2 sign-inversion is same-mechanism-different-direction; G3
shared-payoff trap must not merge different signals; G4 payoff
correlation is never a primary novelty metric; G5 the six primary
comparisons (target-weight Pearson AND Spearman, signal-rank correlation,
sign agreement, active-set Jaccard, decision overlap, exposure cosine)
each with hand-computed fixtures; G6 same-day/same-release samples
cluster to one effective observation; G7 price-only payoff controls
class as E_FALSIFICATION; G8 thresholds + aggregation frozen and hashed
before any candidate measurement, fail-closed on mismatch; G9 the 0.20
pooled |rho| bar is program law and the loader refuses any lower bar; G10
a deliberately wrong `signal × shared future return` kernel must FAIL the
suite.

Implementation lives under `research/control/forex_ng6_run/m0/` in the
integration worktree. If M0 does not PASS independently: no scored
research proceeds; the run records `BLOCKED_METHOD_CONTRACT`; D1 never
opens; budget stays 0/3.

## 4. Source authority and P0 gates

Price/instrument source: Twelve Data `XAU/USD` 1day under the existing
owner entitlement (`TWELVE_DATA_API_KEY`, never echoed). Macro sources:
the FRED granted set (re-pin, AX2 as-of semantics) plus P0-gated
candidates. Frontier probe facts this plan inherits (all sha-pinned):
XAU/USD served (45 bars, 2026-08-01..2026-09-14, meta "Precious Metal",
no volume field); depth to 1979-12-26; bars exist for ALL calendar days
including non-flat weekend bars; T-1 availability; never-existed pair
`ZZW/ZZQ` 404 shape recorded.

```text
F1 INSTRUMENT IDENTITY     prove the EXACT tradeable instrument: provider
                           TD, symbol XAU/USD, quote convention (USD per
                           troy ounce, "Precious Metal" class), no
                           volume field, and the classification
                           disclosure of §0. The cycle trades this quote
                           as the registered instrument or does not run.
F2 CLOCK + SESSIONS        freeze ONE daily-close convention: which of
                           the seven calendar-day bars is the decision/
                           fill price (weekend bars measured non-flat —
                           the Fri-close vs Sun-close choice is frozen at
                           P0, never resolved lazily); timezone/DST
                           fixtures; holiday behavior; T-1 availability
                           (measured) becomes the binding availability
                           rule.
F3 HISTORY + REVISIONS     full-depth census from the measured 1979-12-26
                           start; retrieved-once sha-pinned substrate;
                           vendor daily closes are treated as a
                           point-in-time snapshot at retrieval; any later
                           revision is annotated-and-kept, never silently
                           re-pulled; double-pull byte-identity test.
F4 COST AUTHORITY (the cycle's first-order kill gate)
                           TD is a data vendor, NOT a broker: spread,
                           commission, minimum size, tick/point value,
                           overnight swap points, triple-swap weekday and
                           margin are UNMEASURABLE from it. The owner
                           law is fail-closed: unless P0 evidences a
                           CITABLE, preregistered conservative
                           spread/commission/swap band (source quoted
                           bytes; no invented numbers; current spread
                           never applied to all history without a stress
                           regime), the cycle terminates
                           FOREX_NG6_BLOCKED_SOURCE_OR_COST with budget
                           0/3 and NO GLD fallback in-cycle. If a band is
                           evidenced, the D2 cost ceiling (P-21) runs on
                           it BEFORE any scored execution and the
                           family must survive stress tier 2.0 with the
                           triple-swap weekday stressed.
F5 MACRO AUTHORITY         real yield: DFII10/DFII5 re-pinned from the
                           granted set with AX2 as-of availability
                           (effective != publication; conservative
                           declared lag; no vintage fabrication;
                           ALFRED stays BLOCKED_DATA_AUTHORITY — not
                           retried). Nominal: DGS10/DGS2 (granted).
                           Breakeven: T10YIE/T5YIE (granted, controls
                           only). USD leg: DTWEXBGS is
                           CANDIDATE_NOT_AUTHORIZED (keyless candidate;
                           H.10 Monday-cadence measured — a Friday
                           decision cannot read that Friday's value;
                           revision behavior must be evidenced before
                           any grant) OR the outcome-blind lane's
                           constructed PIT-clean TD 5-leg basket, which
                           requires its own P0 authority row (weights,
                           availability, canaries) before use. Optional
                           risk-off controls (SPY, VIX-class) are
                           controls only — never the signal.
F6 FOLD FREEZE (Q-6)       three chronological folds frozen before any D2
                           diagnostic; recent-window population floors
                           measured on the frozen representation.
F7 REPRODUCIBILITY         census code, request manifests, digests, clock
                           contract, cost band source, folds committed
                           under research/control/forex_ng6_run/;
                           detached rerun reproduces or names a revision.
```

P0 is source engineering and census only: no candidate PnL, PF, Sharpe,
drawdown, survivors or S1 evidence. GLD/IAU may be pulled at P0 ONLY as
the Q-15 proxy-agreement diagnostic series, never as the tradeable
instrument.

## 5. D1 outcome-blind proposal contract

Only after M0 PASS and P0 PASS. Exactly ONE family enters D2 with at most
two constructions; if A and B are the same exposure in different
formulas, they are variants (arms) of the one family — the frontier lane
has already declared them ONE family (identical information set), with
any A/B separation reserved as an owner decision if D2 ever measures them
distinct.

```text
A MACRO-STATE RESPONSE     direction/state from aligned real-yield and
                           USD shocks (granted-set inputs per F5), frozen
                           decision-time rule.
B RESIDUAL DISLOCATION     expanding/PIT regression of XAUUSD response on
                           real-yield and USD shocks. DIRECTION
                           PREREGISTERED, outcome-blind, before any
                           measurement, by the frontier lane (binding on
                           D1): MEAN-REVERSION of the macro-implied
                           residual — the anchor fades the dislocation
                           (short when XAUUSD is above its macro-implied
                           path, long when below), unconditionally.
                           Mechanism: the inputs are themselves fast
                           market-price channels, so a material residual
                           reflects non-macro flow that unwinds;
                           continuation would collapse the family into
                           the momentum shadow that measurably killed
                           FOREX-NG5 (rho 0.230/0.353). Falsifier:
                           sign-inverted continuation control out-earns
                           the anchor (or anchor <= 0 with continuation
                           >= 0.5x positive) -> family falsified, no
                           sign-flip rescue.
```

Variants are arms consuming declared trial identities; total scored cells
<= 3. Proposal hashes freeze before any sanitized dry-run.

## 6. Mandatory controls and killers

```text
C1  PRICE-ONLY XAU MOMENTUM      same construction on XAUUSD prices alone
C2  REAL-YIELD-ONLY              yield state without USD interaction
C3  USD-ONLY                     USD shock state alone
C4  CLOCK-ONLY                   decision clock with no macro input —
                                 the P-24 kill class (#16/#17)
C5  SIGN-INVERTED                continuation-vs-reversal identity test
C6  DELAYED MACRO                +1w/+2w delayed macro books must NOT
                                 reproduce the anchor (Q-11 invalid-null
                                 distinction explicit)
C7  SHUFFLED RELEASE DATES       release-calendar sham (V5 house standard)
C8  GLD PROXY DIAGNOSTIC         Q-15 proxy-agreement only; never a
                                 substitute instrument, never scored
C9  NO-SWAP VS FULL-SWAP         reconciliation book pair
C10 HIGH-SPREAD / TRIPLE-SWAP    stress regime on the evidenced band
C11 PIT MUTATION                 one-session-earlier mutation must change
                                 or refuse the book
C12 NULL VALIDITY                autocorrelation + population reported
C13 ANCESTRY RHO                 pooled |rho| <= 0.20, frozen bar (G9)
```

## 7. D2 ancestry and feasibility gate (non-scored)

Measured on the frozen decision-grid representation (P-12: representation
committed before any rho). Mandatory battery (owner list + critic
additions):

```text
A1  XAUUSD MOMENTUM AND REVERSAL forms (price-only; first XAUUSD family,
    but gold price history is CONSUMED ancestry via COMMNG1-A4-P2
    088691/IAU — release-clock killed)
A2  USD-ONLY exposure forms
A3  REAL-YIELD-ONLY forms
A4  NOMINAL-YIELD LEVEL — the DGS10-LEVEL shadow, falsification #14/#15;
    a level-vs-shape decomposition control is mandatory on every lane
    (RATES-NG1 §1 law)
A5  INFLATION/BREAKEVEN forms (FXFV8-A5-P1 dispersion ancestry;
    real-rate-deviation FXFV9-A5-P1 veto 0.3034 named)
A6  SPY RISK-OFF state
A7  VOLATILITY shadows
A8  DAY-OF-WEEK / SESSION geometry (FOREX-NG4 Friday class)
A9  MACRO RELEASE CLOCK (FOMC/CPI instants — census precedents exist)
A10 GLD MOMENTUM (diagnostic plane)
A11 COMMODITIES-NG1 CoT POSITIONING (gold 088691 release-clock template)
A12 RATES-NG1 CURVE/RELEASE families
A13 FOREX RATE-DIFFERENTIAL / CARRY ancestry (V4 closure 0.997-1.000)
A14 COST CEILING (P-21) — conservative spread + commission + swap vs the
    gross diagnostic band; if costs exceed the band, the family dies at
    D2 and consumes no scored cell; the FOREX-NG5 E1 financing ceiling
    (18.07 bps, weekly-hold killer) is the named precedent risk
```

D2 PASS requires: all vetoes survived, folds populated under F6, costs
chargeable and inside the ceiling under F4's evidenced band, no relabelled
level/carry/momentum/clock family (M0 battery adjudicates), proposal +
arm hashes frozen. Otherwise selection is empty and the cycle closes at
0/3.

## 8. Trading, costs and risk contract

```text
decision        frozen daily-close grid point where ALL macro inputs are
                available under the F5 availability rules (T-1 price
                availability measured; macro AX2 as-of); weekly-class
                holding windows declared per arm; no intra-week retrade
entry/exit      next frozen daily close; force-flat at fold boundary
universe        XAUUSD only; the registered instrument of F1; long/short
                allowed ONLY because the instrument quote supports both —
                gross cap 1.0, no leverage
accounting      price PnL + full swap accrual per holding day (C9
                reconciliation); raw and financing-adjusted books both
                reported (FOREX-NG5 E1 law)
costs           evidenced conservative band only (F4); stress tier 2.0
                incl. triple-swap weekday; break-even margin reported
claims          no claim on gross-only or no-swap performance
```

## 9. Execution phases and ownership

```text
M0  methodology golden tests (§3) — gate before D1
P0  F1-F7 instrument/cost/macro authority gates (F4 fail-closed)
D1  constructions A + B (direction preregistered §5), outcome-blind
D2  ancestry/novelty + feasibility + cost ceiling (non-scored)
S   selection + exact arm/data/fold/config hash freeze
I   isolated implementation lanes; A1 integrates one handoff at a time
Z   sanitized exact-arm dry-run + recursive leak scan
A7  fresh-context independent prelaunch audit; zero unresolved HIGH/CRITICAL
GO  owner types `GO FOREX NG6 SCORED EXECUTION` at this cycle's own gate;
    early/paraphrased GO dies unconsumed (P-8)
E   at most 3 scored cells under the machine-wide heavy lock
R   detached reproduction from committed artifacts
T   terminal audit and two-half close
```

All delegated lanes write `zcode_orch_v3_handoff@1` JSON to their exact
dispatch path. Lanes never merge, rebase, push, edit registries/ledgers
or read other lanes' outcomes.

## 10. Trial accounting and result language

Observed and published trials counted separately; every computed cell
consumes an observed slot even if publication fails; unused slots are not
reassigned. `D2 eligible` means only "allowed to be tested" — never
profitable, robust or promotable. Forex denominators currently 48/48;
program 257/260 (P-9) — this cycle starts at budget 0/3.

## 11. Prewritten terminal outcomes

```text
FOREX_NG6_BLOCKED_METHOD_CONTRACT
FOREX_NG6_BLOCKED_SOURCE_OR_COST
FOREX_NG6_BLOCKED_SOURCE_OR_SCHEMA
FOREX_NG6_BLOCKED_DATA_OR_SELECTION
FOREX_NG6_BLOCKED_PRELAUNCH
FOREX_NG6_REJECT_ALL
FOREX_NG6_INCOMPLETE_NOT_PROMOTABLE
FOREX_NG6_TECHABORT_PRESERVED
```

A correct early close (most likely at F4 or D2) is success of governance,
not failure of engineering. This plan contains no predeclared survivor
outcome.

## 12. Boundaries

- No new paid source, signup, API key, credential or broker account;
  keys never echoed; no terms accepted on the owner's behalf.
- No XAUUSDT, generic gold index or GLD substitution for the registered
  instrument anywhere in the spec.
- No S1 access and no paper/testnet/live orders.
- No score before A7 authorization plus the fresh exact owner GO.
- No pushes or writes to `.zcode/`.
- `CYCLE_REGISTRY.json` changes only through `researchctl`.
- One heavy job machine-wide; never kill a foreign worker.
- Shadow valuation remains light and independent.
- No budget/GO/rescue sharing with STOCKS-NG5.

## 13. Immediate actions

```text
1. Commit this plan and the frontier evidence by exact pathspec.
2. Independent fresh-context adversarial plan audit (A7).
3. Remediate every valid HIGH/CRITICAL finding; re-audit with a NEW
   fresh-context A7 if the verdict was REFUSED.
4. Register FOREX-NG6 through researchctl as PLANNED_NOT_STARTED.
5. Bootstrap the integration worktree; run M0 golden tests; PASS required
   before D1.
6. Dispatch P0 only after registration; the F4 cost-authority gate runs
   early; stop at the scored prelaunch gate and wait for the exact owner
   GO.
```
