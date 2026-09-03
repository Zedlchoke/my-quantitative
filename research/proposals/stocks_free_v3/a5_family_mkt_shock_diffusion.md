# SFV3-A5-MKT-SHOCK-DIFFUSION — blind mechanism proposal (lane A5, proposal 2 of 2)

- producer: A5 (blind proposal lane 2)
- frozen input: `research/proposals/stocks_free_v3/blind_input_packet.json`
  (sha256 `034cf4d657be41450b5d5e11f5b09613fac2217742303fc724dc168549b78106`)
- worktree HEAD at writing: `d388f8c9ea180c3e127fce811bcbfc3e9c6028a6`
- blinding statement: no market data read, no returns/PnL/PF/Sharpe/rankings/correlations
  computed, no V2 outcomes, no other-lane directories opened. All quantity statements
  below are literature-anchored priors and design arithmetic, never measurements.
- sources used here are priors, not profitability evidence (PLAN section 10).
- relation to the packet's search spaces: this is the CROSS-sectional (lead-lag) term of
  the shock literature — the complement of the own-shock reversal term proposed in the
  companion family `SFV3-A5-IDIO-SHOCK-REVERSAL`; the two share estimation plumbing but
  have different triggers, different predicted signs, and different controls.

## 1. Family identity, primary-source claim, ETF-market mechanism

**family_id**: `SFV3-A5-MKT-SHOCK-DIFFUSION`

**Primary-source claims** (all real, citable; described, not quoted):

- Hou, K. (2007), "Industry Information Diffusion and the Lead-Lag Effect in Stock
  Returns", *Review of Financial Studies* 20(2). Documents that information — especially
  market-wide information — diffuses only gradually across industry portfolios, producing
  a lead-lag effect: industries that under-adjust to a market-wide move continue to
  adjust in subsequent periods (catch-up), and this diffusion, not momentum, drives the
  post-event drift.
- Lo, A. and MacKinlay, A.C. (1990), "When Are Contrarian Profits Due to Stock Market
  Overreaction?", *Review of Financial Studies* 3(2). Documents significantly positive
  cross-autocovariances — past returns of leading securities predict current returns of
  lagging securities — and separates this lead-lag term from the own-shock term. This
  family claims the cross term only.
- Jegadeesh, N. (1990), "Evidence of Predictable Behavior of Security Returns",
  *Journal of Finance* 45(3). Documents weekly-frequency lead-lag structure consistent
  with slow adjustment.

**ETF-market mechanism story.** On an unusually large positive market day, the broad
index proxy (SPY) and the high-turnover sectors reprice within the session, while
lower-attention sector ETFs (staples, utilities, real estate, materials) under-adjust:
their marginal traders are slow-cycle allocators (committee/T+1 review cycles), their AP
creation windows settle next session, and their liquidity suppliers have not yet
re-marked quotes to the new market level. The sector whose same-day move fell furthest
short of its beta-implied move is the under-adjusted one; over the following sessions its
residual should catch up toward the market (Hou's diffusion). The tradable long/cash
expression: after a market-shock day, buy the most under-adjusted sector for a fixed
short window and hold the residual catch-up.

## 2. Expected counterparty and falsifiable expected sign

**Counterparty.** Suppliers of the lagging sector at a stale relative price on and after
the shock day: (i) liquidity providers of the quiet sector whose marks lag the new market
level, (ii) slow-cycle allocators who sell or underweight the lagging sector before
completing their own market adjustment, (iii) APs whose creation/redemption response
lands one session later. Each accepts the stale relative price because their cost of
speed (committee cycles, operational latency, inventory risk in a thin ETF) exceeds the
small per-name mispricing — exactly the rational inattention that makes diffusion persist.

**Falsifiable expected sign.** After a positive market-shock day (r_SPY >= 2.0 sigma_SPY
as defined in section 4), the sector selected as most under-adjusted earns, over the
5-session hold, a total return exceeding beta-times-SPY by a positive margin net of
costs. Zero or negative realized margin kills the diffusion claim (section 11).

## 3. Required fields and PIT availability

| field | use | PIT availability |
|---|---|---|
| daily raw OHLCV per ETF | closes for returns; opens for execution | provider daily bar, completed regular sessions only |
| daily volume | NOT USED (attention is expressed in prices, not volume, to keep the mechanism price-only) | n/a |
| official split factors | issuer-TR construction; fill accounting | issuer/agent records |
| official cash distributions | issuer-TR construction; accounting | issuer/agent records |
| US_EQUITY_REGULAR_V1 calendar | session indexing, rolling windows, budget year | frozen calendar |

No earnings, analyst, borrow, quote/spread, fundamentals, institutional-flow, or options
data. All signal inputs come from completed sessions through t; execution is at the next
session's open event. Signal returns use the issuer-TR path (raw + official distributions
+ official splits), so ex-dividend sessions never fake an under-adjustment; fills occur
at raw prices per the packet contract.

