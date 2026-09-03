# A8 Proposal 2 — TICKET-MIX CONTRARIAN: participation-mix microstructure in USD-M perpetuals

Hypothesis ID: `A8-P2-TICKET-MIX-CONTRARIAN` · Lane A8 · outcome-blind proposal (no returns/PnL/PF/Sharpe/rankings computed anywhere in this lane).

## 1. Mechanism in one paragraph

Every completed 15-minute bar carries two direction-less participation aggregates: quote
volume and trade count. Their ratio — the average USD ticket — separates retail-scale
tickets from institution-scale tickets. At each Monday 00:00:00Z stamp, compute each
symbol's weekly ticket and normalise it by the symbol's own trailing 90-day median of
weekly tickets (removing price level, lot conventions and venue min-notional mechanics).
Rank the 19 tradable perps cross-sectionally and hold a beta-neutral spread: short the
bottom quintile (ticket shrank relative to its own norm = retail influx), long the top
quintile (ticket thickened). The claim is the uninformed-flow channel of the small-trades
literature: price-insensitive retail arrival concentrates at the wrong end of the move
and is followed by weeks of underperformance.

## 2. Primary source and exact claim used

Hvidkjaer (2008), "Small Trades and the Cross-Section of Stock Returns", *Review of
Financial Studies* 21(3), 1123-1151, DOI `10.1093/rfs/hhn049` (venue verified 2026-09-03;
working-paper citations listing JFQA are superseded). Exact claim used: small-trade order
imbalance — uninformed retail participation — is followed by economically large negative
abnormal returns.

### Crypto-perpetual transfer caveats

1. **No direction.** Binance 15m bars give no buy/sell split, so the signed small-trade
   *imbalance* is unavailable. The mechanism is tested on the ticket-SIZE mix level as a
   direction-less proxy for retail presence — a strictly weaker identification, stated as
   such, with the sign-flipped control as the arbiter.
2. **Bar-level averages blur bucket decomposition** (share-count buckets per print in the
   equity literature). The within-symbol normalisation exists precisely so that raw
   cross-symbol ticket levels are never compared.
3. **Retail crypto flow is narrative-driven** (Kogan, Kogan, Makarov, Marinova &
   Szydlowski 2023, "Are Cryptos Different? Evidence from Retail Trading", NBER WP 31317
   — working paper, cited as a transfer caveat only): supports mistiming but does not
   test ticket-mix predictability in perps.
4. **Derivatives wrapper**: the same flow maps to leveraged positioning on perps, and
   liquidation cascades can compress or invert the sign at extremes; weekly horizon +
   hysteresis avoid holding through the most extreme leverage events, and
   `drop_one_symbol` bounds single-name dependence.
5. **Min-notional/lot regimens change over time**; the trailing median normalisation uses
   only PIT data so regime shifts are slow, not lookahead.

## 3. Economic counterparty and expected sign

Counterparty: uninformed retail ticket flow — small-notional orders chasing alt moves,
whose arrival shifts a symbol's traded-ticket distribution toward small prints. They
supply liquidity to better-informed participants at the point of maximal influx and leave
the symbol overpriced. Expected sign: positive spread for SHORT retail-influx (bottom
quintile of normalised ticket) / LONG ticket-thickening (top quintile), beta-neutral,
net of the frozen cost stack.

## 4. PIT fields and availability clock

