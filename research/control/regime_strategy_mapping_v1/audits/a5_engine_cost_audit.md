# A5 — ENGINE, COST AND CHURN AUDIT (findings report)

- Cycle: `REGIME-STRATEGY-MAPPING-V1` (S0 discovery)
- Task: `RSMV1-A5-ENGINE-AUDIT` — lane `a5-engine-audit`
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/regime-strategy-mapping-v1/a5-engine-audit`
- Branch: `orca/rsmv1-a5-engine-audit`
- Dispatch/base SHA (re-measured at open, clean tree): `02167db05cb5d494c9ef992883e522c234c4391d`
- Object under audit: the `rsmv1` fork at `research/control/regime_strategy_mapping_v1/rsmv1/`
  (`engine.py`, `strategies.py`, `arms.py` helpers, `data.py`, `metrics.py`), forked from
  terminal cycle JEV-REGIME-ROUTER-V2 at `0c277a94`.
- Method: hand-computed golden fixtures on small synthetic bars (15–97 bars), every expected
  number derived from the pinned laws (costs = `bps*1e-4*notional`, qty = `round(cash/px, 8)`,
  equity traced bar by bar, regime targets tabulated by the strictly-before/staleness law).
  Fixtures: `tests_py/fixtures_engine_golden.py` + `tests_py/test_engine_golden.py`.
  Verification: `python -m pytest tests_py -q` → **26 passed, 1 xfailed, exit 0**
  (21 golden tests + 5 pre-existing regime-timeline smoke tests; the xfail is finding A5-F1,
  `strict=True`).
- Isolation: synthetic fixtures only. No Jev API calls, no paper/live/orders, no reads of any
  `runtime/` or `evidence/` directory, no real-corpus PnL runs, V2 worktree untouched,
  `rsmv1` core unmodified, no scored artifacts produced.

## Per-law verdicts

| Law | Verdict | Fixture evidence |
|---|---|---|
| 1. Next-bar-open fills; no same-bar fill; no same-open flip | **PASS** | `test_law1_next_bar_open_fills`: signal at close of bar 19 (close 102 > ema20 = 100.190476 > ema50 = 100.078431) fills at open of bar 20 (px 100, `entry_ts = ts_open[20]`); `invested[19] == 0`, equity flat through bar 19. Exit signal at close of bar 29 (101.0 < ema20 = 101.335076) fills at open of bar 30. Structural proof of no same-open flip: the fill step is an if/elif on `(pos, pending_exit)` vs `(pos is None, pending_entry)`, and `pending_entry` is provably always `None` while a position is open (it is consumed or dropped at the very next open) — exercised by law 7 where the exit open (bar 25) and the flip entry open (bar 26) are distinct. |
| 2. Costs debited exactly once per fill (BTC fee+slip; SPY all-in band as fees, zero slip) | **PASS** | `test_law2_costs_exactly_once_btc`: one entry + one exit → fees exactly 50+50 = 100, slip 10+10 = 20, net −120; the hand-traced 34-bar equity path (100000 → −60+1000·close → 99940) is only reachable with single charging (entry costs debit at entry, `exit_costs = fees+slip − entry_costs` debits the exit side only). `test_law2_spy_band_booked_as_fees_zero_slippage`: SPY `CostModel(10 bps, 0)` → fees 200, **slip exactly 0.0**, net −200. Stop and fold-flat fills also carry their own single charge (laws 3/5/7 fixtures). |
| 3. Intrabar stops only on bars AFTER the entry bar; fill at stop price, slippage debited separately | **PASS** | `test_law3_stop_after_entry_bar_at_stop_price`: bars 0..19 carry TR = 2 exactly ⇒ Wilder ATR14[19] = 2 (hand-derived); entry at open 100 ⇒ stop = 100 − 3·2 = 94. Entry-bar low is 94 (≤ stop) yet `invested[20] == 1` — the entry bar is excluded (`i > pos.entry_bar`). Bar 21 low ≤ stop → fill **exactly at 94.0**, stamped `ts_open[21]`, with fee 47 + slip 9.4 debited on the 94 notional (totals fees 97, slip 19.4, net −6116.4, equity 93883.6 hand-traced). NaN stop (ATR uninit) is fail-safe hold (`stop_hit` returns False). |
| 4. Strategy/regime-off exits fill at the NEXT open; reconcile to new target at next open | **PASS** | `test_law4_regime_off_exit_at_next_open`: targets flip to FLAT after the entry bar → close at the open of the first FLAT bar (bar 21 @ 101, reason `regime_off`, net 879.4); reconciliation runs BEFORE the stop check at the same open (exit reason is `regime_off`, not `stop`, despite the intrabar low). `test_law4_entry_dropped_when_target_vanishes_before_fill`: a queued entry whose target no longer matches at the fill open is dropped — zero trades, equity exactly 100000 throughout (conservative, deterministic; see O4). |
| 5. Contiguous fold partition; no position across a fold boundary; force-flat at fold's LAST exec bar close with costs; equity continuous; Σfold_net = total net (1e-9); entries refused on unassigned bars | **PASS** | `test_law5_fold_partition_and_force_flat`: `folds_from_regime_ts` yields the hand-derived contiguous partition `[(0,8,17),(1,18,19)]`; `fold_id` = `[−1]×8 + [0]×10 + [1]×2`; the signal on unassigned bar 5 is refused at the fill open (no position, equity 100000 through bar 7) and entry signals require `fold_id[i] >= 0`; force-flat at `ts_close[17]` with full costs (fees 100, slip 20); equity continuous across the boundary (`eq[17] == eq[18]`); `fold_net == [−120, 0]`, Σ = totals net −120 (also hard-asserted inside every run by `_assert_engine_invariants`). `fold_partition_invariants` accepts `first_required_bar=8` and raises for 7. The engine additionally hard-fails on any invested bar with `fold_id == −1` and on any trade crossing its fold range. |
| 6. BTC funding: rate × signed notional at every 8h UTC boundary strictly after entry up to exit; longs pay, shorts receive | **PASS** | `test_law6_funding_long_pays_at_boundaries`: entry fills at open of bar 31 = 07:45Z; events at 08:00Z (entry bar close is the boundary, ref = close 102) and 16:00Z (bar 63 closes AT the boundary, ref 102); funding = +2×1.377e-5×1000×102 = **+2.814708** (long pays), net −122.814708, equity path hand-traced; the exit at the 16:00Z open charges nothing further (boundary already consumed). `test_law6_funding_short_receives_signed_credit`: short pays/receives mirrored → funding = **−2.69892** (signed credit), net 2083.89892 = gross 2000 − fees 99 − slip 19.8 + credit. |
| 7. Every position cycle = exactly one trade record; flips are close-then-open, both costed, never netted | **PASS** | `test_law7_flip_is_close_then_open_two_costed_fills`: TREND_LONG→TREND_SHORT flip produces exactly 2 trades — long closed `regime_off` @ 103 at open of bar 25 (net 2878.2), short opened at open of bar 26 @ 100 with qty = round(102878.2/100, 8) = 1028.782 (net 5023.542506), each carrying entry+exit fee and slip; `t2.entry_ts > t1.exit_ts` (distinct opens). Totals = 7901.742506, equity[-1] = 107901.742506 hand-traced. |
| 8. No-op target ⇒ no reconciliation, no fill (engine precondition of the churn law) | **PASS** | `test_law8_noop_target_no_reconciliation_no_churn`: constant TREND_LONG target → exactly one entry and zero reconciliation fills; the only exit is the strategy's own signal (`reasons == ["strategy_exit"]`); on the holding plateau (bars 21..28, unchanged target and close) equity is exactly flat — no cost events. Reconciliation fires only on `tgt is None or FLAT or tgt != strategy`. |
| 9. Regime-clock governance (H1/H4 → 15m), strictly-before-open law, bar-by-bar | **PASS** | `test_law9_regime_clock_governing_h1` (41-bar hand table): ts_o == decision ts → previous regime governs / None before the first decision (k=8); `ts_o == R0+1h` → governed by R0 (k=12); transitions at (R0, R0+1h], (R0+1h, R0+3h], (R0+3h, R0+5h] hand-tabulated. `test_law9_regime_clock_governing_h4` (97-bar hand table): H4 boundaries at 4h/8h/12h/20h with the exact-8h staleness boundaries governed (k=48, k=80). `test_law9_unknown_and_unmapped_labels_map_flat`: `TRANSITION_UNKNOWN` and unmapped labels → FLAT via `mapping.get(label, FLAT)`. `test_law9_arms_target_grid_matches_governing_law`: `arms._targets_from_regime_target_grid` is element-identical to `targets_from_regime` on the same timeline. |
| 10. Determinism: same inputs → byte-identical trades and equity | **PASS** | `test_law10_determinism_byte_identical_reruns`: two runs of the 2-trade flip scenario → `equity.tobytes()`, `invested.tobytes()`, `fold_id.tobytes()` identical; totals dicts equal; all 16 fields of every trade equal. No RNG anywhere in the engine path. |
| 11. Stale-data rejection: decision older than 2 regime periods → FLAT | **PASS** | `test_law11_stale_beyond_two_periods_maps_flat`: single decision at T0, period 1h → age exactly 2h governs (bar at T0+2h = TREND_LONG, boundary equality is NOT stale — `>` comparison), ages > 2h all FLAT. Boundary equality at scale also covered inside the law-9 tables (H1 k=28 age 2h; H4 k=48/k=80 age exactly 8h = 2 periods). |

**Engine-level laws: 11/11 PASS. Also-audit items: PASS (below). One proven deviation from a
module-documented law outside the 11 dispatch laws: A5-F1.**

## Also-audit (metrics.py, equity MTM identity)

- **Equity MTM identity** `100000 + totals.net_pnl == equity[-1]` — **PASS** within 1e-9 on the
  stop and flip scenarios (`test_mtm_identity_on_flip_and_stop_scenarios`), plus every fixture's
  full equity path is hand-traced bar by bar. Reading-level proof: per round trip,
  Δcash = dir·qty·(fill−entry) − entry_costs − exit_costs − funding = gross − fees − slip − funding
  = `net_pnl`; positions only open/close inside folds, and the fold attribution identity
  Σ(eq[e]−eq[s−1]) telescopes to the same number (hard-asserted each run).
- **turnover** — **PASS** with a definitional note: `compute_arm_metrics` computes
  **entry-side notional** (Σ qty·entry_px), divided by mean equity and by the fold-span year count
  (`test_metrics_turnover_and_time_in_market_hand_check`, rel 1e-9 vs hand components; hand case:
  entry notional 202878.2 over 31 bars). It is an annualized entry-notional churn measure, not a
  round-trip (double-sided) turnover — the cycle's churn law builds on per-fill counts, which the
  engine supplies exactly (one fill = one costed event, laws 2/7/8).
- **time_in_market / expectancy / win_rate** — PASS on the flip scenario (9/31 invested, mean net
  per trade, 100% winners).
- **regime_occupancy / switches / avg_dwell / unknown_share** — **PASS**
  (`test_metrics_regime_stats_hand_case`): [A,A,B,B,B,A,C,C] → switches 3, occupancy
  {A: 3/8, B: 3/8, C: 2/8}, avg dwell (2+3+1+2)/4 = 2.0, unknown_share 0; TRANSITION_UNKNOWN share
  0.5 on a mixed stream. These are timeline metrics (label stream), independent of trade records
  by construction — consistent with their use.
- **data.py (reading-level)** — snap-close (≤1ms, snap UP, fail-closed), bucket resample
  (complete iff exactly span_bars aligned bars; partials reported, never decide), census
  fail-closed vs freeze, SPY adjusted-series construction and duplicate-session rejection all
  match the frozen contract texts. NOT exercised against the real corpus (forbidden here);
  runtime census equivalence is NOT_RUN in this lane.

## Findings

### A5-F1 (MEDIUM, PROVEN — xfail fixture committed) — BUY_HOLD reference violates its documented hold-to-end law

- **Documented law** (`rsmv1/engine.py` module docstring): "BUY_HOLD (arm A): enters TREND_LONG at
  the first exec bar open of each fold, exits **only via fold force-flat** (hold-to-end modulo
  fold law)."
- **Observed**: the engine opens BUY_HOLD positions with `strategy = TREND_LONG` (the entry queued
  for BUY_HOLD targets is TREND_LONG), so the full TREND_LONG exit machinery applies: the trend
  exit signal (`close < EMA20`) closes the position mid-fold with reason `strategy_exit`, and the
  intrabar stop (`entry − 3·ATR14`) is also live. Re-entry happens only at fold starts
  (`i in _fold_starts`), so after a mid-fold exit the reference sits flat until the next fold.
- **Minimal reproduction** (`test_buyhold_documented_hold_to_end_law`, strict xfail, and its PASS
  companion `test_buyhold_observed_deviation_documented`): one fold of 20 bars, targets BUY_HOLD;
  bars flat 100, bar 2 closes 98 (< EMA20 = 99.809519) → trade exits at open of bar 3 @ 98 with
  reason `strategy_exit` (entry bar 1 @ 100, net −2118.8), then `invested == 0` through the fold
  end (bars 3..19) — no fold-flat exit ever occurs.
- **Impact**: the buy-hold REFERENCE metric per cell (freeze: "reference metric only, never a
  scored arm") is a strategy-controlled path, not buy-and-hold: in down-drifting folds it
  liquidates early and misses the subsequent re-entry, and it churns (2 extra fills). Headline
  cell comparisons "arm vs buy-hold" therefore compare against a path the docstring does not
  describe. No scored arm is affected; no pinned dispatch law is violated (this is a
  module-documented law).
- **Reported to A1** (audit-only lane; not repaired). Options for A1: (a) re-pin the docstring to
  the observed semantics, or (b) enforce hold-to-end (e.g. suppress exit signals for BUY_HOLD
  positions). Either way the BUY_HOLD reference numbers currently in play must be labeled
  "trend-exit-managed buy-hold", not buy-and-hold, until resolved.

### A5-O1 (LOW) — stop level uses the entry bar's own ATR on the first ATR bar (intra-bar lookahead, warmup edge)

`Engine._open_position` reads `atr14[i−1]` and, when it is NaN, falls back to `atr14[i]`. The only
index where this fires is i = 13 (ATR's first defined bar): the stop level then includes bar 13's
true range, i.e. information from the entry bar itself (the fill happens at that bar's open).
Stops are still evaluated only on later bars, so no self-trigger is possible. Unreachable in
production cells (warmup = 192 exec bars ⇒ `atr14[i−1]` is always finite at any allowed entry),
but it is a genuine lookahead edge in the engine proper. Report to A1; not repaired.

### A5-O2 (INFO) — `folds_from_regime_ts` ignores the frozen span END timestamps

Fold k's exec range is `[first bar after span_k start, first bar after span_{k+1} start − 1]`
(last fold → final bar); the frozen `end` values are decorative in the exec mapping. This is
exactly the documented A7-1 F3 contiguous-partition amendment (and is what makes
Σfold_net = totals hold), recorded here so nobody expects the frozen ends to bind exec ranges.

### A5-O3 (INFO) — staleness constant duplicated in `arms._targets_from_regime_target_grid`

The arms helper inlines `2 * regime_period_ns` instead of importing
`engine.STALE_REGIME_PERIODS`. Currently consistent — proven element-identical to
`targets_from_regime` by `test_law9_arms_target_grid_matches_governing_law`. If the gate is ever
re-pinned, both sites must move together.

### A5-O4 (INFO) — queued entry silently dropped when the target changes before the fill open

A signal queued at bar i's close is filled at bar i+1's open only if `targets[i+1]` still matches
(or is BUY_HOLD); a regime change between close and open drops the entry without a trace. This is
the conservative reading of "decisions act on bars strictly after their close" and is
fixture-pinned (`test_law4_entry_dropped_when_target_vanishes_before_fill`); noted because it
suppresses entries exactly at regime boundaries (churn-relevant, never look-ahead).

### A5-O5 (INFO) — stop exits stamped at the bar's OPEN timestamp

`_close_position(..., reason="stop")` stamps `ts_open` of the trigger bar (fill price = stop
level). Funding is charged up to that stamp (a boundary exactly at the stamp is charged via the
close path). Deterministic and hand-verified (law 3/6 fixtures); intrabar fill timing is otherwise
not modeled.

### A5-O6 (INFO) — engine relies on folds covering the final exec bar

If a caller passed folds whose last range ended before the final bar and a position were still
open, fold_net would include unrealized MTM while totals would not — the run would hard-fail on
the built-in Σfold_net assert (never silent). The runner path is safe because
`folds_from_regime_ts` extends the last fold to the final bar, forcing a fold-flat close.

## Explicitly NOT audited

- `rsmv1/attribution.py` and `rsmv1/feasibility.py` — forbidden to this lane (A2 owns attribution).
- `questionio.py`, `safety.py`, `deterministic.py`, `regime_timeline.py`, `features.py`,
  `indicators.py` formulas beyond the load-bearing constants consumed by the fixtures (EMA
  seed/alpha and Wilder-ATR seed behavior are hand-derived in the fixture comments where a law
  depends on them); `regime_timeline.py` has its own passing smoke tests in this directory.
- `data.py` loaders against the real catalog/corpus (forbidden — synthetic fixtures only);
  census-vs-freeze equivalence at runtime is NOT_RUN here (reading-level contract audit only).
- Security guard internals (`security.py`), freeze digests (`freezes.py`), pyarrow parquet decode.
- Any `runtime/` or `evidence/` artifact, any scored output, the V2 worktree, and all other lanes.
- No Jev API calls; no paper/live/orders; workers 0; no heavy-lock jobs.

## Verification

```
cd <worktree>/research/control/regime_strategy_mapping_v1
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests_py -q
→ 26 passed, 1 xfailed in ~5s, exit 0
(21 A5 golden tests: 20 PASS + 1 strict xfail = A5-F1; plus 5 pre-existing regime-timeline tests)
```
