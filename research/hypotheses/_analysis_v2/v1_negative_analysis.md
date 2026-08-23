# Sprint V1 Negative Analysis — 77 FAIL Post-Mortem

- **Author:** A4 (quant researcher / independent reviewer), Sprint V2
- **Date:** 2026-08-23
- **Sources (read-only):** `results/stage_a/sprint_summary_20260823T085842Z.json` (49 combos, matrix `stage_a_s0_20260823`), `results/stage_a/sprint_summary_20260823T090218Z.json` (28 combos, matrix `stage_a_volcomp_iter1`), and all 77 cell artifacts under `results/matrix/*/cells/*.json`.
- **Scope of this memo:** descriptive post-mortem only. It exists to inform *future hypothesis families* (per PLAN §16 step 1). See the red-line statement at the end.

---

## 1. Headline

| Metric | Value |
|---|---|
| Combos evaluated | 77 (49 inventory + 28 volcomp grid) |
| PASS | 0 |
| CANDIDATE_FAIL | 77 |
| INCONCLUSIVE | 0 |
| Cells with positive after-funding expectancy | 8 / 77 (all still FAIL on ≥1 hard gate) |

No candidate survived Stage A. Every failure below is reported exactly as recorded; nothing in this document may be used to modify, re-parameterize, or "rescue" any of the 77 candidates (see §7).

## 2. Distribution of rejection reasons

Two layers record reasons: factual observations computed inside each cell (`matrix_runner.execute_cell`) and gate verdict reasons attached by the sprint evaluator (`sprint_eval` + `contracts.protocol`). Counts per reason code across all 77 combos:

### Gate-layer verdict reasons (sprint summaries)

| Reason code | Meaning | Count (of 77) |
|---|---|---:|
| `fold_pf_below_floor` | some fold with ≥5 trades has PF < 0.80 | 70 |
| `exp_nonpositive` | aggregate after-cost expectancy ≤ 0 | 69 |
| `pf_below_min` | aggregate position PF < 1.10 | 69 |
| `positive_folds_ratio_low` | fewer than 2/3 folds positive after cost | 68 |
| `fold_concentration_high` | one fold contributed >50% of total PnL | 63 |

### Cell-level factual observations (cell JSONs)

| Reason code | Count | Note |
|---|---:|---|
| `exp_nonpositive` | 69 | matches gate layer exactly |
| `positive_folds_ratio_low` | 68 | matches gate layer exactly |
| `funding_coverage_insufficient` | 8 cells / 14 folds | **caveat:** inspection shows every flagged fold had ZERO closed trades — the code conflates "no activity" with genuine funding-data gaps (`matrix_runner._funding_fold_metrics` returns the same sentinel when `pnls` is empty) |
| `trades_below_min` | 6 | all six are breakout cells (<20 trades/symbol, see §5) |

Interpretation: failures are not marginal — 90% of combos fail expectancy and PF simultaneously, and ~90% fail fold-stability. The typical V1 combo loses roughly a full round-trip cost per trade.

## 3. Dead strategies (consistently negative, large samples)

Per-symbol after-funding expectancy in USDT/trade (trades in parentheses), frozen params, S0 window 2025-08-21 → 2026-08-21, 3 chronological folds, 15m bars, maker/taker + one-tick slippage + funding audit:

| Strategy | ADA | BNB | DOGE | ETH | LINK | SOL | XRP | #neg symbols | Σ trades | avg exp/trade |
|---|---|---|---|---|---|---|---|---|---|---|
| ema_atr | −0.460 (392) | −0.312 (374) | −0.296 (384) | −0.370 (415) | −0.395 (407) | −0.455 (379) | −0.489 (379) | 7/7 | 2,730 | **−0.397** |
| mean_reversion | −0.610 (383) | −0.362 (335) | −0.669 (340) | −0.223 (278) | −0.489 (370) | −0.521 (304) | −0.568 (361) | 7/7 | 2,371 | **−0.492** |
| regime_switch | −0.612 (562) | −0.368 (523) | −0.506 (523) | −0.213 (487) | −0.274 (551) | −0.469 (494) | −0.449 (537) | 7/7 | 3,677 | **−0.413** |
| trend_pullback | −0.753 (328) | −0.339 (372) | −0.185 (341) | −0.375 (405) | −0.596 (385) | −0.331 (408) | −0.068 (335) | 7/7 | 2,574 | **−0.378** |

