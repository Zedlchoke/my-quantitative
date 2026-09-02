# V10-N1 — A8 Blinded Mechanism Proposals

- **Agent:** A8 (hypothesis-1 role)
- **Wave:** N1 (blinded proposal firewall, PLAN §8)
- **Worktree:** `/Users/hoangminhlong/my-quantitative-v10-wt/n-a8-proposals`
- **Branch:** `orca/v10-n-a8`
- **Base SHA:** `aec9324c97771c26e840c1c10b73dd56737f8f96` (verified clean at intake)
- **Authorization:** `V9H_PASS_V10_AUTHORIZED`, contract
  `research/control/v10_discovery_run/v10_contract.json`
- **Written:** 2026-08-27T05:2xZ
- **Deliverable class:** evidence only. No strategy code, no backtest run, no
  metric/PnL inspection. `results/**` never opened.

---

## 0. Scope, discipline and blindness statement

Three independent mechanisms are proposed. Each is written to be implementable by
an engineer who has never read this document and to be falsifiable by the
frozen Stage-A gate set in PLAN §12.

**Hard-discipline attestation.** None of the three proposals reuses a lookback,
threshold, cadence, symbol subset, cap, direction rule or post-result filter
from any V1–V9 artifact, including `H-V9-TSTREND-v1`. Every numeric quantity in
the anchor configurations below derives from one of exactly four sources:

1. an exchange or calendar fact (15-minute bar grid close stamps, UTC day /
   week boundaries, funding settlement instants),
2. the frozen universe manifest `data/v9_manifests/universe_selection_v9.json`
   (pre-window reference ranges already used by the frozen selector),
3. preregistered transaction costs (`5 bp taker + one adverse tick` per side,
   native funding) from the V10 contract,
4. a risk bound derived arithmetically from a PLAN §12 hard gate (the 40%
   symbol-contribution cap).

There are **no free tuning parameters** in any of the three anchors, and each
proposal carries exactly one anchor plus one theoretically-justified neighbour
plus one negative control, within the frozen budget of three scored slots per
selected family.

**Blindness attestation.** Realized performance for every scored V1–V9 cell was
never accessed. Historical family documentation was consulted *only* to
enumerate nearest-family names and articulate structural deltas; no parameter
value from any prior family was copied into these designs.

---

## 1. Proposed mechanisms (summary)

| # | Hypothesis ID | Essence | Geometry class | Decision clock |
|---|---|---|---|---|
| 1 | `A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL` | Net aggressor-side order flow that failed to move price marks an exhausted liquidity-consuming crowd; fade it with continuous full-cross-section weights | Continuous monotone dollar-neutral panel book, always invested | Daily, UTC day boundary |
| 2 | `A8-V10-M02-TICKET-SIZE-SIGNATURE-EPISODIC` | A record-low average ticket size on a directional day identifies retail-dominated participation at maximum euphoria/panic; trade the hand-off reversal | Two-sided episodic single-name conditional exposure, event-driven clock | Event-driven, evaluated once per UTC day |
| 3 | `A8-V10-M03-LEAVE-ONE-OUT-RESIDUAL-DIFFUSION` | Idiosyncratic return dislocation versus a leave-one-out peer composite clears slowly because no hedging/index flow acts on it; hold the residual-inverse book | Per-symbol time-series exposure orthogonalized against the panel by construction | Weekly, Monday 00:00 UTC |

The three occupy mutually disjoint economic pillars (liquidity-consumption
microstructure / agent-population composition / cross-asset information
diffusion), disjoint raw observables (`taker_buy_quote_volume`, `count` +
`quote_volume`, residualised panel returns) and disjoint payoff geometries.
Pairwise independence arguments appear in §6.

---

## 2. Shared measured data foundation (manifests only)

All sizing below comes from committed layout manifests and file listings. No
bar value, funding rate value, derivative metric or performance number was
read.

### 2.1 Universe and window

Source: `data/v9_manifests/universe_selection_v9.json`.

- Traded cohort: **10 altcoin USD-M perpetuals**, all `role = required`,
  verdict `PASS`:
  `ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, ENAUSDT, SUIUSDT, 1000PEPEUSDT,
  ADAUSDT, BNBUSDT, LINKUSDT` (ranks 1–10).
- Benchmark context: `BTCUSDT-PERP.BINANCE`,
  `excluded_from_ranks_weights_pnl = true`, measurement only. All three
  proposals therefore use **alt-only** constructions and consume BTC neither as
  an input feature nor as a hedge leg.
- Scored window (common completed-bar intersection):
  `2025-08-21T14:30:00Z → 2026-08-21T00:00:00Z` (≈365 days).
- Selection/pre-window (strictly before scoring):
  `2025-07-22T00:00:00Z → 2025-08-21T00:00:00Z` = 30 days.

### 2.2 Row counts (sample-feasibility basis)

Per-symbol completed 15-minute bars inside the scored window:

| Symbol | Completed bars | Notes |
|---|---:|---|
| ETHUSDT | 34,983 | 57-slot capture-boundary hole at `2025-08-21T00:00Z→14:00Z`, classified explained, unexplained gaps = 0 |
| SOLUSDT | 35,040 | gapless |
| XRPUSDT | 35,040 | gapless |
| DOGEUSDT | 35,040 | gapless |
| ENAUSDT | 35,040 | funding cadence differs (see 2.3) |
| SUIUSDT | 35,040 | gapless |
| 1000PEPEUSDT | 35,040 | gapless |
| ADAUSDT | 35,040 | gapless |
| BNBUSDT | 35,040 | gapless |
| LINKUSDT | 35,040 | gapless |

Panel totals:

- Symbol-bars available for feature construction: `9 × 35,040 + 34,983 =
  350,343`.
- Pre-window slots audited per symbol: `2,880` (gap census `expected_15m_slots =
  2880`, `gaps_found = 0`).
- Combined census scope across every candidate and both windows:
  `758,400` expected 15-minute grid slots, `57` gaps total,
  `0` unexplained.

Bar files also extend back to roughly `2024-08-21/2024-08-23` per the pinned
paths (approximately two years of history). This older region is **outside** the
audited gap census. Nothing in any proposal depends on it; see §5.4 caveat.

### 2.3 Funding overlay

- Settled-funding counts in the scored window: `1,095` per symbol for nine
  symbols, but **`2,189` for ENAUSDT**. Funding settlement cadence is therefore
  *heterogeneous across the same cohort*, consistent with
  `rule_constants.legal_funding_intervals_seconds = [3600, 7200, 14400, 28800]`
  and `max_funding_interval_seconds = 28800`.
