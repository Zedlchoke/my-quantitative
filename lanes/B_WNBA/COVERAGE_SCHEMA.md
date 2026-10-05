# COVERAGE & SCHEMA — Lane B (WNBA PLAYER DATA) · cycle WINPROB-PLAYERDATA-PREP-V1 · 2026-10-05

All numbers measured this session by `lanes/B_WNBA/measure_b.py` over the read-only corpus
`~/.my-quantitative-data/wnba-prep-v1/roster_audit/` (hash-verified first — see INVENTORY.md)
and `~/.my-quantitative-data/wnba-v1/raw/espn_schedules/`. Machine output:
`lanes/B_WNBA/measurements_b.json`. WNBA only; schema/coverage counting only.

## 1. Game universe re-derivation (ESPN side)

The Lane A filter law (GAME_UNIVERSE_SPEC_WNBA_1997PLUS.md §4) re-applied to the ESPN
schedules 2002–2026: keep `status_type_state=='post'`; drop `Forfeit`/`Postponed`; drop
All-Star alias rows (`EAST/WEST/ALL/USA/DEL/PAR/WIL/STE/CLA/COL/SPO/COOP/WNBASTARS` on home
or away abbreviation); TBD placeholders are `pre` and already excluded.

**Re-derived ESPN-side universe = 5,988 games — exactly matches the prior cycle's census
(cross-check `match: true`).** Per-season: 271, 255, 237, 238, 257, 242, 259, 242, 220, 224,
223, 221, 222, 225, 220, 219, 220, 220, 147, 210, 240, 261, 263, 311, 341 (2002→2026).
Dropped rows re-measured: forfeit `401018942` (2018), postponed `401507167` (2023) +
`401857072` (2026), 21 All-Star rows (exactly one per non-Olympic-year season; 0 in
2008/2012/2016/2020).

## 2. Join of player-level files vs the ESPN universe (key: ESPN `game_id`)

| family | games in files | universe covered | join rate vs 5,988 | file games not in universe |
|---|---:|---:|---:|---:|
| `game_rosters` | 5,997 | **5,983** | **99.92%** | 14 (13 ASG + 1 forfeited game) |
| `player_box` | 5,643 | **5,624** | **93.92%** | 19 (all All-Star games) |

Both files join cleanly on integer ESPN `game_id`; no crosswalk needed (both are ESPN-side).

**Per-season join rate, player_box** (covered/universe):

| season | covered | universe | rate | missing universe games |
|---|---:|---:|---:|---:|
| 2002 | 16 | 271 | 5.9% | 255 |
| 2003 | 194 | 255 | 76.1% | 61 |
| 2004 | 214 | 237 | 90.3% | 23 |
| 2005 | 229 | 238 | 96.2% | 9 |
| 2006 | 255 | 257 | 99.2% | 2 |
| 2007 | 240 | 242 | 99.2% | 2 |
| 2008 | 252 | 259 | 97.3% | 7 |
| 2009–2011 | 242/224/220 | 242/224/220 | 100/100/99.5% | 0/0/1 |
| 2012 | 221 | 223 | 99.1% | 2 |
| 2013–2015 | 100% | — | 100% | 0 |
| 2016 | 218 | 220 | 99.1% | 2 |
| 2017–2026 | all | — | **100% every season** | 0 |

**Per-season join rate, game_rosters**: 100% in every season except 2002 (270/271), 2006
(255/257), 2008 (258/259), 2016 (219/220) — 5 universe games ever lack rosters.

**Backfill-hole law for successors**: player_box coverage is total from 2013 onward,
≥96% from 2004 (excl. 2008's 97.3%), and collapses in 2002 (a 16-game stub) and 2003
(76.1%). Prior-games aggregate features must carry a per-season coverage floor.

**Extra games in the files are explainable, not noise**: every "not in universe" player_box
game is the season's All-Star game (ESPN-side ASG rows are excluded from the universe by the
alias filter; 19 extras = one per ASG season 2003–2026, none in Olympic years or 2002).
game_rosters has the same 13 ASG extras **plus the forfeited game `401018942`** — rosters of
the 2018-08-03 forfeit exist, its player_box does not. The forfeit/postponed games are
otherwise absent from both files (postponed `401507167`, `401857072`: absent from both).

