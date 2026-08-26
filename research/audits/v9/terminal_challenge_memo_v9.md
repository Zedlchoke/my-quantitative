# A7 Terminal Challenge Memo — Sprint V9 (multi-family crypto discovery)

- Auditor: A7 (independent terminal audit; audit-only, no production code touched, no trials rerun)
- Date: 2026-08-26T10:13:04Z
- Launch SHA W: `206faf8aac5b3f7136001a45d3e7a3e85cb923e5` (pinned in all five launch manifests)
- Audit artifact: `research/audits/v9/a7_terminal_audit_v9.json`
- **Audit verdict: PASS** (process/evidence chain honest regardless of strategy outcomes)
- **Terminal verdict recommendation: V9_REJECT_ALL_MULTI_FAMILY**

## 1. Per-trial results (all values read from bytes)

| Trial | Tree | Kind | Verdict | PF | total_pnl | MDD | FG2 | FG6 | Score |
|---|---|---|---|---|---|---|---|---|---|
| XSECT-TSTREND-L14 | r1 | candidate | REJECTED | 1.0483 | +3964.57 | 15.43% | FAIL | PASS | 57 |
| XSECT-TSTREND-L28 | r2 | candidate | REJECTED | 1.1067 | +6686.00 | 6.06% | FAIL | PASS | 77 |
| XSECT-TSTREND-CTRL | r1 | neg-control | CONTROL_ONLY | 0.8555 | −11050.83 | 24.22% | FAIL | PASS | 30 |
| XSECT-VOLSHK-S15 | r2 | candidate | REJECTED | 0.7346 | −9257.72 | 14.69% | FAIL | PASS | 20 |
| XSECT-VOLSHK-CTRL | r1 | neg-control | CONTROL_ONLY | 1.1333 | +3430.97 | 6.66% | FAIL | PASS | 61 |

FG2 claims match canonical_metrics bytes on all five (PF, equity-delta PnL, MDD, fold PnLs verified numerically). Scorecard band=null / score_meaningful=false everywhere — correct, since hard gates failed and score can never rescue a gate. Fold-level position PFs (auditor-computed from positions.jsonl): L14 F3=0.717; L28 min=0.992; S15 F2=0.581/F3=0.096; TSTREND-CTRL F1=0.768/F2=0.644; VOLSHK-CTRL F3=0.849.

## 2. Evidence-chain integrity (why PASS despite all-reject)

- **FG0/hash integrity:** all gate-result `source_hashes` recompute to actual file bytes across all five trials.
- **Reproduction 5/5:** every reproduction_report pins its VERIFY-V9-* comparison.json by sha256; pins match disk; all_match=true with 21/21 checks. FG6 PASS x5.
- **Stress unconditional:** stress_manifest all_required_executed=true, missing=[], 16 variants per trial.
- **Provenance:** baseline_sha256 `0300ce72…`, attestation_sha256 `c35b63f8…` identical across all five manifests and byte-verified in both exec trees; git_commit_at_launch == W on all five; preflight PASS x5.
- **Budget freeze honored:** exactly the frozen 5 of cap 9 (`v9_budget_freeze.json`, no_post_hoc_additions=true); registry shards exist for exactly those five ids.
- **F2 archived pre-score:** orthogonality gate mean|ρ|=0.676 > 0.50 over 33 Monday stamps → ARCHIVED_NOT_RUN, zero budget. H-XSECT-REVERSAL-BREADTH-CRYPTO-v1 likewise archived per ledger novelty.
- **Technical archives honest:** both TECHABORT dirs contain only frozen/launch_manifest/run.log — zero scored metrics. Event log records exactly two aborts (`scored_metric_published:false`), and each active relaunch started ~1s after its logged abort (clean pre-score retries). No hidden `.TECHABORT-V9-B` shard exists anywhere; the visible archive dir is the sole artifact for that abort.

## 3. Stage-A floor assessment (explicit check)

Criteria: expectancy>0 ∧ PF≥1.10 ∧ ≥2/3 folds positive ∧ no populated fold PF<0.80 ∧ risk within contract ∧ no concentration breach ∧ stress survives ∧ repro all-match.

- **TSTREND-L14: NO** — PF 1.048 < 1.10; fold-PF F3 0.717 < 0.80; MDD 15.43% > 10%.
- **TSTREND-L28: NO** (closest miss) — meets everything except *stress survival as defined by FG5* ("cost/delay survival; no single-point dependency"): `drop_one_dependency_free` violated by `drop_one_symbol_ENAUSDT`; additionally fails contract FG3 adjacency (0 < 2). Caveat recorded: under a narrow reading counting only the three cost/delay perturbations, L28 would satisfy the listed floor; under the frozen gate definition it does not. Either way it is NOT_ELIGIBLE and not lock-eligible.
- **VOLSHK-S15: NO** — negative PnL; PF 0.735; folds F2/F3 negative; fold PFs 0.58/0.10; MDD 14.69%.
- Controls (not promotable by role): TSTREND-CTRL fails nearly everything; VOLSHK-CTRL passes PF≥1.10 but has 1/3 positive folds, symbol-share breach (0.4018>0.40), negative net funding (−808.12), and ENAUSDT drop-one dependency.

⇒ `stage_a_floor_any_pass = false`. The briefing's premise "both families' candidates failing PF≥1.10" is true for L14/S15 but **not** for L28 (PF 1.1067) — L28's rejection rests on stress-dependency-freeness and adjacency, which this memo records explicitly so the terminal rejection is not overstated.

## 4. Multiple-testing honesty

Historical ledger denominator N=112 headline unique scored trials (99+1+4+4+4). With V9's five scored cells the honest denominator is 117. All five statistical_haircut docs pin `effective_n_trials=112` without adding the +5 cells — a LOW documentation gap only: DSR and PBO are UNAVAILABLE_FAIL_CLOSED in every haircut (trial_sharpe_dispersion_missing / returns_matrix_missing), scorecards award 0/10 statistical points with no interpolation, so the insufficiency verdicts hold under either denominator and nothing changes. Acceptable.

## 5. Residuals (all LOW; unresolved high/critical = 0/0)

1. Haircut denominator 112 vs 117 (+5 V9 cells) — immaterial, fail-closed statistics.
2. `dirty_worktree_at_launch=true` disclosed on all manifests — inputs hash-pinned; empirically moot given 5/5 all-match reruns.
3. Briefing referenced a hidden `.TECHABORT-V9-B` shard that does not exist as a separate artifact (no scored leakage either way).
4. Resolved contract lacks a direction field ⇒ FG1 sign test honestly NOT_TESTED on all five (moot at terminal rejection).

## 6. Conclusion

Process PASS. Strategy outcome terminal: **V9_REJECT_ALL_MULTI_FAMILY** — both candidate families exhausted their frozen budget without any trial meeting the complete STAGE_A floor; recommend closing multi-family discovery for this sprint with no lock-eligible artifact carried forward.
