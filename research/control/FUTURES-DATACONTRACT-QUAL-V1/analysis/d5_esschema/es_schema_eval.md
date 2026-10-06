# D5-ESSCHEMA — ES vendor schema, close conventions, spread-proxy recompute

Cycle `FUTURES-DATACONTRACT-QUAL-V1`, lane D5 (Co-Owner schema-eval). Read-only
evaluation of data we ALREADY OWN. Generated 2026-10-03 from
`es_schema_eval.py` (this directory); machine-readable output in
`es_schema_eval.json`.

**Claims class: everything below is MODELED-COST input quality only.**
No fill/queue/execution-realism claims are made or supported. bbo-1m is NOT
owned and, per Co-Owner, would be insufficient anyway. Missing statistics
items are marked `NOT_RUN`.

Data: Databento GLBX ohlcv-1m ES parquet at
`/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/`
(`AV1R-O1M-ES-DELTA` 2010-06..2023-10, `AV1T-O1M-ES` 2023-10..2026-10),
plus `AV1T-definition-ALL10` / `AV1T-statistics-ALL10`, plus the IBKR intake
raw files (`~/.my-quantitative-data/futures-10syms-v1/raw/ES_*.json`).
Sample windows (cheap, no 16y sweep): W1 = 2026-03-31..09-30 (CDT), W2 =
2025-09-30..2026-03-31 (CST+CDT); 173 front sessions joined to IBKR dailies.

## 1. Vendor schema (ohlcv-1m)

Both batches share one schema (parquet, 1 row group per chunk):

| column | physical | logical | notes |
|---|---|---|---|
| `rtype` | int32 | int16 | constant **33** (1-minute bar) in every row sampled |
| `instrument_id` | int32 | uint32 | matches definition schema 1:1 |
| `raw_symbol` | binary | string | e.g. `ESZ6`; **calendar spreads are mixed in** (`ESM6-ESU6`, …) |
| `ts_event` | int64 | — | ns epoch; bar interval **START** (see §3) |
| `open/high/low/close` | int64 | — | fixed-point **1e-9** (7635250000000 = 7635.25) |
| `volume` | int32 | uint32 | traded contracts in that minute |

**No publication fields** in these trimmed exports: no `publisher_id`,
`sequence`, `ts_init` (absent, not null). Definitions give
`min_price_increment = 250000000` (0.25) and `unit_of_measure_qty =
50000000000` ($50/point) for every ES outright — matches the CME contract.

## 2. Tick grid, instrument_id stability

- **Outrights: 0 off-grid OHLC rows** out of 240,629 (W1) and 238,322 (W2);
  every open/high/low/close is an exact multiple of 0.25.
- Spread combos (`ES*-ES*`, 38,882 / 42,199 rows): 79–84% off the 0.25 grid
  but **0 off the 0.05 grid** — they are legitimate ES calendar-spread
  instruments on the nickel grid, not corruption. **Filter `raw_symbol`
  containing `-` before any outright analysis.**
- instrument_id stability: 66 symbols in the 2023-10..2026-10 ohlcv files,
  **zero symbols mapping to >1 instrument_id**, and every ohlcv id resolves
  in the definition map. Batch boundary AV1R→AV1T touches at 2023-10-01
  (row-level duplicate check across the boundary: not re-run here, out of D5
  scope).

## 3. Timestamp convention (verified empirically)

`ts_event` is the **interval start** in exchange time (America/Chicago, DST
handled): zero bars stamped 16:00–16:59 CT (Globex maintenance halt) while
the session's final trades (15:59:00–15:59:59.99) sit in the 15:59-stamped
bar, and reopen trades at 17:00:00 CT appear in the 17:00-stamped bar. So:
- "16:00 CT last-trade close" = close of the **15:59-stamped** bar;
- the bar whose interval **ends exactly at 15:00 CT** is the **14:59-stamped**
  bar. Both used below.

## 4. Close conventions — the 16:00 last trade vs the settlement mark

Statistics schema is PRESENT (`AV1T-statistics-ALL10`); `stat_type=3` =
`SETTLEMENT_PRICE` (enum confirmed from the vendor's own `databento_dbn`
package shipped in our venv; note `CLOSE_PRICE` stat_type 11 has zero ES
rows — the settlement mark is what CME publishes for ES). Settlement rows
publish a preliminary mark at ~15:00 CT and the final mark at ~16:38–16:39
CT; we take the day's last update.

Front = highest-1m-volume outright per session (schema-lane approximation of
the T-5 front; W1 fronts ESM6 53 / ESU6 65 / ESZ6 14 sessions). n=173
sessions joined to IBKR `TRADES_1day` (flat v=0 synthetic rows excluded):

| comparison (ticks = 0.25 pt = $12.50) | n | med \|diff\| | mean | p90 | exact |
|---|---|---|---|---|---|
| vendor 15:59-bar close (≈16:00 CT last trade) vs IBKR daily close | 173 | **18.0** | 26.0 | 57 | 1 |
| vendor 14:59-bar close (ends 15:00 CT) vs IBKR daily close | 173 | **4.0** | 5.7 | 11 | 10 |
| vendor 15:00-bar close vs IBKR daily close | 173 | 8.0 | 10.5 | 22 | 12 |
| **vendor final SETTLEMENT vs IBKR daily close** | 96 | **0.0** | 0.0 | 0 | **96/96** |
| vendor final SETTLEMENT vs vendor 15:59-bar close | 96 | 18.5 | 27.6 | 60 | 1 |
| vendor final SETTLEMENT vs vendor 14:59-bar close | 96 | 5.0 | 6.9 | 13.6 | 4 |

