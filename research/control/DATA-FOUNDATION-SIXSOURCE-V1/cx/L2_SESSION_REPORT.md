# L2_SESSION_REPORT — lane CX, Binance spot L2 (BTCUSDT + ETHUSDT)

**LABEL LAW: `PROSPECTIVE_FROM_2026-09-28`.** This is a from-today sample, NOT
historical data. The repo law stands unchanged: no order-book or forced-flow
inference from candles, and nothing in this session may be presented as
backtestable history. It is one bounded 10-minute observation window, single
day, single venue, keyless public feed.

- Session date: 2026-09-28 (window 2026-09-28T02:16:50.009Z → 02:26:49.380Z, 599.4 s)
- Executor: lane CX subagent under `research/control/DATA-FOUNDATION-SIXSOURCE-V1/dispatch/PACKET_lane_cx.md`
- Collector: `research/control/DATA-FOUNDATION-SIXSOURCE-V1/cx/collect_binance_l2.py`
- Raw evidence root (outside git): `~/.my-quantitative-data/sixsource-foundation-v1/crypto_l2/`

## 1. Pre-flight and terms screen (recorded BEFORE first call)

| Check | Result |
|---|---|
| df free (root volume) | 26 GiB at session start (floor 5 GiB) — PASS; 25.1 GiB at collector start |
| Python | `/Users/hoangminhlong/my-quantitative/.venv/bin/python` 3.12.14, aiohttp 3.14.3 |
| Binance API terms URL | https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/rest-api.md (official spec); WS: .../web-socket-streams.md |
| One-line ruling | Official spec: "For APIs that only send public market data, please use the base endpoint https://data-api.binance.vision"; security `NONE` = "Public market data" (no key); HTTP 429 on rate-limit breach; limits per IP. Keyless public market data used well within documented limits; no account, no API key. Screened 2026-09-28, before any request. |

Stop conditions: none triggered. No auth demand, no paywall, no ToS conflict.

## 2. Method

1. REST snapshot `GET {base}/api/v3/depth?symbol=<S>&limit=1000`
   (base: `https://data-api.binance.vision`; fallback `https://api.binance.com` — not needed).
2. WS combined stream `wss://stream.binance.com:9443/stream?streams=btcusdt@depth@100ms/ethusdt@depth@100ms`,
   connected BEFORE snapshots so pre-snapshot events buffer and bridge the gap
   (official diff-sync procedure). Sequential REST, ≥1 s spacing, hard caps:
   ≤30 REST requests, ≤200 MB raw.
3. Sequence verification per event: first applied event must satisfy
   `U <= lastUpdateId+1 <= u`; thereafter require `U == prev_u + 1`.
   **Measured deviation from packet expectation:** the spot diff-depth payload
   carries **no `pu` field** (verified empirically on 11,981 events: 0 `pu`
   fields seen; `pu` is a USDT-M *futures* field). The packet's `U/u/pu` chain
   therefore reduces, for spot, to the official spot U-chain rule; the checker
   verifies `pu` whenever a payload carries one (0 opportunities here) and
   records its absence rather than inventing violations. This finding is
   evidence about the feed schema, not a data-quality defect.
4. Raw ndjson: one line per ws event with `receive_ns`, `stream`, `U`,`u`,`pu`,`E`,
   `bids`,`asks`, plus a first `meta` line; every artifact labeled
   `PROSPECTIVE_FROM_2026-09-28` (label in file name, meta line, manifest, report).
5. On disconnect: reconnect + full re-snapshot (0 such events occurred).
6. NO candle/OHLC substitution anywhere; book stats are snapshot-only per packet.

## 3. Session table (ONE bounded window, 600 s)

