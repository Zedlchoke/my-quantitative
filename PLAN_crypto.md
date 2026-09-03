# CRYPTO PLAN — V11 TERMINAL RECONCILIATION AND V12 CONTROLLED DISCOVERY

> Owner authority for a fresh A1 coding-agent context.
>
> Read this file in full before changing files, creating worktrees, launching
> agents or computing a scored result. Historical `PLAN.md` remains the frozen
> V11 contract and must not be rewritten. This document governs V11 terminal
> reconciliation and the next crypto-only V12 cycle.

## 0. Measured starting point and authority order

Measured from `/Users/hoangminhlong/my-quantitative` on 2026-09-03 after
`git fetch --all --prune`:

```text
origin/main                    b8876ef8e0f7dd235d66f5cae5bfd8fd9034147f
origin/orca/v11-integration    df18f53dba30291065f9be157cae04bdcf15bf50
relationship                  origin/main is an ancestor; V11 is 123 commits ahead
V11 sprint verdict            V11_REJECT_ALL
V11 terminal audit            APPROVED, 0 FAIL
V11 reproduction              ALL_MATCH, 33/33 matrix cells
V11 base cells                6 computed and published of 9 eligible
logical denominators          125 published / 128 observed
S1                            SEALED_UNTOUCHED
paper/testnet/live/orders     none
owned workers at close        0
```

Primary V11 evidence at `origin/orca/v11-integration@df18f53`:

- `research/control/v11_run/terminal_report_v11.json`;
- `research/control/v11_run/family_verdict_lot.json`;
- `research/control/v11_run/family_verdict_illiq.json`;
- `research/control/v11_run/family_blocked_oilev.json`;
- `research/control/v11_run/reproduction_report_lot.json`;
- `research/control/v11_run/reproduction_report_illiq.json`;
- `research/audits/v11p/a7_terminal/a7_terminal_wave1.json`;
- `research/audits/v11p/a7_terminal/a7_terminal_wave2.json`;
- `research/control/v11_run/lessons_register.json`.

Authority order for this cycle:

1. this owner-approved `PLAN_crypto.md`;
2. the frozen historical `PLAN.md` for interpreting V11 only;
3. independent A7 terminal audit arithmetic;
4. V11 terminal reports and family verdicts;
5. state, heartbeat, map and prose summaries.

Lower-ranked stale metadata never overrides independently reproduced science.
A1 MUST re-measure all refs, SHA values, dirty files, worktrees, workers and
counters. If any measured fact differs, preserve this section as historical
intake, write `research/control/v12_run/intake_delta.json`, and stop only when
the difference affects identity, results, authority or data safety.

## 1. Scientific reading of V11 — frozen, no rescue

### 1.1 LOT is closed REJECT

`V11-SEED-LOTTERY-MAX-SKEW` failed seven gates:

```text
anchor net-return sum    -0.791808705897
anchor PF                 0.724508191586
anchor MDD                0.791808705897
positive folds            1/3
inverted control net     +0.710926701399
inverted control PF       1.337193330325
```

The positive inverted control is falsification evidence, not an automatically
tradable candidate. V12 MUST NOT invert LOT, retune its lookback, reduce its
fees, select its winning symbols or rename it as a new mechanism.

### 1.2 ILLIQ is a near-miss REJECT and a replication candidate

`A8-V11-ILLIQ-AMIHUD` passed 12/13 frozen gates:

```text
anchor net-return sum    +0.581969254868
anchor PF                 1.354841010840
anchor MDD                0.091821657373
positive folds            3/3
stress cells              positive and PF >= 1
inverted control          negative
largest positive-fold share 0.705496856297 > frozen limit 0.50
```

It remains `V11_FAMILY_REJECT`. V12 may perform one new preregistered
replication, but MUST NOT lower the 0.50 concentration threshold, change the
28/56-day mechanism after seeing results or call the V11 window OOS.

### 1.3 OILEV is unscored, not rejected for PnL

`A8-V11-OILEVER-DELEV` was blocked before scoring: all 52/52 decision stamps
produced weights above the frozen adapter cap. Its PnL is unknown. A new
cap-compatible design is permitted only as a new identity frozen before any
score. Raising the cap or post-score renormalisation is forbidden.

### 1.4 V11 accounting remains immutable

