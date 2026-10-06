# FAIL RECORD — F-V2 pin-enforcement hole (reproduced to COMPLETION before fix)

- Reproduced 2026-10-05 by the controller THROUGH THE PRODUCTION RUNNER
  (sandbox; valid fake GO; fresh sandbox copy with ONE tampered pin:
  v2_2_addendum.scored_executor.sha256 = ffff…): the runner executed the
  FULL scored pass and returned **exit 0, verdict EXECUTION_COMPLETE** —
  the addendum-only drift was recorded by check_drift (pass=false,
  mismatched_pins=[scored_executor]) but NEVER enforced. This is STRONGER
  than the owner-side audit's boundary proof (audit stopped at the
  execution boundary with an audit-stop executor; our reproduction ran
  synthetic execution to completion and reported success).
- Root causes (code-level):
  1. The RefusalGate facts' `input_sha_matches` is built from
     `contract["pins"]` (BASE ONLY) — addendum pins never reach the gate.
  2. The post-acquire TOCTOU set `TOCTOU_PIN_NAMES` (executor) is a
     BASE-ONLY hardcoded tuple.
  3. Nothing ties the pinned bytes to the module ACTUALLY imported.
- **Claim erratum (append-only)**: the earlier remediation report/verdict
  language claiming "TOCTOU-side checks catch addendum drift" /
  "preflight wiring + drift.pass catch it" as enforcement was WRONG for
  the execution path — preflight refusal is NOT execution refusal
  (behaviorally distinct; the dispatch states this law and the
  reproduction proves the execution path did not refuse). D-8's
  "deliberately deferred" disposition for F-V2 is RESCINDED as
  insufficient — the owner's directive is correct: this is a PRE-GO
  blocker and D-8 must become a fixed-with-evidence disposition.
- Fix law (from the dispatch): ONE consistent live-operative-pin
  definition everywhere (base + effective addenda; path-keyed
  supersession, later wins; HISTORY rows are evidence, never live);
  execution gate refuses on check_drift.pass=false regardless of where
  the mismatch sits; post-acquire reverify covers ALL live pins +
  authority; pin checks must match the bytes ACTUALLY loaded/imported
  (self-integrity for runner/executor); F-V1: live and history
  diagnostics separated, no name clobber.

— End FAIL record. NO fix in this commit.
