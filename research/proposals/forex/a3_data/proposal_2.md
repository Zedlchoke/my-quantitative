# FX2-A3-P2 — Cross-sectional relative-spread scarcity signal (quote-dynamics liquidity imbalance)

Lane: A3 data/provider (market data, quotes, provider/dealer structure). Outcome-blind proposal: no returns, no PnL, no backtest computed. JSON is authoritative; this file is the human narrative of the same content.

## Economic mechanism

Dealer intermediation capacity in FX is currency-specific and balance-sheet constrained. Quoted bid-ask spreads vary systematically with dealer quoting conditions (Bessembinder 1994), and FX liquidity measured from quoted spreads exhibits strong cross-pair commonality plus priced pair-specific variation (Mancini, Ranaldo & Wrampelmeyer 2013).

Hypothesis: when a pair's spread rises relative to (i) its own trailing same-clock-hour norm and (ii) the contemporaneous cross-pair panel median, dealers are rationing intermediation in that currency leg; the scarce currency subsequently earns a positive premium as inventory-risk compensation, while the abundant currency underperforms. The information is in the quote dynamics, not the price: subtracting the contemporaneous panel median z-score removes the common dealer-wide liquidity shock, leaving a pair-specific scarcity state. The tradeable arm is dollar-neutral: long the panel-scarce leg, short the panel-abundant one. Claims are scoped to the frozen provider's panel — a spread state is that panel's intermediation condition, never "global FX volume".

## Expected counterparty

Balance-sheet-constrained dealer intermediaries who widen quotes when rationing a scarce currency, and the flow that pays the widened spread (leveraged funds pushing inventory, corporate hedging flow). They are compensated immediately through the widened quote but not subsequently; the strategy earns the later premium for standing on the provider side.

## Signal fields and publication clock

- Bid/ask quote panel for the 7 frozen G10-USD pairs; pair spread s_i,t = (ask − bid)/mid at each 1-minute timestamp.
- Pair-normalized z-score: z_i,t = (s_i,t − median of s_i over the trailing 63 business days of same-clock-hour quotes) / MAD_i,t. Same-clock-hour conditioning (DST-correct) keeps the deterministic session spread periodicity (Bollerslev & Domowitz 1993) out of the norm.
- Panel-relative scarcity state: q_i,t = z_i,t − median_j(z_j,t) at the same timestamp (removes the common liquidity shock).
- Quote-age field for the staleness gate.
- Publication clock: spreads are instantaneous observable states; lag is zero but staleness is real. Formation is the daily 17:00 America/New_York rollover (zoneinfo-correct). Only quotes strictly pre-timestamped may enter; if any panel pair's newest quote at formation is older than 60 seconds, that pair drops out of the panel median for the day and the arm abstains on it (fail-closed gate). The trade price enters only after the formation instant.
- Prohibited information: no volume, no order flow, no macro vintage, no rate field. Macro vintages are UNAVAILABLE and deliberately not a dependency.

## Formation / holding / rebalance

- Formation: daily at the 17:00 ET rollover instant, business days only.
- Holding: 72 hours, executed as 3 equal staggered tranches initiated on consecutive days (one third of the book turns per day).
- Rebalance: daily staggered rebalance of the expiring tranche only; no intraday re-formation.
- Sizing: long the panel-worst relative-spread percentile leg, short the panel-best, dollar-neutral, volatility-scaled to 8% annualized from a trailing 63-day proxy; the 1-vs-7 extreme quantile construction is fixed ex ante — no ranking grid searched.

## Pair universe and neutralization

All 7 frozen G10-USD pairs form the panel because the scarcity state is defined relative to the panel median. Scoreable arms: EURUSD (anchor) and GBPUSD (neighbour) evaluated within the same panel rule. Dollar-neutral by construction (long scarce vs short abundant through USD pairs); residual USD exposure capped by the plan's currency caps; no crosses required, avoiding the point-in-time cross-coverage gate of PLAN section 1.

## Expected spread, rollover, turnover

