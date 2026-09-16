# PLAN STOCKS-NG6 — single-name failed-breakdown unwind (bear-trap reclaim)

> Status: `PLANNED_NOT_STARTED` (2026-09-16). Authority: explicit owner
> directive 2026-09-16 (three-cycle program STOCKS-NG6 / FOREX-NG7 /
> CRYPTO-NG4; this cycle: ONE price/volume family with a settlement-stress
> or crowding-unwind mechanism; SEC FTD/N-PORT at D2 as non-scored controls
> ONLY; budget max 3 scored cells / 1 family; plan audited by fresh-context
> A7 before registration). Outcome-blind dossier evidence is committed under
> `research/control/ng6_ng7_ng4_dossiers_2026-09/` (A2 proposal
> `7ad37d70…`, A3 SEC source contract `90ec23cd…`, A4 hostile critique
> `7827610f…`; SHA256SUMS.txt pinned). A P0/D2 close with zero scored cells
> is a valid result. Nothing in this plan is evidence of profitability.

## 0. Cycle identity

```text
cycle_id          STOCKS-NG6
asset             stocks
plan              plans/PLAN_stocks_ng6.md
branch            orca/stocks-ng6-integration
worktree          /Users/hoangminhlong/my-quantitative/.worktrees/stocks-ng6/integration
budget            3 scored cells max / 1 family max
go_phrase         GO STOCKS NG6 SCORED EXECUTION
S0                OPEN — screening only
S1                SEALED_UNTOUCHED
orders            NONE — no paper, testnet or live orders
```

Family name (frozen): `SINGLE-NAME FAILED-BREAKDOWN UNWIND (BEAR-TRAP
RECLAIM)`. `PROSPECTIVE-SHADOW-V1` remains independent and ACTIVE_LIGHT;
this cycle never reads its PnL, trades, marks or verdicts. FOREX-NG7 and
CRYPTO-NG4 share no budget, no GO and no rescue path with this cycle.

## 1. Question, in simple language

At a 252-session low the marginal seller is forced (stops, margin calls,
systematic breakdown rules). When the SAME session reclaims the level at
the close, the sell supply below the level is exhausted and a downside
crowd is trapped. We ask one narrow question:

> Using only session-t close information, does a failed 252-session-low
> breakdown (same-session reclaim, upper-half close, elevated
> participation) predict positive multi-session forward drift on the
> death-inclusive cohort — beyond what short-term reversal, volatility,
> liquidity, the calendar, and long-market exposure already explain?

Anchor (frozen): long-only equal-notional event book, entry at t+1 open,
exit at t+11 open (H=10), no leverage, no short leg, no stops, force-flat
at fold boundaries and name deaths.

## 2. Why this is a new cycle — and its honest ancestry risk

- No stocks-plane dead family consumed a failed-breakdown/reclaim event
  (dossier ancestry greps: zero hits in FAMILY_FAILURES.jsonl and the
  ledger; the only name-relative is crypto-sprint Wyckoff
  `markdown-breakdown-short`, an OPPOSITE sign class, cross-plane,
  disclosed). The nearest stocks dead relative is
  `SFV3-A5-IDIO-SHOCK-REVERSAL` (expectancy −0.00296) — the anchor is
  structurally reversal-SELECTED, so A4 mandates BINDING event-conditional
  reversal shadows (§6). Novelty is a proposal claim until the frozen D2
  inventory passes.
- STOCKS-NG5 died D2_VETO_ALL as relative momentum in new words; this
  family shares nothing with it (single-name event book vs 2-ETF weekly
  rotation) and the NG5 rotation state is an enumerated R0 shadow.
- A4 corrections adopted: warmup is 252 served sessions (the 60-session
  dollar-volume window is contained in it; first eligible event no earlier
  than the 253rd served session); the "0.20 bar killed every NG proposal"
  claim is FALSE as stated across planes (crypto ng proposals 10/10
  killed; FXNG1 4/4, RATES 1/4, VOL 2/4, COMM 1/4 were eligible) — the
  dossier sentence is corrected here and must not travel.
