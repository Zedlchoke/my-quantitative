# COVERAGE AUDIT — Lane B_WNBA_FEAT · WINPROB-PLAYERFEAT-PREP-V1 · 2026-10-05

All numbers measured this session from bytes by `build_features.py` (recorded in
`FEATURE_TABLE_MANIFEST.json`) over the read-only corpus
`~/.my-quantitative-data/wnba-prep-v1/roster_audit/` and schedules
`~/.my-quantitative-data/wnba-v1/raw/espn_schedules/`. Counting/joining only — no scored
computation.

## 1. Corpus integrity before use

Spot re-hash of **8 files** vs `download_manifest_r2.json` (requirement: ≥6, incl. ≥1
player_box + ≥1 game_rosters, incl. 2002-era and 2026): player_box 2002/2013/2020/2026 +
game_rosters 2002/2013/2019/2026 — **8/8 sha256 match, 8/8 byte-size match, 0 mismatches**.
Row counts (data rows, excl. header): player_box 2002 = 344, 2013 = 4,961, 2026 = 8,293;
game_rosters 2002 = 5,959, 2013 = 4,961, 2026 = 8,293. Full corpus = 50 CSVs
(86,572,091 bytes per predecessor full re-hash, 50/50 match — spot check re-verified here).

## 2. Game universe (law re-applied, cross-checked)

Filter law: keep `status_type_state=='post'`; drop `Forfeit`/`Postponed`; drop All-Star alias
rows (EAST/WEST/ALL/USA/DEL/PAR/WIL/STE/CLA/COL/SPO/COOP/WNBASTARS on home or away
abbreviation); TBD placeholders are `pre` and already excluded.

**Re-derived universe = 5,988 games — exactly the predecessor's census (`match: true`).**
Per-season 2002→2026: 271, 255, 237, 238, 257, 242, 259, 242, 220, 224, 223, 221, 222, 225,
220, 219, 220, 220, 147 (Wubble), 210, 240, 261, 263, 311, 341 — identical to the
predecessor's measured list, row by row.

## 3. Per-season join rates vs the 5,988 universe (key: ESPN `game_id`)

| season | player_box cov | pb rate | rosters cov | gr rate | ≥90% floor | minutes-eligible (2013+) |
|---|---|---|---|---|---|---|
| 2002 | 16/271 | 5.9% | 270/271 | 99.6% | no | no |
| 2003 | 194/255 | 76.1% | 255/255 | 100% | no | no |
| 2004 | 214/237 | 90.3% | 237/237 | 100% | **yes** | no |
| 2005 | 229/238 | 96.2% | 238/238 | 100% | yes | no |
| 2006 | 255/257 | 99.2% | 255/257 | 99.2% | yes | no |
| 2007 | 240/242 | 99.2% | 242/242 | 100% | yes | no |
| 2008 | 252/259 | 97.3% | 258/259 | 99.6% | yes | no |
| 2009 | 242/242 | 100% | 242/242 | 100% | yes | no |
| 2010 | 219/220 | 99.6% | 220/220 | 100% | yes | no |
| 2011 | 224/224 | 100% | 224/224 | 100% | yes | no |
| 2012 | 221/223 | 99.1% | 223/223 | 100% | yes | no |
| 2013 | 221/221 | 100% | 221/221 | 100% | yes | **yes** |
| 2014–2026 | 100% every season | 100% | 100% (2016: 219/220) | ≥99.6% | yes | yes |

Overall (predecessor cross-check): player_box covers 5,624/5,988 = 93.92%; game_rosters
5,983/5,988 = 99.92%. File-side extras are All-Star games (19 pb, 13 gr + the forfeited
2018-08-03 game `401018942` whose rosters exist but player_box does not); postponed
`401507167`/`401857072` absent from both. All extras excluded from every feature input (the
build restricts to universe games).

**Floors enforced in the feature table** (FEATURE_SPEC §7): game-coverage ≥90% applies
2004+; minutes-quality floor 2013+ for ALL minutes-weighted variants (Groups A/B/C);
2002 minutes 100% null → excluded. Consequences in the table: 2003–2004 continuity neutral
(prior season <2013 and 2003 coverage 76.1% <90%); Group B/C computed rows exist only for
seasons ≥2013 (plus `games_played`-only rows would exist 2004+ but every B value is
minutes-dependent, so B/C are uniformly pre-2013-neutral).

## 4. Minutes / DNP semantics per era (restated from predecessor + re-measured)

- 2002: legacy `min` column, `--` = null, **100% null** (344/344 rows) — minutes excluded.
- 2003–2011: `minutes` float; nulls = non-players; `did_not_play` never populated (0 True).
- 2012–2026: `did_not_play` populated (180–1,461 rows/season, e.g. 733 in 2013, 1,461 in
  2026); null minutes ≈ DNP count (±10).
