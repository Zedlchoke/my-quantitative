# DATABENTO_METADATA_PROBE — metadata-only probe report

Task `FUTURES-BEHAVIOR-10SYMS-PREP-20261002` · lane `METADATA-PROBE` · 2026-10-02 (UTC).
Namespace: `research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/databento_metadata_probe/`.
Script: `probe_metadata.py` (this dir). Raw evidence: `metadata_results.json`
(sha256 `fa9fe26d5d4832f5a60a6283f2d6f40e0e91d0171aa6e348feb0a9af46babe1b`).

**Authority scope honored:** metadata READ-ONLY against official Databento
endpoints. **Zero data bytes downloaded** — no `timeseries.get_range`, no batch
job, no live session, no purchase, no subscription, no ToS acceptance, no
account change. Every number below came from a live metadata call at run time
(recorded per request in `metadata_results.json` with UTC timestamps).

## 1. Endpoint verification (BEFORE any call; docs + official client source)

Verified against CURRENT official sources on 2026-10-02:
- Docs URLs (JS-rendered pages; routes verified HTTP 200; content verified via
  Databento's own docs search API `api.databento.com/v0/docs/search`, build
  `01M3QSBT40W79JPVNV0CHMKD5E`, and web search over the same published pages).
- Official Python client source `github.com/databento/databento-python`
  @ main `25eef4ee8e66559e2370166a57c20925ce244d49` — snapshots frozen in
  `evidence/databento_client_metadata.py.snapshot` (sha256 `f6e0d1dac704b017597b270a6ef5c7f21d8b446b4bb3b35d4fceddfae524d890`),
  `evidence/databento_client_symbology.py.snapshot` (sha256 `92d919e7d62381c00e06adf42215fb95d11a77740eec6d37f202661e43725ef4`).
- RPC form confirmed by docs API-reference page: `https://hist.databento.com/v0/METHOD_FAMILY.METHOD`.

| Endpoint | Method | Docs URL (access 2026-10-02) | Billing-safety conclusion |
|---|---|---|---|
| metadata.list_datasets | GET | https://databento.com/docs/api-reference-historical/metadata/list-datasets | SAFE — returns list of dataset codes; no data payload |
| metadata.list_schemas | GET | https://databento.com/docs/api-reference-historical/metadata/list-schemas | SAFE — schema name list |
| metadata.get_dataset_range | GET | https://databento.com/docs/api-reference-historical/metadata/get-dataset-range | SAFE — "available range for the dataset given the user's entitlements"; metadata only |
| metadata.list_unit_prices | GET | https://databento.com/docs/api-reference-historical/metadata/list-unit-prices | SAFE — "unit prices ... in US dollars per gigabyte" per schema per mode |
| metadata.get_record_count | POST | https://databento.com/docs/api-reference-historical/metadata/get-record-count | SAFE — returns an integer count; no data |
| metadata.get_billable_size | POST | https://databento.com/docs/api-reference-historical/metadata/get-billable-size | SAFE — returns integer "billable uncompressed raw binary size"; no data |
| metadata.get_cost | POST | https://databento.com/docs/api-reference-historical/metadata/get-cost | SAFE — returns a float USD quote ("definitive quote" per docs data-catalog page); a quote cannot bill |
| symbology.resolve | POST | https://databento.com/docs/api-reference-historical/symbology/resolve | SAFE — docs symbology page: "Databento offers symbology resolution for free in our symbology.resolve endpoint" |

Billing model evidence (usage-pricing docs page, via docs search, 2026-10-02):
"you pay only for the data that you've used ... Historical data is billed per
byte consumed. Databento meters data by its uncompressed size in binary
encoding." Charges therefore accrue on DATA DELIVERY endpoints only.

**NOT_RUN_DOC_UNCLEAR:** any whoami/account/balance endpoint — none exists in
the official client API surface or the docs nav. Consequence: account credits
(the $125 signup credit) are NOT visible through any endpoint this lane could
verify → credits = NOT_RUN_DOC_UNCLEAR (and are not free spend in any case).
Authentication itself was verified by the authenticated metadata calls
(HTTP 200 with the owner key vs 401 without).

## 2. Execution summary

- 80 logical requests planned and executed (hard cap 80; sequential; 1 in
  flight; ≤3 attempts each; sleep 0.4 s between requests).
- Outcome: **78 ok (HTTP 200), 2 blocked (HTTP 422), 0 auth failures (no
  401/403), 0 retries exhausted.** PILOT block was clean → EXPANSION block
  executed per dispatch gate.
