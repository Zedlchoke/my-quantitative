# SUCCESSOR_DATA_AUDIT — Lane A_DATA, cycle NFL-WINPROB-NG-SCORED-V1

Measured 2026-10-05, audit run 09:06:07Z. Snapshot: `~/.my-quantitative-data/nfl-ng-scored-v1/raw_schedules_fresh/games.csv`
(nflverse-data `schedules` release compile 2026-10-05T05:46:22Z, sha256
`486d72273c0d9650756176fc016a0852c65ad6f030f443805c20cb35e387a9fc`, 2,182,513 bytes —
byte-identical to the predecessor r1 snapshot `raw_schedules_r1_20261005/`; snapshot mtime
2026-10-05T09:03:27Z = download write time, disclosed against the 09:06:07Z measured-at
instant). Kickoff-UTC derivation unchanged: `gameday`+`gametime` in `America/New_York`
(zoneinfo) → UTC. Coverage counting and PIT/audit work only — no win-prob metric, model
score, or outcome evaluation computed anywhere in this lane.

## 1. Freeze facts (all re-measured from fresh bytes — nothing copied)

**TRAIN season list = complete seasons 2000–2018.** Re-measured: 2000 = 259 rows, 2001 =
259, 2002–2018 = 267 each (5,057 rows total, **0 rows missing final scores**). 2022 carries
**271** REG rows (canceled BUF@CIN omitted upstream — consumers use row counts, never
nominal 256/272). 9 tie rows 2000–2018 (context only; predecessor tie law compatible).

**1999 exclusion re-measured (not inherited prose):** 1999 = 259 rows, `gametime` empty on
**259/259** (100% missing) and kickoff unparseable on 259/259 → not kickoff-capable →
excluded. 2000–2018: `gametime` empty on **0 rows in every season**.

**Kickoff fallback X = NOT ACTIVATED.** `gametime` is 100% present (0 empty, 0 unparseable)
in **every season 2000–2026** on this snapshot (incl. all 272 rows of 2026). The fallback
trigger condition ("gametime <100% present 2000+") does not hold; no fallback needed.

**Neutral-site flag = games.csv `location` column.** Values measured: only {`Home`,
`Neutral`} across all seasons (7,446 Home / 102 Neutral total 2000–2026). Window 2000–2018:
**5,006 Home / 51 Neutral** (1–2 Neutral early years, 3–6 from 2013). HCA=0 law applies on
every `Neutral` row (frozen predecessor convention; flag is directly usable).

**Season-boundary margins (C3 input-determination margin).** Last kickoff of season s−1
(incl. Super Bowl) precedes first kickoff of season s by **213.0–223.7 days (~7 months)**
for every boundary 2001–2017. The 2000 boundary is undefined (1999 has no parseable
kickoffs) — immaterial: the first TRAIN season 2000 receives no C3 prior (per C3 spec,
"first season in data: no term").

## 2. Fresh 2026 recount (at audit time)