- Absence proxy (Group C) therefore uses the null-minutes reading uniformly; DNP flag
  exists throughout the eligible (2013+) window and is consistent with null-minute counts.

## 5. Team-minutes degeneracy — measured answer

Question (packet): does WNBA team minutes ≡ 200 + 25·n_OT hold in this corpus?

**Measured answer: NOT exactly, for two distinct reasons.**

1. **Backfill era (2003–2008): systematically incomplete.** Team-game minute totals: share
   in [195,205] is only 8.5–13.1%; share ≤194 is 79.8–86.5%; share ==200 is 0.000–0.004.
   Medians ≈190, maxima up to 272 — many players' minutes are missing from the era's
   backfilled box rows, so totals sit well below 200. This independently confirms the
   packet's minutes-quality floor: even where GAME coverage passes ≥90% (2004+), MINUTE
   totals are not trustworthy before 2009, and the frozen law stays 2013+.
2. **Modern era (2009–2026): complete but integer-rounded.** Share in [195,205] is
   90.6–97.7%; share ==200 is 40.1–49.8% (ESPN rounds each player's minutes to integers, so
   regulation totals scatter 199–202); share ≥205 is 2.3–11.3% (OT games ≈ 205 + 5·n_OT
   appearance); share ≤194 is 0.0% from 2013 (≤1% 2009–2012). So `200 + 25·n_OT` is the
   NOMINAL law; the corpus carries integer-rounded per-player minutes, making exact
   equality rare (~34% of all team-games pooled 2002–2026). Consequence frozen into the
   spec: no feature assumes the identity; totals are consumed as measured; OT is NOT
   normalized away (documented as a residual wobble of ±2 minutes/game in Group B inputs).

| season | team-games | ==200 | 195–205 | ≥205 | ≤194 | median |
|---|---|---|---|---|---|---|
| 2002 | 0 (all null) | – | – | – | – | – |
| 2003 | 390 | 0.000 | 0.085 | 0.056 | 0.859 | 190 |
| 2004 | 428 | 0.000 | 0.103 | 0.063 | 0.836 | 189 |
| 2005 | 460 | 0.000 | 0.087 | 0.059 | 0.857 | 190 |
| 2006 | 512 | 0.000 | 0.098 | 0.037 | 0.865 | 190 |
| 2007 | 482 | 0.000 | 0.098 | 0.077 | 0.826 | 190 |
| 2008 | 504 | 0.004 | 0.131 | 0.071 | 0.798 | 190 |
| 2009 | 486 | 0.451 | 0.876 | 0.113 | 0.010 | 200 |
| 2010 | 440 | 0.436 | 0.934 | 0.061 | 0.004 | 200 |
| 2011 | 450 | 0.473 | 0.942 | 0.053 | 0.004 | 200 |
| 2012 | 442 | 0.401 | 0.932 | 0.063 | 0.004 | 200 |
| 2013 | 444 | 0.446 | 0.946 | 0.054 | 0.000 | 200 |
| 2014 | 446 | 0.442 | 0.906 | 0.094 | 0.000 | 200 |
| 2015 | 452 | 0.467 | 0.938 | 0.062 | 0.000 | 200 |
| 2016 | 436 | 0.433 | 0.908 | 0.092 | 0.000 | 200 |
| 2017 | 440 | 0.461 | 0.946 | 0.054 | 0.000 | 200 |
| 2018 | 442 | 0.498 | 0.968 | 0.032 | 0.000 | 200 |
| 2019 | 442 | 0.439 | 0.977 | 0.023 | 0.000 | 200 |
| 2020 | 294 | 0.490 | 0.973 | 0.027 | 0.000 | 200 |
| 2021 | 422 | 0.436 | 0.924 | 0.076 | 0.000 | 200 |
| 2022 | 482 | 0.442 | 0.950 | 0.050 | 0.000 | 200 |
| 2023 | 524 | 0.468 | 0.958 | 0.042 | 0.000 | 200 |
| 2024 | 528 | 0.449 | 0.962 | 0.038 | 0.000 | 200 |
| 2025 | 624 | 0.482 | 0.974 | 0.026 | 0.000 | 200 |
| 2026 | 684 | 0.453 | 0.962 | 0.038 | 0.000 | 200 |

## 6. Feature-table outcome

11,976 rows = 2 × 5,988 (every universe game, both sides). Computed rows: continuity
5,907 (2014–2026); Group B k=5 5,778; Group C form 5,778. Neutral reasons (continuity):
`prior_minutes_floor_pre2013` 5,168; `no_prior_in_corpus` 542 (2002);
`expansion_no_prior` 202 (CHI 2006, ATL 2008, GSV 2025, TOR/PDX 2026, both sides);
`game1_v2_not_usable` 157 (game-1 rows of continuity-eligible seasons). Full counts in
`FEATURE_TABLE_MANIFEST.json → neutral_reason_counts`.
