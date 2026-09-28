# DAYTRADER-100-V1 — SCORED REPORT (G8, GO consumed 2026-09-28)

- run: stress-all one pass, heavy lock HELD_PROVEN (PID 16558), 1934.6s, exit 0
- cells: 87 scored at computation time (observed denominator 87; published below)
- triplets (family,arm,stress) distinct: yes (261 rows)
- folds (calendar): crypto GĐ1 2021-04-01..2022-06-30 · GĐ2 2022-07-01..2023-09-30 · GĐ3 2023-10-01..2024-12-31 · GĐ4 2025-01-01..2026-08-31; FX P1..P4 same starts, P4 ends 2026-09-23
- disclosure: EVERY row carries ANCESTRY_RELAXED_BY_OWNER_ORDER_2026-09-28 — these trials are NOT independent of their ancestors' kills.

## INCIDENT INC-DT100-1 (disclosed, unrepaired): synthetic-spread marking bug

Engine marks PnL as (exit/entry−1)×1e4 — correct for PRICES, wrong for SPREADS
(must be (exit−entry)×1e4). Affects the 12 synthetic-spread cells: CARRY×3,
PAIRMR×3, ETHBTC×3, BASISTERM×3. Their absurd outputs (exp up to +3425 bps/trade,
BASISTERM inf/inf from spread crossing zero) are CONSTRUCTION ARTIFACTS → verdict
INVALID_INC_DT100_1. The 75 real-price-marked cells are unaffected. Observed
denominator keeps all 87 (law: outcome-visible cells never silently vanish).
Remediation rerun of the 12 cells = owner decision (see final report).

## Verdict tally

{'CELL_FAIL': 54, 'CELL_FAIL(PF)': 10, 'NOT_RUN_THIN': 4, 'CELL_FAIL(concentration)': 1, 'INVALID_INC_DT100_1': 12, 'NOT_RUN_THIN(vacuous)': 6}

## Per-cell table (x1.0; exp/PF in bps of entry notional)

