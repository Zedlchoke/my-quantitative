# COVERAGE AUDIT — NBA player box 2016–2026 (Lane A_NBA_FEAT, WINPROB-PLAYERFEAT-PREP-V1)

All numbers measured 2026-10-05 from bytes with pandas
(`coverage_audit.py`, evidence in
`~/.my-quantitative-data/playerfeat-prep-v1/nba/provenance/
coverage_audit_11seasons.{txt,json}`). Box inputs: 8 seasons downloaded this
lane (player_box_raw/ here) + 2016/2021/2026 reused read-only from the
predecessor (`~/.my-quantitative-data/playerdata-prep-v1/nba/player_box_raw/`,
sha-verified at load: hashes equal both download manifests). Schedule corpus:
`~/.my-quantitative-data/nba-hoopr-v1/raw/nba_schedule_<season>.csv`
(14,254 rows total across 11 files, read-only).

## 1. Per-season coverage (join on ESPN game_id)

| season | sched rows | REG+POST rows | played games | box rows | box games | played-join rate | orphan box games | dup (game_id,athlete_id) | DNP rows | NULL athlete rows | players/game median |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 1,317 | 1,317 | 1,317 | 33,715 | 1,317 | **1.0000** | 0 | 0 | 5,698 | 0 | 26 |
| 2017 | 1,310 | 1,310 | 1,310 | 33,631 | 1,309 | **0.9992** | 0 | 0 | 5,731 | 0 | 26 |
| 2018 | 1,314 | 1,314 | 1,314 | 33,119 | 1,313 | **0.9992** | 0 | 0 | 5,256 | 0 | 25 |
| 2019 | 1,314 | 1,314 | 1,314 | 32,985 | 1,313 | **0.9992** | 0 | 0 | 5,060 | 0 | 25 |
| 2020 | 1,157 | 1,156 | 1,145 | 28,764 | 1,145 | **1.0000** | 0 | 0 | 4,609 | 0 | 25 |
| 2021 | 1,204 | 1,198 | 1,172 | 31,593 | 1,172 | **1.0000** | 0 | 0 | 6,517 | 0 | 27 |
| 2022 | 1,335 | 1,329 | 1,324 | 33,880 | 1,324 | **1.0000** | 0 | 0 | 5,806 | 0 | 26 |
| 2023 | 1,322 | 1,316 | 1,321 | 34,057 | 1,321 | **1.0000** | 0 | 0 | 6,290 | 0 | 26 |
| 2024 | 1,322 | 1,316 | 1,320 | 35,028 | 1,320 | **1.0000** | 0 | 0 | 6,638 | 0 | 27 |
| 2025 | 1,329 | 1,323 | 1,324 | 35,250 | 1,324 | **1.0000** | 0 | 0 | 6,857 | 0 | 27 |
| 2026 | 1,330 | 1,324 | 1,326 | 34,883 | 1,326 | **1.0000** | 0 | 0 | 6,082 | 33 | 26 |
| **Σ** | **14,254** | **14,211** | **14,187** | **366,905** | **14,184** | — | **0** | **0** | **64,544** | **33** | — |

- Played = `status_type_name==STATUS_FINAL` + both scores present. The
  REG+POST/played gap is postponed/cancelled rows (32 in 2021 COVID, 4 in 2026,
  12 in 2020, 6 in 2022) and 2020/2021/2023/2024/2025/2026 play-in rows
  (`season_type=5`: 1+6+6+6+6+6+6 = 37 rows, of which all played; play-in rows
  sit OUTSIDE the {2,3} REG+POST count). Effective coverage of games actually
  played = **100%** (8 seasons) / **99.92%** (2017/2018/2019, see below).
- The 3 box-less played games (one per season, all `STATUS_FINAL`):
  2017 `400900132` NY@ATL 2017-01-29; 2018 `400975285` BKN@BOS 2017-12-31;
  2019 `401070917` NY@ORL 2018-11-18
  (`provenance/missing_played_games.txt`). These 3 games are emitted as
  targets (played) but contribute no player stats to any prior window
  (0 usable rows); n=6 target rows of 28,374 (0.02%).
