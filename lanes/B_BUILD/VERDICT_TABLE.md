# VERDICT_TABLE — B_BUILD · NFL-PLAYERFEAT-PREP-V1 · 2026-10-05

Every check measured by this lane's own code (`build_features.py --selftest`, machine copy
`selftest_results.json` beside the parquet and in this lane dir).

## Build-gate checks

| # | check | evidence | verdict |
|---|---|---|---|
| G1 | Input integrity: 6 input sha256s vs predecessor manifests (5 stats/snap + crosswalk) | re-hashed at build start, 6/6 match (pins in FEATURE_SPEC §0 / MANIFEST) | **PASS** |
| G2 | Predecessor manifest lookup | C_NFL DOWNLOAD_MANIFEST + C_NFL_CROSSWALK DOWNLOAD_MANIFEST cited in spec/manifest | **PASS** |
| G3 | Rights posture | inherited: nflverse-data CC BY 4.0 pinned (predecessor live re-fetch byte-identical); league rights unverified, internal-research-only, fail-closed | **PASS (carried)** |
| G4 | Row universe law | 633 stats games × 2 sides = 1,266 rows; 0 orphan gids; 0 dup (game_id, side); 209 future 2026 games → no rows, disclosed | **PASS** |
| G5 | No outcome columns | 44-col whitelist; banned-vocabulary scan S8 = 0 hits; games.csv score/result fields never read | **PASS** |
| G6 | No scored computation / betting vocabulary / win-prob on outcomes | builder contains only aggregations; grep-clean vocabulary per spec §9 | **PASS** |
| G7 | NOT_RUN_PIT law (target-game status absent) | no target-game status column or value anywhere; G3 = lagged prior-game proxy only (PIT_AUDIT §4) | **PASS** |
| G8 | Write boundaries | only `lanes/B_BUILD/**` + `~/.my-quantitative-data/nfl-playerfeat-prep-v1/**`; no git; predecessor dirs read-only; NFL-WINPROB-NG-SCORED-V1 untouched | **PASS** |
| G9 | Determinism | double-run byte-identical: in-process rebuild (S6) + fresh-process rerun, sha `f1bc6b4a8c7f5c36457aaa393666ca90cc446cc6f934c3ea55f739b5de7c4f57` | **PASS** |
| G10 | Compute budget | ~2 min wall per selftest run (≪ 30 min stop condition) | **PASS** |

## Selftest checks (8/8 PASS)

| # | check | method | verdict |
|---|---|---|---|
| S1 | Kickoff strict-inequality as-of, full table | recount of every row's strictly-prior same-season support: 0/1,266 mismatches | **PASS** |
| S2 | KC 2024 worked example (predecessor PIT basis) | 2024_11_KC_BUF KC prior-3 = 819 yds / 6 TD / 1 INT / 124 att, n_prior 9 (wk6 bye) — exact from bytes | **PASS** |
| S3 | Target-game absence | one-at-a-time perturbation of 4 fixture games' own stats rows → their rows byte-identical (2024_11_KC_BUF, 2024_07_KC_SF, 2026_04_PIT_CLE, 2026_03_ATL_GB) | **PASS** |
| S4 | Crosswalk canary (pfr-null) | WhitCo05 / Cody White (gsis 00-0035891, crosswalk pfr NULL): 3 snap-2026 rows excluded by rule; LV 2026 rows flagged `g3_pfr_null_excluded` | **PASS** |
| S5 | Bye-week fixture | KC 2024_07_KC_SF: window wks 5/4/3, qb_yds_k3 = 793.0 exact, rest_days 12.8403, no synthetic bye row | **PASS** |
| S6 | Determinism double-run | fresh rebuild → identical parquet sha | **PASS** |
| S7 | Placeholder exclusion | 48 NaN-player rows (1/week: 22+22+4) excluded before aggregation | **PASS** |
| S8 | Outcome-column ban | 0 banned tokens in 44-col schema | **PASS** |

## Inherited / residual (NOT_RUN carried, by law)

| item | status |
|---|---|
| Target-game injury/active/DNP/starter status | **NOT_RUN_PIT** (no pre-game publish timestamps in any source; not bypassed) |
| snap_counts 2026 in-season release lag ≤1 week (build 2026-10-02 vs stats 2026-10-05) | carried, release-level (frozen sha256s are evidence anchors) |
| Release-cadence (not row-level) availability of weekly files | carried |
| G3 = noisy lagged proxy (in-game-injury conflation by design) | documented, spec §6 / PIT_AUDIT §4 |
| QB-identity continuity (snap-based lead-QB share) | out of scope v1 — snap corpus has no 2024 coverage; disclosed, not silently omitted |

## Lane verdict

**BUILD_COMPLETE_PASS** — frozen table shipped at
`~/.my-quantitative-data/nfl-playerfeat-prep-v1/features/nfl_playerfeat_table_v1.parquet`
(1,266 × 44, sha `f1bc6b4a…7c4f57`), spec-first frozen, artifacts uncommitted-by-design
(controller commits per plan §Boundaries).
