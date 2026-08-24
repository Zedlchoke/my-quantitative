# V2 → V3 Execution Impact Analysis (A4, Sprint V3)

Author: A4 (Independent Quant Reviewer) · Date: 2026-08-24
Scope: pure artifact analysis. No gates/scorecard/runner/engine/config/results artifacts modified.

## 1. Question

Both rounds score position-level PF after funding on the **identical clean window**
(`2025-08-21T14:30:00Z → 2026-08-21T00:00:00Z`, continuous clean intersection) with
**frozen parameters** and identical split policy (`chrono_wf3fold`), fees
(`maker_taker`) and slippage model (`one_tick_slippage`). The only intended difference:

| Round | Execution semantics | Accounting | Canonical source |
|---|---|---|---|
| V2 | `SAME_BAR_CLOSE_DIAGNOSTIC` — signal bar t close fill | `position_level_after_funding_v2` | `results/stage_a_v2/EXP-*/canonical_metrics.json` |
| V3 | `NEXT_BAR_EVENT_BASELINE` — submit on first event of bar t+1, fill at t+1 close ± slippage ticks | `position_level_after_funding_v3` | `results/stage_a_v3/EXP-*/canonical_metrics.json` |

Deltas therefore **isolate execution semantics** (+ minor path effects: changed fills
propagate into stop/TP paths, trade counts, and funding accrual windows).

## 2. Matching

* Match key: `strategy_type + symbol + param_variant`.
* Result: **98 / 98 V3 cells matched to exactly one V2 experiment** each
  (no duplicates on either side).
* `config_sha256` identical for **77 / 98** pairs. The 21 mismatched are all
  `funding_crowding`: between rounds the frozen `candidate.yaml` gained lifecycle
  status lines (`state: REJECTED` + stamp), which perturbs the file hash. Per the
  coordinator sidecar `research/hypotheses/H-FUNDCROWD-MR-v2/status.yaml`, spec
  rules/grid bytes are unchanged since lock commit `0bc1a4c`; the diff between the two
  frozen copies is metadata-only (verified by direct diff). All 98 pairs are therefore
  parameter-frozen comparisons; we report headline stats both ways.

## 3. Headline distributions

Δ defined as `V3 − V2` unless labelled "optimism" (= `V2 − V3`, the same-bar-close
excess). Expectancy in USDT/trade; PF is position-level profit factor.

### 77 config-identical combos

| Statistic | Δ expectancy (V3−V2) | Δ PF (V3−V2) |
|---|---:|---:|
| median | **+0.0277** | +0.0187 |
| mean | +0.0558 | +0.0286 |
| min | −0.7904 | −0.2771 |
| max | +1.4896 | +0.3910 |
| median \|Δ\| | 0.1394 | — |
| improved / degraded | 42 / 35 | — |

**Optimism magnitude (V2 exp − V3 exp): median −0.0277, mean −0.0558.**
The sign is the opposite of the working assumption: on the median combo, next-bar-close
execution scored *slightly better* than same-bar-close. Same conclusion on all 98
(optimism median −0.0156, mean −0.0413).

Aggregate over matched cells: total canonical PnL −7,208.7 USDT (17,617 trades, V2)
→ −6,491.9 USDT (17,320 trades, V3).

### Sign flips of aggregate expectancy: 7

All 7 inside the 77 config-identical set:

| Strategy | Symbol | Variant | Exp V2 → V3 | PF V2 → V3 |
|---|---|---|---|---|
| markdown_breakdown | ADAUSDT | base | +0.0782 → **−0.1415** | 1.0274 → 0.9546 |
| markdown_breakdown | BNBUSDT | base | +0.1238 → **−0.2198** | 1.0614 → 0.9051 |
| markdown_breakdown | DOGEUSDT | base | −0.0007 → **+0.1335** | 0.9997 → 1.0528 |
| vol_compression_breakout | BNBUSDT | v1 | −0.0499 → **+0.0822** | 0.9461 → 1.1005 |
| vol_compression_breakout | XRPUSDT | v0 | −0.4219 → **+0.0119** | 0.7048 → 1.0096 |
| vol_compression_breakout | XRPUSDT | v2 | −0.1920 → **+0.1693** | 0.8507 → 1.1457 |
| vol_compression_breakout | XRPUSDT | v3 | −0.4121 → **+0.1052** | 0.6983 → 1.0892 |

Pattern: flips concentrate in marginal (|exp| < ~0.2) strategies. The three XRP volcomp
flips are one symbol-family cluster — treat as path noise around zero, not evidence of
delay-*robust* edge. PF ≥ 1.10 count moves 8 → 11 of 98; positive-exp combos 11 → 14
(9 positive in both rounds; 2 lost, 5 gained).

### G3 verdict changes: 2 (both FAIL → PASS)

Only among the 21 fundcrowd pairs (metadata-only hash drift):

| Combo | V2 exp / PF | V3 exp / PF | Folds pos | Verdict |
|---|---|---|---|---|
| funding_crowding ETHUSDT v0 (0155→0713) | +0.5866 / 1.4006 | +0.6187 / 1.4485 | 2/3 → 3/3 | FAIL → **PASS** |
| funding_crowding ETHUSDT v2 (0157→0715) | +0.4934 / 1.3431 | +0.5198 / 1.3793 | 2/3 → 3/3 | FAIL → **PASS** |

