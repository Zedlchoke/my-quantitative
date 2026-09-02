# FX2-A3-P1 — Session-boundary liquidity-cycle premium (DST-correct New York rollover window)

Lane: A3 data/provider (market data, quotes, provider/dealer structure). Outcome-blind proposal: no returns, no PnL, no backtest computed. JSON is authoritative; this file is the human narrative of the same content.

## Economic mechanism

Dealer liquidity provision in spot FX is cyclically withdrawn at deterministic clock boundaries of the 24/5 week: the New York 17:00 ET rollover / dealer day-end, and session opens/closes across Asia, Europe and North America. Interbank evidence shows quote arrivals and bid-ask spreads vary systematically with these market opens and closes (Bollerslev & Domowitz 1993), intraday FX volatility carries a large deterministic clock-hour periodic component (Andersen & Bollerslev 1997), and electronic/algorithmic participation is concentrated in specific clock hours (Chaboud, Chiquoine, Hjalmarsson & Vega 2014).

Hypothesis: returns earned over the rollover-boundary clock window differ persistently from returns earned over ordinary clock windows, as compensation for transacting at the hour of maximal liquidity withdrawal. The arm holds the pair across the DST-correct 17:00 ET boundary with direction set only by the trailing same-window drift (same-clock history, never full-day history), volatility-targeted from window-only variance. This is a clock-anchored liquidity-cycle hypothesis, not a directional price view.

## Expected counterparty

Liquidity demanders transacting at the boundary at the day's widest quotes: funds rebalancing at the dealer day-end, hedgers and retail flow rolling at the swap-point reset, dealers flattening inventory before the cut. The strategy is the small liquidity provider on the opposite side.

## Signal fields and publication clock

- Historical bid/ask quotes (tick or <=1-minute bars) for the pair, used for window returns and window spread levels.
- Session/DST clock: America/New_York via zoneinfo (real DST) defining the 17:00 ET boundary instant year-round. Wall-clock labels (fixed UTC offsets) are prohibited for window placement; SYNTHETIC_TEST_ONLY label defaults must never drive windows or fills.
- Trailing same-window drift: mean of the prior 126 rollover-window 1h returns, most recent 5 windows excluded (fixed ex ante purge).
- Publication clock: quotes are instantaneous states of a continuous dealer feed (no delayed publication). Formation is evaluated at the close of the 15-minute bar ending 16:45 America/New_York each business day; only quotes timestamped strictly before that instant may enter. Staleness guard: if the newest quote at formation is older than 60 seconds, the arm abstains that day.

## Formation / holding / rebalance

- Formation: daily, business days only, at the 16:45 ET bar close (zoneinfo-correct).
- Holding: 60 minutes — enter at 16:45 ET bar close, exit at the 17:45 ET bar close, straddling the 17:00 ET rollover widening.
- Rebalance: none within the window; flat outside the window by construction.
- Sizing: volatility-targeted at 10% annualized from window-only variance; direction = sign of the trailing same-window mean; zero position if that mean sits inside its trailing interquartile band (deadband fixed ex ante).

## Pair universe and neutralization

Frozen G10-USD candidates EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD (PLAN section 1). Scoreable arms: EURUSD (anchor), GBPUSD (neighbour). Single-pair arms with no deliberate USD book: exposure is flat outside the daily window and bounded by the window position within the plan's currency caps. Cross-pair neutralization is deliberately not applied — the hypothesis is per-pair clock compensation, not a cross-sectional ranking.

## Expected spread, rollover, turnover

- Spread: adverse by design — both legs execute inside/adjacent to the documented daily spread-widening window, so cost per round trip is expected above the pair's 24h average; the premium must clear this after bid/ask execution modeling. Midpoint-only measurement is DIAGNOSTIC_ONLY and can never support an executable claim (PLAN section 2).
- Rollover: each daily round trip straddles the 17:00 ET cut and should accrue one swap event per day. Attribution requires an authoritative historical swap schedule — UNAVAILABLE in the repo; blocking until authorized.
- Turnover: about 260 round trips per pair per year; about 520 across the two scoreable arms.

## Anchor, neighbour, causal negative control

- Anchor — EURUSD, the DST-correct rollover-window volatility-targeted same-window-drift arm. Why it validates: the deepest, tightest-quoted pair on any dealer panel; if a clock-anchored liquidity premium exists anywhere, it is most cleanly measurable there.
- Neighbour — GBPUSD, identical rule and window, no re-tuning. Why it validates: same dealer panel structure, same 17:00 ET dealer day-end, near-identical session-cycle participation; the mechanism predicts the same-signed premium, attenuated, with its own noise.
- Causal negative controls, fixed ex ante: (C1) identical rule with the window shifted +6 hours into the mid-session liquidity plateau (no boundary event); (C2) identical rule with the window placed by a fixed UTC-5 offset year-round instead of zoneinfo, drifting one hour off the true rollover in EDT months. Why they destroy: a boundary-compensation premium must vanish in C1 and attenuate exactly in EDT months in C2; survival means the effect is generic intraday drift, falsifying the mechanism.

## Expected regimes and falsification

Expected: the premium concentrates in liquidity-scarcity regimes (stress episodes such as 2008 and 2020) and is near zero in calm regimes; boundary spread widening deepens in stress, raising the bar the premium must clear. Falsified if: the +6h control shows an indistinguishable premium; the DST-naive clock shows no EDT attenuation; the premium vanishes after schedule-only bid/ask cost accounting; it appears only in midpoint measurement; or it is uniform across stress and calm regimes (no liquidity-risk link).

