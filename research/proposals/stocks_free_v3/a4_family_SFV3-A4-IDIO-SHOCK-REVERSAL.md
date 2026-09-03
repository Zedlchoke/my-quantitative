# SFV3-A4-IDIO-SHOCK-REVERSAL — blind mechanism proposal (lane A4, document 1 of 2)

- Author lane: A4 (blind proposal lane 1 of 3), STOCKS-FREE-V3 Phase D1.
- Written on worktree `orca/stocks-free-v3-d1-a4-proposals`, HEAD `d388f8c9ea180c3e127fce811bcbfc3e9c6028a6`.
- Inputs consulted (complete list): `blind_input_packet.json` / `.md`, `forbidden_family_inventory.json`,
  `PLAN_stocks.md` sections 10–11, and docstrings/signatures of `research/stocks_free_v3/benchmarks.py`,
  `research/stocks_free_v3/incremental.py`, `research/assets/stocks/factory.py`, `research/assets/stocks/loader.py`.
- Blinding: no V2 run directory, no audits, no results, no scored PnL, no V3 lane directories opened.
  No returns, PnL, PF, Sharpe, rankings or correlations were computed on any data. This document is a
  proposal only; every number below is either a frozen contract constant from the packet or a fixed
  parameter constant proposed here with its reasoning.

## 0. Identity

- family_id: `SFV3-A4-IDIO-SHOCK-REVERSAL`
- One-line mechanism: after a sector ETF's large market-adjusted (idiosyncratic) single-day decline,
  buy that sector at the next session's close and hold it for three sessions inside an otherwise
  equal-weight sector book — harvesting the liquidity-provision premium paid by mandated,
  price-insensitive sellers, with the market return removed before the event is defined.

## 1. Primary-source claim and ETF-market mechanism

Primary sources (real, citable; mechanisms described, not quoted):

1. Jegadeesh, S. (1990), "Evidence of Predictable Behavior of Security Returns", *Journal of Finance*
   45(3). Documents short-horizon reversal: securities with extreme recent returns systematically
   revert over the following weeks; the extreme-decile loser portfolio is followed by positive
   abnormal returns. The reversion is concentrated at short horizons (roughly the first month).
2. Lehmann, B. (1990), "Fads, Martingales, and Market Efficiency", *Quarterly Journal of Economics*
   105(1). Documents weekly reversal in US equities and interprets it as compensation for providing
   liquidity against non-informational price pressure.
3. Da, Z., Liu, Q., Schaumburg, E. (2014), "A Closer Look at the Short-Term Return Reversal",
   *Management Science* 60(2). Shows the reversal is concentrated in the non-fundamental,
   idiosyncratic component of returns — removing the market factor before measuring the shock
   strengthens the reversal — and attributes it to liquidity-driven temporary price pressure rather
   than to fundamental news.
4. Nagel, S. (2012), "Evaporating Liquidity", *Review of Financial Studies* 25(7). Models and documents
   liquidity-provision returns to contrarian strategies: the premium is a risk premium for intermediaries
   whose capital evaporates in high-volatility states, so reversal-type compensation is larger when
   market volatility is elevated.

ETF-market mechanism story. Sector ETFs are the execution vehicle for scheduled and risk-driven
sector rotation: portfolio desks rotating out of a sector, risk systems cutting exposure after an
intra-sector shock, and index-rebalance execution desks completing mandated trades all demand
immediacy and are constrained to trade regardless of price. When that flow lands on one sector on
one day while the broad market is roughly flat, the price move is mostly non-informational pressure
that the market-maker community cannot fully absorb (ETF arbitrage bands are wide at exactly those
moments because the underlying basket is also moving). Part of the move is therefore a temporary
discount, and the documented short-horizon reversal premium is the payment for standing on the other
side. This is precisely the mechanism Da–Liu–Schaumburg isolate: the reversal lives in the
market-adjusted component, which is why the family defines its event AFTER removing the market return.

## 2. Expected counterparty and falsifiable expected sign

- Counterparty: liquidity-demanding, constraint-driven sellers in the shocked sector — sector-rotation
  program desks, risk-limit/stop-loss sellers, and mandated index/rebalance executors. They accept a
  temporarily depressed price because their trade is triggered by a mandate, a risk limit, or a
  completion deadline, not by private information about the sector's fundamentals. The arm acts as the
  provider of immediacy and is compensated for adverse-selection and inventory risk (Nagel 2012).