- PIT convention: settled rates only, keyed by exchange stamp, no forward fill
  past the last settlement (mirrors the repo's funding-PIT fail-closed rules).
- Funding eligibility flags in the manifest report complete held-exposure
  coverage for all ten names.

### 2.4 Available bar fields (code-level schema)

`data/catalog.py` stores bars as Nautilus `BinanceBar`. Fields carried into the
catalog for every row: `open, high, low, close, volume, quote_volume, count,
taker_buy_base_volume, taker_buy_quote_volume, ts_event, ts_init`.

Repo PIT convention (`research/pit_hooks_v10.py`): **a bar's `ts_event_ns` IS
its exchange close stamp**; strict duplicate-close-stamp rejection;
`decision_time_ns = bar.ts_event_ns + info_lag_bars × interval_ns`;
`assert_no_lookahead` enforced downstream.

Two of the three proposals depend on `taker_buy_quote_volume` and `count`.
These exist in the stored bar type but their *population* was not verified
(field values were deliberately not inspected under this wave's blindness
rules). See §5.4, `PREREQUISITE_ATTESTATION_REQUIRED`.

### 2.5 Known-unavailable overlays

`derivatives_data/20260821/manifest.json`: open-interest and mark-price bundles
cover **7 of 10** cohort symbols (`ADA, BNB, DOGE, ETH, LINK, SOL, XRP`) over
only **30 days** ending `2026-08-21T14:00Z`. They cannot support any
panel-wide mechanism over the scored window and are explicitly excluded from
all three designs. Any future OI-based family is currently
`UNAVAILABLE_FAIL_CLOSED` for this universe.

### 2.6 Cost basis

Preregistered baseline from the V10 contract: `5 bp taker + one adverse tick`
per fill plus native funding. Used throughout as `C_rt ≈ 12 bp` round trip for
order-of-magnitude drag arithmetic only; the binding harness figure governs at
scoring time.

---

## 3. Mechanism 1 — `A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL`

### 3.1 Economic source and counterparty

**Source.** Transfer of inventory between *liquidity consumers* and *liquidity
providers*. In a central limit order book, takers cross the spread and consume
the resting depth; makers supply it and must warehouse the resulting inventory.
When a large share of a session's traded value arrives as aggressive
market-buy flow yet price fails to advance, the marginal buyer was
price-insensitive rather than informed — someone bought because of a deadline,
a stop-chase, leverage-onboarding or narrative urgency, not private
information. The resting maker absorbed that demand at successively worse
prices and now carries the other side.

**Counterparty and why they exist.** The counterparty is the uninformed
liquidity-consuming crowd — predominantly leveraged retail and short-horizon
momentum allocators who execute on marketable orders because immediacy matters
more than price to them. They exist structurally in crypto perpetuals because
(a) access is permissionless and fee-tiered toward takers, (b) 24/7 sessions
mean there is always a market open to chase, and (c) perp leverage turns small
conviction moves into urgent executable flow. On the other side stands the
market maker, who exists because standing passive depth earns the spread plus
the reversion premium documented when crowd participation peaks.

This mechanism monetises the *replenishment* leg of that transfer: after
one-sided aggression has been absorbed without commensurate price progress, the
maker's inventory is at its extreme and the crowd's capital is committed, so
the next-day expected return runs against the aggressors.

### 3.2 PIT inputs

Exactly two completed-bar series per symbol, both immutable once stamped:

1. `taker_buy_quote_volume_b(i,t)` — aggressive-buy USDT notional in bar `t`.
2. `quote_volume_b(i,t)` — total traded USDT notional in bar `t`.

PIT safety argument: both are *completed* quantities of a closed 15-minute
interval, stamped with `ts_event_ns` equal to that interval's exchange close
time. The aggregation block for decision at boundary `D` contains only bars
whose close stamp satisfies `(D−1) 00:00:00Z < close ≤ D 00:00:00Z`. Every
contributing bar has therefore finished strictly before the decision instant.
No rolling estimation, no fitting, no forward-filled series, no funding input,
no benchmark series, no regime classifier, no OI/mark overlay. Under
`assert_no_lookahead` the joined frame provably contains only rows whose
feature timestamp precedes `decision_time_ns`.

Also required: the day's block **close-to-close path endpoints**
`open(first bar)` and `close(last bar)` of the same block, used solely for the
eligibility sanity check (§3.6 step 6). Same PIT properties.

### 3.3 Causal sign and justification

**Sign: contrarian to net aggressor imbalance.** Long the symbols whose
yesterday's imbalance was most negative (aggressive selling dominated),
short those where it was most positive.

Mechanism-level justification for *negative* rather than positive sign: if the
aggressive flow carried private information, it would be priced through within
the same session, producing the co-movement that our block-level comparison of
flow and price would reveal as *abnormal persistence*. The proposal restricts
itself to cross-sectional *relative* positioning precisely because the claim is
not "selling pressure depresses price" but "unrewarded, one-sided
liquidity-consuming flow exhausts its own participants". Once a majority of
would-be buyers has executed, the demand curve shifts left: remaining buyers
are of lower willingness-to-pay, and the passive side re-widens quotes to
rebuild target inventory, which mechanically pushes price back toward the maker's
entry band. This is a supply-of-immediacy argument, not a statistical
regularity harvested from the sample.

Note what is *not* claimed: no conditioning on volatility, trend, funding,
breadth or any state variable. Sign is unconditional and monotonically applied
across the whole cross-section.

### 3.4 Signal clock and fill clock

- **Signal clock:** once per UTC calendar day. Decision instant `D_t =
  D 00:00:00Z` is defined by the close stamp of the last 15-minute bar of the
  previous UTC day (that bar opens `D−1 23:45:00Z` and closes `D 00:00:00Z`).
  UTC days are an exchange-native, non-overlapping partition of crypto's 24/7
  tape — chosen because they are structural, not because they were searched.
- **Fill clock:** next allowed event after the signal bar completes, i.e. the
  **OPEN of the 15-minute bar whose open timestamp equals `D 00:00:00Z`**.
  This is the first tradable print after every contributing bar has closed.
  Fills are taker fills at that open.
- Order placement and fills occur at a single synchronous event per rebalance;
  intra-block partial fills are out of scope. Stress variant adds one further
  event delay per PLAN §11.

### 3.5 Holding horizon

One UTC day, continuously renewable. Positions are retargeted to fresh targets
at every daily boundary and force-flattened at the final scored-window
boundary so nothing carries past the fold edge. Effective holding period
distribution is therefore geometrically renewable around 24 hours; there is no
separate stop, take-profit or trailing exit.

### 3.6 Concrete construction recipe

Implementer recipe. Inputs are the hash-pinned catalog bars for the ten
required symbols.

1. Build the completed-bar table per symbol sorted ascending by close stamp,
   rejecting duplicate close stamps (harness behaviour).
2. For each UTC date `D` in `[scored_start+1d, scored_end]`:
   a. Block `B(D)` = all bars with `(D−1) 00:00:00Z < close_stamp ≤ D
      00:00:00Z`.
   b. A symbol is **eligible** on `D` iff `len(B_i(D)) == 96`. Otherwise it is
      dropped from that day's cross-section (this cleanly removes ETHUSDT's
      57 missing opening slots before the common intersection starts).
   c. If eligible count `< MIN_ELIGIBLE`, skip the whole rebalance and carry
      previous weights unchanged (see constant table).
   d. `Q_i(D)  = Σ_{B} quote_volume`, requires `Q_i > 0` else ineligible.
      `F_i(D)  = Σ_{B} taker_buy_quote_volume / Q_i` ∈ [0,1].
      `A_i(D)  = 2·F_i(D) − 1` ∈ [−1, 1].
   e. Cross-sectionally standardise over eligible `i`:
      `Ā = mean(A_i)`, `s_A = stdev(A_i)` (sample, ddof=1);
      `Ạ_i = (A_i − Ā)/s_A`; if `s_A == 0` treat all `Ạ_i = 0`.
   f. Raw signed weight `raw_i = −Ạ_i`.
   g. Solve for the unique scalar `λ ≥ 0` such that `Σ_i |clip(λ·raw_i,
      ±CAP)| = 1.0` by deterministic bisection: bracket `λ ∈ [0, 1e6]`,
      200 halvings or until the constraint residual `< 1e-12`, taking the
      first λ satisfying it. Always converges because `Σ|raw_i| ≥ CAP·n`
      slack exists whenever `n_eligible ≥ MIN_ELIGIBLE`.
   h. Emit targets `w_i = clip(λ·raw_i, ±CAP)`.
