# SFV3-A4-QEND-FLOW-REBAL — blind mechanism proposal (lane A4, document 2 of 2)

- Author lane: A4 (blind proposal lane 1 of 3), STOCKS-FREE-V3 Phase D1.
- Written on worktree `orca/stocks-free-v3-d1-a4-proposals`, HEAD `d388f8c9ea180c3e127fce811bcbfc3e9c6028a6`.
- Inputs consulted (complete list): `blind_input_packet.json` / `.md`, `forbidden_family_inventory.json`,
  `PLAN_stocks.md` sections 10–11, and docstrings/signatures of `research/stocks_free_v3/benchmarks.py`,
  `research/stocks_free_v3/incremental.py`, `research/assets/stocks/factory.py`, `research/assets/stocks/loader.py`.
- Blinding: no V2 run directory, no audits, no results, no scored PnL, no V3 lane directories opened.
  No returns, PnL, PF, Sharpe, rankings or correlations were computed on any data. Every number below
  is either a frozen contract constant from the packet or a fixed parameter constant proposed here
  with its reasoning.

## 0. Identity

- family_id: `SFV3-A4-QEND-FLOW-REBAL`
- One-line mechanism: at each calendar quarter-end, mandated institutional rebalancing and
  window-dressing desks systematically sell the quarter's relative sector WINNERS and buy the relative
  LOSERS at prices they do not choose; after the boundary, the depressed losers recover, so an
  otherwise equal-weight sector book tilts into the prior quarter's bottom-3 sector ETFs (and away
  from its top-3) for the first sessions of the new quarter — harvesting a scheduled, non-informational
  flow-pressure premium.

## 1. Primary-source claim and ETF-market mechanism

Primary sources (real, citable; mechanisms described, not quoted):

1. Lakonishok, J., Smidt, S. (1988), "Are Seasonal Anomalies Real? A Ninety-Year Perspective",
   *Review of Financial Studies* 1(4). Documents that turn-of-the-month / turn-of-period return
   seasonality is persistent across ninety years of data and is not an artifact of a few episodes —
   establishing that calendar-boundary return patterns tied to recurring institutional and payment
   cycles are a standing feature of equity markets.
2. Ogden, J. (1990), "Turn-of-Month Evaluations of Liquid Profits and Stock Returns", *Journal of
   Finance* 45(5). Provides the mechanism: a recurring cycle of payments and portfolio evaluations
   concentrated at calendar boundaries creates predictable aggregate demand for equities at the turn
   of the month/period, moving prices at those dates in ways unrelated to news.
3. Lakonishok, J., Shleifer, A., Thaler, R., Vishny, R. (1991), "Window Dressing by Pension Fund
   Managers", *American Economic Review* 81(2). Documents that pension money managers systematically
   rebalance and window-dress around reporting/benchmark dates, producing mandated, price-insensitive
   trades that push recently outperforming assets up and recently underperforming assets down at the
   boundary — pressure that must unwind afterwards.
4. Sias, R., Starks, L. (1997), "Return Autocorrelation and Institutional Investors", *Journal of
   Financial Research*. Documents that turn-of-the-year/period seasonality is stronger where
   institutional ownership concentration is higher, tying the calendar premium to institutional
   trading rather than to data quirks.

ETF-market mechanism story. Sector ETFs are precisely the instruments through which benchmarked
institutions implement quarter-end rebalancing and window dressing: a desk whose equity sleeve is
overweight the quarter's winning sectors sells sector ETFs into the boundary, and buys the lagging
sectors, to bring reported weights back to benchmark — trades whose timing is fixed by the calendar
and whose size is set by the quarter's return dispersion, not by views. On the ETF plumbing side,
month/quarter-end subscription and redemption processing concentrates creation/redemption flow at the
same boundaries. The pressure depresses the quarter's losers into the boundary; once the mandated
trades are done, the temporary discount unwinds over the first sessions of the new quarter. Ogden and
Lakonishok–Smidt establish the recurring calendar-boundary price cycle; Lakonishok et al. (1991)
identify the mandated seller; Sias–Starks tie it to institutional concentration. The family bets on
the unwind, long-only, at a fixed calendar clock.

## 2. Expected counterparty and falsifiable expected sign