- A4 predicted kill site: fold concentration, not cost.

## 3. M0 — methodology contract gate (before D1)

The shared D2-methodology golden suite (G1–G10 + G4N = 11/11, NG5 §3
lineage: same-family detection, sign-inversion, shared-payoff trap, no
payoff-correlation primary, seven named primary comparisons, shared-instant
clustering, price-only control classing, freeze-before-measurement,
no-threshold-rescue, wrong-implementation sensitivity, verdict-purity
negative control) is re-inherited BYTE-EXACT from the NG5 M0 machinery and
re-run in this cycle's worktree. Code and fixtures live under
`research/control/stocks_ng6_run/m0/`. M0 PASS is required before D1
dispatch. If M0 does not PASS independently: `BLOCKED_METHOD_CONTRACT`; D1
never opens; budget stays 0/3.

## 4. Source authority and P0 gates

Primary scored source: EODHD `/eod` daily OHLCV incl. delisted, owner
entitlement (`EODHD_API_KEY`, never echoed; V8/V13 precedent). The family
consumes ONLY the `/eod` channel (fundamentals measured 403-dead at NG3 —
by design no fundamentals/earnings/short-interest input exists).

```text
F1 ENTITLEMENT + TERMS     P-25 three-layer gate (reachable/permitted/
                           served) run FIRST, before any bulk retrieval;
                           the death-inclusive priced cohort re-pinned;
                           SPY benchmark leg re-evidenced by NG6's own P0
                           (NG5 frontier probes are P-1 prior evidence).
F2 LIVENESS + RETRIEVAL    canaries at window start/middle/recent end;
                           double-pull byte-identity; raw sha256 pinned;
                           never-existed ticker canary.
F3 RAW/ADJUSTED + ACTIONS  adjusted (total-return) series is THE single
                           representation (P-12, dossier §data_authority):
                           state and returns on the same adjusted series;
                           dividend-decomposition NON-scored check at D2
                           (SFV13 SH-A9 class; distribution-dominated
                           event identity = fail-closed contamination).
F4 COHORT + COVERAGE       death-inclusive cohort census; per-name served-
                           session census; bookability floors ($1.00
                           adjusted close, $2M trailing 60-session median
                           dollar volume) declared ex ante; warmup
                           attrition CENSUSED, never silently dropped.
F5 CLOCK + EXECUTION       ONE frozen daily decision clock (decision at t
                           close; fills at t+1 and t+11 regular-session
                           opens); bar-readable close+1 availability (V7
                           law); timezone/DST fixtures.
F6 COSTS                   band schedule BAND_BPS = {A:10, B:15, C:25}
                           bps/fill on ADV bands {50M, 10M, 2M}, fail-closed
                           (kernel_band_cost_v9.py lineage re-inherited
                           byte-exact per the RULES §9 adoption boundary);
                           cost exactly once per fill; STRESS TIER 2.0 IS
                           THE PRIMARY GATE; PREREGISTERED worst-case
                           ceiling (P-21): 25bps x 2 fills x 2.0 = 100 bps
                           per round trip; annualized ceiling =
                           100bps x realized recent-window event turnover;
                           fills/yr = 2 x E_recent / window_years;
                           break-even bps per round trip reported per arm
                           (A4 form: 30–50 bps tier-1, 60–100 stress-2.0).
F7 BENCHMARK CONSTRUCTION  SPY buy-and-hold exposure-matched; C-RANDOM-
                           TIMING clock twin; both total-return basis.
F8 FOLD FREEZE (Q-6)       three chronological folds frozen BEFORE any D2
                           diagnostic; RECENT-window event-population floor
                           >= 30 events/fold measured at A9/P2 (fail-closed
                           kill if unmet); folds span at least one major
                           deleveraging regime; 2008Q4–2009 and 2020-03
                           never share a fold.
F9 REPRODUCIBILITY         census code, raw-request manifest, digest
                           manifest, calendar/clock contract, cost bands,
                           folds committed under research/control/
                           stocks_ng6_run/; detached rerun reproduces.
F10 SEC CONTROL SOURCES    SEC FTD + N-PORT enter ONLY as D2 non-scored
                           controls (§7) and pass their own three-layer
                           authority gate BEFORE any control is computed
                           (P-25). The A3 source contract is binding:
                           FTD available_time = settlement half-month end
                           + 15 days posting bound with a >=16-day
                           conditioning guard (settlement date is NEVER
                           availability; per-file posting timestamps
                           NOT_MEASURED — historical archive joins stay
                           RETROSPECTIVE_ONLY-labeled until a per-file
                           timestamp pass); N-PORT available_time =
                           FILING_DATE + 1-day guard (NEVER report_date;
                           lag p50 57d / p95 62d so 60 days is not a safe
                           bound); amendments identified as SUB_TYPE
                           NPORT-P/A with supersession = max FILING_DATE
                           per (series, REPORT_DATE); the 2026q2 one-
                           quarter cap means every long-history crowding
                           claim is INSUFFICIENT_COVERAGE; current
                           holdings never reconstruct historical holdings.
                           A4 adjudication: with one quarter and a >=63-day
                           lag, N-PORT is INERT for historical event
                           conditioning in this cycle — recorded as such,
                           not forced into use.
```

