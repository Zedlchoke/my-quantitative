# A8 Proposal 2 — V11-OILEVER-DELEV: open-interest leverage build-up underperformance on crypto perpetuals

Producer: D1-A8 (outcome-blind). Generated 2026-09-02T15:20:00Z.
Bootstrap SHA 0684914b7bf64a5b9b8eeaa82529a2d11a8a251d. Branch orca/v11d-a8-proposals.
Outcome-blindness: no V11 candidate returns, PnL, PF, Sharpe or ranking were read or
computed by this lane in any V11 tree; all figures below are schedule-level.

## 0. Family identity

- family_id: `A8-V11-OILEVER-DELEV`
- One-line hypothesis: coins whose open interest (per unit of traded dollar volume)
  GREW fastest over the trailing month subsequently UNDERPERFORM coins with flat or
  shrinking open interest, on a beta-aware weekly perpetual book, after adapter costs
  and native funding — a deleveraging/liquidation-friction premium shorting the most
  newly-leveraged books.

## 1. Primary-source citations with claim-to-test mapping

Honest disclosure first: NO peer-reviewed paper directly prices the CROSS-SECTION of
open-interest growth in crypto. The claim transferred here rests on a verified
mechanism-friction chain plus one time-series predictability prior; this is a novel
transfer with a higher external-validity risk than a direct-pricing transfer, declared
per packet rule 1. Every source below is a primary source with verified identity.

| id | source (identity verified) | exact claim used | repo test that could reject it |
|---|---|---|---|
| P5 | Cheng, Zhiyong; Deng, Jun; Wang, Tianyi; Yu, Mei (2021). "Liquidation, Leverage and Optimal Margin in Bitcoin Futures Markets." arXiv:2102.04591. | Daily forced liquidations are SIZABLE relative to outstanding perpetual futures (3.51% long, 1.89% short of OI per day on BitMEX perps), and liquidated investors trade at extreme leverage (~60x average). | If forced-deleveraging risk were not materially OI-linked, high-OI-growth coins would show no subsequent underperformance; the causal negative control tests the sign directly. |
| P6 | Seuma, Ramon Marc Garcia (2026). "Where does the criticality live? Early-warning signals are event-heterogeneous across seven crypto-perpetual liquidation cascades." arXiv:2607.27070. | Seven major BTC-perp liquidation cascades (2022-2025, incl. the 2025-10-10 $19B event) are preceded by leverage/price buildup signatures in 5 of 7 events; the 2 misses are exogenous news shocks; endogenous-buildup and exogenous-shock cascade types are DISTINCT. | Mechanism evidence that deleveraging cascades follow positioning build-ups, PLUS a declared fragility caveat: the mechanism only claims the endogenous-buildup channel; exogenous-shock losses are part of the honest null. |
| P7 | Palazzi, Rafael; Gerson Junior; Klotzle, Marcelo Cabus (2026). "From Network Fundamentals to Macro-Financial Integration: The Evolving Predictability of Bitcoin Returns." SSRN 6199098 (also listed 6725492/6179378; USP / PUC-Rio). | Crypto-native POSITIONING variables — explicitly including OPEN INTEREST (alongside funding and MVRV) — predict Bitcoin returns across regimes (time-series prior). | Time-series prior only; the cross-sectional transfer must re-earn the claim; A7-N orthogonality and Stage-A gates can reject the transfer. |
| P8 | He, Songrun; Manela, Asaf; Ross, Omri; von Wachter, Victor (2022-2024). "Fundamentals of Perpetual Futures." arXiv:2212.06888 (v6). | Perpetuals are the dominant leveraged exposure vehicle in crypto (leveraged exposure without rollover), with funding as the anchoring payment — i.e. OI on a perp is a direct measure of leveraged positioning. | Background mechanics; no separate test. |
| P9 | Giagkiozis, Ioannis; Said, Emilio (2023/2024). "Reconciling Open Interest with Traded Volume in Perpetual Swaps." arXiv:2310.14973; Ledger 9:1-15. | OI in BTC perpetual swaps is SYSTEMATICALLY MISQUOTED by some of the largest exchanges (implausible figures; delayed liquidation messages). | Mandatory data-quality constraint (see §3, §11): the family FAILS CLOSED on implausible or missing OI coverage rather than trading through it. |

Identity-verification trail: `research/proposals/v11/a8_search_log.json` (Q2, Q3, Q4,
Q9-Q12).

## 2. Economic mechanism + expected counterparty

Mechanism: open interest on a perp is outstanding leveraged positioning (P8). When a
coin's OI per unit of traded volume builds rapidly, marginal buyers are adding LEVERAGE,
not cash: their positions are exposed to automatic liquidation at bounded adverse moves
(P5: liquidated traders run ~60x; daily forced liquidations are percent-level fractions
of OI). An over-levered long book both (i) transiently overprices the coin relative to
unlevered demand, and (ii) raises the probability that the next adverse move is
mechanically amplified into forced selling — a deleveraging cascade whose
endogenous-buildup type is empirically preceded by positioning build-up (P6). The
priced implication: high recent OI-growth coins carry negative expected drift relative
to low-OI-growth coins over weekly horizons; the family is short that fragility and
long the un-levered alternative. Expected counterparty: late, over-leveraged
directional retail (the counterparty who funds the premium by paying both funding and
liquidation losses), plus sellers of the un-crowded coins to the family's long leg.

