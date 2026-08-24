# PLAN.md — V5 Recovery and Scientific Closure for a Fresh Agent

> **Repository:** `/Users/hoangminhlong/my-quantitative`
> **Effective date:** 2026-08-24
> **Team:** six persistent agents coordinated by A1, plus up to two ephemeral
> frozen-run workers; old worktrees remain read-only
> **Scope:** close legacy V5 truthfully, recover through a clean V5R lineage when
> necessary, then execute one bounded V6 family only after a valid transition
> **Environment:** research/Testnet/Demo only; live-money trading remains disabled
> **Timebox:** target 24 wall-clock hours using parallel work; evidence gates,
> not the clock, decide whether the team may advance

---

## 0. Mission for the new agent

Your first job is not to find a profitable strategy. First determine whether
the research machine is scientifically trustworthy, preserve all existing
evidence, repair preventable engineering defects, and publish one unambiguous
V5 or V5R transition verdict. Only then may the team execute the bounded V6
funding-carry research family defined later in this plan.

Work as a fresh investigator. Do not inherit claims merely because an older
agent wrote them in `CONTINUE.md`, a report, a commit message, or a terminal
log. Recompute every completion claim from current code and current artifacts.

The only valid final outcomes are:

```text
V5_PASS_V6_AUTHORIZED
V5_FAIL_V5R_PASS_V6_AUTHORIZED_CLEAN_LINEAGE
V5_FAIL_V6_BLOCKED
V5R_INDEPENDENT_AUDIT_BLOCKED
V6_PIPELINE_FAIL
V6_CANDIDATE_FAIL
V6_CANDIDATE_INCONCLUSIVE
V6_LOCK_ONE_FOR_FUTURE_S1
```

`PARTIAL`, “mostly pass”, and “continue anyway” are not transition outcomes.

### 0.1. Orca topology: six core agents plus bounded run workers

| Agent | Primary ownership | Parallel work | Forbidden role conflict |
|---|---|---|---|
| **A1 — coordinator/integrator** | master snapshot, contracts, merge queue, trial ledger, transitions, final report | unblock A2–A5; serialize shared-state integration | may not self-sign independent audit |
| **A2 — provenance/recovery** | test isolation, exact-byte search, immutable baselines, quarantine | root-cause and prevention work | may not redefine a baseline after drift |
| **A3 — data/PIT** | bar/funding/metadata coverage, settlement cadence, universe/benchmark contract | V5R data proof and V6 funding panel | may not inspect results then change universe |
| **A4 — execution/accounting** | engine, canonical PnL, terminal handling, costs, exposure controller | V5R engineering and V6 adapter | may not set score thresholds after results |
| **A5 — metrics/reproduction** | hashes/finalization, reconciliation, gates, DSR/PBO, rerun tooling | artifact audit and independent-process reproduction | may not change locked hypothesis/spec |
| **A6 — independent scientific auditor** | adversarial protocol, sampling, challenge memos, final attestation | read-only baseline review and post-freeze audit | may not implement or repair code/scored artifacts |
| **R1/R2 — ephemeral run workers** | execute exact frozen commands into isolated roots | diagnostic, stress, or scored runs after launch authorization | no code/spec edits, no shared-registry writes, no verdict |

All six core agents may work concurrently, but not on the same owned file. A1
owns the integration queue and resolves overlaps. A6's independence is more
important than keeping A6 busy with implementation. R1/R2 exist only while a
frozen run queue exists and terminate after returning artifacts plus checksums.
Orca may spawn more agents, but an additional persistent coding agent requires
a new non-overlapping ownership row. Otherwise use extra capacity only for
ephemeral frozen-run or read-only verification workers.

### 0.2. Worktree and branch policy for the new team

1. The old `my-quantitative-wt` locations remain read-only forever in this run.
2. During Wave 1, A2–A6 perform read-only work against the current checkout.
3. After A1 validates and commits the bootstrap/test-isolation state, A1 may
   create **new**, uniquely named worktrees from that exact commit for A2–A6.
4. Each agent receives an explicit file allowlist and one branch. Never reuse an
   old agent branch or worktree.
5. Shared result writers use per-agent/per-run output roots and registry shards.
   A1 merges/reconciles shards after jobs finish; concurrent processes must not
   append to the same JSONL/index file.
6. Start with at most two CPU-heavy backtests concurrently through R1/R2. Add
   further ephemeral runners only after
   a measured CPU/RAM/I/O preflight shows no swapping, OOM risk, or throughput
   regression. Parallel agents do not imply unlimited concurrent runners.
7. Every handoff includes commit SHA, changed paths, tests, artifact hashes,
   known limitations, and conflict list.

### 0.3. Parallel 24-hour critical path

```text
H00–H01  Wave 1: A1 snapshot; A2 patch review; A3 data audit; A4 engine audit;
                    A5 artifact audit; A6 independent audit protocol
H01–H03  Wave 2: A2 test isolation/C02 search; A3 PIT proof; A4 accounting fixes;
                    A5 hash/reconciliation fixes; A6 independent recheck
H03      Sync gate: choose exact-recovery path or clean-lineage V5R path
H03–H06  Wave 3: A2 baseline/quarantine; A3 data; A4 engine; A5 gates;
                    A6 adversarial fixtures and sample freeze
H06–H10  Wave 4: R1/R2 diagnostics in isolated roots; A6 frozen sampling
H10–H12  Wave 5: A5 reproductions; A6 independent audit; A1 transition
H12      Hard gate: V6 authorized or terminal stop
H12–H15  Wave 6: V6 spec/data/metrics lock, then implementation
H15–H19  Wave 7: exactly four V6 experiments with controlled compute concurrency
H19–H22  Wave 8: stresses, selection adjustment, reproduction, independent audit
H22–H24  Wave 9: final score, verdict, artifacts, handoff
```

The schedule is a coordination target, not permission to skip evidence. If a
hard gate is not complete, dependent work stops even when a later time block
has begun.

### 0.4. Initial Orca dispatch briefs

A1 launches A2–A6 at the start of Wave 1 with these bounded briefs:

```text
A2: Read PLAN §§1–7 and 12. Own only provenance/test-isolation/quarantine
    paths. Prove the contamination cause safely, search for exact bytes, and
    return evidence plus a scoped patch. Do not touch old artifacts/worktrees.

A3: Read PLAN §§3, 8, 12, 14–15. Own data/PIT/funding coverage and contracts.
    Verify actual settlement/publication timing and S0 boundaries. Do not code
    signal or change the universe after results.

A4: Read PLAN §§3, 8–9, 12, 14–15. Own execution/accounting/risk paths. Repair
    canonical identities, terminal/WFA/cost/exposure behavior with fixtures.
    Implement V6 signal only after A1 sends the locked transition/spec hash.

A5: Read PLAN §§8–15. Own metrics/hash finalization/reconciliation/gates and
    reproduction tooling. Remove constant evidence and prove negative fixtures.
    Do not alter locked strategy or data contracts.

A6: Read the entire PLAN as independent auditor. Stay read-only except your
    audit protocol, challenge memos, and attestations. Independently recompute
    baseline/transition claims and reject role conflicts or selected evidence.
```

