# H-XSECT-FUNDING-CARRY-v1 — V6 hypothesis specification (A6 blind draft)

State: SPEC_DRAFT — PENDING_V6P_AUTHORIZATION
Owner: A6 (hypothesis owner)
Drafted at: H00–H00:30 block of PLAN §4 (V6P), BEFORE any V6P validation run exists.
Machine contract: `candidate.yaml` (verbatim PLAN §8.2). Status sidecar: `status.yaml`.
Freeze/hash by A1 happens only if V6P passes 20/20 (PLAN §5 checkpoint / §8).

## 1. Mechanism

Perpetual futures funding is a periodic cashflow transferred between directional
holders: when funding is positive, longs pay shorts; when negative, shorts pay
longs. Trailing mean funding therefore measures which side of each market is
crowded and how much carry a position on the other side collects per unit of
exposure.

This hypothesis builds a market-neutral cross-sectional portfolio on the
S0-seven universe: rank symbols by trailing mean of published, already-settled
funding observations as of signal time, go LONG the bottom-2 funding group
(uncrowded / shorts-pay side, i.e., we collect or pay minimal carry) and SHORT
the top-2 funding group (crowded longs who are paying elevated carry away from
us). Only funding observations settled AND published at or before the daily
00:00 UTC signal clock enter the feature — no lookahead, no forward-fill beyond
the last settled timestamp.

Economic intuition: crowded-long names carry elevated funding that (a) pays us
while we are short and (b) pressures crowded holders to unwind, while uncrowded
names offer cheap or negatively-priced long exposure. Equal-ish gross split,
24h rebalance, 24h purge/embargo around chronological folds.

## 2. Economic prior vs edge claim

**This is an economic prior, not an edge claim** (PLAN §8.1). It can fail:
price loss may overwhelm collected carry; funding may reflect information price
already impounded; costs may dominate an 8h-cadence cashflow harvested at 24h
rebalance; the effect may live in only one fold or one symbol. No claim of
confirmed edge may be made from drafting, locking, or any single passing gate.
Eligible outcomes are restricted to the allowed set in `status.yaml`.

## 3. Frozen pre-registration contract (summary)

The machine-readable contract is `candidate.yaml`, copied field-for-field from
PLAN §8.2 without deviation:

- Family `cross_sectional_funding_carry`, stage S0_EXPLORATORY.
- Universe: ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, LINKUSDT, ADAUSDT;
  BTCUSDT benchmark context only.
- Signal clock daily_00_00_utc; feature = trailing mean of published settled
  funding ONLY; lookbacks {1D, 3D, 7D} = exactly three scored candidates plus
  one negative control (`reverse_funding_rank_3d`) = four launches, no fifth
  (PLAN §9.1).
- Long bottom-2 funding / short top-2 funding; rebalance 24h.
- Chronological 3-fold with 24h purge/embargo.
- Risk caps: target_gross 0.80, hard_gross_cap 1.00, hard_abs_net_cap 0.10,
  max_abs_weight_per_symbol 0.20.
- Trial budget: 3 scored candidates + 1 negative control.

Items marked `TO_FREEZE_AT_AUTHORIZATION` in `candidate.yaml` (effective S0
common window; data/funding/metadata hashes; warmup and signal/fill clock
details; funding publication convention and missing-settlement policy;
cost/latency/terminal/risk/accounting/metric versions; global trial-ledger
count and DSR estimator; hard gates/scorecard/tie-break/resource limits/seeds/
tolerances) are frozen by A1 before signal implementation, per PLAN §8.2.

## 4. Mechanism invalidation conditions (from PLAN §9.3, summarized)

Reject the candidate if ANY of:

1. After-cost canonical PnL <= 0.
2. Net funding cashflow <= 0, or fewer than 2/3 folds positive on funding.
3. Price PnL masks negative funding while the strategy claims carry.
4. PF < 1.10, fewer than 2/3 positive folds, or median fold return <= 0.
5. No adjacent positive lookback pair among 1D/3D/7D.
6. Top fold > 50% or top symbol > 40% of positive PnL.
7. MDD > 10%, risk cap breach, margin breach, or abs(BTC beta) > 0.25.
8. Any required stress loses the mechanism or violates a hard risk/data gate.
9. Reverse control beats the best directional candidate.
10. DSR probability < 0.95 using the complete global trial ledger.
11. Any data/PIT/accounting/integrity/reproduction/audit check not PASS.

## 5. Forbidden post-lock changes

After A1 freezes this spec, NONE of the following may change (PLAN §8.2):

- Any frozen parameter value (universe, lookbacks, legs, rebalance, folds,
  purge/embargo, risk caps, trial budget, negative control).
- Adding OI, momentum, volatility, regime filters, per-symbol parameters,
  extra lookbacks, or another rebalance interval in v1.
- Window or universe changes after results; silent skip/replacement.
- Editing rules/grid bytes after lock — verdicts and metadata corrections go
  to `status.yaml` only (sidecar principle).
- Relabeling a mechanism failure as a pipeline failure to unlock V7/S1.
