# DISPATCH — Lane INV_C2 (NFL-WINPROB-NG-SCORED-V1, wave B) — C2 MACHINERY SUSPECT INVESTIGATION

ROLE: diagnostic lane (read-only analysis). NO code changes, NO freeze changes, NO arm
re-admission. C2 stays OUT of the slate regardless of findings (owner law: no post-outcome
revival). Purpose: root-cause the MACHINERY_SUSPECT and determine whether the SAME fault
taints the time-shuffled controls that admitted C3.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration
BRANCH: orca/nfl-winprob-ng-scored-v1-integration · DISPATCH SHA: ecf8371abf7839ca49e9245c99f8aa7386d48fdd
ALLOWED PATHS (write): lanes/INV_C2/** + lanes/DISPATCH/handoff_INV_C2.json (+ tmp under your dir).
READ-ONLY: everything else. You MAY run replay/control code read-only (outputs to your dir only).
BACKGROUND: T_SELECT reported C2's venue-label-permutation control WON (ΔLL −0.0069
[−0.00995, −0.00373] vs parent B1*), i.e. the control arm improved calibration with corrupted
venue labels — a comparison-machinery fault by definition (a control must not beat its parent).
TASKS:
1. Read lanes/T_SELECT/{arms.py,select.py,boot.py,SELECTION_REPORT.md,SELECTION_LEDGER.jsonl}
   and reconstruct EXACTLY how the venue-permutation control is implemented: what is permuted
   (prediction-time labels? update-time labels? both? the h term? E computation? scoring
   rows?), the seed/path, and what the control arm actually computes end-to-end.
2. Hypothesis-test the root cause with small read-only probes (synthetic or tiny real slices
   are both fine; NO writes outside your dir): candidate faults include (a) labels permuted
   for updates but predictions use true roles (mismatch = unintended regularization); (b) E
   recomputed with permuted roles creating double-counted signal; (c) the control accidentally
   implements a SHRUNK/half-speed update (λ_effective = λ/2) which genuinely helps an
   overconfident replay; (d) row-set or pairing mismatch in the ΔLL computation; (e) sign or
   indexing bug swapping control/parent. Probe each; identify which reproduces the −0.0069.
3. Determine taint scope: is the time-shuffled-twin machinery (used for C1/C3/C4 verdicts and
   C3's ADMIT) implemented by shared code with the fault, or independent? Read the twin
   implementation; state explicitly whether C3's "shuffled control clean" verdict is sound,
   tainted, or unverifiable — with code-line evidence.
4. Verdict options: (i) FAULT_ISOLATED_TO_VENUE_CONTROL (C2-specific implementation; C3
   verdict stands); (ii) SHARED_CONTROL_FAULT (C3's control evidence void — remediation
   required: fix control implementation ONLY, re-run the PRE-REGISTERED C3 control check,
   document as ERRATUM; grids/criterion unchanged; C2 still stays out); (iii) INCONCLUSIVE
   (name exactly what additional evidence a remediation lane must produce).
5. Deliverable: lanes/INV_C2/C2_MACHINERY_INVESTIGATION.md (root cause with reproduced
   numbers, taint scope, verdict, remediation spec if needed — as a PROPOSAL for the
   controller, not an action) + VERDICT_TABLE.md.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_INV_C2.json (task_id
nfl-winprob-ng-scored-v1-INV-C2, dispatch_sha=actual_start_sha=ecf8371a…, commit_sha=null).
STOP CONDITIONS: none — investigate to a verdict.
