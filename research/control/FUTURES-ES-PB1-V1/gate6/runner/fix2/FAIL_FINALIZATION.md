# FAIL RECORD — scored_executor finalization false-success (reproduced BEFORE fix)

- Reproduced 2026-10-05 by the controller THROUGH the production path
  (`scored_executor.run_scored_execution` over the regenerated synthetic
  sandbox; faults injected at the boundary exactly as the independent
  audit did; no real lock/ledger/GO/panel; script preserved in
  fix2/repro_finalization_bugs.py):
  - **BUG 1 — lock release raises**: `handle.release()` raising after a
    fully successful computation ⇒ **exit_code 0, terminal_state
    EXECUTION_COMPLETE, lock_released_status "FINISHED"** while
    `lock_release_error` sits in the same terminal dict. False success;
    the status is written OUTSIDE the try (executor ~L789-797) merely
    because release was CALLED.
  - **BUG 2 — terminal handoff write raises**: `_write_atomic(
    terminal_handoff.json)` raising OSError ⇒ **exit_code 0,
    EXECUTION_COMPLETE** with only `terminal_handoff_error` recorded
    (~L801-803). False success; the run claims completion without its
    terminal artifact.
  - Same defect class for the ledger-summary failure path (~L770-773:
    error recorded, exit unchanged).
- **Claim withdrawal (scoped)**: the "fail-closed toàn tuyến / exit 0
  impossible for incomplete execution" claim (EXEC-BUILD report +
  verifier E1) is WITHDRAWN for the FINALIZATION dimension: computation
  completeness was proven, finalization failure propagation was NOT.
  Everything else those verdicts covered stands.
- Fix law (from the owner dispatch, binding): finalization errors
  (ledger summary / lock release / terminal handoff) can never keep a
  success verdict or exit 0; computation-complete vs finalization-failed
  must be distinguished; lock_released_status only from measured
  evidence (canonical inspect after a release failure); release raising
  ⇒ re-check canonical lock state, fail closed, keep evidence, never
  force-take or kill workers; handoff write failure ⇒ non-zero exit +
  diagnostics, never claim the artifact exists; cleanup exceptions must
  not mask the original error nor skip remaining cleanup; ledger bytes /
  observed denominator / computed results preserved (no recompute).
  Terminal-state names checked against plan/SPEC; any authority gap ⇒
  decision packet, never self-approved.

— End FAIL record. NO fix in this commit.
