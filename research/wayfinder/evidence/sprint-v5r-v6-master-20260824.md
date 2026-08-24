# Sprint V5R→V6 Master Evidence Report — 2026-08-24

```text
ENGINEERING_VERDICT          = PASS (pipeline integrity restored and proven end-to-end)
SCIENTIFIC_AUDIT_VERDICT     = PASS (A6, post-freeze, full population; 2 MED findings recorded)
V5_COMPLETION_COUNT          = 5/26 PASS; 4 FAIL; 17 NOT_TESTED
V5_FAILED_GATES              = C02 (provenance mutation), C19 (diag recalc invalid),
                               C21 (reconciliation PARTIAL), C25 (run.log hash mismatches)
V5_BLOCKED_GATES             = none
V5R_COMPLETION_COUNT         = 16/18 PASS; 2 FAIL; 0 BLOCKED
V5R_FAILED_GATES             = R06 (data coverage/funding cadence below declared),
                               R12 (stress matrix skipped behind base-edge gate)
V6_TRANSITION                = V5_FAIL_V6_BLOCKED  (terminal)
V6_ENGINEERING_VERDICT       = NOT_RUN (intentionally blocked)
V6_FAMILY_VERDICT            = NOT_RUN (H-XSECT-FUNDING-CARRY-v1 never pre-registered or implemented)
GLOBAL_SCORED_TRIAL_COUNT    = unchanged (registry snapshot frozen in baseline;
                               diagnostics are DIAGNOSTIC_RECALC, trial_count_increment=false)
LOCKED_CANDIDATE_OR_NONE     = NONE
S1_STATUS                    = NOT_STARTED
LIVE_MONEY_STATUS            = UNCHANGED_DISABLED
```

## 1. Found vs claimed

| Prior handoff claimed | This sprint measured |
|---|---|
| V5-C02 six mutated files, cause = test fixture | PROVEN: stale default-arg binding (`stage_a_root=DEFAULT` bound at def time) let `test_matrix_runner` write the real provenance zone of EXP-0001/0002. Mechanism demo + pre/post-test recheck evidence committed. |
| Exact recovery might be possible | EXHAUSTIVELY NOT FOUND: 5,726 files hashed across current repo + all 18 old worktrees, 445 git blobs (full history), no archives → 0/6 byte-identical. |
| 557 tests pass | 581 pass at final code state (suite grew with new negative/isolation/finalization tests), exit 0, 0 xfail. |
| Diagnostics "4/4 complete" | Legacy DIAG-V5 invalid as scientific evidence: run.log hash mismatches 4/4, reconciliation PARTIAL, source trials quarantined. |
| baseline_v5.json "474 passed" | Historical snapshot at earlier commit e00c535; superseded by measured counts above (not a contradiction). |

## 2. Root cause & blast radius of the provenance mutation

Cause: Python default arguments bind once at function definition; `run_matrix(..., stage_a_root=DEFAULT_V3_STAGE_A_ROOT)` therefore ignored any test-time monkeypatch and wrote `launch_manifest.yaml`, `execution_evidence.json`, and frozen snapshots into the real zone on every test run. Blast radius: exactly EXP-20260824-0001/0002 provenance trios plus their derived matrix cells (`usable_for_scientific_claims=false`; forensic use only). Quarantine manifest: `research/audits/v5r/quarantine_manifest.json`. Nothing was deleted or moved.

## 3. Exact-byte recovery: attempted and honestly failed

Bounded single search per PLAN §7-C2 across git objects/history, both old-worktree locations, local archives, artifact stores. Outcome NOT_FOUND for all six files ⇒ per §7-C3 legacy V5 is permanently **V5_FAIL**; no baseline reset, no guessed reconstruction.

## 4. What the defensive patch prevents

Late-bound `stage_a_root=None` + autouse fixture redirect ⇒ zero test writes into immutable zones (pre/post-test 1474-path rechecks identical). Committed as scoped fix `2cadb25`.

## 5. Trustworthiness of existing V5 diagnostics

Not trustworthy as validation evidence (quarantined provenance + C19/C21/C25 integrity failures); retained for forensic debugging. Old-vs-new economics comparison published under the clean namespace: `results/matrix/v4_recalc_diagnostic_v5r/old_new_comparison.json`.

## 6. Fresh diagnostics/reproductions (clean lineage, allowed)

Four frozen DIAGNOSTIC_RECALC runs executed after A6 pre-launch verification of the frozen baseline (HEAD 66917f7): 3D −8,239 / 7D +9,542 (PF 1.048) / 14D −8,158 / reverse-control −27,334. All manifests verify CLEAN via external reader; four independent-process reproductions all_match. Consistent with original V4 rejections — no candidate exists.

## 7. Failed/blocked gates without euphemism

Legacy: C02/C19/C21/C25 FAIL; 17 gates NOT_TESTED because no untainted end-to-end population existed to measure them — missing evidence was not converted into PASS.
V5R: **R06 FAIL** — XG0 measured `coverage_below_declared` + `funding_coverage_insufficient` on 4/4 fresh runs (A6 confirmed the coverage shortfall substantiates this independently). **R12 FAIL** — fee/two-tick/delay/drop-one stress matrix did not execute because the runner gates stresses behind a passing base edge; the plan requires unconditional execution. A6 audit added: gross exposure >1.00 semantics finding (MED), XG0 funding-reason vs data-manifest conflict (MED), universe-count and purge/embargo declaration gaps (LOW).

## 8–10. Transition, learning loop, next action

No authorization path exists: legacy FAIL and V5R FAIL ⇒ **V5_FAIL_V6_BLOCKED**. V6 directories are intentionally absent. Failure taxonomy for the backlog: data-coverage limitation (R06) + execution-diagnostic design defect (stress gating, R12) + no momentum edge in window. Next actions for the owner:
1. Fix data coverage/funding cadence to match the declared window (or freeze a smaller honest window) before any future lineage.
2. Make stresses/drop-one unconditional in `portfolio_runner`.
3. Decide on the two MED findings from `challenge_memo_v5r.md`.
4. Only then re-open a fresh validation lineage; do not reuse V5R verdicts.

Machine-readable artifacts: `research/audits/v5r/{v5_legacy_transition,v5r_transition,master_transition,gate_ledger_v5_legacy,gate_ledger_v5r}.json`, `scientific_audit_v5r.json`, `quarantine_manifest.json`, `new_lineage_baseline.json`.
