# DISPATCH — Lane A7_PRELAUNCH (NFL-WINPROB-NG-SCORED-V1, wave 5) — INDEPENDENT PRELAUNCH AUDIT

ROLE: A7 independent auditor. Fresh context; writes ONLY audit artifacts; NEVER repairs,
never edits implementation, freeze, or test code; never asks implementers how to PASS.
Recompute from bytes and source; actively look for reasons claims could be wrong.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration
BRANCH: orca/nfl-winprob-ng-scored-v1-integration · DISPATCH SHA: 8cf29fe60809dd62c7d573292853d62b01cae0d4
ALLOWED PATHS (write): lanes/A7_PRELAUNCH/** + lanes/DISPATCH/handoff_A7_PRELAUNCH.json.
READ-ONLY: everything else (this worktree, the predecessor worktrees, root checkout registry,
data dirs). You MAY run read-only verification code (replays, re-hashes, re-tests) writing
outputs only into your lane dir / tmp.
AUDIT CHECKLIST (each with command + exit code + evidence):
A7-1 SHA chain: base f55dab66 → bootstrap 832f695 → A_DATA f6ff4945 → T_SELECT 69798a83 →
   F_FREEZE 7ec4c539 → addendum e08e4c42 → S_SYNTH 8cf29fe6 (verify with /usr/bin/git -C
   <worktree> log --format='%H %s' — git READ-ONLY commands are permitted to the auditor);
   every commit tree-clean parentage; worktree status clean now.
A7-2 Designed-null re-run: independently re-execute (import arms.py; do not modify) the
   designed-null equivalence on YOUR OWN synthetic stream — max |Δp| == 0 vs B1*.
A7-3 No-spent-window audit: grep lanes/T_SELECT code for the load filters (season caps 2018/
   2017), verify assertion behavior by code reading + a runtime probe with a doctored
   2019-row fixture (expect loud failure); scan for any odds/rating input columns (must be
   none).
A7-4 Real-ledger absence: re-verify all real ledger paths absent worktree-wide; sandbox
   ledger(s) contain only SYNTH_ ids; freeze GENESIS digest string ae99a803… appears ONLY in
   freeze/packet docs, never inside any ledger file.
A7-5 Rights: LICENSE pin sha 2a82ac9b… re-verified live by lane A; spot re-fetch allowed
   (≤1 URL); attribution chain present in data dirs.
A7-6 Selection ledger completeness: 38 rows; every pre-registered grid point present (C1×5,
   C2×12+null, C3×5, C4×3, B0, B1*); recompute pooled LL for ≥3 configs from the raw stream
   with your own replay (tolerance 1e-9) to confirm the ledger is not fabricated.
A7-7 Freeze §7 completeness: all 10 dispatch items present in FREEZE_PACKET.md; arm configs
   match SELECTION_REPORT.md; CODE_FREEZE_ADDENDUM SHA == 7ec4c539… (git cat-file verify);
   GENESIS placeholder discipline consistent.
A7-8 Boundary compliance: 0 arms scored; no win-prob rows for real games anywhere; no GO
   phrase typed anywhere in artifacts (grep the exact phrase — expect only registered-not-
   typed contexts); no S1; no push; budget 0/9.
A7-9 Power language + ≥2-season rule + no-early-stop present verbatim in freeze packet.
A7-10 Incidents/caveats coherence: C2 MACHINERY_SUSPECT properly recorded (not silently
   dropped); B1* TRAIN slope 1.605 underconfidence note present; margin-config
   NOT_RUN_TOOLING documented with caller-side law.
VERDICT: A7_PRELAUNCH_PASS | A7_PRELAUNCH_REFUSED (with blocking reasons). REFUSED is a
normal outcome — do not soften blockers. Also emit the OWNER_GATE_BRIEF.md: a ≤25-line
summary for the owner decision (typed GO or not; what happens on GO: week-capture mechanics,
first target week-5 2026-10-09T00:15Z, batch margin ≥6h ⇒ GO + first batch by 2026-10-08
~18:15Z to capture week 5; what remains forbidden).
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_A7_PRELAUNCH.json (task_id
nfl-winprob-ng-scored-v1-A7-PRELAUNCH, dispatch_sha=actual_start_sha=8cf29fe6…, commit_sha=null).
STOP CONDITIONS: none — audit to a verdict; if a check cannot run, record NOT_RUN with reason.
