# DISPATCH — Lane D_VERIFY (WINPROB-PLAYERFEAT-PREP-V1, wave 2)

ROLE: INDEPENDENT VERIFIER (A7-role). Never repairs; never edits other lanes' files; writes
only its own dir + handoff. Recomputes from bytes with INDEPENDENT code (do not import lane
scripts; read them only as claims).
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration
BRANCH: orca/winprob-playerfeat-prep-v1-integration · DISPATCH SHA: 8ad8785bb1332540d0a3e92ca3feed14f92c3116
ALLOWED PATHS (write): lanes/D_VERIFY/** + lanes/DISPATCH/handoff_D_VERIFY.json.
READ-ONLY: everything else.
FORBIDDEN: git; repairs; scored metrics; new downloads beyond ≤3 license/provenance URL
re-fetches; keys; betting vocabulary.
TASKS:
1. NBA (lane A claims): re-hash ≥4 of the 8 new season files + the output feature table vs
   FEATURE_TABLE_MANIFEST; re-join 2 seasons incl. one 0.9992 season (2017/2018/2019 —
   reproduce the 3 box-less FINAL games by game_id); independently recompute with YOUR OWN
   code ≥6 sampled team-game feature rows across seasons incl. one neutral row, one trade-guard
   case (e.g. the Patty Mills 2025 stale-DNP case the lane cites) — values must match the
   table within documented tolerance; verify no outcome columns exist in the table (schema
   inspection + content scan for score-like columns).
2. WNBA (lane B claims): re-hash ≥4 corpus files; re-derive per-season join rates for ≥4
   seasons incl. 2002/2003/2004/2013/2026; independently recompute ≥6 sampled rows (incl. one
   expansion-neutral row and one continuity row via the 20-key lineage); verify deterministic
   rebuild claim by re-running the lane's build_features.py into a temp copy and comparing
   sha256 (running lane code for REPRODUCTION is allowed; your verdict rows must come from
   your own code).
3. NFL crosswalk (lane C claims): re-hash players.parquet; re-join weekly stats 2026 + snap
   2026 match rates with your own code; re-count round-trip 97.55%; re-count 32-team presence;
   spot-check ≥3 named players incl. one pfr-null.
4. ADJUDICATION (owner-mandated): explicit CONFIRM or DISCONFIRM of lane C's LIFT
   recommendation for the predecessor NFL HOLD, with evidence. The NOT_RUN_PIT law for
   target-game status is a LAW (restated in the plan) — verifier checks the lanes respected
   it, and confirms LIFT only means: crosswalk blocker cleared with named residual blockers
   (snap lag, release-cadence, target-game status NOT_RUN_PIT).
5. Boundaries: grep lanes/ for metric patterns (log_loss/brier/win_prob/calibrat) — expect 0
   computation hits (design mentions allowed); verify 0 scored anywhere; write-scope audit
   (git status shows only expected paths — read-only observation).
DELIVERABLES: lanes/D_VERIFY/{VERIFICATION_REPORT.md (+ machine outputs *_output.json),
VERIFY_MATRIX.md, discrepancy register}. Verdict overall: VERIFIED / VERIFIED_WITH_MINOR /
DISCREPANCY_MAJOR.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_D_VERIFY.json
(task_id winprob-playerfeat-prep-v1-D-VERIFY, dispatch_sha=actual_start_sha=8ad8785b…, commit_sha=null).
