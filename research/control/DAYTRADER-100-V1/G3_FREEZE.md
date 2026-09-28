# DAYTRADER-100-V1 — G3 IDENTITY FREEZE

- frozen_utc: 2026-09-28 (this session, BEFORE any scored PnL)
- worktree: `.worktrees/daytrader-100-v1/integration` branch `orca/daytrader-100-v1-integration`
- base chain: aa954939 (root main) → f98087f6 (registration + amendment r1) → this freeze commit
- authority: owner order 2026-09-28 verbatim (AMENDMENT_r1) + plan §3 floors + census matrix

## 1. Trial identities (frozen enumeration)

27 families × (A anchor + N1 + N2) = **81 scored-cell candidates**, defined to the
parameter level in `research/daytrader100/dt100/arms.py` (this file is part of the
freeze; its sha256 is pinned below). Controls are RE-EVALUATIONS (zero cells):
`clock_shadow` (Q-7 direction-permutation within weekday×hour strata, seed 20260928),
`sign_flip`, `stale_lag`. Drop-one robustness re-evaluations (zero cells): SOLUSDT for
crypto-1m families, GBPUSD for FX families.

Substrate-blocked families under the owner order (verdict at scoring:
`NOT_RUN_DATA_BLOCKED_UNDER_OWNER_ORDER`): listed in `dt100/arms.py::BLOCKED_UNDER_ORDER`
(census matrix §2.2).

## 2. Windows (explicit calendar dates — plan §3.1/§4, unchanged)

- Crypto: warmup 2020-09-01..2021-03-31 · GĐ1 2021-04-01..2022-06-30 · GĐ2
  2022-07-01..2023-09-30 · GĐ3 2023-10-01..2024-12-31 · GĐ4 2025-01-01..2026-08-31.
  Force-flat: UTC day end + fold edges; fill = NEXT bar open (signal-close law;
  pinned by golden fixture `test_golden_execution_math`).
- FX: warmup 2021-01-01..2021-03-31 · P1 2021-04-01..2022-06-30 · P2 2022-07-01..
  2023-09-30 · P3 2023-10-01..2024-12-31 · P4 2025-01-01..2026-09-23.

## 3. Cost model (frozen; Q-8 disclosures inline)

- Crypto per side = taker 5.0 bps (exchange CONTRACT constant — stated-not-tape,
  disclosed) + half-spread 1.0/0.5/1.0/1.5 bps (BTC/SOL/ETH/XRP; SOL from the measured
  bookTicker census p50 0.469). Stress ×1.0/×1.5/×2.0. Pairs (PAIRMR/ETHBTC): ×2 legs.
- Funding: MEASURED bytes — fundingRate monthly zips fetched keyless this session
  (288/288 files ok, 0 miss; premium + funding for BTCUSDT/SOLUSDT 2020-09..2026-08),
  charged in bps of entry notional for positions held across settlements.
- FX per fill = per-bar MEASURED half-spread from Dukascopy M1 bid/ask (floor 0.05 bps)
  × stress. **Broker-realizability cross-check (owner TWS reminder this session)**:
  read-only paper probe 7497 measured median 0.088 bps EURUSD / 0.302 GBPUSD /
  0.254 USDJPY (`TWS_SPREAD_PROBE_20260928T015508Z.json`; 96/191/213 quotes, 360s).
  TWS API confirmed READ-ONLY (order requests refused at source). The Dukascopy
  per-bar bill is the scored cost; the TWS probe evidences realizability today.

## 4. Floors (plan §3.2, unchanged) + verdicts

PF ≥ 1.10 @×1.0; expectancy > 0; ≥100 trades/fold, ≥400 total else NOT_RUN_THIN;
≥2/4 folds positive; top-fold ≤ 50%; weekday share ≤ 0.35; drop-one survival; PBO
≥8 configs else NOT_RUN; sub-power = INCONCLUSIVE. Every result row carries
`ANCESTRY_RELAXED_BY_OWNER_ORDER_2026-09-28` (amendment r1 §4 disclosure) and any
positive additionally requires the decorrelation court vs its named dead ancestor
(pooled |rho| ≤ 0.20 measured on the frozen representation) before any label
stronger than `OWNER_ORDERED_RESCORE_POSITIVE`.

## 5. Engine + verification (pre-PnL)

- Engine: `research/daytrader100/dt100/` (config/data/signals/arms/engine).
- Fixtures: `tests/test_dt100.py` — 7/7 PASS: hand-computed golden fill/cost math
  (signal-close → next-open, which caught and fixed a real 1-bar lookahead),
  no-lookahead mutation, day force-flat, clock-shadow parity+permutation,
  determinism, signal domain across 16 builders.
- Exact-arm dry-run: `--mode dry` emits per-arm record_id (params-digest),
  trades per fold, decision digest, clock-shadow parity, non-vacuity — NO PnL at
  any depth. Output: `research/control/DAYTRADER-100-V1/dry_run/dt100_dry_stress1.0.json`.
- Dry-run acceptance: record_ids pairwise distinct; every arm non-vacuous
  (≥50 trades); parity True. Any arm failing → NOT_RUN_THIN verdict, not rescue.

## 6. Staged data (this cycle, fetched this session)

- premiumIndexKlines 1m: BTCUSDT+SOLUSDT 72 months each (keyless, HTTP 200).
- fundingRate: BTCUSDT+SOLUSDT 72 months each.
- Cross-worktree reads (append-only evidence, sha manifest at staging time):
  klines_um_{BTC,SOL}USDT_1m (74+74 zips), ETH/SOL 1h panels, EURUSD/GBPUSD/USDJPY
  Dukascopy M1 BID/ASK day files.

## 7. Two-key status

Key-1 (A7 prelaunch): PENDING — dispatched after this freeze lands.
Key-2 (owner GO at gate): phrase `GO DAYTRADER 100 V1 SCORED EXECUTION`
registered-not-consumed. The owner's in-chat order is recorded as intent + scope
authority (AMENDMENT_r1 §1.3); it is NOT key-2 (P-8 / FOREX-FREE-V9 precedent).

## 8. Pin

- arms.py sha256: see commit metadata (freeze commit pins `sha256sum` of arms.py,
  config.py, engine.py, signals.py, data.py at commit time).
- Scored run contract: `run_dt100.py --mode scored --stress {1.0,1.5,2.0}` under the
  machine-wide heavy lock; per-cell identity report after each family; ledger rows
  appended to `TRIAL_LEDGER.jsonl` at computation time (observed denominator law).