* Signal inputs: bar `quote volume` and `trade count` over the closed week `(T-7d, T]`
  (usable iff bar close boundary <= T per the data contract's completed-bar rule);
  within-symbol normaliser = trailing 12 weekly values (from the same 90d window), all
  strictly PIT.
* Risk constraint: 90d trailing BTC beta from daily returns aggregated off completed bar
  closes — identical estimator to A8-P1 but used ONLY to keep the book beta-neutral;
  never a signal.
* Signal available AT Monday 00:00:00Z (the week is fully closed); one declared
  execution lag with strict-later fills; `+1_event_delay` stress adds one more event.
* Gaps are failures, never back-filled; if fewer than 9 names are eligible at a stamp,
  the book carries forward unchanged (zero-turnover stamp).

## 5. Universe, formation, holding, rebalance

* **Universe**: 19 staged USD-M perps; BTCUSDT context-only (enters only the beta
  constraint).
* **Formation**: weekly; quintile ranks of the normalised ticket mix; long leg = top
  quintile (4 names), short leg = bottom quintile (4 names).
* **Holding**: hysteresis — exit a long only when the rank leaves the top two quintiles,
  a short only when it leaves the bottom two; entry requires the extreme quintile.
* **Rebalance**: weekly stamps only; churn guards: max 2 replacements per leg per stamp,
  no re-entry within one stamp, hard cap 6 exits/symbol/365d; terminal force-flat counted
  separately from discretionary decisions.

## 6. Target book, neutralisation, turnover

* Shape: long/short extreme-quintile book (permitted form), 4 + 4 names.
* Construction: equal weights 1/4 per leg name; leg scales solve
  `c_long * mean(beta_long) - c_short * mean(beta_short) = 0`; final pure-shrink clamp
  `w -> w * min(1, 0.30/max|w|)` inside the deterministic constructor before emission
  (never a post-score renormalisation). `max|w| <= 0.30` at every stamp by construction
  (0.25 before the clamp).
* Expected turnover (schedule arithmetic only): 52 discretionary decisions/365d
  (<= 60 floor); every completed span a multiple of 7d (>= 3d floor); ~0-2 leg
  replacements per stamp under hysteresis; cost drag and per-symbol turnover share
  enforced ex ante by the schedule-only feasibility gate.

## 7. Controls (family = anchor + neighbour + causal negative control)

* **Anchor**: contrarian ticket-mix spread as above.
* **Neighbour (theoretically justified)**: informed-participation arm — same bar
  aggregates, 4-week TREND of the normalised ticket instead of the level; long the
  fastest-thickening mixes (medium/large-ticket accumulation), short the fastest-shrinking.
  Justified by Barclay & Warner (1993), "Stealth trading and volatility: Which trades
  move prices?", *JFE* 34(3), 281-305, DOI `10.1016/0304-405X(93)90029-B`: informed
  traders camouflage in medium-size trades, so distributional shifts toward medium/large
  tickets reveal informed flow — the same participation channel read out as a trend
  rather than a cross-sectional level.
* **Causal negative control (primary)**: sign-flipped arm on the identical pipeline —
  long retail-influx, short ticket-thickening, same cost stack. A sign-flip win after
  costs destroys the uninformed-flow mechanism.
* **Secondary placebo**: shuffled-ticket labels across symbols within each stamp (book
  shape and cost stack preserved).
* Budget: 3 scored cells (anchor, neighbour, sign-flip) <= the 3/family floor.

## 8. Costs, slippage, funding, stress

Identical frozen treatment to A8-P1: tier-0 taker fee floor per side on changed notional
(adapter `rebalance_cost_between`); one-tick adverse slippage at each instrument's own
tick size (1e-7..1e-2); funding native while held (`LONG_PAYS_POSITIVE_RATE`, mixed
8h/4h/1h cadences honoured per symbol; a cost, never a signal); stress cells
`fee_slippage_x1_5`, `plus_2_ticks`, `plus_1_event_delay`, `drop_one_symbol`,
`drop_one_fold` per the family folds contract; `drop_one_symbol` re-derives leg weights
and re-applies the 0.30 clamp.

## 9. Falsification

Reject the family if the sign-flipped control matches or beats the anchor after the
frozen cost stack, or if the shuffled-ticket placebo is indistinguishable from the
anchor; also reject if `drop_one_symbol` overturns the anchor's sign (single-listing-event
dependence of the mix), if fewer than 9 names are eligible at > 20% of stamps, or if any
frozen schedule floor fails at the feasibility gate. A FAIL is terminal — no
re-bucketing, normalisation retune, fee cut or winning-symbol selection may follow.

## 10. Ancestry map vs V1-V11 (mechanism-level)

| Forbidden class | Relation | Distinction |
|---|---|---|
| `V10-M01-AGGRESSOR-ABSORPTION` | none | no order direction anywhere; only direction-less aggregates |
| `V11-ILLIQ-AMIHUD` | distinct variable + mechanism | Amihud = \|r\|/dollar-volume (price impact); ticket = dollar-volume/trades (participation granularity, NO price term); not a parameter/window/transformation rescue of the reserved identity |
| `V1-VOLCOMP` | none | no volume-magnitude shock trigger; contrarian direction, not continuation |
| `V11-LOTTERY-MAX-SKEW` | none | no return-distribution statistic; signal never touches returns |
| `V4-XSECT-MOM` | none | no past-return ranking |
| `WEEKLY-REVERSAL / MR-RESCUE` | none | never reads a return; a name can be shorted without having risen |
| `V11-OILEVER-DELEV` | none | OI never read |
| `V6/V1-CARRY-FUNDING` | none | funding passive cost only |
| `DATA-GATED` | none | in-contract bar fields only |

## 11. Why this is not a rescue

Not a LOT inversion: zero return-shape statistics; the sorting variable is participation
granularity. Not an ILLIQ rescue: the signal contains no price term, so no price-impact
ratio exists to re-parameterise; "who trades" is not "how much price moves per dollar".
Not an OILEV rescue: open interest is unused. Not a funding rescue: funding never
conditions anything. Not a renamed baseline: aggressor absorption, volume-shock
continuation and Amihud each require a variable (order direction, volume shock, price
impact) that is absent from this pipeline by construction; no V1-V11 class sorts on
traded-ticket granularity.

## 12. Isolation attestation

This lane read only the packet, the declared schema/interface files, the schedule-only
feasibility gate and the mechanism-level forbidden inventory. No V11 metrics or verdict
artifacts, no other lane's proposals, no S1 or audit material. No returns, PnL, PF,
Sharpe, ranking or backtest was computed; all numbers above are schedule arithmetic or
frozen-contract constants. Literature queries, retrieval UTC stamps and accept/reject
reasons are in `a8_lane_log.md`.