Each agent first returns `SCOPE_ACK`, owned file list, read-only observations,
and conflicts. A1 resolves ownership before authorizing edits. R1/R2 receive
only an exact command, input hashes, output root, registry shard, resource cap,
and expected artifact contract.

---

## 1. Current verified starting state

This snapshot is a starting hypothesis. The new agent must verify it before
making changes.

### 1.1. Git and tests

```text
branch                         main
HEAD                           3e1d2d0
origin/main                    f4288e7
last full test evidence        557 passed, 16 warnings, 0 failed/xfailed
test command                   .venv/bin/python -m pytest tests/ -q
```

Current uncommitted state:

```text
M  research/matrix_runner.py
M  tests/test_matrix_runner.py
?? my-quantitative-wt/
?? research/audits/v5/final_tests_v5.json
?? research/audits/v5/source_hash_recheck_v5.json
```

The two modified Python files form a defensive patch: tests now redirect
`stage_a_root` into `tmp_path`, preventing test runs from rewriting immutable
V3 provenance artifacts. This patch is not trusted until reviewed and tested.

### 1.2. Worktrees

There are two worktree-looking locations:

```text
/Users/hoangminhlong/my-quantitative-wt/       registered Git worktrees
```

This location belong to previous agents and are **READ-ONLY evidence** for
this sprint. Never delete, prune, clean, reset, commit inside, or modify them.

Most historical branches are already ancestors of `main`. These four were not
merged at the time of this snapshot:

```text
wt/data-pipeline
wt/ops-reporting
wt/quality-safety
wt/research-analysis
```

Their existence is not permission to merge them. Inventory their commits and
diffs; cherry-pick only if a separately documented requirement in this plan
cannot be met by current `main`, the patch is still applicable, and tests prove
it. Never merge task-brief commits or a whole branch blindly.

### 1.3. Existing V5 evidence

Already present:

```text
research/audits/v5/baseline_v5.json
research/audits/v5/v3_v4_findings.json
research/audits/v5/v3_v4_source_hashes.json
research/audits/v5/global_trial_ledger.json
research/audits/v5/final_tests_v5.json                 untracked
research/audits/v5/source_hash_recheck_v5.json         untracked

results/diagnostic_v5/<four DIAG-V5 experiments>/
results/matrix/v4_recalc_diagnostic_v5/
```

Missing or not yet valid:

```text
results/reproduction_v5/                               missing
research/audits/v5/challenge_memo_v5.md                missing
research/audits/v5/scientific_audit_v5.json            missing
results/matrix/v4_recalc_diagnostic_v5/v5_transition.json  missing
```

### 1.4. Known blocking evidence

The current source-hash recheck compares 1,474 paths and reports seven changes:

- one expected append-only registry change;
- six unexpected changes under immutable V3 experiments
`EXP-20260824-0001` and `EXP-20260824-0002`;
- the changed files are `execution_evidence.json`, `frozen/candidate.yaml`, and
`launch_manifest.yaml` in each experiment.

The suspected cause is a test fixture that wrote into the real
`results/stage_a_v3` default directory. This cause must be proven from code and
tests; it does not restore the original bytes.

Additional current defects:

- all four diagnostic experiments have `run.log` mismatching
`artifact_hashes.json`;
- matrix reconciliation is `PARTIAL` with `stage_a_dirs<indexed`;
- reconciliation counts eight registry entries for four indexed cells;
- current diagnostics did not execute the newly committed delay/drop-one
stresses, so code existence is not evidence of V5-C14/C15;
- four independent reproductions are absent;
- an independent scientific audit is absent.

Therefore the starting status is:

```text
V5_STATUS = NOT_CLOSED
V6_STATUS = NOT_AUTHORIZED
S1_STATUS = NOT_STARTED
LIVE_MONEY_STATUS = UNCHANGED_DISABLED
```

---

## 2. Authority and evidence order

When sources disagree, use this order:

1. current executable code plus machine-verifiable artifacts;
2. this `PLAN.md`;
3. frozen specifications and manifests created before a run;
4. Git history and scoped diffs;
5. `CONTINUE.md`, old sprint reports, NOTES, and agent messages.

`CONTINUE.md` is historical handoff context, not current truth. It contains
stale instructions, including an already-committed CLI patch, an older test
count, and work that later code completed. Do not execute its commands without
revalidating them against this plan.

Claims must be backed by file paths, hashes, exact commands, exit codes, and
machine-readable results. A boolean written by the same component being tested
is not independent evidence.

---

## 3. Non-negotiable safety and scientific rules

1. Use `.venv/bin/python`; do not use system `python`.
2. Never read, capture, score, or tune on S1 in this sprint.
3. Never send a live order or enable live-money paths.
4. Do not rerun or retune V4 to rescue its rejected candidates.
5. V4 recalculation may only be labeled `DIAGNOSTIC_RECALC` and must retain a
 link to the source trial.
6. Never overwrite V1–V4 or existing V5 artifacts. Use a fresh immutable run ID.
7. Never replace the original source-hash baseline after observing drift.
8. A regenerated file is not an exact restoration unless its SHA-256 equals the
 frozen expected SHA-256.
9. Never use `git add -A`; stage an explicit allowlist of reviewed files.
10. Never use `git reset --hard`, `git clean`, destructive `rm`, `pkill`,
  `git worktree remove`, or `git worktree prune` in this sprint.
11. Preserve every pre-existing dirty file and untracked artifact.
12. Do not push, open a PR, or alter remote state unless the owner explicitly
  asks for it.
13. The implementer cannot sign their own independent scientific audit.
14. Missing evidence is `NOT_TESTED`, `MISSING`, or `BLOCKED`; never translate
  it into PASS.
15. No hard gate may be waived by a high score or positive PnL.

---

## 4. Definition of done

This sprint is complete only when all of the following are true:

