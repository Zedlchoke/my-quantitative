# A6 Proposal 1 — V11-A6-ILLIQUIDITY-PREMIUM (crypto-perpetual, monthly, low-turnover)

Producer: D1-A6 (outcome-blind lane). Frozen 2026-09-02T14:56:31Z, AFTER the logged
literature search (a6_search_log.json) and BEFORE any candidate return, PnL, PF, Sharpe
or ranking for this family was computed or read. V11 budget 0/12; no scored artifact
exists in any V11 tree. This document is a proposal only; no code, no data computation.

## 1. Primary-source citations with claim-to-test mapping

| ID | Source (identity verified in a6_search_log.json) | Exact claim used | Repo test that could reject it |
|---|---|---|---|
| P1-S1 | Amihud, Y. (2002), "Illiquidity and stock returns: cross-section and time-series effects", Journal of Financial Markets 5(1), 31–56, DOI 10.1016/S1386-4181(01)00024-6 | Price impact per dollar of volume (the Amihud ratio) is priced cross-sectionally: high-illiquidity assets earn higher expected returns, compensating liquidity providers | Monthly spread book net of adapter costs + native funding; causal inverted control (see §7) |
| P1-S2 | Liu, Y., Tsyvinski, A., Wu, X. (2022), "Common Risk Factors in Cryptocurrency", Journal of Finance 77(2), 1133–1177, DOI 10.1111/jofi.13119 | The crypto cross-section admits a small factor model; the size premium partly captures an illiquidity premium; the Amihud measure is admissible in the crypto cross-section | Same monthly spread book; orthogonality rho vs the book of any size/low-vol sort (A7-N) |
| P1-S3 | Wei, W.C. (2018), "Liquidity and market efficiency in cryptocurrencies", Economics Letters 168, 21–24, DOI 10.1016/j.econlet.2018.04.003 | Crypto return predictability is governed by liquidity conditions (predictability concentrates in less liquid names) | Liquidity-bucket diagnostic; PIT/no-leak fixtures |
| P1-S4 | Pástor, Ľ., Stambaugh, R.F. (2003), "Liquidity Risk and Expected Stock Returns", Journal of Political Economy 111(3), 642–685, DOI 10.1086/374184 | Sensitivity to aggregate liquidity shocks (liquidity risk) is a distinct priced channel from the illiquidity LEVEL | Neighbour arm book (see §7) |
| P1-S5 | Binance USD-M market-data docs (= frozen packet source S4, verified by A1) | Semantics of completed 15m klines (OHLCV incl. quote volume) used for daily aggregation | PIT/no-leak fixtures; coverage fail-closed per lesson L-V10P-COVERAGE |

