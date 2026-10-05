# DISPATCH — Lane A_DATA (NFL-WINPROB-NG-SCORED-V1)

ROLE: data lane. OBJECTIVE: successor data provenance — pbp 2000–2017 for C3 train priors +
successor data audit (TRAIN list, neutral-site flag, kickoff fallback, fresh 2026 recount).
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration
BRANCH: orca/nfl-winprob-ng-scored-v1-integration · BASE/DISPATCH SHA: 832f6956b9afb82f3e7f14b0fcbd01688c049f5f
ALLOWED PATHS (write): lanes/A_DATA/** and ~/.my-quantitative-data/nfl-ng-scored-v1/**
(raw_pbp_2000_2017/, raw_schedules_fresh/, rights/, provenance/). READ-ONLY: everything else
incl. ~/.my-quantitative-data/nfl-nflverse-v1/** (archive pbp 2021–2025 + games.csv) and
nfl-ng-prep-v1/** (predecessor snapshots + rights).
FORBIDDEN: git; scored metrics; reading 2019–2025 outcome data for any evaluation purpose
(cite-only context allowed); purchases; keys; betting vocabulary.
REQUIRED INPUTS: plan plans/PLAN_nfl_winprob_ng_scored_v1.md; predecessor audit
.worktrees/nfl-winprob-ng-prep-v1/integration/lanes/A_DATA/DATA_AUDIT_NFL_NG.md (+ r1 handoff);
mechanisms doc lanes/B_MECHANISMS/MECHANISMS_NFL_NG.md (C3 spec §2).
TASKS: (1) download play_by_play_2000..2017.parquet (18 files, release `pbp`, URL pattern
https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_YYYY.parquet)
with URL+http+downloaded_utc+bytes+sha256 each + ATTRIBUTION.md + release timestamp.json;
spot re-download determinism on 1 file; (2) license re-fetch live, sha256 must equal pinned
2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111 (divergence ⇒ BLOCKED_DATA_
RIGHTS stop); (3) pbp coverage audit: rows + games per season vs games.csv season counts,
regular/post split, team-abbreviation domain vs 32-lineage map (relocations SD→LAC 2017,
STL→LA 2016, OAK→LV 2020), EPA column presence/non-null rates by season (C3 needs
EPA/play + play counts; verify `epa`, `posteam`, `defteam`, `season_type` populated 2000–2017);
(4) freeze facts: TRAIN season list = complete seasons 2000–2018 (1999 excluded — gametime
100% missing; restate from fresh bytes), neutral-site flag = games.csv `location` column
(HCA=0 law), kickoff fallback X = not activated (gametime 100% present 2000+; re-measure);
(5) fresh 2026 recount at audit time: re-download current games.csv snapshot into
raw_schedules_fresh/ + sha256 + measured counts (played/future, earliest future kickoff,
week-5 slate opener 2026_05_TB_DAL expected 2026-10-09T00:15Z — record actual); (6) C3
admissibility verdict: pbp snapshot story (completed seasons finalize post-SB; in-season
re-cuts) + season-boundary margin statement (prior-season last kickoff precedes new-season
first prediction by months) → PASS_PIT_SEASON_GRAIN or NOT_RUN_PIT for C3 with evidence.
DELIVERABLES: lanes/A_DATA/{DOWNLOAD_MANIFEST.md (+json), PBP_COVERAGE_AUDIT.md,
SUCCESSOR_DATA_AUDIT.md (freeze facts + 2026 recount + C3 verdict), VERDICT_TABLE.md}.
STOP CONDITIONS: license divergence; >60 min download stalls (record partial + resume note).
COMMIT-PUSH: none. HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_A_DATA.json
(task_id nfl-winprob-ng-scored-v1-A-DATA, dispatch_sha=832f695…, commit_sha=null).
