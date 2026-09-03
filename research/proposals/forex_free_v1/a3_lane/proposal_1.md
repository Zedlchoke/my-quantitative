# FXFV1-A3-P1 — London-Open Session Continuation (3-bar post-open momentum, flatten before NY rollover)

**Label: RESEARCH_CANDIDATE_NOT_LIVE_READY.** Outcome-blind F4 proposal; zero returns/backtests computed in this lane; all constants frozen before any scoring.

- Cycle: FOREX-FREE-V1, lane A3, phase F4
- Mechanism group: `session_bounded_price_continuation`
- Pair universe: EUR/USD, GBP/USD, AUD/USD, NZD/USD, USD/JPY, USD/CHF, USD/CAD
- Data: Twelve Data H1 OHLC closes-eligible canonical bars, 2020-01-29 -> 2026-09-02 (~6.59y); H1 OHLC + timestamps only

## 1. Economic mechanism

At the London open (08:00 Europe/London) the largest FX liquidity pool of the trading day arrives — the UK is the largest global FX dealing centre at 38% of global turnover (BIS Triennial Survey 2022). Information and order flow that accumulated over the thin Asian session is repriced when London dealers, clients and algorithms arrive. The signed return of the first **three** completed London-session H1 bars measures the direction of that arrival flow.

Why the effect should persist into the later trading day (within-session continuation):

1. **Slow hedging** — dealers and corporate hedgers adjust hedge ratios with a lag, spreading arrival-flow pressure across hours.
2. **Stop-loss cascades** — stop orders execute in the direction of the prevailing move and create self-reinforcing (but same-signed) cascades (Osler 2003/2005).
3. **Liquidity-provision dynamics** — FX intraday momentum has been documented and attributed to liquidity provision rather than informed trading (Elaut, Lampaert & Froemmel 2018); market-level intraday momentum was established by Gao, Han, Li & Zhou (2018) in futures, with follow-up evidence including currency futures.

The candidate holds the continuation from London mid-morning to the end of the New York afternoon and is **always flat before the 17:00 America/New_York rollover** — no financing, no overnight gap, no weekend exposure by construction.

## 2. Signal (exact, single frozen configuration)

For weekday `d` and London open `L = 08:00 Europe/London` (DST-correct, zoneinfo):

| Step | Definition |
|---|---|
| Reference close | `c0` = close of the last completed H1 bar with end `<= L` (the bar `[L-1h, L)` London) |
| Signal close | `c3` = close of the 3rd London-session bar `[L+2h, L+3h)`; public at `L+3h` = 11:00 London |
| Momentum score | `m = c3/c0 - 1` |
| Position | `m > 0` -> +1 (long base); `m < 0` -> -1; `m = 0` -> no trade |
| Entry fill | close of the NEXT completed bar `[L+3h, L+4h)`; fill instant 12:00 London |
| Flatten | close of the last completed H1 bar with end **strictly before** the same day's 17:00 America/New_York rollover |

Because hourly bars end on whole hours, the flatten bar is the bar ending **16:00 New York wall clock** in both EST (end 21:00Z < 22:00Z rollover) and EDT (end 20:00Z < 21:00Z rollover). Holding window is uniformly 9 completed bars (12:00 London -> 16:00 New York). On Friday the last in-session bar is the 16:00 New York weekly-close bar, so the flatten rule coincides with the frozen Friday 16:00 America/New_York week close and never spans the weekend.

London's UTC offset is always a whole hour (+0/+1), so `L` always coincides with an H1 bar boundary; the implementation must assert this alignment and fail closed otherwise. Missing-bar rule (fail closed): any pair-day missing a required bar (c0, c3, entry bar, flatten bar) is skipped as `NO_TRADE` and counted; no interpolation, no signal carry-over. One position per pair per day; no re-entry.

## 3. Execution model

Next-allowed-bar execution, conservative close-to-close: the signal is computed on completed bar `t` only; the earliest fill is the close of bar `t+1`. No intra-bar fills, no open-of-bar assumptions. Under cost cell S3 one additional one-bar delay is applied (fill at `t+2` close).

## 4. Frozen cost stress matrix (declared before any returns)

Conservative **proxy** costs chosen a priori; not measured, not evidence of achievable execution, no bid/ask series exists in the contract.

| Cell | Spread-proxy per side | Round trip | Extra delay |
|---|---|---|---|
| S1 (base) | x1.0 -> 1.50 bps | 3.00 bps | none |
| S2 | x1.5 -> 2.25 bps | 4.50 bps | none |
| S3 (worst) | x2.0 -> 3.00 bps | 6.00 bps | one-event (entry +1 bar) |

## 5. Anchor / neighbour / negative control

