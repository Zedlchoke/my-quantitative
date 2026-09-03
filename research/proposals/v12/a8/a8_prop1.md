# A8 Proposal 1 — BAB-PERP: cross-sectional systematic-beta mispricing in USD-M perpetuals

Hypothesis ID: `A8-P1-BAB-PERP` · Lane A8 · outcome-blind proposal (no returns/PnL/PF/Sharpe/rankings computed anywhere in this lane).

## 1. Mechanism in one paragraph

At each Monday 00:00:00Z stamp, estimate each symbol's beta to BTC over a trailing
90-day window of daily returns aggregated from completed 15-minute bars. Rank the 19
tradable perps (BTCUSDT is context-only) and hold a beta-neutral spread: long the
lowest-beta quintile (4 names), short the highest-beta quintile (4 names), with leg
scales chosen so the book's BTC beta is zero. The claim is Frazzini-Pedersen's leverage
constraint: in a venue where tiered leverage up to ~100x is retail-accessible, high-beta
alt perps are the natural leverage vehicle, leverage-seeking demand bids them up, and
their risk-adjusted returns are depressed relative to low-beta names. The book collects
the resulting spread with slow covariance ranks, so turnover is structurally low.

## 2. Primary source and exact claim used

Frazzini & Pedersen (2014), "Betting Against Beta", *Journal of Financial Economics*
111(1), 1-25, DOI `10.1016/j.jfineco.2013.10.005` (verified 2026-09-03). Exact claim
used: leverage-/margin-constrained investors overweight high-beta assets, depressing
their risk-adjusted returns; a long-low-beta / short-high-beta, beta-neutral factor earns
significant positive risk-adjusted returns across asset classes, including futures.

### Crypto-perpetual transfer caveats

1. **Direction of the transfer is honest, not assumed.** Retail-dominant, deep-tiered
   leverage should make the constraint channel *stronger* than in FP2014's samples, but
   the crypto factor literature contests the transfer: Liu, Tsyvinski & Wu (2022),
   "Common Risk Factors in Cryptocurrency", *Journal of Finance* 77(2), 1133-1177
   (DOI `10.1111/jofi.13121` — resolved by publisher pattern, flagged inferred) price
   market/size/momentum and some crypto samples find a positive risk-return relation.
   Response: the sign-flipped arm is pre-registered as the causal control, and a control
   win falsifies the family — there is no tuning path.
2. **No BTC hedge leg exists inside the book** (BTCUSDT is context-only), so beta
   neutrality comes from leg rescaling. Residual net beta is a pipeline output to be
   measured, never assumed zero.
3. **Funding is passive.** The short high-beta leg may incidentally collect positive
   funding; the mechanism's sign must hold with funding accounted natively
   (`LONG_PAYS_POSITIVE_RATE`, settlements strictly inside holding spans). The sign-flip
   control faces an identical funding profile, so incidental carry cannot masquerade as
   the mechanism.
4. **Estimation noise.** 90d window, weekly refresh, quintile ranks (not cardinal betas)
   and hysteresis bands keep OLS beta noise from propagating into weights.
5. **Thin quintiles.** 4 names per leg is the whole basis; the `drop_one_symbol` stress
   cell is mandatory, and its rejection condition is pre-registered.

## 3. Economic counterparty and expected sign

Counterparty: accounts that use high-beta alt perps as their leverage vehicle
(leverage-constrained or leverage-seeking retail-tiered users) plus attention-driven
allocation into high-beta alts in risk-on phases. They accept lower risk-adjusted
returns in exchange for amplified exposure. Expected sign: positive spread for
LONG lowest-beta / SHORT highest-beta, beta-neutral, net of the frozen cost stack.

## 4. PIT fields and availability clock

* Inputs: completed 15m bars (close boundary `ts_event` < stamp) for the 19 tradables
  and BTCUSDT; instrument metadata for the cost model. Funding and OI are NOT read by
  the signal (funding accrues passively as a cost only).
* Daily returns: daily close = last completed 15m bar close strictly before each UTC day
  boundary; estimator window = trailing 90 daily returns. Matches
  `data_contract.warmup_days_required.binding_max = 90` (beta_90d), declared satisfiable
  from pre-window history.
* Signal available AT Monday 00:00:00Z; one declared execution lag: targets emitted at T
  fill at the first strict-later event (adapter `FillRecord` semantics); `+1_event_delay`
  stress adds one more event.
* Gaps are failures, never back-filled (`load_validation`).

## 5. Universe, formation, holding, rebalance

* **Universe**: 19 staged USD-M perps; BTCUSDT benchmark-context only.
* **Eligibility per stamp**: fully covered trailing 90d completed-bar window; if fewer
  than 9 names are eligible, the book carries forward unchanged (zero turnover stamp).
* **Formation**: weekly; quintile ranks of beta; long leg = bottom quintile (4 names),
  short leg = top quintile (4 names).
* **Holding**: hysteresis — exit the long leg only when rank leaves the bottom two
  quintiles, the short leg only when rank leaves the top two; entry requires the extreme
  quintile.
* **Rebalance**: weekly stamps only; churn guards: max 2 replacements per leg per stamp,
  no re-entry within one stamp, hard cap 6 exits/symbol/365d. Terminal force-flat at the
  scored-window boundary, counted separately from discretionary decisions.

## 6. Target book, neutralisation, turnover

