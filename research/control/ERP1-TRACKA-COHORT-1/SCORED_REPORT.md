# SCORED REPORT — ERP1-TRACKA-COHORT-1 (tracka1-scored, GO-2)

Generated: 2026-09-25T23:55:17+00:00. Authority: freeze/GO1_freeze_artifact.json (+ erratum E1); plan 9.1-9.4, 10, 4.2; GO-2 record EXACT match.
First PnL-bearing execution of the cycle. Dry-run evidence was committed BEFORE any scored computation (scored_dryrun.json).

## Pair AUDUSD

### R-ANCHOR dev gates (k=1.0 book; RT dev union = 923)

| gate | verdict | margin to fail | detail |
|---|---|---|---|
| G1_net_gt0_k1.0 | PASS | 323.3 | {"net_pips": 323.3, "threshold": 0} |
| G2_pf_ge_1.20 | FAIL | -0.1666 | {"pf": 1.0334, "threshold": 1.2} |
| G3_pos_folds_ge_4of6 | FAIL | -1 | {"positive_folds": 3, "of": 6, "per_fold": {"F1": -5.6, "F2": -62.3, "F3": 350.4, "F4": 3.2, "F5": -391.2, "F6": 428.8}} |
| G4_net_gt0_k1.5 | FAIL | -652.35 | {"net_pips": -652.35, "threshold": 0} |
| G5_rt_ge_100_and_months_ge_6 | PASS | {'rt_margin': 823, 'months_margin': 52} | {"rt": 923, "months": 58, "rt_threshold": 100, "months_threshold": 6} |
| G6_top_fold_share | PASS | 0.457136 | {"share": 0.042864, "threshold": 0.5, "k2.0_share": 0.014149, "argmax": "F6"} |
| G7_top5_trades_share | PASS | 0.429437 | {"share": 0.070563, "threshold": 0.5, "k2.0_share": 0.07687, "argmax": null} |
| G8_top_hour_share | PASS | 0.009117 | {"share": 0.490883, "threshold": 0.5, "k2.0_share": 0.496366, "argmax": 8} |

Anchor net @k: 1.0=323.3 pips (923 RT), 1.5=-652.35 pips (923 RT), 2.0=-1628.0 pips (923 RT)

### Seam law (per pair, k=1.0)

- S = net(R-ORIG) - net(R-ANCHOR) = 3207.4 - 323.3 = **2884.1 pips**; c_rt frozen = 2.0 pips (recomputed {'R-ORIG': 2.0, 'R-ANCHOR': 2.0})
- limb (i): S > 10*c_rt = 20.0 -> **FIRES**
- limb (ii): S > 3*c_rt = 6.0 AND S>0 on >=4/6 folds (S>0 folds = 4) -> **FIRES**
- limb (iii): matched pairs 337 (>= 20 floor); mean R-ORIG-matched 2.4733 vs mean R-ANCHOR-matched -5.5718; delta 8.0451 vs 1*c_rt = 2.0 -> **FIRES** (unmatched excluded: 29 orig / 25 anchor)
- seam verdict: **KILL_PIT_SEAM**; per-fold S: {'F1': 499.3, 'F2': 1520.1, 'F3': -362.2, 'F4': 515.7, 'F5': 774.8, 'F6': -63.6}

### Kill laws (per pair, k=1.0)

- KILL_INVERSION: inverted net -2274.6 vs anchor 323.3 -> overall limb no; shadow-folds limb FIRES {'F5': {'anchor': -391.2, 'inverted': 92.1}} => **KILL_INVERSION**
- KILL_CONTROL_REPRODUCED: placebo net -2207.3 vs 0.5*anchor 161.65 -> band limb no; fold-residue limb (placebo folds>0 = 1/6, anchor < 2x placebo) no => **NO_KILL_CONTROL**
- KILL_BETA_EXPLAINED: beta-matched book = SHORT_ALWAYS net -18.2; anchor - beta = 341.5; always-on books {'SHORT_ALWAYS': -18.2, 'LONG_ALWAYS': -2684.2} => **NO_KILL_BETA**

Placebo rider (net per occupied entry-hour): anchor 24.8692 pips/hour over 13 hours; placebo -157.6643 pips/hour over 14 hours

### All-arm dev summary (k=1.0 net pips | RT | PF | G-gates)