- **Zero data bytes downloaded** (all endpoints metadata-only).
- 2 blocked requests: `symbology.resolve` with
  `stype_in=continuous -> stype_out=raw_symbol` on GLBX.MDP3 (both PILOT-06
  and EXP-09). API message: "Unable to process symbology with parameters ...
  See the symbology docs for supported combinations per dataset". Typed as
  **BLOCKED_INVALID_REQUEST**; the manifest's P0-4 assumption
  (continuous→raw_symbol) is not a supported combination for this dataset.
  Free-endpoint fix for next round: resolve `continuous -> instrument_id`
  (still free, still metadata-only).

## 3. Phase-A metadata findings (P0-1 / P0-2)

- `list_datasets`: GLBX.MDP3 **present** (28 datasets listed). OBSERVED.
- `list_schemas` (GLBX.MDP3): `mbo, mbp-1, mbp-10, tbbo, trades, bbo-1s,
  bbo-1m, ohlcv-1s, ohlcv-1m, ohlcv-1h, ohlcv-1d, definition, statistics,
  status, cmbp-1, cbbo-1s, cbbo-1m`.
  **P0-1 additional check: `ohlcv-eod` is NOT exposed** → session-aligned
  dailies CANNOT come from the vendor directly; the manifest's fallback
  (self-aggregate session dailies from ohlcv-1m / statistics official OHLC)
  stands. OBSERVED.
- `get_dataset_range` (entitlement-aware) — full per-schema coverage returned:

