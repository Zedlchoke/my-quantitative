# FINALIZE_FIX_REPORT — scored_executor finalization fail-closed (controller-completed deliverable)

- Provenance note: lane FINALIZE-FIX went inactive mid-wave; the executor
  fix, F-suite, and EXEC_BUILD_REPORT D-7 entry were complete in the
  worktree; the controller verified them, corrected one stale test
  baseline (F10, disclosed below), and wrote this report + the handoff.
  The lane's code was not modified by the controller except: nothing.
- FAIL-before-fix: fix2/FAIL_FINALIZATION.md committed at c17ab2bf
  (reproduction through the production path: BUG1 release-raises ⇒ exit 0
  + EXECUTION_COMPLETE + lock_released_status FINISHED; BUG2 handoff
  write-raises ⇒ exit 0 + EXECUTION_COMPLETE). The scoped claim
  "fail-closed toàn tuyến" was withdrawn there for the finalization
  dimension.
- The fix (scored_executor.py finally block, diff disclosed in the wave
  commit): per-stage cleanup tries with `finalization_failures[]`
  collection (no masking, no skipped steps); ledger summary failure ⇒
  failure; lock release RAISE ⇒ `UNVERIFIED_RELEASE_RAISED` +
  canonical `heavy_lock.inspect()` evidence recorded PRE-restore (same
  runtime, sandbox-safe), never a released claim, never force-unlock /
  kill / delete; runtime restore own-try; handoff write failure ⇒
  failure + `terminal_handoff_error`, no path claim, fallback
  `terminal_handoff_ERROR.json` best-effort; **terminal state
  FINALIZATION_FAILURE + exit 4** whenever any finalization failure
  occurred (computation_complete recorded separately); ledger bytes /
  observed denominator / computed results untouched (no recompute).
- Terminal vocabulary: **D-7** [IMPLEMENTED-DEFAULT-PENDING-RATIFICATION]
  recorded in EXEC_BUILD_REPORT.md §7 (single class state + per-stage
  list; exit 4 distinct from 3; SPEC §9 `*_BLOCKED_<reason>` is the A7
  layer, not selectable here). Owner ratification REQUIRED before GO.
- After-fix reproduction (fix2/repro_after_fix_output.json): BUG1 ⇒
  exit 4 / FINALIZATION_FAILURE / UNVERIFIED_RELEASE_RAISED (no FINISHED);
  BUG2 ⇒ exit 4 / FINALIZATION_FAILURE / no handoff-path claim.
- Test matrix (production path, sandbox, boundary fault injection):
  F01 happy unchanged PASS · F02 handoff-write fail-closed PASS · F03
  release-raises + inspect evidence PASS · F04 release-raises-after-real-
  unlock (inspect shows FREE; still failure) PASS · F05 ledger-summary
  failure rows-stand PASS · F06 compute+cleanup both errors no-masking
  PASS · F07 ledgers verify + bytes prefix-preserved after failures PASS
  · F08 retry after finalization failure (no recompute of terminals)
  PASS · F09 existing suites re-run PASS · F10 production-default safety
  PASS after baseline correction: the lane's `assertEqual(hits, 2)` was
  its own wrong count (pre-fix code ALSO has 3 RUNTIME_DIRNAME Attribute
  nodes: read + 2 assignment targets, verified vs c17ab2bf); corrected
  to 3 with the explanation in-test; the sandbox-containment property
  itself passed throughout.
- Regression: test_execution_path.py + test_runner_refusals.py = **24/24
  passed** (133s) after the fix.
- No real outcomes / lock / ledger / GO consumed; frozen laws untouched;
  D-1..D-7 all unratified.

— End FINALIZE_FIX_REPORT.

## F1/F2 REMEDIATION (append-only, 2026-10-05, post-verifier)

- **F1 HIGH (GO-blocking) CLOSED**: verifier caught that LAUNCH_CONTRACT
  v2_1 new_pins pinned the PRE-fix executor/runner bytes and that R4
  never verified addendum pins (silent-drift hole). Remediated:
  (1) `operative_pins()` law — R4 + sandbox-path resolution + post-acquire
  TOCTOU all consume base pins + EVERY addendum's new_pins, deduped by
  ARTIFACT PATH with the LATER addendum winning; superseded rows demoted
  HISTORY_SUPERSEDED (recorded, never live-checked — name aliases like
  scored_runner_v2_1 vs scored_runner are the same file); (2) v2.2
  addendum re-pins the changed bytes (executor 2e3c4387, runner 58217ad4)
  + exit-code table v2.2 incl. code 4; (3) production resolution: pins
  without a DEFAULT_RELS entry resolve via the pin's own contract path
  (worktree-relative) — no fixture literals in production source (T8
  property re-proven).
- **F2 LOW CLOSED**: handoff_FINALIZE-FIX.json completed to full schema
  (tests with exit_code/log_digest, recommended_next_action, empty
  authority_claims).
- Suites on the remediated state: refusals **14/14** (4.56s), execution
  T1-T10 **10/10** (96.8s), finalization F01-F10 **10/10** (1361s).
- D-7 + the v2.2 re-pins ride the same owner ratification as D-1..D-6.

— End remediation addendum.
