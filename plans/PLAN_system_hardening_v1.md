# SYSTEM-HARDENING-V1 — Bounded control-plane repair before research resumes

Status: `PLANNED_NOT_STARTED`

This document proposes a controlled pause of the currently active Crypto,
Stocks, and Forex cycles so the shared research control plane can be repaired.
It is not authority to stop processes, create branches, score cells, merge, or
push. Execution starts only after the owner explicitly dispatches this plan.

This plan does not replace any asset-cycle scientific plan. Frozen hypotheses,
arm definitions, data partitions, gates, budgets, and prior evidence remain
owned by their original cycle authorities.

## 1. Decision and scope

Recommended decision: pause all three asset cycles at their next safe
checkpoint and complete the mandatory SHV1 gates before resuming them.

This is a bounded maintenance pause, not a request to rebuild the platform or
finish every desirable upgrade. Only defects that can corrupt coordination,
repeat failed jobs indefinitely, create registry drift, or weaken auditability
are blocking for resumption.

The following larger improvements are explicitly deferred to a later SHV2
cycle unless they become necessary to pass an SHV1 gate:

- migrating all historical data into a content-addressed store;
- deleting or archiving the existing worktree/branch history;
- redesigning every asset runner into a single framework;
- building a new statistics service;
- changing scientific gates, thresholds, families, or scored-cell budgets.

## 2. Measured starting point

Measured on 2026-09-08 from
`/Users/hoangminhlong/my-quantitative`:

- owner checkout: `main` at
  `180dbc97aed19b9761f973373f98043cadb90837`, equal to `origin/main`;
- owner checkout was already dirty before this plan:
  `plans/ACTIVE_CYCLES.json` modified and `.zcode/` untracked;
- Crypto V17 integration:
  `2b176e3ed9ec1da5fedc189e665e13a7a95a9eb4`, clean, P0 active,
  budget 0/6 and S1 sealed;
- Stocks V12 integration:
  `69459102ef1ef93459991791902ec78fd0744075`, clean, D2 in progress,
  budget 0/6 and S1 sealed;
- Forex V8 integration:
  `5b1c23c9106f392657c63c3b578d33be4551ee36`, clean, D2 selection
  frozen, budget 0/6 and S1 sealed;
- program ledger: 233 published / 236 observed, zero survivors, S1 sealed;
- targeted governance tests: 54 passed;
- family-failure registry validation: 55 entries, zero errors;
- the current router is stale: `plans/ACTIVE_CYCLES.json` names older closed
  cycles while `CONTINUE.md` names V17/V12/V8;
- the repository currently has 51 worktrees, 319 local branches, and about
  12 GB under `.worktrees`;
- Stocks V12 has repeatedly retried the same deterministic D2 failure:
  `TypeError: fromisoformat: argument must be str` in
  `d2_v12_novelty_measure.py`. This is a code/schema failure and must not be
  classified as a transient lock or network failure.

Every value above must be remeasured at dispatch. Drift is reported, never
silently normalized. The pre-existing dirty owner files must be preserved and
must not be overwritten by bootstrap.

## 3. Why pause now

All three active cycles are still before their first scored cell. Their budgets
remain untouched and S1 remains sealed. This is therefore the least expensive
point to repair shared governance.

Continuing now creates avoidable risks:

1. a stale router can dispatch an agent into a closed cycle or wrong worktree;
2. deterministic failures can consume hours through blind retries;
3. dashboard refreshes can dirty tracked control files;
4. incompatible state schemas make automation infer lifecycle status;
5. dozens of worktrees make ownership and resource usage harder to establish.

No evidence currently requires abandoning any scientific cycle. After SHV1,
each asset resumes from its last verified checkpoint.

## 4. Pause protocol

The owner/A1 of each active cycle performs its own pause. The system-hardening
controller must not kill arbitrary processes or edit another cycle's evidence.

For each of Crypto V17, Stocks V12, and Forex V8:

1. stop launching new work;
2. let a valid atomic write or short-running gate finish;
3. cancel only an owned retry loop after its current attempt returns;
4. record exact HEAD, branch, tree status, phase, budget, denominators, S1
   seal, workers, lock ownership, and the next safe action;
5. hash every frozen scientific artifact named by that cycle;
6. append a pause event without rewriting history;
7. leave the worktree on disk and release owned resources.

Until a versioned lifecycle schema is installed, retain the cycle's existing
valid status and add `hard_stop_reason: SYSTEM_HARDENING_V1`. Do not invent a
new status in legacy records. SHV1 may introduce `PAUSED_MAINTENANCE` only via
a schema migration with backward-compatible readers.

Special handling for Stocks V12: its owner must stop the bounded waiter after
the current attempt, record the repeated deterministic exception and retry
count, and leave D2 incomplete. No manual data repair or scientific workaround
is permitted during the pause.

## 5. Branch and worktree topology

The commit containing this plan becomes `OWNER_PLAN_SHA`. An uncommitted copy
of this plan is not an authorized bootstrap.

Recommended topology:

```text
.worktrees/system-hardening-v1/
  integration/   orca/system-hardening-v1-integration
  router/        orca/system-hardening-v1-router
  scheduler/     orca/system-hardening-v1-scheduler
  dashboard/     orca/system-hardening-v1-dashboard
  audit/         orca/system-hardening-v1-audit
```

Before every `git worktree add`, print and verify `pwd`, branch occupancy,
base ancestry, and clean-tree status. Never reuse a branch already checked out.

All implementation lanes branch from one frozen `SHV1_WAVE_SHA`. A1 alone
integrates commits in the declared order. No lane merges directly into main.

## 6. Agent allocation

Use at most A1 plus three light lanes concurrently. This cycle should not
compete with asset research for a heavy slot.

- A1 Controller: intake, freeze, integration, gate publication, and resume
  packet. A1 never self-approves the terminal verdict.
- A2 Router/Schema: canonical active-cycle registry, versioned schemas,
  atomic writes, and lifecycle adapters.
- A3 Scheduler/Retry: job admission, heavy-lock queueing, error
  classification, bounded retry, cancellation, and crash recovery.
- A4 Dashboard/Doctor: read-only runtime snapshots, freshness checks,
  consistency diagnostics, and operator CLI surfaces.
- A7 Independent Auditor: works from frozen evidence after implementation;
  tests negative cases and reports objections without repairing them.

If fewer agents are available, run A2, A3, and A4 sequentially. Separation of
A1 and A7 remains mandatory.

## 7. Required deliverables

### 7.1 Canonical cycle control CLI

Provide one command surface, tentatively:

```text
researchctl cycle list
researchctl cycle doctor
researchctl cycle pause <cycle>
researchctl cycle resume <cycle>
researchctl job list
researchctl job cancel <owned-job>
researchctl locks inspect
researchctl program counters
```

The exact module name may follow repository conventions, but there must be one
documented operator entrypoint. It must resolve cycle IDs to exact paths,
branches, plans, HEADs, phases, and state artifacts without guessing from
worktree existence.

### 7.2 Versioned state and router schema

Create a versioned canonical schema for:

- active-cycle identity and lifecycle;
- exact worktree/branch/plan authority;
- current phase and next authorized action;
- budget and observed/published denominators;
- S0/S1 status;
- worker and lock ownership;
- heartbeat freshness;
- pause/resume reason and timestamp.

Legacy records remain byte-unchanged. Read adapters normalize them in memory;
writers only emit the new schema for new/explicitly migrated records.

`plans/ACTIVE_CYCLES.json` becomes either the canonical atomically written
registry or a generated projection from a more authoritative registry. There
must never be two writable sources of truth.

### 7.3 Transactional writes

All mutable control files must use:

1. schema validation before write;
2. write to a sibling temporary file;
3. `fsync` where supported;
4. atomic rename;
5. post-write read and validation;
6. append-only event describing the transition.

Concurrent writers must fail closed through a lock or compare-and-swap token.
Malformed or partially written control state is `CONTROL_STATE_DRIFT`, not a
recoverable default.