| schema | start | end (probe time) |
|---|---|---|
| mbo | 2017-05-21 | 2026-10-02 |
| mbp-1 | 2010-06-06 | 2026-10-02 |
| mbp-10 | 2010-06-06 | 2026-10-02 |
| tbbo | 2010-06-06 | 2026-10-02 |
| trades | 2010-06-06 | 2026-10-02 |
| bbo-1s | 2010-06-06 | 2026-10-02 |
| bbo-1m | 2010-06-06 | 2026-10-02 |
| ohlcv-1s | 2010-06-06 | 2026-10-02 |
| ohlcv-1m | 2010-06-06 | 2026-10-02 |
| ohlcv-1h | 2010-06-06 | 2026-10-02 |
| ohlcv-1d | 2010-06-06 | 2026-10-02 |
| definition | 2010-06-06 | 2026-10-02 |
| statistics | 2010-06-06 | 2026-10-02 |
| status | 2010-06-06 | 2026-10-02 |
| cmbp-1 | 2017-05-21 | 2026-10-02 |
| cbbo-1s | 2017-05-21 | 2026-10-02 |
| cbbo-1m | 2017-05-21 | 2026-10-02 |

  Dataset level: 2010-06-06 .. 2026-10-02. This is
  consistent with historical entitlement to GLBX.MDP3 at metadata level
  (dataset range is documented as "given the user's entitlements"); no 403
  occurred anywhere. Entitlement status per line: AVAILABLE (metadata level).
  NOTE (dataset-level statement; per-symbol x per-schema x per-date start
  dates remain P0-3's job — see limitations).
- `list_unit_prices` (GLBX.MDP3, USD per GB, captured 2026-10-02 — the only
  legitimate price source):

| schema | historical $/GB | historical-streaming $/GB | live $/GB |
|---|---|---|---|
| bbo-1m | 18.0 | 18.0 | 21.6 |
| bbo-1s | 18.0 | 18.0 | 21.6 |
| cbbo-1m | 18.0 | 18.0 | 21.6 |
| cbbo-1s | 18.0 | 18.0 | 21.6 |
| cmbp-1 | 1.8 | 1.8 | 2.16 |
| definition | 1.7 | 1.7 | 2.04 |
| mbo | 1.8 | 1.8 | 2.16 |
| mbp-1 | 1.8 | 1.8 | 2.16 |
| mbp-10 | 0.5 | 0.5 | 0.6 |
| ohlcv-1d | 190.0 | 190.0 | 228.0 |
| ohlcv-1h | 190.0 | 190.0 | 228.0 |
| ohlcv-1m | 70.0 | 70.0 | 84.0 |
| ohlcv-1s | 70.0 | 70.0 | 84.0 |
| statistics | 1.0 | 1.0 | 1.2 |
| status | 4.0 | 4.0 | 4.0 |
| tbbo | 28.0 | 28.0 | 33.6 |
| trades | 28.0 | 28.0 | 33.6 |

Full historical-mode price list: {"mbo": 1.8, "mbp-1": 1.8, "mbp-10": 0.5, "tbbo": 28.0, "trades": 28.0, "bbo-1s": 18.0, "bbo-1m": 18.0, "ohlcv-1s": 70.0, "ohlcv-1m": 70.0, "ohlcv-1h": 190.0, "ohlcv-1d": 190.0, "definition": 1.7, "statistics": 1.0, "status": 4.0, "cmbp-1": 1.8, "cbbo-1s": 18.0, "cbbo-1m": 18.0}

## 4. Per-request table (all 80; timestamps UTC; errors redacted)

| rid | ts_utc | endpoint | line | schema | symbols | window | HTTP | result | note | error_redacted |
|---|---|---|---|---|---|---|---|---|---|---|
| R001 | 2026-10-02T10:37:47 | list_datasets | P0-1 | - |  | .. | 200 | list[29] | auth check + dataset list |  |
| R002 | 2026-10-02T10:37:49 | list_schemas | P0-1 | - |  | .. | 200 | list[17] | schema set; ohlcv-eod presence check |  |
| R003 | 2026-10-02T10:37:51 | get_dataset_range | P0-1 | - |  | .. | 200 | dict keys=start,end,schema | coverage range GIVEN entitlements |  |
| R004 | 2026-10-02T10:37:52 | list_unit_prices | P0-2 | - |  | .. | 200 | list[3] | USD/GB per schema per mode; the only pri |  |
| R005 | 2026-10-02T10:37:54 | symbology.resolve | PILOT-06 | - | NQ.c.0,NQ.n.0,NQ.v.0,CL.c.0,CL.n.0 | 2010-01-01..2026-10-01 | 422 | - | vendor roll tables (FREE endpoint) | HTTP 422: {"detail":{"case":"symbology_invalid_request","message":"Unable to process symbo |
| R006 | 2026-10-02T10:37:55 | get_record_count | PILOT-01 | definition | NQ.FUT,CL.FUT | 2024-12-01..2026-10-01 | 200 | 2,496,868 |  |  |
| R007 | 2026-10-02T10:37:57 | get_billable_size | PILOT-01 | definition | NQ.FUT,CL.FUT | 2024-12-01..2026-10-01 | 200 | 1,298,371,360 |  |  |
| R008 | 2026-10-02T10:38:04 | get_record_count | PILOT-02 | statistics | NQ.FUT,CL.FUT | 2025-08-01..2026-10-01 | 200 | 11,209,402 |  |  |
| R009 | 2026-10-02T10:38:06 | get_billable_size | PILOT-02 | statistics | NQ.FUT,CL.FUT | 2025-08-01..2026-10-01 | 200 | 896,752,160 |  |  |
| R010 | 2026-10-02T10:38:08 | get_cost | PILOT-02 | statistics | NQ.FUT,CL.FUT | 2025-08-01..2026-10-01 | 200 | 0.835165530443 | get_cost cross-check vs bs*unit_price |  |
| R011 | 2026-10-02T10:38:10 | get_billable_size | PILOT-03 | ohlcv-1d | NQ.FUT,CL.FUT | 2025-08-25..2025-09-19 | 200 | 270,648 | window NQ-U5->Z5 |  |
| R012 | 2026-10-02T10:38:12 | get_billable_size | PILOT-03 | ohlcv-1d | NQ.FUT,CL.FUT | 2025-11-17..2025-12-19 | 200 | 342,048 | window NQ-Z5->H6 |  |
| R013 | 2026-10-02T10:38:14 | get_billable_size | PILOT-03 | ohlcv-1d | NQ.FUT,CL.FUT | 2026-02-23..2026-03-20 | 200 | 343,896 | window NQ-H6->M6 |  |
| R014 | 2026-10-02T10:38:15 | get_billable_size | PILOT-03 | ohlcv-1d | NQ.FUT,CL.FUT | 2026-05-25..2026-06-19 | 200 | 284,424 | window NQ-M6->U6 |  |
| R015 | 2026-10-02T10:38:18 | get_billable_size | PILOT-03 | ohlcv-1d | NQ.FUT,CL.FUT | 2025-09-22..2025-10-03 | 200 | 124,488 | window CL-roll-1 |  |
| R016 | 2026-10-02T10:38:21 | get_billable_size | PILOT-03 | ohlcv-1d | NQ.FUT,CL.FUT | 2025-12-22..2026-01-02 | 200 | 98,336 | window CL-roll-2 |  |
| R017 | 2026-10-02T10:38:22 | get_billable_size | PILOT-03 | ohlcv-1d | NQ.FUT,CL.FUT | 2026-03-24..2026-04-03 | 200 | 125,608 | window CL-roll-3 |  |
| R018 | 2026-10-02T10:38:24 | get_billable_size | PILOT-03 | ohlcv-1d | NQ.FUT,CL.FUT | 2026-06-24..2026-07-03 | 200 | 102,592 | window CL-roll-4 |  |
| R019 | 2026-10-02T10:38:28 | get_record_count | PILOT-04 | ohlcv-1m | NQU5 | 2025-08-28..2025-08-29 | 200 | 1,380 | window NQU5 |  |
| R020 | 2026-10-02T10:38:29 | get_billable_size | PILOT-04 | ohlcv-1m | NQU5 | 2025-08-28..2025-08-29 | 200 | 77,280 | window NQU5 |  |
| R021 | 2026-10-02T10:38:34 | get_record_count | PILOT-04 | ohlcv-1m | NQZ5 | 2025-11-26..2025-11-28 | 200 | 2,520 | window NQZ5 |  |
| R022 | 2026-10-02T10:38:36 | get_billable_size | PILOT-04 | ohlcv-1m | NQZ5 | 2025-11-26..2025-11-28 | 200 | 141,120 | window NQZ5 |  |
| R023 | 2026-10-02T10:38:38 | get_record_count | PILOT-04 | ohlcv-1m | NQH6 | 2026-02-26..2026-02-27 | 200 | 1,380 | window NQH6 |  |
| R024 | 2026-10-02T10:38:39 | get_billable_size | PILOT-04 | ohlcv-1m | NQH6 | 2026-02-26..2026-02-27 | 200 | 77,280 | window NQH6 |  |
| R025 | 2026-10-02T10:38:43 | get_record_count | PILOT-04 | ohlcv-1m | NQM6 | 2026-05-28..2026-05-29 | 200 | 1,380 | window NQM6 |  |
| R026 | 2026-10-02T10:38:44 | get_billable_size | PILOT-04 | ohlcv-1m | NQM6 | 2026-05-28..2026-05-29 | 200 | 77,280 | window NQM6 |  |
| R027 | 2026-10-02T10:38:47 | get_record_count | PILOT-04 | ohlcv-1m | NQU6 | 2026-08-28..2026-08-31 | 200 | 1,380 | window NQU6 |  |
| R028 | 2026-10-02T10:38:50 | get_billable_size | PILOT-04 | ohlcv-1m | NQU6 | 2026-08-28..2026-08-31 | 200 | 77,280 | window NQU6 |  |
| R029 | 2026-10-02T10:38:52 | get_record_count | PILOT-04 | ohlcv-1m | NQZ6,NQH7 | 2026-09-30..2026-10-01 | 200 | 1,663 | window NQZ6/NQH7 |  |
| R030 | 2026-10-02T10:38:54 | get_billable_size | PILOT-04 | ohlcv-1m | NQZ6,NQH7 | 2026-09-30..2026-10-01 | 200 | 93,128 | window NQZ6/NQH7 |  |
| R031 | 2026-10-02T10:38:57 | get_record_count | PILOT-04 | ohlcv-1m | CLV5 | 2025-08-28..2025-08-29 | 200 | 1,323 | window CLV5 |  |
| R032 | 2026-10-02T10:39:00 | get_billable_size | PILOT-04 | ohlcv-1m | CLV5 | 2025-08-28..2025-08-29 | 200 | 74,088 | window CLV5 |  |
| R033 | 2026-10-02T10:39:02 | get_record_count | PILOT-04 | ohlcv-1m | CLX5 | 2025-09-29..2025-09-30 | 200 | 1,346 | window CLX5 |  |
| R034 | 2026-10-02T10:39:04 | get_billable_size | PILOT-04 | ohlcv-1m | CLX5 | 2025-09-29..2025-09-30 | 200 | 75,376 | window CLX5 |  |
| R035 | 2026-10-02T10:39:07 | get_record_count | PILOT-04 | ohlcv-1m | CLZ5 | 2025-10-30..2025-10-31 | 200 | 1,367 | window CLZ5 |  |
| R036 | 2026-10-02T10:39:11 | get_billable_size | PILOT-04 | ohlcv-1m | CLZ5 | 2025-10-30..2025-10-31 | 200 | 76,552 | window CLZ5 |  |
| R037 | 2026-10-02T10:39:14 | get_record_count | PILOT-04 | ohlcv-1m | CLF6 | 2025-11-26..2025-11-28 | 200 | 2,532 | window CLF6 |  |
| R038 | 2026-10-02T10:39:16 | get_billable_size | PILOT-04 | ohlcv-1m | CLF6 | 2025-11-26..2025-11-28 | 200 | 141,792 | window CLF6 |  |
| R039 | 2026-10-02T10:39:25 | get_record_count | PILOT-04 | ohlcv-1m | CLJ6 | 2026-02-26..2026-02-27 | 200 | 1,368 | window CLJ6 |  |
| R040 | 2026-10-02T10:39:28 | get_billable_size | PILOT-04 | ohlcv-1m | CLJ6 | 2026-02-26..2026-02-27 | 200 | 76,608 | window CLJ6 |  |
| R041 | 2026-10-02T10:39:32 | get_record_count | PILOT-04 | ohlcv-1m | CLN6 | 2026-05-28..2026-05-29 | 200 | 1,376 | window CLN6 |  |
| R042 | 2026-10-02T10:39:33 | get_billable_size | PILOT-04 | ohlcv-1m | CLN6 | 2026-05-28..2026-05-29 | 200 | 77,056 | window CLN6 |  |
| R043 | 2026-10-02T10:39:36 | get_record_count | PILOT-04 | ohlcv-1m | CLU6 | 2026-07-30..2026-07-31 | 200 | 1,372 | window CLU6 |  |
| R044 | 2026-10-02T10:39:40 | get_billable_size | PILOT-04 | ohlcv-1m | CLU6 | 2026-07-30..2026-07-31 | 200 | 76,832 | window CLU6 |  |
| R045 | 2026-10-02T10:39:42 | get_record_count | PILOT-04 | ohlcv-1m | CLV6,CLX6 | 2026-09-30..2026-10-01 | 200 | 1,369 | window CL front strip |  |
| R046 | 2026-10-02T10:39:46 | get_billable_size | PILOT-04 | ohlcv-1m | CLV6,CLX6 | 2026-09-30..2026-10-01 | 200 | 76,664 | window CL front strip |  |
| R047 | 2026-10-02T10:39:48 | get_billable_size | PILOT-05 | bbo-1m | NQU5 | 2025-08-28..2025-08-29 | 200 | 110,880 | window NQU5 |  |
| R048 | 2026-10-02T10:39:55 | get_billable_size | PILOT-05 | bbo-1m | NQZ5 | 2025-11-26..2025-11-28 | 200 | 205,600 | window NQZ5 |  |
| R049 | 2026-10-02T10:39:57 | get_billable_size | PILOT-05 | bbo-1m | NQH6 | 2026-02-26..2026-02-27 | 200 | 111,440 | window NQH6 |  |
| R050 | 2026-10-02T10:39:58 | get_billable_size | PILOT-05 | bbo-1m | NQM6 | 2026-05-28..2026-05-29 | 200 | 110,880 | window NQM6 |  |
| R051 | 2026-10-02T10:40:19 | get_billable_size | PILOT-05 | bbo-1m | NQU6 | 2026-08-28..2026-08-31 | 200 | 110,960 | window NQU6 |  |
| R052 | 2026-10-02T10:40:21 | get_billable_size | PILOT-05 | bbo-1m | NQZ6,NQH7 | 2026-09-30..2026-10-01 | 200 | 221,520 | window NQZ6/NQH7 |  |
| R053 | 2026-10-02T10:40:23 | get_billable_size | PILOT-05 | bbo-1m | CLV5 | 2025-08-28..2025-08-29 | 200 | 110,960 | window CLV5 |  |
| R054 | 2026-10-02T10:40:25 | get_billable_size | PILOT-05 | bbo-1m | CLX5 | 2025-09-29..2025-09-30 | 200 | 110,560 | window CLX5 |  |
| R055 | 2026-10-02T10:40:27 | get_billable_size | PILOT-05 | bbo-1m | CLZ5 | 2025-10-30..2025-10-31 | 200 | 111,040 | window CLZ5 |  |
| R056 | 2026-10-02T10:40:30 | get_billable_size | PILOT-05 | bbo-1m | CLF6 | 2025-11-26..2025-11-28 | 200 | 210,960 | window CLF6 |  |
| R057 | 2026-10-02T10:40:33 | get_billable_size | PILOT-05 | bbo-1m | CLJ6 | 2026-02-26..2026-02-27 | 200 | 110,640 | window CLJ6 |  |
| R058 | 2026-10-02T10:40:38 | get_billable_size | PILOT-05 | bbo-1m | CLN6 | 2026-05-28..2026-05-29 | 200 | 110,720 | window CLN6 |  |
| R059 | 2026-10-02T10:40:47 | get_billable_size | PILOT-05 | bbo-1m | CLU6 | 2026-07-30..2026-07-31 | 200 | 111,040 | window CLU6 |  |
| R060 | 2026-10-02T10:40:49 | get_billable_size | PILOT-05 | bbo-1m | CLV6,CLX6 | 2026-09-30..2026-10-01 | 200 | 111,040 | window CL front strip |  |
| R061 | 2026-10-02T10:40:52 | get_cost | PILOT-04 | ohlcv-1m | CLF6 | 2025-11-26..2025-11-28 | 200 | 0.009243786335 | get_cost cross-check on largest PILOT-04 |  |
| R062 | 2026-10-02T10:40:54 | get_record_count | EXP-01 | definition | NQ.FUT,ES.FUT,CL.FUT,NG.FUT,GC.FUT | 2010-06-06..2026-10-01 | 200 | 51,408,105 | joined 10 roots |  |
| R063 | 2026-10-02T10:40:56 | get_billable_size | EXP-01 | definition | NQ.FUT,ES.FUT,CL.FUT,NG.FUT,GC.FUT | 2010-06-06..2026-10-01 | 200 | 26,732,214,600 | joined 10 roots |  |
| R064 | 2026-10-02T10:41:07 | get_record_count | EXP-02 | statistics | NQ.FUT,ES.FUT,CL.FUT,NG.FUT,GC.FUT | 2010-06-06..2026-10-01 | 200 | 262,206,777 | joined 10 roots |  |
| R065 | 2026-10-02T10:41:10 | get_billable_size | EXP-02 | statistics | NQ.FUT,ES.FUT,CL.FUT,NG.FUT,GC.FUT | 2010-06-06..2026-10-01 | 200 | 20,976,542,160 | joined 10 roots |  |
| R066 | 2026-10-02T10:41:13 | get_record_count | EXP-03 | ohlcv-1d | NQ.FUT,ES.FUT,CL.FUT,NG.FUT,GC.FUT | 2010-06-06..2026-10-01 | 200 | 2,094,058 | joined 10 roots |  |
| R067 | 2026-10-02T10:41:22 | get_billable_size | EXP-03 | ohlcv-1d | NQ.FUT,ES.FUT,CL.FUT,NG.FUT,GC.FUT | 2010-06-06..2026-10-01 | 200 | 117,267,248 | joined 10 roots |  |
| R068 | 2026-10-02T10:41:30 | get_record_count | EXP-04 | ohlcv-1m | NQ.FUT | 2019-01-01..2026-10-01 | 200 | 3,933,682 | per-root NQ full line window |  |
| R069 | 2026-10-02T10:41:32 | get_record_count | EXP-04 | ohlcv-1m | ES.FUT | 2019-01-01..2026-10-01 | 200 | 4,356,678 | per-root ES full line window |  |
| R070 | 2026-10-02T10:41:35 | get_record_count | EXP-04 | ohlcv-1m | CL.FUT | 2019-01-01..2026-10-01 | 200 | 52,904,358 | per-root CL full line window |  |
| R071 | 2026-10-02T10:41:38 | get_record_count | EXP-04 | ohlcv-1m | NG.FUT | 2019-01-01..2026-10-01 | 200 | 35,792,075 | per-root NG full line window |  |
| R072 | 2026-10-02T10:41:40 | get_billable_size | EXP-04 | ohlcv-1m | NQ.FUT,ES.FUT,CL.FUT,NG.FUT | 2019-01-01..2026-10-01 | 200 | 5,431,260,408 | joined NQ,ES,CL,NG |  |
| R073 | 2026-10-02T10:41:45 | get_record_count | EXP-05 | ohlcv-1m | GC.FUT | 2021-01-01..2026-10-01 | 200 | 6,469,794 | per-root GC full line window |  |
| R074 | 2026-10-02T10:41:47 | get_record_count | EXP-05 | ohlcv-1m | SI.FUT | 2021-01-01..2026-10-01 | 200 | 4,304,935 | per-root SI full line window |  |
| R075 | 2026-10-02T10:41:48 | get_record_count | EXP-05 | ohlcv-1m | 6E.FUT | 2021-01-01..2026-10-01 | 200 | 2,946,494 | per-root 6E full line window |  |
| R076 | 2026-10-02T10:41:50 | get_record_count | EXP-05 | ohlcv-1m | 6J.FUT | 2021-01-01..2026-10-01 | 200 | 2,707,178 | per-root 6J full line window |  |
| R077 | 2026-10-02T10:41:53 | get_record_count | EXP-05 | ohlcv-1m | 6B.FUT | 2021-01-01..2026-10-01 | 200 | 2,331,442 | per-root 6B full line window |  |
| R078 | 2026-10-02T10:41:55 | get_record_count | EXP-05 | ohlcv-1m | 6A.FUT | 2021-01-01..2026-10-01 | 200 | 2,461,135 | per-root 6A full line window |  |
| R079 | 2026-10-02T10:42:04 | get_billable_size | EXP-05 | ohlcv-1m | GC.FUT,SI.FUT,6E.FUT,6J.FUT,6B.FUT | 2021-01-01..2026-10-01 | 200 | 1,188,374,768 | joined GC,SI,6E,6J,6B,6A |  |
| R080 | 2026-10-02T10:42:06 | symbology.resolve | EXP-09 | - | ES.c.0,ES.n.0,ES.v.0,NG.c.0,NG.n.0 | 2010-01-01..2026-10-01 | 422 | - | vendor roll tables (FREE endpoint) | HTTP 422: {"detail":{"case":"symbology_invalid_request","message":"Unable to process symbo |

## 5. Per-line aggregates (API numbers only)

cost_usd_computed = sum(get_billable_size)/1e9 x unit_price(schema,
historical mode) — the request manifest's own method. get_cost (API's own
quote) called on 2 shapes as cross-checks.

| line | ok/req | record_count (measured) | billable GB | cost computed (list) | get_cost API | errors |
|---|---|---|---|---|---|---|
| PILOT-01 | 2/2 ok | 2496868 | 1.2984 | 2.2072 | - | - |
| PILOT-02 | 3/3 ok | 11209402 | 0.8968 | 0.8968 | 0.835165530443 | - |
| PILOT-03 | 8/8 ok | DERIVED 30,215 | 0.0017 | 0.3215 | - | - |
| PILOT-04 | 29/29 ok | 21756 | 0.0012 | 0.0853 | 0.009243786335 | - |
| PILOT-05 | 14/14 ok | DERIVED 23,228 | 0.0019 | 0.0334 | - | - |
| PILOT-06 | 0/1 ok | - | None | 0 | - | R005 |
| EXP-01 | 2/2 ok | 51408105 | 26.7322 | 45.4448 | - | - |
| EXP-02 | 2/2 ok | 262206777 | 20.9765 | 20.9765 | - | - |
| EXP-03 | 2/2 ok | 2094058 | 0.1173 | 22.2808 | - | - |
| EXP-04 | 5/5 ok | 96986793 | 5.4313 | 380.1882 | - | - |
| EXP-05 | 7/7 ok | 21220978 | 1.1884 | 83.1862 | - | - |
| EXP-06 | NOT_RUN (windows_rule / placeholder — not enumerated by manifest) | - | - | - | - |
| EXP-07 | NOT_RUN (windows_rule / placeholder — not enumerated by manifest) | - | - | - | - |
| EXP-08 | NOT_RUN (windows_rule / placeholder — not enumerated by manifest) | - | - | - | - |
| EXP-09 | 0/1 ok | - | None | 0 | - | R080 |

Internal consistency check (OBSERVED): for every line where both record_count
and billable_size were measured, billable_bytes = record_count x DBN record
size (definition 520 B, statistics 80 B, ohlcv 56 B) EXACTLY — cross-validates
the API numbers against the DBN-ADAPTER lane's frozen spec (`code/futbt/dbn/spec.py`).

### get_cost vs computed cost (cross-checks)

| rid | schema | get_cost USD | computed bs x price USD | ratio |
|---|---|---|---|---|
| R010 | statistics | 0.835165530443 | 0.896752 | 0.9313 |
| R061 | ohlcv-1m | 0.009243786335 | 0.009925 | 0.9313 |

The ratio is **exactly 0.9313 on both cross-checks** (two different schemas,
two different shapes): `get_cost` returns ~6.9 % LESS than billable_size x
list unit price. Mechanism NOT documented/verified (docstring: "respects any
discounts provided by flat rate plans"). get_cost is treated as the
authoritative quote; ratio-adjusted estimates below are labeled as such.

## 6. Package aggregates (from API numbers only)

**PILOT package (PILOT-01..05, exactly as the manifest specifies):**
- record_count measured: **13,728,026** (PILOT-01
  2,496,868 + PILOT-02 11,209,402 + PILOT-04 21,756);
  plus DERIVED-not-measured 53,443
  (PILOT-03 from bytes/56, PILOT-05 from bytes/80 — record counts for those
  two lines are NOT_RUN this round, request-cap bound).
- billable size: **2.1999 GB** (uncompressed DBN basis).
- cost: **$3.5442** at list unit prices;
  **~$3.3** applying the measured get_cost ratio 0.9313.
- PILOT-06 (symbology roll tables): FREE endpoint; BLOCKED_INVALID_REQUEST
  this round on an unsupported stype combination (fix documented above); $0.

**EXPANSION measured lines (EXP-01..05 as specified):**
- record_count measured: **433,916,711**
  (definition 51,408,105; statistics
  262,206,777; ohlcv-1d 2,094,058;
  ohlcv-1m tier-A 96,986,793; tier-B 21,220,978).
- billable size: **54.4457 GB** (≈21.8–32.7 GB on disk at the
  manifest's ASSUMED 0.4–0.6 zstd factor — well under the 200 GB internal cap).
- cost: **$552.0765** at list; **~$514.15**
  ratio-adjusted.
- Per-root ohlcv-1m record counts (OBSERVED): EXP-04 NQ 3,933,682,
  ES 4,356,678, CL 52,904,358, NG 35,792,075
  (2019-01-01..2026-10-01); EXP-05 GC 6,469,794, SI 4,304,935,
  6E 2,946,494, 6J 2,707,178, 6B 2,331,442,
  6A 2,461,135 (2021-01-01..2026-10-01). All 10 roots > 0
  over their full line windows.
- EXP-06/07/08: NOT_ENUMERATED by manifest design (windows depend on inputs
  not yet in hand) → excluded from every aggregate above.
- EXP-09: BLOCKED_INVALID_REQUEST (same 422 cause as PILOT-06); free endpoint.

## 7. Caveats, exclusions, quote validity

1. **get_cost is a quote, NOT a purchase.** No endpoint called by this lane
   can move money or deliver data. Credits (e.g. the $125 signup credit) are
   NOT free spend and are NOT visible via any verifiable metadata endpoint.
2. **Quote validity:** no explicit validity window is documented for
   get_cost/list_unit_prices values; prices captured 2026-10-02 are current
   as of capture. The manifest already mandates re-probing exact chunk
   params before each spend gate — treat these quotes as decision inputs for
   this cycle only.
3. **Billing exclusions/notes the API/docs state:** billable size is
   UNCOMPRESSED DBN bytes; vendor caveat — estimates "may not be accurate for
   time ranges that are not discrete multiples of 10 minutes" (all probed
   windows are whole UTC days, except the ohlcv-1m/bbo-1m named windows whose
   exclusive-end semantics are noted below); usage-pricing docs: you are
   billed for actual bytes delivered.
4. **End dates are EXCLUSIVE** per API semantics. Manifest windows were
   passed verbatim, so windows labeled e.g. 2026-09-30..2026-10-01 cover
   2026-09-30 only. If the owner wants 2026-10-01 included in the front-strip
   windows, the delivery request needs end+1 day and a re-probe then (small
   delta; do not extrapolate).
5. **Parent symbology correction:** with stype_in=parent the correct symbols
   are `{ROOT}.FUT` (e.g. NQ.FUT), per docs
   standards-and-conventions/symbology + examples (access 2026-10-02). The
   prepared probe scripts in `data/request/` pass bare roots (`NQ`) — that
   would mis-probe. NOT modified by this lane (frozen for audit); flagged
   here for the owner/audit lane.
6. **Method corrections vs prepared probes:** get_record_count /
   get_billable_size / get_cost are POST (form-encoded) on
   `https://hist.databento.com/v0/...` per the current official client; the
   prepared scripts assumed GET on `https://databento.com`. (The legacy host
   answered too during this run's fallback logic — no attempt needed it.)
7. list_unit_prices row shape observed: `{"mode": ..., "unit_prices": {schema: $/GB}}`.

## 8. NOT_RUN / limitations (never inferred as PASS)

- PILOT-06 / EXP-09 roll tables: BLOCKED_INVALID_REQUEST (422) — unsupported
  stype combination; HC3 divergence table NOT produced this round.
- Record counts for PILOT-03 (ohlcv-1d) and PILOT-05 (bbo-1m): NOT_RUN
  (request-cap bound); sizes/costs measured; DERIVED counts labeled as such.
- P0-3 earliest-window coverage grid (per root x schema x 2010/2012/2015/
  2019/2021 windows): NOT_RUN (request-cap bound). Partial compensation:
  get_dataset_range per-schema ranges (above) + per-root full-window record
  counts (all > 0) + dataset-level history start 2010-06-06.
- Account/whoami/credits: NOT_RUN_DOC_UNCLEAR (no verifiable endpoint).
- ohlcv-eod: ABSENT from list_schemas (answered, see §3).
- EXP-06/07/08: NOT_ENUMERATED by manifest design.

## 9. Provenance

- Raw per-request evidence: `metadata_results.json` (sha256
  `fa9fe26d5d4832f5a60a6283f2d6f40e0e91d0171aa6e348feb0a9af46babe1b`) — every request with UTC timestamps,
  params, HTTP status, payload, redacted errors; generated by
  `probe_metadata.py` (exit code 0; 80 logical requests; 2 non-200).
- Official client snapshots: `evidence/` (sha256 above; source
  github.com/databento/databento-python @ main 25eef4ee8e66559e2370166a57c20925ce244d49,
  accessed 2026-10-02).
- Docs accessed 2026-10-02: the 8 endpoint URLs in §1 +
  https://databento.com/docs/standards-and-conventions/symbology +
  https://databento.com/docs/pricing/usage-based-pricing-and-data-credits
  (content via api.databento.com/v0/docs/search, build 01M3QSBT40W79JPVNV0CHMKD5E,
  and web search over the published pages).
