# FOREX-FREE-V2 — LOW-FREQUENCY BLIND DISCOVERY AFTER V1 REJECT-ALL

> Owner plan for the next Forex research cycle.
>
> `PLAN_forex.md` and FOREX-FREE-V1 evidence remain immutable historical
> authorities. V2 reuses the validated factory and authorized snapshot; it does
> not regrade or rescue either rejected V1 family.

## 0. Frozen starting point

```text
completed branch       orca/forex-free-v1-integration
terminal SHA           bee64beaf2637ea51216cffc6be6393d545bf474
terminal verdict       FOREX_FREE_V1_REJECT_ALL
V1 W1                  f33a32a2f245d08447a67bb6a0b1f7276c7c5a85
V1 cells               6 observed / 6 published / 6 reproduced exact
Forex denominator      6 observed / 6 published
survivors              0
S1                     SEALED_UNTOUCHED
workers at close       0
```

V1 data authority:

- seven-pair free snapshot;
- H1 is authorized for research;
- D1 is context only;
- H4, historical institutional bid/ask and authoritative rollover/swap remain
  unavailable fail-closed;
- the frozen proxy cost was 1.5 bps per side with stress tiers;
- no live/paper/broker claim follows from research-data authority.

A1 remeasures all facts and records drift before creating V2 artifacts.

## 1. Closed V1 mechanisms

V1 rejected both selected families after exact reproduction:

```text
London-open continuation anchor  expectancy -2.353, PF 0.849, 11459 trades
late-NY fade anchor              expectancy -2.896, PF 0.638, 1020 trades
all six V1 arms                 EXPECTANCY_NONPOSITIVE
```

Controls were worse than anchors, so direction coherence existed, but neither
anchor was profitable after cost. A worse control cannot rescue a negative
mechanism.

Forbidden V2 inputs:

- London-open continuation and NY-open nearby-clock variants;
- late-NY standardized-extension fade and nearby threshold/horizon variants;
- sign inversion, reduced costs, selected winning pairs or session relabeling;
- the near-duplicate London-to-NY momentum proposal identified in V1 novelty
  audit;
- any result-aware reuse of V1's six proposals without a fresh blind packet and
  independent novelty decision.

## 2. Mission

V2 searches for mechanisms that are genuinely different and deliberately less
turnover-intensive than V1 while staying inside free H1 authority.

Useful blind search domains include:

- conditional session-range expansion rather than unconditional continuation;
- cross-pair lead/lag with explicit USD-factor neutrality;
- cross-sectional dispersion or relative-value dislocation;
- volatility/liquidity state transitions visible in H1 OHLCV;
- other literature-backed intraday mechanisms that do not require rates,
  authoritative swap, order book or news calendars.

These are research directions, not preselected families. Any proposal requiring
unavailable bid/ask, swap, fixing, macro release or rate-vintage fields is
ineligible unless the owner separately supplies authority.

Allowed terminal outcomes:

```text
FOREX_FREE_V2_REJECT_ALL
FOREX_FREE_V2_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
FOREX_FREE_V2_BLOCKED_DATA_OR_SELECTION
FOREX_FREE_V2_BLOCKED_PRELAUNCH
FOREX_FREE_V2_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Branches and worktrees

```text
integration branch    orca/forex-free-v2-integration
integration worktree  .worktrees/forex-free-v2/integration
base                  measured bee64be... terminal descendant only

lanes
.worktrees/forex-free-v2/p0-a2-accounting
.worktrees/forex-free-v2/p0-a3-data
.worktrees/forex-free-v2/d1-a4-proposals
.worktrees/forex-free-v2/d1-a5-proposals
.worktrees/forex-free-v2/d1-a6-proposals
.worktrees/forex-free-v2/d2-a7-novelty
.worktrees/forex-free-v2/d2-a9-feasibility
.worktrees/forex-free-v2/i-family-1
.worktrees/forex-free-v2/i-family-2
.worktrees/forex-free-v2/q-a7-prelaunch
.worktrees/forex-free-v2/e-exec-1
.worktrees/forex-free-v2/r-reproduce
.worktrees/forex-free-v2/r-a7-terminal
```

Every lane starts from one frozen wave SHA and records exact path/branch/base.
A1 alone cherry-picks and may never integrate a dirty lane.

## 4. Agents and capacity

- A1: controller, integrator, freezes, counters and sole ledger publisher;
- A2: runner/accounting/cost/digest correctness;
- A3: provider snapshot, clocks, DST and data authority;
- A4/A5/A6: two outcome-blind proposals each;
- A7: independent novelty, prelaunch and terminal audit; no repairs;
- A8/A9: feasibility and family implementations.

Maximum A1 plus three light lanes. Heavy cap is measured fresh. Scored arms in
one family run serially; separate families may overlap only if the host cap and
ledger serialization permit it. Do not run pytest beside a heavy worker.

## 5. Phase F2-R — terminal reconciliation

Before new research, verify:

- terminal `bee64be...` contains the completed A7 audit and corrected state;
- V1 W1 pin and six content-addressed rows;
- 6/6 exec/repro equality;
- observed=published=6 and zero duplicate keys;
- S1 sealed, data raw untracked, workers zero;
- both V1 families entered the forbidden inventory.

Create the V2 control plane under:

```text
research/control/forex_free_v2_run/
  run_contract.json
  state.json
  heartbeat.json
  event_log.jsonl
  worktree_manifest.json
  forbidden_family_inventory.json
  data_manifest.json
