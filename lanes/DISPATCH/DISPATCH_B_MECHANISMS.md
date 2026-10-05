# DISPATCH — Lane B · MECHANISMS (task wbap-b-mech, cycle WNBA-WINPROB-PREP-V1)

ROLE: quant-explorer (mechanism adjudication for a FRESH league; research/protocol design
ONLY). No outcome runs, no downloads, no writes outside your lane directory.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration
BRANCH: orca/wnba-winprob-prep-v1-integration (you do NOT commit; controller lands)
EXPECTED BASE SHA: measure `git rev-parse HEAD` in the worktree; record as dispatch_sha.
CYCLE: WNBA-WINPROB-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write): lanes/B_MECHANISMS/** only.
FORBIDDEN: everything else (plans/**, research/control/**, other lanes, any frozen artifact
of any cycle, .worktrees/nba-winprob-*/** and .worktrees/winprob-ng-prep-v1/** READ-ONLY),
push/merge/commit, credentials, purchases, any metric on real outcomes.

INDEPENDENCE LAW (load-bearing): no NBA data, hypothesis, parameter, or verdict is WNBA
evidence. NBA numbers may be CITED as cross-league context only. The NBA spent-window
prohibition does not bind WNBA, but the same train-only discipline does.

REQUIRED INPUTS (read-only):
- Evidence base: /Users/hoangminhlong/my-quantitative/.worktrees/winprob-ng-prep-v1/integration/lanes/C_MECHANISMS/MECHANISMS.md
  (H-C5 WNBA continuity-modulated carryover + F10) and .../lanes/B_WNBA/WNBA_SOURCE_AUDIT.md
  (coverage: schedules 1997–2026; box 2003+/2025-sample; pbp 2002+; ~220–260 RS games/
  season pre-2025; 2025 = 312; roster assets espn_wnba_game_rosters 2002–2026).
- Lane A of THIS cycle once landed (../A_DATA/*); if absent, proceed from the plan + corpus
  facts and note the dependency.
- Plan: plans/PLAN_wnba_winprob_prep_v1.md.

DELIVERABLE (lanes/B_MECHANISMS/MECHANISMS_WNBA.md + handoff_B.json):
1. (a) FRESH WNBA Elo baseline design: own train-only K/HCA selection inside the WNBA
   program (NBA K=32/HCA=100 is a citable starting point, NOT a WNBA law); HCA prior
   expectation stated (WNBA travel/schedule structure differs; measured later, not assumed);
   (b) H-C5 continuity-modulated rating carryover (R_start = league_mean + ρ·continuity·
   (R_end_prev − league_mean); continuity from season-start rosters — PIT-safe; requires
   roster coverage check vs Lane A's census); (c) at most ONE additional WNBA-structure-
   specific mechanism if it survives mechanism-first scrutiny (short season/high churn/
   roster-overseas effects...). ADVANCE at most 3 hypotheses total.
   Each advanced hypothesis: mechanism, exact operationalization on WNBA data, $0 source +
   rights pointer, as-of law, FROZEN falsifier (REJECT iff pooled 95% CI of ΔLL vs the
   fresh WNBA baseline includes 0 or ≥ half folds non-negative; paired date-cluster
   bootstrap), negative control (time-shuffled twin), capacity/power estimate (~230 RS
   games/season × ~25 usable seasons ≈ 5.5–6k RS games; state the fold count honestly),
   train-internal kill test, designed-null parent.
2. Explicit REJECTS with reasons (must cover: additive logistic-over-Elo layers — dead
   shape per both terminal cycles; MOV-weighted Elo — dead-family re-grid; 538 forecasts/
   closing odds/current-game box scores — banned; any NBA-derived parameter presented as
   WNBA evidence — independence-law violation).
3. Roster/availability: stays NOT_RUN_PIT unless Lane A clears a rights-verified archive
   with publish timestamps; post-game DNP fields never pre-game features.
4. handoff_B.json — schema zcode_orch_v3_handoff@1 at lanes/B_MECHANISMS/handoff_B.json
   (task_id "wbap-b-mech", commit_sha "NOT_COMMITTED_CONTROLLER_LANDED", ...).

TEST COMMANDS: none (document lane).
STOP CONDITIONS: dependency missing → note + proceed; plan conflict → record in handoff.

COMMIT RULES: no commits; leave files untracked in lanes/B_MECHANISMS/.
