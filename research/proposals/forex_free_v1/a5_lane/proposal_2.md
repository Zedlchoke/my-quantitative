# FXFV1-A5-P2 — NY-morning USD-factor intraday momentum, flat before rollover

**Label: RESEARCH_CANDIDATE_NOT_LIVE_READY** — research proposal only. No returns, PnL, or backtest has been computed in this lane. Nothing here is live-ready.

## 1. Mechanism

Market intraday momentum — the first part of the session predicting the last part — is documented in US equities by Gao, Han, Li & Zhou (2018, JFE): the first half-hour return predicts the last half-hour, attributed to slow-moving institutional demand and liquidity-provider risk-bearing that do not fully equilibrate within the day. The FX analogue proposed here is economically motivated, not scan-selected: during the **NY morning (09:00–13:00 ET)** the USD absorbs the bulk of US-hours hedging and macro flow — equity-linked USD hedging adjustments, option-related flow after the 10:00 ET NY cut, and slow-moving momentum-chasing leveraged accounts. These flows arrive against liquidity providers who ratchet quotes rather than clear the move, leaving a **partially unarbitrated intraday USD risk premium** that persists into the NY afternoon.

Trade: measure the USD's NY-morning move on the deepest USD pair (EUR/USD); if material (|z| ≥ 1.0), hold the **same direction** into the NY afternoon (entry after 13:00 ET, flat before the 17:00 ET rollover). This is directional USD risk premium with strictly bounded single-pair intraday exposure — deliberately distinct from P1's currency-neutral two-leg structure, with its own falsification rule and trial budget.

## 2. Signal and publication clock

- Fields: Twelve Data H1 **closes only** (EUR/USD anchor; USD/JPY neighbour). No bid/ask, no volume, no rates, no cross-asset data — the USD factor is proxied by the authorized pair's own morning move.
- Bar labeled by UTC open `t`, covers `[t, t+1h)`, complete and publishable at `t+1h`.
- Decision instant = close of the bar closing **13:00 America/New_York**:
  - `r = log close(13:00 ET bar) − log close(09:00 ET bar)` (4 NY-morning bars)
  - `z = r / sd20`, `sd20` = std of the same window return over the **prior 20 trade-dates** (causal; <20 priors ⇒ skip)
  - trade iff `|z| ≥ 1.0` (frozen)
- Direction: continuation — `sign(r)` held (EUR/USD up ⇒ long EUR/USD; down ⇒ short; USD/JPY mirrored consistently in USD-side terms).

## 3. Entry / exit / rollover-flat rule

One trade per trade-date max.

- **Entry (next-allowed-bar):** fill at the close of the bar closing **14:00 ET**. No chasing; no runway ⇒ skip.
- **Exit:** close of the bar closing **16:00 ET** — the last completed H1 bar **strictly before** the 17:00 ET NY rollover. The 16:00–17:00 ET fixing-adjacent bar is never held.
- **Flat rule:** zero exposure at every NY rollover and at the Friday 16:00 ET weekly close (last Friday action bar closes 15:00 ET). No overnight/weekend positions ever ⇒ no financing or rollover accrual.

## 4. Execution model

H1 close granularity; decision 13:00 ET bar close, fill 14:00 ET bar close, exit 16:00 ET bar close (two-bar holding window — the shortest honest expression of the hypothesis). Conservative proxy price (mid/last; contract has no bid/ask), full spread+slippage burden in the frozen cost matrix. Single pair per trade, 1× notional, no stops/limits/partial fills.

## 5. Frozen cost stress matrix (fixed BEFORE any returns)

Proxy half-spread+slippage per side: **EUR/USD 0.9 pip, USD/JPY 1.1 pips**; round trip = 2× side. Pip = 0.0001 (EUR/USD), 0.01 (USD/JPY). Frozen reference rates (constants, not data): EUR/USD 1.10, USD/JPY 110.00. Round trips: EUR/USD **1.6364 bp**, USD/JPY **2.0000 bp**.

This mechanism is single-leg, so the cross-pair both-legs rule is not triggered at ×1; the **×2 tier (3.2727 bp EUR/USD; 4.0 bp USD/JPY) deliberately exceeds any plausible two-leg both-sides charge**, making the matrix double-conservative.

