# COVERAGE & SCHEMA — Lane C (NFL PLAYER DATA) · WINPROB-PLAYERDATA-PREP-V1

All numbers measured from downloaded bytes 2026-10-05 (pandas 3.0.5 / pyarrow). Files per
`DOWNLOAD_MANIFEST.md`. Release as-of: `stats_player` build 2026-10-05T05:30:28Z.

## 1. Weekly player stats (`stats_player_week_{season}.parquet`)

| file | rows | cols | distinct games | weeks | season_type |
|---|---|---|---|---|---|
| stats_player_week_2024.parquet | 18,983 | 150 | 285 | 1–18 REG; 19–22 POST | REG 272 games, POST 13 (wk19:6 WC, wk20:4 DIV, wk21:2 CON, wk22:1 SB) |
| stats_player_week_2025.parquet | 19,422 | 150 | 285 | 1–18 REG; 19–22 POST | REG 272, POST 13 (same shape) |
| stats_player_week_2026.parquet | 4,379 | 150 | 63 | 1–4 (REG only) | REG (season in progress) |

2026 in-progress status consistent with frozen split law (63 played / 209 future; prospective
window re-verified in PIT_AUDIT.md §3).

## 2. Keys and identity columns

- `player_id` — GSIS id, format `00-0033873` (e.g. P.Mahomes). **Missing on exactly one
  placeholder row per week** (2024: 22, 2025: 22, 2026: 4 = one per week 1–4): all-zero stat
  rows with NaN player_name/position (artifact, exclude from aggregates).
- `player_name` — **abbreviated** ("P.Mahomes"); `player_display_name` — full ("Patrick
  Mahomes"). Naming differs from the legacy `player_stats` release; use `player_id` as key.
- `position`, `position_group`, `team`, `opponent_team` (per-game team of record — handles
  mid-season trades correctly at week granularity).
- `game_id` — identical format to games.csv (`2024_11_KC_BUF`). `season`, `week`,
  `season_type` (REG/POST).

## 3. Stat blocks (150 cols)

Block counts programmatically verified (sum = 150, no overlaps):

- keys/meta: 12 (player_id, player_name, player_display_name, position, position_group,
  headshot_url, season, week, season_type, game_id, team, opponent_team)
- passing: 20 (completions…passing_epa, passing_cpoe, pacr, passing_10/16/20/40 depth bins)
- rushing: 12 (carries…rushing_epa, 10/12/20/40 depth bins)
- receiving: 19 (receptions, targets, …receiving_epa, racr, **target_share, air_yards_share,
  wopr** — share features ship in-file)
- defense: 20 (def_tackles_solo … def_2pt_made)
- misc/fumbles/returns/penalties/ST-TDs: 18 (misc_yards, fumble_recovery_*, penalties,
  punt_returns, kickoff_returns, special_teams_tds)
- kicking: 34 (fg_made…gwfg_distance incl. distance bins and made/missed lists)
- punting: 13 (pt_att…pt_net_yards)
- fantasy: 2 (fantasy_points, fantasy_points_ppr)
- **No snap/participation columns** in weekly stats — snap mass lives in the separate
  `snap_counts` release (downloaded 2025+2026, §5).

Selectively-populated columns (by design, not corruption): `passing_epa` non-null on 691/19,422
rows (2025) — only rows with pass attempts + pbp epa linkage; `rushing_epa` 2,356;
`receiving_epa` 4,537; `fg_long`/`fg_pct`/`fg_made_list` only on kicking rows.

## 4. Games join vs on-disk games.csv (`~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv`, 2026-10-04 pull)

| season | stats games | games.csv games | joined | stats-only | games-only |
|---|---|---|---|---|---|
| 2024 | 285 | 285 | **285 (100%)** | 0 | 0 |
| 2025 | 285 | 285 | **285 (100%)** | 0 | 0 |
| 2026 | 63 | 272 | **63 (100%)** | 0 | 209 (all future/unplayed — consistent with frozen split law) |

Team/opponent sanity on one-row-per-game sample: 285/285 + 285/285 + 63/63 consistent with
games.csv home/away (100%). Postseason game_types present in games.csv (WC/DIV/CON/SB) match
weekly-file POST weeks 19–22.

## 5. snap_counts (supporting source, downloaded)

- `snap_counts_2025.parquet`: 26,613 rows × 16 cols; 285 distinct games (= stats 2025);
  weeks 1–22. Cols: game_id, pfr_game_id, season, game_type, week, player, **pfr_player_id**,
  position, team, opponent, offense_snaps, offense_pct, defense_snaps, defense_pct, st_snaps,
  st_pct.
- `snap_counts_2026.parquet`: 4,579 rows, 49 distinct games, weeks 1–4 — **lags the stats
  release** (build 2026-10-02 vs stats 2026-10-05): 14 week-4 games missing at pull time.
  In-season cadence is slower than stats_player.
- Duplicates (pfr_player_id, game_id): 0 in both files.
- **Key caveat:** snap_counts keys on PFR ids, weekly stats on GSIS ids; joining the two
  requires the `players.parquet` crosswalk (published in the `players` release, not yet
  downloaded — flagged for FEATURE-PREP).
- Release-listing coverage: snap_counts 2012–2026; pbp_participation 2016–2025.

## 6. Season-aggregate variant (`stats_player_regpost_2025.parquet`)

2,025 rows × 148 cols. `season_type` ∈ {REG 1,496; REG+POST 524; POST 5}. Has `games` count,
`recent_team` (instead of per-game team/opponent_team); drops `week`/`game_id`/
`team`/`opponent_team`; adds `gwfg_distance_list`. Same 150-col core minus/plus the above.
Useful only for sanity/level checks — weekly files are the modeling substrate.

## 7. Duplicates, missing, per-game player counts

- Duplicates (player_id, game_id): **0** in all three weekly files (dropna player_id).
- Players per game (2024/2025): min 57, median 66–68, max 82, mean 66.5/68.1 — plausible
  (53-man rosters + practice-squad callups + special-teamers).
- Placeholder rows: 1/week all-zero NaN-player row (see §2) — deterministic artifact.
- Missing gametime in games.csv: 259 rows, **all season 1999** (kicked-off-time absent in the
  earliest season only) — relevant only if pre-2000 windows are ever used.

## 8. Schema drift across seasons

2024 vs 2025 vs 2026: identical column name lists **and** order (150 cols). No drift in the
observed window. Cross-season dtype consistency verified via identical read paths.

## 9. Offseason re-cut caveat (documented release-date)

nflverse re-releases whole-history files: weekly `stats_player_week_{2018..2025}` assets were
last rewritten 2026-08-13 (post-SB finalize) and change only at season boundaries; 2026 rewrites
~daily in-season. This lane's snapshot = `stats_player` build **2026-10-05T05:30:28Z**
(timestamp.json) — any future re-pull must re-hash and re-audit; sha256 in
DOWNLOAD_MANIFEST.md is the frozen evidence for this cycle. Prior seasons' historical stat
values are subject to nflverse corrections in re-cuts (post-hoc edits possible).