3. At `D 00:00:00Z`, trade from current holdings to `{w_i}` at the open of the
   bar opening at `D 00:00:00Z`. Charge baseline costs on traded notional.
4. Accrue native funding on whatever legs remain held across each settlement
   instant between boundaries.
5. Repeat; force-flat everything at the final scored-window boundary using the
   same fill convention.

Constants (all structural or gate-derived):

| Constant | Value | Derivation |
|---|---:|---|
| bars per block | 96 | 24 h ÷ 15 min — exchange grid fact |
| signal instants | 365 | UTC calendar days in scored window |
| `MIN_ELIGIBLE` | 8 of 10 | guarantees both sides of a capped book stay diversified and keeps the bisection feasible |
| `CAP` | 0.30 | margin below the PLAN §12 hard gate "symbol contribution/risk ≤ 40%" |
| gross target | 1.0 | unit-gross dollar-neutral book, cash-neutral by construction |

### 3.7 Expected regimes

**Edge concentrates:**

- High-participation, churn-heavy tape where retail-sized marketable flow
  dominates and intraday reversals are frequent.
- Periods of elevated aggressor-flow dispersion across the cohort but low
  directional persistence — i.e. crowded, contested markets.
- Low-trend stretches following sharp single-day squeezes (post-squeeze give-back).

**Edge should lose:**

- Genuine information regimes: protocol incidents, delisting/lockup news,
  macro shocks, listing-driven repricing — where aggressor flow *is* informed
  and continues. Expect losses concentrated there.
- Persistent trending quarters where momentum overwhelms one-day mean reversion
  (this is the classic anti-regime for contrarian books).
- Days with truncated blocks (fewer than 96 bars) — partially mitigated by the
  eligibility rule but thin cross-sections weaken standardisation.

Because sign is unconditional, honest expectation is a modest gross-book edge
with significant drawdown episodes during sustained trends. Stated plainly: a
contrarian always-invested book is the *more* likely of the three to breach
`MDD ≤ 10%`.

### 3.8 Falsification procedure

Killed if any of the following holds after scoring the anchor cell:

1. After-cost expectancy ≤ 0 (PLAN §12 hard gate).
2. Overall PF < 1.10.
3. Fewer than 2 of 3 chronological folds positive, or any populated fold
   PF < 0.80.
4. Fold contribution > 50%, max drawdown > 10% of gross, or symbol
   contribution/risk > 40% (should be impossible above 40% given `CAP=0.30`,
   which itself serves as an implementation-correctness assertion).
5. **Mechanism-specific killer:** if stressed PnL ≤ 0 or stressed PF < 1.00
   under the fee/slippage ×1.5 and +1-event-delay stresses, the assumed
   inventory-rebuild horizon is not economically reachable at realizable cost
   and the mechanism is dead regardless of nominal profitability.
6. Any drop-one-symbol or drop-one-fold rerun flipping the sign of expectancy —
   the claim is cross-sectional and must not depend on a single name.

### 3.9 Negative control

Replace per-symbol `Ạ_i` with the **cross-sectional day mean** `Ā` assigned to
every symbol, i.e. destroy all symbol-specific variation while preserving the
common market-wide flow component, then run the identical pipeline,
standardisation, caps, clocks, fills and costs.

Interpretation: the claimed causal channel is *relative* aggressor positioning
per name. If the control book earns expectancy statistically indistinguishable
from the anchor, the profit came from timing aggregate market-wide flow (a
different, unstated mechanism) and the stated causal sign is invalidated. The
control must materially degrade; otherwise reject the family irrespective of
its absolute score.

### 3.10 Nearest historical families and material deltas

Nearest families from the existing inventory, ordered by proximity:

- `H-XSECT-REVERSAL-v1/v2`, `H-XSECT-REVERSAL-BREADTH-CRYPTO-v1`
  (cross-sectional price-rank weekly reversal)
- `H-XSECT-MOM-v1` (cross-sectional price-rank momentum)
- `H-XSECT-FUNDING-CARRY-v1`, `H-XSECT-FUNDING-PRICE-DIVERGENCE-v1`

Material-delta claims, all four dimensions asserted TRUE:

| Dimension | Prior families | This proposal | Material? |
|---|---|---|---|
| Economic source | Past-price-based crowding, or crowded-side carry burden | Inventory transfer from liquidity *consumers* to *providers*; aggressor exhaustion, independent of price history and carry level | YES |
| Observable construction | Trailing cumulative-return rank; published settled-funding-rate rank; bandwidth/Donchian/volume-ratio gates | Raw exchange-reported aggressor-side notional split (`taker_buy_quote_volume` / `quote_volume`) — a field no V1–V9 family ever consumed | YES |
| Selection-payoff geometry | Binary extreme-N tails (long bottom-k / short top-k) with equal weights inside each leg; fixed weekly/daily clocks; or dead-zone time-series rules | Continuous monotone weights applied across the entire cross-section, unit gross, cap-bounded, no discrete selection set, always invested, no flat state | YES |
| Counterparty / regime prediction | Momentum chasers providing exit liquidity; crowded leverage paying carry; breakout chasers paying post-expansion spread | Identifiable microstructural actor pair (taker crowd vs standing maker) whose inventory imbalance is directly measurable — prediction is about *who transacted*, not how price behaved | YES |

Explicitly disclosed overlap risk: dimension 3 shares the "dollar-neutral multi-leg
book" surface with the families above. Novelty rests on *how* weights arise
(continuous function of a flow observable over all names versus binary tail
selection), not on being long-something-short-something. Should A5 score that
as insufficient, M01 loses geometry credit honestly rather than by renaming.

### 3.11 Sample feasibility

- Feature samples: 365 daily crossings × up to 10 names ≈ 3,650 symbol-day
  feature observations built from ~350,343 underlying completed symbol-bars —
  enormous relative to the estimator's complexity (zero fitted parameters).
- Statistical units for fold evaluation: ~120 daily rebalances per fold, 3
  folds. Comfortably exceeds any reasonable sample floor.
- Concentration: bounded structurally by `CAP=0.30`, satisfying the §12 gate
  with margin.
- Warmup requirement: 96 completed bars = 24 h, trivially satisfied inside the
  audited pre-window.
