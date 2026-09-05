# STOCKS-FREE-V4 — BLIND MECHANISM DISCOVERY AFTER TWO REJECT-ALL CYCLES

> Owner plan for the next Stocks research cycle.
>
> `PLAN_stocks.md` remains the historical authority for V2/V2R/V3 and must not
> be rewritten. This file starts a new cycle only. Profit is not a required
> outcome; a correct `STOCKS_FREE_V4_REJECT_ALL` is a successful research run.

## 0. Frozen starting point

Measured terminal authority:

```text
completed branch       orca/stocks-free-v3-integration
terminal SHA           4a9457ab5682b2db1d0a188a51f4715f431c3fe3
terminal verdict       STOCKS_FREE_V3_REJECT_ALL
terminal A7            STOCKS_FREE_V3_REJECT_ALL_CONFIRMED
V3 W1                  586f9febe29ae6ba0b176c8c9a9b1b4645f3bca4
V3 cells               6 observed / 6 published / 6 reproduced exact
Stocks denominator     12 observed / 12 published after V2 + V3
survivors              0
S1                     SEALED_UNTOUCHED
paper/live/orders      none
workers at close       0
```

A1 must remeasure these facts. Any drift affecting scientific identity,
counters, data authority or S1 becomes an intake blocker. Harmless branch/path
drift is recorded, not silently normalized.

## 1. What is closed and may not be rescued

The following families and close variants are forbidden inputs:

1. sector relative-strength / 12-1 momentum / bottom-versus-top inversion;
2. long-only trend, SMA200, volatility-targeted trend-defense variants;
3. idiosyncratic shock/crash/overshoot reversal at nearby horizons;
4. turn-of-month, settlement-window and mid-month calendar variants;
5. any inversion, fee reduction, selected ETF subset or lookback tweak whose
   purpose is to rescue one of the above results.

The reasons are scientific, not cosmetic:

- V2 sector momentum produced positive raw PnL but its control retained 96.5%
  of anchor expectancy; beta dominated the proposed ranking mechanism.
- V2 trend-defense failed MDD, fold and drop-one gates.
- V3 idiosyncratic shock reversal lost 20.6%, PF 0.426 and 0/3 folds.
- V3 TOM made +38.52%, PF 1.620 and 3/3 folds, yet incremental alpha was
  negative and the placebo reproduced the sign; raw sector beta was not edge.

These rows remain in the historical denominator. V4 never regrades them.

## 2. Mission and allowed scope

V4 asks one narrow question:

> Can an outcome-blind mechanism using the already-authorized free ETF daily
> data produce incremental, after-cost information beyond SPY/sector beta?

Allowed inputs are only fields already authorized by the Stocks free-data
contract, such as PIT daily OHLCV, the frozen ETF cohort/calendar, corporate
action treatment and the authorized SPY total-return benchmark. Earnings,
fundamentals, borrow, short interest, holdings and institutional flow are
unavailable unless a separate owner data-authority decision is made.

Candidate mechanisms may explore genuinely distinct observables such as:

- cross-sectional dispersion or correlation-state transitions;
- volume/participation imbalance at daily frequency;
- range, gap or volatility-shape information not reducible to trend;
- relative-risk pricing with explicit market-factor neutralization;
- other literature-backed mechanisms proven distinct from the forbidden set.

This list guides search; it does not preselect winners.

Allowed terminal outcomes:

```text
STOCKS_FREE_V4_REJECT_ALL
STOCKS_FREE_V4_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
STOCKS_FREE_V4_BLOCKED_DATA_OR_SELECTION
STOCKS_FREE_V4_BLOCKED_PRELAUNCH
STOCKS_FREE_V4_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Branch and worktree topology

Integration seat:

```text
branch    orca/stocks-free-v4-integration
worktree  .worktrees/stocks-free-v4/integration
base      measured terminal SHA 4a9457ab... unless intake records a newer
          owner-authorized reconciliation descendant
