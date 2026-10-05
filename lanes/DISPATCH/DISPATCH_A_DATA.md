# DISPATCH — Lane A · DATA (task nflng-a-data, cycle NFL-WINPROB-NG-PREP-V1)

ROLE: quant-explorer (data authority audit; A3-equivalent). Research + audit ONLY.
OBJECTIVE: audit nflverse $0 data rights/provenance/coverage for the next-gen NFL win-prob
program; classify 2026 played-vs-future relative to the cycle prospective epoch; verdict
injury/availability PIT. NO metrics on outcomes, NO scored computation.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-prep-v1/lane-a-data
BRANCH: orca/nfl-ngprep-a-data
EXPECTED BASE SHA: the HEAD of your worktree at spawn (controller-created from the bootstrap commit; record git rev-parse HEAD output in your handoff as dispatch_sha) (verify with git rev-parse HEAD before starting)
CYCLE: NFL-WINPROB-NG-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write):
- lanes/A_DATA/** (your lane directory, this worktree)
- ~/.my-quantitative-data/nfl-ng-prep-v1/** (downloads, outside git)
- ~/.my-quantitative-data/nfl-nflverse-v1/** (EXTEND ONLY: add new files under a clearly
  named refresh/ subdir or new filenames; never overwrite/delete existing bytes)

FORBIDDEN: any file outside the paths above; any frozen artifact/ledger of any cycle (including
.worktrees/nfl-winprob-prep-v1/** and .worktrees/nfl-winprob-scored-v1/** — READ-ONLY evidence);
plans/**; research/control/** except nothing (this lane writes no control files); push/merge/
rebase; credentials in any artifact; buying anything. Reads of other worktrees are allowed.

REQUIRED INPUTS (read-only evidence):
- Existing archive: ~/.my-quantitative-data/nfl-nflverse-v1/ (raw/games.csv, pbp 2021-2025
  parquets, ATTRIBUTION.md, timestamp_*.json)
- Old PREP audit: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-prep-v1/integration/PREP_SUMMARY_NFL.md
  and lanes/* data-audit artifacts (evidence of past coverage findings)
- Terminal cycle data contract: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-scored-v1/integration/research/control/NFL-WINPROB-SCORED-V1/**
  (quarantine list: odds columns, pbp-derived features, injuries NOT_RUN_PIT)
- Cycle plan: plans/PLAN_nfl_winprob_ng_prep_v1.md (in-tree)

DELIVERABLES (all under lanes/A_DATA/):
1. DATA_AUDIT_NFL_NG.md — for each nflverse asset used by a win-prob program (games/schedules
   2000–2026, results, pbp): license text verbatim + URL (CC BY 4.0 claim must be re-verified,
   not assumed), provenance chain, measured coverage per season (row counts, teams, games),
   kickoff-time schema + UTC conversion story, team-ID crosswalk & franchise moves, neutral-site
   flag availability, tie/cancel/forfeit handling, schema drift 2000 vs 2026, publish/as-of
   story (release cadence, whether current-week data is post-game compiled).
2. GAMES_2026_CLASSIFICATION.md — pull the 2026 schedule/results AS OF NOW; measure which games
   have final scores (already played) vs future; state the exact count of played games and the
   earliest future kickoff UTC; PROSPECTIVE EPOCH of this cycle = 2026-10-05T03:13:51Z
   (bootstrap commit time, controller-measured); every played game is NOT_RUN prospective.
3. INJURY_PIT_VERDICT.md — injury/availability sources: only if BOTH (a) $0 rights verified
   verbatim AND (b) per-record publish timestamps provably ≤ kickoff − report cadence on a
   SPOT-CHECKED SAMPLE; else NOT_RUN_PIT with candidate list + why each fails. No retro-fill.
4. DOWNLOAD_MANIFEST.md (+ files under ~/.my-quantitative-data/nfl-ng-prep-v1/) — every
   download: URL, version/release tag, pull time UTC, sha256, size, license note. If you
   re-derive anything from the existing archive, record source path + sha256 of inputs.
   $0 only: no accounts, no keys, no purchases.
5. handoff_A.json — schema zcode_orch_v3_handoff@1 at EXACT path
   lanes/A_DATA/handoff_A.json (task_id "nflng-a-data", cycle_id, role, lane "A_DATA",
   dispatch_sha = base SHA, actual_start_sha, commit_sha = your commit, changed_paths,
   tests [], authority_claims [your verdicts], known_limitations, incidents, tree_status,
   workers 0, outputs [artifact list]).

TEST COMMANDS: shasum -a 256 on every downloaded/derived file (record in manifest);
row-count/crosscheck counts via python/pandas from .venv if available (read-only compute on
SCHEMA/COVERAGE is allowed — it is not outcome computation; computing WIN-PROB METRICS or
model scores on game outcomes is FORBIDDEN).

STOP CONDITIONS: rights text not verifiable for an asset → mark that asset
BLOCKED_DATA_RIGHTScandidate and continue with the rest; download failures after 2 retries →
record NOT_RUN_DOWNLOAD and proceed with existing archive audit; any instruction conflict with
the plan → stop and write the conflict into handoff known_limitations/incidents.

COMMIT RULES: exactly ONE clean commit on your branch (message prefix "NFL-NG-PREP lane A:"),
stage by pathspec only (no git add -A), never push/merge. Verify pwd+branch+HEAD before commit.
