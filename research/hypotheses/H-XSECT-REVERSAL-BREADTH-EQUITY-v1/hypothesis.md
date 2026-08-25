# H-XSECT-REVERSAL-BREADTH-EQUITY-v1 — Ten-stock weekly cross-sectional reversal mechanism screen (V8X Cohort E prereg)

**Family:** `cross_sectional_weekly_reversal_breadth_equity` · **Cohort:**
`US_EQUITY_SPOT_1Y_10` (Mode B) · **Stage:**
`S0_EXPLORATORY_BREADTH_SCREEN` · **Owner:** A6 · **Data:** A9
(performance-blind) · **Validator:** A7 · Frozen **before** the first scored
V8 core artifact (PLAN §8).

## Research question (PLAN §8/10)

Does weekly cross-sectional reversal exist at all outside crypto: rank a
frozen ten-stock US large-cap basket by past return over ~3D/7D/14D
formation windows expressed in trading sessions, long the bottom-2 losers /
short the top-2 winners, hold one week, fill next regular-session open?
This is an independent breadth/mechanism screen on a DIFFERENT asset class
with its own clock, cost model and accounting — NOT a symbol addition to
`H-XSECT-REVERSAL-v2`, and NOT derived from any V6/V7/V8 performance.

## Instrument mode honesty (PLAN §10.1)

Mode A (`BINANCE_TRADFI_PERP_1Y`) is expected `NOT_STARTED_DATA_MATURITY`
(the latest repo snapshot shows 0 qualifying stock perpetuals); it is NOT
backfilled by underlying spot and this cohort does not silently substitute
for it. Mode B uses an external provider under a frozen contract:
preferred official Alpaca historical bars or owner-approved equivalent,
read-only environment credentials, provider/feed (`SIP`/`IEX`)/adjustment
mode/`asof`/calendar version/hashes all frozen before score. Provider or
credential unavailable ⇒ `V8X_EQUITY_NOT_STARTED_PROVIDER_BLOCKED`; no
silent fallback to undeclared sources.

## Frozen basket (chosen before performance)

AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AVGO, JPM, XOM; SPY =
measurement-only benchmark (never traded, never ranked).

## Frozen design summary (full contract: candidate.yaml)

Signals use last completed regular-session close before rebalance on the
official US exchange calendar (holidays/early closes fail-closed) — the
crypto Monday 00:00 UTC clock is explicitly NOT assumed for stocks. Fills
at next valid regular-session open. No funding; dividends, splits and
borrow costs accounted separately; raw vs adjusted views reconciled.
Three chronological folds by trading sessions with ≥one-holding-week
purge/embargo. Exactly three normal trials plus the 7D momentum control
(`V8X-E-WMOM-7D-CONTROL`) = four scored candidates, waves X1–X4 (§11.1).

## Labels and constraints

- With only ~52 weekly observations/year this cohort is an exploratory
  mechanism screen ONLY. Best case:
  `V8X_EQUITY_MECHANISM_PASS_EXPLORATORY`; missing point-in-time borrow
  evidence caps the outcome at `MECHANISM_SCREEN_NON_EXECUTABLE`. It can
  never be locked for S1/live.
- Fully separate ledgers/cost models/calendars/statistics from crypto and
  V8 core; no combined PASS (PLAN §11.2).
- If this preregistration lands after any scored V8 core metric exists:
  label `V8X_PREREG_WINDOW_MISSED`; no V8X this sprint.
