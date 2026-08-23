# Challenge Memo — Adversarial Review of the V1 Pipeline

- **Author:** A4 (independent reviewer), Sprint V2
- **Date:** 2026-08-23
- **Objects reviewed:** `research/matrix_runner.py`, `research/baseline_wf.py`, `backtest/engine.py`, `strategy_base.py`, `strategy_trend_pullback.py` (representative strategy), `reports/funding.py`, `research/breakout_wf.py::_metrics_in_window`, `research/sprint_eval.py`; Nautilus Trader **1.230.0** as installed in `.venv` (`backtest/engine.pyx`, `backtest/models/fill.pyx`). Artifacts cross-checked against `results/matrix/stage_a_s0_20260823/` and `stage_a_volcomp_iter1/`.
- **Method:** code-path tracing + two empirical probes executed against the repo's own engine builder and catalog data (probes are reproducible; suggested below as permanent regression tests for A3/A1).

Severity scale: HIGH = can create or inflate a reported edge / blocks G1–G3 credibility; MED = distorts metrics or audit trail without necessarily creating edge; LOW = hygiene.

---

## Finding 1 — (a) BAR-CLOSE FILL OPTIMISM: fills occur at bar_t CLOSE, same bar, same timestamp

**Severity: HIGH. Confidence: VERY HIGH (code path + direct empirical probe).**

### Question
When a strategy submits a market order inside `on_bar(bar_t)` in Nautilus 1.230, does the fill occur at bar_t close or bar_{t+1} open?

### Answer
**At bar_t's close ± one tick slippage, with fill `ts_init` equal to bar_t's own timestamp. Not bar_{t+1}'s open.**

### Evidence

1. *Code path.* All strategies submit MARKET orders synchronously from `on_bar` (`strategy_base._submit_entry`, strategy_base.py:247–254; entry call sites e.g. strategy_trend_pullback.py:80). The venue is built from bar data only, default zero latency (`backtest/engine.py:169–179`; no `latency_model` passed to `add_venue`). In Nautilus 1.230, `SimulatedExchange.process_bar` (`nautilus_trader/backtest/engine.pyx:4726`) synthesizes trade ticks from the bar OHLC via `_process_trade_ticks_from_bar` (engine.pyx:4847): open → high/low (adaptive order) → **close as the final tick**, then sets `_fill_at_market = True`. A marketable order submitted during `on_bar(bar_t)` therefore meets an L1 book whose last update IS bar_t's close.
2. *Empirical probe (decisive).* Using the exact venue setup of `run_backtest_for_symbol` (maker_taker fees, `one_tick_slippage`, ETHUSDT 15m catalog bars) and a probe strategy submitting one market BUY during `on_bar`:
   - signal bar ts=2024-08-23 07:29:59.999Z, O=2677.50 H=2679.30 L=2670.15 **C=2672.10** → **fill avg_px = 2672.11 (= close + one 0.01 tick), ts_init = 07:29:59.999.999000064 — identical to the signal bar's timestamp**;
   - exit submitted on next bar C=2668.35 → filled 2668.34 (close − 1 tick), again same-bar;
   - fill price equals bar_t close, not bar_{t+1} open; even where opens happen to equal prior closes, `ts_init` proves execution was modeled AT decision time.
3. *Consequence.* Entry signals are computed FROM `bar_t.close` (e.g., reclaim tests `close > fast.value`, strategy_trend_pullback.py:94–108) and filled AT bar_t.close. No real account can observe a close and also transact at it. This systematically overstates expectancy for reclaim/breakout-style entries across all 77 V1 cells — reported edges are upper bounds. PLAN §9 G1 already flags exactly this ("current-bar signal must not assume same-close fill unless proven"); it is now proven false.

### Fix owners
- **A2:** move execution semantics to next-bar fills (act on previous-bar signal state, or defer queued signals to t+1); declare execution delay in configs and specs.
- **A3/A1:** adopt the regression test below.

