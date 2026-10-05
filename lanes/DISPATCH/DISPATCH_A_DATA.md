# DISPATCH — Lane A · DATA NORMALIZATION (task nbang-a-data, cycle NBA-WINPROB-NG-PREP-V1)

ROLE: quant-explorer (data authority + normalization; A3-equivalent). Research + audit ONLY.
OBJECTIVE: build the normalized NBA 2016+ game-universe spec from the hoopR corpus + BDL spot
cross-check + PIT audit. NO metrics on outcomes, NO scored computation, NO win-prob numbers.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-ng-prep-v1/integration
BRANCH: orca/nba-winprob-ng-prep-v1-integration (you do NOT commit; controller lands your files)
EXPECTED BASE SHA: run `git -C /Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-ng-prep-v1/integration rev-parse HEAD` and record it in your handoff as dispatch_sha/actual_start_sha.
CYCLE: NBA-WINPROB-NG-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write):
- lanes/A_DATA/** (your lane directory only, inside the integration worktree)
- ~/.my-quantitative-data/nba-ng-prep-v1/** (new BDL cross-check outputs, outside git)

FORBIDDEN: any file outside the paths above; any frozen artifact/ledger of any cycle
(.worktrees/nba-winprob-scored-v1/**, .worktrees/nfl-winprob-ng-prep-v1/** (foreign live chat),
.worktrees/winprob-ng-prep-v1/** — ALL READ-ONLY evidence); plans/**; research/control/**
(no control-file writes); push/merge/rebase/commit; credentials or the BDL key VALUE in any
artifact; bulk BDL download (free-tier 5 req/min is a spot-sample budget only); purchases.

REQUIRED INPUTS (read-only):
- Corpus: ~/.my-quantitative-data/nba-hoopr-v1/raw/ (11 schedule files 2016–2026, pbp 2026,
  crosswalk 2026, _download_provenance.tsv, ATTRIBUTION.md) — EXTEND-ONLY, never modify bytes.
- Evidence memos: /Users/hoangminhlong/my-quantitative/.worktrees/winprob-ng-prep-v1/integration/lanes/A_NBA_POST2015/NBA_POST2015_SOURCES.md (rights + dedupe law + crosswalk law)
  and .../lanes/T2_BDL_ADAPTER/BDL_STATUS_AND_COMPARISON.md + bdl_adapter.py + bdl_t2c_crosscheck.py
  (BDL usage pattern; key is in macOS Keychain `balldontlie`/`winprob-ng`, read via the adapter,
  never printed).
- Plan: plans/PLAN_nba_winprob_ng_prep_v1.md (in-tree).
- Old-cycle baseline facts: .worktrees/nba-winprob-scored-v1/integration/research/control/NBA-WINPROB-SCORED-V1/results/scored_summary.json (B1* K=32/HCA=100 LL 0.5987; READ-ONLY).

DELIVERABLES (all under lanes/A_DATA/):
1. GAME_UNIVERSE_SPEC_NBA_2016PLUS.md — the normalization law, MEASURED on the corpus with
   python/pandas (row counting is allowed; win-prob metrics are not):
   (a) identity: ESPN game_id primary key; one-row-per-game law; uniqueness re-verified;
   (b) tip UTC: canonicalization of game_date_time (local+offset) and start_date (UTC) into
       tip_utc; DST-correctness sampled; never the coarse `date` column;
   (c) dedupe/exclusion law APPLIED with per-season measured counts: keep
       status_type_completed==True; exclude All-Star EAST/WEST rows; identify + flag NBA Cup
       final rows (2023+); identify postponed duplicate listings; output per-season PLAYED
       regular/play-in/playoff game counts 2016–2026 (raw vs deduped);
   (d) season composition: season_type 2/5/3 splits, playoffs separate by design;
   (e) crosswalk law restated + re-verified on a sample (ESPN game_id primary; 2026+ nba_
       crosswalk; to-538-era join = LOCAL date + home team, never the UTC-shifted game_id date);
   (f) spread-feature coverage census (game_spread/home_favorite) across ALL 2016+ pbp seasons
       if downloadable at $0 within etiquette — else per-plan NOT_RUN with the 2026-sample
       number cited and clearly scoped.
2. BDL_CROSSCHECK_NBA.md — spot-sample cross-check vs hoopR using the T2 adapter pattern:
   ≤25 games, ≥5 seasons (must include 2016, 2020, 2026), targeted dates[] queries, hard
   5 req/min throttle (≥13s spacing), record every request URL-pattern (never the key),
   response counts, field-level match verdict (date/home/away/score/tip_utc), match rate,
   and any mismatch escalated as a data-contract BLOCKER candidate (never silently absorbed).
   New request/response artifacts (redacted) under ~/.my-quantitative-data/nba-ng-prep-v1/.
3. PIT_AUDIT_NBA.md — for every candidate feature class named in the plan (results-derived
   ratings, schedule-derived rest/travel, box/pbp-derived priors, spread line, injury/roster):
   pre-game knowability verdict + input-freeze law; injury/roster = NOT_RUN_PIT unless a
   rights-verified archive with per-record publish timestamps ≤ tip − cadence is proven on a
   spot sample (candidate list + why each fails, else).
4. DOWNLOAD_MANIFEST.md — anything newly downloaded: URL, release tag, pull time UTC, sha256,
   size, license note. $0 only.
5. handoff_A.json — schema zcode_orch_v3_handoff@1 at EXACT path lanes/A_DATA/handoff_A.json
   (task_id "nbang-a-data", cycle_id "NBA-WINPROB-NG-PREP-V1", role "quant-explorer",
   lane "A_DATA", dispatch_sha = measured HEAD, actual_start_sha = same, commit_sha =
   "NOT_COMMITTED_CONTROLLER_LANDED", changed_paths, tests [], authority_claims [your verdicts],
   known_limitations, incidents, tree_status "clean", workers 0, outputs [artifact list]).

TEST COMMANDS: shasum -a 256 on new downloads; python/pandas row counts from the repo's
.venv if importable (read-only compute on SCHEMA/COVERAGE only).

STOP CONDITIONS: BDL quota/errors → record NOT_RUN_BDL_CROSSCHECK and proceed with the rest;
rights doubt on any new asset → BLOCKED_DATA_RIGHTS-candidate + continue; conflict with the
plan → stop, write the conflict into handoff known_limitations/incidents.

COMMIT RULES: you make NO commits (controller lands). Leave files untracked in lanes/A_DATA/.