| arm | net@1.0 | net@1.5 | RT | PF | G1-G8 |
|---|---|---|---|---|---|
| R-ANCHOR (view R-ANCHOR) | 323.3 | -652.35 | 923 | 1.0334 | G1:P G2:F G3:F G4:F G5:P G6:P G7:P G8:P |
| R-ORIG (view R-ORIG) | 3207.4 | 2232.5 | 927 | 1.3804 | G1:P G2:P G3:P G4:P G5:P G6:P G7:P G8:P |
| R-NEIGH (view R-NEIGH) | 497.5 | -477.75 | 923 | 1.0521 | G1:P G2:F G3:F G4:F G5:P G6:P G7:P G8:P |
| CAUSAL-PLACEBO (view CAUSAL-PLACEBO) | -2207.3 | -3453.75 | 1185 | 0.8087 | G1:F G2:F G3:F G4:F G5:P G6:P G7:P G8:P |
| INVERTED (view INVERTED) | -2274.6 | -3250.25 | 923 | 0.7941 | G1:F G2:F G3:F G4:F G5:P G6:P G7:P G8:P |
| BASELINE-SET (view SHORT_ALWAYS) | -18.2 | -1369.4 | 1276 | 0.9989 | G1:F G2:F G3:F G4:F G5:P G6:P G7:P G8:F |

### Holdout (one-look law)

- **HOLDOUT_UNREAD_CONSUMED_BY_NONE** — R-ANCHOR dev status KILLED_AT_DEV (KILL_PIT_SEAM) - a dead arm takes no holdout look (plan 9.1)

### Terminal verdict — R-ANCHOR AUDUSD: **KILL_PIT_SEAM**

## Pair USDCAD

### R-ANCHOR dev gates (k=1.0 book; RT dev union = 962)

| gate | verdict | margin to fail | detail |
|---|---|---|---|
| G1_net_gt0_k1.0 | PASS | 681.0 | {"net_pips": 681.0, "threshold": 0} |
| G2_pf_ge_1.20 | FAIL | -0.1491 | {"pf": 1.0509, "threshold": 1.2} |
| G3_pos_folds_ge_4of6 | FAIL | -1 | {"positive_folds": 3, "of": 6, "per_fold": {"F1": -244.7, "F2": 228.7, "F3": 1007.8, "F4": 564.8, "F5": -365.3, "F6": -510.3}} |
| G4_net_gt0_k1.5 | FAIL | -509.4 | {"net_pips": -509.4, "threshold": 0} |
| G5_rt_ge_100_and_months_ge_6 | PASS | {'rt_margin': 862, 'months_margin': 52} | {"rt": 962, "months": 58, "rt_threshold": 100, "months_threshold": 6} |
| G6_top_fold_share | PASS | 0.428296 | {"share": 0.071704, "threshold": 0.5, "k2.0_share": 0.04022, "argmax": "F3"} |
| G7_top5_trades_share | PASS | 0.43968 | {"share": 0.06032, "threshold": 0.5, "k2.0_share": 0.065129, "argmax": null} |
| G8_top_hour_share | PASS | 0.036659 | {"share": 0.463341, "threshold": 0.5, "k2.0_share": 0.473215, "argmax": 8} |

Anchor net @k: 1.0=681.0 pips (962 RT), 1.5=-509.4 pips (962 RT), 2.0=-1699.8 pips (962 RT)

### Seam law (per pair, k=1.0)

- S = net(R-ORIG) - net(R-ANCHOR) = 5029.6 - 681.0 = **4348.6 pips**; c_rt frozen = 2.4 pips (recomputed {'R-ORIG': 2.4, 'R-ANCHOR': 2.4})
- limb (i): S > 10*c_rt = 24.0 -> **FIRES**
- limb (ii): S > 3*c_rt = 7.2 AND S>0 on >=4/6 folds (S>0 folds = 4) -> **FIRES**
- limb (iii): matched pairs 306 (>= 20 floor); mean R-ORIG-matched 4.1327 vs mean R-ANCHOR-matched -8.8235; delta 12.9562 vs 1*c_rt = 2.4 -> **FIRES** (unmatched excluded: 29 orig / 24 anchor)
- seam verdict: **KILL_PIT_SEAM**; per-fold S: {'F1': 1476.0, 'F2': 1252.4, 'F3': -916.0, 'F4': -21.9, 'F5': 1029.4, 'F6': 1528.7}

### Kill laws (per pair, k=1.0)

- KILL_INVERSION: inverted net -3061.8 vs anchor 681.0 -> overall limb no; shadow-folds limb FIRES {'F1': {'anchor': -244.7, 'inverted': 12.3}, 'F6': {'anchor': -510.3, 'inverted': 103.1}} => **KILL_INVERSION**
- KILL_CONTROL_REPRODUCED: placebo net -978.3 vs 0.5*anchor 340.5 -> band limb no; fold-residue limb (placebo folds>0 = 2/6, anchor < 2x placebo) no => **NO_KILL_CONTROL**
- KILL_BETA_EXPLAINED: beta-matched book = LONG_ALWAYS net -1126.5; anchor - beta = 1807.5; always-on books {'SHORT_ALWAYS': -1995.3, 'LONG_ALWAYS': -1126.5} => **NO_KILL_BETA**