- **Anchor**: London-open 3-bar continuation exactly as above, all 7 pairs. *Validates* the proposal if, at S1, net expectancy is positive on a majority of pairs with the predicted ordering anchor >= neighbour >= control.
- **Neighbour (theoretically justified)**: New York-open analogue, identical construction anchored at 08:00 America/New_York (signal 11:00 New York, fill 12:00 New York, same flatten rule). Theory: the NY open is the second-largest daily liquidity event (US is the second-largest dealing centre; the NY/late-London overlap is the turnover peak), so the same arrival-repricing friction should give a **same-signed, weaker** effect (the informational gap across the London midday is smaller than across the Asian night). *Validates*: same-signed weaker effect shows generalization across liquidity events, monotone in the size of the arrival. *Destroys*: opposite-signed neighbour on >= 4/7 pairs implies a London-bar artifact rather than a mechanism.
- **Negative control (causal)**: sign-flipped anchor (fade the London move), identical timing, costs and universe. *Destroys*: control >= anchor net per-trade expectancy on >= 4/7 pairs at S1 means the effect is not causal continuation (close-series artifact suspicion) and the proposal fails.

## 6. Falsification rule (preregistered; thresholds frozen now; evaluated once in F8)

REJECT if any of:

- **F1a** (causal control): at S1, sign-flipped control's mean net per-trade return >= anchor's on >= 4 of 7 pairs.
- **F1b** (cost stress): at S3 (x2 + one-event delay), anchor cumulative net return < 0 on >= 5 of 7 pairs.
- **F1c** (neighbour contradiction): neighbour's mean net per-trade return opposite-signed to anchor on >= 4 of 7 pairs.
- **F1d** (DST robustness; diagnostic on anchor trades, not a new trial): if anchor mean net per-trade return flips sign between EDT-computed and EST-computed session-day subsets on >= 5 of 7 pairs, the effect is a clock artifact -> REJECT.

Necessary survival: anchor cumulative net return > 0 at S1 on >= 5/7 pairs AND ordering anchor >= neighbour >= control (neighbour same-signed, may be weaker) on a majority of pairs. No other analysis may be scored; a failed rule is terminal.

## 7. Expected regimes, trials, boundaries

- **Expected to work**: macro-flow regimes — data-release weeks, policy-repricing weeks, directional post-Asian days, high overlap volatility.
- **Expected to fail**: holiday-thinned ranges (late December, mid-August), post-central-bank consolidation, intervention episodes (JPY, CHF).
- **Exact trial count**: 21 scored trials = 3 variants x 7 pairs, each scored once over the full sample. The 3-column cost matrix re-costs identical trade streams (no new trials); F1d is a diagnostic partition (no new trials). No parameter grid exists for this proposal: one momentum window (3 bars), two anchors (London, NY), one control.
- **Forbidden assumptions**: no bid/ask used (proxy stress only); no volume; no financing (flat strictly before every rollover); no overnight/weekend positions; no look-ahead (completed bars only, next-bar fills); no outcome-based tuning (zero returns computed in this lane).

## 8. DST / session clock spec

Week window Sunday 21:00 America/New_York -> Friday 16:00 America/New_York (frozen; identical to `DEFAULT_FX_WEEK_CONVENTION` in `research/assets/forex/sessions.py`); session anchors 08:00 Europe/London and 08:00 America/New_York declared a priori and frozen for the cycle; daily rollover 17:00 America/New_York; all instants via zoneinfo named zones (DST-correct, never fixed offsets); nonexistent wall times fail closed; Sunday open maps to Monday's FX trading day and carries no session signal.

## 9. Literature

| Source | Claim used | Retrieval (UTC) |
|---|---|---|
| Gao, Han, Li & Zhou (2018), "Market Intraday Momentum", JFE 129(2), 394-414. https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351 | First half-hour market return predicts last half-hour (futures); template for early-session continuation. | 2026-09-03T07:55Z (WebSearch) |
| Elaut, Lampaert & Froemmel (2018), "Intraday Momentum in FX Markets: Disentangling Informed Trading from Liquidity Provision", J. Financial Markets; SSRN 2694985. https://www.sciencedirect.com/science/article/abs/pii/S1386418116300313 | FX intraday momentum exists and is liquidity-provision-driven. | 2026-09-03T08:05Z (WebSearch) |
| Osler (2003/2005), "Stop-Loss Orders and Price Cascades in Currency Markets", NY Fed Staff Report 150; JIMF 24(2), 219-241. https://www.newyorkfed.org/research/staff_reports/sr150.html | Stop-loss orders execute with the move and create self-reinforcing cascades. | 2026-09-03T07:55Z (WebSearch) |
| BIS (2022), Triennial Central Bank Survey — OTC FX turnover April 2022; Bank of England national results. https://www.bis.org/publications/202210-commentary-otc-derivatives | UK 38% of global FX turnover (largest centre); US second — justifies London/NY anchors. | 2026-09-03T08:05Z (WebSearch) |

All retrieval timestamps approximate to the search session 2026-09-03T07:55-08:15Z; claims paraphrased from abstracts/releases, not full texts.