1. the initial dirty state and both worktree locations are inventoried;
2. the test-contamination cause is reproduced safely in a temporary directory;
3. the defensive test patch is reviewed, regression-tested, and recorded;
4. V5-C02 is decided using the original baseline, without redefining it;
5. current diagnostic/matrix/hash/reproduction status is recomputed;
6. if execution reaches Phase F, A6 either signs PASS/FAIL
 or the lack of auditor is explicitly recorded as a blocker; if an earlier
 hard gate fails, the audit is recorded as `NOT_RUN_DUE_PRIOR_GATE_FAIL`;
7. `v5_legacy_transition.json` contains all 26 legacy gates and, when needed,
   `v5r_transition.json` contains every clean-lineage gate;
8. a human-readable recovery report explains exactly what can and cannot be
 trusted;
9. V6 starts only through either `V5_PASS_V6_AUTHORIZED` or
   `V5_FAIL_V5R_PASS_V6_AUTHORIZED_CLEAN_LINEAGE`;
10. if V6 is authorized, exactly one pre-registered family and four experiments
    run, then A6 signs or blocks the final verdict;
11. the final report records engineering, scientific, family, S1, and live-money
    status without implying a candidate exists when none passed.

Success does not require a profitable candidate. A truthful blocked transition
or `V6_CANDIDATE_FAIL` is still a successful execution of the scientific plan.

---

## 5. Phase A — Read-only intake and forensic snapshot (Wave 1, H0–H1)

### A1. Capture state before edits

Record in `research/audits/v5r/intake_snapshot.json`:

- UTC timestamp;
- current branch, HEAD, `origin/main`, and ahead/behind status;
- `git status --short`;
- SHA-256 of every pre-existing dirty/untracked file in scope;
- Python, pytest, pandas, numpy, and NautilusTrader versions;
- worktree path, branch, HEAD, dirty count, and unmerged commits;
- current V5 artifact inventory and file counts.

Do not include secrets or `.env` content.

### A2. Review, do not overwrite, current dirty changes

Inspect the exact diff of:

```text
research/matrix_runner.py
tests/test_matrix_runner.py
```

Confirm the late-bound `stage_a_root` behavior is required for monkeypatching
the default in tests. Confirm every matrix-runner test writes only below
`tmp_path`. Add a regression assertion that the real immutable root's mtimes and
hashes do not change during the relevant tests.

### A3. Re-run baseline tests

Run:

```bash
.venv/bin/python -m pytest tests/ -q
```

Capture start/end time, exit code, full summary, warnings count, failures, and
xfailed count. The gate requires exit code 0, zero failures, and zero xfails.
Do not hard-code an expected test count; report the measured count.

### A4. Inventory old unmerged branches

Create `research/audits/v5r/worktree_inventory.json`. For each old worktree,
record commits and changed paths relative to `main`. Classify each as:

```text
ALREADY_SUPERSEDED
POTENTIALLY_RELEVANT_REVIEW_REQUIRED
OUT_OF_SCOPE
```

This phase is read-only. No merge/cherry-pick occurs here.

---

## 6. Phase B — Prove and prevent test contamination (Wave 2, H1–H3)

### B1. Reproduction proof

Use only a temporary test directory and copied/synthetic fixtures. Demonstrate:

1. why the old default argument could bind the real V3 path;
2. why monkeypatching only the module constant was insufficient;
3. why late-binding `stage_a_root=None` plus the autouse fixture redirects all
 writes into `tmp_path`;
4. that the regression test fails against the vulnerable behavior and passes
 against the patch.

Do not deliberately modify the actual V3 directory to reproduce the bug.

### B2. Immutability regression

Before and after the focused test set, hash the immutable V3/V4 source set using
the existing baseline path list. A test run must produce zero new differences.

Write:

```text
research/audits/v5r/test_contamination_root_cause.md
research/audits/v5r/test_isolation_check.json
```

### B3. Scoped integration

If the patch and tests pass, it may be committed as one scoped preventive fix.
Stage only the reviewed source/test files and supporting audit evidence. Do not
stage `my-quantitative-wt/`, shared datasets, old results, or unrelated changes.

This commit prevents recurrence; it does not repair V5-C02.

---

## 7. Phase C — Decide V5-C02 without laundering evidence (Wave 2, H1–H3)

### C1. Recompute from the original baseline

Recheck all 1,474 paths in:

```text
research/audits/v5/v3_v4_source_hashes.json
```

Classify every difference as:

```text
EXPECTED_APPEND_ONLY
UNEXPECTED_MUTATION
MISSING
RESTORED_BYTE_IDENTICAL
```

The registry may differ only according to its predeclared append-only contract.
Do not exempt provenance files merely because the mutation came from a test.

### C2. One bounded exact-recovery search

Search read-only sources for the six original byte sequences:

- Git objects and tracked history;
- both old-worktree locations;
- existing immutable archives or backups already available locally;
- artifact stores already configured in the repository, if access is read-only.

An acceptable recovery file must:

1. be traceable to a source that predates the mutation;
2. match the expected SHA-256 exactly;
3. preserve the original path and metadata contract;
4. be restored with before/after evidence and no other artifact changes.

Do not reconstruct values by guessing, rewrite the frozen baseline, or bless the
new bytes as original.

### C3. Mandatory decision fork

```text
if all six files are restored byte-identically and the full source recheck passes:
    continue to Phase D
else:
    V5-C02 = FAIL
    close legacy V5 as V5_FAIL
    continue to the clean-lineage V5R protocol in Section 12
```

If V5-C02 fails, the original V5 lineage can never authorize V6 and must remain
permanently recorded as failed. This plan now has owner authorization to create
the explicitly separated V5R clean lineage in Section 12. V5R must quarantine
the compromised evidence and earn its own gates; it must never relabel legacy
V5 as PASS.

---

## 8. Phase D — Repair evidence finalization (Wave 3, H3–H6)

Run this implementation once for either the exact-recovery path or the V5R
clean-lineage path. It may start after the H3 decision and must write only to
the selected new namespace.

### D1. Artifact finalization contract

Fix and test the writer lifecycle so:

1. all data files and `run.log` are closed first;
2. no hashed file is modified afterward;
3. `artifact_hashes.json` is written last;
4. the hash manifest is verified by a separate reader/process;
5. registry/index updates outside the experiment directory are reconciled
 separately;
6. a second finalization attempt fails closed instead of silently changing an
 immutable artifact.

Required tests must detect a post-hash append to `run.log`.

### D2. Matrix reconciliation contract

Correct the mismatch between diagnostic output roots, indexed cell directories,
and registry records. The reconciler must validate:

```text
declared cells == indexed cells == completed cell files
one intended experiment identity per cell
all referenced experiment directories exist
all required artifacts exist
registry records are unique under the declared identity rule
report is derived from the final index, not last-batch counters
```

