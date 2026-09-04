# STOCKS-FREE-V5 — PIT CONDITIONING VARIABLES VIA DATA FUSION AFTER THREE REJECT-ALL CYCLES

> Owner plan for the next Stocks research cycle, dated 2026-09-04.
>
> `PLAN_stocks.md` (V2/V2R/V3) and `PLAN_stocks_v4.md` (V4) are closed
> historical authorities and must not be rewritten. This file starts V5 only.
> A correct `STOCKS_FREE_V5_REJECT_ALL` is a successful research run.

## 0. Frozen starting point

Measured terminal authority (A1 must remeasure; drift affecting identity,
counters, data authority or S1 is an intake blocker):

```text
completed branch       orca/stocks-free-v4-integration
terminal SHA           341dfc18903e98520e13f2ffc2401415cba24943
terminal verdict       STOCKS_FREE_V4_REJECT_ALL
terminal A7            STOCKS_FREE_V4_REJECT_ALL_CONFIRMED (0 findings)
V4 cells               6 observed / 6 published / 6 reproduced EXACT_MATCH
V4 W1                  dfa099abe... (twins e-exec-1 / r-reproduce detached)
stocks denominators    18 observed / 18 published (V2 6 + V3 6 + V4 6)
survivors              0
S1                     SEALED_UNTOUCHED
paper/live/orders      none
workers at close       0
Data Fusion V1 core    FROZEN at MULTISOURCE_DATA_CORE_SHA
                       c6a0576ef98dd4392e90805c8ba33821da62eabc
                       (adapters: A2 stocks SEC lane, A3 macro FRED/ALFRED
                       lane, A4 forex lane — all lane-merged and audited)
```

## 1. What is closed and may not be rescued

Cumulative ancestry veto, in addition to the V3 and V4 forbidden inventories:

1. sector relative-strength / 12-1 momentum and bottom-versus-top inversions;
2. long-only trend, SMA200, volatility-targeted trend-defense;
3. idiosyncratic shock/crash reversal at nearby horizons;
4. turn-of-month, settlement-window, mid-month calendar variants;
5. fresh-versus-stale participation-shift (21d/252d dollar-volume shock) and
   its stale-rank inversion;
6. semivariance-SHAPE pricing (downside/total variance) and its
   vol-level inversion as a rescue of the shape family;
7. any ETF subset, lookback tweak, fee reduction or relaxed gate whose
   purpose is to rescue any row above.

Scientific basis, unchanged: V2 sector momentum was 96.5% beta; V3 TOM and
idio-reversal failed incremental alpha; V4 both anchors were negative while
their controls earned raw PnL that belonged to sector-exposure form (stale
participation) and to plain vol-LEVEL sorting (semivariance control).

### 1.1 Shadow-effect region — the only sanctioned re-entry

Two shadow effects exist as measured V4 control-arm observations: vol-level
sorting (+53.14% raw, PF 2.582, but MDD 34.1% and concentration fail) and the
sector-exposure form (+14.91% raw, negative incremental alpha). They are not
tradable findings and not rescuable. A V5 proposal may enter this region ONLY
through the front door:

- the proposal states a new mechanism question — for V5, specifically
  "is the vol-level premium tradable when risk-managed?" — with the risk
  overlay (vol targeting, beta hedge, gross clamp) chosen BEFORE any V5 data
  is scored, never selected ex post;
- the family is preregistered as **confirmatory** (the raw effect was already
  observed in a V4 control arm) and this status is recorded in the family
  verdict and the denominator;
- it carries its own falsification control (for example one-quarter-stale
  vol-level ranks) distinct from the V4 control arms;
- A7-N measures anchor rank correlation against the V4 semivariance anchor
  and the V4 vol-level control; |rho| <= 0.20 vs the shape anchor, and the
  relationship to the level axis is documented, not hidden;
- Stage-A gates apply with no relaxation; MDD <= 15% is not negotiable. The
  V4 control's raw +53% is not evidence and not a target.

## 2. Mission and allowed scope

V5 asks one question:

> Does point-in-time conditioning from newly adopted free sources — SEC
> filing-clock fundamentals aggregated to the frozen sector cohort, and
> vintage-dated macro series — produce incremental, after-cost information
> beyond SPY/sector beta on the authorized 12-ETF universe?

