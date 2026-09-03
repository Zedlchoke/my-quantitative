# SFV3-A5-IDIO-SHOCK-REVERSAL — blind mechanism proposal (lane A5, proposal 1 of 2)

- producer: A5 (blind proposal lane 2)
- frozen input: `research/proposals/stocks_free_v3/blind_input_packet.json`
  (sha256 `034cf4d657be41450b5d5e11f5b09613fac2217742303fc724dc168549b78106`)
- worktree HEAD at writing: `d388f8c9ea180c3e127fce811bcbfc3e9c6028a6`
- blinding statement: no market data read, no returns/PnL/PF/Sharpe/rankings/correlations computed,
  no V2 outcomes, no other-lane directories opened. All quantity statements below are
  literature-anchored priors and design arithmetic, never measurements.
- sources used here are priors, not profitability evidence (PLAN section 10).
- search space used (packet, not mandatory): market-adjusted idiosyncratic shock reversal
  with the market return removed before the trigger.

## 1. Family identity, primary-source claim, ETF-market mechanism

**family_id**: `SFV3-A5-IDIO-SHOCK-REVERSAL`

**Primary-source claims** (all real, citable; described, not quoted):

- Lehmann, B. (1990), "Fads, Martingales, and Market Efficiency", *Quarterly Journal of
  Economics* 105(1). Documents that a contrarian strategy built from period returns
  demeaned against the cross-section (i.e., market-adjusted, not raw) earns economically
  significant positive returns at short horizons — the canonical statement that the
  *market-adjusted* extreme move, not the raw move, carries predictable reversion.
- Jegadeesh, N. (1990), "Evidence of Predictable Behavior of Security Returns",
  *Journal of Finance* 45(3). Documents significant short-horizon reversal of extreme
  losers, distinct from longer-horizon momentum.
- Lo, A. and MacKinlay, A.C. (1990), "When Are Contrarian Profits Due to Stock Market
  Overreaction?", *Review of Financial Studies* 3(2). Decomposes contrarian profit into
  own-autocovariance (overreaction/reversal), cross-autocovariance (lead-lag), and a
  mean/variance term. This family claims ONLY the own-shock term; the cross term is a
  separate family (see companion proposal `SFV3-A5-MKT-SHOCK-DIFFUSION`).
- Nagel, S. (2012), "Evaporating Liquidity", *Review of Financial Studies* 25(7).
  Documents short-term reversal returns as compensation to liquidity providers, which
  spike precisely when liquidity evaporates (high volatility, heavy one-directional
  flow days) — the mechanism predicts our events cluster in stressed periods.
- Cheng, M. and Madhavan, A. (2009), "The Dynamics of Leveraged and Inverse
  Exchange-Traded Funds", *Journal of Investment Management*. Documents that daily-reset
  leveraged/inverse ETFs generate end-of-day rebalancing trades in the direction of the
  day's move (buy strength, sell weakness) — a mechanical, non-fundamental flow source
  in the ETF complex that amplifies same-day moves and must unwind.

**ETF-market mechanism story.** A 1x sector ETF's single-day move decomposes into a
market component and an idiosyncratic component. On days when the idiosyncratic
component is extreme (3+ own-vol units after removing the market), part of the move is
non-fundamental transitory pressure: daily-reset leveraged/inverse product hedging that
must trade into the move at the close (Cheng-Madhavan), stop-loss and margin sellers,
and fast-money flow. AP creation/redemption and allocator review cycles resolve over the
following sessions, so the transitory component retraces. The retrace is the liquidity
provider's compensation (Nagel). Because the trigger is beta-orthogonalized, the tradable
claim is pure idiosyncratic recovery, expressible long/cash by buying the shocked sector.

## 2. Expected counterparty and falsifiable expected sign

**Counterparty.** Constraint-driven sellers of the shocked sector on the event day:
leveraged/inverse product hedging desks (mechanically must trade with the move at the
close), stop-loss/margin sellers, and horizon-constrained fast money. They accept a
transitorily bad price because their constraints are intraday or mandate-driven, while
the reversion accrues over subsequent sessions — the classic liquidity-provision wedge.

**Falsifiable expected sign.** For sectors entering on an extreme negative
market-adjusted shock (z <= -3.0 as defined in section 4), the mean total return of the
held sector over the 5-session holding window, minus its beta-times-SPY return over the
same window, is strictly positive after costs. If the realized sign is zero or negative
(after-cost), the mechanism (transitory idio overshoot + liquidity-provision
compensation) is absent in this cohort/window and the family dies (section 11).

