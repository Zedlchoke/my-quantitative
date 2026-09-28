# OPTIONS_SAMPLE_REPORT — lane CX, Deribit crypto options (keyless public market data)

**LABEL LAW: `PROSPECTIVE_FROM_2026-09-28`.** From-today market-state sample,
NOT historical data; no backtestable-history claim permitted. Scope note:
crypto options (Deribit) only — equity/OpRA options are out of scope for this
lane (licensed vendor needed; no purchase made).

- Sampled: 2026-09-28T02:29–02:30 UTC (receive timestamps per request in raw log)
- Sampler: `research/control/DATA-FOUNDATION-SIXSOURCE-V1/cx/sample_deribit_options.py`
- Raw root (outside git): `~/.my-quantitative-data/sixsource-foundation-v1/options/`

## 1. License screen (recorded BEFORE first call)

| Item | Value |
|---|---|
| Docs/terms URLs | https://docs.deribit.com/ (markdown mirrors: `/articles/authentication.md`, `/articles/api-usage-policy.md`, `/articles/rate-limits.md`); site terms https://www.deribit.com/pages/terms (JS-rendered; title verified only) |
| Verified quote 1 | "Public API methods (market data, etc.) do not require authentication" — Authentication article |
| Verified quote 2 | "All API traffic, whether authenticated or public, must follow Deribit's broader trading-integrity rules" (OTV + anti-abuse); market-data polling should prefer WebSocket; excessive usage → stricter rate limits — API Usage Policy |
| One-line ruling | Keyless public market-data access permitted under fair-use policy; ≤25 sequential REST calls at ≥1 s spacing, internal research only; **no explicit redistribution clause was located in the pages screened (disclosed)** — sample is not redistributed beyond this lane's evidence root. |
| Screened at | 2026-09-28, before the first request |

Stop conditions: none triggered (no auth demand, no paywall).

## 2. Chain membership census (request 1, HTTP 200)

`GET /api/v2/public/get_instruments?currency=BTC&kind=option&expired=false`

- **988 live BTC option instruments across 13 listed expiries.**
- First four expiries (all 08:00 UTC daily expiries): 2026-09-28 (58 instruments,
  29 strikes, 29C/29P), 2026-09-29 (58, 29), 2026-09-30 (56, 28), 2026-10-01 (56, 28).
- Selected expiry: **2026-09-28T08:00Z (nearest; expires ~5.5 h after sampling)**.
- Selection rule: 5 strikes nearest the census median strike (83,500), each
  call+put → 10 instruments; names taken **verbatim from the census payload**
  (an earlier attempt constructed `BTC-20260928-…` names and got
  `-32602 Invalid params` — Deribit uses `DDMONYY` tokens, e.g. `BTC-28SEP26-83000-C`;
  the failed attempt's raw file is preserved as evidence).

## 3. Quote sample (10 tickers, requests 2–11, all HTTP 200)

Instruments: `BTC-28SEP26-{83000,83500,84000,84500,85000}-{C,P}`

| Field presence | Count |
|---|---|
| `mark_iv` / `bid_iv` / `ask_iv` | 10/10 |
| Greeks (`delta`,`gamma`,`vega`,`theta`,`rho` in `greeks`) | 10/10 |
| Two-sided quotes (`best_bid_price`+`best_ask_price`) | 10/10 |
| Exchange `timestamp` (ms) | 10/10 |
| `underlying_price` / `index_price` / `underlying_index` | 10/10 (e.g. 83,650.39 / 83,650.19 / `BTC-28SEP26`) |

Representative row (verbatim from `BTC-28SEP26-84000-P`, state `open`):
bid 0.0046 ×15.0 / ask 0.0055 ×15.0; mark 0.0052; mark_iv 25.38 (bid_iv 17.80,
ask_iv 29.46); greeks delta −0.74302, gamma 0.00061, vega 6.75778, theta
−85.75191, rho −0.39295; timestamp 1790562579213 ms.

Timestamps: exchange `timestamp` (ms, quoted above) vs local `receive_utc` per
request are both recorded for every row in the raw file, enabling exchange-vs-
receive clock-offset checks on this sample (not generalized).

Budget: 11/25 requests this run (≥1 s sequential, observed ~0.35–0.55 s
latencies); session total including the failed first attempt: 13 requests
(1 census + 1 bad ticker + 1 census + 10 tickers). df check 25.27 GiB free (floor 5 GiB).

## 4. Authority claims

CAN claim (measured): the keyless Deribit public API returns full option-chain
membership (988 instruments / 13 expiries for BTC options at sample time) and,
for the 10 sampled near-ATM instruments of the nearest expiry, complete quote
state — two-sided prices, IV surface quotes (mark/bid/ask), all five Greeks,
underlying/index prices and exchange timestamps — as AS-OF-NOW state on 2026-09-28.
CANNOT claim: anything historical (label law); any representation of the IV
surface or greeks beyond the 10 sampled rows and one point in time; no
redistribution beyond internal research (screened pages located no explicit
redistribution clause — recorded as a limitation, not a permission).

## 5. Artifacts

| Artifact | Path | Status |
|---|---|---|
| Sampler | `research/control/DATA-FOUNDATION-SIXSOURCE-V1/cx/sample_deribit_options.py` | AVAILABLE_VALIDATED (11/11 HTTP 200 run) |
| Raw (final run) | `~/.my-quantitative-data/sixsource-foundation-v1/options/Deribit_sample_20260928T022945Z.json` | AVAILABLE_VALIDATED |
| Sanitized rows | `~/.my-quantitative-data/sixsource-foundation-v1/options/Deribit_sample_20260928T022945Z_rows.json` | AVAILABLE_VALIDATED |
| Raw (first attempt, census + 400 error evidence) | `~/.my-quantitative-data/sixsource-foundation-v1/options/Deribit_sample_20260928T022829Z.json` | AVAILABLE_UNVALIDATED (superseded evidence, preserved) |
| Manifest (sha256, all sample files) | `~/.my-quantitative-data/sixsource-foundation-v1/options/options_manifest.json` | AVAILABLE_VALIDATED |