- Costs: turnover per day is bounded by gross (≤ 1.0) and realistically well
  under it because standardized cross-sectional weights drift slowly; even at
  a pessimistic 60% of gross turned over daily, drag ≈ 0.60 × 12 bp × 365 ≈
  263 bp/year against a gross book — material but not prohibitive. Flagged as
  the main cost sensitivity; the ×1.5 stress covers it.

Verdict: **SIZABLE**. No data gap affects this design.

### 3.12 Audit cost estimate

Implementation + unit tests + PIT/golden review: **~6–8 agent-hours**. Runtime
per scored cell: seconds (350k rows, zero iterative optimisation). Reproduction
and stress waves: negligible compute. Audit effort is dominated by verifying
that `taker_buy_quote_volume` semantics are as declared (attestation prerequisite).

### 3.13 Anchor and neighbour configs

**ANCHOR — `M01-A`**: exactly the construction in §3.6.
Base volume weighting (`taker_buy_quote_volume` / `quote_volume`),
cross-sectional standardisation, `MIN_ELIGIBLE=8`, `CAP=0.30`, gross 1.0,
daily UTC signal/fill clocks, one-day horizon, costs = `5bp + 1 tick` per fill
plus native funding.

**NEIGHBOUR — `M01-N` (one theoretically-motivated change only)**: replace the
cross-sectional standardisation denominator with a **pre-window flow-dispersion
normalisation**. Compute, once, per symbol, at the last completed bar before
the scored window starts, `σ_i` = sample stdev of *per-bar* aggressor imbalance
`a_{i,b} = 2·taker_buy_quote_volume_b/quote_volume_b − 1` over the 2,880 audited
pre-window slots (all PIT, all inside the already-censused range). Then set
`raw_i = −A_i(D)/(σ_i/√96)` instead of `−(A_i−Ā)/s_A`. Everything else
identical, including clocks, caps, gross and costs.

Justification: the anchor lets *today's panel dispersion* define comparability;
the neighbour asks whether comparability should instead come from *each name's
own historically typical microstructure activity*. This isolates whether the
edge requires the concurrent cross-section at all, which is the load-bearing
part of the causal story. It touches no clock, no threshold, no parameter count.

---

## 4. Mechanism 2 — `A8-V10-M02-TICKET-SIGNATURE-EPISODIC`

### 4.1 Economic source and counterparty

**Source.** Wealth transfer from impatient, unsophisticated capital to patient
capital, observable through *ticket-size composition*. Average ticket size =
notional traded ÷ number of trades. When a symbol's average ticket collapses to
a record low while price is moving directionally, the day's flow was carried by
a very large number of small orders — the canonical footprint of dispersed
retail participation chasing (up-moves) or capitulating (down-moves). Such
order flow is the least informed and most momentum-correlated population in the
market; it reaches its own historical extremity exactly when enthusiasm or panic
peaks.

**Counterparty and why they exist.** The counterparty is the small-ticket retail
crowd itself, plus the passive depth selling into their euphoria. They exist
because crypto perps offer the lowest-friction, highest-leverage, 24/7 access
of any asset class; their decision cycle is attention-driven rather than
valuation-driven, and they systematically transact *after* the informational
content of a move has been realised. The provider side exists because somebody
must take the other end, and the compensation for doing so at peak crowd
participation is the subsequent unwind.

Distinct from Mechanism 1: M01 identifies *which side of the book initiated*
(this is aggressor orientation); M02 identifies *what kind of agent did the
initiating* (this is ticket granularity). A day can exhibit extreme aggressor
imbalance composed of institutional-size prints (informed continuation risk) or
extreme imbalance composed of retail-size prints (crowd-exhaustion opportunity).
The two observables can and do disagree.

### 4.2 PIT inputs

Completed-bar series per symbol, aggregated over the same UTC day block
`(D−1 00:00:00Z, D 00:00:00Z]`:

1. `count_b(i,t)` — number of trades in the bar.
2. `quote_volume_b(i,t)` — traded USDT notional.
3. Bar `close` prices for the day's block return `r_i(D)`.

Derived block statistic:

```
ticket_size_i(D) = Σ_B quote_volume_i / Σ_B count_i       [USDT per trade]
```

Reference distribution (static, frozen once, never updated during OOS): the 30
daily values `ticket_size_i(d)` for `d` in the audited pre-window
`2025-07-22T00:00:00Z → 2025-08-21T00:00:00Z`. These 30 values come entirely
from the censused range (`gaps_found = 0`) and are frozen at the moment the
scored window opens. Let `m_i = min_d ticket_size_i(d)`.

PIT safety: every element of the reference is strictly earlier than every
scored decision; the reference is never refreshed, recursively updated or
expanded during OOS, so there is no adaptive-threshold lookahead. Per-symbol
references keep the trigger scale-free despite the ~six-orders-of-magnitude
price span across the cohort (PEPE vs BNB).

Funding accrual applies natively; no funding, volatility, trend, breadth, OI or
regime variable enters anywhere.

### 4.3 Causal sign and justification

**Sign: fade the crowd's direction on a record-low average-ticket day.**

- Record-low `ticket_size` AND `r_i(D) > 0` → the up-move was carried by maximal
  dispersion of small buyers, i.e. euphoric retail absorption of inventory held
  by better-capitalised holders. Position: **SHORT**. Expected forward return
  negative.
- Record-low `ticket_size` AND `r_i(D) < 0` → panic liquidation by the least
  patient holders, transferring inventory down-scale to more resilient owners.
  Position: **LONG**. Expected forward return positive.

Mechanism justification: composition identifies the *population*, and
populations have stable behavioural horizons. Retail flows arrive late relative
to information arrival and face binding margin/attention constraints; when their
participation hits an extreme, the source of incremental buying (or selling) is
about to be exhausted, while the opposite side — holders with longer horizons —
is still present. The predicted correction is therefore *directional* (against
the crowd) and *multi-session* (positions need time to rebuild), which is why
holding is calendar-week scoped rather than intraday.

Contrast with the failed prior uses of volume in the inventory: every prior
family treated volume as a *magnitude* (dollar-volume shock ratio, volume burst
vs moving average). Magnitude confounds "many participants" with "large
participants"; composition does not. That distinction is the whole hypothesis.

### 4.4 Signal clock and fill clock

- **Evaluation clock:** once per UTC day at the completed 96-bar day block, as
  in M01 — but this family's *decision* clock is **event-driven**: on most days
  most symbols produce no position at all. Trigger occurrence is determined
  exogenously by the data, making this the only one of the three proposals
  whose decision times are not a fixed calendar grid (a structural class the
  current family inventory records as absent).
- **Fill clock:** entry at the OPEN of the 15-minute bar opening exactly at
  `D 00:00:00Z` (first allowed event after the triggering block closes).
- **Exit clock:** force-close at the fill event seven UTC days later, i.e. at
  the open of the bar opening `D+7 00:00:00Z`. No stops, no take-profit, no
  trailing logic, no re-entry while a position is live in that symbol.

### 4.5 Holding horizon

Exactly 7 UTC calendar days per event. Justification: the hypothesised hand-off
unwinds over multiple sessions and needs to span the full weekly liquidity
cycle including the thin weekend regime, so the horizon is fixed by market
structure rather than searched. Purge/embargo ≥ 7 days satisfies PLAN §11's
"purge/embargo ≥ holding horizon" automatically.

