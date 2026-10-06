# FIX_LOG — exec lane, FUTURES-5SYM-PRESCORED-20261005

Scope: defects FIXED in `exec/scored_runner_v2.py` relative to the upstream
FUTURES-ES-PB1-V1 runner (extract `exec/_upstream_scored_runner.py`,
FAIL-record revision c17ab2bf), plus defects found and fixed while building
v2 itself. Every entry carries its test evidence (all tests drive the REAL
CLI via subprocess over sandbox temp dirs).

## 1. Upstream BUG1-class — lock-release failure => false success (FIXED)

- Upstream: `handle.release()` raising after a fully successful computation
  gave exit 0 + `EXECUTION_COMPLETE` + `lock_released_status "FINISHED"`
  (status written outside the try merely because release was CALLED).
- v2: release is ALWAYS attempted (success, fault, or exception paths);
  a raising release sets `lock_released_status = "RELEASE_RAISED"`, records
  a finalization failure, and the terminal status is computed AFTER release
  from measured evidence — exit 3, `FAILED_LOCK_RELEASE`. Evidence is
  preserved (the RUNNING row stays; no force-unlock, no kill, no delete).
- Proof: `test_lock.py::test_T11_fail_release_bug1_proof` — `--test-fault
  fail_release` => exit 3, `RELEASE_RAISED`, `computation_complete: true`
  yet NO success token in any output and NO handoff artifact.

## 2. Upstream BUG2-class — terminal handoff write failure => false success (FIXED)

- Upstream: `_write_atomic(terminal_handoff.json)` raising OSError gave
  exit 0 + `EXECUTION_COMPLETE` without the terminal artifact; same class
  for the ledger-summary path (error recorded, exit unchanged).
- v2: handoff write, ledger summary, publication and FINAL_STATUS are all
  guarded; any failure forces FAILED + non-zero; the handoff is written
  only AFTER the lock release measured `RELEASED`; the success token
  appears in an output only when EVERY mandatory step (incl. final-status
  write) is measured done.
- Proof: `test_execution.py::test_T12_fail_handoff_write_bugs2_class`
  (exit 3, `FAILED_HANDOFF_WRITE`, no handoff, no success token,
  publication stands); `test_fail_ledger_summary_bugs2_sibling`;
  `test_T13_fail_publication_keeps_observed` (observed denominator kept in
  the append-only ledger, `PUBLICATION_QUARANTINE.json` written, published
  withheld).

## 3. Defects found in v2 during this build (caught by the suite, fixed)

1. **Mandatory-step chicken-and-egg (2x).** The first `terminal_state()`
   required `handoff_write`/`final_status_write` to already be done — so
   success was unreachable. Fixed with `core_complete()` (pre-handoff
   precondition) and `terminal_state(ignore_missing=("final_status_write",))`
   (the final-status write's OWN failure path forces FAILED/non-zero).
   Evidence: first pytest passes showed `FAILED` with empty failures and
   all-but-one mandatory steps true across the whole suite.
2. **Success token inside an explanatory field.** FINAL_STATUS carried a
   `terminal_artifact_rule` string that itself contained the literal
   `EXECUTION_COMPLETE` on FAILED runs — violating the success-token law
   by construction. Removed the field; the law lives in RUNNER_SPEC_V2.
   Evidence: refusal tests grepping the FINAL_STATUS text failed in early
   passes, pass afterwards.
3. **Refusal-record isolation leak (REAL-GOVERNANCE WRITE, caught by the
   suite's own T16 snapshot guard).** `refusal_record.json` was derived
   from the FINAL_STATUS parent dir: with `--final-status-out` under the
   real governance dir (T16d), the runner wrote `refusal_record.json` INTO
   `/Users/hoangminhlong/.my-quantitative-governance/`. The session-scope
   snapshot flagged the change immediately. Fix: when that parent resolves
   under the real governance dir, the refusal record (and the emergency
   FINAL_STATUS) fall back into the validated sandbox run dir; the real
   dir is never written by any path. Remediation: the created file was
   MINE (created by an earlier suite pass; content = my runner's refusal
   record; the real dir had only `heavy_runtime/` + `mdp_dvc_remote/`
   before this session) — deleted, listing restored and re-verified.
   Evidence: `test_isolation.py::test_T16d_final_status_into_real_dir_ref
 used_no_write` now asserts the violating path does not exist and the
   fallback artifacts are in the sandbox; the session snapshot passed on
   the final suite runs.
4. **Per-run-dir stale-marker bypass.** The IN_PROGRESS marker lived in
   the per-label run dir, so re-running under a DIFFERENT label silently
   bypassed the stale-marker refusal (T20 step 2 initially returned
   EXECUTION_COMPLETE). Fixed: markers are CYCLE-SCOPED — any
   `IN_PROGRESS.json` under the runs root blocks any new run until
   `--resume-with-recovery-check` + integrity passes, and a successful
   recovery run adopts (removes) every cycle marker. Evidence:
   `test_lock.py::test_T20_recovery_resume_with_recovery_check`.
5. **Recovery integrity check could crash on the very ledger it must
   judge.** `recovery_integrity_check` built a full `Ledger` (whose scan
   raises on torn JSON) => an uncaught JSONDecodeError. Fixed with a
   line-by-line, never-raising `ledger_integrity_errors()`. Also: the
   refusal evidence writes were split so a torn ledger never blocks the
   refusal_record (the runner refuses to APPEND to a ledger failing
   integrity, discloses on stderr, exit stays 2).
   Evidence: `test_refusals.py::test_T20c_stale_marker_refused_when_recover
 y_integrity_fails`.
6. **FINAL_STATUS lacked failure details.** `failure_code`/`failed_step`
   were present but the human-readable detail list was not serialized,
   weakening the terminal evidence. Added a `failures[]` list (capped
   details). Evidence: `test_T10_mid_run_exception_releases_lock_and_kee
 ps_ledger_open` asserts the injected-fault message is IN the terminal
   status.

## 4. Explicit non-fixes (laws, not defects)

- Lock DRIFT (free flock + RUNNING row) is refused, never reclaimed —
  reclaim discipline belongs to the controller tooling, not the runner.
- `--allow-real-governance` is a DEAD FLAG: hard-compiled refusal in this
  PREP build (`REFUSED_ALLOW_REAL_GOVERNANCE_DISABLED`). No code path can
  reach the real governance dir.
- A raised lock release leaves the RUNNING registry row in place —
  intentional evidence preservation (the upstream FAIL-record law: never
  fake cleanup); `test_T11` asserts the row survives.

## 5. Test evidence summary

- Suite: `exec/test_runner_v2/` — 42 tests, all driving the real CLI
  (`<venv>/bin/python scored_runner_v2.py ...`) over sandbox tmp dirs.
- Final run: `42 passed` (pytest -q, two consecutive full runs).
- Machine lock discipline: `researchctl.py locks inspect` verdict
  `FREE_PROVEN` immediately before and immediately after the suite; the
  canonical machine lock was never taken (all lock dirs are sandbox tmp).
