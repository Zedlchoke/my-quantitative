# A8 Proposal 1 — V11-ILLIQ-AMIHUD: cross-sectional illiquidity (Amihud) premium on crypto perpetuals

Producer: D1-A8 (outcome-blind). Generated 2026-09-02T15:10:00Z.
Bootstrap SHA 0684914b7bf64a5b9b8eeaa82529a2d11a8a251d. Branch orca/v11d-a8-proposals.
Outcome-blindness: no V11 candidate returns, PnL, PF, Sharpe or ranking were read or computed
by this lane in any V11 tree; all figures below are schedule-level (floors, cadences, counts).

## 0. Family identity

- family_id: `A8-V11-ILLIQ-AMIHUD`
- One-line hypothesis: coins with HIGHER trailing price impact per unit of traded
  dollar volume (Amihud illiquidity) earn HIGHER subsequent cross-sectional returns on
  Binance USD-M perpetuals, held weekly-or-slower, after adapter taker costs, slippage
  and native funding.

## 1. Primary-source citations with claim-to-test mapping

| id | source (identity verified) | exact claim used | repo test that could reject it |
|---|---|---|---|
| P1 | Ali, Asgar; Peng, Sanshao; Shams, Syed (2025). "Unravelling cross-sectional patterns in cryptocurrencies: a four-factor asset pricing model." China Accounting and Finance Review (Emerald / HK PolyU) 27(4):493; SSRN preprint 5527518, DOI 10.2139/ssrn.5527518. | A SIGNIFICANT ILLIQUIDITY PREMIUM exists in the cryptocurrency cross-section, measured with the Amihud (2002) ratio (absolute daily return divided by daily dollar volume). The same paper reports size and reversal effects — NEITHER is used here; only the illiquidity characteristic is the mechanism. | Causal negative control sign test; Stage-A after-cost expectancy/PF gates; fold-dispersion gates; A7-N orthogonality rho. |
| P2 | Amihud, Yakov (2002). "Illiquidity and stock returns: cross-section and time-series effects." Journal of Financial Markets 5(1):31-56. | Definition of the ILLIQ measure: mean of |return|/dollar-volume as a price-impact-per-unit-volume proxy. | Measure-construction fixtures (PIT, completed bars); schedule-only cost gate. |
| P3 | Amihud, Yakov; Hameed, Allaudeen; Kang, Wenjin; Zhang, Huiming (2015). "The Illiquidity Premium: International Evidence." Journal of Financial Economics (S0304405X15000483). | The illiquidity premium generalises across 45 equity markets: illiquid assets earn higher average returns as compensation for providing liquidity. | Mechanism-level falsification: if the perp-transfer sign is negative (illiquid coins UNDERPERFORM net of costs), the transfer claim is rejected. |
| P4 | Wei, Wang Chun (2018). "Liquidity and market efficiency in cryptocurrencies." Economics Letters (S0165176518301320). | The Amihud measure is robust and applicable to cryptocurrencies specifically. | Feature-validity fixtures; Amihud computed from staged snapshot bars must reproduce plausible cross-sectional dispersion (fail-closed otherwise). |

Identity-verification trail (every query, retrieval UTC, verdict): see
`research/proposals/v11/a8_search_log.json` (Q1, Q6-Q9, Q13-Q15). Note on the correction
trail: Borri & Shakhnov (2022, RAPS 12(3):667-705, DOI 10.1093/rapstu/raac007) was
initially surfaced by search summaries as an illiquidity-pricing result; direct RePEc
retrieval shows its actual claim concerns cross-exchange price gaps. It is therefore
REJECTED as mechanism evidence and is NOT cited as support; logged in Q6/Q7.

Published returns are PRIORS (packet rule 1): they never waive novelty, orthogonality,
data, cost, stress, negative-control or A7 gates.

## 2. Economic mechanism + expected counterparty

Mechanism: coins with high price impact per dollar of trading volume impose inventory
and immediacy risk on anyone who demands liquidity. Following the standard
liquidity-provision compensation logic (P3), investors who PROVIDE liquidity in the
illiquid tail — i.e. take and hold positions in high-Amihud coins when others will not —
must be compensated with higher expected returns. The counterparty is (a) flow that must
trade illiquid coins regardless of price (index-like rebalancing, listing-driven retail
arrivals) and (b) the convenience/attention crowd that clusters in liquid majors,
leaving the illiquid tail structurally under-owned. On perpetuals the same compensation
must be re-earned through the perp wrapper: funding charged while held, native shorting
of the liquid leg, and basis behaviour.

## 3. Required observable fields + PIT clock

Required fields (all already staged in the frozen Binance USD-M snapshot; no new
external data):

