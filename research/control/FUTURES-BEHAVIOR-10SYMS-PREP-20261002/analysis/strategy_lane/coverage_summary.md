# Coverage summary — STRATEGY-CONFIGS lane (2026-10-02)

Per-hypothesis data cross-check: `configs/symbols/*.yaml` minimal-test requirements
vs `data/COVERAGE_MANIFEST.json` (data lane, 2026-10-02, read-only).
Verdicts are DATA-AVAILABILITY verdicts for the minimal legal (descriptive) test;
no hypothesis has been run. Scored runs are blocked today for ALL hypotheses
(depth floor >=24m true-volume front chain vs measured 14-17m; declared slippage
missing; exchange fees unfetched except ES; registration required).

| symbol | front-chain real-volume (months) | hypotheses | RUNNABLE_NOW | WAIT_DATA | BLOCKED_NONDATA |
|---|---|---|---|---|---|
| 6A | 14 | 5 | 3 | 1 | 1 |
| 6B | 14 | 5 | 2 | 3 | 0 |
| 6E | 14 | 5 | 1 | 4 | 0 |
| 6J | 14 | 5 | 1 | 4 | 0 |
| CL | 17 | 5 | 1 | 4 | 0 |
| ES | 17 | 5 | 3 | 2 | 0 |
| GC | 16 | 5 | 1 | 3 | 1 |
| NG | 17 | 5 | 2 | 3 | 0 |
| NQ | 17 | 5 | 0 | 5 | 0 |
| SI | 17 | 5 | 2 | 1 | 2 |

**Totals**: 50 hypotheses — 16 RUNNABLE_NOW, 30 WAIT_DATA, 4 BLOCKED_NONDATA (minimal-test level).

## RUNNABLE_NOW hypotheses (minimal descriptive test, data in hand)

- **6A-H1** (rank 1) — descriptive_event_day_gap_distribution; floors unmet: daily_trades_per_contract
- **6A-H3** (rank 2) — construction_rule_check_measured_volumes
- **6A-H5** (rank 4) — descriptive_gap_vs_differential_sign; floors unmet: derived_roll_gaps
- **6B-H5** (rank 1) — descriptive_release_day_gap_distribution; floors unmet: daily_trades_per_contract
- **6B-H1** (rank 2) — descriptive_roll_migration_measurement; floors unmet: daily_trades_per_contract
- **6E-H1** (rank 1) — construction_rule_check_against_measured_ramps
- **6J-H1** (rank 1) — construction_rule_check_measured_volumes
- **CL-H1** (rank 1) — descriptive_conditional_return; floors unmet: daily_trades_per_contract
- **ES-H1** (rank 1) — construction_rule_check_against_measured_ramps
- **ES-H4** (rank 2) — descriptive_event_vs_nonevent_spread_variance; floors unmet: daily_trades_per_contract
- **ES-H5** (rank 3) — descriptive_gap_by_regime; floors unmet: daily_trades_per_contract
- **GC-H3** (rank 2) — descriptive_curve_compression_conditioning; floors unmet: daily_trades_per_contract
- **NG-H5** (rank 1) — execution_constraint_declaration
- **NG-H3** (rank 2) — descriptive_conditional_return; floors unmet: daily_trades_per_contract
- **SI-H1** (rank 1) — construction_rule_check_against_measured_ramps
- **SI-H5** (rank 4) — descriptive_gap_tail_clustering; floors unmet: daily_trades_per_contract

## Top blocking data classes (count of hypotheses waiting)

- external_rates_vintages(US): 6
- consensus_surprise_archive(US): 4
- mof_intervention_archive(JP): 2
- eia_wpsr_vintages(CL): 2
- eia_wngsr_vintages(NG): 2
- weather_forecast_vintages(NG): 2
- hg_copper_daily(HG): 1
- gilt_yields_pit(UK): 1
- uk_fiscal_calendar(UK): 1
- consensus_surprise_archive(UK,US): 1
- ons_calendar_vintages(UK): 1
- full_session_globex_intraday(6B): 1
- external_rates_vintages(US,EU): 1
- minute_trades_m1(6E): 1
- consensus_surprise_archive(US,EU): 1
- full_session_globex_intraday(6E): 1
- external_rates_vintages(US,JP): 1
- boj_statement_archive(JP): 1
- consensus_surprise_archive(CL): 1
- minute_trades_m1(CL): 1
- synchronous_bbo(CL): 1
- daily_trades_per_contract(RB,HO): 1
- spx_dividend_yield(US): 1
- minute_trades_m1(ES): 1
- serial_contracts_refetch(GC): 1
- minute_trades_m1(GC): 1
- consensus_surprise_archive(NG): 1
- minute_trades_m1(NG): 1
- cftc_cot_archive(NQ): 1
- full_session_globex_intraday(NQ): 1
- minute_trades_m1(NQ): 1
- synchronous_bbo(NQ): 1
- lbma_lease_rates(SI): 1

Config-vs-manifest `available_today` disagreements: 0 (recorded as findings in coverage_report.json)

