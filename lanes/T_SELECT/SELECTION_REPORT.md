# SELECTION REPORT — WNBA-PLAYERFEAT-SCORED-V1 · lane T_SELECT · TRAIN-INTERNAL

Date of record: 2026-10-05 · seed 20261005 · interpreter /Users/hoangminhlong/my-quantitative/.venv/bin/python · no git operations · OOS [2020..2026] NEVER touched (select mode hard-capped at season <= 2018; doctored-2019 probe aborts loud).

## 1. Inputs and integrity

- Feature table: `/Users/hoangminhlong/.my-quantitative-data/playerfeat-prep-v1/wnba/features/wnba_player_features_2002_2026.parquet` — sha256 verified vs manifest (`ceaf10ba…`), file = 11,976 rows x 40 cols (2002–2026), no outcome columns (asserted). THIS LANE READS ONLY the ≤2018 slice (7990 rows); 2019–2026 rows never entered memory (cap enforced at read time; doctored-row probe aborts).
- Universe: ESPN-side filter law re-applied, seasons 2002–2018 → 3995 games (2002–2018 slice of the 5,988-game universe law; per-season census matches COVERAGE_AUDIT). Scores used ONLY for outcomes (home-win indicator) + tips + neutral flag.
- Warm-up: stats-side schedules 1997–2001 FOUND on disk (1022 rows, 100% scored, 0 duplicates) — used as rating-stream WARM-UP ONLY, never train/score/feature rows. Warm-up fallback (2002–2004) NOT needed.
- Lineage: 20-key table `team_key_table.csv`; ratings live on `franchise_key` from the frozen feature table (ESPN side) and lineage `stats_abbrs` (warm-up side). Raw-abbreviation joins FAIL by construction (canary in --selftest: ESPN labels all Detroit 2002–2009 as TUL; 'UTH'/'LA'/'CONN'/'CT'/'NY'/'WSH' unmapped on the stats-side list).
- Heavy lock: FREE_PROVEN (attempts used: 1).

## 2. Engine law (frozen, reproduced by --selftest)

- p_home = 1/(1+10^(-(R_h − R_a + HCA_eff)/400)); update R ← R + K·(outcome − expected) with the AWAY side's expectation 1 − p_home (zero-sum pair update — regression-fixture enforced after the selftest caught a hardcoded-outcome bug); season boundary R ← 1500 + γ·(R_end − 1500); new franchise at 1500; games at an identical tip_utc are predicted from one snapshot then updated (strict-inequality as-of law); neutral-site rows take HCA_eff = 0; ratings live on the 20-key franchise identity (relocation-safe).

## 3. B0 constant floor

- p_home = TRAIN-window home-win rate, frozen: **0.603755** (3995 games, 2002–2018).

## 4. B1-WNBA grid (27 fits, all counted) — FROZEN CONFIG

- Grid K∈{8,16,32} × HCA∈{0,50,100} × γ∈{0.65,0.75,0.85}; 4 expanding-origin 2-season validation blocks over the TRAIN tail (2011-12, 2013-14, 2015-16, 2017-18; 1774 validation games); criterion = LOWEST pooled inner LL (log loss); tie-break (K,HCA,γ) ascending.
- **FROZEN: K=32, HCA=50, γ=0.65** — pooled validation LL 0.623498 (full-train LL 0.636541, context only).
- Warm-up law: 1997–2001 stats-side rows feed the rating stream; γ reversion applies at every season boundary including inside the warm-up and into 2002; new franchises enter at league mean 1500.
- Train-internal kill test vs B0 (same 1774 validation games, paired tip-date-cluster bootstrap, 10,000 resamples, seed 20261005): ΔLL = -0.054386 [-0.070150, -0.038275] — CI excludes 0: True; kill passed: True. Calibration slope 0.9530 (band [0.85, 1.15]). Degenerate K→0 kill: selected K=32 ≠ 0; engine improves on B0 train-internally iff kill passed.
- Grid twin (time-shuffled outcomes, seed 20261005, one global within-season permutation): twin-B1 LL 0.696856 vs twin-B0 LL 0.677884 on the same shuffled validation games → ΔLL +0.018972; MACHINERY_SUSPECT = False (flag only if the twin beats its OWN parent). Parent (real-data) slope 0.9530 reported alongside per the adjudication refinement.
- Warm-up-vs-cold-start rerun (diagnostic only): warm-up LL 0.636541 vs cold-start LL 0.636773 on the train window.

## 5. Designed-null gate (FIRST, real data)

- c≡1 (WF-A null) and φ=0 (WF-B null) both reproduce the frozen B1-WNBA p_home stream **bit-for-bit** on all 5017 corpus games (byte-identity of the float64 stream): True. Also verified on 3 synthetic streams in --selftest. Failure would have been a TECHABORT stop.