- Falsifiable expected sign (event level): the market-adjusted 3-session forward return of a sector
  ETF after an idiosyncratic shock day is positive —
  `E[ r_i(next 3 sessions) − β_i · r_SPY(next 3 sessions) ] > 0` conditional on
  `ε_i(T) ≤ −2.0%` at the shock close T. If the conditional mean is ≤ 0 (i.e., idio shocks continue,
  not revert), the mechanism is dead and the family must be rejected.
- Falsifiable expected sign (book level): positive risk-matched excess versus SPY in at least 2/3
  folds and positive incremental mechanism alpha (section 9), driven by the event positions.

## 3. Required fields and PIT availability

Only fields already authorized by the frozen packet are used:

| Field | Used for | PIT status |
|---|---|---|
| daily raw close (per ETF, incl. SPY) | daily returns for ε and β; nothing else | completed sessions only |
| official split factors | issuer-TR return reconstruction; fills at raw prices | known at effective date |
| official cash distributions | issuer-TR return reconstruction | known at declared ex-date |
| US_EQUITY_REGULAR_V1 calendar | session sequencing, decision/execution clock | calendar is known in advance |

Daily volume is available but deliberately unused. No earnings dates, estimates, borrow, intraday
quotes, fundamentals, flows or options data are used or needed. Every feature at decision session T
uses only returns realized through T's close; the first scored session of S0 already has the full
63-session warmup (2018-01-02..2018-04-03) available for the trailing β window, so no scored session
lacks feature history.

## 4. Universe, formation, holding, decision and execution clocks

- Universe (held): the 10 sector ETFs `XLK XLE XLF XLV XLI XLP XLY XLU XLB XLRE`. SPY is in the
  cohort but is NEVER held; it enters only as the market factor in the ε computation. Rationale for
  excluding SPY from holdings: the benchmarks already express SPY; holding it would blur attribution
  and concentrate positive PnL in a single name.
- Formation (continuous, daily): at the close of each session T, for each sector i compute
  `β_i(T)` = OLS slope of `r_i` on `r_SPY` over the trailing 63 completed sessions (issuer-TR daily
  returns), and `ε_i(T) = r_i(T) − β_i(T) · r_SPY(T)`. Event if `ε_i(T) ≤ −0.020` (−2.0%, fixed).
  −2.0% is roughly 2–3 daily standard deviations of the idiosyncratic component of a sector ETF
  (typical sector daily σ ≈ 1.0–1.5%, idio σ after market removal ≈ 0.6–1.0%), i.e. clearly an event
  and not noise, while still occurring often enough to populate the schedule.
- Event selection per session: at most ONE new event position per session; if multiple sectors
  qualify at T, take the most negative ε_i(T); ties broken lexicographically by symbol.