### Probe test suggestion (for A3/A1)
`tests/backtest/test_fill_timing_probe.py`: minimal venue mirroring `run_backtest_for_symbol` (maker_taker + one_tick_slippage), ~60 real catalog bars, submit market BUY in `on_bar` of fixed index; assert (i) `fill.avg_px == bar_t.close ± price_increment`, (ii) `fill.ts_init == bar_t.ts_event`, (iii) on a slice where they differ, `fill.avg_px != bar_{t+1}.open`. Include the indicator-inclusion assertion from Finding 2 so any future Nautilus upgrade changing handler ordering fails loudly.

---

## Finding 2 — (b) SIGNAL USES CURRENT-BAR CLOSE WITH SAME-BAR INDICATOR STATE

**Severity: MED standalone; HIGH in combination with Finding 1. Confidence: VERY HIGH (empirical).**

Indicators registered via `register_indicator_for_bars` (strategy_base.py:117–118) are fed bar_t BEFORE `on_bar(bar_t)` executes. Empirical probe: inside `on_bar`, an EMA(10)'s value matched a pandas EMA computed **including** the current bar on 6/6 checked bars, and the through-previous-bar EMA on 0/6. Consequently every "current" comparison in strategies (close vs fast EMA, RSI/Bollinger reads, ATR sized on bar_t's true range) uses full current-bar information, then — per Finding 1 — fills at that same close. This is intra-bar lookahead by composition.

