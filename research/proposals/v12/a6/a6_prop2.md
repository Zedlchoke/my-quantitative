# A6 Proposal 2 — RVX: Cointegration Error-Correction Relative Value (threshold pairs)

- `proposal_id`: A6-P2-RVX · `hypothesis_id`: H-A6-RVX · lane `a6`
- Companion machine-readable file: `a6_prop2.json`
- Outcome-blind attestation: this lane computed no returns, PnL, PF, Sharpe, ranking or backtest. Everything below is a construction rule, a PIT definition or a worst-case schedule bound in weight-units.

## 1. Mechanism (one paragraph)

Pre-registered pairs of crypto sector substitutes (two L1 platforms, two meme names, two payments assets, …) share a stationary long-run log-price relation when they are cointegrated [Engle & Granger 1987, Econometrica 55(2)]. One-sided attention or news flow regularly dislocates one leg while its substitute does not move; a relative-value rule that trades divergence of the estimated spread beyond a threshold and exits on convergence harvests the error-correction term, and historically such rules earned spreads robust to conservative execution [Gatev, Goetzmann & Rouwenhorst 2006, RFS 19(3)], including in crypto when gated by Engle-Granger-type tests and sized by OU dynamics [Tadi & Kortchmeski 2021, arXiv:2109.10662; Avellaneda & Lee 2010, QF 10(7)]. Expected sign: **long the cheap leg, short the rich leg; earn convergence**. The frozen weekly clock deliberately leaves the fast convergence margin to faster players and harvests only the slow reversion component — this is what makes the family low-turnover.

## 2. Primary-source claim and transfer caveats

Claim (primary sources with DOI/stable URLs, verified 2026-09-03, lane log W8–W12): cointegration implies an error-correction representation; threshold divergence/convergence rules work out-of-sample; OU half-life informs the lookback; realistic execution matters.

Crypto-perpetual transfer caveats (each bound to a design choice):

1. **Crypto cointegration is less persistent than equity cointegration.** Mitigations: pairs pre-registered on prior sector-substitute grounds (no pair mining), activation gate (trailing 56d EG residual ADF, 10% level, hedge ratio in [0.25, 4]) re-run every stamp, relation re-estimated every stamp, 8-week max holding.
2. **Funding on both legs can rival the convergence payoff** (mixed 8h/4h/1h native cadences). Funding is charged natively in every cell and never enters the signal — the family makes no funding-selection claim.
3. **Convergence fails in crash regimes** (correlations jump to 1; a leg can collapse idiosyncratically). Partial mitigations: dollar+beta-neutral legs capped at 0.25, hedge-ratio sanity bound, 8w max holding. The residual tail risk is declared, not engineered away; no intraweek stop is possible under the frozen weekly clock.
4. **Weekly stamps accept stamp-gap exposure** — that is the packet's clock; position size is bounded by construction instead.

## 3. Economic counterparty and expected sign

Counterparty: flow-imbalanced traders — attention/news hitting one substitute leg while the others stand still; the RV desk fading the dislocation is compensated at convergence, the flow trader pays for immediacy and single-name exposure. Expected sign: spread z-scores entered at |z| ≥ 2 revert toward the estimated equilibrium.

## 4. PIT fields and availability clock

- Fields: daily log prices built from completed 15m bars (last close per UTC day) strictly before the stamp; trailing 56d EG regression (hedge ratio + residual ADF); rolling 90d daily BTC betas. Open interest and funding are never signal inputs.
- PIT rule: completed bars only, no partial tails, no synthesized gaps (frozen loader semantics); estimates strictly pre-stamp.
- Availability clock: a pair is activatable at Monday 00:00:00Z stamp T iff both legs have complete daily closes on (T−56d, T] and the trailing EG test passes at 10% with |hedge ratio| in [0.25, 4]; otherwise dormant for that stamp.
- Execution lag (declared): fills at the first strictly-later completed 15m event (FILLED_NEXT_EVENT); baseline 0, stress +1 event — the execution-realism point of S7 is exactly why the lag is frozen.

## 5. Universe, formation, holding, rebalance

- Universe: 19 tradeable names (BTC context-only, never held). Pre-registered candidate pairs, same-sector substitutes, formed on prior grounds: (ETH,SOL), (SOL,SUI), (AVAX,NEAR), (ADA,AVAX), (AAVE,LINK), (DOGE,1000PEPE), (1000PEPE,BOME), (XRP,BCH) — all `*USDT` perps. ≥9 eligible names required per stamp, else fail-closed.
- Formation: 56d trailing daily closes (anchor); max(28d, 2× OU half-life) (neighbour).
- Holding: state-dependent — entry at a stamp when |z| ≥ 2.0; exit at the first later stamp with |z| ≤ 0.5, or at 8 weeks (max); one state change per pair per 2 consecutive stamps (cooldown).
- Rebalance: every Monday 00:00:00Z → **52 discretionary decisions/365d ≤ 60 floor**.

## 6. Target book, neutralisation, expected turnover

