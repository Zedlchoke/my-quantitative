# DATASET AUDIT — Lane B — NFL-WINPROB-PREP-V1

Measured 2026-10-04 from `~/.my-quantitative-data/nfl-nflverse-v1/raw/`
(games.csv = nflverse-data `schedules` release, as-of 2026-10-04 08:16:30 EDT;
pbp = `pbp` release, as-of 2026-10-04 05:03:18 EDT). Reproduce with
`audit_script.py` (no writes, prints census).

## 1. games.csv structure

- **46 columns**: game_id, season, game_type, week, gameday, weekday, gametime,
  away_team, away_score, home_team, home_score, location, result, total,
  overtime, old_game_id, gsis, nfl_detail_id, pfr, pff, espn, ftn, away_rest,
  home_rest, away_moneyline, home_moneyline, spread_line, away_spread_odds,
  home_spread_odds, total_line, under_odds, over_odds, div_game, roof, surface,
  temp, wind, away_qb_id, home_qb_id, away_qb_name, home_qb_name, away_coach,
  home_coach, referee, stadium_id, stadium.
- **7,548 rows**, seasons **1999..2026** (28 seasons). Dispatch expected
  "1920s..2026" — the release starts at 1999; there is no earlier coverage in
  this source. Correction stands as measured.

## 2. game_type domain

REG 7,239 · WC 120 · DIV 108 · CON 54 · SB 27. No other values (no preseason,
no other domain leakage).

## 3. Finished-games filter

- Finished (both scores non-NA): **7,325** (97.05%). Unfinished: **223**, all
  in season 2026 (2026 has 272 rows: 49 finished, 223 future-scheduled, all
  REG). Last finished game: `2026_04_PIT_CLE`, 2026-10-01.
- Protocol consequence: the finished filter (home_score & away_score non-NA)
  exactly isolates played games — no other season has score-NA rows.

## 4. Per-season REG counts vs era expectations

| seasons | teams | REG games/team | measured | verdict |
|---|---|---|---|---|
| 1999-2001 | 31 | 16 | 248 every season | PASS (CLE reactivated 1999; HOU not yet) |
| 2002-2020 | 32 | 16 | 256 every season | PASS |
| 2021-2025 | 32 | 17 | 272 (2021, 2023, 2024, 2025) | PASS |
| 2022 | 32 | — | **271** | EXPLAINED: cancelled BUF@CIN (Damar Hamlin, no-contest); `2022_17_BUF_CIN` absent from file (checked) |

- **Strike seasons 1982/1987: NOT_IN_RELEASE** (release starts 1999). The
  dispatch's strike benchmarks (1982: 9/team; 1987: 15/team) cannot be
  exercised on this source.
- 2026 in progress: 272 scheduled REG rows, 49 played.
- Zero unexplained anomalies across all 28 seasons.

## 5. Identity census

- **35 distinct team abbreviations** (home_team ∪ away_team). Renames measured
  via season-transition census — exactly 4 transitions:
  - 2001→2002: new `HOU` (Texans expansion, 32nd team)
  - 2015→2016: `STL` → `LA` (Rams; VERIFIED, first season of LA = 2016)
  - 2016→2017: `SD` → `LAC` (Chargers; VERIFIED, first LAC season 2017)
  - 2019→2020: `OAK` → `LV` (Raiders; VERIFIED, first LV season 2020)
  - Full rename table with spans: STL[1999-2015]→LA[2016-], SD[1999-2016]→LAC[2017-],
    OAK[1999-2019]→LV[2020-]; HOU appears 2002; `WAS` is used for Washington for the
    whole range (this release does NOT use WSH).
- **game_id**: 7,548 rows / 7,548 distinct — **0 duplicates**. Format
  `{season}_{wk}_{AWAY}_{HOME}`.
- **gsis**: 7,340 non-null (97.24%), all distinct, 0 duplicates; 208 missing
  are **all 2026 future games** (GSIS id not yet assigned) — every finished
  game 1999-2025 has a unique gsis.
- **Franchise lineage proposal (1999+ release range)** — one row per lineage:

| lineage | member abbrevs (measured span) | note |
|---|---|---|
| LA-Rams | STL[1999-2015], LA[2016-2026] | pure rename in-range |
| LA-Chargers | SD[1999-2016], LAC[2017-2026] | pure rename in-range |
| LV-Raiders | OAK[1999-2019], LV[2020-2026] | pure rename in-range |
| CLE-BAL | BAL[1999-2026], CLE[1999-2026] | NOT resolvable from abbrevs: 1999 CLE reactivation vs 1996 BAL move is a protocol decision, not a data observation |
| HOU-TEN | TEN[1999-2026] | Oilers→Titans rename (1997) predates release; only TEN visible |
| single-abbrev | 26 lineages: ARI, ATL, BUF, CAR, CHI, CIN, DAL, DEN, DET, GB, HOU[2002-], IND, JAX, KC, MIA, MIN, NE, NO, NYG, NYJ, PHI, PIT, SEA, SF, TB, WAS | HOU(Texans) = expansion lineage, distinct from HOU-TEN history |

Total 31 lineages over 1999-2026. Protocol must decide CLE/BAL mapping
explicitly; abbrev continuity alone cannot.

## 6. PIT surface: gametime

- **Semantics: DOCUMENTED, not ambiguous.** Both Lee Sharpe's DATASETS.md and
  nflreadr `dictionary_schedules.csv` state: *"The kickoff time of the game.
  This is represented in 24-hour time and the Eastern time zone, regardless of
  what time zone the game was being played in."* So gametime = kickoff time,
  24h HH:MM, US Eastern civil time, naive string, no tz suffix.
- Format: 100.00% of non-null values match `^\d{1,2}:\d{2}$`; single format
  family `##:##`; no stray formats.