Momentum (a factor in P1-S2's model) is NOT used anywhere in this proposal; only the
illiquidity/size-liquidity claims are consumed.

## 2. Economic mechanism + expected counterparty

Thin-book assets impose price impact on impatient traders. Investors who demand
immediacy (retail chasers, forced deleveragers, headline-driven flow) pay that impact
repeatedly; agents willing to hold illiquid names for weeks are compensated with a
premium (Amihud 2002 channel; in crypto, Liu–Tsyvinski–Wu attribute part of the size
premium to exactly this). Expected counterparty: impatient liquidity demanders in
thin order books, whose flow is persistent at daily-to-weekly horizons but not at the
monthly formation horizon of this book. The mechanism is compensation for PROVIDING
liquidity/sleeping breadth — it is not a trend, reversal, lottery or carry harvest.

## 3. Required observable fields + PIT clock

- Inputs: completed 15m bars only (close, quote volume) for every symbol and BTC in the
  frozen staged snapshot. No funding, OI or mark input enters the SIGNAL (funding is
  charged while held only, §9).
- Daily UTC aggregation: r_i,d (close-to-close) and DollarVol_i,d = sum of 15m quote
  volumes, from COMPLETED bars only.
- Residualisation: rolling 90d daily beta vs BTC (frozen rule of the A1 packet); the
  numerator uses the BTC-residual daily return |r_i,d − β_i·r_BTC,d| so the sort is not
  a beta/trend proxy.
- Feature: ILLIQ_i,T = trailing 28d mean of |residual daily return| / DollarVol, scaled
  by 1e-6, cross-sectionally rank-normalised at each decision.
- PIT clock: features computed strictly from data available before the decision instant;
  decision at 00:05 UTC on the first calendar day of each 28d cycle; ONE declared
  execution lag — orders fill at the first completed 15m bar after the decision instant.
  Coverage gaps fail closed (no stale-tail synthesis).

## 4. Universe + benchmark role

- Universe: Binance USD-M staged snapshot; eligibility at each decision requires ≥90d
  completed-bar history (beta + feature window) and a tradability floor (median daily
  dollar volume ≥ declared minimum so taker fills are realistic); fail-closed on
  missing symbols. BTC and ETH retained (they anchor the liquid leg).
- Benchmark role: BTC is residualisation CONTEXT only; the family benchmark is the
  equal-weight universe return. The claim is the cross-sectional SPREAD, not market
  direction; the book is designed beta-neutral (§6).

## 5. Schedule, holding period, turnover rationale

- Schedule: 13 discretionary decisions/365d (one per 28d cycle) « floor 60.
- Holding: intended holding ≈ 28d per name; median intended holding ≥ 3d floor with a
  large margin. A no-trade half-bucket band suppresses churn when ranks barely move.
- Cost feasibility: ~13 one-way book transitions/yr on gross 1.0 (0.5 long + 0.5 short)
  at the declared taker floor + adverse-tick slippage gives a base drag of order
  1–2%/yr « 8% floor; stressed cell (fee ×1.5, +2 ticks) of order 2–3%/yr « 12% floor.
- Symbol concentration: both legs are equal-weight buckets of many names; with a no-trade
  band and per-symbol weight caps, no symbol should exceed 25% of one-way turnover —
  verified by the A3 schedule-only gate before scoring.

## 6. Target construction + risk neutralisation

- Sort eligible names by ILLIQ_i,T; long the top illiquidity tercile, short the bottom
  (most liquid) tercile, equal weight, gross 1.0 split 0.5/0.5.
- Risk neutralisation: (a) BTC-beta neutrality via the rolling 90d beta applied per leg;
  (b) per-symbol weight cap; (c) residual feature (already BTC-residualised) so the book
  is not a market-beta tilt; (d) minimum 6 names per leg or the decision fails closed.

## 7. Arms: anchor, theoretically-justified neighbour, causal negative control

- Anchor: ILQ-AMIHUD-28D-M — long high / short low BTC-residualised 28d Amihud
  illiquidity, monthly, gross 1.0.
- Theoretically-justified neighbour: ILQ-LIQBETA-90D-M — long high / short low
  sensitivity of daily residual returns to the aggregate market illiquidity shock
  (cross-sectional high-frequency innovation of the universe-median Amihud level),
  90d window, monthly (Pástor–Stambaugh liquidity-RISK channel: compensation for
  bearing systematic liquidity shocks, distinct from holding an illiquid LEVEL).
- Causal negative control: ILQ-AMIHUD-28D-M-INV — the sign-INVERTED anchor book
  (long liquid / short illiquid). Mechanism-destroying: if the liquidity-provider
  compensation story is what earns the spread, the inverted book must NOT earn a
  positive after-cost spread.

## 8. Expected sign + falsification condition

- Expected sign: anchor net spread > 0 (illiquid minus liquid outperforms after adapter
  costs and native funding); neighbour net spread > 0; inverted control ≤ 0.
- Falsification: any positive after-cost spread on ILQ-AMIHUD-28D-M-INV, or a
  non-positive after-cost anchor spread, kills the mechanism claim. Published returns
  (P1-S1..S4) are priors only; they waive nothing.

## 9. Funding / cost treatment

- Funding: charged while held via the adapter (LONG_PAYS_POSITIVE_RATE) — ~84 native
  8h settlements per 28d holding; funding is never a signal input, so no carry
  contamination is possible.
- Costs: transition cost via the frozen adapter arithmetic
  (taker_fee_bps × multiplier per side + adverse ticks × tick_size/price), gated by the
  A3 schedule-only cost floor gate BEFORE any scoring. Illiquid legs carry wider real
  slippage than generic floors — the stressed cell exists to expose exactly this; a
  FAIL or UNAVAILABLE verdict stops the family pre-score.

## 10. Known ancestry / proximity + orthogonality argument

- V1–V10 families: this lane knows only M01 (V10 high-turnover aggressor-flow
  absorption, rejected with ~zero gross edge, loss ~100% costs). No shared signal,
  horizon or book construction: M01 consumed high-frequency aggressor-flow pressure;
  this family consumes a monthly cross-sectional liquidity LEVEL. The banned
  mechanisms (trend/momentum, reversal/residual mean-reversion, funding carry,
  volume-shock continuation, weekly reversal, aggressor-flow absorption) contain no
  liquidity-sorted family; nothing here rescues any of them (§12).
- Reserved seeds: DEF-RESIDUAL-RISK sorts on residual volatility; LOTTERY-MAX-SKEW
  sorts on residual MAX/skew. This family sorts on price impact per dollar volume.
  Residual overlap risk is disclosed: illiquid coins skew high-vol and high-MAX.
  Orthogonality argument: the sort key is a volume-normalised IMPACT measure, not a
  return-moment; the proposed Stage-A A7-N check is the book-weight correlation rho
  against both seed books (reject if rho high), plus a within-volatility-bucket
  illiquidity-spread diagnostic (no new arm; diagnostic only) to show the premium is
  not repackaged low-vol.

## 11. Data readiness + implementation estimate

- Data: completed 15m bars incl. quote volume already staged in the frozen snapshot;
  no new external data. Coverage diagnostics only (no candidate returns) needed first,
  fail-closed per lesson L-V10P-COVERAGE.
- Implementation: plugin on GenericStrategyBase reusing schedule/folds/cost/funding
  accrual unchanged; new code is the daily aggregator, residual beta, Amihud feature
  and bucket book builder. Estimate 1–2 working days + A3 gate run.

## 12. Why this is not a rescue of a previously rejected family

M01 died from ~100% cost drag at ~zero gross edge with thousands of positions; this
proposal is the opposite regime (13 decisions/yr, ≥28d median holding, cost gate
before scoring) and a different signal family (liquidity level, not order-flow
absorption). It is not funding carry (funding never enters the signal), not
volume-shock continuation (no volume-spike event logic; volume enters only as the
denominator of a slow level feature), not reversal or weekly reversal (no price
mean-reversion signal at any horizon), and not a lookback/threshold variant of the two
reserved seeds (different sort key and different economic counterparty).
