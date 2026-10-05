# GAME UNIVERSE SPEC — NBA 2016+ (hoopR corpus) — Lane A, NBA-WINPROB-NG-PREP-V1

Cycle NBA-WINPROB-NG-PREP-V1 · lane A_DATA · measured 2026-10-05 (UTC) on the
EXTEND-ONLY corpus at `~/.my-quantitative-data/nba-hoopr-v1/raw/`
(11 schedule files `nba_schedule_2016..2026.csv`, `play_by_play_2026.parquet`,
`nba_schedule_crosswalk_2026.csv`, plus pbp 2016–2025 newly downloaded this lane —
see DOWNLOAD_MANIFEST.md). Measurement script:
`lanes/A_DATA/measure_schedule_corpus.py` → `measure_schedule_corpus.json`.
SCHEMA/COVERAGE COUNTING ONLY — no metrics were computed on real outcomes
(plan boundary). Not legal advice; internal research only.

Attribution law (carried verbatim from `~/.my-quantitative-data/nba-hoopr-v1/raw/ATTRIBUTION.md`):
data © hoopR.nba authors, CC BY 4.0; release store © SportsDataverse, MIT; upstream
ESPN NBA API; season key = ENDING year (`2025` = 2024-25). Any derivative output
must carry the ATTRIBUTION.md credit line.

---

## 1. Identity law

- **Primary key: ESPN `game_id`** (numeric string, e.g. `401766128`). MEASURED:
  14,254 total rows across the 11 season files; `game_id` unique 14,254/14,254;
  `id` column identical to `game_id` on all 14,254 rows; 0 duplicated `game_id`
  values within or across files (no cross-file collisions).
- **One row per game law**: after the dedupe/exclusion law of §4, one row per
  `game_id` holds by construction; no further deduplication is needed or allowed.
- File = season (ending year). `season` field == season file for all 14,254 rows.
- Schema: 69 columns in files 2016–2019; files 2020–2026 additionally carry
  `away_linescores, away_records, broadcast, broadcast_market, broadcast_name,
  highlights, home_linescores, home_records, play_by_play_available` and DROP
  `venue_capacity` (measured identical for all seven 2020+ files). Any consumer
  must select columns by name, never by position.

## 2. Tip-time law (UTC canonicalization)

- **`game_date_time` is the true tip instant with explicit offset** (e.g.
  `2016-06-19T20:00:00.000000-0400`). MEASURED: parses ISO-8601 on
  14,254/14,254 rows, zero failures.
- **CORRECTION to the prior-cycle memo**: the offset is **always Eastern**
  (`-0400`: 4,869 rows; `-0500`: 9,385 rows; these two values cover all
  14,254 rows) — ESPN reports tip in `America/New_York` regardless of venue
  time zone. It is NOT venue-local time. Canonicalization via the embedded
  offset is therefore always correct, but consumers must NOT re-localize by
  venue.
- **Canonical `tip_utc`** = `to_utc(game_date_time)` using the embedded offset.
  MEASURED: equals the `start_date` column on 14,254/14,254 rows
  (`start_date` = the UTC twin; `date` == `start_date` on all rows too).
- **Never use the coarse `date`/`game_date` as tip**: `game_date` is the local
  ET calendar date; the UTC calendar date of the same instant differs on
  **11,023/14,254 rows (77.3%)** — late tips cross midnight UTC.
- **DST correctness verified exhaustively for ET-home games**: 6,632 ET-home
  rows, offset matches `America/New_York` on all 6,632 (0 mismatches). Flip
  demo (BOS home, season 2025): last `-0400` game 2024-10-28 → first `-0500`
  game 2024-11-06 (DST ended 2024-11-03); last `-0500` game 2025-03-08 →
  first `-0400` game 2025-03-10 (DST started 2025-03-09).
- As-of law: any pre-game input must be frozen strictly before `tip_utc`
  (see PIT_AUDIT_NBA.md).

## 3. Season composition (`season_type`, raw rows)

Only codes {2, 3, 5} occur in 2016–2026. 2 = regular season, 3 = postseason,
5 = play-in. Raw (pre-dedupe) rows per season file:

| season (ending yr) | RS(2) | PO(3) | PI(5) | total |
|---|---:|---:|---:|---:|
| 2016 | 1,231 | 86 | 0 | 1,317 |
| 2017 | 1,231 | 79 | 0 | 1,310 |
| 2018 | 1,232 | 82 | 0 | 1,314 |
| 2019 | 1,232 | 82 | 0 | 1,314 |
| 2020 (COVID) | 1,064 | 92 | 1 | 1,157 |
| 2021 (72-gm) | 1,113 | 85 | 6 | 1,204 |
| 2022 | 1,242 | 87 | 6 | 1,335 |
| 2023 | 1,232 | 84 | 6 | 1,322 |
| 2024 | 1,234 | 82 | 6 | 1,322 |
| 2025 | 1,239 | 84 | 6 | 1,329 |
| 2026 | 1,239 | 85 | 6 | 1,330 |
| **total** | | | | **14,254** |

Playoffs are a separate stratum **by design** (reported separately, never
pooled into RS metrics without an explicit separate label).

## 4. Dedupe / exclusion law (APPLIED, measured)

Law, in order:

1. **Keep only `status_type_completed == "true"`.**
2. **Exclude exhibition/All-Star-family rows**: `notes_headline` (lowercased)
   contains `all-star` OR `rising stars`. MEASURED 19 rows total (1/season
   2016–2017 and 2021–2024; 2/season 2018–2020 = All-Star Game + Rising Stars;
   3 in 2025; 4 in 2026 — the 2025/2026 All-Star tournament formats produce
   multiple event rows). **Do NOT identify exhibitions by team names** — pseudo
   teams vary by era and are unreliable: `Eastern/Western Conf All-Stars`
   (2016/2017/2024), `Team LeBron/Stephen/Giannis/Durant` (2018–2023),
   `Team Chuck/Kenny/Shaq/Candace` (2025), `Team Stars/Stripes/World` (2026),
   `USA vs World` (Rising Stars 2018–2020); abbreviations observed:
   `EAST, WEST, DUR, LEB, CHK, SHQ, CAN, KEN, STRIPES, STARS, WORLD`.
3. **Flag (do not exclude) NBA Cup rows**: `notes_headline` contains
   `in-season tournament` OR `nba cup` — 2024/2025/2026 only, exactly
   67 rows per season = 60 Group Play + 4 Quarterfinals + 2 Semifinals
   + 1 Championship. **Group Play/QF/SF (66/season) are standings-embedded
   real regular-season games** — verified: per-team census of played
   RS-standings-embedded games = exactly 82 for all 30 teams in 2024 while
   including the 66 Cup non-final games. **The Championship final (1/season)
   is an EXTRA 83rd game that does NOT count in regular-season standings** —
   it must carry a `is_cup_final` flag and be reportable separately.
4. **Postponed duplicate listings** are the rows failing law 1: MEASURED 67
   rows, all `status_type_description == "Postponed"`, all
   `status_type_state == "post"`, per season: 2020: 12 (3 RS + 9 PLAYOFF
   bubble-strike games), 2021: 32, 2022: 11, 2023: 1, 2024: 2, 2025: 5,
   2026: 4. All 67 have a completed makeup row with the same
   home|away pair inside the same season file (67/67 makeup candidates
   verified); the makeup carries a DIFFERENT `game_id`. Never drop the
   makeup; never count the postponed listing.
5. **Global/neutral-site REAL games stay in**: London/Mexico City/Paris
   regular-season games (19 rows 2016–2026, `neutral_site == "true"` with
   real team pairs) are standings games. Only the All-Star-family and
   (flagged) Cup-final rows are special.

### Per-season PLAYED counts (raw → deduped), 2016–2026

