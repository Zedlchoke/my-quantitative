# V10-I — A8impl spec trace for `A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL`

- **Agent:** A8-impl (wave I implementation role, PLAN §8 I1)
- **Worktree:** `/Users/hoangminhlong/my-quantitative-v10-wt/i-a8-implement`
- **Branch:** `orca/v10-i-a8imp` · base HEAD verified clean `030b183d`
- **Spec authority:** `research/audits/v10/proposals/a8_proposals_v10.{md,json}`
  §3 (M01) as integrated at `77400df`, bound to freeze conditions **C1–C5** of
  `research/control/v10_discovery_run/selection_freeze.json`
- **Module:** `research/hyp_a8_m01.py` · **Tests:** `tests/test_hyp_a8_m01.py`
  (72 passed, synthetic fixtures only)
- **C1 artifact:** `research/audits/v10/i1_c1_field_verification.json` (this
  wave ran the check: verdict **VERIFIED**, all three fields, 20/20 dirs)

---

## 1. Spec sentence → module symbol → test → derivation

| Spec source (a8_proposals §3 unless noted) | Module symbol | Value | Derivation origin | Test |
|---|---|---|---|---|
| Constant table r1 "bars per block" | `BARS_PER_BLOCK` | `96` | 24 h ÷ 15 min exchange grid fact | `test_block_window_is_exclusive_low_inclusive_high`, feature tests |
| Pit convention `ts_event_ns` IS close stamp | `M01Bar.ts_event_ns`, `read_bars_15m` | — | `research/pit_hooks_v10.py` header convention | `test_read_bars_*`, PIT group |
| Recipe step 1 duplicate-close rejection | `read_bars_15m` raises `DataIntegrityError` | — | harness behaviour quoted by spec step 1 | `test_read_bars_rejects_duplicate_close_stamp_fail_closed` |
| Recipe step 2 `[scored_start+1d, scored_end]` | `decision_days()` | UTC midnights `(start, end]`, len = `365` on the contract window | calendar partition; C4 forbids 14:30Z variant | `test_decision_days_exclude_window_start_and_count_365`, `test_decision_days_floor_and_ceiling_partial_edges_per_contract_window_rule` |
| Step 2a block `(D−1)00:00Z < close ≤ D00:00Z` | `block_window_ns()` | exclusive-low / inclusive-high | spec literal | `test_block_window_is_exclusive_low_inclusive_high` |
| Step 2b eligibility `len(B)==96` | `symbol_day_feature(INELIGIBLE_BLOCK_SIZE)` | `96` | spec recipe | `test_ineligible_when_block_size_is_not_ninety_six` |
| Step 2c skip rebalance when `< MIN_ELIGIBLE` | `compute_targets(STATUS_SKIP_BELOW_MIN_ELIGIBLE)` + driver carry | `MIN_ELIGIBLE = 8` | constant table r3 (diversified capped book, bisection feasibility) | `test_book_below_min_eligible_skips_and_reports_reason` |
| Step 2d `Q_i>0` else ineligible | `INELIGIBLE_NONPOSITIVE_QUOTE_VOLUME` | — | spec recipe | `test_ineligible_on_nonpositive_block_quote_volume` |
| Step 2d `F_i = Σtqv/Q ∈ [0,1]`, `A_i=2F−1` | `SymbolDayFeature.imbalance_f/_a` | — | spec observables | `test_feature_aggregates_hand_computed_over_ninety_six_bars` |
| §3.2 endpoints `open(first)/close(last)` sanity-only | `block_open/block_close/block_move` | recorded, never used in anchor sign | §3.2 "used solely for the eligibility sanity check" | `test_feature_aggregates_hand_computed_over_ninety_six_bars`; anchor-sign test proves sign uses flow |
| Step e sample stdev ddof=1, zero-stdev ⇒ zeros | `cross_sectional_z()` | ddof=1 | spec literal | `test_cross_sectional_z_zero_mean_and_constant_vector_handling` |
| Step f `raw_i = −Ạ_i` (contrarian, §3.3) | `compute_day_signals(CONTROL_ANCHOR)` | — | §3.3 causal sign | `test_anchor_sign_longs_heaviest_aggressive_sellers` |
| Step g bracket `[0,1e6]`, ≤200 halvings, residual <1e-12 | `solve_lambda()` (`LAMBDA_BRACKET_HIGH/LAMBDA_MAX_HALVINGS/GROSS_RESIDUAL_TOL`) | `1e6`, `200`, `1e-12` | verbatim from step g | `test_emit_targets_hits_unit_gross_within_tolerance_and_respects_cap`, `test_solve_lambda_rejects_degenerate_books_and_infeasible_gross` |
| Step h `w_i = clip(λ·raw, ±CAP)` | `emit_targets()` | `CAP = 0.30` | constant table r4: margin under PLAN §12 hard gate "symbol contribution/risk ≤40%" (`contract_v10.CAPS_V10 = 0.40`) | cap assertions across weight tests |
| Table r5 unit-gross dollar-neutral | `GROSS_TARGET = 1.0` | Σ\|w\| → 1.0 within 1e-12 | spec table | `test_dollar_neutrality_exact_when_no_clip_binds` |
| Table r2 "signal instants 365/year" | `SIGNAL_INSTANTS_PER_YEAR = 365` | matched by `len(decision_days(contract window)) == 365` | UTC days in scored window | idem `test_decision_days_...` |
| §3.4 fill clock "OPEN of bar whose open == D 00:00Z" | `resolve_fill_event()` via `derived_open <= D < ts_event` (`SPEC_FILL_CLOCK_QUOTE_VERBATIM`) | offset 0 | §3.4 literal; real stamps sit ~100 µs inside grid so containment ≡ "first bar closing after D" | `test_fill_event_is_open_of_bar_covering_boundary`, `test_missing_opening_slot_yields_no_event_never_a_substitute` |
| §3.5 one-day renewable holding + §3.6 step 5 force-flat | `build_rebalance_schedule()` opens at `D_1..D_{n−1}`, flattens at `D_n` | final `weights == []` | steps 3+5 | `test_schedule_opens_daily_and_force_flats_at_final_scored_boundary`, `test_turnover_accounted_per_side_through_force_flat` |
| Step 3 taker fills at that open, costs on traded notional | `FillEvent.price`, `rebalance_cost()`, `fill_cost_rate()` | fee `TAKER_FEE_FLOOR_BPS = 5.0`, ticks `ADVERSE_TICK_SLIP_FLOOR = 1` | preregistered cost basis (v10_contract floors) | cost-primitive tests |
| Step 4 native funding across held settlements | `funding_cashflows()`, `derive_holding_spans()`, `normalize_settlements()` (shared PIT hook) | sign `LONG_PAYS_POSITIVE_RATE` | spec step 4 + repo funding-PIT rules | funding group incl. `test_funding_hook_integration_hand_computed_single_settlement` |
| §3.13 NEIGHBOUR M01-N denominator σ_i/√96 over 2880 slots | `prewindow_sigma_i()`, `prewindow_sigma_table()` (hash-pinned once), `NEIGHBOUR_PREWINDOW_DISPERSION` | `PREWINDOW_SLOTS = 2880 = 30×96` | §3.13 neighbour config | neighbour + sigma tests |
| Negative control (frozen arm) `CONTROL_A8_SPEC_DAYMEAN` | common level `Ā` for every eligible name; quotes carried verbatim | see AMB-02 | §3.9 substitution | `test_a8_spec_daymean_control_reproduces_the_quoted_defect` |
| Condition-C2 strengthened control | `SELECTION_FREEZE_C2_VERBATIM`, `A7N_M01_CONTROL_DEFECT_QUOTE_VERBATIM`, `A7N_M01_REQUIRED_BEFORE_FREEZE_QUOTE_VERBATIM` + arm `CONTROL_C2_PRICE_CONTRARIAN_PLACEBO` + probe `wide_range_flip_probe()` | flow observable replaced by negated standardised block price move (zero added parameters) | selection_freeze C2 + a7n §3 verbatim | `test_verbatim_quotations_survive_as_named_module_constants`, placebo / probe tests |
| §3.8 killer 6 drop-one-symbol / drop-one-fold | `StressParams(drop_symbols/dropped_fold_index)`, `apply_stress_filter()`, `chronological_folds(purge_days≥holding)` | purge = 1 day = holding horizon | §3.8 + contract folds/purge | stress + fold tests |
| §3.8 mechanism-specific killer (fee/slip ×1.5, +1 event delay) | `StressParams(fee_multiplier/event_delay_events/tick_slip_ticks)` mapped onto `contract_v10.STRESS_MATRIX_V10` names | defaults reproduce baseline exactly | PLAN §11 surface | `test_fee_slippage_x1_5_cell_scales_the_fee_component_only`, `test_plus_one_event_delay_cell_shifts_every_offset_and_hash` |
| Cohort/benchmark separation (§2.1) | `FROZEN_TRADING_COHORT` (10), `BENCHMARK_SYMBOL_EXCLUDED = "BTCUSDT"` (never read below) | — | universe manifest via spec §2.1 | `test_c1_verified_when_every_frozen_symbol_present` |
| Window freeze C4 | `SCORED_WINDOW_START_UTC/END_UTC = 2025-08-21T00:00Z / 2026-08-21T00:00Z`, `PREWINDOW_START_UTC = 2025-07-22T00:00Z` | 00:00Z contract rule, NOT measured 14:30Z | selection_freeze C4 | C1 scope keys; `test_decision_days_*` |

