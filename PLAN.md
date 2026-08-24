# PLAN.md — 12-Hour Sprint V6P → V6 → V7 · Bounded Scientific Research Loop

> **Repository:** `/Users/hoangminhlong/my-quantitative`
> **Effective from:** current `main` at `2e3bc9c` (2026-08-24)
> **Target duration:** maximum 12 wall-clock hours of unattended Orca execution
> **Team:** seven core agents plus bounded frozen-run workers
> **Scope:** repair and independently validate the portfolio research path, run
> one pre-registered V6 family, then one pre-registered V7 family only through
> explicit machine-readable gates; no unbounded strategy search
> **Environment:** research/Testnet/Demo only; S1 untouched; live money disabled

---

## 0. Executive instruction

V6 did not run in the prior sprint. Do not skip directly to V7, but V7 is now
part of this same execution contract and may start automatically after a valid
V6 terminal transition.

The completed sprint ended safely at:

```text
LEGACY_V5_VERDICT       = FAIL
DECLARED_V5R_VERDICT    = FAIL
MASTER_TRANSITION       = V5_FAIL_V6_BLOCKED
V6_STATUS               = NOT_RUN
LOCKED_CANDIDATE        = NONE
S1_STATUS               = NOT_STARTED
LIVE_MONEY_STATUS       = UNCHANGED_DISABLED
```

That terminal decision was correct. However, a fresh review of code and raw
artifacts found that the V5R ledger and A6 audit overclaimed several PASS gates.
The next sprint therefore has three strictly ordered stages:

```text
V6P  SCIENTIFIC PIPELINE REPAIR AND ADVERSARIAL VALIDATION
V6   ONE BOUNDED FUNDING-CARRY FAMILY, only if V6P PASS
V7   ONE BOUNDED FUNDING-PRICE-DIVERGENCE FAMILY, only if V6 is terminal
     and the V7 authorization gate passes
```

The objective is not to make V5R look better and not to force a profitable V6
or V7 candidate. The objective is to obtain one research path whose data,
accounting, risk, walk-forward, gates, reproduction, and audit claims all
describe what the runtime actually did, then exercise that path through two
small, pre-registered and scientifically separated hypothesis families.

---

## 1. Verified starting assessment

### 1.1. What the previous sprint did well

1. It preserved the safe transition: V6 was blocked rather than run through two
   declared V5R failures.
2. It proved the V3 provenance mutation mechanism and permanently quarantined
   the compromised experiments without deleting evidence.
3. Test isolation was fixed; the current full suite was independently rerun for
   this plan and produced `581 passed, 16 warnings, exit 0`.
4. Artifact finalization improved: all four V5R hash manifests currently verify
   with zero mismatches.
5. Four separate-process reproductions deterministically match the limited
   fields they compare.
6. Matrix index references four existing diagnostic directories and reports no
   missing experiment directory.
7. No S1 or live-money surface was used.

These accomplishments remain valid. Do not rewrite old verdicts or artifacts.

### 1.2. Why “16/18 V5R PASS” is not accepted as current truth

The following findings were verified directly from current code and artifacts.
They must be recorded in a new addendum; never edit the immutable V5R ledger.

| ID | Severity | Verified finding | Affected claim |
|---|---|---|---|
| N01 | **CRITICAL** | `new_lineage_baseline.json` still says `PENDING_A6`; no pre-launch A6 attestation exists, yet R04 claims A6 PASS | R04 and report provenance |
| N02 | **CRITICAL** | All four launch manifests record `dirty_worktree_at_launch=true`; baseline and contract were committed only after launches, while contract claims a clean tree | R03/R04 |
| N03 | **HIGH** | The baseline includes a hash of itself that does not equal its current bytes; a self-referential hash is not a valid immutable-root design | R04 |
| N04 | **CRITICAL** | `execute_experiment` calls the engine once per fold; every fold begins at 100,000, so the outer curve is still reset-fold, not continuous capital | R08, MDD, fold returns |
| N05 | **CRITICAL** | Runtime adapter does not enable `RISK_MODE_V1`; gross exceeds 1.00 on about 39% of bars, up to 1.2746 | R10 and risk evidence |
| N06 | **CRITICAL** | Required settlement/accounting artifacts are not written: `funding_cashflows.jsonl`, `accounting_reconciliation.json`, `commission_slippage.json`, `terminal_positions.jsonl`, `exposure_control.jsonl` are absent 4/4 | R09 and audit completeness |
| N07 | **CRITICAL** | Portfolio runner still passes hand-built XG1 booleans; it never supplies `execution_ledger_rows`, so XG1 PASS is not measured runtime evidence | R11 and scientific audit |
| N08 | **HIGH** | Default panel adapter returns `coverage=None`; XG0 therefore sees zero days. The failure is an unimplemented coverage adapter, not proof that the frozen funding bundle is incomplete | R06 diagnosis |
| N09 | **HIGH** | Missing BTC benchmark coverage is mislabeled `funding_coverage_insufficient`; the data manifest independently reports complete funding cadence for all seven traded symbols | R06 reason semantics |
| N10 | **HIGH** | Stress executor is conditional on base XG3 PASS and uses `expectancy_r`, although this portfolio family explicitly has no R normalization | R12 and future V6 robustness |
| N11 | **HIGH** | Reproduction compares orders/positions digests plus four metrics, but does not compare funding, costs, equity ledger, terminal rows, accounting, stresses, gates, or final artifact digest | R16 |
| N12 | **HIGH** | `reconciliation.json` says `registry_append_only_verified=false`, while R15 claims TRUE; `report.json` still declares `stage_a_root=results/portfolio_v4` | R15 |
| N13 | **HIGH** | A6 audit missed N01–N12 and called gate measurement honest; its independence can remain true, but its scientific completeness verdict cannot authorize future work | R17 |
| N14 | **MEDIUM** | No explicit purge/embargo fields are frozen in the run contract | future V6 fold isolation |
| N15 | **MEDIUM** | Transition/audit timestamps and `final_head` fields were not refreshed consistently after audit integration | transition provenance |

### 1.3. Correct interpretation of R06

The current real-data contract contains seven traded symbols and one BTC
benchmark. BTC is context-only and must not appear in the traded-symbol count.
The current manifest reports complete funding cadence for the seven traded
symbols in its measured bundle. The requested V5R run starts at the already
trimmed common boundary around `2025-08-21T14:30Z`.

Therefore R06 remains FAIL, but its primary cause is:

```text
RUNTIME_COVERAGE_EVIDENCE_NOT_WIRED_AND_REASON_CODES_CONFLATED
```

Do not download data, remove ETH, shrink the window, or change the universe
until the runtime reads the existing canonical bundle and produces a measured
coverage report. Only then may a genuine data shortfall be declared.

