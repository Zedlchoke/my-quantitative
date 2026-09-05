# CRYPTO V13 — PIT-AUTHORITY ADOPTION AND CONDITIONED DISCOVERY AFTER V12 REJECT_ALL

> Owner plan for the next Crypto research cycle, dated 2026-09-04.
>
> `PLAN.md` remains the historical authority for V11/V12 and must not be
> rewritten. `PLAN_crypto_stronghost.md` remains the strong-host operations
> authority. This file starts V13 only. Profit is not a required outcome; a
> correct `V13_REJECT_ALL` is a successful research run.

## 0. Frozen starting point

Measured terminal authority (A1 must remeasure; drift affecting identity,
counters, data authority or S1 is an intake blocker):

```text
completed branch       orca/v12-integration (authority on origin)
terminal SHA           b1529e1925ecb195920ac9f38c5b819db409218d
terminal verdict       V12_REJECT_ALL
terminal A7            V12_TERMINAL_APPROVED_0_FAIL (8/8 PASS, 3 non-blocking)
V12 cells              6 observed / 6 published / 6 reproduced ALL_MATCH
V12 budget             6/9 (ILLIQ replication BLOCKED_DATA, 3 slots unused)
W12 execution SHA      f0799cae6fc47846937cf1a370719314696ee990
W12R2 driver fix       ce52e3e2e817806c984b3e2cdda9daace17440f7 (TECHABORT
                       remediation, science surface empty, zero budget)
crypto denominators    131 published / 134 observed logical (>=128 floor)
survivors              0 across the whole program
S1                     SEALED_UNTOUCHED
paper/live/orders      none
workers at close       0
Data Fusion V1 core    FROZEN at MULTISOURCE_DATA_CORE_SHA
                       c6a0576ef98dd4392e90805c8ba33821da62eabc
```

Local/origin divergence is expected at intake: the local
`orca/v12-integration` branch may still sit at the pre-launch hard stop. V13-R
reconciles it (fast-forward only) and verifies the transferred ledger package
before any new work. Lesson L-V11-5 (machine-local ledgers strand on host
migration) is binding here.

## 1. What is closed and may not be rescued

Cumulative ancestry veto, in addition to every entry already in the V12
forbidden-family inventory:

1. V6 funding-carry horizons and their inverse;
2. V8R cross-sectional reversal;
3. V9 time-series trend (L14/L28) and dollar-volume shock continuation;
4. V10 M01 aggressor-absorption;
5. V11 LOT residual-MAX and OILEV weekly-quintile v1;
6. V11 ILLIQ-AMIHUD as originally frozen (rejected on symbol concentration
   0.7055);
7. V12 OILEV-V2 as frozen (anchor sign falsified by its own inverted control)
   and V12 BAB-LOWBETA (dead after native costs and funding);
8. any sign-flip, horizon tweak, cost exemption, universe carve-out or
   threshold relaxation whose purpose is to rescue any row above.

### 1.1 Shadow-effect region — the only sanctioned re-entry

Five recent families died because a control arm outperformed its anchor. Three
shadow effects now exist as *measured control-arm observations*: inverted
OI-flow (+0.758 raw in V12 OILEV-V2-INV), V11 LOT inversion, and (stocks
program) vol-level sorting. These are not tradable findings and not rescuable
descendants. A V13 proposal may enter this region ONLY through the front door:

- it states a new economic mechanism in its own words (for example a
  liquidity-provision / crowding-premium story), never "the inverted anchor";
- the proposal packet discloses that the sign was already observed in a V12 or
  V11 control arm, and the family is preregistered as **confirmatory**;
- it carries its own causal negative control designed to separate the new
  mechanism from the rejected ancestor AND from beta/funding carry;
- A7-N measures anchor rank correlation against the frozen OILEV-V2 anchor and
  its inverted control; |rho| <= 0.20 against each, on the common window,
  or the proposal is INELIGIBLE;
- Stage-A gates apply with no relaxation, and the confirmatory status is
  recorded in the family verdict and the denominator.