## 3. Required observable fields + PIT clock

Required fields (all in the frozen Binance USD-M staged snapshot; no new external data):

- completed 15m base bars per symbol (close; quote volume for the volume deflator);
- per-symbol OPEN INTEREST snapshots at declared cadence in the staged snapshot
  (S4 venue docs define the endpoint semantics);
- BTC completed bars for beta residualisation;
- funding settlements consumed ONLY for cost accounting (never a feature — this keeps
  the family outside the funding-carry/crowding adjacency by construction).

PIT clock:

- daily UTC aggregates: last completed-bar close per day; daily dollar volume; last OI
  snapshot value with publish timestamp strictly inside the completed UTC day;
- `OILEV_FLOW_28D_i,t` = log change over 28 completed UTC days of
  OI_i / daily_dollar_volume_i (open interest per unit of traded volume — the
  flow-of-leverage build-up measure, self-normalised against activity so pure volume
  regimes do not masquerade as positioning build-ups);
- freeze at 00:00 UTC of day d+1; declared 24h execution lag before the next weekly
  decision instant; no partial bars, no OI values with undeclared or future timestamps;
- P9 data-quality gate (fail-closed): per symbol, OI series must be non-negative, free
  of >50% level gaps over the formation window, and pass a plausibility continuity
  check (no single-snapshot level jumps >10x without a settlement-scale volume event);
  any failure marks that symbol's feature UNAVAILABLE for the instant — a missing or
  implausible OI input can never produce an inferred weight.

## 4. Universe + benchmark role

- Universe: Binance USD-M perpetual symbols in the staged snapshot passing (i) the
  completed-bar coverage rule and (ii) the P9 OI plausibility gate for the full
  formation window; BTC excluded from the book (benchmark and beta input); the same
  minimum traded-liquidity listing floor convention as prop1 (bottom decile of median
  daily dollar volume), declared before scoring.
- Benchmark role: flat benchmark and BTC-perp buy-and-hold context benchmark; the book
  is constructed beta-neutral so the context benchmark measures residual beta share,
  not the claim.

## 5. Schedule, holding period, turnover rationale

- Decision instants: weekly, Monday 00:00 UTC; 52 discretionary decisions/365d vs the
  60 floor. Forced-flat/terminal actions reported separately by A3.
- Holding: 7 calendar days; median intended holding = 7d (>= 3d floor).
- Turnover rationale vs L-V10-TURNOVER / L-V10-COST: a 28d trailing characteristic on a
  weekly clock with two bucket legs; OI is a stock variable (slower-moving than any
  flow signal), so bucket membership is persistent and one-way turnover low. M01's
  6,916-position cost burn is structurally impossible at this cadence; the frozen A3
  gate verifies decisions/365d, holding, drag and per-symbol share on schedule
  artifacts BEFORE scoring.
- No symbol > 25% of turnover: quintile-bucket pair construction (tens of symbols per
  leg); verified by A3's per-symbol share metric, not assumed.

## 6. Target construction + risk neutralisation

- Book: long the lowest-OI-growth (least newly-levered) quintile equally weighted,
  short the highest-OI-growth (most newly-levered) quintile equally weighted;
  dollar-neutral.