- Counterparty: mandated quarter-end traders — benchmarked pension/insurance rebalancing desks and
  window-dressing fund managers (Lakonishok et al. 1991) — plus boundary-day creation/redemption
  facilitators. They accept temporarily bad prices because their mandate fixes the trade date (and
  often the reported price date); a desk must complete the rebalance by the boundary regardless of
  execution quality. The arm supplies the other side of those final-day prints and is paid when the
  pressure unwinds.
- Falsifiable expected sign (event level, stated ex ante): over the first 6 sessions after each
  quarter-end entry,
  `E[ r(bottom-3 prior-quarter sectors) − r(EW-10) ] > 0` AND
  `E[ r(top-3 prior-quarter sectors) − r(EW-10) ] < 0`
  (mirror-image pressure unwind). If the bottom-3 minus top-3 forward spread is ≤ 0, the mandated-flow
  story is dead and the family must be rejected.
- Falsifiable expected sign (book level): positive risk-matched excess versus SPY in ≥ 2/3 folds and
  positive incremental mechanism alpha (section 9), contributed by the quarterly tilts only.

## 3. Required fields and PIT availability

| Field | Used for | PIT status |
|---|---|---|
| daily raw close (per ETF) | quarterly total-return ranking inputs | completed sessions only |
| official split factors | issuer-TR reconstruction of quarterly returns; fills at raw prices | known at effective date |
| official cash distributions | issuer-TR reconstruction of quarterly returns | known at declared ex-date |
| US_EQUITY_REGULAR_V1 calendar | quarter boundaries, decision and exit session identification | known in advance |

Volume is available but unused. No earnings, estimates, borrow, quotes, fundamentals, flows or
derivatives data are used. Calendar features are known ex ante by construction, which makes this the
PIT-cleanest family possible: the decision date is a property of the calendar, and the decision input
(quarterly TR ranks) is fully determined at the decision close. The first decision (last session of
calendar Q2 2018) ranks a quarter whose April sessions fall in the warmup window — warmup history
exists exactly for such feature needs, so no scored decision lacks input.

## 4. Universe, formation, holding, decision and execution clocks

- Universe (held): the 10 sector ETFs `XLK XLE XLF XLV XLI XLP XLY XLU XLB XLRE`. SPY is never held;
  it appears only in the benchmark. Rationale: identical to the sibling document — benchmarks already
  express SPY, and a held SPY would concentrate positive PnL and blur attribution.
- Formation (quarterly, calendar-deterministic): at the close of the LAST regular session T of each
  calendar quarter, compute each sector's total return over all regular sessions of that quarter
  (issuer-TR path; for the first decision, the observable sessions of the quarter, warmup included).
  Rank ascending. Bottom-3 = tilt-BUY set; top-3 = tilt-SELL set; middle-4 = neutral.
- Entry: at the next session's close (T+1, the first session of the new quarter) — the packet's PIT
  clock. The position therefore earns sessions T+2 onward; the first new-quarter session's return is
  deliberately not claimed (it is the price of the PIT-clean clock).
- Holding: 6 sessions. Entered at T+1 close, exited at T+7 close, earning the 6 session returns
  T+2..T+7. Six sessions (~1.2 weeks) sits inside the documented post-boundary unwind window of
  turn-of-period pressure effects and leaves the book in normal state for the rest of the quarter.
- Decision count and sufficiency: exactly 4 decisions/yr, ~30 over S0, ~10 per fold, zero missing-data
  risk (calendar-deterministic). Each decision re-weights all ten sectors and creates a multi-session
  position set, so positions per fold are ≥ 60 (10 sectors × ~10 windows in normal state plus tilt
  states). Sufficiency for the frozen clock is claimed on this basis.
- No governors are needed: the quarterly cadence bounds turnover by construction (section 6).

## 5. Long/cash target construction and cash semantics