**Verdict — DEAD as configured.** All four strategies are negative in **every one of 28 symbol-cells**, over 2,300–3,700 trades each. The loss per trade (~−0.38 to −0.49 USDT on ~100 USDT max notional ≈ −0.4%/trade) is the same order as modeled round-trip cost (taker in/out ≈ 0.10% + one-tick slippage + adverse funding), i.e., these signals carry no gross edge large enough to survive costs anywhere in the S0 universe. With 28/28 consistent negatives and n ≥ 278 per cell, this is not noise. Honest caveat: without gross-of-cost reporting we cannot fully separate "negative alpha" from "zero alpha minus costs"; either way there is nothing to salvage at current cost levels. The vol_compression_breakout family adds 28 more combos averaging exp ≈ −0.40 with 3,053 trades — also dead outside BNB (see §4).

These four remain dead for ANY future family that would reuse their entry logic unchanged. New hypotheses must change the mechanism (e.g., gating, different horizon, different signal source), not just thresholds — and any such change counts against trial budgets as a new version.

## 4. Positive-but-gate-blocked combos, and why each block matters

8 of 77 combos show positive after-funding expectancy yet FAIL. Fold PnL = after-funding USDT per fold (chronological folds F0/F1/F2).

| Combo | Trades | exp_af (USDT/t) | Σ fold PnL_af | Fold PnLs (F0/F1/F2) | \|top\|/\|total\| | Gates hit |
|---|---:|---:|---:|---|---:|---|
| breakout ETH base | 5 | +1.586 | +7.93 | +7.93 / 0 / 0 | **1.000** | ratio_low, conc |
| breakout BNB base | 47 | +0.321 | +15.08 | +8.54 / +6.54 / 0 | **0.566** | conc |
| reclaim_mr ETH | 75 | +0.189 | +14.17 | −16.85 / +21.30 / +9.72 | **1.503** | fold_pf_floor (F0 PF .718 @31t), conc |
| markdown_breakdown ADA | 139 | +0.078 | +10.86 | +8.68 / −30.20 / +32.38 | **2.981** | conc |
| markdown_breakdown BNB | 55 | +0.212 | +11.65 | 0 / +27.23 / −15.58 | **2.337** | ratio_low (1/3), fold_pf_floor (F2 PF .715 @23t), conc |
| markdown_breakdown ETH | 83 | +0.092 | +7.63 | −2.38 / −16.23 / +26.24 | **3.437** | ratio_low (1/3), conc |
| volcomp BNB v2 | 154 | +0.219 | +33.67 | +24.09 / −2.67 / +12.25 | **0.715** | conc |
| volcomp BNB v3 | 135 | +0.302 | +40.83 | +24.76 / −1.82 / +17.89 | **0.606** | conc |

### Concentration math (requested cells)

Gate: no fold contributes >50% (`MAX_SINGLE_FOLD_CONTRIBUTION = 0.50`, implemented in `sprint_eval._combo_inputs` as |top fold| / |net total|):

| Combo | top-fold PnL | net total PnL | \|top\|/\|total\| | Verdict-relevant reading |
|---|---:|---:|---:|---|
| reclaim_mr ETH | +21.30 | +14.17 | 150.3% | >100% because F0 lost −16.85; the two winning folds must first repay F0 before any net edge exists. Sign flips if F1 or F2 is dropped → fails drop-one robustness by construction |
| markdown ADA | +32.38 | +10.86 | 298.1% | F1 lost −30.20 while F2 made +32.38: this is regime-switching luck (one markdown leg), not an edge; PF pattern (+1.06/+0.81/+1.31) straddles 1.0 |
| volcomp BNB v2 | +24.09 | +33.67 | 71.5% | Least fragile of the set: F2 independently earns +12.25 with PF 1.40; but F0 alone still carries >2/3 of net profit |
| volcomp BNB v3 | +24.76 | +40.83 | 60.6% | Same shape as v2 with slightly better margins; still >50% from one fold |

