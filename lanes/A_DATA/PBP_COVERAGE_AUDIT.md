# PBP_COVERAGE_AUDIT — Lane A_DATA, cycle NFL-WINPROB-NG-SCORED-V1

Measured from bytes 2026-10-05 (downloaded_utc 09:02:02–09:02:41Z; measurement run
2026-10-05T09:06Z). Inputs: `raw_pbp_2000_2017/play_by_play_2000..2017.parquet` (this lane's
fresh snapshot) + `raw_schedules_fresh/games.csv` (schedules compile 2026-10-05T05:46:22Z).
Coverage counting and PIT-relevant presence measurements ONLY — no win-prob metric, model
score, or outcome evaluation computed. Raw numbers: `~/.my-quantitative-data/nfl-ng-scored-v1/
provenance/audit_measures.json`, `pbp_blanks_playtype_2000_2017.json`.

## 1. Per-season coverage and join vs games.csv

| season | pbp rows | pbp games | games.csv games | orphans (pbp∉games) | games missing from pbp | REG/POST games (pbp) |
|---|---|---|---|---|---|---|
| 2000 | 45,491 | 257 | 259 | 0 | **2** (`2000_03_SD_KC`, `2000_06_BUF_MIA`) | 246 REG / 11 POST (games.csv: 248/11) |
| 2001 | 44,969 | 259 | 259 | 0 | 0 | 248 / 11 |
| 2002–2017 (each) | 45,917–48,158 | 267 | 267 | 0 | 0 | 256 / 11 |

- Join key `game_id` matches **exactly** on 17 of 18 seasons; **0 orphan game_ids anywhere**.
  The only gap: 2 finished REG games of 2000 (SD@KC week 3, BUF@MIA week 6 — both carry
  final scores in games.csv) are absent from `play_by_play_2000.parquet` (257/259 = 99.2%
  of the 2000 season present). POST structure is exactly 11 playoff games per season in
  every year (WC4+DIV4+CON2+SB1), reconciling row-for-row with games.csv `game_type`.
- REG row counts 43,074–46,255 per season (2001–2017), 43,576 in 2000.

## 2. Team-abbreviation domain vs the 32-lineage map

**Measured finding (corrects the dispatch's stated expectation):** in pbp 2000–2017 the
abbreviation domain is the **32 CURRENT lineage codes only** — `SD`, `STL`, `OAK` appear in
**no** season (2000–2017); `LAC`, `LA`, `LV` appear in **every** season. nflverse pbp
normalizes historical abbreviations to current franchise codes across all history, while
games.csv keeps historical codes (SD 2000–2016, STL 2000–2015, OAK 2000–2019 measured in
games.csv; union 2000–2017 = 34 codes incl. all three old codes). The relocation dates
(SD→LAC 2017, STL→LA 2016, OAK→LV 2020) are invisible in pbp because pbp is already
lineage-normalized — the old-abbrev condition fails **by normalization, not by data loss**.

Role-aligned verification (2000, the season with both old SD and old OAK lineages): all
257 pbp games' `home_team`/`away_team` match games.csv exactly after applying the frozen
lineage map {SD→LAC, STL→LA, OAK→LV} — **0 home mismatches, 0 away mismatches in 257
games**. `posteam`/`defteam` non-null counts are equal per season (e.g., 2000: 44,963 both).

**Consequence for C3 (operational, not blocking):** pbp aggregates key directly on the
32-lineage convention; the games.csv side must apply the frozen predecessor lineage map
when pulling game-level labels for pre-2017 seasons. One non-team code exists in pbp:
**blank posteam** (see §3).

## 3. EPA availability and attribution blanks (C3 input readiness)

C3 needs per-team-season offensive EPA/plays and defensive EPA-allowed/plays over REG games
of completed seasons (`epa`, `posteam`, `defteam`, `season_type`).

| season | epa non-null among posteam-set rows | blank-posteam rows (REG / of which epa non-null) | play_type non-null | down non-null |
|---|---|---|---|---|
| 2000 | 99.971% | 569 / 81 | 91.2% | 84.2% |
| 2001 | 99.986% | 2,501 / 1,998 | 97.0% | 84.9% |
| 2002–2017 (each) | 99.37–99.39% | 2,214–2,341 / ~1,960–2,086 | ~97.0–97.3% | 85.0–86.4% |

- `epa` is populated on 99.37–100.0% of team-attributable rows in every season 2000–2017.
  `posteam` and `defteam` are populated on identical row sets per season.
- Blank-posteam rows (team not attributable; excluded from any C3 aggregate) are ~5% of rows
  in 2001–2017 and 1.3% in 2000; ~2,000/season of them still carry non-null `epa` and must
  be dropped by the C3 aggregator (they are dropped from the per-team counts below).
- `play_type` has **exactly the same 9 distinct values in all 18 seasons** — the
  "pre-2006 different pipeline" caveat is **not measurable** as a play-type vocabulary gap
  between eras; the measurable era difference is only in blankness rates (2000 has more
  `play_type` blanks, 8.8%, than 2001–2017, ~3%). `down` non-null ~84–86% everywhere.
- Column presence: every file carries the identical **372-column** parquet schema; all
  C3-relevant columns (`game_id`, `season`, `season_type`, `week`, `posteam`, `defteam`,
  `epa`, `play_type`, `down`, `home_team`, `away_team`) present in all 18 seasons.

## 4. Per-team-season REG play samples (C3 effective-sample check)

REG rows with `posteam` set, non-blank, and `epa` non-null, per lineage-season:

| season | lineages | min | median | max |
|---|---|---|---|---|
| 2000 | 31 | 1,221 | 1,407 | 1,535 |
| 2001 | 31 | 1,211 | 1,316 | 1,393 |
| 2002–2017 (each) | 32 | 1,197 (2003) | 1,302–1,366 | 1,375–1,522 |

Offensive-attributed samples ≈ 1,200–1,535 plays per lineage-season; the off+def combined
C3 reading (offensive EPA plays + defensive EPA-allowed plays) ≈ 2,400–3,070 per
lineage-season. The C3 spec's "≈ 2,000+ plays per team-season" holds on the combined
reading; on the offense-only reading it is ~1,200–1,500. 31 lineages in 2000–2001
(pre-HOU expansion), 32 from 2002 — consistent with games.csv. 2000's two missing games
remove at most one game's plays from four lineages (SD/LAC-lineage, KC, BUF, MIA).

## 5. Verdict-relevant summary (full verdict in VERDICT_TABLE.md / SUCCESSOR_DATA_AUDIT.md)

- Coverage supports train-internal C3 evaluation on seasons 2001–2018 priors (pbp 2000–2017
  present; 17/18 seasons join exactly; 2000 is 99.2% complete with the gap named).
- Abbreviation domain is already the 32-lineage convention (documented normalization;
  games.csv side needs the frozen lineage map).
- No rights, schema, or availability blocker found for the offseason-prior role.