- Six legitimate V11 base cells are published.
- Two defective zero-position computations are disclosed observations, remain
  quarantined and count conservatively in the observed denominator.
- Published logical total is 125; observed logical total is 128.
- Reproduction is 33/33 all-match for all applicable stress matrix cells.
- No V11 result is promoted to S1, paper, testnet or live.

## 2. Mission and allowed outcomes

This plan has two missions:

1. Reconcile V11 terminal metadata without changing any scientific result.
2. Build and prelaunch-audit a nine-cell V12 cycle containing:
   - exact-mechanism ILLIQ replication on a separately frozen screening window;
   - cap-compatible OILEV-V2, still outcome-blind because V11 computed no PnL;
   - exactly one genuinely new family selected outcome-blind from six proposals.

V12 success means correct evidence, not profit. Allowed terminal outcomes:

- `V12_REJECT_ALL`;
- `V12_ONE_OR_MORE_STAGE_A_SURVIVORS_LOCKED_FOR_FUTURE_S1`;
- `V12_BLOCKED_PRELAUNCH`;
- `V12_BLOCKED_DATA_OR_SELECTION`;
- `V12_INCOMPLETE_NOT_PROMOTABLE`.

No outcome in this plan authorizes S1 inspection, paper trading, testnet,
live trading, credentials, orders or leverage.

## 3. Hard boundaries

- Crypto USD-M perpetuals only. Do not mix stocks, forex or TradFi perpetuals.
- V11 files and scored artifacts are append-only evidence.
- S0 and S0R are screening data, not untouched OOS.
- S1 remains sealed and must not be listed, opened, hashed, copied or scored.
- No scored grids, optimizer, parameter search or family substitution.
- No changing a threshold, universe, cost, window, control or book after the
  first V12 scored metric exists.
- Every computed scored base result increments observed exactly once, even if
  publication fails. Exact replay increments neither counter.
- Missing PIT fields, data, hashes or authority are `UNAVAILABLE_FAIL_CLOSED`.
- Raw market data remains gitignored. Commit manifests and hashes, not raw data.
- A1 alone owns integration, central counters, ledgers, freeze and publication.
- A7 audits independently and never repairs audited production code.
- No push, merge to `main`, worktree deletion, history rewrite or data purchase
  without a new explicit owner instruction.
- Existing hard live guards remain unchanged.

## 4. Branches, worktrees and agent topology

### 4.1 Owner-plan bootstrap

The root checkout is owner/bootstrap space. If `PLAN_crypto.md` is the only
owner-created change, A1 is authorized to commit only this file on `main` as
`OWNER_CRYPTO_PLAN_SHA`. Any other dirty path is preserved and reported; it is
not swept into the plan commit.

A1 then creates reconciliation from the pushed V11 terminal:

```text
path:   /Users/hoangminhlong/my-quantitative/.worktrees/crypto/v11r-integration
branch: orca/v11r-integration
base:   origin/orca/v11-integration@df18f53dba30291065f9be157cae04bdcf15bf50
```

Cherry-pick only `OWNER_CRYPTO_PLAN_SHA` into this branch. Do not merge `main`.
After reconciliation closes, V12 starts locally from `V11R_TERMINAL_SHA`:

```text
path:   /Users/hoangminhlong/my-quantitative/.worktrees/crypto/v12/integration
branch: orca/v12-integration
base:   V11R_TERMINAL_SHA
```

Literal placeholders such as `OWNER_CRYPTO_PLAN_SHA` and
`V11R_TERMINAL_SHA` MUST be replaced with measured full 40-character SHAs.

### 4.2 Roles and concurrency

Logical roles:

| Role | Ownership |
|---|---|
| A1 | controller, integration, freezes, counters, publication, terminal report |
| A2 | publication/ledger repairs and migration contract |
| A3 | PIT data, S0R window, manifests and coverage |
| A4 | cap feasibility and OILEV-V2 schedule design |
| A5 | blind proposal lane 1, exactly two proposals |
| A6 | blind proposal lane 2, exactly two proposals |
| A8 | blind proposal lane 3, exactly two proposals |
| A7 | independent novelty, prelaunch and terminal audit |
| A9 | independent feasibility and resource audit |

Maximum simultaneous coding agents: A1 plus three light agents. Full suites run
alone. Heavy workers follow a fresh measured resource cap; cells within one
family are always serial. On the owner's 8 GB Mac, heavy cap is at most one. On
a stronger host A1 may authorize at most three concurrent family chains after
measurement, one cell per family.

