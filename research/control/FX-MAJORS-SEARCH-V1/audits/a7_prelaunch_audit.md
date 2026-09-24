# A7 PRELAUNCH AUDIT — FX-MAJORS-SEARCH-V1

- **Auditor**: A7, independent fresh-context (no prior lane context; all evidence re-measured from bytes and re-runs on 2026-09-24)
- **Scope**: prelaunch gate BEFORE the ONE holdout look per pair (GBPUSD, USDJPY; window 2026-01-01..2026-06-30)
- **Worktree**: `/Users/hoangminhlong/my-quantitative/.worktrees/fx-majors-search-v1/integration` @ branch `orca/fx-majors-search-v1-integration`, HEAD `f87b79ff`
- **measured_utc**: 2026-09-24T02:07:19Z
- **VERDICT: AUTHORIZED** (0 blocking findings; 1 LOW non-blocking housekeeping finding F1)

---

## 1. CHAIN — PASS

Measured from git objects, not messages:

| commit | time (committer, +07:00) | role | evidence |
|---|---|---|---|
| `aa49ed2a` (main) | 07:44:45 | plan on main | plan blob `7067794d5c41…` |
| `15b70310` (branch) | 07:44:46 | plan cherry-pick | same plan blob `7067794d5c41…` — byte-identical to main |
| `19503e51` | 07:55:00 | code freeze | `selection_freeze_fx.json` FIRST appears here (blob `ac801e8c`, unchanged through HEAD); `scripts/engine.py` FIRST appears here (blob `9846803f`) |
| `f87b79ff` | 09:00:28 | outcomes | `candidates_frozen_fx.json` FIRST and ONLY appearance; freeze→outcomes diff contains exactly the 5 outcome files, zero code drift |

- Engine sha256 in `selection_freeze_fx.json` = `14455ca22888b5d853d30ca52e075ce2e70bd182e6c6b0ac1e7c6a936ae156e3`; recomputed over the on-disk file and over `git show 19503e51:…engine.py` — both identical. Engine blob at freeze == HEAD.
- This cycle's engine blob `9846803f` DIFFERS from the EURUSD frozen engine blob `9aad1a60` (=cc868402 shorthand) **by design** (pip parametrization, `run_strategy(..., pip=None)` with `pnl = (exit-entry)·pos·(1/pip)`). Backcompat verified by suite instead (§6).
- Strict order plan < freeze < outcomes holds.

## 2. LEAK GUARDS — PASS

- `fxm_campaign.py` L146: `dev = slice_plane(plane_full, plane_full.ts < int(HOLDOUT_START.timestamp()))` with FAIL_CLOSED assertion (any ts ≥ 2026-01-01 or <20k bars → SystemExit). Independently re-executed during my re-runs: assertion held.
- `fxm_holdout.py` L29: `hold = slice_plane(plane, plane.ts >= int(HOLDOUT_START.timestamp()))` with FAIL_CLOSED (any ts < 2026-01-01 or <1000 bars → SystemExit).
- `outcomes/holdout_check_fx.json` **does not exist**; `holdout_run_count_fx.json` does not exist. `git log --all -- '*holdout_check_fx*' '*holdout_run_count_fx*'` = empty — never committed anywhere.
- Zero occurrences of the string `2026` in either `campaign_dev_*.jsonl` (dev outcomes contain no holdout-period anything). The only `holdout`/`2026` strings in outcomes are the preregistration text in `candidates_frozen_fx.json` (`holdout_SUCCESS_preregistered`, `frozen_utc`) — no metrics.

## 3. DATA — PASS

- Per-pair manifests: 4014 files each, 0 missing (`files` dict, entries carry sha256+bytes). Manifest sha256 on disk: GBPUSD `ed8d26a5…`, USDJPY `043dc073…` — both match the `data_manifest.m1_manifest_sha256` recorded inside each census and the `data_manifest_sha256` on every JSONL record.
- **32 raw files sha-verified** (16 per pair: first 3, last 3, 10 seeded-random) against manifest entries — 32/32 OK, 0 mismatch.
- Census: GBPUSD `verdict=BUILD_PASS`, bars15_valid 131,488, spread_pips p50 0.8; USDJPY `BUILD_PASS`, 131,676 bars, p50 0.5. Gates (midweek share >0.90, nonpos spread <1%, bars >100k) all True.
- Derived `bars1h.parquet` re-read: GBPUSD 30,876 rows (== census), 2021-01-03 22:00Z → 2026-06-30 21:00Z, dev/holdout split 28,095/2,781; USDJPY 31,130 rows (== census), split 28,322/2,808.
- Probe evidence `data_local/probe/probe_pairs_evidence.json`: `ALL_PROBE_PASS`; USDJPY P3_scale PASS (sample last close 150.453) with P4 tick cross-check 120 minutes / 0 mismatches; GBPUSD likewise PASS (1.2689). Scale is **proven, not assumed** — matches plan's probe-gating requirement.

## 4. TRIAL ACCOUNTING — PASS

