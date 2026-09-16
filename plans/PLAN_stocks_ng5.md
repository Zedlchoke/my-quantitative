# PLAN STOCKS-NG5 — QQQ/SPY relative-breadth rotation

> Status: `PLANNED_NOT_STARTED` (2026-09-16). Authority: explicit owner
> directive 2026-09-16 (A1 dispatch: "STOCKS-NG5, QQQ/SPY
> RELATIVE-BREADTH ROTATION", budget 3 scored cells / 1 family, M0
> methodology gate before D1, plan audit by fresh-context A7 before
> registration). Pre-cycle frontier evidence is committed under
> `research/control/ng5_ng6_frontier_2026-09/`: outcome-blind researcher
> dossier (frozen anchor L=13w z104 + L=4/L=52 sensitivity arms, LEVEL
> neighbour, 8 ordered falsification kills), cross-ancestry critique
> (verdict: CONDITIONAL — no breadth-ratio row exists in any dead family,
> but three measured exposure-form shadows bind), and bounded probes
> (QQQ/SPY/QQEW/RSP all HTTP 200 with `adjusted_close`; never-existed
> canary 404 shape recorded; earliest served: QQEW 2006-04-25 — the common
> window binds there; band-cost constants located). A P0 close with zero
> scored cells is a valid result. Nothing in this plan is evidence of
> profitability.

## 0. Cycle identity

```text
cycle_id          STOCKS-NG5
asset             stocks
plan              plans/PLAN_stocks_ng5.md
branch            orca/stocks-ng5-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng5/integration
budget            3 scored cells max / 1 family max
go_phrase         GO STOCKS NG5 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders
```

Family name (frozen): `QQQ/SPY RELATIVE-BREADTH ROTATION`.

`PROSPECTIVE-SHADOW-V1` remains independent and `ACTIVE_LIGHT`. This cycle
must not read its PnL, trades, marks or verdicts when proposing or
selecting. The two sibling pre-cycles (FOREX-NG6) share no budget, no GO
and no rescue path with this cycle.

## 1. Question, in simple language

QQEW tracks the equal-weighted NASDAQ-100; RSP tracks the equal-weighted
S&P 500. The ratios QQEW/QQQ and RSP/SPY rise when breadth is improving
(more of the index is participating) and fall when gains concentrate. We
ask one narrow question:

> After a weekly decision, using only information available at that
> decision, does the relative-breadth state between equal-weight and
> cap-weight proxies contain repeatable information about whether to hold
> QQQ or SPY for the following week — beyond what relative price
> momentum, volatility, sector/tech beta, and the calendar already explain?

Anchor construction (frozen): long-only, 100% QQQ or 100% SPY, no
leverage, no shorting, total-return accounting, next-session executable
fill, force-flat or rotate strictly per the frozen weekly rule.

## 2. Why this is a new cycle — and its honest ancestry risk

- No scored family in the frozen ancestry consumed equal-weight/cap-weight
  breadth ratios as its information source. The NEAREST dead ancestor is
  STOCKS-FREE-V2 `A4_XSEC_ETF_RELATIVE_MOMENTUM` (12-1 month relative
  momentum across 12 sector ETFs; killed because the bottom-3 control
  earned 96.5% of anchor expectancy — long sector beta dominated ranking
  information). A 2-asset QQQ/SPY rotation is exposed to the identical
  confound: **this family must not receive credit merely because QQQ
  outperformed SPY during a technology bull market.** The relative-
  momentum-only control and the beta-decomposition battery exist to kill
  exactly that reading.
- Breadth-via-ETF-ratio deliberately avoids the forbidden shortcut: no
  constituent history may be reconstructed from today's index membership,
  and current membership may never be presented as historical membership.
- STOCKS-NG1..NG4 died on other frontiers (declared intent, amendments,
  earnings entitlement, FINRA terms) — no measured kill exists for this
  observable, and none is assumed. Novelty is a proposal claim until the
  exact D2 ancestry measurement passes.
- **A7-F3 remediation (closest book-geometry ancestor, disclosed):**
  STOCKS-FREE-V2 `A5-SFV2-TREND-DEFENSIVE` — TSM12 + vol-target defensive
  rotation between ETF and cash, a weekly binary index-ETF book — died on
  MDD 23.22% > 15% and fold-positive-share 60.7% > 50%. The anchor shares
  its two-book weekly rotation geometry; Stage-A MDD/fold-share and the
  R2 beta-dominance kill bind this cycle; no additional gate is required,
  but this disclosure must travel with every D2 measurement.