Do not mark `stage_a_dirs<indexed` as harmless. Either point the reconciler to
the correct diagnostic root or change the schema to represent that root
explicitly and test it.

### D3. Measured gates only

Audit XG1 and XG2 code paths. Remove any remaining prebuilt `True` or synthetic
integrity object that can make a scored gate pass without reading real evidence.
Use negative fixtures to prove each gate fails when its underlying evidence is
tampered with.

---

## 9. Phase E — Fresh immutable diagnostic run (Wave 4, H6–H10)

Run only after Phase D and either legacy V5-C02 or the V5R pre-run baseline gate
pass. Do not overwrite the existing `-DIAG-V5` directories. Use a new namespace:

```text
results/diagnostic_v5r/<fresh_experiment_id>/
results/matrix/v4_recalc_diagnostic_v5r/
```

Run exactly the three frozen V4 momentum specs and one reverse control. Each run
must be a separate process and must be labeled:

```text
registry_kind = DIAGNOSTIC_RECALC
source_trial_experiment_id = <original V4 trial>
trial_count_increment = false
```

Requirements for all four runs:

- frozen inputs/spec identity captured before launch;
- no post-hoc parameter edits;
- no risk-mode change used to rescue V4;
- canonical accounting identity reconciles at fold and experiment levels;
- actual funding settlements and cashflows persist;
- commission, slippage, rejection, and terminal-close effects persist;
- continuous-capital or mathematically chained WFA is used;
- fee ×1.5, adverse two-tick, and extra 15m delay stresses execute;
- drop-one-symbol and drop-one-fold diagnostics execute;
- XG0–XG5 reasons distinguish PASS, FAIL, NOT_TESTED, and MISSING;
- final hashes are verified after every writer closes;
- matrix report/index/registry reconciliation is `PASS` with no mismatch.

Publish an old-versus-new comparison. It may explain changed economics but may
not revise the original V4 candidate verdict.

---

## 10. Phase F — Independent reproduction and audit (Wave 5, H10–H12)

### F1. Four reproductions

A separate process must reproduce all four fresh diagnostics from frozen inputs.
Write into:

```text
results/reproduction_v5r/<verify_id>/
```

Compare at minimum:

- code/spec/data identities;
- orders, positions, funding rows, and terminal rows;
- fold and total canonical PnL;
- PF, MDD, turnover, exposure, beta, and contributions;
- stress and drop-one results;
- final gate verdict and artifact digest.

Tolerance must be predeclared. Any unexplained mismatch fails V5-C20.

### F2. Independent scientific audit

The implementation agent freezes code and artifacts, then hands only read access
to a genuinely separate auditor. The auditor must not have authored the engine,
gates, diagnostics, or transition decision.

The auditor samples at least:

- 50 orders;
- 50 positions;
- 30 funding settlements;
- every fold boundary;
- every exposure breach and forced reduction;
- all four hash manifests and reproduction comparisons.

The sample seed, population hashes, sampled IDs, and findings must be recorded.
Required outputs:

```text
research/audits/v5r/challenge_memo_v5r.md
research/audits/v5r/scientific_audit_v5r.json
```

If A6 is unavailable or loses independence, record
`V5R_INDEPENDENT_AUDIT_BLOCKED`; an implementer must not self-sign PASS.

---

## 11. Phase G — Legacy V5 gate ledger (H12 checkpoint)

Produce a machine-readable row for every gate below. Each row must contain:

```text
gate_id
status = PASS | FAIL | BLOCKED | NOT_TESTED
measured_value
threshold_or_contract
evidence_paths
evidence_sha256
verified_by
verified_at_utc
reason_code
```

### 11.1. The 26 non-waivable V5 gates

```text
V5-C01 current_full_tests_pass_no_xfail
V5-C02 v3_v4_source_artifacts_hash_unchanged
V5-C03 global_scored_trial_ledger_complete
V5-C04 canonical_leg_pnl_field_reconciles
V5-C05 total_pnl_cost_funding_terminal_identity_reconciles
V5-C06 terminal_position_policy_frozen_and_evidenced
V5-C07 continuous_capital_or_chained_return_wfa_valid
V5-C08 mdd_recomputed_from_valid_equity_path
V5-C09 symbol_and_fold_contribution_use_canonical_pnl
V5-C10 funding_cashflows_persist_and_reconcile
V5-C11 commission_and_slippage_persist_and_reconcile
V5-C12 xg0_coverage_and_reason_semantics_correct
V5-C13 actual_funding_settlement_cadence_supported
V5-C14 fee_twotick_delay_stresses_execute
V5-C15 dropone_symbol_and_fold_execute
V5-C16 gross_net_exposure_controller_passes_fixtures
V5-C17 family_aware_portfolio_metrics_no_fake_r
V5-C18 missing_not_tested_and_negative_are_distinct
V5-C19 v4_diagnostic_recalc_four_of_four_complete
V5-C20 independent_reproduction_four_of_four_match
V5-C21 matrix_report_index_registry_reconcile
V5-C22 independent_scientific_audit_pass
V5-C23 no_live_money_change
V5-C24 no_s1_read_or_score
V5-C25 artifact_hashes_verified_after_all_writes
V5-C26 xg1_xg2_use_measured_evidence_no_true_constants
```

### 11.2. Starting gate posture — must be recomputed

```text
V5-C01  provisional PASS evidence exists; rerun after final code state
V5-C02  current FAIL: six unexpected immutable-file mutations
V5-C03  evidence exists; completeness still requires verification
V5-C04–C18  code/tests partly exist; end-to-end evidence not yet sufficient
V5-C14  current NOT_TESTED in existing diagnostic artifacts
V5-C15  current NOT_TESTED in existing diagnostic artifacts
V5-C19  current FAIL: four runs exist but integrity/reconciliation is invalid
V5-C20  current NOT_TESTED: reproduction directories absent
V5-C21  current FAIL: reconciliation is PARTIAL
V5-C22  current NOT_TESTED: independent audit absent
V5-C23  requires diff and runtime safety verification
V5-C24  requires filesystem/access audit
V5-C25  current FAIL: four run.log hash mismatches
V5-C26  requires adversarial code-path verification
```

The provisional posture is not a substitute for measured final rows.

### 11.3. Transition logic

```python
if all(gate.status == "PASS" for gate in V5_C01_to_C26):
    legacy_v5_outcome = "V5_PASS"
elif V5_C22.status == "BLOCKED" and all_other_gates_pass:
    legacy_v5_outcome = "V5_INDEPENDENT_AUDIT_BLOCKED"
else:
    legacy_v5_outcome = "V5_FAIL"
```

