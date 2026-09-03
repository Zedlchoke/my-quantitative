# A4 Z3 Family Specification — Cross-Sectional ETF Relative Momentum / Sector Rotation

Status: FROZEN, outcome-blind. No returns, PnL, PF, Sharpe or ranking of these arms has been
computed. Canonical machine-readable spec: `a4_z3_relative_momentum_spec.json`
(sha256 `98d5307c3c3810a236f230475b190b34bd38461461cc7ea0a5ebdf38741416fa`).

## Family

`A4_XSEC_ETF_RELATIVE_MOMENTUM` — monthly cross-sectional relative-momentum rotation among the
ten accepted Select Sector SPDR ETFs, long-only plus cash, with a causal negative control.

## Cohort (frozen)

- Eligible universe: the 11 accepted ETFs (census digest `c9d4e88a…bc96`) + explicit cash (yield 0).
- Rankable cross-section: the 10 sector ETFs XLK, XLE, XLF, XLV, XLI, XLP, XLY, XLU, XLB, XLRE.
- SPY is benchmark-only (census role `BROAD_US_EQUITY_BENCHMARK`); never ranked, never held —
  putting the broad index inside a sector cross-section would double-count market beta.
- Limitation: current-survivor SPDR seed list; inference restricted to the frozen cohort.

## Series semantics

- Features on the TR index `P^TR` built by the amended FD2 formula: raw closes x issuer-confirmed
  split factors + official issuer distributions. Fills on raw executable prices, never the signal
  close. Strict separation of TR features from raw fill prices.
- One-event delay mandatory: decide at session t close, execute at session t+1.

## Clock (frozen)

MONTHLY. Decision on the completed bar of the last regular session of each calendar month
(US_EQUITY_REGULAR_V1); fills the immediately following regular session; hold to next rebalance or
force-flat event. Weekly was rejected a priori: the 12-1 mechanism is documented at monthly
horizons; a weekly clock imports short-horizon reversal contamination and ~3-4x turnover.

## Features (frozen)

- `mom_i(t) = P^TR_i(t-21) / P^TR_i(t-252) - 1` (12-month formation, 1-month skip; canonical
  Carhart/Jegadeesh-Titman horizon).
- `sigma_i(t)` = sample std of daily log TR returns over the same formation window [t-252, t-21].
- `mra_i(t) = mom_i(t) / sigma_i(t)`.
- Data readiness: a decision is valid for ETF i only if the full 253-session window exists;
  failing ETFs are excluded from that decision's ranking (not expected in S0).
- Warmup extension (declared, not silent): vendor coverage starts 2018-01-02, so the first valid
  decision is the 2019-01-31 month-end (filled 2019-02-01). Monthly slots 2018-04..2018-12 are
  unscored warmup-extension. No truncated-lookback fallback permitted.
- Ties: ascending symbol (deterministic; probability ~0).

## Arms (exactly three, preregistered)

1. `ARM_A4_ANCHOR_MOM121_EQW_TOP3` — ANCHOR. Rank by `mom_i` descending, hold top 3 equal-weight
   (33.33% each), gross 1.0. Literature: Jegadeesh & Titman (1993, JF); Moskowitz & Grinblatt
   (1999, JF); Carhart (1997, JF); Asness-Moskowitz-Pedersen (2013, JF); O'Neal (2000, FAJ)
   (exact wording MODEL_INTERNAL_UNVERIFIED).
2. `ARM_A4_NEIGHBOR_VOLADJ_MOM121_INVVOL_TOP3` — NEIGHBOUR. Rank by `mra_i` descending, top 3,
   inverse-vol weights `w_i ∝ 1/sigma_i`, 35% cap then renormalized. Mechanism lever: risk
   normalization (momentum-crash channel), not a new lookback. Literature: Barroso & Santa-Clara
   (2015, JFE); Daniel & Moskowitz (2016, JFE) (MODEL_INTERNAL_UNVERIFIED).
3. `ARM_A4_NEGCTRL_BOTTOM3_EQW_MOM121` — NEGATIVE CONTROL. Identical everything, sign reversed:
   hold the BOTTOM 3 by `mom_i`. If cross-sectional persistence is real, this must destroy the
   mechanism. Falsification rule: if the control passes both primary Stage-A gates (after-cost
   expectancy > 0 AND PF >= 1.10) or matches/beats the anchor's after-cost expectancy in >= 2 of
   3 folds, the mechanism is FALSIFIED and the family is rejected regardless of anchor results.

## Portfolio (frozen)

Long-only + cash; gross <= 1.0; no shorts, no leverage; per-ETF weight cap 35%; no rank buffers
(required so the control differs from the anchor by the ranking sign only); deterministic target
books.

## Windows, folds, terminal close (frozen)

- Warmup 2018-01-02..2018-04-03 plus the readiness extension to 2019-01-31; no scored trades.
- Three chronological S0 folds (2018-04-04..2020-09-09 / 2020-09-10..2023-02-16 /
  2023-02-17..2025-07-31), scored ends 2020-09-01 / 2023-02-09 / 2025-07-24, 5 purge sessions,
  force-flat at each scored end and at the 2025-07-31 S0 terminal close. Force-flat exits are
  costed one-way trades; each fold starts flat; a holding crossing a force-flat event is closed
  early at that event.
- S1 (2025-08-01..2026-07-31) is SEALED: referenced only for the force-flat boundary; no S1 date
  enters any decision, hold, feature or evaluation schedule.

## Benchmark

SPY total return (same TR architecture) reported as context; the hard benchmark for Stage-A gates
remains flat (0% after cost). SPY TR carries the recorded 0.39% cumulative divergence vs SSGA
NAV-TR with a priori tolerances (DA2).

## Costs and delay (frozen)

- Base case: 7 bps one-way per ETF clip = spread 2 + slippage 3 + conservative commission/ops
  buffer 2 bps. No free-trading claim; commission levels are not evidenced and are covered by the
  buffer.
- Stress: 12 bps one-way for Z6 schedule feasibility only; stress never tunes the base case.
- Cash yield 0. One-event delay mandatory.

## Evidence count (frozen)

Minimum 60 independent monthly decisions total and >= 15 per fold (independence from
non-overlapping monthly holds). Expected calendar slots in S0: 77 total (20 / 28 / 29 across
folds 1-3) — arithmetic on the frozen partition, no outcome computation. Fewer realized decisions
=> arm UNCOUNTED, not rescued.

## Turnover, capacity, concentration

- Prior expectation (not computed): ~1.5-3.5x gross one-way per year for anchor/control
  (~1-2 of 3 holdings change monthly, no buffers); neighbour moderately higher from inverse-vol
  reweighting. Z6 feasibility ceiling: <= 6.0x gross one-way per year at base-case cost.
- Capacity: smallest member XLRE median ADV ~$197M; a 33.3% weight on a $1M book is ~$333K
  ~ 0.17% of that ADV; not binding below roughly $50M book at <= 1% participation. Realized
  participation measured at Z6.
- Concentration: weight cap 35% everywhere; Stage-A gate "no ETF > 35% of positive PnL/risk" and
  "no fold > 50% of positive PnL" apply as measured.

## Why this is not a lookback grid

Each arm is one frozen configuration: one lookback pair (252/21), one vol window (the same
formation window), one rank count (3), one weighting scheme, one clock (monthly), one cost base
(7 bps). All constants were fixed a priori from literature convention or frozen plan constraints.
No alternative value was scored or compared; changing any value after any scored computation
voids the arm. No tuning of any kind was performed; no scored artifact exists; the A5 (z3-trend)
lane was never opened; no branch switching occurred.