Scope decisions (frozen):

- **Trading universe stays the frozen 12-ETF cohort**, calendar, benchmark
  contract and cost model unchanged from V4. Single-name equity widening is
  explicitly deferred: a PIT survivorship-free universe of individual names
  is its own data-authority cycle and must not be rushed inside V5.
- **Data Fusion adoption happens BEFORE the V5 data and selection
  freeze**, by explicit compatibility cherry-pick of the frozen core plus the
  A2 (SEC) and A3 (macro) adapters. Shared code must prove compatibility with
  the stocks calendar, cost model, TR benchmark and ledger.
- Adoptable datasets: SEC Company Facts / Submissions (fundamentals with
  filing clocks), FRED/ALFRED (vintage macro). FINRA short interest and
  Alpha Vantage earnings require an owner key/signup decision first; they are
  candidates, not defaults.
- Every adopted dataset must pass `/pit-data-audit`: license and entitlement
  captured; `available_time_utc` from filing stamps or ALFRED vintage dates —
  retrieval time never substitutes; raw bytes + SHA pinned; normalizer
  version recorded; revisions append as vintages.
- If adoption fails or a source proves unauthorized, the truthful outcome is
  `STOCKS_FREE_V5_BLOCKED_DATA_OR_SELECTION`, not a fallback to forbidden
  price-derived variants.

Allowed terminal outcomes:

```text
STOCKS_FREE_V5_REJECT_ALL
STOCKS_FREE_V5_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
STOCKS_FREE_V5_BLOCKED_DATA_OR_SELECTION
STOCKS_FREE_V5_BLOCKED_PRELAUNCH
STOCKS_FREE_V5_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Branch and worktree topology

```text
branch    orca/stocks-free-v5-integration
worktree  .worktrees/stocks-free-v5/integration
base      measured terminal SHA 341dfc1... unless intake records a newer
          owner-authorized reconciliation descendant
lanes     .worktrees/stocks-free-v5/{p0-a2-fusion,p0-a3-data,
          d1-a4-proposals,d1-a5-proposals,d1-a6-proposals,
          d2-a7-novelty,d2-a9-feasibility,i-family-1,i-family-2,
          q-a7-prelaunch,e-exec-1,r-reproduce,r-a7-terminal}