Runner adoption surface (no adapters needed): `compute_targets(**features, control_mode,
neighbour_mode, prewindow_sigma, min_eligible, cap, gross, reverse)` returns
`{"status","longs","shorts","weights","diagnostics","n_eligible","carried_forward",
"signals", ...}` matching the V9 weekly/`[[symbol, weight], ...]` payload shape;
day-level entry is `build_rebalance_schedule(bars_by_symbol=…, window_start_iso,
window_end_iso, …)` returning one row per boundary with `weights`, `fills`,
`turnover_one_side`, `book_diagnostics`, `signal_sha256`, `features_sha256`,
plus `holding_spans` and `schedule_sha256`.

---

## 2. Determinism and PIT guarantees (tested)

* Two independent builds → identical `schedule_sha256` /
  `payload_sha256(features)`; dict insertion order irrelevant
  (`test_determinism_identical_inputs_identical_hashes`). Hashing uses
  `research.pit_hooks_v10.canonical_repr`.
* Post-cutoff perturbation invariance of features, raw scores and schedule rows
  (`test_signal_hash_invariant_to_post_cutoff_perturbation`), with a deliberate
  guardrail showing the block's own last bar (closing AT the instant) DOES move
  the signal (`test_perturbing_the_decision_blocks_own_last_bar_does_move_the_signal`).
