# A6 Proposal 2 — V11-A6-POSITIONING-SATURATION (crypto-perpetual, monthly, low-turnover)

Producer: D1-A6 (outcome-blind lane). Frozen 2026-09-02T14:56:31Z, AFTER the logged
literature search (a6_search_log.json) and BEFORE any candidate return, PnL, PF, Sharpe
or ranking for this family was computed or read. V11 budget 0/12; no scored artifact
exists in any V11 tree. This document is a proposal only; no code, no data computation.

## 1. Primary-source citations with claim-to-test mapping

| ID | Source (identity verified in a6_search_log.json) | Exact claim used | Repo test that could reject it |
|---|---|---|---|
| P2-S1 | de Roon, F.A., Nijman, T.E., Veld, C. (2000), "Hedging Pressure Effects in Futures Markets", Journal of Finance 55(3), 1437–1456, DOI 10.1111/0022-1082.00253 | Futures risk premia depend on own-market (and cross-market) hedging pressure: premia accrue to the side that takes the other side of net hedging/speculative positioning | Monthly OI-saturation spread book net of adapter costs + native funding; causal inverted control (§7) |
| P2-S2 | Dunbar, K., Owusu-Amoako, J. (2023), "Role of hedging on crypto returns predictability: A new habit-based explanation", Finance Research Letters 55(B), art. 104009, DOI 10.1016/j.frl.2023.104009 | The hedging factor (futures positioning of hedgers vs speculators) has a statistically significant, economically important effect on crypto returns predictability (CFTC positioning version) | Same monthly spread book; spot/CFTC→perp-OI transfer must be re-earned in the repo snapshot |
| P2-S3 | Schmeling, M., Schrimpf, A., Todorov, K. (2026), "Crypto Carry", Management Science, DOI 10.1287/mnsc.2024.05069 | MARKET-STRUCTURE evidence only: crypto perps deliver leveraged exposure with little up-front capital; speculative OI is large and dynamic | Stage-A concentration gates; PIT/no-leak fixtures. Its CARRY mechanism is banned and is NOT used |
| P2-S4 | Binance USD-M market-data docs (= frozen packet source S4, verified by A1) | Open-interest snapshot endpoint semantics + completed 15m klines + funding settlement cadence used for PIT features and cost accounting | Coverage checks fail-closed (lesson L-V10P-COVERAGE); PIT/no-leak fixtures |

## 2. Economic mechanism + expected counterparty

In futures markets, risk premia compensate the side that absorbs others' positioning
pressure (Keynes–Cootner–Hirshleifer line formalised by de Roon–Nijman–Veld): when
open positions are dominated by one-directional leveraged speculators, expected
returns accrue to the opposite side, because those speculators must eventually
de-risk into thin books. Crypto perps are the purest modern laboratory: they give
leveraged directional exposure with little capital (P2-S3), so open interest IS the
positioning book. Mechanism to test: open-interest GROWTH in excess of what the
contemporaneous price move justifies marks fresh leveraged demand (crowding);
crowded coins should subsequently underperform, and deleveraged coins outperform.
Expected counterparty: over-leveraged directional speculators paying price impact
and (typically, being net long) funding when they unwind.

## 3. Required observable fields + PIT clock

- Inputs: (a) OI snapshot series per symbol from the frozen staged snapshot, used at
  their published timestamps with a declared staleness lag (decision uses the latest
  snapshot published ≥24h before the decision instant); (b) completed 15m bars → daily
  UTC closes for the coin and BTC (orthogonalisation and residualisation only).
- Features at each monthly decision T:
  - OIGRTH_i,T = 28d Δlog(OI_i) z-scored cross-sectionally;
  - orthogonalisation: cross-sectional regression at T of OIGRTH on the trailing 28d
    coin return; the sort key is the regression RESIDUAL (SAT_i,T). This uses only
    information at ≤ T (PIT-safe) and guarantees the signal is positioning, not price
    trend: the price component is explicitly removed, sign-free.
- Funding rate and traded volume NEVER enter any signal field (guards against carry
  and volume-shock contamination).
- PIT clock: decision at 00:05 UTC on the first calendar day of each 28d cycle; ONE
  declared execution lag (fills at first completed 15m bar after the decision);
  missing OI coverage fails closed, no synthesis.

## 4. Universe + benchmark role

- Universe: Binance USD-M staged snapshot; eligibility requires ≥90d completed-bar
  history and ≥60d of OI snapshot coverage at the declared cadence; tradability floor
  on median daily dollar volume; fail-closed eligibility. BTC and ETH retained.
- Benchmark role: BTC is the residualisation/market context (rolling 90d beta, frozen
  packet rule); the family benchmark is the equal-weight universe return; the claim is
  the positioning-conditioned cross-sectional SPREAD, beta-neutral by construction.

## 5. Schedule, holding period, turnover rationale

- Schedule: 13 discretionary decisions/365d (one per 28d cycle) « floor 60.
- Holding: intended holding ≈ 28d; median intended holding ≥ 3d floor with large
  margin; no-trade half-bucket band suppresses churn.
- Cost feasibility: ~13 one-way book transitions/yr on gross 1.0 (0.5/0.5) at the
  declared taker floor + slippage → base drag of order 1–2%/yr « 8% floor; stressed
  (fee ×1.5, +2 ticks) of order 2–3%/yr « 12% floor; both to be verified by the A3
  schedule-only gate BEFORE scoring.
- Symbol concentration: equal-weight buckets with per-symbol caps and the no-trade
  band; no symbol should exceed 25% of one-way turnover; verified by A3.

## 6. Target construction + risk neutralisation