### 4.6 Concrete construction recipe

1. Load completed 15-minute bars for the ten required symbols.
2. Freeze per-symbol references from the pre-window only:
   `REF_i = {ticket_size_i(d) : d ∈ pre-window}` (30 values),
   `m_i = min(REF_i)`. Hash-pin `REF_i`; never touch again.
3. For each UTC date `D` in the scored window:
   a. Form the 96-bar block `B_i(D)`; require exactly 96 bars, else skip symbol.
   b. Require `Σ_B count_i > 0` and `Σ_B quote_volume_i > 0`, else skip.
   c. `ts_i ← Σ_B quote_volume / Σ_B count`;
      `r_i ← ln(close(last bar)/open(first bar))`;
      `dir_i ← sign(r_i)`.
   d. **Trigger** iff `ts_i < m_i` (strictly below the frozen record).
      Direction: SHORT if `r_i > 0`, LONG if `r_i < 0`.
      Note `r_i = 0` is not triggerable; log-only.
   e. Skip the trigger if a position in that symbol is already live
      (single-position-per-symbol invariant); do not queue or roll it.
4. Position sizing: each event receives notional `GROSS/n_max` where
   `GROSS = 1.0` and `n_max = 10` = cohort size. Per-event notional is thus a
   constant `0.10` of the book, giving worst-case concurrent gross ≤ 1.0 and
   worst-case single-symbol concentration ≤ 10%.
5. Execute entries/exits at the specified event opens; charge baseline costs
   per fill; accrue native funding while held.
6. Force-flat any surviving position at the final scored-window boundary.

Constants:

| Constant | Value | Derivation |
|---|---:|---|
| block size | 96 bars | exchange grid fact |
| reference length | 30 daily blocks | audited pre-window length from the frozen manifest |
| trigger | strictly below pre-window minimum | record property — parameter-free |
| holding | 7 UTC days | canonical weekly liquidity cycle |
| `GROSS` | 1.0 | unit-risk convention shared with M01/M03 |
| `n_max` | 10 | cohort size ⇒ concentration bound 10% |
| positions/symbol | 1 | avoids pyramiding without introducing a limit parameter |

### 4.7 Expected regimes

**Edge concentrates:**

- Post-parabolic retail attention episodes in the higher-beta, smaller-cap
  members of the cohort (`DOGEUSDT`, `SUIUSDT`, `ENAUSDT`, `1000PEPEUSDT`).
- Capitulation flushes at local lows, where forced small-holder selling exhausts.
- High-realized-dispersion stretches where single-name narratives dominate the
  tape rather than a common factor.

**Edge should lose:**

- Institutionally-driven regimes — ETF/index-related flow, large treasury
  allocations, market-wide deleveraging — where large-print participation, not
  small-print, dominates and moves continue instead of reverting.
- Quiet, low-interest stretches: few triggers fire at all, so realised event
  counts fall below expectation and the family contributes nothing.
- Immediately around protocol-specific news, where small-ticket records may
  simply lag legitimate repricing (false positives).

### 4.8 Falsification procedure

1. Standard gates: after-cost expectancy ≤ 0; PF < 1.10; fewer than 2 of 3
   folds positive; populated-fold PF < 0.80; fold contribution > 50%;
   concentration > 40%; stressed PnL ≤ 0 or stressed PF < 1.00.
2. **Mechanism-specific killer A (sign symmetry):** if pooled post-event mean
   forward return has the same sign for both trigger directions (i.e. both the
   SHORT-after-up and LONG-after-down cohorts lose, or both win), the result is
   a general long/short market tilt rather than crowd-composition reversion —
   kill.
3. **Mechanism-specific killer B (event rarity):** if total triggered events
   across the scored window fall below the fold-statistics floor such that
   `≥2/3 folds positive` cannot be evaluated, report the failure as
   `UNAVAILABLE_FAIL_CLOSED: EVENT_COUNT_INSUFFICIENT`. Do not widen the
   trigger to manufacture events — that is forbidden tuning.
4. Drop-one-symbol robustness: removing any single name must not flip the
   expectancy sign.

### 4.9 Negative control

Run the identical machinery, triggers, clocks, sizing and holding with the
signature **inverted**: substitute `ts'_i = ticket_size_i(D)` compared against
`M_i = max(REF_i)` (record-*high* average ticket size = institutionally
dominated participation), keeping the same direction matching.

Causal claim under test: *small tickets mark uninformed crowding, hence
reversion.* If record-high-ticket events show equal or stronger post-event
reversal at comparable event counts, the effect is a generic
extreme-participation anomaly unrelated to agent composition and the stated
causal sign fails. Reject the family in that case regardless of profitability.

### 4.10 Nearest historical families and material deltas

Nearest families:

- `H-VOLCOMP-BRKOUT-v1` — single-name conditional event entries
- `H-V9-VOLSHOCK-v1` — dollar-volume shock gate selecting a traded sub-cohort
- `H-FUNDCROWD-MR-v2` — crowding-*gated* single-name mean reversion

Material-delta claims, four dimensions asserted TRUE (one with disclosure):

| Dimension | Nearest priors | This proposal | Material? |
|---|---|---|---|
| Economic source | Liquidity-provider immediacy demand (VOLSHOCK); breakout chasers paying spread (VOLCOMP); crowded-side carry burden (FUNDCROWD) | Agent-population composition — wealth transfer based on *who* transacted, identified from order-size granularity | YES |
| Observable construction | Bollinger-bandwidth percentile / Donchian channel break / volume-burst ratio; normalised dollar-volume vs trailing baseline; funding percentile rank | Distributional shape of executed order size (`quote_volume ÷ count`), never consumed by any V1–V9 family; `count` appears nowhere in the inventory | YES |
| Selection-payoff geometry | VOLCOMP: single-name long-only breakouts with ATR/R exits; VOLSHOCK: two-stage conditional sub-basket continuation; FUNDCROWD: reclaim-MR with funding gate | Symmetric two-sided episodic reversal, event-driven clock, flat-by-default, fixed 7-calendar-day exit, no indicator stack, no stop/target | YES |
| Counterparty/regime prediction | Named counterparties exist in priors but are inferred from price/volume magnitude states | Predicts from the identified *class* of the marginal trader; composition is a direct measurement of that counterparty | YES, with disclosure |

Disclosure: `H-V9-VOLSHOCK-v1`'s framing ("attention/liquidity shock, providers
demanding immediacy") is conceptually adjacent in spirit. The delta is that
VOLSHOCK conditions on the *size* of an abnormal volume outcome and predicts
continuation, whereas M02 conditions on the *granularity composition* of a
normal-volume day and predicts reversal. Opposite predicted signs from related
but distinct observables.

### 4.11 Sample feasibility

Derivation, fully explicit so the estimate can be checked:

- Reference length `n = 30` daily blocks. Under exchangeability, the
  probability that a new independent observation falls below the minimum of
  30 draws is `1/(n+1) = 1/31 ≈ 0.03226`.