- Cross-plane control template: the QuantPulse IF1/IF2 rows
  (`research/wayfinder/external/quantpulse_dossier_extracted.txt`) recorded
  that an index-futures causal/tape mechanism (MNQ) with train IC +0.063
  collapsed to −0.005 out of sample — index-level causal conditioning has
  one measured dead instance; it enters the D2 battery as a control
  template, never as an automatic veto.

## 3. M0 — methodology contract gate (before D1; owner-mandated)

> Forward-only amendment 2026-09-16 (owner directive round 2 + A2 review):
> the golden suite now runs ELEVEN gates — G4's dead `or True` form is
> replaced by an AST purity proof (`verify_verdict_purity`: exact signature
> + frozen name whitelist, closing the optional-param and module-global
> bypass shapes demonstrated by the A2 reviewer) and **G4N** is added as a
> negative control proving a payoff-contaminated verdict variant FAILS the
> fixture. The binding suite is G1–G10 + G4N = 11/11 PASS. The M0
> machinery hash and the D2 shadow inventory v2
> (`d2_shadow_inventory_freeze_v2.json`, self-hashed pre-rho, with the
> fail-closed UNMEASURABLE clause and the not-constructible register) are
> the binding D2 inputs.

M0 builds and runs synthetic/golden tests for the D2 structural-novelty
machinery this cycle (and, by shared contract, FOREX-NG6) will use. Code
and fixtures live under `research/control/stocks_ng5_run/m0/` in the
integration worktree. M0 PASS is required before D1 dispatch.

```text
G1 SAME-FAMILY DETECTION   two deterministic transforms of one signal
                           series (z-score vs rank) must be flagged
                           SAME_FAMILY by the primary-comparison battery.
G2 SIGN-INVERSION          negating a signal must produce the verdict
                           SAME_MECHANISM_DIFFERENT_DIRECTION (negative
                           weight Pearson, ~0 sign agreement, low long-book
                           decision overlap) — an inverted form may never
                           register as a new family; it is an arm/control.
G3 SHARED-PAYOFF TRAP      two genuinely different signal series multiplied
                           by the SAME future returns must NOT be merged:
                           the verdict must stay DIFFERENT_FAMILY when the
                           six primary signal-space comparisons are under
                           threshold, even though payoff correlation is 1.
G4 NO PAYOFF-CORRELATION PRIMARY   structural novelty verdicts must not use
                           payoff/PnL correlation as a primary metric; the
                           frozen primary vector is exactly the six
                           comparisons of G5. A code path that feeds payoff
                           correlation into the primary verdict must fail.
G5 PRIMARY COMPARISONS     six comparison families, seven named metrics
                           (A7-F5: Pearson and Spearman counted
                           separately): target-weight Pearson AND
                           Spearman; signal-rank correlation; sign
                           agreement; active-set Jaccard overlap;
                           decision overlap; exposure cosine similarity —
                           each with a hand-computed fixture asserting
                           the exact expected value.
G6 CLUSTERING OF SHARED INSTANTS   samples sharing a decision date (or a
                           macro release) are one observation: a synthetic
                           N-symbol same-date panel must collapse to
                           n_dates effective observations, never n_rows.
G7 PRICE-ONLY CONTROL CLASSING     price-only payoff controls are classified
                           E_FALSIFICATION (E-stage evidence), never as
                           structural-novelty comparators.
G8 FREEZE BEFORE MEASUREMENT       thresholds + aggregation rule are written
                           to a frozen, hashed contract BEFORE any candidate
                           measurement; measurement refuses (fail-closed)
                           on contract-hash mismatch.
G9 NO THRESHOLD RESCUE     the pooled |rho| <= 0.20 bar is program law; the
                           contract loader must refuse any lower bar — being
                           vetoed by NG1-NG3-class shadows is not grounds to
                           move the bar.
G10 WRONG-IMPLEMENTATION SENSITIVITY  a deliberately wrong D2 kernel that
                           computes signal × shared future return must FAIL
                           the golden suite (the tests are proven able to
                           catch the lookahead/payoff-correlation variant).
```

If M0 does not PASS independently: no scored research proceeds; the run
records `BLOCKED_METHOD_CONTRACT`; D1 never opens; budget stays 0/3.

## 4. Source authority and P0 gates

Primary source: EODHD end-of-day US ETF channels under the existing owner
entitlement (`EODHD_API_KEY`, never echoed; V13/V8 precedent). Instruments:
QQQ, SPY (cap-weight legs), QQEW, RSP (equal-weight breadth legs).

