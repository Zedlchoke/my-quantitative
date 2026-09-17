# PLAN STOCKS-SEARCH-V1 — bounded construction-blind strategy search (owner-relaxed acceptance)

> Status: `PLANNED_NOT_STARTED` (2026-09-17). Authority: explicit owner
> instruction 2026-09-17, verbatim: "mở cycle tìm kiếm strategy overfit tí
> xíu cũng được Cho stocks và forex". Frozen English reading (authoritative
> for gates): open a strategy-search cycle for stocks; a MILD, BOUNDED amount
> of overfit is acceptable in the acceptance statistics. The relaxation is
> frozen in §3 and nowhere else. This plan is audited by fresh-context A7
> before registration. A P0/D2 close with zero scored cells is a valid
> result. Nothing in this plan is evidence of profitability.

## 0. Cycle identity

```text
cycle_id          STOCKS-SEARCH-V1
asset             stocks
plan              plans/PLAN_stocks_search_v1.md
branch            orca/stocks-search-v1-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/stocks-search-v1/integration
budget            3 scored cells max
go_phrase         GO STOCKS SEARCH V1 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders
```

`PROSPECTIVE-SHADOW-V1` remains independent and ACTIVE_LIGHT; this cycle
never reads its PnL, trades, marks or verdicts. FOREX-SEARCH-V1 is a sibling
cycle under the same owner instruction; the two share NO budget, no GO and no
rescue path. The name STOCKS-NG7 is deliberately NOT used: the DATA-EDGE-
UNLOCK-V1 closure reserved it for an FTD-successor that this cycle is not.

## 1. Question, in simple language

> On the death-inclusive single-name daily grid, does ANY construction in a
> frozen, pre-enumerated grid of standard conditioning classes — event
> unwind/reclaim, gap, 52-week-high proximity, range/CLV accumulation,
> volume-shock, volatility-regime — predict positive multi-session forward
> drift net of costs, under an acceptance battery whose overfit-sensitive
> statistics have been relaxed by a bounded owner grant?

This is a SEARCH cycle, not a one-family probe: breadth is the point. The
grid is frozen before any measurement; selection inside the grid is
construction-based and outcome-blind; every scored evaluation is honest
trial accounting.

## 2. Why this cycle is legal — reopening ancestry (audit item #1)

