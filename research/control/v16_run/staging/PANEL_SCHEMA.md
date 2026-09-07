# CRYPTO-V16 staged panel schema (frozen at the wave commit)

The staged panel is the ONLY data surface proposals may reference. It is the
bounded reduction of the P0-frozen design (`p0_freeze_v16.json`): BTCUSDT +
ETHUSDT, monthly aggTrades zips row-filtered to S0 `2025-08-22..2026-08-21`,
one row per symbol-day (UTC). Extraction: `extract_v16_panel.py` (streaming,
sha256-pinned sources, raw deleted post-reduction, manifest committed).

All fields are exchange-event-time (transact_time) aggregates — availability
class EVIDENCED for every column; zero conditioning lag at decision time.

| column | semantics | unit |
|---|---|---|
| symbol, date | identity, UTC date | — |
| trade_count | aggressor prints kept in window | count |
| total_qty / buy_qty / sell_qty | base-asset volume, aggressor-signed (buy = taker buys) | base |
| total_notional | Σ qty·price | USDT |
| flow_imbalance | (buy−sell)/(buy+sell) | (−1, 1) |
| vwap, last_price, high_price, low_price | price stats of kept prints | USDT |
| avg/median/p90_trade_size | qty per print distribution (lower-median, decile p90) | base |
| large_trade_share | qty share of prints with size ≥ p90 (self-referential decile) | 0–1 |
| interarrival_mean/median/p90_s | gaps between consecutive prints | seconds |
| arrival_burstiness | variance/mean − 1 of print counts in 5-min buckets | (−1, ∞) |
| buy_streak_max / sell_streak_max | longest same-side print run | count |
| first_ts_ms / last_ts_ms | day boundary integrity stamps | ms epoch |
| source_files, integrity_ok | provenance (13 monthly sources per symbol; time-ascending enforced) | — |

Absent by design: anything not derivable from aggTrades (no OI, no funding,
no order-book depth). A proposal needing such a field must source it from the
V15 staged bulk-metrics durable asset as CONTEXT/CONTROL only (pins re-verified),
never as a rescued family.
