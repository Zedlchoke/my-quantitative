# DOWNLOAD MANIFEST — Lane C_NFL_CROSSWALK · WINPROB-PLAYERFEAT-PREP-V1

All downloads 2026-10-05, unauthenticated public URLs only, HTTP 200. Cost: **$0**.
Data dir (outside git): `~/.my-quantitative-data/playerfeat-prep-v1/nfl/raw_players/`
Machine-readable authority: `download_manifest_C_NFL_CROSSWALK.json` (this lane).
Evidence logs: `logs/release_api_players_tag.json` (the 1 GitHub API call, cached),
`logs/license_fetch_log.json`, `rights_nflverse-data_LICENSE_live.md` (byte copy).

## Files

| # | file (rel to data dir) | release tag | URL | HTTP | downloaded UTC | bytes | sha256 |
|---|---|---|---|---|---|---|---|
| 1 | players.parquet | players | https://github.com/nflverse/nflverse-data/releases/download/players/players.parquet | 200 | 2026-10-05T09:01:53Z | 3,389,574 | 485b198070f831ed3a9098b991cd4b5dd97407e23a08fe31629d18dc304885e2 |
| 2 | timestamp.json | players | https://github.com/nflverse/nflverse-data/releases/download/players/timestamp.json | 200 | 2026-10-05T09:01:53Z | 43 | 23955f4e32cd7899d6c50bb478438161b89d974058eeee81fef1d1c33042f4b4 |
| 3 | timestamp.txt | players | https://github.com/nflverse/nflverse-data/releases/download/players/timestamp.txt | 200 | 2026-10-05T09:01:54Z | 24 | 3f7f9207bf59ecdf8a9a6720cee5205961055eddce2a68769d2336791231339b |

- Release last-updated markers (both files agree): `{"last_updated":"2026-10-04 11:06:29 EDT"}`
  = **2026-10-04T15:06:29Z** — the release build taken by this lane.
- GitHub API cross-check (1 unauthenticated call, cached at
  `logs/release_api_players_tag.json`): asset `players.parquet` declared `size` 3,389,574 B =
  actual bytes; asset `updated_at` **2026-10-04T15:06:30Z** (consistent with the timestamp
  markers); tag `players` published_at 2022-06-19T05:36:22Z (rolling re-cut release).
- First attempt at 09:01:36Z without redirect-following returned HTTP 302 with 0 bytes
  (recorded, discarded); retried with `-L`, HTTP 200. Not a machinery failure — evidence in
  shell log; the recorded downloads are the 200 responses above.

## Rights gate (run BEFORE data download)

- Live refetch `https://raw.githubusercontent.com/nflverse/nflverse-data/HEAD/LICENSE.md`
  at **2026-10-05T09:05:49Z**, HTTP 200, 18,651 B,
  sha256 `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111`
  = pinned value, **byte-identical** (cmp of the lane copy; predecessor C_NFL live fetch
  agrees). No BLOCKED_DATA_RIGHTS. CC BY 4.0.
- Underlying league data rights remain UNVERIFIED for publication/commercial use (carried
  law; internal research only, fail-closed).

## Re-download determinism (determinism spot check)

`players.parquet` re-pulled at 2026-10-05T09:01:59Z (6 s after first pull):

- first: 3,389,574 B, sha256 `485b198070f831ed…304885e2`
- second: 3,389,574 B, sha256 `485b198070f831ed…304885e2` — **BYTE-IDENTICAL: True**

Caution: `players` is a rolling re-cut release (asset rewritten at each build; latest build
2026-10-04T15:06:29Z). The sha256 above is this cycle's frozen evidence anchor; any future
re-pull in-season may differ by design (same caveat as predecessor's `stats_player` law).

## Predecessor input integrity (spot re-hash at lane start)

All 5 predecessor files re-hashed 2026-10-05 ≈08:50Z — **all match** the pinned manifest:

| file | sha256 match |
|---|---|
| raw_stats_player/stats_player_week_2024.parquet | `847569d1…55c1` ✓ |
| raw_stats_player/stats_player_week_2025.parquet | `2a461bec…ff10` ✓ |
| raw_stats_player/stats_player_week_2026.parquet | `49bc644e…6179` ✓ |
| raw_snap_counts/snap_counts_2025.parquet | `47220218…ce20` ✓ |
| raw_snap_counts/snap_counts_2026.parquet | `fae0627d…8273` ✓ |

## Budget

GitHub REST calls: **1** (cached). Public URLs only, no accounts, no keys. Actual cost **$0**.
