# V8X Crypto Breadth Audit (Agent A8)

- Agent session: `5208f2fa-efce-442e-92d0-6be230729d1c`
- Branch/worktree: `orca/v8-a8-crypto-breadth` @ `/Users/hoangminhlong/my-quantitative-v8-wt/a8-crypto-breadth`
- Date: 2026-08-26
- Performance-blind: **yes** — `results/portfolio_v7`, `results/portfolio_v8`, and any V7/V8 metrics/verdict files were NOT opened.
- Manifest: `data/v8x_manifests/crypto_universe_selection.json` (schema_version 1.0.0)
- **Verdict: `V8X_CRYPTO_TOP10_ELIGIBLE`** — eligible_count = **20/20**, top-10 selected.

## 1. Data sources (primary repo, read-only)

| Source | Path | Layout |
|---|---|---|
| Catalog | `/Users/hoangminhlong/my-quantitative/catalog_live_crypto` | `data/binance_bar/<SYM>-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL/*.parquet` (BinanceBar; columns incl. `ts_event` ns, `quote_volume` string), `data/crypto_perpetual/<SYM>-PERP.BINANCE/*.parquet` (CryptoPerpetual instruments, embedded exchange `info` JSON) |
| Funding | `/Users/hoangminhlong/my-quantitative/funding_data/scan_2026/<TICKER>/funding.json` | `{schema_version, captured_at, symbol, requested_start_ms, requested_end_ms, rows[{fundingTime, fundingRate, markPrice, rateType}]}` |

## 2. Rule constants (FROZEN BEFORE SCANNING)

The constants below were fixed in the scanner prior to any data access and are
embedded verbatim in the manifest under `rule_constants`.

- Window: `[2025-08-21T00:00:00Z, 2026-08-21T00:00:00Z)` = 365 days (`WINDOW_DAYS=365`).
- Universe filter: venue `BINANCE`, quote `USDT`, contract type `PERPETUAL`, 15-MINUTE-LAST-EXTERNAL bars.
- Req. 4 gate: `first_bar <= 2025-08-21T00:00:00Z` (`FIRST_BAR_MAX_STR`).
- Coverage gate: distinct bar-days inside window >= `MIN_COVER_DAYS_IN_WINDOW = 365`.
- Gap rule (`gap_day`, DAILY granularity): a UTC calendar day with ZERO bars inside the effective span `[max(first_bar_day, 2025-08-21), min(last_bar_day, 2026-08-21)]` for which at least one bar-day exists earlier AND later in the symbol's full sorted bar-day series ("missing entire day where neighbors exist"). Days with >=1 bar count as covered; **single-bar / partial-day gaps are tolerated**. Gate: `gap_days <= GAP_DAYS_MAX_ALLOWED = 0`.
- Funding gate: `funding.json` present with >= `FUNDING_MIN_ROWS = 1` row.
- Volume proxy decision: the 15m parquet carries a native `quote_volume` field ⇒ **median daily quote volume IS measurable locally**. Per the no-fabrication instruction, the "median daily bar count × constant" proxy was NOT used and no symbol fell back to `metric_unavailable`.
- Ranking: primary `median_daily_quote_volume_usdt` desc, tie-break symbol asc. Fallback (frozen, unused): if quote_volume absent/all-null → rank by coverage-days desc then symbol asc.
- Determinism: overlapping capture files deduped on exact `ts_event`; all sums use Decimal; hashes over file bytes.

## 3. Methodology

1. Enumerated catalog bar dirs matching `<TICKER>-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL` → 20 candidates.
2. Per symbol: read instrument parquet (quote/settlement USDT, `contractType=PERPETUAL`, `onboardDate` from embedded exchange info JSON).
3. Read all 15m bar parquets; deduped on `ts_event`; derived first/last bar, total bars, distinct bar-days (all-time and in-window), daily `quote_volume` sums in-window → median.
4. Gap screen at DAILY granularity per frozen rule above (zero-bar interior days counted; boundary/trailing uncovered days are not gaps by construction since neighbors must exist).
5. Funding: row count + min/max `fundingTime` per symbol.
6. Eligibility gates evaluated in fixed order (metadata → quote/perp → first bar → coverage → gaps → funding). Ranked eligibles by frozen ranking; took top 10.
7. Hashes: SHA-256 of each `funding.json`; per-symbol bar-dir digest = SHA-256 over sorted `(filename : file-sha256)` lines.

## 4. Accepted top 10 (ranked by median daily quote volume, USDT)

| # | Symbol | Median daily quote vol (USDT) | In-window days | Gap days | Funding rows |
|--:|---|---:|--:|--:|--:|
| 1 | BTCUSDT | 12,107,829,986.06 | 365 | 0 | 2190 |
| 2 | ETHUSDT | 10,240,030,728.20 | 365 | 0 | 2190 |
| 3 | SOLUSDT | 2,248,115,171.52 | 365 | 0 | 2190 |
| 4 | XRPUSDT | 817,013,508.96 | 365 | 0 | 2190 |
| 5 | ZECUSDT | 599,035,706.66 | 365 | 0 | 2190 |
| 6 | DOGEUSDT | 574,147,365.18 | 365 | 0 | 2190 |
| 7 | BNBUSDT | 397,338,117.68 | 365 | 0 | 2190 |
| 8 | 1000PEPEUSDT | 302,541,407.99 | 365 | 0 | 2190 |
| 9 | SUIUSDT | 239,049,000.43 | 365 | 0 | 2190 |
| 10 | ADAUSDT | 216,382,761.61 | 365 | 0 | 2190 |

