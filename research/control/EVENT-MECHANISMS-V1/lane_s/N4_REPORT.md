# N4 DATED IDENTITY MAP v1 — REPORT (lane S, 2026-09-27)

## Inputs (measured, on-disk)

| Input | Path (relative to `.staging_eventmech/`) | Digest / lineage |
|---|---|---|
| Cohort members (ticker→CIK carried) | `integration/research/control/stocks_ng6_run/p0/cohort/cohort_members.json` (from stocks-ng6_integration.tar.gz, sha `808ca4f1…`) | derivative re-pin; lineage source `cohort_v9.json` sha `6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195666249e3fa2aa62` verified EXACT in this lane (extracted from stocks-free-v13 tar) |
| form4_stream (dated issuer CIKs) | `integration/.staging_sec_v13/form4_stream.jsonl` | sha256 `6ac2cd5b…742b2` = G2 pin EXACT |
| NG2 census-B resolver | extracted from git branch `orca/stocks-ng2-integration` → `research/control/stocks_ng2_run/p0_census_b_amendments_extended.json` (blob `d28b9e5c`, staging copy sha256 `ee58aead…`) | 3,059 amendment docs; **1,877 resolvable (issuerCik, rptOwnerCik, periodOfReport) pairs** per NG2 handoff `d2-measurement-handoff.json` (MATCH fail-closed). Note: this resolver serves the 4/A amendment arm, which G1 dropped — corroboration context only for this cycle |
| Price-panel member list | NG6 panel file stems (2,169 files) | sha manifest `ng6_panel_digest.txt` (`b0b5a2a9…`) |

## Measured schema facts

- `form4_stream.jsonl` row fields (measured from bytes): `cik` (issuer, `CIK##########`),
  `accession`, `acceptance` (UTC, `.000Z`), `filing_date`, `transaction_date`,
  `transaction_code`, `direction` (`A`/`D`), `shares` (string), `owner_cik`
  (nullable), `owner_name`, `table` (`nonDerivative`).
  **No issuer-name field; no ticker field.** Per R2-3 ambiguity law: recorded,
  mapping authority cannot be form4_stream — it can only corroborate CIKs.
- `cohort_members.json` row fields: `ticker`, `cik` (CIK##########), `name`,
  `bucket` (`ALIVE_EVIDENCED` 409 / `DEAD_EVIDENCED` 1,769), `sector`, `death_date`,
  `join_method`. Counts match `cohort_manifest.json` (`members: 2178`, `alive: 409`,
  `dead: 1769`, `shared_tickers: 10`, `unique_tickers: 2168`).
  Manifest `expected_sha256 6a95401f…` refers to the V9 SOURCE `cohort_v9.json`
  (verified EXACT here); the NG6 file is the re-pinned derivative — count-equality
  + source-sha equality close the chain.
- EDGAR `submissions` JSON: for DEAD issuers the `tickers[]` array is EMPTY
  (delisted); `name` still served. Measured below.

## Output

`.staging_eventmech/n4_map_v1.jsonl` — 2,178 rows (one per cohort member;
2,168 unique tickers; 10 tickers carry 2 members each → `ticker_reuse_risk: true`).

Per row: `ticker, cik, cik_num, name, bucket, sector, death_date, provenance,
form4_issuer_seen, price_file_present, ticker_reuse_risk, sources`.

## Coverage (measured)

| Metric | Value |
|---|---|
| rows total | 2,178 |
| provenance `censusB` | 2,178 (100%) — CIK carried by the sha-verified census lineage |
| provenance `unresolved` | 0 |
| provenance `form4_stream` | 0 as mapping authority (stream carries no ticker/name — measured); corroboration flag instead |
| `form4_issuer_seen: true` | 1,898 / 2,178 (87.1%) — issuer CIK appears in the pinned 546,039-row form4_stream (1,899 unique issuer CIKs; 1,898 intersect cohort) |
| `price_file_present: true` | 2,178 / 2,178 (100%) — every cohort ticker has an NG6 panel file |
| dead-name coverage | 1,769 / 1,769 dead rows have CIK + price file (survivorship-correct cohort) |
| panel stems not in cohort | 1 — `SPY` (benchmark series, not a cohort member) |

## Verification sample (network, 25 CIKs, data.sec.gov/submissions only)

Random sample seed=2026: 12 ALIVE_EVIDENCED + 13 DEAD_EVIDENCED.

- 12/12 ALIVE: HTTP 200 and mapped ticker ∈ `tickers[]` — **verified**.
- 13/13 DEAD: HTTP 200 (dead issuers fully served — replicates G2 BBBY
  finding), `tickers[]` = `[]` (empty for delisted issuers), `name` consistent
  with census name (e.g. CIK0001104855 "Support.com, Inc." = SPRT; CIK0000006284
  "ANALOGIC CORP" = ALOG). **0 contradictions; ticker-level check not applicable
  for dead names by SEC design.**
- Implication (recorded for engine lane): the ticker-level `tickers[]` check can
  only verify alive names. Dead-name identity rests on census lineage
  (sha-pinned) + Form-4 substrate issuer names — exactly the R4 "dated + never
  name-based" requirement, satisfied through the census CIK, not name matching.
- Evidence: `n4_verification.json` (raw per-row), fetch_log.jsonl.

## Identity-law notes for engine lane

1. Events attach to TICKER; 10 tickers carry 2 members each
   (`ticker_reuse_risk: true`, 20 rows) — per cohort identity law these are
   flagged and never silently merged.
2. 1 form4_stream issuer CIK is NOT in the cohort (1,899 stream issuers vs
   1,898 cohort-intersecting) — out-of-cohort insider flow is NOT in scope.
3. Ticker-level CIK conflicts: none found (all 2,178 rows map to distinct
   ticker→CIK pairs; `dup_cik_ticker_anomalies: 0` measured at S5 start).