No agent may spawn a child agent unless A1 records the delegation first.

### 4.3 Worktree manifest

A1 maintains `research/control/v12_run/worktree_manifest.json` with:

```text
role, task, absolute_path, branch, bootstrap_sha, allowed_globs,
forbidden_globs, expected_artifacts, required_tests, commit_sha,
status, merge_order, model_requested, reasoning_effort_requested,
reasoning_effort_effective_or_unverified
```

Every lane starts from the exact recorded wave SHA, verifies `pwd`, full HEAD,
branch and empty porcelain before writing, returns one focused clean commit and
never merges, rebases, pushes or amends another lane.

## 5. Phase R0/R1 — V11 terminal reconciliation

This phase is metadata-only. It may not modify strategy code, inputs, metrics,
family verdicts, ledgers, selection freeze, reproduction reports or A7 math.

### R0 — intake

A1 records:

- current UTC, refs, ancestry and dirty status;
- V11 terminal SHA and all primary-artifact hashes;
- zero active V11 workers;
- 6 legitimate published V11 cells;
- 125 published / 128 observed logical denominators;
- S1 seal and no deployment activity;
- exact list of stale metadata fields.

Create `research/control/v11_run/v11r_reconciliation_intake.json`.

### R1 — reconcile only stale surfaces

Required corrections:

- `state.json`: terminal phase and terminal verdict only; remove stale
  `P0_IN_PROGRESS`, old reasons saying D3/A7 were unfinished and obsolete next
  actions;
- `heartbeat.json`: remove stale “ILLIQ computing”, archive-wait and old remote
  tip fields; preserve terminal workers=0, 6/9, 125/128 and S1 seal;
- `terminal_report_v11.json`: distinguish audited science SHA, terminal metadata
  SHA and pushed remote SHA without a self-referential hash; mark push complete;
- `research/wayfinder/MAP.md` and `CONTINUE.md`: concise V11 terminal truth and
  next safe action;
- append one reconciliation event; never rewrite prior JSONL rows.

Required regression test:

```text
tests/test_v11_terminal_metadata.py
```

The test must assert agreement across state, heartbeat, terminal report, family
verdicts, reproduction reports and A7 audits. It must fail on stale in-progress
fields, wrong counters, S1-open claims or a reversed performed/not-performed
schema.

### R2 — independent A7 metadata audit

A7 gets a fresh worktree from the reconciliation candidate SHA. A7 may write
only:

```text
research/audits/v11r/a7_terminal_reconciliation.{json,md}
```

A7 independently recomputes hashes and agreement. Required verdict:

```text
V11R_METADATA_RECONCILED
```

Any scientific-byte change, counter mismatch or unresolved stale terminal claim
is FAIL. A1 integrates the audit and freezes `V11R_TERMINAL_SHA`.

Required R gates:

```bash
.venv/bin/python -m pytest tests/test_v11_terminal_metadata.py -q
.venv/bin/python -m pytest tests/test_v11p_a2_publication.py tests/test_protocol_contracts.py tests/test_protocol_metrics.py -q
.venv/bin/python -m compileall research/v11 research/adapter_v10
git diff --check
git status --porcelain
```

## 6. Phase P0 — V12 control plane and accounting authority

A1 creates under `research/control/v12_run/`:

- `run_contract.json`;
- `state.json`;
- `heartbeat.json`;
- append-only `event_log.jsonl`;
- `worktree_manifest.json`;
- `denominator_authority.json`;
- `data_manifest.json` initially pending;
- `lessons_register.json` seeded from L-V11-1 through L-V11-7;
- `forbidden_family_inventory.json`.

Frozen starting accounting:

```text
published denominator start     125
observed denominator start      128
V12 scored-cell budget          0/9
S1                              SEALED_UNTOUCHED
```

The historical global physical ledger may remain unavailable only when
`denominator_authority.json` hashes all tracked terminal summaries, states the
logical totals and forces every statistical consumer to use observed >=128.
Before scoring, create a portable per-sprint V12 ledger package containing its
empty-ledger hash, schema and transfer manifest. Host migration without this
package is a prelaunch FAIL.