## Macro/session external-validity risks

- Rollover conventions are dealer-specific (16:59 vs 17:00 cuts, different swap-crediting instants); findings are scoped to the frozen provider's panel and must not be labeled "the global FX market" (BIS Triennial 2022: decentralized OTC market, USD 7.5 trillion/day April 2022).
- Local dealer participation differs by pair (AUDUSD/NZDUSD Asia sessions); a uniform NY-cut window may carry different content per pair.
- Fixed clock hours coincide with scheduled macro releases at other hours; the 17:00 ET window is fixed ex ante and must never be re-selected after observing returns near NFP/FOMC hours.
- Holiday-thinned sessions distort the window; repo holiday tables are SYNTHETIC_TEST_ONLY, so holiday robustness cannot be authoritatively assessed today.
- Secular microstructure change (algorithmic share, spread compression) may time-vary the premium.

## Exact trial count

Exactly 2 scoreable arms (anchor EURUSD, neighbour GBPUSD). Controls C1/C2 and midpoint diagnostics are non-scoreable falsification diagnostics. No post-score arm replacement.

## Required PIT fields and availability (measured repo facts)

| Field | Source | Availability |
|---|---|---|
| Historical bid/ask quotes (tick or <=1m), EURUSD + GBPUSD | owner-authorized institutional quote provider, or owner-supplied normalized Parquet with provider documentation (PLAN section 2) | UNAVAILABLE — 0 of 7 pairs; no entitlement; fail-closed. Feasibility-blocked until owner authorizes data. |
| Rollover/swap schedule (historical, per pair, per value date) | provider financing documentation (PLAN section 2) | UNAVAILABLE — no authority in repo. Blocking for rollover attribution. |
| Holiday tables | authoritative holiday sources per currency (PLAN section 2) | SYNTHETIC_TEST_ONLY — descriptive use only. |
| Session/DST clocks (America/New_York rollover instant) | repo session correctness contracts; zoneinfo | AVAILABLE — contracts implemented, zoneinfo DST real; wall-time labels are SYNTHETIC_TEST_ONLY defaults and prohibited for window placement (this prohibition is control C2). |
| PIT macro vintages (rates, CPI, releases) | none required | UNAVAILABLE in repo, but not a dependency — the thesis deliberately uses quote/clock information only. |

## Literature sources

1. Andersen, T.G. & Bollerslev, T. (1997), "Intraday Periodicity and Volatility Persistence in Financial Markets", Journal of Empirical Finance 4(2-3), 115-158. https://www.sciencedirect.com/science/article/pii/S0927539897000042 — retrieved 2026-09-02T23:50:00Z — claim: large deterministic intraday periodicity in FX volatility tied to the 24h cycle dominates short-horizon dynamics.
2. Bollerslev, T. & Domowitz, I. (1993), "Trading Patterns and Prices in the Interbank Foreign Exchange Market", Journal of Finance 48(4). https://doi.org/10.1111/j.1540-6261.1993.tb04760.x — retrieved 2026-09-02T23:50:00Z — claim: quote arrivals and bid-ask spreads vary systematically with Asia/Europe/North-America market opens and closes.
3. Chaboud, A.P., Chiquoine, B., Hjalmarsson, E. & Vega, C. (2014), "Rise of the Machines: Algorithmic Trading in the Foreign Exchange Market", Journal of Finance 69(5), 2045-2084. https://doi.org/10.1111/jofi.12186 — retrieved 2026-09-02T23:50:00Z — claim: FX activity and algorithmic participation vary strongly across the 24-hour clock.
4. Bank for International Settlements (2022), "BIS Triennial Central Bank Survey", https://www.bis.org/statistics/rpfx22.htm — retrieved 2026-09-02T23:50:00Z — claim: decentralized OTC FX market, USD 7.5 trillion/day April 2022 (net-net); one feed is not the global market.

A further candidate source (Chaboud, Chernenko & Wright on FX trading activity and expected returns) could not be verified during the bounded search window (search rate limit) and was therefore NOT used and NOT built upon, per the source-verification rule.

## Prohibited shortcut check

- RSI/EMA parameter grids without mechanism: NOT APPLICABLE — no price-indicator parameters; the only anchor is the dealer-convention boundary, fixed ex ante; no grid searched.
- Single-provider volume treated as global FX volume: NOT APPLICABLE — no volume field used; quotes are one dealer panel per PLAN section 2.
- Carry computed from today's rate applied historically: NOT APPLICABLE — no rates or swaps in the signal; rollover attribution requires an authoritative historical schedule (declared UNAVAILABLE/blocking).
- Session filters selected after seeing profitable hours: NOT APPLICABLE — window fixed by dealer convention before any return observation; pre-registered +6h and DST-naive controls catch post-hoc selection.
- Midpoint backtests labeled executable: NOT APPLICABLE — executable claims require bid/ask fills; midpoint results stay DIAGNOSTIC_ONLY.

## Ancestry statement

New, first-time FX proposal from the A3 data lane. Prior researched families in this repository are crypto funding/momentum mechanisms; no FX family has previously been proposed, scored or rejected here, so there is nothing to rescue. Not a re-labeled carry, trend or session-filter idea: the thesis is clock-anchored liquidity-provision compensation with pre-registered destruction controls, matching PLAN_forex.md section 9 priority space "session/overnight risk premium with correct DST clocks".
