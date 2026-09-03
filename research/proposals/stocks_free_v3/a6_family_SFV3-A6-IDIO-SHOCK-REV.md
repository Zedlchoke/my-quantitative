# SFV3-A6-IDIO-SHOCK-REV — Market-adjusted idiosyncratic shock reversal in sector ETFs

Lane: A6 (blind proposal lane 3), STOCKS-FREE-V3 Phase D1.
Frozen 2026-09-03 from `STOCKS_FREE_V3_BLIND_PACKET_SHA`. Document only —
no returns, PnL, PF, Sharpe, rankings or correlations were computed; no market
data, no scored outcomes, and no other lane's files were opened.

## 1. Family identity, primary source, and ETF-market mechanism

- **family_id:** `SFV3-A6-IDIO-SHOCK-REV`
- **Mechanism class:** event-contingent liquidity-provision reversal after
  market-adjusted idiosyncratic sector shocks (priority search space:
  market-adjusted idiosyncratic shock reversal; the SPY return is removed
  before any threshold is evaluated).

**Primary-source claim.** Bruce Lehmann (1990), "Fads, Martingales, and Market
Efficiency", *Quarterly Journal of Economics* 105(1): short-horizon reversal
profits are statistically robust and are attributed to transitory
price pressure from liquidity/overreaction trading rather than to information.
Corroborating primary source: Narasimhan Jegadeesh (1990), "Evidence of
Predictable Behavior of Security Returns", *Journal of Finance* 45(3)
(monthly-horizon reversal; the horizon over which transitory components
unwind). Both papers locate the effect at the weekly-to-monthly horizon,
which fixes the family's holding clock below. These are priors on mechanism,
not profitability evidence.

**ETF-market mechanism story.** When one sector ETF falls far over a few
sessions *relative to SPY*, the likely marginal seller is flow-motivated
(rotation redemptions, risk-limit driven selling, rebalancing of satellite
allocations) — flow whose urgency comes from mandates, not from sector
fundamentals. In the ETF wrapper this flow arrives as redemptions and forced
hedges that authorized participants and market makers must absorb at
prevailing prices. Because the shock is *idiosyncratic* (SPY's return removed),
it is not compensation for market-wide risk; the residual is a transitory
price concession to whoever supplies liquidity. The mechanism predicts a
partial bounce over the following 2–4 weeks. The market-return leg of the
trigger and the non-systemic-market filter (section 4) exist precisely so the
trade cannot be "buy the market's dip".

## 2. Expected counterparty and falsifiable expected sign

- **Counterparty:** flow-motivated sellers — rotation/redemption flow and
  risk-limit sellers who must transact promptly and accept a price below
  fundamental value because breaching a mandate or a risk limit costs more
  than the concession; on the other side, APs/market makers who absorb the
  inventory and demand a premium realized as the post-shock bounce.
- **Falsifiable expected sign:** after sector i's 5-session idiosyncratic
  return (5-session issuer-TR of i minus contemporaneous 5-session
  issuer-TR of SPY) is at or below a fixed deep threshold, sector i's
  forward after-cost total return over a fixed 20-session hold exceeds the
  risk-matched benchmark: **anchor incremental alpha > 0**, expected in every
  fold that contains events. If deep idiosyncratic sector shocks contain no
  transitory component (fully informative shocks), forward returns are flat
  to negative and the family must die.

## 3. Required fields and PIT availability

Only already-authorized fields:

- daily raw OHLCV (closes only), official split factors, official cash
  distributions (issuer-TR path), `US_EQUITY_REGULAR_V1` calendar.
- The trigger at session T uses only closes of completed sessions T−4..T for
  the sector and SPY; execution at T+1's close (canonical factory fill
  event). **PIT availability is exact** — two issuer-TR series and a fixed
  threshold; no estimation window beyond the fixed 5-session formation.

No earnings, analyst, borrow, flow, quote/spread, options or fundamental
fields; no new accounts, paid data, or network fetch.

## 4. Universe, formation, trigger, holding, decision and execution clocks

- **Universe (tradable legs):** the 10 sector ETFs `XLK XLE XLF XLV XLI XLP
  XLY XLU XLB XLRE`. **SPY is never a tradable leg** — it serves only as the
  market-adjustment series (structurally separating the family from any
  long-SPY result).
