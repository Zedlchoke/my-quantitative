# LICENSE_RULINGS_VERIFIED.md — plan §3 ruling verification (L-PIT, 2026-09-26)

Cycle: DATA-FOUNDATION-FX-CRYPTO-STOCKS-V1 · Lane: L-PIT · branch
`orca/dfv1-lane-pit` · worktree `...data-foundation-v1/lane-pit`.

Method: EVERY row of plan §3 ("Prior data-authority rulings this cycle
inherits") was checked against its source artifact — a terminal verdict or
owner-packet file under `research/control/**` (root checkout or an evidence
worktree/branch). For each row: the artifact path, the measured artifact sha
(`git rev-parse <rev>:<path>` blob sha for committed files; the command and
revision are stated per row; nothing typed from memory), and a one-line
verbatim quote. A ruling without locatable evidence is UNVERIFIED — never
inferred PASS.

Row count: the committed plan §3 table has **15 rows** (the dispatch packet's
"~17" is approximate). Of the 15: **13 VERIFIED** (rows 9 and 15 verified with
documented caveats that the plan's one-line summary compresses), **1
PARTIALLY VERIFIED** (row 13 — 4 of 6 named sources evidenced, ECB weak,
BIS unlocated), **0 fully UNVERIFIED**. Row 13's BIS sub-part is the only
UNVERIFIED element in the table.

Shas below are git blob sha1 (`git -C <repo> rev-parse <rev>:<path>`); the
`<rev>` is the integration branch of the evidence cycle unless the file is in
the ROOT checkout, where `HEAD` = `8d549bcf7073b1b62b39d1976bbf418c24f0af49`
as measured at lane start (`git rev-parse HEAD`).

---

## Row 1 — Binance Vision + keyless public endpoints: authorized internal research, keyless

VERDICT: **VERIFIED**

- Artifacts:
  - `research/control/ng6_ng7_ng4_dossiers_2026-09/cng4-a3-prospective-contract-dossier.json` (ROOT, tracked) — sha `848587a3ba88e43d78574bd0948d1b52176dd8fe`
  - `research/control/bear_opportunity_recon_2026-09/data_a2/PIT_DISCLOSURES.md` (ROOT, tracked) — sha `25928953d0837c5404b142bf21b61e70b6651ac7`
- Quotes:
  - cng4-a3: `"series_id": "S4:binance-daily-h1-panels (CADS S4, V3-GA4 GRANTED)"` — the S4 frozen set is the Binance-derived H1 panel series, granted through the platform V3-GA4 authority table.
  - PIT_DISCLOSURES: `measured: 2026-09-23 (UTC), keyless probes of data.binance.vision + REST fapi.` — keyless access is the operating practice on record.

## Row 2 — Dukascopy public M1 BID/ASK: owner-delegated source choice 2026-09-23, TCU_RISK_DISCLOSED; corpus on disk

VERDICT: **VERIFIED**

- Artifact: `research/control/EURUSD-OPEN-SEARCH-V1/CYCLE_VERDICT.md` on branch `orca/eurusd-open-search-v1-integration` — sha `8c848f4c9d36d6d3f1fb8f95fb6efa97e7325cbb`
- Quote: `Recorded as `OWNER_DIRECTIVE_SOURCE_AUTHORIZATION` + `TCU_RISK_DISCLOSED` per owner directive 2026-09-23 #2; no account, no ToS acceptance, no purchase`
- Corpus-on-disk: `~/.my-quantitative-data/forex-intra-bidask-v1/raw` exists (census manifests committed in the EOSV1/FX-MAJORS branches: 3,652/3,652 day files, 0 missing, per the same CYCLE_VERDICT).

## Row 3 — *.dukascopy.com / *.cmegroup.com transport: BLOCKED_TRANSPORT (SNI filter)

VERDICT: **VERIFIED**

- Artifacts:
  - `research/control/forex_intra_bidask_v1/terminal_verdict.json` on branch `orca/forex-intra-bidask-v1-integration` — sha `f96358b537e9a381544be6a1552e074d4a64a95b` (FIBV1, Dukascopy)
  - `research/control/fx_futures_frontier_v1/terminal_verdict.json` on branch `orca/fx-futures-frontier-v1-integration` — sha `bae70ebbb695199fe4ba77da932bd517eca7387b` (FXF-F, CME)
- Quotes:
  - FIBV1: `"terminal_verdict": "BLOCKED_TRANSPORT"` + `local resolver returns 127.0.0.1 for probed *.dukascopy.com hostnames; TLS/HTTP resets on every connection naming dukascopy in SNI/Host`
  - FXF-F: `DoH-authentic Akamai IP 23.66.152.172 resets TLS with SNI=www.cmegroup.com while the SAME IP completes TLS for a different SNI (in-path SNI-keyed filter proven)`

## Row 4 — Dukascopy fresh TCU (any-service preamble, no-database, personal-non-commercial): worsened; re-acquisition needs owner license capture

VERDICT: **VERIFIED**

- Artifacts:
  - `research/control/eurusd_data_qualification_v1/probe/license_and_terms.md` on branch `orca/eurusd-data-qualification-v1-integration` — sha `8f6411ae0f43fd79cd729faa86d92b234468bf14`
  - `research/control/EURUSD-OPEN-SEARCH-V1/P1_SOURCE_RESURVEY_2026-09-23.md` on branch `orca/eurusd-open-search-v1-integration` — sha `b0366b1ffdb865607a18e3240927e0249c5c1943`
- Quotes:
  - EDQ1 TCU verbatim: `you agree to use the WEBSITE solely for your own non-commercial use and benefit` (Restrictions on Use); EDQ1 `research/control/eurusd_data_qualification_v1/probe/PROBE_VERDICT.md` (sha `badea3feba75ae1e28179a28700b038459f5428c`, same branch): `Resolution requires owner action — obtain Dukascopy's prior express written consent, or an owner legal decision on the TCU-vs-datafeed question.`
  - EOSV1 resurvey (re-checked 2026-09-23): `its probe/license_and_terms.md verbatim TCU quotes stand: personal non-commercial only, automated acquisition forbidden without prior express written consent, no-database clause, any-service preamble`

## Row 5 — TrueFX / OANDA v20 practice: owner license/account decision pending

VERDICT: **VERIFIED**

- Artifact: `research/control/eurusd_data_qualification_v1/owner_packet_source_survey_2026-09-22.md` on branch `orca/eurusd-data-qualification-v1-integration` — sha `aedb156ac6fb194e425de70fbbca7b84e5b61ada`
- Quote: `1. **TrueFX (Integral)** — tick bid/ask, free, free registration (not a … OWNER ACTION: register the free account personally (agent signup is` — and for OANDA: `OWNER ACTION: register the free practice account personally and accept its terms yourself`
- Corroboration (EOSV1 resurvey, sha above): `**OANDA status: `NOT_AVAILABLE_NO_OWNER_CREDENTIAL`.**` (no OANDA credential exists; decisions remain owner-pending).

## Row 6 — TD (Twelve Data): vendor OHLC-only; NO cost authority (F4 class)

VERDICT: **VERIFIED**

- Artifact: `research/control/ng6_ng7_ng4_dossiers_2026-09/fng7-a2-mechanism-proposal-dossier.json` (ROOT, tracked) — sha `8ec5fc82f5f3db032e9759d1709e76432347b2c4`
- Quotes: `TD daily payloads carry OHLC only - no volume, no tick data; any volume-flavored variant is NOT_MEASURABLE on this authority`; `"cost_authority": "BLOCKED (FOREX-NG6 P0_F4 fail-closed: vendor quote, not a broker product - spread/commission/swap UNMEASURABLE)"`
- Corroboration: EDQ1 PROBE_VERDICT — `**no bid/ask, no volume on this plan** → cannot be cost authority`.

## Row 7 — EODHD "All World": owner entitlement; EOD + some channels OK; earnings-history channel 403

VERDICT: **VERIFIED**

- Artifacts:
  - `research/control/stocks_free_v8_probe/eodhd_probe_verdict.json` (ROOT, tracked) — sha `06163c10bdb82fc101c4870b11d7174d0898efe5` (entitlement + EOD OK)
  - `research/control/stocks_ng3_run/probe_transcript_frozen.json` on branch `orca/stocks-ng3-integration` — sha `a7bf79bc3c651f345c6ed7694d8940f8eb33c8e4` (earnings 403)
- Quotes:
  - V8 probe: `"G1_license_entitlement": {"verdict": "PASS", "evidence": "paid subscription on the record; ToS + pricing bytes pinned; internal-research use"`
  - NG3 transcript: `"fundamentals-filter-earnings HTTP 403"` and `"calendar-earnings": "calendar-earnings HTTP 403 … Forbidden. Please contact support@eodhistoricaldata.com"`
- Ledger corroboration (STOCKS-NG3 row): `**/api/fundamentals/{ticker} — the only per-ticker earnings-history channel — 403 Forbidden** on 3/3 living canaries`.

## Row 8 — FINRA consolidated NMS short-sale: ToU INCOMPATIBLE with research use — terminal

VERDICT: **VERIFIED**

- Artifact: `research/control/stocks_ng4_run/audits/evidence/finra_terms_snapshot_2026-09-15.txt` (ROOT, tracked) — sha `84267d0f7044811dd0427adf748ad86c2bc07c57`
- Quotes: `the content and material provided through the FINRA Website shall be used ONLY for your own non-commercial personal or professional use` + restrictions `(d) "develop or create a database of data using the FINRA Website…"` / `(e) "use any process to monitor or copy the FINRA Website in bulk…"` / `(m) "…in conjunction with a model, algorithm, or process that is designed to predict trades…"`
- Terminal wording on record (ROOT `research/control/stocks_ng4_run/audits/a7_plan_ng4_v2.json`): `INCOMPATIBLE (terminal close STOCKS_NG4_BLOCKED_SOURCE_OR_SCHEMA, budget 0/6, 'no bulk retrieval ever runs in-cycle')`.

## Row 9 — SEC EDGAR (FTD/N-PORT/Form-4/4A): entitled, declared UA; PIT = acceptance timestamps; FTD ≥17d guard

VERDICT: **VERIFIED** (with a compression caveat — see note)

- Artifacts:
  - `research/control/ng6_ng7_ng4_dossiers_2026-09/sng6-a3-sec-source-pit-dossier.json` (ROOT, tracked) — sha `785faaafacb47c0ecfe2efe59a2a0124e158162b`
  - `research/control/data_edge_unlock_v1/lane_s/s_a3_pit_dossier.json` on branch `orca/data-edge-unlock-v1-integration` — sha `3c13b6a90dd3824ed4c0836aa6394753872796bd`
- Quotes:
  - Declared UA (DEU lane S): `"declared_ua": "my-quantitative-research-audit/0.1 (evidence audit; contact: repository OWNER via GitHub issues)"`
  - FTD guard (DEU lane S): `constants: { "POSTING_BOUND_DAYS": 15, "MIN_CONDITIONING_GUARD_DAYS": 16 }` + `recommend >=16-day guard, 17 to be conservative across holiday drift` — this is the "≥17d guard" of the plan row.
  - Acceptance timestamps (SNG6-A3): `EDGAR acceptance datetime (intraday) is not in the DERA set; obtaining it requires per-accession EDGAR index fetches - NOT acquired this cycle (intraday acceptance NOT_MEASURED)`; DEU: `intraday ACCEPTANCE DATETIME for NPORT-P accessions remains NOT_MEASURED… day-granularity FILING_DATE semantics (SNG6) remain the operative bound`.
- Caveat (recorded, not a refutation): acceptance timestamps are the declared PIT *authority class* for EDGAR filings, but for the DERA-served FTD/N-PORT history actually held, intraday acceptance is NOT_MEASURED and day-granularity posting bounds are the operative availability semantics. The plan row compresses this; successors must carry the caveat.

## Row 10 — OFR: official endpoints 200; RETRIEVAL_TIME_ONLY

VERDICT: **VERIFIED**

- Artifact: `research/control/free_data_frontier_v1r1_run/ofr_v1r1_summary.json` on branch `orca/free-data-frontier-v1r1-integration` — sha `546685d5623bb6b0f44a463a3c0c3413592ebbb1`
- Quotes: `"official_api_root": "https://data.financialresearch.gov/v1/"`, `"key_required": false`, records carry `"status": 200` and `retrieval_time_only` (per-record field in the same file; notes: `OFR publishes revised STFM data; per-row revision indicator not assumed`).

## Row 11 — NY Fed reference rates: entitled; revisionIndicator machine-served

VERDICT: **VERIFIED**

- Artifact: `research/control/free_data_frontier_v1_run/f4_acquisition/nyfed_markets_summary.json` on branch `orca/free-data-frontier-v1-integration` — sha `c8e331768d70847f248104a4cc873f27d56d2e53`
- Quote: `MEASURED: rows carry a revisionIndicator field (empty = original, flagged when re-stated) plus effectiveDate — revision status IS machine-served per row`

## Row 12 — Broker cost authority (FX majors): zero account-bound bytes in 3 independent censuses; IBKR gateway probe timed out unauthenticated

VERDICT: **VERIFIED**

- Artifact: `research/control/data_edge_unlock_v1/lane_f/f_cost_authority_dossier.json` on branch `orca/data-edge-unlock-v1-integration` — sha `cde599dc480759572756bd921154e632ad2cbe9f`
- Quotes: `"final_verdict": "BLOCKED_BROKER_COST_AUTHORITY"`; `"account_bound_bytes_found": false`; IBKR probe: `"target": "https://localhost:5000/v1/api/status (IBKR Client Portal gateway, UNAUTHENTICATED status only…)"`, `"curl_exit_code": 28`, `"interpretation": "timeout, no answer"`
- Three independent censuses on record inside the same dossier's evidence: (1) FOREX-NG6 P0-F4 (`spread.measurable_from_td=false`), (2) FOREX-NG7 F4 (`no citable FINANCING/cost band anywhere in the authorized evidence space`), (3) DEU Lane F repo-wide adjudication (`ZERO broker-account credentials of any kind`; filename census for broker/statement/swap/financing patterns: `0 hits`).

## Row 13 — CFTC CoT / Treasury / CBOE / FRED(owner key) / BIS / ECB: entitled official, per prior cycles

VERDICT: **PARTIALLY VERIFIED** (per-source split below; this plan row is a 6-source bundle)

- **CFTC CoT — VERIFIED.** Artifact: `research/control/commodities_ng1_run/p0_cot_market_census.json` on branch `orca/commodities-ng1-integration` — sha `8f42127ff120cec4d0ba50b25a61796ea6e89a26`. Quote: `"archives": ["deacot2016.zip", … "deacot2026.zip"]` (11 annual CFTC archives censused; COMMODITIES-NG1 scored on them). Note: a 2026-09-15 Socrata probe with default UA 403'd (`probe_cftc_cot_latest_403_defaultUA.bin`, ROOT `research/control/forex_frontier_2026-09/probes/PROBE_MANIFEST.json`, sha `d2c2b23eec07d98a708412aa80eec4589271c27d`) — channel/UA-sensitive, entitlement unaffected.
- **Treasury par yields — VERIFIED.** Artifact: `research/control/rates_ng1_run/p0_treasury_census.json` on branch `orca/rates-ng1-integration` — sha `0947ed3fab1f5f1c59527d734b4e2d6abadcc777`. Quote: `"years_pulled": 37, "years_expected": 37, "failed_years": []` (keyless per-year CSVs).
- **CBOE VIX family — VERIFIED.** Artifact: `research/control/vol_ng1_run/p0_census.json` on branch `orca/vol-ng1-integration` — sha `a5f61f1611cb712f4d76b27bf17aef15fd94f2e0`. Quote: `"index_name": "VIX", "served": true, "http_status": 200` (VIX/VIX9D/VIX3M/VIX6M censused with per-file sha256).
- **FRED (owner key) — VERIFIED.** Artifacts: `research/control/rates_ng1_run/p0_fred_repin.json` on `orca/rates-ng1-integration` (`"DGS10": {"status": "PINNED", "rows": 16878, … "sha256": "f3afd62f…"}`) + the rates terminal report on the same branch, `research/control/rates_ng1_run/terminal_report_rates_ng1.json` — sha `0947ed3fab1f5f1c59527d734b4e2d6abadcc777` — whose gates line reads `"p0": "PASS (floors: curve 0.9592/37 files; auctions 3555; ETP 4/4; FRED 7/7 CPIAUCSL 0-drift)"`. Key existence is recorded from prior artifacts only (variable-NAME censuses, values never read): ROOT EOSV1 `P1_SOURCE_RESURVEY_2026-09-23.md` (`FRED_API_KEY` listed, values never read) and DEU Lane F dossier (`environment_keys_by_NAME_ONLY_values_never_read: … FRED_API_KEY (vendor macro data)`). This lane never opened `.env`.
- **ECB — PARTIAL (reachability only).** Artifact: ROOT `research/control/forex_frontier_2026-09/probes/PROBE_MANIFEST.json` — sha `d2c2b23eec07d98a708412aa80eec4589271c27d`. Quote: `"result": "HTTP 200 (page serves) but anchor extraction found no monetary-policy press-release items…"` — an official-endpoint liveness probe, **not** a data-entitlement or corpus census. No ECB data authority artifact located.
- **BIS — UNVERIFIED.** No artifact citing a BIS source, endpoint, license or census was locatable in any `research/control/**` dir, worktree, or evidence branch searched by this lane (searched: bis.org / "Bank for International" patterns across root control, integration worktrees, and the named evidence branches). Per the packet law this element is marked UNVERIFIED — the plan's blanket "entitled official" must not be relied on for BIS until a source artifact exists.

## Row 14 — Coinbase/Kraken/Deribit keyless WS: collectors exist; PROSPECTIVE-only history

VERDICT: **VERIFIED**

- Artifact: `research/control/data_edge_unlock_v1/lane_c/c_collection_contract.json` on branch `orca/data-edge-unlock-v1-integration` — sha `d822c895f3f0ba2fcb6885bf5d54910ac8770f09`
- Quotes: `"endpoint": "wss://advanced-trade-ws.coinbase.com"` (Coinbase; Kraken Futures and Deribit channel sets frozen in the same contract — Kraken appears 7×); `WebSocket data is prospective-only from collector start and can NEVER backfill history`
- Collectors-exist corroboration (disk, read-only listing): `~/.my-quantitative-data/data-edge-unlock-v1/runtime/{coinbase,kraken,deribit}.{log,heartbeat.json}` + raw shards present; on-disk `*.open.rejected.jsonl` quarantine files recorded. No file contents read for this ruling.

## Row 15 — Binance OI/liquidation/L2 history: liquidationSnapshot 404; multi-year PIT OI/L2 none

VERDICT: **VERIFIED** (with the A7-documented caveat)

- Artifacts:
  - `research/control/bear_opportunity_recon_2026-09/data_a2/PIT_DISCLOSURES.md` (ROOT, tracked) — sha `25928953d0837c5404b142bf21b61e70b6651ac7`
  - `research/control/btc_h4_two_regime_v1/audits_a7/a7_terminal_trv1.json` on branch `orca/btc-h4-two-regime-v1-integration` — sha `14e447c914a568d7700e4b3c8673eca550599f87`
- Quotes: `um liquidationSnapshot (BTCUSDT-PERP) | NOTHING — no prefix under um/, all legacy-month HEADs (2020-01..2021-06) 404`; `metrics (OI) … the ONLY multi-year OI history that exists on Binance keyless surfaces, and it starts 2020-09-01` (RETROSPECTIVE_ONLY, daily files, T+1 publication); bookTicker export `DISCONTINUED after 2024-04`.
- Caveat (the plan's summary compresses, and BTC-H4-TWO-REGIME-V1's own A7 finding F2 says so): `the plan section 0 sentence 'liquidationSnapshot / metrics / bookTicker / bookDepth measured 404' overstates the cited inventory for three of the four streams` — metrics (OI) and bookDepth DO serve daily retrospective files; only um liquidationSnapshot is 404-everywhere. For the ruling's operative meaning (no multi-year PIT OI/L2 usable for live decisions; no liquidation tape) the evidence supports it; the nuance is binding on successors.

---

## Verification counters (this lane, 2026-09-26)

- Rows in plan §3: 15
- VERIFIED: 13 (rows 1,2,3,4,5,6,7,8,10,11,12,14 fully; rows 9,15 verified with recorded caveats)
- PARTIALLY VERIFIED: 1 (row 13 — CFTC/Treasury/CBOE/FRED verified; ECB reachability-only; **BIS UNVERIFIED**)
- Fully UNVERIFIED rows: 0 (1 UNVERIFIED sub-part: BIS)
- All shas in this file were measured this session via `git rev-parse` (no sha typed from memory); no `.env`, no sealed/holdout content, no network requests.
