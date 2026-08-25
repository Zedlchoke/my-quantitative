# A7 Independent Challenge Memo — V6 family `v6_xsect_funding_carry`

- Auditor: A7 (independent), session `orca/v6p-a7-independent-audit`
- Primary HEAD observed: `e27692e5620b92faac95949d3c3a93314b6917a8` (read-only)
- Interpreter: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`
- Scope: 4 scored trials under `results/portfolio_v6/` (1D, 3D, 7D carry; REVERSE-3D control),
  matrix artifacts `results/matrix/v6_xsect_funding_carry/*`, reproductions
  `VERIFY-V6-CARRY-7D-R4` and `VERIFY-V6-REVERSE-3D-R3`, registry shards + tail rows,
  `research/audits/v6/v6_family_transition_input.json`.
- Method: every gate-relevant number below was **recomputed from raw row-level artifacts**
  (positions.jsonl, funding_cashflows.jsonl, portfolio_ledger.jsonl, orders.jsonl), not copied
  from summary JSONs. Summary files were used only as cross-checks.

## 1. FG3 conjunction recomputation (raw rows)

| check | CARRY-1D | CARRY-3D | CARRY-7D | REVERSE-3D (control) |
|---|---|---|---|---|
| total pnl (positions sum) | −5 679.96 ✗ | +2 076.03 ✓ | +20 580.87 ✓ | −20 102.83 ✗ |
| net funding (Σ cashflows) | +1 958.03 ✓ | +2 129.47 ✓ | +2 277.23 ✓ | −1 677.84 ✗ |
| position PF ≥ 1.10 | 0.9784 ✗ | 1.0116 ✗ | 1.1570 ✓ | 0.8699 ✗ |
| ≥2/3 folds pnl>0 | 2/3 ✓ | 2/3 ✓ | 2/3 ✓ | 1/3 ✗ |
| ≥2/3 folds funding>0 (funding_allocated per experiment_fold) | 3/3 ✓ | 3/3 ✓ | 3/3 ✓ | 0/3 ✗ |
| median continuous fold return > 0 | +0.07067 ✓ | +0.06950 ✓ | +0.09172 ✓ | −0.12338 ✗ |
| rebalances ≥ 90 | 364 ✓ | 364 ✓ | 364 ✓ | 364 ✓ |
| legs ≥ 100 | 1 037 ✓ | 872 ✓ | 761 ✓ | 855 ✓ |
| top fold ≤ 50% of positive pnl | F1 56.51% ✗ | F2 55.60% ✗ | **F1 51.66% ✗** | F3 100% ✗ |
| top symbol ≤ 40% of positive pnl | XRP 60.78% ✗ | ETH 53.68% ✗ | ADA 36.54% ✓ | SOL 93.84% ✗ |

All values match `family_summary.json` fg3 dicts where the artifact reports them.
**Addition:** the artifact fg3 dict omits PLAN §10 FG3's concentration clauses
(top fold ≤50%, top symbol ≤40%). Recomputed, 7D fails FG3 explicitly on
top-fold concentration (F1 = 51.66% > 50%), in addition to the PF/net-funding
failures that already disqualify 1D and 3D. No directional trial passes full FG3.

## 2. No eligible candidate — confirmed, with one refuted sub-claim

- `family_summary.eligible_candidate = null` — verified correct.
- **REFUTED sub-claim:** "7D MDD = 0.2885 > 0.10 hard risk fail". Recomputed MDD from the
  full 37 862-row ledger equity curve for XSECT-FUND-CARRY-7D is **0.088350 ≤ 0.10**,
  byte-consistent with canonical_metrics and with the R4 independent rerun
  (`mdd_match: true`). The value 0.28851675 appears **only** in superseded buggy reruns
  (`VERIFY-V6-CARRY-7D-R2`, harness env-deletion bug) — it is not a property of the frozen
  source artifacts. XG5 for 7D is PASS with `mdd_lock_blocker=false`. 7D is therefore
  **not** a risk_fail(MDD); it is ineligible via FG3 concentration + un-gated robustness +
  INCONCLUSIVE cell status + DSR unavailable.
- Adjacency note does not rescue: `invalidation_checks.adjacent_positive_pair = true`
  (3D +2 076 and 7D +20 581 both pnl>0) only blocks mechanism-invalidation item #5;
  it confers no eligibility because each member independently fails its own gates
  (3D: PF<1.10, MDD 15.18%>10%, symbol 53.68%; 7D: top-fold 51.66%, XG4 not gated).

## 3. Reverse control

Verdict CONTROL_ONLY (`is_negative_control=true`, score DIAGNOSTIC_ONLY). PnL −20 102.83
loses to best directional +20 580.87 → invalidation item #9 ("reverse beats best") NOT
triggered. Control carries negative funding (−1 677.84) as expected for sign-flipped carry.
Control rows are never promotable (CONTROL_ONLY verdict + DIAGNOSTIC_ONLY score mode in
shard and experiments.jsonl). §9.3 item 9 not triggered — confirmed.

## 4. Stress

All four runs: `executed_unconditionally=true`; 13 variants each across 5 complete families
(adverse_two_ticks ×1, fee_x1_5 ×1, extra_one_event_delay ×1, drop_one_fold ×3,
drop_one_symbol ×7); all variants executed. Stress is explicitly diagnostic
("a negative base edge remains REJECTED regardless of variant outcomes"); base_edge_verdict
equals the cell verdict on all four runs and no variant flips any base verdict.

## 5. Risk census

4 runs × 37 862 ledger rows scanned row-by-row:
max gross_exposure 0.96274 (REVERSE) ≤ 1.00+tol; max |net_exposure| 0.06867 (REVERSE)
≤ 0.10+tol; **zero violations**; margin_breach_rows=0 on all runs; |BTC beta| ≤ 0.0227
for all trials (limit 0.25). Exposure-control events: exposure_control.jsonl present but
empty (0 events) on all four real runs — consistent with caps never being breached;
risk_mode_active=true recorded; source and rerun empty-file hashes identical
(e3b0c442…). Logged as LOW observation F-4, not a census failure.

## 6. Reproduction

- R4 (CARRY-7D) and R3 (REVERSE-3D): `all_match=true`, schema 5, `rerun_process_separate=true`,
  tolerance 1e-09. Component list = **15 ≥ 14**, including accounting_reconciliation,
  funding_cashflows, exposure_control, stress_report, gate_result_verdicts, scorecard_totals,
  artifact_hashes (+canonical_metrics, commission_slippage, fold_returns, ledger, orders,
  positions, signals, terminal_positions). All component sha256 pairs match.
- Earlier VERIFY-*-R1/R2 mismatches fully explained: commit `fe31440` shows the harness
  deleted inherited `PORTFOLIO_SIGNAL_FAMILY` from flagless rerun workers, silently
  dispatching a different signal family (R2 rerun pnl +4 413.69 / mdd 0.28852 vs source
  +20 580.87 / 0.08835). Documented in v6_family_transition_input.json
  ("earlier R2 mismatched due to env bug now fixed"). Verify shard preserves append-only
  history: FAIL rows for R1/R2 followed by PASS rows for R3/R4. Supersession valid.

## 7. Matrix reconciliation & budget

`reconciliation.json`: final_verdict COMPLETE, mismatches [], registry_append_only_verified=true,
4/4 cells completed. Registry: CELL_RESULT shard+tail rows exist for exactly the four scored
trials; verify-shard rows appended for six verification attempts (2 PASS final).
Budget: run_contract trial_budgets {v6_scored 4, v7_scored 4, total_new_scored_max 8};
event log records "4/4 scored consumed by pre-suspension quartet" → **scored count 4/8**.

## 8. DSR/PBO honesty

`dsr_pbo_report.json`: dsr_probability=null with explicit reason (fold-level series n=3
insufficient for deflated Sharpe at frozen estimator settings); pbo="NOT_ENOUGH_CONFIGURATIONS".
Honest nulls, no fabrication — zero score contribution per FG6 fallback semantics.

## 9. Family verdict input consistency

Recommended `V6P_PASS_V6_CANDIDATE_FAIL` is justified and **agreed**: pipeline surfaces
valid (XG0/XG1 pass, hashes clean 21/21 per trial — independently re-verified by sha256,
matrix complete, append-only true, reproduction green post-fix), while every directional
candidate fails hard gates. Taxonomy review:
- 1D `mechanism_failure` — agreed (pnl<0, PF<1).
- 3D `edge_too_weak_pf_below_hard_min` — agreed (PF 1.0116); note it additionally fails
  MDD (15.18%) and symbol concentration (53.68%) — risk co-failures worth recording.
- 7D input label `inconclusive_pending_reproduction_adjacency_fail` is stale post-R4:
  reproduction now PASSes, and a raw-pnl adjacent positive pair (3D&7D) *does* exist.
  **I do NOT reclassify to risk_fail(MDD)** (recomputed MDD 8.84% ≤ 10%).
  My classification: **`fg3_concentration_fail_top_fold_gt_50pct_with_robustness_inconclusive`**
  — edge is real but concentrated (F1 = 51.66% of positive pnl) and FG4/XG4 gating plus DSR
  were never completed.
- REVERSE `negative_control_as_expected` — agreed.

## 10. Launch manifests

All four manifests: argv contains only local interpreter/script paths and offline flags
(--experiment-id/--lookback-days/--window-start/--window-end/--folds/--output-root/
--matrix-id/--registry-kind/--signal-family/--registry-path); **no env blocks; zero matches**
for S1/live/API/token/secret strings. No live surface anywhere in the launch surface.

## Findings summary

- **F-1 MEDIUM**: audit-brief claim "7D MDD=0.2885>0.10 (FG5 fail)" refuted by frozen
  artifacts (recomputed 0.088350; 0.28852 exists only in superseded buggy R2 rerun and the
  unrelated v6p MOM trial). No impact on family verdict — 7D fails eligibility on other grounds.
- **F-2 LOW**: family_summary fg3 dict omits FG3 concentration sub-clauses; including them
  makes 7D's FG3 failure explicit. Conclusion unchanged.
- **F-3 LOW**: transition-input taxonomy for 7D stale post-R4 (repro PASS; adjacency pair
  exists at raw-pnl level); relabel recommended (see §9 classification).
- **F-4 LOW**: exposure_control.jsonl emitted zero events on all four real runs; consistent
  with no cap breach, but reduce-only enforcement remains unevidenced-by-exercise.
- **F-5 INFO**: XG4 robustness gate left not_tested/INCONCLUSIVE at gate level although
  diagnostic stress variants ran; future eligible-candidate paths require FG4 gating.

No HIGH or CRITICAL findings. Verdict: **PASS**; family verdict agreed:
**V6P_PASS_V6_CANDIDATE_FAIL**.
