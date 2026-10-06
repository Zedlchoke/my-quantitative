# PIN_ENFORCE_REPORT — F-V1/F-V2 closed with evidence (controller-completed deliverable)

- Provenance: lane PIN-ENFORCE went inactive (600s) after completing the
  code fix + P-suite; the controller verified everything, corrected ONE
  lane-authored script defect (disclosed below), and wrote this report +
  handoff. Lane code was not modified by the controller.
- FAIL-before-fix: fix3/FAIL_FV2.md @ 47e54e55 (BEFORE the fix commit).
  The controller's reproduction ran the tampered-addendum-pin scenario
  THROUGH the production runner to COMPLETION (exit 0 EXECUTION_COMPLETE)
  — stronger than the owner-side audit's boundary proof — plus the
  claim erratum (prior "TOCTOU catches addendum drift" was wrong for the
  execution path; D-8 'deferred' rescinded).
- The fix (minimal diffs, documented in the wave commit):
  1. `live_operative_pins()` — ONE definition: base + all v2_*_addendum
     new_pins; supersession BY ARTIFACT PATH, later addendum wins; live
     and history returned separately (history = evidence only).
  2. Execution gate: explicit `if not drift["pass"] ⇒ REFUSED_DRIFT`
     (fail-closed regardless of which pin mismatched); gate facts
     `input_sha_matches` built from the LIVE set (no hardcoded names).
  3. Post-acquire TOCTOU reverify covers the FULL LIVE pin set via a
     contract-driven closure (base-only TOCTOU_PIN_NAMES retired).
  4. Self-integrity: at the execution boundary the runner hashes the
     module ACTUALLY imported (`scored_executor.__file__`) and its own
     `__file__` vs their live pins (path AND sha) — stale imports and
     path tricks refuse (REFUSED_CONTROL_STATE_DRIFT / SELF-INTEGRITY).
  5. F-V1: check_drift output splits `pins_live` (path/expected/actual/
     match per name) and `pins_history` — live diagnostics never clobbered
     (P7: 23 live + 6 history names; scored_executor live row visible
     alongside its 2 history twins).
  6. Missing/unreadable pinned file ⇒ fail-closed named refusal (P6).
- **Behavioral proof (execution, not preflight)**: fix3/repro_fv2_after_fix.py
  — the EXACT FAIL_FV2 tamper now yields exit 2 REFUSED_DRIFT naming
  scored_executor + ledger REFUSED row + ZERO execution artifacts + no
  EXECUTION_COMPLETE (all 8 checks true; flip_vs_FAIL_FV2=true). Script
  note: the lane-authored version had an internal defect (read evidence
  from a nonexistent refusal_record path + a tamper-target bug) producing
  false-negatives; the controller replaced its core with the proven debug
  body — disclosed in the script docstring.
- P1-P10 matrix (production path; exit codes in pin_enforce_results.json
  + fresh re-run 10/10 in 1381s): P1 happy 0 (24 rows, EXECUTION_COMPLETE)
  · P2 tampered live executor pin (v2_3) ⇒ 2 REFUSED_DRIFT, history-tamper
  inert · P3 runner self-pin ⇒ 2 via SELF-INTEGRITY (stale-import proof)
  · P4 injected v2_3 probe pin checked with NO code change (green 0 /
  tampered 2; pins_live visible) · P5 post-acquire drift ⇒ 2 (closure at
  the enforcement site; CLI fault too) · P6 missing pinned file ⇒ 2 ·
  P7 live/history separation proven · P8 registry tamper ⇒ 2 · P9 ALL
  THREE regression suites exit 0 (finalization + execution + refusals)
  · P10 preflight-vs-execution distinction documented (both refuse,
  different records; preflight proves wiring only).
- Regression re-run by controller after the script fix: refusals +
  execution = 24/24 (97s); pin-enforce 10/10 (1381s).
- Sandbox mirror: the generator now stages ALL live pins (no pin dropped
  from enforcement for happy-path convenience).
- D-1..D-7 remain pending owner ratification; **D-8 disposition updated:
  F-V1/F-V2 FIXED with evidence (see EXEC_BUILD_REPORT addendum) — the
  packet no longer asks the owner to accept an enforcement defect.**

— End PIN_ENFORCE_REPORT.