| Metric | BTCUSDT | ETHUSDT | Session |
|---|---|---|---|
| Events received (verified) | 5,993 | 5,988 | 11,981 raw lines written |
| Sequence gaps (`U != prev_u+1`) | **0** | **0** | — |
| `pu` violations / `pu` fields seen | 0 / 0 | 0 / 0 | field absent from spot payload |
| Dropped stale (`u <= lastUpdateId`, pre-sync) | 6 | 19 | 25 |
| Dropped pre-snapshot | 0 | 0 | buffered bridging worked |
| First-event sync OK | yes | yes | official rule satisfied |
| Reconnects | 0 | 0 | 0 (0 connect failures) |
| Snapshot host | data-api.binance.vision | data-api.binance.vision | 2/30 REST used |
| Snapshot `lastUpdateId` | 100,742,782,827 | 81,516,903,614 | at 02:16:50.784Z / 02:16:51.947Z |
| Snapshot top-of-book | bid 83718.21 / ask 83718.22 (1000×1000 levels) | bid 2658.95 / ask 2658.96 (1000×1000 levels) | snapshot-only stats |
| WS latency (receive_ms − event `E`): p50 / p95 / max | 0 / 0 / 1633 ms | 0 / 0 / 1633 ms | n = 5,993 / 5,988 |
| Raw bytes | 14,109,556 total (`l2_events_PROSPECTIVE_FROM_2026-09-28_20260928T021649Z.ndjson`) | | ≤200 MB cap, not approached |
| Stop reason | WINDOW_COMPLETE | | exit code 0 |

Manifest: `~/.my-quantitative-data/sixsource-foundation-v1/crypto_l2/collector_manifest.json`
(sha256 of the ndjson re-computed post-write and matched: `sha_match: True`).

## 4. Calibration disclosure (all provider calls counted)

Three discarded calibration runs into `/tmp/l2_smoke` (never entered the
evidence root; deleted after use): run 1 exposed a missing initial-snapshot
call (fixed) with 4 failed transport attempts and rest_used 0; runs 2–3 each
made 2 successful REST snapshots + 1 WS connection. Provider-side totals this
session: 6 successful REST requests (≤30 cap), ≤4 failed transport attempts,
4 WS connections (3 calibration ≤25 s + 1 production). All sequential, ≥1 s
spacing. The production evidence root contains only the single production
window's files.

## 5. Authority claims (what this sample can and cannot support)

CAN claim (measured, evidenced):
- For ~10 minutes on 2026-09-28 02:16–02:27 UTC, the keyless Binance spot
  combined depth@100ms stream for BTCUSDT+ETHUSDT was continuous with **zero
  detected sequence gaps and zero reconnects**; the U-chain and the
  snapshot-first sync rule held for all 11,981 events.
- Spot diff payloads carry no `pu` field (schema evidence, 11,981 events).
- End-to-end feed latency (local receive minus exchange event time) is
  typically sub-millisecond at ms resolution in this window; worst observed
  1.63 s (outliers exist; distribution not characterized beyond p50/p95/max).
- Snapshot book depth at window start: 1000 bid + 1000 ask levels retrievable
  keyless from data-api.binance.vision; top-of-book spread at start was one
  tick (0.01) on both symbols.

CANNOT claim:
- Any historical order-book state or forced-flow inference (label law).
- Exchange-venue completeness: this is one connection, one region, one 10-minute
  window; it does not bound feed quality across days, volatility regimes, or
  network paths, and does not measure cross-venue differences.
- True exchange-side latency: `E`-based latency includes local receive
  processing; p50=0 reflects ms-resolution rounding, not physics.
- No candle-based order-book inference was performed or is licensed by this artifact.

## 6. Artifacts

| Artifact | Path | Status |
|---|---|---|
| Collector | `research/control/DATA-FOUNDATION-SIXSOURCE-V1/cx/collect_binance_l2.py` | AVAILABLE_VALIDATED (compile + smoke + production run, exit 0) |
| Raw events (ndjson, 14,109,556 B) | `~/.my-quantitative-data/sixsource-foundation-v1/crypto_l2/l2_events_PROSPECTIVE_FROM_2026-09-28_20260928T021649Z.ndjson` | AVAILABLE_VALIDATED (sha256 verified vs manifest) |
| Manifest | `~/.my-quantitative-data/sixsource-foundation-v1/crypto_l2/collector_manifest.json` | AVAILABLE_VALIDATED |
