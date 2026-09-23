# REGIME_SAMPLE_CENSUS — A3 (REGIME-STRATEGY-MAPPING-V1)

Definitive regime-sample census per cell x regime. NO PnL anywhere: every number is counts/durations/margins over the persisted regime timeline rebuilt from the frozen V2 decision cache (`rsmv1.regime_timeline.rebuild_cell_timeline`, self-verified vs V2 recorded metrics and vs A1's saved runtime rows).

Floors (preregistered): >= 20 independent episodes/regime/cell; >= 3 episodes/regime/outer-fold; >= 100 eligible decisions/regime/outer-fold; eligible episode = length >= 6 regime bars (persistence min_dwell). Below any floor => NOT_RUN_THIN_REGIME for that regime x cell — a sample-floor verdict, NOT a market judgment.

Convention: an episode belongs to the outer fold containing its START-bar close ts (spans inclusive). Straddling episodes are counted once, wholly to the start fold; `bars_in_own_fold` is the reconciliation diagnostic (bars physically inside each fold). Cells are never pooled.

Cross-check vs A1 preliminary (evidence/regime_sample_feasibility.json): the census is re-derived independently — segmentation, fold assignment, aggregation, margins and verdicts are re-implemented in rsmv1/census.py on top of the sanctioned self-verifying rebuild — then compared field-by-field against A1's P2 draft. All compared fields agree exactly (counts, durations, margins, verdicts), which is the expected outcome: both implement the same frozen definitions on the same verified timeline. The match is therefore a confirmation, not a copy: the census additionally carries per-episode records, per-fold transitions, fold-boundary reconciliation diagnostics and margin components that the P2 draft did not have.

## BTC_H1

- Rebuild verified vs V2 (switches 90 == 90, n_decisions 8567, effUNKNOWN share 0.4271); vs A1 saved runtime rows: **MATCH**.
- Cross-check vs A1 preliminary feasibility: MATCH (94 fields compared).
- Decisions (post-warmup, evaluable): 8567; transitions: 90 per fold f0=26, f1=21, f2=20, f3=23, no_fold=0; bars outside all fold spans: 0.
- TRANSITION_UNKNOWN (unselectable, UNK_FLAT fixed): 6 bars in 1 episode(s) (share 0.0007); floors not applied.

| regime | episodes | elig.ep. | elig.dec. | mkt bars (share) | dur min/p25/med/p75/max | margin | verdict |
|---|---|---|---|---|---|---|---|
| ACCUMULATION | 23 | 23 | 2955 | 2955 (0.345) | 19/59/81/139/610 | 1.150 | **PASS** |
| UPTREND | 28 | 28 | 1774 | 1774 (0.207) | 8/33/54/92/194 | 1.400 | **PASS** |
| DISTRIBUTION | 5 | 5 | 1621 | 1621 (0.189) | 107/159/266/394/695 | 0.000 | **NOT_RUN_THIN_REGIME** |
| DOWNTREND | 34 | 34 | 2211 | 2211 (0.258) | 9/19/55/74/335 | 1.700 | **PASS** |

### Per-fold detail

| regime | fold | episodes | elig.ep. | elig.dec. | bars_in_own_fold | eps floor ok | dec floor ok |
|---|---|---|---|---|---|---|---|
| ACCUMULATION | 0 | 7 | 7 | 629 | 629 | True | True |
| ACCUMULATION | 1 | 5 | 5 | 817 | 817 | True | True |
| ACCUMULATION | 2 | 4 | 4 | 339 | 212 | True | True |
| ACCUMULATION | 3 | 7 | 7 | 1170 | 1297 | True | True |
| UPTREND | 0 | 8 | 8 | 486 | 486 | True | True |
| UPTREND | 1 | 7 | 7 | 466 | 466 | True | True |
| UPTREND | 2 | 6 | 6 | 413 | 413 | True | True |
| UPTREND | 3 | 7 | 7 | 409 | 409 | True | True |
| DISTRIBUTION | 0 | 1 | 1 | 266 | 266 | False | True |
| DISTRIBUTION | 1 | 2 | 2 | 266 | 252 | False | True |
| DISTRIBUTION | 2 | 2 | 2 | 1089 | 1103 | False | True |
| DISTRIBUTION | 3 | 0 | 0 | 0 | 0 | False | False |
| DOWNTREND | 0 | 10 | 10 | 789 | 755 | True | True |
| DOWNTREND | 1 | 7 | 7 | 573 | 607 | True | True |
| DOWNTREND | 2 | 8 | 8 | 414 | 414 | True | True |
| DOWNTREND | 3 | 9 | 9 | 435 | 435 | True | True |

- Fold-boundary reconciliation: 3 episode(s) straddle a fold boundary (ACCUMULATION:[189], DISTRIBUTION:[159], DOWNTREND:[335]); each is counted wholly to its start fold, so per-fold eligible decisions can exceed the bars physically inside the fold (see bars_in_own_fold).

## BTC_H4

- Rebuild verified vs V2 (switches 31 == 31, n_decisions 1997, effUNKNOWN share 0.2724); vs A1 saved runtime rows: **MATCH**.
- Cross-check vs A1 preliminary feasibility: MATCH (94 fields compared).
- Decisions (post-warmup, evaluable): 1997; transitions: 31 per fold f0=9, f1=5, f2=8, f3=9, no_fold=0; bars outside all fold spans: 0.
- TRANSITION_UNKNOWN (unselectable, UNK_FLAT fixed): 7 bars in 1 episode(s) (share 0.0035); floors not applied.

| regime | episodes | elig.ep. | elig.dec. | mkt bars (share) | dur min/p25/med/p75/max | margin | verdict |
|---|---|---|---|---|---|---|---|
| ACCUMULATION | 4 | 4 | 204 | 204 (0.102) | 15/26/40/123/123 | 0.000 | **NOT_RUN_THIN_REGIME** |
| UPTREND | 12 | 12 | 611 | 611 (0.306) | 8/17/36/65/228 | 0.600 | **NOT_RUN_THIN_REGIME** |
| DISTRIBUTION | 1 | 1 | 272 | 272 (0.136) | 272/272/272/272/272 | 0.000 | **NOT_RUN_THIN_REGIME** |
| DOWNTREND | 14 | 14 | 903 | 903 (0.452) | 9/17/47/96/182 | 0.667 | **NOT_RUN_THIN_REGIME** |

### Per-fold detail

| regime | fold | episodes | elig.ep. | elig.dec. | bars_in_own_fold | eps floor ok | dec floor ok |
|---|---|---|---|---|---|---|---|
| ACCUMULATION | 0 | 0 | 0 | 0 | 0 | False | False |
| ACCUMULATION | 1 | 0 | 0 | 0 | 0 | False | False |
| ACCUMULATION | 2 | 2 | 2 | 55 | 55 | False | False |
| ACCUMULATION | 3 | 2 | 2 | 149 | 149 | False | True |
| UPTREND | 0 | 4 | 4 | 108 | 108 | True | True |
| UPTREND | 1 | 3 | 3 | 61 | 56 | True | False |
| UPTREND | 2 | 2 | 2 | 282 | 287 | False | True |
| UPTREND | 3 | 3 | 3 | 160 | 160 | True | True |
| DISTRIBUTION | 0 | 1 | 1 | 272 | 81 | False | True |
| DISTRIBUTION | 1 | 0 | 0 | 0 | 191 | False | False |
| DISTRIBUTION | 2 | 0 | 0 | 0 | 0 | False | False |
| DISTRIBUTION | 3 | 0 | 0 | 0 | 0 | False | False |
| DOWNTREND | 0 | 4 | 4 | 304 | 304 | True | True |
| DOWNTREND | 1 | 2 | 2 | 252 | 252 | False | True |
| DOWNTREND | 2 | 4 | 4 | 264 | 157 | True | True |
| DOWNTREND | 3 | 4 | 4 | 83 | 190 | True | False |

- Fold-boundary reconciliation: 3 episode(s) straddle a fold boundary (UPTREND:[17], DISTRIBUTION:[272], DOWNTREND:[182]); each is counted wholly to its start fold, so per-fold eligible decisions can exceed the bars physically inside the fold (see bars_in_own_fold).

## SPY_D1

- Rebuild verified vs V2 (switches 34 == 34, n_decisions 2751, effUNKNOWN share 0.2908); vs A1 saved runtime rows: **MATCH**.
- Cross-check vs A1 preliminary feasibility: MATCH (94 fields compared).
- Decisions (post-warmup, evaluable): 2751; transitions: 34 per fold f0=11, f1=7, f2=10, f3=6, no_fold=0; bars outside all fold spans: 2.
- TRANSITION_UNKNOWN (unselectable, UNK_FLAT fixed): 14 bars in 1 episode(s) (share 0.0051); floors not applied.

| regime | episodes | elig.ep. | elig.dec. | mkt bars (share) | dur min/p25/med/p75/max | margin | verdict |
|---|---|---|---|---|---|---|---|
| ACCUMULATION | 1 | 1 | 9 | 9 (0.003) | 9/9/9/9/9 | 0.000 | **NOT_RUN_THIN_REGIME** |
| UPTREND | 17 | 17 | 1918 | 1918 (0.697) | 13/23/106/171/412 | 0.850 | **NOT_RUN_THIN_REGIME** |
| DISTRIBUTION | 1 | 1 | 95 | 95 (0.035) | 95/95/95/95/95 | 0.000 | **NOT_RUN_THIN_REGIME** |
| DOWNTREND | 15 | 15 | 715 | 715 (0.260) | 11/17/34/59/215 | 0.750 | **NOT_RUN_THIN_REGIME** |

### Per-fold detail

| regime | fold | episodes | elig.ep. | elig.dec. | bars_in_own_fold | eps floor ok | dec floor ok |
|---|---|---|---|---|---|---|---|
| ACCUMULATION | 0 | 1 | 1 | 9 | 9 | False | False |
| ACCUMULATION | 1 | 0 | 0 | 0 | 0 | False | False |
| ACCUMULATION | 2 | 0 | 0 | 0 | 0 | False | False |
| ACCUMULATION | 3 | 0 | 0 | 0 | 0 | False | False |
| UPTREND | 0 | 5 | 5 | 422 | 422 | True | True |
| UPTREND | 1 | 4 | 4 | 644 | 434 | True | True |
| UPTREND | 2 | 5 | 5 | 408 | 460 | True | True |
| UPTREND | 3 | 3 | 3 | 444 | 601 | True | True |
| DISTRIBUTION | 0 | 1 | 1 | 95 | 95 | False | False |
| DISTRIBUTION | 1 | 0 | 0 | 0 | 0 | False | False |
| DISTRIBUTION | 2 | 0 | 0 | 0 | 0 | False | False |
| DISTRIBUTION | 3 | 0 | 0 | 0 | 0 | False | False |
| DOWNTREND | 0 | 4 | 4 | 297 | 147 | True | True |
| DOWNTREND | 1 | 3 | 3 | 104 | 253 | True | True |
| DOWNTREND | 2 | 5 | 5 | 228 | 228 | True | True |
| DOWNTREND | 3 | 3 | 3 | 86 | 86 | True | False |

- Fold-boundary reconciliation: 4 episode(s) straddle a fold boundary (UPTREND:[412, 180, 106], DOWNTREND:[215]); each is counted wholly to its start fold, so per-fold eligible decisions can exceed the bars physically inside the fold (see bars_in_own_fold).

- 2 timeline bar(s) fall outside every frozen fold span (SPY date-span convention at fold edges); they count toward market time of their episode's start fold when inside an eligible episode, and no episode STARTs in no-fold.

## Verdict summary — which regime x cell slots pass

| cell | regime | verdict | margin |
|---|---|---|---|
| BTC_H1 | ACCUMULATION | PASS | 1.150 |
| BTC_H1 | UPTREND | PASS | 1.400 |
| BTC_H1 | DISTRIBUTION | NOT_RUN_THIN_REGIME | 0.000 |
| BTC_H1 | DOWNTREND | PASS | 1.700 |
| BTC_H4 | ACCUMULATION | NOT_RUN_THIN_REGIME | 0.000 |
| BTC_H4 | UPTREND | NOT_RUN_THIN_REGIME | 0.600 |
| BTC_H4 | DISTRIBUTION | NOT_RUN_THIN_REGIME | 0.000 |
| BTC_H4 | DOWNTREND | NOT_RUN_THIN_REGIME | 0.667 |
| SPY_D1 | ACCUMULATION | NOT_RUN_THIN_REGIME | 0.000 |
| SPY_D1 | UPTREND | NOT_RUN_THIN_REGIME | 0.850 |
| SPY_D1 | DISTRIBUTION | NOT_RUN_THIN_REGIME | 0.000 |
| SPY_D1 | DOWNTREND | NOT_RUN_THIN_REGIME | 0.750 |

- PASS (all floors met): BTC_H1/ACCUMULATION, BTC_H1/UPTREND, BTC_H1/DOWNTREND.
- NOT_RUN_THIN_REGIME (below a sample floor; specialist defaults FLAT there): BTC_H1/DISTRIBUTION, BTC_H4/ACCUMULATION, BTC_H4/UPTREND, BTC_H4/DISTRIBUTION, BTC_H4/DOWNTREND, SPY_D1/ACCUMULATION, SPY_D1/UPTREND, SPY_D1/DISTRIBUTION, SPY_D1/DOWNTREND.

Binding laws honored: no PnL read or computed; no runtime/scored* input; BTC_H1 / BTC_H4 / SPY_D1 never pooled; feasibility.py untouched.
