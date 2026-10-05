# GAMES_2026_CLASSIFICATION — Lane A · DATA (nflng-a-data), cycle NFL-WINPROB-NG-PREP-V1

Source file: `~/.my-quantitative-data/nfl-ng-prep-v1/raw_schedules_20261005/games.csv`
(freshest 2026 schedule/results available — nflverse-data `schedules` release,
asset updated_at 2026-10-05T03:16:30Z, release timestamp.json
"2026-10-04 23:16:28 EDT" = 2026-10-05T03:16:28Z; pulled 2026-10-05T03:23:53Z,
sha256 `338d7fe01d803916b2d5ed31fb4e5405914a8030ae2296ed449e27471d5b594f`).
Kickoff UTC derived as `gameday`+`gametime` in `America/New_York` → UTC
(documented ET semantics; DATA_AUDIT_NFL_NG.md §4). All 272 rows parse.

CYCLE PROSPECTIVE EPOCH (controller-measured bootstrap commit time, from the
dispatch packet): **2026-10-05T03:13:51Z**.

## Measured 2026 counts

| quantity | count |
|---|---|
| Total 2026 games scheduled in file | **272** (all `REG`, weeks 1–18; playoff games not yet scheduled rows) |
| Games with final scores in the fresh file (played, as of pull) | **62** |
| Games with kickoff_utc ≤ epoch | **63** (= 62 finished + 1 in flight at epoch) |
| Games with kickoff_utc > epoch | **209** (0 of them scored) |
| Not-yet-kicked-off as of audit time (~03:30Z) | 209 |

Earliest FUTURE kickoff UTC: **2026-10-06T00:15:00Z** — game `2026_04_ATL_NO`
(ATL @ NO, Monday night). Next: 2026-10-09T00:15Z `2026_05_TB_DAL`, then
2026-10-11T13:30Z `2026_05_PHI_JAX` (London) and 17:00Z games.

Boundary row (explicitly classified): `2026_04_DET_CAR` (DET @ CAR, SNF Oct 4)
kicked off **2026-10-05T00:20:00Z — BEFORE the epoch** but had no final score at
the release compile (03:16:28Z) nor at audit time (in progress). It is a
played-before-epoch game for prospective purposes; it additionally cannot be
scored from this file yet. Nothing about it may be presented as a forecast.

## Prospective law statement (verbatim intent)

**Every 2026 game already played before the epoch 2026-10-05T03:13:51Z is
NOT_RUN for prospective scoring and must never be presented as a pre-game
forecast.** Count of 2026 games already played before the epoch: **63**
(62 with final scores + 1 in flight at the epoch instant, kickoff 00:20Z <
03:13:51Z). The 209 not-yet-kicked-off games are the only 2026 games eligible
for a genuinely prospective append-only prediction ledger, and only if recorded
strictly before their kickoff UTC at a successor scored cycle's own gate.

Sanity checks measured: all 62 scored 2026 games have kickoff_utc ≤ epoch (no
"future" game carries a score); no already-scored row changed between the
2026-10-04 archive copy and this fresh copy; the archive copy held 49 finished
2026 games → the release added 13 (Sunday week-4 finals) between the two
compiles, consistent with post-game compilation.

Delta vs archive copy (both sha256-pinned in DOWNLOAD_MANIFEST.md):
games.csv `f1e8fe78…` (2026-10-04T12:16:32Z compile) → `338d7fe0…`
(2026-10-05T03:16:28Z compile).