- Expected breaches per symbol per scored year: `365 / 31 ≈ 11.77`.
- Panel-wide: `10 × 11.77 ≈ 117.7`.
- Direction matching roughly halves the usable events (the record-low may fall
  on a day whose own return direction is inconsistent or zero): expect
  **≈ 59 events/year**, ± clustering variance substantially larger than a
  Poisson approximation suggests.
- Per fold (~122 days): ≈ 20 events expected, but distribution across folds
  will be uneven because record breaches cluster in stressed regimes; one fold
  may be sparsely populated.

This is the weakest sample of the three proposals and is disclosed as such.
Options considered and rejected: widening the trigger via a quantile (introduces
an arbitrary probability constant), shortening the reference (weakens PIT
standing), or dropping the direction filter (destroys the mechanism). None is
permissible under the no-grid discipline. Therefore either the family is
selected *with this disclosed limitation accepted*, or it is not selected.

Costs: ~59 events/year × 2 fills × ~12 bp ≈ 14 bp annual drag — negligible.

Warmup: satisfied entirely inside the audited pre-window.

Verdict: **MARGINAL — sizeable but statistically thin; flagged, not hidden.**

### 4.12 Audit cost estimate

Implementation + tests: **~7–9 agent-hours** (record/reference freezing and
hash-pinning adds provenance work beyond M01). Runtime per scored cell:
seconds. Additional audit burden: verify the reference series is genuinely
pre-window-only and never mutated during OOS — the single most important
anti-leak check for this family and an obvious candidate for an A10 adversarial
golden test.

### 4.13 Anchor and neighbour configs

**ANCHOR — `M02-A`**: exactly §4.6 — record-low average ticket size, direction-
matched, 7-day calendar holding, fixed 0.10 per-event notional, single position
per symbol, pre-window-minimum reference.

**NEIGHBOUR — `M02-N` (one theoretically-motivated change only)**: replace the
block-level ticket statistic `Σqv / Σcount` with the **median per-bar ticket
size** across the block (`median_t(quote_volume_t / count_t)` over the 96 bars),
same reference construction (minimum of 30 pre-window daily medians), same
everything else.

Justification: the anchor's ratio is sensitive to a handful of very large
prints dominating the notional numerator, so a day could register as
"retail-dominated" while actually containing one institutional sweep. The
median is robust to exactly that contamination and asks whether the crowd signal
is a genuine *typical* participant characteristic rather than a mixture artefact.
One measurement choice changes; no clock, threshold, horizon or parameter count
changes.

---

## 5. Mechanism 3 — `A8-V10-M03-RESIDUAL-DIFFUSION-WEEKLY`

### 5.1 Economic source and counterparty

**Source.** Slow information diffusion and stale-reference quoting across linked
assets. In a correlated cohort, shocks common to the group are impounded in the
liquid, heavily watched names almost immediately but propagate imperfectly to
individual constituents; conversely each name accumulates an idiosyncratic
return component with no fundamental support once the common factor is removed.
Two frictions delay the closing of that residual: heterogeneous-attention
investors respond to headline price action rather than to peer-relative value,
and market makers quote off recently observed levels, so stale prices persist
until arbitrageurs commit costly inventory.

**Counterparty and why they exist.** (i) Slow-attention investors who act on
absolute price changes and thus push an idiosyncratic outperformer further than
peer-consistent fundamentals justify — they exist because monitoring a cohort
costs more than watching one chart. (ii) Passive limit-order traders anchored to
stale references — they exist because quoting off the last print is cheaper and
operationally simpler than repricing to a peer composite. Both are systematic,
persistent features of decentralised, non-consolidated crypto venue structure
where no index-arbitrage or creation/redemption mechanism mechanically enforces
cohort consistency as it does in ETFs.

Important honesty note: this is the *lowest-prior* of the three proposals. At
top-ten-by-volume liquidity, much of the exploitable diffusion lag may already
be arbitraged away, especially at weekly frequency. It is proposed because it
is structurally novel, cheap to test, occupies an untouched mechanism class, and
its falsification is clean.

### 5.2 PIT inputs

All inputs are completed-bar returns derived from `close` prices only.

1. Per-bar log returns for each of the ten symbols.
2. Leave-one-out panel composite at bar frequency: `r̄_(−i),b =
   (Σ_{j≠i} r_j,b)/9`.
3. One coefficient per symbol, estimated **once**, from the audited 30-day
   pre-window (2,880 paired bar observations):

```
β̂_i = cov(r_i,b , r̄_(−i),b) / var(r̄_(−i),b)        over pre-window bars
σ_e,i = stdev(r_i,b − β̂_i · r̄_(−i),b)               over pre-window bars
```

Both coefficients are computed from data strictly inside the censused range,
frozen at the scored window start, hash-pinned and never refitted during OOS.
No rolling estimation, no per-period recalibration, no vol targeting, no
beta drift.

Weekly decision features: the completed-bar weekly log return
`r_i,w = ln(P_i(w) / P_i(w−1))` using close stamps of the last completed 15m
bar before consecutive Monday `00:00:00Z` boundaries; leave-one-out composite
`r̄_(−i),w` formed analogously from weekly returns.

PIT safety: every `r_i,w` is fully determined by bars closing at or before the
Monday boundary; the pre-window coefficients predate the first scored decision
by the entire pre-window; nothing else enters. The weekly clock reuses a
convention already proven in the repo harness, reducing implementation risk,
though clock reuse is expressly *not* a novelty claim.

### 5.3 Causal sign and justification

**Sign: short the idiosyncratic overperformer, long the idiosyncratic
underperformer — contrarian in residual space.**

Weight vector `raw_i = − e_i / σ_e,i` where the week's dislocation is
`e_i,w = r_i,w − β̂_i · r̄_(−i),w`.

Mechanism-level justification for a *negative* sign: because the common factor
is stripped out, the residual cannot reflect cohort-wide demand. What remains is
name-specific pressure. Two forces then act on it: attention-driven inflow that
chases absolute performance (pushing positive residuals further near-term) and
re-pricing to peer consistency (pulling it back). The bet is that at a *weekly*
horizon the second dominates, because (a) there is no mechanical holder of the
idiosyncratic leg comparable to an index fund who would keep it elevated, (b)
makers rebuild inventories around peer-relative bands, and (c) residual spikes
are disproportionately caused by transient order imbalance rather than durable
fundamental divergence. Dividing by `σ_e,i` puts names on a common footing so
the bet is on standardised dislocation rather than raw percentage moves.

Deliberately not claimed: continuation effects from momentum, carry from
funding, or anything driven by the absolute level of returns.

### 5.4 Signal clock and fill clock

- **Signal clock:** Monday `00:00:00Z`, at the close stamp of the final
  completed 15-minute bar preceding the boundary. 52 crossing times in the
  scored window.
- **Fill clock:** OPEN of the 15-minute bar whose open timestamp equals the
  Monday boundary — the first allowed event after every contributing bar has
  closed. Same convention as M01/M02 so the three families share one
  implementation primitive.

### 5.5 Holding horizon

Exactly one UTC week, rebalanced at every Monday boundary, force-flattened at
the final scored-window boundary. No stops or targets.

### 5.6 Concrete construction recipe