Per-window medians are stable (W1: 18 / 4 / 0; W2: 18.5 / 5 / 0). Settlement
coverage here is 96/173 only because 4 of 5 statistics chunks were loaded
(chunk-coverage artifact, not data absence); on every covered session the
match is exact.

**Findings.**
1. Earlier result corroborated and sharpened: vendor 16:00-ish last trade vs
   IBKR daily close medians ~18 ticks (~$225/contract) in both windows
   (earlier lane: 15); the 15:00-CT edge is only 4–5 ticks (earlier: 4).
2. Root cause identified: **the IBKR ES daily close IS the CME final
   settlement mark — exact tick-for-tick in 96/96 covered sessions.** It is
   an administrative, 15:00-CT-anchored calculated mark (median 5 ticks from
   the final pre-15:00 trade — consistent with a VWAP-style calculation over
   a window, not a single print), NOT the 16:00 CT last trade.
3. Consequence for modeling: an IBKR-daily-close backtest assumes fills at
   the settlement mark (no trade occurs there for the marginal order; ~18
   ticks ≈ $225/ct from the last traded price). Any engine using IBKR dailies
   for ES entry/exit pricing must label it a settlement-mark fill assumption,
   and can now instead use vendor-settlement (same number, sourced from the
   exchange statistics record) or the true last-trade close with the gap
   made explicit.

## 5. Volume semantics

Vendor `volume` = traded contracts per minute (outright). Corroboration:
sum(1m vendor volume) / IBKR daily volume, front sessions: **median 1.189**
(p10 1.124, p90 1.258). Both are trade-volume semantics; the vendor counts
~19% more prints than IBKR's daily total. Exact reconciliation
(`NOT_RUN`): would require an IBKR methodology doc we do not own. Ratio is
tight (±7%) and stable across two seasons — good enough for volume-weighted
work with a disclosed vendor≥IBKR bias.

## 6. Spread-proxy recompute (S6 mirror + vendor analogue)

**What the IBKR proxy actually was** (read from
`FUTURES-DATA-10SYMS-V1/fut10_validate.py::spread_stats` and
`S6_FRONT_SPREADS.json`; the file's "close-to-close" means *same-session
BID-daily-close vs ASK-daily-close*, not day-over-day): per day
`ASK_close − BID_close`, median over the front's last 20 sessions.

**Reproduction (ESZ6, 2026-09-03..2026-10-01):** median **1.0 tick = $12.50**,
p90 **$50.00**, crossed days 0 — **exactly equal to `S6_FRONT_SPREADS` ES**
(median_ticks 1.0, median_usd 12.5, p90_usd 50.0). Intake number confirmed
reproducible from raw.

**Vendor 1m analogue, same 20 sessions, 23,904 consecutive-minute
transitions (front ESZ6, outrights only):** the vendor owns no BBO, so the
BID/ASK proxy **cannot be mirrored** — stated, not faked. What the trade
data supports: median |Δclose| **2.0 ticks** (12.6% of transitions flat;
median nonzero 3; p90 8), RTH-only median 4.0 ticks; median 1m high–low
range 5 ticks.

**Magnitude comparison and honest capability statement.** IBKR quote-close
proxy: 1 tick ($12.50). Vendor trade-based |Δclose|: 2–4 ticks ($25–$50),
which *overstates* spread-only cost because minute-to-minute drift is mostly
true price movement; the IBKR proxy *understates* contemporaneity because
its two marks are non-synchronous administrative closes (§4 shows single
time marks can sit many ticks apart). Both agree that the ES front trades in
a ~1-tick effective-spread regime. Therefore:

- **CAN support:** tiering inputs for modeled cost — ES sits in the
  tightest tier, on the order of 1–4 ticks per side depending on proxy, with
  an explicit overstatement caveat and a floor from the tick grid (min
  possible effective spread = 1 tick = $12.50).
- **CANNOT support:** execution realism — no fill probability, no queue
  position, no capacity, no "we would have gotten the mid/inside" claims.
  bbo-1m not owned and insufficient per Co-Owner; the two owned proxies
  bracket the order of magnitude only.

## 7. NOT_RUN / absent items

- IBKR↔vendor volume reconciliation to the contract: `NOT_RUN` (no IBKR
  volume methodology source owned).
- AV1R/AV1T boundary row-level duplicate check: `NOT_RUN` (bulk coverage is
  another lane's scope; file ranges touch at 2023-10-01).
- `CLOSE_PRICE` stat (type 11): absent for ES in sampled chunks (documented;
  not a gap — settlement is the ES mark).
- BBO-derived anything: `NOT_RUN — data not owned` by design of this lane.

## Reproduction

```
/Users/hoangminhlong/my-quantitative/.venv/bin/python \
  research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d5_esschema/es_schema_eval.py
```
Runtime ~1 min; writes `es_schema_eval.json` (full per-session audit trail
in `close_conventions.detail_rows`, 173 rows).