* Every contributing bar satisfies `ts_event_ns ≤ decision_ns`
  (`assert_signal_pit`, called inside every feature build).

## 3. Dollar-neutrality algebra (measured, not asserted away)

Standardised z-scores sum to exactly zero, so an unclipped book is exactly
neutral; CAP clipping truncates asymmetric tails and leaves a small nonzero
net exposure that the module REPORTS (`diagnostics.net_exposure`,
`clip_bound_active`) instead of silently projecting away
(`test_clipped_extremes_leave_reported_nonzero_net_exposure`). This is the
spec's own arithmetic (clip after bisect), kept faithful; |net| stayed ≤ CAP in
every fixture and is bounded structurally by `CAP`.

## 4. C1 field-population verification (RUN this wave)

Command (read-only, root master):
`python -m research.hyp_a8_m01 --verify-fields --catalog-root
/Users/hoangminhlong/my-quantitative/catalog_live_crypto --out
research/audits/v10/i1_c1_field_verification.json`

| Item | Result |
|---|---|
| Overall verdict | **VERIFIED** (`taker_buy_quote_volume`: VERIFIED, `quote_volume`: VERIFIED, `count`: VERIFIED) |
| Directories present | 20 of 20 root-master dirs scanned (+0 missing); bytes 135,016,614 |
| Frozen-universe symbols MISSING from disk entirely | none — all 10 (`ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, ENAUSDT, SUIUSDT, 1000PEPEUSDT, ADAUSDT, BNBUSDT, LINKUSDT`) present |
| On disk outside the frozen cohort | 10 context dirs incl. `BTCUSDT` (benchmark, excluded from features/weights/PnL), `AAVEUSDT, ACEUSDT, AVAXUSDT, BCHUSDT, BOMEUSDT, NEARUSDT, ONGUSDT, WLDUSDT, ZECUSDT` |
| Scored-window scope rows (20 dirs) | 700,743 (`2025-08-21T00:00Z..2026-08-21T00:00Z`); full-history rows 1,401,546 |
| non-null share | 1.0 exactly for all three fields, all 20 dirs, both scopes |
| zero fraction | 0.0 for `quote_volume`, `taker_buy_quote_volume`, `count` |
| negatives | 0 everywhere |
| sane ranges (scored window, all dirs) | `count` 22 .. 1,721,522; `quote_volume` 190.53 .. 7.502e9 USDT; `taker_buy_quote_volume` 42.83 .. 3.637e9 USDT; each field varies |
| `taker > quote` violations | 0 rows (tolerance 1e-9 relative) |
| Spot cross-check vs spec §2.2 | ETHUSDT scored-window completed bars measured **34,983**, identical to the proposal's declared figure |