Standing law at the stocks frontier (STOCKS-NG6 terminal, 2026-09-17):
"reopening: materially new evidenced source or owner plan naming a changed
killer." STOCKS-NG6's family died at D2 R0_VETO_ALL with measured event-
conditional rho 0.260 / 0.219 / 0.201 against the immovable 0.20 floor, on a
P0-proven feasible data plane (2,169 symbols, 3.21M rows, folds 1,136/1,495/
694). Nothing about the data plane changed here — NO new source is claimed.
What changed is the killer: the owner instruction of 2026-09-17 names the
acceptance battery as changed, per the reserved second branch of the
reopening clause. This is an owner-plan-named changed killer, DISCLOSED as
such and never dressed up as new information. A7 must adjudicate that this
reading is faithful to the reserved clause (audit item #1).

Other ancestry facts that must not travel silently:

- The claim "the 0.20 bar killed every NG proposal" is FALSE as stated
  (NG6 §2 correction re-inherited): crypto ng 10/10 killed, FXNG1 4/4,
  RATES 1/4, VOL 2/4, COMM 1/4 were eligible. The relaxed floor is not a
  response to a universal kill; it is a bounded owner grant.
- STOCKS-NG3 (EODHD fundamentals 403) and STOCKS-NG4 (FINRA ToU) stay dead;
  this cycle consumes ONLY the `/eod` channel and no fundamentals, earnings,
  short-interest or FINRA input exists by design.
- DATA-EDGE-UNLOCK-V1 Lane S law re-inherited: FTD/N-PORT historical scored
  use is RETROSPECTIVE_ONLY; they do not enter this cycle in any form.

## 3. Owner-grant relaxation ledger (frozen BEFORE any measurement)

The owner grant relaxes EXACTLY these axes, for THIS program only:

```text
axis                        standing value              this program
-------------------------------------------------------------------------
R0 ancestry veto floor      pooled |rho| <= 0.20        <= 0.30 (owner)
DSR deflation set N         program-cumulative ~260     frozen grid size
                            (P-9)                       (<= 120, §5)
DSR alpha                   0.05                        0.10
search breadth              1 family + 1 neighbour      <= 120 enumerated
                                                        configurations
```

Boundedness argument, frozen: 0.30 is a 50% relative relaxation of the
standing floor, chosen before any this-cycle rho exists; it re-admits the
STOCKS-NG6 measured class (0.201–0.260, public committed history) and does
NOT re-admit the FOREX-NG5 momentum kill class (0.353). alpha 0.10 is one
notch. Every result artifact prints BOTH the standing and relaxed values.

NOT relaxed (mission invariant, non-negotiable): data identity and PIT
class, cost bands and stress-2.0 primary, R1 net expectancy > 0, R2/R3/R5/
R6 control-out-earn rules, fold structure, per-fold population floors,
death-censoring contract, drop-one stability, PBO < 8, concentration <= 50%,
MDD <= 15%, SPY-excess fold rule, reproduction, trial accounting, S1 seal,
GO-at-gate. If a survivor exists it must clear the battery EXCEPT on the
three relaxed axes. Being vetoed at 0.30 is not grounds to move the bar
again in-cycle; a further relaxation is a NEW owner instruction and a NEW
cycle.

## 4. Source authority and P0 gates

Primary scored source: EODHD `/eod` daily OHLCV incl. delisted, owner
entitlement (`EODHD_API_KEY`, never echoed; V8/V13/NG6 precedent). The
family consumes ONLY the `/eod` channel.

```text
F1 ENTITLEMENT + TERMS     P-25 three-layer gate (reachable/permitted/
                           served) FIRST; death-inclusive priced cohort
                           re-pinned by THIS cycle's own P0.
F2 LIVENESS + RETRIEVAL    canaries at window start/middle/recent end;
                           double-pull byte-identity; raw sha256 pinned;
                           never-existed ticker canary.
F3 RAW/ADJUSTED + ACTIONS  adjusted (total-return) series is THE single
                           representation (P-12); state and returns on the
                           same adjusted series; dividend-decomposition
                           NON-scored D2 check (distribution-dominated
                           event identity = fail-closed contamination).
F4 COHORT + COVERAGE       death-inclusive cohort census; per-name served-
                           session census; PER-FOLD IN-HORIZON DEATH CENSUS
                           (BC-7a) counted BEFORE any scored computation;
                           bookability floors $1.00 adjusted close / $2M
                           trailing 60-session median dollar volume declared
                           ex ante; warmup attrition CENSUSED.
F5 CLOCK + EXECUTION       ONE frozen daily decision clock (decision at t
                           close; fills at t+1 open and t+1+H opens);
                           bar-readable close+1 availability (V7 law);
                           timezone/DST fixtures.
F6 COSTS                   band schedule BAND_BPS = {A:10, B:15, C:25}
                           bps/fill on ADV bands {50M, 10M, 2M}, fail-closed
                           (kernel_band_cost_v9.py lineage, RULES §9);
                           cost once per fill; STRESS TIER 2.0 PRIMARY;
                           worst-case ceiling 25bps x 2 fills x 2.0 = 100
                           bps/round trip (P-21); band-C fraction measured
                           ON the fired population; majority-band-C => the
                           100 bps ceiling is the OPERATIVE stress number.
F7 BENCHMARK CONSTRUCTION  SPY buy-and-hold exposure-matched; C-RANDOM-
                           TIMING clock twin; total-return basis.
F8 FOLD FREEZE (Q-6)       three chronological folds frozen BEFORE any D2
                           diagnostic; RECENT-window fired-population floor
                           >= 30 decisions/fold measured at P2 (fail-closed
                           kill); folds span at least one major
                           deleveraging regime; 2008Q4–2009 and 2020-03
                           never share a fold.
F9 REPRODUCIBILITY         census code, raw-request manifest, digest
                           manifest, calendar/clock contract, cost bands,
                           folds, AND the frozen search-space manifest
                           committed under research/control/
                           stocks_search_v1_run/; detached rerun
                           reproduces.
```

P0 is source engineering and census only. It may NOT compute candidate
PnL, PF, Sharpe, drawdown, survivors or S1 evidence.

## 5. D1 — the frozen search-space contract (this cycle's core artifact)

Before any D2 diagnostic, this cycle commits a hashed
`search_space_manifest.json` enumerating EVERY configuration:

```text
grid cap          <= 120 configurations total
config ID         SSS-<FAMILY>-<PARAMKEY>, stable, lexicographic
families (6)      with FROZEN parameter sub-grids, all parameters declared
                  from construction logic (Q-12), never tuned:
 1 EVENT-UNWIND   failed K-session-low breakdown w/ same-session reclaim,
                  K in {21, 63, 252} x hold H in {5, 10, 20}
                  (NG6 anchor class, grid-extended)
 2 GAP            overnight-gap fade and confirm, gap threshold at
                  {25th, 50th, 75th} percentile of trailing 252-session
                  gap distribution, H in {1, 5}
 3 52W-HIGH       proximity-to-252-session-high drift, band in
                  {2%, 5%, 10%} below the high, H in {5, 20}
 4 CLV-RANGE      20-session CLV accumulation slope state (NG7 class
                  adapted), slope window in {5, 10}, H in {5, 10}
 5 DVOL-SHOCK     dollar-volume ratio vs trailing 60-session median,
                  ratio in {1.5x, 3.0x} x direction {fade, confirm},
                  H in {1, 5}
 6 VOL-REGIME     realized-vol tercile-conditional drift, lookback
                  {21, 63}, H in {5, 20}
long-only         no short leg (no borrow-cost authority — FOREX-NG6 F4
                  class); direction falsification by R1 + inversion-
                  SUBSTITUTE controls, honestly labelled.
```

Selection inside the grid (frozen BEFORE D2, outcome-blind): survivors of
D2 are ranked by (i) ancestry-distance tier (family's min measured |rho|
descending — construction property of the measurement, applied
mechanically), then (ii) P0 fired-population size descending, then (iii)
lexicographic config ID; the top <= 3 become scored candidates. NO
return, expectancy, PF, Sharpe or any performance statistic may be
computed for ANY configuration before the S freeze; a performance-based
narrowing at any point consumes scored cells for everything narrowed-on
and is a BLOCKED_METHOD_CONTRACT incident, not a do-over.

## 6. Mandatory controls and killers

Controls are falsification books, consume no scored slots. Each family's
complement/placebo control is declared in the manifest alongside its
configs; the generic battery runs for every scored candidate:

```text
C-COMPLEMENT        the family's own causal placebo (e.g. raw breakdown
                    without reclaim for EVENT-UNWIND; gap state without
                    direction for GAP; range-state without volume for
                    CLV-RANGE) — declared ex ante per family
C-RANDOM-TIMING     every-63rd-session H-session clock twin
C-CAL-HIST          deterministic calendar book matched to the fired-date
                    distribution; must NOT out-earn the candidate (R6
                    extends to it)
C-MARKET            SPY buy-and-hold, exposure-matched
C-DELAY-H           identical candidate entering H sessions late — Q-11
                    invalid-null class: out-earning delay converts to a
                    lookahead audit first, then feeds K6; never an
                    automatic kill
C-PIT-MUTATION      one-session-earlier recomputation changes/refuses the
                    book on every fired decision
C-NULL-VALIDITY     autocorrelation + population of every null reported
                    before any control may kill
```

R0 shadow inventory (ENUMERATED, hashed and committed BEFORE any rho;
under-enumerated inventory = invalid PASS, fail-closed): momentum_63s
generic; 12–1mo cross-sectional momentum; event-conditional 5d/21d return
and drawdown-depth short-term-reversal states (BINDING — sparse books
understate in cohort-wide rho); dollar-volume-shock state (event-
conditional, tagged); realized-vol LEVEL + semivariance share states
(event-conditional vol-tercile + vol-restricted shadows BINDING); rolling-
beta state; DGS10-LEVEL state; event-calendar geometry (P-24 class); V13
death-event proximity; STOCKS-NG5 relative-breadth rotation state;
dividend-decomposition divergence (non-scored, fail-closed if
distribution-dominated); 52-week-high proximity generic (this grid makes
it a candidate AND a shadow for other families — both roles hashed).

Ordered kill rules (first binding kills; all NET, total-return basis;
every control null-validated before it kills):

```text
R0  pre-score ancestry veto   pooled |rho| > 0.30 (owner-relaxed, §3) vs
                              ANY R0 shadow on the frozen decision grid
                              -> configuration dies pre-score; the 0.2010
                              standing value is printed alongside
R1  expectancy                net expectancy <= 0 at stress 2.0
                              -> REJECT_ALL
R2  long-market reduction     candidate <= max(C-MARKET, C-RANDOM-TIMING)
                              net expectancy -> REJECT; Stage-A requires
                              SPY-excess >= 2/3 folds, MDD <= 15%, largest-
                              fold PnL concentration <= 50%
R3  mechanism specificity     C-COMPLEMENT out-earns OR reproduces
                              >= 0.5x same-sign in >= 2/3 folds -> REJECT
R4  component placebo         family component-only book reproduces
                              >= 0.5x same-sign -> REJECT
R5  clock geometry            C-RANDOM-TIMING out-earns -> REJECT
K6  slow-drift combination    {candidate, C-DELAY-H} x {state, complement}
                              mutually indistinguishable within fold noise
                              (exact test frozen at S) -> REJECT
```

Plus the frozen stocks Stage-A gates on any survivor (UNCHANGED, §3):
fold-positive-share > 50% KILLS; largest-fold concentration > 50% KILLS;
SPY-excess positive >= 2/3 folds; MDD <= 15%; stress-2.0 net positive with
break-even margin; drop-one sign stability; death contract per BC-7 in
full (death-session open exit when served; DEATH_CENSORED legs excluded
from the numerator, reported separately; death-censoring invariance binds
the verdict AND every Stage-A gate); PIT mutation; per-period series
persisted (P-11) for DSR with N = frozen grid size at alpha 0.10
(owner-relaxed) AND program-cumulative ~260 at alpha 0.05 (reported, not
gating); PBO fail-closed < 8 configurations. Disposition rule: a control
that is unpopulated or has an invalid null is NOT_ADJUDICABLE, never
silently skipped.

## 7. D2 ancestry and feasibility gate (non-scored)

D2 measures, on the frozen P-12 representation and decision grid, for EVERY
grid configuration: the R0 inventory (relaxed 0.30 floor, per-configuration
pooled rho against the hashed shadow list), feasibility floors (F6/F8
forms), fired-population census, band-C fraction, control identifiability.
NO scored outcome is computed at D2. Configurations failing R0-relaxed or
feasibility die pre-score with their measured values committed. No future
publication may inform a past decision anywhere in D2. If fewer than one
configuration survives: selection empty -> close at 0/3.

## 8. Trading, costs and risk contract

```text
decision        frozen daily clock (F5); bar-readable close+1 availability
entry/exit      t+1 open / t+1+H open; force-flat at fold boundary and at
                death (last served session; DEATH_CENSORED flagged,
                included in censored-leg accounting)
universe        death-inclusive priced cohort; single-name; long-only;
                no leverage; no short; no stops
accounting      total-return (adjusted series); equal-notional per fired
                decision; portfolio book reported alongside for fold/MDD
                gates
costs           measured ADV bands charged once per fill; stress 2.0
                PRIMARY + break-even margin (P-2, Q-12 bar heights)
claims          D2 eligible means only "allowed to be tested" — never
                profitable; no survivor claim without all Stage-A gates
```

## 9. Execution phases and ownership

```text
M0  methodology golden suite (G1–G10 + G4N = 11/11, NG5/NG6 lineage)
    re-inherited BYTE-EXACT, re-run in this cycle's worktree under
    research/control/stocks_search_v1_run/m0/ — PASS required before D1
P0  F1–F9 source authority + census gates
D1  search-space manifest freeze (outcome-blind; hashed; this cycle's
    A2-equivalent dossier IS the manifest)
D2  R0-relaxed ancestry + feasibility measurement for EVERY configuration
    (non-scored)
S   selection by frozen construction-based order + exact arm/data/fold/
    config hash freeze
I   isolated implementation lanes; A1 integrates one handoff at a time
Z   sanitized exact-arm dry-run + recursive leak scan
A7  fresh-context independent prelaunch audit; zero unresolved HIGH/CRITICAL
GO  owner types `GO STOCKS SEARCH V1 SCORED EXECUTION` at this cycle's own
    gate; early/paraphrased GO dies unconsumed (P-8)
E   at most 3 scored cells under the machine-wide heavy lock
R   detached reproduction from committed artifacts
T   terminal audit and close
```

All delegated lanes write `zcode_orch_v3_handoff@1` JSON to their exact
dispatch path. Lanes never merge, rebase, push, edit registries/ledgers or
read other lanes' outcomes.

## 10. Trial accounting and result language

Observed and published denominators counted separately; every computed
cell consumes an observed slot even if publication fails; unused slots are
never reassigned and never force-filled. The frozen grid size is itself
published as the search's multiple-testing universe. Stocks denominators
currently 42/42; program 257/260 (P-9) — this cycle starts at budget 0/3.
Any result language must carry the §3 relaxation disclosure verbatim:
"accepted under owner-relaxed acceptance battery (R0 0.30 / DSR alpha 0.10
at N = grid)".