- **Formation:** for each sector i and session T,
  `idio5(i,T) = TR5(i,T) − TR5(SPY,T)`, where `TR5` is the compounded
  issuer-TR over sessions T−4..T (split factors + distributions).
- **Trigger (fixed constants):** enter-eligible at T iff
  `idio5(i,T) <= −5.0%` AND `TR5(SPY,T) >= −2.0%`.
  Reasoning for the constants: sector-ETF idiosyncratic daily variation is
  of order 0.6–0.9%, so a 5-session idio move of −5.0% is a ~3σ idio event —
  deep enough to indicate forced/one-sided flow rather than ordinary noise,
  and the depth is chosen so that expected event counts stay inside the
  turnover ceiling (section 6). The SPY filter keeps the trigger
  *non-systemic*: during a market-wide crash the idio decomposition is
  unstable and the subsequent "bounce" would be crash beta, not liquidity
  provision; excluding systemic windows sharpens the mechanism and prevents
  event clustering in Mar-2020-class episodes.
- **Position machinery (fixed):** at most **2 concurrent sector positions**,
  each at gross weight **0.40** (max book gross 0.80). If more than two
  sectors trigger on the same session, fills are taken in **lexicographic
  symbol order** up to capacity — a deterministic, return-independent
  tie-break (deliberately NOT a top-K by signal depth; see section 12).
  A sector with an open position cannot re-trigger; re-entry is allowed only
  after its exit.