- Zero orphan box games in every season. Zero duplicates on
  (`game_id`,`athlete_id`) in every season. NULL `athlete_id` rows: 33, all in
  2026 (predecessor finding reproduced: CHI placeholder rows) — excluded from
  all aggregates with counts as frozen in FEATURE_SPEC §2.

## 2. Schema drift vs predecessor-documented 2026 schema

Zero drift: all 11 seasons have exactly the predecessor's 57 columns
(sorted-list compare; per-season evidence in the provenance json,
`schema_drift.missing_vs_pred` / `extra_vs_pred` = [] everywhere).

## 3. Season label convention (ending-year) — verified in every season

| season label | game_date min | game_date max | ending-year OK |
|---|---|---|---|
| 2016 | 2015-10-27 | 2016-06-19 | yes |
| 2017 | 2016-10-25 | 2017-06-12 | yes |
| 2018 | 2017-10-17 | 2018-06-08 | yes |
| 2019 | 2018-10-16 | 2019-06-13 | yes |
| 2020 | 2019-10-22 | 2020-10-11 | yes |
| 2021 | 2020-12-22 | 2021-07-20 | yes |
| 2022 | 2021-10-19 | 2022-06-16 | yes |
| 2023 | 2022-10-18 | 2023-06-12 | yes |
| 2024 | 2023-10-24 | 2024-06-17 | yes |
| 2025 | 2024-10-22 | 2025-06-22 | yes |
| 2026 | 2025-10-21 | 2026-06-13 | yes |

`season` column = label exactly (single value per file). Store label 2016 =
2015-16 season (workspace text offset note from predecessor COVERAGE_SCHEMA §2
carried forward).

## 4. Tip-time timezone semantics (from bytes, every row of every file)

- `game_date_time`: arena-local time with offset
  (e.g. `2017-06-12T21:00:00.000000-0400`); `start_date`: same instant UTC
  (e.g. `2017-06-13T01:00Z`). After `pd.to_datetime(..., utc=True,
  format='mixed')` the two are equal on **14,254/14,254 rows (100% in all 11
  seasons)**; parse failures 0. The as-of join uses `game_date_time` → `tip_utc`
  per FEATURE_SPEC §0; the predecessor MIL example tip 2021-03-15T23:00Z
  reproduces (PIT_AUDIT.md §2).

## 5. season_type composition (box rows)

| season | 2 (reg) | 3 (playoffs) | 5 (play-in) |
|---|---|---|---|
| 2016–2019 | ~31.0–31.6k | ~2.0–2.2k | — |
| 2020 | 26,592 | 2,147 | 25 |
| 2021 | 28,906 | 2,518 | 169 |
| 2022–2026 | ~31.4–32.7k | ~2.3–2.4k | ~155–170 |

Predecessor caveats carried forward and re-measured: 2021 play-in boxes
unpopulated (roster scaffolds, stats NULL), 2026 play-in partially populated;
`season_type=5` excluded from ALL prior windows (FEATURE_SPEC §2); play-in
played games are emitted as targets only. 2020 also carries the single
pandemic play-in game (25 rows). No `season_type=1` (preseason) rows exist in
either corpus — no preseason law needed.

## 6. Exhibition games in the played universe (new measurement, FEATURE_SPEC §1)

19 exhibition games are present and played in the schedule universe (NBA
All-Star formats + Rising Stars, all inside `season_type=2`), both sides
carrying event-specific team ids (full list in
`provenance/exhibition_games.txt`). 38 of the 28,374 target rows are
`is_exhibition=1`. Franchise ids = ESPN league-46 ids {1..30}, stable all 11
seasons (franchise team-games/season 64–107; exhibition entities 1–8).
Exhibition games never enter franchise prior sequences (both sides are event
ids). Names measured from team ids: e.g. 26=UTAH, 12=LAC (2025), 15=MIL,
27=WSH (2021).

## 7. Players per game

Medians 25–27 (per-season column above); min 17 (2025/2026 truncated roster
scaffolds), max 27–35. Predecessor §5 findings (starter=5/team-game validates,
`active` unreliable) are carried forward and were re-verified on the 2021
sample by the predecessor's own evidence; this lane's build uses only
`did_not_play` + `minutes` + `reason` per the frozen spec.
