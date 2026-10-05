# DOWNLOAD_MANIFEST — Lane A_DATA, cycle NFL-WINPROB-NG-SCORED-V1

Audit time: 2026-10-05 (downloads 09:02:02–09:03:26 UTC) · auditor: Lane A_DATA · $0 only
(anonymous browser-download GitHub release URLs; no accounts, no keys). Machine-readable twin:
`DOWNLOAD_MANIFEST.json` (same directory). No win-prob metric, model score, or outcome
evaluation computed in this lane; coverage counting and rights/audit work only.

## 0. Rights gate (ran FIRST — no BLOCKED_DATA_RIGHTS)

`https://raw.githubusercontent.com/nflverse/nflverse-data/HEAD/LICENSE.md` re-fetched live
2026-10-05T09:01:18Z, HTTP 200, 18,651 bytes, sha256
`2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111` — **equals the pinned
predecessor sha256 exactly** (pin: nfl-ng-prep-v1 DATA_AUDIT §1). Copy held at
`~/.my-quantitative-data/nfl-ng-scored-v1/rights/nflverse-data_LICENSE.md`; title line
"Creative Commons Attribution 4.0 International Public License" verbatim at line 57.
CC BY 4.0 confirmed live; underlying league/ESPN publication-commercial rights remain
UNVERIFIED (inherited fail-closed law: internal research only).

## 1. pbp 2000–2017 — release `pbp` (nflverse/nflverse-data), 18/18 OK

URL pattern (public, anonymous):
`https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_YYYY.parquet`
All 18 HTTP 200, PAR1 magic verified, sizes match the GitHub release-API asset metadata
(cached at `~/.my-quantitative-data/nfl-ng-scored-v1/provenance/release_api_pbp.json`);
where the API carries an asset digest (2000/2001/2002) it equals the local sha256 exactly.
Total 315,021,834 bytes. Held at `~/.my-quantitative-data/nfl-ng-scored-v1/raw_pbp_2000_2017/`.

| season | http | downloaded_utc | bytes | sha256 | asset updated_at (API) |
|---|---|---|---|---|---|
| 2000 | 200 | 2026-10-05T09:02:02Z | 13,404,971 | `595c3b0e…d54706` | 2025-07-16T14:29:04Z |
| 2001 | 200 | 2026-10-05T09:02:04Z | 14,007,738 | `43f0eea9…724bca` | 2026-08-13T12:38:45Z |
| 2002 | 200 | 2026-10-05T09:02:06Z | 14,742,308 | `4930befb…4c4aa17` | 2026-08-13T12:39:26Z |
| 2003 | 200 | 2026-10-05T09:02:08Z | 14,620,361 | `a5bc20c6…a2d279d` | 2025-04-30T06:35:51Z |
| 2004 | 200 | 2026-10-05T09:02:11Z | 14,568,240 | `94658bc1…5ae6a03` | 2025-04-30T06:37:54Z |
| 2005 | 200 | 2026-10-05T09:02:13Z | 14,612,857 | `1b93d868…4df92` | 2025-04-30T06:38:09Z |
| 2006 | 200 | 2026-10-05T09:02:15Z | 18,555,685 | `f3d45c8c…b11c2b4` | 2025-04-30T06:33:16Z |
| 2007 | 200 | 2026-10-05T09:02:17Z | 18,716,524 | `bcfded2f…caede9a9` | 2025-04-30T06:41:08Z |
| 2008 | 200 | 2026-10-05T09:02:19Z | 18,565,820 | `f625e836…3af0f07` | 2025-04-30T06:34:15Z |
| 2009 | 200 | 2026-10-05T09:02:21Z | 18,905,386 | `17ba96f5…9d77dee7` | 2025-04-30T06:36:09Z |
| 2010 | 200 | 2026-10-05T09:02:25Z | 19,059,048 | `d2ef9c40…d3a7573b` | 2025-04-30T06:34:41Z |
| 2011 | 200 | 2026-10-05T09:02:27Z | 19,117,830 | `c54753b8…8795b1` | 2025-04-30T06:38:47Z |
| 2012 | 200 | 2026-10-05T09:02:29Z | 19,322,039 | `447b9078…b1cc6278` | 2025-04-30T06:33:24Z |
| 2013 | 200 | 2026-10-05T09:02:32Z | 19,521,610 | `f454605a…a780d00` | 2024-08-25T12:30:13Z |
| 2014 | 200 | 2026-10-05T09:02:34Z | 19,360,792 | `54c01408…e2fb4f7` | 2024-08-25T12:30:16Z |
| 2015 | 200 | 2026-10-05T09:02:36Z | 19,545,842 | `01b5ae7d…fda7ed9` | 2025-04-30T06:33:27Z |
| 2016 | 200 | 2026-10-05T09:02:39Z | 19,344,382 | `95eba04e…4a45f54a3b` | 2025-04-30T06:34:29Z |
| 2017 | 200 | 2026-10-05T09:02:41Z | 19,050,401 | `84eacd96…b4d3710` | 2025-04-30T06:41:25Z |