### 1.4. Current evidence verdict

```text
SAFE_TRANSITION_DECISION          = CORRECT
V5R_ENGINEERING_PROGRESS          = MATERIAL_BUT_INCOMPLETE
V5R_GATE_LEDGER_ACCURACY          = FAILS_ADVERSARIAL_REVIEW
A6_INDEPENDENCE                   = PRESERVED
A6_AUDIT_COMPLETENESS             = INSUFFICIENT_FOR_AUTHORIZATION
V6_AUTHORIZATION                  = NONE
```

No existing V5R result is promoted or re-scored. Reproduction of a defective
pipeline proves determinism of that pipeline, not scientific correctness.

---

## 2. Authority, immutability, and safety

Authority order:

1. current code plus raw machine artifacts recomputed by an independent reader;
2. this PLAN;
3. specifications/baselines committed before execution;
4. Git history and exact command logs;
5. `CONTINUE.md`, sprint summaries, transition prose, and agent messages.

Rules:

1. Existing V1–V5R artifacts and transition files are immutable evidence.
2. Write corrections only as V6P addenda in a new namespace.
3. Old `my-quantitative-wt` locations are read-only; do not prune or reuse them.
4. Use `.venv/bin/python`, never system Python.
5. Preserve a clean or explicitly frozen Git state; no `git add -A`.
6. No destructive reset/clean/remove commands.
7. No S1 read, capture, score, or backfill.
8. No live order, credential use, or live-mode enablement.
9. Do not tune the universe/window after seeing strategy results.
10. Missing evidence is FAIL/BLOCKED/NOT_TESTED, never PASS.
11. A unit test cannot substitute for required end-to-end evidence.
12. A deterministic rerun cannot validate a wrong accounting or gate contract.
13. The final auditor may author audit files only.
14. V6 begins only from a committed machine-readable `V6P_PASS` transition.

---

## 3. Orca team topology

Use seven persistent roles. Additional agents are allowed only as bounded run or
read-only verification workers with no overlapping code ownership.

| Agent | Ownership | Required outputs | Forbidden |
|---|---|---|---|
| **A1 Coordinator** | intake, contracts, merge queue, baselines, transitions, trial ledger, final report | integration ledger and transitions | self-signing audit; editing results to change verdict |
| **A2 Provenance** | committed pre-run baseline, immutable roots, launch identity, transition timestamps | provenance tests and V6P baseline | post-launch baseline creation; self-hashing artifact |
| **A3 Data/PIT** | bar/benchmark/funding/metadata coverage, publication-time contract, XG0 payload | measured coverage report | changing universe/window after results |
| **A4 Engine/Accounting** | one-pass continuous WFA, risk mode, costs/funding/terminal artifacts | golden accounting fixtures and runtime artifacts | metric thresholds or strategy selection |
| **A5 Gates/Reproduction** | measured XG1/XG2, family metrics, unconditional stresses, reconciliation, full reproduction | gate/repro schemas and negative fixtures | strategy/spec edits |
| **A6 Hypotheses** | V6/V7 specs and implementations after V6P PASS; V7 scored execution only after V7 authorization | locked V6/V7 hypothesis specs and strategy code | coding before V6P authorization; result-driven spec changes |
| **A7 Independent auditor** | adversarial audit of V6P and V6 frozen populations | challenge memos and attestations | implementation, gate repair, artifact repair |
| **R1–R4 workers** | exact frozen commands in isolated output roots | logs, exit code, artifact digest | code/spec edits, shared registry writes, verdict |

Every coding agent gets a unique new branch/worktree created from the same A1
bootstrap commit. Shared JSONL/index files have one writer: A1. Workers write
registry shards which A1 merges deterministically after all writers close.

---

## 4. Adaptive unattended 12-hour schedule

```text
H00:00–H00:30  A1 freeze/intake; A2–A5 audits; A7 challenge protocol;
                 A6 drafts V6 and V7 specifications without seeing results
H00:30–H03:00  A2–A5 repair in parallel; A1 integrates bounded commits
H03:00–H04:00  full tests; committed V6P baseline; A7 pre-launch attestation
H04:00–H05:00  V6P sentinels, full reproduction, A7 audit, V6P transition
H05:00          checkpoint: stop if V6P is not 20/20 PASS
H05:00–H07:00  V6 four base trials, stresses, reproductions, audit, terminal verdict
H07:00          checkpoint: compute V7 authorization; no result-driven spec edits
H07:00–H09:00  V7 four base trials, stresses, reproductions, audit, terminal verdict
H09:00–H10:15  global ledger reconciliation and cross-family learning memo
H10:15–H11:15  reserve only for incomplete tests/stresses/reproductions/audits;
                 never use this reserve for an extra strategy or parameter trial
H11:15–H12:00  final hashes, reports, CONTINUE handoff, graceful shutdown
```

These are checkpoints, not waivers. If repair work consumes the window, finish
V6P truthfully and stop; never compress tests/audit to reach V6 or V7. Start at
most two CPU-heavy jobs concurrently and increase only after CPU/RAM/I/O
preflight shows no swapping or throughput loss. Section 15 defines the exact
deadline, retry, resume, and shutdown rules. Twelve hours is a ceiling, not a
quota: if every required state becomes terminal in 3–4 hours, finalize and stop
immediately instead of inventing more work to fill the remaining time.

---

## 5. Phase V6P-0 — freeze current truth

A1 and A7 create:

```text
research/audits/v6p/intake_snapshot.json
research/audits/v6p/v5r_reaudit_addendum.md
research/audits/v6p/v5r_reaudit_gates.json
```

The addendum must:

1. preserve `V5_FAIL_V6_BLOCKED` as the historical safe verdict;
2. list N01–N15 with code/artifact paths and hashes;
3. distinguish correct old evidence from overclaimed gates;
4. never modify V5R gate ledgers, audit, transition, or report;
5. record the independently rerun current test result;
6. record that V6 artifacts/hypothesis were absent at intake.

No repair begins until each owner returns a file allowlist and A1 confirms no
overlap.

---

## 6. Phase V6P-1 — parallel repair tracks

### 6.1. A2 — provenance and baseline truth

Implement a baseline design that can be proven, not asserted:

1. Commit all source/spec/contract files before baseline creation.
2. Require clean `git status --porcelain` before the baseline timestamp.
3. Hash source/spec/data inputs into an external root manifest. Do not include
   the baseline file's own hash inside itself.
4. Commit the baseline and A7 pre-run attestation before any worker launch.
5. Launch manifest must record the committed baseline hash and clean launch SHA.
6. Abort execution when `dirty_worktree_at_launch=true` or baseline/attestation
   is absent.