Placebo rider (net per occupied entry-hour): anchor 52.3846 pips/hour over 13 hours; placebo -75.2538 pips/hour over 13 hours

### All-arm dev summary (k=1.0 net pips | RT | PF | G-gates)

| arm | net@1.0 | net@1.5 | RT | PF | G1-G8 |
|---|---|---|---|---|---|
| R-ANCHOR (view R-ANCHOR) | 681.0 | -509.4 | 962 | 1.0509 | G1:P G2:F G3:F G4:F G5:P G6:P G7:P G8:P |
| R-ORIG (view R-ORIG) | 5029.6 | 3838.9 | 967 | 1.428 | G1:P G2:P G3:P G4:P G5:P G6:P G7:P G8:P |
| R-NEIGH (view R-NEIGH) | 1128.6 | -66.2 | 964 | 1.0858 | G1:P G2:F G3:F G4:F G5:P G6:P G7:P G8:P |
| CAUSAL-PLACEBO (view CAUSAL-PLACEBO) | -978.3 | -2405.75 | 1143 | 0.9305 | G1:F G2:F G3:F G4:F G5:P G6:P G7:P G8:P |
| INVERTED (view INVERTED) | -3061.8 | -4252.2 | 962 | 0.8011 | G1:F G2:F G3:F G4:F G5:P G6:P G7:P G8:P |
| BASELINE-SET (view LONG_ALWAYS) | -1126.5 | -2687.4 | 1258 | 0.9495 | G1:F G2:F G3:F G4:F G5:P G6:P G7:P G8:F |

### Holdout (one-look law)

- **HOLDOUT_UNREAD_CONSUMED_BY_NONE** — R-ANCHOR dev status KILLED_AT_DEV (KILL_PIT_SEAM) - a dead arm takes no holdout look (plan 9.1)

### Terminal verdict — R-ANCHOR USDCAD: **KILL_PIT_SEAM**

## DSR (deflated Sharpe, ALL cohort trials)

- DSR per anchor cell, deflated against the SR dispersion of ALL 12 cohort scored cells (FLAT null book contributes SR=0 by convention)
- AUDUSD: DSR = **0.000798** (SR_hat daily = 0.008399, SR0 = 0.082127, N = 12, T = 1826 trading days)
- USDCAD: DSR = **0.001631** (SR_hat daily = 0.013123, SR0 = 0.082127, N = 12, T = 1826 trading days)
- PBO: NOT_RUN_FAIL_CLOSED (6-arm classes = 12 cells but < 8 distinct CONFIG classes for PBO's CSCV; fail-closed per plan 10)

## Cohort-level conclusion

No arm of this cohort reached candidate status under the frozen gates; the cohort closes per the per-pair verdicts above (REJECT/KILL_* as recorded). No replacement enters mid-cohort (plan 9.3).

The decisive finding is the seam attribution, exactly as preregistered in plan 4.2/9.4: the PIT-clean anchor fails G2 (PF 1.033/1.051 vs 1.20), G3 (3/6 positive folds) and G4 (net < 0 at k=1.5) on BOTH pairs, while its one-day-lookahead twin R-ORIG passes ALL EIGHT gates on BOTH pairs (AUDUSD +3207.4 net, PF 1.380, 5/6 folds, +2232.5 @1.5; USDCAD +5029.6, PF 1.428, 5/6 folds, +3838.9 @1.5). All three seam limbs fire on both pairs (S = 2884.1 and 4348.6 pips vs thresholds 20.0/24.0; per-trip matched deltas 8.05/12.96 pips vs 1*c_rt 2.0/2.4 on 337/306 matched pairs): **the apparent range-expansion edge on these pairs was the PIT seam, not economics**. The edge also fails cost stress violently (net flips negative at k=1.5 on both pairs; ~2100/2400 pips of round-trip cost against ~2300/3100 pips gross), the clock-placebo loses money outright (-2207.3/-978.3), and the inverted control wins on folds where the anchor loses (KILL_INVERSION) — the sign carried no mechanism. The one-look holdout windows (2026-01-01..2026-06-30) were consumed by NOBODY and remain unread for any future re-derivation.

## Ledger

- 14 scored rows appended to trial_ledger.jsonl (append-only). Verdict vocabulary: CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION / NOT_POWERED_CANDIDATE / KILL_* / REJECT (+ HOLDOUT_UNREAD_CONSUMED_BY_NONE bookkeeping rows).
- Mandatory labels on every row: SINGLE_SOURCE_PANEL, FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK, PAPER_TIER.