**Cross-check vs the §6 residuals of the game-universe spec**: the 9 ESPN-only rows (3
regular games `270620018`, `290709009`, `400182104` + 6 Commissioner's Cup finals 2021–2026)
are all present in player_box (they are ESPN-side universe rows); the 7 stats-only
2002–2004 extras and all 1,022 pre-2002 games have no ESPN `game_id` and cannot key to
player-level data.

## 3. Era gap vs the 7,017-game model universe

- Model universe union (prior cycle): 7,017 = 5,988 ESPN-side + 1,029 stats-only.
- Player-level data is structurally limited to the 5,988 ESPN-side rows = **85.3% of the
  union**. The uncovered 14.6% (1,022 games) is the entire 1997–2001 warm-up era + 7
  stats-only rows 2002–2004. No source in the store publishes pre-2002 player box/rosters.
- Usable player-level modeling floor therefore starts 2002 **nominally**, but with the
  §2 backfill holes: realistically **2004+** for game-level aggregates, **2013+** for
  anything needing clean minutes or DNP flags (see §6).

## 4. Players-per-game, team-side completeness, duplicates

From `player_box_quality` (per season, all 25 seasons in measurements_b.json):

- **Players per game** (unique `athlete_id` per game): min 14–21, median 22–25, p95 23–27,
  max 24–35 across seasons. No season has a pathological distribution; the 2002 stub
  (16 games) shows median 22 like every other year.
- **Team-side completeness**: distinct `team_id` per game == 2 for **every** game in every
  season (0 violations in 5,643 player_box games). Both sides of every game are present.
- **Duplicates on (`game_id`, `athlete_id`)**: exactly **1 duplicate key in 129,617 rows
  across 25 seasons**: game `250521017` (2005-05-21), athlete 30 (Adrienne Goodson) appears
  twice — once listed under HOU and once under SAS (a same-day traded player double-listed);
  both rows have null minutes, `starter=False`. A single, explained artifact; a
  `drop_duplicates(['game_id','athlete_id'])` guard is still mandatory in any successor.
- game_rosters: 137,587 rows; 0 duplicate keys on (`game_id`,`athlete_id`) reported by the
  prior cycle's roster audit and no (game,team,athlete) collisions found here beyond the
  same 2002-era coverage notes.

## 5. player_box vs game_rosters (row-level agreement)

Player_box (`game_id`,`athlete_id`) keys are a **strict subset of game_rosters keys in all
25 seasons** (measured: 0 player_box keys missing from rosters in any season; e.g. 2013,
2020, 2026: exact 1:1 key sets; 2010: 4,831 pb keys vs 4,854 roster keys — the 23 extra
roster rows are players absent from the box listing; 2003: 4,279 vs 5,605 — the backfill
gap). Rosters are the fuller table; player_box never contains a player the roster table lacks.

## 6. Missing minutes / DNP / `active` / `reason` semantics (measured — important caveats)

| era | `did_not_play` flag | non-player rows | minutes |
|---|---|---|---|
| 2002 (35-col schema) | present but never True (0 rows) | appear as `active=False` rows (189) | **100% null (`--`)** — minutes unusable for 2002 |
| 2003–2011 (56-col) | **never populated** (0 True rows) | appear as null-`minutes` rows (594–1,311 per season) | numeric float; nulls ≈ non-players |
| 2012–2026 (57-col) | populated (180–1,461 rows/season) | `did_not_play=True`, `minutes` null | nulls ≈ DNP count (±10) |

- Non-players **do appear** in player_box as rows with null minutes (and, from 2012, the
  DNP flag). Player_box is a full roster-sheet listing, not only players who played.
- **`reason` is NOT a clean DNP field**: measured in 2013, all 2,220 starter rows carry the
  default string `COACH'S DECISION` (4,500 of 4,934 non-empty reasons league-wide). Only
  injury-specific strings (`KNEE INJURY`, `TORN LEFT ACL`, `CONCUSSION PROTOCOL`, …) are
  informative, and they sit on non-playing rows. `reason` was absent pre-2012 (added with
  the 57-col schema).
- **`active` is NOT an availability flag in any era**: crosstabs vs `starter` show
  active=True covering roughly half of BOTH starters and bench in 2002, 2005, 2010, 2013,
  2020, 2026 (e.g. 2026: 1,805 of 3,420 starters active=True; 1,615 of 4,873 bench players
  active=True). A starter who played 30 minutes can carry `active=False` (e.g. Tamika
  Catchings, 2013). **Do not read `active` as "dressed/available".** The meaningful
  availability signals are `did_not_play` (2012+), null minutes (all eras), and
  injury-specific `reason` strings (2012+).

## 7. Starters = 5 per team per game (game_rosters sanity)

Across all 25 seasons: **12,005 team-games; 11,969 (99.70%) have exactly 5 `starter=True`
rows.** Exceptions, all enumerated:

- **33 team-games with 0 starter rows** (both teams' starter flags missing in the same
  game): 2002×12, 2003×1 (`230628004`), 2005×4, 2006×2, 2008×2, 2009×4, 2011×2, 2012×4,
  2018×2 — scattered early/mid-era games where ESPN's roster sheet carried no starter flags.
- **3 team-games with a wrong count**: one team-game with **6** starters (2016), two with
  **4** (2017, 2020). No season after 2020 has any violation; 2021–2026 are perfect
  (5/5 in every team-game).

Conclusion: the starter flag is trustworthy 2021+ and ≥99% before, with the 33 flag-empty
team-games concentrated 2002–2018.

## 8. Schema drift (player_box: 3 eras; game_rosters: none)

- **2002 — 35 columns, legacy short names**: stats as `fg, fg3, ft, oreb, dreb, reb, ast,
  stl, blk, to, pf, pts, min` (all strings); no `minutes`, no `game_date_time`, no
  `opponent_*`, no `home_away`, no `team_score`, no `reason`, no `team_slug/uid`.
- **2003–2011 — 56 columns, long names + opponents**: `field_goals_made, …, minutes`
  (float), plus `opponent_team_*`, `team_score`, `team_winner`, `home_away`,
  `game_date_time`.
- **2012–2026 — 57 columns**: adds `reason` (the DNP/injury note, §6).
- **`game_rosters` schema is byte-identical (22 columns) across 2002–2026** — re-verified
  this session (`game_rosters_schema_identical_2002_2026: true`), matching the prior cycle's
  `measurements_r2.json`.

Successor law: any player_box consumer needs era guards at 2002|2003 and 2011|2012
(column naming, minutes dtype, DNP/reason availability); rosters need none.
