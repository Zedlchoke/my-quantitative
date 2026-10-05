# SELECTION_REPORT — Lane T_SELECT, cycle NFL-WINPROB-NG-SCORED-V1

- Run started: 2026-10-05T10:17:17Z · report written: 2026-10-05T10:17:28Z
- Scope: TRAIN-INTERNAL selection ONLY (TRAIN = complete seasons 2000–2018).
  Zero access to season > 2018 outcomes (hard load filter + assertions; grep-auditable
  constants `SEASON_MAX_GAMES=2018`, `SEASON_MAX_PBP=2017` in arms.py). No real-game
  predictions, no prediction-ledger file, calibration/forecasting vocabulary only.
- Preregistration authority: DISPATCH_T_SELECT.md (grids pinned), PROTOCOL_NFL_NG.md §0/§2/§6,
  MECHANISMS_NFL_NG.md §2. Selection criterion: pooled mean LL over inner folds 2014–2018;
  tie-break fewer active parameters, then lexicographic config id.

## 1. Lock observations (heavy lock, read-only inspect; registry never written)

- BEFORE run attempt 1 @ 2026-10-05T10:17:17Z: verdict = **FREE_PROVEN**
- AFTER run @ 2026-10-05T10:17:26Z: verdict = **FREE_PROVEN**

## 2. Data facts (measured at load, this run)

- games.csv rows loaded: 5057 (seasons 2000–2018; 2491 rows outside 2000–2018 dropped at load; 0 PRE rows dropped)
- REG rows 4848; POST rows 209 (update ratings, never scoring/training rows)
- Ties: 9 total (9 REG); excluded from all LL/training rows; S=0.5 update. Per season: {2000: 0, 2001: 0, 2002: 1, 2003: 0, 2004: 0, 2005: 0, 2006: 0, 2007: 0, 2008: 1, 2009: 0, 2010: 0, 2011: 0, 2012: 1, 2013: 1, 2014: 1, 2015: 0, 2016: 2, 2017: 0, 2018: 2}
- Neutral-site rows (location==Neutral): 51 total 2000–2018 — matches Lane A (51). Per season: {2000: 1, 2001: 1, 2002: 1, 2003: 2, 2004: 1, 2005: 2, 2006: 1, 2007: 2, 2008: 3, 2009: 2, 2010: 3, 2011: 2, 2012: 2, 2013: 4, 2014: 5, 2015: 4, 2016: 5, 2017: 6, 2018: 4}; scored HCA=0 (B1* carries HCA=0; C2 zeroes h and skips deviation updates)
- Odds/probability columns quarantined at load (never read): ['away_moneyline', 'away_spread_odds', 'home_moneyline', 'home_spread_odds', 'over_odds', 'spread_line', 'total', 'total_line', 'under_odds']
- Inner-eval rows: 1275 ({'2014': 255, '2015': 256, '2016': 254, '2017': 256, '2018': 254}); away-short-week eval cells: 365
- C3 priors: pbp seasons ≤ 2017 only; z-table boundaries 2001–2018; 574 (season,lineage) entries; 2000 has no prior (no term)

## 3. B0 constant (frozen)

- **B0 p = 0.571399049390** = TRAIN 2000–2018 REG non-tie home-win rate (2765 home wins of 4839 rows).
- B0 pooled inner LL = 0.683037 (calibration slope N/A — degenerate constant)
- B1* pooled inner LL = 0.652497; per fold: 2014=0.635816, 2015=0.652348, 2016=0.654671, 2017=0.651687, 2018=0.668035
- ΔLL(B1*, B0) pooled inner = -0.030540 [-0.043498, -0.017108] (context only; B1* vs B0 gates are terminal-cycle law)

## 4. Designed-null equivalence (FIRST — proven before any other number)

All four designed nulls reproduce B1*'s p_home stream **bit-for-bit** (max |Δp| = 0.0 exactly)
on the full inner-eval stream (and on all 5,057 rows):

| null config | max abs Δp (inner-eval stream) | max abs Δp (all rows) |
|---|---|---|
| C1_B000 | 0.0 | 0.0 |
| C2_NULL | 0.0 | 0.0 |
| C3_T000 | 0.0 | 0.0 |
| C4_D000 | 0.0 | 0.0 |
| C3 θ=0 full replay vs B1* replay ratings/expected bit-identical | True | (all 5,057 records) |

