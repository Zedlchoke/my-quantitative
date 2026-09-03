# V12 A7-PRELAUNCH — final independent prelaunch audit

- Auditor: A7-PRELAUNCH (independent; recompute-from-raw-bytes; producer claims never trusted; no production code repaired)
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v12/a7-prelaunch`
- Branch: `orca/v12-a7-prelaunch` — HEAD audited: `367a4eb5c3ba243ab2864589b047586ea5ef2ba1`, porcelain empty at start and at close (except this audit directory)
- Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`; import-order contract respected (`research.adapter_v10` before `research.v11.publication_identity`)

## VERDICT: `V12_S0_LAUNCH_AUTHORIZED`

Authorization carries explicit recorded launch conditions (see below). Zero unresolved HIGH/CRITICAL.

## Per-item results

| # | Item | Status | Decisive numbers |
|---|------|--------|------------------|
| 1 | Ancestry | PASS | `142f50c` (V11R terminal) and `df18f53` (pushed V11 terminal) both `--is-ancestor` of HEAD; 24 V12 commits single-parent linear; 0 merges post-V11R; reflog clean (1 no-op reset) |
| 2 | Denominator authority | PASS | 11/11 terminal-summary sha256 recomputed = recorded; totals 125/128 consistent (v11 terminal report / v12 state / heartbeat); consumer rule observed>=128 stated; ledger empty-seed `e3b0c442…b855` pinned; **no scored V12 artifact anywhere** (no CELL_RESULT/OBSERVATION payload outside history/schema; event log control-only) |
| 3 | Selection + arm digests | PASS | **6/6** recomputed via `arm_config_digest` from freeze-v2 identity fields = freeze record = module `FROZEN_ARM_CONFIG_DIGESTS` (oilev `2d9c5644…`, `0ba51b43…`, `e57b26fe…`; bab `7a233cf4…`, `c1c2ed26…`, `fabeb43a…`); ILLIQ arms not frozen, 3 slots unused, no ILLIQ lane exists |
| 4 | Data / window / fold / warmup / PIT | PASS | S0 2025-08-22..2026-08-21 only for OILEV-V2 (V11 OILEV scored 0 metrics) + blind BAB; S0R 2024-08-22..2025-08-21 ends 1 day before V11 window start ⇒ non-overlap (arithmetic verified); ILLIQ `V12_ILLIQ_REPLICATION_BLOCKED_DATA` honestly recorded (14/20 head-bar gaps, warmup unsatisfiable, no substitution); PIT spot-checks: completed bars only, features strictly pre-stamp, future universe data never touched (`close_ns > decision: break`), benchmark refused, close decode i128/1e16, folds F0/F1/F2 + 1d purge |
| 5 | OILEV-V2 52/52 | PASS | Independent re-run of the A4 validator chain from raw OI parquet: 3 arms × **52/52 PASS**, n_fail=0, eligible_min=19 (>=9), max\|w\|=0.125 (<=0.30), uniform-scale never triggered (4+4 legs × 1/8 by construction); A4 funding open item closed by lane (`funding_status=OK`, 6612 events while held) |
| 6 | Blind novelty + outcome isolation | PASS | A7-N: A5-P1-BAB-LOWBETA ELIGIBLE; OSCOMP INELIGIBLE (HIGH, inverted reserved-ILLIQ rank \|rho\| 0.81/0.87); A8-P1 INELIGIBLE (HIGH, fabricated DOI + duplicate, \|rho\|=1.0 52/52); merge map applied in rubric (A5-P1 representative; A8-P2 loses to A5-P2); proposals contain **0 scored metrics** (all metric tokens are blind attestations; all floats are DOIs/pages/years); lane logs show literature-first DOI-verified discipline |
| 7 | Dummy dry-run (own temp ledger) | PASS | 3 arms: zero-position **REFUSED** (OBSERVATION, `REFUSED_ZERO_POSITIONS`), dummy **PUBLISHED** exactly once (CELL_RESULT `fee_x1_5`), replay **IDEMPOTENT**; ledger ends 6 rows (3+3), trial_keys 6/6 unique, `scored=False`, `real_pnl=False`; full replay byte-identical (2627 B); real V12 ledger still absent |
| 8 | Publication guard / drop-one / stress | PASS | `test_v12p_a2_publication.py` + `test_v12i_bab_feasibility.py`: **21 passed**; drop-one independently exercised: selects HELD max-\|w\| symbol, lexicographic ties, unheld never selected, zero-held + out-of-cohort refused; lane drop-one `all_match=true` on real stamps; cells derived from frozen folds (L-V11-1) |
| 9 | Pin chain | PASS | exec-v12-1 and repro-v12-1 both detached at **`f0799cae6fc4…e990`**, porcelain 0/0; staged_data **90/90** data files per tree; staged manifest sha256 **`f855ad9c778f…3c40`** byte-identical exec==repro; manifest↔bytes 90/90 both trees; sha sets = `a3_staging_manifest.json` 90/90; 0 writable staged files |
| 10 | Tests + tree | PASS | Targeted 6-file matrix: **119 passed**; FULL SUITE ALONE: **1601 passed, 1 skipped** (documented V9 slow-archive manual smoke), 272 s; re-run stable; tree unchanged after (only `research/audits/v12p_a7prelaunch/`) |
| 11 | Resources + boundaries | PASS with launch condition | Fresh probe (vm_stat): free **0.05 GB** on 8 GB host ⇒ measured_safe_cap **0** (freeze-time probe 0.06 GB, cap 0 — same). Budget **0/9**; denominators **125/128**; S1 **SEALED_UNTOUCHED** (untouched by audit); workers **0**; 0 raw hits for api-key/credential/testnet/order tokens; `scored_cells_exist=0` |