Why each block matters:

- **>100% cases (reclaim_mr ETH, markdown ADA/BNB/ETH):** the concentration number exceeds 100% precisely because another fold *lost* money. These are not "concentrated profits" but sign-unstable results; G3 blocks them correctly, and G4's drop-one-fold test would flip signs anyway.
- **volcomp BNB v2/v3 (>50%, <100%):** genuinely profitable-looking with healthy per-fold PFs (F0 1.40–1.47, F2 1.40–1.75, F1 ≈0.94–0.95), but the majority of net PnL comes from one fold (Aug→Dec 2025). Under PLAN §9 G3's literal wording ("no fold contributes >50% of positive total PnL") v3 computes 24.76/(24.76+17.89) = 58.1% and v2 = 66.3% — still blocked, so the discrepancy between plan wording and implementation (denominator includes losses) does not change these verdicts. A1 should nonetheless pin down which definition is canonical.
- **All three volcomp positives are the same symbol (BNB):** symbol breadth = 1/7, which matches H-VOLCOMP-BRKOUT-v1's pre-registered invalidation ("edge confined to a single symbol"). This is the signature of a universe artifact (BNB-specific volatility regime), not a transferable mechanism.
- **breakout ETH:** blocked additionally by sample size — see §5.
- **breakout BNB:** passes everything except concentration (56.6%) with zero trades in F2 — its "stability" rests on two active folds out of three.

## 5. Sample-size caveats

- Breakout trade counts per symbol: XRP **1**, ETH **5**, ADA 6, LINK 7, DOGE 11, SOL 18, BNB 47. All except BNB were flagged `trades_below_min`. ETH's +1.59 USDT/trade expectancy rests on **5 trades** — the confidence interval spans nearly any plausible value; it must not be read as promising. Even BNB's 47 trades give a ±~0.3 USDT/trade standard error at observed variance.
- Fold-level floor checks silently skip folds with <5 trades (`FOLD_PF_FLOOR_MIN_TRADES = 5`) — several cells have one or two such folds, so "no fold_pf_below_floor" sometimes means "not testable", not "passed".
- Zero-trade folds (14 across the corpus) are labeled `funding_coverage_insufficient`; downstream users of these artifacts should treat that code as "no scored activity" here, not as a data outage.
- Expectancy is expressed in USDT/trade on a fixed ~100 USDT notional cap; cross-symbol comparisons embed price-scale effects (a USDT is not the same % edge on DOGE as on BTC). Future specs should pre-register R-multiple normalization (PLAN §10.2C already penalizes its absence).

## 6. What did NOT fail

For the record, pipeline facts held up across all 77 runs: 3/3 folds completed everywhere, no `cell_failed_exception`, config hashes and snapshot ids present in every artifact, funding audit applied wherever positions existed (raw vs after-funding deltas are small and signed consistently with observed rates). The failures are strategy/economic failures, not execution artifacts — subject to the pipeline findings in the companion memo `challenge_memo_v1_pipeline.md` (notably same-bar close fills, which bias ALL cells, including the 77 failures, toward optimism; true edges may be even smaller than reported).

## 7. Red line — no post-hoc rescue

**Nothing in this memo may be used to retune, re-gate, re-window, re-universe, or otherwise rescue any of the 77 evaluated candidates.** All 77 saw the full S0 dataset; any modification informed by these results would be in-sample selection dressed as iteration. This analysis exists solely to inform **future hypothesis families** (e.g., which mechanisms are worth a fresh, pre-registered spec with new candidate versions and fresh trial budget). Per Sprint V1 handoff and PLAN §16: rejection reasons feed new hypotheses; they do not reopen old ones.

---

*Companion documents:* `challenge_memo_v1_pipeline.md` (adversarial pipeline review), `fundcrowd_spec_draft_v2.yaml` (the one permitted forward use — a corrected pre-registration written before any new run).
