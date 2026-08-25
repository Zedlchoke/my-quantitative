# H-XSECT-REVERSAL-BREADTH-CRYPTO-v1 — Ten-crypto weekly cross-sectional reversal breadth (V8X Cohort C prereg)

**Family:** `cross_sectional_weekly_reversal_breadth` · **Cohort:**
`CRYPTO_USDM_1Y_10` · **Stage:** `S0_EXPLORATORY_BREADTH_SCREEN` ·
**Owner:** A6 · **Universe:** A8 (performance-blind) · **Validator:** A7 ·
Frozen **before** the first scored V8 core artifact (PLAN §8).

## Research question (PLAN §8–9)

Does the weekly cross-sectional reversal mechanism found in the frozen
six-alt V8 contract generalize in *breadth*: does it survive when the
universe is enlarged to the top-10 most liquid Binance USD-M perpetuals
selected by a deterministic pre-performance volume rule, over a common
one-year intersection? This is a NEW breadth screen — NOT an amendment,
extension, or symbol-addition to `H-XSECT-REVERSAL-v2`, and NOT derived from
any V6/V7/V8 performance observation.

## Universe selection freeze (PLAN §9.1 — applied by A8, blind to all PnL)

1. Binance USD-M `PERPETUAL`, quote `USDT`, valid trading status at the
   frozen cutoff.
2. `onboardDate ≤ window_start − 365 days`.
3. ≥365 days of common 15m bars and native funding coverage.
4. Zero unexplained gaps in the scored window; PIT metadata/hash complete.
5. Rank eligible symbols by **median daily quote volume in the 30 days
   strictly before** the scored window; take exactly the top 10.
6. Both accepted and rejected universes are recorded (anti-survivorship).
7. Fewer than 10 eligible ⇒ `V8X_CRYPTO_NOT_STARTED_DATA_INCOMPLETE`; gates
   are never lowered.

Window: common one-year intersection ending no later than `2026-08-21T00:00Z`;
exact endpoints belong to the audit, not to this memo.

## Frozen design summary (full contract: candidate.yaml)

Monday 00:00 UTC signal on completed bars only; formation lookbacks exactly
3D/7D/14D; long bottom-2 losers / short top-2 winners; hold one week;
gross 0.80, net 0; fills at the next completed 15m event, one-tick adverse
slippage, fee 0.0005, native funding; three chronological folds with 7-day
purge/embargo and ≥14-day warmup; all-ten eligibility with whole-rebalance
skip on incompleteness. Exactly three normal trials plus the 7D momentum
control (`V8X-C-WMOM-7D-CONTROL`) = four scored candidates, waves X1–X4
(PLAN §11.1).

## Labels and constraints

- Exploratory breadth screen only. Best possible outcome is
  `V8X_CRYPTO_BREADTH_PASS_EXPLORATORY`; no V8X outcome authorizes S1/live.
- Statistical treatment is fully separate from equities and from V8 core:
  separate ledgers/cost models/calendars; DSR counts global search history
  but estimates per comparable cohort; PBO never mixes cohorts (PLAN §11.2).
- The forbidden-after-freeze list (PnL-based universe edits, added
  lookbacks, threshold/cost/fold/window changes, use of V8 core results,
  replacement trials) is binding and enumerated in candidate.yaml.
- If this preregistration lands after any scored V8 core metric exists:
  label `V8X_PREREG_WINDOW_MISSED`; no V8X this sprint.