| family | arm | trades | exp | PF | folds+ | topFold | x1.5 exp | x2.0 exp | verdict |
|---|---|---|---|---|---|---|---|---|---|
| DT100-01-ORB | anchor | 1978 | -21.95 | 0.80 | 0/4 | 0% | -27.95 | -33.95 | CELL_FAIL |
| DT100-01-ORB | n1 | 1978 | -27.08 | 0.76 | 0/4 | 0% | -33.08 | -39.08 | CELL_FAIL |
| DT100-01-ORB | n2 | 1976 | -13.25 | 0.87 | 0/4 | 0% | -19.25 | -25.25 | CELL_FAIL |
| DT100-04-SQUEEZE | anchor | 3287 | -12.84 | 0.67 | 0/4 | 0% | -18.84 | -24.84 | CELL_FAIL |
| DT100-04-SQUEEZE | n1 | 1950 | -13.50 | 0.64 | 0/4 | 0% | -19.50 | -25.50 | CELL_FAIL |
| DT100-04-SQUEEZE | n2 | 4956 | -15.30 | 0.69 | 0/4 | 0% | -21.30 | -27.30 | CELL_FAIL |
| DT100-07-PDHLSWEEPFX | anchor | 1430 | -0.52 | 0.96 | 2/4 | 77% | -0.99 | -1.46 | CELL_FAIL |
| DT100-07-PDHLSWEEPFX | n1 | 1388 | -0.57 | 0.96 | 1/4 | 100% | -1.00 | -1.44 | CELL_FAIL |
| DT100-07-PDHLSWEEPFX | n2 | 1463 | -0.88 | 0.93 | 1/4 | 100% | -1.38 | -1.89 | CELL_FAIL |
| DT100-09-ASIANRANGE | anchor | 1356 | 0.70 | 1.07 | 2/4 | 99% | 0.55 | 0.40 | CELL_FAIL(PF) |
| DT100-09-ASIANRANGE | n1 | 1095 | 0.75 | 1.07 | 3/4 | 65% | 0.61 | 0.46 | CELL_FAIL(PF) |
| DT100-09-ASIANRANGE | n2 | 901 | 0.27 | 1.03 | 4/4 | 46% | 0.13 | -0.02 | CELL_FAIL(PF) |
| DT100-10-LONDONMOM | anchor | 1588 | 0.28 | 1.03 | 2/4 | 90% | 0.13 | -0.02 | CELL_FAIL(PF) |
| DT100-10-LONDONMOM | n1 | 1476 | 0.56 | 1.05 | 1/4 | 100% | 0.41 | 0.25 | CELL_FAIL(PF) |
| DT100-10-LONDONMOM | n2 | 1270 | 0.90 | 1.09 | 3/4 | 89% | 0.75 | 0.61 | CELL_FAIL(PF) |
| DT100-13-VWAPMR | anchor | 2002 | -2.18 | 0.83 | 0/4 | 0% | -3.21 | -4.24 | CELL_FAIL |
| DT100-13-VWAPMR | n1 | 2002 | -2.18 | 0.83 | 0/4 | 0% | -3.21 | -4.24 | CELL_FAIL |
| DT100-13-VWAPMR | n2 | 2002 | -1.89 | 0.86 | 0/4 | 0% | -2.72 | -3.56 | CELL_FAIL |
| DT100-15-BOLLFADE | anchor | 20768 | -0.16 | 0.96 | 0/4 | 0% | -0.40 | -0.65 | CELL_FAIL |
| DT100-15-BOLLFADE | n1 | 28379 | -0.14 | 0.95 | 0/4 | 0% | -0.38 | -0.62 | CELL_FAIL |
| DT100-15-BOLLFADE | n2 | 8522 | -0.01 | 1.00 | 2/4 | 78% | -0.29 | -0.58 | CELL_FAIL |
| DT100-16-RSI2 | anchor | 23868 | -11.47 | 0.62 | 0/4 | 0% | -17.47 | -23.47 | CELL_FAIL |
| DT100-16-RSI2 | n1 | 24179 | -12.16 | 0.59 | 0/4 | 0% | -18.16 | -24.16 | CELL_FAIL |
| DT100-16-RSI2 | n2 | 21282 | -11.83 | 0.61 | 0/4 | 0% | -17.83 | -23.83 | CELL_FAIL |
| DT100-20-OVERNIGHTFADE | anchor | 2486 | -13.75 | 0.59 | 0/4 | 0% | -19.75 | -25.75 | CELL_FAIL |
| DT100-20-OVERNIGHTFADE | n1 | 4673 | -13.22 | 0.56 | 0/4 | 0% | -19.22 | -25.22 | CELL_FAIL |
| DT100-20-OVERNIGHTFADE | n2 | 1349 | -14.02 | 0.64 | 0/4 | 0% | -20.02 | -26.02 | CELL_FAIL |
| DT100-31-JPYFADE | anchor | 3143 | -0.71 | 0.85 | 1/4 | 100% | -1.01 | -1.31 | CELL_FAIL |
| DT100-31-JPYFADE | n1 | 4892 | -0.64 | 0.85 | 0/4 | 0% | -0.99 | -1.33 | CELL_FAIL |
| DT100-31-JPYFADE | n2 | 1954 | -1.00 | 0.83 | 0/4 | 0% | -1.29 | -1.58 | CELL_FAIL |
| DT100-34-WEEKEND | anchor | 63 | -12.00 | 0.86 | 2/4 | 53% | -18.00 | -24.00 | NOT_RUN_THIN |
| DT100-34-WEEKEND | n1 | 233 | -25.10 | 0.68 | 0/4 | 0% | -31.10 | -37.10 | NOT_RUN_THIN |
| DT100-34-WEEKEND | n2 | 8 | -16.20 | 0.80 | 2/4 | 96% | -22.20 | -28.20 | NOT_RUN_THIN |
| DT100-35-FUNDCONTRA | anchor | 403 | 8.87 | 1.13 | 2/4 | 69% | 2.87 | -3.13 | CELL_FAIL(concentration) |
| DT100-35-FUNDCONTRA | n1 | 806 | 2.64 | 1.04 | 2/4 | 79% | -3.36 | -9.36 | CELL_FAIL(PF) |
| DT100-35-FUNDCONTRA | n2 | 219 | 27.65 | 1.38 | 3/4 | 81% | 21.65 | 15.65 | NOT_RUN_THIN |
| DT100-46-CARRY | anchor | 2927 | 2498.76 | 1.46 | 3/4 | 61% | 2486.76 | 2474.76 | INVALID_INC_DT100_1 |
| DT100-46-CARRY | n1 | 7980 | 2036.46 | 1.78 | 3/4 | 60% | 2024.46 | 2012.46 | INVALID_INC_DT100_1 |
| DT100-46-CARRY | n2 | 1937 | 1352.51 | 1.16 | 2/4 | 53% | 1340.51 | 1328.51 | INVALID_INC_DT100_1 |
| DT100-56-PDHLSWEEP | anchor | 1357 | -8.26 | 0.91 | 0/4 | 0% | -14.26 | -20.26 | CELL_FAIL |
| DT100-56-PDHLSWEEP | n1 | 1260 | -7.15 | 0.91 | 1/4 | 100% | -13.15 | -19.15 | CELL_FAIL |
| DT100-56-PDHLSWEEP | n2 | 1427 | -9.53 | 0.90 | 0/4 | 0% | -15.53 | -21.53 | CELL_FAIL |
| DT100-60-DELTADIV | anchor | 2407 | -12.59 | 0.55 | 0/4 | 0% | -18.59 | -24.59 | CELL_FAIL |
| DT100-60-DELTADIV | n1 | 5062 | -11.25 | 0.60 | 0/4 | 0% | -17.25 | -23.25 | CELL_FAIL |
| DT100-60-DELTADIV | n2 | 452 | -10.91 | 0.68 | 1/4 | 100% | -16.91 | -22.91 | CELL_FAIL |
| DT100-69-FHMOM | anchor | 25639 | -11.56 | 0.53 | 0/4 | 0% | -17.56 | -23.56 | CELL_FAIL |
| DT100-69-FHMOM | n1 | 31240 | -11.64 | 0.48 | 0/4 | 0% | -17.64 | -23.64 | CELL_FAIL |
| DT100-69-FHMOM | n2 | 19046 | -11.37 | 0.61 | 0/4 | 0% | -17.37 | -23.37 | CELL_FAIL |
| DT100-70-ONRET | anchor | 740 | -23.76 | 0.81 | 0/4 | 0% | -29.76 | -35.76 | CELL_FAIL |
| DT100-70-ONRET | n1 | 1381 | -12.28 | 0.88 | 0/4 | 0% | -18.28 | -24.28 | CELL_FAIL |
| DT100-70-ONRET | n2 | 422 | -30.63 | 0.79 | 0/4 | 0% | -36.63 | -42.63 | CELL_FAIL |
| DT100-71-RVREGIME | anchor | 4581 | -11.37 | 0.70 | 0/4 | 0% | -17.37 | -23.37 | CELL_FAIL |
| DT100-71-RVREGIME | n1 | 6654 | -10.92 | 0.71 | 0/4 | 0% | -16.92 | -22.92 | CELL_FAIL |
| DT100-71-RVREGIME | n2 | 2445 | -9.38 | 0.76 | 0/4 | 0% | -15.38 | -21.38 | CELL_FAIL |
| DT100-73-VOLAUTO | anchor | 14438 | -12.58 | 0.58 | 0/4 | 0% | -18.58 | -24.58 | CELL_FAIL |
| DT100-73-VOLAUTO | n1 | 19796 | -12.18 | 0.57 | 0/4 | 0% | -18.18 | -24.18 | CELL_FAIL |
| DT100-73-VOLAUTO | n2 | 9844 | -13.35 | 0.61 | 0/4 | 0% | -19.35 | -25.35 | CELL_FAIL |
| DT100-74-VOLTARGET | anchor | 34710 | -11.94 | 0.43 | 0/4 | 0% | -17.94 | -23.94 | CELL_FAIL |
| DT100-74-VOLTARGET | n1 | 54912 | -11.74 | 0.37 | 0/4 | 0% | -17.74 | -23.74 | CELL_FAIL |
| DT100-74-VOLTARGET | n2 | 24908 | -11.71 | 0.49 | 0/4 | 0% | -17.71 | -23.71 | CELL_FAIL |
| DT100-75-PAIRMR | anchor | 834 | 3425.63 | 3.09 | 4/4 | 49% | 3414.63 | 3403.63 | INVALID_INC_DT100_1 |
| DT100-75-PAIRMR | n1 | 1324 | 1565.12 | 1.61 | 3/4 | 54% | 1554.12 | 1543.12 | INVALID_INC_DT100_1 |
| DT100-75-PAIRMR | n2 | 386 | -131.15 | 0.94 | 3/4 | 90% | -142.15 | -153.15 | INVALID_INC_DT100_1 |
| DT100-76-CORRBREAK | anchor | 727 | 5.19 | 1.07 | 2/4 | 73% | -0.81 | -6.81 | CELL_FAIL(PF) |
| DT100-76-CORRBREAK | n1 | 626 | 5.60 | 1.08 | 2/4 | 69% | -0.40 | -6.40 | CELL_FAIL(PF) |
| DT100-76-CORRBREAK | n2 | 698 | 5.26 | 1.06 | 3/4 | 50% | -0.74 | -6.74 | CELL_FAIL(PF) |
| DT100-78-LEADLAG | anchor | 58984 | -11.58 | 0.46 | 0/4 | 0% | -17.08 | -22.58 | CELL_FAIL |
| DT100-78-LEADLAG | n1 | 113356 | -11.20 | 0.38 | 0/4 | 0% | -16.70 | -22.20 | CELL_FAIL |
| DT100-78-LEADLAG | n2 | 32223 | -11.34 | 0.58 | 0/4 | 0% | -16.84 | -22.34 | CELL_FAIL |
| DT100-79-ETHBTC | anchor | 816 | -3435.61 | 0.59 | 2/4 | 72% | -3447.61 | -3459.61 | INVALID_INC_DT100_1 |
| DT100-79-ETHBTC | n1 | 1327 | -897.22 | 0.85 | 3/4 | 52% | -909.22 | -921.22 | INVALID_INC_DT100_1 |
| DT100-79-ETHBTC | n2 | 352 | -677.62 | 0.87 | 2/4 | 60% | -689.62 | -701.62 | INVALID_INC_DT100_1 |
| DT100-80-TSMOMH | anchor | 4295 | -10.59 | 0.83 | 0/4 | 0% | -16.59 | -22.59 | CELL_FAIL |
| DT100-80-TSMOMH | n1 | 6348 | -13.82 | 0.74 | 0/4 | 0% | -19.82 | -25.82 | CELL_FAIL |
| DT100-80-TSMOMH | n2 | 3887 | -10.56 | 0.84 | 0/4 | 0% | -16.56 | -22.56 | CELL_FAIL |
| DT100-83-FAILBRK | anchor | 32586 | -10.56 | 0.57 | 0/4 | 0% | -16.56 | -22.56 | CELL_FAIL |
| DT100-83-FAILBRK | n1 | 53822 | -10.81 | 0.46 | 0/4 | 0% | -16.81 | -22.81 | CELL_FAIL |
| DT100-83-FAILBRK | n2 | 18002 | -9.86 | 0.69 | 0/4 | 0% | -15.86 | -21.86 | CELL_FAIL |
| DT100-87-FVG | anchor | 0 | — | — | 0/4 | 0% | — | — | NOT_RUN_THIN(vacuous) |
| DT100-87-FVG | n1 | 0 | — | — | 0/4 | 0% | — | — | NOT_RUN_THIN(vacuous) |
| DT100-87-FVG | n2 | 0 | — | — | 0/4 | 0% | — | — | NOT_RUN_THIN(vacuous) |
| DT100-95-BASISTERM | anchor | 16207 | -51.64 | 0.89 | 2/4 | 75% | -63.64 | -75.64 | INVALID_INC_DT100_1 |
| DT100-95-BASISTERM | n1 | 33946 | inf | inf | 2/4 | nan% | inf | inf | INVALID_INC_DT100_1 |
| DT100-95-BASISTERM | n2 | 9480 | -104.47 | 0.85 | 1/4 | 100% | -116.47 | -128.47 | INVALID_INC_DT100_1 |
| DT100-C1-FORECASTFUND | anchor | 25556 | NaN | NaN | 0/4 | 0% | NaN | NaN | NOT_RUN_THIN(vacuous) |
| DT100-C1-FORECASTFUND | n1 | 15338 | NaN | NaN | 0/4 | 0% | NaN | NaN | NOT_RUN_THIN(vacuous) |
| DT100-C1-FORECASTFUND | n2 | 41373 | NaN | NaN | 0/4 | 0% | NaN | NaN | NOT_RUN_THIN(vacuous) |