Measured now_utc = **2026-10-05T09:06:07Z** on the snapshot above (compile 05:46:22Z —
the newest schedules release at download time; no newer compile existed between the
predecessor r1 pull and this lane's pull):

| quantity | count |
|---|---|
| 2026 games scheduled | **272** (all `REG`, weeks 1–18; no playoff rows yet) |
| played — final scores present | **63** |
| started-or-finished (kickoff ≤ 09:06:07Z) | 63 (identical set — started-without-score: 0) |
| future (kickoff > 09:06:07Z) | **209** |
| future rows already carrying scores (law check) | **0** — holds |
| earliest future kickoff UTC | **2026-10-06T00:15:00Z — `2026_04_ATL_NO`** (measured, matches predecessor expectation) |
| next future kickoffs | 2026-10-09T00:15Z `2026_05_TB_DAL`; 2026-10-11T13:30Z `2026_05_PHI_JAX` (London); 2026-10-11T17:00Z `2026_05_CIN_MIA`, `2026_05_LV_NE` |
| week-5 slate opener | **`2026_05_TB_DAL` 2026-10-09T00:15:00Z — measured actual, matches expected** (15 week-5 games) |

Prospective law restated: the cycle prospective epoch is unchanged
(2026-10-05T03:13:51Z, controller bootstrap time); the 09:06:07Z recount instant is a
measurement instant, not a new epoch. All 63 games kicked off ≤ now are NOT_RUN
prospective forever; no retrospective predictions for any played game, ever. The 209
future games are the only 2026 games eligible for a genuinely prospective append-only
ledger, and only if recorded strictly before kickoff UTC at this cycle's own gate.

## 3. C3 admissibility verdict — **PASS_PIT_SEASON_GRAIN** (offseason-prior role ONLY)

1. **Snapshot story (measured from the release API metadata, cached).** The `pbp` release
   re-cuts the **current** season weekly in-season: the only asset updated at the release's
   2026-10-05T05:28:24Z touch was `play_by_play_2026.parquet` (05:28:23Z). Completed-season
   assets 2000–2017 were last updated 2024-08-25 (2013/2014) … 2026-08-13 (2001/2002) —
   i.e., finalized long after each Super Bowl and stable for months-to-years since
   (evidence also that maintenance retro-cuts of old seasons DO occur arbitrarily later —
   hence the freeze semantics below). Current-season files are therefore never usable
   pre-game for the current week; the offseason-prior role never reads them.
2. **Season-boundary margin (measured).** 213.0–223.7 days (~7 months) between the last
   prior-season kickoff and the first new-season kickoff at every boundary 2001–2017: the
   C3 input set (prior completed season's REG plays) is fully determined months before the
   first prediction that consumes it — kickoff-grain law satisfied with maximal margin.
3. **Coverage (measured, PBP_COVERAGE_AUDIT.md).** pbp 2000–2017 covers the prior-season
   needs of every TRAIN season (priors for 2001–2018): 17/18 seasons join to games.csv
   exactly (0 orphan game_ids); 2000 is 99.2% complete (2 named missing games); `epa`
   populated on 99.37–100.0% of team-attributable rows; ~1,200–1,535 offensive EPA plays
   per lineage-season (~2,400–3,070 off+def); `posteam`/`defteam`/`season_type` present
   and populated; all 372 columns in all 18 files.
4. **Rights (re-verified live).** CC BY 4.0, sha256 = pinned predecessor value; no
   BLOCKED_DATA_RIGHTS.
5. **Restriction (spec-verbatim).** PASS is for the **offseason-prior role only**: season-
   start prior from prior-season completed REG games; NEVER an in-season or within-season
   pbp feature. The snapshot must be frozen and sha-disclosed at registration (all 18
   sha256s already pinned in DOWNLOAD_MANIFEST.json); retro-corrections landing after the
   freeze are out of scope and disclosed. θ=0 remains the designed null reproducing B1*.
6. **Power disclosure (honest).** Coverage starts exactly at the TRAIN window start
   (2000), so no overlap shortening occurs; the pre-registered MDD arithmetic of the
   mechanisms spec applies unchanged. Data-side residuals disclosed: 2 missing 2000 games;
   ~5% blank-posteam rows (dropped from aggregates); 2000 has elevated `play_type` blankness
   (8.8%) — none of these blocks a season-grain EPA aggregate.

Designed-null consequence for Lane T: C3 is **admissible to run** on TRAIN 2000–2018;
if its train-internal gate fails, the disposition remains NOT_RUN_PIT per protocol (that
decision belongs to Lane T's ledger, not this lane).

## 4. Laws held (this lane)

Writes only in `lanes/A_DATA/**` and `~/.my-quantitative-data/nfl-ng-scored-v1/**`; no git
commands, nothing committed; $0 anonymous downloads only; ≤2 unauthenticated GitHub API
calls (used exactly 2, cached to `provenance/`); no scored computation, no win-prob or
calibration metric, no evaluation of 2019–2025 outcomes (archive 2021–2025 pbp untouched);
calibration/forecasting vocabulary only; no existing bytes overwritten or deleted.
