# FXFV1-A3-P2 — Late-NY Fade of the Volatility-Standardized Intraday Extension (session-bounded mean reversion)

**Label: RESEARCH_CANDIDATE_NOT_LIVE_READY.** Outcome-blind F4 proposal; zero returns/backtests computed in this lane; all constants frozen before any scoring.

- Cycle: FOREX-FREE-V1, lane A3, phase F4
- Mechanism group: `session_bounded_mean_reversion`
- Pair universe: EUR/USD, GBP/USD, AUD/USD, NZD/USD, USD/JPY, USD/CHF, USD/CAD
- Data: Twelve Data H1 OHLC closes-eligible canonical bars, 2020-01-29 -> 2026-09-02 (~6.59y); H1 OHLC + timestamps only

## 1. Economic mechanism

Intraday FX extensions that have accumulated by early-to-mid New York hours are disproportionately liquidity-driven rather than information-driven:

1. **Stop-loss cascades** execute in the direction of the prevailing move and generate rapid, self-reinforcing but *transient* price cascades (Osler 2003/2005); pressure reverts once the cascade exhausts.
2. **Liquidity-provision dynamics** — FX intraday effects have been attributed to liquidity provision rather than informed trading (Elaut, Lampaert & Froemmel 2018), implying that liquidity-driven move segments are the ones that mean-revert.
3. **Late-day inventory management** — dealers ahead of the 17:00 America/New_York rollover shade quotes to attract offsetting flow, adding systematic late-afternoon counter-pressure.

The strategy: measure the same-day move from the NY-open reference after exactly four completed NY-session H1 bars. When that move is **large relative to the pair's trailing 20-trading-day daily volatility** (frozen gate `|z| >= 1.0`), take the opposite side for the late-NY window (13:00 -> 16:00 New York wall clock) and flatten strictly before the rollover. The volatility gate is the causal discriminator: only standardized-large moves are transient-pressure candidates; small moves are noise/information and are not traded.

## 2. Signal (exact, single frozen configuration)

For weekday `d`, NY open `N = 08:00 America/New_York` (DST-correct, zoneinfo):

| Step | Definition |
|---|---|
| Reference close | `p0` = close of the last completed H1 bar with end `<= N` |
| Signal close | `p4` = close of the 4th NY-session bar; public at 12:00 New York wall clock |
| Extension | `r = p4/p0 - 1` |
| Volatility scale | `sigma` = sample stdev (n-1) of the trailing **20** completed FX trading days' rollover-to-rollover daily log returns (closes of the last completed bar strictly before each 17:00 NY rollover; days strictly before `d`; Sunday open maps to Monday) |
| Standardized gate | `z = r/sigma`; `z >= +1.0` -> short; `z <= -1.0` -> long; `|z| < 1.0` -> no trade |
| Entry fill | close of the NEXT completed bar (5th NY-session bar; fill instant 13:00 New York) |
| Flatten | close of the last completed H1 bar with end **strictly before** 17:00 America/New_York |

The flatten bar is uniformly the bar ending **16:00 New York wall clock** in EST (end 21:00Z < 22:00Z) and EDT (end 20:00Z < 21:00Z); the holding window is uniformly 3 completed bars (13:00 -> 16:00 New York), DST-exact. On Friday the flatten bar is the frozen 16:00 New York weekly-close bar; no weekend exposure. NY's UTC offset is a whole hour, so `N` always coincides with an H1 bar boundary (assert, fail closed otherwise). Warm-up: no trades before 20 completed trading days (~2020-02-26; data-determined, not tuned). Missing-bar rule (fail closed): a pair-day missing any required bar — including any of the 20 sigma-day boundary bars — is skipped as `NO_TRADE` and counted; no interpolation, no carry-over. One position per pair per day.

## 3. Execution model

Next-allowed-bar execution, conservative close-to-close: signal on completed bar `t` only; earliest fill is the close of bar `t+1`. Under cost cell S3 one additional one-bar delay applies (fill at `t+2` close); the flatten rule is unchanged and remains strictly pre-rollover, which stays feasible in every session/DST configuration.

## 4. Frozen cost stress matrix (declared before any returns)

Identical to FXFV1-A3-P1 for cycle comparability. Conservative **proxy** costs chosen a priori; not measured; no bid/ask series exists in the contract.

| Cell | Spread-proxy per side | Round trip | Extra delay |
|---|---|---|---|
| S1 (base) | x1.0 -> 1.50 bps | 3.00 bps | none |
| S2 | x1.5 -> 2.25 bps | 4.50 bps | none |
| S3 (worst) | x2.0 -> 3.00 bps | 6.00 bps | one-event (entry +1 bar) |

## 5. Anchor / neighbour / negative control

