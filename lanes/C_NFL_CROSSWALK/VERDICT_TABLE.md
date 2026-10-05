# VERDICT TABLE — Lane C_NFL_CROSSWALK · WINPROB-PLAYERFEAT-PREP-V1

Measured 2026-10-05, all from bytes/commands this session; nothing inferred.
Interpreter: /Users/hoangminhlong/my-quantitative/.venv/bin/python (Python 3.12.14,
pandas 3.0.5, pyarrow 25.0.1). Cost $0. No scored computation; calibration/forecasting
vocabulary only.

## Checks × verdict

| # | check | verdict | evidence |
|---|---|---|---|
| 1 | Rights gate: live LICENSE.md re-fetch byte-identical to pin | **PASS** | HTTP 200 2026-10-05T09:05:49Z, sha256 `2a82ac9bbc3e3ee0…b9111` == pinned (byte-identical); `logs/license_fetch_log.json`; no BLOCKED_DATA_RIGHTS |
| 2 | Download players.parquet with full provenance | **PASS** | HTTP 200 2026-10-05T09:01:53Z, 3,389,574 B, sha256 `485b1980…304885e2`; asset size/updated_at cross-checked via 1 cached GitHub API call; DOWNLOAD_MANIFEST.md (+json) |
| 3 | Release timestamp marker file | **PASS** | timestamp.json + timestamp.txt both 2026-10-04T15:06:29Z; agrees with API asset updated_at 2026-10-04T15:06:30Z |
| 4 | Re-download determinism | **PASS** | second pull 2026-10-05T09:01:59Z byte-identical (cmp True, same sha256) |
| 5 | Predecessor input integrity (5 files re-hashed) | **PASS** | all match pinned sha256s (see DOWNLOAD_MANIFEST.md §Predecessor) |
| 6 | Schema audit | **PASS** | 24,844×39; gsis_id PK (0 null, unique); pfr_id 22,679 unique (8.71% null); latest_team 32/32 no nulls; 13 statuses; 25 positions; SCHEMA_AUDIT.md |
| 7 | JOIN weekly stats 2024/2025/2026 (GSIS) | **PASS** | match rate **1.000000 / 1.000000 / 1.000000** (2,001/2,024/1,512 distinct); 0 dups; 0 unmatched; null-id rows = known 1/week placeholder artifact (22/22/4) |
| 8 | JOIN snap_counts 2025/2026 (PFR) | **PASS (residual named)** | match rate **0.997259 / 0.998213**; unmatched = 6/3 fringe ids (rows 54/8), same ids recur 2025→2026 = deterministic crosswalk pfr-null cohort; 0 dups |
| 9 | Round-trip 2026 stats→crosswalk→snaps | **PASS (residual named)** | 1,475/1,512 = **97.55%** of 2026 weekly-stats players joinable into snap_counts_2026 (97.81% of pfr-holders); 4 pfr-null players block the join; 33 pfr-holders absent consistent with snap-file 49/63-game lag |
| 10 | 2026 freshness | **PASS** | build T-1 day; 32/32 teams; ACT∧last_season-2026 = 1,731 (52–55/team); top-8 QBs by 2026 pass yds all present with both ids |
| 11 | Target-game injury/active/DNP status | **NOT_RUN_PIT (restated, not re-litigated)** | law holds regardless of this lane: no per-record publish timestamps anywhere in these sources; predecessor PIT_AUDIT F5 carried verbatim |
| 12 | snap_counts 2026 in-season lag ≤1 week | **RESTATED (unchanged)** | snap build 2026-10-02 vs stats 2026-10-05 (predecessor measurement); this lane adds: 33 pfr-holding stats-players absent from snap_2026 consistent with that lag; weekly cadence OK, intra-week not |
| 13 | Release-cadence (not row-level) availability | **RESTATED (unchanged)** | only release-level timestamp.json exists; frozen sha256s are the evidence anchors for both lanes' snapshots |
| 14 | Scored computation / win-prob metrics | **NOT_RUN (by law)** | 0 scored; join/coverage/freshness tests only |

## HOLD recommendation: **LIFT** the predecessor's crosswalk blocker

The predecessor HOLD named 4 blockers. Blocker (2) — "players.parquet GSIS↔PFR crosswalk
not downloaded" — is now **cleared by measurement**: the crosswalk is downloaded, hashed,
rights-clean, and joins at 100% (GSIS side, all seasons) and 99.73–99.82% (PFR side), with
a **97.55% measured round-trip** for 2026 player-level stats+snaps. The residual is small,
named, and stable (8 fringe ids recurring across seasons + 4 named 2026 players with
crosswalk pfr NULL: Cody White, Alec Anderson, Basil Okoye, Peter Woods).

Residual items carried (explicit, none blocks feature-PREP at weekly cadence):

1. **pfr-null cohort** (2,165 crosswalk rows; 8 fringe snap ids unmatched; 4 named 2026
   stats-players unjoinable to snaps) — handling rule for the future feature lane: drop
   from snap-join features, never impute; document per-feature exclusion counts.
2. **Target-game injury/active/DNP/starter status = NOT_RUN_PIT** — carried law, unchanged,
   no per-record publish timestamps in any of these sources.
3. **snap_counts 2026 lag ≤1 week** (build 2026-10-02 vs stats 2026-10-05) — weekly-cadence
   OK; snap-dependent features must tolerate ≤1-week staleness and the 49/63-game coverage
   at predecessor pull.
4. **Release-cadence availability (not row-level)** — frozen sha256s
   (`players` 485b1980…304885e2 @2026-10-04T15:06:29Z; predecessor stats/snap hashes) are
   the evidence anchors; any re-pull must re-hash and re-audit.
5. Underlying league data rights for publication/commercial use remain UNVERIFIED
   (internal research only, fail-closed) — carried from lane R.

Scope note: this lane authorizes NO scored work; LIFT here is the data-lane recommendation
only. Per plan, the NFL feature lane additionally remains gated on lane D's independent
CONFIRM/DISCONFIRM verdict on this recommendation.

## Cost

Actual: **$0** (public URLs only; 1 unauthenticated GitHub API call, cached). No accounts, no keys.
