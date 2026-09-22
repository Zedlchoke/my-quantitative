# EDQ1 — EURUSD source/license survey: owner decision packet (2026-09-22)

Light/read-only Phase-3 work performed under owner instruction of 2026-09-22
("mở đường cho EURUSD... tuyệt đối không vượt qua license bằng suy đoán") while
JEV-REGIME-ROUTER-V2 bulk runs. Read-only browsing only; no sign-ups, no terms
acceptance, no data downloads. Every license claim carries a verbatim quote +
URL in the survey transcript; this packet summarizes the decision surface.

## Current blocker (unchanged, arguably worsened)

`BLOCKED_SOURCE_LICENSE`: Dukascopy site TCU forbids automated acquisition
without prior express written consent AND states the website "may not be used
to construct a database of any kind" nor stored in databases, with downloads
licensed "ONLY for your own personal, non-commercial use". The TCU preamble
("...or any service accessible via this website") can be read to cover the
datafeed host. No datafeed-specific public permission exists. Twelve Data
terms are clear but provide no bid/ask on our tier and prohibit storage
beyond documented timeframes — reconciliation-only, as frozen.

## Survey verdict

No candidate fully documents all six criteria (automated access CLEAR,
bid+ask, >=3y history, storage-for-research CLEAR, clear cost, no brokerage
account) from public pages. Closest: TrueFX, OANDA v20 practice, Polygon.

## The three unblock paths (owner picks ONE — exact decision questions)

1. **TrueFX (Integral)** — tick bid/ask, free, free registration (not a
   brokerage account); license text only visible AFTER login.
   OWNER ACTION: register the free account personally (agent signup is
   prohibited), capture the verbatim license at the historical-downloads
   page, and paste it into this cycle. If it permits storage for internal
   research + programmatic monthly-zip retrieval -> new PRIMARY candidate;
   else discard at zero cost.
2. **Dukascopy written consent** — keep the frozen plan, resolve the blocker
   at its root.
   OWNER ACTION: email Dukascopy Bank SA requesting express written consent
   for automated retrieval of bi5 files from datafeed.dukascopy.com for
   internal non-commercial research (and consent to retain a derived
   research dataset). Consent letter lands in this cycle as license
   authority; silence/decline -> formally abandon the Dukascopy plan.
3. **OANDA v20 practice** — bid/ask/mid candles to ~2005 (verify
   empirically), free practice token, documented rate limits.
   OWNER ACTION: register the free practice account personally and accept
   its terms yourself; then we read OANDA's API Terms (Legal Hub) for
   storage permission and run an empirical M1 depth probe. Runner-up if
   neither 1 nor 2 lands: Polygon/Massive forex BBO quotes (endpoint
   confirmed via archived official docs; tier depth + storage terms need
   reading on an unrestricted network).

## What happens after a path clears

Per the frozen plan and owner law: successor probe 7–14 days FIRST (P1-bis
on the new primary), then stage-2 (3–5y) only after license+schema PASS;
cost authority from measured bid/ask spreads (no invented spread); volume
identity decision (tick_activity_proxy vs dropped) BEFORE any Jev call;
only after `EURUSD_DATA_QUALIFIED` does a new cycle (e.g.
JEV-EURUSD-EXTENSION-V1) open with its own full freeze set and both owner
gates.

Full survey transcript with verbatim quotes and URLs: preserved in the
session evidence of 2026-09-22 (key quotes reproduced in this packet's
source table below).

| Source | Bid/Ask | >=3y | Auto access CLEAR | Storage CLEAR | Cost | Account | Verdict |
|---|---|---|---|---|---|---|---|
| Dukascopy datafeed | Y | Y (2003+) | N (TCU forbids w/o consent) | N (no-database clause) | free | no | UNCLEAR-worse |
| TrueFX | Y (tick) | ~2009+ (3rd-party) | login-gated text | login-gated text | free | free reg | UNCLEAR (best fit) |
| OANDA v20 practice | Y (bid/ask/mid candles) | ~2005 (verify) | API is product | not captured | free | free practice | UNCLEAR |
| Polygon/Massive | Y (BBO quotes) | tier-dependent | API is product | not captured | $49+/mo | API key | UNCLEAR |
| HistData | Y (tick only) | Y | silent | silent | free/$7 FTP | no | UNCLEAR (silence≠permission) |
| Twelve Data | N | Y | Y (limits) | N (30-day deletion) | $79+/mo | API key | FAILS |
| Alpha Vantage / Finnhub | N (OHLC) | — | — | — | — | — | FAILS (no bid/ask) |
| Cboe FX / EBS | Y | Y | institutional license | institutional | institutional | institutional | FAILS |