- Beta neutralisation: rolling 90d daily beta vs BTC (packet's frozen beta rule); leg
  weights scaled to ~0 combined BTC beta — the deleveraging claim must not be a
  hidden BTC beta position.
- Contamination diagnostic (declared BEFORE scoring): report the cross-sectional rank
  correlation between OILEV_FLOW_28D and trailing 28d price return. If OI growth were
  merely a momentum proxy, the book would smuggle the forbidden momentum family;
  the diagnostic is reported alongside the anchor, and A7-N's orthogonality rho vs
  rejected ancestors is the binding test.

## 7. Arms

- anchor: `OILEV-FLOW-28D-W` — long low-OI-growth quintile minus short high-OI-growth
  quintile; 28d formation; weekly hold; beta-neutral.
- theoretically-justified neighbour: `OILEV-STOCK-56D-W` — same book replacing the
  flow feature with the STOCK of leverage: trailing 56d mean of
  OI_i / daily_dollar_volume_i (level intensity, 28d formation on the 56d mean).
  Justification: the deleveraging mechanism implies that not only the RECENT BUILD-UP
  (flow) but the standing leverage intensity (stock) marks fragile books; the two are
  distinct theoretical quantities (derivative vs level), so the anchor's claim predicts
  the neighbour shares the sign; a sign flip would indicate the anchor rode an
  artefact of the differencing window.
- causal negative control (sign-destroying): `OILEV-FLOW-28D-W-INV` — sign-inverted
  anchor (long MOST newly-levered minus short least), same schedule and
  neutralisation. If the inverted book earns a positive after-cost spread, the
  mechanism claim is dead: it would mean OI build-up predicts CONTINUATION (a
  leverage-momentum effect), not deleveraging drag, and the family's mechanism label
  is falsified.

## 8. Expected sign + falsification condition

- Expected sign: anchor net spread > 0 (low-OI-growth coins outperform high-OI-growth
  coins after costs and funding); neighbour same sign, weaker expected magnitude;
  inverted control <= 0.
- Falsification conditions (any one kills the family):
  1. inverted control positive after costs;
  2. anchor net spread negative or ~0 on the scored window (the cross-sectional
     transfer fails even though the time-series prior exists);
  3. neighbour sign opposite to anchor (flow result is a differencing artefact);
  4. anchor edge fully explained by the return-momentum contamination diagnostic plus a
     failed A7-N orthogonality test vs momentum ancestors;
  5. A3 floors fail (cost, decision, holding, per-symbol share) — schedule-infeasible;
  6. OI coverage/plausibility coverage too thin for the universe (fail-closed
     UNAVAILABLE — never traded through).

## 9. Funding / cost treatment

- Costs: adapter taker fees + adverse-tick slippage floor per side via
  `GenericStrategyBase.rebalance_cost_between`; stressed cell fee x1.5 + 2 ticks; all
  cost math reused verbatim, nothing re-implemented.
- Funding: native 8h settlements accrue over held spans via
  `checked_funding_accrual`; funding is a COST LINE ONLY, never a feature. Declared
  economic note: high-OI coins typically carry positive funding while crowded long, so
  the short high-OI leg usually RECEIVES funding — a tailwind that the mechanism must
  not be allowed to claim as its edge; the funding attribution is reported separately
  from the price spread in the family's accounting so the deleveraging claim and the
  funding tailwind are separately visible (this is an attribution disclosure, not a
  scored outcome computed here).

## 10. Ancestry / proximity + orthogonality argument

- V1-V10 forbidden inventory: weekly_reversal_V8, funding_carry_V6, funding_crowding_MR,
  volatility-compression breakout, funding_price_divergence_V7, A8-V10-M01 aggressor
  absorption, trend/momentum, residual mean-reversion, volume-shock continuation. This
  family's only positional observable is OPEN INTEREST — none of the forbidden
  families used OI; no funding signal, no price-return signal, no flow signal, no
  breakout geometry enters the features.
- Funding-crowding adjacency, addressed: the forbidden crowding family is
  FUNDING-based (rate levels/implied crowding). Here funding is excluded from the
  signal by construction and the mechanism is margin/liquidation FRICTION (P5, P6),
  which exists even at zero funding rates. Different observable, different mechanism,
  different counterparty.
- M01 adjacency, addressed: M01 absorbed aggressor FLOW at 15m cadence (6,916
  positions/fold, ~100% cost burn). This family holds a weekly positioning book from
  OI snapshots — 3 orders of magnitude lower decision frequency, different observable
  class, different mechanism (deleveraging drag vs flow absorption).
- Reserved seeds: neither seed uses OI or any positioning observable; both are
  return-shape/risk books. Expected book overlap modest; the short leg (high-OI-growth
  coins) may partially overlap the seed books' long-risk/short-lottery sides, but the
  feature spaces are disjoint, so any overlap is incidental and measurable by A7-N.
- Within-lane orthogonality vs prop1 (ILLIQ-AMIHUD): both deflators use dollar volume,
  so the features share a scale factor; the mechanisms are disjoint (liquidity-provision
  compensation vs deleveraging fragility) and the rank correlation of the two features
  is reported as a diagnostic at implementation time. A7-N's rho gates remain binding.

## 11. Data readiness + implementation estimate

- Readiness: 15m completed bars + OI snapshots + funding settlements are in the frozen
  staged snapshot (S4 semantics). The P9 finding that major venues misquote OI is the
  binding external-validity risk: the plausibility gate (§3) fails closed per symbol,
  and the family reports UNAVAILABLE_FAIL_CLOSED rather than substituting any external
  OI source. If the staged snapshot's OI coverage is venue-implausible for most
  symbols, the family dies at the coverage gate — that is the designed outcome, not a
  blocker for the proposal.
- Estimate: OI ingestion + plausibility gate ~1 day; daily aggregation + flow/stock
  features + contamination diagnostic ~1 day; schedule artifacts for A3 ~0.5 day;
  beta-neutral weighting ~0.5 day. No new adapter or gate code. Estimate only; no code
  written by this lane.

## 12. Why this is not a rescue of a previously rejected family

No rejected family used open interest, so no re-tuned lookback or threshold of a
rejected family can reproduce this mechanism. The failure modes of V10 (zero gross edge
at 15m cadence burned by 6,916 positions/fold) are avoided structurally: 52 decisions/yr,
a stock-variable feature, and a pre-score cost gate. The forbidden crowding-rescue route
is closed by design: funding is never a feature, the crowding here is LEVERAGE crowding
measured from OI with a margin-friction mechanism (P5/P6), and the negative control
would expose any relabelled momentum (contamination diagnostic + A7-N) or continuation
claim. If the mechanism is false, the inverted control and the negative-sign conditions
kill it; nothing in this proposal depends on any previously scored or rejected result
being wrong.