- Entry: at the next session's regular-session close (T+1) — the packet's PIT clock (signal through T
  is executable at the next session's event); the canonical factory fills at the fill close.
- Holding: 3 sessions. The position entered at T+1 close is exited at the close of T+4, earning the
  3 session returns T+2..T+4. 3 sessions sits inside the documented ≤ 1-week reversal horizon.
- Exits and re-entry: exit is deterministic at the holding expiry close. A sector with an active
  event position cannot open a second one; it may re-qualify after expiry.
- Governors (fixed constants, motivated by the turnover ceiling, not by outcomes): at most
  3 concurrent event positions; at most 6 new entries per calendar year; when a cap binds, later
  qualifying events are skipped (never queued). Worst-case realized behavior is therefore bounded by
  construction: ≤ 6 entries/yr × 0.60 two-way turnover per entry-cycle (section 6).
- Gross reset clock: the book's gross level is re-targeted at every mechanism fill and at the FIRST
  session of each calendar month (monthly gross reset; section 5). Both clocks use completed-session
  data only and are executable at the next session's close.

## 5. Long/cash target construction and cash semantics

Frozen gross/vol rule (risk-match convention, identical to the benchmark's): the arm declares
`VolScalingRule(lookback_sessions=63, target_daily_vol=0.01, min_gross=0.0, max_gross=1.0)` — the
P1-frozen baseline rule with the no-leverage cap of the packet. The arm's ETF gross at any fill is
`s(d) = clip(0.01 / realized_vol_63(SPY TR through d−1), 0.0, 1.0)`; the risk-matched benchmark is
built from the SAME rule and the SAME SPY history, so the two scale identically ex ante and the
scaling cancels in incremental alpha by construction (it multiplies both sides). The rule never
selects assets — it only sizes the whole book; section 12 explains why this is not A5 ancestry.

Target book at any fill on session d, with `n` = number of active event positions (0..3):

- each active event sector: `0.15 × s(d)`
- each of the 10 base sectors: `s(d) × (1 − 0.15·n) / 10`
- CASH: `1 − s(d)`

Sum of ETF weights = `s(d)` ≤ 1.0 always; no leverage; gross ≤ 1.0 per the packet.
Cash semantics: the explicit CASH leg carries the residual `1 − s(d)`, earns 0.0, is never counted in
tradable-leg turnover, and never pays cost — exactly the canonical A2 factory semantics. In calm
regimes `s(d) ≈ 1.0` and the book is effectively fully invested; in elevated-vol regimes the book
de-risks identically to its benchmark, which is the packet's risk-match contract, not a defensive
rotation claim.

## 6. Turnover, capacity, cost, distribution and split handling

- Turnover (two-way, ETF legs only, CASH excluded): one entry moves 0.15 in (event buy) + 0.15 out
  (pro-rata base trim) = 0.30; the expiry exit mirrors it = 0.60 per entry-cycle. The calendar-year
  entry governor caps this at `6 × 0.60 = 3.6×/yr`. Monthly gross resets add `Σ|Δs(d)|` per year —
  for a 63-session trailing-vol ratio this is expected in the 0.2–1.2×/yr range. Total bound:
  ≈ 3.8–4.8×/yr, inside the 6.0×/yr feasibility ceiling with headroom. The exact figure is a
  schedule-only measurement for D3 (deterministic from the rule + S0 SPY history; no PnL involved);
  if the measured gross-reset component exceeds 1.2×/yr, the family declares itself schedule-infeasible.
- Capacity: daily 11-ETF cohort with ≤ 6 entries/yr and gross ≤ 1.0; no capacity claim beyond
  schedule feasibility, per the packet.
- Cost: 10 bps/side base on ETF turnover (2 spread + 3 slippage + 2 ops + 3 execution), 20 bps
  stress. Expected after-cost drag ≈ 3.8–4.8 × 10 bps ≈ 38–48 bps/yr base, ≈ 76–96 bps/yr stress.
  The stress gate (stress PnL > 0, stress PF ≥ 1.00) therefore requires the mean 3-session
  market-adjusted reversal per shocked sector to be at least ≈ +70 bps — inside the range documented
  by Jegadeesh/Lehmann/Da–Liu–Schaumburg for extreme short-horizon moves, and stated here as an
  explicit viability condition, not an assumption of success.
- Distributions and splits: all feature returns (daily `r_i`, `r_SPY`, β window) are computed on the
  issuer-TR reconstruction path, which the packet designates the accounting authority (lesson 6).
  Fills occur at raw prices; splits enter via official factors; distributions are credited on ex-dates
  through the issuer-TR path. An ex-date inside a 3-session hold distorts nothing because both the
  feature and the accounting sides are TR-consistent. Costs are charged exactly once per fill by the
  canonical factory; CASH is never a costed leg.

## 7. Expected behaviour against the four benchmarks

1. Flat (hard floor): the book is risk-on and fully invested in calm regimes, so absolute return is
   dominated by equity beta and the family does NOT claim to beat flat by mechanism. In drawdown
   periods the vol-matched gross reduction lowers absolute losses, but the honest expectation is that
   flat is beaten or missed mostly with the market, not by the mechanism. The hard benchmark is
   respected as a gate, not claimed as the edge.
2. SPY total return: expected to track SPY plus (a) the EW-10-vs-SPY base tilt, which is a frozen
   nuisance shared by all three arms of the family, and (b) the event overlay, which is the claim.
   Excess over raw SPY is expected positive but small and noisy; the scored claim is NOT this
   benchmark (see 9).
3. Equal-weight sector TR: the base is EW-10, so outside event overlays the book ≈ this benchmark ×
   s(d). The family's expected outperformance versus this benchmark is exactly the event overlay's
   contribution — this is the cleanest descriptive comparison of the mechanism, though still not the
   pass-eligible one.
4. Risk-matched SPY context: the pass-eligible benchmark. Because the arm's gross path follows the
   same frozen VolScalingRule as the benchmark, the difference isolates composition. Expected: the
   event overlay contributes a small positive excess in each fold, positive in ≥ 2/3 folds; folds
   containing volatility episodes should carry MORE of the excess (Nagel: the premium widens in
   high-vol states), which is exactly what the neighbour arm tests. Honest risk: the EW-10-vs-SPY
   base tilt adds noise to this comparison that the shared-base control design (section 8) is built
   to neutralize.

## 8. Arms: anchor, theoretically justified neighbour, causal negative control

- ANCHOR `IDIO-SHOCK-REV-ANCHOR`: exactly as specified in sections 4–6.
- NEIGHBOUR `IDIO-SHOCK-REV-HIGHVOL` (theoretically justified, distinct identity): identical in every
  constant and clock, but a qualifying event additionally requires an elevated market-vol state:
  SPY trailing-63-session realized daily vol (ddof=0, the same estimator the frozen rule uses)
  ≥ 0.012 at the decision close (≈ 19% annualized — an elevated-but-not-crisis level, fixed constant).
  Justification: Nagel (2012) — liquidity-provision returns concentrate in high-volatility states
  because intermediary capital evaporates exactly then. Expected direction: per-event reversal alpha
  in high-vol events exceeds per-event alpha in low-vol events; the neighbour thereby tests the
  state-dependence the source theory predicts. If the neighbour shows the OPPOSITE ordering, the
  mechanism's risk-premium interpretation is unsupported and the preregistered
  "neighbour supports the mechanism" gate fails.
- CAUSAL NEGATIVE CONTROL `IDIO-SHOCK-REV-LATE` (time-shifted, distinct identity): identical event
  list, identical sizing, caps, base, gross rule and 3-session holding — but every entry is delayed
  by 3 sessions (entered at the close of E+3 instead of E, where E is the anchor's entry session),
  with the control's own deterministic cap accounting. The reversal mechanism predicts the effect is
  concentrated INSIDE the 3 sessions after the shock; a delayed entrant buys after the hypothesized
  window has closed and should earn ≈ 0 (or the continuation sign). The control falsifies the
  mechanism if it reproduces the anchor (frozen gate: anchor passes only if the control shows the
  opposite alpha sign OR |α_control| < 0.5 × |α_anchor|). Because both arms share the identical base,
  identical gross rule and identical event detection, the anchor-minus-control comparison is a pure
  timing comparison — immune to "which sectors got picked" and to base beta.

The three identities are stable and distinct: same book architecture, three different causal claims
(immediate reversal entry / high-vol-amplified reversal / no-timing edge), and the control can kill
the family by construction.

## 9. Incremental mechanism test (alpha vs equity beta)

- Per fold f: `α(f) = R_strategy_after_cost(f) − R_RISK_MATCHED_SPY(f)` using the frozen
  `research.stocks_free_v3.incremental` contract and the arm's declared VolScalingRule.
- Beta isolation: because the benchmark's gross path is built from the SAME ex-ante rule as the arm's,
  the difference is the composition excess scaled by s(d); long equity beta alone yields α ≈ 0
  regardless of how large beta was. A family cannot pass on beta.
- Anchor pass condition (frozen gates): α(f) > 0 in ≥ 2/3 folds and cumulative incremental
  mechanism alpha > 0.
- Mechanism isolation on top of beta isolation: α_anchor − α_control must be positive and the frozen
  control gate must hold (opposite control sign, or |α_control| < 0.5 × |α_anchor|). The shared base
  makes this difference a direct estimate of the reversal premium net of every book-level nuisance.
- Decision evidence: ~6 entries/yr + 6 exits/yr + 12 gross resets ≈ 24+ deterministic decisions/yr,
  ≥ 70 over S0 and ≥ 20 per fold — sufficient for the frozen clock.

## 10. Drop-one-ETF and drop-one-fold expectations

- Drop-one-ETF (factory rule: HELD ETF with the largest realized absolute-weight contribution,
  lexicographic tie-break): the mechanism is sector-agnostic — any sector can be shocked, and the
  base holds all ten equally — so removing one sector removes ≈ 1/10 of the base and whatever event
  positions that sector happened to host. Expected: sign and fold pattern of α preserved in ≥ 2/3
  folds for every single-ETF drop; magnitude attenuated roughly proportionally. If the family only
  survives when one specific sector is present, the mechanism is degenerate and the concentration
  gate (no ETF > 35% of positive PnL) should already have flagged it.
- Drop-one-fold: the liquidity-provision premium is a standing feature of markets, not one regime;
  Nagel predicts MORE of it in high-vol folds. Expected: α > 0 in each of the three leave-one-fold-out
  recombinations, with the middle fold (2020-09..2023-02, which contains a broad drawdown year) the
  most likely weakest contributor for absolute-return gates but not for alpha gates. Honest risk
  statement: if the premium exists only inside one fold, the family fails the fold-robustness gate and
  must be rejected.

## 11. Exact falsification rule and implementation estimate

The family is REJECTED if ANY of the following is observed (all preregistered now):

1. F1 (event sign): the anchor's event-level conditional mean 3-session market-adjusted forward
   return of shocked sectors is ≤ 0.
2. F2 (alpha): anchor after-cost expectancy ≤ 0, or anchor risk-matched excess ≤ 0 in ≥ 2/3 folds,
   or anchor incremental mechanism alpha ≤ 0.
3. F3 (control): the late-entry control shows the SAME-sign incremental alpha with
   |α_control| ≥ 0.5 × |α_anchor| — i.e., buying 3 sessions late does as well as buying immediately,
   which kills the reversal-timing claim and leaves only beta/base drift.
4. F4 (state direction): high-vol events earn strictly LESS per-event alpha than low-vol events
   (neighbour ordering inverted), in which case the Nagel interpretation fails and, with it, the
   preregistered neighbour gate.
5. F5 (schedule): measured schedule-only turnover > 6.0×/yr, or gross-reset component > 1.2×/yr
   (infeasibility, not mechanism failure).

Implementation estimate (modules reuse the four allowed existing modules; nothing else exists yet):

- New `research/stocks_free_v3/family_idio_shock/`: `features.py` (β/ε computation, issuer-TR daily
  returns, ~1 day), `scheduler.py` (event detection, per-session selection, concurrency and annual
  caps, deterministic tie-breaks, ~1 day), `book.py` (target-weight construction × s(d) at fills and
  monthly resets, ~1 day), `preflight.py` (schedule-only turnover bound and cost table, ~0.5 day),
  tests with hand-computed synthetic fixtures (split, distribution, ex-date, cap-binding cases,
  ~1.5 days). Integration against `loader.py` (checksummed parquet reads), `factory.py` (canonical
  accounting), `benchmarks.py` (four builders + VolScalingRule) and `incremental.py` (alpha contract)
  requires no changes to those modules. Total ≈ 5 engineer-days; main risks are cap-binding
  determinism and the gross-reset turnover measurement.

## 12. Ancestry comparison — why this is not a closed family

- NOT `A4_XSEC_ETF_RELATIVE_MOMENTUM` / ordinary cross-sectional momentum: the selection sign is
  OPPOSITE (we buy the day's largest negative idio shock, not trailing winners); the trigger is a
  single-day threshold event, not a top-K ranking over a multi-month lookback; the market factor is
  removed BEFORE the event is defined (momentum families in the inventory rank raw relative returns);
  the holding is 3 sessions, not months. No parameter of the closed family (lookback, top-K,
  vol-adjusted weights) appears here.
- NOT `A5-SFV2-TREND-DEFENSIVE`: there is no trend filter, no SMA/EMA, no defensive-asset selection.
  The book is always fully allocated to risk-on sector ETFs at gross s(d); the VolScalingRule is the
  P1-frozen risk-match convention applied IDENTICALLY to the arm and its benchmark, contributes
  exactly zero to incremental alpha by construction, and never chooses an asset. A5's claimed edge
  was vol-timed avoidance; this family's claimed edge is a conditional cross-sectional premium, and
  its own control would flag pure de-risking as base drift.
- NOT long-SPY/sector beta: the scored claim is the anchor-vs-risk-matched-SPY excess AND the
  anchor-vs-control difference with a shared base; a beta-only book reproduces zero of both. The V2
  lesson (bottom-ranked control reproduced the anchor) is addressed head-on by a control designed for
  the specific causal claim (timing), not a generic opposite ranking.
- NOT a selected-ETF rescue: no ETF subset is inherited from any prior cycle; all ten sectors are
  permanently eligible by rule, and events select themselves by threshold.
- NOT a daily-indicator grid: one feature (ε), one threshold (−2.0%), one response (buy, hold 3),
  one state filter (neighbour), each fixed and each tied to a single documented economic mechanism.
- No new accounts, paid data, or network fetch: runs entirely on the existing Twelve Data Basic
  account inputs and the frozen local parquet path.
