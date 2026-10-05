# DISPATCH — Lane A · DATA NORMALIZATION (task wbap-a-data, cycle WNBA-WINPROB-PREP-V1)

ROLE: quant-explorer (data authority + normalization; A3-equivalent). Research + audit ONLY.
OBJECTIVE: build the normalized WNBA 1997+ game-universe spec from the wehoop/stats corpus +
PIT audit. NO metrics on outcomes, NO scored computation, NO win-prob numbers. WNBA data
only — NBA evidence is context, never input.

ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration
BRANCH: orca/wnba-winprob-prep-v1-integration (you do NOT commit; controller lands your files)
EXPECTED BASE SHA: run `git -C /Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration rev-parse HEAD` and record it in your handoff as dispatch_sha/actual_start_sha.
CYCLE: WNBA-WINPROB-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · NO GO phrase

ALLOWED PATHS (write):
- lanes/A_DATA/** (your lane directory only, inside the integration worktree)
- ~/.my-quantitative-data/wnba-prep-v1/** (new downloads/audits, outside git)

FORBIDDEN: any file outside the paths above; any frozen artifact/ledger of any cycle
(.worktrees/winprob-ng-prep-v1/**, .worktrees/nba-winprob-scored-v1/**,
.worktrees/nfl-winprob-ng-prep-v1/** (foreign live chat) — ALL READ-ONLY evidence);
plans/**; research/control/**; push/merge/rebase/commit; credentials; direct scraping of
wnba.com / stats.wnba.com / ESPN / Sports Reference (rights FAIL recorded already);
purchases; full-history bulk mirror (optional extension is census-first, see deliverable 1f).

REQUIRED INPUTS (read-only):
- Corpus: ~/.my-quantitative-data/wnba-v1/raw/ (espn_schedules 2002–2026; wnba_stats_
  schedules 1997–2026; espn_sample_2025 team/player box + pbp; DATA_MANIFEST.md sha256s;
  ATTRIBUTION.md; audit_results.json) — EXTEND-ONLY, never modify existing bytes.
- Evidence memo: /Users/hoangminhlong/my-quantitative/.worktrees/winprob-ng-prep-v1/integration/lanes/B_WNBA/WNBA_SOURCE_AUDIT.md
  (rights table, coverage census, rename map, timezone flavors, forfeit/placeholder law,
  NOT_RUN_PIT) + DATA_MANIFEST.md + audit_script.py.
- Plan: plans/PLAN_wnba_winprob_prep_v1.md (in-tree).

DELIVERABLES (all under lanes/A_DATA/):
1. GAME_UNIVERSE_SPEC_WNBA_1997PLUS.md — the normalization law, MEASURED with python/pandas
   (row counting allowed; win-prob metrics not):
   (a) identity + join law per source (ESPN game_id; stats-side season-prefixed game_id;
       cross-source join via display_name / wnba_crosswalk release — NEVER raw ESPN
       abbreviations, measured unreliable pre-2011 incl. the 2002 DET/TUL artifact);
   (b) franchise rename/relocation map re-verified FROM THE DATA with season boundaries
       (Starzz→SAN→DAL merge tree; Miracle→CON; Shock DET→TUL→(merge DAL); SAS→LVA 2018;
       defunct CHA/CLE/HOU/SAC/MIA/POR end years; expansion ATL 2008 / CHI 2006 / GSV 2025 /
       TOR+PDX 2026) + one canonical team-key table output;
   (c) timestamp canonicalization: the 4 measured flavors (ESPN schedule UTC instant; ESPN
       box venue-local+offset; ESPN pbp UTC wallclock; stats naive local date) → one
       canonical tip_utc law, DST-sampled;
   (d) filter/exclusion law APPLIED with per-season measured counts: keep
       status_type_state=='post'; drop Forfeit (exactly 1: 2018-08-03, 0–0) + Postponed
       details; drop/flag All-Star alias rows (EAST/WEST/ALL/DEL/PAR/CLA/COOP/WNBASTARS);
       drop TBD if-necessary placeholders; NEVER filter on score presence (unplayed rows
       pre-filled 0–0); neutral-site flag (15 rows) carried; Commissioner's Cup rows (2021+,
       embedded in RS) flagged for separate report; playoffs season_type=3 separate;
       2020 Wubble 147 games kept as real;
   (e) per-season census 1997–2026 (played RS/playoff counts after the filter law) + the
       ESPN-vs-stats reconciliation diff table re-measured;
   (f) OPTIONAL extension census (NOT a full mirror): depth census of box/pbp/rosters
       availability per era (which seasons have team_box/player_box/pbp on each side;
       what a successor TRAIN window would need); pull ONLY rights-cleared release assets
       needed to answer the census (e.g. one mid-era box file + game_rosters coverage list),
       within etiquette, recorded in the manifest.
2. PIT_AUDIT_WNBA.md — every candidate feature class: pre-game knowability verdict.
   Release assets are current-state snapshots with NO publication timestamps ⇒ rolling
   window features must use strictly-prior-game inputs under the canonical clock;
   player_box active/DNP/starter fields are POST-GAME facts — forbidden as pre-game
   features; injury/lineup stays NOT_RUN_PIT unless a rights-verified archive with real
   publish timestamps is proven (candidate list + why each fails, else).
3. DOWNLOAD_MANIFEST.md — anything newly downloaded: URL, release tag, pull time UTC,
   sha256, size, license note. $0 only.
4. handoff_A.json — schema zcode_orch_v3_handoff@1 at EXACT path lanes/A_DATA/handoff_A.json
   (task_id "wbap-a-data", cycle_id "WNBA-WINPROB-PREP-V1", role "quant-explorer",
   lane "A_DATA", dispatch_sha = measured HEAD, actual_start_sha = same, commit_sha =
   "NOT_COMMITTED_CONTROLLER_LANDED", changed_paths, tests [], authority_claims, known_
   limitations, incidents, tree_status "clean", workers 0, outputs).

TEST COMMANDS: shasum -a 256 on new downloads; python/pandas row counts (read-only,
SCHEMA/COVERAGE only).

STOP CONDITIONS: rights doubt on any new asset → BLOCKED_DATA_RIGHTS-candidate + continue;
download failure after 2 retries → NOT_RUN_DOWNLOAD + continue; plan conflict → record in
handoff.

COMMIT RULES: no commits; leave files untracked in lanes/A_DATA/.