Legacy V5 remains immutable after this verdict. If it passes, Section 13 may
authorize V6 directly. If it fails, execute Section 12 V5R; never edit the
legacy rows to make the transition easier.

---

## 12. V5R clean-lineage recovery when legacy V5 fails

Run this section only when legacy V5 is permanently closed as FAIL or its
independent audit is irrecoverably blocked. V5R is a new validation lineage, not
a waiver and not a retroactive repair of V5.

Execution routing for this branch:

```text
1. Write/freeze the legacy Section 11 ledger with V5-C02 FAIL or audit BLOCKED.
2. Execute Sections 12.1–12.2 to quarantine and freeze the new baseline.
3. Execute the shared engineering/diagnostic/reproduction work in Sections 8–10
   using only v5r roots and the new baseline.
4. Return to Sections 12.3–12.4, decide all R01–R18, then evaluate Section 13.
```

### 12.1. Quarantine without deletion

A1 and A2 create `research/audits/v5r/quarantine_manifest.json` containing:

- every compromised experiment/path and expected/current hash;
- cause classification and discovery timestamp;
- `usable_for_scientific_claims=false`;
- `usable_for_forensic_debugging=true`;
- downstream reports that referenced the compromised evidence;
- explicit prohibition on promotion, scoring, baseline reset, or source-trial
  reuse from the quarantined IDs.

Do not move, edit, or delete the old artifacts. Quarantine is metadata and
policy, not concealment.

### 12.2. Create a genuinely new pre-run baseline

After the prevention/finalization/reconciliation fixes are reviewed and merged:

1. A1 freezes exact clean commit SHAs and the allowed dirty-state manifest.
2. A2 hashes all source/spec/data-contract paths **before** any V5R execution.
3. A3 freezes data coverage, funding cadence, metadata limitations, and S0
   boundaries; S1 paths remain prohibited.
4. A4 freezes accounting, execution, costs, terminal, WFA, and risk versions.
5. A5 freezes metric estimators, gates, hash schema, tolerances, and global
   trial-ledger snapshot.
6. A6 independently verifies the baseline timestamp precedes every V5R launch.

Write:

```text
research/audits/v5r/new_lineage_baseline.json
research/audits/v5r/new_lineage_contract.md
```

V5R may reuse frozen, uncompromised V4 candidate specifications only as
`DIAGNOSTIC_RECALC`. It may not reuse old results as pass evidence and may not
change the original V4 rejection.

### 12.3. V5R non-waivable gates

```text
V5R-R01 legacy_v5_verdict_frozen_and_not_rewritten
V5R-R02 compromised_experiments_quarantined_complete
V5R-R03 clean_code_identity_and_allowed_dirty_manifest_frozen
V5R-R04 pre_run_source_spec_data_hash_baseline_verified
V5R-R05 full_tests_and_real_artifact_write_isolation_pass
V5R-R06 data_coverage_universe_benchmark_funding_pit_pass
V5R-R07 canonical_pnl_and_total_equity_identity_reconcile
V5R-R08 terminal_policy_and_continuous_capital_wfa_valid
V5R-R09 funding_commission_slippage_rejection_rows_reconcile
V5R-R10 gross_net_weight_controller_passes_every_bar_fixtures
V5R-R11 family_metrics_and_reason_semantics_measured_not_constant
V5R-R12 fee_twotick_delay_dropone_stresses_execute
V5R-R13 four_fresh_diagnostic_recalcs_complete_without_overwrite
V5R-R14 artifact_hashes_verify_after_all_writers_close
V5R-R15 matrix_report_index_registry_reconcile_without_mismatch
V5R-R16 four_independent_process_reproductions_match
V5R-R17 a6_independent_scientific_audit_pass
V5R-R18 no_live_money_change_and_no_s1_access
```

Every gate uses the row schema from Section 11. Missing evidence fails closed.
Code/unit tests alone cannot satisfy R06–R16; the fresh end-to-end artifacts
must also prove them.

### 12.4. V5R output and verdict

Write:

```text
research/audits/v5r/gate_ledger_v5r.json
research/audits/v5r/v5r_transition.json
research/wayfinder/evidence/sprint-v5r-clean-lineage-20260824.md
```

Valid outcomes:

```text
V5R_PASS
V5R_FAIL
V5R_INDEPENDENT_AUDIT_BLOCKED
```

---

## 13. Unified transition into V6

```python
legacy_path_ok = all(g.status == "PASS" for g in V5_C01_to_C26)
clean_path_ok = (
    legacy_v5_outcome in {"V5_FAIL", "V5_INDEPENDENT_AUDIT_BLOCKED"}
    and all(g.status == "PASS" for g in V5R_R01_to_R18)
)

if legacy_path_ok:
    transition = "V5_PASS_V6_AUTHORIZED"
elif clean_path_ok:
    transition = "V5_FAIL_V5R_PASS_V6_AUTHORIZED_CLEAN_LINEAGE"
else:
    transition = "V5_FAIL_V6_BLOCKED"
```

Before V6 begins, A1 publishes the transition artifact and every other agent
verifies its hash. A6 verifies the transition was computed from measured gate
rows. No agent may begin V6 signal code, inspect V6 partial PnL, or create a
scored V6 run before this checkpoint.

When the clean path authorizes V6:

- legacy V5 remains FAIL in every report;
- quarantined V3 artifacts are never cited as validation evidence;
- V6 manifests reference the V5R baseline and transition, not legacy V5 PASS;
- the global scored-trial ledger still includes all legitimate previous trials;
- V5R diagnostics do not increase the scored-trial count.

---

## 14. Sprint V6 — one bounded funding-carry family

### 14.1. Selected hypothesis

```text
H-XSECT-FUNDING-CARRY-v1
```

The mechanism ranks only funding observations that were already settled and
published at decision time. Because positive funding means longs pay shorts,
the strategy goes long the low-funding group and short the high-funding group,
seeking net funding carry in a market-neutral portfolio.

This is an economic prior, not an edge claim. Price movement can overwhelm
funding. Open interest is excluded from v1 if its point-in-time history is not
complete enough; momentum/regime filters are not added to rescue results.

### 14.2. Pre-registration — lock before signal implementation

```yaml
hypothesis_id: H-XSECT-FUNDING-CARRY-v1
family: cross_sectional_funding_carry
stage: S0_EXPLORATORY
universe: [ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, LINKUSDT, ADAUSDT]
benchmark: BTCUSDT
signal_clock: daily_00_00_utc
feature: trailing_mean_of_published_settled_funding_only
lookback_days: [1, 3, 7]
long: bottom_2_funding
short: top_2_funding
rebalance: 24h
split_policy: chronological_3fold_with_24h_purge_embargo
target_gross: 0.80
hard_gross_cap: 1.00
hard_abs_net_cap: 0.10
max_abs_weight_per_symbol: 0.20
trial_budget:
  scored: 3
  negative_control: 1
negative_control: reverse_funding_rank_3d
```