```text
F1 ENTITLEMENT + TERMS     P-25 three-layer gate (reachable / permitted /
                           served), run FIRST before any bulk retrieval:
                           reachable — all four symbols probed HTTP 200
                           (frontier probes, sha-pinned); permitted — the
                           owner's paid EODHD entitlement covering
                           research use of served EOD data (V8-precedent
                           terms evidence re-quoted, never assumed);
                           served — the /eod channel returns full-depth
                           history for all four instruments. Any symbol
                           the channel does not serve fails the family
                           closed (no substitute instrument in-cycle).
F2 LIVENESS + RETRIEVAL    canaries at window start/middle/recent end;
                           double-pull byte-identity; raw sha256 pinned;
                           P-7 canaries: one never-existed ticker must
                           reproduce identical absent-semantics.
F3 RAW/ADJUSTED + ACTIONS  raw and adjusted channels separated; the
                           `adjusted_close` dividend channel is measured
                           live (QQQ adj == close after the 2026-06 ex-date,
                           ~$0.82 divergence before); split handling
                           evidenced against a SEC-pinned fact (V8
                           convention: CMG 50:1, TJX 2:1 method); no split
                           exists in these four instruments to reconcile
                           fresh — recorded honestly; total-return
                           reconstruction contract frozen (which channel
                           is TR-authoritative and why; A7-F6: the TR
                           series is frozen once at the P0 substrate
                           freeze and later re-pulls never restate
                           history — annotate-and-keep).
F4 COMMON HISTORY          common window across all four symbols; measured
                           earliest served: QQEW 2006-04-25 (binding),
                           RSP 2003-04-30, QQQ 1999-03-10, SPY 1993-01-29;
                           missing sessions censused against the NYSE/
                           Nasdaq calendar; half-days flagged.
F5 CLOCK + EXECUTION       timezone/DST fixtures; ONE frozen weekly decision
                           clock (decision based on data through a named
                           session close; fill at the NEXT regular-session
                           open); force-flat/rotate rule frozen textually;
                           availability convention bar-readable close+1
                           (V7 law).
F6 COSTS                   frozen measured band schedule
                           `BAND_BPS = {A:10, B:15, C:25}` bps/fill (ADV
                           bands 50M/10M/2M, fail-closed; A7-F1 remediated
                           quote of the pinned kernel: exit fills are
                           charged the instrument's OWN measured band via
                           `resolve_exit_band_bps`, and the C ceiling is
                           applied only to exits that cannot be rated —
                           `research/assets/stocks/
                           kernel_band_cost_v9.py` lineage, TRACKED_CLEAN
                           at f1fba3c4); P0 must measure the ADV band of
                           QQQ/SPY per window fail-closed (band A is a
                           hypothesis until measured); frontier ceiling
                           arithmetic: weekly rotation ≈ 52×2 fills ⇒
                           1,040 bps/yr at band A up to 2,600 bps/yr
                           absolute-worst at band C, stress tier 2.0
                           doubles (2,080–5,200); break-even margin
                           definition frozen; the ceiling is never
                           re-derived after numbers exist (P-21/P-15).
F7 BENCHMARK CONSTRUCTION  QQQ B&H, SPY B&H, static 50/50 (rebalanced per
                           frozen rule), risk-matched passive benchmark —
                           total-return basis identical to the anchor's.
F8 FOLD FREEZE (Q-6)       three chronological folds frozen before any D2
                           diagnostic exists; recent-window population
                           floors measured (decision counts per fold; the
                           nearest-window ceiling, not the archive average).
F9 REPRODUCIBILITY         census code, raw-request manifest, digest
                           manifest, calendar/clock contract, cost bands,
                           folds committed under research/control/
                           stocks_ng5_run/; detached rerun reproduces
                           counts and digests or names a source revision.
```

P0 is source engineering and census only. It may NOT compute candidate
PnL, PF, Sharpe, drawdown, survivors or S1 evidence.

## 5. D1 outcome-blind proposal contract

Only after M0 PASS and P0 PASS. At most THREE constructions enter D2:

```text
1 anchor                 the relative-breadth rotation as specified §1
1 structural neighbour   one materially different construction of the SAME
                         family (e.g. persistence vs exhaustion of the
                         breadth spread). If exhaustion is only the
                         sign-inversion of persistence, it is an ARM of the
                         anchor family, never an independent family.
1 mandatory inverted/delayed control   sign-inverted breadth and/or
                         one-week-delayed breadth as the preregistered
                         falsification control.
```

