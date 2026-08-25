# V5R Re-audit Addendum (V6P-0) — 2026-08-24T12:34:05.758138+00:00

Preserves `V5_FAIL_V6_BLOCKED` as the historical safe verdict. This addendum
records adversarial findings N01–N15 about the V5R sprint's gate-ledger claims.
Historical ledgers/audits/transitions/reports remain byte-immutable; corrections
live only here and in `v5r_reaudit_gates.json`.

## Verified findings
- N01 CRITICAL: pre-launch attestation slot says PENDING_A6 yet R04 claimed PASS.
- N02 CRITICAL: all four launch manifests record dirty_worktree_at_launch=true;
  the contract's clean-tree claim is false for launches.
- N03 ADJUSTED: no literal self-referential hash embedded; the real defect is
  post-launch commit of baseline+contract under a self-exemption.
- N04 CRITICAL: folds F1/F2/F3 all begin at cash=equity=100000 -> reset-fold WFA;
  MDD/fold-return claims from stitched curves are invalid.
- N05 CRITICAL: RISK_MODE_V1 never wired into portfolio_runner; gross exceeded 1.0.
- N06 CRITICAL: funding_cashflows/accounting_reconciliation/commission_slippage/
  terminal_positions/exposure_control artifacts absent 4/4.
- N07 CRITICAL: XG1 fed by hand-built runner booleans, not execution rows.
- N08 HIGH: coverage adapter returns None; XG0 saw zero days by construction.
- N09 HIGH: benchmark shortfall mislabeled as funding_coverage_insufficient.
- N10 HIGH: stresses conditional on base XG3; expectancy_r inappropriate for family.
- N11 HIGH: reproduction compares narrow surface only.
- N12 HIGH: final reconciliation artifact itself records append_only=false while
  ledger row R15 claimed TRUE (stale evidence ordering).
- N13 HIGH: prior A6 audit missed N01-N12; completeness insufficient for authorization.
- N14 MEDIUM: no purge/embargo frozen. N15 MEDIUM: transition heads/timestamps stale.

## Correct interpretation of R06
R06 remains FAIL with primary cause RUNTIME_COVERAGE_EVIDENCE_NOT_WIRED_AND_
REASON_CODES_CONFLATED (see PLAN §1.3). Data bundle identity to be proven at
runtime before any genuine shortfall claim.

## Independently rerun tests at intake
581 passed, 16 warnings, exit 0 (2026-08-24T12:34:05.758138+00:00).

## V6/V7 absence at intake
results/portfolio_v6, results/portfolio_v7, both hypothesis dirs: ABSENT.

Intake snapshot: sha256 ab346d331df018de
Gates JSON: sha256 704b4768a4ff29d2