- Shape: threshold pairs book, up to 3 concurrently active pairs; each symbol in at most one active pair (no stacking).
- Cap by construction: legs at most ±0.25 (lone active pair: ±0.20) → every |weight| ≤ 0.25 ≤ 0.30 at every stamp, independent of outcomes.
- Beta neutralisation: per pair, legs sized so the beta-weighted net exposure is zero (90d PIT BTC betas); portfolio BTC beta ≈ 0 by construction; BTC never held.
- Expected turnover (schedule bounds, not outcomes): cooldown + concurrency caps bound worst case at ≤ 78 one-way weight-units/yr; each leg move is a fixed unit (0.25/0.20) and the lone-pair rule holds any single symbol's turnover share ≤ 20% ≤ 25% floor by construction; base drag bound stays under the 8%/yr floor at declared tier-0 floors, stressed under 12%. Median intended holding ≥ 7d ≥ 3d floor by construction (all completed spans are whole weeks). Gate verification is the schedule-only A3 gate's job; a FAIL defers the family, never renegotiates a floor.

## 7. Anchor, neighbour, causal negative control (3 scored cells)

| Cell | ID | Definition | Scored |
|---|---|---|---|
| Anchor | RVX-ANCHOR-FIXED56 | 56d formation; \|z\| ≥ 2.0 in, \|z\| ≤ 0.5 out or 8w max; cooldown; ≤3 pairs | yes |
| Neighbour | RVX-NEIGHBOUR-OUHALF | same rule; formation = max(28d, 2× OU half-life) per stamp | yes |
| Control | RVX-RANDOMPAIR-CONTROL | fixed-seed (20260903) per-stamp random pair→symbol permutation, everything else identical (mechanism-destroying) | yes |

Neighbour justification: the OU calibration literature [Avellaneda-Lee 2010] and its crypto application [Tadi-Kortchmeski 2021] both tie the sampling window to the estimated half-life — the neighbour samples the SAME mechanism at its theory-matched horizon, rather than at an arbitrary fixed window. Not a separate family.

Non-scored diagnostic (declared, consumes no cell): sign-flipped "fade the wrong way" arm.

## 8. Fees, slippage, funding, stress

Adapter-declared floors only (tier-0 taker + 1 adverse tick), arithmetic reused verbatim from `GenericStrategyBase.rebalance_cost_between`; funding native on both legs (`LONG_PAYS_POSITIVE_RATE`) inside holding spans, mixed cadences consumed natively per official Binance `fundingTime` documentation; frozen stress surface fee ×1.5 / +2 ticks / +1 event delay; full six-cell surface supported.

## 9. Falsification condition

Falsified if: (a) the randomized-pairing control matches the anchor under the scored protocol; (b) post-entry convergence is indistinguishable from pre-entry drift under a preregistered block-bootstrap sign test; (c) fewer than 2 of the 8 pairs are ever activatable; (d) signal availability < 0.95 of served stamps; (e) any frozen feasibility floor FAILs or is UNAVAILABLE. Scoring is the pipeline's job; this lane computes no outcomes.

## 10. Ancestry map vs V1–V11 (mechanism-level; forbidden inventory only)

| Forbidden class | Relationship |
|---|---|
| WEEKLY-REVERSAL / MR-RESCUE | **declared adjacency, argued distinct**: rejected class = single-name reversal on own past returns; this family = two-name cointegration residual (no own-return term), state-dependent holding, and a mechanism-destroying control (pair randomization) that preserves any single-name reversal exposure while destroying the RV structure — the mechanisms are separable by construction. Flagged for A7-N adjudication; NO fallback parameterization offered |
| V4 XSECT-MOM | none — no trend or past-return statistic |
| V6/V1 CARRY-FUNDING | none — funding is a held cost only, never signal/sizing |
| V11 LOTTERY-MAX-SKEW | none — no return-shape statistic |
| V11 ILLIQ-AMIHUD (reserved) | none — no volume or impact statistic |
| V11 OILEVER-DELEV (reserved) | none — OI never read; no cap raise or renormalization sought |
| V10-M01 AGGRESSOR-ABSORPTION | none — no signed flow input |
| V1 VOLCOMP / volume-shock | none |
| DATA-GATED | clean — staged native fields only |

## 11. Why this is not a rescue

No lottery/return-shape statistic, no Amihud-type ratio, and open interest is never touched; no cap raise or post-score renormalization is sought. The family's only adjacency — mean reversion — lives at the two-name spread level with an estimated error-correction relation, a mechanism class not present in the forbidden inventory as such, and it ships with the one control (pair randomization) that specifically separates it from any renamed single-name reversal. If A7-N adjudicates it inside MR-RESCUE, the family dies; no rescue is offered.

## 12. Budget and isolation

3 scored cells (anchor + neighbour + control) of the per-family 3; 6 of 9 sprint cells across both A6 families. Built solely from the blind packet, allowed interface files, the forbidden inventory and public primary literature.
