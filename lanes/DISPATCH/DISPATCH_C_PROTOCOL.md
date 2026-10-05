# DISPATCH — Lane C · PROTOCOL (task nflng-c-proto, cycle NFL-WINPROB-NG-PREP-V1)

ROLE: quant-explorer (protocol design). Design ONLY.
OBJECTIVE: design the evaluation protocol for the successor NFL scored cycle(s): train-internal
selection, prospective append-only prediction ledger, frozen ≤9-arm budget, metrics, uncertainty,
playoffs separation, stop rules, ≥2-season condition. NO outcome computation, NO data downloads.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-prep-v1/lane-c-proto
BRANCH: orca/nfl-ngprep-c-proto
EXPECTED BASE SHA: the HEAD of your worktree at spawn (controller-created from the bootstrap commit; record git rev-parse HEAD output in your handoff as dispatch_sha) (verify before starting)
CYCLE: NFL-WINPROB-NG-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write): lanes/C_PROTOCOL/** (this worktree) ONLY.
FORBIDDEN: everything else; downloads; edits to frozen artifacts/ledgers; push/merge/rebase;
git add -A. Reads of other worktrees allowed (read-only).

REQUIRED INPUTS (read-only evidence):
- Frozen NFL protocol semantics (inherit where still valid):
  /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-prep-v1/integration/lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md
  (kickoff-grain as-of law, identical-kickoff exclusion, TIE LAW, neutral-site HCA=0,
  walk-forward by season, log loss primary/Brier/10-bin reliability/calibration slope, paired
  ΔLL date-clustered bootstrap seed 20261005, T1-T3/R1-R3)
- Terminal results: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-scored-v1/integration/research/control/NFL-WINPROB-SCORED-V1/results/scored_summary.json
- NBA-cycle protocol sketch (§3): /Users/hoangminhlong/my-quantitative/.worktrees/winprob-ng-prep-v1/integration/lanes/C_MECHANISMS/MECHANISMS.md
- Cycle plan: plans/PLAN_nfl_winprob_ng_prep_v1.md (in-tree)

DELIVERABLES (under lanes/C_PROTOCOL/):
1. PROTOCOL_NFL_NG.md — successor-cycle protocol draft:
   - TRAIN window definition (2000–2018-equivalent; the spent TEST 2019–2025 may be cited but
     never re-used as a new hypothesis window; 2026+ prospective only) + train-INTERNAL
     rolling-origin selection for every free parameter, frozen before any prospective look.
   - Prospective prediction ledger design: append-only JSONL, one row per (game, arm) recorded
     STRICTLY BEFORE kickoff UTC with recorded_at_utc, arm config digest, p_home, inputs
     digest; hash-chained; games already played before the row's recorded_at are NOT_RUN
     prospective and must be excluded by validator; retrospective injection impossible.
   - Frozen ≤9-arm budget enumeration: (1) B0 constant, (2) B1* own-Elo K=40 HCA=0 (mandatory
     baseline), (3)-(5) the ≤3 Lane-B candidate mechanisms, (6) conditional interaction arm
     only if train-internal gate passes, (7) ONE pre-registered reserve (specified in freeze
     doc before any prospective look; unused = released, never reallocated). Negative
     controls are diagnostic arms — reported, never counted as candidate wins.
   - Metrics: log loss primary; Brier + 10-bin reliability + calibration slope (band
     [0.85, 1.15]) secondary; paired ΔLL with kickoff-date-clustered bootstrap (seed
     inherited or new — state it); T1/T2/T3 gate shape inherited; R1-R3 negative-terminal
     thresholds re-stated.
   - Playoffs: reported separately, never pooled into regular-season headline.
   - Stop rules: early-kill conditions per arm (train-internal failure ⇒ never spend
     prospective window); program-level stop if all candidates fail train-internal.
   - ≥2-new-season rule: no single-season NFL OOS presented as decisive; strong conclusions
     require ≥2 completed prospective seasons (~540 games) or pre-registered pooling plan.
   - Quarantine inheritance: odds columns, pbp-derived current-game features, injuries
     (unless Lane A clears PIT) stay quarantined/NOT_RUN_PIT.
   - Prediction-ledger operational plan: WHO/WHEN records rows (per-week cadence before
     first kickoff of each week), how kickoff UTC is sourced, how played-vs-future is
     validated, and what happens on postponement/flex changes.
2. LEDGER_SCHEMA.md — exact JSONL row schema + validation rules + a small set of synthetic
   example rows (fabricated examples clearly labelled SYNTHETIC — no real-game predictions).
3. handoff_C.json — schema zcode_orch_v3_handoff@1 at lanes/C_PROTOCOL/handoff_C.json
   (task_id "nflng-c-proto").

STOP CONDITIONS: conflict with frozen terminal semantics → record as open question for the
successor freeze doc, do not silently amend; anything requiring a decision only the owner can
make → list in handoff known_limitations.

COMMIT RULES: exactly ONE clean commit on your branch (message prefix "NFL-NG-PREP lane C:"),
stage by pathspec, never push/merge.
