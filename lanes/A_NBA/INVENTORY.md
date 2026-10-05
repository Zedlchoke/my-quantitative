# INVENTORY — NBA player-level data (Lane A, WINPROB-PLAYERDATA-PREP-V1)

Measured 2026-10-05. Every claim below states whether it is **on-disk (measured)**
or **source-publishes (verified from official docs/releases, not downloaded this
session unless stated)**.

## 1. On-disk inventory: NBA player box scores — NONE before this lane (PROVEN)

Search executed (commands + results):

```bash
find ~/.my-quantitative-data -iname "*player*"      # 37 hits, ALL WNBA or crosswalk
find ~/.my-quantitative-data -iname "*athlete*"     # 0 hits
find ~/.my-quantitative-data/nba-hoopr-v1 ~/.my-quantitative-data/nba-ng-prep-v1 -type f
```

- `~/.my-quantitative-data/nba-hoopr-v1/raw/` (EXTEND-ONLY): 11 schedule CSVs
  (`nba_schedule_2016..2026.csv`, 14,254 rows total — matches plan's game universe),
  `nba_schedule_crosswalk_2026.csv`, `play_by_play_2026.parquet`, provenance TSV,
  ATTRIBUTION.md. **No player box scores.**
- `~/.my-quantitative-data/nba-ng-prep-v1/` (EXTEND-ONLY): `pbp_2016_2025/*.parquet`
  (10 seasons) + `bdl_spotcheck/resp_*.json`. The PBP parquets contain event-level
  athlete fields (`athlete_id_1/2/3`, `athlete_name_1/2/3` — 63 columns verified on
  `play_by_play_2016.parquet`), i.e. player identities attached to play events.
  **This is NOT player-game box score data** (no per-player-game aggregates, no
  starter/DNP/minutes rows). Counted as adjacent player-adjacent data, not a
  player-box corpus.
- WNBA player files exist (`~/.my-quantitative-data/wnba-prep-v1/roster_audit/
  player_box_2002..2026.csv`) — **different league, out of lane-A scope** (Lane B).
- balldontlie spotcheck JSONs are one-date per-season game-list samples, not player stats.

Conclusion: expectation "NONE for NBA player box scores" **confirmed by exhaustive
filename search** of all `~/.my-quantitative-data` dirs on 2026-10-05.

## 2. What sources publish (verified from official sources this session)

### hoopR ecosystem (primary candidate) — PUBLISHES NBA player box scores

Evidence chain (all fetched and cached under
`~/.my-quantitative-data/playerdata-prep-v1/nba/provenance/`):

1. `sportsdataverse/hoopR` man page `hoopR_loaders.Rd` (raw.githubusercontent.com,
   fetched 2026-10-05T07:18Z): "Loaders for full seasons of pre-scraped data from
   the `sportsdataverse/hoopR-{nba,mbb}-data` releases on `sportsdataverse-data`",
   table entry: `load_nba_player_box()` → "NBA player boxscores".
2. `hoopR` `_pkgdown.yml` (fetched 2026-10-05): exports `load_nba_player_box`
   (NBA Data Functions) and `load_nba_stats_player_boxscores` (NBA Stats API
   loaders). Docs site `hoopr.sportsdataverse.org/reference/load_nba_player_box.html`
   currently redirects to the loaders page (consolidated); the function remains an
   official export per `_pkgdown.yml`.
3. `hoopR` README (fetched 2026-10-05): "`load_nba_*()` ... bulk-data loaders
   backed by the `sportsdataverse-data` release repos"; NBA (ESPN) pipeline repo
   documented as `github.com/sportsdataverse/hoopR-nba-data`; NBA Stats API repo
   as `github.com/sportsdataverse/hoopR-nba-stats-data`; assets at
   `github.com/sportsdataverse/sportsdataverse-data/releases`.
4. Distribution store `sportsdataverse/sportsdataverse-data` release tag
   `espn_nba_player_boxscores` (GitHub API, cached 2026-10-05): assets
   `player_box_2002.csv/.parquet/.rds` … `player_box_2026.csv/.parquet/.rds`
   — **25 seasons** (ESPN ending-year labels; e.g. label 2016 = 2015-16 season),
   plus `timestamp.txt` (store last rebuild 2026-09-09 01:17:39 EDT) and
   `package_function.*`. Release created 2023-03-29; assets rebuilt
   2026-05-30 (2016) / 2026-08-26 (2021) / 2026-09-09 (2026).
5. `hoopR-nba-data` / `hoopR-nba-stats-data` repos themselves carry **no GitHub
   releases and no tags** (verified via `git ls-remote` + API: empty release
   lists) — they are the pipeline repos; the artifacts land in the
   `sportsdataverse-data` release store. Additional related NBA tags exist in the
   store (NOT downloaded this session): `espn_nba_game_rosters`,
   `espn_nba_rosters`, `espn_nba_player_core`, `espn_nba_player_season_stats`,
   `espn_nba_depthcharts`, `espn_nba_injuries`, `espn_nba_shots`,
   `espn_nba_team_boxscores`, `espn_nba_pbp`.

### balldontlie — NOT verified for player stats, NOT used

Per plan inheritance: balldontlie Free covers Teams/Players/Games endpoints only;
this lane did **not** use the key (kept in Keychain, unused) and did not assume
player-stats availability. Left to Lane R.

## 3. Downloaded and checked this session

See `DOWNLOAD_MANIFEST.md` + `download_manifest.json`: samples for store labels
2016, 2021, 2026 (CSV format) — 50.5 MB total, sha256-verified, re-download
determinism proven. Full season-level schema/coverage audit in
`COVERAGE_SCHEMA.md`.

## 4. Gaps between published and on-disk (before this session)

- Player box 2002–2026: published, was NOT on disk. Now sampled (3 seasons).
- Game rosters / injuries / depth charts / shots / player season stats: published
  by the same store, NOT on disk, NOT downloaded this session (out of lane scope).