- Spread: adverse by construction — entries occur after spreads have already widened, so entry cost is above the unconditional average; the hypothesis requires the 72h premium to exceed that elevated entry spread under bid/ask execution modeling. Midpoint evaluation is DIAGNOSTIC_ONLY (PLAN section 2).
- Rollover: 72h holds accrue roughly 3 rollover events per tranche leg cycle; attribution requires an authoritative historical swap schedule — UNAVAILABLE, blocking until authorized.
- Turnover: about one third of the book per business day, roughly 85 full-book turns per year across the panel.

## Anchor, neighbour, causal negative control

- Anchor — EURUSD inside the panel rule. Why it validates: deepest, most reliable quotes on any dealer panel, minimizing measurement error in the spread state itself.
- Neighbour — GBPUSD inside the same rule, no re-tuning. Why it validates: same dealer panel, same 17:00 ET clock, near-identical interbank quoting structure; the mechanism predicts same-signed, attenuated behavior — agreement supports a dealer-panel mechanism rather than a pair-idiosyncratic quoting artifact.
- Causal negative control — +180-day temporal-shift placebo: replace each pair's spread history with the same series shifted by 180 calendar days before computing the signal. The shift preserves each pair's unconditional spread distribution, intraday periodicity and autocorrelation envelope while destroying timestamp alignment with the evaluation returns. Why it destroys: genuine quote-state information must collapse to noise under the placebo; a surviving premium demonstrates the effect is slow price trend correlated with spread level (price-led contamination), destroying the mechanism. Secondary gate: the A7 pre-window lead-lag check must show the spread state leads, not merely co-moves with, subsequent returns.

## Expected regimes and falsification

Expected: strongest in funding/liquidity stress (2008, 2020, the January 2015 CHF discontinuity) when dealer rationing binds and FX liquidity risk is priced; near zero in calm, competitively quoted regimes. Falsified if: the premium survives the +180-day placebo; it is not monotone in the relative-spread percentile (no dose-response in scarcity); it is uniform across stress and calm regimes; the spread state does not lead returns in the pre-window check; or it exists only in midpoint measurement and vanishes under bid/ask execution accounting.

## Macro/session external-validity risks

- Provider scope: the spread panel is one dealer's quoting behavior; the provider must be frozen before any candidate PnL inspection (PLAN section 2).
- Secular spread compression from electronic competition shifts level regimes; trailing same-hour normalization mitigates but cannot eliminate provider-contract or technology breaks.
- Formation is DST-correct 17:00 ET; SYNTHETIC_TEST_ONLY wall-time labels would silently shift formation across session boundaries in EDT months.
- Holiday-thinned days degrade the panel median; holiday tables are SYNTHETIC_TEST_ONLY, so thin-day treatment cannot be authoritatively gated today.
- Scheduled macro releases cluster near fixed clock hours; no event exclusion may be tuned after observing returns; PIT event vintages are UNAVAILABLE, so event-day robustness is declared untestable rather than assumed benign.
- CHF-type discontinuities can gap through stops; discontinuity handling must be declared at freeze, not adapted after results.

## Exact trial count

Exactly 2 scoreable arms (anchor EURUSD, neighbour GBPUSD within the same panel rule). The +180-day placebo and lead-lag gates are non-scoreable falsification diagnostics. No post-score arm replacement.

## Required PIT fields and availability (measured repo facts)

| Field | Source | Availability |
|---|---|---|
| Historical bid/ask quote panel (tick or <=1m), all 7 G10-USD pairs, aligned | owner-authorized institutional quote provider, or owner-supplied normalized Parquet with documentation (PLAN section 2) | UNAVAILABLE — 0 of 7 pairs; no entitlement; fail-closed. Feasibility-blocked until owner authorizes data. |
| Rollover/swap schedule (historical, per pair) for 72h holds | provider financing documentation (PLAN section 2) | UNAVAILABLE — no authority in repo; blocking for multi-day accounting. |
| Holiday tables | authoritative holiday sources per currency (PLAN section 2) | SYNTHETIC_TEST_ONLY — descriptive use only. |
| Session/DST clocks (America/New_York formation instant; same-hour conditioning) | repo session correctness contracts; zoneinfo | AVAILABLE — contracts implemented, zoneinfo DST real; wall-time labels are SYNTHETIC_TEST_ONLY defaults, prohibited for formation placement. |
| PIT macro vintages (rates, CPI, releases) | none required | UNAVAILABLE in repo, but not a dependency — quote-state-only thesis; event-day robustness declared untestable, not assumed benign. |

