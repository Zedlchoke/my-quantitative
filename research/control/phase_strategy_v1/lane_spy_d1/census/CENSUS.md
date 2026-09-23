# CENSUS — SPY_D1 (lane L3, cycle PHASE-STRATEGY-V1)

Rule `PSV1-SPYD1-QUAD-SMA200-SLOPE20` on `adjusted_close`; warmup 219 sessions; post-warmup window 2724 sessions (2015-11-13 → 2026-09-16); folds = eras on session-index edges (see freezes/era_fold_freeze.json).

## Cell occupancy (post-warmup)

| phase | occupancy | episodes (global / fold-local sum) | dwell median / max (sessions) |
|---|---|---|---|
| ACCUMULATION | 2.20% | 15 / 15 | 3.0 / 14 |
| UPTREND | 71.11% | 22 / 23 | 17.5 / 395 |
| DISTRIBUTION | 0.99% | 5 / 5 | 2.0 / 20 |
| DOWNTREND | 7.56% | 10 / 11 | 13.5 / 66 |
| TRANSITION_UNKNOWN | 18.14% | 48 / 49 | 2.5 / 65 |

UNKNOWN share 18.14%; longest UNKNOWN run 65 sessions.

## Floors (immutable 20 / 3 / 100) and verdicts

| phase | episodes cell (floor 20) | episodes per fold (floor 3) | decisions per fold (floor 100) | verdict |
|---|---|---|---|---|
| ACCUMULATION | 15 (-5) | F1:1(-2), F2:2(-1), F3:5(+2), F4:7(+4) | F1:3(-97), F2:10(-90), F3:24(-76), F4:23(-77) | **NOT_RUN_THIN_PHASE** |
| UPTREND | 23 (+3) | F1:6(+3), F2:7(+4), F3:3(+0), F4:7(+4) | F1:581(+481), F2:314(+214), F3:280(+180), F4:762(+662) | **NO_ELIGIBLE_PROPOSAL** |
| DISTRIBUTION | 5 (-15) | F1:2(-1), F2:0(-3), F3:1(-2), F4:2(-1) | F1:2(-98), F2:0(-100), F3:3(-97), F4:22(-78) | **NOT_RUN_THIN_PHASE** |
| DOWNTREND | 11 (-9) | F1:2(-1), F2:2(-1), F3:5(+2), F4:2(-1) | F1:26(-74), F2:32(-68), F3:141(+41), F4:7(-93) | **NOT_RUN_THIN_PHASE** |

| TRANSITION_UNKNOWN | n/a | n/a | n/a | **NO_ELIGIBLE_PROPOSAL** (uncertainty state by construction) |

## Sensitivity (±1 notch, reported never optimized)

- `sma_n_down`: label agreement 0.8990
- `sma_n_up`: label agreement 0.8781
- `slope_k_down`: label agreement 0.9501
- `slope_k_up`: label agreement 0.9662
- `p_band_down`: label agreement 0.9864
- `p_band_up`: label agreement 0.9853
- `s_band_down`: label agreement 0.9336
- `s_band_up`: label agreement 0.9130

## Calendar-defect gate

- Gate 10.3a weekday-rotation replay: **PASS** (+1..+4 day date relabels; labels, per-fold occupancy and transitions invariant).
- Gate 10.3b Tuesday test: PASS in tests_py (synthetic predecessor defect shape produces weekly Tuesday force-flats in the defective reference engine; this lane's pipeline produces ZERO weekday-attributable force-flats; `clock_attributable_force_flats == 0`).
- Structural: no staleness/holding-duration flat law exists in the lane package.

## Ancestry measurements (rho, pre-PnL)

- month-settle vs quarter-opex dummies: rho -0.141
- month-settle vs ex-div-window dummies: rho -0.142
- quarter-opex vs ex-div-window dummies: rho +0.559

Quarter-anchored timing subclasses form one correlated class (0.56 > 0.20 bar); month-settle timing is a measured-dead family (SFV3-A6-TOM-SETTLE). See proposals/proposals.json.

