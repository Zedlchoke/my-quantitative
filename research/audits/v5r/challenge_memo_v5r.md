# A6 Challenge Memo — V5R Independent Scientific Audit

- Auditor: A6 (independent; authored no engine/gate/run/transition artifact)
- Audited head: `e3d82ad2109da06d7727357fb0cbbccec3cb5bad` (verified via `git log -1`)
- Date: 2026-08-24 · Seed: 20260824 (`random.Random(20260824)` over deterministically sorted IDs)
- Scope: the four clean-lineage diagnostic recalcs under `results/diagnostic_v5r/`, window 2025-08-21T14:30Z..2026-08-21T00:00Z, 3 folds.

## What I recomputed (independently, from raw artifacts)

1. **Population (census).** Recounted every row of `orders.jsonl`, `positions.jsonl`, `portfolio_ledger.jsonl` for all four runs: orders 2297/2036/1909/2054; legs 955/838/786/857; ledger rows 43,622 each. Legs == `legs_closed`, scored rebalances == 364 per run in `canonical_metrics`; all IDs present in registry shards.
2. **Leg identity.** Convention recovered from data: **`canonical_pnl = gross_pnl − costs_allocated + funding_allocated`**. Sampled 170 positions (50+50+50+20): **0 violations @1e-6**. Full-population recompute of all 3,436 legs: **0 violations**.
3. **Orders.** 80 sampled: qty>0, price>0, timestamps inside window, symbols ⊆ frozen universe (8 symbols). Rejected rows carry `rejected_reason` with null fill — coherent. 0 violations.
4. **Funding.** Census: **3,321 funding-bearing legs** (≥30 required). Momentum aggregate carry negative as long-bias predicts: −511.90 / −589.50 / −180.34 (3D/7D/14D). Reverse control **+583.07 flips the sign vs base 7D**, fold-by-fold too.
5. **Fold boundaries.** `{F1,F2,F3}` × 4 experiments; fold PnLs sum to total with **Δ = 0.0** (<1e-6) everywhere. No purge/embargo fields exist in frozen config (see findings).
6. **Exposure census (all 174,488 bars).** `cash_identity_ok` true on **every** row; margin breaches 0. Max gross 1.2746, max |net| 0.0964. Gross > 1.00 on ~39% of bars → MED finding below.
7. **Hashes & reproduction.** I ran `verify_artifact_hashes` myself as external reader: **zero mismatches, 4/4**. All four `VERIFY-*/comparison.json`: `all_match=true`, `rerun_process_separate=true`.
8. **Terminal policy.** Exactly **12 terminal legs per run** = 4 symbols × 3 fold boundaries; final book flat (`positions={}`), consistent with FORCE_LIQUIDATE at each boundary and at last bar.
9. **XG0 forensics.** XG0 FAIL rows present 4/4 with `coverage_below_declared` + `funding_coverage_insufficient`. Independently quantified shortfall: declared universe 8 symbols; only 7 scored (**BTCUSDT absent entirely**) and ETHUSDT head-trimmed to 14:29:59.999Z (unexplained 870-min gap ETH-G1, no network egress to repair).
10. **Transition logic.** With R06+R12 FAIL, `clean_path_ok=false` per PLAN §13 ⇒ **V5_FAIL_V6_BLOCKED** follows mechanically. Verified no V6 surface exists (`results/portfolio_v6`, `results/reproduction_v6`, `matrix/v6_*`, `H-XSECT-FUNDING-CARRY-v1` all absent).

## What failed

Nothing failed under audit recomputation: zero identity violations, zero order violations, zero cash/margin breaches, zero hash/reproduction mismatches. The two gate FAILs are properties of the evidence, honestly measured:

- **R06 FAIL is honest and substantiated**: the coverage shortfall is real (BTC unscored, ETH trimmed) and XG0 fails end-to-end in all four runs.
- **R12 FAIL is honest and substantiated**: `gate_result.json` shows XG4 `INCONCLUSIVE / not_tested` because the stress matrix is gated behind a base edge (XG3 FAIL) that did not pass — violating unconditional execution.

## New findings (none change the transition)

- **MED** — Gross exposure >1.00 on ~17.1k–17.6k of 43,622 bars/run (max 1.2746) despite config `leverage: 1`; cash identity intact, documented by R10 as strategy concentration. Clarify gross-cap semantics before any future authorization. (`portfolio_ledger.jsonl`)
- **MED** — Runtime XG0 reason `funding_coverage_insufficient` conflicts with the frozen data contract showing complete 8h cadence for all 7 scored symbols (1094–1096/1096). Likely bundle mismatch (`funding_data/20240820_20260821` vs manifest `scan_2026`). Immaterial here since coverage independently fails R06, but should be reconciled. (`frozen/data_manifest.json`)
- **LOW** — Declared-vs-scored universe mismatch (8 declared / 7 scored; BTCUSDT missing). (`frozen/universe.json`)
- **LOW** — No explicit purge/embargo fields in frozen config; isolation via chronological folds + warmup + boundary liquidation only. Formalize before any promotion lineage. (`frozen/config.yaml`)

## Independence statement

I had full read access to the entire population of raw artifacts (no sampling of convenience): all 174,488 ledger rows, 8,296 orders, and 3,436 position legs were available to me, and the exposure/funding/identity censuses were run over full populations while the mandated samples used seed 20260824 over deterministically sorted IDs. I authored none of the audited artifacts; my only writes were `research/audits/v5r/challenge_memo_v5r.md` and `research/audits/v5r/scientific_audit_v5r.json`. Independence was preserved throughout.

## Verdict

Audit **PASS** (10/10 checks PASS; 0 unresolved high/critical findings). This attests artifact integrity and honest gate measurement. It does **not** authorize V6: **V5_FAIL_V6_BLOCKED stands** by construction (R06, R12 hard-fail under PLAN §12.3).