Per-fold warm/eval slice equivalence (fold s = warm replay 2000→s−1 then evaluate s):
single-replay + slice verified bit-for-bit against an independent truncated replay for
every inner fold (ratings, expected scores, SOS adjustments, rest days): {"2014": true, "2015": true, "2016": true, "2017": true, "2018": true}

## 5. Grid results (every evaluated config; trial accounting)

| config | arm | params | pooled LL | ΔLL vs B1* | 95% CI (date-cluster) | slope | band |
|---|---|---|---|---|---|---|---|
| B0 | B0 | {} | 0.683037 | +0.030540 | [+0.017108, +0.043498] | N/A (degenerate) | FAIL |
| B1STAR | B1STAR | {"HCA": 0, "K": 40, "gamma": "2/3", "mu": 1500} | 0.652497 | +0.000000 | [+0.000000, +0.000000] | 1.6051 | FAIL |
| C1_B000 | C1 | {"beta": 0.0} | 0.652497 | +0.000000 | [+0.000000, +0.000000] | 1.6051 | FAIL |
| C1_B025 | C1 | {"beta": 25.0} | 0.652638 | +0.000141 | [-0.000011, +0.000295] | 1.6260 | FAIL |
| C1_B050 | C1 | {"beta": 50.0} | 0.652786 | +0.000290 | [-0.000015, +0.000596] | 1.6473 | FAIL |
| C1_B075 | C1 | {"beta": 75.0} | 0.652942 | +0.000445 | [-0.000012, +0.000905] | 1.6689 | FAIL |
| C1_B100 | C1 | {"beta": 100.0} | 0.653104 | +0.000607 | [-0.000002, +0.001220] | 1.6909 | FAIL |
| C2_L025_D1O2_H000 | C2 | {"gamma_d": 0.5, "gamma_d_name": "1O2", "h": 0.0, "lambda": 0.25} | 0.648719 | -0.003778 | [-0.005212, -0.002279] | 1.4677 | FAIL |
| C2_L025_D1O2_H025 | C2 | {"gamma_d": 0.5, "gamma_d_name": "1O2", "h": 25.0, "lambda": 0.25} | 0.645608 | -0.006889 | [-0.009298, -0.004405] | 1.4657 | FAIL |
| C2_L025_D1O3_H000 | C2 | {"gamma_d": 0.3333333333333333, "gamma_d_name": "1O3", "h": 0.0, "lambda": 0.25} | 0.649590 | -0.002907 | [-0.004034, -0.001746] | 1.5065 | FAIL |
| C2_L025_D1O3_H025 | C2 | {"gamma_d": 0.3333333333333333, "gamma_d_name": "1O3", "h": 25.0, "lambda": 0.25} | 0.646187 | -0.006310 | [-0.008444, -0.004131] | 1.5044 | FAIL |
| C2_L050_D1O2_H000 | C2 | {"gamma_d": 0.5, "gamma_d_name": "1O2", "h": 0.0, "lambda": 0.5} | 0.646176 | -0.006321 | [-0.008992, -0.003505] | 1.3520 | FAIL |
| C2_L050_D1O2_H025 | C2 | {"gamma_d": 0.5, "gamma_d_name": "1O2", "h": 25.0, "lambda": 0.5} | 0.643710 | -0.008787 | [-0.012207, -0.005198] | 1.3505 | FAIL |
| C2_L050_D1O3_H000 | C2 | {"gamma_d": 0.3333333333333333, "gamma_d_name": "1O3", "h": 0.0, "lambda": 0.5} | 0.647388 | -0.005109 | [-0.007266, -0.002864] | 1.4148 | FAIL |
| C2_L050_D1O3_H025 | C2 | {"gamma_d": 0.3333333333333333, "gamma_d_name": "1O3", "h": 25.0, "lambda": 0.5} | 0.644493 | -0.008003 | [-0.010948, -0.004981] | 1.4132 | FAIL |
| C2_L075_D1O2_H000 | C2 | {"gamma_d": 0.5, "gamma_d_name": "1O2", "h": 0.0, "lambda": 0.75} | 0.644478 | -0.008019 | [-0.011829, -0.004016] | 1.2545 | FAIL |
| C2_L075_D1O2_H025 | C2 | {"gamma_d": 0.5, "gamma_d_name": "1O2", "h": 25.0, "lambda": 0.75} | 0.642470 | -0.010027 | [-0.014440, -0.005374] | 1.2533 | FAIL |
| C2_L075_D1O3_H000 | C2 | {"gamma_d": 0.3333333333333333, "gamma_d_name": "1O3", "h": 0.0, "lambda": 0.75} | 0.645744 | -0.006753 | [-0.009874, -0.003490] | 1.3312 | FAIL |
| C2_L075_D1O3_H025 | C2 | {"gamma_d": 0.3333333333333333, "gamma_d_name": "1O3", "h": 25.0, "lambda": 0.75} | 0.643249 | -0.009248 | [-0.012997, -0.005344] | 1.3299 | FAIL |
| C2_NULL | C2 | {"gamma_d": 0.3333333333333333, "gamma_d_name": "1O3", "h": 0.0, "lambda": 0.0} | 0.652497 | +0.000000 | [+0.000000, +0.000000] | 1.6051 | FAIL |
| C3_T000 | C3 | {"theta": 0.0} | 0.652497 | +0.000000 | [+0.000000, +0.000000] | 1.6051 | FAIL |
| C3_T025 | C3 | {"theta": 25.0} | 0.649196 | -0.003301 | [-0.006185, -0.000341] | 1.3054 | FAIL |
| C3_T050 | C3 | {"theta": 50.0} | 0.648348 | -0.004149 | [-0.009944, +0.001837] | 1.0788 | OK |
| C3_T075 | C3 | {"theta": 75.0} | 0.649960 | -0.002537 | [-0.011280, +0.006498] | 0.9081 | OK |
| C3_T100 | C3 | {"theta": 100.0} | 0.654044 | +0.001547 | [-0.010209, +0.013703] | 0.7773 | FAIL |
| C4_D000 | C4 | {"delta": 0.0} | 0.652497 | +0.000000 | [+0.000000, +0.000000] | 1.6051 | FAIL |
| C4_D025 | C4 | {"delta": 25.0} | 0.654111 | +0.001614 | [+0.000775, +0.002479] | 1.5787 | FAIL |
| C4_D050 | C4 | {"delta": 50.0} | 0.655992 | +0.003495 | [+0.001818, +0.005233] | 1.5380 | FAIL |