```

Logical lanes:

```text
.worktrees/stocks-free-v4/p0-a2-factory
.worktrees/stocks-free-v4/p0-a3-data
.worktrees/stocks-free-v4/d1-a4-proposals
.worktrees/stocks-free-v4/d1-a5-proposals
.worktrees/stocks-free-v4/d1-a6-proposals
.worktrees/stocks-free-v4/d2-a7-novelty
.worktrees/stocks-free-v4/d2-a9-feasibility
.worktrees/stocks-free-v4/i-family-1
.worktrees/stocks-free-v4/i-family-2
.worktrees/stocks-free-v4/q-a7-prelaunch
.worktrees/stocks-free-v4/e-exec-1
.worktrees/stocks-free-v4/r-reproduce
.worktrees/stocks-free-v4/r-a7-terminal
```

Never check out one branch in two worktrees. Every lane records path, branch,
base SHA, head SHA, ownership and disposition in
`research/control/stocks_free_v4_run/worktree_manifest.json`.

## 4. Agent allocation and concurrency

Use eight logical roles; not all run simultaneously:

- A1: controller, only integrator, freezer, counter owner and publisher;
- A2: accounting/publication/digest reconciliation;
- A3: PIT data, cohort, benchmark and window authority;
- A4/A5/A6: two blind proposals each, six total;
- A7: independent novelty, prelaunch and terminal audits; never repairs;
- A8/A9: family implementation or feasibility as assigned by A1.

Concurrency:

- maximum A1 plus three light lanes;
- run full pytest alone;
- heavy cap is set by a fresh resource probe;
- on the 8 GB Mac, default heavy cap is one;
- scored arms within one family are serial;
- A1 is the only process allowed to append the canonical ledger.

## 5. Phase V4-R — terminal reconciliation

A1 first verifies:

- V3 terminal SHA and A7 ancestry;
- 6/6 V3 artifacts and reproduction exactness;
- append-only digest repins from A7T-B1;
- corrected ADJ-5 turnover convention;
- historical Stocks denominator 12/12;
- S1 seal, workers zero and clean trees;
- no active Stocks scorer.

Create:

```text
research/control/stocks_free_v4_run/run_contract.json
research/control/stocks_free_v4_run/state.json
research/control/stocks_free_v4_run/heartbeat.json
research/control/stocks_free_v4_run/event_log.jsonl
research/control/stocks_free_v4_run/forbidden_family_inventory.json
research/control/stocks_free_v4_run/worktree_manifest.json
```

Start budget at `0/6`. Start the new-cycle counters at zero while preserving the
historical 12/12 denominator separately.

## 6. Phase V4-P — factory and data gates

### P1 — publication/accounting regression

A2 proves with hand-computed fixtures:

- CASH is excluded from symbols, turnover and concentration;
- execution cost is charged once per fill and never repeated in a sidecar;
- turnover is `sum(abs(delta_weight))` under one named convention;
- canonical artifact digest hashes exact artifact bytes, not a wrapper;
- append-only correction does not alter observation/publication counters;
- observed increments once when a score exists; replay increments neither;
- zero-position and out-of-contract cells are refused;
- simultaneous workers cannot append without A1 serialization.

Any failure blocks proposal selection because V3 showed these are result-level,
not merely metadata-level, hazards.

### P2 — free-data authority replay

A3 replays the existing authorized snapshot without downloading new data:

- exact file hashes, license evidence and provider identity;
- cohort rule fixed before returns;
- exchange calendar and missing-session census;
- raw versus total-return separation;
- corporate actions applied PIT with one-event lag where applicable;
- SPY total-return reconstruction and benchmark availability;
- S0 folds and purge; S1 never listed, opened, hashed or copied;
- coverage sufficient for every proposed warmup and scoring timestamp.

If a proposal requires unavailable fields, mark it ineligible. Do not fabricate
fundamentals, borrow or earnings proxies from OHLCV.

### P3 — baseline invariants

Before proposals, freeze common definitions:

- long/short/gross/net/cash accounting;
- fills and cost schedule;
- force-flat fold boundaries;
- SPY and optional sector-factor residual calculation already supported by the
  authorized data;
- concentration, drop-one and stress conventions;
- minimum number of decisions/positions;
- resource formula and execution timeout.

No PnL is computed in Phase P.

## 7. Phase V4-D1 — blind proposal generation

A4, A5 and A6 branch from the same `V4_PROPOSAL_WAVE_SHA`. Each writes exactly
two proposals without reading V2/V3 per-arm outcome files beyond the provided
forbidden-family packet.

Each proposal must specify:

- causal/economic mechanism and falsifiable prediction;
- primary sources or stable literature citation;
- PIT observable using authorized fields only;
- universe, warmup, decision clock, holding and fill clock;
- exact anchor, one neighbour and one causal negative control;
- factor-neutralization or incremental-alpha test;
- base costs and stress costs;
- expected turnover and sample-size floor;
- drop-one design and concentration risk;
- failure interpretation;
- source-to-test map and implementation estimate;
- signed outcome-blind attestation.

Forbidden proposal patterns include parameter menus, grids, “best of” choices,
unnamed controls and any descendant of Section 1.

## 8. Phase V4-D2 — independent audit and selection

A7-N performs novelty and anti-rescue review. It measures feature/rank
similarity against every forbidden family where data permits. A renamed or
inverted old signal is `INELIGIBLE`, regardless of prose.

A9-F checks without PnL:

- PIT coverage and warmup;
- schedule count and minimum breadth;
- cap, gross/net and leverage feasibility;
- estimated turnover and frozen cost application;
- benchmark/factor availability;
- meaningful control and drop-one construction;
- implementation risk and host resources.

A1 selects at most two families with the frozen rubric:

1. no novelty/rescue veto;
2. authorized data PASS;
3. factor/control test is identifiable;
4. cap/cost/turnover/sample feasibility PASS;
5. strongest source-to-test trace;
6. lowest implementation risk;
7. lexicographic hypothesis ID tie-break.

Freeze exactly three arms per selected family. Maximum is six scored cells.
Unused slots are never reassigned. If fewer than two families are eligible,
continue with one only if its three-arm falsification design remains complete;
otherwise close blocked selection.

## 9. Phase V4-I — implementation

Create one lane per selected family from the exact selection-freeze SHA. A lane
may edit only its family module, tests, fixtures and lane evidence.

Required evidence:

- hand-computed feature and target golden;
- completed-session/PIT and no-lookahead mutation tests;
- next-allowed-session fill;
- deterministic double generation;
- split/dividend/raw/TR correctness;
- factor calculation and scale invariance;
- control cannot accidentally equal the anchor;
- cap/gross/net/cash invariants;
- cost-once and turnover convention checks;
- schedule-only feasibility on the real snapshot;
- meaningful held-max-weight drop-one;
- dummy publication/refusal/replay with no scored metrics.

A1 integrates one family at a time and runs targeted tests after each pick.

## 10. Phase V4-Q — freeze and prelaunch

A1 then:

1. runs all Stocks V4 and compatibility suites;
2. runs six-arm or applicable-arm dummy dry-run into a temporary ledger;
3. verifies exact arm digests and pairwise uniqueness;
4. verifies data and benchmark hashes;
5. verifies zero real scored artifacts and budget 0/6;
6. runs full pytest alone plus compileall and `git diff --check`;
7. records a fresh resource probe;
8. freezes final code-bearing `STOCKS_FREE_V4_W1`;
9. creates detached equal-twin execution/reproduction trees at W1;
10. stages byte-identical read-only data and empty ledger authority.

Independent A7 recomputes the entire chain. Only
`STOCKS_FREE_V4_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL may
reach the owner checkpoint.