The outcome-blind proposal dossier from the frontier lane
(`research/control/ng5_ng6_frontier_2026-09/handoffs/
stocks_ng5_researcher.json`) is binding input, frozen before any return is
visible: primary anchor = L=13-week change of the combined equal-weight/
cap-weight log-spread, z-scored over 104 weeks; declared sensitivity arms
L=4 and L=52 (never a grid); neighbour = LEVEL form (regime z of the
spread level) with a preregistered self-subsumption rho <= 0.98 check
(P-20); weekly clock = decision on the last regular-session close, fill
next session open, fail-closed skip rule; per-fold force-flat; per-period
series persisted (P-11). Sign (rising breadth -> QQQ) is declared
hypothesis, both directions economically arguable ex ante. Variants are
arms consuming declared trial identities; total scored cells <= 3
(A7-F7: the budget counts declared scored arm identities only — the
allocation across anchor/arms is frozen at selection, and the mandatory
controls are falsification comparison books that consume no scored
slots).

## 6. Mandatory controls and killers

```text
C1  QQQ BUY-AND-HOLD        C2  SPY BUY-AND-HOLD
C3  STATIC 50/50 QQQ-SPY    C4  RISK-MATCHED PASSIVE BENCHMARK
C5  RELATIVE-MOMENTUM-ONLY  same construction on price ratios alone
C6  VOLATILITY-ONLY         vol-state construction alone
C7  WEEKLY CLOCK-ONLY       rotation clock with no breadth input — the
                            P-24/COMMODITIES-NG1 clock-geometry kill class
C8  SIGN-INVERTED BREADTH   C9  BREADTH DELAYED ONE WEEK
C10 QQEW/QQQ-ONLY           one-proxy family forms
C11 RSP/SPY-ONLY
C12 PIT MUTATION            one-session-earlier mutation must change or
                            refuse the book
C13 NULL VALIDITY           autocorrelation + population of each null
                            reported; Q-11 invalid-null distinction
C14 ANCESTRY RHO            pooled |rho| <= 0.20 on the frozen weekly grid
```

If a momentum/volatility/clock/beta shadow explains the anchor, the family
dies. Regime honesty: folds must span at least one major QQQ-underSPY and
one QQQ-overSPY regime; a family that only earns inside one regime fails
fold coverage. Raw PnL in a tech bull market is never the evidence; the
anchor must beat C3/C4/C5 after costs on the preregistered Stage-A gates.

## 7. D2 ancestry and feasibility gate (non-scored)

Mandatory ancestry battery, measured on the frozen decision grid
(P-12 representation identity; representation committed before numbers):

```text
A1 QQQ/SPY RELATIVE MOMENTUM (price-form; V2 ancestor template)
A2 ABSOLUTE MOMENTUM forms (momentum_63s generic shadow)
A3 VOLATILITY level/shock shadows (V4 vol-level class)
A4 LIQUIDITY/dollar-volume shadows
A5 DAY-OF-WEEK / MONTH-END clock geometry (FOREX-NG4 Friday class)
A6 SPY BETA decomposition — does the book just hold more QQQ when QQQ is hot
A7 TECH-SECTOR BETA — breadth vs sector-tilt separation control
A8 RATES/REAL-YIELD STATE shadows (cross-plane template from RATES-NG1)
A9 STOCK TREND/REVERSAL FAMILIES — V2 relative momentum, V4 semivariance
   (vol-level control +53.14% class), SFV2-A5 TREND-DEFENSIVE
   book-geometry; momentum_63s (A7-F4 corrected attribution: it killed
   the V11 mandatory filing-event lanes at 0.219/0.2192, while the V13
   mandatory lane died vs vol_level at 0.232/0.2402); MANDATORY SFV13
   dividend-policy decomposition — the QQEW/QQQ ratio embeds dividend
   policy, so the spread must be decomposed into price-only and
   distribution-only components, or the family dies as a dividend
   artifact.
A10 MNQ CAUSAL/TAPE FAILURE class (QuantPulse IF1/IF2 template)
```

D2 PASS requires: pooled |rho| <= 0.20 against the full same-plane shape
inventory and all ten templates; folds populated under F8; turnover
chargeable under F6 bands; no family identity that is a relabelled
momentum/clock/beta family (M0 battery adjudicates); proposal + arm
hashes frozen. A7-F2 remediation: the same-plane shadow inventory is
ENUMERATED AND FROZEN as a committed list BEFORE any rho computation
(P-12); measuring against an under-enumerated inventory is an invalid
PASS and fails D2 fail-closed. Otherwise selection is empty and the
cycle closes at 0/3.