### 7.4 Scheduler and retry classifier

Implement explicit classes:

- `RESOURCE_BUSY`: queue without consuming a scientific attempt;
- `TRANSIENT_TRANSPORT`: bounded backoff with a frozen retry limit;
- `RATE_LIMITED`: honor provider reset evidence and quota policy;
- `CODE_OR_SCHEMA_ERROR`: no automatic retry;
- `DATA_AUTHORITY_FAILURE`: terminal/blocking for the applicable gate;
- `HASH_OR_CONTRACT_DRIFT`: immediate hard stop;
- `OPERATOR_CANCELLED`: clean resource release and recorded cancellation.

The same exception signature must not loop indefinitely. Retry state must
survive controller restart. A job must expose owner cycle, command digest,
attempt, start time, heartbeat, resources, and last classified failure.

### 7.5 Dashboard separation

Dashboard collection and refresh are read-only with respect to tracked files.
Ephemeral snapshots go under a gitignored runtime directory. Starting,
refreshing, or stopping the dashboard must leave `git status --porcelain=v1`
unchanged.

The dashboard must label stale and contradictory state; it must not repair it.

### 7.6 Doctor and resume packets

`researchctl cycle doctor` must detect at least:

- stale router entries;
- branch/worktree mismatch;
- missing or malformed state;
- stale heartbeat;
- live worker not represented in state;
- lock owner without a live process;
- budget/denominator disagreement;
- S1 seal disagreement;
- frozen-artifact hash drift;
- tracked-file mutation caused by monitoring.

Generate a machine-readable and Markdown resume packet for each paused asset.

## 8. Execution phases

### H0 — Owner decision and safe pause

- receive explicit dispatch;
- remeasure all anchors and dirty files;
- have each owning A1 publish a pause packet;
- stop the Stocks deterministic retry loop through its owner;
- verify scored budgets remain zero and S1 remains sealed.

Gate H0: three valid pause packets, zero unowned workers, no scientific hash
drift, and no scored-cell publication during the transition.

### H1 — Contract freeze

- freeze `OWNER_PLAN_SHA`, `SHV1_WAVE_SHA`, file ownership, lane paths,
  schema version, error taxonomy, and acceptance tests;
- snapshot current router contradictions and legacy state shapes;
- preregister migration and rollback behavior.

Gate H1: A7 can reproduce the inventory and hashes from a clean tree.

### H2 — Router and state foundation

- implement canonical registry/schema and legacy read adapters;
- implement atomic transition helpers;
- implement list/doctor/pause/resume commands;
- reconcile V17/V12/V8 only after the owner classifies the currently dirty
  `plans/ACTIVE_CYCLES.json`.

Gate H2: exact active cycles are V17/V12/V8; closed cycles cannot appear active;
parallel-write and truncated-file tests fail closed.

### H3 — Scheduler and retry safety

- implement job records and admission;
- integrate heavy-lock inspection and fair queueing;
- implement the retry taxonomy and bounded backoff;
- add graceful cancellation and stale-lock recovery.

Gate H3: a fixture reproducing the Stocks `fromisoformat` TypeError executes
once and stops as `CODE_OR_SCHEMA_ERROR`; it never enters retry/backoff.

### H4 — Read-only operations surface

- separate runtime dashboard data from tracked evidence;
- add doctor output and freshness labels;
- document operator commands and recovery paths.

Gate H4: repeated dashboard refreshes produce zero tracked or untracked changes
outside the approved gitignored runtime directory.

### H5 — Integration and regression

Integration order: A2, A3, A4, then A1 reconciliation. After every pick:

- run lane-targeted tests;
- run schema validation;
- run `git diff --check`;
- verify asset scientific hashes and counters remain unchanged.

Run the full suite alone only when all asset workers are paused and no heavy
job owns the lock. `NOT_RUN_RESOURCE_CONFLICT` is the truthful result if that
condition is not met.

### H6 — Independent audit and release

A7 receives the frozen wave, implemented commit, test logs, negative fixtures,
and all pause/resume packets. A7 verifies evidence independently and does not
repair findings.