A1 stops before the first scored cell until the owner explicitly says:

```text
GO STOCKS V4 SCORED EXECUTION
```

## 11. Phase V4-E — maximum six scored cells

After owner GO, each family runs serially:

1. anchor;
2. neighbour;
3. causal negative control.

Heavy families may run concurrently only when a fresh probe authorizes the cap;
A1 still serializes publication. No tests run beside a heavy worker.

Each score records exact input/code/arm hashes, positions, fills, costs,
turnover, cash, PnL, benchmark/factor residual, folds, concentration, stresses,
drop-one, observed/publication events and canonical artifact digest.

## 12. Stage-A gates

A family must satisfy every applicable frozen gate:

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
- causal control does not reproduce the mechanism under its preregistered rule;
- independent reproduction ALL_MATCH;
- zero unresolved HIGH/CRITICAL.

Positive raw PnL, PF or folds cannot override failed incremental alpha or
control. Negative anchor plus a worse control remains a reject.

## 13. Reproduction and terminal closeout

Reproduce every computed cell from the detached reproduction tree in fresh
processes. Require exact match for schedules, targets, fills, costs, metrics,
gates and canonical digests except explicitly volatile metadata.

Terminal A7 independently checks:

- ledger once-only accounting and exact artifact-byte hashes;
- CASH/cost/turnover reconciliation;
- factor/benchmark claims;
- all family verdicts and denominator math;
- S1 seal and deployment boundaries;
- workers zero and clean trees.

If there is a survivor, freeze it for a future owner-approved S1 plan. Do not
open S1 and do not paper/live trade in V4.

## 14. Required commands and reporting

Use `.venv/bin/python` on macOS/Linux. A1 discovers the exact new test names
after implementation, but at minimum runs:

```bash
.venv/bin/python -m pytest tests/assets/stocks -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q
.venv/bin/python -m pytest tests -q
.venv/bin/python -m compileall research/assets/stocks research/assets/common
git diff --check
git status --porcelain=v1
```

Every gate reports command, exit code, stdout/stderr paths, full HEAD, input and
output hashes, expected/observed, verdict, blocker and tree status.

Owner checkpoints:

1. intake/reconciliation;
2. P factory/data gates;
3. six proposals and independent audit;
4. selected families and freeze;
5. implementations and W1;
6. A7 prelaunch verdict;
7. each completed family after a later owner GO;
8. reproduction and terminal A7.

## 15. Hard boundaries

- No paid data, provider signup or new download without owner approval.
- No S1 access, paper, live, orders or credentials.
- No raw-data commit.
- No optimizer, scored grid, threshold weakening or family substitution.
- No rewriting prior ledgers, artifacts or terminal reports.
- No force-push, main merge, history rewrite or worktree deletion without owner
  instruction.
- No percentage-complete claim; report gates as PASS/FAIL/NOT_RUN/BLOCKED.
- A correct negative result is preferable to a fabricated survivor.

## 16. First report from a fresh A1

Before editing beyond the V4 bootstrap, report:

```text
measured UTC
root path / branch / full HEAD / porcelain
terminal V3 SHA and A7 ancestry
V2 + V3 observed/published denominator
S1 seal and active worker scan
data snapshot and benchmark authority
integration worktree path / branch / base SHA
RAM / CPU / disk / preliminary heavy cap
GO/NO_GO for metadata and factory-only phases
```

A1 may then continue autonomously through prelaunch and must stop before the
first scored V4 cell unless a real blocker occurs earlier.
