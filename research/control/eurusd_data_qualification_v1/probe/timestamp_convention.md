# EDQ1 — Timestamp and candle convention record (P1 probe)

Cycle: EURUSD-DATA-QUALIFICATION-V1 · Lane: eurusd-source-qualification
Window: 2024-03-04T00:00:00Z → 2024-03-14T00:00:00Z (frozen)

Everything below is PROVEN from decoded bytes / cross-source alignment; nothing
is assumed from vendor folklore.

## 1. Dukascopy .bi5 ticks — epoch-ms UTC, proven

Decoding: each `<HH>h_ticks.bi5` is LZMA (FORMAT_AUTO) whose decompressed
stream is 20-byte records `struct('>5i')` =
`(time_offset_ms_within_hour, ask_int, bid_int, ask_volume_bits, bid_volume_bits)`.

- **Absolute tick time = hour-file UTC instant + offset_ms.** The hour files
  are indexed by UTC calendar hours (URL month is 0-indexed: March → `02`).
- **Point scale verified = int / 1e5** (0.1 pip granularity): decoded prices
  across the window land in 1.08377–1.09815 — the actual EURUSD range of the
  window (cross-checked against Twelve Data closes 1.0842 → 1.0954). The same
  scale decodes plausible ranges on multi-year boundary probes (2023 file:
  1.08244–1.08375; 2025 file: 1.15253–1.15475).
- **Sanity bar (London open, weekday):** file `2024/20240305_07h_ticks.bi5`
  (07:00 UTC hour) first tick has offset 89 ms → absolute
  `2024-03-05T07:00:00.089Z`, bid 1.08468 / ask 1.08470. Offsets stay within
  [0, 3 600 000) in every file; no file's ticks precede its hour start.
- **Monotonicity:** strictly increasing offsets within every file (0
  violations in 240 files); zero cross-file monotonicity violations; zero
  exact-duplicate ticks (same ts + same bid/ask) in 578,916 ticks.

## 2. Weekend closure shape — measured, not assumed

From the tick stream (minute indices):

- Last tick before weekend: **2024-03-08T21:59:xxZ** (Friday); minutes with
  ticks stop at 21:59.
- First tick after weekend: **2024-03-10T21:00:xxZ** (Sunday).
- Empty (0-byte, HTTP 200) hour files: exactly 2024-03-08T22:00Z →
  2024-03-10T20:00Z (47 files). **Zero HTTP 404s** in the whole probe — the
  server serves empty bytes, not 404, for closed hours.

DST note (US switch 2024-03-10 07:00 UTC, inside the window): Friday close
≈ 22:00 UTC and Sunday open 21:00 UTC are both "5 pm New York" — Friday in
EST (UTC−5 → 22:00Z) and Sunday in EDT (UTC−4 → 21:00Z). The one-hour shift
across the DST boundary is VISIBLE in the data and is consistent with a UTC
index: the weekend gap is 47 h 00 m in UTC in both file layout and tick
stream.

## 3. Intra-week gaps

Within measured trading spans (excluding the weekend closure), 44 gaps of
1–3 missing minutes (53 minutes total) in 11,580 span minutes → **99.542%
minute coverage**. They cluster in the rollover hour (21:00–23:59 UTC) and
thin Asia hours — enumerated in `coverage_census.json` →
`gap_census_within_trading`. No interpolation anywhere; missing minutes stay
missing.

## 4. Twelve Data bars — UTC, open-time-labeled, proven by alignment

- All 11,509 bar labels parse as `YYYY-MM-DD HH:MM:SS` with second == 00 and
  align exactly to UTC minute boundaries (requested `timezone=UTC`).
- **Convention test** (window `2024-03-04 00:00` → `2024-03-14 00:00`,
  `outputsize=5000`): the API returned the NEWEST 5000 bars first
  (descending) and NO `next_url` member on this plan; pagination was done by
  re-requesting with `end_date = oldest_bar − 1min` (3 pages, ≤8 req/min).
  Field inventory: `datetime, open, high, low, close` — NO bid/ask, NO
  volume on this plan.
- **Bar-edge proof** (close-to-close vs Dukascopy tick-derived mid):
  | hypothesis | n | median abs diff | p95 | max |
  |---|---|---|---|---|
  | A: bar `T` covers [T, T+1) — label = open time | 11 459 | **0.35 pips** | 1.15 | 42.65 |
  | B: bar `T` covers [T−1, T) — label = close time | 11 458 | 0.60 pips | 1.90 | 25.40 |
  Hypothesis A wins on median AND p95 → **Twelve Data labels each 1-min bar
  by its open time, in UTC**. (Residual 0.35-pip median is snapshot
  difference between vendors, not a timestamp error; formal tolerance test is
  P2 per plan §2.)

## 5. Verdict-relevant conclusion

Both sources expose UTC-anchored, unambiguous timestamps:
Dukascopy tick epoch-ms UTC (offsets within hour), Twelve Data open-time
minute labels in UTC. Gate `TIMESTAMPS_UTC_UNAMBIGUOUS` = PASS.
