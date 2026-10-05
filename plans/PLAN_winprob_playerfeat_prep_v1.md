# PLAN — WINPROB-PLAYERFEAT-PREP-V1 (frozen player-feature tables for NBA/WNBA + NFL crosswalk unblock, $0)

- cycle_id: WINPROB-PLAYERFEAT-PREP-V1 · asset: shared · ACTIVE_LIGHT, budget 0 scored, NO GO phrase
- owner authority 2026-10-05 (this chat): feature-PREP/data ONLY — build frozen player-feature tables
  from strictly pre-game-known information; pin sources, hashes, coverage, player/team keys and
  missing-data handling rules; propose few falsifiable hypotheses to compare LATER against each
  league's own baseline. For NFL: download the free players.parquet crosswalk, test joins with
  weekly stats/snap counts and 2026 freshness; the predecessor HOLD may be lifted ONLY on
  independent-verifier confirmation. Explicitly NOT a GO for any scored backtest, NOT authority to
  run win-prob metrics on real outcomes, no S1, no paper/live/betting, no purchases ($0), no push,
  no merge. Use ZCode controller + subagent lanes; one independent verifier lane.
- Predecessor law (re-measured 2026-10-05, registry + bytes): WINPROB-PLAYERDATA-PREP-V1 =
  PREP_COMPLETE_PENDING_OWNER_DECISIONS, lane D VERIFIED (0 BLOCKER/MAJOR, 1 MINOR + 2 INFO). This
  cycle is the successor step that plan's terminal clause authorizes (PREP_COMPLETE verdict + owner
  instruction + fresh registration). All prior cycles' frozen sources/results/ledgers are
  read-only evidence.

## Inheritance (from registry + disk, re-measured 2026-10-05)

- NBA: player box sampled 2016/2021/2026 sha-pinned at `~/.my-quantitative-data/
  playerdata-prep-v1/nba/` (100% played-join, 0 dups); game universe 14,254 rows 2016–2026 keyed by
  ESPN `game_id` at `~/.my-quantitative-data/nba-hoopr-v1/` (EXTEND-ONLY); missing seasons
  2017–2020, 2022–2025 must be downloaded fresh here with full provenance. Baseline law: B1* =
  B1-d own-Elo K=32 HCA=100 FROZEN (NBA-WINPROB-SCORED-V1 TERMINAL); T1 team-rest/form ancestry
  veto applies verbatim (lanes/A_NBA/FEATURE_PROPOSALS.md header).
- WNBA: corpus `~/.my-quantitative-data/wnba-prep-v1/roster_audit/` player_box + game_rosters
  2002–2026 (50 CSVs, hash-verified; read-only). Scope laws: franchise 20-key lineage
  (`team_key_table.csv`, never raw abbreviations); coverage floor ≥90% seasons 2004+, minutes
  quality 2013+ for minutes-weighted variants; `active` field unusable; opening-roster v1
  NOT_RUN_PIT, v2 = game-1 membership used only from game 2 onward; era 1997–2001 warm-up-only.
- NFL: weekly player stats + snap_counts 2024–2026 sha-pinned at `~/.my-quantitative-data/
  playerdata-prep-v1/nfl/`; predecessor HOLD blockers: (1) target-game injury/active/DNP
  NOT_RUN_PIT — NO per-record publish timestamps (unchanged law; stays NOT_RUN_PIT here
  regardless), (2) players.parquet GSIS↔PFR crosswalk not downloaded — THIS cycle's lane C job,
  (3) snap_counts 2026 in-season lag ≤1 week, (4) release-cadence (not row-level) availability.
  Baseline law: NFL B1* = B1-c own-Elo K=40 HCA=0 FROZEN.
- Rights law (lane R + verifier re-verification): hoopR-nba-data CC BY 4.0, sportsdataverse-data
  MIT, nflverse-data CC BY 4.0 (all verbatim pinned on disk); balldontlie Free = metadata only.
  Underlying ESPN/league data rights for publication/commercial use remain UNVERIFIED — internal
  research only, fail-closed.
- PIT law (doctrine §13, carried): three times (event/effective/available); same-game player
  stats of the target game BANNED as features; target-game roster/active/starter/DNP/injury
  status = NOT_RUN_PIT unless a pre-game publish timestamp is evidenced (none exists today);
  prior-games aggregates PIT-safe only via the proven as-of join on tip/kickoff UTC with strict
  inequality. Feature tables must carry the as-of timestamp columns used.

## Tasks (owner round 2026-10-05)