## Literature sources

1. Mancini, L., Ranaldo, A. & Wrampelmeyer, J. (2013), "Liquidity in the Foreign Exchange Market: Measurement, Commonality, and Risk Premiums", Journal of Finance 68(5), 1805-1841. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1447869 ; https://ideas.repec.org/p/snb/snbwpa/2010-03.html — retrieved 2026-09-02T23:45:00Z — claim: FX liquidity from quoted spreads shows strong cross-pair commonality and is priced in risk premiums; DOI of the published version not independently verified in this session (working-paper URLs verified).
2. Bessembinder, H. (1994), "Bid-Ask Spreads in the Interbank Foreign Exchange Markets", Journal of Financial Economics 35(3), 317-348. https://www.sciencedirect.com/science/article/pii/0304405X94900361 — retrieved 2026-09-02T23:50:00Z — claim: interbank quotations and spreads vary systematically, documenting dealer quoting/inventory conditions.
3. Bollerslev, T. & Domowitz, I. (1993), "Trading Patterns and Prices in the Interbank Foreign Exchange Market", Journal of Finance 48(4). https://doi.org/10.1111/j.1540-6261.1993.tb04760.x — retrieved 2026-09-02T23:50:00Z — claim: deterministic intraday spread periodicity tied to global session opens/closes, motivating same-clock-hour normalization.
4. Bank for International Settlements (2022), "BIS Triennial Central Bank Survey", https://www.bis.org/statistics/rpfx22.htm — retrieved 2026-09-02T23:45:00Z — claim: decentralized OTC FX market, USD 7.5 trillion/day April 2022 (net-net); a spread panel is not global liquidity or volume.

A further candidate source (Chaboud, Chernenko & Wright on FX trading activity and expected returns) could not be verified during the bounded search window (search rate limit) and was therefore NOT used and NOT built upon, per the source-verification rule.

## Prohibited shortcut check

- RSI/EMA parameter grids without mechanism: NOT APPLICABLE — no price-indicator parameters, no grid; 63-day window, 1-vs-7 quantile and 72h hold are fixed ex ante from the inventory-risk mechanism.
- Single-provider volume treated as global FX volume: NOT APPLICABLE and explicitly inverted — no volume used; the spread panel is strictly one dealer panel's state with scoped claims.
- Carry computed from today's rate applied historically: NOT APPLICABLE — no rate/swap inputs in the signal; rollover accruals require an authoritative historical schedule (declared UNAVAILABLE/blocking).
- Session filters selected after seeing profitable hours: NOT APPLICABLE — the 17:00 ET formation instant and same-hour conditioning are fixed ex ante from dealer convention; the +180-day placebo would expose implicit timing selection.
- Midpoint backtests labeled executable: NOT APPLICABLE — the spread state uses bid/ask by construction; executable claims require bid/ask fills at realized entry spreads; midpoint-only study is DIAGNOSTIC_ONLY.

## Ancestry statement

New, first-time FX proposal from the A3 data lane. Previously researched families in this repository are crypto funding/momentum mechanisms; no FX family has previously been proposed, scored or rejected here, so this is not a rescue or re-labeling of any rejected idea. Not a disguised carry or trend family: the information set is the quote panel's relative-spread state only, the cross-sectional construction follows the documented commonality-plus-priced-liquidity structure of the FX microstructure literature, and quote-dynamics information is exactly the A3 lane's declared expertise under PLAN_forex.md section 9.