7. Separate `created_at`, `audited_at`, `integrated_at`, `audited_head`, and
   `final_head`; refresh transition content after integration.
8. Negative tests must catch post-launch baseline creation, self-hash mismatch,
   dirty launch, timestamp inversion, and transition-head mismatch.

### 6.2. A3 — real XG0 and funding PIT evidence

Wire `portfolio_runner` to `coverage_report` or a versioned equivalent.

Required payload blocks:

```text
traded_bar_coverage: seven traded symbols only
benchmark_coverage: BTCUSDT context only
funding_coverage: actual settlement count/first/last/completeness per traded symbol
metadata_coverage: tick, step, min-notional identity per traded symbol
requested_window and effective_common_window
```

Rules:

1. Use one canonical funding bundle identity, recommended current
   `funding_data/scan_2026`, and freeze its path/hash.
2. Compare coverage to the predeclared requested V6P window before results.
3. BTC absence from the traded universe is expected, not a coverage failure.
4. Benchmark failure reason is `benchmark_coverage_incomplete`, never a funding
   reason.
5. Funding failure requires measured missing/late settlements from the same
   runtime bundle, not `coverage=None` or a different config path.
6. Funding features later use only rows whose publication/settlement timestamp
   is `<= signal_ts`.
7. Add negative fixtures for missing BTC, missing traded bars, missing funding,
   bundle mismatch, metadata missing, and one-symbol partial window.
8. Do not fetch data unless measured canonical coverage truly fails. Network
   repair, if later authorized, must be a separate checksummed data task.

### 6.3. A4 — one-pass WFA, canonical accounting, and risk

Redesign the orchestration so all three folds run in one engine invocation or
carry real ending equity into the next fold without reset.

Required behavior:

1. One chronological timeline with three declared fold intervals.
2. `reset_folds=false`; F2 starting equity equals F1 ending equity and F3 starts
   from F2 ending equity within tolerance.
3. MDD derives from the continuous equity path, never stitched 100k curves.
4. Pass `risk_mode=RISK_MODE_V1` end-to-end for V6P and future V6.
5. Enforce gross `<=1.00`, `abs(net)<=0.10`, and declared symbol-weight cap on
   every completed 15m event after deterministic reduce-only action.
6. Persist all engine-native outputs:

```text
portfolio_ledger.jsonl
orders.jsonl
positions.jsonl
funding_cashflows.jsonl
terminal_positions.jsonl
exposure_control.jsonl
accounting_reconciliation.json
commission_slippage.json
```

7. Reconcile at fold and experiment level:

```text
ending_equity - starting_equity
= closed_price_pnl + terminal_pnl + funding_cashflows
 - commissions - slippage - rejection_costs
```

8. Funding allocations in legs must reconcile to settlement-level funding rows.
9. Terminal rows must reconcile to closed legs and leave a flat final book.
10. Golden fixtures must catch reset folds, missing settlement rows, inactive
    risk mode, exposure after trim above cap, and terminal double counting.

### 6.4. A5 — measured gates, family-aware stresses, and full reproduction

1. Delete the scored-path dependency on hand-built XG1 booleans.
2. Pass real order/execution rows into `evaluate_xg1_measured`; verify counters
   for missing timestamps and `signal_ts < fill_ts` violations.
3. XG2a is external-reader hash/schema/accounting/reconciliation evidence after
   all writers close. XG2b is populated only after separate reproduction.
4. Supply measured fold returns to XG3. Do not infer return from reset-fold PnL.
5. Replace portfolio stress `expectancy_r` with family-aware metrics:
   canonical PnL, PF, funding PnL, fold returns, MDD, and exposure.
6. Execute fee ×1.5, adverse two ticks, extra one-event delay,
   drop-one-symbol, and drop-one-fold regardless of base-edge verdict.
7. Negative base edge remains rejected; stress execution is diagnostic evidence,
   not rescue logic.
8. Reconciliation must fail when append-only verification is false, report root
   is stale, required files are missing, or transition counts disagree.
9. Full reproduction compares digests and metrics for:

```text
signals, orders, positions, ledger, funding, terminal, exposure-control,
accounting, costs, canonical metrics, stresses, gates, scorecard, final hashes
```

10. Reproduction uses frozen inputs and a separate process/output root; it may
    not call the source artifact's verdict as its expected truth.

### 6.5. A7 — adversarial protocol before execution

A7 freezes a challenge plan before V6P runs. It must explicitly test N01–N15,
not only sample correct rows. A7 verifies the committed baseline/attestation
precedes launch and audits the full population after freeze.

---

## 7. Phase V6P-2 — bounded end-to-end validation

Use fresh immutable IDs and do not overwrite V5R:

```text
results/validation_v6p/V6P-MOM-7D-BASEFAIL-SENTINEL/
results/validation_v6p/V6P-REVERSE-7D-FUNDING-SIGN/
results/validation_v6p/V6P-GOLDEN-SYNTHETIC/
results/reproduction_v6p/<verify_id>/
results/matrix/v6p_validation/
```

The MOM sentinel is intentionally expected to fail its edge gate. It proves
that all stresses execute even when base edge fails. The reverse control proves
funding-sign/accounting behavior. The synthetic run has hand-computed expected
orders, funding, costs, risk trims, terminal PnL, and continuous equity.

These are `PIPELINE_VALIDATION`/`DIAGNOSTIC_RECALC`, never scored trials and
never promotion-eligible.

### 7.1. V6P hard gates — all must PASS

```text
V6P-C01 prior_v5_v5r_artifacts_unchanged_and_addendum_complete
V6P-C02 clean_source_commit_and_external_baseline_root_frozen
V6P-C03 a7_prelaunch_attestation_committed_before_workers
V6P-C04 all_launches_clean_and_match_frozen_commit_baseline
V6P-C05 full_tests_pass_zero_fail_zero_xfail
V6P-C06 xg0_real_bar_benchmark_funding_metadata_blocks_pass
V6P-C07 funding_bundle_identity_and_publication_pit_pass
V6P-C08 xg1_measured_rows_no_boolean_fallback_on_scored_path
V6P-C09 one_pass_continuous_capital_threefold_identity_pass
V6P-C10 continuous_equity_mdd_and_fold_returns_valid
V6P-C11 funding_cost_terminal_accounting_artifacts_complete_reconcile
V6P-C12 risk_mode_active_every_bar_and_all_caps_hold_after_action
V6P-C13 all_stresses_and_dropone_execute_despite_base_edge_fail
V6P-C14 family_aware_stress_metrics_no_fake_expectancy_r
V6P-C15 artifact_hashes_last_external_reader_clean
V6P-C16 matrix_report_index_roots_registry_reconcile_complete
V6P-C17 registry_append_only_verified_true_in_final_artifact
V6P-C18 full_surface_separate_process_reproductions_match
V6P-C19 a7_postfreeze_adversarial_audit_pass
V6P-C20 no_unresolved_high_critical_no_s1_no_live
```