Total evaluated configs (selection ledger rows, type=config): 28 (B0 + B1* + C1 5 + C2 12 + C2 designed-null 1 + C3 5 + C4 3). Negative-control runs: 6. Full ledger: SELECTION_LEDGER.jsonl.

Note on the slope column: the pre-registered calibration band [0.85, 1.15] is an ADMIT gate
for CANDIDATE arms (PROTOCOL §6.1); B0's slope is degenerate (N/A) and B1* is exempt from
selection by BASELINE LAW. Measured on the pooled inner folds, the B1* baseline itself is
underconfident on TRAIN (slope 1.605) — every C1/C2 grid point inherits this. The gate is
therefore binding: only a candidate that both improves the pooled LL AND calibrates inside
the band can be fielded. The C3 EPA prior is the only mechanism that moves the slope into
the band (θ=50: 1.079; θ=75: 0.908) while improving the pooled LL.

Designed-null configs (C1_B000, C2_NULL, C3_T000, C4_D000) are equivalence arms, not
candidates: each arm's selection runs over its pre-registered non-null grid points only.

## 6. Negative controls (diagnostic arms; never candidates)

| arm | parent config | control | ΔLL vs B1* | 95% CI | wins? |
|---|---|---|---|---|---|
| C1 | C1_B025 | time_shuffled_sos_twin (seed 20261005) | +0.000029 | [-0.000119, +0.000173] | no |
| C2 | C2_L075_D1O2_H025 | time_shuffled_devs_twin (seed 20261005) | +0.003656 | [-0.000229, +0.007682] | no |
| C2 | C2_L075_D1O2_H025 | venue_label_permutation (seed 20261005) | -0.006873 | [-0.009950, -0.003733] | YES — MACHINERY_SUSPECT |
| C3 | C3_T050 | time_shuffled_epa_prior_twin (seed 20261005) | -0.000455 | [-0.004890, +0.004169] | no |
| C4 | C4_D025 | time_shuffled_short_week_labels (seed 20261005) | +0.000826 | [-0.000082, +0.001759] | no |
| C4 | C4_D050 | time_shuffled_short_week_labels (seed 20261005) | +0.001921 | [+0.000099, +0.003792] | no |

