# A7 Terminal Challenge Memo — V7 family `v7_xsect_funding_price_divergence`

- Auditor: A7 (independent), session `orca/v7-a7-audit`
- Audited head: `c7e9d94481ccf93c4f685a34e40cba4a35c42fdd` (primary, clean)
- Created: 2026-08-25T14:17:45Z
- Population: `results/portfolio_v7` (4 trials), `results/reproduction_v7` VERIFY-V7-DIV-{1D,3D,7D,REV3D}, `results/matrix/v7_xsect_funding_price_divergence/{index,report,reconciliation,family_summary,statistical_haircut,finalizer_outputs}.json`, registry tail (CELL_RESULT + verify rows), `research/audits/v7p/*`.
- Method: read-only on primary; every headline number recomputed from raw artifacts (ledger / positions.jsonl / registry jsonl) in this worktree.

## Verdict

**AUDIT_VERDICT: PASS** — machine family verdict `V7_REJECT_ALL_CANDIDATE` is justified and reproduced. Unresolved high/critical findings: **0**.

## Check 1 — Per-trial metrics & verdicts; FG2 ⇒ REJECT_ALL

Recomputed PnL and MDD independently from `portfolio_ledger.jsonl` equity curve; PF at closed-leg (position) level per artifact definition. All match `canonical_metrics.json`, registry CELL_RESULT rows, and `family_summary.json` to full float precision:

| Trial | PnL (recalc) | PF (closed-leg) | MDD (recalc) | Verdict (registry=index=summary) | scorecard.total |
|---|---|---|---|---|---|
| XSECT-FUND-PRICE-DIV-1D | −5,982.48 | 0.976461 | 0.164501 | REJECTED | 15 |
| XSECT-FUND-PRICE-DIV-3D | −3,443.75 | 0.983489 | 0.139742 | REJECTED | 15 |
| XSECT-FUND-PRICE-DIV-7D | +938.24 | **1.004910** | 0.153139 | REJECTED | 20 |
| XSECT-FUND-PRICE-DIV-REV-3D (control) | −23,415.55 | 0.887646 | 0.282582 | CONTROL_ONLY | 15 |

FG2 "PF ≥ 1.10" is preregistered (PLAN.md:428). All three directional trials fail it — the best is 7D at PF 1.00491 ≈ coin-flip after costs. The control losing −23.4k (worse than every treatment) plus `adjacent_positive_pair=false` and `eligible_candidates=[]` makes **REJECT_ALL justified**.

Note (F1): the machine `final_gate_result.json` reports FG2 PF criterion `NOT_TESTED` (`min_profit_factor_threshold_missing`) — the preregistered numeric thresholds were not wired into the resolved contract's machine-gate block, so the gate failed closed instead of evaluating. Substantively irrelevant here (PF<1.10 fails regardless, and FG2 also fails on `no_negative_fold`: F2 negative in all directional trials), but see Findings.

## Check 2 — Concentration (positive pnl only, closed legs)

Recomputed from `positions.jsonl` closed legs (`canonical_pnl > 0`); matches `concentration_report.json` (leg-level POSITIVE_AGGREGATE_PNL_ONLY_V1) exactly:

| Trial | top positive fold | share | top positive symbol | share |
|---|---|---|---|---|
| 1D | F1 | 39.37% | ADAUSDT | 21.50% |
| 3D | F1 | 38.56% | DOGEUSDT | 19.30% |
| 7D | F1 | 42.30% | ADAUSDT | 19.70% |
| REV-3D | F1 | 43.18% | LINKUSDT | 17.62% |

FG3 is moot given FG2 rejection. Definitional duality noted (F2): `canonical_metrics.top_*_share` uses a *net-aggregate* variant (fold/symbol NET pnl, positives only: e.g. 7D F1 = 5601.10/(5601.10+2547.51) = 68.74%, ETHUSDT 30.58%) — I reproduced those numbers exactly under that definition too. Both artifacts are internally consistent; they answer different questions. If FG3 is ever revived, pin which estimator the gate consumes.

## Check 3 — Reproduction

All four `results/reproduction_v7/VERIFY-V7-DIV-*/comparison.json`: `all_match=true`, `rerun_process_separate=true`, comparison surface `full_v6p_n11`, **15 components** each (accounting_reconciliation, artifact_hashes, canonical_metrics, commission_slippage, exposure_control, fold_returns, funding_cashflows, gate_result_verdicts, ledger, orders, positions, scorecard_totals, signals, stress_report, terminal_positions) with identical source/rerun sha256 pairs. Completeness ≥ 15 satisfied. Registry verify verdicts: PASS ×4 (13:40–13:59Z). Reproduction 4/4 confirmed.

## Check 4 — Reconciliation & budget