## 5. All candidates evaluated (20; `*` = accepted top 10)

| Sym | Onboard | First bar (UTC) | Last bar (UTC) | Bar-days all-time | In-window | Gaps | Fund rows | Fund first | Fund last | Median daily qvol (USDT) |
|---|---|---|---|--:|--:|--:|--:|---|---|---:|
| * BTCUSDT | 2019-09-08 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 12,107,829,986.06 |
| * ETHUSDT | 2019-11-27 | 2024-08-23T00:14:59Z | 2026-08-23T06:59 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 10,240,030,728.20 |
| * SOLUSDT | 2020-09-14 | 2024-08-21T14:14:59Z | 2026-08-21T13:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 2,248,115,171.52 |
| * XRPUSDT | 2020-01-06 | 2024-08-21T14:14:59Z | 2026-08-21T13:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 817,013,508.96 |
| * ZECUSDT | 2020-02-05 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 599,035,706.66 |
| * DOGEUSDT | 2020-07-10 | 2024-08-21T14:14:59Z | 2026-08-21T13:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 574,147,365.18 |
| * BNBUSDT | 2020-02-10 | 2024-08-21T14:14:59Z | 2026-08-21T13:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 397,338,117.68 |
| * 1000PEPEUSDT | 2023-05-05 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 302,541,407.99 |
| * SUIUSDT | 2023-05-03 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 239,049,000.43 |
| * ADAUSDT | 2020-01-31 | 2024-08-21T14:14:59Z | 2026-08-21T13:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 216,382,761.61 |
| AVAXUSDT | 2020-09-23 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 151,501,462.64 |
| LINKUSDT | 2020-01-17 | 2024-08-21T14:14:59Z | 2026-08-21T13:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 144,417,621.66 |
| ENAUSDT | 2024-04-02 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 4379 | 2024-08-23T08:00 | 2026-08-23T04:00 | 131,933,200.98 |
| NEARUSDT | 2020-10-15 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 112,861,800.79 |
| BCHUSDT | 2019-12-19 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 118,648,882.38 |
| AAVEUSDT | 2020-10-16 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 96,145,223.56 |
| WLDUSDT | 2023-07-24 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 2190 | 2024-08-23T08:00 | 2026-08-23T00:00 | 106,532,907.72 |
| BOMEUSDT | 2024-03-16 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 4379 | 2024-08-23T08:00 | 2026-08-23T04:00 | 8,942,278.17 |
| ACEUSDT | 2023-12-18 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 4636 | 2024-08-23T08:00 | 2026-08-23T04:00 | 2,572,231.89 |
| ONGUSDT | 2023-11-27 | 2024-08-23T05:14:59Z | 2026-08-23T04:44 | 731 | 365 | 0 | 4418 | 2024-08-23T08:00 | 2026-08-23T04:00 | 1,283,733.12 |

## 6. Rejected

None. All 20 candidates passed every frozen gate (first-bar ≤ 2025-08-21, ≥365 in-window covered days, 0 unexplained gap days, funding present ≥1 row).

## 7. Honesty notes — what could / could not be measured locally

1. **Quote volume is real, not proxied.** The 15m parquet stores a native `quote_volume` field (Binance kline quote-asset volume), so the ranking metric is measured, not fabricated. The frozen bar-count-proxy fallback was never triggered; zero symbols were marked `metric_unavailable`.
2. **Local capture ≠ exchange truth (no network).** Everything below is asserted only about the local parquet/JSON artifacts. No cross-check against Binance was possible.
3. **Intra-day sparsity is tolerated by design.** The gap screen is DAILY: a day counts as covered with ≥1 bar, so a day with a single 15m bar would pass. No symbol exhibited this pathology in practice (all show full-year coverage and plausible bar counts ≈ 96/day × 731 d), but the screen itself cannot detect sub-daily holes.
4. **Median daily volume uses only in-window bar-days**, capped at 2026-08-21T00:00Z even though several catalogs extend to 2026-08-23; first/last calendar days of symbols starting mid-window are included as-is (partial days are not rescaled).
5. **Overlapping captures deduped on exact `ts_event`.** ETHUSDT's bar dir has 4 fragmented files (capture sessions); dedupe is deterministic, but any bars lost at capture boundaries upstream cannot be detected here.
6. **Funding provenance unaudited.** Row-count differences (2190 vs 4379–4636 for ACE/BOME/ENA/ONG) reflect differing funding intervals in the source data (8h vs shorter); intervals/rate sanity were not independently verifiable offline. `captured_at`, `requested_start_ms/end_ms` recorded but not re-derived.
7. **Onboard dates come from the exchange `info` blob embedded in instrument parquets** (e.g., BTCUSDT 2019-09-08); treated as metadata note only — no eligibility weight.
8. **Performance-blind honored:** no V7/V8 metrics or verdict files accessed; selection depends solely on catalog/funding inputs and the pre-frozen rules.

## 8. Outcome

- `eligible_count`: 20
- `accepted_top10`: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, ZECUSDT, DOGEUSDT, BNBUSDT, 1000PEPEUSDT, SUIUSDT, ADAUSDT
- Manifest includes per-funding-file SHA-256 and per-symbol bar-dir digests for all 20 candidates (reproducibility anchors).