## 6. Standardization moments (pinned)

- WF_B x = `b5_minutes_hhi`: mean 0.117794, sd 0.010039 (population sd, ddof=0), n = 2292 computed rows, seasons 2013-2018 (train computed rows only; neutral rows excluded).
- WF_C x = `c_absence_share`: mean 0.107699, sd 0.103548 (population sd, ddof=0), n = 2292 computed rows, seasons 2013-2018 (train computed rows only; neutral rows excluded).
- Pre-registered constructions (pinned before any scored look): WF-B x = `b5_minutes_hhi` (rotation concentration; k=5 chosen a priori — k-selection remains deferred per FEATURE_SPEC §3, the k=3 variant is NOT scored); WF-C x = `c_absence_share` (uniform null-minutes proxy). Era floor: rows season < 2013 → x=0 + flag `era_floor`; neutral-reason rows → x=0 + flag `neutral_x0`. Feature folds are 2014–2018 (era-floor adaptation of the packet's 4×2-season blocks, disclosed in the plan).

## 7. Feature arms — G-ENTRY vs the FROZEN B1-WNBA

Folds: 5 expanding-origin single-season folds 2014..2018 (1106 scored games); criterion LOWEST pooled inner LL (log loss); grids φ∈{−50,−25,0,25,50} immutable; tie-break (|φ|,φ) ascending. Bootstrap: paired tip-date-cluster, 10,000 resamples, seed 20261005. Twin: time-shuffled outcomes (seed 20261005), flagged MACHINERY_SUSPECT only if the twin beats its OWN parent arm; parent slope reported alongside.

| arm | frozen φ | arm fold LL | parent fold LL | ΔLL [95% CI] | slope [band] | twin ΔLL | verdict |
|---|---|---|---|---|---|---|---|
| WF-A | — | 0.633348 | 0.632928 | +0.000420 [-0.002750, 0.003621] | 0.9845 | -0.000968 | MACHINERY_SUSPECT |
| WF-B | +0 | 0.632928 | 0.632928 | +0.000000 [0.000000, 0.000000] | 0.9047 | +0.000000 | RELEASE |
| WF-C | +0 | 0.632928 | 0.632928 | +0.000000 [0.000000, 0.000000] | 0.9047 | +0.000000 | RELEASE |

- WF-A: continuity-modulated carryover R_start = 1500 + γ_sel·c·(R_end−1500), c from the frozen table (2014+; game-1 v2 rows / expansion / missing → c=1 = parent). NO free scalar; γ frozen from B1-WNBA. Real-data ΔLL +0.000420 [-0.002750, 0.003621] sits inside the ±0.003 inconclusive scale at this capacity. Its time-shuffled twin scored ΔLL -0.000968 vs its OWN parent on the same shuffled corpus → MACHINERY_SUSPECT under the frozen rule (twin-beats-own-parent). Adjudication refinement applied verbatim: the miscalibrated-parent exemption does NOT apply because the parent's real-data fold slope 0.9047 is INSIDE [0.85, 1.15]; the twin-vs-reference reading is therefore not exculpatory either. Arm UN-SCORED this cycle; the flag plus both ΔLL magnitudes (real +0.000420 / twin -0.000968, both inside the ±0.003 inconclusive scale) are recorded for a machinery audit at the next owner round before any WF-A re-proposal.
- WF-B per-φ pooled fold LL (all 5 counted): φ=-50: 0.641544, φ=-25: 0.634829, φ=+0: 0.632928, φ=+25: 0.635825, φ=+50: 0.643415.
- WF-C per-φ pooled fold LL (all 5 counted): φ=-50: 0.648506, φ=-25: 0.637160, φ=+0: 0.632928, φ=+25: 0.636072, φ=+50: 0.646431.

- Fold-game flags (selected configs): WF-B: {"neutral_hca0": 2, "neutral_x0": 165}; WF-C: {"neutral_hca0": 2, "neutral_x0": 165}.
- Effects smaller than ~0.003 ΔLL are INCONCLUSIVE at this capacity (packet §6) — stated, not stretched.

## 8. Neutral-site rows (separate report)

- The ESPN corpus carries a `neutral_site` flag: 2 rows inside the train window (400864492, 400910457); HCA=0 applied there (flag `neutral_hca0`). The stats-side warm-up corpus carries NO neutral flag — absence disclosed.

## 9. Fit counts and trial discipline

- Scored-selection fits: B1 grid 27 (all counted) + WF-A 1 + WF-B 5 + WF-C 5 = **38**. Diagnostics outside budget: twins (4), warm-up-vs-cold-start (1), designed-null checks (byte-identity, not fits), B0 reference.
- Ledger: `SELECTION_LEDGER.jsonl` (every run incl. all 27 grid fits).