## 11. Prewritten terminal outcomes

```text
STOCKS_SEARCH_V1_BLOCKED_METHOD_CONTRACT
STOCKS_SEARCH_V1_BLOCKED_SOURCE_OR_SCHEMA
STOCKS_SEARCH_V1_BLOCKED_DATA_OR_SELECTION
STOCKS_SEARCH_V1_BLOCKED_PRELAUNCH
STOCKS_SEARCH_V1_REJECT_ALL
STOCKS_SEARCH_V1_SURVIVORS_UNDER_RELAXED_BATTERY (only if Stage-A passes;
    carries the §3 disclosure; never a profitability claim)
STOCKS_SEARCH_V1_INCOMPLETE_NOT_PROMOTABLE
STOCKS_SEARCH_V1_TECHABORT_PRESERVED
```

A correct early close is success of governance, not failure of
engineering. No predeclared survivor outcome is promised by this plan.

## 12. Boundaries

- No paid source beyond the existing EODHD entitlement; no signup, no API
  key requests; keys never echoed.
- No S1 access; no paper/testnet/live orders; no deployment.
- No fundamentals/earnings/short-interest/FINRA/FTD/N-PORT input of any
  kind (NG3/NG4/DATA-EDGE closures re-inherited).
- No score before A7 authorization plus the fresh exact owner GO.
- No pushes or writes to `.zcode/`; `CYCLE_REGISTRY.json` changes only
  through `researchctl`.
- One heavy job machine-wide; never kill a foreign worker.
- No budget/GO/rescue sharing with FOREX-SEARCH-V1 or PROSPECTIVE-SHADOW-V1.
- The §3 relaxation may not be widened in-cycle.

## 13. Immediate actions

```text
1. Commit this plan by exact pathspec.
2. Independent fresh-context adversarial plan audit (A7) — audit items:
   the §2 reopening reading, the §3 boundedness of "tí xíu", the §5 grid
   and outcome-blind selection, the §6 battery integrity under R0 0.30.
3. Remediate every valid HIGH/CRITICAL; re-audit with a NEW fresh-context
   A7 if the verdict was REFUSED.
4. Register STOCKS-SEARCH-V1 through researchctl as PLANNED_NOT_STARTED.
5. Bootstrap the integration worktree; run M0; PASS required before D1.
6. Stop at the scored prelaunch gate and wait for the exact owner GO.
```