## 3. Required fields and PIT availability

Only packet-allowed fields are used:

| field | use | PIT availability |
|---|---|---|
| daily raw OHLCV per ETF | closes for returns; opens for execution | provider daily bar, completed regular sessions only |
| daily volume | NOT USED by this family | n/a |
| official split factors | issuer-TR return construction; fill accounting | issuer/agent records |
| official cash distributions | issuer-TR return construction; accounting | issuer/agent records |
| US_EQUITY_REGULAR_V1 calendar | session indexing, rolling windows, budget year | frozen calendar |

No earnings, analyst, borrow, quote/spread, fundamentals, flow, or options data. All
signal inputs are computed from completed sessions through session T only; the signal is
executable at the NEXT session's event (section 4). Ex-dividend drops never masquerade as
idio shocks because signal returns are built on the issuer-TR path (raw + official
distributions + official splits), while fills occur at raw prices per the packet's
corporate-action contract.

## 4. Universe, formation, holding, decision and execution clocks

**Universe.** All 11 cohort members are loaded. SPY serves only as the market factor and
benchmark symbol (its idio residual vs itself is identically zero). The trigger and
selection universe is the 10 sector ETFs: XLK XLE XLF XLV XLI XLP XLY XLU XLB XLRE.

**Formation (exact, frozen constants).** On each completed session t:

- r_i,s = issuer-TR daily return of ETF i (SPY included as factor) from the issuer-TR path.
- beta_i(t) = OLS slope of r_i on r_SPY over the trailing 60 completed sessions
  [t-59 .. t], inclusive of t.
- epsilon_i,s(t) = r_i,s - beta_i(t) * r_SPY,s for s in that window;
  sigma_i(t) = population standard deviation (ddof=0) of {epsilon_i,s(t)}.
- z_i(t) = (r_i,t - beta_i(t) * r_SPY,t) / sigma_i(t).

Trigger: z_i(t) <= -3.0 (extreme negative market-adjusted shock). Selection among
simultaneous triggers: smallest z_i(t); exact tie broken by alphabetically first symbol.
No other thresholds, lookbacks, or grids exist anywhere in the family.

**Holding.** Anchor/control: exactly 5 sessions. Neighbour: exactly 10 sessions (section 8).

**Decision and execution clocks.** One decision pass per session, evaluated after that
session's close using data through t (completed-session PIT). Entry executes at the
regular-session OPEN of t+1. Exit executes at the regular-session open of session
entry+6 (anchor), entry+11 (neighbour) — i.e., the position spans 5 (10) full sessions.
A trigger evaluated at the close of the exit-eve session may enter at the same open as
the exit (same-open switch; both orders were decided at the prior close, so PIT-clean).

**Concurrency and budget.** Concurrency 1: while a position is open, all triggers are
ignored. Episode budget: at most 5 new entries in any rolling 252-session window (counted
by entry session, entries rolling off after 252 sessions). Episodes are taken in strict
chronological order; no retrospective re-ranking. Constants 5/252/1 are fixed.

## 5. Long/cash target construction and cash semantics

- Target book when an episode is live: 0.50 in the selected sector ETF, 0.50 in the
  explicit CASH leg. Otherwise: 1.00 CASH. No leverage; gross exposure <= 1.0 always.
- CASH is an explicit leg handled canonically by the harness: zero yield assumed, never
  counted in tradable-leg turnover, valued identically by sidecar and canonical valuation
  (packet accounting lesson: CASH is not a tradable leg; costs are charged exactly once).
- Weights are deterministic step functions of the state machine in section 4; no
  continuous rebalancing, no drift correction between events (hold-to-exit).

## 6. Turnover, capacity, cost, distribution/split handling

**Turnover.** Each episode trades buy 0.5 (entry open) and sell 0.5 (exit open):
1.0 gross-units of purchases+sales per episode. With the 5-episode/252-session budget:
<= 5.0x two-way per year under the most conservative counting (purchases + sales summed),
2.5x under the (P+S)/2 convention — inside the frozen 6.0x/yr ceiling under either
reading, with margin. Same-open switches count both legs. Neighbour (10-session holds):
same budget bound, realized turnover lower because concurrency blocks more trigger days.

**Capacity.** Daily ETF cohort, schedule-only feasibility claim per the packet; no
capacity claim beyond schedule feasibility. The binding feasibility risk is trigger
frequency, not size; the episode budget is the schedule governor.