## 2. Mission and allowed scope

V13 asks two questions, in this order:

> 1. Can the frozen Data Fusion V1 PIT core be adopted for crypto without
>    disturbing any frozen V12 identity, and does it make existing authorized
>    datasets (bars, funding, OI, mark price) strictly more auditable?
> 2. Can an outcome-blind mechanism conditioned on positioning/liquidity
>    information produce incremental after-cost information beyond buy-and-hold
>    and BTC-beta context?

Scope rules:

- Data Fusion adoption happens BEFORE the V13 data and selection freeze, by
  explicit compatibility cherry-pick of the frozen core; shared code must
  prove compatibility with the crypto calendar, cost model and ledger.
- V13 adoption covers the record schema, PIT join contract, identity mapping
  and license/entitlement machinery. Existing authorized crypto datasets are
  re-keyed as fusion records with explicit `available_time_utc`; retrieval time
  never substitutes for availability.
- No new source, download, key or signup enters scored use without a separate
  owner data-authority decision and `/pit-data-audit`.
- The ILLIQ replication may re-open ONLY if an authorized window covering the
  frozen replication brief becomes available through such an owner decision;
  the frozen V12 brief is then executed unchanged. Window substitution remains
  forbidden.

Allowed terminal outcomes:

```text
V13_REJECT_ALL
V13_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1
V13_BLOCKED_DATA_OR_SELECTION
V13_BLOCKED_PRELAUNCH
V13_INCOMPLETE_NOT_PROMOTABLE
```

## 3. Branch and worktree topology

```text
branch    orca/v13-integration
worktree  .worktrees/crypto/v13/integration
base      measured V12 terminal b1529e1... after V13-R reconciliation
lanes     .worktrees/crypto/v13/{p0-a2-fusion,p1-a3-data,d1-a5-proposals,
          d1-a6-proposals,d1-a8-proposals,d2-a7n-novelty,d2-a9f-feasibility,
          i-family-1,i-family-2,q-a7-prelaunch,e-exec-1,r-reproduce,
          r-a7-terminal}
```

Never check out one branch in two worktrees. Every lane records path, branch,
base SHA, head SHA, ownership and disposition in
`research/control/v13_run/worktree_manifest.json`.

## 4. Agent allocation and concurrency

- A1: controller, only integrator, freezer, counter owner, publisher;
- A2: fusion adoption and accounting/publication regression;
- A3: PIT data, window and benchmark authority, fusion record re-keying;
- A5/A6/A8: two blind proposals each, six total;
- A7: independent novelty, prelaunch and terminal audits; never repairs;
- A9: feasibility and family implementation as assigned.

Concurrency: A1 plus at most three light lanes; full pytest runs alone; heavy
cap from a fresh probe; arms within a family are serial; only A1 appends the
canonical ledger. The strong host is the default execution seat per
`PLAN_crypto_stronghost.md`; its staging-transfer verification pattern is
mandatory for any host move.

## 5. Phase V13-R — terminal reconciliation

A1 verifies:

- V12 terminal SHA, A7 ancestry and verdict on the authority branch;
- local `orca/v12-integration` is fast-forwarded to the terminal (never
  merged, never rebased);
- the strong-host ledger package transfers with matching checksums; the
  canonical registry reconciles 6/6 V12 rows and the 131/134 denominators;
- TECHABORT forensics: attempt-1 consumed zero budget, W12R2 touched driver
  code only, BAB cells under W12R remain valid;
- S1 seal, workers zero, clean trees, no active scorer;
- no forbidden-family inventory drift.

Create `research/control/v13_run/{run_contract,state,heartbeat,
event_log,forbidden_family_inventory,worktree_manifest,lessons_register}`
with budget `0/9`, V13 counters at zero, historical 131/134 preserved
separately, and L-V11-1..7 plus the V12 falsification observations seeded.

## 6. Phase V13-P — adoption, factory and data gates

### P0 — Data Fusion core adoption (new)

