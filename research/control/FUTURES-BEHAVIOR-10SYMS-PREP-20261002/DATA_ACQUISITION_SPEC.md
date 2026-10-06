# DATA_ACQUISITION_SPEC — Databento GLBX.MDP3 for FUTURES-BEHAVIOR-10SYMS (PREP ONLY)

Task: FUTURES-BEHAVIOR-10SYMS-PREP-20261002 · Lane: DATA-PIT-ACQUISITION-PREP
Date: 2026-10-02. Status: SPECIFICATION ONLY.

**Nothing in this document is authorization to purchase, register, activate,
subscribe, or download paid data.** Every paid action listed here requires an
explicit owner decision taken after the free pre-purchase verification
(§7 Request Plan) returns measured numbers. No credentials exist in this
document; none were created during this prep. Framework passages mentioning
Databento ("Databento phase-1 …") are HYPOTHESES about data needs, not orders.

Claims taxonomy used below: FACT(sourced) = primary/vendor doc + URL + access
date; OBSERVED = computed by `data/scripts/measure_coverage.py` over the legal
raw corpus; POSTULATED = mechanism reasoning; NOT_RUN/NOT_AVAILABLE = default.

Symbols: NQ, ES (CME equity index), CL, NG (NYMEX energy), GC, SI (COMEX
metals), 6E, 6J, 6B, 6A (CME FX).

---

## 1. Why a vendor at all (measured walls we cannot fetch through IBKR)

OBSERVED (`data/coverage_measured.json`, 1160 files, 0 parse errors; raw dir
`~/.my-quantitative-data/futures-10syms-v1/raw/`, read-only):

| Wall | Measurement (all 10 symbols) | Consequence |
|---|---|---|
| Expired-resolution depth wall | IBKR expired FUT secdef resolves only ~1y back (FUTURES-DATA-10SYMS-V1 finding 1). Measured front-chain REAL-VOLUME daily runs: NQ/ES/CL/NG/SI 17 months (2025-05→2026-09), GC 16, 6E/6J/6B/6A 14 | Cannot extend true-volume history retrospectively via IBKR |
| Settlement-only deep bars | 65–88% of on-disk daily bars are close-only O=H=L=C, v=0 (NQ 76%, ES 82%, CL 76%, NG 65%, GC 73%, SI 71%, 6E 83%, 6J 87%, 6B 87%, 6A 88%) | Deep per-contract closes are reference/signal prices, never fill prices |
| Intraday vintage wall | On-disk intraday is a snapshot: 2 trading days of M1 (RTH) + ~30 days of H1 per contract; IBKR M1/H1 availability probed only ~10 recent months (NG ~2.2y; S7_DEPTH_ACTIVE.json: probes at 2024/2022 ends returned n=0) | No multi-year intraday possible via IBKR backfill |
| Missing classes | No open interest, no exchange statistics schema, definitions only as embedded headers for fetched contracts | OI/statistics/definitions must come from elsewhere |

## 2. Dataset selection: GLBX.MDP3

FACT(sourced) — Databento catalog, https://databento.com/catalog/cme/GLBX.MDP3
(access 2026-10-02):