- completed 15m base bars per symbol: close, and per-bar quote/dollar volume
  (klines fields; S4 venue docs define semantics);
- nothing else. Funding settlements are consumed ONLY by the adapter's cost
  accounting, never by the signal. OI and mark price are NOT used by this family.

PIT clock:

- features from COMPLETED 15m bars only; aggregate to daily UTC closes (daily return
  and daily dollar volume);
- `AMIHUD_28D_i,t` = mean over trailing 28 completed UTC days of
  daily_|r_i| / daily_dollar_volume_i (rank-transformed cross-sectionally, scale
  invariant; log-1p first to tame outliers);
- freeze: day-d close at 00:00 UTC of day d+1 completes the last bar used; one declared
  execution lag of 24h — the signal enters the next scheduled weekly decision instant
  with feature availability at least 24h old (no intrabar or partial-bar input, no
  lookahead);
- listing/survivorship handled by the staged snapshot as-is (PIT listing dates from
  first completed bar; delisted symbols keep their history; no tail synthesis — the
  Q-phase coverage rule fails closed).

## 4. Universe + benchmark role

- Universe: all Binance USD-M perpetual symbols in the staged snapshot with sufficient
  completed-bar coverage for a 28d trailing window (fail-closed coverage gate, no
  substitution); BTC excluded from the book (reserved as benchmark and residualisation
  input); a minimum traded-liquidity LISTING floor (bottom decile of median daily
  dollar volume excluded) is applied for implementability only — the floor is set so
  the illiquid half of the remaining universe is still tradeable; the floor's
  percentile is declared before scoring and never tuned after any scored result.
- Benchmark role: flat benchmark, and BTC-perp buy-and-hold as the context benchmark.
  The family's book is benchmark-neutral in construction (see §6), so the context
  benchmark measures beta share, not the claim.

## 5. Schedule, holding period, turnover rationale

- Decision instants: weekly, Monday 00:00 UTC. 52 discretionary decisions per 365d
  against the frozen floor of 60. Forced-flat/terminal actions counted separately by
  the A3 gate.
- Holding period: 7 calendar days between rebalances; median intended holding = 7d
  (>= 3d floor). Bucket membership under a 28d trailing window is persistent, so most
  positions simply roll within the same bucket, keeping one-way turnover and the
  per-symbol share low.
- Turnover rationale vs the M01 lesson (L-V10-TURNOVER): M01 died at 6,916
  positions/fold with ~100% cost burn. This family makes ~52 decisions/yr, two bucket
  legs, and re-ranks a slow (28d) characteristic; the only economically relevant design
  question is drag, which the frozen A3 gate measures on schedule artifacts BEFORE any
  scoring.
- No symbol > 25% of turnover: the book is a quintile-bucket pair (not a single-coin
  book); with tens of symbols per leg the largest expected single-symbol share is far
  below the floor; verified, not assumed, by A3's per-symbol turnover share metric.

## 6. Target construction + risk neutralisation

- Book: long the top-Amihud (most illiquid) quintile equally weighted, short the
  bottom-Amihud (most liquid) quintile equally weighted (dollar-neutral pair of
  buckets).
- Beta neutralisation: rolling 90d daily beta vs BTC (the same frozen beta rule the
  packet seeds use); leg weights scaled so the combined book's BTC beta is ~0 —
  beta-aware construction, BTC-residualised exposure by design.
- Orthogonalisation diagnostic (declared BEFORE scoring): within each 28d rebalance,
  re-rank Amihud within three dollar-volume-size terciles (size proxy = trailing 30d
  median daily dollar volume) and report the anchor spread from the
  size-orthogonalised ranking alongside the raw ranking. If the raw anchor spread dies
  entirely once size-orthogonalised, the "illiquidity compensation" claim is
  size-relabelled and the mechanism claim is rejected. This is a diagnostic, not a
  post-hoc filter; both rankings are declared now.

## 7. Arms

- anchor: `ILLIQ-AMIHUD-28D-W` — long most-illiquid quintile minus short most-liquid
  quintile; 28d formation; weekly hold.
- theoretically-justified neighbour: `ILLIQ-AMIHUD-56D-W` — same book with a 56d
  formation window. Justification: P3's premium is a compensation for a persistent
  structural characteristic, so the anchor's claim predicts the sign survives a slower
  formation; a sign flip or collapse under 56d would indicate the anchor rode a
  28d-specific transient rather than the compensation mechanism.
- causal negative control (sign-destroying): `ILLIQ-AMIHUD-28D-W-INV` — sign-inverted
  anchor (long MOST-LIQUID minus short MOST-ILLIQUID), same schedule, same
  neutralisation. If the inverted book earns a positive after-cost spread, the
  mechanism claim is dead (it would mean the market pays FOR liquidity rather than
  paying the liquidity provider, i.e. the anchor's positive result could not be
  liquidity compensation).

