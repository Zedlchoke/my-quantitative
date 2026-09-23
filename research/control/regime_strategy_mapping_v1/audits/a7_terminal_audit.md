# A7 TERMINAL AUDIT — REGIME-STRATEGY-MAPPING-V1

- Auditor: A7, fresh context; did not implement, remediate, or reproduce any
  audited artifact. Audit-only; nothing repaired.
- Worktree: `.worktrees/regime-strategy-mapping-v1/a7-terminal`, branch
  `orca/rsmv1-a7-terminal`, HEAD at audit start `26715bbc6d640b7c9ee8af1da10094d96e9c0919`
  (verified = dispatch base). Tree clean before deliverables.
- Proposed verdict under audit: `NO_REGIME_STRATEGY_INCREMENTAL_VALUE`
  (`evidence/terminal_evaluation.json`, `evidence/REGIME_STRATEGY_MAPPING_REPORT.md`).
- Scored-run tier files audited from the integration worktree
  (`runtime/scored`, `runtime/scored_run1_invalid`, `runtime/scored_repro`;
  untracked execution outputs, byte-identical audit object — same cycle, same HEAD).

# VERDICT: `TERMINAL_VERDICT_AUTHORIZED_NO_REGIME_STRATEGY_INCREMENTAL_VALUE`

Zero unresolved HIGH/CRITICAL. The negative verdict is **not understated**:
no arm passes all gates anywhere (see "Negative not understated" below).

## Terminal checks (12/12 executed; PASS/FAIL/NOT_RUN)

