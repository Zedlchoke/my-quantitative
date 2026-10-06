# DATABENTO_REQUEST_PACKET — GLBX.MDP3 for FUTURES-BEHAVIOR-10SYMS-PREP-20261002

Lane REQUEST-PACKET · 2026-10-02 · Status: **REQUEST SPECIFICATION ONLY.**
Machine-readable mirror: `data/request/request_manifest.json` (15 lines: 6
PILOT + 9 EXPANSION). **Nothing here is authorization to purchase, register,
subscribe, accept ToS or download.** No key exists; no call was made; every
price/quote in this packet is `NOT_RUN_NO_CALL` until the owner runs the free
metadata probes (`data/request/probe_cost.py`, `probe_record_count.py`).

Claims taxonomy: FACT(sourced)=vendor doc URL + access date; OBSERVED=our
script over legal raw; POSTULATED=mechanism reasoning; ASSUMED=labeled
planning constant, not vendor fact.

## 1. Why each line exists (requirement, not wishlist)

Every line is justified by (a) a hypothesis class HC1–HC4 defined in
`data/COVERAGE_MANIFEST.json`, (b) a named dossier hypothesis (§5 of each
`dossiers/*_DOSSIER.md`), or (c) an engineering need from
`BACKTEST_LAUNCH_DRAFT.md` (admission bars) or the measured coverage walls in
`DATA_ACQUISITION_SPEC.md` §1. The four walls driving every request:

| Wall (OBSERVED) | Consequence | Lines fixing it |
|---|---|---|
| Expired-resolution depth: true-volume front chain only 13.5–17 months | DAILY_BT admission (≥24 months) BLOCKED 10/10 | EXP-03 (+EXP-01/02) |
| Settlement-only deep bars 65–88% | deep dailies are marks, never fills | EXP-02 official settlement/OI; EXP-03 real volume |
| Intraday vintage wall: M1/H1 ~10 recent months RTH-only | HC2/HC4 multi-year event & session work BLOCKED | EXP-04/05 (+EXP-06/07 selective) |
| Missing classes: no OI, no statistics, definitions partial | PIT roll tables + CoT/OI work BLOCKED | EXP-01/02 |

**Dataset**: GLBX.MDP3 (FACT(sourced): CME Group MDP 3.0 covering
**CME, CBOT, NYMEX, COMEX** — one dataset for all 10 roots; history begins
June 2010; pre-May-2017 data from legacy FIX/FAST; docs
`/venues-and-datasets/glbx-mdp3`, access 2026-10-02). Expected venue per
root (from FUTURES-DATA-10SYMS-V1 S1 identity; re-verified per instrument
from vendor `definition` records at pilot): NQ/ES/6E/6J/6B/6A → CME;
CL/NG → NYMEX; GC/SI → COMEX.

