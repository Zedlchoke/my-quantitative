# GO_READY WITHDRAWAL — append-only correction of record (2026-10-04)

- The prior **GO_READY** verdicts (verify/prego3 + verify/gate6) are
  **WITHDRAWN** as incomplete on one dimension: the scored execution
  path in `gate6/runner/scored_runner.py` (~L749) is a **STUB** that
  prints "WOULD EXECUTE" and exits 0 after all authority gates pass.
  Execution, scored-output twin, and terminal accounting are NOT fully
  wired. A GO typed against that state would reach a stub, not a scored
  run.
- What REMAINS valid from those verifications (not withdrawn): the
  ledger fix + suites; refusal gates; contract-v2 authority bindings;
  preflight wiring; registry/doctor state. The withdrawal is scoped to
  the EXECUTION-PATH completeness dimension only.
- This is the honest state record required by the owner's dispatch;
  nothing is hidden and no history is edited. A NEW GO_READY verdict
  may be issued only after the execution path is implemented and
  proven through the production path with synthetic fixtures, verified
  at a committed SHA by a fresh-context verifier.

— End withdrawal. (Pre-GO implementation authorization only; NOT a GO.)
