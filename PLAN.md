# SPRINT V9H → V10 — HARDEN, PRESERVE, THEN DISCOVER

> **Authority at intake:** `main == origin/main == 425843d`.
> V9 is closed as `V9_REJECT_ALL_MULTI_FAMILY`; A7 terminal audit is `PASS`,
> 5/5 frozen trials reproduced `all_match`, active workers = 0. Immutable V9
> execution SHA: `206faf8aac5b3f7136001a45d3e7a3e85cb923e5`.
>
> **Order is mandatory:** V9H repairs and proves the research machine. V10 may
> start only after every V9H gate and an independent A7 audit pass.

## 1. Mission

1. **V9H — evidence/runtime hardening:** preserve all V9 raw evidence; replace
   ambiguous shell monitoring with an auditable controller; repair lifecycle,
   resource, contract and statistical gaps; prove behavior under crash, timeout,
   memory pressure and restart.
2. **V10 — fresh discovery:** select at most ten genuinely new crypto mechanisms
   before new PnL is visible, freeze at most six trials, then walk-forward,
   stress, reproduce, score and honestly retain or reject them.

Rejecting every strategy is a valid scientific outcome. Producing attractive
metrics through leakage, rescue-tuning, missing evidence or ambiguous retries is
not success.

## 2. Non-negotiable facts and scope

- Honest historical multiple-testing denominator after V9: **117 scored trials**.
- No V9 candidate passed the complete Stage-A floor; there is no locked edge.
- `TSTREND-L28` is a research note only. Its ENA dependency may inform future
  falsification design, but its parameters must not be tuned or rescued here.
- Every terminal-rejected family stays on the forbidden-rescue ledger. Renaming,
  changing lookback/threshold/cadence/symbols/caps/direction, or adding a
  post-result filter does not create a new mechanism.
- The present crypto window is inspected **S0 screening**, not untouched OOS.
- Equity stays separate and `PROVIDER_AND_SPEC_BLOCKED`; no equity scored trial.
- No S1 inspection, paper/testnet/live execution, orders, leverage changes,
  credentials, remote push or worktree deletion is authorized.

## 3. Terminal outcomes

V9H must end in exactly one:

- `V9H_PASS_V10_AUTHORIZED`
- `V9H_BLOCKED_V10_NOT_AUTHORIZED`

If V9H passes, V10 ends in exactly one:

- `V10_NO_ELIGIBLE_FAMILY_NOT_RUN`
- `V10_BLOCKED_PRELAUNCH`
- `V10_INCOMPLETE_NOT_PROMOTABLE`
- `V10_REJECT_ALL`
- `V10_STAGE_A_SURVIVOR_LOCKED_FOR_FUTURE_S1`

Forbidden labels: `EDGE_CONFIRMED`, `PRODUCTION_READY`, `PAPER_READY`,
`TESTNET_READY`, `LIVE_READY`.

## 4. Multi-agent execution model

### 4.1 A1 controller/integrator

A1 is the only merge authority and owns the integration worktree, run state,
freeze, launches and closeout. Only A1 may create worktrees, integrate commits,
freeze the code-bearing SHA, launch scored workers and issue a terminal verdict.

### 4.2 Worktrees and roles

Create under `/Users/hoangminhlong/my-quantitative-v10-wt/`. Wave-H branches
start from one clean bootstrap recorded in the run contract. Later-wave branches
start from the clean integration SHA produced by the preceding wave.

| Role | Worktree / branch | Exclusive responsibility |
|---|---|---|
| A1 | `integration-v10` / `orca/v10-integration` | orchestration, merges, freeze, launch, closeout |
| A2 | `a2-evidence` / `orca/v10-a2-evidence` | V9 bundle, hashes, restore verification, retention |
| A3 | `a3-runtime` / `orca/v10-a3-runtime` | PID/PGID controller, heartbeat, timeout, status CLI, governor |
| A4 | `a4-reproduction` / `orca/v10-a4-reproduction` | streaming repro, completion semantics, safe cache |
| A5 | `a5-contracts-stats` / `orca/v10-a5-contracts-stats` | canonical contract, N=117+, returns matrix, DSR/PBO inputs |
| A6 | `a6-data-pit` / `orca/v10-a6-data-pit` | S0/hash/clock/warmup/purge audit; shared data hooks |
| A7 | `a7-independent-audit` / `orca/v10-a7-audit` | V9H, prelaunch, terminal audit; never production code |
| A8 | `a8-hypothesis-1` / `orca/v10-a8-hypothesis-1` | independent proposals; selected family 1 if authorized |
| A9 | `a9-hypothesis-2` / `orca/v10-a9-hypothesis-2` | independent proposals; selected family 2 if authorized |
| A10 | `a10-qa` / `orca/v10-a10-qa` | fault injection, golden vectors, parity/anti-leak tests |
| R1/R2 | detached clean worktrees | frozen execution only; unique result/shard/log roots |

