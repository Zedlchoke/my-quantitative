# DOWNLOAD MANIFEST — Lane A, NBA-WINPROB-NG-PREP-V1 (2026-10-05, $0 only)

Newly downloaded THIS lane. The pre-existing hoopR corpus
(`~/.my-quantitative-data/nba-hoopr-v1/raw/`, 13 files, pulled 2026-10-05T01:35–01:36Z
by WINPROB-NG-PREP-V1 lane A) is untouched — EXTEND-ONLY honored; its provenance
lives in that directory's `_download_provenance.tsv` + `ATTRIBUTION.md`.

## New downloads: play-by-play seasons 2016–2025 (spread-feature census)

- **Destination**: `~/.my-quantitative-data/nba-ng-prep-v1/pbp_2016_2025/` (outside git)
- **Source URL pattern**: `https://github.com/sportsdataverse/sportsdataverse-data/releases/download/espn_nba_pbp/play_by_play_{season}.parquet`
- **Release tag**: `espn_nba_pbp` on `github.com/sportsdataverse/sportsdataverse-data`
  (asset `updated_at` per GitHub API for this tag, from the prior lane's provenance
  of the same tag: 2026-09-09T05:16:34Z for play_by_play_2026; per-season assets
  refresh daily in-season — bytes hashed below are what was pulled)
- **Pull time UTC**: 2026-10-05T03:44–03:47Z (10 sequential direct downloads,
  ~4s apart; file mtimes 10:46:26→10:46:57 local, UTC+7)
- **Auth**: none (release body verbatim: "Direct download (no auth, no API key)")
- **License**: data © hoopR.nba authors, CC BY 4.0 (covers "data, code, and
  documentation" on the producer repo `sportsdataverse/hoopR-nba-data`);
  distribution repo `sportsdataverse-data` root LICENSE = MIT © 2023
  SportsDataverse. Upstream source: ESPN NBA API (release body verbatim).
  Attribution law: credit line in `~/.my-quantitative-data/nba-hoopr-v1/raw/ATTRIBUTION.md`.

| file | bytes | sha256 |
|---|---:|---|
| play_by_play_2016.parquet | 25,999,321 | 70f594cf09ed2a3d157e91aa433206854ad6b58f403802a1f5679936f9adb151 |
| play_by_play_2017.parquet | 26,151,903 | 06a0426af80e58d50b532aab2334e1f8d84fdf4e3b152a4c5fbbe526612c5aa6 |
| play_by_play_2018.parquet | 26,839,399 | 75ce3720fd3c53e33619ff0309eed3df7e9a8d26447470a9927ebe08229544c6 |
| play_by_play_2019.parquet | 28,103,629 | 8580ff36b58665c43e05beebd78d830e4ef69694cfb7fcf4c284bfa0b9bc8507 |
| play_by_play_2020.parquet | 24,966,617 | b6413e4c9d0bfd0d57b3b8b4f23c0dfef9487022c5e02da87adb77ff6ac127b5 |
| play_by_play_2021.parquet | 25,031,848 | 1aa4b333bed1c43dfb457f6ff1542f0a47d9e1b6c10461b40e456ed646b5f700 |
| play_by_play_2022.parquet | 28,327,133 | c7269c55787a43952e071cae9364de378e79f55e956a14d8846b83051ff66537 |
| play_by_play_2023.parquet | 21,052,023 | 4714c6b0c9bad84e2a0579f13474ba6ffb6fdb0a1923f7c890020c5e55373738 |
| play_by_play_2024.parquet | 20,618,404 | 62b609ea487d23aec11e6756d7477a8b1df3a1e57e97fc90c7230b62a5835af1 |
| play_by_play_2025.parquet | 21,552,259 | e3a61b57e491b71379abd1ad4c0b2617500a3921deadd3319ee9362d49d2a9dc |

Total new bytes: 268,642,536 (~256 MiB). Purpose: spread-feature coverage
census + pbp/schedule reconciliation (GAME_UNIVERSE_SPEC §5–6). Parquet read
with pyarrow 25.0.1 / pandas 3.0.5 (schema/coverage counting only).

## BDL spot-check request artifacts (redacted)

- **Destination**: `~/.my-quantitative-data/nba-ng-prep-v1/bdl_spotcheck/` —
  one redacted response summary per queried date
  (`resp_{season}_{date}.json`: game id/date/datetime/status/scores/team
  abbreviations only). API key never stored, never logged; requests carry the
  key in the Authorization header only (never in any URL pattern recorded).
- Underlying network calls: `GET https://api.balldontlie.io/v1/games?dates[]=YYYY-MM-DD`
  (free tier, ≤5 req/min enforced at ≥13 s spacing, targeted dates only,
  no bulk). Aggregate: `lanes/A_DATA/BDL_CROSSCHECK_A_DATA.json`.

## Nothing else downloaded

No other network fetches this lane beyond the BDL spot requests above
(26 spot requests total across the session, all ≥13 s apart, $0).