## 4. Universe, formation, holding, decision and execution clocks

**Universe.** All 11 cohort members loaded. SPY is the market factor and benchmark
symbol and is never selected (its residual vs itself is identically zero). Selection
universe: the 10 sector ETFs XLK XLE XLF XLV XLI XLP XLY XLU XLB XLRE.

**Formation (exact, frozen constants).** On each completed session t:

- r_i,s and r_SPY,s are issuer-TR daily returns (issuer-TR path).
- beta_i(t) = OLS slope of r_i on r_SPY over the trailing 60 completed sessions
  [t-59 .. t], inclusive of t; sigma_i(t) = population std (ddof=0) of the in-window
  residuals r_i,s - beta_i(t) * r_SPY,s.
- sigma_SPY(t) = population std (ddof=0) of SPY issuer-TR returns over the same
  trailing 60 completed sessions.
- Market-shock trigger: r_SPY,t >= 2.0 * sigma_SPY(t) (positive side only; the
  long/cash book has no short leg, so the negative-side symmetric trade is NOT taken by
  the anchor — it is the control, section 8).
- Adjustment residual: rho_i(t) = r_i,t - beta_i(t) * r_SPY,t.
- Selection: smallest rho_i(t) among the 10 sectors SUBJECT TO the meaningfulness floor
  rho_i(t) <= -1.0 * sigma_i(t). If no sector meets the floor, no trade: on that
  reading the diffusion already completed within the session and the mechanism is absent.
  Exact tie broken by alphabetically first symbol.