### 4.3 Parallelism

- Worktrees may all exist, but dispatch agents in dependency waves.
- Maximum four light agents active at once, including A1, unless measured
  preflight proves more safe.
- Heavy workers = `min(2, resource_governor_cap)`.
- A family with prior silent death/memory pressure runs sequentially unless
  three consecutive two-worker smoke runs are safe.
- Never run the full test suite concurrently with heavy backtests.
- Agents cannot spawn grandchildren or new worktrees unless A1 records the
  delegation in the manifest.

### 4.4 Ownership and merge contract

`worktree_manifest.json` freezes each role/path/branch/bootstrap, allowed and
forbidden globs, deliverables, tests, commit, clean-tree result, integration
decision and merge SHA.

1. Agents never edit root/main or another agent's worktree.
2. One production file has one owner per wave.
3. Every agent returns a clean narrow commit, SHA, tests and limitations.
4. A1 integrates one commit group at a time and runs targeted tests after each.
5. Conflicts affecting signal time, fills, costs, funding, folds or scoring
   require manual review; never auto-resolve them.
6. After launch SHA `W` is frozen, only allowlisted audit/control artifacts may
   change. Production-code changes invalidate baseline and A7 authorization.

## 5. Phase 0 — preserve V9 evidence first

Approximately 222 MB of ignored V9 trial/reproduction evidence is still in
`exec-v9-r1` and `exec-v9-r2`; root/main does not contain these `results/`
trees. Do not remove either worktree.

A2 must:

1. Inventory each V9 execution worktree: path, HEAD, tree state and result size.
2. Create an immutable content-addressed bundle under ignored
   `research_snapshots/v9_closed_<UTC>/` containing:
   - five official scored trial directories;
   - five reproduction directories and comparison reports;
   - both zero-score `.TECHABORT` archives;
   - baseline, contract, budget, universe/data manifests;
   - A7 prelaunch/terminal evidence, registry shards, logs and control files.
3. Commit an archive manifest with source path, bundle path, role, size and
   SHA-256 for every file, plus a top-level bundle hash and retention policy.
4. Restore to a temporary directory and independently verify every hash, five
   readable gates, five `all_match=true` comparisons, launch/baseline/
   attestation pins and zero metrics in both technical archives.
5. Create a local preservation ref at `425843d`.

No V9 worktree cleanup is part of this sprint. Cleanup needs separate owner
authorization after A7 confirms the archive restore.

## 6. V9H — harden the research machine

V9H publishes no strategy PnL and consumes no trial budget. Synthetic fixtures
and explicitly unscored resource probes are allowed.

### H01 — authoritative worker controller

Create one Python controller/status CLI. Each worker record contains trial ID,
PID, PGID, process-start identity, command hash, launch SHA, worktree, output,
phase, timestamps, exit code/signal, peak RSS if available, terminal state and
artifact verification.

Phases: `PREPARE`, `BASE`, `STRESS`, `FINALIZE`, `REPRODUCE`.

`pgrep -f`, `pkill -f` and broad name matching are forbidden in new controller
and command templates. Resume must match PID + start identity + command hash +
worktree; PID alone is insufficient.

### H02 — atomic heartbeat and completion truth

Heartbeat/worker/terminal JSON uses temporary file + atomic replace and updates
at most every 15 seconds even when the engine is quiet.

Terminal states are only:

- `COMPLETED`
- `FAILED_INCOMPLETE`
- `TIMED_OUT`
- `SIGNALLED`
- `CONTROLLER_LOST`
- `UNKNOWN_EXTERNAL_KILL`
- `PARTIAL_PRE_SCORE`