## Launch conditions attached (binding)

1. **Execution-host resource gate.** Before the scoring clock starts, a fresh RAM probe on the owner's execution host must measure `measured_safe_cap >= 1` using the frozen formula `min(3, floor((free_gb-1.5)/2.0))` with the PLAN_crypto 4.2 host cap. This 8 GB prelaunch/audit host measures cap 0 and must not run scored execution.
2. **Staging on execution host.** The 12-hour scoring clock starts ONLY after this authorization AND equal-twin staging on the execution host re-verifies: 90/90 files hash-exact vs `research/audits/v12p/a3_staging_manifest.json` (staged-manifest sha `f855ad9c…`), exec/repro detached at W12 `f0799cae…`, porcelain clean.
3. **Clock rules (run_contract).** No new cell with <120 min remaining; <45 min: stop workers safely and close incomplete.
4. **Owner GO.** A separate explicit owner instruction "V12 SCORED EXECUTION" is required per the run_contract boundary; no scored PnL in the prelaunch session.

## Objections ledger

| ID | Severity | Status |
|----|----------|--------|
| A7P-RES-1 (host cap 0) | LAUNCH_CONDITION | Resolved by condition 1 (would be BLOCKING on a cap-0 execution attempt) |
| A7N-OSCOMP-1 (reserved-family inversion) | HIGH | Resolved — proposal INELIGIBLE, excluded from frozen set |
| A7N-BABPERP-1 (fabricated DOI + duplicate) | HIGH | Resolved — proposal INELIGIBLE, merge map applied |

## Fail conditions

None triggered: no digest mismatch, no unresolved HIGH/CRITICAL, no scored artifact, no S1/deployment exposure, no pin-chain break, no test failures, no staging mismatch.

## Scratch

- `research/audits/v12p_a7prelaunch/a7_scratch/dryrun_a7_prelaunch.jsonl` — audit-owned dummy dry-run ledger (3 CELL_RESULT + 3 OBSERVATION, idempotent replay verified byte-identical).