1. Load completed 15m bars for the ten required symbols; build per-bar log
   returns aligned on close stamps, requiring all ten names present on each
   bar slot for composite formation (drops the ETHUSDT pre-intersection slots
   automatically).
2. Using pre-window slots only, compute and freeze `β̂_i` and `σ_e,i` per
   symbol as in §5.2. Hash-pin them.
3. For each scored week `w` with boundary Mondays `M_w`:
   a. `r_j,w = ln(close_j(M_w) / close_j(M_(w−1)))` for all ten names.
   b. `e_i,w = r_i,w − β̂_i · mean_{j≠i}(r_j,w)`.
   c. `raw_i = −e_i,w / σ_e,i`.
   d. Apply the identical cap-and-normalise routine as M01 §3.6(g–h):
      solve `λ` so `Σ_i |clip(λ·raw_i, ±CAP)| = 1.0`, emit `w_i`.
4. Trade to targets at the open of the bar opening `M_w 00:00:00Z`; charge
   baseline costs on traded notional; accrue native funding across settlements
   during the week.
5. Repeat weekly; force-flat at the final scored-window boundary.

Constants:

| Constant | Value | Derivation |
|---|---:|---|
| decision instants | 52 | Monday 00:00 UTC weeks in a 365-day window |
| estimation sample | 2,880 pre-window bar pairs | audited pre-window length |
| `CAP` | 0.30 | margin under the §12 40% concentration gate |
| gross | 1.0 | unit-gross convention shared with M01 |
| normaliser | pre-window `σ_e,i` | PIT, frozen once |

### 5.7 Expected regimes

**Edge concentrates:**

- Cohorts trading as a correlated block (high average pairwise correlation),
  where a well-defined systematic component exists to be stripped.
- Weeks of sharp coordinated sector moves followed by partial retracement.
- Low-news stretches, where residuals are dominated by order-flow noise rather
  than protocol events.

**Edge should lose:**

- Idiosyncratic-information regimes: token unlocks, governance votes, protocol
  exploits, stablecoin/bridge incidents, delistings, index-inclusion news.
  There the residual *is* the information and persists or extends.
- Very high-dispersion decoupling phases where the factor model breaks down
  (`β̂` no longer representative), leading to wrongly signed bets.
- Regimes where correlation collapse makes the leave-one-out composite nearly
  meaningless, leaving raw noise sized by a stale `σ_e,i`.

Since this family shorts recent idiosyncratic winners, a persistent
winner-streak quarter is its principal drawdown scenario.

### 5.8 Falsification procedure

1. Standard Stage-A gates: after-cost expectancy ≤ 0; PF < 1.10; < 2 of 3 folds
   positive; populated fold PF < 0.80; fold contribution > 50%; MDD > 10%;
   concentration > 40%; stressed PnL ≤ 0 or PF < 1.00; drop-one dependency.
2. **Mechanism-specific killer:** if the residual-inverse book's expectancy is
   not materially improved over the `β̂ ≡ 0` negative control (§5.9), the
   systematic-neutralisation step is decorative and the family reduces to a
   plain prior-week loser-reversal, i.e. an occupied mechanism wearing new
   clothes. Kill regardless of absolute results.
3. Estimation fragility: if splitting the pre-window in halves yields `β̂`
   estimates whose signs differ for any symbol, flag the coefficient set as
   unreliable and require the failure to be reported rather than patched by
   extending the estimation sample (extension would be post-hoc data mining).

### 5.9 Negative control

Set `β̂_i ≡ 0` for every symbol and rerun the identical machinery: `e_i,w =
r_i,w`, weights `-e_i,w/σ_e,i` with the same caps, clocks, fills, costs.

The claim under test is specifically that *factor-neutralised dislocations*
clear slowly while raw single-name losers behave differently. If the control
matches or beats the anchor, the value added came from ordinary short-horizon
loser reversal — an already-occupied mechanism (`H-XSECT-REVERSAL-*`) — and the
novelty claim collapses along with the causal attribution.

### 5.10 Nearest historical families and material deltas

Nearest families:

- `H-V9-TSTREND-v1` — per-name time-series rule on own trailing return
- `H-XSECT-REVERSAL-v1/v2`, `H-XSECT-REVERSAL-BREADTH-CRYPTO-v1` — rank of own
  trailing return, long/short tails
- `H-XSECT-MOM-v1`, `H-XSECT-FUNDING-*-v1` — rank-based composites of own
  return and/or funding

Material-delta claims, four dimensions asserted TRUE:

| Dimension | Nearest priors | This proposal | Material? |
|---|---|---|---|
| Economic source | Crowd-crowding from past price path; crowded-side carry burden; compressed-range expansion | Heterogeneous attention / information diffusion across linked assets plus stale-reference quoting; profit from slow closure of name-specific mispricing relative to peers | YES |
| Observable construction | Rank or dead-zone transform of the name's *own* trailing return; funding percentile ranks; bandwidth/Donchian percentiles | Return **residualised** against a leave-one-out peer composite via a pre-window regression coefficient; no V1–V9 family constructs any beta-, hedge-, index- or orthogonality-adjusted object (confirmed against the full family inventory) | YES |
| Selection-payoff geometry | Binary extreme-N tail baskets, equal-weighted, or absolute per-name dead-zone trend states | Per-symbol exposure that is **orthogonal to the panel by construction**; the book is factor-neutral, not merely cash-neutral; continuous weights, no selection set | YES |
| Counterparty/regime prediction | Momentum chasers, crowded leverage, breakout chasers, immediacy-demanding shock flow | Named two-sided friction: slow-attention investors acting on absolute moves, and makers quoting off stale references — an interaction between agents *across assets*, not within one | YES |

### 5.11 Sample feasibility

- Cell decisions: 52 weekly crossings × 10 symbols = **520 cell-weeks**;
  ~170 per chronological fold. Adequate.
- Independent time dimension: only **52 non-overlapping weekly periods**. That
  is the binding statistical ceiling: cross-fold and multiple-testing inference
  rests on at most 52 independent draws of the crossing-time dimension.
  Consequence stated now rather than discovered later — the §12 requirement of
  "multiple-testing proof" should be expected to resolve to an honest
  `UNAVAILABLE_FAIL_CLOSED` for this family given six scored cells and n=52;
  that is a reporting posture, not a hidden weakness.
- Features needed: ~350,343 completed symbol-bars plus 2,880×10 pre-window
  cells; warmup satisfied inside the audited range.
- Turnover/costs: weekly retargeting with slowly varying residuals; assuming
  ~35% of gross turned per week gives drag ≈ 0.35 × 12 bp × 52 ≈ 22 bp/year —
  negligible.
- Concentration: `CAP=0.30` bounds symbol contribution well under the 40% gate.

Verdict: **SIZEABLE** computationally, **MODERATE** statistically (52 effective
independent periods).

### 5.12 Audit cost estimate

Implementation + tests: **~5–7 agent-hours** (simplest of the three — pure
return algebra, no new field dependencies, no event handling). Runtime per
cell: seconds. The audit's critical item is confirming the pre-window
coefficients are computed once and pinned, plus asserting `leave-one-out`
composites exclude self correctly.