## 8. Expected sign + falsification condition

- Expected sign: anchor net spread > 0 (illiquid quintile outperforms liquid quintile
  after costs and funding); inverted control <= 0.
- Falsification conditions (any one kills the family):
  1. inverted control positive after costs;
  2. anchor sign negative on the scored window (perp transfer fails — illiquid coins
     underperform once shorting/costs are native);
  3. anchor positive raw but ~0 after size-orthogonalisation (§6), i.e. the result is a
     size effect wearing illiquidity clothing;
  4. A3 floors fail (cost drag > 8%/yr base or > 12%/yr stressed, or holding/decision
     floors violated) — schedule-infeasible by construction;
  5. fold concentration gates fail (a single fold or symbol dominates).

## 9. Funding / cost treatment

- Costs: adapter taker fees + declared adverse-tick slippage floor, applied per side on
  every transition via `GenericStrategyBase.rebalance_cost_between` (reused verbatim by
  the A3 gate); stressed cell = fee x1.5 + 2 extra ticks. No cost math is re-implemented.
- Funding: native 8h settlements accrue over held spans via the adapter's
  `checked_funding_accrual`; funding is a COST LINE ONLY and never a feature. Economic
  note declared in advance: the short leg sits in liquid majors, which typically carry
  positive funding (shorts receive) — a potential tailwind; the long leg's funding sign
  varies. Funding drag must be carried by the mechanism, not waived.
- Known cost risk, disclosed: the long leg trades the illiquid tail where the frozen
  generic tick-slippage floor most likely UNDERSTATES true impact. The stressed cell
  (x1.5 fees, +2 ticks) is the pre-score safety margin; if A3 stressed drag fails, the
  family dies at the gate, before any scored return exists.

## 10. Ancestry / proximity + orthogonality argument

- V1-V10 rejected/forbidden inventory: weekly_reversal_V8, funding_carry_V6,
  funding_crowding_MR, volatility-compression breakout variant,
  funding_price_divergence_V7, aggressor-flow absorption (A8-V10-M01), trend/momentum,
  residual mean-reversion, volume-shock continuation. None of these used a
  price-impact/liquidity characteristic; this family uses none of their observables
  (no past returns, no funding, no flow, no breakout geometry).
- Reserved seeds: V11-SEED-DEFENSIVE-RESIDUAL-RISK (low BTC-residual vol/downside risk)
  and V11-SEED-LOTTERY-MAX-SKEW (residual MAX/skew). Neither seed uses volume or
  price-impact; both are return-SHAPE/RISK books, this is a microstructure-compensation
  book. Expected book correlation sign vs the defensive seed is NEGATIVE (the illiquid
  tail is typically high-residual-vol, so this book is long what the defensive seed
  shorts) — anti-correlated, hence not a close variant; no MAX/skew input exists here.
  A7-N will compute the actual orthogonality rho vs rejected ancestors; proposal-level
  expectation: |rho| modest and the overlap sign negative vs seed 1.
- Volume usage disclaimer vs the forbidden volume-shock-continuation family: that
  family traded volume SHOCKS for CONTINUATION. Here dollar volume is only a deflator
  inside a slow 28d impact LEVEL, at 1/500th of the decision frequency, with the
  opposite (compensation, not continuation) mechanism.

## 11. Data readiness + implementation estimate

- Readiness: 15m completed bars with quote volume for USD-M symbols are in the frozen
  staged snapshot (S4 semantics); no new external data; no OI/mark dependency (keeps
  the family independent of the OI data-quality caveat).
- Estimate: feature builder (daily aggregates + 28/56d Amihud + size-orthogonalised
  ranking) ~1 day; schedule-artifact emission for A3 (instants, target books, fill
  price inputs, availability flags) ~1 day; beta-neutral weighting ~0.5 day. No new
  adapter or gate code required (A3 consumes schedule artifacts as-is). Estimate only;
  no code written by this lane.

## 12. Why this is not a rescue of a previously rejected family

The rejected families failed for (i) zero gross edge burned by turnover (M01) or (ii)
mechanisms outside this lane's scope (reversal, carry, crowding rescue, breakout,
momentum). This proposal changes the observable class (price impact per dollar volume),
the cadence (52 decisions/yr vs 6,916 positions/fold), and the mechanism (compensation
for liquidity provision vs flow absorption or continuation). No rejected family becomes
a special case of this one, and no threshold of a rejected family is re-tuned: the
28d/56d windows are new construction choices for a new characteristic, declared before
scoring, with frozen floors unchanged.
