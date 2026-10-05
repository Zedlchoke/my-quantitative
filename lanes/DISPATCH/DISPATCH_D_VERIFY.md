# DISPATCH — Lane D · VERIFY (task nflng-d-verify, cycle NFL-WINPROB-NG-PREP-V1)

ROLE: quant-auditor (independent verifier; A7-equivalent). Verify ONLY — NEVER repair.
OBJECTIVE: after lanes A/B/C land, verify claims against bytes: downloads exist with recorded
sha256; rights quotes verbatim-match the cited URLs/licenses; PIT/NOT_RUN_PIT verdicts
internally consistent and consistent with quarantine law; no outcome computation occurred
(0 scored, no win-prob metrics in any artifact); trial accounting = 0; registry row
NFL-WINPROB-NG-PREP-V1 coherent (lifecycle/budget/worktree/branch/head); lane branches based
on the recorded dispatch SHA; integration tree clean; heavy lock free.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-prep-v1/lane-d-verify
BRANCH: orca/nfl-ngprep-d-verify (created from the post-landing integration HEAD by controller)
CYCLE: NFL-WINPROB-NG-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write): lanes/D_VERIFY/** (this worktree) ONLY.
FORBIDDEN: modifying anything else anywhere; repairs of any kind (report defects, never fix);
push/merge/rebase; credentials; downloads. Reads across the repo and data dirs allowed.

DELIVERABLES (under lanes/D_VERIFY/):
1. VERIFICATION.md — numbered checks with PASS/FAIL/NOT_RUN verdicts + evidence (command,
   expected, observed): (D-1) download manifest ↔ bytes (sha256 spot re-hash ≥3 files incl.
   one pbp/large file); (D-2) rights: license quotes verbatim vs upstream for each asset
   claimed CC BY 4.0 (at least the license URL + one sentence match); (D-3) 2026 played/future
   classification: recount played games from the downloaded 2026 results yourself; confirm
   every played game is marked NOT_RUN prospective in Lane A artifact; (D-4) injury PIT
   verdict consistency; (D-5) no-metrics scan: grep artifacts for log-loss/Brier values
   computed on real 2026 outcomes (schema/coverage counts allowed; model metrics forbidden);
   (D-6) mechanisms ≤3 candidates + conditional interaction; no re-grid of rejected mains;
   each has falsifier + control + power; (D-7) protocol: ledger schema forbids retrospective
   rows; ≤9 arms incl B0/B1*; playoffs separate; ≥2-season rule present; (D-8) handoffs A/B/C
   schema-valid at exact dispatch paths; (D-9) registry coherence + lock free + integration
   tree clean; (D-10) trial accounting: 0 scored outcomes anywhere in this cycle.
2. handoff_D.json — schema zcode_orch_v3_handoff@1 at lanes/D_VERIFY/handoff_D.json
   (task_id "nflng-d-verify").

STOP CONDITIONS: a defect that blocks verification (missing file, unreadable evidence) → mark
that check FAIL with evidence and continue the rest; NEVER repair the defect yourself.

COMMIT RULES: exactly ONE clean commit on your branch (message prefix "NFL-NG-PREP lane D:"),
stage by pathspec, never push/merge.
