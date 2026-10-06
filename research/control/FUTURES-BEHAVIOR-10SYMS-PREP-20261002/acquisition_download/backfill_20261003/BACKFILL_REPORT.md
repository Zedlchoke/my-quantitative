# BACKFILL_REPORT — FX deep-history extension (lane FX-BACKFILL)

Task FUTURES-DEEPRESEARCH-V2-20261003 · lane FX-BACKFILL · generated 2026-10-03T00:10+00:00

- Owner mission (verbatim): 'tải lùi về cho các mã tiền tệ thêm xíu nữa' — extend the four FX roots' ohlcv-1m history further back.
- Parent windows (ledger-verified, no double-billing): 6E/6J/6B/6A all started **2022-01-01** (continuous to 2026-10-01). New windows butt exactly: **2020-01-01 → 2022-01-01** per root.
- Budget: additional cap **$16.19** (cumulative cap $122.00 = owner $125 ceiling − $3 drift buffer; parent delivered $105.810097). Dispatch target 2020-01-01 (~$14.8 est.); fallback 2021-01-01 only if quotes exceeded the cap. **Quotes fit; fallback not used.**

## Window decision (metadata-only quotes, zero spend — BACKFILL_QUOTES.json)

| candidate start | 6E | 6J | 6B | 6A | total additional | cumulative | fits? |
|---|---|---|---|---|---|---|---|
| 2020-01-01 (target) | $3.473309 | $2.966474 | $2.893437 | $3.009875 | **$12.343094** | $118.153191 | YES (chosen) |
| 2021-01-01 (fallback) | $1.683552 | $1.458470 | $1.406728 | $1.494314 | $6.043063 | $111.853160 | yes (unused) |

## Per-chunk table (all MIRRORED; QA PASS 4/4)

| # | chunk | window | records (quoted→actual, drift) | raw .dbn.zst | parquet | get_cost | cumulative after | job |
|---|---|---|---|---|---|---|---|---|
| 1 | `AV1B-O1M-6E-BACKFILL2__2020-01-01_2022-01-01` | 2020-01-01..2022-01-01 | 951,387→951,387, 0.0% | 11,681,660 B | 10,948,621 B | $3.473309 | $109.283406 | GLBX-20261002-94UVSCXK6G |
| 2 | `AV1B-O1M-6J-BACKFILL2__2020-01-01_2022-01-01` | 2020-01-01..2022-01-01 | 812,558→812,558, 0.0% | 9,517,194 B* | 8,770,930 B | $2.966474 | $112.249880 | GLBX-20261002-L6WLTE43UD |
| 3 | `AV1B-O1M-6B-BACKFILL2__2020-01-01_2022-01-01` | 2020-01-01..2022-01-01 | 792,552→792,552, 0.0% | 9,272,418 B | 8,567,055 B | $2.893437 | $115.143316 | GLBX-20261002-H56Q57BULG |
| 4 | `AV1B-O1M-6A-BACKFILL2__2020-01-01_2022-01-01` | 2020-01-01..2022-01-01 | 824,446→824,446, 0.0% | 9,619,532 B | 8,969,113 B | $3.009875 | $118.153191 | GLBX-20261002-9XY8K33AYG |

\* raw column = per-chunk .dbn.zst payload bytes; each chunk also carries vendor manifest/condition/metadata sidecars (recorded in the ledger).

