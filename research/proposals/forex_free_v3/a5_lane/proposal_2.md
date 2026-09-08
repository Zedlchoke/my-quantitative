# FXFV3-A5-P2 — Daily panel-outlier reversal in a high-dispersion state

Lane A5, cycle FOREX-FREE-V3. Outcome-blind. MACRO-FREE (permitted second proposal; signal uses
only the authorized price snapshot). Machine-readable packet: `proposal_2.json` (authoritative).

## Mechanism (one paragraph)

When one pair's 5-day move is an extreme outlier against the 7-pair panel (scale-free z vs panel
median and dispersion), the move is disproportionately one-sided-flow-driven and partially reverts
over the following days as liquidity providers unwind inventory (order flow drives FX — Evans-Lyons;
short-term reversal as liquidity-compensation — Nagel 2012, equity evidence, FX transfer is the
hypothesis under test). Trades fire only in a HIGH-DISPERSION state (cross-pair stdev of 5-day
returns above its own trailing median): the days where outliers are most plausibly overextension
rather than information. USD common moves are netted by the panel centering.

## Conditioning

None on macro (signal-side). The v3 dual-book mandate still applies: financing-adjusted book per
the frozen policy-rate-differential formula is computed as a book attribute for every arm and
gated (price-only must not invert anchor sign), but no macro series conditions any decision.

## Frozen constants

| quantity | value |
|---|---|
| decision clock | completed 16:00 America/New_York flat bar (daily) |
| return window | 5 daily bars |
| panel z | (R − median₇)/sd₇, population sd (ddof=0); sd=0 → day voided fail-closed |
| dispersion state | sd(t) > median of trailing 126 daily sd values |
| z threshold | 1.0 (strict) |
| exits | z zero-crossing or 10-bar time stop, next daily bar open |
| governor | 1 open position/pair; ≤ 3 RT/pair/week; excess signals dropped deterministically |
| fills | open of next existing 16:00-NY bar (Friday decision fills Monday) |
| warmup | 126 daily bars (schedule activates ~2020-08-03) |
| costs | 1.5 bps/side base; tiers 1.0/1.5/2.0 → 1.5/2.25/3.0 bps/side, F1-fixed on booked stress PnL; one-event delay stress kept separate (V3-L2) |

## Arms

- **anchor** `FXFV3-A5-P2-anchor`: high-dispersion state only; SHORT z>+1.0, LONG z<−1.0.
- **neighbour** `FXFV3-A5-P2-neigh` (one presumption away): same state/exits; selection by RANK
  (single max-|z| pair per day, frozen pair-order tie-break) instead of the z threshold.
- **causal control** `FXFV3-A5-P2-ctrl`: replaces panel z with the pair's own time-series z
  (R/σ_own(126d), same state gate, threshold, exits) — removes the cross-sectional ingredient.
  Preregistered non-reproduction rule: control expectancy > 0 AND PF ≥ 1.10 → control fires → family fails.
- **benchmark** `FXFV3-A5-P2-bench` (unscored reference inside the anchor cell): ungated panel
  reversal (dispersion-state gate removed), identical everything else. Overall incremental alpha =
  per-pair-day after-cost financing-adjusted PnL, anchor − benchmark > 0.

## Turnover / floors (schedule-level estimates, never optimized)

~1180 decisions/pair full-sample (floor ≥ 40 met by two orders of magnitude); anchor 15–35
RT/pair/yr, ~700–1600 panel-wide; F1 thinnest (~200–500 panel trades). Break-even headroom:
5-day moves order 20–100 bps gross vs 3–6 bps round trip.

## Drop-one

Drop-one pair: excluded pair leaves BOTH the trading set and the panel (honest 6-name panel);
≥ 5/7 recomputes keep positive expectancy and PF ≥ 1.00. Drop-one fold: expectancy stays positive
in all 3.

## Novelty

No session geometry anywhere (vs all four forbidden rows). The closest-looking row (V1 family2
late-NY extension fade) is distinguished in the packet by observable (5-day panel-relative return
vs intraday session standardized extension), clock (one 16:00-NY decision vs intraday), and
trade-time distribution (non-overlapping by construction). The "just short reversal" reading is
treated as a failure mode via the causal control, not a rescue. Full per-row self-check in
`proposal_2.json`.
