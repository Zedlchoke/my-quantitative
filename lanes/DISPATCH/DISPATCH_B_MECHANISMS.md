# DISPATCH — Lane B · MECHANISMS (task nbang-b-mech, cycle NBA-WINPROB-NG-PREP-V1)

ROLE: quant-explorer (mechanism adjudication; research/protocol design ONLY). No data
downloads, no outcome computation, no git writes outside your lane directory.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-ng-prep-v1/integration
BRANCH: orca/nba-winprob-ng-prep-v1-integration (you do NOT commit; controller lands)
EXPECTED BASE SHA: measure `git rev-parse HEAD` in the worktree; record as dispatch_sha.
CYCLE: NBA-WINPROB-NG-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write): lanes/B_MECHANISMS/** only.
FORBIDDEN: everything else, incl. plans/**, research/control/**, other lanes, any frozen
artifact of any cycle (.worktrees/nba-winprob-scored-v1/** etc. = READ-ONLY), push/merge/
commit, credentials, purchases, running any model on real outcomes.

REQUIRED INPUTS (read-only):
- Evidence base: /Users/hoangminhlong/my-quantitative/.worktrees/winprob-ng-prep-v1/integration/lanes/C_MECHANISMS/MECHANISMS.md
  (H-C1 SOS-Elo, H-C2 home/away split, H-C3 availability NOT_RUN_PIT, H-C4 fatigue×venue
  interactions, F8 pace/efficiency priors, F11 negative controls) — proposals to re-adjudicate
  FOR NBA 2016+, not authority.
- Terminal facts: .worktrees/nba-winprob-scored-v1/integration/research/control/NBA-WINPROB-SCORED-V1/results/scored_summary.json
  (B1* = B1-d K=32 HCA=100 LL 0.5987 vs B0 0.6769 n=8369; ΔLL −0.0782 [−0.0875,−0.0687];
  rest/form T1 FAIL −0.0010 [−0.0033,+0.0013]; slope 0.989).
- Lane A inputs (once landed): ../A_DATA/GAME_UNIVERSE_SPEC_NBA_2016PLUS.md + PIT_AUDIT_NBA.md
  (if not yet present, proceed from the plan + corpus facts and note the dependency).
- Plan: plans/PLAN_nba_winprob_ng_prep_v1.md.

DELIVERABLE (lanes/B_MECHANISMS/MECHANISMS_NBA_NG.md + handoff_B.json):
1. Adjudication of (a) H-C1 SOS-adjusted Elo, (b) H-C2 home/away split ratings, (c) H-C4
   fatigue×venue interaction block (b2b_away / 3in4_away / travel_bucket_away /
   tz_shift_away), (d) F8 pace/efficiency train-only aggregates as rating INITIALIZATION
   (never additive features over Elo). ADVANCE at most 3–4; each advanced hypothesis gets:
   mechanism (who is mispriced and why), exact operationalization on the 2016+ corpus
   (allowed data only), $0 source + rights pointer, as-of law (inputs frozen at prior tip),
   FROZEN falsifier (REJECT iff pooled 95% CI of ΔLL vs B1* includes 0 or ≥ half folds
   non-negative — CI machinery = paired date-cluster bootstrap), negative control
   (time-shuffled twin), capacity/power estimate on 2016+ (~1230 RS games/season; 2020
   1059 played, 2021 1080 played per lane A dedupe), train-internal kill test, and its
   designed-null parent (what result proves the extra parameter is empty).
2. Explicit REJECTS with reasons (must cover: additive logistic-over-Elo rest/form layer —
   dead; MOV/blowout-weighted Elo — dead-family re-grid; any 538-forecast/closing-odds/
   current-game-box-score feature — banned; K/HCA re-grid on 2009–2015 — banned spent window).
3. Availability/injury (H-C3): keep NOT_RUN_PIT unless Lane A's PIT audit clears a source;
   if cleared, spec the provenance audit steps that must precede any arm.
4. Interactions-must-beat-null-parents rule restated (per owner law).
5. handoff_B.json — schema zcode_orch_v3_handoff@1 at lanes/B_MECHANISMS/handoff_B.json
   (task_id "nbang-b-mech", commit_sha "NOT_COMMITTED_CONTROLLER_LANDED", ...).

TEST COMMANDS: none (document lane; no computation on real outcomes).
STOP CONDITIONS: dependency on Lane A missing → note and proceed; plan conflict → record in
handoff; anything requiring outcome computation → out of scope, say so.

COMMIT RULES: no commits; leave files untracked in lanes/B_MECHANISMS/.