Transition:

```python
if all(g.status == "PASS" for g in V6P_C01_to_C20):
    transition = "V6P_PASS_V6_AUTHORIZED"
else:
    transition = "V6P_FAIL_V6_BLOCKED"
```

No waiver. A safe V6P FAIL is a valid terminal sprint outcome.

---

## 8. V6 hypothesis — lock only after V6P PASS

### 8.1. Selected mechanism

```text
H-XSECT-FUNDING-CARRY-v1
```

Positive funding means longs pay shorts. The hypothesis buys the relatively
low-funding group and shorts the relatively high-funding group, using only
funding observations already settled/published by signal time.

This is a prior, not an edge claim. Price loss may overwhelm collected carry.

### 8.2. Pre-registration contract

```yaml
hypothesis_id: H-XSECT-FUNDING-CARRY-v1
family: cross_sectional_funding_carry
stage: S0_EXPLORATORY
traded_universe: [ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, LINKUSDT, ADAUSDT]
benchmark_context: BTCUSDT
signal_clock: daily_00_00_utc
feature: trailing_mean_of_published_settled_funding_only
lookback_days: [1, 3, 7]
long_rule: bottom_2_funding
short_rule: top_2_funding
rebalance: 24h
folds: chronological_3fold
purge_embargo: 24h
target_gross: 0.80
hard_gross_cap: 1.00
hard_abs_net_cap: 0.10
max_abs_weight_per_symbol: 0.20
trial_budget:
  scored_candidates: 3
  negative_controls: 1
negative_control: reverse_funding_rank_3d
```

Freeze before signal implementation:

- effective S0 common window;
- data/funding/metadata hashes;
- folds, purge/embargo, warmup, signal/fill clocks;
- funding publication convention and missing-settlement policy;
- cost, latency, terminal, risk, accounting, and metric versions;
- trial ledger count and DSR estimator;
- hard gates, scorecard, tie-break, resource limits, seeds/tolerances.

Do not add OI, momentum, volatility, regime filters, per-symbol parameters,
extra lookbacks, or another rebalance interval in v1.

---

## 9. V6 execution

### 9.1. Exactly four scored launches

```text
XSECT-FUND-CARRY-1D
XSECT-FUND-CARRY-3D
XSECT-FUND-CARRY-7D
XSECT-FUND-REVERSE-3D-CONTROL
```

There is no fifth launch. A crashed/abandoned launch that accessed scored data
still enters the global scored-trial ledger. Diagnostic stresses and independent
reproductions link to their source trial but do not increment scored count.

### 9.2. Parallel run policy

1. A1 freezes a run queue and registry shard per experiment.
2. Start two workers; add more only after resource preflight.
3. Workers run exact commands and cannot edit code/spec.
4. No agent sees partial PnL for decision-making.
5. A1 merges shards once, after all writers close.
6. Hash each experiment last and verify from a separate process.
7. Hard gates run before score.
8. A7 receives the entire frozen population, not a selected subset.

### 9.3. Mechanism invalidation

Reject a candidate if any condition holds:

1. after-cost canonical PnL `<=0`;
2. net funding cashflow `<=0` or fewer than 2/3 folds have positive funding;
3. price PnL masks negative funding while the strategy claims carry;
4. PF `<1.10`, fewer than 2/3 positive folds, or median fold return `<=0`;
5. no adjacent positive lookback pair among 1D/3D/7D;
6. top fold `>50%` or top symbol `>40%` of positive PnL;
7. MDD `>10%`, risk cap breach, margin breach, or `abs(BTC beta)>0.25`;
8. any required stress loses the mechanism or violates a hard risk/data gate;
9. reverse control beats the best directional candidate;
10. DSR probability `<0.95` using the complete global trial ledger;
11. data, PIT, accounting, integrity, reproduction, or audit is not PASS.

---

## 10. V6 hard gates

### FG0 — Data/universe

- seven traded symbols complete for the frozen effective window;
- BTC benchmark separately complete for context;
- funding settlement/publication coverage complete from the frozen runtime bundle;
- tick/step/min-notional metadata complete;
- no silent skip, replacement, or post-result universe/window change.

### FG1 — Point-in-time/leakage

- every funding input has publication timestamp `<= signal_ts`;
- feature bars complete before signal;
- `signal_ts < fill_ts`; execution bar excluded;
- warmup outside scored folds; explicit 24h purge/embargo evidenced;
- measured violation/missing counters are zero.

### FG2 — Accounting/integrity/reproduction

- continuous-capital accounting reconciles at fold and experiment levels;
- settlement funding, costs, terminal, and exposure artifacts present;
- hashes-last external verification clean;
- full-surface separate-process reproduction matches frozen tolerance;
- matrix/report/index/registry/transition reconcile and append-only is true.

### FG3 — Base mechanism

- after-cost PnL `>0`, net funding `>0`, position PF `>=1.10`;
- at least 2/3 folds positive in both PnL and funding;
- median continuous-capital fold return `>0`;
- at least 90 scored daily rebalances and 100 closed/terminal legs;
- top fold `<=50%`, top symbol `<=40%`.

### FG4 — Robustness/execution

- fee ×1.5, adverse two ticks, and extra 15m delay remain PnL-positive and
  funding-mechanism-positive;
- at least two adjacent lookbacks are positive;
- drop-one-symbol/drop-one-fold do not reveal prohibited single dependency;
- turnover/capacity contract passes.

### FG5 — Shared-capital risk

- gross `<=1.00`, `abs(net)<=0.10`, `abs(weight/symbol)<=0.20` after every event;
- risk mode active and reduce-only actions evidenced;
- no margin breach/liquidation;
- MDD `<=10%`, `abs(BTC beta)<=0.25`, top-symbol contribution `<=40%`.

### FG6 — Multiple testing

- global scored-trial ledger complete and append-only;
- DSR probability `>=0.95` using the frozen global trial count/distribution;
- PBO/CSCV only gives a verdict when prerequisites hold, otherwise explicit
  `NOT_ENOUGH_CONFIGURATIONS` and zero score contribution.

### FG7 — Independent science

- A7 audit PASS after code/result freeze;
- no unresolved HIGH/CRITICAL finding;
- trial budget and negative control verified;
- no S1/live access and no post-lock spec change.

All FG0–FG7 must PASS for eligibility.

---

## 11. V6 scorecard — 100 points

Score is considered only after all hard gates PASS. Missing values score zero.

### A. Data and PIT — 15