The V12 engineering clock is not a reason to rush. A separate 12-hour scoring
clock starts only after A7 prelaunch authorization and data are staged on the
execution host. Start no new cell with less than 120 minutes remaining; with
less than 45 minutes, stop workers safely and close incomplete.

## 7. Phase P1 — factory repairs before proposals

A1 dispatches A2, A3 and A4 concurrently from `V12_BOOTSTRAP_SHA`.

### A2 — publication and ledger hardening

Worktree:

```text
.worktrees/crypto/v12/p1-a2-ledger
orca/v12p-a2-ledger
```

Deliverables:

1. Publication requires `n_positions > 0` and at least one valid decision/fill.
2. Refused computed outputs increment observed once and cannot publish.
3. Exact replay increments neither observed nor published.
4. Per-family cell matrices are derived from the frozen family contract; a
   generic superset cannot silently launch unsupported stress cells.
5. Portable ledger package and cross-host checksum verification.
6. Migration/fault/concurrent-append tests.

Allowed writes: publication/accounting helpers, dedicated tests and
`research/audits/v12p/a2_*`. No family strategy files.

### A3 — PIT data and replication window

Worktree:

```text
.worktrees/crypto/v12/p1-a3-data
orca/v12p-a3-data
```

Deliverables:

1. Inventory existing local bars, funding, OI, mark and instrument metadata.
2. Freeze an ILLIQ replication window that does not overlap the V11 scored
   window `2025-08-22T00:00:00Z` through `2026-08-21T00:00:00Z`.
3. Preferred S0R window is `2024-08-22T00:00:00Z` through
   `2025-08-21T00:00:00Z`, only if every required symbol/bar/funding field meets
   the declared coverage and PIT rules. This is secondary screening, not S1.
4. OILEV-V2 and the blind family may use the existing V11 S0 snapshot only
   because no OILEV PnL was computed and the blind proposal does not yet exist.
5. Create immutable per-file hashes and equal-twin staging manifests.
6. Do not fetch new network data. If the preferred window is incomplete,
   report `V12_ILLIQ_REPLICATION_BLOCKED_DATA`; leave its three slots unused.

Allowed writes: V12 data-contract/load-validation code, tests, manifests and
`research/audits/v12p/a3_*`. Never commit raw data.

### A4 — cap feasibility and meaningful robustness diagnostics

Worktree:

```text
.worktrees/crypto/v12/p1-a4-feasibility
orca/v12p-a4-feasibility
```

Deliverables:

1. Pre-score target-book validator over every decision stamp.
2. Drop-one-symbol chooses the largest realized absolute-weight held symbol,
   with deterministic tie-break; it cannot choose an unheld symbol.
3. OILEV-V2 uses a new fixed identity and a deterministic diversified book:
   rank the eligible universe, take the four lowest and four highest names when
   at least nine are eligible, equal-weight each leg, apply the frozen beta
   hedge, then uniformly scale the entire book when needed so every final
   absolute weight is <=0.30. Never clip and renormalize individual names.
4. Every one of the 52 pre-window stamps must have >=9 eligible names, exactly
   four names per signal leg and cap compliance. One failure blocks OILEV-V2.
5. Schedule-only costs, turnover, holding and funding-event counts; no PnL.

Allowed writes: feasibility helpers, OILEV-V2 schedule/spec draft, tests and
`research/audits/v12p/a4_*`. No scored result code or central freeze.

### P1 integration gate

A1 cherry-picks A2, A3, A4 in that order, running targeted tests after each.
Then run the V11 regression suites, all V12P tests and one full suite alone.
Tests must not mutate tracked artifacts. Freeze `V12P_REPAIR_SHA` only with a
clean tree and zero unresolved HIGH/CRITICAL findings.

## 8. Phase D0 — frozen family inputs and blind packet

Before proposal agents start, A1 freezes:

- `research/proposals/v12/illiq_replication_brief.{json,md}`;
- `research/proposals/v12/oilever_v2_brief.{json,md}`;
- `research/proposals/v12/blind_input_packet.{json,md}`;
- V1–V11 forbidden/rescue inventory;
- data schema, costs, clocks and implementation interfaces;
- current observed denominator 128 and nine-cell maximum.

### 8.1 ILLIQ replication identity

The replication keeps:

- anchor: 28-day daily Amihud, weekly, long illiquid / short liquid,
  BTC-beta-neutral;
