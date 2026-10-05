# COVERAGE & SCHEMA — NBA player box samples (Lane A, WINPROB-PLAYERDATA-PREP-V1)

All numbers measured 2026-10-05 with pandas from the three downloaded CSVs
(`~/.my-quantitative-data/playerdata-prep-v1/nba/player_box_raw/`) against the
schedule corpus `~/.my-quantitative-data/nba-hoopr-v1/raw/nba_schedule_<season>.csv`
(EXTEND-ONLY, read-only). Command evidence in
`~/.my-quantitative-data/playerdata-prep-v1/nba/provenance/*.txt`.

## 1. Seasons

- **Store contents** (from cached release listing): `player_box_2002` …
  `player_box_2026` — 25 seasons, each in `.csv`/`.parquet`/`.rds`.
- **Downloaded + checked this session**: labels 2016, 2021, 2026 only.

## 2. Season label convention — CRITICAL NAMING NOTE

Both corpora use ESPN's **ending-year** season label, measured:

- store `player_box_2016.csv`: `season=2016`, game_date 2015-10-27 → 2016-06-19
- `nba_schedule_2016.csv`: `season=2016`, game_date 2015-10-27 → 2016-06-19
- 2021: 2020-12-22 → 2021-07-20; 2026: 2025-10-21 → 2026-06-13 (both files)

So store label 2016 = the 2015-16 season. The workspace convention text says
"NBA season 2016 = 2016-17" — a **1-year offset against the store/schedule
labels**. Join keys (`game_id`) are unaffected; **season naming in future
feature tables must state which convention it uses**. This lane reports ESPN
store labels as-is.

## 3. Rows, columns, keys

| season label | rows | cols | unique game_id | rows/game (mean) |
|---|---|---|---|---|
| 2016 | 33,715 | 57 | 1,317 | 25.6 |
| 2021 | 31,593 | 57 | 1,172 | 27.0 |
| 2026 | 34,883 | 57 | 1,326 | 26.3 |

Column set (57) is **identical across all three sampled seasons** (sorted-list
comparison; zero drift in sample). Columns:

```
active, assists, athlete_display_name, athlete_headshot_href, athlete_id,
athlete_jersey, athlete_position_abbreviation, athlete_position_name,
athlete_short_name, blocks, defensive_rebounds, did_not_play, ejected,
field_goals_attempted, field_goals_made, fouls, free_throws_attempted,
free_throws_made, game_date, game_date_time, game_id, home_away, minutes,
offensive_rebounds, opponent_team_* (11 cols), plus_minus, points, reason,
rebounds, season, season_type, starter, steals, team_* (13 cols),
team_winner, three_point_field_goals_attempted, three_point_field_goals_made,
turnovers
```

Key fields present: `game_id` (ESPN), `athlete_id`, `team_id`/`team_abbreviation`,
`minutes`, `starter`, `did_not_play`, `active`, `reason`, `ejected`,
`season_type` (2=regular, 3=playoffs, 5=play-in), `game_date_time`,
`home_away`. No separate DNP-reason column beyond `reason`.

## 4. Join vs schedule corpus (ESPN game_id)

| season | schedule rows | playerbox games | joined | join rate | orphans (playerbox ∉ schedule) | joined rows w/ `game_date_time` | w/ `start_date` |
|---|---|---|---|---|---|---|---|
| 2016 | 1,317 | 1,317 | 1,317 | **1.0000** | 0 | 1317/1317 | 1317/1317 |
| 2021 | 1,204 | 1,172 | 1,172 | **0.9734** | 0 | 1172/1172 | 1172/1172 |
| 2026 | 1,330 | 1,326 | 1,326 | **0.9970** | 0 | 1326/1326 | 1326/1326 |

- Every "missing" schedule game is `STATUS_POSTPONED` with 0-0 score (32 in
  2021 — COVID season; 4 in 2026; 0 in 2016). **Effective coverage = 100% of
  games actually played.** Zero orphan player-box games in all samples.
- Schedule rows carry `game_date_time` (local-with-offset) and `start_date`
  (UTC); they normalize to the same UTC instant on **100% of rows in all three
  seasons** (1317/1317, 1204/1204, 1330/1330) — the as-of join input is complete.

## 5. Players per game, duplicates, missing

- Players/game: 2016 min 23 / p50 26 / max 29; 2021 min 22 / p50 27 / max 31;
  2026 min 17 / p50 26 / max 34. Games with <24 player rows: 12 (2016), 2 (2021),
  34 (2026) — truncated roster scaffolds, small effect.
- Duplicates on (`game_id`,`athlete_id`): **0 in all three seasons**.
- `game_id` / `athlete_id` / `athlete_display_name` / `team_abbreviation` /
  `game_date`: 0 missing in 2016 & 2021. In **2026: 33 rows have NULL
  `athlete_id` + NULL name** (all CHI games, flags present, `reason`
  "COACH'S DECISION") — identity-less placeholder rows (~0.09% of rows);
  drop or impute in any future feature build.
- `minutes` missing ≈ DNP rows (5698/6517/6082): DNP rows never carry minutes
  (0/5698, 0/6517, 0/6082). Minutes of players who played are numeric
  integers (e.g. 30.0). `plus_minus` is stringly-typed in the CSV (mixed
  numeric/text in 2016, ~0.1% non-numeric); numeric coercion needed.
- Starter flag validates perfectly: exactly **5 starters per team-game**
  (2021: 2,344 team-games, all = 5). `active` flag does NOT validate —
  it averages ~10/game but disagrees with `starter`/`did_not_play` on ~46%
  of rows (e.g. starter=True & active=False rows have minutes). Treat
  `active` as **unreliable**; use `did_not_play` + `minutes` + `reason` for
  availability. Known anomaly; do not build on `active`.
- DNP reasons present and specific: "COACH'S DECISION" (2021: 5,355 of 6,517),
  "HEALTH & SAFETY PROTOCOLS" (76), "REST" (36), plus named injuries
  ("SPRAINED LEFT ANKLE", "SORE RIGHT KNEE", "NOT WITH TEAM", …).

## 6. Season-type and known data caveats

- `season_type`: 2=regular, 3=playoffs (all samples), 5=play-in (2021: 169 rows,
  2026: 170; absent 2016).
- **2021 play-in games (6) have roster scaffold rows but ALL player stats NULL**
  (minutes 0/169 populated) although the schedule shows FINAL with scores —
  unpopulated boxes in this store. 2026 play-in partially populated (126/170
  minutes). 2016 has no play-in. Any future feature build must exclude or
  specially handle `season_type=5` boxes (scores exist at team level).
- Regulation team minutes-mass sums to 240/player-team-game (verified: MIL
  prior-5 mean 239.4); 327/1172 games in 2021 sum <480 total with median
  shortfall 1 minute (individual sub-minute rows recorded as NaN minutes) —
  treat per-player missing minutes as "played <1 min" imputation candidate.
  6/1172 games (2021 play-in) sum to 0 — see above.

## 7. Schema drift

Zero column-set drift across 2016/2021/2026 samples (57 == 57 == 57). Values
differ (e.g. play-in rows appear 2021+). Full-store drift (2002–2015) NOT
checked this session — samples only cover 2016+ window per lane scope.
