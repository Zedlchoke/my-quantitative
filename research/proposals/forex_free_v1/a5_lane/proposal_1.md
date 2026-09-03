# FXFV1-A5-P1 — EUR-core intraday lead-lag propagation (London–NY overlap), two-leg USD-neutral

**Label: RESEARCH_CANDIDATE_NOT_LIVE_READY** — research proposal only. No returns, PnL, or backtest has been computed in this lane. Nothing here is live-ready.

## 1. Mechanism

The USD factor is discovered first in EUR/USD — the single most liquid FX venue (Mancini, Ranaldo & Wrampelmeyer 2013; BIS Triennial 2022: EUR/USD ~1/4 of global turnover vs GBP/USD ~1/10, USD the dominant vehicle currency). Periphery USD pairs (GBP/USD, AUD/USD) are quoted and traded off the core: dealers re-hedge EUR exposure with a lag and real-money periphery flow works orders over tens of minutes. When a material USD-factor move builds inside the **London–NY overlap (08:00–12:00 ET, the deepest liquidity window)**, the periphery pair has only partially adjusted by window end. That residual is a transient **intraday relative risk premium** that decays over the following hours.

Trade: after a material EUR/USD overlap-window move, **long the lagging periphery leg against a short EUR/USD leg of equal USD notional** (economic equivalent of a short EUR/GBP or EUR/AUD cross built exclusively from authorized pairs) — buy the pair that has not yet caught up to the USD move already priced in the core.

The lead-lag **direction is fixed ex ante by market structure** (deep core leads thin periphery), not scan-selected. Lead-lag structure in FX intraday data is documented (Basnarkov et al. 2019), but the specific EUR→GBP direction at 1–4h horizons is **UNVERIFIED** in prior literature — hence the pre-registered reversed-direction causal control.

## 2. Signal and publication clock

- Fields: Twelve Data H1 **closes only** (EUR/USD lead; GBP/USD or AUD/USD follower). No bid/ask, no volume, no rates. High/low deliberately unused.
- Bar labeled by UTC open `t`, covers `[t, t+1h)`, complete and publishable at `t+1h`.
- Signal evaluated at the close of the bar closing **12:00 America/New_York** on the trade date:
  - `r_eur = log close(12:00 ET bar) − log close(08:00 ET bar)` (4 overlap bars)
  - `z = r_eur / sd20`, `sd20` = std of the same window return over the **prior 20 trade-dates** (causal; <20 priors ⇒ skip)
  - trade iff `|z| ≥ 1.0` (frozen materiality filter)
- All inputs strictly available at the decision instant. DST-correct: ET labels resolved via zoneinfo per date.

## 3. Entry / exit / rollover-flat rule

One trade per trade-date max. Direction: `sign(r_eur)` — EUR/USD up ⇒ **short EUR/USD + long follower**; EUR/USD down ⇒ mirror.

- **Entry (next-allowed-bar):** fill at the close of the bar closing **13:00 ET** (first completed bar after the decision). No intrabar fills, no chasing; if the entry bar would be the last strictly-before-rollover bar, the trade is skipped.
- **Exit:** close of the bar closing **16:00 ET** — the last completed H1 bar **strictly before** the 17:00 ET NY rollover. The 16:00–17:00 ET fixing-adjacent bar is never held.
- **Flat rule:** zero exposure at every NY rollover and at the Friday 16:00 ET weekly close (last Friday action bar closes 15:00 ET). No overnight/weekend positions ever ⇒ no financing or rollover accrual of any kind.

## 4. Execution model

H1 close granularity; decision at close of bar `t`, fill at close of bar `t+1`. Fills at the conservative proxy price (mid/last; the contract has no bid/ask) — the whole spread+slippage burden sits in the frozen cost matrix. Equal USD notional per leg (50/50). No stops, limits, or partial fills.

## 5. Frozen cost stress matrix (both legs, fixed BEFORE any returns)

Proxy half-spread+slippage per side: **EUR/USD 0.9 pip, GBP/USD 1.3 pips, AUD/USD 1.3 pips**; round trip = 2× side. Pip = 0.0001. Frozen reference rates (constants, not data): EUR/USD 1.10, GBP/USD 1.30, AUD/USD 0.65.

Round trips: EUR/USD 1.8 pips = **1.6364 bp**, GBP/USD 2.6 pips = **2.0000 bp**, AUD/USD 2.6 pips = **4.0000 bp**. Cross-pair ⇒ **both legs pay entry + exit**; book cost = average of leg RT bps.

| Configuration | ×1 (bp of book) | ×1.5 | ×2 |
|---|---|---|---|
| Anchor EUR→GBP | 1.8182 | 2.7273 | 3.6364 |
| Neighbour EUR→AUD | 2.8182 | 4.2273 | 5.6364 |
| Negative control GBP→EUR | 1.8182 | 2.7273 | 3.6364 |

**One-event delay stress:** entry delayed one further completed bar (13:00→14:00 ET close), exit unchanged; a configuration must survive the delay at the ×1.5 cost tier.