Freeze estimator versions, costs, latency, terminal policy, universe, data
window, fold boundaries, seed, tie behavior, missing-data policy, and all gates
in the same pre-run manifest.

Forbidden after lock:

- extra lookback or rebalance interval;
- per-symbol parameters;
- momentum, OI, volatility, or regime filters;
- changing weights, costs, universe, folds, or thresholds;
- restarting a failed scored run under a new ID without ledgering the launch;
- choosing a candidate from partial PnL.

### 14.3. Exactly four V6 experiments

```text
XSECT-FUND-CARRY-1D
XSECT-FUND-CARRY-3D
XSECT-FUND-CARRY-7D
XSECT-FUND-REVERSE-3D-CONTROL
```

No fifth scored experiment. The reverse control is never promotion-eligible.
Every attempted scored launch, including an abandoned/crashed launch that saw
scored data, enters the global trial ledger.

### 14.4. Mechanism-specific invalidation

Reject a candidate if any condition holds:

1. total canonical PnL after costs and funding is `<=0`;
2. net funding cashflow is `<=0` or fewer than 2/3 folds have positive funding;
3. positive price PnL masks negative funding while the strategy claims carry;
4. position PF `<1.10`, fewer than 2/3 folds are positive, or median fold
   return is `<=0`;
5. there are not two adjacent positive lookbacks;
6. top fold exceeds 50% or top symbol exceeds 40% of positive PnL;
7. MDD exceeds 10%, any exposure cap breaches, or `abs(BTC beta)>0.25`;
8. baseline fails fee/two-tick/delay/drop-one stress;
9. reverse control beats the best eligible-direction candidate;
10. DSR probability is `<0.95` after global trial adjustment;
11. a data, PIT, integrity, reproduction, or audit gate fails/blocks.

---

## 15. V6 parallel execution, gates, scoring, and learning loop

### 15.1. Wave 6 — lock and implementation (H12–H15)

- **A1:** verify transition; freeze global trial count/spec/budget; allocate file
  ownership and merge order.
- **A2:** create launch-provenance and immutable input/hash contract.
- **A3:** verify actual funding settlement/publication timestamps, clean common
  panel, universe, benchmark, metadata, and purge/embargo boundaries.
- **A4:** implement the pure funding-rank signal and shared-capital adapter only
  after spec lock; validate terminal/cost/risk behavior with hand fixtures.
- **A5:** freeze family metrics, DSR/PBO estimator, hard gates, scorecard,
  reconciliation, and reproduction tolerances.
- **A6:** review the locked contract for contradictions and leakage; write no
  signal/engine/gate code.

H15 implementation gate:

```text
TRANSITION_HASH_VERIFIED
SPEC_AND_TRIAL_BUDGET_LOCKED
DATA_AND_FUNDING_PIT_PASS
CANONICAL_ACCOUNTING_PASS
SHARED_CAPITAL_RISK_PASS
COST_AND_TERMINAL_RECONCILIATION_PASS
FULL_TESTS_PASS_NO_XFAIL
A6_PRE_RUN_PROTOCOL_REVIEW_COMPLETE
```

Fail or block any item: stop V6 before scored execution.

### 15.2. Wave 7 — scored execution (H15–H19)

A1 creates an immutable run queue. R1/R2 execute exact commands in separate
processes, output roots, logs, and registry shards. A2–A5 monitor only contract
violations and infrastructure failures; they may not change parameters.

Recommended queue:

```text
batch 1: 1D candidate + 3D candidate
checkpoint: hashes/resources/registry-shard integrity
batch 2: 7D candidate + reverse 3D control
```

Adding runner agents is allowed only after resource preflight. Each extra runner
gets one frozen experiment and zero code-edit authority. A1 merges registry
shards deterministically after all run processes close.

### 15.3. Wave 8 — gates, stresses, reproduction, audit (H19–H22)

- A5 evaluates hard gates before score.
- R1/R2 run the frozen fee ×1.5, adverse two-tick, extra-15m-delay,
  drop-one-symbol, and drop-one-fold jobs for base survivors.
- If there is no survivor, reproduce at least the best diagnostic and reverse
  control to validate the pipeline; do not promote either.
- A5 independently reproduces every base survivor in separate processes and
  compares orders, positions, funding, costs, equity, metrics, and digests.
- A6 audits only after code/results freeze, receiving the full population rather
  than a favorable subset.
- A1 aggregates machine outputs; A1 cannot override A6 or a hard gate.

### 15.4. V6 hard gates

#### FG0 — Data and universe

- all seven traded symbols plus BTC benchmark satisfy the declared common window;
- actual funding settlement/publication coverage and cadence are complete;
- tick/step/min-notional metadata is point-in-time or its frozen limitation
  fails closed;
- no silent symbol replacement/skip; universe freezes before results.

#### FG1 — Point-in-time and leakage

- funding feature uses only publication timestamps `<= signal_ts`;
- all bars used by features/marks completed before signal;
- `signal_ts < fill_ts`; execution bar is excluded from feature calculation;
- warmup lies outside scored folds; 24h purge/embargo boundaries are evidenced.

#### FG2a/FG2b — Integrity and reproduction

- canonical accounting, hashes, index/report/registry reconciliation all pass;
- independent reruns match frozen tolerance for orders, positions, funding,
  costs, equity, metrics, and digests.

#### FG3 — Base edge

- total after-cost/funding PnL `>0`; net funding cashflow `>0`; PF `>=1.10`;
- at least 2/3 folds have positive PnL and positive funding; median fold return
  `>0`;
- at least 90 scored daily rebalances and 100 canonical closed/terminal legs;
- top fold `<=50%`; top symbol `<=40%`;
- daily net Sharpe `>=0.50`; DSR remains the selection-bias gate.

#### FG4 — Robustness

- fee ×1.5, adverse two ticks, and extra 15m delay retain positive PnL and the
  positive funding mechanism;
- at least two adjacent lookbacks are positive;
- drop-one-symbol and drop-one-fold diagnostics do not expose a sign-flip
  dependency inconsistent with the pre-registered rule;
- turnover/capacity contract passes.

#### FG5 — Shared-capital risk

- gross `<=1.00`, `abs(net)<=0.10`, `abs(weight/symbol)<=0.20` on every completed
  bar;
- no margin breach/liquidation; MDD `<=10%`; `abs(BTC beta)<=0.25`;
- top-symbol contribution `<=40%`.

