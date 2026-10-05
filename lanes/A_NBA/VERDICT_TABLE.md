# VERDICT TABLE — Lane A (NBA player data), WINPROB-PLAYERDATA-PREP-V1

Date: 2026-10-05. Verdicts are PREP-level (data/readiness), never scored GO.

## Checks × data type

| check | NBA player box (store `espn_nba_player_boxscores`) | notes |
|---|---|---|
| on-disk inventory before lane | **PASS** (NONE proven) | exhaustive `find` over `~/.my-quantitative-data`; only WNBA player files + PBP athlete fields |
| source publishes player box scores | **PASS** | hoopR man page + pkgdown + README + store release listing (all cached) |
| license verified from official file | **PASS** | store LICENSE (MIT) + hoopR-nba-data LICENSE.md (CC BY 4.0), verbatim, URLs+timestamps in RIGHTS.md |
| download ≥1 early / 1 mid / latest season | **PASS** | labels 2016 / 2021 / 2026 (CSV), HTTP 200, bytes==API metadata |
| per-file provenance (URL/tag/name/status/utc/bytes/sha256) | **PASS** | DOWNLOAD_MANIFEST.md + download_manifest.json |
| re-download determinism | **PASS** | HEAD/ETag + full re-fetch sha256 identical + `cmp` IDENTICAL |
| schema/columns audit | **PASS** | 57 cols, identical across 3 samples; keys present |
| coverage vs schedule corpus (game_id join) | **PASS** | 100% / 97.34% / 99.70% raw; 100% of PLAYED games (all gaps = STATUS_POSTPONED) |
| duplicates (game_id+athlete_id) | **PASS** | 0 / 0 / 0 |
| missing-value audit on keys | **PASS** (with noted caveat) | 2026: 33 identity-less rows (~0.09%) |
| DNP/inactive rows present | **PASS** | 5,698 / 6,517 / 6,082 DNP rows with specific `reason` values |
| schema drift across samples | **PASS** (samples only) | zero drift 2016/2021/2026; 2002–2015 not sampled |
| field-semantics validation | **PASS** (with caveats) | `starter` = exactly 5/team-game; `active` UNRELIABLE (documented); 2021 play-in boxes unpopulated |
| PIT: prior-game as-of join constructible | **PASS** (constructible) | tip_utc inputs 100% present; worked example max(prior tip) < target tip |
| PIT: target-game availability/starter/DNP as feature | **NOT_RUN_PIT** | no pre-game publish timestamp; post-game fields only |
| PIT: per-row availability timestamps | **NOT_RUN_PIT** | store has none; margin option documented |
| feature hypotheses + comparison design | **PASS** (design only) | FEATURE_PROPOSALS.md; nothing computed |
| scored evaluation | **NOT_RUN** (correct for PREP) | out of scope by plan |

## Actually-downloaded files (path + sha256)

Under `~/.my-quantitative-data/playerdata-prep-v1/nba/`:

| path | bytes | sha256 |
|---|---|---|
| `player_box_raw/player_box_2016.csv` | 16,687,907 | `ffd09dec990bc3226ab7fc02d8a80c4933832527a5ae8eb808d0f6513ec74397` |
| `player_box_raw/player_box_2021.csv` | 16,122,075 | `86b12342459b786450460000ad4de6a6c6a618ae064f6047e19565110bcc638f` |
| `player_box_raw/player_box_2026.csv` | 17,729,581 | `7a4868da67ae7f6ebfba23389e04220be2e3f69d2e56a3942c02aa56f1becc89` |
| `provenance/timestamp_refetch1.txt` | 24 | `142bf92af1ceb359703f01d85ac25f04e611f5f25206b9b048d0007b1194038c` |
| `provenance/timestamp_refetch2.txt` | 24 | `142bf92af1ceb359703f01d85ac25f04e611f5f25206b9b048d0007b1194038c` |

Plus written artifacts: `ATTRIBUTION.md`, `download_manifest.json`,
`provenance/*` (release listing, LICENSE copies, hoopR docs, analysis logs,
HEAD/ETag evidence, download log).

## Remaining blockers

- None blocking PREP. Carry-forward caveats: (1) season-label offset
  (ESPN ending-year vs workspace naming) must be fixed in any successor spec;
  (2) `active` field unreliable — use `did_not_play`+`minutes`+`reason`;
  (3) 2021 play-in (season_type=5) boxes unpopulated; (4) 2026 has 33
  identity-less rows; (5) underlying ESPN/NBA data rights unresolved for any
  future publication/commercial use (RIGHTS.md §4); (6) target-game
  availability status remains NOT_RUN_PIT — only prior-game constructions are
  admissible.

## Cost

Actual spend: **$0** (all sources free; no API keys used; balldontlie key
untouched in Keychain).

## Recommendation

**GO** for a future FEATURE-PREP step (building frozen player-feature tables
under the pre-registered design in FEATURE_PROPOSALS.md) — conditioned on
owner instruction + fresh cycle registration per plan. **This is NOT a scored
GO**; no win-prob/metric computation was performed and none is authorized by
this lane.