Do not call unexplained SIGKILL “OOM”; record memory pressure as an evidence-
backed inference. Completion requires exit 0, valid artifact hashes, readable
gate and registry terminal row; reproduction additionally requires both
`comparison.json` and `reproduction_report.json`.

Clarify base-only timestamps: base execution ending is not pipeline completion.

### H03 — timeout and retry contract

- Non-null timeouts are frozen for scored worker, outer harness and rerun worker.
- Spawn a dedicated process group.
- Timeout: SIGTERM exact group, wait 30 seconds, then SIGKILL exact group, reap
  children and record evidence.
- At most one technical retry per frozen trial, only when archive proves zero
  scored metrics.
- A crash after publishing a score consumes budget.
- A failed retry becomes `TECHNICALLY_BLOCKED`; no substitute trial/lookback.

### H04 — streaming logs

Real reproduction must not retain hour-long nested stdout/stderr with
`capture_output=True`. Stream timestamped phase-aware logs, update
`last_log_at_utc`, rotate/bound large logs and retain only a tail in terminal
reports. Progress must be observable before completion.

### H05 — enforced resource governor

Freeze from unscored measurements:

```text
effective_heavy_workers = min(
    contract_cap,
    floor((available_ram - reserved_ram) / measured_peak_worker_ram)
)
```

Reserve at least 2 GB for macOS/Orca. The controller rejects worker `N+1`.
Cap=2 requires three consecutive safe two-worker probes; otherwise cap=1.
Concurrency may be reduced for safety, never changed after viewing PnL.

### H06 — safe performance work

Preferred flow:

```text
prepare immutable raw inputs
→ build deterministic signal schedule
→ base run
→ process-local reuse for frozen stress variants
```

Cache keys include data/catalog hash, symbols, window, bar type, funding and
signal inputs. Reproduction is a fresh process with a fresh cache; never reuse
scored results/orders/positions/metrics.

Merge a cache only if cache on/off artifacts are byte-identical, reproduction
stays all-match and full stress reads raw bars no more than twice. Target ≥30%
wall-time reduction. If parity is uncertain, reject cache and use cap=1.

### H07 — scientific-contract/statistics repair

Make one machine-readable authority for warmup/OOS, bar/fill clock, purge,
embargo, costs, slippage, funding, required `direction`, fold/symbol caps,
drop-one/stress, PF definition and frozen trial/family/role allowlist.

Runner must reject an archived or unfrozen family even if code supports it.
Update denominator automatically from 117 as valid V10 cells finish. Produce
deterministic return matrices/Sharpe inputs. If DSR/PBO is impossible, report
`UNAVAILABLE_FAIL_CLOSED`; award no inferred statistical points.

### H08 — adversarial test matrix

A10 covers at least:

1. complete exit 0 → `COMPLETED`;
2. exit 0 with missing artifact → `FAILED_INCOMPLETE`;
3. exception records exit and stderr tail;
4. signals never become completed;
5. timeout kills only exact group and leaves no orphan;
6. restart recognizes exact worker and rejects reused PID;
7. simultaneous trials never cross-match;
8. stale heartbeat warns without inventing death;
9. interrupted atomic write stays parseable;
10. death after base/before stress → `PARTIAL_PRE_SCORE`;
11. production timeout is never null;
12. log is readable while worker is alive;
13. over-cap worker is rejected;
14. governor lowers cap when RAM is insufficient;
15. cache on/off byte parity;
16. reproduction cache is process-local;
17. full stress loads raw bars at most twice;
18. full-surface reproduction stays all-match;
19. VOLSHOCK real-path golden is deterministic across two roots;
20. budget allowlist blocks archived/unfrozen family.

### V9H gates H01–H14

All must pass:

1. V9 authority commits are ancestors of clean bootstrap.
2. V9 archive and restore verification pass.
3. No V9 worker is active.
4. Atomic controller/status tests pass; no new broad process monitor.
5. Timeout/orphan tests pass ten consecutive rounds.
6. Heartbeat and terminal truth are unambiguous/current.
7. Every subprocess layer has a non-null frozen timeout.
8. Resource governor is enforced and heavy cap frozen honestly.
9. Streaming logs are visible during execution.
10. Any enabled cache has byte and independent-reproduction parity.
11. Denominator=117; direction/funding-sign/return-matrix contracts pass.
12. TS-TREND and VOLSHOCK golden paths are byte-identical across two roots.
13. Targeted tests and full suite pass on a clean integrated tree.
14. A7 hardening audit PASS, zero unresolved HIGH/CRITICAL.

