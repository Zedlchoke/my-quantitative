# DATA_COST_FREEZE — BTC-COMBO6-SCORED-V1 (2026-09-29, lane A3 DATA-VERIFY measured)

## Corpus (frozen)
- Master: research/control/bear_opportunity_recon_2026-09/killer_a4/dl5m/kl_*.zip —
  102 files (80 monthly 2020-01..2026-08 + 22 daily 2026-09-01..22), 32,532,793 bytes.
  Identical between root and cycle worktree (exhaustive 102-file sha256 diff).
  Per-file sha256 map: worktree research/control/BTC-COMBO6-SCORED-V1/staging/data_manifest.json
  (loader re-verifies every file before use; mismatch = fail closed).
- Funding: research/control/bear_opportunity_recon_2026-09/data_a2/funding_events.parquet
  sha256 fbc99a3ade3b2703e8fd53afd8ff191ca2b5bc136596e80215ef7ca3132de41b.
- Panel census (measured): 707,616 rows, 2020-01-01T00:00Z → 2026-09-22T23:55Z,
  gap-free 5m grid (0 missing of 707,616 slots), 0 duplicate open_time, 0 high<low,
  0 OHLC≤0, close_time−open_time=299,999ms on all rows. 66 zero-volume flat bars
  (genuine no-trade bars, kept). CSV header regime change at 2022-01 (auto-detected per file).
- Funding census (measured): 7,643 rows, contiguous 8h grid 2019-09-10→2026-08-31,
  interval always 8h, rate per-8h decimal min/median/max −0.003/0.0000972/+0.003,
  ts jitter ≤47ms (engine floors to 8h slot before join), 5,451 events inside [2021-01-04, 2025-12-26) as first measured; A7 recomputed 5,460 inside the corrected erratum window [2021-01-04, 2025-12-29) — engine loads by corrected window (A7 finding F-3).

## FOLD ERRATUM (2026-09-29, before code freeze)
Plan §4 prose "F10 ends 2025-12-26" was arithmetically wrong: 2021-01-04 + 260 weeks
= 2025-12-29 (Monday); 2025-12-26 is 259w+4d. AUTHORITATIVE calendar (implemented):
F1_START 2021-01-04T00:00Z, 10 folds × exactly 26 weeks, EVAL_END 2025-12-29T00:00Z,
sealed tail [2025-12-29, 2026-09-22T23:55Z) loaded-not-evaluated. Plan file erratum
lands with the code-freeze commit on the cycle branch. Evidence: DATA-VERIFY fold
sanity check (replay snippet in lane report).

## Cost kernel (frozen, plan §3)
- Per side on notional: taker fee 5.0 bps (DECLARED — CHR3F frozen posture, unvalidated
  vs fills) + half-spread 1.0 bp (DECLARED_PESSIMISTIC) = 6.0 bps/side.
- Stress multipliers ×1.0/×1.5/×2.0 on fee+spread only; funding measured signed, unstressed.
- Worst-fill grading: SL gap-through fills at bar open; same-bar TP+SL → SL first.
- GROSS/NET dual books; NET is decision-grade. UNMEASURED register: slippage beyond
  half-spread (U1, guarded by gap-through rule), venue fee tier validation (U2),
  spread census at 5m fill hours (U3) — all DECLARED, flagged in outputs.

## PIT posture (frozen)
- Vision klines = RETROSPECTIVE_SNAPSHOT (no per-bar publication ts); house convention
  (PSV1): bar knowable at close, first executable fill at next bar open. Labels carried.
- Engine truncation-replay test is the no-lookahead proof (byte-stable prefixes).
- No prospective data joined as history. S1 SEALED_UNTOUCHED.
