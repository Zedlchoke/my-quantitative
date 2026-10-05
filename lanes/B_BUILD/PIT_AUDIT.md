# PIT_AUDIT — B_BUILD · NFL-PLAYERFEAT-PREP-V1 · 2026-10-05

Point-in-time correctness audit for the frozen player-feature table. Law restated up front:

> **Target-game injury/active/DNP/starter status = NOT_RUN_PIT.** No row, column, or value
> in `nfl_playerfeat_table_v1.parquet` encodes any target-game availability or outcome. All
> features are aggregates of *strictly prior* games under the kickoff-time as-of law
> (`asof_rule_version = asof-1.0.0-nfl-playerfeat-prep-v1`).

## 1. As-of law

- `kickoff_utc` = gameday + gametime localized **America/New_York** → UTC (predecessor
  canonical law; DST handled by zoneinfo).
- Prior set P(team, target) = team's same-season games in the stats corpus with
  `kickoff_utc(prior) < kickoff_utc(target)` — **strict inequality on the UTC timestamp**.
  Same-day earlier games count as prior; equal kickoffs never do.
- `n_prior_games_used` = |P| (G1/G2 support). G3 support disclosed separately as
  `g3_n_snap_prior_games` (prior games present in the snap corpus).
- Verified for **all 1,266 rows** by full-table scan (S1): declared n_prior == recount of
  strictly-prior team games; 0 mismatches.

## 2. Worked example (numbers re-derived from bytes) — 2024_11_KC_BUF, KC side

Target: 2024-11-17T21:25:00Z (16:25 ET), BUF at KC. KC same-season priors: weeks 1–5, 7–10
(wk6 bye) → **n_prior_games_used = 9**; last prior = 2024_10_DEN_KC (2024-11-10T18:00:00Z)
→ **rest_days = 7.1424**.

**G1 prior-3 window** (most recent 3 priors by kickoff order):

| game | kickoff_utc | att | yds | td | int |
|---|---|---|---|---|---|
| 2024_08_KC_LV | 2024-10-27T20:25Z | 38 | 262 | 2 | 1 |
| 2024_09_TB_KC | 2024-11-05T01:15Z | 44 | 291 | 3 | 0 |
| 2024_10_DEN_KC | 2024-11-10T18:00Z | 42 | 266 | 1 | 0 |
| **Σ (qb_*_k3)** | | **124** | **819** | **6** | **1** |

Matches the predecessor PIT worked example **exactly** (819 yds / 6 TD / 1 INT / 124 att —
selftest S2). Derived: qb_ypa_k3 = 6.60484; qb_epa_k3 = 30.55991; qb_epa_pa_k3 = 0.24645;
season-to-date qb_yds_std_pg = 2208/9 = 245.33333, qb_epa_std_pg = 3.33435; form
qb_yds_form_k3 = 819/3 − 245.33333 = **+27.66667 yds/g**, qb_epa_form_k3 = **+6.85229**.
k5 window (wks 5,7,8,9,10) = 1304 yds / 190 att (selftest-consistent).

**G2 prior-3 usage** (targets + carries, position_group ∈ {WR,RB,TE}), U_tot = 189:
top-3 = K.Hunt 74, T.Kelce 40, D.Hopkins 17 → **skill_top3_share_k3 = 131/189 = 0.69312**;
skill_hhi_k3 = 0.22208; skill_usage_pg_k3 = 63.0; skill_top5_share_k5 = 0.79299.

**G3**: 2024 has no snap corpus → NaN + `flag_g3_no_snap_prior` = 1 (neutral rule; no
imputation).

## 3. Leak guards (selftest, `selftest_results.json`)

| check | method | result |
|---|---|---|
| S1 kickoff strict inequality | full-table recount of every row's strictly-prior support | 1,266/1,266 rows, 0 mismatches — **PASS** |
| S2 KC worked example | prior-3 sums re-derived from parquet bytes | 819/6/1/124 exact — **PASS** |
| S3 target-game absence | per-game perturbation: add +1000 pass yds / +50 targets / +5 EPA to **only game X's** stats rows, rebuild, assert row X unchanged (4 fixtures: 2024_11_KC_BUF, 2024_07_KC_SF, 2026_04_PIT_CLE, 2026_03_ATL_GB) | all 4 identical — **PASS** (control: later games that legitimately see X as prior do move — verified during development) |
| S6 determinism | fresh in-process rebuild + fresh-process rerun, parquet sha | `f1bc6b4a…7c4f57` identical — **PASS** |

S3 design note (development incident, resolved): the first version perturbed all four
fixtures at once and flagged a diff on 2024_11_KC_BUF — root cause was the test, not the
table: 2024_07_KC_SF is a legitimate *prior* of 2024_11_KC_BUF, so its perturbation must
change the later row. One-game-at-a-time perturbation is the correct formulation and passes.

A second development incident was a real bug caught by S3's precursor diff: the tz-aware
kickoff comparison `.values < np.datetime64(target)` mis-scoped the season-to-date aggregate
(window sums stayed right via a later `isin`, but STD means absorbed the target game). Fixed
by pure pandas `Series < Timestamp` comparisons; S1/S2/S3 now pass on the corrected build
and the output sha is from the corrected code.

## 4. G3 proxy semantics (by-design lag, NOT availability)

- "Absent in most recent prior game" uses `snaps_recent < 0.5 × window-mean` over the
  team's top-5 snap players (prior-3 window). A player injured **during the prior game**
  still logs that game's snaps; their absence in the *next* game's "recent" column is
  lagged evidence — noisy by design (predecessor F3 risk note, inherited verbatim).
- With exactly 1 snap-prior game, absent share = 0.0 by construction (recent game IS the
  mean) — documented, not a bug (n_w=1 rows: 2025 wk2, 2026 wk2 cohorts).
- **NOT_RUN_PIT is not bypassed**: G3 reads no target-game roster/injury/status source
  (none exists in the corpus — verified in predecessor D_VERIFY §4); it is a prior-game
  snap proxy only.

## 5. pfr-null rule (crosswalk canary, S4)

Cody White (gsis 00-0035891) has crosswalk pfr_id = NULL but snap rows under `WhitCo05`
(3 rows in 2026, LV). Rule: pfr-null/unresolved rows are **excluded from the G3 candidate
pool** (never tracked, never fabricated as absent); rows whose G3 window contained ≥1 such
row carry `flag_g3_pfr_null_excluded` = 1. Measured: LV 2026 rows wk2–4 all flagged
(wk1 = no-snap flag); whole-corpus exclusion cohort = {AndeAl01, CartNa00, HallGa01,
JohnIs03, OkoyCJ00, WhitCo05 (2025)}, {AndeAl01, OkoyCJ00, WhitCo05 (2026)} — 82 table rows
flagged in total. **S4 PASS.**

## 6. Bye-week fixture (S5)

KC 2024 bye = week 6. Target 2024_07_KC_SF (2024-10-20T20:25Z): window = weeks 5,4,3
(2024_05_NO_KC 331 + 2024_04_KC_LAC 245 + 2024_03_KC_ATL 217 = **qb_yds_k3 = 793.0** exact);
rest_days = 12.8403 (post-bye gap, no synthetic bye row); n_prior_games_used = 5. **PASS.**

## 7. Verdict

PIT: **PASS** — as-of law proven by full-table recount + byte-level worked example +
perturbation absence test; target-game status NOT_RUN_PIT preserved with zero exceptions.
