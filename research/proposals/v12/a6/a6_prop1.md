# A6 Proposal 1 — OSCOMP: Order-Size Composition (ticket-fragmentation) book

- `proposal_id`: A6-P1-OSCOMP · `hypothesis_id`: H-A6-OSCOMP · lane `a6`
- Companion machine-readable file: `a6_prop1.json`
- Outcome-blind attestation: this lane computed no returns, PnL, PF, Sharpe, ranking or backtest. Everything below is a construction rule, a PIT definition or a worst-case schedule bound in weight-units.

## 1. Mechanism (one paragraph)

Crypto perpetual flow is dominated by two structurally different ticket populations: small notional tickets (attention-driven retail participants, 24/7 access, app-based, leveraged) and large notional tickets (institutional execution, sliced parent orders). The equity retail-flow literature establishes that (i) trade size is the standard retail-flow classifier and aggressive retail orders create temporary price pressure that subsequently reverses [Kelley & Tetlock 2013, JF 68(3)], and (ii) periods of intense attention-induced retail buying are followed by negative abnormal returns over the following days-to-weeks [Barber, Huang, Odean & Schwarz 2022, JF 77(6)]. Retail vs institutional attention also carry distinct, separable return effects in crypto specifically [Ozdamar et al. 2022, JIFMIM 81]. The mechanism: names whose recent flow is retail-fragmented carry an attention premium that decays; names whose recent flow is institution-weighted do not. Expected cross-sectional sign over the following ~4 weeks: **long high-average-notional-per-trade names, short low-average-notional-per-trade names** — dollar-neutral and BTC-beta-neutral, with BTC never held.

## 2. Primary-source claim and transfer caveats

Claim (primary sources with DOI/stable URLs, verified 2026-09-03, see lane log W2–W7): attention-induced retail buying predicts negative subsequent abnormal returns; small trade size identifies retail flow; aggressive retail pressure is temporary.

Crypto-perpetual transfer caveats (each one bound to a design choice):

1. **Attention co-moves positively with contemporaneous crypto returns** [Smales 2021, SSRN 3889923]. The equity claim is lagged and cross-sectional; transferring it to lagged crypto returns is precisely what the falsification condition tests. No contemporaneous co-movement is assumed.
2. **Ticket size is a noisy composition proxy on a futures venue** (algo slicing, fee-tier clustering). Mitigation: only cross-sectional ranks of average notional per trade are used — never raw dollar levels, never signed flow.
3. **Reported trade counts can be inflated on unregulated venues** [Cong, Li, Tang & Yang 2023, Mgmt Sci 69(11)]. Mitigation: single-venue statistics from native Binance USD-M kline fields only ("Number of trades" and quote asset volume are documented native kline payloads; official Binance API docs), no purchased or cross-exchange data.
4. **Funding accrues while held** on both sides at native mixed 8h/4h/1h cadences. It is charged as a cost and never enters the signal or sizing — the family makes no funding claim.

## 3. Economic counterparty and expected sign

Counterparty: attention-driven small-ticket buyers into salient moves; the absorbing side is liquidity providers and slower institutional flow, compensated as the attention premium decays. Expected sign: bottom-quintile (retail-fragmented) names underperform top-quintile (institution-weighted) names over the holding horizon; the book monetizes the differential long/short.

## 4. PIT fields and availability clock

