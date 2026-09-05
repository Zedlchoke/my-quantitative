# FXFV4-A6-P1 family1 — implementation notes (lane I-FAMILY-1)

Mechanical implementation of the SELECTED, FROZEN proposal
`research/proposals/forex_free_v4/d1-a6-proposals/PROPOSAL_FXFV4-A6-P1.json`
(sha256 `e827c904183c13e503441bd252004963027d03c792e7e6ca2c5a7fc65ee7eb0c`)
against the inherited, unmodified V3 kernel architecture
(`research/assets/forex_free_v3/{scored_runner,accounting,family1,exec_driver}.py`,
code hashes pinned in `research/control/forex_free_v3_run/w3_freeze.json`).
No V3 frozen file was touched. No scored/PnL run of any kind was performed;
the test suite uses hand-computed synthetic fixtures only.

## 1. Files

| File | Purpose |
|---|---|
| `research/assets/forex_free_v4/__init__.py` | V4 family package marker |
| `research/assets/forex_free_v4/family1.py` | the frozen mechanism (schedule + financing carrier + margin fields + drop-one helper) |
| `tests/assets/forex_free_v4/__init__.py` | test package marker |
| `tests/assets/forex_free_v4/test_family1.py` | 20 tests, synthetic fixtures only |
| `research/assets/forex_free_v4/FAMILY1_IMPLEMENTATION_NOTES.md` | this file |
| `research/assets/forex_free_v4/AMBIGUITIES.md` | recorded spec ambiguities for A1 |

## 2. Kernel plug-in pattern (mirrors V3 discovery exactly)

The V3 runner is family-agnostic: `scored_runner.register_family(family_id,
module)` accepts any module exposing `run_arm`, and `exec_driver` injects
families as `--family family_id=module.path`. The V4 module is therefore a
plain importable module with the identical entry point:

```
run_arm(arm, data_paths, macro_reader, freeze_token=None)
    -> {"decisions": [...], "financing_events": [...], "meta": {...}}
```

Registration at execution time (no V3 file modified):

```
.venv/bin/python -m research.assets.forex_free_v3.exec_driver \
    --mode dummy --data-paths <paths.json> \
    --family family1=research.assets.forex_free_v4.family1 --report <out.json>
```

`data_paths.price_h1_dir` is the authorized H1 snapshot directory
(`family_api_note` in w3_freeze: family1 reads `price_h1_dir`). The runner
owns ALL booking (`accounting.book_dual`, `book_stress`), validation
(`validate_decisions`: DECISION_CLOCK_VIOLATION / ONE_EVENT_LAG_VIOLATION /
FOLD_FORCE_FLAT_VIOLATION / financing-event matching), gating
(`stage_a_gates`, `mechanism_sanity`), the USD-drift diagnostic, the
incremental-alpha computation and publication. The family produces schedules
and carries financing events; it computes no PnL.

## 3. Packet field -> code map