- 5: traded, benchmark, funding, and metadata coverage complete;
- 5: signal/fill/publication/warmup/purge evidence complete;
- 5: input identities and universe/window frozen before implementation/run.

### B. Accounting and costs — 15

- 5: continuous fold/experiment equity identities reconcile;
- 5: commissions, slippage, rejection, terminal decomposition reconcile;
- 5: settlement funding persists and reconciles by fold/symbol.

### C. Chronological edge — 20

- 5: after-cost total PnL positive;
- 5: PF `>=1.20`; 3 for `1.15–<1.20`; 1 for `1.10–<1.15`;
- 5: 3/3 positive folds; 3 for exactly 2/3;
- 5: daily Sharpe `>=1.00`; 3 for `0.75–<1.00`; 1 for `0.50–<0.75`.

### D. Risk/concentration — 15

- 5: MDD `<=6%`; 4 for `>6–8%`; 2 for `>8–10%`;
- 5: no gross/net/weight/margin violation;
- 5: top symbol `<=30%` and top fold `<=40%`; 3 when within hard limits.

### E. Robustness — 15

- 6: fee/two-tick/delay survive, two points each;
- 4: drop-one-symbol/fold pass, two points each;
- 3: turnover/capacity pass;
- 2: adjacent positive lookbacks.

### F. Multiple testing — 10

- 6: DSR `>=0.99`; 4 for `0.975–<0.99`; 2 for `0.95–<0.975`;
- 2: global ledger complete/append-only;
- 2: PBO `<=25%` when estimable; otherwise zero.

### G. Reproduction/audit — 10

- 5: full-surface reproduction all-match;
- 3: A7 audit PASS with no unresolved HIGH/CRITICAL;
- 2: all matrix/registry/status/transition artifacts reconcile.

```text
eligible = all(FG0..FG7 PASS) and score >= 75
tie_break = highest_DSR_then_lower_MDD_then_lower_turnover
max_locked_candidates = 1
```

---

## 12. Terminal outcomes and learning loop

Valid outcomes:

```text
V6P_FAIL_V6_BLOCKED
V6P_PASS_V6_PIPELINE_FAIL
V6P_PASS_V6_CANDIDATE_FAIL
V6P_PASS_V6_CANDIDATE_INCONCLUSIVE
V6P_PASS_V6_CANDIDATE_ELIGIBLE_PENDING_V7
V6P_PASS_V6_LOCK_ONE_FOR_FUTURE_S1
V6_TERMINAL_V7_NOT_AUTHORIZED
V6_TERMINAL_V7_SKIPPED_TIME_BUDGET
V6_TERMINAL_V7_PIPELINE_FAIL
V6_TERMINAL_V7_CANDIDATE_FAIL
V6_TERMINAL_V7_CANDIDATE_INCONCLUSIVE
V6_TERMINAL_V7_LOCK_ONE_FOR_FUTURE_S1
```

After V6, classify every failure as data, PIT, execution, accounting, cost,
capacity, risk, statistical power, multiple testing, or mechanism failure.
Write the facts into the hypothesis status and next-sprint backlog.

Do not run a v1.1 rescue on the same S0. V7 is a distinct family locked before
V6 results, not a rescue parameterization. The bounded loop is:

```text
idea -> lock -> implement -> multi-symbol WFA -> stresses -> score -> reproduce
-> independent audit -> reject/lock -> failure taxonomy -> next locked family
```

The loop ends after V7. There is no automatic V8, no dynamic parameter search,
and no new idea selected from partial PnL. A1 may record a future backlog but
must not execute it in this sprint.

Across V6 and V7, lock at most one candidate total. When V7 is authorized, an
eligible V6 result stays `ELIGIBLE_PENDING_V7`, not finally locked. If V7 cannot
run only because of the frozen time/resource budget, A1 may finalize the
eligible V6 result after all V6 evidence and audit are complete. Create only a
**future** S1 start timestamp. Do not backfill or inspect S1 in this sprint.
Later promotion still requires untouched Stage B, PF `>=1.15`, MDD `<=10%`,
stresses, and 6–8 weeks signal-only shadow.

---

## 13. Required artifacts

```text
research/audits/v6p/
  intake_snapshot.json
  v5r_reaudit_addendum.md
  v5r_reaudit_gates.json
  baseline_root.json
  a7_prelaunch_attestation.json
  final_tests.json
  gate_ledger_v6p.json
  challenge_memo_v6p.md
  scientific_audit_v6p.json
  v6p_transition.json

results/validation_v6p/<validation_id>/
results/reproduction_v6p/<verify_id>/
results/matrix/v6p_validation/

research/hypotheses/H-XSECT-FUNDING-CARRY-v1/
  hypothesis.md
  candidate.yaml
  status.yaml

results/portfolio_v6/<experiment_id>/
  launch_manifest.yaml
  frozen/
  signals.jsonl
  orders.jsonl
  positions.jsonl
  portfolio_ledger.jsonl
  funding_cashflows.jsonl
  terminal_positions.jsonl
  exposure_control.jsonl
  accounting_reconciliation.json
  commission_slippage.json
  canonical_metrics.json
  stress_report.json
  beta_report.json
  contribution_report.json
  dsr_pbo_report.json
  gate_result.json
  scorecard.json
  artifact_hashes.json

results/reproduction_v6/<verify_id>/
results/matrix/v6_xsect_funding_carry/
research/audits/v6/challenge_memo.md
research/audits/v6/scientific_audit.json
research/audits/v6/final_transition.json

research/control/twelve_hour_run/
  run_contract.json
  state.json
  heartbeat.json
  event_log.jsonl
  resource_samples.jsonl
  worker_registry.json
  shutdown_report.json

research/hypotheses/H-XSECT-FUNDING-PRICE-DIVERGENCE-v1/
  hypothesis.md
  candidate.yaml
  status.yaml

results/portfolio_v7/<experiment_id>/
  launch_manifest.yaml
  frozen/
  signals.jsonl
  orders.jsonl
  positions.jsonl
  portfolio_ledger.jsonl
  funding_cashflows.jsonl
  terminal_positions.jsonl
  exposure_control.jsonl
  accounting_reconciliation.json
  commission_slippage.json
  canonical_metrics.json
  stress_report.json
  beta_report.json
  contribution_report.json
  dsr_pbo_report.json
  gate_result.json
  scorecard.json
  artifact_hashes.json

results/reproduction_v7/<verify_id>/
results/matrix/v7_xsect_funding_price_divergence/
research/audits/v7/v7_authorization.json
research/audits/v7/challenge_memo.md
research/audits/v7/scientific_audit.json
research/audits/v7/final_transition.json
research/wayfinder/evidence/sprint-v6p-v6-v7-master-20260824.md
CONTINUE.md
```