1. Lane A — NBA FEATURE TABLE: download missing hoopR player_box seasons (2017–2020, 2022–2025)
   to `~/.my-quantitative-data/playerfeat-prep-v1/nba/raw/` with URL+version+timestamp+bytes+
   sha256 per file + ATTRIBUTION.md (extend predecessor manifest format); per-season coverage
   audit vs the 14,254-row schedule universe (played-join rate, dups, DNP rows, identity-less
   rows, schema drift); BUILD the frozen NBA player-feature table (parquet outside git) for the
   3 pre-registered groups from lanes/A_NBA/FEATURE_PROPOSALS.md (A: minutes-mass/rotation load,
   B: top-player form vs own baseline, C: key-player absence from prior games) — exact scalar
   definitions frozen in FEATURE_SPEC.md incl. OT normalization, ≥5-team-games gate with neutral
   values, same-team-10-games trade guard, season_type exclusion laws; one row per (game_id,
   team side), as-of columns (tip_utc, as_of_join_digest) embedded; FEATURE_TABLE_MANIFEST.md
   with input/output sha256 + row counts + per-season coverage + missing-data rule outcomes.
   No outcome columns anywhere near the table; no win-prob metric computed.
2. Lane B — WNBA FEATURE TABLE: from the read-only corpus build the frozen WNBA player-feature
   table per lanes/B_WNBA/FEATURE_PROPOSALS.md groups (A: roster continuity linked to W-H2 —
   v2 as-of law only, B: minutes-mass/load, C: top-player form + absence proxy with DNP 2012+
   law), 20-key lineage joins, coverage floors enforced + disclosed per season; same
   manifest discipline; parquet outside git at `~/.my-quantitative-data/playerfeat-prep-v1/wnba/`.
   No WNBA downloads expected (corpus exists; re-hash spot sample first).
3. Lane C — NFL CROSSWALK UNBLOCK: download nflverse-data `players` release players.parquet
   ($0) to `~/.my-quantitative-data/playerfeat-prep-v1/nfl/raw_players/` with full provenance +
   re-hash determinism spot check; join tests: weekly stats (`gsis_id`) ↔ players, snap_counts
   (`pfr_player_id`) ↔ players (`pfr_id`), coverage rates per season 2024/2025/2026 + position/
   team completeness + 2026 freshness (release timestamp, 32-team presence, current-season
   roster share); verdict recommendation: LIFT or KEEP predecessor HOLD, with named residual
   blockers. Target-game status fields stay NOT_RUN_PIT (law above). No feature build for NFL
   this cycle.
4. Lane D — INDEPENDENT VERIFIER (after A/B/C land; never repairs): re-measure vs bytes — spot
   re-hash downloads + outputs, re-join rates, independently recompute feature values for a
   sample of games with fresh code (leak audit: strict as-of inequality, target-game absence,
   neutral/fallback values per spec), missing-data rule behavior, PIT verdict logic, trial
   accounting (0 scored; grep for metric patterns), boundaries compliance, and an explicit
   CONFIRM/DISCONFIRM verdict on lane C's HOLD recommendation.

## Boundaries

- No scored computation, no win-prob/calibration metric on real outcomes (feature construction,
  coverage counting and PIT audits allowed), no S1, no paper/live, no betting language, no
  purchases, no accounts, no keyed signups, no push, no merge, no edits to frozen
  artifacts/ledgers/registries by lanes. Registry writes only via researchctl from root
  (controller). No API key values anywhere.
- Root checkout = control plane only. Lanes write ONLY inside
  `.worktrees/winprob-playerfeat-prep-v1/integration/lanes/<their-dir>/` (+ handoff JSON at
  their dispatch handoff_path) and data outside git under `~/.my-quantitative-data/
  playerfeat-prep-v1/`. Existing data dirs (playerdata-prep-v1, wnba-prep-v1, nba-*, nfl-*)
  are EXTEND-ONLY/read-only.
- Lane artifacts land uncommitted; the controller inspects and commits (one semantic commit per
  lane). Language law: calibration/forecasting vocabulary only. Heavy jobs take the global lock
  via researchctl and release it in finally.

## Artifacts

`lanes/A_NBA_FEAT/ · lanes/B_WNBA_FEAT/ · lanes/C_NFL_CROSSWALK/ · lanes/D_VERIFY/ ·
lanes/DISPATCH/` under the integration worktree; each lane ends with handoff JSON
`zcode_orch_v3_handoff@1` at its handoff_path. Data: `~/.my-quantitative-data/
playerfeat-prep-v1/{nba,wnba,nfl}/`.

## Terminal outcomes (negative-first)

PREP_COMPLETE_PENDING_OWNER_DECISIONS | BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING | TECHABORT_*.
This cycle registers no GO phrase and consumes none. A scored player-feature successor (arming
features vs each league's frozen baseline) needs this cycle's PREP_COMPLETE verdict + fresh
registration + freeze + A7 prelaunch + owner typed GO at its own gate. The NFL feature lane
additionally remains gated on lane D's HOLD verdict.