| Packet field (PROPOSAL_FXFV4-A6-P1.json) | Code |
|---|---|
| `pit_observable.decision_clock` (daily 16:00 America/New_York, DST-aware; "bar stamps 20:00Z in EDT weeks / 21:00Z in EST weeks") | `daily_decision_bars` filters H1 bars whose OPEN instant maps to 16:00 NY wall time on NY weekdays via `zoneinfo` (named zone, never fixed offsets); `decision_ts` carries that 16:00-NY bar instant. The trigger is evaluated at the bar's completion instant from completed closes (see AMBIGUITIES.md item A1-1 on stamp vs completion-instant labeling; fills, prices and PnL are identical under both readings) |
| `mechanism` S_t = mean(r(AUD/USD), r(NZD/USD), −r(USD/CAD)), daily log returns of 16:00-NY completed closes | `TRIGGER_PAIRS`, `TRIGGER_SIGNS = {AUD:+1, NZD:+1, CAD:−1}`; `bloc_signed_returns` = `sign * ln(close_t / close_{t−1})` over consecutive valid days; `trigger_day_series(estimator="mean")` |
| `mechanism` z_t = (S_t − mean(S over the 60 most recent completed NY-days STRICTLY before t)) / std(same 60); event iff z_t <= −1.0 | `STANDARDIZATION_WINDOW_NY_DAYS = 60`; `z_standardize` (window `S[k−60:k]`, decision day never in its own window); `EVENT_THRESHOLD = −1.0`; `event_flags_from_z` (`<=` frozen; `z == −1.0` fires) |
| `warmup` (60 completed valid NY-days; a NY-day is valid only if all of that day's completed H1 bars exist; fail-closed) | `ny_day_valid_map` / `valid_daily_bars`: a NY-day is valid iff its 16:00-NY bar exists AND the pair's bars of that NY-day are gap-free (consecutive 1-hour steps); first evaluable decision = the 62nd valid day (61 prior closes + 60-day window). Per-day bar-count convention: see AMBIGUITIES.md A1-2 |
| `arms.anchor.single_frozen_parameter_set.response_legs` (SHORT AUD/USD, SHORT NZD/USD, LONG USD/CAD, SHORT USD/JPY, SHORT USD/CHF) | `RESPONSE_LEGS = ((AUD/USD,−1),(NZD/USD,−1),(USD/CAD,+1),(USD/JPY,−1),(USD/CHF,−1))` |
| `entry_rules` (next-session 16:00-NY bar open when flat; leg already in a position -> event ignored; governor max 1 position/pair, max 1 entry/pair/NY-day; blocked = NO_TRADE never deferred) | `schedule_legs`: flat-at-decision test `entry_bar_ts <= T < exit_bar_ts`; fills at the OPEN of the first existing 16:00-NY bar strictly after the decision instant; one entry per event day per leg by construction |
| `fill_convention` (>= 1 session, <= 4 calendar days, else fail-closed NO_TRADE; never same-bar, never fill-forward) | `MAX_FILL_LAG_DAYS = 4` in `schedule_legs`: `NO_NEXT_BAR_FOR_ENTRY_FILL` / `ENTRY_FILL_LAG_EXCEEDS_FROZEN_ALLOWANCE` skip records in `meta.skipped_entries`; the V3 validator re-enforces the same bound (ONE_EVENT_LAG_VIOLATION) |
| `exit_rules` (exit at the open of the 16:00-NY bar after the 5th completed NY-day; missing bar -> earliest-scheduled exit; force-flat at fold boundaries, no position crosses) | `HOLDING_NY_DAYS = 5`; `_resolve_exit`: exit bar = entry index + 5 in the leg's existing-bar sequence (exactly 5 completed daily closes in the hold), clamped to the last pre-boundary bar (`force_flat=true`); `force_flat_indices` over `FORCE_FLAT_BOUNDARIES = (2022-05-01, 2024-07-01, 2026-09-02T23:59:59Z)`; an entry whose FILL would land on the flatten bar is suppressed (`ENTRY_FILLS_AT_FOLD_FLATTEN_BAR`) so zero-length round trips are impossible; entries filling after a boundary are scored in the next fold by the runner's `fold_of` |
| `arms.neighbour` (median instead of mean, everything else byte-identical) | `trigger_day_series(estimator="median")` via `_ARM_TRIGGER["neighbour"]`; `meta.bloc_estimator == "median"` |
| `arms.control` (sham majors bloc EUR/USD+GBP/USD, own trailing 60 valid days, same threshold/legs/clocks/holding/costs) | `SHAM_TRIGGER_PAIRS`, `SHAM_TRIGGER_SIGNS`; `_ARM_TRIGGER["causal_negative_control"]`; alias `control` accepted; preregistered non-reproduction rule applied at scoring (`scored_runner.mechanism_sanity`, `CONTROL_REJECT_PF`), not in the family |
| `incremental_test` (anchor law with trigger read on NY-day t−10; identical legs/clocks/holding/fills/costs; gate = anchor minus benchmark financing-adjusted expectancy) | `BENCHMARK_STALENESS_NY_DAYS = 10`; `benchmark_event_flags` (10 VALID NY-days shift); `benchmark_treatment` arm (`FXFV4-A6-P1-bench`); `meta.alpha_definition = "per_trade_expectancy_difference_v1"` = the runner's frozen `ALPHA_EXPECTANCY_DIFFERENCE`, which computes exactly the packet's gate |
| `costs` (1.5 bps/side x {1.0,1.5,2.0} on booked stress PnL; tier 2.0 primary; delay stress separate, unblended) | runner/kernel-owned: `accounting.book_stress` re-books the SAME trade set at 2.25/3.0 bps per side with `STRESS_ROWS_NOT_DISTINCT` certification; the module emits `meta.fill_delay_events = {}` (the kernel's unblended metadata channel; the frozen one-session delay is a separate component, never blended into cost tiers) |
| `dual_book_and_financing` (price-only and financing-adjusted columns; frozen formula; disclosure) | runner/kernel-owned (`book_dual`, digest-covered columns); family emits per-decision `financing_adjustment_usd` = `sign * notional * Σ day-start as-of differential / 365` read ONLY through the injected availability-gated `macro_reader` (`financing_adjustment_usd`; single `/100` conversion; fail-closed BLOCKED_DATA on an unreadable day), formula id `FXFV4_FROZEN_POLICY_RATE_CARRY_ACCRUAL`, disclosure string carried in `meta` |
| `turnover_and_sample_floor.folds_frozen` (2020-03-01, 2022-05-01, 2024-07-01, end 2026-09-02) | `FOLD_BOUNDARIES` mirrors the runner verbatim (selection-freeze directive: fold gates evaluate on POPULATED folds — runner `fold_metrics`/`stage_a_gates` semantics, unchanged) |
| `drop_one_design` (5 leg-drops + inherited best-fold drop; non-vacuity asserted at implementation) | `drop_one_leg_schedule(leg, ...)`: trigger-leg drops remove the pair from S_t (frozen signs kept), response-leg drops remove it from the basket; non-vacuity test `test_drop_one_leg_schedules_are_non_vacuous`. Best-fold drop + the 5-of-6 survival arithmetic are scoring-time (see AMBIGUITIES.md A1-4) |
| `governor` | `schedule_legs` (max 1 position per leg; one decision per NY-day; NO_TRADE records, never deferrals) |
| `universe.authorized_universe` | `PAIRS` (7 pairs); legs always a subset; `"USD"` never a pair (kernel `BAD_PAIR` backstop tested) |

## 4. source_to_test_map -> tests (all in `tests/assets/forex_free_v4/test_family1.py`)

| Packet source_to_test_map row | Test(s) |
|---|---|
| Signed daily return convention incl. −r(USD/CAD); event-day determinism | `test_bloc_signed_returns_sign_convention_golden`; `test_feature_golden_event_basket_and_fills` |
| S_t / z_t goldens; `z == −1.0` fires (<=); warmup shortfall => NO_EVAL | `test_z_standardize_golden_window_excludes_decision_day`; `test_zscore_warmup_no_trigger_before_60_ny_days` |
| Holding-clock goldens; fold force-flat; missing-bar fail-closed | `test_feature_golden_event_basket_and_fills`; `test_force_flat_at_window_end_no_open_positions`; `test_force_flat_internal_fold_boundary_and_entry_suppression` |
| Fill convention: one-event lag, 4-day bound, DST-aware stamps | `test_dst_boundary_clock_and_next_session_fills`; `test_no_lookahead_window_and_future_perturbation` (c) |
| Dual-book separation; price-only sign-inversion refusal | dual-book columns are kernel-owned (V3 `test_accounting.py`); the family-side refusal surface is the runner's `FINANCING_MANUFACTURES_EDGE` gate; the module pins the carrier side in `test_runner_contract_validator_and_registration` (1:1 events, single formula) |
| F1-fixed stress tiers, tier 2.0 primary (inherited remediation regression) | `test_stress_tiers_rebook_at_tiered_costs_and_margins_scale` (kernel `book_stress`: booked net == gross recomputed at 4.5/6.0 USD RT; rows pairwise distinct) |
| Control removes exactly the commodity-bloc ingredient; schedules differ | `test_control_sham_bloc_fires_differently_and_differs_from_anchor` |
| Benchmark schedule identity (+10-NY-day stale trigger) | `test_benchmark_stale_trigger_shifts_events_by_ten_ny_days` |
| Drop-one non-vacuity | `test_drop_one_leg_schedules_are_non_vacuous` |

Task-mandated coverage map (selection-freeze margin machinery + robustness):

| Required test | Test(s) |
|---|---|
| feature golden (trigger value, legs, directions) | `test_bloc_signed_returns_sign_convention_golden`, `test_z_standardize_golden_window_excludes_decision_day`, `test_feature_golden_event_basket_and_fills` |
| one-event/one-bar lag, no-lookahead mutation (fails if the trigger read the decision bar in its window / future data) | `test_no_lookahead_window_and_future_perturbation` |
| DST fall-back + spring-forward weeks (16:00-NY -> 20:00Z/21:00Z; next-session fills) | `test_dst_boundary_clock_and_next_session_fills` |
| force-flat at window end (no open positions after the last bar) | `test_force_flat_at_window_end_no_open_positions` |
| costs once per fill; cash never traded | `test_costs_charged_once_per_fill_and_cash_never_traded` |
| stress tiers re-book (multipliers reach booked PnL); margins scale | `test_stress_tiers_rebook_at_tiered_costs_and_margins_scale` |
| control-arm difference (fails if control == anchor schedule) | `test_control_sham_bloc_fires_differently_and_differs_from_anchor` |
| control runs to completion, fail-closed NO_TRADE on missing bars | `test_control_runs_to_completion_fail_closed_missing_bars` |
| z-score warmup (no trigger before 60 NY-days) | `test_zscore_warmup_no_trigger_before_60_ny_days` |
| malformed/missing data fail-closed (skip + record, never fabricate) | `test_malformed_and_missing_data_fail_closed`, `test_ny_day_validity_gap_free_and_16bar` |
| deterministic (two runs identical) | `test_deterministic_two_runs_identical_records` |
| margin-to-fail record fields | `test_margin_to_fail_fields_hand_computed` |
| neighbour estimator wiring (median-vs-mean) | `test_neighbour_median_estimator_diverges_from_anchor_mean` |
| runner contract + validator + registration discovery | `test_runner_contract_validator_and_registration` |

## 5. Margin-to-fail reporting (selection-freeze directive)

`family1.margin_to_fail(record)` takes a V3-shaped `compute_cell` record and
returns per-gate distance-to-threshold fields. Sign convention (frozen):
positive = distance into the PASSING side, 0 = at-threshold (passing for
`>=` gates, failing for strict `>` gates exactly as `stage_a_gates`
evaluates them), negative = failing, `None` = not evaluable. The eight
directive-required margins: `margin_expectancy_vs_0`, `margin_pf_vs_1_10`,
`margin_fold_positive_share_vs_50pct`, `margin_mdd_vs_ceiling_usd`,
`margin_usd_drift_vs_0_30`, `margin_concentration_vs_40pct`,
`margin_dropout_vs_6_of_8`, `margin_incremental_alpha_vs_0`; plus every
remaining frozen Stage-A gate (price-only sign, decision floor, populated
folds positive, fold PF, stress tier PF/total for tiers 1.5 and 2.0) and
population context. Wiring: the executor attaches
`record["gate_margins"] = family1.margin_to_fail(record)` after
`compute_cell` (one line, runner file untouched); covered by digest when
attached pre-publication.

## 6. Verification performed (this lane)

* `pytest tests/assets/forex_free_v4/test_family1.py -q` -> **20 passed**.
* `pytest tests/assets/forex_free_v3/ -q` -> **95 passed, 2 skipped**; both
  skips are data-dependent ("real snapshot not copied into this worktree",
  gitignored) — the allowed case; no real data was staged. No V3 file
  modified (git diff on V3 paths is empty).
* `compileall` on both new packages: exit 0.
* No scored/PnL run of any kind on real data; no network; no outcome files read.

## 7. Known limitations

* The module is validated against the frozen V3 validator and cost kernel on
  synthetic fixtures; real-snapshot schedule generation (D2/owner-authorized
  dry-run) is the next integration step and is expected to be validator-clean
  by construction (same validator, synthetic-proven).
* `meta.fill_delay_events` is an explicitly empty mapping: the frozen
  one-session delay stress is carried as the kernel's separate unblended
  component with no booked entries in this design (mirrors the V3 family1
  precedent; the kernel books one schedule at tiered costs).
* The sham-bloc control's preregistered non-reproduction rule and the
  incremental-alpha gate are applied at scoring by the runner
  (`mechanism_sanity`, `stage_a_gates`); this module only supplies the
  schedules and carries the benchmark arm.