Results may be gitignored, but final tracked evidence must contain their exact
paths, counts, hashes, commands, exit codes, and verdicts. Do not claim an
artifact exists without checking the filesystem.

---

## 14. Definition of done

The sprint ends only when:

1. V5R re-audit addendum records N01–N15 without changing old evidence;
2. all current code changes are scoped, reviewed, tested, and integrated;
3. V6P has exactly 20 machine-readable gate rows;
4. A7 independently signs V6P PASS/FAIL/BLOCKED;
5. V6 starts only from `V6P_PASS_V6_AUTHORIZED`;
6. if authorized, exactly four V6 scored launches are ledgered;
7. all V6 gates and scorecards are measured from complete artifacts;
8. full reproductions and A7 audit are complete or explicitly block promotion;
9. no S1/live access occurs;
10. final report separates engineering, scientific audit, family, candidate,
    S1, and live-money verdicts;
11. `CONTINUE.md` reflects final current state, not intended work;
12. V7 starts only from a valid V6 terminal state plus all V7 authorization
    checks and executes exactly four scored launches at most;
13. the global scored-trial ledger includes every V6/V7 attempt that saw scored
    data, including aborted or failed attempts;
14. the controller reaches a terminal state, leaves no orphan worker, and writes
    a shutdown report before the 12-hour deadline;
15. Git status and untracked result locations are explicitly handed off.

Progress is reported as gate counts, not intuition:

```text
V6P x/20 PASS; V6 authorization PASS/BLOCKED
V6 FG x/8 PASS per candidate; trials used y/4
V7 authorization x/12 PASS; V7 FG x/8 PASS per candidate; trials used z/4
global new scored trials used n/8; wall clock h/12
```

---

## 15. Unattended loop controller and 12-hour safety contract

The coordinator must implement or reuse one deterministic supervisor. The
supervisor controls phase transitions; conversational agent judgment does not.
Before any mutation it writes `research/control/twelve_hour_run/run_contract.json`
with the start time, hard deadline, code/data/spec hashes, trial budgets,
resource limits, exact phase graph, and stop reasons.

### 15.1. Finite-state machine

```text
INTAKE
  -> V6P_REPAIR
  -> V6P_VALIDATION
  -> V6P_AUDIT
  -> V6P_PASS | TERMINAL_V6P_FAIL

V6P_PASS
  -> V6_SPEC_AND_V7_SPEC_LOCKED
  -> V6_BASE
  -> V6_STRESS_REPRO
  -> V6_AUDIT
  -> V6_TERMINAL

V6_TERMINAL
  -> V7_AUTHORIZATION
  -> V7_BASE | TERMINAL_V7_NOT_AUTHORIZED
  -> V7_STRESS_REPRO
  -> V7_AUDIT
  -> V7_TERMINAL
  -> FINAL_RECONCILIATION
  -> SHUTDOWN_COMPLETE
```

Only A1 writes `state.json`. Every transition includes previous/new state,
UTC timestamp, Git SHA, required-input hashes, gate artifact, actor, and reason.
There is no backward transition and no transition whose required gate is
missing. Every command has an experiment ID, owner, output root, timeout,
expected artifacts, exit code, and final digest.

### 15.2. Resume and idempotency

1. On restart, read the frozen run contract and state before launching work.
2. Verify every completed-state artifact and hash; resume the first incomplete
   state only. Never rerun a valid completed trial.
3. Use exclusive per-experiment lock files and a worker registry containing
   exact child PIDs. Never use broad `pkill` or process-name matching.
4. Output roots are append-only. An incomplete root is marked `ABORTED`; it is
   never cleaned and reused for another experiment.
5. If scored data was opened or any score/metric was emitted, the attempt counts
   in the global trial ledger even when it crashes.
6. One infrastructure retry is allowed only with a new `-RETRY1` ID and a
   machine-recorded failure reason. No second retry.
7. No retry is allowed for negative PnL, a failed gate, or an adverse audit.

### 15.3. Blindness and anti-overfitting

1. Freeze and hash both V6 and V7 specifications after V6P PASS and before the
   first V6 scored launch.
2. Workers may not stream PnL to agents. A1 exposes results only after the whole
   family population is frozen.
3. V6 results may authorize or block V7 operationally, but may not change V7's
   universe, features, lookbacks, thresholds, costs, folds, gates, or score.
4. Maximum new scored attempts for the entire run is eight: four V6 plus four
   V7. Diagnostics, stresses, and exact reproductions are linked non-scored
   jobs. No Bayesian/grid/random/LLM-generated parameter expansion is allowed.
5. Never change the S0 start/end or symbol universe after results appear.
6. Never interpret repeated use of S0 as untouched OOS evidence.

### 15.4. Resource, heartbeat, and deadline policy

1. Record CPU, available RAM, swap, load, free disk, and active worker count at
   preflight and every five minutes. Write a heartbeat even when no phase ends.
2. Default to two heavy workers. Increase to four only when free RAM remains at
   least 30%, swap growth is zero, disk has at least 20 GiB free, and a measured
   pilot shows throughput improvement. Reduce concurrency when any condition
   fails.
3. Stop launching new jobs if free disk is below 10 GiB, the test suite fails,
   hashes drift, an orphan/duplicate worker exists, or A7 raises HIGH/CRITICAL.
4. Each heavy command has a frozen timeout no greater than 90 minutes. On
   timeout, signal only its recorded child process group with `SIGTERM`, allow
   30 seconds, then stop that exact group if necessary; record the event.
5. At T-minus 45 minutes, launch no new base/stress/reproduction job. At
   T-minus 15 minutes, checkpoint, finalize the current known state, write
   transition/report artifacts, and stop all owned workers gracefully.
6. Check `research/control/STOP_AFTER_CURRENT_STEP` before every new command. If
   present, finish the current atomic write, reconcile, and shut down.
7. Never wait silently: `heartbeat.json` identifies phase, progress, latest
   completed command, active exact PIDs, resource status, blocker, and ETA.

Time exhaustion produces a truthful `SKIPPED_TIME_BUDGET` or `INCOMPLETE`; it
never converts a missing test, reproduction, stress, or audit into PASS.
Early completion produces `SHUTDOWN_COMPLETE`; unused time never authorizes an
extra hypothesis, trial, retry, or parameter search.

---

## 16. V7 hypothesis — pre-register before V6 results

### 16.1. Selection rationale and novelty check

```text
H-XSECT-FUNDING-PRICE-DIVERGENCE-v1
```

