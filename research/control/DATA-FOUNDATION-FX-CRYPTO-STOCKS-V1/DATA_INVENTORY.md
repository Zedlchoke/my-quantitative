# DATA_INVENTORY — DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 (deliverable D1)

Machine authority: `data_inventory.jsonl` (91 rows after consolidator dedup (nyfed/fred cross-lane duplicates) + 1 honest R1 downgrade, merged from the 5 lane
files with `source_lane` tags; two intentional cross-lane duplicate ids —
`nyfed_reference_rates`, `fred_granted_set` — censused by both L-ST and
L-PIT with consistent facts). Statuses are per plan §5; **no PASS was
inferred from file existence** — every AVAILABLE_VALIDATED row carries
this-cycle re-measurement evidence (sha sample/full match + coverage
census) in its `status_evidence` field.

Status tally (post-conformance-fix): **AVAILABLE_VALIDATED 32 / AVAILABLE_UNVALIDATED 26 / NOT_RUN 28 / BLOCKED_TRANSPORT 2 / BLOCKED_LICENSE 1 / BLOCKED_ACCOUNT 2** — `validate_rows.py` returns VALID on the consolidated file (consolidation erratum: the first D1 commit message claimed validator PASS prematurely; the file then failed with 109 violations, fixed honestly in the erratum commit per P-19: bytes measured from disk, enum mappings conservative + original text preserved, 1 row downgraded for missing byte-level evidence, lane sample sizes referenced not transcribed).
Taxonomy note (plan §14 F9): BLOCKED_TRANSPORT ≡ the owner's 7-state view
"BLOCKED, cause = transport" (standing SNI-filter environment constraint,
L-FXFF-1) — it is a superset state, not a new verdict class.

## FOREX (26 rows)

**Validated (7):** the program's entire tick-adjacent FX price authority —
5 Dukascopy M1 BID/ASK corpora (EURUSD 2021→2026-06 ×2 copies + GBPUSD +
USDJPY →2026-09-23; file counts == committed per-file manifests; 5/5 sha
sample per corpus; 15m-bar censuses 119k–137k) + TD XAU/USD 1day (12,268
rows 1979→2026-09, full re-hash) + TD 4-pair daily spot (re-hash EXACT vs
NG5 digest pin). Measured spread censuses on 5 pairs (p50 0.3–1.2 pips;
rollover 0.9–2.3) — the only order-timing-resolved spread numbers held.
**Unvalidated (8):** vintaged CPI/rates archives + 8-region macro events +
NG7 5-pair legs + CoT censuses (all archive-level, sha-matched, contents
not re-extracted), FOREX-SEARCH-V1 staging, IBKR probe artifacts, live
FX-RANGEFADE corpus (F5 names-only).
**Blocked (2 BLOCKED_TRANSPORT):** Dukascopy + CME fresh acquisition
(SNI-filter, measured). **NOT_RUN (6):** ERP1 AUDUSD/USDCAD corpora +
sealed 2026-H1 holdouts (F8: manifest pins only, content unread), MT5
cost probe (collector audited, awaiting owner run).
Key measured facts: BIS/ECB bulk was **never held** (fixtures only); CFTC
raw pulls absent locally (censuses survive on the NG5 branch); the rangeexp
corpus is a byte-identical duplicate of eosv2 (35.4 MB — consolidation
candidate).

## CRYPTO (25 rows, per dataset family)