Threshold provenance: ATT-TAKER-QV / ATT-COUNT / ATT-QUOTEV wording in
a8_proposals §8.1 ("present, non-null, non-degenerate"); null share must equal
the threshold `FIELD_NULL_SHARE_MAX = 0.0`, degeneracy includes
never-varying columns and unparsable floats read as null-like.

## 5. Ambiguities, deviations and open items

Recorded openly rather than reinterpreted:

* **AMB-01 (open, owner action needed): fill-clock unification.** A7-N's
  required-before-freeze item demands a *strictly later* event fill fleet-wide;
  the frozen spec (§3.4) fills at the open of the bar opening exactly at the
  decision instant. No frozen amendment exists, so the module implements the
  frozen text byte-for-byte and exposes `event_delay_events` plumbing
  (already used by the `plus_1_event_delay` cell). A1/I2 must freeze one
  fleet-wide choice before scoring; flipping it is a parameter change.
* **AMB-02 (documented realisation of §3.9): the frozen negative control's
  stated goals conflict arithmetically.** "Replace Ạ_i with Ā … then run the
  identical pipeline, standardisation…" — standardising a constant vector has
  zero sample stdev, which zeroes exactly the market-wide flow component the
  same sentence requires to survive. The module substitutes at the imbalance
  level WITHOUT re-standardising, which realises the behaviour A7-N describes
  verbatim ("degenerates into an all-long/all-short net-exposed book") and is
  covered by a dedicated test. The strengthened C2 arm exists because of this.
* **AMB-03 (declared approximation): funding basis.** Mark-price/OI overlays
  are UNAVAILABLE for this universe (spec §2.5), so accrual uses
  `cashflow = −weight × rate` per unit of unit-gross capital on
  boundary-rebalanced legs instead of mark-to-settlement notionals. Requires
  harness confirmation at cost-gate time.
* **AMB-04 (unfrozen convention, fail-safe usage): wide-range stratum split.**
  C2 fixes no numeric split. The split uses the deterministic median of the
  daily cross-sectional mean `range_fraction` purely as a POST-HOC diagnostic;
  it can never touch signals/weights/fills/costs, and the credit rule requires
  BOTH strata to degrade. Needs an explicit A1 freeze before any scored claim
  relies on it.
* **AMB-05 (data-edge caveat): ISO-second truncation.** Caller-supplied window
  edges parse at second resolution while bar close stamps sit ~100 µs inside
  the grid, so a mid-second upper edge drops whole bars from a *scope*
  (`test_c1_scoped_seconds_truncation_is_reported_not_hidden`). Decision
  instants are exact UTC midnights, so signal blocks are immune; surfaced so
  census consumers pass midnight-aligned scopes.
* **AMB-06 (needs harness confirmation): refused-boundary accrual tail.** When
  the final force-flat finds no allowed event, `derive_holding_spans` closes
  the tail at `decision_ns + one bar` (the legs demonstrably survived that far)
  instead of leaving accrual unbounded.
* **DEV-01 (spec-consistent degenerate day): zero-dispersion cross-section.**
  If every eligible name shares one imbalance (or `n_eligible < MIN_ELIGIBLE`),
  spec step e yields all-zero scores, the step-g bisection becomes
  unsatisfiable, and the whole rebalance is skipped with prior weights carried
  (`SKIP_INFEASIBLE_BOOK` / `SKIP_BELOW_MIN_ELIGIBLE`), recorded per row with a
  reason code and counted in `skipped_rebalances`. Tested explicitly for the
  day-mean control arm.
* **UNAVAILABLE_FAIL_CLOSED items carried into I2/QA:** multiplicity proof not
  derivable (expected per spec §8.2 and selection freeze C5); native settlement
  bundles are stage-owner territory (C3) — this module accepts them ONLY as an
  injected validated series; weight-vector rank correlation against
  XSECT-WREV/XSECT-MOM demanded by A7-N is a harness-level measurement and was
  NOT implemented here (out of wave-I scope, listed in A7-N's quote above).

Non-goals honoured: no BTC consumption anywhere, no OI/mark overlay, no equity
extension, no volatility targeting or regime filters, no parameter search; no
scoring of any kind happens in this module (no PnL/PF/MDD code paths exist).
