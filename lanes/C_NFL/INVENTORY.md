# INVENTORY — Lane C (NFL PLAYER DATA) · WINPROB-PLAYERDATA-PREP-V1

Measured 2026-10-05 (session UTC ~07:15–07:45). All commands and exit codes logged in the
session transcript; measurements below are from bytes, never inferred.

## 1. On-disk player-level inventory (READ-ONLY corpora re-measured)

### `~/.my-quantitative-data/nfl-nflverse-v1/` (prior corpus, pulled 2026-10-04)

| file | level | evidence |
|---|---|---|
| raw/play_by_play_2021..2025.parquet (5 files, ~20.2–20.6 MB each) | **PLAY-level, not weekly player stats** | `play_by_play_2024.parquet` = 49,492 rows × 372 cols; player columns are per-play *attributions* (`passer_player_id`, `rusher_player_id`, `receiver_player_id`, `td_player_name`, `punt_returner_player_id`, `pass_defense_1_player_id`, …). One row = one play (game_id + play_id), not one player-week. |
| raw/games.csv (2,182,449 B) | game-level schedule/results | 7,548 rows, seasons 1999–2026, 46 cols incl. `game_id, season, game_type, week, gameday, gametime` |
| raw/timestamp_pbp.json, timestamp_schedules.json | as-of markers | pbp last_updated 2026-10-04 05:03:18 EDT; schedules 2026-10-04 08:16:30 EDT |
| raw/ATTRIBUTION.md | provenance | nflverse-data CC BY 4.0 attribution + per-file sha256 table |
| derived/ (games_nfl.csv, features_nfl.csv, lineages, manifests) | team-level derived | no player-level tables |

### `~/.my-quantitative-data/nfl-ng-prep-v1/` (prior cycle, pulled 2026-10-05)

raw_schedules_20261005/, raw_schedules_r1_20261005/ (games.csv + release API JSON),
raw_injuries_20261005/ (injuries 2025/2026 — prior-cycle law: NO timestamp schema →
NOT_RUN_PIT, blocker carried), raw_teams_20261005/, rights/ (nflverse-data LICENSE.md CC BY 4.0
copy + nfldata DATASETS.md). No player-level stats tables.

### Full-tree sweep for player-level NFL files

Filesystem walk over all of `~/.my-quantitative-data/` for filenames containing `player`/`stat`:
every hit is a **WNBA** corpus (`wnba-prep-v1/roster_audit/player_box_*.csv`,
`wnba-v1/raw/espn_sample_2025/player_box_2025.*`) or unrelated (NWS weather stations, BOJ
statements). **No NFL player-level weekly stats file exists anywhere on disk.** Expectation
"NONE" from dispatch: CONFIRMED.

## 2. Published sources (verified from the nflverse-data release listing this session)

Source of truth: GitHub API
`https://api.github.com/repos/nflverse/nflverse-data/releases?per_page=100` (1 unauthenticated
call, HTTP 200, cached at `~/.my-quantitative-data/playerdata-prep-v1/nfl/release_api_listing.json`,
25 releases).

Key releases relevant to player-level NFL data:

| tag | release name | assets | what it publishes |
|---|---|---|---|
| `stats_player` | "Player Summary Stats" | 554 | **CURRENT weekly player stats store** (`stats_player_week_{season}.{parquet,csv,csv.gz,qs,rds}` per season; `stats_player_reg_`, `stats_player_post_`, `stats_player_regpost_` season aggregates). Release body (verbatim): *"Player stats in different summary levels created with `nflfastR::calculate_stats()`"*. `stats_player_week_2026.parquet` updated 2026-10-05T05:30:11Z (in-season cadence). |
| `player_stats` | `player_stats` | 1,822 | **Superseded store** — legacy weekly player stats (`player_stats_{season}.*`, `player_stats_season_*`, `player_stats_def_*`, `player_stats_kicking_*`); newest asset update 2025-05-07T08:22:06Z, i.e. frozen since the store re-organization. Not used. |
| `snap_counts` | `snap_counts` | 77 | per-player per-game snap counts 2012–2026 (`snap_counts_{season}.*`); 2026 file updated 2026-10-02T11:01:51Z. |
| `pbp_participation` | `pbp_participation` | 46 | per-player per-play participation 2016–2025 (`pbp_participation_{season}.*`). Not downloaded this session. |
| `players` / `players_components` | players | 7 / 12 | player-id crosswalks (`players.parquet` etc.). Needed to map GSIS ↔ PFR ids. Not downloaded this session. |
| `weekly_rosters` | `weekly_rosters` | 104 | weekly rosters 2002+ (`roster_weekly_{season}.*`). Not downloaded. |

Boundary note: the legacy `player_stats` tag ALSO contains `stats_player_week_*`-named assets
(dual-published until 2025-05); the CURRENT updating store is `stats_player` (verified by
2026-10-05 asset updates on `stats_player` vs frozen 2025-05-07 on `player_stats`).

## 3. Downloaded and checked this session

See `DOWNLOAD_MANIFEST.md` — 8 files (HTTP 200): weekly player stats 2024/2025/2026 (parquet),
season-aggregate `stats_player_regpost_2025.parquet`, snap_counts 2025/2026 (parquet), 2
release `timestamp.json` markers. Full sha256 provenance + byte-identical re-download proof
inside.