- Missing: **259/7,548 (3.43%) — all 259 in season 1999** (100% of 1999 rows).
  Seasons 2000-2026: 0 missing.
- Grain: 11-21 distinct kickoff times per season (mode `13:00`, ~47-55% of
  games). No placeholder-collapse pattern after 1999.
- **Earliest season from which kickoff grain is safe: 2000** (first season with
  0 missing and ≥6 distinct times; all later seasons also 0-missing). 1999 has
  NO kickoff times → any kickoff-time-dependent feature is NOT_RUN for 1999.
- Parse assumptions for absolute instants (both recorded):
  - **A (recommended)**: localize `gameday`+`gametime` to America/New_York with
    DST rules → UTC. Matches the documented ET semantics exactly.
  - **B (fallback)**: fixed UTC-05:00 (EST) year-round. Differs from A for
    **42.5%** of games (those inside EDT; measured on 7,066 sample rows).
  - Ordering of kickoffs is identical under A and B; a
    "kickoff strictly before as-of" law is exact under A and conservative by
    1h (EDT games only) under B. **Protocol input: use A; 2000 is the kickoff-
    grain boundary season.**

## 7. Quality census

- Nulls (key/pit columns): game_id, season, game_type, week, gameday,
  away_team, home_team, location, stadium, stadium_id, away_rest, home_rest,
  old_game_id — **0 nulls each**. Nulls: away/home_score, result, total,
  overtime 223 each (= the 2026 future games); gametime 259 (= 1999);
  gsis 208 (= 2026 future); spread_line/total_line 193 (2026 futures minus
  some posted lines).
- Score arithmetic: across 7,325 finished games — result == home−away: **0
  violations**; total == home+away: **0 violations**; no negative scores.
  15 tie games (REG only; playoffs resolved in OT).
- **Neutral-site flag exists**: `location ∈ {Home, Neutral}` (Home 7,446 /
  Neutral 102). Measured Neutral games include every SB (27) and
  international games; 49 games at international stadiums detected by stadium
  name (Wembley, Tottenham Hotspur, Estadio Azteca, Allianz Arena, Bernabéu).
  Sample of 10 measured neutral rows (5 recent SBs + 5 internationals incl.
  2024 NE@JAX Wembley, 2024 NYG@CAR Munich, 2026 IND@WAS Tottenham) — all
  flagged Neutral. NFL International games and SBs are fully flaggable from
  data; no external lookup needed.
- **Bye/rest support**: per-team consecutive-game gaps within team-season:
  n=14,203, p50=7d, p95=14d, max=21d (2001, 9/11 postponement). Gap mass at
  7d (9,488), 6d (1,262 short weeks), 14d (825 byes) — rest computation is
  fully supported; the file also ships `away_rest`/`home_rest` (0% null all
  seasons) as a cross-check column pair.

## 8. pbp subset (parquet, pyarrow 25.0.1 — row counts RUN)

| file | bytes | sha256 | rows | distinct game_id | joins into games.csv | season values |
|---|---|---|---|---|---|---|
| play_by_play_2021.parquet | 20,249,925 | 333ad343…f78d8 | 49,922 | 285 | 285/285 | {2021} |
| play_by_play_2022.parquet | 20,426,548 | 931121d8…edc09 | 49,434 | 284 | 284/284 | {2022} |
| play_by_play_2023.parquet | 20,534,088 | bd348473…dc6776 | 49,665 | 285 | 285/285 | {2023} |
| play_by_play_2024.parquet | 20,597,560 | 3fd2896b…f6a3b | 49,492 | 285 | 285/285 | {2024} |
| play_by_play_2025.parquet | 20,337,029 | c6ecedd6…67df29 | 48,771 | 285 | 285/285 | {2025} |

- Total **247,284 plays**, 102.1 MB. Full sha256s in ATTRIBUTION.md.
- 2022 parquet holds 284 games = 271 REG + 13 playoff (cancelled BUF@CIN
  absent in both sources — consistent).
- Identity cross-check: 100.0% of parquet game_ids join into games.csv; each
  file contains exactly one labeled season. Identity between the two sources
  reconciles cleanly on `game_id`.

## 9. Freeze proposal (measured)

- Coverage end (finished games): **2026 week 4** (last finished 2026-10-01);
  last COMPLETE season: **2025**.
- **TEST = final 7 complete seasons: 2019..2025** (measured complete: seasons
  ≤ 2025; 2026 excluded as in progress).
- **TRAIN = 2000..2018** (19 seasons). Rationale: kickoff-time grain is safe
  from season **2000** (1999 gametime is 100% missing), so a 1970-merger-style
  deep TRAIN is impossible on this source (data starts 1999) and unnecessary —
  2000 already gives the full modern-schedule era. If a lane needs 1999 rows
  for gametime-independent features only, allow TRAIN=1999..2018 with an
  explicit feature-level NOT_RUN marker for PIT columns in 1999.
- Recommended splits by game count: TEST = seasons 2019-2025 measured at
  267/269/285/284/285/285/285 rows (incl. postseason) = 1,960 games.

## 10. Known limitations

1. Source covers **1999+ only**; no 1920s-1998 coverage; strike-season checks
   impossible on this release.
2. 1999 has no kickoff times (PIT not computable for 1999).
3. gametime is naive ET — DST conversion required for absolute instants;
   42.5% of games shift 1h if the fixed-EST fallback is used.
4. Washington is `WAS` throughout this release (not WSH); any external join
   keyed on WSH must map WAS↔WSH.
5. 2022 contains 271 REG games (cancelled BUF@CIN absent) — schedule-shape
   features for 2022 must tolerate the missing 17th week game.
6. 2026 is in progress (49/272 played); use finished-filter.