```

V2 budget starts `0/6`; historical Forex denominator remains 6/6.

## 6. Phase F2-P — factory hardening

### P1 — runner and exact accounting

Forex V1 demonstrated that high trade count can turn a plausible signal into a
large, stable loss. A2 must prove:

- one position lifecycle per trade ID;
- entry and exit cost applied once per side;
- proxy spread and stress tiers cannot be skipped or double counted;
- cash/account currency is not a pair and is excluded from concentration;
- USD conversion is either identity under the frozen USD-unit design or
  unavailable fail-closed;
- turnover and trade counts reconcile from fills;
- canonical digest hashes exact artifact bytes;
- observed/published/replay rules are once-only;
- parallel compute cannot parallel-append the ledger.

Use hand-computed multi-pair goldens spanning positive, negative, flat and
missing-bar cases.

### P2 — data, clock and DST replay

A3 replays existing source evidence without new download:

- seven pairs and exact snapshot hashes;
- H1 coverage, duplicates, missing bars and weekend classification;
- provider timestamp semantics and completed-bar rule;
- America/New_York, Europe/London, Asia/Tokyo and Australia/Sydney DST clocks;
- last allowed flat bar strictly before 17:00 New York;
- S0 folds and purge boundaries;
- D1 context never enters scored H1 returns;
- S1 never listed, opened, hashed or copied.

Because authoritative rollover/swap is absent, every proposed position must be
flat before the rollover boundary. Carry claims remain unavailable.

### P3 — low-frequency feasibility contract

Before proposals, freeze a V2 operational preference:

- no more than one entry per pair per UTC day;
- no more than three round trips per pair per week at the schedule-only stage;
- no position crosses the daily rollover boundary;
- all costs use V1's frozen base/stress authority unless a new owner-approved
  authority replaces it before selection.

This is an a priori feasibility rule, not a post-result fee rescue.

No PnL is computed in Phase P.

## 7. Phase F2-D1 — six blind proposals

A4/A5/A6 branch from the same `FOREX_FREE_V2_PROPOSAL_WAVE_SHA`. Each writes two
proposals and a search log. They may read the forbidden inventory and data
contract, but not V1 per-cell PnL tables.

Each proposal freezes:

- economic mechanism and causal prediction;
- primary literature/source trace;
- exact H1 observables and PIT timing;
- pair universe and any USD-factor-neutral construction;
- warmup, decision, entry, exit and forced-flat clocks;
- anchor, one neighbour and one causal/placebo control;
- cost tiers and break-even-cost diagnostic;
- expected trade frequency and schedule-only turnover;
- folds, concentration and drop-one-pair behavior;
- minimum decision/trade count;
- failure interpretation;
- outcome-blind attestation.

No grids, optimization, parameter menus, cost menus or after-result pair
selection.

## 8. Phase F2-D2 — A7/A9 and selection

A7-N audits:

- novelty against both rejected V1 families and their clock/sign variants;
- overlap among the six new proposals;
- source integrity and fabricated-citation risk;
- whether a control really removes the proposed mechanism;
- whether USD/market drift can explain the anchor by construction.

A9-F checks without PnL:

- H1 PIT coverage and warmup;
- DST and forced-flat correctness;
- entries/trades per pair and frequency contract;
- base/stress cost drag at the schedule level;
- pair/currency concentration and USD neutrality where claimed;
- missing-bar fail-closed behavior;
- implementation and resource risk.

A1 selects at most two families using:

1. novelty PASS and no rescue veto;
2. free-data authority PASS;
3. low-frequency/cost feasibility PASS;
4. meaningful control and drift/factor falsification;
5. adequate sample and pair breadth;
6. strongest source-to-test trace;
7. lowest implementation risk;
8. lexicographic ID tie-break.

Each selected family receives exactly three immutable arms. Maximum six scored
cells. Unused slots are never reassigned.

## 9. Phase F2-I — implementation

One clean lane per family owns only its module, fixtures, tests and evidence.
Required evidence:

- hand-calculated features, signals, fills, costs and PnL;
- completed-H1/PIT and one-event-lag tests;
- no-lookahead mutation test;
- DST tests across both US and European transitions;
- forced-flat before 17:00 New York;
- missing-bar `NO_TRADE`, never silent fill-forward;
- deterministic double generation;
- currency/pair exposure and cap invariants;
- cost once per side and break-even-cost calculation;
- real-snapshot schedule-only trade-frequency audit;
- meaningful drop-one-pair test;
- distinct anchor/neighbour/control digests;
- dummy publication/refusal/idempotent replay without real PnL.

A1 integrates one family at a time and runs targeted tests after every pick.

## 10. Phase F2-Q — W2 and prelaunch

A1 must:

1. integrate the central scorer before code freeze;
2. prove the scorer calls the actual family APIs rather than a sidecar
   approximation;
3. pin every schedule/fill/cost/metric/publication code hash;
4. run applicable six-arm dummy dry-run;
5. verify all arm and data digests;
6. run targeted Forex, protocol and full test suites alone;
7. run compileall, diff check and clean-tree checks;
8. probe resources and freeze heavy cap;
9. freeze code-bearing `FOREX_FREE_V2_W2`;
10. create detached equal-twin exec/repro trees with byte-identical staging and
    empty-ledger authority.

A7 independently recomputes all gates. Only
`FOREX_FREE_V2_S0_LAUNCH_AUTHORIZED` with zero unresolved HIGH/CRITICAL reaches
the owner checkpoint.

Stop before scoring until the owner explicitly says:

```text
GO FOREX V2 SCORED EXECUTION
```

## 11. Phase F2-E — scoring

Run at most two family chains. Within each chain:

1. anchor;
2. neighbour;
3. causal/placebo control.

For every cell:

```text
verify W2/data/arm pins
-> compute schedule and three chronological folds
-> next-allowed-H1 fills and forced-flat clock
-> charge frozen cost once per side
-> base + frozen stresses + break-even cost
-> pair/fold concentration and meaningful drop-one
-> canonical artifact and exact-byte digest
-> observed +1 once a scored metric exists
-> A1 publication once
-> replay zero-delta
-> heartbeat/counter checkpoint
```

No later cell may change after an earlier result becomes visible.

## 12. Stage-A gates

All applicable gates are mandatory:

- after-cost expectancy > 0;
- PF >= 1.10;
- at least 2/3 folds positive;
- no populated fold PF < 0.80;
- MDD within the frozen family ceiling;
- largest positive-fold share <= 50%;
- pair contribution within frozen concentration limit;
- base and stress PnL > 0 with stress PF >= 1.00;
- realised frequency/turnover obeys the preregistered contract;
- meaningful drop-one-pair survival;
- neighbour supports anchor;
- control does not reproduce the proposed mechanism;
- USD/common-factor explanation is rejected where the proposal claims
  neutrality;
- independent reproduction ALL_MATCH;
- zero unresolved HIGH/CRITICAL.

A coherent control ordering does not rescue negative expectancy. A positive
anchor whose placebo reproduces the mechanism is also rejected.

## 13. Reproduction and terminal audit

Recompute every scored cell from the detached reproduction tree in fresh
processes. Require exact schedules, fills, costs, trades, metrics, gates and
digests except explicitly volatile metadata.

Terminal A7 checks:

- W2 and data pin chain;
- once-only counters and ledger rows;
- exact artifact-byte hashes;
- cost/trade/turnover reconciliation;
- direction and control claims;
- denominator = historical 6 plus every V2 observation;
- S1, credential and deployment boundaries;
- workers zero and trees clean.

A survivor is frozen for a future S1 plan only. V2 never paper/live trades.

## 14. Tests and gate evidence

Minimum routing, extended with V2-specific suites after implementation:

```bash
.venv/bin/python -m pytest tests/assets/forex -q
.venv/bin/python -m pytest tests/assets/forex_free_v1 -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q
.venv/bin/python -m pytest tests -q
.venv/bin/python -m compileall research/assets/forex research/assets/forex_free_v1 research/assets/common
git diff --check
git status --porcelain=v1
```

Every gate artifact includes full SHA, command, exit code, stdout/stderr paths,
expected/observed, hashes, verdict, blockers, corrective action and tree state.
Only PASS/FAIL/NOT_RUN/BLOCKED are allowed gate labels.

Owner checkpoints:

1. intake and terminal reconciliation;
2. factory/data/frequency gates;
3. six proposals;
4. novelty/feasibility selection;
5. family implementations and W2;
6. independent A7 prelaunch;
7. each family after a later owner GO;
8. reproduction and terminal A7.

## 15. Hard boundaries

- Zero-cost/no-new-account remains in force unless owner changes it explicitly.
- No paid data or fabricated bid/ask/swap/rate/fixing authority.
- No S1, paper, live, orders, credentials or broker adapter activity.
- No raw-data commit.
- No optimization, parameter rescue, pair cherry-pick or family substitution.
- No rewriting V1 results or denominator.
- No force-push, main merge, worktree deletion or history rewrite without owner
  instruction.
- A correct `REJECT_ALL` is a complete research outcome.

## 16. First report from a fresh A1

```text
measured UTC
root / branch / full HEAD / porcelain
Forex V1 terminal SHA and A7 ancestry
historical observed/published denominator
provider/data authority and snapshot hashes
S1 seal and worker scan
V2 integration worktree / branch / base SHA
RAM / CPU / disk / preliminary heavy cap
GO/NO_GO for reconciliation and factory-only phases
```

A1 may proceed autonomously through prelaunch, then must stop before the first
V2 scored cell until the explicit owner GO arrives.