**Validated (6 families):** Binance Vision 1h klines panel (BTC/ETH/BNB/
XRP/ADA/SOL), settled 8h funding (fapi) + fundingRate vision cross-check,
SOL bookTicker spread census (p50 0.469 bps, n=13.8M), DEU/NG4 WS
collectors (19/19 + 146 shards), ERP1-TRACKB spot/perp 1h planes — 38/38
sampled files sha256+bytes ALL_MATCH this cycle.
**Unvalidated (2):** root catalog 15m parquets (no manifest), JRV regime
decisions (derived). **NOT_RUN (13):** BTC H4 raw bytes (not located in
any surviving tree — archived copy ABSENT, see incident I-1), OI/
liquidation/L2 history (zero bytes on disk; the verbatim law "Không suy ra
order book hay forced flow từ nến" is carried in every such row),
forecast/premiumIndex funding history (never staged), fee/rules history,
cross-venue depth (WAITING_COVERAGE, 14-day floors), basis/mark-index
(live-owner CHR3F, F5 inherited), BNB spread census (needs ≥25 GB free).
Incident I-1 (P-13 drift): 8 of 14 `~/staging_backups` archives named in
SHA256SUMS.txt are ABSENT — including `crypto-v14_full.tar.gz` (V14
basis/OI/klines forest) and `legacy_root_data.tar.gz` (oi_data 98 MB):
the historical OI copy is unrecoverable locally. Owner item (runbook R7).

## STOCKS (20 rows)

**Validated (9):** amihud-v1 staging (8,219/8,219 full re-hash ALL_MATCH;
4,676,951 rows 2017-07→2022-12 byte-censused) + retest copy (byte-identical),
form4_stream (`6ac2cd5b…` streamed EXACT), FTD half-month archive (434 zips
2009-07→2026-08, 15/15 sampled MATCH + P-26 ≥17-day posting-bound
machinery), N-PORT 2026q2 (byte-verified; QQQ 102 holdings), Form-15 death
census (`6a95401f…` EXACT; 3,395 filings/2,301 filers), OFR (3/3), NY Fed
(2/2).
**Unvalidated (8):** EODHD entitlement umbrella (EOD + div/splits 2,168+2,168
files + delisted-inclusive panels incl. stocks-search-v1 cache 111,322
symbols / 142.6M rows 2015→2026-09), Form-4 XML substrate (packet digest
`5d351623…` verified EXACT via streamed manifest re-hash), 4/A corpus
(6,123 files, archive sha MATCH), NG6 panel, Treasury/FRED/CBOE shared.
**Blocked:** FINRA (BLOCKED_LICENSE, P-25 — reopen only via FINRA data
license); EODHD earnings channels (BLOCKED_ACCOUNT — NG3 403 map; reopen =
entitlement upgrade OR the free EDGAR acceptance-datetime path).
**NOT_RUN (2):** Stooq bulk + Twelve Data (terminal canary kills, P-7).
Defect discovered: stocks-search-v1's 1.9 G staging identity is effectively
unpinned (6/111,322 retrieval records carry shas despite
`f9_artifact_digests.json` claiming per-pull pinning) — a ~2-minute
SHA256SUMS job closes it (runbook R8).

## SHARED / RATES / VOL / COMMODITIES (17 rows: 15 shared + 2 rates + 1 vol + 4 commodities)

Validated: NYFed 5 reference rates, OFR 442-mnemonic inventory + 5 series,
EIA/NWS/USDA (FDF-V1) — all hashed this cycle. Unvalidated: FRED (owner
key exists; key use forbidden this cycle — AVAILABLE_UNVALIDATED by rule),
ALFRED, exchange_calendars 4.13.2. NOT_RUN with reasons: Treasury/CBOE/
CFTC raw (pruned with worktrees; censuses survive on evidence branches),
BIS (UNVERIFIED ruling — no artifact anywhere; needs P-25 screen before
any use), ECB SDMX (reachability-probe evidence only). Full detail:
`pit_license/inventory_rows.jsonl` + `LICENSE_RULINGS_VERIFIED.md`
(13/15 plan-§3 rulings VERIFIED, 1 PARTIAL — the CFTC/Treasury/CBOE/FRED/
ECB/BIS row, 0 unverified).

## Cross-cutting cost/execution authority (L-COST, 12 rows)

6 AVAILABLE_VALIDATED (census artifacts re-hashed byte-identical to their
authority records), 4 AVAILABLE_UNVALIDATED (incl. 3 live-owner F5
metadata-only), 1 BLOCKED_ACCOUNT, 1 NOT_RUN. Full table:
`cost_execution/COST_AUTHORITY_TABLE.md` — FX majors 2/10 components
measured, crypto 3/10 + 2 declared, stocks 0/10 (channel carries no
execution cost), XAU 2/10. **Key: IBKR TWS ran TODAY (Jts logs
20260926.105853); socket 7497 + Read-Only API already proven server-side
(321 order-read rejections recorded). The gates are NOT installation —
they are (a) two-sided FX market data NOT_SUBSCRIBED (bid/ask = −1 over
720 s) and (b) no Activity/Flex statement ever exported.**

## Outcome-exposure separation (D-map)

`pit_license/OUTCOME_EXPOSURE_MAP.md`: 21 outcome-exposed family windows
(EURUSD/GBPUSD/USDJPY dev + 2026-H1 holdout reads, BTC H1/H4 2020–2026,
ETH 2020–2026, EODHD panels, etc.) vs 5 UNOPENED classes (S1 everywhere;
ERP1 sealed 2026-H1 AUDUSD/USDCAD; post-2026-09 prospective streams; all
future windows; BNBUSDT pre-read plane) + the 5-rule separation law.