The existing catalog already contains scored/diagnostic pure cross-sectional
momentum work; `H-VOLCOMP-BRKOUT-v1` and `H-FUNDCROWD-MR-v2` are rejected, and
`H-XSECT-REVERSAL-v1` is draft-only/data-blocked with zero trials. V7 must not
rerun or merely rename those exact specifications. This V7 hypothesis asks a
different, narrower question:
does a market-neutral portfolio improve when low-funding assets must also show
relative price strength and high-funding assets must also show relative price
weakness?

This is an economic prior, not an established edge. It can fail because carry
and price continuation may not coexist, trading costs may dominate, or the
signal may be only a repackaged momentum/carry exposure. A catalog novelty
check must be frozen with the V7 spec; a material duplicate blocks V7.

### 16.2. Frozen V7 contract

```yaml
hypothesis_id: H-XSECT-FUNDING-PRICE-DIVERGENCE-v1
family: cross_sectional_funding_price_divergence
stage: S0_EXPLORATORY
traded_universe: [ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, LINKUSDT, ADAUSDT]
benchmark_context: BTCUSDT
signal_clock: daily_00_00_utc
funding_feature: trailing_mean_of_published_settled_funding_only
funding_lookback_days: 3
price_feature: trailing_close_to_close_return_using_completed_bars_only
price_lookback_days: [1, 3, 7]
cross_sectional_score: percentile_rank(price_return) - percentile_rank(funding)
long_rule: top_2_score
short_rule: bottom_2_score
rebalance: 24h
folds: chronological_3fold
purge_embargo: 24h
target_gross: 0.80
hard_gross_cap: 1.00
hard_abs_net_cap: 0.10
max_abs_weight_per_symbol: 0.20
trial_budget:
  scored_candidates: 3
  negative_controls: 1
negative_control: reverse_score_sides_at_price_lookback_3d
```

Freeze the same data, accounting, execution, latency, terminal, risk, metric,
fold, DSR, cost, and artifact contracts as V6. The only candidate dimension is
the declared price lookback. Do not add an OI, volatility, regime, liquidity,
trend, symbol-specific, or threshold filter.

### 16.3. Exactly four V7 scored launches

```text
XSECT-FUND-PRICE-DIV-1D
XSECT-FUND-PRICE-DIV-3D
XSECT-FUND-PRICE-DIV-7D
XSECT-FUND-PRICE-DIV-REVERSE-3D-CONTROL
```

There is no fifth launch. V7 shares the global multiple-testing ledger with all
prior scored work, including the four V6 attempts and any scored aborted retry.

---

## 17. V7 authorization, gates, and score

### 17.1. Twelve authorization gates — all must PASS

```text
V7-A01 v6p_transition_is_exactly_v6p_pass_v6_authorized
V7-A02 v6_reached_terminal_with_pipeline_data_pit_accounting_integrity_pass
V7-A03 v7_spec_and_novelty_check_hashed_before_first_v6_scored_launch
V7-A04 v7_code_matches_spec_and_has_no_post_v6_result_spec_diff
V7-A05 v6_global_trial_ledger_and_artifact_population_reconcile
V7-A06 no_unresolved_high_critical_from_v6_audit
V7-A07 full_tests_pass_on_clean_committed_v7_launch_head
V7-A08 a7_prelaunch_attestation_committed_before_v7_workers
V7-A09 fresh_nonoverwriting_output_roots_and_unique_trial_ids
V7-A10 resource_preflight_pass_and_at_least_180_minutes_remain
V7-A11 no_s1_no_live_no_window_or_universe_change
V7-A12 total_new_scored_attempt_budget_can_remain_at_or_below_eight
```

V6 candidate failure is allowed only when the failure is a measured mechanism,
cost, robustness, power, or multiple-testing failure on an otherwise valid
pipeline. Any V6 data/PIT/accounting/integrity/reproduction/audit failure blocks
V7. If fewer than 180 minutes remain, record
`V6_TERMINAL_V7_SKIPPED_TIME_BUDGET` and proceed to final reconciliation.

### 17.2. V7 hard gates

Reuse V6 FG0, FG1, FG2, FG4, FG5, FG6, and FG7 without relaxation. Replace only
FG3 with the following mechanism gate:

```text
FG3-V7
- after-cost total PnL > 0;
- position PF >= 1.10;
- net funding cashflow > 0 and future price PnL > 0;
- at least 2/3 folds have positive total PnL;
- at least 2/3 folds have positive funding contribution;
- median continuous-capital fold return > 0;
- at least 90 scored daily rebalances and 100 closed/terminal legs;
- top fold <= 50% and top symbol <= 40% of positive PnL;
- at least two adjacent price lookbacks are positive;
- reverse control does not beat the best directional candidate.
```

Every required stress must preserve positive total PnL, positive funding, all
risk limits, and valid accounting. A result dominated by only price momentum or
only funding carry is recorded as mechanism-inconclusive, never relabeled as a
new edge.

Use the same 100-point scorecard in Section 11 after all hard gates pass. For V7
the two robustness points for adjacent lookbacks refer to price lookbacks; the
chronological edge and accounting sections use total PnL while the mechanism
memo separately decomposes price and funding. Eligibility remains all eight
hard gates PASS and score `>=75`.

---

## 18. Cross-family decision and bounded learning

1. A1 freezes all V6/V7 candidates before exposing the family comparison.
2. A7 audits the full population, including failed and aborted trials.
3. If neither family has an eligible candidate, lock none.
4. If only one family has an eligible candidate, it is the sole provisional S1
   candidate.
5. If both have eligible candidates, choose one by highest DSR, then lower MDD,
   then lower turnover. No subjective override and no portfolio combination.
6. Write a cross-family table with total/price/funding PnL, PF, continuous fold
   returns, MDD, beta, concentration, stresses, DSR/PBO, score, reproduction,
   audit, and rejection reason for every trial.
7. Classify each failure into data, PIT, execution, accounting, cost, capacity,
   risk, mechanism, robustness, concentration, statistical power, multiple
   testing, reproduction, or audit.
8. Agents may use those failure labels to write future hypothesis cards. They
   may not implement, score, or run them in this sprint.
9. Stop after the V7 terminal transition. There is no automatic V8.

This is how the loop “learns”: it improves the next written question and the
pipeline evidence, not the current strategy's parameters after observing PnL.

---

## 19. Final unattended handoff

Before shutdown, A1 must produce one final report that states, separately:

```text
V6P_VERDICT
V6_PIPELINE_VERDICT
V6_FAMILY_VERDICT
V6_BEST_CANDIDATE_OR_NONE
V7_AUTHORIZATION_VERDICT
V7_PIPELINE_VERDICT
V7_FAMILY_VERDICT
V7_BEST_CANDIDATE_OR_NONE
CROSS_FAMILY_LOCKED_CANDIDATE_OR_NONE
NEW_SCORED_TRIALS_USED_OUT_OF_8
GLOBAL_LEDGER_COUNT
S1_STATUS
LIVE_MONEY_STATUS
FINAL_HEAD_AND_WORKTREE_STATUS
ACTIVE_OWNED_WORKERS
UNRESOLVED_FINDINGS
NEXT_SAFE_ACTION
```

