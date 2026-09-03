# V12P A4 evidence summary — cap feasibility, diagnostics repair, OILEV-V2 schedule

Worktree `p1-a4-feasibility`, branch `orca/v12p-a4-feasibility`,
bootstrap `8bfbae5073d0d2079a18863d060084cc929ba7a4` (verified before any write).
Scope: schedule-only diagnostics and feasibility. No PnL, no returns, no scored metric.

## 1. Pre-score target-book validator (deliverable 1)

`research/v12/feasibility.py` — `validate_target_book` / `validate_stamp_schedule`.
Validates EVERY stamp: finite weights, `|w| <= 0.30 + WEIGHT_TOL` (frozen adapter cap,
semantics mirrored from `research/adapter_v10/converters.normalise_target_book`), duplicate
refusal, non-empty where the contract requires, optional exact leg counts (4+4).
Fail-closed with per-stamp reason codes; empty schedule can never PASS.
Verdict artifact: `a4_stamp_validator_verdict.json` (PASS 52/52, anchor arm).
The validator runs BEFORE scoring and produces verdicts only — never capital paths.

## 2. Drop-one-symbol repair, L-V11-7 (deliverable 2)

`research/adapter_v10/stress.py` — `select_drop_one_symbol` (+ optional
`realized_weights=` on `build_stress_spec` / `stress_matrix_cells`).
With the realized book supplied, the dropped symbol is the HELD symbol with the LARGEST
absolute realized weight; exact ties break to the lexicographically smallest symbol id;
an unheld symbol (absent or `|w| <= WEIGHT_TOL`) can never be selected; weights outside
the declared droppable cohort and zero-held books fail closed with `ContractViolation`.
Regression test uses a hand-built book where the lexicographically-first HELD symbol is
NOT the largest holder and an unheld symbol sits in the cohort
(`tests/test_v12p_a4_feasibility.py::test_drop_one_selects_largest_held_weight_not_lexicographic_first`).
The frozen legacy sorted-first fallback is preserved ONLY for the V10/V11 driver
call signature that carries no book (default arguments unchanged; runner.py and the
frozen V11 tooling stay byte-compatible).

## 3. Per-family stress-cell matrix derivation, L-V11-1 (deliverable 3)

`research/adapter_v10/stress.py` — `probe_family_dropped_fold_support` (frozen V11 driver
probe semantics preserved exactly), `derive_family_stress_matrix`, and a
`supported_cells=` / `exclusion_record=` extension of `stress_matrix_cells`.
The cell list is derived FROM the frozen family `folds()` contract: LOT-like contracts
that refuse a dropped fold get a 5-cell matrix (3x5), ILLIQ/OILEV-like contracts that
accept it get the 6-cell matrix (3x6). Unsupported cells are excluded AND recorded in
the returned preflight record (`excluded_cells`, `folds_contract_probe_accepts_drop_one_fold`).
`build_stress_spec(..., supported_cells=...)` refuses unsupported cells hard.
Default (no family contract declared) keeps the generic 6-cell superset unchanged —
`tests/test_adapter_v10_g1.py` stress tests and `tests/test_v11p_a4_dryrun.py` still pass.

## 4. OILEV-V2 deterministic diversified book (deliverable 4)

`research/v12/oilev_v2_book.py` — fixed identity per PLAN §8.2: rank the eligible
universe by the INJECTED PIT signal (feature frozen later by the A1 brief; mechanics are
ranking-agnostic), >= 9 eligible required else fail-closed `EligibilityShortfall`,
4 lowest + 4 highest names (exact score ties → lexicographically smallest symbol id),
equal weight per leg, frozen BTC beta hedge as V11 CONTEXT semantics (BTCUSDT
benchmark-excluded, can never be a position), then uniform scale of the ENTIRE book when
needed so every `|w| <= 0.30`. Individual names are NEVER clipped or renormalised.
Post-scale cap is asserted (`assert post_max <= cap + WEIGHT_TOL`).
`research/v12/oilev_v2_spec.py` — schedule/spec draft (3 arms: 28d flow anchor,
56d stock neighbour, sign-inverted control; stamp calendar reuses the V11 plugin's
`weekly_mondays` for the CALENDAR ONLY; provisional PIT OI feature scores as the
injected ranking for this lane's feasibility run, explicitly marked provisional).

## 5. 52/52 pre-window stamp feasibility (deliverable 5)

Data: 20 consolidated OI parquets (gitignored, absolute-path reads, never copied),
staging `v11_oi_staging_v1`, window 2025-07-01..2026-08-21, 417/417 days, 0 gaps.
Universe: 19 tradeable symbols; BTCUSDT held out as context-only benchmark.

Verdict: **PASS n=52** — every stamp, all three arms:

| arm | stamps | eligible (min–max) | legs | max abs weight | scale |
|---|---|---|---|---|---|
| OILEV-V2-FLOW-28D (anchor) | 52/52 PASS | 19–19 | 4+4 | 0.125 | 1.0 |
| OILEV-V2-STOCK-56D (neighbour) | 52/52 PASS | 19–19 | 4+4 | 0.125 | 1.0 |
| OILEV-V2-FLOW-28D-INV (control) | 52/52 PASS | 19–19 | 4+4 | 0.125 | 1.0 |

No stamp needed the uniform scale (per-name 0.125 < 0.30 by construction); no failures;
`BLOCKED_PRE_SCORE` condition NOT triggered.

## 6. Schedule-only diagnostics (deliverable 6)

Decision count 52 per arm; one-way turnover from target deltas:
flow-28d 50.0, stock-56d 55.5, control 50.0 (total |Δw| across 51 steps);
holding spans from target occupancy: 90/103/90 spans, median 14 days (weekly stamps,
4+4 slots persist >1 week). Funding events while held: `UNAVAILABLE` — no local funding
settlement series exists (honest fail-closed; never inferred); the diagnostics verdict is
`UNAVAILABLE_FAIL_CLOSED` for that metric only and does not alter the stamp feasibility
verdict. No cost-threshold evaluated, no PnL/returns anywhere.

## Tests

`tests/test_v12p_a4_feasibility.py` (27 tests) plus the required regression suites:
`tests/test_v11p_a4_dryrun.py`, `tests/test_v11i_oilever_delev_frozen.py` — see
`a4_pytest.txt` for the recorded run.

## Assumptions / disclosures

- The PIT ranking for the feasibility run is the provisional raw OI feature
  (log-growth / own-history percentile, V11 anchor semantics: last daily row strictly
  before stamp, staleness <= 48h, positive). A1's `oilever_v2_brief` freezes the final
  feature; book mechanics and this feasibility verdict are ranking-value-independent
  given >= 9 finite scores per stamp.
- Funding-event counts require funding settlements; none exist locally, hence
  UNAVAILABLE (fail-closed), not blocking (the blocking gate is the 52-stamp
  breadth/leg/cap verification).
- `research/v12/oilev_v2_spec.py` is a DRAFT; it freezes nothing centrally and its
  arm ids are schedule labels, not publication identities.