Indicator-same-bar-update alone is conventional; the pairing with same-bar-close fills is what manufactures optimism. Fixing either half removes most of the bias; fixing both (Finding 1's owner actions) is cleanest. Owner: A2 semantics; A3 regression coverage.

---

## Finding 3 — (c) WARMUP CONTAMINATION: warmup-opened positions ARE counted in scored folds

**Severity: LOW–MED. Confidence: HIGH (code reading; both metric paths consistent).**

- `_metrics_in_window` (breakout_wf.py:53–87) selects positions purely by `w_start <= ts_closed <= w_end`. A position **opened during warmup but closed inside the scored fold is counted**, with its full realized PnL.
- `_funding_fold_metrics` (matrix_runner.py:333–375) applies the identical `ts_closed` filter, so raw and funding-adjusted ledgers stay mutually consistent (no raw-vs-funded mismatch).
- Bias direction: **no lookahead leakage** (warmup entries used only pre-window data), but three second-order effects:
  1. fold results partly depend on warmup-period signals → folds not fully independent; effective sample slightly inflated;
  2. multi-fold holds attribute their ENTIRE PnL/funding to the single closing fold → inflates fold-concentration readings (interacts with Finding 4's attribution note and the G3 concentration gate);
  3. positions open at w_end are force-closed by `on_stop` (`close_position_on_stop=True`, strategy_base.py:135–145) at the last in-slice bar's close — all PnL realizes inside its fold, quietly removing gap/carry risk a live account would face (boundary realism optimism).
- Related inconsistency: `positive_folds` feeding `positive_folds_ratio_low` uses **pre-funding** expectancy (matrix_runner.py:476) while headline verdicts use after-funding values. Gate inputs should be canonicalized.

Owner: A2 (implementation); A1 decides canonical gate basis and whether re-scoring policy changes.

---

## Finding 4 — (d) FUNDING AUDIT: multi-day holds handled correctly; reason-code conflation + attribution quirks

**Severity: MED (labeling/aggregation), LOW (per-position math). Confidence: HIGH.**

Per-position math is sound:

- Settlements apply iff `opened_ns <= fundingTime < closed_ns` (reports/funding.py:165–171). The sorted-settlement loop `continue`s past pre-open stamps and `break`s at close, so a position held across many days receives **every** intermediate 8h settlement — no truncation at the position level.
- Sign convention LONG = −rate × notional matches Binance (`data/derivatives.py:147–153`).
- Coverage is enforced: the bundle must span min(ts_opened)..max(ts_closed) across all positions or `build_funding_audit` raises (reports/funding.py:139–153).
- Quantity = `peak_qty × settlement markPrice`; correct for the single-entry netting positions this pipeline generates.

Issues found:

1. **Reason-code conflation (MED).** `_funding_fold_metrics` returns the `funding_coverage_insufficient` sentinel both when data is genuinely unavailable AND when a fold simply has no closed positions (matrix_runner.py:334–342 — empty `pnls` → same dict). In the V1 corpus **all 14 flagged folds had zero trades**: 8 cells carry a data-integrity code that really means "no activity". Misleading codes corrupt rejection-reason statistics downstream.
2. **Exclusion bias channel (MED, latent).** Cell-level after-funding aggregates sum ONLY folds where funding applied (matrix_runner.py:478–485). If a genuine coverage failure ever coincided with active folds, those folds would vanish silently from `exp_after_funding` instead of failing loudly. Today's data shows no such case (every unfunded fold is zero-trade), but the mechanism is unsafe.
3. **Attribution concentration (LOW).** A hold spanning several folds books all its settlements in the closing fold (per-position correctness ⇒ cross-fold attribution skew). This widens fold-PnL dispersion and can trip `fold_concentration_high` for strategies with multi-day holds even when the edge is stable per-day.
4. **baseline_wf variant (LOW).** `_funding_metrics` (baseline_wf.py:66–88) silently returns zeros when the funding path/audit yields nothing — older runner, but any reuse inherits the conflation problem without even a reason code.

Owner: A2 (separate "no positions" from "coverage gap"; fail loudly on partial coverage over non-empty scored sets); A3 to re-label historical artifacts in eval summaries.

---

## Finding 5 — (e) PROVENANCE GAPS vs PLAN §7 MANIFEST CHECKLIST

**Severity: HIGH relative to Sprint-V2 G2 ambitions (the V1 artifacts could not support an independent rerun verdict today). Confidence: HIGH.**

What IS present per cell artifact: `config_sha256`, `data_snapshot_id` (catalog|symbol|window), `split_policy`, `fee_model`, `slippage_model`, `seed`, warmup_days, fold/window declarations, experiment_id, generated_at_utc. That is a decent skeleton but falls far short of PLAN §7. Enumerated gaps:

| # | PLAN §7 requirement | Status in V1 cells | Risk |
|---|---|---|---|
| 1 | `git_commit_at_launch` | **absent** | code state irreproducible (only config hash pins inputs, not logic) |
| 2 | `dirty_worktree_at_launch` | **absent** | uncommitted local edits could have altered behavior undetectably |
| 3 | `exact_argv` | **absent** | CLI invocation not reconstructable (folds/symbols/window came from argv) |
| 4 | `parameter_lock_utc` (+ run_started) | **absent** | cannot prove parameters were frozen BEFORE the run |
| 5 | frozen candidate snapshot file | **absent** — only sha256 of a mutable path (e.g., `research/hypotheses/H-VOLCOMP-BRKOUT-v1/candidate.yaml` referenced by path+hash; the file itself is NOT copied into the artifact dir) | path can drift/rebase; hash alone is unverifiable if file changes later |
| 6 | frozen config snapshot file | same as #5 (hash of `config/*.yaml`, no copy) | same drift risk |
| 7 | `data_manifest_path/sha256` + universe_snapshot | **absent** (data freshness delegated to external `data_audit`) | cell cannot self-certify its input data |
| 8 | `purge_bars` / `embargo_bars` | **absent** — `fold_windows` explicitly declares "no overlap, no embargo" (matrix_runner.py:204) | purge/embargo policy undocumented; acceptable only if pre-declared as zero |
| 9 | `declared_parameter_combinations` / executed / prior_family_trials | **absent for inventory strategies** (49 cells have no hypothesis_id/candidate_version at all) | trial-budget accounting impossible for inventory runs |
| 10 | owner_agent / validator_agent / hypothesis linkage | absent except volcomp | unclear accountability chain |
| 11 | experiment identity robustness | `experiment_id = EXP-<date>-<HHMM>` generated once per matrix from wall-clock (matrix_runner.py:590); registry uses a DIFFERENT numbering (e.g., EXP-20260823-0061 vs cell EXP-20260823-0848) | collision-prone across matrices started in the same minute; two competing ID systems confuse cross-referencing |
| 12 | `funding_mode` declared field | implicit only (audit fields present) | spec asks for explicit native-vs-audited declaration |

Also note: resume/index reuse keys on identity WITHOUT data freshness (deliberate, matrix_runner.py:289–300 docstring) — safe only if G0 audit runs separately and its result is bound into the manifest; currently it isn't.

Owner split: **A1** owns the §7 manifest schema + lock semantics (protocol layer); **A2** implements capture inside `matrix_runner` (argv/commit/dirty-state snapshots, artifact-local copies of config+candidate, purge/embargo fields, single canonical experiment-id scheme). These gaps are exactly what H4/H9-style gates exist to close before H-FUNDCROWD runs.

---

## Finding 6 — Execution realism extras (supporting findings)

1. **Zero-spread book from LAST-price bars (MED).** Bars are PriceType.LAST → the venue book is built from synthesized trade ticks; best bid ≈ best ask ≈ last price. Market orders therefore cross a ~zero spread plus one modeled tick. Real altcoin perpetuals routinely show spreads of many ticks on 15m horizons; one-tick slippage is likely generous to the strategy. Owner: A2/A1 to declare spread stress in G4 (two-tick adverse fill already planned — keep it).
2. **Maker/taker fees correct (info).** `MakerTakerFeeModel` charges instrument taker rates on the taker fills observed (probe: both fills `liquidity_side=TAKER`). No fee optimism found.
3. **Daily-loss/cooldown machinery driven by bar timestamps** (`_roll_trading_day` on every bar, strategy_base.py:156–159) — consistent between backtest/live paths; no finding.

---

## Verdict summary table

| # | Finding | Severity | Bias direction | Fix owner |
|---|---|---|---|---|
| 1 | Same-bar-close fill of on_bar market orders (probe-proven) | **HIGH** | inflates expectancy (upper bound) | A2 fix; A3/A1 probe test |
| 2 | Indicators include current bar in on_bar (probe-proven) | MED (HIGH w/ #1) | intra-bar lookahead with #1 | A2; A3 tests |
| 3 | Warmup-opened positions counted by ts_closed; boundary force-closes; positive_folds computed pre-funding | LOW–MED | sample inflation / attribution noise; gate-input inconsistency | A2; A1 canonicalization |
| 4 | Funding audit: multi-day OK; `funding_coverage_insufficient` conflates zero-trade folds (14 real cases); silent fold exclusion channel | MED | misleading reason codes; latent exclusion bias | A2; A3 relabel |
| 5 | Provenance vs PLAN §7: git commit/dirty/argv/lock timestamps absent; candidate+config hashed-not-snapshotted; no purge/embargo fields; dual experiment-id systems | HIGH (for G2) | auditability, not PnL | A1 schema; A2 capture |
| 6 | Zero-spread L1 book + one-tick slippage | MED | optimistic costs | A1/A2 declare stress |

**Overall:** the V1 pipeline is structurally sane (no catastrophic double-counting, funding math per-position correct, raw/funded ledgers consistent), but its reported expectancies are upper bounds due to same-bar-close execution, and its provenance cannot yet satisfy the Sprint-V2 reproducibility contract. Both must be addressed before H-FUNDCROWD results can be trusted; this aligns with the phase rule that H-FUNDCROWD implementation waits for A1's H4/H9/H14 PASS.

*Companion documents:* `v1_negative_analysis.md` (77-FAIL post-mortem), `fundcrowd_spec_draft_v2.yaml` (corrected pre-registration).