The report must distinguish `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`,
`INCONCLUSIVE`, and `SKIPPED_TIME_BUDGET`. `CONTINUE.md` must point to the exact
state, transition, report, hashes, incomplete work, exact safe resume command,
and confirm whether any owned worker remains. Do not push, open a PR, start S1,
or enable live execution.

---

## 20. Orca implementation prompt

```text
You are A1, coordinator and final integrator for:
/Users/hoangminhlong/my-quantitative

The owner will leave this machine unattended for at most 12 hours. Read PLAN.md
completely before acting. It is the complete execution contract. Implement its
finite-state supervisor, deadlines, trial budgets, scientific gates, and
shutdown handoff exactly. Twelve hours is a maximum, not a requirement: finish
and shut down as soon as all required terminal artifacts exist. Time pressure
never waives a gate, and unused time never permits extra trials.

CONTINUE.md and sprint-v5r-v6-master-20260824.md are historical handoffs whose
safe V6-blocked verdict remains valid, but their claim that V5R had only two
failed gates is not accepted without the V6P re-audit.

Treat all V1–V5R artifacts, transitions, reports, and both old
my-quantitative-wt locations as read-only. Never rewrite the old V5R ledger or
audit. Record corrections only under research/audits/v6p.

Use Orca to launch seven bounded roles:
A1 coordinator/integrator;
A2 provenance/baseline;
A3 data/funding PIT and XG0;
A4 engine/accounting/risk/continuous WFA;
A5 measured gates/stress/reproduction/reconciliation;
A6 V6/V7 hypothesis specifications and implementations after V6P authorization;
V7 scored execution remains inactive until V7 authorization;
A7 independent scientific auditor.

Use R1–R4 only as frozen-command workers with isolated output roots and registry
shards. Do not create overlapping coding owners. Start no more than two heavy
runs until resource preflight passes. A1 alone writes shared state/ledger/index
files. Every coding role uses a unique branch/worktree from the same bootstrap
commit and an explicit file allowlist.

Begin read-only. Confirm HEAD, worktree state, current tests, V6/V7 absence, raw
artifacts, hypothesis catalog, and findings N01–N15. A7 must independently
challenge them. Create a tracked V5R re-audit addendum; do not alter historical
evidence. Create research/control/twelve_hour_run/run_contract.json and state.json
before repair work, with an absolute start/deadline and the Section 15 state
graph. Heartbeat and resource samples are required every five minutes.

Run A2–A5 repairs in parallel with explicit file allowlists. Required repairs:
- committed clean baseline and committed A7 attestation before launch;
- real bar/benchmark/funding/metadata coverage and correct reason codes;
- one-pass three-fold continuous capital and continuous MDD;
- active RISK_MODE_V1 with every-bar caps;
- complete funding/cost/terminal/exposure/accounting artifacts;
- measured XG1 with no scored boolean fallback;
- unconditional family-aware stresses even when base edge fails;
- reconciliation that fails on append-only false or stale roots;
- full-surface reproduction, not only orders/positions and four metrics.

Use .venv/bin/python. Preserve user work. Never use git add -A, destructive
reset/clean, S1, live credentials, or live execution.

After integration, run the three V6P validation cases in fresh namespaces and
evaluate V6P-C01..C20. A7 must verify the committed pre-launch baseline before
workers and audit the frozen population afterward.

If any V6P gate is not PASS, write V6P_FAIL_V6_BLOCKED and stop. Do not implement
or run V6/V7. Reconcile artifacts, update CONTINUE.md, and shut down cleanly.

Only after committed V6P_PASS_V6_AUTHORIZED may A6 freeze and hash both
H-XSECT-FUNDING-CARRY-v1 and
H-XSECT-FUNDING-PRICE-DIVERGENCE-v1. Freeze both specifications and the V7
catalog-novelty check before the first V6 scored launch. Implement V6 and run
exactly four scored experiments: 1D, 3D, 7D, and reverse-3D control.

Run hard gates FG0–FG7 before the 100-point score. Execute all stresses and
full reproductions even when the base edge fails. A7 receives the entire frozen
V6 population and may write audit files only. Produce a terminal V6 pipeline and
family verdict; do not tune or rescue V6.

Then evaluate V7-A01..V7-A12. Start V7 only if all 12 PASS, at least 180 minutes
remain, V6's pipeline/data/PIT/accounting/integrity/reproduction/audit surfaces
are valid, no HIGH/CRITICAL remains, and the global scored-attempt budget can
stay <=8. A V6 mechanism/cost/robustness/power failure may proceed; a pipeline
or audit failure may not.

If authorized, implement the already-hashed V7 specification with no result-
driven edit. Run exactly four scored experiments: price lookback 1D, 3D, 7D,
and reverse-3D control, with funding lookback fixed at 3D. Apply the inherited
hard gates plus FG3-V7, all stresses, full reproduction, DSR/PBO, scoring, and
A7 audit. No fifth trial, search expansion, changed filter, changed window,
changed universe, or retry for bad performance.

Across V6 and V7, every attempt that opens scored data or emits a metric enters
the append-only global ledger. Maximum eight new scored attempts total. Freeze
each family population before exposing results. If both families produce an
eligible candidate, select at most one by highest DSR, then lower MDD, then
lower turnover. Never read/backfill S1 or combine the two portfolios.

Resume idempotently from state.json. Never overwrite completed roots. Use exact
recorded child PIDs, never broad pkill. Permit at most one infrastructure retry
under a new RETRY1 ID. At T-minus 45 minutes launch no new job; at T-minus 15
minutes checkpoint and finalize. Stop early on hash drift, failed tests, disk
below 10 GiB, duplicate/orphan worker, or unresolved HIGH/CRITICAL. A truthful
FAIL/BLOCKED/INCONCLUSIVE/SKIPPED_TIME_BUDGET is a valid outcome.

At every phase boundary report: role status, owned files, commits, tests,
commands/exit codes, artifact paths/hashes, gate counts, resource state,
findings, blockers, and next transition. A truthful FAIL is valid; never create
PASS to stay on schedule.

Finish with all V6P/V6/V7 transitions, audits, full global reconciliation,
sprint-v6p-v6-v7-master-20260824.md, shutdown_report.json, and a rewritten
CONTINUE.md that contains the exact safe resume point. Verify no owned worker is
left running. Do not push, open a PR, start V8, start S1, or change remote state.
```
