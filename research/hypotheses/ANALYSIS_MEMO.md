# Analysis memo — sprint-24h research loop (A4)

**Status:** SKELETON (placeholders until matrix results land) · **Owner:** A4 ·
**Scope:** how Stage-A / scan-matrix outputs will be analyzed for hypothesis
drafts under `research/hypotheses/`, and how near-winners are handled.

## 1. Inputs

- `results/scan_matrix/<stamp>/report.json` — per strategy×symbol rows:
  `trades, positive_folds_after, exp_after, pnl_after, pf_after, buy_hold,
  p_value, bh_q, gate`.
- `results/stage_a/<experiment_id>/` (once H-VOLCOMP-BRKOUT-v1 runs):
  manifest, cells.jsonl, summary.json, gate_result.json, scorecard.json.
- Funding audit blocks inside summaries (`funding_cashflows`,
  `funding_adjustment`) for carry context.

## 2. Method

### 2.1 Tables produced per candidate

1. **Per-symbol table** — trades, expectancy (after cost/funding), position PF,
   positive folds ratio, buy-and-hold context, flat benchmark (=0 hard floor).
2. **Per-fold table** — fold boundaries, trades, PnL, PF; flag folds with
   ≥5 trades and PF < 0.80 (`fold_pf_below_floor`).
3. **Per-quarter table** — calendar-quarter aggregation of closed-position PnL;
   used to describe *where* losing folds concentrate (motivation only).

### 2.2 Concentration checks (before any verdict language)

- Top-fold contribution = max single-fold PnL / total PnL; >50% is a G3 fail.
- Drop-one-fold / drop-one-symbol sensitivity: expectancy sign flips recorded
  as `dropone_signflip` evidence for G4.
- Symbol concentration: one symbol ≤40% of PnL at portfolio level (G5 preview).

### 2.3 EXPLORATORY labeling rule (mandatory wording)

A combo is labeled **EXPLORATORY** iff it fails any strict gate but shows
exp > 0 AND PF ≥ 1.10 on the same window. Scan-matrix survivors are selected
from 58 tested combos ⇒ multiple-testing hazard dominates: BH-FDR q-values are
reported alongside raw p-values, and NO near-winner may be called an edge,
promoted, or tuned post hoc (PLAN §2 rules 8–10). Near-winners from
2026-08-23 (`NEAR reclaim_mr`, `BOME trend_pullback`, `ADA markdown_breakdown`,
`SOL reclaim_mr`) are cited only as motivation for NEW pre-registered
candidates.

### 2.4 Near-winner handling

- Never resurrect parameters of a failed/rejected candidate; new mechanism ⇒
  new `hypothesis_id` + `candidate_version`, locked before scored runs.
- If a near-winner inspires a gate (e.g., funding crowding), the ungated
  baseline MUST be rerun on identical folds in the same experiment so the gate
  demonstrates incremental value; otherwise reject both.
- Watchlist entries expire at sprint end unless locked via verdict
  `LOCK_FOR_FUTURE_OOS`.

## 3. Results placeholders

### 3.1 H-VOLCOMP-BRKOUT-v1 (volatility_compression_breakout)

| Combo (lookback × vol_ratio) | Trades | Exp after | PF | Folds+ | Verdict |
|---|---|---|---|---|---|
| 96 × 1.5 | TBD | TBD | TBD | TBD | TBD |
| 96 × 2.0 | TBD | TBD | TBD | TBD | TBD |
| 192 × 1.5 | TBD | TBD | TBD | TBD | TBD |
| 192 × 2.0 | TBD | TBD | TBD | TBD | TBD |

- Per-symbol table: TBD
- Per-fold table: TBD
- Concentration / top-fold %: TBD
- Fee-stress (+50%) result: TBD

### 3.2 H-FUNDCROWD-MR-v1 (funding_oi_crowding)

| threshold_p | HTF | Trades | Exp after | PF | Δ vs ungated | Verdict |
|---|---|---|---|---|---|---|
| 70 | ON | TBD | TBD | TBD | TBD | TBD |
| 75 | ON | TBD | TBD | TBD | TBD | TBD |
| 80 | ON | TBD | TBD | TBD | TBD | TBD |

### 3.3 H-XSECT-REVERSAL-v1

Blocked (`DATA_INCOMPLETE`): common intersection ~1y < required; portfolio
engine gap. No results table by design.

## 4. Conclusions placeholder

TBD after scored runs; verdict vocabulary limited to PLAN §6 states +
`REJECTED` / `INCONCLUSIVE` / `STAGE_A_PASS_EXPLORATORY` / `LOCK_FOR_FUTURE_OOS`.