(Full sha256 values in `DOWNLOAD_MANIFEST.json` / `provenance/pbp_download_log.tsv`; the
truncated forms above are display-only.)

Release markers:

- Release `pbp` updated_at **2026-10-05T05:28:24Z** (GitHub API, cached) — driven solely by
  the in-season `play_by_play_2026.parquet` re-cut (asset updated_at 2026-10-05T05:28:23Z).
  **None of the 2000–2017 assets was touched today**; the newest completed-season asset
  update is 2026-08-13 (2001, 2002), the oldest 2024-08-25 (2013, 2014).
- Release `timestamp.json`: `{"last_updated":"2026-10-05 01:28:21 EDT"}` =
  2026-10-05T05:28:21Z, sha256 `7ad032c1b829f7220c5578c07ae55b28046618d7e6cff2850f3f87fb575aca87`.

Spot re-download determinism (1 file, season 2011): re-fetched 2026-10-05T09:02:59Z HTTP 200 →
sha256 `c54753b8137b88dab260489b1462cbf1309c3d11741eb8d10e5f1b0a9b8795b1`, 19,117,830 bytes —
**byte-identical** to the first download. Record:
`~/.my-quantitative-data/nfl-ng-scored-v1/provenance/pbp_spot_recheck_2011.txt`.

GitHub API budget: exactly **2** unauthenticated calls (releases/tags/pbp,
releases/tags/schedules), both cached to `provenance/` and not re-called.

Attribution (verbatim, also in `raw_pbp_2000_2017/ATTRIBUTION.md`):
> Data: nflverse/nflverse-data releases (CC BY 4.0), https://github.com/nflverse/nflverse-data

## 2. Fresh schedules snapshot (2026 recount input)

- `https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv`
  (exact URL the predecessor used; provenance
  `~/.my-quantitative-data/nfl-ng-prep-v1/raw_schedules_r1_20261005/release_api_schedules.json`,
  `browser_download_url`). Downloaded 2026-10-05T09:03:26Z, HTTP 200, 2,182,513 bytes,
  sha256 **`486d72273c0d9650756176fc016a0852c65ad6f030f443805c20cb35e387a9fc`** —
  **byte-identical to the predecessor r1 snapshot**; the 2026-10-05T05:46:22Z compile
  (timestamp.json `{"last_updated":"2026-10-05 01:46:22 EDT"}`, sha256 `e7710608…`) is still
  the newest release at this lane's download time.
- Held at `~/.my-quantitative-data/nfl-ng-scored-v1/raw_schedules_fresh/` (games.csv +
  timestamp.json). Snapshot mtime 2026-10-05T09:03:27Z (download write time); measured-at
  time for the recount: 2026-10-05T09:06:07Z (see SUCCESSOR_DATA_AUDIT.md).
- 2018 pbp (`play_by_play_2018.parquet`, present in the release, asset updated_at
  2025-04-30T06:39:20Z) was **not** downloaded: C3 priors for TRAIN seasons 2000–2018
  require prior-season pbp 2000–2017 only. If a successor needs it, it is at the same
  release URL with the API metadata cached in `provenance/release_api_pbp.json`.

## 3. File inventory written by this lane

```
~/.my-quantitative-data/nfl-ng-scored-v1/
  raw_pbp_2000_2017/play_by_play_2000..2017.parquet (18 files)
  raw_pbp_2000_2017/timestamp.json, ATTRIBUTION.md
  raw_schedules_fresh/games.csv, timestamp.json
  rights/nflverse-data_LICENSE.md
  provenance/{pbp_download_log.tsv, pbp_spot_recheck_2011.txt, release_api_pbp.json,
              release_api_schedules.json, release_api_*.json.meta, audit_coverage.py,
              audit_measures.json, pbp_blanks_playtype_2000_2017.json, download_pbp.sh}
```

No existing bytes anywhere were overwritten or deleted; no git commands; nothing committed.