One failure closes `V9H_BLOCKED_V10_NOT_AUTHORIZED`; no scored backtest.

## 7. V10 proposal firewall and selection

Only after V9H authorization may A8/A9 independently propose at most three
mechanisms each. They may use economic reasoning/primary literature, but not old
numeric PnL to calibrate parameters or design a rescue.

Every proposal specifies economic source/counterparty, PIT inputs, causal sign,
signal/fill clocks, horizon, portfolio construction, success/failure regimes,
falsification, negative control, nearest historical families, structural delta,
sample feasibility, audit cost, and a fixed anchor + theoretically justified
neighbor. No valid proposal is an acceptable outcome.

### 7.1 Rescue firewall

Archive proposals whose novelty is only lookback/threshold/cadence/horizon,
universe/symbol, cap/overlay, direction, data span, name or post-result filter.

A proposal must be materially novel in at least four dimensions:

1. economic source;
2. observable/signal construction;
3. selection/payoff geometry;
4. counterparty and falsifiable regime prediction.

If needed, run preregistered non-PnL diagnostics only: rank/position correlation,
trade Jaccard, exposure overlap and nearest-family mapping. Freeze thresholds
before calculation. High overlap or missing proof defaults to
`ARCHIVE_NOT_RUN_RESCUE_RISK`.

### 7.2 Pre-score rubric

| Component | Points |
|---|---:|
| Novelty/independence | 35 |
| Mechanism/falsifiability | 25 |
| PIT/data readiness | 15 |
| Negative-control quality | 10 |
| Sample feasibility | 10 |
| Implementation/auditability | 5 |

Select at most two families with no hard fail, total ≥75, novelty ≥28, no data
blocker and A7 no-rescue concurrence. Ties use frozen hypothesis-ID order. If
none pass, close `V10_NO_ELIGIBLE_FAMILY_NOT_RUN` with zero budget.

## 8. V10 implementation and trial budget

Do not implement strategy modules before selection is frozen. Per selected
family: exactly two candidates (anchor + preregistered neighbor), one negative
control, complete specs, isolated module where possible, golden/PIT tests.

Global cap: **six scored trials**. One family freezes exactly 3; two freeze 6.
Unused slots cannot be filled after any metric is seen. Forbidden: grids, extra
lookbacks, replacements, universe changes, post-result filters, performance
retries and ledger deletion.

## 9. Dispatch and merge order

### Wave H1

- A2 evidence archive; A3 runtime; A4 reproduction; A1 integration scaffolding.
- Merge A2 → A3 → A4, targeted tests after each.

### Wave H2

- A5 contracts/statistics; A6 data/PIT; A10 QA against integrated H1; A1 merge.
- Merge A5 → A6 → A10, then full suite, golden twice, resource/fault probes.
- Dispatch A7 V9H audit only after the integration tree is clean.

### Wave N

- A8/A9 proposals independently; A5 novelty matrix; A7 rescue challenge; A1
  freezes selected/archived inventory and exact budget.

### Wave I

- A8/A9 selected isolated modules; A6 shared hooks; A5 statistics/finalizer;
  A10 golden/adversarial tests.
- Merge isolated modules → shared hooks → statistics → tests → full suite.

### Freeze/launch

1. Freeze final code SHA `W`.
2. Freeze data/universe/spec hashes, trial IDs, commands and budget.
3. Freeze contract, baseline and execution manifest.
4. Create clean detached R1/R2 exactly at `W`; verify identical environment and
   hashes.
5. A7 independent prelaunch audit.
6. Only `V10_LAUNCH_AUTHORIZED` permits scored execution.

Then launch at governor cap with unique outputs; stress every cell; reproduce
every cell from a clean worktree; build multiple-testing/family summaries;
perform A7 terminal audit; A1 closes.

## 10. Prelaunch gates G01–G20

All machine-readable and PASS:

1. V9 closure/A7 ancestry; 2. V9 archive restore; 3. V9H+A7 authorization;
4. clean tree/no worker; 5. universe/window/hash freeze; 6. PIT coverage;
7. ledger N=117; 8. proposal firewall; 9. novelty; 10. no rescue;
11. families≤2; 12. exact budget 3 or 6/no placeholders; 13. complete specs;
14. lookahead/warmup/purge tests; 15. cost/funding/direction/accounting tests;
16. golden twice; 17. governor/timeouts/retry freeze; 18. all provenance pins;
19. clean detached R1/R2 at `W`; 20. A7 PASS, zero HIGH/CRITICAL.

Any failure means no scored launch.

## 11. Scientific execution contract

- At least three chronological folds; warmup outside scored OOS.
- Purge/embargo ≥ holding horizon.
- Completed-bar features and next-allowed-event fills.
- Baseline 5 bp taker + one adverse tick + native funding unless stricter values
  were frozen before score.
- Stress every cell: fee/slippage ×1.5, +2 ticks, +1 event delay,
  drop-one-symbol and drop-one-fold.
- Flat hard benchmark; buy-and-hold and BTC-beta-neutral context.
- Shared-capital replay if multiple candidates survive.
- Engine, finalizer, scorecard and auditor read the same gate contract.

## 12. Stage-A gates and score

`STAGE_A_PASS_EXPLORATORY` requires all:

- after-cost expectancy >0; PF ≥1.10;
- ≥2/3 folds positive; no populated fold PF <0.80;
- fold positive-PnL contribution ≤50%; MDD ≤10%;
- symbol positive-PnL/risk contribution ≤40%;
- frozen trade/sample floor passes;
- no drop-one-symbol/fold dependency;
- cost/delay stress remains PnL positive and PF ≥1.00;
- preregistered neighbor supports the anchor;
- negative control does not invalidate the causal sign;
- reproduction all-match;
- multiple-testing evidence valid or honest fail-closed with zero credit;
- zero unresolved HIGH/CRITICAL.

Hard-gate failure is always `REJECTED`. The scorecard only ranks full hard-gate
passers: validity 20, after-cost return 20, fold/regime stability 20,
stress/concentration 25, statistical evidence 15. A score cannot rescue failure;
controls are never promotable.

## 13. S0 → future S1

No passer: close `V10_REJECT_ALL`, archive families and do not tune/rerun them.

Passer: immediately freeze code/parameters/universe/costs/lock timestamp and
label at most `LOCK_FOR_FUTURE_S1`. Define S1 strictly after lock without overlap
but do not inspect it in V10. A separate Stage-B plan must apply Wayfinder's
future-OOS, PF≥1.15, MDD≤10%, stability, shared-capital and stress requirements;
even Stage-B success still needs 6–8 weeks signal-only observation.

## 14. Fail-safe

A1 freezes exact UTC deadline. Do not skip gates to fit time.

- <300 minutes: no new family/implementation wave.
- <120 minutes: no new scored wave.
- <45 minutes: stop exact owned workers, reconcile and close honestly.
- Missing reproduction/A7 terminal audit → `V10_INCOMPLETE_NOT_PROMOTABLE`.
- Unattended runs never wait for interactive input.
- No remote push or destructive cleanup without owner approval.

## 15. Definition of Done

- V9 archive manifest/bundle hash/restore report.
- V9H worktree manifest, controller/resource/test reports and A7 PASS.
- Ledger 117 + exact V10 consumption.
- Proposal inventory and selected/archive novelty decisions.
- Frozen specs/budget/contract/baseline/preflight.
- Exact scored/stress/reproduction artifacts for frozen inventory only.
- Return matrix and DSR/PBO or honest fail-closed artifact.
- Family summary, challenge memo, A7 terminal audit.
- Master report `.md` + `.json`.
- `PLAN.md`, `CONTINUE.md`, Wayfinder map synchronized.
- Clean integration tree, active workers=0, one terminal verdict.

## 16. Mandatory A1 reports

A1 reports at: intake; V9 archive restore; V9H tests/resource cap/A7 verdict;
proposal selection; prelaunch pins/commands; each execution wave; terminal
budget/metrics/repro/audit/PIDs/tree/artifacts/next action.

A1 continues autonomously through safe steps and stops only for a real gate
failure, destructive cleanup, credential, remote push, S1, paper/live or order.