P0 is source engineering and census only. It may NOT compute candidate
PnL, PF, Sharpe, drawdown, survivors or S1 evidence.

## 5. D1 outcome-blind proposal contract

The committed A2 dossier (sha `7ad37d70…`) is BINDING and frozen before
any return exists. At most THREE constructions enter D2:

```text
1 anchor                 SNG6-A2-P1-ANCHOR-TRAP-RECLAIM: event = (1) BREAK
                         adj_low_t < min(adj_low_{t-252..t-1}); (2) RECLAIM
                         adj_close_t > that same prior 252-session low;
                         (3) RANGE (close_t - low_t)/(high_t - low_t) >= 0.5;
                         (4) PARTICIPATION dollar_volume_t >= 1.5x trailing
                         60-session median; $1.00 / $2M bookability floors;
                         all parameters declared from construction logic,
                         never tuned (Q-12 bar heights declared).
1 structural neighbour   SNG6-A2-P1-NEIGH-CONFIRM-2S: two-session
                         confirmation (t+1 close holds above the broken
                         level; entry t+2 open, same H/filters/costs);
                         preregistered self-subsumption |rho| <= 0.98 vs
                         anchor (P-20 books-distinct), else SELF-SUBSUMED.
1 mandatory no-fail control book (non-scored) — C-NOFAIL-BREAKDOWN below.
```

No short leg (no borrow-cost authority exists — FOREX-NG6 F4 precedent
class); direction falsification carried by R1 expectancy and
C-NOFAIL-BREAKDOWN, honestly labelled an inversion-SUBSTITUTE.

## 6. Mandatory controls and killers

Controls (falsification books, consume no scored slots):

```text
C-NOFAIL-BREAKDOWN   raw 252-low break without reclaim/range/volume —
                     primary causal control + direction surrogate
C-REVERSAL-PLAIN     worst-5-session-return equal-weight re-formed every 5
                     sessions (SFV3-A5 ancestor class)
C-RANGE-ONLY         upper-range-close + volume, no level event
C-DVOL-ONLY          volume-condition-only book (A4: >= 0.5x same-sign
                     reproduction -> REJECT)
C-RANDOM-TIMING      every-63rd-session H-session clock twin
C-MARKET             SPY buy-and-hold, exposure-matched
C-DELAY-H            identical anchor entering H=10 sessions late — Q-11
                     invalid-null class DECLARED IN ADVANCE: out-earning
                     delay converts to a lookahead audit first, then feeds
                     the K6 horizon rule; never an automatic kill
C-PIT-MUTATION       one-session-earlier recomputation changes/refuses
                     the book on every event
C-NULL-VALIDITY      autocorrelation + population of every null reported
                     before any control may kill (Q-11)
```

