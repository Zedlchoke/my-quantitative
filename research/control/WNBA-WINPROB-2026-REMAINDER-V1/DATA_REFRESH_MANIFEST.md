# DATA_REFRESH_MANIFEST — Lane W26, cycle WNBA-WINPROB-2026-REMAINDER-V1

PROSPECTIVE PREP ARTIFACT — NOT OOS EVIDENCE · $0 / NO AUTH · APPEND-ONLY
(never overwrites any frozen snapshot; new lineage dir
`~/.my-quantitative-data/wnba-2026-remainder-v1/refresh_20261007/`;
sha256 manifest sidecar: `SHA256_MANIFEST.txt` in this control dir)

- Refresh instant: **2026-10-07T06:44Z** (file mtimes; pull ran 06:44:02–06:44:03Z).
- Puller: `curl` (public release assets, no authentication, no account, $0).
- Heavy lock checked before any long job: `researchctl.py locks inspect` →
  `FREE_PROVEN` (2026-10-07, pre-pull).

## Store

- SportsDataverse release store (the frozen corpus lineage),
  https://github.com/sportsdataverse/sportsdataverse-data — public release
  assets, no authentication; upstream statistics scraped by SportsDataverse
  (not by us) from the ESPN WNBA API and stats.wnba.com; data CC BY 4.0 +
  MIT code; internal research + attribution only.

## Files (URL + tag + retrieved_at + bytes + sha256)

All bytes are **byte-identical to the 2026-10-06 precedent lane-A refresh**
(cycle WNBA-WINPROB-PROSPECTIVE-PREP-V1, `lanes/A_DATA/DATA_REFRESH_PROVENANCE.md`)
— the release store has not updated between the two pulls, so this refresh
re-proves the same snapshot state; the W26 **pinned schedule snapshot** is
`wnba_schedule_2026.csv` below.

| file | URL | tag | retrieved_at (UTC) | bytes | sha256 |
|---|---|---|---|---|---|
| wnba_schedule_2026.csv | github.com/sportsdataverse/sportsdataverse-data/releases/download/espn_wnba_schedules/wnba_schedule_2026.csv | espn_wnba_schedules | 2026-10-07T06:44:02Z | 2,528,172 | `0ed97fafa4392a38f2467e5a588b0a8713ece835ec7cb4fb96a48f8761d05f26` |
| team_box_2026.csv | github.com/.../releases/download/espn_wnba_team_boxscores/team_box_2026.csv | espn_wnba_team_boxscores | 2026-10-07T06:44:03Z | 302,488 | `0218105afd2374a0187317f4b23025764d8b63501ac7b1f32479e44d67a9aba2` |
| timestamp.txt | github.com/.../releases/download/espn_wnba_schedules/timestamp.txt | espn_wnba_schedules | 2026-10-07T06:44:02Z | 24 | `6c383d4635495fc292870210b4b002137f24fb26d165d08b6cb8a013259ff9b8` |
| timestamp.json | github.com/.../releases/download/espn_wnba_schedules/timestamp.json | espn_wnba_schedules | 2026-10-07T06:44:02Z | 43 | `3f9cb7c33a805755ffb9f7a4381258eba5f7d6c75225d1713bf4279f198878cb` |
| package_function.txt | github.com/.../releases/download/espn_wnba_schedules/package_function.txt | espn_wnba_schedules | 2026-10-07T06:44:02Z | 29 | `3653be1c98884f9b4f044b0dca24ff20612adc906c5930264cced16ee9975030` |
| release_store_README.md | raw.githubusercontent.com/sportsdataverse/sportsdataverse-data/main/README.md | (main) | 2026-10-07T06:44:02Z | 292,938 | `ab5be8c4c7a303883f6e8eea134b7737ff06eab884b8b6303e18d618ca4d9df9` |
| espn_wnba_schedules_tag_meta.json | api.github.com release tag metadata (local capture) | espn_wnba_schedules | 2026-10-07T06:44Z | text | n/a (metadata capture) |
| espn_wnba_team_boxscores_tag_meta.json | api.github.com release tag metadata (local capture) | espn_wnba_team_boxscores | 2026-10-07T06:44Z | text | n/a (metadata capture) |

- Asset timestamps from tag metadata: `wnba_schedule_2026.csv` asset updated
  2026-10-06T11:09:26Z; `team_box_2026.csv` asset updated 2026-10-06T11:08:36Z
  (store self-refresh minutes before the precedent lane's 10-06 pull; **no
  newer asset version exists as of this pull**).
- `timestamp.txt` content: `2026-10-06 07:09:39 EDT`; `package_function.txt`:
  `wehoop::load_wnba_schedule()`.

## History absorption (completed 2026 playoff games)

Refreshed `wnba_schedule_2026.csv` = **360 rows: 345 `post` (state), 15 `pre`**.

- All 345 completed 2026 games carry scores (0 missing `home_score` /
  `away_score`) and are **HISTORY ONLY — stream/warm-up material, never scored
  rows**. This absorbs the completed postseason through Game 1 of both
  semifinals (incl. `401918295` 2026-10-04T18:00Z ATL 92–82 NY and
  `401918296` 2026-10-04T20:00Z GS 71–60 LV, first absorbed by the 10-06
  precedent refresh; no additional completion since — the next games tip
  2026-10-07T23:30Z, i.e. after this pull).
- The 15 remaining `pre` rows are the prospective window (census in
  `FREEZE_PACKET.md` §5): 8 semifinal-series rows + 7 Finals placeholders
  (teams TBD in the snapshot).

## Rights re-verification (fail-closed)

| artifact | measured sha256 | pin | verdict |
|---|---|---|---|
| `~/.my-quantitative-data/wnba-v1/raw/ATTRIBUTION.md` | `1068e5c7aae614347550266da94d067f38c7c2cc9b569e685cfed3aced301f5a` | `1068e5c7…` (dispatch) | **== pin** |
| feature table `wnba_player_features_2002_2026.parquet` (826,415 B) | `ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf` | `ceaf10ba…` | **== pin** |
| crosswalk `wnba_schedule_crosswalk_2026.csv` | `e4115f04d45d3bc7fb9b43eca9c5babd26185e2ecf51e65bc3b66bf02aa6eea6` | `e4115f04…` | **== pin** |
| frozen engine `arms.py` | `82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3` | ERRATUM_R1 | **== pin** |
| frozen engine `harness.py` | `b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e` | ERRATUM_R1 | **== pin** |

Release README carries the CC BY 4.0 license badge; code LICENSE = MIT; the
pull itself re-proves no-auth public assets. Any pin mismatch was defined as
BLOCKED_TOOLING (stop and report) — **no mismatch occurred**.

## Boundary compliance

0 scored cells; 0 real forecast rows; no real-game probability computed
anywhere; no frozen byte modified (closed-cycle corpus read-only; new bytes
only under `~/.my-quantitative-data/wnba-2026-remainder-v1/`).