- Sort eligible names by SAT_i,T (orthogonalised OI-growth residual); long the bottom
  tercile (deleveraged / uncrowded), short the top tercile (leveraged-crowded), equal
  weight, gross 1.0 split 0.5/0.5.
- Risk neutralisation: (a) BTC-beta-neutral legs via rolling 90d beta; (b) per-symbol
  weight cap; (c) return-orthogonalised sort key (no momentum tilt by construction);
  (d) minimum 6 names per leg, else the decision fails closed.

## 7. Arms: anchor, theoretically-justified neighbour, causal negative control

- Anchor: POS-OIGRTH-28D-M — long low / short high 28d return-orthogonalised OI
  growth (SAT), monthly, gross 1.0.
- Theoretically-justified neighbour: POS-OILEVEL-90D-M — long low / short high OI
  LEVEL percentile of its own 90d history (stock-of-positions saturation instead of
  flow-of-positions). Justification: in de Roon et al. the pricing variable is the
  pressure implied by outstanding positions; growth (flow) and level-vs-own-history
  (stock) are two admissible measurements of the same latent hedging-pressure state.
- Causal negative control: POS-OIGRTH-28D-M-INV — sign-INVERTED anchor (long crowded
  / short deleveraged). Mechanism-destroying: if the premium comes from absorbing
  positioning pressure, the inverted book must NOT earn a positive after-cost spread;
  if it does, the "crowding" reading is wrong (e.g. it is continuation) and the
  mechanism claim is dead.

## 8. Expected sign + falsification condition

- Expected sign: anchor net spread > 0 (low-OI-growth minus high-OI-growth,
  after adapter costs and native funding); neighbour net spread > 0; inverted
  control ≤ 0.
- Falsification: any positive after-cost spread on POS-OIGRTH-28D-M-INV, or a
  non-positive after-cost anchor spread, kills the mechanism claim. Published
  returns (P2-S1, P2-S2) are priors only; they waive nothing.

## 9. Funding / cost treatment

- Funding: charged while held via the adapter (LONG_PAYS_POSITIVE_RATE) — ~84 native
  8h settlements per 28d holding. Funding is never a signal input; the mechanism
  DISCLOSES that crowded-long coins often carry positive funding, so the short leg may
  receive funding — that is part of the counterparty's cost of crowding, but the sort
  key contains no funding field, so this is not a carry harvest.
- Costs: transition cost via the frozen adapter arithmetic, gated by the A3
  schedule-only cost floor gate before any scoring; FAIL/UNAVAILABLE verdicts stop
  the family pre-score.

## 10. Known ancestry / proximity + orthogonality argument

- V1–V10 families: only M01 is known to this lane (high-turnover aggressor-flow
  absorption, rejected, ~zero gross edge, ~100% cost loss). No shared input (M01
  consumed trade-side order-flow pressure; this family consumes the stock/flow of
  OPEN positions at monthly horizon), no shared schedule, no shared book. None of the
  banned mechanisms is an OI-positioning sort:
  - not trend/momentum: the trailing-return component is explicitly ORTHOGONALISED
    OUT of the sort key (sign-free removal), and the expected sign is
    anti-crowding, which cannot survive if the key is a trend proxy;
  - not reversal / residual mean-reversion: no price mean-reversion signal at any
    horizon; return enters only as a removed control;
  - not funding carry: funding never enters the signal and the book is not a
    funding-earning book (§9);
  - not volume-shock continuation: traded volume never enters; OI is the stock of
    open positions, not traded flow, and the expected sign is the opposite of
    continuation;
  - not the weekly reversal, and not a lookback/threshold variant of the reserved
    seeds.
- Reserved seeds (DEF-RESIDUAL-RISK, LOTTERY-MAX-SKEW): their sort keys are return
  moments (residual vol, MAX/skew); this sort key is a positioning quantity.
  Disclosed overlap risk: OI surges co-occur with high-vol, high-MAX episodes.
  Orthogonality argument: the SAT residual conditions on the return path, and the
  proposed Stage-A A7-N gate must confirm low book-weight rho against both seed
  books, plus a within-volatility-bucket spread diagnostic (diagnostic only, no new
  arm) to show the premium is not repackaged low-vol or anti-lottery.

## 11. Data readiness + implementation estimate

- Data: OI snapshot series and completed 15m bars are in the frozen staged snapshot;
  no new external data. OPEN READINESS RISK (disclosed): the depth/cadence of the
  staged OI history over the full scored window must be validated with coverage
  diagnostics ONLY (fail-closed per lesson L-V10P-COVERAGE) before any implementation;
  if OI coverage is too shallow for 28d/90d features, the family fails closed rather
  than being re-cut post-hoc.
- Implementation: plugin on GenericStrategyBase (schedule/folds/cost/funding accrual
  reused); new code = OI snapshot loader, Δlog-OI feature, cross-sectional
  orthogonalisation, bucket book builder. Estimate 2–3 working days including the
  coverage validation + A3 gate run.

## 12. Why this is not a rescue of a previously rejected family

M01's failure mode was cost-dominated high-frequency order-flow absorption; this
family shares no input, horizon or schedule with it and sits far inside every frozen
cost floor. It is not a funding-carry rescue (no funding signal, no carry harvest —
§9), not a crowding RESCUE of any rejected book (the sorted quantity — open interest
— belongs to no prior repo family known to this lane, and the "crowding" here is the
mechanism itself, priced via the de Roon et al. channel, not a patch for a dead
signal), not volume-shock continuation, not reversal at any horizon, and not a
re-cut lookback/threshold of the two reserved seed families (different sort key,
different data type, different economic counterparty).