- Fields: completed 15m bars only — `quote_volume`, trade count (formation), daily closes derived from completed bars (90d beta). Open interest is deliberately never read.
- PIT rule: features from bars with close time strictly before the stamp (frozen loader's completed-bar / no-partial-tail semantics); funding settlements applied only inside holding spans.
- Availability clock: signal available at Monday 00:00:00Z stamp T iff every 15m slot in (T−28d, T] is a completed bar for a candidate and 90d of daily closes exists; partial coverage serves only fully-covered names, subject to the ≥9-name rule.
- Execution lag (declared): fill at the first strictly-later completed 15m event after the stamp (adapter `FILLED_NEXT_EVENT`); baseline delay 0, stress +1 event.

## 5. Universe, formation, holding, rebalance

- Universe: 19 tradeable names (REQUIRED_SYMBOLS minus BTCUSDT, context-only); eligible at T iff formation window fully covered; ≥9 eligible names required to form, else fail-closed carry/flat.
- Formation: trailing 28d of completed 15m bars ending strictly before the stamp.
- Holding: until the next formation stamp (28d minimum by construction; persisting legs roll over without trades).
- Rebalance: every 4th Monday 00:00:00Z → **13 discretionary decisions/365d ≤ 60 floor**.

## 6. Target book, neutralisation, expected turnover

- Shape: long/short quintile book — top 4 names long, bottom 4 short, lexicographic tie-break.
- Cap by construction: per-leg weight = side-gross/4 with side-gross ≤ 1.0 → every |weight| ≤ 0.25 ≤ 0.30 at every stamp, independent of outcomes.
- Beta neutralisation: 90d PIT BTC betas; the side-gross split within [1.0, 2.0] is chosen so β-weighted long exposure equals β-weighted short exposure (portfolio BTC beta ≈ 0) **without holding BTC**; infeasible splits halve the book (legs 0.125) — cap still holds.
- Expected turnover (schedule bounds, not outcomes): worst case 4.0 weight-units per formation → ≤ 52 units/yr; single symbol can contribute at most 0.5 units per stamp → ≤ 12.5% ≤ 25% symbol-share floor by construction; base drag bound = 52 units × (declared taker rate + 1 tick) — comfortably under the 8%/yr floor at tier-0 floors; stressed (×1.5 fee, +3 ticks total) under the 12% floor. Exact verification belongs to the schedule-only feasibility gate on the realized schedule; a gate FAIL triggers family deferral, never floor renegotiation.
- Median intended holding = 28d ≥ 3d floor by construction.

## 7. Anchor, neighbour, causal negative control (3 scored cells)

| Cell | ID | Definition | Scored |
|---|---|---|---|
| Anchor | OSCOMP-ANCHOR-LEVEL | rank on trailing-28d average notional per trade; long top quintile, short bottom | yes |
| Neighbour | OSCOMP-NEIGHBOUR-DLEVEL | same book, ranked on the 28d **change** in average ticket size (long rising-ticket, short falling-ticket) | yes |
| Control | OSCOMP-SIGNFLIP-CONTROL | anchor with book sign flipped (sign-destroying) | yes |

Neighbour justification: attention buying is episodic [Barber et al. 2022]; an episode manifests as ticket-size compression before the level statistic moves — the first difference of the same composition variable is the theoretically matched event detector. Same mechanism family, different moment; not a separate family.

Non-scored diagnostic (declared, consumes no cell): fixed-seed (20260903) symbol→rank permutation placebo — mechanism-destroying, preserves book shape/gross/turnover.

## 8. Fees, slippage, funding, stress

Adapter-declared floors only (tier-0 taker per side + 1 adverse tick), arithmetic reused verbatim from `GenericStrategyBase.rebalance_cost_between`; funding native (`LONG_PAYS_POSITIVE_RATE`) inside holding spans only; frozen stress surface fee ×1.5 / +2 ticks / +1 event delay, full six-cell surface supported.

## 9. Falsification condition

Falsified if: (a) the anchor fails to separate from the sign-flipped control in the preregistered direction under the scored protocol; (b) neighbour and anchor contradict in sign with comparable magnitude; (c) signal availability < 0.95 of served stamps; (d) any frozen feasibility floor FAILs or is UNAVAILABLE. Scoring is the pipeline's job; this lane computes no outcomes.

## 10. Ancestry map vs V1–V11 (mechanism-level; forbidden inventory only)

| Forbidden class | Relationship |
|---|---|
| V10-M01 AGGRESSOR-ABSORPTION | none — signal is sign-agnostic; no signed flow or imbalance statistic |
| V11 LOTTERY-MAX-SKEW | none — no MAX/skew/return-shape statistic; zero return inputs |
| V11 ILLIQ-AMIHUD (reserved) | adjacency checked, no lineage — `dollar_volume / trade_count` (ticket size, a retail-flow classifier) vs Amihud `|return| / dollar_volume` (price impact); no shared functional form; expectation is attention decay, not an illiquidity premium |
| V11 OILEVER-DELEV (reserved) | none — open interest never read |
| V4 XSECT-MOM | none — no past-return term |
| V6/V1 CARRY-FUNDING | none — funding is a held cost only |
| V1 VOLCOMP / volume-shock | none — neighbour is a composition change, not a volume shock; no continuation claim |
| WEEKLY-REVERSAL / MR-RESCUE | none — no own-past-return signal at any horizon |
| DATA-GATED | clean — staged native fields only |

## 11. Why this is not a rescue

The statistic `sum(quote_volume)/sum(trade_count)` lives in a parameter space disjoint from LOT/MAX/skew (return shapes), Amihud (|return|-conditioned volume) and open interest entirely. No sign flip, lookback retune, cap change, fee reduction, winning-symbol selection or renaming of any forbidden family reproduces this signal; the family's own preregistered sign-flip control tests its specific claimed direction. The economic expectation comes from the retail-flow/attention literature (S1–S3), not from liquidity-premium or lottery-demand mechanisms.

## 12. Budget and isolation

3 scored cells (anchor + neighbour + control) of the per-family 3; 6 of 9 sprint cells across both A6 families. Built solely from the blind packet, allowed interface files, the forbidden inventory and public primary literature.