A2 cherry-picks the frozen core (exact SHA c6a0576e...) and proves:

- record schema, PIT join and identity mapping compile and pass their own
  tests inside the crypto tree;
- every authorized crypto dataset maps to fusion records with true
  availability semantics (bar close time, funding settlement, OI snapshot
  stamps);
- a regression test pins: a decision at T can never read a row whose
  `available_time_utc > T`;
- no V12 frozen artifact, digest, counter or ledger byte changes.

Adoption failure blocks proposals; V13 may then proceed data-fusion-less only
if the owner accepts the downgrade in writing.

### P1 — accounting/publication regression

Inherit the V12 suite and add: zero-position and out-of-contract refusal;
drop-one non-vacuousness (L-V11-7: the dropped symbol must have held
positions); observed increments once, replays never; append-only corrections
leave counters untouched; simultaneous workers cannot append without A1
serialization.

### P2 — data authority replay

A3 replays every authorized dataset without downloading: exact hashes, window
coverage including tail completeness (G05 lesson: coverage must fail closed,
never synthesize a stale tail), funding/OI/mark availability stamps expressed
as fusion records, benchmark context availability, S0 folds and purge, S1
never listed, opened, hashed or copied.

### P3 — baseline invariants

Freeze before proposals: book/cash accounting; fills and cost schedule
including funding settlement; force-flat fold boundaries; benchmark and
BTC-beta context calculation; concentration, drop-one and stress conventions;
minimum decisions/positions; resource formula and timeout.

No PnL is computed in Phase P.

## 7. Phase V13-D1 — blind proposal generation

Three lanes branch from the same `V13_PROPOSAL_WAVE_SHA`. Each writes exactly
two outcome-blind proposals with the full V12 packet discipline: mechanism and
falsifiable prediction; literature; PIT observable with fusion-record
availability semantics; universe/warmup/clock/holding/fills; anchor, one
neighbour, one causal negative control; incremental test vs benchmark context;
base and stress costs; turnover and sample floor; drop-one design; failure
interpretation; source-to-test map; signed outcome-blind attestation.
Proposal agents receive the forbidden-family packet (Section 1 plus the V12
inventory) and no per-arm outcome files.

## 8. Phase V13-D2 — independent audit and selection

A7-N measures novelty/anti-rescue, including rank correlation against every
forbidden ancestor AND its inverted control (Section 1.1 thresholds). A9-F
checks schedule feasibility on the real snapshot, cost/turnover/cap
arithmetic, control identifiability and host resources without computing PnL.

A1 selects at most two families by the frozen V12 rubric: no novelty/rescue
veto; authorized data PASS; identifiable factor/control test; feasibility
PASS; strongest source-to-test trace; lowest implementation risk;
lexicographic hypothesis-ID tie-break. Exactly three arms per family. Ceiling
six scored cells (budget ceiling nine); unused slots are never reassigned.

## 9. Phase V13-I — implementation

One lane per selected family from the selection-freeze SHA. Evidence required
per family mirrors V12: hand-computed feature/target goldens; PIT/no-lookahead
mutation tests; next-allowed-fill; deterministic double generation;
control-cannot-equal-anchor; cap/gross/net/cash invariants; cost-once and
funding settlement checks; schedule-only feasibility on the real snapshot;
non-vacuous drop-one; dummy publication/refusal/replay with zero scored
metrics. A1 integrates one family at a time with targeted tests after each
pick.

## 10. Phase V13-Q — freeze and prelaunch

A1 runs: full crypto and compatibility suites; applicable-arm dummy dry-run
into a temporary ledger; exact arm digests, pairwise unique; data and
benchmark hashes; budget 0/9; full pytest alone; compileall;
`git diff --check`; fresh resource probe; freeze code-bearing
`V13_W1`; create detached equal-twin execution/reproduction trees; stage
byte-identical read-only data and the reconciled empty-seed ledger authority.
If execution moves to the strong host, the staging transfer artifact is
recorded and verified exactly as in V12.

