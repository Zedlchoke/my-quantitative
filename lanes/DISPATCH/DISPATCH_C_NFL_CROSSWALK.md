# DISPATCH — Lane C_NFL_CROSSWALK (WINPROB-PLAYERFEAT-PREP-V1)

ROLE: data lane. OBJECTIVE: unblock (or keep) the predecessor NFL feature HOLD by downloading
the free nflverse-data `players` release players.parquet and testing GSIS↔PFR joins + 2026
freshness. NO feature build this cycle.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/winprob-playerfeat-prep-v1/integration
BRANCH: orca/winprob-playerfeat-prep-v1-integration · BASE/DISPATCH SHA: 00323ba64ebbbc107d05fcf926c7cadf8dfa7acd
ALLOWED PATHS (write): lanes/C_NFL_CROSSWALK/** and
~/.my-quantitative-data/playerfeat-prep-v1/nfl/raw_players/** (+ provenance json/logs).
READ-ONLY: predecessor data ~/.my-quantitative-data/playerdata-prep-v1/nfl/** (weekly stats +
snap_counts + manifest with sha256s), predecessor lanes/C_NFL docs.
FORBIDDEN: git; writes to predecessor dirs; scored metrics; purchases; keys; betting vocabulary.
REQUIRED INPUTS: plan; predecessor lanes/C_NFL/{VERDICT_TABLE.md, COVERAGE_SCHEMA.md,
PIT_AUDIT.md, DOWNLOAD_MANIFEST.md}; data files listed there.
TESTS (all measured from bytes): (1) download players.parquet from the `players` release
(URL pattern https://github.com/nflverse/nflverse-data/releases/download/players/players.parquet)
with full provenance (url, http, downloaded_utc, bytes, sha256, asset updated timestamp via 1
unauthenticated GitHub API call if needed) + re-download determinism spot check; (2) license
unchanged: re-fetch LICENSE.md live, compare sha256 vs pinned 2a82ac9bbc3e3ee0… (byte-identical
expected; record divergence if any); (3) schema audit: columns incl. gsis_id, pfr_id, name,
position, team, status/handedness etc., row count, unique gsis_id, unique pfr_id, null rates;
(4) JOIN weekly stats (gsis_id ↔ players.gsis_id) per season 2024/2025/2026: match rate of
distinct player_ids, plus unmatchable-row census; (5) JOIN snap_counts (pfr_player_id ↔
players.pfr_id) same; (6) 2026 freshness: release last_updated timestamp, count of players on
2026 active rosters (team column non-null current), 32-team presence, cross-source consistency
spot checks (e.g. notable QB ids present in both weekly stats and snap_counts via crosswalk);
(7) verdict recommendation: LIFT or KEEP predecessor HOLD with named residual blockers;
target-game status fields remain NOT_RUN_PIT regardless (no publish timestamps — restated).
DELIVERABLES: lanes/C_NFL_CROSSWALK/{DOWNLOAD_MANIFEST.md (+json), SCHEMA_AUDIT.md,
JOIN_TESTS.md, FRESHNESS_2026.md, VERDICT_TABLE.md} + handoff JSON.
STOP CONDITIONS: license divergence (stop, BLOCKED_DATA_RIGHTS); join machinery doubt.
COMMIT-PUSH: none. HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_C_NFL_CROSSWALK.json
(task_id winprob-playerfeat-prep-v1-C-NFL-CROSSWALK, dispatch_sha=00323ba…, commit_sha=null).