**Totals: additional spend $12.343094 (quotes == delivered, drift $0.00 on all 4 chunks, extending the predecessor's 72-chunk $0.00 record); cumulative $118.153191 of the $122.00 cap / $125 owner ceiling; unused additional headroom $3.846906.** 3,380,943 records; 40,400,389 B raw; 37,255,719 B parquet.

## Budget accounting

| item | USD |
|---|---|
| parent delivered (COMPLETION_LEDGER, 72 chunks) | $105.810097 |
| this backfill quoted = delivered | $12.343094 |
| **cumulative delivered** | **$118.153191** |
| additional cap (dispatch) | $16.190000 |
| cumulative cap | $122.000000 |
| owner ceiling | $125.000000 |
| remaining to cumulative cap | $3.846909 |

Gate discipline: FRESH `get_cost` re-quote immediately before **every** submit, projected additional AND cumulative checked against caps (ledger `budget_before_submit` per chunk); SUBMITTED-first ledger; exact-param `batch.list_jobs` dedupe guard; machine-wide heavy lock held 2026-10-02T23:29:34Z → 2026-10-03T00:02:57Z and released. No STOP file was written (no gate tripped).

## QA (adapter, same conventions as predecessor)

- 4/4 PASS; record drift 0.000% (quoted == delivered == decoded on every chunk); window checks min ≥ requested AND max < end-exclusive on every chunk.
- Identity: 0 fully-unresolved instruments; 7 raw_symbol decade-wrap collisions per chunk vs the 2023-10+ definition-window registry (known vendor convention — one-digit-year raws repeat per decade; `instrument_id` is the true identity; DBN-prelude mapping fallback). Registry never written (ohlcv chunks).
- Bars: outright vs spread census recorded (e.g. 6E 890,958 outright / 60,429 spread); downstream uses the documented OUTRIGHT_RE filter.
- Negative prices: only on calendar-spread instruments (6A 5,067; 6B 403; dash raw_symbols, price differences — vendor convention); **0 on outright contracts**; 6E/6J none anywhere. Preserved, not dropped.
- 6J scale: 0.008659..0.0099185 USD/JPY — sane.
- Vendor sha256: **16/16 files MATCH** (vendor-declared `sha256:<hex>` == local re-hash == ledger record).

## Butt / no-gap verification (independent, at parquet level)

New chunk actual range all roots: 2020-01-01T23:00Z .. 2021-12-31T21:59Z (first/last 1m bar). Existing 2022 chunk starts 2022-01-02T23:00Z. No overlap anywhere; exact butt at 2022-01-01. The ~49h boundary interval is the New-Year-2022 holiday weekend (Fri Dec 31 22:00Z close → Sun Jan 2 23:00Z Globex open) — session calendar, not missing data.

**Resulting coverage: 6E/6J/6B/6A each 2020-01-01 → 2026-10-01 ohlcv-1m continuous (vendor holidays excepted).**

## Artifacts

- Raw: `~/.my-quantitative-data/futures-databento-av1trim/raw/dbn_zst/AV1B-O1M-{6E,6J,6B,6A}-BACKFILL2/` (immutable, kept forever)
- Parquet: `~/.my-quantitative-data/futures-databento-av1trim/parquet/AV1B-O1M-{root}-BACKFILL2/{chunk_key}.parquet` (ints end-to-end, no floats in value path)
- Lane evidence: `backfill_20261003/` — BACKFILL_LEDGER.json (chained authority), BACKFILL_QUOTES.json, qa/*.qa.json + *.qa_bundle.json, this report, BACKFILL_MANIFEST.json
- iCloud mirror: `CloudDocs/my-quantitative-futures/av1-trim/AV1B-O1M-{root}-BACKFILL2/{chunk_key}/` (raw + sidecars + parquet + qa.json + ledger_entry.json; every copy SHA256-verified; state COPIED, sync SYNC_PENDING_UNVERIFIED — cloud upload is macOS/iCloud's job, never claimed here). Owner's personal backup of licensed data; no redistribution.
- Parent ledger: appended a `backfill_chains` pointer section (history untouched; parent chunks verbatim).

## Known limitations

- Actual invoice reconciliation vs the vendor usage page remains owner-side (NOT_RUN_DOC_UNCLEAR — no account balance endpoint exposed to the client; same status as predecessor).
- Registry identity for 2020-2021 contracts relies on instrument_id + file mappings (def-window registry starts 2023-10); raw_symbol alone is ambiguous across decades (vendor convention, documented).
- iCloud sync state unverifiable from this lane (SYNC_PENDING_UNVERIFIED on every mirrored file).