- **Anchor**: late-NY fade exactly as above, all 7 pairs. *Validates* if net expectancy is positive on a majority of pairs at S1 with anchor > sign-flipped control and the predicted liquidity-thinness ordering.
- **Neighbour (theoretically justified)**: Tokyo-open analogue, identical construction anchored at 09:00 Asia/Tokyo (signal 13:00 Tokyo, fill 14:00 Tokyo), same `|z| >= 1.0` gate, same 20-day sigma series, same flatten rule. Theory: transient price pressure per unit of flow scales inversely with session liquidity — Tokyo is the thinnest G10 session, so standardized extensions there should revert **at least as strongly** (predicted same-signed, magnitude >= anchor). *Validates*: a Tokyo >= NY fade gradient is a distinctive implication of the pressure mechanism. *Destroys*: no fade in Tokyo (opposite-signed, or same-signed but < 25% of the anchor's mean net per-trade return) on >= 5/7 pairs implies the NY result is a late-session data artifact rather than the stated mechanism.
- **Negative control (causal)**: sign-flipped anchor — buy the standardized extension instead of fading it; identical gate, timing, costs, universe. *Destroys*: control >= anchor mean net per-trade return on >= 4/7 pairs at S1 means gated days behave like intraday-momentum days and the fade mechanism is falsified.

## 6. Falsification rule (preregistered; thresholds frozen now; evaluated once in F8)

REJECT if any of:

- **F2a** (causal control): at S1, sign-flipped continuation control's mean net per-trade return >= anchor's on >= 4 of 7 pairs.
- **F2b** (cost stress): at S3 (x2 + one-event delay), anchor cumulative net return < 0 on >= 5 of 7 pairs.
- **F2c** (liquidity gradient): Tokyo neighbour opposite-signed to anchor, or same-signed but < 25% of anchor's mean net per-trade return, on >= 5 of 7 pairs.
- **F2d** (DST robustness; diagnostic on anchor trades, not a new trial): anchor mean net per-trade return flips sign between EDT-computed and EST-computed session-day subsets on >= 5 of 7 pairs -> clock artifact -> REJECT.

Necessary survival: anchor cumulative net return > 0 at S1 on >= 5/7 pairs AND anchor > sign-flipped control on >= 5/7 pairs. No other analysis may be scored; a failed rule is terminal.

## 7. Expected regimes, trials, boundaries

- **Expected to work**: range-bound low-surprise weeks; one-sided stop-cascade days; late-afternoon inventory-unwind conditions.
- **Expected to fail**: sustained macro-trend weeks (FOMC/ECB/BOJ turning points); intervention episodes (JPY, CHF) where extensions are information; gap days where the 20-day sigma understates the new regime.
- **Exact trial count**: 21 scored trials = 3 variants x 7 pairs, each scored once over the full sample (warm-up data-determined). The 3-column cost matrix re-costs identical trade streams (no new trials); F2d is a diagnostic partition (no new trials). No parameter grid: gate exactly 1.0, window exactly 4 bars, sigma lookback exactly 20 days, anchors exactly NY/Tokyo.
- **Forbidden assumptions**: no bid/ask used (proxy stress only); no volume (volatility scale is return-based); no financing (flat strictly before every rollover); no overnight/weekend positions; no look-ahead (completed bars only; sigma uses strictly prior days); no outcome-based tuning (zero returns computed in this lane).

## 8. DST / session clock spec

Week window Sunday 21:00 America/New_York -> Friday 16:00 America/New_York (frozen; identical to `DEFAULT_FX_WEEK_CONVENTION` in `research/assets/forex/sessions.py`); session anchors 08:00 America/New_York and 09:00 Asia/Tokyo declared a priori and frozen for the cycle; daily rollover 17:00 America/New_York; the sigma series uses the same rollover-to-rollover closes as the strategy clock; all instants via zoneinfo named zones (DST-correct, never fixed offsets); nonexistent wall times fail closed; Sunday open maps to Monday's FX trading day.

## 9. Literature

| Source | Claim used | Retrieval (UTC) |
|---|---|---|
| Osler (2003/2005), "Stop-Loss Orders and Price Cascades in Currency Markets", NY Fed Staff Report 150; JIMF 24(2), 219-241. https://www.newyorkfed.org/research/staff_reports/sr150.html | Stop orders execute with the move and create transient self-reinforcing cascades — the mechanism faded here. | 2026-09-03T07:55Z (WebSearch) |
| Elaut, Lampaert & Froemmel (2018), "Intraday Momentum in FX Markets: Disentangling Informed Trading from Liquidity Provision", J. Financial Markets; SSRN 2694985. https://www.sciencedirect.com/science/article/abs/pii/S1386418116300313 | FX intraday effects are liquidity-provision-driven, supporting the transient-pressure reading of standardized-large extensions. | 2026-09-03T08:05Z (WebSearch) |
| Savaser, "Extreme Returns Without News" — **UNVERIFIED**: surfaced only as a cross-reference snippet (venue/year unconfirmable in this lane); recorded for honesty, not load-bearing. | PER SNIPPET: extreme no-news returns are temporary and mean-revert once cascades exhaust. | 2026-09-03T07:55Z (WebSearch snippet only) |
| BIS (2022), Triennial Central Bank Survey — OTC FX turnover April 2022. https://www.bis.org/publications/202210-commentary-otc-derivatives | Session liquidity hierarchy (UK > US > Asia) grounds the predicted Tokyo >= NY fade gradient. | 2026-09-03T08:05Z (WebSearch) |

All retrieval timestamps approximate to the search session 2026-09-03T07:55-08:15Z; claims paraphrased from abstracts/releases, not full texts.