Frozen gross/vol rule (risk-match convention, identical to the benchmark's): the arm declares
`VolScalingRule(lookback_sessions=63, target_daily_vol=0.01, min_gross=0.0, max_gross=1.0)` — the
P1-frozen baseline rule with the packet's no-leverage cap. Arm ETF gross at any fill is
`s(d) = clip(0.01 / realized_vol_63(SPY TR through d−1), 0.0, 1.0)`; the risk-matched benchmark uses
the SAME rule and the SAME SPY history, so the scaling multiplies both sides of the incremental-alpha
subtraction and cancels by construction. The rule sizes the book; it never selects an asset (see
section 12 re A5 ancestry).

Target book at any fill on session d:

- Normal state (all sessions outside a tilt window): each of the 10 sectors `0.10 × s(d)`.
- Tilt state (from the T+1 fill until the T+7 exit fill of each quarter transition):
  bottom-3 sectors `0.18 × s(d)` each; top-3 sectors `0.02 × s(d)` each; middle-4 `0.10 × s(d)` each.
  Sum of ETF weights = `s(d)` in every state; the tilt is internally funded (buyers of losers are paid
  by sellers of winners), so the tilt adds zero gross.
- CASH: `1 − s(d)`.

Cash semantics: the explicit CASH leg carries `1 − s(d)`, earns 0.0, is never counted in tradable-leg
turnover and never pays cost — canonical A2 factory semantics. The gross level follows the frozen
vol-match convention, re-targeted at every mechanism fill (4 entries + 4 exits per year) and at the
FIRST session of each calendar month (12 gross resets/yr) so the arm's gross tracks the benchmark's
`s(d)` with a declared monthly-step approximation; that approximation is identical across all three
arms and is therefore invisible to the anchor-vs-control comparison.

## 6. Turnover, capacity, cost, distribution and split handling

- Turnover (two-way, ETF legs only): each quarterly tilt cycle moves the bottom-3 from 0.10 to 0.18
  (+0.24 buys) and the top-3 from 0.10 to 0.02 (−0.24 sells) = 0.48 at entry and 0.48 at exit = 0.96
  per quarter = 3.84×/yr. Monthly gross resets add `Σ|Δs(d)|`, expected 0.2–1.2×/yr for a 63-session
  trailing-vol ratio. Total ≈ 4.0–5.0×/yr — inside the 6.0×/yr ceiling with headroom. Exact figure is
  a schedule-only D3 measurement; if the gross-reset component measures > 1.2×/yr the family declares
  itself schedule-infeasible.
- Capacity: 8 mechanism fills/yr + 12 resets/yr on an 11-ETF liquid cohort; no capacity claim beyond
  schedule feasibility, per the packet.
- Cost: 10 bps/side base, 20 bps stress. Expected drag ≈ 4.0–5.0 × 10 bps ≈ 40–50 bps/yr base,
  ≈ 80–100 bps/yr stress. Viability condition stated ex ante: the mechanism must be worth at least
  ≈ +25 bps of book return per quarter (≈ +60 bps per-sector tilt-window relative return at the 0.16
  active spread) to clear base costs, and ≈ 2.5× that to clear the stress gate — the upper but
  documented range of turn-of-period pressure effects. This is declared as a testable condition, not
  assumed.
- Distributions and splits: ranking inputs are quarter total returns on the issuer-TR path (the packet's
  accounting authority); fills at raw prices; splits via official factors; distributions credited on
  ex-dates through the issuer-TR path. A distribution ex-date landing inside a tilt window affects
  ranking and accounting symmetrically and needs no special case. Costs charged exactly once per fill;
  CASH never costed.

## 7. Expected behaviour against the four benchmarks

1. Flat (hard floor): the book is risk-on with gross s(d); absolute return is beta-dominated and the
   family does not claim a flat-beating mechanism. Drawdown behavior is governed by the shared vol
   rule, identically to its benchmark.
2. SPY total return: expected ≈ SPY plus the EW-10 base tilt (shared nuisance) plus a small quarterly
   tilt contribution. Raw SPY excess is expected positive but is NOT the scored claim.
3. Equal-weight sector TR: the base is exactly EW-10, so this benchmark isolates the tilts as the only
   structural difference. Expected: the book beats EW-10 by roughly (tilt spread per quarter − tilt
   turnover cost); this is the most legible descriptive comparison, though not the pass-eligible one.
4. Risk-matched SPY context: the pass-eligible benchmark. Expected: small positive excess per fold from
   the tilt overlay, positive in ≥ 2/3 folds. Honest risk: the EW-10-vs-SPY base tilt is a nuisance of
   the same order as the mechanism; the shared-base control design (section 8) exists precisely so the
   mechanism can be separated from that nuisance.

## 8. Arms: anchor, theoretically justified neighbour, causal negative control

- ANCHOR `QEND-FLOW-REBAL-ANCHOR`: exactly as specified in sections 4–6.
- NEIGHBOUR `QEND-FLOW-REBAL-LONGHOLD` (theoretically justified, distinct identity): identical
  ranking, sizing, calendar and entry — but the tilt is held 12 sessions instead of 6 (exit at T+13).
  Justification: the flow-pressure literature (Ogden 1990; Lakonishok et al. 1991; and the
  flow-pressure reversal persistence documented by Lou, C. (2012), "A Flow-Based Explanation for
  Return Predictability", *Review of Financial Studies*) describes unwinds that persist for weeks, not
  days — pressure reverses gradually because the mandated flow is absorbed over multiple sessions.
  Expected direction: the anchor's per-quarter tilt alpha persists (positive, decaying) through the
  longer window; the extra 6 sessions should add non-negative incremental alpha. If the extra window
  sharply REVERSES the anchor's alpha (the effect exists only in days 1–6 and mean-reverts by day 13),
  the gradual-unwind interpretation fails and the preregistered neighbour gate flags it.
- CAUSAL NEGATIVE CONTROL `QEND-FLOW-REBAL-WINNERS` (opposite ranking, distinct identity): identical
  calendar, sizing, holding, base, gross rule — but the tilt direction is INVERTED: top-3 prior-quarter
  winners at `0.18 × s(d)`, bottom-3 losers at `0.02 × s(d)`. The mandated-flow theory is directional:
  mandated SELLING hits winners into the boundary and mandated BUYING supports losers, so the unwind
  pays the loser-buyer, not the winner-buyer. If buying the quarter's winners at the boundary earns as
  much as buying the losers, the calendar Premium is not coming from rebalancing-flow direction — the
  anchor's alpha would be base drift or a generic momentum effect — and per the frozen gate
  (control opposite alpha sign, or |α_control| < 0.5 × |α_anchor|) the family is falsified.

The three identities are stable and distinct: same calendar architecture, three different causal
claims (loser-pressure unwind / multi-week unwind persistence / direction-agnostic calendar premium),
and the control can kill the family by construction.

## 9. Incremental mechanism test (alpha vs equity beta)

- Per fold f: `α(f) = R_strategy_after_cost(f) − R_RISK_MATCHED_SPY(f)` via the frozen
  `incremental.py` contract and the arm's declared VolScalingRule. Because the benchmark scales SPY by
  the SAME ex-ante rule as the arm, α isolates composition from beta: a beta-only book yields α ≈ 0.
- Anchor pass condition (frozen gates): α(f) > 0 in ≥ 2/3 folds and cumulative incremental alpha > 0.
- Mechanism isolation on top of beta isolation: α_anchor − α_control > 0 with the frozen control gate
  satisfied; because both arms share base, gross rule and calendar, the difference estimates the
  DIRECTIONAL flow-pressure premium net of every book-level nuisance.
- Decision evidence: 4 decisions/yr × 7.5 yr = 30 scheduled decisions, ~10/fold, each creating 10
  position re-weights and a 6-session position set; plus 12 gross resets/yr. Sufficiency argued on the
  calendar determinism: no decision can fail to exist or to have complete inputs.

## 10. Drop-one-ETF and drop-one-fold expectations

- Drop-one-ETF (factory rule: HELD ETF with largest realized absolute-weight contribution,
  lexicographic tie-break): the ranking runs over all ten sectors each quarter, so the dropped sector
  changes at most one rank slot per quarter. Expected: re-ranking among the remaining nine preserves
  the tilt's sign and fold pattern in ≥ 2/3 folds; magnitude attenuates proportionally (the dropped
  sector removes ≤ 0.18 × s of book weight in tilt states and 0.10 × s in normal states). If survival
  requires one specific sector, the mechanism is degenerate and the 35% concentration gate should
  already have flagged it.
- Drop-one-fold: the counterparty is a standing institutional calendar (every quarter has a boundary),
  and dispersion — the size of the mandated imbalance — exists in every regime. Expected: the tilt
  contribution is positive in each leave-one-fold-out recomputation; the weakest fold is predicted to
  be a low-dispersion, low-volatility fold (smaller mandated imbalances → smaller pressure). Honest
  risk: if the premium exists in only one fold, the family fails fold-robustness and must be rejected.

## 11. Exact falsification rule and implementation estimate

The family is REJECTED if ANY of the following is observed (all preregistered now):

1. F1 (event sign): the anchor's per-quarter bottom-3-minus-top-3 forward 6-session return spread is
   ≤ 0 (aggregated over S0).
2. F2 (alpha): anchor after-cost expectancy ≤ 0, or anchor risk-matched excess ≤ 0 in ≥ 2/3 folds, or
   anchor incremental mechanism alpha ≤ 0.
3. F3 (control): the winner-tilt control shows the SAME-sign incremental alpha with
   |α_control| ≥ 0.5 × |α_anchor| — i.e., calendar timing without directional flow pressure earns the
   same, killing the mechanism.
4. F4 (persistence direction): the long-hold neighbour's incremental alpha is NEGATIVE relative to the
   anchor's holding-window completion (the effect reverses inside days 7–12), contradicting the
   documented multi-session unwind; combined with the preregistered neighbour gate this contributes to
   rejection.
5. F5 (schedule): measured schedule-only turnover > 6.0×/yr, or gross-reset component > 1.2×/yr.
6. F6 (viability): base-cost drag exceeds the ex-ante viability threshold (section 6) — i.e., the
   documented effect size cannot clear the packet's own cost structure; the family is economically
   empty even if directionally correct.

Implementation estimate (reuses the four allowed existing modules):

- New `research/stocks_free_v3/family_qend_flow/`: `calendar.py` (quarter boundary anchors from the
  frozen calendar, ~0.5 day), `ranks.py` (issuer-TR quarterly returns and ascending ranks, ~0.5 day),
  `book.py` (normal/tilt target construction × s(d) at fills and monthly resets, ~1 day),
  `preflight.py` (schedule-only turnover and cost table, ~0.5 day), tests with hand-computed synthetic
  fixtures (rank ties, ex-date inside tilt window, split inside ranking quarter, boundary at fold edge,
  ~1.5 days). No changes to `loader.py`, `factory.py`, `benchmarks.py`, `incremental.py`. Total ≈ 4
  engineer-days — the lowest-risk of the two proposals, since every clock is calendar-deterministic.

## 12. Ancestry comparison — why this is not a closed family

- NOT `A4_XSEC_ETF_RELATIVE_MOMENTUM` / ordinary cross-sectional momentum: the family buys the
  prior-quarter LOSERS and sells the WINNERS — the opposite sign — and the trigger is a fixed calendar
  boundary plus a mandated-flow mechanism, not a momentum lookback/top-K construction. Ordinary
  momentum claims drift of trailing winners; this family claims unwind of boundary pressure on
  trailing losers, with a mirror-sign control preregistered to prove the direction matters. No
  lookback/top-K parameter of the closed family is present: the "lookback" is the calendar quarter
  itself (a property of the counterparty's mandate), and the rank is used with an inverted sign.
- NOT `A5-SFV2-TREND-DEFENSIVE`: no trend filter, no SMA/EMA, no vol-based asset selection. The book
  is always fully allocated among the ten risk-on sector ETFs at gross s(d); the VolScalingRule is the
  P1-frozen risk-match convention applied identically to arm and benchmark, contributes exactly zero to
  incremental alpha by construction, and never chooses an asset. A5's edge claim was vol-timed
  avoidance; this family's edge claim is a calendar-scheduled directional flow premium.
- NOT long-SPY/sector beta: the scored claim is the anchor-vs-risk-matched-SPY excess AND the
  anchor-vs-control directional difference with a shared base; a beta-only book reproduces neither.
- NOT a selected-ETF rescue: no subset inherited from any prior cycle; all ten sectors participate
  every quarter by rule; the tilt sets are recomputed from data each quarter.
- NOT a daily-indicator grid: one decision per quarter, one ranking feature (prior-quarter TR), one
  fixed tilt structure (0.18/0.10/0.02), one fixed holding (6 sessions), one economic mechanism.
- No new accounts, paid data, or network fetch: calendar + existing authorized data only.