* Shape: long/short extreme-quintile book (quintile book form permitted by the packet).
* Construction: equal weights 1/4 per leg name; leg scales `c_long`, `c_short` solve
  `c_long * mean(beta_long) - c_short * mean(beta_short) = 0`; final pure-shrink clamp
  `w -> w * min(1, 0.30/max|w|)` inside the deterministic constructor, before the stamp
  is emitted (not a post-score renormalisation).
* Cap by construction: 0.25 per name before the clamp; `max|w| <= 0.30` at every stamp.
* Beta neutralisation: `sum(w * beta) = 0` at every stamp via leg scales.
* Expected turnover (schedule arithmetic only): 52 discretionary decisions/365d
  (<= 60 floor; force-flat counted separately); every completed span is a multiple of
  7d, so median holding >= 3d holds by construction; hysteresis + guards target ~0-2 leg
  replacements per stamp. Cost drag and per-symbol turnover share are enforced ex ante by
  the schedule-only feasibility gate; the guards exist so no single symbol can plausibly
  exceed 25% of turnover.

## 7. Controls (family = anchor + neighbour + causal negative control)

* **Anchor**: the beta-quintile BAB-perp book above.
* **Neighbour (theoretically justified)**: downside-beta sort — same pipeline, beta
  replaced by covariance restricted to BTC-down days (Ang, Chen & Xing 2006, "Downside
  Risk", *RFS* 19(4), 1191-1239, DOI `10.1093/rfs/hhj035`). Same leverage-constraint
  channel concentrated in crash-covariant names; a sibling parameterisation of the same
  theory, not a free hypothesis.
* **Causal negative control (primary)**: sign-flipped arm on the identical pipeline —
  long highest-beta, short lowest-beta, same cost stack. The mechanism fixes the sign of
  the beta premium; a sign-flip win after costs destroys it.
* **Secondary placebo**: permuted-beta labels across symbols within each stamp (book
  shape and cost stack preserved).
* Budget: 3 scored cells (anchor, neighbour, sign-flip) <= the 3/family floor.

## 8. Costs, slippage, funding, stress

Fees at the frozen tier-0 taker floor, per side, changed notional only (adapter
`rebalance_cost_between`); one-tick adverse slippage at each instrument's own tick size
(1e-7..1e-2 declared); funding native while held (`LONG_PAYS_POSITIVE_RATE`, mixed
8h/4h/1h cadences honoured per symbol; funding is a cost, never a signal); stress cells
`fee_slippage_x1_5`, `plus_2_ticks`, `plus_1_event_delay`, `drop_one_symbol`,
`drop_one_fold` per the family folds contract; under `drop_one_symbol` the constructor
re-derives leg weights from surviving names and re-applies the 0.30 clamp.

## 9. Falsification

Reject the family if the sign-flipped causal control matches or beats the anchor after
the frozen cost stack, or if the permuted-beta placebo is indistinguishable from the
anchor; also reject if fewer than 9 names are eligible at > 20% of stamps, if
`drop_one_symbol` overturns the anchor's sign, or if any frozen schedule floor fails at
the feasibility gate. A FAIL is terminal — no lookback retune, fee cut, bucket-width
change or winning-symbol re-selection may follow (that is the forbidden LOT pattern).

## 10. Ancestry map vs V1-V11 (mechanism-level)

| Forbidden class | Relation | Distinction |
|---|---|---|
| `V10-M01-AGGRESSOR-ABSORPTION` | none | no order-flow/aggressor data; covariance of bar closes |
| `V11-LOTTERY-MAX-SKEW` | distinct variable + mechanism | systematic co-moment vs idiosyncratic return-shape statistics (MAX/skew); no return-level or skew term in the pipeline |
| `V11-ILLIQ-AMIHUD` | none | no volume or price-impact ratio in the signal |
| `V11-OILEVER-DELEV` | none | OI never read |
| `V4-XSECT-MOM` | none | no past-return ranking at any horizon |
| `V6/V1-CARRY-FUNDING` | none | funding passive cost only; identical profile for the sign-flip control |
| `V1-VOLCOMP` | none | no compression/breakout/volume-shock trigger |
| `WEEKLY-REVERSAL / MR-RESCUE` | none | no reversal signal of any sign/horizon |
| `DATA-GATED` | none | frozen in-contract fields only |

## 11. Why this is not a rescue

Not a LOT inversion: the sorting variable is a systematic second moment (covariance with
BTC), not idiosyncratic skew or MAX; the channel is a leverage-constraint premium, not
lottery-demand mispricing; no lookback, fee or selection parameter of the LOT family is
re-touched. Not an ILLIQ/OILEV rescue: no illiquidity ratio and no open-interest field
exists anywhere in the pipeline. Not a funding rescue: funding never conditions anything.
Not a renamed baseline: no V1-V11 class sorts on trailing systematic beta, and FP2014's
factor is absent from the documented crypto factor set (market/size/momentum).

## 12. Isolation attestation

This lane read only the packet, the declared schema/interface files, the schedule-only
feasibility gate and the mechanism-level forbidden inventory. No V11 metrics or verdict
artifacts, no other lane's proposals, no S1 or audit material. No returns, PnL, PF,
Sharpe, ranking or backtest was computed; all numbers above are schedule arithmetic or
frozen-contract constants. Literature queries, retrieval UTC stamps and accept/reject
reasons are in `a8_lane_log.md`.