```

Never check out one branch in two worktrees. Every lane records path, branch,
base SHA, head SHA, ownership and disposition in
`research/control/stocks_free_v5_run/worktree_manifest.json`.

## 4. Agent allocation and concurrency

- A1: controller, only integrator, freezer, counter owner, publisher;
- A2: fusion adoption, accounting/publication regression;
- A3: PIT data, cohort, benchmark, window and adopted-source authority;
- A4/A5/A6: two blind proposals each, six total;
- A7: independent novelty, prelaunch, terminal audits; never repairs;
- A8/A9: family implementation or feasibility as assigned.

Concurrency: A1 plus at most three light lanes; full pytest alone; on the
8 GB Mac the default heavy cap is one; arms within a family serial; only A1
appends the canonical ledger.

## 5. Phase V5-R — terminal reconciliation

A1 verifies: V4 terminal SHA and A7T ancestry; 6/6 V4 artifacts and
EXACT_MATCH reproduction; denominator 18/18; budget fully consumed 6/6 with
zero replays delta; S1 seal, workers zero, clean trees, no active scorer;
forbidden inventories intact (V3 + V4). Then creates
`research/control/stocks_free_v5_run/{run_contract,state,heartbeat,event_log,
forbidden_family_inventory,worktree_manifest,lessons_register}` with budget
`0/6`, V5 counters at zero, historical 18/18 preserved separately, L1-L7
seeded plus the V4 falsification observations.

## 6. Phase V5-P — adoption, factory and data gates

### P0 — Data Fusion adoption (new)

A2 cherry-picks the frozen core and the A2-stocks / A3-macro adapters, then
proves:

- SEC and macro rows map onto the fusion record schema with true availability
  (filing timestamps, ALFRED vintage dates) inside the stocks tree;
- a decision at T can never read a row whose `available_time_utc > T`
  (regression-pinned);
- sector aggregation from filer-level facts is deterministic and
  survivorship-aware at the cohort's sector level;
- no V4 frozen artifact, digest, counter or ledger byte changes.

### P1 — publication/accounting regression

Inherit the full V4 P1 suite unchanged: CASH exclusion, cost-once, one named
turnover convention (ADJ-5), byte-exact digests, append-only corrections,
observed-once/replay-never, zero-position refusal, A1 serialization.

### P2 — data authority: existing snapshot plus adopted sources

A3 replays the authorized ETF snapshot exactly as V4-P2 (hashes, cohort,
calendar, raw/TR separation, corporate actions PIT with one-event lag, SPY TR
benchmark, coverage fail-closed), then extends the authority to adopted
sources: per-series license evidence, availability stamps, vintage handling,
warmup coverage for every proposed conditioning clock, and an explicit
`AUTHORIZED` / `CANDIDATE_NOT_AUTHORIZED` disposition per source. Fabricating
fundamental or macro proxies from OHLCV is forbidden.

### P3 — baseline invariants

Freeze before proposals: book/cash accounting; fills and the frozen cost
schedule; force-flat fold boundaries; SPY and sector-factor residual
calculation; concentration, drop-one, stress conventions; minimum
decisions/positions; resource formula and timeout; the conditioning-lag
rule (a macro or fundamental observation influences decisions no earlier than
its availability stamp plus one session).

No PnL is computed in Phase P.

## 7. Phase V5-D1 — blind proposal generation

A4, A5, A6 branch from the same `V5_PROPOSAL_WAVE_SHA`. Each writes exactly
two outcome-blind proposals with the full V4 packet discipline (mechanism,
falsifiable prediction, literature, PIT observable with availability
semantics, universe/warmup/clock/holding/fills, anchor + neighbour + causal
negative control, incremental-alpha test, base and stress costs, turnover and
sample floor, drop-one design, failure interpretation, source-to-test map,
signed attestation). At least three of the six proposals must condition on
adopted PIT sources (SEC or macro); the remainder may use authorized
price/volume fields within the non-forbidden space. Proposal agents receive
the forbidden packet (Section 1 + V4 inventory) and no per-arm outcome files.

## 8. Phase V5-D2 — independent audit and selection

A7-N: novelty and anti-rescue with measured rank correlation against every
forbidden family, the V4 anchors and the V4 control arms (Section 1.1
thresholds); a renamed or inverted old signal is INELIGIBLE regardless of
prose. A9-F: PIT coverage and warmup on the real snapshot, schedule count
and breadth, cap/gross/net feasibility, frozen-cost turnover arithmetic,
benchmark availability, control identifiability (the V4 lesson: a control
that is rank-identical to its anchor cannot identify anything), drop-one
meaningfulness, implementation risk — all without PnL.

A1 selects at most two families with the frozen V4 rubric (no veto; data
PASS; identifiable control test; feasibility PASS; strongest source-to-test
trace; lowest implementation risk; lexicographic tie-break). Exactly three
arms per family; maximum six scored cells; unused slots never reassigned.

## 9. Phase V5-I — implementation

One lane per selected family from the selection-freeze SHA, with the full V4
evidence list: hand-computed feature/target goldens; PIT/no-lookahead mutation
tests including conditioning-lag; next-allowed-session fills; deterministic
double generation; split/dividend/raw/TR correctness; factor calculation and
scale invariance; control-cannot-equal-anchor; cap/gross/net/cash invariants;
cost-once and turnover conventions; schedule-only feasibility on the real
snapshot; non-vacuous drop-one; dummy publication/refusal/replay with zero
scored metrics. A1 integrates one family at a time, targeted tests after each
pick.

## 10. Phase V5-Q — freeze and prelaunch

A1 runs all Stocks V5 and compatibility suites; six-arm dummy dry-run into a
temporary ledger; exact arm digests, pairwise unique; data, benchmark and
adopted-source hashes; zero real scored artifacts, budget 0/6; full pytest
alone, compileall, `git diff --check`; fresh resource probe; freeze
code-bearing `STOCKS_FREE_V5_W1`; detached equal-twin execution/reproduction
trees; byte-identical read-only data (ETF snapshot plus adopted PIT series)
and empty ledger authority.

Independent A7 recomputes the chain; only
`STOCKS_FREE_V5_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL
reaches the owner. A1 stops before the first scored cell until the owner
types:

```text
GO STOCKS V5 SCORED EXECUTION
```

## 11. Phase V5-E — maximum six scored cells

Serial per family: anchor, neighbour, causal control. No tests beside a
heavy worker; A1 serializes publication. Each score records input/code/arm
hashes, positions, fills, costs, turnover, cash, PnL, benchmark/factor
residual, folds, concentration, stresses, drop-one, conditioning-lag
attestation, observed/publication events and the canonical digest.

## 12. Stage-A gates (frozen ex ante; identical to V4)

- after-cost anchor expectancy > 0;
- PF >= 1.10;
- at least 2/3 chronological folds positive;
- MDD <= 15%;
- largest positive-fold share <= 50%;
- ETF positive-PnL share <= 35%;
- frozen turnover ceiling and cap/gross rules;
- stress PnL > 0 and stress PF >= 1.00;
- meaningful drop-one ETF and fold survival;
- risk-matched excess positive in at least 2/3 folds;
- overall incremental alpha > 0;
- neighbour supports the same mechanism;
- the causal control does not reproduce it under its preregistered rule;
- independent reproduction ALL_MATCH;
- zero unresolved HIGH/CRITICAL.

Positive raw PnL never overrides failed incremental alpha or a firing
control — the exact V2/V4 failure mode. A control that outperforms a
negative anchor falsifies the mechanism (confirmatory-region families
included).

## 13. Reproduction and terminal closeout

Reproduce every computed cell from the detached twin in fresh processes;
exact match except volatile metadata. Terminal A7 independently checks ledger
once-only accounting and byte hashes; CASH/cost/turnover reconciliation;
PIT-availability claims of adopted sources; family verdicts and denominator
math (18 + V5 cells); S1 seal and deployment boundaries; workers zero, clean
trees. If a survivor exists, freeze it for a future owner-approved S1 plan;
do not open S1 and do not paper/live trade in V5.

## 14. Required commands and reporting

Use `.venv/bin/python`. Minimum:

```bash
.venv/bin/python -m pytest tests/assets/stocks -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q
.venv/bin/python -m pytest tests -q
.venv/bin/python -m compileall research/assets/stocks research/assets/common
git diff --check
git status --porcelain=v1
```

plus the data-fusion compatibility suite after P0. Every gate reports command,
exit code, stdout/stderr paths, full HEAD, input/output hashes,
expected/observed, verdict, blocker, tree status.

Owner checkpoints: intake/reconciliation; P gates incl. fusion adoption and
per-source authorization; six proposals and audits; selection freeze;
implementations and W1; A7 prelaunch verdict; each completed family after
GO; reproduction and terminal A7.

## 15. Hard boundaries

- No paid data; no key/signup (FRED, Alpha Vantage, FINRA feed) without an
  owner data-authority decision; no new download outside it.
- No S1 access, paper, live, orders or credentials.
- No raw-data commit.
- No optimizer, scored grid, threshold weakening, family substitution or
  result-aware retrofit of Data Fusion.
- No rewriting prior ledgers, artifacts or terminal reports.
- No force-push, main merge, history rewrite or worktree deletion without
  owner instruction.
- No percentage-complete claims; gates report PASS/FAIL/NOT_RUN/BLOCKED.
- A correct negative result is preferable to a fabricated survivor.

## 16. First report from a fresh A1

```text
measured UTC
root path / branch / full HEAD / porcelain
terminal V4 SHA and A7T ancestry
V2+V3+V4 observed/published denominator 18/18
S1 seal and active worker scan
ETF snapshot + benchmark authority + fusion-core SHA
integration worktree path / branch / base SHA
RAM / CPU / disk / preliminary heavy cap
GO/NO_GO for reconciliation and factory-only phases
```

A1 continues autonomously through prelaunch and stops before the first scored
V5 cell unless a real blocker occurs earlier.