R0 shadow inventory (ENUMERATED AND FROZEN before any rho; measuring
against an under-enumerated inventory is an invalid PASS, fail-closed):
momentum_63s generic; 12–1mo cross-sectional momentum; **event-conditional**
5d/21d return and drawdown-depth short-term-reversal states (A4: cohort-wide
rho understates a sparse event book — the conditional forms are BINDING);
dollar-volume-shock state; realized-vol LEVEL + semivariance share states
(A4: event-conditional vol-tercile + vol-restricted event shadows BINDING);
rolling-beta state; DGS10-LEVEL state; event-calendar geometry (event
day-of-week / month-end coincidence, P-24 class); V13 death-event proximity;
STOCKS-NG5 relative-breadth rotation state; dividend-decomposition divergence
(non-scored, fail-closed if distribution-dominated).

Ordered kill rules (first binding rule kills; all NET, total-return basis;
every control null-validated before it kills):

```text
R0  pre-score ancestry veto   pooled |rho| > 0.20 vs ANY R0 shadow on the
                              frozen decision grid -> proposal dies pre-score
R1  expectancy                anchor net expectancy <= 0 -> REJECT_ALL
R2  long-market reduction     anchor <= max(C-MARKET, C-RANDOM-TIMING)
                              net expectancy -> REJECT (A4: this rule runs
                              on the max; Stage-A additionally requires
                              SPY-excess >= 2/3 folds, MDD <= 15%, largest-
                              fold PnL concentration <= 50%)
R3  mechanism specificity     C-NOFAIL-BREAKDOWN out-earns OR reproduces
                              >= 0.5x same-sign in >= 2/3 folds -> REJECT
R4  reversal reduction        C-REVERSAL-PLAIN out-earns OR reproduces
                              >= 0.5x same-sign >= 2/3 folds -> REJECT
R5  component placebo         C-RANGE-ONLY reproduces >= 0.5x same-sign
                              -> REJECT
R6  clock geometry            C-RANDOM-TIMING out-earns -> REJECT
K6  slow-drift combination    {anchor, C-DELAY-H} x {trap, no-fail} books
                              mutually indistinguishable within fold noise
                              (exact test frozen at S) -> REJECT
```

Plus the frozen stocks Stage-A gates on any survivor: fold-positive-share
<= 50%, largest-fold concentration <= 50%, MDD <= 15%, stress 2.0 net
positive with break-even margin, drop-one sign stability, death-censoring
invariance (excluding in-horizon deaths must not flip the verdict — a
verdict coupled to death-censoring is unbookable, fail-closed; deaths
inside H=10 force-flat at last served session and INCLUDED), PIT mutation,
per-period series persisted (P-11) for DSR over the cumulative ~260
observed trials, PBO fail-closed < 8 configurations.

## 7. D2 ancestry and feasibility gate (non-scored)

D2 measures, on the frozen P-12 representation and decision grid: the R0
inventory (pooled |rho| <= 0.20 immovable — being vetoed is not grounds to
move the bar); feasibility floors (F6/F8 forms); control identifiability.
The SEC controls bind here and ONLY here:

- FTD settlement-stress state (elevated fails around trap events) may be
  used as a NON-SCORED D2 corroboration/falsification control under the
  >=16-day availability guard; it never enters a scored arm, weight or
  feature; without the P0 authority gate it is NOT_RUN fail-closed.
- N-PORT crowding/holdings overlap is INERT this cycle (INSUFFICIENT_
  COVERAGE, §4 F10) — recorded honestly, never substituted or extrapolated.
- No future publication may inform a past decision anywhere in D2.

Selection empty -> close at 0/3. A7-F2/P-12 law: the shadow inventory is
committed as a hashed list BEFORE any rho computation.

## 8. Trading, costs and risk contract

