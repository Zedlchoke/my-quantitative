# DISPATCH — Lane A_NBA_FEAT (WINPROB-PLAYERFEAT-PREP-V1)

ROLE: data/feature lane (quant A3+implementer hybrid). OBJECTIVE: NBA frozen player-feature
table 2016–2026 from strictly pre-game-known information; no outcome metric, ever.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration
BRANCH: orca/winprob-playerfeat-prep-v1-integration · BASE/DISPATCH SHA: 00323ba64ebbbc107d05fcf926c7cadf8dfa7acd
ALLOWED PATHS (write): lanes/A_NBA_FEAT/** and data outside git under
~/.my-quantitative-data/playerfeat-prep-v1/nba/** . READ-ONLY: everything else, incl.
predecessor worktrees/artifacts and all existing data dirs (playerdata-prep-v1, nba-hoopr-v1).
FORBIDDEN: any git command (no commit/push/stage — controller commits); edits outside allowed
paths; scored/win-prob metrics; S1; purchases; API keys; betting vocabulary.
REQUIRED INPUTS: plan plans/PLAN_winprob_playerfeat_prep_v1.md; predecessor lane docs at
.worktrees/winprob-playerdata-prep-v1/integration/lanes/A_NBA/{FEATURE_PROPOSALS.md,
PIT_AUDIT.md, COVERAGE_SCHEMA.md, DOWNLOAD_MANIFEST.md}; predecessor manifest
~/.my-quantitative-data/playerdata-prep-v1/nba/download_manifest.json (3 sampled seasons);
schedule corpus ~/.my-quantitative-data/nba-hoopr-v1/raw/nba_schedule_20{16..6}.csv
(14,254 rows, ESPN game_id keys).
DELIVERABLES (in lanes/A_NBA_FEAT/): build_features.py (runnable, deterministic),
FEATURE_SPEC.md (frozen definitions + missing-data rules + measured degeneracy notes),
DOWNLOAD manifest (new seasons json+md), COVERAGE_AUDIT.md (per season 2016–2026),
FEATURE_TABLE_MANIFEST.md (+json) with input/output sha256 + row counts, PIT_AUDIT.md
(worked as-of examples + leak guards), VERDICT_TABLE.md. Feature table parquet(s) outside
git under ~/.my-quantitative-data/playerfeat-prep-v1/nba/features/.
TEST COMMANDS: coverage joins + leak-guard asserts inside build_features.py --selftest.
STOP CONDITIONS: rights doubt on new downloads (stop, record BLOCKED_DATA_RIGHTS);
any same-game leakage suspicion (stop and document); >30 min compute (reduce scope to
spec+audit and record features NOT_RUN).
COMMIT-PUSH RULES: none — artifacts uncommitted; handoff JSON (zcode_orch_v3_handoff@1)
at lanes/DISPATCH/handoff_A_NBA_FEAT.json with dispatch_sha=00323ba…, commit_sha=null.
HANDOFF FORMAT: zcode_orch_v3_handoff@1 (task_id winprob-playerfeat-prep-v1-A-NBA-FEAT).
