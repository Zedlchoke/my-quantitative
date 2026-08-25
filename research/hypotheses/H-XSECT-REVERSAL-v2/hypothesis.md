# H-XSECT-REVERSAL-v2 — Six-alt weekly cross-sectional reversal (V8 prereg)

**Family:** `cross_sectional_weekly_reversal` · **Stage:** `S0_EXPLORATORY` ·
**Owner:** A6 · **Validator:** A7 · Frozen **before** the first scored V7
artifact (PLAN §17.1).

## Research question (PLAN §17.1)

This is an independent family from V6/V7 — **not** a rescue, filter, or tuning
of funding-price divergence. The question under test is different: after a
period of relatively strong up/down moves, do the winning and losing altcoins
reverse over the following week? Concretely: rank the six-alt universe by past
return over a formation lookback (3D / 7D / 14D), go long the bottom-2 losers
and short the top-2 winners, hold one week, rebalance every Monday 00:00 UTC.

## Why v2 exists (v1 lineage)

H-XSECT-REVERSAL-v1 was drafted as an IDEA but blocked: its universe included
ETH, whose common data intersection was only about one year of 15m bars — too
short for stable weekly ranks across seven symbols and ≥20 observations per
fold. It also lacked a portfolio engine for cross-sectional baskets.

v2 resolves the data blocker by dropping ETH **only** via a data-availability
rule that is itself frozen here, BEFORE any performance is observed. The v2
universe is six altcoins with roughly two years of clean history:
SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, LINKUSDT, ADAUSDT (BTCUSDT is
measurement-only context). This is the exact v1 promotion criterion recorded
in the v1 hypothesis ("common 15m intersection ≥ 2y"). No symbol may be added
or removed based on PnL after this freeze; the eligibility rule requires all
six symbols or the whole rebalance is skipped.

The portfolio-engine gap is addressed by PLAN §17 topology (dedicated V8
worktree), not by changing the science.

## Frozen design summary (full contract: candidate.yaml)

Weekly Monday 00:00 UTC signal on completed bars; lookbacks exactly
3D/7D/14D; long bottom-2 losers / short top-2 winners; gross 0.80, net 0
(0.40/0.40 per leg), max abs symbol weight 0.20; fills at the next completed
15m event with one-tick adverse slippage, fee 0.0005, native funding
accounting; three chronological folds with 7-day purge/embargo and ≥14-day
warmup; exactly three normal trials plus one 7D momentum control
(XSECT-WMOM-7D-CONTROL) to verify the reversal sign is doing the work.

## Labels and constraints

- S0 exploratory screening only — never "untouched OOS", never S1/promotion
  evidence.
- The full forbidden-after-freeze list (filters, cadence changes,
  per-symbol removal, added lookbacks, threshold/cost/fold/window/universe
  changes, use of V7 results, OOS relabeling) is binding and enumerated in
  candidate.yaml.
- The V8 agent must not read `results/portfolio_v7`, partial logs, metrics,
  or verdicts; scored runs wait for a valid V7 terminal outcome plus gates
  T01–T15 (PLAN §17.3).
- If this preregistration lands after any V7 metric leaks: label
  `V8_PREREG_WINDOW_MISSED`; no V8 that night.
