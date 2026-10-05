# DOWNLOAD MANIFEST — NBA player box samples (Lane A, WINPROB-PLAYERDATA-PREP-V1)

All downloads 2026-10-05 from GitHub release
`espn_nba_player_boxscores` of `sportsdataverse/sportsdataverse-data`
(the distribution store documented by hoopR's `load_nba_player_box()`).
Machine-readable twin: `~/.my-quantitative-data/playerdata-prep-v1/nba/download_manifest.json`.

## Files downloaded (CSV format chosen for inspectability)

| file (local path under `~/.my-quantitative-data/playerdata-prep-v1/nba/`) | asset URL | HTTP | bytes | sha256 | downloaded_utc |
|---|---|---|---|---|---|
| `player_box_raw/player_box_2016.csv` | `https://github.com/sportsdataverse/sportsdataverse-data/releases/download/espn_nba_player_boxscores/player_box_2016.csv` | 200 | 16,687,907 | `ffd09dec990bc322…13ec74397` | 2026-10-05T07:24:06Z |
| `player_box_raw/player_box_2021.csv` | `…/espn_nba_player_boxscores/player_box_2021.csv` | 200 | 16,122,075 | `86b12342459b7864…5110bcc638f` | 2026-10-05T07:24:09Z |
| `player_box_raw/player_box_2026.csv` | `…/espn_nba_player_boxscores/player_box_2026.csv` | 200 | 17,729,581 | `7a4868da67ae7f6e…56f1becc89` | 2026-10-05T07:24:12Z |
| `provenance/timestamp_refetch1.txt` | `…/espn_nba_player_boxscores/timestamp.txt` | 200 | 24 | `142bf92af1ceb359…07b1194038c` | 2026-10-05T07:24:38Z |
| `provenance/timestamp_refetch2.txt` | `…/espn_nba_player_boxscores/timestamp.txt` | 200 | 24 | `142bf92af1ceb359…07b1194038c` | 2026-10-05T07:24:41Z |

Full sha256 (from `shasum -a 256`):

```
ffd09dec990bc3226ab7fc02d8a80c4933832527a5ae8eb808d0f6513ec74397  player_box_2016.csv
86b12342459b786450460000ad4de6a6c6a618ae064f6047e19565110bcc638f  player_box_2021.csv
7a4868da67ae7f6ebfba23389e04220be2e3f69d2e56a3942c02aa56f1becc89  player_box_2026.csv
```

Byte sizes equal the GitHub API asset metadata exactly (cached listing,
`provenance/sportsdataverse-data_release_espn_nba_player_boxscores.json`).

## Release metadata (from cached GitHub API listing, 2026-10-05)

- Release/tag: `espn_nba_player_boxscores`; release object published 2023-03-29T22:29:13Z.
- Assets rebuilt by pipeline: 2016 asset 2026-05-30T12:54:14Z; 2021 asset
  2026-08-26T06:15:07Z; 2026 asset 2026-09-09T05:17:39Z.
- Store contents (season list from the release assets, not just downloads):
  `player_box_2002 … player_box_2026` in `.csv`, `.parquet`, `.rds` (25 seasons,
  ESPN ending-year season labels), plus `timestamp.txt`
  ("2026-09-09 01:17:39 EDT" = last pipeline rebuild) and `package_function.*`.
- Latest available season in the store: **2026** (checked: 2026 present).
  2025 also present. Both older than requested and newer seasons absent (none expected —
  the 2026-27 season has not started as of 2026-10-05).

## Re-downloadability (determinism) — PROVEN

1. HEAD request (2026-10-05T07:24:27Z) on the 2016 asset: 302 → release-assets CDN,
   final target `HTTP/2 200`, `content-length: 16687907` (matches download),
   `etag: "0x8DEBE4A8DACFE64"`, `last-modified: Sat, 30 May 2026 12:54:14 GMT`
   (evidence: `provenance/head_etag_player_box_2016.txt`).
2. Full re-fetch of `player_box_2016.csv` (2026-10-05T07:24:38Z): sha256
   `ffd09dec…13ec74397` — identical to first download; `cmp` → IDENTICAL (exit 0).
3. `timestamp.txt` fetched twice, identical sha256 both times.

The store is therefore re-downloadable and byte-stable for a fixed asset
revision. Caveat: the pipeline rebuilds assets (last 2026-09-09); a future
rebuild can change bytes — manifests must pin sha256 at download time, as here.

## Season choice rationale

- 2016: earliest of the NBA 2016+ evaluation window (store label; see
  COVERAGE_SCHEMA.md §6 for the label-convention note).
- 2021: mid-window, COVID-disrupted season (postponements + play-in) — stress case.
- 2026: latest season available in the store (checked 2025 and 2026; 2026 chosen).