## 8. Trading, costs and risk contract

```text
decision        frozen weekly clock (F5); macro/PIT availability rules N/A
                (price-only family); bar-readable close+1 availability
entry/exit      next executable regular-session open; hold to next decision;
                force-flat at fold boundary
universe        QQQ, SPY only; long-only; no leverage; no short
accounting      total-return (adjusted channel per F3 contract)
costs           measured band schedule charged once per fill; stress tier
                2.0 + break-even margin
gross cap 1.0   PREREGISTERED SYMBOL-CAP AMENDMENT: the inherited stocks
                symbol cap 0.10 (PLAN_stocks_ng4 §7 lineage) is infeasible
                for a 100%-single-ETF rotation book; THIS PLAN amends it
                for this cycle only — instrument weight is structurally
                1.0 in {QQQ, SPY} by the anchor form itself, disclosed
                before any number exists. The mandatory compensating
                controls are C3/C4 (static 50/50, risk-matched passive)
                and the A6/A7 beta decomposition; without them the book
                is unscoreable, with them concentration risk is measured
                against those benchmarks rather than hidden by a cap.
claims          no claim on gross-only performance; no survivor claim
                without all of: expectancy, PF, folds, drawdown, stress,
                drop-one, benchmark-excess
```

## 9. Execution phases and ownership

```text
M0  methodology golden tests (§3) — gate before D1
P0  F1-F9 source authority + census gates
D1  anchor + neighbour + inverted/delayed control freeze (outcome-blind)
D2  ancestry/novelty + feasibility measurement (non-scored)
S   selection + exact arm/data/fold/config hash freeze
I   isolated implementation lanes; A1 integrates one handoff at a time
Z   sanitized exact-arm dry-run + recursive leak scan
A7  fresh-context independent prelaunch audit; zero unresolved HIGH/CRITICAL
GO  owner types `GO STOCKS NG5 SCORED EXECUTION` at this cycle's own gate;
    early/paraphrased GO dies unconsumed (P-8)
E   at most 3 scored cells under the machine-wide heavy lock
R   detached reproduction from committed artifacts
T   terminal audit and two-half close
```

All delegated lanes write `zcode_orch_v3_handoff@1` JSON to their exact
dispatch path. Lanes never merge, rebase, push, edit registries/ledgers or
read other lanes' outcomes.

## 10. Trial accounting and result language

Observed and published trials counted separately; every computed cell
consumes an observed slot even if publication fails; unused slots are not
reassigned. `D2 eligible` means only "allowed to be tested" — never
profitable, robust or promotable. Stocks denominators currently 42/42;
program 257/260 (P-9) — this cycle starts at budget 0/3.

## 11. Prewritten terminal outcomes

```text
STOCKS_NG5_BLOCKED_METHOD_CONTRACT
STOCKS_NG5_BLOCKED_SOURCE_OR_SCHEMA
STOCKS_NG5_BLOCKED_DATA_OR_SELECTION
STOCKS_NG5_BLOCKED_PRELAUNCH
STOCKS_NG5_REJECT_ALL
STOCKS_NG5_INCOMPLETE_NOT_PROMOTABLE
STOCKS_NG5_TECHABORT_PRESERVED
```

A correct early close is success of governance, not failure of engineering.
This plan contains no predeclared survivor outcome.

## 12. Boundaries

- No paid source beyond the existing entitlements, no signup, no API key
  or credential request; keys never echoed.
- No S1 access and no paper/testnet/live orders.
- No constituent-history reconstruction from current index membership.
- No score before A7 authorization plus the fresh exact owner GO.
- No pushes or writes to `.zcode/`.
- `CYCLE_REGISTRY.json` changes only through `researchctl`.
- One heavy job machine-wide; never kill a foreign worker.
- Shadow valuation remains light and independent.
- No budget/GO/rescue sharing with FOREX-NG6.

## 13. Immediate actions

```text
1. Commit this plan and the frontier evidence by exact pathspec.
2. Independent fresh-context adversarial plan audit (A7).
3. Remediate every valid HIGH/CRITICAL finding; re-audit with a NEW
   fresh-context A7 if the verdict was REFUSED.
4. Register STOCKS-NG5 through researchctl as PLANNED_NOT_STARTED.
5. Bootstrap the integration worktree; run M0 golden tests; PASS required
   before D1.
6. Dispatch P0 only after registration; stop at the scored prelaunch gate
   and wait for the exact owner GO.
```
