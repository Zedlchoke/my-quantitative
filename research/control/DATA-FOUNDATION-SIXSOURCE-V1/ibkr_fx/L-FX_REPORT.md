# L-FX REPORT — IBKR FX cost-band, read-only (2026-09-28)

Lane of DATA-FOUNDATION-SIXSOURCE-V1 (P1). Collector:
`collect_fx_ticks.py` sha256 `b35e2d7c58985d29…` — raw-ibapi,
whitelist-literal: reqCurrentTime, reqContractDetails,
reqMarketDataType(1), reqMktData, reqTickByTickData("BidAsk") +
cancels + disconnect. **No order function exists in the file**
(placeOrder/cancelOrder/whatIf absent by construction). Port 7497
(paper) only. Account id never printed (count + sha256-12 only).

## Sessions

| Session | Window (UTC) | Status | Evidence |
|---|---|---|---|
| s0_verify attempt 1 | 2026-09-28T02:02Z | ENGINEERING_FAIL (Decimal crash killed reader thread mid-session; partial raw kept, never used as data) | `raw_s0_verify_20260928T020226Z.ndjson` (82 B) — incident disclosed |
| **s0_verify (attempt 2)** | 2026-09-28T02:03:37–02:08:38Z (~303 s) | COMPLETE (status label says DISCONNECTED_MID_STREAM — cosmetic bug: my own cleanup disconnect tripped the trap; full window streamed, fixed for later runs) | `sanitized_s0_verify_20260928T020329Z.json`; raw sha256 `789e7e45318a86a2…`, 1,990,131 B |
| fix_window | 2026-09-28T14:50–15:15Z | SCHEDULED (in-app automation, one-shot) | pending |
| rollover_window | 2026-09-28T20:50–21:20Z | SCHEDULED (detached runner pid class + collector self-writes sanitized; target = 17:00 ET rollover) | pending |

## Verification verdict (S0)

- **Two-sided LIVE (mdt=1) quotes on all 5 pairs — INDEPENDENTLY
  CONFIRMED.** 1,665/1,982/1,688/1,373/1,776 valid tbt observations
  (EURUSD/GBPUSD/AUDUSD/USDCAD/USDJPY), zero subscription errors.
- Owner's 2026-09-28T01:52Z observation (mdt 1, bid/ask valid, spreads
  0.2/0.6/0.2/0.4/0.4 pip) — reproduced within live variation.
- Read-Only guard did NOT fire this session (no order-channel request
  was made; guard was proven active on 2026-09-26 with error 321).

## Spread distribution (pips; paper book; Sun-evening ET thin liquidity)

| Pair | n valid | p10 | p50 | p90 | min | max | max silence | gaps>2 s |
|---|---|---|---|---|---|---|---|---|
| EURUSD | 1,665 | 0.1 | 0.1 | 0.2 | 0.1 | 0.3 | 8.3 s | 28 |
| GBPUSD | 1,982 | 0.3 | 0.4 | 0.5 | 0.1 | 0.6 | 6.8 s | 20 |
| AUDUSD | 1,688 | 0.1 | 0.1 | 0.2 | 0.1 | 0.3 | 7.3 s | 27 |
| USDCAD | 1,373 | 0.4 | 0.6 | 0.6 | 0.2 | 0.7 | 5.9 s | 25 |
| USDJPY | 1,776 | 0.2 | 0.4 | 0.6 | 0.1 | 0.8 | 5.4 s | 19 |

Hour/DST coverage: ONLY the 02:00–03:00 UTC bucket (Sun 22:00 ET) is
measured. Scheduled: 14–15 Z (fix) and 20–21 Z (rollover). All other
hour-buckets, DST transition windows (EU 2026-10-25, US 2026-11-01) and
scheduled-news windows: **NOT_RUN** — not fabricable from 5 pretty
minutes; the cost-band must be assembled from repeated bounded sessions
across sessions/conditions before any research use.

## Timestamping

- `tbt ts` = IB server stamp (second resolution); `recv_ns` = local UTC
  receive. Skew recv−tbt: p50 ≈ 0.79–0.84 s, max 2.08 s (all pairs).
- Clock offsets via reqCurrentTime (start/end): +1.154 s / +0.069 s.
- Exchange-event time at sub-second precision is NOT served by this
  channel — recorded as `approx` (second-granularity server stamp +
  measured receive skew). No forward-fill anywhere.

## minTick finding (feeds ERRATUM)

- secdef `contractDetails.minTick` declares 5e-05 (0.5 pip) × 4 pairs,
  0.005 (USDJPY) — SAME as Saturday.
- Observed stream granularity is 1e-05 (0.1 pip): spreads of 0.1 pip
  measured on all pairs. Declared minTick ≠ observable quote granularity;
  declared value may govern order-price increments only (untestable —
  orders forbidden).
- → `ERRATUM_2026-09-28_sixsource.md` written beside the Saturday
  verdict (E1: NOT_SUBSCRIBED corrected to market-closure; E2: 0.5-pip
  spread-floor premise contradicted). P3-A verdict NOT reopened (law).

## Cost component ledger (FX majors, this venue)

| # | Component | Class | Evidence |
|---|---|---|---|
| 1 | executable spread (observed) | **MEASURED — streaming, paper book** (this report; continuing sessions scheduled) | S0 + scheduled windows |
| 2 | commission | **UNMEASURED** — needs Activity/Flex statement Trade+Commission rows | owner export (see below) |
| 3/4 | financing swap L/S | **UNMEASURED** — needs Interest Accruals w/ overnight FX | same |
| 5 | triple-swap/weekend | **UNMEASURED** | same |
| 6 | rollover clock | **UNMEASURED** (spread behavior around 21:00 Z being sampled; swap-posting schedule itself needs statement/docs) | rollover_window session |
| 7 | minimum size | **UNMEASURED** via API (secdef returns minSize=null) | statement or docs |
| 8 | tick geometry | secdef 0.5 pip declared; stream 0.1 pip measured | this session |
| 9 | margin | NOT_RUN by law (whatIf forbidden) | — |
| 10 | stress multiplier | inherited frozen 2.0 | lane-F law |
| — | slippage | **UNMEASURED** — needs real fills (creating trades to sample is forbidden) | owner executions only |

## Exact owner document that unblocks components 2–7

IBKR **Activity Statement or Flex Query**, any window containing FX
trades + at least one weekend-spanning overnight FX position (best
window T4–T7 including a weekend), saved as raw bytes to
`~/.my-quantitative-data/ibkr_statement/`. Needed rows: Trades +
Commission, Interest Accruals, (dated rollover entries). Never paste
contents into chat/Git. If no such trades exist yet, DO NOT trade to
create them — the components stay UNMEASURED until organically produced
activity exists.

## Boundaries honored

No orders/whatIf (absent from code), no account id printed, live port
7496 untouched, owner's DT100 probe process untouched, TWS config
unchanged, no scoring/OOS/shadow, sealed surfaces untouched, raw bytes
outside Git with sha256 manifests.