`reconciliation.json`: `final_verdict="COMPLETE"`, `mismatches=[]`, `registry_append_only_verified=true`; counts 4/4/4/4/8 consistent with my independent scan of `results/registry/experiments.jsonl` (533 rows, append timestamps monotone non-decreasing → append-only holds). Scored V7 rows = **exactly 4** CELL_RESULT (REJECTED×3, CONTROL_ONLY×1). Budget: V6 carry scored 4 + V7 scored 4 = **8 total used** (= `statistical_haircut.effective_n_trials_scored_to_date=8`). Finalizer: all 4 `NOT_ELIGIBLE` (machine 0/4 eligible).

## Check 5 — Statistical haircut honesty

Sentinels present verbatim: `"dsr": "DSR_UNAVAILABLE_FAIL_CLOSED"`, `"pbo": "PBO_UNAVAILABLE_FAIL_CLOSED"`. The aligned matrix exists: 8 configs × n_days=394 each (min_days≈394 as expected). `pbo_note` states CSCV preregistered partitions not yet wired into dsr.py. Verified honest against code: `research/dsr.py::pbo_cscv` exists with fail-closed governance (`NOT_ENOUGH_CONFIGURATIONS` unless ≥ min configs/partitions) — no caller wiring exists, so reporting unavailable rather than invoking the primitive with an ad-hoc partition scheme is the honest fail-closed choice. Nothing fabricated.

## Check 6 — Provenance chain

- `baseline_root.json.launch_head = 653ce08d…6533ce08d3fe7fd711772c89c59129e9ec8732f4` ✓; `resolved_run_contract.launch_sha` identical ✓.
- Attestation pins vs **current bytes** (recomputed by me):
  - baseline_root.json → `6853a003…defcfb4f5` == pin ✓
  - resolved_run_contract.json → `7db4d6b9…79112fb5` == pin (both attestation & baseline_root) ✓
  - worktree_manifest.json (v7_twelve_hour_run) → `92e62fee…fa2fbe7d` == pin ✓
- `preflight.json` (schema v3, head 3475dfd, final_code_sha 6533ce0): **14/14 checks true**, `preflight_pass=true`.

## Check 7 — V8 prereg freeze

- Trio frozen in `research/audits/v8p/v8_spec_freeze.json` at **2026-08-25T12:24:23Z** < first V7 scored artifact (**2026-08-25T13:24:43Z**, registry first V7 CELL_RESULT append). Freeze-before-first-score rule satisfied.
- Hashes re-verified by me now against current bytes:
  - candidate.yaml `9dcd0ea3…5c75cfc4` ✓, hypothesis.md `a0439a20…573dc` ✓, status.yaml `6e58feeb…332516` ✓, novelty memo `0501fc08…351ae` ✓.
- Novelty: memo compares all six catalog entries; verdict **DISTINCT** for each (incl. exact-sign-flip distinction vs H-XSECT-MOM-v1 and spread-vs-rank distinction vs V7 divergence); v1→v2 delta is data-availability universe rule only, frozen pre-results. Attestation records `NOVEL_MATERIAL_DISTINCT`.
- `a7_hash_verified=true` is set **by me, now**, in `research/audits/v7/scientific_audit.json` (this audit) — the spec_freeze field remains `PENDING_A7_HASH` upstream, correctly untouched.

## Check 8 — No S1 / live

No S1/live/mainnet/api-key markers in worktree manifest, resolved contract (execution_contract is worker waves only), launch manifests (`execution_mode: NEXT_BAR_EVENT_BASELINE`, `funding_mode: audited-post-trade`), or environment. Preflight `no_s1_live_in_diff=true`. All results are backtest/paper semantics.

## Findings register

| ID | Severity | Finding | Action |
|---|---|---|---|
| F1 | MEDIUM (non-blocking) | Preregistered FG numeric thresholds (PF≥1.10 etc.) absent from resolved contract machine-gate block → gates report NOT_TESTED fail-closed rather than evaluating. Outcome unaffected (REJECT_ALL conservative), but future families must wire thresholds pre-launch. | Carry into V8 contract generation checklist |
| F2 | LOW | Dual concentration definitions (net-aggregate in canonical_metrics vs leg-level gross-positive in concentration_report). Both reproduced exactly; document gate-facing estimator if FG3 revived. | Note only |
| F3 | INFO | `spec_freeze.first_v7_scored_artifact_utc` left null post-hoc (freeze ordering still independently provable from timestamps). | Optional backfill |
| F4 | INFO | `exposure_control.jsonl` hashes equal empty-sha (e3b0c442…) consistent with `exposure_control_rows=0`. | None |

Unresolved high/critical: **none**.

— A7, independent auditor
