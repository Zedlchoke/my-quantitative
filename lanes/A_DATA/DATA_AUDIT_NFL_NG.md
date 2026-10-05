# DATA_AUDIT_NFL_NG — Lane A · DATA (nflng-a-data), cycle NFL-WINPROB-NG-PREP-V1

Audit date: 2026-10-05 · auditor: Lane A quant-explorer · $0 only (free public GitHub
releases of nflverse; no accounts, keys, purchases). Schema/coverage/chronology
measurements ONLY — no win-prob metric, model score, or outcome metric was computed.

## 1. Rights verdict — PASS (re-verified verbatim from upstream bytes, not assumed)

Fetched 2026-10-05T03:20:40Z:
`https://raw.githubusercontent.com/nflverse/nflverse-data/main/LICENSE.md`
(sha256 `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111`,
18,651 bytes, held at `~/.my-quantitative-data/nfl-ng-prep-v1/rights/nflverse-data_LICENSE.md`).
The held bytes are the canonical license text, title line verbatim:

> Creative Commons Attribution 4.0 International Public License

Load-bearing clauses, verbatim from the held copy:

- §2(a)(1) grant: "the licensor grants You a worldwide, royalty-free,
  non-sublicensable, non-exclusive, irrevocable license to Reproduce the
  Licensed Material, in whole or in part, and to perform, Display, and
  communicate the Licensed Material, in whole or in part" and "to produce,
  Reproduce, and Share Adapted Material".
- §3(a)(1)(A): attribution condition — "retain the following if it is supplied
  by the Licensor with the Licensed Material: (i) identification of the creator
  of the Licensed Material ... (ii) a copyright notice".
- §4 (Sui Generis Database Rights): "for the avoidance of doubt, Section
  2(a)(1) grants You the right to extract, reuse, reproduce, and Share all or a
  substantial portion of the contents of the database".

Cross-check: the independent verifier of the terminal cycle fetched the same
URL on 2026-10-04 and reached the same verdict
(`.worktrees/nfl-winprob-scored-v1/integration/research/control/NFL-WINPROB-SCORED-V1/lanes/E2_data_freeze/VERIFICATION_REPORT.md` §7,
"Rights — DATA_RIGHTS_OK"). Attribution string to use verbatim (from the
archive's `ATTRIBUTION.md`):

> Data: nflverse/nflverse-data releases (CC BY 4.0), https://github.com/nflverse/nflverse-data

**nfldata caveat (documentation-only use):** the `games.csv` column dictionary
lives in the `nflverse/nfldata` repo (DATASETS.md, fetched 2026-10-05, sha256
`8835ca9c15784a2cdc04c2c599c54b373629f8fbe91117acd5b7d0c615e03bf4`). The
nfldata repo root listing (GitHub contents API, held bytes) contains **no
LICENSE file** — therefore NO data is pulled from nfldata; data comes ONLY from
nflverse-data release browser-download URLs, which are CC BY 4.0. DATASETS.md
is cited as documentation of column semantics.

Verdict per asset (all from `https://github.com/nflverse/nflverse-data/releases/download/<tag>/<asset>`):

| asset | release tag | rights verdict |
|---|---|---|
| schedules/games.csv (+timestamp.json) | `schedules` | PASS — CC BY 4.0 verified verbatim |
| pbp/play_by_play_2021..2025.parquet (+timestamp.json) | `pbp` | PASS — CC BY 4.0 verified verbatim |
| teams/teams_colors_logos.csv (+timestamp.json) | `teams` | PASS — CC BY 4.0 verified verbatim |
| injuries/injuries_2025.csv, injuries_2026.csv (+timestamp.json) | `injuries` | PASS — CC BY 4.0 verified verbatim (rights PASS ≠ PIT PASS; see INJURY_PIT_VERDICT.md) |

No asset hit the BLOCKED_DATA_RIGHTS stop condition.

## 2. Provenance chain

- Upstream: nflverse-data release browser downloads (GitHub Releases), tags
  `schedules`, `pbp`, `teams`, `injuries`. schedules/games.csv is maintained by
  Lee Sharpe (per nfldata DATASETS.md); pbp parquets are the nflfastR ecosystem
  build; injuries is the nflverse injuries scrape.
- Archive (frozen inputs of the prior cycles): `~/.my-quantitative-data/nfl-nflverse-v1/`
  — all 9 files re-hashed 2026-10-05 by this lane; every sha256 matches the
  inventory recorded in `raw/ATTRIBUTION.md` and the terminal-cycle
  FREEZE_MANIFEST chain (games.csv `f1e8fe78…5248e`; ATTRIBUTION.md
  `b1852975…3aedc`). Raw archive untouched (no bytes written).
- This cycle's fresh pulls: `~/.my-quantitative-data/nfl-ng-prep-v1/`
  (see DOWNLOAD_MANIFEST.md for URL/version/pull-time/sha256/size per file).

## 3. Measured coverage per season — games.csv (fresh copy, release compile
2026-10-05T03:16:28Z)