funding_crowding ETHUSDT v1 improved identically in shape but still fails G3 by
0.3 pp on fold concentration (top fold = 50.3% > 50%). No other combo among the 77
changed verdict; V2 had 0 G3 PASS overall, V3 has exactly these 2.

## 4. Per-strategy-family optimism (V2 exp − V3 exp), n=77 cfg-identical

| Family | n | median | mean | min | max | improved/degraded |
|---|---:|---:|---:|---:|---:|---|
| breakout | 7 | +0.0199 | −0.2374 | −1.4896 | +0.7904 | 3 / 4 |
| ema_atr | 7 | −0.0395 | +0.0146 | −0.1675 | +0.0988 | 2 / 5 |
| mean_reversion | 7 | +0.0726 | +0.0751 | −0.0391 | +0.2264 | 3 / 4 |
| reclaim_mr | 7 | +0.0451 | +0.0531 | −0.4705 | +0.4187 | 3 / 4 |
| regime_switch | 7 | +0.0326 | +0.0319 | −0.0521 | +0.1714 | 3 / 4 |
| trend_pullback | 7 | +0.0708 | +0.0703 | −0.1314 | +0.2530 | 6 / 1 |
| markdown_breakdown | 7 | −0.0103 | −0.0039 | −0.3436 | +0.4172 | 4 / 3 |
| vol_compression_breakout | 28 | +0.0155 | +0.0412 | −0.5349 | +0.5173 | 15 / 13 |

(funding_crowding, n=21, excluded here as cfg-hash-drifted: optimism mean +0.0119,
median −0.0096.)

Largest single movers: breakout LINK base (exp −5.2122 → −3.7225, tiny-n=7),
breakout ADA base (−2.2580 → −1.0167), volcomp ADA v1 (−0.2141 → −0.7490),
reclaim_mr DOGE base (−0.9094 → −1.3799). Trade counts per combo changed in 76/98
pairs (max |Δtrades| = 21), confirming that delay changes *which* signals survive,
not only prices.

## 5. Fundcrowd ETH v0/v2 deep dive: why delay flipped folds

Fold PnL after funding (`pnl_after_funding` / `profit_factor_after_funding`,
top-fold share of positive total):

**ETHUSDT v0**

| Fold | V2 trades | V2 PnL (PF) | V3 trades | V3 PnL (PF) |
|---|---:|---:|---:|---:|
| f0 (Q4'25) | 31 | −3.241 (0.937) | 30 | **+13.783** (1.319) |
| f1 (Q1'26) | 23 | +11.979 (1.284) | 23 | +11.260 (1.298) |
| f2 (Q2'26) | 26 | +38.188 (2.646) | 26 | +23.834 (1.849) |
| total / top share | | +46.93 / **81.4%** | | +48.88 / **48.8%** |

**ETHUSDT v2**

| Fold | V2 trades | V2 PnL (PF) | V3 trades | V3 PnL (PF) |
|---|---:|---:|---:|---:|
| f0 | 32 | −5.016 (0.906) | 31 | **+12.406** (1.279) |
| f1 | 25 | +18.835 (1.467) | 25 | +17.095 (1.452) |
| f2 | 31 | +29.598 (1.904) | 31 | +15.724 (1.427) |
| total / top share | | +43.42 / **68.2%** | | +45.22 / **34.8%** |

(v1 for reference: V2 f0 −5.016/f1 +13.884/f2 +38.188, top share 81.2% → V3
+12.406/+11.142/+23.834, top share **50.3%** — still FAIL.)

Mechanism, stated from artifacts:

1. **Fold-0 composition flip.** One fewer trade in fold 0 under next-bar fill
   (31→30, 32→31); fold-0 PnL moved from ≈ −3…−5 to ≈ +12…+14. The dropped/marginal
   entries were precisely the ones whose same-bar-close fill chased the reclaim spike;
   deferring one bar avoids the worst chases (empirically, across all V3 ledgers,
   longs fill below the signal-bar reference price 51.4% of the time, median −0.4 bps).
2. **Fat-tail fold-2 compression.** The Q2'26 fold that carried 81% of V2 positive PnL
   shrinks toward the pack (PF 2.65→1.85 v0; 1.90→1.43 v2). Delay removes part of the
   single-fold windfall that V2's concentration clause flagged.
3. Both pre-registered failure modes of V2 (fold0 negative ⇒ <2/3 positive folds; top
   fold >50% contribution) clear simultaneously in v0/v2 — but only just in v1's case
   (50.3%), i.e., the pass sits within path-noise distance of the clause boundary.

Interpretation caution: the improvement is a *redistribution*, not new edge — total
fold-sum PnL barely moves (+46.9→+48.9 v0; +43.4→+45.2 v2). What changed is fold
*shape*, which is what G3 keys on.

## 6. Caveats (honest limits of this comparison)

* Window is the identical clean intersection and params are frozen, so deltas isolate
  execution semantics **up to second-order effects**: changed entry prices alter
  ATR-scaled stops (initial risk), R multiples, daily-loss/cooldown paths and funding
  accrual windows. These are legitimate consequences of the execution change, not bugs.
* Small-n cells (breakout ADA/LINK/XRP ≤ 12 trades) dominate the tails of Δ
  distributions; family means are not robust there.
* 21 fundcrowd pairs carry a lifecycle-stamp hash drift (metadata-only, verified);
  if stricter identity is required, use the 77-combo block.
* V2 schema lacks `expectancy_r`; R-based deltas are not computable for V2.
