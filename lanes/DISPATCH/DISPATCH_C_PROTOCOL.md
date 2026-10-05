# DISPATCH — Lane C · PROTOCOL (task wbap-c-proto, cycle WNBA-WINPROB-PREP-V1)

ROLE: quant-explorer (successor scored-cycle protocol DRAFT; design ONLY). No outcome runs.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration
BRANCH: orca/wnba-winprob-prep-v1-integration (you do NOT commit; controller lands)
EXPECTED BASE SHA: measure `git rev-parse HEAD` in the worktree; record as dispatch_sha.
CYCLE: WNBA-WINPROB-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write): lanes/C_PROTOCOL/** only.
FORBIDDEN: everything else (all other lanes, plans/**, research/control/**, frozen artifacts
of any cycle, NBA worktrees READ-ONLY), push/merge/commit, credentials, purchases, any
metric on real WNBA outcomes.

REQUIRED INPUTS (read-only):
- Terminal-cycle protocol machinery to INHERIT (shapes, not windows): .worktrees/nba-winprob-scored-v1/integration/lanes/C_protocol/PROTOCOL_EVAL.md
  (fold law, paired date-cluster bootstrap, T1/T2/T3 gates, trial ledger law) — inherit the
  MACHINERY; the NBA splits/parameters are NOT WNBA law.
- WINPROB-NG-PREP-V1 lane C §3 + lane B WNBA audit (.worktrees/winprob-ng-prep-v1/integration/lanes/{C_MECHANISMS,B_WNBA}/*.md).
- Lanes A/B of THIS cycle once landed; if absent proceed from the plan and note it.
- Plan: plans/PLAN_wnba_winprob_prep_v1.md.

DELIVERABLE (lanes/C_PROTOCOL/PROTOCOL_DRAFT_WNBA.md + handoff_C.json):
1. Fresh split design: TRAIN-internal rolling-origin selection inside a TRAIN sub-window
   (era handling frozen in the document: 1997–2001 stats-side-schedule-only era — either
   excluded from feature arms or schedules-only baseline arms, chosen + frozen here);
   walk-forward OOS on held-out recent seasons; future seasons PROSPECTIVE ONLY (append-only
   ledger rows timestamped strictly before tip UTC).
2. Arm budget sketch ≤9 (frozen BEFORE any test look): WNBA B0 constant; fresh WNBA B1
   (own-Elo, train-only K/HCA); the ≤3 mechanisms from Lane B; negative-control diagnostics
   reported, never counted as candidate wins; reserve-slot rule (pre-specified or released).
3. Metrics + uncertainty: log loss primary; Brier + reliability + calibration slope [0.85,
   1.15] secondary; paired date-cluster bootstrap CIs; T1/T2/T3 gate shapes inherited;
   playoffs/Cup/All-Star separate from the RS headline.
4. Negative-control law per hypothesis (time-shuffled twin); control-beats-parent ⇒
   machinery audit, hypothesis un-scored.
5. Stop rules + negative-first terminal outcomes for the successor; capacity honesty
   (~230 RS games/season; state minimum fold populations).
6. Freeze/A7/GO law verbatim: successor needs fresh registration + data/code freeze + A7
   prelaunch AUTHORIZED + owner typed GO at its own gate; this cycle registers/consumes none.
7. handoff_C.json — schema zcode_orch_v3_handoff@1 at lanes/C_PROTOCOL/handoff_C.json
   (task_id "wbap-c-proto", commit_sha "NOT_COMMITTED_CONTROLLER_LANDED", ...).

TEST COMMANDS: none (document lane).
STOP CONDITIONS: plan conflict or missing dependency → record in handoff and proceed with
explicit NOT_RUN markers.

COMMIT RULES: no commits; leave files untracked in lanes/C_PROTOCOL/.