### 5.13 Anchor and neighbour configs

**ANCHOR — `M03-A`**: exactly §5.6 — `β̂_i` estimated on bar-frequency pre-window
pairs (2,880 observations, best-conditioned estimator of the horizon-invariant
sensitivity), residual `e = r_i − β̂_i · r̄_(−i)`, `σ_e,i` scaling, `CAP=0.30`,
unit gross, weekly Monday clock, one-week holding.

Declared assumption: the bar-frequency sensitivity transfers to weekly returns.
Stated openly; the neighbour is designed to probe precisely this assumption.

**NEIGHBOUR — `M03-N` (one theoretically-motivated change only)**: estimate
`β̂_i^week` by regressing **weekly-frequency** pre-window returns (4 paired
observations) instead of bar-frequency ones, leaving everything else identical.

Justification: the anchor optimises estimator precision at the wrong horizon;
the neighbour matches the horizon exactly but is estimated from almost no data.
Comparing them isolates whether the mechanism depends on accurate horizon-
matched sensitivities or merely on some sensible factor neutralisation — a
direct test of the declared assumption with zero additional parameters. If the
neighbour performs materially differently, horizon instability is established
and the family's characterisation is incomplete even if profitable.

---

## 6. Independence among the three proposals

| Axis | M01 Aggressor-Absorption | M02 Ticket-Signature | M03 Residual-Diffusion |
|---|---|---|---|
| Pillar | Microstructure liquidity provision/consumption | Agent-population composition | Cross-asset information diffusion |
| Raw observable | `taker_buy_quote_volume ÷ quote_volume` | `quote_volume ÷ count` (+ block return) | Peer-residualised `close`-to-`close` returns |
| Payoff geometry | Continuous monotone full-cross-section dollar-neutral book, always invested | Episodic two-sided single-name conditional, flat by default | Continuous factor-neutral book, orthogonal by construction |
| Clock class | Fixed daily UTC grid | **Event-driven** (trigger-dependent) | Fixed weekly Monday grid |
| Holding | 1 day, renewing | 7 calendar days | 1 week |
| Counterparty named | Taker crowd vs standing maker | Small-ticket retail vs patient holders | Slow-attention investors + stale-quote makers |
| Predictor type | Contemporaneous realised flow | Class identification of the marginal trader | Relative mispricing vs peer consensus |
| Negative control probes | Cross-sectional specificity | Composition vs magnitude | Factor neutralisation vs plain reversal |

Overlap risks disclosed for A5's novelty matrix:

1. M01 and M03 both emit a unit-gross, `CAP`-bounded, multi-leg book through the
   shared risk primitive. If both are selected together, the combined portfolio
   inherits overlapping gross and possibly correlated short-legs; margin and
   `symbol contribution` accounting should be assessed jointly rather than
   per-family. This is a resource question, not a novelty claim.
2. M01 and M03 both contain the words "reversal" and "contrarian". Their causal
   objects differ (aggressor inventory vs residual dislocation) and their
   observables share no field, but a critic could argue dimensional adjacency on
   the "economic source" axis. Disclosed; let A5 score it.
3. M02's epistemic weight rests on the `count` field being genuinely populated
   at the venue-source level (see §8 prerequisites).

---

## 7. Recommendation ordering for selection

Given the pre-score rubric weights (novelty/independence 35, mechanism/
falsifiability 25, PIT/data readiness 15, negative control 10, sample
feasibility 10, auditability 5), my own blind ranking, offered as input only:

1. **M03 Residual-Diffusion** — strongest raw-novelty (the inventory confirms
   zero prior residual/beta/index object), cheapest to audit, cleanest negative
   control, weakest expected effect size and a known statistical ceiling at
   n_weeks=52.
2. **M01 Aggressor-Absorption** — strongest sample and cleanest mechanism
   economics; consumes an unused exchange field; expects meaningful trend-regime
   drawdowns that make the `MDD ≤ 10%` gate genuinely uncertain.
3. **M02 Ticket-Signature** — most original observable and the only event-driven
   clock; thinnest event sample, explicitly disclosed.

If only one family can be selected overall, M03 maximises information gained
about whether a fundamentally new object-class works; M01 maximises the chance
of passing Stage A outright.

---

## 8. Prerequisites, limitations and UNAVAILABLE_FAIL_CLOSED items

### 8.1 Field-population attestations required before any scoring

| ID | Requirement | Blocking? | Applies to |
|---|---|---|---|
| `ATT-TAKER-QV` | A6 attests `taker_buy_quote_volume` is present and non-degenerate (non-null, varies) across all ten symbols' scored-window bars | Fail-closed | M01 |
| `ATT-COUNT` | A6 attests `count` is present, positive-sum per audited 96-bar block, and varies across blocks | Fail-closed | M02 |
| `ATT-QUOTEV` | A6 attests `quote_volume` is positive for effectively all scored bars | Fail-closed | M01, M02 |
| `ATT-SETTLE` | A6 confirms settled-funding timestamps are exchange-stamped and complete per manifest (`1,095` / `2,189`) | Contextual | cost accrual for all three |

I did not inspect these values (bar/funding contents outside permitted reading
for this wave). If any attestation fails, the affected proposal becomes
`UNAVAILABLE_FAIL_CLOSED` and must not be substituted with a proxy — substitution
would silently change the mechanism.

### 8.2 Honest multiple-testing posture

With ≤2 families and 3 scored cells each, plus ≤3 chronological folds and at
most 365 (M01) / 52 (M03) independent crossing times, a formal multiplicity
proof will not be derivable. All three proposals should expect to publish
`UNAVAILABLE_FAIL_CLOSED: MULTIPLE_TESTING_PROOF_NOT_DERIVABLE` with the exact
effective-sample accounting rather than assert a deflated significance claim.
Flagged now so it is not discovered as a surprise during scoring.

### 8.3 Data regions outside the audited census

Bar files nominally extend back to about `2024-08-21`, but the gap census
covers only the 30-day pre-window plus the scored window. All three proposals
were deliberately constrained so that **every** consumed feature lies inside
the audited range. No proposal requires pre-`2025-07-22` data. Should anyone
later propose extending reference windows backwards for sample reasons, that
requires an A6 coverage attestation first and is not part of these designs.

### 8.4 Explicit non-goals

- No open-interest or mark-price usage: overlays cover only 7 of 10 symbols for
  30 days (`UNAVAILABLE_FAIL_CLOSED` for any panel-wide use).
- No equity/TradFi extension: separate contract per PLAN §3.
- No BTC consumption as feature or hedge: manifest forbids it in ranks,
  weights and PnL.
- No volatility targeting, regime filters, funding gates, symbol substitutions
  or post-result filtering on any of the three designs.
- No parameter search anywhere; each family ships exactly anchor + neighbour +
  negative control.

---

## 9. Deliverable map

| File | Role |
|---|---|
| `research/audits/v10/proposals/a8_proposals_v10.md` | human-readable proposal set (this file) |
| `research/audits/v10/proposals/a8_proposals_v10.json` | machine-parseable mirror with identical semantics |

Budget impact of this wave: **0 scored cells consumed**. Proposals only.