Total rows 7,548, seasons 1999–2026 (schedule + results in one file; scores NA
for unplayed). Season structure measured directly from the file:

| seasons | rows/season | teams | game_type composition |
|---|---|---|---|
| 1999–2001 | 259 | 31 | REG 248 + WC 4, DIV 4, CON 2, SB 1 |
| 2002–2019 | 267 | 32 | REG 256 + WC 4, DIV 4, CON 2, SB 1 |
| 2020 | 269 | 32 | REG 256 + WC 6, DIV 4, CON 2, SB 1 |
| 2021, 2023, 2024, 2025 | 285 | 32 | REG 272 + WC 6, DIV 4, CON 2, SB 1 |
| 2022 | 284 | 32 | REG **271** + 13 playoff (canceled game omitted, §7) |
| 2026 (in progress) | 272 | 32 | REG only, weeks 1–18 scheduled; no playoff rows yet |

- Kickoff-grain coverage: `gametime` is 100% missing in 1999 (259 rows) and
  100% present 2000–2026. Kickoff-UTC-capable coverage = seasons 2000–2026
  (consistent with the PREP-era finding "1999 gametime 100% missing —
  measured, 259 rows skipped").
- Every finished game has scores; `result` == home_score − away_score and
  `total` == home_score + away_score hold on all 7,446 finished Home rows +
  Neutral rows (checked all finished rows). 446 finished games have
  overtime == 1.
- pbp parquets 2021–2025 (archive): measured 49,922 / 49,434 / 49,665 /
  49,492 / 48,771 plays = 247,284 total, 285/284/285/285/285 games per season,
  REG 271–272 + POST 13 each, weeks 1–22, 32 teams — counts reconcile exactly
  with games.csv per-season rows.

## 4. Kickoff-time schema + UTC conversion story

- Verbatim semantics (nfldata DATASETS.md §Games, held bytes): `gametime` —
  "The kickoff time of the game. This is represented in 24-hour time and the
  Eastern time zone, regardless of what time zone the game was being played in."
- The file has NO UTC column. UTC is derived consumer-side as
  `gameday + gametime` in `America/New_York` (zoneinfo), which resolves
  EDT/EST per date. The PREP-era controller decision (America/New_York → UTC
  via zoneinfo; uniform-offset safety argument for ordering) remains the
  documented method. Every 2026 row has a parseable gametime (272/272).
- Edge semantics: `gameday` is the game date (local US); London/Munich/Madrid
  morning kickoffs are still stored in ET (e.g., 09:30 ET international games)
  — conversion to UTC remains correct under the documented rule.

## 5. Team-ID crosswalk + franchise moves (measured from the file itself)

35 distinct team abbreviations appear in games.csv 1999–2026. Move evidence is
directly measurable from season ranges:

| lineage | abbreviation timeline (measured) | note |
|---|---|---|
| Raiders | OAK 1999–2019 → LV 2020–2026 | relocation Oakland→Las Vegas |
| Chargers | SD 1999–2016 → LAC 2017–2026 | relocation San Diego→Los Angeles |
| Rams | STL 1999–2015 → LA 2016–2026 | relocation St. Louis→Los Angeles |
| Washington | WAS 1999–2026 (constant) | renames (Football Team→Commanders) are invisible in IDs; current full name "Washington Commanders" from teams_colors_logos.csv |
| Browns/Ravens | CLE 1999–2026 and BAL 1999–2026, separate | file begins at the 1999 Browns reactivation; standard convention keeps CLE and BAL as separate franchise lines (32-lineage convention frozen in PREP_SUMMARY_NFL.md) |
| Texans | HOU 2002–2026 (expansion) | 31 teams 1999–2001, 32 from 2002 |

Crosswalk source for abbreviation → full name/conf/division:
`teams_colors_logos.csv` (release tag `teams`, 32 rows; measured e.g.
`WAS,Washington Commanders,5110,Commanders,NFC,NFC East`;
`LV,Las Vegas Raiders,2520,...AFC West`). The teams file is current-state only
— historical abbreviations (SD/STL/OAK) are NOT in it; historical continuity
must come from the season ranges above (measured) and the 32-lineage mapping
frozen by the predecessor cycle.

## 6. Neutral-site flag, ties / cancel / forfeit

- `location` ∈ {`Home`, `Neutral`} — verbatim doc: "Either `Home` if the home
  team is playing in their home stadium, or `Neutral` if the game is being
  played at a neutral location. This still shows as `Home` for games between
  the Giants and Jets even though they share the same home stadium."
  Measured: 7,446 Home / 102 Neutral rows total; Neutral per season 1–2 early,
  4–8 from 2020s (international games + Super Bowl); 2026 has 8 (REG only).
  HCA-neutral handling was already frozen predecessor-side (HCA=0 on Neutral).
- Ties: no explicit flag column; ties are score-equality rows. Measured 15
  finished ties total (2002, 2008, 2012, 2013, 2014, 2016×2, 2018×2, 2019,
  2020, 2021, 2022×2, 2025); none in 2026 so far. Predecessor law (tie counts
  half-win in form; excluded from scoring) stays compatible.
- Cancellations/forfeits: no flag column exists. The only in-scope cancellation
  (2022 week 17 BUF@CIN, Damar Hamlin incident, never played) is **omitted
  from the file entirely**: 2022 has 271 REG rows, zero rows with missing
  scores after the season completed. Consumers must not assume
  `n_REG == 256 or 272` exactly — use row counts, not nominal schedule size.
  No forfeited/scoreless-awarded rows exist anywhere in the file.
- Anomaly scan: rows with `gameday < 2026-10-05` and no score = exactly 1 —
  `2026_04_DET_CAR` (SNF 2026-10-04, kickoff 2026-10-05T00:20:00Z; in progress
  at the release compile 03:16:28Z and at audit time). No retro-corrupted rows
  detected between the two daily snapshots (see §8).

## 7. Schema drift early vs late seasons

Schema is a single 46-column table (identical between the 2026-10-04 archive
copy and the 2026-10-05 fresh copy — verified). Drift is in column POPULATION,
not shape:

| column group | 1999–2005 | 2006–2010 | 2011–2015 | 2016–2020 | 2021–2026 |
|---|---|---|---|---|---|
| gametime (ET) | 14% missing (1999=100%) | 0% | 0% | 0% | 0% |
| gsis id | 0% | 0% | 0% | 0% | 12.3% (2026 unplayed rows) |
| pff id | 100% | 0% | 0% | 0% | 64.3% (2026 unplayed) |
| ftn id | 100% | 100% | 100% | 60% | 16.8% |
| espn id | 0% | 0% | 0% | 0% | 0% |
| moneyline / spread / total_line | 100% / 0% / 0% | 10.1% / 0% / 0% | 0% | 0.1% | 11.4% (2026 unplayed) |
| temp / wind | 21.2% (domes) | 26.6% | 26.8% | 27.7% | 49.2% (2026 unplayed) |
| referee / QB ids | 0% | 0% | 0% | 0% | 13.2% / 11.4% (2026 unplayed) |

Reading: core identity columns (game_id, season, game_type, week, gameday,
weekday, teams, location) are complete across all seasons; kickoff-UTC grain is
reliable from 2000; venue/weather/officials/QB and odds columns fill in closer
to kickoff, so UNPLAYED rows are systematically sparse. Odds/betting columns
(away/home_moneyline, spread_line, total_line, *_odds) remain QUARANTINED for
modeling per the terminal-cycle data contract — their presence here is measured
for schema completeness only.

Doc drift noted: nfldata DATASETS.md still says "Data begins with the 2006 NFL
season" and documents 1–17 regular-season weeks, but the release file begins
1999 and includes 272-game 18-week REG seasons + ftn/nfl_detail_id/rest/QB
columns absent from the doc. The release file bytes (this audit) supersede the
doc where they disagree.

pbp schema note: pbp parquets carry 372 columns (2021) including embedded
model-output columns (`wp`, `home_wp`, `epa`, `vegas_wp`, …). Those are
nflfastR/vegas model artifacts INSIDE the data — this audit only records their
presence; per the terminal-cycle quarantine they are not used to compute any
score, and pbp-derived features were NOT_RUN in v1 (post-game compilation +
retro corrections). pbp has `season_type` (REG/POST), not `game_type`.

## 8. Publish / as-of story (release-cadence evidence)

- schedules release compiles ~twice daily; evidence from asset `updated_at`:
  2026-10-04T12:16:32Z (archive pull) and 2026-10-05T03:16:30Z (this cycle's
  pull), with timestamp.json contents "2026-10-04 08:16:30 EDT" /
  "2026-10-04 23:16:28 EDT". Post-game compiled: the 03:16:28Z compile contains
  ALL Sunday week-4 finals EXCEPT the game still in progress at compile time
  (DET@CAR, kickoff 00:20Z, ended after the compile). There is no per-record
  publish timestamp in schedules; the release timestamp.json is the only as-of
  marker.
- Retro-correction observation (single 15h window, not a law): comparing
  archive copy vs fresh copy, 13 games gained final scores, 0 already-scored
  rows changed scores.
- pbp release: per-season parquets; completed seasons finalize after the Super
  Bowl (2025 parquet asset updated_at 2026-08-13; 2024 2026-08-13; 2023/2022
  2026-02-12; 2021 2026-01-08); current-season pbp updates weekly in-season.
  NEVER usable pre-game for the current week.
- injuries release: timestamp.json "2026-10-04 09:08:56 EDT" (=13:08:56Z),
  i.e., AFTER the week's Sunday games begin — weekly report snapshots as of
  compile time, no per-record timestamps (verdict in INJURY_PIT_VERDICT.md).

## 9. Conclusion

- Rights: PASS for every audited asset (CC BY 4.0, verbatim-re-verified
  2026-10-05 from upstream bytes; nfldata = documentation-only, no license).
- Coverage: 2000–2026 complete at kickoff grain (schedule + results); 1999
  rows exist but lack kickoff times; 2026 in progress (272 REG scheduled).
- 2026 split vs the cycle prospective epoch: see GAMES_2026_CLASSIFICATION.md —
  every played 2026 game is NOT_RUN prospective.
- Injury/availability: NOT_RUN_PIT (see INJURY_PIT_VERDICT.md).
- No metric on real outcomes was computed anywhere in this lane.