A control "wins" iff its ΔLL 95% CI lies entirely below 0. Any winning control blocks
admission and raises MACHINERY_SUSPECT (never a pass).

## 7. Slot dispositions (freeze input)

- **C1: KILL** — G-ENTRY failure: pooled inner dLL point >= 0 vs B1*; calibration slope outside [0.85,1.15]
  - selected config: `C1_B025` (params {"beta": 25.0})
- **C2: KILL** — G-ENTRY failure: calibration slope outside [0.85,1.15]; shuffled negative control wins (CI entirely < 0) -> MACHINERY_SUSPECT
  - selected config: `C2_L075_D1O2_H025` (params {"gamma_d": 0.5, "gamma_d_name": "1O2", "h": 25.0, "lambda": 0.75})
- **C3: FIELD** — G-ENTRY PASS: point dLL < 0, slope in band, no winning negative control
  - selected config: `C3_T050` (params {"theta": 50.0})
- **C4: RELEASE** — G-INT failure: no pre-registered delta>0 config has away-short-week slice CI excluding 0 in the pre-registered direction with pooled direction consistent; slot released
  - δ=25: slice n=365 ΔLL=+0.005637 CI [+0.002762, +0.008617]; pooled +0.001614; G-INT=FAIL
  - δ=50: slice n=365 ΔLL=+0.012209 CI [+0.006457, +0.018169]; pooled +0.003495; G-INT=FAIL

Gates applied per PROTOCOL §6: G-ENTRY admission requires pooled inner point ΔLL < 0 AND
calibration slope ∈ [0.85, 1.15] AND no winning shuffled control; CI entirely > 0 ⇒ kill.
C4 (slot 6) is gate-only: G-INT requires the away-short-week slice ΔLL CI to exclude 0 in the
pre-registered direction AND the pooled direction to be consistent; failure ⇒ slot RELEASED.

Disclosure (C4 cell count): the frozen f2 rest definition (days between the away team's
strictly-prior kickoffs; ≤ 6 ⇒ short week) yields 365 away-short-week eval cells over the
5 inner folds (≈ 73/season) — larger than the mechanisms doc's rough 15–20/season estimate;
the gate ran exactly as pre-registered on the frozen definition. Both δ>0 configs landed
WORSE than B1* (positive ΔLL, slice CI excluding 0 on the wrong side): direction inconsistent
⇒ slot 6 RELEASED, as the mechanisms spec anticipated.

Freeze language (PROTOCOL §6.1 verbatim consequence): ADMIT (C3, θ=50) is weak-but-positive
train-internal evidence (pooled ΔLL point < 0 with CI including 0) — it admits the arm to
accrue prospective evidence; it never converts a train-internal CI into a claim.
C2's venue-label permutation control WON (ΔLL CI entirely < 0 with corrupted venue labels),
i.e. the C2 gain does NOT depend on true venue labels ⇒ MACHINERY_SUSPECT (comparison-
machinery fault per MECHANISMS §2-C2 falsifier; a negative control can never win and a
winning control un-scores the candidate). C2 is KILLED and returned to design; it is never
fielded this cycle. C1 is killed on G-ENTRY (point ΔLL ≥ 0 AND slope out of band).

## 8. Determinism

- Seed 20261005 for all bootstrap resamples and control shuffles (inherited).
- Fixed iteration orders: games sorted by (kickoff UTC, game_id); batches = identical kickoffs;
  control shuffles iterate scoring weeks in (season, week) sorted order.
- Single process, single pass per arm; interpreter /Users/hoangminhlong/my-quantitative/.venv/bin/python

## 9. Boundary compliance

- No season > 2018 outcome row was read (filter + assertion at load; constant above).
- No real-game win-probability row produced; no prediction ledger file created.
- No writes outside lanes/T_SELECT/**, ~/.my-quantitative-data/nfl-ng-scored-v1/selection/**
  and lanes/DISPATCH/handoff_T_SELECT.json; no git commands; no lock-registry writes.
- Calibration/forecasting vocabulary only.