#### FG6 — Multiple testing and independent audit

- DSR probability `>=0.95` using the complete global scored-trial ledger;
- PBO/CSCV reports a value only when preconditions hold, otherwise
  `NOT_ENOUGH_CONFIGURATIONS` rather than fake PASS;
- A6 scientific audit PASS with no unresolved HIGH/CRITICAL finding.

Every FG0–FG6 gate must PASS before score can make a candidate eligible.

### 15.5. V6 scorecard — 100 points

Hard gates precede score. A missing metric scores zero for its component and has
an explicit reason code. A 100-point candidate with one failed hard gate is
rejected.

#### A. Data and point-in-time — 15

- 5: seven symbols, BTC, and funding coverage/cadence complete;
- 5: no lookahead; signal/fill/warmup/fold evidence complete;
- 5: universe, metadata, manifest, and hashes frozen before run.

#### B. Accounting and cost truth — 15

- 5: canonical/fold/terminal/total equity identities reconcile;
- 5: commission, slippage, and rejection decomposition reconcile;
- 5: funding cashflows are persisted, PIT-valid, and reconcile by symbol/fold.

#### C. Chronological edge — 20

- 5: after-cost total PnL positive;
- 5: PF `>=1.20`; 3 for `1.15–<1.20`; 1 for `1.10–<1.15`;
- 5: 3/3 positive folds; 3 for exactly 2/3;
- 5: daily Sharpe `>=1.00`; 3 for `0.75–<1.00`; 1 for `0.50–<0.75`.

#### D. Risk and concentration — 15

- 5: MDD `<=6%`; 4 for `>6–8%`; 2 for `>8–10%`;
- 5: no gross/net/weight/margin violation;
- 5: top symbol `<=30%` and top fold `<=40%`; 3 when both remain within the
  hard limits of 40% and 50%.

#### E. Robustness and execution — 15

- 6: fee/two-tick/extra-delay positive, two points each;
- 4: drop-one-symbol and drop-one-fold pass, two points each;
- 3: turnover/capacity contract passes;
- 2: at least two adjacent lookbacks are positive.

#### F. Multiple testing — 10

- 6: DSR `>=0.99`; 4 for `0.975–<0.99`; 2 for `0.95–<0.975`;
- 2: global scored-trial ledger is complete and append-only;
- 2: PBO `<=25%` when estimable; zero with
  `NOT_ENOUGH_CONFIGURATIONS`, without inventing a hard-gate PASS.

#### G. Reproduction and audit — 10

- 5: independent rerun all-match;
- 3: A6 audit PASS with no unresolved HIGH/CRITICAL finding;
- 2: matrix/report/index/registry/status artifacts reconcile.

Selection rule:

```text
eligible = all(FG0..FG6 PASS) and score >= 75
tie_break = highest_DSR_then_lower_MDD_then_lower_turnover
max_locked_candidates = 1
```

### 15.6. Wave 9 — verdict and research-learning loop (H22–H24)

Valid V6 terminal outcomes:

```text
V6_PIPELINE_FAIL
V6_CANDIDATE_FAIL
V6_CANDIDATE_INCONCLUSIVE
V6_LOCK_ONE_FOR_FUTURE_S1
```

After the verdict, A3–A5 classify failures into data, PIT, execution, accounting,
cost, capacity, risk, statistical-power, selection-bias, or mechanism failure.
A1 writes those facts into the hypothesis status and next-sprint idea backlog.

This is the learning loop:

```text
frozen idea -> implementation -> multi-symbol WFA/backtest -> hard gates
-> score -> independent challenge -> reject/lock -> failure taxonomy
-> next pre-registered idea in a future sprint
```

Do not convert the learning loop into same-window tuning. No fifth V6 experiment
and no v1.1 rescue run occur in this sprint.

### 15.7. Future S1 rule

1. Existing S0 is already inspected and is not untouched OOS.
2. Only after one V6 candidate is locked may the team create a future S1 start
   timestamp; do not backfill S1.
3. V6 must not read, score, or tune on S1.
4. Insufficient future duration/trades is `WAIT_FOR_MORE_DATA`, not early PASS.
5. Later promotion requires Stage B after-cost PF `>=1.15`, MDD `<=10%`,
   shared-capital replay, stresses/delayed fills, global-trial adjustment, and
   6–8 weeks signal-only observation.
6. No candidate means no fake S1 and no live money.

---

## 16. Required final artifacts

```text
research/audits/v5r/
  intake_snapshot.json
  worktree_inventory.json
  test_contamination_root_cause.md
  test_isolation_check.json
  exact_recovery_search.json
  source_hash_recheck_v5r.json
  final_tests_v5r.json
  gate_ledger_v5r.json
  quarantine_manifest.json              required when legacy V5 fails
  new_lineage_baseline.json              required on clean-lineage path
  new_lineage_contract.md                required on clean-lineage path
  challenge_memo_v5r.md                  written by A6
  scientific_audit_v5r.json              PASS/FAIL/BLOCKED
  v5_legacy_transition.json
  v5r_transition.json                    required on clean-lineage path

results/matrix/v4_recalc_diagnostic_v5r/
  index.json
  report.json
  reconciliation.json
  old_new_comparison.json

results/diagnostic_v5r/<experiment_id>/
results/reproduction_v5r/<verify_id>/

research/hypotheses/H-XSECT-FUNDING-CARRY-v1/
  hypothesis.md
  candidate.yaml
  status.yaml

results/matrix/v6_xsect_funding_carry/
  index.json
  report.json
  reconciliation.json
  v6_final_transition.json

results/portfolio_v6/<experiment_id>/
  launch_manifest.yaml
  frozen/
  signals.jsonl
  orders.jsonl
  positions.jsonl
  terminal_positions.jsonl
  funding_cashflows.jsonl
  portfolio_ledger.jsonl
  accounting_reconciliation.json
  canonical_metrics.json
  beta_report.json
  contribution_report.json
  stress_report.json
  dsr_pbo_report.json
  gate_result.json
  scorecard.json
  artifact_hashes.json

results/reproduction_v6/<verify_id>/
research/audits/v6/challenge_memo.md
research/audits/v6/scientific_audit.json

research/wayfinder/evidence/sprint-v5r-v6-master-20260824.md
research/audits/v5r/master_transition.json
CONTINUE.md                                  rewritten only at final handoff
```

If neither transition path authorizes V6, all V6 result directories must remain
absent. The final report must say V6 was intentionally blocked. If V6 runs, all
artifacts must identify whether authorization came from legacy V5 or clean V5R.

### `master_transition.json` minimum schema

