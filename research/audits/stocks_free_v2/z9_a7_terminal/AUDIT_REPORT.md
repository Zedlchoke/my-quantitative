# Z9 A7T — Independent Terminal Audit (STOCKS-FREE-V2)

- Auditor: A7T (independent; verify-only, no repairs)
- Audit worktree: `.worktrees/stocks-free-v2/z9-a7t` @ `66a5eae565738f7d0b4e0600a808e8fd67b58d1c`, branch `orca/stocks-free-v2-z9-a7t`, clean status
- Execution pin verified: z8-exec-1 / z8-exec-2 / z9-reproduce all detached at `106378230abecbaefff4248eeb373794f1b73038` (W1); main `b8876ef8e0f7dd235d66f5cae5bfd8fd9034147f`; integration `66a5eae` clean
- Interpreter: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`; no `.env` read; no API calls; no child agents

## FINAL VERDICT

```
TERMINAL_AUDIT_EXCEPTION_A5_FAIL_CLOSED_IS_RUNNER_ARTIFACT_STRONGEST_CLAIM_IS_REJECT_ALL
```

NOT_PROMOTABLE itself is CONFIRMED and is not in dispute: zero survivors, nothing promotable, S1 sealed. The exception concerns the A5 verdict rationale and, derivatively, the sprint verdict label.

## Per-task results

1. **Ledger — PASS.** All six `artifact_digest` values recompute exactly as `sha256(json.dumps(artifact, sort_keys=True, separators=(',',':')))`, i.e. the staged artifact bytes as written (artifacts unmodified since publication). `observed=6`, `published=6`; 24 entries = 6 x (COMPUTE_RECORDED, digest+publication, FIRST_PUBLICATION, REPLAY_ZERO_DELTA); replay events zero-delta by construction (`TrialLedger.publish` is idempotent). `published_keys` unique (6); arm segments == `selection_freeze.json` arms == `state.json` arms; all keys `US_ETF_CASH|...|S0`.
2. **Cell science — PASS (exact).** My from-scratch valuation loop (independent split adjustment, prev-date lookup, fill-close rebalance, turnover cost, period PnL, MDD; `a7t_recompute.py` in this directory) reproduces the A4 anchor artifact to every printed digit: `total_pnl=1.3719092079218296`, `expectancy=0.0129348274848704`, `pf_overall=1.8959883586565809`, fold PnLs `0.233882/0.387650/0.385302`, max fold MDD `0.303628` = 30.36% (MDD gate FAIL confirmed). Control expectancy `0.012476374265088816` reproduced identically; control/anchor = 96.456% ("96.5%"); control folds positive 2/3. My loop also matches the harness valuation to `0.0000000000` on A5 folds.
3. **A5 fail-closed — DOCUMENTATION CONFIRMED, TRIGGER REFUTED (MAJOR, see below).** The 2%-equity tolerance is documented in the staged runner (`crosscheck_tolerance_abs = 0.02`, line 129; `attribution_residual_note`, line 178; docstring line 8) and the recorded crosschecks (per-cell maxima 0.0808 / 0.3059 / 0.1133; base folds 0.036–0.160) do exceed it. But the recorded residuals are bookkeeping artifacts of the sidecar `attribution()` function, not real divergence (evidence below).
4. **S1 isolation — PASS.** Max fill/period date across all six published artifacts = `2025-07-24` (fold-3 `scored_end`), <= S1 start `2025-08-01`; fold filters enforce `fill_date <= fe`; `split_factors.json` records the five 2025-12-05 2:1 events (XLK/XLE/XLY/XLU/XLB) — all outside S0; no S1 access events in `event_log.jsonl` (14 lifecycle events, none open/access); FD7 gate PASS recorded.
5. **Reproduction — PASS.** All six z9 artifacts are content-identical to z8 with only `pid`/`utc` differing (full deep diff = zero remaining deltas); runner + staged data inputs byte-identical between z8-exec-1 and z9-reproduce; both trees at W1. The 16-hex digests in `z9_reproduction.json` reproduce as `sha256(json.dumps(artifact_minus_pid_utc, sort_keys=True))[:16]` — `z8_digest == z9_digest == recomputed` for all six.
6. **Budget/denominators — PASS.** 6/6 consistent across `ledger.json`, `state.json` counters, `z8_publication.json` (counters + budget), `terminal_report.json` (budget computed/published/planned + denominators), `z9_reproduction.json` (6 cells).
7. **Boundary — PASS.** main `b8876ef`; z8-exec-1/z8-exec-2/z9-reproduce clean at `1063782 30abecba…`; integration clean at `66a5eae`. Zero pytest/nautilus/backtest/cell_runner processes. Credential grep over tracked trees: single hit is policy text in `run_contract.json` ("never printed/logged/committed"); no credential values tracked.
8. **Verdict consistency — A4 REJECT: SOUND.** Follows strictly from PLAN §14 gates (MDD 30.36% > 15%) plus the preregistered falsification rule (control expectancy = 96.5% of anchor, 2/3 folds positive, control PF 1.559 >= 1.10, min fold PF 0.9149 >= 0.80, 2/3 folds positive): long sector beta explains the anchor; the momentum ranking carries no incremental information. A4 REJECT is final and not relabeled. **Sprint claim: NOT the strongest supported (see MAJOR).** Verdict-input spot-checks that DO reproduce: anchor etf-share max 24.86% (XLE), stress +1.332, neighbour +1.303, drop-one-fold min +0.310/+0.0718, A4 drop-one "+0.121" and A5 "−0.0305" (both = anchor-only min drop-one FOLD PNL — consistent metric, loose "expectancy" label).

## MAJOR objection (verdict logic)

The A5 "concentration evidence UNAVAILABLE_FAIL_CLOSED" ruling rests on crosschecks that are artifacts of the staged runner's sidecar `attribution()`, not genuine attribution-vs-harness divergence:

- Defect (a): A5 target books carry explicit `CASH` inside `targets` (A4 books do not). The runner's turnover sum `set(targets) | set(weights) - {"CASH"}` includes the `CASH` leg (line 223-224), roughly doubling per-fill cost in the sidecar. The harness `value_book` strips `CASH` before turnover (harness line 249).
- Defect (b): `total_cost += cost` executed twice (runner lines 227-228) — equity is deducted once but the cost accumulator doubles.
- Evidence: with correct bookkeeping my independent attribution reconciles to the harness valuation at residual ~1e-15 on **all nine A5 base folds** (and A4). Recorded A5 crosschecks (0.036–0.160 base; 0.081–0.306 maxima) are therefore cost-inflation artifacts.
- Consequence: the concentration evidence was in fact reconcilable and would PASS (`max symbol_pnl_shares_overall` = 21.07% / 24.15% / 25.04%, all <= 35%). With the sidecar corrected, A5 has only genuine hard fails — MDD 23.22% > 15%, drop-one-ETF anchor XLK fold-3 PnL −0.0305 < 0, and fold-3 share > 50% under the verdict's own reading — i.e. a clean `STOCKS_FREE_V1_FAMILY_REJECT`. Under PLAN §15 the strongest evidence-supported sprint claim is then `STOCKS_FREE_V1_REJECT_ALL`, not `STOCKS_FREE_V1_INCOMPLETE_NOT_PROMOTABLE`. The published claim under-states: "A5 incomplete" is bug-induced.
- Not load-bearing for safety: NOT_PROMOTABLE is unaffected. MDD/drop-one hard fails independently bar A5; "No scorecard points can rescue a failed hard gate" (PLAN §14). A4 REJECT is untouched (my recomputation confirms its inputs exactly).

## Other objections

- **MEDIUM (audit trail):** fold-positive-share gate inputs are not reproducible from published artifacts under any single consistent definition. A4's "38.5%" matches only the NEIGHBOUR under per-arm fold-gains/total-gains (anchor shows 43.3%; control 52.2%); A5's "60.7%" matches nothing exactly (closest: family-pooled gross-share fold-3 = 61.3%; per-arm gives A5 max 42.0% = PASS; under pooled-gross A4 fold-3 = 68.4% = FAIL). The two families' recorded numbers cannot both be right under one definition. Not load-bearing: A4 fails MDD+control regardless; A5 fails MDD+drop-one regardless.
- **LOW:** `crosscheck_tolerance_abs` is documented but never enforced in-runner (no abort on breach); fail-closed was applied post-hoc by the verdict step. Fine in outcome here, but the enforcement point should be pinned.
- **INFO:** "expectancy" label used for min drop-one FOLD PNL (A4 +0.121 / A5 −0.0305) — loose but applied consistently (anchor-only scope both times).
- **INFO:** "control … passes primary gates" — control MDD is 46.35% (fails MDD too); immaterial to the falsification rule, which concerns mechanism reproduction.
- **INFO:** staged runner contains unreachable dead code (lines 180–184, a second `return`); inert.

## Bottom line

Data gates, ledger, counters, S1 sealing, reproduction, boundaries and hygiene: all verified clean and independently reproduced. A4 FAMILY_REJECT is final and correct. A5 is NOT promotable on genuine hard fails (MDD 23.22%, drop-one-ETF), but its published "incomplete/fail-closed" rationale is disproven (true attribution residual ~0; concentration evidence available and passing), so the strongest evidence-supported sprint claim is REJECT_ALL rather than INCOMPLETE_NOT_PROMOTABLE. Sprint outcome NOT_PROMOTABLE: confirmed.
