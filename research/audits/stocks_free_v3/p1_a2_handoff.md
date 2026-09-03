# P1/A2 — Stocks measurement factory repair (handoff)

- Lane: A2 (`PLAN_stocks.md` §9 A2 — sidecar, canonical attribution and trial
  accounting repairs)
- Worktree: `.worktrees/stocks-free-v3/p1-a2-factory`
- Branch: `orca/stocks-free-v3-p1-a2-factory`
- Base HEAD at start: `a29bc070b72fc72d324fd529224a19152b41711b` (verified)
- Interpreter: `/Users/hoangminhlong/my-quantitative/.venv/bin/python` only;
  no network, no API keys, no S1 data, no raw-data commits, no scored PnL on
  real S0 data (synthetic fixtures only)

## Repaired defects (inputs: V2 terminal audit `z9_a7_terminal`)

1. **Defect (a) — CASH in tradable-leg turnover.** A5-style target books carry
   an explicit `CASH` leg inside `targets`; the V2 staged runner's sidecar
   turnover union `set(targets) | set(weights) - {"CASH"}` binds as
   `set(targets) | (set(weights) - {"CASH"})` (precedence), so the CASH leg
   was counted. Repair: ONE canonical turnover,
   `etf_leg_turnover(previous, targets) = sum(|targets - previous| over
   (targets ∪ previous) − {CASH})` — CASH is never a tradable leg anywhere in
   the V3 path.
2. **Defect (b) — double cost accumulator.** `total_cost += cost` ran twice
   while equity was deducted once. Repair: the canonical loop deducts equity
   once, appends one per-fill `(date, turnover, cost)` record, and
   `assert_reconciles` fails closed unless `total_cost == fsum(per-fill
   costs)` and the attribution identity closes — the regression test
   (`test_cost_accumulator_equals_fsum_of_per_fill_costs`,
   `test_reconcile_fails_on_reintroduced_double_add_pattern`) fails on any
   reintroduced double-add.

## Deliverable mapping

| PLAN §9 A2 | Where |
|---|---|
| 1. one canonical accounting path + equivalence proof | `research/assets/stocks/factory.py` (`value_book`); bit-identical equivalence vs `research/stocks_free_v2/harness.py::value_book` proven in `test_factory_valuation.py` (both book styles × adverse/delay/excluded/distribution variants) |
| 2. CASH excluded everywhere | `etf_leg_turnover` (single definition); pinned by `test_etf_leg_turnover_excludes_cash_everywhere` and the A5 golden |
| 3. cost charged exactly once | per-fill `fill_costs` ledger + `assert_reconciles` (regression test fails on double-add) |
| 4. hand-computed A4-style and A5-style fixtures | docstrings + goldens in `tests/stocks_free_v3/test_factory_valuation.py` (Fixture A4-A, Fixture A5-A; every number hand-derived) |
| 5. attribution reconciles at 1e-12 | `ATTRIBUTION_TOLERANCE = 1e-12`; identity `fsum(contrib) − total_cost = total_pnl` exact to ~1e-16 on all fixtures/variants (`test_factory_attribution_reconcile.py`) |
| 6. ONE fold-concentration definition | `fold_concentration` / `per_arm_fold_concentration`: per-fold `max(pnl,0) / Σ max(pnl,0)` of the SAME arm; no family pool / neighbour / mixed denominator (`test_fold_concentration.py`) |
| 7. drop-one-ETF | `select_drop_one_symbol` + `assert_drop_one_allowed`: largest realized \|contribution\| among HELD ETFs, lexicographic tie-break; non-held / CASH / zero-contribution drops rejected (`test_drop_one.py`) |
| 8. publication refuses zero-event/zero-position | `GatedTrialLedger.publish_result` (+ `publication_metrics`); observed recorded even when refused; replay increments neither; counters inherited unchanged from V2 `TrialLedger` (`test_publication_gate.py`) |
| 9. V2 diagnostic replay | `tests/stocks_free_v3/test_v2_diagnostic_replay.py`: on the synthetic A5-style fixture the corrected path reconciles at ~1e-16 while the replicated V2 defect pattern yields residual −0.013464430 (== deducted − accumulated), detected at the frozen 1e-12 tolerance; first-fill turnover exactly 2x (CASH leg) |

## Semantics pinned (exact)

- **Turnover (costs):** non-CASH legs only; `CASH` in `targets` or in
  previous weights is stripped by the union difference.
- **Costs:** `cost = equity × ETF_turnover × (cost_bps + adverse_bps) / 1e4`,
  deducted from equity once, accumulated once, recorded once per fill.
- **Attribution:** per-session `contrib[s] += equity_before_growth × w_s ×
  r_s`; CASH earns nothing and never appears as a contribution leg; identity
  tolerance frozen at 1e-12 (measured ≤ ~2.5e-16 on all fixtures).
- **Fold concentration:** `share_f = max(pnl_f, 0) / Σ_f' max(pnl_f', 0)`,
  denominator restricted to the SAME arm; no positive folds ⇒ all shares 0.0.
- **Drop-one:** rank held ETFs by `(-|realized contribution|, symbol)`;
  zero-weight / `CASH` / zero-contribution candidates raise `ValueError`.
- **Publication:** `n_fill_events == 0` (no decision fills; FORCE_FLAT is
  bookkeeping) or `n_held_positions == 0` (never holds a non-CASH leg) ⇒
  `PUBLICATION_REFUSED_ZERO_RESULT` recorded, key unpublished, published
  counter unchanged; `compute_recorded` had already incremented observed;
  replays of published keys are zero-delta (inherited from V2 ledger).

## V2 safety (nothing scored touched)

- `research/stocks_free_v2/harness.py` is UNCHANGED (zero-byte diff): the
  canonical path lives in the new V3 module and equivalence to the frozen
  harness is proven by tests, so V2 goldens/artifacts remain pinned.
- No V2 family code, ledger, artifact, or result file was modified; the
  diagnostic replay is synthetic and in-memory only; no new V2 trial.
- Two documented fail-closed divergences from harness `value_book`, both only
  on inputs where the V2 code silently produced a wrong book: (i) explicit
  `CASH` in `targets` must agree with `cash_weight` (else error) and is
  honored when `cash_weight` is absent; (ii) with `excluded_symbol` on a book
  carrying explicit CASH, cash is the residual of the remaining ETF legs.

## Test evidence (this worktree, this branch)

- `pytest tests/stocks_free_v3 -q` → 46 passed
- `pytest tests/stocks_free_v2 -q` → 123 passed (V2 regression intact)
- `pytest tests/assets/stocks -q` → 233 passed
- `compileall -q research/assets/stocks research/stocks_free_v2` → OK
- `git diff --check` clean; tests mutate no tracked files