Possible verdicts:

- `SYSTEM_HARDENING_V1_PASS`;
- `SYSTEM_HARDENING_V1_INCOMPLETE`;
- `SYSTEM_HARDENING_V1_FAIL_CONTROL_DRIFT`.

Only `SYSTEM_HARDENING_V1_PASS` permits a resume recommendation.

## 9. Mandatory acceptance gates

1. **G0 Baseline preservation** — three pause packets; budgets unchanged;
   S1 sealed; scientific hashes unchanged.
2. **G1 Router truth** — a single writable authority resolves exactly the
   current cycles, paths, plans, branches, and states.
3. **G2 Atomic state** — concurrent, interrupted, malformed, and stale writes
   are tested and fail closed.
4. **G3 Retry safety** — deterministic code/schema failures execute once;
   transient retries are bounded and evidenced.
5. **G4 Resource safety** — job admission and heavy-lock behavior prevent
   hidden contention, spin loops, and orphan ownership.
6. **G5 Monitoring purity** — dashboard/doctor reads do not mutate tracked
   control files.
7. **G6 Legacy compatibility** — historical cycle records are readable without
   byte rewrites; existing governance tests remain green.
8. **G7 Repository regression** — targeted suites, governance suites,
   compile checks where applicable, `git diff --check`, and the affordable full
   suite pass from a clean integration tree.
9. **G8 Independent audit** — no unresolved HIGH/CRITICAL objection and no
   missing mandatory evidence.

PASS, FAIL, and NOT RUN must be reported literally. A missing gate is not PASS.

## 10. Resume protocol

SHV1 does not authorize scored execution. After G0–G8 pass:

1. generate one resume packet for each cycle;
2. remeasure integration HEAD/tree/workers/locks;
3. compare scientific hashes with its pause packet;
4. verify budget, denominators, and S1 seal;
5. rerun the cycle's applicable cheap gates;
6. resume from the recorded next safe action.

Recommended resume order:

1. Forex V8, because selection is frozen and implementation is next;
2. Stocks V12, after the deterministic D2 bug is fixed and independently
   tested inside the Stocks cycle authority;
3. Crypto V17, after transport/resource admission is rechecked.

The order is operational, not a claim about expected profitability. Cycles may
run concurrently again only after the new scheduler admits them.

Every cycle retains its own pre-scoring owner gate. No prior owner GO carries
across this maintenance pause.

## 11. Hard stops and forbidden actions

Stop immediately on scientific hash drift, S1 access, budget change, unknown
worker ownership, router ambiguity, malformed state, or inability to preserve
the owner's pre-existing dirty files.

This plan does not authorize:

- scoring any asset cell;
- editing frozen hypotheses, controls, thresholds, or selection files;
- rewriting historical event logs;
- deleting worktrees or branches;
- resetting another agent's work;
- killing processes not owned by the current cycle/controller;
- using, logging, or committing credentials;
- merging to main or pushing to a remote.

## 12. Closeout report

The terminal report must include:

- full SHA chain and tree cleanliness;
- all file ownership and merge order;
- gate commands, exits, pass/fail counts, and log paths;
- negative-test results for atomicity, retry, lock, and dashboard behavior;
- pre/post hashes for every asset scientific freeze;
- program counters, budgets, S1 seals, workers, and locks;
- A7 objections and final verdict;
- exact next action for Forex V8, Stocks V12, and Crypto V17;
- an explicit list of deferred SHV2 work.

Suggested owner dispatch after committing this plan:

```text
Execute SYSTEM-HARDENING-V1 from PLAN_system_hardening_v1.md. Start with H0
only: remeasure all anchors, preserve the existing dirty owner files, coordinate
a safe pause of Crypto V17, Stocks V12 and Forex V8 through their owning A1s,
and report the three pause packets. Do not score, merge main, push, delete
worktrees, or change frozen scientific artifacts. Continue autonomously through
H1-H6 only after H0 passes. A7 must independently audit before any resume
recommendation.
```

