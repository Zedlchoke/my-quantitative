# VERDICT TABLE — Lane A_NBA_FEAT (WINPROB-PLAYERFEAT-PREP-V1)

Measured 2026-10-05 from bytes. Nothing inferred: every PASS below has a
number + artifact path behind it; anything not measured is NOT_RUN.

| # | check | verdict | evidence (number / artifact) |
|---|---|---|---|
| 1 | 8 missing seasons downloaded, HTTP 200, full provenance (url, status, utc, bytes, sha256, asset updated_at) | **PASS** | all sizes == GitHub API asset metadata exactly; `~/.my-quantitative-data/playerfeat-prep-v1/nba/download_manifest.{json,md}` |
| 2 | GitHub API discipline (≤2 unauthenticated calls, response cached) | **PASS** | 1 call 2026-10-05; cache `provenance/github_api_release_espn_nba_player_boxscores.json` |
| 3 | Re-download determinism (1 file spot check) | **PASS** | `player_box_2023.csv` re-fetch byte-identical (sha256 `1b797107…a589493`); `provenance/redownload_check_player_box_2023.txt` |
| 4 | ATTRIBUTION.md conventions extended from predecessor | **PASS** | `~/.my-quantitative-data/playerfeat-prep-v1/nba/ATTRIBUTION.md` (predecessor file untouched) |
| 5 | Coverage audit 2016–2026 (11 seasons) vs schedule corpus | **PASS** | played-join 1.0000 ×8, 0.9992 ×3 (3 named box-less FINAL games); 0 orphans; 0 dups; 33 NULL-athlete rows (2026); `COVERAGE_AUDIT.md`, `provenance/coverage_audit_11seasons.{txt,json}` |
| 6 | Schema drift vs predecessor 2026 schema | **PASS** (zero drift) | 57 cols identical in all 11 seasons |
| 7 | Season label convention (ending-year) verified every new season | **PASS** | 11/11 label checks true (game-date ranges measured) |
| 8 | Tip timezone semantics verified from bytes | **PASS** | `game_date_time` == `start_date` (UTC) on 14,254/14,254 rows; 0 parse failures |
| 9 | Degeneracy law: measure before freeze; substitute non-degenerate form | **PASS** | raw mass level degenerate (≈95% in [239,266] = 240+25k±noise; std 6.3–18.4 = OT mix); substituted `a_top5_share_k5` + `a_load_top5_k5` (std 0.040/0.028); OT-normalized mass and HHI measured and documented (`FEATURE_SPEC.md` §3, `provenance/degeneracy_measurements.txt`) |
| 10 | As-of law: strict tip inequality, no same-game inputs | **PASS** | builder emits before committing target; selftest leak checks 8/8 rows strict-`<` + target absent |
| 11 | Predecessor MIL worked example reproduced by this build | **PASS** | prior-5 = {401267680, 401267700, 401267715, 401307356, 401307372}; mean mass 239.4; tip 2021-03-15T23:00Z |
| 12 | Independent recomputation of scalars (separate code path) | **PASS** | 8/8 sample rows match to <1e-12 |
| 13 | Missing-data rules (≥5 team-games neutral gate, identity-less exclusion, season_type=5 prior exclusion) | **PASS** | 1,688 neutral rows, 0/1 assert both ways; 33 NULL-athlete excluded; play-in never in priors |
| 14 | Trade guard (Group C) | **PASS** | synthetic logic tests (count/expiry/streak) + real Mills 2025 case measured (no fabricated absence; stale scaffold row documented) |
| 15 | No outcome columns; no scored metric anywhere | **PASS** | column whitelist assert; grep discipline (feature-construction only); row keys game/team/tip only |
| 16 | Determinism (fixed ordering, no timestamps in data, byte-stable csv.gz) | **PASS** | sort (season, tip_utc, game_id, team_id); gzip mtime=0; outputs sha-pinned |
| 17 | Feature table built (parquet + csv.gz outside git) | **PASS** | 28,374 rows = 2 × 14,187 played games; `features/nba_player_features_2016_2026.{parquet,csv.gz}`; `FEATURE_TABLE_MANIFEST.{md,json}` |
| 18 | `build_features.py --selftest` green, non-zero exit on failure | **PASS** | 42/42 checks PASS, exit 0; `provenance/selftest_checks.txt` |
| 19 | Compute budget ≤ ~30 min | **PASS** | full build+write+selftest ≈ 67 s wall |
| 20 | Rights on new downloads | **PASS (with standing caveat)** | store MIT + hoopR-nba-data CC BY 4.0 (pinned in ATTRIBUTION.md); underlying ESPN/NBA rights remain UNRESOLVED — internal research only, fail-closed (carried law, not a new stop) |
| 21 | Target-game availability (starter/DNP/injury) as features | **NOT_RUN_PIT** (by law; not used) | PIT_AUDIT §1 |
| 22 | Any scored/win-prob/calibration metric on outcomes | **NOT_RUN (forbidden this cycle)** | plan boundaries |
| 23 | Predecessor-dir or other-lane writes | **PASS** (none) | writes only under `lanes/A_NBA_FEAT/` + `~/.my-quantitative-data/playerfeat-prep-v1/` |

**Lane verdict: FEATURES_BUILT** — downloads verified, coverage audited,
frozen feature table + selftest green; no stop condition triggered. Handoff:
`lanes/DISPATCH/handoff_A_NBA_FEAT.json`.