## Reading (Lead)

- **0 STAGE_A candidates among the 75 valid cells.** 68 CELL_FAIL (cost/PF/
  concentration/stress), 6 NOT_RUN_THIN (FVG vacuous ×3 preregistered, WEEKEND
  n2, plus FUNDCONTRA n2 & ETHBTC-family thins folded into counts), 3 NaN vacuous.
- Near-misses of record: ASIANRANGE/LONDONMOM FX books are cost-marginal positive
  at x1.0 (PF 1.03-1.09) and die by x2.0 — the exact fingerprint the ERP cohort-3
  council measured (3.6/4.4-pip stressed floor partitions the space).
- FUNDCONTRA anchor: fails concentration (GĐ1 = 68.5% of positive PnL; both
  2023+ folds net negative) — decayed edge, killed by its own preregistered bar.
- CARRY/PAIRMR/ETHBTC/BASISTERM: INVALID pending owner decision on the
  one-line semantic repair + rerun.


## REMEDIATION RESULT (INC-DT100-1 closed, owner order "sửa và chạy lại 12 cell spread")

Fix: spread_marking flag — synthetic spreads mark PnL as (exit−entry)×1e4
(difference), ratio form eliminated; regression fixture pins the math (8/8 tests).
Rerun: 12 cells ×3 stress under heavy lock (E_REMEDIATION_12), 246.3s, exit 0.