**Cost.** Base 10 bps/side on traded notional: 10 bps of book equity per episode round
trip (0.5 x 2 x 10 bps). Stress 20 bps/side: 20 bps of equity per episode. Expected
episode-level gross edge (literature-scale prior: reversion of a fraction of a 3-sigma
idio shock, order tens of bps on position notional) must clear the stress cost for the
family to be viable — the stress gate tests exactly this.

**Distributions/splits.** Fills at raw prices; distributions on held positions reinvest
via the issuer-TR path for accounting; splits via official factors. Issuer records are
the accounting authority (packet lesson on the 2025-12-05 provider/issuer split conflict:
provider `adjust=all` flags lose; issuer-TR reconstruction wins). Signals use issuer-TR
returns, so distributions never create synthetic shocks.

## 7. Expected behaviour against the four frozen benchmarks

- **Flat (hard benchmark).** Expected positive after-cost expectancy overall, with the
  honest caveat that in a quiet year the budget may take 2-4 episodes and net expectancy
  can be slightly negative for that year; the mechanism claim is averaged over folds.
- **SPY TR.** Expected BELOW SPY TR in absolute terms in most folds: the book is 0.5
  gross on roughly 2-5% of sessions. The family does not compete on absolute return and
  must not be scored as if it did.
- **Equal-weight sector TR.** Below, same reasoning.
- **Risk-matched SPY (the target).** The arm's frozen gross/vol rule is declared as a
  constant-scale rule (min_gross = max_gross = 0.025 for anchor/control; 0.05 for the
  10-session neighbour; derivation: 5 episodes x 5 sessions x 0.5 gross / 252 sessions =
  0.0248, and x2 holding = 0.0496), so the benchmark is SPY TR scaled ex ante at the
  arm's expected average gross. Expected: positive after-cost excess in >= 2/3 folds and
  positive incremental mechanism alpha — the arm must beat always-invested SPY per unit
  of average exposure, which is precisely the beta/alpha separation the contract demands.

## 8. Anchor, neighbour, causal negative control

- **Anchor** `SFV3-A5-IDIO-SHOCK-REVERSAL/A1`: z <= -3.0 trigger, hold 5 sessions,
  0.5 gross, budget 5/252, concurrency 1. Claim: negative idio shocks revert.