```text
decision        frozen daily clock (F5); bar-readable close+1 availability
entry/exit      t+1 open / t+11 open; force-flat at fold boundary and at
                death (last served session; DEATH_CENSORED flagged, included)
universe        death-inclusive priced cohort; single-name; long-only;
                no leverage; no short; no stops
accounting      total-return (adjusted series); equal-notional per event;
                portfolio book reported alongside for fold/MDD gates
costs           measured ADV bands charged once per fill; stress 2.0
                PRIMARY + break-even margin (P-2, with Q-12 bar heights)
claims          D2 eligible means only "allowed to be tested" — never
                profitable; no survivor claim without all Stage-A gates
```

## 9. Execution phases and ownership

```text
M0  methodology golden tests (§3) — gate before D1
P0  F1–F10 source authority + census gates
D1  anchor + neighbour + no-fail control freeze (outcome-blind; A2 dossier binding)
D2  ancestry/novelty + feasibility + SEC control measurement (non-scored)
S   selection + exact arm/data/fold/config hash freeze
I   isolated implementation lanes; A1 integrates one handoff at a time
Z   sanitized exact-arm dry-run + recursive leak scan
A7  fresh-context independent prelaunch audit; zero unresolved HIGH/CRITICAL
GO  owner types `GO STOCKS NG6 SCORED EXECUTION` at this cycle's own gate;
    early/paraphrased GO dies unconsumed (P-8)
E   at most 3 scored cells (anchor + neighbour declare up to 2 scored arm
    identities; the 3rd cell is reserved, never force-filled) under the
    machine-wide heavy lock
R   detached reproduction from committed artifacts
T   terminal audit and two-half close
```

All delegated lanes write `zcode_orch_v3_handoff@1` JSON to their exact
dispatch path. Lanes never merge, rebase, push, edit registries/ledgers or
read other lanes' outcomes.

## 10. Trial accounting and result language

Observed and published denominators counted separately; every computed cell
consumes an observed slot even if publication fails; unused slots are never
reassigned and never force-filled. Stocks denominators currently 42/42;
program 257/260 (P-9) — this cycle starts at budget 0/3.

## 11. Prewritten terminal outcomes

```text
STOCKS_NG6_BLOCKED_METHOD_CONTRACT
STOCKS_NG6_BLOCKED_SOURCE_OR_SCHEMA
STOCKS_NG6_BLOCKED_DATA_OR_SELECTION
STOCKS_NG6_BLOCKED_PRELAUNCH
STOCKS_NG6_REJECT_ALL
STOCKS_NG6_INCOMPLETE_NOT_PROMOTABLE
STOCKS_NG6_TECHABORT_PRESERVED
```

A correct early close is success of governance, not failure of engineering.
This plan contains no predeclared survivor outcome.

## 12. Boundaries

- No paid source beyond the existing EODHD entitlement; no signup, no API
  key requests; keys never echoed.
- No S1 access; no paper/testnet/live orders; no deployment.
- No constituent-history reconstruction; no current-holdings backfill.
- FTD/N-PORT never enter a scored signal without an owner-granted
  historical PIT authority (none exists today).
- No score before A7 authorization plus the fresh exact owner GO.
- No pushes or writes to `.zcode/`; `CYCLE_REGISTRY.json` changes only
  through `researchctl`.
- One heavy job machine-wide; never kill a foreign worker.
- No budget/GO/rescue sharing with FOREX-NG7 or CRYPTO-NG4.

## 13. Immediate actions

```text
1. Commit this plan + the dossier evidence by exact pathspec.
2. Independent fresh-context adversarial plan audit (A7).
3. Remediate every valid HIGH/CRITICAL; re-audit with a NEW fresh-context
   A7 if the verdict was REFUSED.
4. Register STOCKS-NG6 through researchctl as PLANNED_NOT_STARTED.
5. Bootstrap the integration worktree; run M0; PASS required before D1.
6. Stop at the scored prelaunch gate and wait for the exact owner GO.
```