**Holding.** Anchor/control: exactly 5 sessions. Neighbour: exactly 10 sessions
(Hou's diffusion completes over weeks; the longer window lets catch-up accumulate).

**Decision and execution clocks.** One decision pass per session after its close using
data through t (completed-session PIT). Entry at the regular-session OPEN of t+1; exit
at the open of session entry+6 (anchor), entry+11 (neighbour). Same-open switch allowed
(exit and new entry at the same open, both decided at the prior close). No same-session
look-ahead anywhere.

**Concurrency and budget.** Concurrency 1 (triggers while a position is open are
ignored). Episode budget: at most 5 new entries per rolling 252-session window, entries
taken in strict chronological order, no retrospective re-ranking. Constants frozen.

## 5. Long/cash target construction and cash semantics

- Live episode: 0.50 in the selected sector ETF, 0.50 explicit CASH. Otherwise 1.00
  CASH. No leverage; gross <= 1.0 always.
- CASH: explicit leg, zero yield, canonically handled by the harness, never counted in
  tradable-leg turnover, sidecar accounting must equal canonical valuation, costs charged
  exactly once (packet accounting lessons).
- Deterministic step-function targets; hold-to-exit, no drift correction.

## 6. Turnover, capacity, cost, distribution/split handling

**Turnover.** One episode = buy 0.5 + sell 0.5 = 1.0 gross-units of P+S. Budget 5
episodes/252 sessions: <= 5.0x two-way per year under conservative (P+S) counting, 2.5x
under (P+S)/2 — inside the 6.0x/yr ceiling either way, with margin. Same-open switches
count both legs. Neighbour realizes less (concurrency blocks more days).

**Capacity.** Daily ETF cohort, schedule-only feasibility claim; the frequency risk is
trigger scarcity (big positive SPY days are rarer in bear periods — see section 10),
governed by the episode budget.

**Cost.** Base 10 bps/side = 10 bps of book equity per episode round trip; stress 20
bps/side = 20 bps per episode. Prior expectation, stated honestly: residual catch-up on
single sector names after a market shock is plausibly tens of bps on position notional
(Hou finds industry diffusion persists for weeks), so the stress gate is a real test,
not a formality — if catch-up does not clear 2x base costs, the family must die.

**Distributions/splits.** Fills at raw prices; distributions reinvest via the issuer-TR
accounting path; splits via official factors; issuer records are the accounting
authority (packet lesson on the 2025-12-05 provider/issuer split conflict). Signals use
issuer-TR returns so distributions cannot masquerade as under-adjustment.

## 7. Expected behaviour against the four frozen benchmarks

- **Flat.** Expected small positive after-cost expectancy overall; quiet years with
  2-4 episodes can be slightly negative for that year. The claim is cross-fold.
- **SPY TR.** Expected below in absolute terms most folds (0.5 gross on a few percent of
  sessions). The family does not compete on absolute return.
- **Equal-weight sector TR.** Below, same reasoning.
- **Risk-matched SPY (the target).** The arm's frozen gross/vol rule is declared as a
  constant-scale rule: min_gross = max_gross = 0.025 for anchor/control (5 episodes x 5
  sessions x 0.5 / 252 = 0.0248) and 0.05 for the 10-session neighbour. The benchmark is
  SPY TR scaled ex ante at the arm's expected average gross. Expected: positive
  after-cost excess in >= 2/3 folds and positive incremental mechanism alpha — the
  selected catch-up episodes must beat always-invested SPY per unit of average gross,
  which is exactly the alpha-not-beta separation the contract demands. Note the catch-up
  claim is a RELATIVE claim (sector vs its beta-implied path), so this benchmark isolates
  it cleanly.

## 8. Anchor, neighbour, causal negative control

- **Anchor** `SFV3-A5-MKT-SHOCK-DIFFUSION/A1`: positive market-shock trigger
  (r_SPY >= 2.0 sigma_SPY), most-under-adjusted sector with the -1.0 sigma floor, hold 5
  sessions, 0.5 gross, budget 5/252, concurrency 1. Claim: under-adjusters catch up.
- **Neighbour** `.../N1`: identical trigger, selection, budget, clock; hold 10 sessions.
  Theory: Hou's diffusion completes over weeks, so catch-up should persist or grow with
  the window. Also guards the anchor against a 5-session knife-edge artifact; expected
  same-sign alpha.
- **Causal negative control** `.../C1` (mirror side): trigger r_SPY,t <= -2.0 *
  sigma_SPY(t); select the sector with the LARGEST rho_i(t) subject to
  rho_i(t) >= +1.0 * sigma_i(t) (the "defender" that under-adjusted to the downside on a
  crash day); identical hold, clock, budget, gross. Mechanism-derived prediction: the
  diffusion is direction-symmetric in residuals, so the defender's relative outperformance
  on the shock day must REVERT — the defender should fall toward its beta-implied path,
  i.e., C1 incremental alpha <= 0. This control falsifies by construction: if C1 earns
  positive alpha comparable to A1, then "relatively strongest after a market shock keeps
  outperforming" is the live mechanism — flight-to-quality persistence or short-horizon
  momentum, NOT diffusion — and the family is dead. Anchor and control are stable,
  distinct identities: opposite market-sign trigger, opposite residual tail, opposite
  predicted alpha sign.

## 9. Incremental mechanism test (alpha vs equity beta)

Per fold, per arm: incremental alpha = after-cost strategy return minus risk-matched SPY
benchmark return (`benchmarks.build_risk_matched_spy` with the arm's frozen
constant-scale `VolScalingRule`; `incremental.compute_fold_alpha` with
`require_beta_isolation=True`). The design makes a beta explanation impossible to pass:
the benchmark holds SPY at the arm's average gross on ALL sessions, so the arm only wins
if its shock-day-selected under-adjusters beat unconditional SPY exposure per unit of
average gross. The claimed edge is a residual catch-up, which is by construction
orthogonal to the market path — any positive alpha is attributable to the diffusion term
(Lo-MacKinlay's cross-autocovariance), not to equity beta. The mirror control C1 removes
the remaining alternative (generic post-shock drift): a drift story would pay BOTH sides.

## 10. Drop-one-ETF and drop-one-fold expectations

**Drop-one-ETF.** Selection is a residual rank over all 10 sectors on the event day;
residuals are beta- and sigma-standardized, so no sector is structurally favored.
Expectation: survives removing any single ETF. Stated risk: defensive sectors
(staples/utilities/real estate) mechanically produce the largest positive residuals on
crash days (they are the defenders) and the largest negative residuals on melt-up days;
if the anchor's PnL concentrates in one or two defensive names, the 35% single-ETF
contribution gate and drop-one-ETF will catch it, and the family should die.

**Drop-one-fold.** Trigger frequency is regime-dependent: big positive SPY days cluster
in recovery/vol-normal regimes and thin out in grinding bears, so fold 2
(2020-09..2023-02) is expected to have the FEWEST episodes — the opposite concentration
direction from the companion family, and a useful hedge at the cycle level (section 11
of the companion notes the mirror-image risk there). Pre-registered expectation: the
family is expected to survive drop-one-fold on the strength of folds 1 and 3; if fold 2
is sparsely populated, its gates must be judged as an unpopulated-thin fold under the
packet's "sufficient decisions/positions for the family's frozen clock" clause rather
than rescued. If folds 1 and 3 cannot both carry positive excess, drop-one-fold fails
and the family dies.

## 11. Exact falsification rule and implementation estimate

**Falsification rule (exact, any one kills the family):**

1. Anchor incremental alpha <= 0 overall, or positive in < 2/3 folds.
2. Control C1 incremental alpha > 0.5 x A1 alpha, or same (positive) sign as the anchor
   with comparable magnitude — i.e., failing the packet's "opposite sign OR < 50%" gate
   proves the edge is post-shock relative-strength persistence, not diffusion.
3. Neighbour N1 incremental alpha strictly opposite in sign to A1's (effect is a
   holding-clock artifact, not a diffusion process).
4. Anchor after-cost expectancy <= 0, or stress PF < 1.00 at 20 bps/side.
5. Realized two-way turnover > 6.0x/yr, or any episode-budget/concurrency breach.
6. Any preregistered Stage-A gate failure (after-cost expectancy, PF >= 1.10, >= 2/3
   folds positive, no populated fold PF < 0.80, MDD <= 15%/fold, largest positive-fold
   share <= 50%, single-ETF contribution <= 35%, drop-one-ETF, drop-one-fold, exact
   independent reproduction, zero unresolved HIGH/CRITICAL audit objections).

**Implementation estimate.**

- Reuse: `assets/stocks/loader.BarLoader`; `benchmarks.issuer_total_return_daily`,
  `benchmarks.split_adjusted_closes`, `benchmarks.build_risk_matched_spy` (constant-scale
  rule passes existing validation), `factory.etf_leg_turnover/fill_cost/value_book`,
  `factory.select_drop_one_symbol`, `incremental.compute_fold_alpha`.
- New: the SAME `research/stocks_free_v3/event_arm_base.py` state machine proposed by the
  companion family (rolling beta/sigma estimators ddof=0, trigger/selection, budget and
  concurrency ledger, same-open switch, canonical target-weight schedule emission) plus a
  thin configuration head for A1/N1/C1 here (market-side trigger, residual-tail
  selection, mirror control). Marginal code beyond the shared base: ~100-150 LOC +
  tests.
- Effort: ~1-1.5 engineer-days incremental after the shared base (call it ~4 days total
  for both families including golden tests and reproduction fixtures).

## 12. Ancestry comparison (why this is not a closed family)

- **Not cross-sectional momentum (`A4_XSEC_ETF_RELATIVE_MOMENTUM` or any lookback/top-K
  variant)**: no trailing multi-period return ranking and no persistent top-K holding.
  The selection ranks ONE-day beta-adjusted residuals on a small number of pre-declared
  market-shock days and predicts CONVERGENCE of the laggard toward the market — a
  cross-autocovariance (lead-lag) term that Lo-MacKinlay explicitly separate from
  momentum/continuation. V2's momentum held 3 names continuously off 12-1 returns; this
  holds 1 name for 5 sessions a handful of times a year.
- **Not `A5-SFV2-TREND-DEFENSIVE` or trend/SMA/EMA/vol-target rotation**: no price-level
  filter, no trend state, no defensive de-risking schedule; exposure is event-gated
  0.5-or-nothing. The trigger is a vol-standardized single-day market event, not a trend
  signal.
- **Not long-SPY/sector beta**: the claim is a relative catch-up over and above the
  beta-implied path, measured against a constant-scale risk-matched SPY benchmark; the
  mirror control pays the opposite side of the same drift, so a generic beta/drift
  explanation fails the family rather than passing it.
- **Not a selected-ETF rescue**: the selection universe is the full 10-sector set under a
  frozen rule fixed before scoring; no chosen subsets, no post-hoc thresholds.
- **Not an indicator grid**: one market trigger (2.0 sigma_SPY), one residual floor
  (1.0 sigma_i), one clock (5/10 sessions), one budget — all reasoned constants.
- **Not the companion family in disguise**: the companion trades the OWN-shock term
  (contrarian to the name's own idio extreme, any day); this trades the CROSS term
  (directional with the market, conditioned on a market-shock day). Their triggers,
  selection rules, predicted signs, controls, and fold-concentration directions differ;
  they share only estimation plumbing (beta/sigma), which is code reuse, not mechanism.
- **Not crypto-ancestry recycling**: no funding/carry, no perp constructs; exchange
  price history only.
