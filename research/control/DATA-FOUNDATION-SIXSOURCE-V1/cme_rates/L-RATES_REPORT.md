# L-RATES REPORT — CME transport re-measure + rates daily-vs-intraday (2026-09-28)

Lane of DATA-FOUNDATION-SIXSOURCE-V1 (P3). Full transcript:
`probe_transport_transcript.json` (etched ~2026-09-28T02:00–02:05Z).

## CME reachability — BLOCKED_TRANSPORT re-confirmed (fresh discrimination)

Standing constraint L-FXFF-1 re-measured on the CURRENT network path:

1. DNS resolves normally (Akamai edge 23.210.101.168) — no DNS-level block.
2. With SNI `www.cmegroup.com`: TLS completes, then the response is
   killed — HTTP/2 stream reset `INTERNAL_ERROR` (0 bytes, 0.31 s);
   HTTP/1.1 variant silently stalls 20 s with 0 bytes.
3. **No-SNI handshake to the same edge IP: TLS 1.3 completes in 0.07 s**
   (cert served). The filter is keyed to the SNI hostname, not to the
   IP/TCP/TLS path. (Control: nyfed edge also Akamai; its no-SNI failure
   is the edge's normal SNI-required behavior, while WITH-SNI nyfed
   serves HTTP 200 — proving egress is otherwise healthy.)
4. `marketdata.cmegroup.com` does not exist in public DNS (NXDOMAIN).

Verdict: **BLOCKED_TRANSPORT (SNI-keyed), unchanged from FXF-F/FIBV1
measurements, now re-proven 2026-09-28 with the discrimination
experiment recorded.** Not bypassed; no further requests made to the
estate. This is an environment/network-path property, not a license
finding; CME market data additionally carries license/subscription
requirements that are owner-only decisions regardless of transport.

## Rates: daily-published vs intraday (the distinction, measured)

- **NY Fed reference rates (EFFR/SOFR family): REACHABLE, HTTP 200,
  official.** Sample: EFFR effectiveDate 2026-09-24, percentRate 3.88 %,
  percentiles + target range + volume served,
  `revisionIndicator` machine-served (PIT revision flag present in the
  payload). These are **publication-day daily aggregates** — usable as
  daily conditioning series, NOT as an intraday leg.
- **Intraday rate-market reaction (ZQ 30-Day Fed Funds / SOFR futures
  quotes / Treasury futures): still 0 bytes program-wide** (re-affirms
  DTP-FX-MECHCOURT B-leg ruling). The only measured paths: CME Globex
  data (transport-blocked here + license) or a licensed broker-grade
  venue. No candle/proxy substitution permitted (A7-F1 law).

## Six-source taxonomy contribution

| Source | Status |
|---|---|
| CME (any market data) | BLOCKED_TRANSPORT (SNI-keyed; re-measured 2026-09-28; owner network action or ISP contact — never bypass) |
| SOFR/EFFR daily (NY Fed official API) | AVAILABLE_VALIDATED (official 200 + revisionIndicator in payload; daily-only granularity, labeled) |
| Rates intraday (futures quotes) | BLOCKED_TRANSPORT + BLOCKED_LICENSE (needs CME path + entitlement, or alternative licensed venue) |