## 6. Currency neutralization

Equal-and-opposite USD notionals ⇒ net USD delta ≈ 0 at entry; the position is a relative EUR-vs-follower value bet (authorized-pairs build of a EUR cross). Residual USD drift inside the holding window is risk, not neutralized further. PnL in USD; 1× notional; anchor and neighbour never held simultaneously.

## 7. Anchor / neighbour / negative control

| Role | Definition | Why it validates / destroys |
|---|---|---|
| **Anchor** | EUR/USD → GBP/USD, as specified | Most a-priori-linked follower: same session, same European risk block, highest documented EUR spillover. Where core-first discovery should be strongest. |
| **Neighbour** | EUR/USD → AUD/USD, identical rule | Pre-registered by market structure: next periphery with least commodity idiosyncrasy (NZD more land/commodity-idiosyncratic; CAD oil-specific; JPY/CHF funding-driven). Same channel ⇒ weaker but positive trace expected. Anchor-only or neighbour-only success is indistinguishable from mining. |
| **Negative control** | **Reversed direction**: GBP/USD window move drives long EUR/USD + short GBP/USD | No market-structure reason for the discovery venue to follow GBP. An edge here ⇒ generic continuation or artifact ⇒ interpretation destroyed. Anchor must beat it. |

## 8. Falsification rule (pre-registered, one evaluation on the full sample)

Kill if **any** of:
- **F1** anchor sign-agreement hit rate (follower 13:00→16:00 ET move matches signal sign) ≤ 0.50, or sign-test p ≥ 0.05;
- **F2** anchor net mean trade return at ×1.5 ≤ negative-control **gross** mean;
- **F3** unprofitable at ×1.5, or profitable at ×1 but not ×2 (cost-fragile);
- **F4** unprofitable under one-event delay at ×1.5.

Survive as research candidate only if F1–F4 all pass for the anchor; neighbour must be directionally positive; control must be flat-to-negative. All outcomes, including kills, reported.

## 9. Expected regimes

- **Works (if real):** flow-driven normal-vol weeks; high EUR/USD share of USD-pair variance.
- **Degrades:** NFP/CPI/FOMC/divergence days where periphery re-prices simultaneously — *not* filtered ex ante; the statistics must survive them untreated.
- **Fails:** commodity shocks (AUD neighbour), 2020-03-style liquidity spirals, GBP/AUD idiosyncratic news dominating the 3-hour window.

## 10. DST session clock spec

America/New_York wall time via zoneinfo per trade date (EST weeks UTC−5, EDT weeks UTC−4; spring-forward 2026-03-08 07:00Z, fall-back 2026-11-01 06:00Z — matches repo goldens in `tests/assets/forex/test_sessions_dst.py`). Frozen week: Sun 21:00 ET open → Fri 16:00 ET close. Rollover 17:00 ET (22:00Z/21:00Z) falls on an H1 boundary; position flat at the last completed bar **strictly before** each rollover; Friday flat before the 16:00 ET close. Signal (12:00), entry (13:00) and exit (16:00) ET labels self-adjust across all four annual US/EU DST configurations.

## 11. Exact trial count

**3 configurations**: anchor EUR→GBP (1) + neighbour EUR→AUD (1) + reversed control GBP→EUR (1). Every hyperparameter fixed at exactly one value (window 08:00–12:00 ET, |z| ≥ 1.0, sd20, next-bar entry, 16:00 ET exit). Cost tiers ×{1,1.5,2} and the delay stress are accounting stresses on the same 3 configurations, not extra trials. Lane total across both proposals: **6**.

## 12. Data fields used / forbidden-assumptions check

H1 OHLC for EUR/USD, GBP/USD, AUD/USD, closes + UTC open timestamps only; 2020-01-29 → 2026-09-02. **Not used:** bid/ask, ticks, volume (never admissible in FX), rates, rollover/swap data, macro calendars. No look-ahead (causal sd20, strictly-later fills), no intrabar fills/stops, no grid search or outcome tuning, no overnight positions, proxy costs are frozen stress constants — not a claim about live spreads.

## 13. Literature sources

| Source | Claim used | Status |
|---|---|---|
| Mancini, Ranaldo & Wrampelmeyer (2013), *JF* 68(5), https://onlinelibrary.wiley.com/doi/10.1111/jofi.12053 | EUR/USD most liquid FX pair; liquidity commonality | verified (retrieved 2026-09-03T08:22:25Z) |
| BIS Triennial Survey 2022, https://www.bis.org/publ/qtrpdf/r_qt2212f.htm | USD vehicle-currency dominance; EUR/USD ~1/4 turnover vs GBP/USD ~1/10 | ranking verified; exact digits UNVERIFIED |
| Basnarkov, Stojkoski et al. (2019), arXiv:1906.10388, https://arxiv.org/abs/1906.10388 | Measurable intraday lead-lag structure among FX pairs | existence verified; **EUR→GBP direction UNVERIFIED** |

**Label: RESEARCH_CANDIDATE_NOT_LIVE_READY**
