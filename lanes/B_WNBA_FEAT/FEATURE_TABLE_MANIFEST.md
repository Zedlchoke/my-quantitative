# FEATURE TABLE MANIFEST — WNBA player features 2002–2026 · Lane B_WNBA_FEAT

Cycle WINPROB-PLAYERFEAT-PREP-V1 · lane B_WNBA_FEAT · 2026-10-05.
Machine-readable twin: `FEATURE_TABLE_MANIFEST.json` (same directory). Feature construction
only — no scored computation, no outcome columns.

## Output

| item | value |
|---|---|
| parquet | `~/.my-quantitative-data/playerfeat-prep-v1/wnba/features/wnba_player_features_2002_2026.parquet` |
| sha256 | `sha256:ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf` |
| bytes | 826,415 |
| rows | 11,976 (= 2 × 5,988 universe games; one row per (game_id, team side)) |
| columns | 40 (exact whitelist in `build_features.py:EXPECTED_COLUMNS`) |
| determinism | two independent full builds → identical sha256; no wall-clock timestamps in table; `tip_utc` columns are scheduled-fact as-of metadata |
| reproducibility | `/Users/hoangminhlong/my-quantitative/.venv/bin/python build_features.py --selftest` (exit 0; 46/46 checks PASS) |

## Inputs (all READ-ONLY; 0 downloads; $0)

- Corpus: `~/.my-quantitative-data/wnba-prep-v1/roster_audit/` player_box_2002..2026.csv +
  game_rosters_2002..2026.csv — spot re-hash 8/8 vs `download_manifest_r2.json` (pb
  2002/2013/2020/2026, gr 2002/2013/2019/2026): all sha256 + byte sizes match.
- Game universe: `~/.my-quantitative-data/wnba-v1/raw/espn_schedules/`
  wnba_schedule_2002..2026.csv — filter law re-applied, 5,988 games (predecessor census
  reproduced exactly).
- Lineage: `~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv` (20 franchise keys) —
  the ONLY franchise join path; raw ESPN abbreviations never used.

## As-of law

`tip_utc_strict_lt_v1`: features use only same-season games with tip strictly before the
target tip; Group A continuity uses the strictly-prior SEASON and (v2) only from that team's
game 2 onward. Asserted per row in selftest (0 violations).

## Groups and computed-row counts

| group | columns | computed rows | neutral reasons (counts) |
|---|---|---:|---|
| A continuity | `continuity_c`, matched/total minutes, roster size, reason | 5,907 (2014–2026) | prior_minutes_floor_pre2013 5,168 · no_prior_in_corpus 542 (2002) · expansion_no_prior 202 (CHI06, ATL08, GSV25, TOR26, POR_PDX26) · game1_v2_not_usable 157 |
| B minutes-mass (k=3) | `b3_minutes_total/hhi/top5_share/games_played/minutes_per_day`, window tips, reason | 5,778 (2013+) | minutes_quality_floor_pre2013 4,165 · coverage_floor_pre_2004 793 · insufficient_history 690 · no_prior_games 550 |
| B minutes-mass (k=5) | `b5_*` (same shapes) | 5,778 (2013+) | same vocabulary; k-selection deferred to a gated successor — both k frozen in the table |
| C form + absence | `c_top5_athlete_ids`, trailing games, `c_form_z_pts/reb/ast`, `c_absence_share`, recent-game keys, reason | 5,778 (2013+) | minutes_quality_floor_pre2013 4,958 · insufficient_history 690 · no_prior_games 550 |

`absence` uses the uniform null-minutes proxy (DNP flag 2012+ cross-checked);
`active`/`reason` fields are UNUSABLE and never read. Continuity is minutes-weighted
→ eligible only from season 2014 (prior-season minutes-quality floor 2013+).

## Per-season rows

2 × universe per season: 2002:542 · 2003:510 · 2004:474 · 2005:476 · 2006:514 · 2007:484 ·
2008:518 · 2009:484 · 2010:440 · 2011:448 · 2012:446 · 2013:442 · 2014:444 · 2015:450 ·
2016:440 · 2017:438 · 2018:440 · 2019:440 · 2020:294 · 2021:420 · 2022:480 · 2023:522 ·
2024:526 · 2025:622 · 2026:682. (Machine copy: `FEATURE_TABLE_MANIFEST.json →
per_season_rows`.)

## Measured laws frozen into this table

1. Universe = 5,988 ESPN-side games (status post; drop Forfeit/Postponed; drop All-Star
   aliases) — reproduced exactly.
2. Coverage floors: game-coverage ≥90% applies 2004+; minutes-quality 2013+ gates ALL
   minutes-weighted variants; 2002 minutes 100% null → excluded.
3. Team-minutes degeneracy (measured, COVERAGE_AUDIT §5): `200 + 25·n_OT` is only the
   NOMINAL law — 2003–2008 totals are systematically incomplete (share in [195,205]:
   8.5–13.1%; ==200: ~0), while 2009+ is complete-but-integer-rounded (==200 share
   40–50%; ≤194 share 0% from 2013). No feature assumes the identity; OT not normalized.
4. Expansion law: CHI 2006, ATL 2008, GSV 2025, TOR 2026, POR_PDX 2026 + all 2002
   team-seasons → neutral in both arms with reason flags (POR_PDX 2026 forced neutral
   despite the lineage prior — packet/W-H2 law; 24-year gap = new franchise entity).
5. `active`/`reason` defective (predecessor measurement restated) — absent from schema.
6. Opening-roster v1 NOT_RUN_PIT (restated); v2 only.
