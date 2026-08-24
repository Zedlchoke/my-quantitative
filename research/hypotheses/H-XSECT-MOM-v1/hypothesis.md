# H-XSECT-MOM-v1 — dollar-neutral cross-sectional momentum

## Mechanism (economic rationale)

Liquid USD-M perpetuals exhibit persistent cross-sectional return dispersion
driven by staggered demand/supply imbalance: coins with strong trailing
short-horizon momentum keep attracting flow (breakout chasers, funding-carry
seekers) while laggards bleed. Ranking on trailing cumulative log returns and
going long the top / short the bottom captures this relative-strength spread
while the dollar-neutral construction strips the common market beta that
killed every directional family in Sprint V2 (ema_atr avg exp −0.397 across
2,730 trades; mean_reversion −0.492; regime_switch −0.413; trend_pullback
−0.378 — all 28/28 symbol-cells negative after costs).

Literature prior (Liu–Tsyvinski–Wu 2019; Liu–Tsyvinski 2021) documents a
cross-sectional momentum factor in crypto — used strictly as motivation, not
as in-repo evidence: paper universes are broader, mostly spot, cost-free.

## Counterparty

Late momentum chasers entering AFTER our ranking rebalance provide exit
liquidity; crowded funding-paying longs in laggards are the short side's
counterparty. We accept being early against continuation flows in exchange
for neutralizing market direction.

## Expected regimes

Trending dispersive regimes (post-expansion rotation); degraded in tight
correlation squeezes where dispersion < funding + fees.

## Holding horizon & execution

24h rebalance at daily 00:00 UTC signal clock; fills at NEXT_BAR_EVENT
(15m bar following the signal cutoff); legs held continuously between
rebalances; funding settled per actual held positions.

## Costs

Maker/taker fees per instrument tier-0, one-tick adverse slippage per fill,
funding post-trade audit from canonical bundles.

## Quantitative invalidation (pre-registered BEFORE any scored run)

1. Family REJECTED unless at least TWO ADJACENT lookbacks in {3,7,14} have
   positive portfolio expectancy-R after all costs (`parameter_spike_fail`
   otherwise).
2. Best candidate REJECTED if realized |BTC beta| > 0.25 (`BETA_EXPOSURE_FAIL`).
3. Edge confined to a single symbol (>40% positive-aggregate PnL contribution)
   → universe artifact → reject candidate.
4. Any XG0–XG5 FAIL blocks selection regardless of score.
5. Negative control (reverse-rank 7d) outperforming the directional best is a
   mechanism-falsification red flag recorded in the registry.

## Trial budget

3 scored candidates (lookbacks 3/7/14) + 1 negative control = 4 experiments
total. No volatility scaling, no funding threshold, no regime filter, no
per-symbol parameters, no OI overlay, no extra lookback/rebalance interval.

## Universe (fixed before run)

Traded: ETHUSDT SOLUSDT BNBUSDT XRPUSDT DOGEUSDT LINKUSDT ADAUSDT.
Benchmark context only: BTCUSDT.