| Configuration | ×1 (bp of notional) | ×1.5 | ×2 |
|---|---|---|---|
| Anchor EUR/USD | 1.6364 | 2.4545 | 3.2727 |
| Neighbour USD/JPY | 2.0000 | 3.0000 | 4.0000 |
| Placebo (yesterday's signal) | 1.6364 | 2.4545 | 3.2727 |

**One-event delay stress:** entry delayed to the 15:00 ET bar close; exit unchanged — holding window shrinks to a single bar. Must survive the delay at the ×1.5 tier.

## 6. Currency neutralization

**Not currency-neutral** — a directional intraday USD risk-premium bet, stated as such. Discipline: (i) one authorized pair per trade at 1× notional, never aggregated; (ii) anchor and neighbour never held simultaneously (no accidental USD-basket stacking); (iii) PnL in USD; (iv) flat before every rollover, so exposure never bridges a financing boundary.

## 7. Anchor / neighbour / placebo control

| Role | Definition | Why it validates / destroys |
|---|---|---|
| **Anchor** | EUR/USD, today's 09:00–13:00 ET move, held 14:00–16:00 ET | Deepest USD market ⇒ cleanest single-pair USD-factor proxy; where US-hours USD flow concentrates and intraday momentum should be most reliable and cheapest to capture. |
| **Neighbour** | USD/JPY, identical rule | Pre-registered a priori: other top-three USD pair, main non-European carrier of USD hedging flow ⇒ weaker but positive trace expected. EUR-only success, or USD/JPY outperforming EUR/USD, undercuts the USD-factor-flow interpretation (JPY intervention/risk-off idiosyncrasies are channel-external) and downgrades the candidate. |
| **Negative control** | **Placebo on the information set**: same rule, but the signal is the **previous trade-date's** 09:00–13:00 ET return (executed today, 14:00→16:00 ET) | Causally valid (no look-ahead) but carries no intraday-premium content beyond slow drift. If the placebo matches the anchor, the effect is multi-day momentum mislabeled as intraday risk premium ⇒ interpretation and candidate destroyed. |

## 8. Falsification rule (pre-registered, one evaluation on the full sample)

Kill if **any** of:
- **F1** anchor hit rate (14:00→16:00 ET move matches signal sign) ≤ 0.50, or sign-test p ≥ 0.05;
- **F2** anchor net mean at ×1.5 ≤ placebo net mean;
- **F3** anchor unprofitable at ×1.5, or profitable at ×1 but not ×2 (cost-fragile ⇒ dead);
- **F4** anchor unprofitable under one-event delay at ×1.5.

Survive as research candidate only if F1–F4 all pass for the anchor; neighbour must be directionally positive; placebo must be flat-to-negative. All outcomes, including kills, reported.

## 9. Expected regimes

- **Works (if real):** trending NY mornings on persistent macro/hedging flow; US sessions that extend the European move.
- **Degrades:** choppy mean-reverting sessions; single digested headline days; expiry-heavy Fridays where the 10:00 ET cut fully clears the morning move by midday.
- **Fails:** risk-off episodes with JPY intervention/safe-haven gaps; 2020-03-style liquidity spirals; afternoons that reverse the morning via dealer inventory unwinds.

## 10. DST session clock spec

America/New_York wall time via zoneinfo per trade date (EST UTC−5 / EDT UTC−4; matches repo goldens in `tests/assets/forex/test_sessions_dst.py`: rollover 22:00Z EST / 21:00Z EDT; weekly close 21:00Z / 20:00Z EDT). Frozen week: Sun 21:00 ET open → Fri 16:00 ET close. Rollover 17:00 ET falls on an H1 boundary; flat at the last completed bar **strictly before** each rollover; Friday flat before the 16:00 ET close. Signal/entry/exit ET labels (13:00/14:00/16:00) resolved per-date — DST-correct across all four annual US/EU transition configurations.

## 11. Exact trial count

**3 configurations**: anchor EUR/USD (1) + neighbour USD/JPY (1) + previous-day placebo (1). Every hyperparameter fixed at exactly one value (window 09:00–13:00 ET, |z| ≥ 1.0, sd20, 14:00 ET entry, 16:00 ET exit). Cost tiers ×{1,1.5,2} and the delay stress are accounting stresses on the same 3 configurations, not extra trials. Lane total across both proposals: **6**.

## 12. Data fields used / forbidden-assumptions check

H1 OHLC for EUR/USD, USD/JPY, closes + UTC open timestamps only; 2020-01-29 → 2026-09-02. **Not used:** bid/ask, ticks, volume (never admissible in FX), rates, rollover/swap data, equity/futures/commodity prices, macro calendars. No look-ahead (causal scaling; placebo itself is no-look-ahead), no intrabar fills/stops, no grid search or outcome tuning, no overnight positions, proxy costs are frozen stress constants — not a claim about live spreads.

## 13. Literature sources

| Source | Claim used | Status |
|---|---|---|
| Gao, Han, Li & Zhou (2018), "Market intraday momentum", *JFE* 129(2):394–414, https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351 | First half of session predicts last half (US equities) — template for the FX mechanism | verified (retrieved 2026-09-03T08:22:25Z); the FX analogue is our hypothesis, not their finding |
| Mancini, Ranaldo & Wrampelmeyer (2013), *JF* 68(5), https://onlinelibrary.wiley.com/doi/10.1111/jofi.12053 | EUR/USD most liquid FX pair ⇒ cleanest USD-factor proxy | verified (retrieved 2026-09-03T08:22:25Z) |
| BIS Triennial Survey 2022, https://www.bis.org/publ/qtrpdf/r_qt2212f.htm | USD/JPY among most-traded pairs ⇒ a-priori neighbour choice | ranking verified; exact digits UNVERIFIED |

**Label: RESEARCH_CANDIDATE_NOT_LIVE_READY**