- neighbour: 56-day Amihud, otherwise identical;
- control: sign-inverted 28-day book;
- same after-cost, funding, stress and 0.50 fold-concentration gates.

Only the preregistered non-overlapping S0R window and the corrected meaningful
drop-one diagnostic differ. No parameter menu is allowed.

Preregister the explanatory question before scoring: did V11 concentration
arise from a single favorable regime, such that the same sign and robustness do
not replicate in the earlier window? Regime attribution is diagnostic only and
cannot change the verdict.

### 8.2 OILEV-V2 identity

The mechanism remains deleveraging/crowding through PIT OI flow/stock, but the
book is the cap-compatible construction fixed in A4. Arms:

- 28-day OI-flow anchor;
- 56-day OI-stock neighbour;
- sign-inverted 28-day control.

If coverage, PIT staleness, breadth or cap feasibility fails, the family is
`BLOCKED_PRE_SCORE`; its three slots are not reassigned.

### 8.3 Blind input isolation

Blind agents may read only the blind packet, general adapter interfaces,
forbidden inventory, literature sources and data-schema files listed in their
prompts. They may not inspect V11 family metrics, V11 scored artifacts, terminal
reports, proposal outputs from other lanes or S1.

## 9. Phase D1 — six outcome-blind proposals

A1 creates three worktrees from `V12_BLIND_PACKET_SHA`:

```text
.worktrees/crypto/v12/d1-a5-proposals  orca/v12d-a5-proposals
.worktrees/crypto/v12/d1-a6-proposals  orca/v12d-a6-proposals
.worktrees/crypto/v12/d1-a8-proposals  orca/v12d-a8-proposals
```

Each agent proposes exactly two low-turnover mechanisms. Total: six proposals.
Each proposal must include:

- primary-source claim and crypto-perpetual transfer caveats;
- economic counterparty and expected sign;
- PIT fields and availability clock;
- universe, formation, holding and rebalance schedule;
- target book, beta/risk neutralization and expected turnover;
- anchor, justified neighbour and causal negative control;
- fees, slippage, funding and stress treatment;
- falsification condition;
- ancestry map against V1–V11;
- why it is neither LOT inversion nor ILLIQ/OILEV parameter rescue.

Ineligible mechanism classes:

- LOT/MAX/skew inversion or parameter variants;
- Amihud/illiquidity variants reserved for replication;
- OI-deleveraging variants reserved for OILEV-V2;
- aggressor absorption, old funding-carry rescues, ordinary momentum, ordinary
  reversal, volume-shock continuation or a renamed rejected baseline;
- any proposal needing unavailable external data or an account purchase.

Proposal agents compute no returns, PnL, PF, Sharpe or candidate ranking.

## 10. Phase D2/D3 — independent audits and selection freeze

A1 integrates only the six proposal documents, creating
`V12_PROPOSAL_POOL_SHA`, then dispatches A7 and A9 in parallel.

### A7-N — novelty and anti-rescue

A7 maps all proposals to V1–V11, validates sources and counterfactual controls,
rejects hidden rescues and measures prewindow rank similarity when possible.
A7 edits no proposal. Any unresolved HIGH/CRITICAL makes a proposal ineligible.

### A9-F — data and schedule feasibility

A9 independently checks PIT data, coverage, minimum breadth, schedule-only
costs, turnover, holding, adapter compatibility and resource estimates without
computing PnL.

### Selection

A1 selects exactly one blind family using a frozen rubric:

1. no novelty/rescue veto;
2. PIT data PASS;
3. cap/cost/turnover PASS;
4. informative control and falsification rule;
5. lowest implementation risk;
6. strongest source-to-test trace;
7. lexicographically smallest hypothesis ID as final tie-break.

Target frozen set:

```text
ILLIQ replication     3 arms
OILEV-V2              3 arms
one blind family      3 arms
maximum               9 scored base cells
```

An ineligible reserved family keeps unused slots. If no blind proposal is
eligible, do not replace it. Freeze exact arm identity/config digests, data,
windows, folds, universe, costs, funding, controls, stress matrix, gates,
denominator and budget in `research/control/v12_run/selection_freeze.json`.

After the first scored metric, no freeze amendment is permitted.

## 11. Phase I — implementation

Create one worktree per eligible family from `V12_SELECTION_FREEZE_SHA`:

```text
.worktrees/crypto/v12/i-illiq-replication
.worktrees/crypto/v12/i-oilever-v2
.worktrees/crypto/v12/i-blind-family
```

Each implementation lane owns exactly one family module/plugin, its tests,
golden feature vectors and C1-style evidence. It may not edit central
publication, ledgers, freezes or another family.

Required per-family evidence:

- completed-bar/PIT correctness;
- one-event execution lag;
- deterministic feature and target generation;
- no future universe selection;
- native funding while held;
- generic adapter costs/fills only;
- three distinct frozen identities;
- hand-computed causal fixtures;
- schedule-only feasibility;
- exact-arm dummy dry-run;
- double-generation equality;
- clean targeted-test commit.

A1 integrates one family at a time. A centralized wiring commit may register
plugins only after all applicable lanes pass.

## 12. Phase Q — integrated QA and W12 freeze

Before scoring:

1. Run targeted suites for adapter, publication, data and each family.
2. Dry-run every eligible arm into an empty temporary ledger using dummy finite
   metrics: one unique key, one first publication and idempotent replay with
   zero real-counter change.
3. Verify publication refuses zero-position output.
4. Verify drop-one selects a held maximum-weight symbol.
5. Re-run loader-selected coverage, instruments, ticks, funding and terminal
   valuation, not merely file existence.
6. Package and checksum the empty V12 ledger and staging transfer.
7. Run the full suite alone; tree must remain unchanged.
8. Measure RAM/CPU/disk and freeze heavy cap.
9. Freeze final code-bearing `W12`.
10. Create fresh detached execution and reproduction trees at exactly `W12`,
    stage equal-twin read-only data and verify byte-identical manifests.

## 13. Phase A7 — independent prelaunch audit

A fresh A7 lane independently recomputes:

- V11R ancestry and terminal consistency;
- 125/128 denominator authority and portable V12 ledger;
- selection and all arm digests;
- data/window/fold/warmup/purge/PIT rules;
- ILLIQ non-overlap with V11;
- OILEV-V2 52/52 breadth and cap compliance;
- blind-family novelty and absence of outcome access;
- unique/idempotent dummy dry-run;
- nonzero-position publication guard;
- meaningful drop-one behavior;
- schedule-only costs and realised target feasibility;
- code/data/staging/execution-tree pin chain;
- clean tests, resource cap and zero scored V12 artifacts;
- S1 seal and deployment boundaries.

Only this exact verdict authorizes scoring:

```text
V12_S0_LAUNCH_AUTHORIZED
```

Zero unresolved HIGH/CRITICAL is mandatory. The agent executing this plan MUST
stop after integrating prelaunch evidence and before the first scored cell,
unless the owner gives a new explicit `GO V12 SCORED EXECUTION` instruction.

## 14. Phase E — nine-cell maximum, owner GO required

This phase is documented now but is not authorized by the implementation prompt.

Within each eligible family run serially:

1. anchor;
2. neighbour;
3. causal negative control.

Every cell follows:

```text
verify W12/data/spec/arm pins
-> compute schedule and chronological folds
-> next-allowed-event fills
-> costs and native funding
-> base result and frozen stress matrix
-> meaningful drop-one diagnostics
-> canonical artifacts
-> observed +1 exactly once
-> A1 publication exactly once
-> counters and heartbeat checkpoint
```

No pytest runs while a heavy worker is active. No later cell changes after an
earlier result. A technical abort consumes zero budget only when no scored
metric exists and a forensic TECHABORT artifact proves it.

## 15. Stage-A gates and terminal science

Every family must pass all applicable gates:

- after-cost expectancy > 0;
- PF >= 1.10;
- at least 2/3 folds positive;
- no populated fold PF < 0.80;
- largest positive-fold share <= 0.50;
- MDD <= 10%;
- symbol contribution <= 40%;
- sufficient positions/decisions for the family clock;
- meaningful drop-one-symbol survival;
- drop-one-fold survival when frozen as applicable;
- stressed PnL > 0 and stressed PF >= 1.00;
- neighbour supports anchor;
- control supplies incremental mechanism information;
- realised schedule remains inside cost/turnover/cap contract;
- independent reproduction ALL_MATCH;
- zero unresolved HIGH/CRITICAL;
- multiple-testing statement uses observed denominator >=128 plus every V12
  computed result, or remains `UNAVAILABLE_FAIL_CLOSED` with zero credit.