| season | raw rows | RS standings-embedded played | Cup final played (flagged) | play-in played | playoffs played | total played |
|---|---:|---:|---:|---:|---:|---:|
| 2016 | 1,317 | 1,230 | 0 | 0 | 86 | 1,316 |
| 2017 | 1,310 | 1,230 | 0 | 0 | 79 | 1,309 |
| 2018 | 1,314 | 1,230 | 0 | 0 | 82 | 1,312 |
| 2019 | 1,314 | 1,230 | 0 | 0 | 82 | 1,312 |
| 2020 | 1,157 | 1,059 | 0 | 1 | 83 | 1,143 |
| 2021 | 1,204 | 1,080 | 0 | 6 | 85 | 1,171 |
| 2022 | 1,335 | 1,230 | 0 | 6 | 87 | 1,323 |
| 2023 | 1,322 | 1,230 | 0 | 6 | 84 | 1,320 |
| 2024 | 1,322 | 1,230 | 1 | 6 | 82 | 1,319 |
| 2025 | 1,329 | 1,230 | 1 | 6 | 84 | 1,321 |
| 2026 | 1,330 | 1,230 | 1 | 6 | 85 | 1,322 |
| **total** | **14,254** | **13,209** | **3** | **37** | **919** | **14,168** |

**Reconciliation: 14,254 raw = 14,168 played + 19 exhibitions + 67 postponed
listings.** Exact, no residue. Per-team census spot (2017, 2024): every team
exactly 82 played RS-standings-embedded games. Sanity anchors: 2020 played RS
1,059 (COVID season, known figure), 2021 played RS 1,080 = 30×72/2 (72-game
season), 2024–2026 played RS 1,230 + 1 flagged Cup final.

## 5. PBP reconciliation (spread-feature source)

- pbp exists for all 11 seasons (2026 in-corpus; 2016–2025 newly downloaded,
  DOWNLOAD_MANIFEST.md).
- All-Star event rows DO have pbp — ERRATUM R1 (defect D5): MEASURED all 19
  exhibitions across all 11 seasons carry pbp (2016: 1, 2017: 1, 2018: 2,
  2019: 2, 2020: 2, 2021: 1, 2022: 1, 2023: 1, 2024: 1, 2025: 3, 2026: 4).
  The exhibition exclusion law of §4.2 must be applied to pbp-derived game
  lists too, not assumed absent.
- No pbp ever attaches to a postponed listing (0 intersections measured on
  2016/2021/2022/2025/2026).
- Played games WITHOUT pbp (spread features missing there) — ERRATUM R1
  (defect D1, re-measured 2026-10-05 from schedule CSVs minus pbp game_ids,
  int32/str keys agree): **14 games**, not 4 —
  2016×3: `400828893` (WSH–CHI 2016-03-16), `400828600` (CLE–SA 2016-01-30),
  `400828393` (NY–ATL 2016-01-03);
  2018×4: `400974444` (NO–GS 2017-10-20), `400974773` (WSH–DET 2017-10-20),
  `400975617` (SAC–OKC 2018-02-22), `400975670` (SAC–BKN 2018-03-01);
  2020×6: `401161490` (POR–DET 2020-02-24), `401161505` (GS–SAC 2020-02-25),
  `401161528` (LAC–DEN 2020-02-29), `401161533` (MEM–LAL 2020-02-29),
  `401161530` (ATL–POR 2020-03-01), `401161536` (PHX–GS 2020-03-01);
  2026×1: `401810469` (CHI–LAC 2026-01-20).
  Seasons 2017/2019/2021/2022/2023/2024/2025: 0. All 14 are real completed
  regular-season games with final scores. A consumer must tolerate these
  missing-pbp games by game-id list — never silently impute.
  See `lanes/A_DATA/ERRATUM_PBP_GAP_R1.md`.

## 6. Spread-feature coverage census (re-verified, ALL seasons 2016–2026)

Columns `game_spread`, `home_favorite`, `home_team_spread` (ESPN line carried
in the pbp release). Measured per season on unique pbp `game_id`:

| season | unique pbp games | game_spread non-null | home_favorite non-null | coverage |
|---|---:|---:|---:|---:|
| 2016 | 1,314 | 1,314 | 1,314 | 100% |
| 2017 | 1,310 | 1,310 | 1,310 | 100% |
| 2018 | 1,310 | 1,310 | 1,310 | 100% |
| 2019 | 1,314 | 1,314 | 1,314 | 100% |
| 2020 | 1,139 | 1,139 | 1,139 | 100% |
| 2021 | 1,172 | 1,172 | 1,172 | 100% |
| 2022 | 1,324 | 1,324 | 1,324 | 100% |
| 2023 | 1,321 | 1,321 | 1,321 | 100% |
| 2024 | 1,320 | 1,320 | 1,320 | 100% |
| 2025 | 1,324 | 1,324 | 1,324 | 100% |
| 2026 | 1,325 | 1,325 | 1,325 | 100% |

The prior-cycle memo's "99.7% (1,321/1,325) on the 2026 sample" is superseded
by this re-measurement: the 2026 file measures 1,325/1,325 = 100% non-null.
Census artifacts: `lanes/A_DATA/spread_census.json`.
**PIT caveat**: line provenance (opening vs closing, timestamp of freeze) is
UNVERIFIED — the spread rides in the FINAL game payload, so it is not proven
knowable before tip. See PIT_AUDIT_NBA.md (spread verdict).

## 7. Crosswalk law (restated + re-verified)

- ESPN `game_id` is primary inside the hoopR era (2016–2026).
- **2026+ provider crosswalk** (`nba_schedule_crosswalk_2026.csv`, release tag
  `nba_crosswalk`, season=2026 only): 1,416 rows; columns include
  `espn_game_id, nba_game_id, nba_game_code, nba_home/away_team_id,
  fox_*, yahoo_*, match_method, match_confidence`. MEASURED: 1,403 rows carry
  `espn_game_id` (13 `match_method=stats_only` rows have only NBA.com ids);
  join to schedule-2026 on `espn_game_id` = **1,330/1,330 schedule rows
  matched, `game_date` agreement 1,330/1,330**; crosswalk `season_type` labels
  map cleanly (Regular Season→2: 1,230; Playoffs→3: 85; Play-In→5: 6; 9 rows
  with empty label→2). 86 crosswalk rows do not join to the schedule file
  (71 Pre-Season, 7 All-Star, 6 empty-label, 2 Playoffs) — preseason and
  All-Star are outside the game universe by §4 anyway. `fox_game_id` and
  `yahoo_game_id` are 0/1,416 populated (do not rely on them).
- **To-538-era join** (nbaallelo, ends 2015-06-16): join by **LOCAL game date +
  home team abbreviation** (`date_game` + `team_id` with
  `game_location=='H'`), NEVER by the date component inside the 538 `game_id`.
  Quirk re-verified: 4/126,314 rows have `game_id`-date ≠ `date_game`,
  including the known `201506170CLE` pair (`date_game` 6/16/2015 = Finals G6,
  9pm ET Jun 16 = Jun 17 UTC). 538 has exactly 2 rows per `game_id`
  (126,314 rows / 63,157 ids); hoopR has 1 row per game.
- **Seam**: 538 max `date_game` = 2015-06-16; hoopR 2016 file first game =
  2015-10-27 — a clean seam, no overlap.

## 8. Known-result spot checks

Carried from the prior lane (3/3 PASS, `NBA_POST2015_SOURCES.md` §4.4) and
re-confirmed here: `401766128` = 2025 Finals G7, OKC home 103 (vs IND 91),
notes `NBA Finals - Game 7` (row re-located in `nba_schedule_2025.csv` this
session). Structural verification this lane: identity uniqueness (§1),
tip/start_date equivalence on all rows (§2), DST exhaustiveness (§2),
dedupe reconciliation to zero residue (§4), per-team 82-game census (§4).

## 9. Boundary statement

This spec authorizes NORMALIZED GAME-UNIVERSE SELECTION only. No win-prob
metric, no model score, no calibration number has been or may be computed on
these outcomes inside this PREP cycle (budget 0 scored). 2026-27 games not yet
played at the cycle epoch are PROSPECTIVE ONLY. New evaluation window = 2016+;
the 2009–2015 window is SPENT and must never be re-scored (plan law).
