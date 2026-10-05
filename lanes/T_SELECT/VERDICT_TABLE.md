# VERDICT_TABLE — Lane T_SELECT, cycle NFL-WINPROB-NG-SCORED-V1

Written 2026-10-05T10:17:28Z. Verdicts: PASS / FAIL / NOT_RUN (missing evidence is NOT_RUN, never inferred PASS).

| # | check | verdict | evidence |
|---|---|---|---|
| 1 | Load filters + assertions (SEASON_MAX_GAMES=2018 / SEASON_MAX_PBP=2017; no 2019+ rows) | PASS | arms.py constants; run-time asserts; 2491 rows dropped at load |
| 2 | Designed-null equivalence vs B1* bit-for-bit (inner-eval stream) | PASS | max abs Δp all = 0.0 exactly; C3 θ=0 replay bit-identical |
| 3 | Per-fold warm/eval slice equivalence (5 folds) | PASS | {"2014": true, "2015": true, "2016": true, "2017": true, "2018": true} |
| 4 | Selftest fixtures | PASS | select.py --selftest exit 0 (hand-computed arithmetic) |
| 5 | Lock FREE_PROVEN before run | PASS | 2026-10-05T10:17:17Z |
| 6 | Lock observation after run | PASS | recorded in report §1 |
| 7 | Grid completeness (5+12+5+3 + nulls, all in ledger) | PASS | SELECTION_LEDGER.jsonl rows |
| 8 | Negative controls executed per candidate | PASS | 6 control runs; winning: 1 |
| 9 | Gates applied (G-SELECT/G-ENTRY per candidate; G-INT for C4) | PASS | dispositions: {'C1': 'KILL', 'C2': 'KILL', 'C3': 'FIELD', 'C4': 'RELEASE'} |
| 10 | Boundary compliance (no 2019+ reads, no real-game rows, no ledger writes, no git, calibration vocabulary) | PASS | report §9 |
| 11 | B0 constant emitted (TRAIN REG non-tie home-win rate) | PASS | report §3 |

Arm-level verdicts:

| arm | G-SELECT | gate | disposition |
|---|---|---|---|
| C1 | PASS | FAIL | **KILL** |
| C2 | PASS | FAIL | **KILL** |
| C3 | PASS | PASS | **FIELD** |
| C4 | PASS | FAIL | **RELEASE** |