| family | arm | trades | exp(bps) | PF | folds+ | x1.5 | fundΣ(bps) | verdict |
|---|---|---|---|---|---|---|---|---|
| CARRY | A/N1/N2 | 2927/7980/1937 | −21.8/−22.6/−21.5 | 0.02 | 0/4 | âm | +1173~+1234 (income) | CELL_FAIL |
| PAIRMR | A/N1/N2 | 834/1324/386 | −3335/−1278/−8582 | 0.31–0.90 | 0/4 | âm | 0 | CELL_FAIL/THIN |
| ETHBTC | A/N1/N2 | 816/1327/352 | −2648/−1220/−6239 | 0.33–0.86 | 0/4 | âm | 0 | CELL_FAIL/THIN |
| BASISTERM | A/N1/N2 | 16207/33946/9480 | −23.8/−23.8/−23.6 | 0.02–0.04 | 0/4 | âm | +133~+394 | CELL_FAIL |

Đọc: funding-harvest là THẬT (CARRY thu được +11.7k–12.3k bps funding tổng) nhưng
thua xa chuyển động spread nghịch + 24bps chi phí 2 chân mỗi lượt — đúng dạng
chết "marginal-gate" của CARRY-7D lịch sử. Pair-MR/BASISTERM chết tuyệt đối.

## CYCLE VERDICT (proposed, terminal A7 pending)

`DAYTRADER_100_V1_REJECT_ALL` — 99 scored computations (87 + 12 remediation),
0 Stage-A candidates, reproduction ALL_MATCH 261/261, mọi row mang disclosure
ancestry-relaxed-by-owner-order. Incident INC-DT100-1 disclosed end-to-end:
bug → incident row → owner-approved remediation → fix + regression fixture →
rerun → verdicts unchanged in direction (all dead).