- **Holding:** exactly **20 sessions** from entry fill to exit fill
  (Jegadeesh's monthly reversal horizon; Lehmann's weekly horizon is the
  neighbour arm's). Entry fill at close of T+1; exit fill at close of
  session T+1+20.
- **Decision clock:** trigger state evaluated at each session-T close from
  completed sessions only; execution at the next session's close.
  Fail-closed on missing sessions (loader gap contract): a sector with an
  observation gap cannot form a trigger.

## 5. Long/cash target construction and cash semantics

- Target book at any session: 0, 1 or 2 sector legs at 0.40 each; **CASH**
  is the residual (1.0 − gross), never a tradable leg, never counted in
  turnover, costs charged exactly once per fill (canonical factory
  semantics). No leverage, gross <= 0.80.
- Positions are initiated and liquidated only at the fixed session clocks
  above; no stop-loss, no profit-taking, no re-entry stacking, no intra-hold
  rebalancing.

## 6. Turnover, capacity, cost, distribution and split handling

- **Turnover (schedule-only):** each event costs exactly 0.80 two-way
  (0.40 entry + 0.40 exit). Feasibility inside the 6.0x/yr ceiling therefore
  requires <= 7 events/yr on average; the ~3σ depth, the non-systemic SPY
  filter, and the no-stacking/cooldown rules are all chosen toward that.
  The schedule-only measurement **before any scoring** is the authority: if
  the measured schedule exceeds 6.0x/yr the family is infeasible as frozen
  and is not repaired (a threshold change post-hoc would be tuning).
- **Capacity:** single-sector ETF legs are deep cash-market instruments; the
  0.40 leg weight at research scale is non-binding.
- **Cost:** base 10 bps/side on ~2–5 two-way/yr ≈ 0.2–0.5%/yr of equity;
  stress 20 bps ≈ 0.4–1.0%/yr. The bounce premium must clear stress costs
  — that is what the stress arm measures.
- **Distributions and splits:** issuer-TR accounting path on every leg;
  fills at raw prices; official split factors (2025-12-05 conflict class
  neutralized per packet lesson 6).

## 7. Expected behaviour against the four benchmarks

- **FLAT_HARD:** expected positive over S0 in aggregate but episodic — the
  book is mostly cash and its PnL arrives in event bunches; flat-negative
  sub-spans are expected and not evidence against the mechanism.
- **SPY total return:** expected to trail SPY TR in bull folds by design
  (average gross far below 1.0, mostly cash); raw comparison is a beta
  comparison, not a test.
- **Equal-weight sector TR:** same as SPY TR — trailing in bulls is the
  expected shape of a low-gross event book.
- **Risk-matched SPY (the only hurdle):** the benchmark replicates the arm's
  ex-ante gross/vol rule, so **positive incremental alpha per event-bearing
  fold is the entire claim**: it can only arise if post-shock idio bounce
  exists. Expected: alpha > 0 in >= 2/3 folds, with returns distributed
  across events rather than concentrated in one fold.

## 8. Anchor, neighbour, causal negative control

| Arm | ID | Definition |
|---|---|---|
| Anchor | `SFV3-A6-IDIO-SHOCK-REV-A` | Trigger `idio5 <= −5.0%` with `TR5(SPY) >= −2.0%`; 2 slots x 0.40; 20-session hold. |
| Neighbour | `SFV3-A6-IDIO-SHOCK-REV-N` | Same trigger, same machinery, **5-session hold** (Lehmann's weekly reversal horizon). |
| Control | `SFV3-A6-IDIO-SHOCK-REV-C` | **Opposite ranking**: mirror trigger `idio5 >= +5.0%` with `TR5(SPY) <= +2.0%`; identical slots, sizes, lexicographic fill order, and 20-session hold — long the idio *surge* under symmetric non-systemic conditions. |

- **Neighbour identity and role:** distinct stable identity (different holding
  clock, same trigger). Theoretically justified: Lehmann (1990) locates
  reversal at the weekly horizon, Jegadeesh (1990) at the monthly horizon —
  if the transitory-pressure mechanism is real, both horizons should show
  positive alpha, with the neighbour potentially stronger earlier in the
  holding window. Support rule: neighbour incremental alpha > 0 and same
  sign as anchor in >= 2/3 folds. If the neighbour is negative while the
  anchor is positive, the "transitory pressure" story is wrong (a
  pressure that decays within 5 sessions is not transitory pressure) and
  the family dies.
- **Control identity and role:** the mirror trigger has the same depth, the
  same symmetric non-systemic filter, and the same book machinery — every
  difference between anchor and control is the *sign of the idio shock*. If
  idio surges were equally followed by positive drift, the observed pattern
  would be sector-level tail drift (e.g. short-horizon industry momentum),
  not liquidity-provision reversal. Mechanism truth predicts control alpha
  ≈ 0 or negative.
- **Control falsification semantics (packet wording):** control falsifies the
  no-mechanism null when its alpha is opposite-signed vs the anchor or
  |control alpha| < 50% of |anchor alpha|. Kill condition is stated in
  section 11.

## 9. Incremental mechanism test (alpha vs equity beta)

Per scored fold f, via the frozen `compute_fold_alpha` contract:

```
incremental_alpha(f) = R_strategy_after_cost(f) − R_risk_matched_SPY(f)
```

- Frozen ex-ante gross/vol rule for the `RISK_MATCHED_SPY_CONTEXT` builder:
  `target_daily_vol = 0.005` (reasoned: half of SPY's long-run ~1% daily
  volatility; a literature-level constant, not a data measurement),
  `lookback_sessions = 63`, `min_gross = 0.10`, `max_gross = 0.80`. The
  `min_gross` floor is deliberately conservative: the benchmark keeps a
  small exposure even when the arm is fully in cash, so the arm's alpha bar
  is *harder*, not easier. All scale inputs are SPY returns strictly before
  session d.
- The trigger already removes SPY's return from the signal, SPY is not
  tradable, and systemic windows are filtered out — three independent
  structural barriers against a beta explanation. Under the frozen
  construction a beta-only arm yields alpha ≈ 0, so positive alpha in
  >= 2/3 folds is evidence of the post-shock idio bounce itself. Raw PnL
  and comparisons against SPY TR / EW sector TR are diagnostics, never
  pass-eligible.

## 10. Drop-one-ETF and drop-one-fold expectations

- **Drop-one-ETF:** the mechanism is claimed panel-wide, not in one sector.
  Expected: overall incremental alpha stays positive after removing any
  single sector from the tradable set; no single ETF should supply > 35% of
  positive PnL (gate). Predeclared risk: if the effect genuinely lived only
  in one sector's episodes (e.g. commodity-cycle events in XLE), the
  drop-one and concentration gates *should* kill the family — a
  single-sector mechanism is not the claimed panel mechanism.
- **Drop-one-fold:** expected positive alpha in each event-bearing fold and
  no fold carrying > 50% of positive PnL. **Predeclared evidentiary risk:**
  the non-systemic filter plus ~3σ depth may leave a fold with very few or
  zero events (a fold with zero entry decisions is insufficient evidence and
  the family fails the packet's sufficient-decisions gate). That is an
  accepted, predeclared outcome of the fixed constants — no re-tuning.

## 11. Exact falsification rule

The family is **killed** if ANY of the following is observed after scoring:

1. Anchor mean incremental alpha <= 0, or positive in fewer than 2/3
   event-bearing folds (no transitory component in deep idio shocks).
2. Control `...-C` does not falsify: control alpha same sign as anchor AND
   |control alpha| >= 50% of |anchor alpha| — i.e. idio surges drift like
   idio crashes bounce, so the mechanism is tail drift, not reversal.
3. Neighbour `...-N` alpha opposite-signed to the anchor in >= 2/3 folds
   (weekly horizon loses where monthly wins — inconsistent with a
   decaying transitory component).
4. Stress PnL <= 0 or stress PF < 1.00 (bounce does not survive 20 bps).
5. Schedule-only turnover > 6.0 two-way/yr; or max fold MDD > 15%; or any
   fold PF < 0.80; or zero-entry decisions in any fold; or drop-one-ETF /
   drop-one-fold survival failure.

No post-hoc threshold change, filter relaxation, horizon change, or sector
substitution is permitted after the first scored metric (PLAN section 12).

## 12. Ancestry comparison — why this is not a rescue

- **Not A4 / ordinary cross-sectional momentum:** no ranking, no top-K, no
  lookback relative-strength sort. The trigger is an absolute idio threshold
  in the *opposite* direction of momentum (buy weakness, never strength),
  with a deterministic lexicographic tie-break chosen specifically to avoid
  signal-ranked selection.
- **Not A5 / time-series trend, SMA/EMA, or vol-target defensive rotation:**
  no trend filter, no moving average, no volatility targeting; the arm
  *adds* risk after bad idio shocks instead of de-risking after weakness,
  and its state is an event clock, not a defensive regime.
- **Not a selected-ETF rescue:** all 10 sector ETFs are permanently eligible;
  nothing is chosen after any outcome.
- **Not long-SPY-beta dressed up:** the signal subtracts SPY's own 5-session
  return, SPY is not a tradable leg, systemic SPY windows are excluded, and
  the risk-matched benchmark removes residual beta — a beta-only arm
  mechanically earns alpha ≈ 0 under the frozen construction.
- **Not an indicator grid:** one trigger, one filter, one holding clock, one
  slot size — every constant is a fixed, reasoned number stated ex ante.

## 13. Implementation estimate

Reuse: `research.assets.stocks.loader.BarLoader`; issuer-TR daily series from
`research.stocks_free_v3.benchmarks` (`issuer_total_return_daily`,
`split_adjusted_closes`); accounting from `research.assets.stocks.factory`
(`value_book`, `etf_leg_turnover`, `fill_cost`, `normalize_entry_targets`);
alpha from `research.stocks_free_v3.incremental` (`compute_fold_alpha`,
`FoldAlphaReport`).

New code: one event state machine + schedule module (~300 LOC): TR5 series,
trigger evaluation, slot bookkeeping (concurrency cap, per-sector
no-stacking, lexicographic fill order, 20/5-session exit clocks), arm
configs and digests; golden tests on synthetic series (~250 LOC) covering
clipped triggers, slot contention, cooldowns, and exit-clock arithmetic.
Effort: **3–4 engineer-days including tests**. Risk: MEDIUM — the state
machine is the main surface; the schedule-only turnover measurement must be
run before scoring and is a hard feasibility gate for the family.

## 14. Blinding statement

This document was written without reading any scored outcome, any V2 arm
PnL, any file under `research/control/stocks_free_v2_run/`, `research/audits/`,
`tests/` numeric fixtures or `results/`, without reading the A4/A5 lanes, and
without computing any return, PnL, PF, Sharpe, ranking or correlation on any
data. All constants above are reasoned ex ante from the packet's constraints
and from the cited literature, not from any measurement of the cohort.
