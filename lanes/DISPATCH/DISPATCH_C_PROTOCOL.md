# DISPATCH — Lane C · PROTOCOL (task nbang-c-proto, cycle NBA-WINPROB-NG-PREP-V1)

ROLE: quant-explorer (successor scored-cycle protocol DRAFT; design ONLY). No outcome runs.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-ng-prep-v1/integration
BRANCH: orca/nba-winprob-ng-prep-v1-integration (you do NOT commit; controller lands)
EXPECTED BASE SHA: measure `git rev-parse HEAD` in the worktree; record as dispatch_sha.
CYCLE: NBA-WINPROB-NG-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write): lanes/C_PROTOCOL/** only.
FORBIDDEN: everything else, incl. plans/**, research/control/**, other lanes, frozen
artifacts of any cycle, push/merge/commit, credentials, purchases, any metric computed on
real NBA outcomes.

REQUIRED INPUTS (read-only):
- Terminal protocol (the machinery to inherit): .worktrees/nba-winprob-scored-v1/integration/
  lanes/C_protocol/PROTOCOL_EVAL.md + research/control/NBA-WINPROB-SCORED-V1/** (fold law,
  paired date-cluster bootstrap, T1/T2/T3 gate shapes, trial ledger law).
- WINPROB-NG-PREP-V1 lane C §3 protocol sketch + lane A data contract
  (.worktrees/winprob-ng-prep-v1/integration/lanes/{C_MECHANISMS,A_NBA_POST2015}/*.md).
- Lanes A/B of THIS cycle once landed (../A_DATA/*, ../B_MECHANISMS/*); if absent, proceed
  from the plan and note the dependency.
- Plan: plans/PLAN_nba_winprob_ng_prep_v1.md.

DELIVERABLE (lanes/C_PROTOCOL/PROTOCOL_DRAFT_NBA_NG.md + handoff_C.json):
1. Split design: TRAIN-internal rolling-origin selection inside 2016..(cutoff) with the
   cutoff chosen and frozen in the document; walk-forward OOS on the remaining NEW seasons;
   the spent 2009–2015 window is citable context, never scoreable; 2026–27 unplayed games at
   the cycle epoch are PROSPECTIVE ONLY (append-only ledger rows timestamped strictly before
   tip UTC; every game already played before the freeze is NOT_RUN prospective).
2. Arm budget sketch ≤9 (frozen BEFORE any test look): B0 constant; NBA B1* K=32/HCA=100
   verbatim (mandatory baseline, never re-tuned); the ≤3–4 mechanisms advanced by Lane B;
   negative-control diagnostics reported but never counted as candidate wins; reserve slot
   rule (specified pre-look or released, never reallocated mid-program).
3. Metrics + uncertainty: log loss primary; Brier + reliability + calibration slope [0.85,
   1.15] secondary; paired date-cluster bootstrap CIs (terminal-cycle machinery); T1/T2/T3
   gate shapes inherited; playoffs + play-in + Cup reported separately; regular season
   headline only.
4. Negative-control law per hypothesis (time-shuffled twin); control-beats-parent ⇒
   machinery audit, hypothesis un-scored.
5. Stop rules + interpretation law (negative-first terminal outcomes for the successor).
6. Freeze/A7/GO law verbatim: successor needs fresh registration + data/code freeze + A7
   prelaunch AUTHORIZED + owner typed GO at its own gate (two-key; no GO survives from any
   earlier cycle; this cycle registers/consumes none).
7. handoff_C.json — schema zcode_orch_v3_handoff@1 at lanes/C_PROTOCOL/handoff_C.json
   (task_id "nbang-c-proto", commit_sha "NOT_COMMITTED_CONTROLLER_LANDED", ...).

TEST COMMANDS: none (document lane).
STOP CONDITIONS: plan conflict or missing dependency → record in handoff and proceed with
explicit NOT_RUN markers.

COMMIT RULES: no commits; leave files untracked in lanes/C_PROTOCOL/.
