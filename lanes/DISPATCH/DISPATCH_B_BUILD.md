# DISPATCH — Lane B_BUILD (NFL-PLAYERFEAT-PREP-V1) — FROZEN NFL PLAYER-FEATURE TABLE

ROLE: data/feature build lane. NO outcome metrics, NO scored computation, NO touch of the
NFL prospective cycle (NFL-WINPROB-NG-SCORED-V1 worktree is strictly read-if-needed and
never written).
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-playerfeat-prep-v1/integration
BRANCH: orca/nfl-playerfeat-prep-v1-integration · DISPATCH SHA: efedf6f47759230294525156aa31137ccd7ba382
ALLOWED PATHS (write): lanes/B_BUILD/** + lanes/DISPATCH/handoff_B_BUILD.json + data under
~/.my-quantitative-data/nfl-playerfeat-prep-v1/**. READ-ONLY: everything else.
FORBIDDEN: git; scored metrics; betting vocabulary; writes to playerdata-prep-v1/
playerfeat-prep-v1 (predecessor dirs, EXTEND-ONLY — your outputs go to YOUR new dir).

## Inputs (read-only)
- Weekly stats + snap_counts: ~/.my-quantitative-data/playerdata-prep-v1/nfl/
  {raw_stats_player,raw_snap_counts}/ (sha256s in predecessor manifest
  .worktrees/winprob-playerfeat-prep-v1/integration/lanes/C_NFL_CROSSWALK/ for crosswalk;
  stats/snap manifests in .worktrees/winprob-playerdata-prep-v1/integration/lanes/C_NFL/).
- Crosswalk players.parquet: ~/.my-quantitative-data/playerfeat-prep-v1/nfl/raw_players/.
- Games/schedule: ~/.my-quantitative-data/nfl-ng-prep-v1/raw_schedules_r1_20261005/games.csv
  (kickoff UTC canonicalization law: gameday+gametime ET→UTC).
- Predecessor design: lanes/C_NFL/FEATURE_PROPOSALS.md (winprob-playerdata-prep-v1 worktree)
  + HOLD-lift verdict in lanes/C_NFL_CROSSWALK/VERDICT_TABLE.md + D_VERIFY adjudication in
  lanes/D_VERIFY/VERIFICATION_REPORT.md (same worktree as crosswalk).

## Feature groups (freeze exact scalars in FEATURE_SPEC.md; all strictly prior-game aggregates)
- G1 QB form/availability: prior-k (k∈{3,5}) passing production per team (EPA-adj if
  available in weekly stats, else yards/TD/INT/atts composite as spec'd) vs own season-to-date.
- G2 skill-player usage mass: prior-k share of team targets+carries concentrated in top-N
  skill players (usage concentration).
- G3 absence proxy: missing snap-share of top-minute players in most recent prior game(s)
  via snap_counts (through the crosswalk; handle pfr-null cohort by GSIS-side fallback or
  exclusion — spec the rule).
- LAWS: kickoff-strict-inequality as-of; bye-week handling (rest_days from prior kickoffs;
  bye = no prior game that week — spec neutral/hold rules); 1 NaN-player placeholder row per
  week excluded; in-game-injury lag documented; target-game status NOT_RUN_PIT (law, restated);
  window disclosure: stats on disk 2024–2026 → prior-game windows fully computable from
  mid-2024+ (measure the first game-date where each group is computable with ≥1 prior game;
  per-season coverage disclosed).
- Output: one row per (game_id, team side) for games with stats data; as-of columns
  (kickoff_utc, n_prior_games_used, asof_rule_version); NO outcome columns; deterministic;
  parquet under ~/.my-quantitative-data/nfl-playerfeat-prep-v1/features/ +
  FEATURE_TABLE_MANIFEST.md (+json) with input/output sha256 + coverage.
- --selftest: leak guards (incl. the predecessor KC 2024 worked example re-derived if in
  window), crosswalk canary (pfr-null player), bye-week fixture, determinism double-run.

## Deliverables
lanes/B_BUILD/{build_features.py, FEATURE_SPEC.md, COVERAGE_AUDIT.md, PIT_AUDIT.md,
FEATURE_TABLE_MANIFEST.md (+json), VERDICT_TABLE.md}.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_B_BUILD.json (task_id
nfl-playerfeat-prep-v1-B-BUILD, dispatch_sha=actual_start_sha=efedf6f4…, commit_sha=null).
STOP CONDITIONS: input sha mismatch vs predecessor manifests; suspected leakage; >30 min
compute (land spec+audit, record features NOT_RUN_TOOLING).