Independent A7 recomputes the chain; only `V13_S0_LAUNCH_AUTHORIZED` with zero
unresolved HIGH/CRITICAL reaches the owner. A1 hard-stops before the first
scored cell until the owner types:

```text
GO V13 SCORED EXECUTION
```

## 11. Phase V13-E — scored execution and TECHABORT discipline

After GO, cells run serially per family (anchor, neighbour, control). Any
crash before a scored metric exists is a `TECHABORT`: record forensics,
consume zero budget, fix driver-only code with the science surface empty,
re-freeze (W1Rn), obtain an A7 delta authorization, and continue. Any crash
after a metric exists is observed and published whatever its value.

## 12. Stage-A gates (frozen ex ante)

A family must satisfy every applicable gate:

- after-cost anchor expectancy > 0;
- position PF >= 1.10;
- at least 2/3 chronological folds positive;
- largest fold-positive share <= 50%;
- MDD <= 20%;
- largest symbol positive-PnL share <= 0.70;
- stress set positive (stress PF >= 1.00);
- non-vacuous drop-one symbol and fold survival;
- benchmark-context / BTC-beta excess positive in at least 2/3 folds;
- neighbour supports the mechanism;
- the causal control does not reproduce it under its preregistered rule;
- independent reproduction ALL_MATCH;
- zero unresolved HIGH/CRITICAL.

Positive raw PnL never overrides failed incremental context or a firing
control. A control that outperforms a negative anchor falsifies the mechanism
(confirmatory-region families included).

## 13. Reproduction, terminal closeout and denominator discipline

Reproduce every cell from the detached twin in fresh processes; exact match
on schedules, fills, costs, metrics, gates, digests except volatile metadata.
Terminal A7 rechecks ledger once-only accounting, artifact-byte hashes,
funding/cost reconciliation, family verdicts, denominator math, S1 seal,
deployment boundaries, workers zero, clean trees.

The terminal report must update the program multiple-testing statement:
observed denominator becomes 134 + computed V13 cells; published 131 +
published V13 cells. If a survivor exists, freeze it for a future
owner-approved S1 plan; do not open S1 and do not paper/live trade in V13.

## 14. Required commands and reporting

Use `.venv/bin/python`. Minimum suite (A1 discovers exact names after
implementation): the crypto asset suites, protocol contracts, data-fusion
compatibility suite, full `pytest -q` alone, `compileall` on touched
packages, `git diff --check`, `git status --porcelain=v1`. Every gate reports
command, exit code, stdout/stderr paths, full HEAD, input/output hashes,
expected/observed, verdict, blocker, tree status.

Owner checkpoints: intake/reconciliation; P gates incl. fusion adoption;
six proposals and audits; selection freeze; implementations and W1; A7
prelaunch; family completions after GO; reproduction and terminal A7.

## 15. Hard boundaries

- No S1 access, paper, live, orders, credentials.
- No new data source, key, signup or download without an owner
  data-authority decision and `/pit-data-audit`.
- No optimizer, scored grid, threshold weakening, family substitution or
  result-aware retrofit of Data Fusion.
- No rewriting prior ledgers, artifacts or terminal reports.
- No push, main merge, history rewrite or worktree deletion without owner
  instruction.
- Report gates only as PASS/FAIL/NOT_RUN/BLOCKED. A correct negative result
  is preferable to a fabricated survivor.

## 16. First report from a fresh A1

```text
measured UTC
root path / branch / full HEAD / porcelain
V12 terminal SHA + A7 ancestry on the authority branch
local vs origin branch state and ledger-package checksums
crypto denominators 131/134 and budget 0/9
S1 seal and active worker scan
data authority and fusion-core SHA
integration worktree path / branch / base SHA
RAM / CPU / disk / preliminary heavy cap / strong-host availability
GO/NO_GO for reconciliation and factory-only phases
```

A1 continues autonomously through prelaunch and stops before the first scored
V13 cell unless a real blocker occurs earlier.