**Per-schema availability caveat (vendor's own wording)**: "Historical data
availability could vary between schemas." The 2010-06-06 dataset start is
only an UPPER BOUND. Per-symbol × per-schema starts are measured free at
Phase 0 (P0-3) before any spend; nothing below assumes 2010 depth per symbol.

## 2. Symbology, roll and conventions (the anti-trap rules)

1. **Outright parents only for bulk** (`stype_in=parent`): all listed
   expiries of a root, per 00_MASTER §8 "store raw individual contracts".
   Named windows use `stype_in=raw_symbol` (venue-native, same convention as
   our IBKR localSymbols, e.g. `NQZ5`, `CLX6` — FACT(sourced): raw symbols
   are "the original string symbols used by the publisher", examples
   "AAPL, ESH3"; docs `/standards-and-conventions/symbology`, 2026-10-02).
2. **Continuous NEVER bought as a price series.** `{ROOT}.c.0/.n.0/.v.0`
   used only via the FREE `symbology.resolve` endpoint
   (FACT(sourced), same page): as vendor-roll measurement objects for the
   HC3 alternative-roll test, and — only if ever needed as a signal feature —
   under the DECLARED convention: rank 0, rule `n` (open interest at previous
   day's close), unadjusted, feature-only, never fills/MTM. Roll rules
   verified today: `c` = calendar/nearest expiry held to end of trading
   (NG.c.0 held NGV2 through 2022-09-28), `n` = OI rank at previous day's
   close (CL.n.1 = second-highest OI), `v` = volume rank.
3. **Our roll is ours**: declared baseline (last session before day-1 of the
   expiry month, canonical basis = last-trade month, audit M2) built from
   per-contract data + `definition.expiration`. Vendor c/n/v divergence
   tables are measurement objects (HC3), never silently adopted.
4. **Liquid month-code cycles** (cited per dossier §1/§5, all OBSERVED on
   IBKR corpus): NQ/ES **HMUZ**; CL/NG **all 12 months monthly**; GC
   **GJMQVZ** (~6/yr, serials thin/missing); SI **H/K/N/U/Z** (~5.4/yr,
   serials measured dead ≤944 lots vs 26k–178k); 6E/6J/6B/6A **HMUZ only
   liquid** (serial fronts ≤0.3%–2-3-OOM thinner).

## 3. Timezone / session / semantics notes (ingestion-critical)

- DBN timestamps: ns since epoch UTC; `ts_event` = engine event time.
  Pre-2015-11-20 → millisecond resolution; pre-2017-05-21 → no `ts_recv`
  (HC4 windows 2010–2017 affected). FACT(sourced), docs glbx-mdp3 page,
  2026-10-02.
- **OHLCV bars are stamped at the INCLUSIVE START of the aggregation
  period** (docs ohlcv page, 2026-10-02). IBKR bars must be re-based before
  any overlap comparison.
- **ohlcv-1d is UTC-day based, NOT exchange-session-day** (same page). Our
  session dailies are self-aggregated from ohlcv-1m, or taken from
  `statistics` official OHLC (venue-session). ohlcv-1d lines are requested
  for the UTC-day reference panel + adjacent-contract roll gaps only.
- Full Globex session coverage (Sun open → Fri close incl. overnight) vs our
  RTH-only IBKR intraday: overlap validation compares the RTH subset;
  session-boundary handling is itself a validation target (spec §5).
- Statistics publish timing (docs glbx-mdp3, 2026-10-02): cleared volume and
  OI normally publish on the FOLLOWING UTC date (Friday's on Sunday);
  settlement publishes preliminary then final ("the final message … is the
  one you should use"). PIT consequence: OI(t) observable at t+1 — matches
  our PIT roll cutoff (data strictly earlier than the decision session).

## 4. Request lines (summary table; full detail in request_manifest.json)

| Line | Phase | Roots | stype_in | Schemas | Date spec | Serves |
|---|---|---|---|---|---|---|
| PILOT-01 | PILOT | NQ,CL | parent | definition | 2024-12-01→2026-10-01 | identity/expiration join vs IBKR lastTradeDate |
| PILOT-02 | PILOT | NQ,CL | parent | statistics | 2025-08-01→2026-10-01 | settlement/OI/cleared-volume reconciliation |
| PILOT-03 | PILOT | NQ,CL | parent | ohlcv-1d | 4 NQ + 4 CL roll windows (enumerated: NQ 2025-08-25→09-19, 2025-11-17→12-19, 2026-02-23→03-20, 2026-05-25→06-19; CL 2025-09-22→10-03, 2025-12-22→2026-01-02, 2026-03-24→04-03, 2026-06-24→07-03) | roll cost = adjacent close gap; volume handover |
| PILOT-04 | PILOT | NQ,CL | raw_symbol | ohlcv-1m | 14 enumerated M1 windows (NQU5 2025-08-28→29; NQZ5 2025-11-26→28; NQH6 2026-02-26→27; NQM6 2026-05-28→29; NQU6 2026-08-28→31; NQZ6/NQH7 2026-09-30→10-01; CLV5, CLX5, CLZ5, CLF6, CLJ6, CLN6, CLU6, CL front strip per spec §5) | bar alignment, session-boundary handling |
| PILOT-05 | PILOT | NQ,CL | raw_symbol | bbo-1m | same windows as PILOT-04 | first synchronous executable-spread check |
| PILOT-06 | PILOT | NQ,CL | continuous | symbology.resolve ONLY (FREE) | 2010→2026 | vendor roll tables vs our rule |
| EXP-01 | EXP | all 10 | parent | definition | ≤2010-06-06→2026-10-01, trimmed to P0-3 verified starts | PIT universe; roll-rule calendar; SI/6J identity |
| EXP-02 | EXP | all 10 | parent | statistics | same verified-range discipline | OI(9)/settlement(3)/cleared volume(6) — fills the two ABSENT classes |
| EXP-03 | EXP | all 10 | parent | ohlcv-1d | same | multi-year real-volume per-contract daily depth (HC1 floor ≥5y; SI-H2 ≥10y) |
| EXP-04 | EXP | NQ,ES,CL,NG | parent | ohlcv-1m | 2019-01-01→2026-10-01 | HC2/HC4: ES-H3 (M1 ≥2019, ≥40 events), NG-H1 (≥100 EIA events), NQ-H4 full-session ≥2y, CL-H2 |
| EXP-05 | EXP | GC,SI,6E,6J,6B,6A | parent | ohlcv-1m | 2021-01-01→2026-10-01 | HC2: SI-H5 overnight tails ≥2y; FX hidden-session (RBA/BoJ/BoE) events |
| EXP-06 | EXP (phase-2 gated) | NQ,ES,CL,NG,6E,6B,6J,6A | raw_symbol | bbo-1m | named event windows only: {FOMC 14:00 ET, CPI/NFP 08:30 ET, EIA 10:30 ET} × [T−30min, T+2h] | HC4 spread response |
| EXP-07 | EXP (phase-2 gated) | all 10 | raw_symbol | trades | roll weeks (declared-roll ±5 sessions; old+new pair) + shared event windows | GC-H1/6B-H1 crossover timing, CL-H5 spread-at-switch |
| EXP-08 | RESERVED | NQ,ES,CL | raw_symbol | tbbo | TBD by future registered cycle | fill-realism only if HC2 survives; NOT REQUESTED now |
| EXP-09 | EXP | all 10 | continuous | symbology.resolve ONLY (FREE) | 2010→2026 | HC3 alternative-roll inputs, all roots |

**Not requested (with reasons)**: mbo / mbp-10 (no hypothesis class needs
full book); mbp-1 (reserved; bbo-1m/tbbo cover shallower needs first);
ohlcv-1s/1h bulk (1s unjustified cost; 1h derivable from 1m); vendor
continuous OHLCV of any schema (never bought, §2); status schema; live
feed/CME license (out of scope).

Hypothesis-ID mapping per line is exhaustive in `request_manifest.json`
(`hypothesis_ids`), drawn verbatim from dossier §5 IDs.

## 5. Estimates: records / storage / compute — METHOD SHOWN, constants labeled

- **Records**: docs publish NO per-symbol records/day (NOT_FOUND_IN_DOCS,
  2026-10-02). OHLCV emission is **sparse by design** (docs ohlcv page:
  "If no trade occurs within the interval, no record is printed" — confirmed
  same-day via the DBN-ADAPTER lane's verification), so records/contract-day
  < session minutes and only measurement counts: `get_record_count` (free)
  at Phase 0. Planning bounds only: ohlcv-1m ≤ 1380 bars/contract-day (23h
  Globex weekday session; **ASSUMED** upper bound); definition ~1–10
  records/contract-lifecycle (**ASSUMED**); statistics ~5–20
  records/instrument/day (**ASSUMED**); ohlcv-1d ≤ active contracts/day
  (NQ/ES ~10, CL/NG ~30, GC/SI ~20–24, 6* ~24 listed per dossier chains;
  vendor listing breadth **ASSUMED** equal until definitions arrive).
- **Storage**: billable bytes MEASURED via `get_billable_size` (free;
  uncompressed; vendor caveat on non-10-minute windows). Byte-exact record
  sizes are FACT(sourced) via this cycle's DBN-ADAPTER lane
  (`code/futbt/dbn/spec.py`, layouts from the official
  github.com/databento/dbn reference implementation, main@2026-10-02):
  **OhlcvMsg 56 B · TradeMsg 48 B · Mbp1Msg/TbboMsg 80 B · StatMsg 80 B ·
  InstrumentDefMsg 520 B · BboMsg 80 B** (16-byte RecordHeader included).
  zstd-compressed on-disk ≈ 0.4–0.6 × billable (**ASSUMED** ratio; vendor
  claims "high compression ratios" without numbers — measure at pilot,
  re-project). Worked formula (NQ ohlcv-1m, 1y, front+1 contracts, UPPER
  BOUND): 252 days × 1380 bars × 2 contracts × 56 B ≈ 39 GB uncompressed
  bound — the real number comes from P0-5.
- **Compute**: L0 lines POSTULATED trivial (single-pass parse+QA); ohlcv-1m
  multi-year × 10 roots is the only non-trivial job (minutes-scale per GB,
  single core, **ASSUMED**) — re-estimated from the pilot's measured GB/s.
- **Prices**: none quoted. `NOT_RUN_NO_CALL` everywhere. Method:
  cost = billable_GB (`get_billable_size`) × unit price
  (`list_unit_prices`: "US dollars per gigabyte" per schema per mode;
  "Every dataset or data feed is priced in $/GB. Every month, you pay only
  for the data that you've used." FACT(sourced) 2026-10-02). $125 new-user
  credit exists (FACT(sourced)) — noted for the owner's pilot funding
  decision; no assertion that the pilot fits within it (P0-5 decides).

## 6. Disk cap, checkpoint/resume, double-billing hazards

- **Disk cap**: 200 GB internal engineering cap (**INTERNAL_ASSUMPTION**,
  not a vendor number) for raw DBN + zstd on this workstation. Hard stop +
  owner consult if P0-5 projections exceed it.
- **Batch boundaries**: every billable line chunks into requests keyed
  `(line_id, root, schema, calendar quarter)` for full-range lines or
  `(line_id, root, schema, named window)` for pilot/event windows. Chunk =
  unit of request, delivery, QA, resume.
- **Resume/idempotency**: completion ledger
  `data/request/completion_ledger.json` (created at delivery time) records
  per chunk: exact request params, batch job id, reported billable size,
  file list + checksums; states SUBMITTED (written BEFORE assuming
  delivery) → DELIVERED (checksummed). Resume: DELIVERED chunks never
  re-requested; SUBMITTED-unverified chunks resolved by listing the batch
  job's files (enumerate, don't blind re-submit).
- **Double-billing hazards**: (1) re-submitting delivered-but-unledgered
  chunks — mitigated by SUBMITTED-first writes + file enumeration; (2)
  overlapping windows (event/roll window inside an already-delivered
  quarter) — mitigated by the one-owner rule: each (root, schema, quarter)
  belongs to exactly one line; nested windows are carved from local data,
  never re-bought; (3) estimate drift from the 10-minute granularity caveat
  — per-chunk `get_billable_size` re-check immediately before each phase
  spend gate.
- **Concurrency**: vendor historical limits 100 concurrent connections /
  100 time-series req/s / 100 symbology req/s per IP (FACT(sourced) 2026-10-02);
  probes stay single-flight; bulk via batch/FTP.

## 7. Phase plan and gates

- **Phase 0 — free verification** (owner, with key from env var
  `DATABENTO_API_KEY`): P0-1 dataset/schemas/range; P0-2 unit prices;
  P0-3 per-symbol × schema coverage probes on windows
  2010-06→09, 2012-01→03, 2015-01→03, 2019-01→03, 2021-01→03; P0-4 free
  roll tables all roots; P0-5 billable size for PILOT + candidate EXPANSION
  chunks. **GATE: owner reviews evidence pack, explicitly approves spend.**
- **Phase PILOT** (NQ+CL, lines PILOT-01..06): IBKR-overlap validation per
  DATA_ACQUISITION_SPEC.md §5 thresholds. **GATE: acceptance table green or
  adjudicated** (see DATA_ACCEPTANCE_CHECKLIST.md) before ANY EXPANSION buy.
- **Phase EXPANSION**: order EXP-01 → EXP-02 → EXP-03 → EXP-04 → EXP-05 →
  (gated) EXP-06/07/08. Each line: per-line cost table vs this manifest →
  owner approval → chunked delivery → acceptance → freeze. ohlcv-1m starts
  trimmed to P0-3-verified coverage; phase-2 L1 lines bought only on
  surviving named windows.

## 8. Sources (all accessed 2026-10-02)

Docs pages are JS-rendered; vendor facts were extracted through Databento's
own docs search API over the current published build
(`api.databento.com/v0/docs/search`, build 01M3QSBT40W79JPVNV0CHMKD5E) plus
the partially-rendered dataset landing page — every URL below is the
official doc location:

- https://databento.com/docs/venues-and-datasets/glbx-mdp3 — venues,
  June 2010 start, FIX/FAST pre-2017, timestamp caveats, statistics publish
  timing
- https://databento.com/docs/schemas-and-data-formats/ohlcv — schema names,
  bar-START ts semantics, ohlcv-1d UTC-day basis
- https://databento.com/docs/standards-and-conventions/symbology —
  raw_symbol/parent/continuous, c/n/v rules, resolve FREE
- https://databento.com/docs/schemas-and-data-formats/statistics — stat
  fields, cleared volume=6, prelim/final settlement (settlement=3, OI=9 per
  DATA_ACQUISITION_SPEC.md §3 same-page access 2026-10-02)
- https://databento.com/docs/schemas-and-data-formats/instrument-definitions
  — definition fields (activation/expiration/tick/multiplier; per spec §3)
- https://databento.com/docs/api-reference-historical/metadata/list-unit-prices
  · /get-billable-size · /get-record-count — the three free metadata methods
- https://databento.com/docs/pricing/usage-based-pricing-and-data-credits —
  $/GB metered model, $125 credits
- https://databento.com/docs/api-reference-historical/basics/authentication —
  key handling, `DATABENTO_API_KEY` env var
- https://databento.com/docs/api-reference-historical/basics/rate-limits —
  100 conn / 100 req/s limits
- https://databento.com/docs/api-reference-historical/batch — batch/FTP bulk
- https://databento.com/docs/schemas-and-data-formats/databento-binary-encoding
  — 16-byte RecordHeader; https://databento.com/docs — 56-byte typical
  message, zstd
- https://databento.com/datasets/GLBX.MDP3 — landing page ($125 credits)
- https://databento.com/catalog/cme/GLBX.MDP3 — catalog (JS-rendered; facts
  carried by DATA_ACQUISITION_SPEC.md §2 same-day access): 2010-06-06,
  per-schema caveat, tier prices

Local evidence: `data/COVERAGE_MANIFEST.json`, `DATA_ACQUISITION_SPEC.md`,
`BACKTEST_LAUNCH_DRAFT.md`, `INTEGRATION_SUMMARY.md`, `dossiers/*_DOSSIER.md`,
`SERIAL_REFETCH_MANIFEST.md` (HANDOFF-RESEARCH lane, same round), and
`code/futbt/dbn/spec.py` (DBN-ADAPTER lane; DBN record layouts from the
official github.com/databento/dbn repo, main@2026-10-02 — the source of the
byte-exact sizes in §5) — all this cycle, 2026-10-02.