| # | Check | Result | Key evidence |
|---|---|---|---|
| 1 | GO chain | **PASS** | `SCORED_GO.json` bytes == exact phrase `GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST` (no trailing newline); sha256 `47ee5e6f2bde5957…c70c` recomputed by auditor == freeze record == `sha256(phrase)`. Quarantine refusal behaviorally re-verified by auditor in-memory: missing token → `authorized=false` (exit-20 path), wrong token → `authorized=false`, `token_matches=false`; `cmd_scored.py` source prints `REFUSED_BACKTEST_QUARANTINE`, exit 20. `test_go_quarantine_phrase_matches_registry` exercises the real gate via subprocess. Heavy-lock history (`~/.my-quantitative-governance/heavy_runtime/heavy_worker.history.jsonl`): 4× `cmd_scored.py` FAILED (the disclosed pre-run-1 TECHABORTs) → `cmd_scored.py` FINISHED (run 1) → 3× `cmd_remediation_run2.py` FAILED (INC-1b/c/d) → FINISHED (INC-1e D/E) + `cmd_repro_run2.py` FINISHED. Every scored/repro process ran heavy-locked. |
| 2 | V2 untouched | **PASS** | V2 worktree HEAD `0c277a94ba28…` (exact), `git status --porcelain` clean. Zero commits in RSMV1 branch history (`102ed500..26715bbc`, plus `--all` scan) touch `research/control/jev_regime_router_v2/`. V2 verdict `JEV_NO_INCREMENTAL_VALUE` present in V2's `REGIME_BACKTEST_REPORT.md` and restated in the RSMV1 report. Auditor spot-check: RSMV1 A1/A2/B `tier_1` totals == V2 stored ledgers (`ALWAYS_ON_MEAN_REVERSION` / `ALWAYS_ON_TREND` / `JEV_ONLY_ROUTER`) with **0.0 max diff** and identical trade counts on all 3 cells (391/1386/978, 374/1269/1060, 18/143/343). |
| 3 | Incident chain honesty | **PASS** | `rsmv1/turnover.py::direction_of` now dispatches specialist names via `SPECIALIST_DIRECTIONS`, fail-closed 0 for unknown (docstring records INC-1). Run-1 summary confirms the symptom: C/C_RELAXED 0 trades on every cell; F/F_RELAXED `NOT_RUN_CONTROL_MATCHING`. Preservation verified: `runtime/scored_run1_invalid/` holds C/C_RELAXED/D/E tier files ×3 cells + full run-1 summary; run-1 C is degenerate (0 trades, all-zero costs); A1/A2/B remain in `runtime/scored` with no `run_identity` marker (untouched run-1 files). C/CR marked `run2-remediation-INC-1`, D/E `run2-remediation-INC-1b-deferral`. Classification coherent: 27 = 9 (A1/A2/B) + 6 (D/E) + 12 (C/CR/F/FR) → 15 valid + 12 invalid; INC-1e supersedes D/E. INC-1e recompute invariance verified: D/E totals identical run-1 vs run-2 on BTC_H1/BTC_H4 and E on SPY; SPY D changed −53,387.93 → −21,134.02 (= the report's "+32k", +32,253.91). Selection audits byte-identical run-1 vs run-2 on all 6 C cells (confirms "evidence path never passes through direction_of"). F entries identical both runs. |
| 4 | Trial accounting | **PASS** | Recounted from both summaries (not the report): run-1 `scored_summary.json` observed 27 (21 primary + 6 sensitivity; 9 arm rows × 3 cells) ; run-2 `scored_summary_run2_cf.json` `run2_observed_cf` 18 (6 arm rows × 3 cells) ; `total_observed_all_runs` **45 = 27 + 18** ✓. Every computed outcome classified (12 invalid INC-1; 6 D/E superseded INC-1e; remainder valid). Multiple-testing disclosed in both summaries, the GO freeze, and the report ("verdict decided on PRIMARY only"). |
| 5 | Numbers recomputed from tier files | **PASS** | Auditor recomputed **162 tier files** (63 current + 36 run-1-invalid + 63 repro) — **0 failures** in: `net == gross − fee − slip − funding`; Σfolds == net (tol 1e-9); per-trade `net == gross − fees − slip − funding`; trade aggregates == totals; per-fold trade sums == `fold_net_pnl`; trade counts; `engine_identity`/`fold_reconciliation` flags TRUE everywhere. Equity identity (`100000 + net == equity[-1]`, tol 1e-6) is enforced at runtime in `scored.py::_identity_ok` and persisted as the flag+residual (verified TRUE in all 162 files); the equity curve itself is not persisted (F-A7T-4, INFO). Headline numbers all reproduce: BTC_H1 C **−49,660.94 / −60,377.47** (398 trades; folds 0 / −36,654.85 / −3,931.78 / −9,074.31), C_RELAXED byte-identical; BTC_H4 C 0 trades (frozen) / C_RELAXED **−4,996.87** (31 trades, fold 4 only); SPY C 0 / C_RELAXED **+2,529.01** at 1.0x, **−803.03** at 1.5x (33 trades, fold 4 only); D BTC_H1 **−23,550.67**; A1/A2/B == V2 stored totals exactly (check 2). Report rounding (−49,661, −4,997, +2,529, −23,551) correct. |
| 6 | Gate evaluation | **PASS** (one LOW label finding) | Recomputed from tier files, BTC_H1 (only evaluable cell): G1 **FAIL** (−49,660.94); G2 **FAIL** (−60,377.47); G3 **PASS** vs max(A1,A2) = −53,132.13; G4 **PASS** vs −88,140.39; G5 **FAIL** (0 positive folds); G6 **FAIL** (C −49,660.94 < D −23,550.67; F `NOT_RUN_CONTROL_MATCHING` → `F_INVALID_REST_ON_ABDE` recorded, gate rests on D — exactly the frozen law). G7 PASS (69/69, re-run by auditor). Thin labeling: BTC_H4/SPY C selection audits = 16/16 rows `OUTER_FLOOR_THIN` → FLAT → `NOT_RUN_THIN_REGIME`; BTC_H1 has non-FLAT selections in folds 1–3 → evaluable. Honest decision table: ≥1 evaluable cell (→ not BLOCKED_THIN), all mechanical checks pass (→ not TECHABORT), gates fail → `NO_REGIME_STRATEGY_INCREMENTAL_VALUE`, exact string ∈ frozen `allowed_values_exactly`. **F-A7T-2 (LOW)**: report's "sum−max = −13,006" is actually sum-minus-**worst**-fold (−49,660.94 − (−36,654.85) = −13,006.09); the frozen formula `sum − max fold` = −49,660.94. FAIL under either reading; verdict unaffected. |
| 7 | Floor-sensitivity law | **PASS** | Freeze `go_authority_and_floor_sensitivity_freeze.json` created in commit `64831eae` 10:44:55 +0700, single-commit history (never modified). Run-1 executed 03:50:21Z–03:59:03Z (= 10:50–10:59 +0700, heavy-lock history agrees); run-2 04:43:46Z–04:51:58Z. Freeze strictly pre-outcome ✓. Relaxed floors 10/2/50 == `RELAXED_OUTER_FLOORS` constant in `scored.py`; frozen 20/3/100 == `FROZEN_OUTER_FLOORS`. Precomputed eligibility deltas in the freeze match the real census (`evidence/regime_sample_census.json`) exactly: BTC_H1 unchanged (ACC 23 / UP 28 / DOWN 34 pass both; DIST 5 < 10 thin in both); BTC_H4 UP 12, DOWN 14 ≥ 10 eligible relaxed, ACC 4 / DIST 1 stay thin; SPY UP 17, DOWN 15 eligible, ACC 1 / DIST 1 thin. Verified empirically: C_RELAXED trades appear only in fold 4 (31 / 33 trades). SPY +2,529 correctly **NOT promoted**: G2 FAIL (−803.03), G3 FAIL (< +19,812.69), G5 FAIL (1 positive fold, sum−max = 0); sensitivity-only per the freeze; verdict decided on PRIMARY only. |
| 8 | Reproduction | **PASS** | `evidence/reproduction_report.json`: 69/69 MATCH = 27 byte (A1/A2/B ×3 cells ×3 tiers) + 36 content-minus-extra (D/E/C/CR) + 6 status-equality (F/F_RELAXED). **Auditor re-ran `tools/cmd_repro_run2.py` under the machine-wide heavy lock** (lock was FREE_PROVEN): exit 0, **69/69 MATCH**, regenerated report **byte-identical** to the committed one (sha `98182b6ccfd9cd3e…`). Content-minus-extra legitimacy confirmed: `extra` holds only audit trails (routing counters, run_identity label, selection_audit, turnover verdict); every computational field (totals, folds, trades, identities) is top-level and compared. `selection_audit` additionally verified identical run-1 vs run-2. |
| 9 | F controls fail-closed | **PASS** | All 6 F-cells `NOT_RUN_CONTROL_MATCHING` in both runs, identical records (attempts 200, seed 20260901). Verified in code this is the designed frozen path, not a crash: `arm_f` raises `ControlMatchFailure` when matcher acceptance + Q-11 movement are never jointly satisfied within 200 attempts; the runner catches it and records `NOT_RUN_CONTROL_MATCHING`. Anchor path = arm C's buffered regime-grid labels (C mostly-FLAT fold-1 + sparse investing ⇒ tolerances unsatisfiable — consistent with a fail-closed outcome, and with F failing identically in run 1 under the degenerate anchor). `F_INVALID_REST_ON_ABDE` fallback applied in the terminal evaluation and report. |
| 10 | Selection law at scored time | **PASS** | Persisted `selection_audit` (`runtime/scored/BTC_H1/C_REGIME_SPECIALIST_ROUTER/tier_1.json` extra): fold 0 all four regimes FLAT (`fold1_empty_inner_default` — the fid==0 empty-inner gate), fold 1 ACC→`ACC-BASE-RECLAIM-L` (`single_eligible_specialist`), UP→`UPT-BREAKOUT-L` (`inner_net_higher_stable`), DOWN→`DNT-CASCADE-S` (`inner_net_higher_stable`), DIST `OUTER_FLOOR_THIN` ×4 folds, fold-2 UP FLAT (`inner_evidence_unstable`) — exactly the selections the A7-R3 pre-outcome audit verified against the real census. Turnover rejection law: `{v2_jev_only_trade_pin: 978, arm_c_trades: 398, verdict: PASS}` — 398 < 978 ✓ (caps 1060/343 on the other cells present in code + freeze + V2 totals). |
| 11 | Hygiene | **PASS** | No S1 paths anywhere (the only `s1_` hits are the security.py leak-detector scanning FOR such markers; `SEALED_UNTOUCHED` asserted). No broker/order/paper/live surface (no `place_order|broker|websocket|paper_trading|live_loop` hits). Zero provider calls: no `requests/urllib/httpx/http(s)` in `rsmv1/` or `tools/`; the `TYPESAFE_API_KEY` env read is a name-only credential-leak check (value never loaded). Contamination ceiling intact: verdict string ∈ frozen vocabulary (exact match); report contains only disclaimers ("Nothing here is live-ready or profitable; no shadow/promotion; no paper/live/orders"); V2's `JEV_NO_INCREMENTAL_VALUE` restated. |
| 12 | Tests | **PASS** | `python -m pytest tests_py -q` at HEAD `26715bbc`: **121 passed, 1 xfailed in 13.29s** (xfail = documented A5-F1 BUY_HOLD hold-to-end law). Matches the mandate exactly. |

## Findings

| ID | Severity | Finding | Impact |
|---|---|---|---|
| F-A7T-1 | **MEDIUM** (artifact integrity, non-blocking) | `freezes/go_authority_and_floor_sensitivity_freeze.json` is **invalid JSON**: brace imbalance (5 opens / 4 closes — the root object is never closed; strict `json.load` fails with "Expecting ',' delimiter" at EOF). The malformed bytes were present from the creation commit `64831eae` (an honest typo, not tampering — content otherwise complete and consistent). No machine consumer parses this file: outer floors live in `scored.py` constants (`FROZEN_OUTER_FLOORS` 20/3/100, `RELAXED_OUTER_FLOORS` 10/2/50 — both verified equal to the freeze's stated values) and the selection freeze wrapper (digest-pinned, verified); the GO sha record matches the token. Content is unambiguous and every claim in it was independently verified. | The authority artifact that freezes the owner's floor comparison cannot be re-parsed by any standard consumer. Recommend a follow-up fix (add the missing brace) by an authorized role — auditor does not repair. Not verdict-changing. |
| F-A7T-2 | LOW | Report's G5 arithmetic label "sum−max = −13,006" is actually sum-minus-worst-fold; the frozen literal `sum − max fold` = −49,660.94. | G5 FAIL under either reading; verdict unaffected. |
| F-A7T-3 | INFO | `incidents/incident_run1.json` accounting says "total observed 39" — the INC-1-time view; superseded by INC-1e (D/E re-run adds 6 → 45), consistently disclosed in the terminal evaluation, report, and run-2 summary; supersession documented in commit `7e6487e1`. | Point-in-time incident record; no inconsistency in the terminal artifacts. |
| F-A7T-4 | INFO | Equity curve is not persisted in tier files; the equity identity is attested by the runtime-computed persisted flag (verified TRUE in all 162 files, tol 1e-6) plus exact A1/A2/B == V2 stored ledger equality. | Acceptable; note for future artifact schema. |

## Negative not understated (active refutation attempt)

- The only candidate arm is C (frozen floors) — D/E/F are controls, A1/A2/B
  references, C_RELAXED/F_RELAXED sensitivity-only per the GO freeze.
- BTC_H1 (only evaluable cell): C fails G1, G2, G5, G6 — no path to a pass.
- BTC_H4/SPY: C is lawfully FLAT (thin) — `NOT_RUN_THIN_REGIME`, excluded from
  the denominator and reported; not evidence FOR anything.
- The single positive number in the entire corpus, SPY C_RELAXED +2,529, was
  attacked directly: it fails G2 (−803 at 1.5x), G3 (loses to always-on +19,813),
  and G5 (single fold) — and is constitutionally barred from candidacy by the
  frozen primary-only law. Correctly reported as a thin-sample mirage.
- Best Jev-aware arm anywhere is control D (−23,551) — still deeply negative;
  no arm × cell × tier combination passes all gates. `E`'s improvement over V2's
  CONFIRM (+16–21k, a true mechanism finding) still leaves it −56,968…−65,185 —
  cost reduction, not edge; the report claims no more than that.
- Therefore `NO_REGIME_STRATEGY_INCREMENTAL_VALUE` is neither understated nor
  overstated; `BLOCKED_THIN` and `TECHABORT` are demonstrably the wrong rungs.

## Audit mechanics

- All recomputation scripts were ad-hoc and lived in `/tmp` (outside the repo);
  no cycle artifact was modified by the audit. The authorized heavy-locked
  repro re-run rewrote `runtime/scored_repro/` (untracked scratch, the tool's
  designed output) and regenerated `evidence/reproduction_report.json`
  **byte-identical** to the committed file (sha verified before/after:
  `98182b6ccfd9cd3e…`); the integration worktree's tracked files remain clean.
- Quarantine refusal was tested in-memory (path swap) — the cycle tree was
  never mutated.