The ILLIQ replication does not pass merely by being positive; it must pass the
same concentration gate that rejected V11. OILEV-V2 does not inherit any merit
from being previously blocked. A blind family receives no discretionary waiver.

Reproduce every computed cell in fresh processes, then run independent A7
terminal audit. A survivor is locked only for a later owner-approved,
non-overlapping S1 plan.

## 16. Mandatory gates and evidence format

Every gate artifact records:

```text
gate_id, measured_utc, producer_role, full_head_sha, command, exit_code,
stdout_path, stderr_path, expected, observed, verdict, blockers,
corrective_action, input_hashes, output_hashes, tree_status
```

Verdicts are only `PASS`, `FAIL`, `NOT_RUN` or `BLOCKED` at the gate level.
Never write PASS from prose or inferred absence.

Minimum test routing:

```bash
.venv/bin/python -m pytest tests/test_v11_terminal_metadata.py -q
.venv/bin/python -m pytest tests/test_v11p_a2_publication.py tests/test_v11p_a3_costgate.py tests/test_v11p_a4_dryrun.py -q
.venv/bin/python -m pytest tests/test_v11i_illiq_amihud_causal.py tests/test_v11i_illiq_amihud_identity.py tests/test_v11i_illiq_amihud_pit.py -q
.venv/bin/python -m pytest tests/test_protocol_contracts.py tests/test_protocol_metrics.py tests/test_protocol_reconciliation.py tests/test_protocol_reproduce.py -q
.venv/bin/python -m pytest tests -q
.venv/bin/python -m compileall research/v11 research/v12 research/adapter_v10
git diff --check
git status --porcelain
```

Commands referencing not-yet-created V12 paths are `NOT_RUN` until the relevant
phase creates them; they may not be reported PASS early.

## 17. Checkpoints

A1 reports to the owner at:

1. measured intake and bootstrap;
2. V11R reconciliation and independent audit;
3. P1 repair commits and data-window authority;
4. six blind proposals received;
5. novelty/feasibility audit and exact three-family dispositions;
6. family implementation and integrated dry-run;
7. W12 pin chain and A7 prelaunch verdict;
8. after each scored cell, only after a later owner GO;
9. reproduction and terminal verdict.

Each report includes full SHA, branch/worktree, clean status, tests, counters,
budget, S1 seal, workers and exact blocker. Detailed logs stay on disk.

## 18. Definition of Done for the implementation prompt

The initial fresh-agent implementation is complete only when:

- V11 stale metadata is reconciled without changing scientific bytes;
- A7 returns `V11R_METADATA_RECONCILED`;
- V12 control plane starts at 125 published / 128 observed and budget 0/9;
- factory lessons L-V11-1 through L-V11-7 have regression tests;
- ILLIQ replication window has PASS authority or an honest data blocker;
- OILEV-V2 passes all-stamp cap feasibility or is blocked pre-score;
- exactly six blind proposals were frozen and independently audited;
- exactly one blind family is selected or the slot closes blocked;
- every eligible family is implemented with three immutable arms;
- integrated dummy dry-run is unique and idempotent;
- `W12` and equal-twin staging are frozen;
- A7 returns `V12_S0_LAUNCH_AUTHORIZED`, or the run closes truthfully blocked;
- budget remains 0/9, denominators remain 125/128, S1 is sealed;
- no paper/testnet/live/order/credential activity occurred;
- all owned workers are zero and the integration tree is clean;
- no push or merge to `main` occurred;
- execution stops before the first V12 scored cell.

## 19. First response required from a fresh A1

Before dispatch or edits beyond the authorized plan-only bootstrap, report:

```text
measured UTC
root path / branch / full HEAD / porcelain
origin/main full SHA
origin/orca/v11-integration full SHA and ancestry
V11 verdict / A7 verdict / reproduction count
published and observed denominators
V11R worktree path / branch / base SHA
active scoring and test workers
RAM / CPU / disk and preliminary heavy cap
owner-plan commit SHA or exact blocker
GO/NO_GO for V11R metadata-only work
```

After this checkpoint A1 continues autonomously through safe local phases and
stops only for a scientific/data/identity blocker, credentials or purchases,
push/main merge/deletion, S1/live boundaries, or immediately before the first
V12 scored cell.