- `campaign_dev_GBPUSD.jsonl` = 48 records, 48 distinct arm_ids; `campaign_dev_USDJPY.jsonl` = 48 records, 48 distinct arm_ids. Every record: `cycle_id=FX-MAJORS-SEARCH-V1`, `d2=OWNER_WAIVED_EXPLORATORY`, `code_freeze_sha=19503e517d69…` (== freeze commit full hash), pair-correct manifest sha.
- All 48 freeze-registry config digests (12 families × 4) recomputed via `engine.config_digest(fid, cfg)` — all match `selection_freeze_fx.json`.
- 7 sampled JSONL digests recomputed and matched, including all four frozen candidates (GBPUSD RANGEEXP-C3 `020e645dbfec2cdc`, C4 `548bb8606af4beae`; USDJPY PDHLOC-C2 `cb97b94ad6e92783`, RANGEEXP-C3 `020e645dbfec2cdc`) plus GBPUSD-GAP-C1, GBPUSD-DAYMOM-C2, USDJPY-ROUNDNUM-C3.
- **All four frozen trials RE-RUN by me from the parquet planes** (`load_h1_plane` → slice ts<2026-01-01 → `engine.run_strategy` at k=1.0/1.5/2.0 with `pip=fx.PAIRS[pair]['pip']` → `E.metrics`, plus the 6 fold metrics at k=1.0): **byte-exact match to the JSONL** on net_pips/trades/pf/hit/maxdd and all folds. Gates G1–G5 recomputed from my own re-runs = all True, matching `eligible=true`. `candidates_frozen_fx.json` dev_stats equal the JSONL values field-for-field.
- Eligibility census matches commit message: GBPUSD 7 positive @1.0, 2 eligible (C3 net@1.5 7702.6 > C4 7024.95); USDJPY 12 positive, 4 eligible.
- During the same session I additionally re-ran (off-by-one in my first sampling, then corrected) GBPUSD-RANGEEXP-C2, USDJPY-PDHLOC-C1, USDJPY-RANGEEXP-C2 — also byte-exact. Total 7 arms independently reproduced.

## 5. USDJPY DUPLICATE CLAIM — PASS (deviation validly disclosed pre-holdout)

- PDHLOC-C2 `{buf:2, opposite_exit:true}` vs PDHLOC-C4 `{buf:2, opposite_exit:false}`: **outcome-identical across all three cost tiers (k=1.0 net 3573.6, k=1.5 net 3251.75, k=2.0 net 2929.9) and all six folds** — full-record dict equality holds. Supports the "opposite_exit never fired" explanation.
- Mechanical ranking by net@1.5: C2 3251.75 (t) C4 3251.75 (t) RANGEEXP-C3 2833.6 > RANGEEXP-C4 2347.5. Freezing C2+RANGEEXP-C3 = rank-1 + distinct-mechanism rank-3, spending the pair's ≤2 looks on two different books rather than two copies of one.
- The deviation is recorded verbatim in `candidates_frozen_fx.json` (`deviation_disclosed.USDJPY`), committed in `f87b79ff` **before** any holdout run (no holdout artifact exists anywhere in history). GBPUSD sibling-mechanism note also self-disclosed in the same artifact.

## 6. FIXTURES (backcompat) — PASS

- `pytest …/EURUSD-OPEN-SEARCH-V2/scripts/test_v2_fixtures.py -q` → **4 passed** (inherited engine semantics preserved under the pip-parametrized engine lineage).
- `pytest …/FX-MAJORS-SEARCH-V1/scripts/test_fx_fixtures.py -q` → **3 passed** (JPY scale + PIT truncation at both scales).

## 7. BOUNDARIES — PASS

- No orders/paper/live/broker references anywhere in cycle `scripts/` (grep: none). No suspicious keys in any JSONL record (order/paper/live/ticket/broker: none).
- Secret-pattern scan (api_key, token, password, AKIA…, ghp_…) over scripts, outcomes, freeze, probe: **no hits**.
- D2 = `OWNER_WAIVED_EXPLORATORY` on all 96 records; never recorded as PASS anywhere.
- No holdout metrics in outcomes/ or in any commit on the branch (§2).
- Plan preregistration verified on main: dev 2021-01-01..2025-12-31, holdout 2026-01-01..2026-06-30, gates G1–G5 with G2 PF≥1.20, G3 ≥4/6 folds, selection "eligible ranked net@1.5, freeze ≤2 per pair", holdout SUCCESS = net>0 @1.0 AND @1.5, ONE look, failure final; 12×4×2 = 96 = cap; instruction explicitly NOT a GO.

## FINDINGS

- **F1 — LOW (non-blocking)**: uncommitted working-tree edit to `scripts/fxm_build.py` (mtime 08:57, after the 07:55:00 freeze commit): manifest key lookup corrected from `{side}/{rel_name}` to `M1/{side}/{rel_name}`. Not part of the outcome computation path (`fxm_campaign`/`fxm_holdout` do not import `fxm_build`); the edit is fail-closed hardening (a wrong key aborts, it cannot fabricate). The committed census/derived artifacts were independently re-verified against raw bytes by me (§3), and all frozen re-runs reproduce byte-exact on the derived planes, so chain of custody holds regardless. Housekeeping: commit or revert this diff before the holdout run so the tree is clean at execution time.
- **F2 — INFO**: GBPUSD freeze takes two sibling configs of the same mechanism (RANGEEXP C3/C4) — holdout is effectively one mechanism test for that pair. Already self-disclosed in `candidates_frozen_fx.json` (`deviation_disclosed.GBPUSD`) and consistent with V2 precedent. Accepted.

## VERDICT

**AUTHORIZED** — the holdout check (ONE look per pair, `fxm_holdout.py`, SUCCESS = net>0 @1.0 AND @1.5 per pair, failure final, no rescue) may be executed against the four frozen candidates as preregistered. F1 is housekeeping only and does not gate.

*Fresh-context declaration: the auditor held no prior context from any lane of this cycle. Every PASS above was re-measured on 2026-09-24 from git objects, raw/sha-verified data files, independently recomputed digests, and independent re-execution of the frozen trials and both fixture suites — none taken on trust from commit messages or lane artifacts.*