- Dataset ID `GLBX.MDP3`; venues **CME, CBOT, NYMEX, COMEX** (covers all 10
  symbols' venues); asset classes futures + options on futures; "Symbols
  650,000+"; "Available history 16 years".
- **"Available from 2010-06-06 UTC"** — dataset-level statement.
- Schemas: **MBO, MBP-1, MBP-10, TBBO, Trades, BBO-1s, BBO-1m, OHLCV-1s,
  OHLCV-1m, OHLCV-1h, OHLCV-1d, Definition, Statistics, Status, CMBP-1,
  CBBO-1s, CBBO-1m**. Encodings DBN, CSV, JSON.
- Feed spec https://databento.com/docs/venues-and-datasets/glbx-mdp3
  (access 2026-10-02): "full coverage of all futures and options on futures
  beginning in June 2010"; data before May 2017 from the legacy FIX/FAST
  protocol.
- Timestamps: source resolution "Timestamps prior to 2015-11-20 are limited to
  millisecond resolution"; "Data prior to 2017-05-21 … does not have capture
  timestamps" (no `ts_recv`; `ts_event` still present). Relevant to event
  studies (HC4) in 2010–2017 windows: expect ms, not ns, precision.

**CRITICAL CAVEAT (verified, verbatim)**: the catalog states "Historical data
availability **could vary between schemas**." Therefore *dataset start
2010-06-06 does NOT prove any specific schema × symbol covers from that date.*
A vendor blog (secondary evidence, https://databento.com/blog/historical-cme-event-contract-data,
access 2026-10-02) confirms product-specific start dates can be much later
(CME event contracts begin 2025-09-25 in GLBX.MDP3). Per-symbol × per-schema
start dates MUST be measured with the free metadata endpoints (§7 Phase 0)
before any purchase. Nothing below assumes 2010 depth per symbol.

**Re-verification note (m4 fix 2026-10-02, audit m4)**: the Databento catalog
page is JS-rendered and could not be re-fetched by an automated reader in the
A7 audit session, so the §2 facts above (2010-06-06, schema list, tier prices)
rest solely on this lane's access-date-stamped fetches — internally consistent
and plausible, but NOT independently re-rendered. Phase 0 step 1–3
(`list_datasets` / `list_schemas` / `get_dataset_range` / `list_unit_prices`,
all free) re-confirms every one of them against the API before any spend;
this is already mandatory and unchanged.

## 3. Schema plan mapped to hypothesis classes

Framework basis: `owner_framework/00_MASTER_FRAMEWORK.md` §5 (event studies),
§6 (tests), §7 (PIT), §8 (futures data rules) + each per-symbol file §10 Data
checklist (`ohlcv-1m`, `definition`, `statistics` phase-1; `bbo-1m`/`bbo-1s`
and `mbp-1` selective later). Hypothesis classes HC1–HC4 are defined in
`data/COVERAGE_MANIFEST.json`.

| Databento schema | Class tier | Justified by | Notes |
|---|---|---|---|
| `definition` (L0) | Phase 1 | HC1, HC3: PIT instrument universe, listing (`activation`), expiration, tick size (`min_price_increment`), contract size (`unit_of_measure_qty`), add/modify/delete actions. FACT(sourced): fields verified at https://databento.com/docs/schemas-and-data-formats/instrument-definitions (access 2026-10-02). Directly satisfies 00_MASTER §8 minimum fields | Replaces our CLASS_PARTIAL_DEFINITIONS gap; tiny volume |
| `statistics` (L0) | Phase 1 | HC1, HC2, HC3: official venue statistics. FACT(sourced): stat_type 3 = settlement (final/preliminary flags), 9 = **open interest**, 6 = cleared volume, 1/4/5 = official open/high/low, 11 = close, 13 = VWAP — verified at https://databento.com/docs/schemas-and-data-formats/statistics (access 2026-10-02) | Fills OI + settlement + official OHLCV reconciliation gaps in one schema |
| `ohlcv-1d` (L0) | Phase 1 | HC1, HC3: cheap per-contract daily panel incl. adjacent contracts for roll cost | Cross-check vs statistics before use |
| `ohlcv-1m` (L0) | Phase 1 (largest item) | HC2, HC4: framework §10 phase-1 ask; session stats, delayed-entry tests, event-window returns at 1m/5m/15m/1h | Multi-year × 10 roots is the dominant cost; verify per-symbol start (§2 caveat) |
| `ohlcv-1h` (L0) | Optional | Coarse intraday cross-check | Cheap; only if marginal |
| `bbo-1m` (L1) | Phase 2, SELECTIVE windows only | HC2: executable spread (synchronous), spread response in event windows. Our IBKR daily BID/ASK is non-synchronous 1y and NOT executable | Deeper L1 history = usage-based fees (§6) |
| `mbp-1` (L1) | Phase 2, SELECTIVE | Execution/microstructure validation (framework §10 "selective later"), per framework explicitly NOT bulk | Same L1 cost note |
| `trades` (L1) | Phase 2, SELECTIVE | Tick-level event studies, fill realism where ohlcv-1m granularity is insufficient | Same L1 cost note |
| `mbo`, `mbp-10` (L3/L2) | NOT REQUESTED | No hypothesis class in the framework currently justifies full-book depth; revisit only if microstructure hypotheses survive | Cost-dominant otherwise |

Licensing/tier FACT(sourced) (catalog page, access 2026-10-02): historical
data requires **no license**; live data requires a CME license (Databento can
be vendor of record) — live is OUT OF SCOPE for this program. Usage-based
pay-as-you-go exists for historical. "$125 in free credits" for new users
(dataset landing page, access 2026-10-02) — relevant to funding the pilot
(owner decision).

**Price-chain licensing caveats** (read before any tier choice):
1. Standard ($199/mo) includes 16+ years of **L0 only** (OHLCV/Definitions/
   Statistics/Status); L1 (Trades/MBP-1/TBBO/BBO) history is only 1 year on
   Standard, L2/L3 one month. FACT(sourced): catalog pricing tables, access
   2026-10-02.
2. Deep L1 history therefore means usage-based per-GB fees, or Plus
   ($1,750/mo license fees, annual contract) / Unlimited ($4,500/mo). These
   are license-fee tiers aimed at firms; annual contracts; owner decision
   required, and PREP does not recommend one — it prices the options (§7).
3. Redistribution/external distribution requires the Plus tier; internal
   research does not. We are internal-research only.
4. Any paid tier activates an account relationship (billing identity); that is
   an owner-level action, never a lane action.

## 4. Symbol and roll mapping (vendor roll ≠ our execution roll)

Root mapping is direct: venue-native `raw_symbol` roots NQ, ES, CL, NG, GC,
SI, 6E, 6J, 6B, 6A (stype_in=`raw_symbol`, e.g. `NQZ5`, `CLX6` — same CME
localSymbol convention as our IBKR corpus, which enables the §5 pilot join).

Continuous symbology FACT(sourced)
(https://databento.com/docs/standards-and-conventions/symbology, access
2026-10-02): format `[ROOT].[ROLL_RULE].[RANK]`; rules `c` = calendar
(closest expiry; rolls when the front expires, e.g. `NG.c.0` held NGV2 until
end of trading 2022-09-28 then pointed to NGX2), `n` = rank by **open interest
at previous day's close**, `v` = rank by previous day's **volume**. GLBX.MDP3
supports `parent` and `continuous` stypes. Continuous symbols are NOT
selectable in the web portal (API only). `symbology.resolve` is free and
returns exact mapping intervals (`d0`/`d1`/`s`).

Mandatory rules for us (framework 00_MASTER §8: "store raw individual
contracts and build continuous series yourself"):

1. **Never buy or use a vendor continuous series as the backtest price
   series.** Request per-contract data (raw_symbol/parent), keep our own roll
   tables (old/new contract, decision ts, reason, old/new volume+OI, raw gap,
   adjustment factor).
2. The declared execution roll (FUTURES-DATA-10SYMS-V1; PIT-legal): hold
   until the last session **before day-1 of the expiry month**, roll to the
   next listed contract at that close. This is NOT any of `c`/`n`/`v`: `c`
   holds the front until its last trading day (up to ~3 business days before
   month-end on NYMEX), `n`/`v` typically roll weeks earlier. Differences are
   measurement objects (HC3), not conventions to adopt.
3. Use free `symbology.resolve` on `{ROOT}.c.0`, `{ROOT}.n.0`, `{ROOT}.v.0`
   for all 10 roots to tabulate vendor roll dates vs our rule BEFORE purchase
   (Phase 0). Roll-date divergence tables feed the alternative-roll test
   (00_MASTER §6.11).
4. Verify symbol identity via `definition` schema per instrument: SI must
   resolve to the 5000oz trading class (not SIL 1000oz) and 6J quote
   convention is venue-native USD/JPY (~0.00633, multiplier 12.5M JPY,
   minTick 5e-7) — identities already established in
   FUTURES-DATA-10SYMS-V1 S1; re-verify against vendor definitions during the
   pilot (§5).

NYMEX month-code caveat (from FUTURES-DATA-10SYMS-V1 S9 C3; **corrected
2026-10-02, audit M4 — an earlier revision of this paragraph inverted the
convention and must not be acted on**): the raw `expiry_month` field in our
IBKR headers is `lastTradeDate`; for CL/NG the **delivery month is the
letter-code month itself** (CLX6 = X = Nov → Nov-2026 delivery, last trade
2026-10-20 ≈ 3 business days before Oct-25, the month prior to delivery;
NGX26 → Nov-2026 delivery, last trade 2026-10-28 = 3rd-last business day of
Oct). Our roll rule's canonical basis is the LAST-TRADE month (audit M2),
not the delivery month; the pilot must join Databento `definition.expiration`
to IBKR lastTradeDate (both are last-trade dates) and keep delivery-month
logic (letter-code month) on our side.

## 5. IBKR-overlap validation pilot (before any bulk purchase)

Purpose: prove vendor data reconciles with the IBKR corpus we already trust
(identity, prices, volumes, session handling, settlement, roll conventions)
on a small, cheap footprint. Symbols: **NQ + CL** (one quarterly-cycle equity
index, one monthly-cycle energy — the two hardest roll regimes). Uses only
L0 schemas + `definition` + `statistics` + `bbo-1m` on narrow windows.

Windows (all chosen where our measured IBKR coverage exists —
`data/coverage_measured.json`):

- **Roll-critical daily windows** (daily 6Y IBKR coverage exists for every
  contract):
  - NQ quarterly roll weeks: 2025-08-25→09-19 (U5→Z5), 2025-11-17→12-19
    (Z5→H6), 2026-02-23→03-20 (H6→M6), 2026-05-25→06-19 (M6→U6).
  - CL monthly roll weeks: 2025-09-22→10-03, 2025-12-22→2026-01-02,
    2026-03-24→04-03, 2026-06-24→07-03 (each spans the adjacent-contract
    liquidity handover; note NYMEX delivery-month convention above).
  - Request all expiries of the root in-window (stype_in=`parent`) + the
    free `symbology.resolve` roll tables for `NQ/CL.c.0/.n.0/.v.0`.
- **Full-session M1 windows** (IBKR M1 exists exactly here):
  - NQ: 2025-08-28→29 (NQU5), 2025-11-26→28 (NQZ5), 2026-02-26→27 (NQH6),
    2026-05-28→29 (NQM6), 2026-08-28→31 (NQU6), 2026-09-30→10-01
    (NQZ6/NQH7).
  - CL: 2025-08-28→29 (CLV5), 2025-09-29→30 (CLX5), 2025-10-30→31 (CLZ5),
    2025-11-26→28 (CLF6), 2026-02-26→27 (CLJ6), 2026-05-28→29 (CLN6),
    2026-07-30→31 (CLU6), 2026-09-30→10-01 (front strip).
  - Compare on the RTH subset 08:30–16:00 CT (IBKR files are `useRTH=true`);
    Databento covers the full Globex session — session-boundary handling is
    itself a validation target.

Acceptance checks (proposed thresholds; PREP proposes, owner/pilot adjudicates):

| Check | Metric | Proposed pass |
|---|---|---|
| Identity | `definition` expiry/settlement mapping vs IBKR `lastTradeDate`, per contract | 100% match; SI/6J-style identity traps re-verified |
| Daily OHLCV | close diff in ticks; OHLC containment | median ≤ 0.5 tick; ≥ 99% days within 1 tick |
| Daily volume | IBKR vs vendor per contract-day | median ratio in [0.9, 1.1]; outliers investigated, not dropped |
| M1 alignment | bar timestamps on minute grid; close diff | ≥ 99% aligned; median ≤ 0.5 tick |
| Settlement | `statistics` stat_type 3 (final) vs IBKR close-only bar close | ≥ 99% within 1 tick |
| OI sanity | `statistics` stat_type 9 vs CFTC/CME published totals spot-check | consistent on sampled dates |
| Roll conventions | `symbology.resolve` c/n/v intervals vs our declared rule | divergence table produced; no silent adoption |

Failure handling: any systematic mismatch (session stitching, volume
consolidation, price scaling 1e-9) is documented and resolved BEFORE bulk
purchase; unresolved identity mismatches (e.g. SI trading class) block that
symbol's bulk request.

Estimated footprint: tens of windows × 2 roots × L0 schemas + narrow `bbo-1m`
— POSTULATED small (likely within the $125 new-user credit; must be confirmed
with `get_billable_size`, §7). No number here is a cost claim.

## 6. Disk / bytes / get_cost estimation methodology

We do NOT fabricate per-GB prices: the unit-price example visible in public
docs is for OPRA.PILLAR, not GLBX.MDP3. The method (all FACT(sourced) from
https://databento.com/docs/api-reference-historical/basics/metered-pricing,
access 2026-10-02):

1. `Historical.metadata.list_unit_prices(dataset="GLBX.MDP3")` → USD per
   gigabyte per schema per mode (historical).
2. `Historical.metadata.get_billable_size(dataset, start, end, symbols,
   schema, stype_in)` → billable **uncompressed** bytes for the exact request
   (free; no data returned; "The amount billed will be based on the actual
   amount of bytes sent"; 10-minute-window granularity caveat; `definition`
   accurate only for discrete multiples of 24h).
3. `Historical.metadata.get_record_count(...)` → record counts per the same
   request (free) — also the Phase-0 per-symbol schema-start probe (count>0
   proves availability in that window).
4. Cost = billable_GB × unit_price; disk = compressed DBN on disk (request
   `encoding=dbn`, zstd) ≈ fraction of billable bytes — measure the ratio on
   the pilot download and use it to project bulk disk.
5. Portal "Get price estimate" on the catalog page is the no-code cross-check
   of 1–3.

Rough planning shapes (POSTULATED, to be replaced by measured values, not
cost claims): definitions/statistics are low-volume L0 with low unit price;
`ohlcv-1m` scales ≈ (contracts × trading days × session minutes); monthly
roots (CL, NG) multiply contract count vs quarterly roots (NQ/ES/6*); L1
(`trades`, `mbp-1`, `bbo-*`) is the expensive tail — hence phase-2 selective
windows only.

## 7. Request plan (RUN THIS BEFORE ANY PAID DOWNLOAD — owner decision gates)

Phase 0 — free verification (requires creating a Databento account + API key;
**that account creation is itself an owner decision**; no lane may register
anything):

1. `metadata.list_datasets` / `list_schemas(GLBX.MDP3)` / `get_dataset_range`
   — confirm schema set and dataset range as of request date.
2. `list_unit_prices(GLBX.MDP3)` — capture current USD/GB per schema.
3. Per-symbol schema-start probes (resolves the §2 caveat): for each of the
   10 roots and each of {ohlcv-1m, ohlcv-1d, definition, statistics}:
   `get_record_count` on e.g. 2010-06→2010-09, 2012-01→03, 2015-01→03,
   2019-01→03, 2021-01→03. Record the earliest window with count>0 per
   symbol×schema. This is the actual coverage table; the 2010-06-06 dataset
   start is only the upper bound.
4. `symbology.resolve` for `{ROOT}.c.0/.n.0/.v.0`, 2010→present, all roots →
   vendor roll tables; diff vs our declared rule; count roll-date mismatches
   per symbol per year (feeds HC3).
5. `get_billable_size` for the exact pilot requests (§5) and for candidate
   bulk shapes (§8) → cost + disk table for the owner decision.

Gate: owner reviews the Phase-0 evidence pack (coverage table + roll tables +
cost table) and explicitly approves spend.

Phase 1 — pilot purchase (only after gate): the §5 NQ+CL windows.

Gate: pilot acceptance table green or adjudicated.

Phase 2 — bulk L0 (staged by hypothesis class priority):
`definition` + `statistics` (all 10 roots, full verified range) first —
cheapest, unlocks roll tables, OI, settlement, PIT universe. Then
`ohlcv-1d` all roots. Then `ohlcv-1m` per symbol priority order agreed with
the backtest lane (engine demand, not data preference). Phase-2 L1
(`bbo-1m`/`mbp-1`/`trades`) only on named execution/event windows that
survive signal work.

## 8. What Databento does NOT solve — NOT_SOLVED_BY_VENDOR list

All items below are PIT-external or execution-external data classes. They
remain open regardless of vendor purchase. Lawful public primary options
listed (URLs verified live or search-verified on 2026-10-02).

1. **Macro PIT vintages (HC1/HC4).** Revised-today series are not PIT.
   Option: ALFRED (St. Louis Fed) — "vintages of economic data … the data
   that were available on a specific date in history."
   https://alfred.stlouisfed.org/ (HTTP 200, access 2026-10-02).
2. **Macro release timestamps (HC4).** BLS schedule of releases (CPI,
   Employment Situation; 8:30 a.m. ET slots): https://www.bls.gov/schedule —
   automated fetch returns 403 (bot filtering), URL verified via web search
   2026-10-02; FOMC calendar: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
   (not re-fetched this session — VERIFY before use). Release timestamps are
   public; consensus is not (see 6).
3. **NG weather forecast vintages (HC4, NG).** Reconstructed analyses are not
   forecast vintages. Option: NOAA NDFD archive — NCEI page (HTTP 200, access
   2026-10-02): https://www.ncei.noaa.gov/products/weather-climate-models/national-digital-forecast-database
   (older data via NCEI AIRS requests); bulk NDFD **from 2020-04-16 to
   present** on AWS Open Data: https://registry.opendata.aws/noaa-ndfd
   [m4 fix 2026-10-02, audit m4: the 2020-04-16 start date is NOT stated on
   the registry page itself — the lane found it via search in NODD/AWS
   documentation; cite and re-verify the page carrying the date at
   collection time before relying on the bound]. Pre-2020 forecast vintages
   are effectively out of reach — treat NG weather-vintage hypotheses as
   bounded to 2020-04-16→ unless another archive is found.
4. **EIA weekly natural gas storage (HC4, NG/CL).**
   https://www.eia.gov/naturalgas/weekly/ (HTTP 200, access 2026-10-02);
   release-time discipline needed (EIA weekly NG release ~10:30 a.m. ET
   Thursdays — VERIFY on the page at collection time).
5. **CFTC CoT positioning + release timestamps (HC1/HC4).** Primary:
   https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm (HTTP
   200, access 2026-10-02): "The COT Report is generally published each
   Friday at 3:30 p.m. Eastern Time (US), using the data from the immediately
   preceding Tuesday." PIT rule: CoT is observable only after Friday 15:30
   ET, and reflects prior-Tuesday OI — never same-day positioning.
6. **Consensus/expectations archives (HC4).** No lawful free public archive of
   survey consensus with timestamps is known. Options: prospective
   self-collection from this date, or a paid archive (owner decision,
   separate from Databento). Mark NOT_AVAILABLE meanwhile.
7. **Broker slippage / real execution costs (HC2).** Only measurable from our
   own paper/live order audit trail. PUBLISHED cost schedules ≠ MEASURED user
   costs (FUTURES-DATA-10SYMS-V1 costs section). Vendor spread data
   (`bbo-1m`) characterizes market state, not our fills.
8. **Vendor roll = execution roll trap (HC3).** §4 rules 1–3.

## 9. Sources accessed (all 2026-10-02)

- https://databento.com/catalog/cme/GLBX.MDP3 (dataset, schemas, 2010-06-06,
  per-schema caveat, tiers/pricing, license rules)
- https://databento.com/datasets/GLBX.MDP3 (landing: $125 free credits)
- https://databento.com/docs/venues-and-datasets/glbx-mdp3 (June 2010 full
  coverage; FIX/FAST pre-2017-05; timestamps)
- https://databento.com/docs/standards-and-conventions/symbology (continuous
  c/n/v, resolve, portal limitation)
- https://databento.com/docs/schemas-and-data-formats/statistics (stat types
  incl. 3 settlement, 9 OI)
- https://databento.com/docs/schemas-and-data-formats/instrument-definitions
  (activation/expiration/tick/multiplier fields)
- https://databento.com/docs/api-reference-historical/basics/metered-pricing
  (list_unit_prices, get_record_count, get_billable_size)
- https://alfred.stlouisfed.org/ ; https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm ;
  https://www.ncei.noaa.gov/products/weather-climate-models/national-digital-forecast-database ;
  https://registry.opendata.aws/noaa-ndfd ; https://www.eia.gov/naturalgas/weekly/ ;
  https://www.bls.gov/schedule (search-verified; fetch 403)
- Local evidence: `research/control/FUTURES-DATA-10SYMS-V1/` (untracked
  snapshot, read-only), `data/coverage_measured.json` (this lane).