- **Neighbour** `.../N1`: identical trigger, selection, budget, clock; hold 10 sessions.
  Theory: liquidity-provision compensation accrues as transitory pressure unwinds over
  days-to-weeks (Nagel; Lehmann's weekly horizon), so the edge should persist or grow
  with the longer window. It also guards the anchor against a K=5 knife-edge artifact:
  expected same-sign alpha with roughly twice the exposure-days.
- **Causal negative control** `.../C1`: OPPOSITE trigger — z_i(t) >= +3.0 (extreme
  positive idio shock), select largest z, identical holding, clock, budget, gross.
  Mechanism-derived prediction: positive idio overshoots also revert, so the LONG control
  must lose to the risk-matched benchmark (incremental alpha <= 0). This control
  falsifies by construction: if C1 instead earns positive alpha comparable to A1's, the
  edge is shock-sign-agnostic — generic post-event drift / attention premium (e.g., a
  high-visibility-volume premium), NOT overreaction reversion — and the family is dead.
  The anchor and control are stable, distinct identities: same plumbing, opposite event
  sign, opposite predicted alpha sign.

## 9. Incremental mechanism test (alpha vs equity beta)

Per fold, for each scored arm: incremental alpha = after-cost strategy return minus the
risk-matched SPY benchmark return (`benchmarks.build_risk_matched_spy` with the arm's
frozen constant-scale `VolScalingRule`; `incremental.compute_fold_alpha` with
`require_beta_isolation=True`). Because the trigger is beta-orthogonalized ex ante and
the benchmark holds SPY at the arm's average gross on ALL sessions, a positive excess
cannot come from equity beta: it can only come from the timed, idio-selected episodes
beating unconditional market exposure per unit of average gross. Pass shape (packet
contract): anchor positive in >= 2/3 folds and positive overall; neighbour same sign
(supports mechanism); control opposite sign or |alpha| < 50% of |anchor alpha|.

## 10. Drop-one-ETF and drop-one-fold expectations

**Drop-one-ETF.** Shocks are sigma-standardized per ETF, so trigger supply is roughly
uniform across the 10 selection names by construction; no single sector is structurally
favored. Expectation: the family survives removing any one ETF (its episodes are replaced
by other names' episodes over the remaining budget capacity). Real risk, stated plainly:
in stressed regimes (e.g., fold 1's dislocations) a tech or energy cluster could dominate
episode PnL; if dropping the largest-held ETF kills the family, that is a genuine
concentration failure and the family should die with it (packet gate: no single ETF >
35% of positive PnL/risk).

**Drop-one-fold.** The rolling annual budget bounds any fold's episode count
(<= ~12-13 entries per 2.4-year fold), so fold concentration is structurally capped, but
not equalized: per Nagel the events cluster in stressed periods, so fold 1
(2018-04..2020-09, containing the 2018 Q4 and COVID shocks) is expected to be the
strongest fold and the most likely to be indispensable. Pre-registered expectation:
positive expectancy in all three folds is possible but NOT required; the family is
expected to survive drop-one-fold if at least one of folds 2 or 3 carries roughly half
the anchor's alpha. If the family needs fold 1 alone to pass any gate, it fails
drop-one-fold and is rejected — that outcome is informative (crisis-only liquidity
provision is not a tradeable family under this contract).

## 11. Exact falsification rule and implementation estimate

**Falsification rule (exact, any one kills the family):**

1. Anchor incremental alpha <= 0 overall, or positive in < 2/3 folds.
2. Control C1 incremental alpha > 0, or |C1 alpha| >= 0.5 x |A1 alpha| — i.e., failing
   the packet's "opposite sign OR < 50%" gate proves the edge is not reversion.
3. Neighbour N1 incremental alpha strictly opposite in sign to A1's (effect is a
   holding-clock artifact, not a recovery process).
4. Anchor after-cost expectancy <= 0, or stress PF < 1.00 at 20 bps/side.
5. Realized two-way turnover > 6.0x/yr, or any episode-budget/concurrency breach
   (schedule infeasibility).
6. Any preregistered Stage-A gate failure (after-cost expectancy, PF >= 1.10, >= 2/3
   folds positive, no populated fold PF < 0.80, MDD <= 15%/fold, largest positive-fold
   share <= 50%, single-ETF contribution <= 35%, drop-one-ETF, drop-one-fold, exact
   independent reproduction, zero unresolved HIGH/CRITICAL audit objections).

**Implementation estimate.**

- Reuse: `assets/stocks/loader.BarLoader` (raw OHLCV/splits/distributions),
  `benchmarks.issuer_total_return_daily`, `benchmarks.split_adjusted_closes`,
  `benchmarks.build_risk_matched_spy` (accepts the constant-scale rule; min==max passes
  the existing validation), `factory.etf_leg_turnover/fill_cost/value_book`,
  `factory.select_drop_one_symbol`, `incremental.compute_fold_alpha`.
- New (~350-450 LOC + ~350 LOC tests): `research/stocks_free_v3/event_arm_base.py`
  (rolling beta/sigma estimators with ddof=0, trigger/selection, concurrency-1 and
  rolling-budget ledger, same-open switch, emission of canonical target-weight schedule)
  plus the thin A1/N1/C1 configuration heads. Shared with the companion family.
- Effort: ~3 engineer-days including golden tests and reproduction fixtures for the
  family (about 1 day marginal given the shared base).

## 12. Ancestry comparison (why this is not a closed family)

- **Not `A4_XSEC_ETF_RELATIVE_MOMENTUM` or any cross-sectional momentum**: no trailing
  multi-period return ranking, no top-K, no persistent holding of relative winners; the
  trigger is a single-day, beta-orthogonalized event and the predicted return sign
  (reversal) is the OPPOSITE of momentum's (continuation). Selection among simultaneous
  same-day triggers orders event severity, not past performance. The V2 momentum family
  died because its bottom-ranked control reproduced the anchor; this family's control is
  sign-inverted so that reproducing the anchor kills it by construction.
- **Not `A5-SFV2-TREND-DEFENSIVE` or any trend/SMA/EMA/vol-target rotation**: no price
  level vs average, no trend filter, no defensive de-risking schedule, no vol-targeting
  of exposure; exposure is 0.5-or-nothing around rare fixed-threshold events.
- **Not long-SPY/sector beta**: beta is removed from the trigger ex ante; the
  constant-scale risk-matched benchmark and the sign-inverted control separate any
  residual beta from the claimed idio reversion (section 9).
- **Not a selected-ETF rescue**: the selection universe is the full 10-sector set under a
  frozen rule fixed before any scoring; no chosen subsets, no post-hoc thresholds.
- **Not an indicator grid**: one state variable (z), one threshold (3.0), one clock
  (5/10 sessions), one budget — every constant reasoned and frozen.
- **Not crypto-ancestry recycling**: unlike funding-carry or funding-crowd MR, the signal
  source is exchange price history only; no perp/funding construct exists here.
