# A5 proposal 2 — V12-A5-P2-MIX-ORDERSIZE (participant-mix / order-size composition)

Lane A5, outcome-blind. This narrative accompanies `a5_prop2.json`; the JSON is the
machine-checkable record. No returns, PnL, PF, Sharpe, ranking or backtest was computed in
this lane; all floor verification belongs to the schedule-only gate.

## Mechanism in one line

A weekly (Monday 00:00:00Z), BTC-beta-neutral long/short quintile book over the 19 non-BTC
perps sorted on within-symbol order-size composition — recent 30-day mean of per-bar average
trade size (quote-volume / trade count) relative to the prior 60-day baseline — long the
rising-institutional-footprint quintile, short the falling-average-trade-size (retail-heavy)
quintile, with the sign prediction that retail-like accumulation overprices (Hvidkjaer 2008;
Kelley & Tetlock 2013).

## Primary-source claim and crypto transfer

- S7 (Hvidkjaer 2008, RFS 21(3), DOI 10.1093/rfs/hhn049): small-trade buy pressure is
  followed by significant subsequent underperformance; large-trade pressure is not. This is
  the anchor sign claim: the participant mix observable in trade sizes carries pricing
  content.
- S8 (Kelley & Tetlock 2013, JF 68(3), DOI 10.1111/jofi.12028): order-size classification
  separates retail from institutional flow and retail imbalance carries predictive content —
  the justification for using quote-volume/trade-count as the mix proxy when client-level
  data are unavailable.
- S9 (Natashekara & Sampath 2024, FRL 61, DOI 10.1016/j.frl.2023.104909): trade-size-based
  informed-trading analysis exists for crypto markets (identity-level support only; the
  abstract was not retrievable, so no empirical sign is imported from it — the crypto sign
  rests on the S7+S8 transfer plus S10's venue evidence).
- S10 caveat (Kim & Hansen 2026, arXiv:2607.09426): on Binance perps, algorithmic bursts at
  quarter-hour marks distort trade-size statistics. Consequences adopted: bar-level,
  multi-week aggregation only; a data-quality gate; and a mechanism-destroying placebo.
  Their intraday order-imbalance claim is NOT used (aggressor-adjacent, wrong horizon).

## Transfer caveats

Bar-level average trade size is a coarse mix proxy (whale splitting, API execution);
minimum-notional and fee-tier changes mechanically reshape distributions — hence a
WITHIN-SYMBOL ratio (30d vs prior 60d inside the same frozen 90d window) so venue-wide shifts
cancel; wash-volume risk bounded by universe choice plus the data-quality gate; and the
equity evidence is signed small-trade pressure while our bar statistic is unsigned — the
composition channel, not flow direction, carries the claim, and the placebo is the primary
guard.

## Economic counterparty and expected sign

Retail cohort splitting into small clips accumulates during speculative episodes (falling
average trade size at rising trade counts), taking inventory from larger participants.
Anchor sign: long the top order-size-ratio quintile (rising institutional footprint), short
the bottom quintile (retail-heavy). Per S7 the retail-heavy side underperforms.

## PIT discipline

Fields: 15m completed bars' `quote_volume` and `trades` columns (plus BTCUSDT closes only
for the beta-neutralisation risk primitive). The formation statistic uses only bars with
`ts_event` at-or-before the Monday 00:00Z stamp and trades > 0; >= 80% of bars in both
sub-windows must have trades > 0; the full 90d block must be covered (shared frozen warmup).
Execution: one declared lag (fill at the 00:15Z close of the first completed bar after the
stamp). Funding: native accrual while held only, PIT span rule; never a signal.

## Schedule

19-name universe. Eligibility: covered 90d block, data-quality gate, >= 9 eligible names
(else carry prior book forward). Formation: quintiles on the order-size ratio. Holding:
intended 28d, two-stamp hysteresis, 28d per-symbol re-entry cooldown. Rebalance: weekly
Mondays, terminal FORCE_FLAT at the frozen boundary; 52 discretionary decisions/365d by
construction.

## Target book and risk neutralisation

Identical book primitives to prop 1 (deliberately shared risk plumbing so the two proposals
differ only in mechanism): `w_i = ±min(0.30, 0.5/n_leg)`, leg gross 0.5, beta-neutral leg
tilt on trailing 90d betas, whole-book uniform shrink so `max|w| <= 0.30` at every stamp by
construction with no post-score renormalisation. Median intended holding 28d; turnover guards
as in prop 1; magnitudes deferred to the schedule gate.

## Anchor, neighbour, causal control (3 scored cells — the family maximum)

- Anchor: order-size-ratio quintile L/S.
- Justified neighbour: small-trade-share — share of the trailing 30d bars sitting in the
  symbol's own bottom quartile of per-bar average trade size; long lowest share / short
  highest. Justified by S7's bucket construction: a bucket-share estimator is a
  theory-mandated alternative estimator of the same latent mix variable, not a
  parameterization of the mean-ratio anchor.
- Causal negative control: trade-count-permuted placebo — permute each symbol's 15m trade
  counts within its own 90d formation window (all marginal distributions preserved, the
  temporal mix signal destroyed) and trade the identical skeleton. If the placebo tracks the
  anchor, the driver is volume/count level (volume-shock / illiquidity adjacency) and the
  mix family is falsified.

## Costs, funding, stress

Identical cost posture to prop 1: repo tier-0 taker fee floor, declared adverse-tick
slippage with schema tick sizes, adapter cost primitive for all transitions, native funding
accrual while held under `LONG_PAYS_POSITIVE_RATE`, frozen stress cells (fee x1.5, +2 ticks,
+1 event delay) plus the derived drop-one-symbol / drop-one-fold matrix.

## Falsification

(1) Anchor fails its pre-registered gate vs the flat hard gate while the placebo does not;
(2) anchor and placebo indistinguishable in gate outcome and turnover profile; (3)
volume-shock adjacency probe — leg changes coincide with 15m quote-volume bursts, i.e., the
ratio moves only around algorithmic bursts; (4) sign failure — the retail-heavy leg
outperforms (anchor sign inverted): the family is falsified, never re-signed post hoc.

## Ancestry and why this is not a rescue

Distinct at mechanism level from every forbidden class: no price-impact statistic (ILLIQ), no
shock or continuation conditioning (VOLCOMP / volume-shock), no signed flow (aggressor
absorption), no return-distribution statistic (LOT/MAX/skew), no past-return ranking
(momentum / reversal), no funding input (carry), no OI input (OILEV), schema-only inputs
(DATA-GATED). The illiquidity boundary is guarded structurally: the placebo collapses the
anchor onto a volume/count-level object exactly when mix is not the driver, so an
illiquidity-like driver is detected and rejected rather than smuggled in. Why not a rescue:
no lottery statistic is inverted; no impact or OI construction is retuned; the 30d/60d
formation windows are derived from the data contract's single frozen 90d warmup; fees are
the declared floors; the full eligible universe is binned mechanically; the 0.30 cap holds
by construction; and if the staged bars lack the trade-count column the proposal is
withdrawn rather than silently re-derived from a substitute statistic.