```json
{
  "schema_version": 1,
  "plan": "V5R_V6_ORCA_20260824",
  "source_head": "<sha>",
  "final_head": "<sha-or-dirty-state>",
  "legacy_v5": {"verdict": "PASS|FAIL|BLOCKED", "gates": []},
  "v5r": {"verdict": "PASS|FAIL|BLOCKED|NOT_REQUIRED", "gates": []},
  "v6_authorization_path": "LEGACY_V5|CLEAN_V5R|NONE",
  "v6": {"verdict": "PIPELINE_FAIL|CANDIDATE_FAIL|CANDIDATE_INCONCLUSIVE|LOCK_ONE_FOR_FUTURE_S1|NOT_RUN", "gates": [], "scorecards": []},
  "scientific_audit_verdict": "PASS|FAIL|BLOCKED|NOT_RUN",
  "s1_status": "NOT_STARTED",
  "live_money_status": "UNCHANGED_DISABLED",
  "created_at_utc": "<timestamp>"
}
```

---

## 17. Final report requirements

The master report must begin with a compact verdict block:

```text
ENGINEERING_VERDICT
SCIENTIFIC_AUDIT_VERDICT
V5_COMPLETION_COUNT = x/26
V5_FAILED_GATES
V5_BLOCKED_GATES
V5R_COMPLETION_COUNT = x/18 or NOT_REQUIRED
V5R_FAILED_GATES
V6_TRANSITION
V6_ENGINEERING_VERDICT
V6_FAMILY_VERDICT
GLOBAL_SCORED_TRIAL_COUNT
LOCKED_CANDIDATE_OR_NONE
S1_STATUS
LIVE_MONEY_STATUS
```

Then explain:

1. what the new agent found versus what previous handoff claimed;
2. root cause and blast radius of provenance mutation;
3. whether exact original bytes were recovered and how this was proven;
4. what the defensive patch prevents;
5. why existing V5 diagnostics are or are not trustworthy;
6. whether fresh diagnostics/reproductions were allowed to run;
7. every failed or blocked gate, without euphemism;
8. which transition path, if any, authorized V6;
9. V6 trial budget, gates, scores, failure taxonomy, and negative-control result;
10. exact next action for the repository owner.

---

## 18. Suggested execution commands

These commands are starting points, not a script to run blindly:

```bash
cd /Users/hoangminhlong/my-quantitative
git status --short
git log --oneline --decorate -12
git diff -- research/matrix_runner.py tests/test_matrix_runner.py
git worktree list --porcelain
.venv/bin/python -m pytest tests/ -q
```

Before any commit:

```bash
git diff --check
git diff --name-only
git status --short
```

Use explicit `git add <reviewed-file>...` only. Never assume `results/` will be
tracked; verify `.gitignore` and preserve audit evidence at an intentional,
reviewable path.

---

## 19. Agent status-report format

At each major phase boundary, report:

```text
PHASE
STATUS = PASS | FAIL | BLOCKED | IN_PROGRESS
FILES_CHANGED
COMMANDS_AND_EXIT_CODES
EVIDENCE_CREATED
NEW_FINDINGS
NEXT_DECISION
```

Do not report a percentage based on intuition. If progress is requested, report
completed mandatory gates by lineage plus phase status, for example
`legacy V5 8/26 PASS and FAIL; V5R 11/18 PASS; V6 not authorized`.

---

## 20. Stop conditions

Stop immediately and document the condition if:

- a command would modify an old worktree or V1–V4 artifact;
- exact restoration requires guessing or changing the baseline;
- S1 or live credentials are required;
- a result directory would be overwritten;
- the same scientific role would implement and independently approve its work;
- a legacy V5 rerun is proposed while V5-C02 remains failed and no V5R
  quarantine/baseline has been frozen;
- evidence cannot distinguish a code assertion from a measured fact.

The right response to these conditions is a clear blocker, not an improvised
waiver.

---

## 21. Orca bootstrap prompt

```text
You are A1, the coordinator and final integrator for repository
/Users/hoangminhlong/my-quantitative.

Read PLAN.md completely before acting. PLAN.md is the execution contract.
CONTINUE.md and old sprint reports are historical context only. Treat both
/Users/hoangminhlong/my-quantitative-wt and the nested my-quantitative-wt/
directory as read-only evidence owned by previous agents. Do not modify, clean,
prune, reset, commit inside, or delete them.

Use Orca to create six persistent roles:
- A1 coordinator/integrator;
- A2 provenance and exact-recovery owner;
- A3 data/funding point-in-time owner;
- A4 execution/accounting/risk owner;
- A5 metrics/reconciliation/reproduction owner;
- A6 independent scientific auditor.

Create R1/R2 only as ephemeral frozen-run workers after a run is authorized.
You may add more runner/read-only verification agents only after resource and
write-isolation checks. Do not add overlapping coding owners merely because
Orca has spare capacity.

Begin with Wave 1 read-only inspection in parallel. Preserve all existing dirty
and untracked work. Record current Git state, worktrees, hashes, environment,
tests, artifacts, and ownership before edits. Use .venv/bin/python. Never use
git add -A or destructive cleanup. Never touch S1 or enable live money.

First close the test-contamination defect and decide legacy V5-C02 from the
original 1,474-path baseline. Search once for byte-identical originals; never
guess or reset the baseline. If legacy V5 cannot pass, freeze V5_FAIL, quarantine
the compromised artifacts without deleting them, and execute the V5R clean-lineage
protocol. V5R must create its baseline before any run and pass all V5R-R01..R18.

Do not begin V6 unless the machine-readable transition is exactly either:
- V5_PASS_V6_AUTHORIZED; or
- V5_FAIL_V5R_PASS_V6_AUTHORIZED_CLEAN_LINEAGE.

If authorized, pre-register H-XSECT-FUNDING-CARRY-v1 before signal implementation.
Run exactly 1D, 3D, 7D, and reverse-3D control experiments. No fifth trial, no
post-hoc filters, no parameter rescue, and no use of partial PnL for decisions.
Run hard gates before scoring. A6 must remain independent and must audit the
frozen full evidence population.

Maintain isolated output roots and registry shards for concurrent workers.
Integrate only reviewed commits with explicit file allowlists. At every wave
boundary report gate counts, files, commands/exit codes, artifacts/hashes,
findings, blockers, and the next transition decision.

Continue until one terminal outcome in PLAN.md is proven. A truthful FAIL or
BLOCKED outcome is valid. Never manufacture PASS to continue the schedule.
Finish by writing all required machine-readable transitions, audit artifacts,
the master evidence report, and a fresh CONTINUE.md handoff. Do not push or
change remote state unless the repository owner explicitly asks.
```
