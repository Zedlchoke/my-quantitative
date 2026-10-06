# futbt.dbn — Databento DBN v3 ingestion adapter (PREP, synthetic-only)

Lane DBN-ADAPTER-RESUME, task FUTURES-BEHAVIOR-10SYMS-PREP-20261002,
round steering-waiting-databento. Resumed after the predecessor lane
(DBN-ADAPTER) died on a usage limit after writing the ten modules but
before running them once, writing tests, or this README.

Everything here is OFFLINE and SYNTHETIC: all bytes consumed in tests come
from `fixtures.build_fixture_dir` (deterministic, fabricated, labeled
`synthetic: true` in the manifest). No API keys, no network, no downloads,
no billable calls. Nothing in this package has ever touched real Databento
data — that is the registered cycle's job.

Run the tests:

```bash
cd research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/code
/Users/hoangminhlong/my-quantitative/.venv/bin/python \
  -m unittest tests.test_dbn_wire tests.test_dbn_ingest tests.test_dbn_session \
  tests.test_dbn_ohlcv tests.test_dbn_bbo tests.test_dbn_qa
# 144 tests, ~2 s, stdlib only
```

## Module map

| module | role |
|---|---|
| `spec.py` | DBN v3 record layouts (byte-exact), rtype/schema/stype enums, sentinels, price fixed-point, pack/unpack, fail-closed unknown-rtype errors |
| `wire.py` | DBN file framing: metadata prelude/body encode+decode, symbol mappings, record stream decode; version gate (v3 only) |
| `textio.py` | CSV/JSONL export shapes (pretty rules + column order per the reference serializer); name-driven readers, typed column errors |
| `fixtures.py` | deterministic synthetic GLBX.MDP3-shaped files + ground-truth manifest (DST days, holiday short session, roll window with volume/OI migration, negative CL day, crossed/locked BBO, duplicate/gap bars, 6J scale, stale + absent-session bars, definition A/M/D, continuous file) |
| `ingest.py` | file -> typed frames (DBN/CSV/JSONL); contract identity resolution; continuous execution guard |
| `session.py` | exchange-tz session calendar (zoneinfo, DST-correct), short-session inference, absence-aware NO_DATA, mixed-cadence refusal |
| `ohlcv.py` | trade classification, 1m->session aggregation with explicit boundaries, settlement separation + revisions, negative-price preservation |
| `bbo.py` | book-time joins with simultaneity taxonomy, crossed/locked detection, executable-quote law, bar-side spread proxies |
| `pit.py` | as-of statistics/identity, settlement vintages, time-travel guard, feature-only roll adjustment |
| `qa.py` | SHA256 manifest, duplicate/gap/monotonic checks (per file, as-received order), coverage report, roll-window volume/OI crossover summary, unknown-stat census |

## IMPLEMENTED / TESTED / NOT_IMPLEMENTED

| capability | status | evidence |
|---|---|---|
| DBN v3 binary decode: prelude, metadata (dataset/schema/start/end/limit/stypes/ts_out/symbols/partial/not_found/mappings), length-prefixed records | IMPLEMENTED + TESTED | `test_dbn_wire.py::TestDbnFileStream`, `TestMetadataCodec` |
| Record layouts OhlcvMsg/TradeMsg/Mbp1Msg(=TbboMsg)/StatMsg/InstrumentDefMsg/SymbolMappingMsg/SystemMsg/BboMsg incl. reserved/skip fields | IMPLEMENTED + TESTED (sizes 56/48/80/80/520/176/320/80) | `TestRecordLayouts`, `TestPackUnpack` |
| Fail-closed on unknown/unsupported record types (typed `UnknownRecordTypeError`, never skip) | IMPLEMENTED + TESTED | `test_dbn_wire::test_unknown_record_type_fails_closed_typed`, `test_dbn_qa::TestFailClosedSchema` |
| DBN version gate (reject v1/v2/>3, bad magic, truncation, non-4-byte-aligned sizes) | IMPLEMENTED + TESTED | `test_bad_magic_rejected`, `test_newer_version_rejected_fail_closed`, `test_truncated_record_rejected` |
| .zst compression | NOT_IMPLEMENTED (typed refusal; Python 3.12 stdlib has no zstd) | `test_dbn_ingest::test_zst_refused_typed` |
| DBN v1/v2 compat decode | NOT_IMPLEMENTED (v3 only, refuses) | `wire.decode_metadata_from_blob` |
| Schema definitions in metadata (schema_definition_length != 0) | NOT_IMPLEMENTED (typed refusal) | `wire.py` |
| CSV export/parse (pretty prices 9-decimals, empty-field sentinels, reference column order incl. header-slot flattening) | IMPLEMENTED + TESTED | `TestCsvJsonShapes`, `test_dbn_ingest::TestIngestParity` |
| JSONL export/parse | IMPLEMENTED + TESTED (ohlcv-1d fixture) | `TestIngestParity`, `TestCsvJsonShapes` |
| stype semantics (raw_symbol/instrument_id/parent/continuous; continuous = ROOT.c.N) | IMPLEMENTED + TESTED (metadata carries stypes; continuous file + mappings) | `test_continuous_file_carries_mappings`, symbology docs |
| Contract identity resolution: raw_symbol -> instrument_id/expiry/activation/tick/multiplier from definition A/M/D actions, ts-ordered, clash/delete/unresolved typed errors | IMPLEMENTED + TESTED | `test_dbn_ingest::TestContractIdentity` |
| first_notice from definitions | NOT_AVAILABLE (field does not exist in InstrumentDefMsg) — asking raises, never fabricates | `test_first_notice_not_available_typed` |
| NO-CONTFUT-fill law (vendor continuous = EXECUTION_FORBIDDEN, signal-feature only) | IMPLEMENTED + TESTED | `TestContinuousGuard` |
| Continuous/outright proof from text exports | NOT_IMPLEMENTED (CSV/JSONL carry no stype metadata; `execution_use() == "unproven_stype"`, typed) | `test_text_exports_have_unproven_stype` |
| Calendar DST handling (America/Chicago via zoneinfo; UTC session bounds shift 22Z->23Z across fall-back; 23h exchange-local sessions) | IMPLEMENTED + TESTED | `test_dbn_session::TestTzConversion`, `TestDstBoundaries` |
| Holiday calendar (exchange-published early closes/halts) | NOT_IMPLEMENTED — no offline holiday source; short sessions are INFERRED from bar coverage (`HOLIDAY_SHORT` + `inferred_short` flag, never asserted as exchange fact) | `test_declared_early_close_detected_as_holiday_short` |
| Short-session / absence handling (NO_DATA weekdays, close-only-by-absence) | IMPLEMENTED + TESTED | `TestHolidayShortSession`, `TestNoDataAndReconstruction`, `test_dbn_qa::TestCoverageReport` |
| Mixed daily+intraday cadence session reconstruction | IMPLEMENTED refusal (fail-closed) + TESTED; QA coverage partitions by cadence and merges | `test_mixed_cadence_refused` |
| 16:00-17:00 CT maintenance-break bars rejected (never silently binned) | IMPLEMENTED + TESTED | `test_maintenance_break_bar_rejected` |
| BID/ASK synchronization: book-time as-of join, EXACT/BOOK_TIME/STALE/NO_QUOTE taxonomy, 1s default staleness | IMPLEMENTED + TESTED | `test_dbn_bbo::TestBookTimeJoin` |
| Crossed/locked detection + never-executable law (incl. UNDEF_PRICE sentinel) | IMPLEMENTED + TESTED | `TestClassifyBbo`, `TestCrossedBook` |
| TBBO pre-trade BBO semantics (join never uses post-trade quotes) | IMPLEMENTED + TESTED | `test_mbp1_bbo_is_pretrade_book` |
| Bar-side spread proxy always BAR_PROXY (non-simultaneous by construction) | IMPLEMENTED + TESTED | `TestBarSpreadProxy` |
| Trade/OHLCV classification (trades schema action=='T'; aggressor side; mbp-1 action-T only; non-T refused) | IMPLEMENTED + TESTED | `test_dbn_ohlcv::TestTradeClassification` |
| 1m -> session aggregation with explicit session boundaries | IMPLEMENTED + TESTED | `TestAggregationBoundaries`, `test_dbn_ohlcv::TestOhlcvConventions` |
| ohlcv-1d = UTC-day bars, ts_event = interval START, sparse (no trade -> no bar) | IMPLEMENTED + TESTED | `test_ohlcv_1d_ts_event_is_utc_midnight_interval_start`, `test_ohlcv_1m_sparsity_no_bar_without_trade` |
| Negative prices preserved exactly (int nanos end-to-end, incl. negative settlement; ratio adjustment refuses non-positive) | IMPLEMENTED + TESTED | `TestNegativePrices`, `test_dbn_qa::test_ratio_refused_on_non_positive` |
| Stale close-only bars (o=h=l=c=prev close) flagged; close-only-by-absence sessions (settlement without bars) counted | IMPLEMENTED + TESTED | `TestStaleCloseOnlyBars`, `TestCoverageReport` |
| Settlement vs trade separation (stat_type=3 keyed by ts_ref UTC date; preliminary/final revisions both kept; compare uses FINAL only) | IMPLEMENTED + TESTED | `TestSettlementVsTrade` |
| Settlement stat_flags semantics (bit0 final, bit1 ACTUAL per GLBX.MDP3 spec) | IMPLEMENTED + TESTED | `test_stat_flags_glbx_semantics`, `test_preliminary_vs_final_flags` |
| PIT publication/vintage (publication-gated statistics, vintage reconstruction, cleared-volume next-morning lag, time-travel refusal, as-of identity incl. deletes) | IMPLEMENTED + TESTED | `test_dbn_qa::TestPitVintage` |
| Feature-only roll adjustment (declarer required; additive splice anchored at first contract; execution context refused) | IMPLEMENTED + TESTED | `TestFeatureOnlyRollAdjustment` |
| Roll-critical window: volume/OI migration, crossovers from venue statistics (volume 2026-11-02 precedes OI 2026-11-05, spanning fall-back), window straddles DST | IMPLEMENTED + TESTED | `test_dbn_qa::TestRollWindow` |
| QA: SHA256 manifest, duplicates, no-trade minute gaps (inference), monotonicity in AS-RECEIVED order per file | IMPLEMENTED + TESTED | `TestShaManifest`, `TestTimeSeriesChecks` |
| QA: coverage report (negative bars, stale bars, close-only sessions, session kinds) | IMPLEMENTED + TESTED | `TestCoverageReport` |
| QA: unknown stat-type census (values, not record types) | IMPLEMENTED + TESTED | `test_unknown_stat_type_flagged_in_report` |
| Live API paths (streaming, live symbol mapping), any network/billable metadata calls | NOT_IMPLEMENTED / NOT_RUN (no API key exists in this round; scripts PREPARED by REQUEST-PACKET lane are NOT_RUN until owner supplies key) | — |
| mbo (0xA0) / mbp-10 (0x0A) / status (0x12) / imbalance (0x14) / error (0x15) / cmbp-1 (0xB1) / cbbo (0xC0-0xC2) record types | NOT_IMPLEMENTED (typed fail-closed on the wire; BboMsg bbo-1s/bbo-1m ARE implemented) | `SUPPORTED_RTYPES` |
| Real Databento data validation (any claim about actual GLBX.MDP3 bytes) | NOT_RUN — first real batch goes through the acceptance checklist (../DATA_ACCEPTANCE_CHECKLIST.md) | — |
| stat_flags normalization on GLBX.MDP3 data prior to 2015-01-20 | KNOWN CAVEAT (published vendor data-quality issue) — re-verify on first real batch | issues.databento.com, access 2026-10-02 |

## Predecessor corrections (defects found and fixed this round)

The predecessor's ten modules had NEVER been executed (death by usage
limit before any run). Every defect below was found by review-against-docs
or first execution, then fixed and pinned by a test:

1. **fixtures: fatal KeyError building the universe.** `raw = f"{root}{code}{yy % 100}"`
   produced two-digit-year symbols (NQZ26/CLF27) while the entire module
   (and manifest truth) references venue-style one-digit-year symbols
   (NQZ6/CLF7) — `build_fixture_dir` crashed on the first contract lookup.
   Fixed to `yy % 10` (CME one-digit-year raw symbols).
2. **fixtures: ES listing mismatch.** The contract list had ESH7 but every
   builder referenced ESZ6 — second fatal KeyError. Fixed the listing.
3. **fixtures: OI crossover could never happen.** With
   `new_oi = 2000 + 6000*f` vs `old_oi = 15000 - 5000*f`, OI never crosses
   inside the window and `next(...)` raises StopIteration (RuntimeError).
   Slope corrected to `+10000*f` so OI crosses 2026-11-05 (volume already
   crosses 2026-11-02 — OI lags volume, as intended).
4. **fixtures: listing window did not cover the bars.** Activation formula
   (`~6 months before delivery`) placed GCZ6/CLZ6 activation in June 2026
   while their daily bars start 2026-02-20. Activation now ~12 months
   before delivery month.
5. **fixtures: fixture determinism broken by construction.** The manifest
   embedded absolute paths (`str(p.resolve())`), so byte-identical rebuilds
   were impossible to verify. Files are now recorded by basename
   (determinism test compares full sha256 of every file).
6. **fixtures: CSV/JSONL rows lacked their own header columns.** Text
   exports wrote `rtype=0, publisher_id=0, instrument_id=0` on every row —
   every text file then self-identified as rtype 0 (trades), and an
   mbp-1 CSV silently parsed as trades rows. Rows now carry
   rtype/publisher_id/instrument_id/ts_event (binary == text proven by
   test).
7. **spec: pack/unpack broken for layouts with reserved fields.**
   `pack_record` skipped `skip`-kind fields while `body_fmt` included them
   (BboMsg: struct arity error) and passed int 0 for `18s`/`17s` bytes
   fields (StatMsg/InstrumentDefMsg: type error); `unpack_record` zipped a
   filtered field list against the full tuple, silently mis-mapping every
   field after a reserved slot. Reserved fields are now zero-filled on pack
   and aligned-then-dropped on unpack (BboMsg field alignment pinned by
   test).
8. **spec: stat_flags bit 1 was INVERTED.** Comment claimed "0x02 set ->
   theoretical"; the GLBX.MDP3 spec normalizes tag 731-SettlPriceType with
   `1 << 1` = ACTUAL (vs theoretical). `STAT_FLAG_THEORETICAL` renamed to
   `STAT_FLAG_ACTUAL`; `SettlementRecord.theoretical` -> `.actual`.
9. **spec: CSV column-order model was wrong.** The reference sorts the
   field list with the RecordHeader as ONE slot at its natural position and
   flattens it afterwards (ts_event, rtype, publisher_id, instrument_id);
   the predecessor flattened first and indexed on the flattened list, so
   e.g. trades CSV put `price` before `action,side,depth` and the
   definition CSV misplaced `raw_instrument_id`/`strike_price`.
   `sorted_for_text` re-modeled after dbn-macros `get_sorted_fields` +
   the flattening `WriteField for RecordHeader` (trades/ohlcv/stat/
   definition column orders pinned by tests). `raw_instrument_id` was also
   missing its `encode_order(20)`.
10. **textio: pretty-print sentinels diverged from the reference.**
    Reference pretty CSV writes EMPTY fields for UNDEF_PRICE, UNDEF_TIMESTAMP
    and NUL chars; the predecessor wrote "UNDEF_PRICE"/"UNDEF_TIMESTAMP"
    strings and chr(0). Fixed to match (readers still accept the explicit
    sentinel strings). Reserved `_reserved` columns no longer appear in
    CSV/JSON (reference hides them).
11. **ingest: BboMsg rtype 0xC4 missing from SUPPORTED_RTYPES.** The
    predecessor wrote a bbo-1m fixture but omitted BBO_1S/BBO_1M from the
    supported set — the package's own fixture failed its own decoder.
    Added (BboMsg layout serves both).
12. **ingest: char fields typed inconsistently across paths.** CSV parse
    yields ordinals, DBN decode yields 1-char strings; definition actions
    compared against "A"/"M"/"D" crashed on CSV input (action 65
    "unknown"). Normalized via `_ch()` in dispatch.
13. **textio: cstr columns coerced to int.** `csv_columns` mapped
    non-px/ts/char kinds to "int", so `raw_symbol='CLV6'` raised
    ValueError on parse. cstr kind now passes through as text.
14. **ohlcv: settlement session dates off by one day.**
    `utc_to_exchange(ts_ref).date()` on a UTC-midnight ts_ref yields the
    PREVIOUS calendar day in Chicago; the trading date is the UTC date of
    ts_ref. Fixed and pinned.
15. **session: daily bars misclassified as holiday-short.** The coverage
    path pushed ohlcv-1d bars through minute-coverage logic; a UTC-midnight
    daily bar is 1h after session open -> coverage < 0.85 -> every daily
    session "HOLIDAY_SHORT". Session classification is now cadence-aware
    (daily = presence-only; mixed cadence refuses), and QA coverage
    partitions by cadence and merges.
16. **qa: non-monotonic check vacuous.** Computed on a SORTED copy, so it
    could never fire. Now checked in AS-RECEIVED order, per file (pooling
    multiple files interleave two valid streams and reported spurious
    reversals at file boundaries).
17. **qa: minute-gap scan applied to daily bars.** Any inter-bar delta > 1
    minute was a "missing minute"; for 1d/1h cadence that fabricates
    thousands of bogus gaps. Gap scan now restricted to rtype ohlcv-1m.
18. **qa: settlement accounting hack.** `qa_report` built anonymous
    `type("S", (), ...)` objects, caught-and-ignored unresolved ids, and
    diverged from `settlement_series`; rewritten cleanly on Statistic
    objects with a roll-window summary (volume/OI crossovers from venue
    statistics).
19. **bbo: UNDEF_PRICE classified CROSSED.** i64::MAX > any ask, so a
    sentinel bid classified as a crossed book instead of UNDEFINED. Fixed.
20. **bbo: fixture trade-join truth internally inconsistent.** A 2.4s
    quote lead was labeled BOOK_TIME while a 2.0s lead was labeled STALE —
    impossible under any threshold (never validated by a run). Timeline
    corrected; all four taxonomy classes now genuinely exercised
    (EXACT/BOOK_TIME 0.5s/STALE 2.9s+2s/NO_QUOTE).
21. **pit: docstring contradicted the splice implementation.** Claimed
    "the LATEST raw prices are untouched" while the code anchors at the
    FIRST contract (bars at/after each roll shift). Docstring fixed;
    behavior pinned by test.
22. **bbo: no-op expression.** `lead if lead > staleness_ns else lead` is
    just `lead`; simplified. Also added `ingest.Ingested.stype_proven` to
    type the CSV/JSONL stype limitation.

## Documentation sources (all accessed 2026-10-02)

docs.databento.com pages are JS-rendered and return only navigation to an
automated reader; the machine-readable authority used is the OFFICIAL
reference implementation (databento/dbn, main branch) plus docs pages
verified through search snippets:

Reference implementation (byte layouts, framing, enums, pretty rules):
- https://github.com/databento/dbn/blob/main/rust/dbn/src/record.rs
- https://github.com/databento/dbn/blob/main/rust/dbn/src/enums.rs
- https://github.com/databento/dbn/blob/main/rust/dbn/src/lib.rs
- https://github.com/databento/dbn/blob/main/rust/dbn/src/compat.rs
- https://github.com/databento/dbn/blob/main/rust/dbn/src/pretty.rs
- https://github.com/databento/dbn/blob/main/rust/dbn/src/flags.rs
- https://github.com/databento/dbn/blob/main/rust/dbn/src/decode/dbn/fsm.rs
- https://github.com/databento/dbn/blob/main/rust/dbn/src/encode/csv/serialize.rs
- https://github.com/databento/dbn/blob/main/rust/dbn-macros/src/dbn_attr.rs

Docs pages (semantics; JS-rendered, verified via search snippets 2026-10-02):
- https://databento.com/docs/schemas-and-data-formats/ohlcv — "The ts_event
  timestamp marks the start of each interval. If no trade occurs within the
  interval, no record is printed."; ohlcv-1d aggregates the UTC date;
  session-based/official daily data -> statistics schema.
- https://databento.com/docs/schemas-and-data-formats/statistics — official
  venue statistics; settlement flags final/preliminary + actual/theoretical.
- https://databento.com/docs/venues-and-datasets/glbx-mdp3 — Stat flags
  table: tag 731-SettlPriceType normalized to stat_flags; `1 << 0` final,
  `1 << 1` actual.
- https://databento.com/docs/schemas-and-data-formats/tbbo — TBBO = every
  trade with the BBO immediately BEFORE the trade's effect.
- https://databento.com/docs/standards-and-conventions/common-fields-enums-types
  — action enum; trades schema carries action 'T'; side = aggressor.
- https://databento.com/docs/standards-and-conventions/symbology — stypes
  raw_symbol/instrument_id/parent/continuous; continuous = ROOT.c|n|v.RANK.
- https://databento.com/docs/standards-and-conventions/databento-binary-encoding
  — DBN binary framing.
- https://databento.com/docs/faqs/difference-between-mbp-and-tbbo — mbp-1 vs
  tbbo vs bbo.
- https://issues.databento.com/roadmap/glbxmdp3-inconsistent-normalization-of-settlement-price-stat-flags-prior-to-2015-01-20
  — known stat_flags normalization issue (caveat recorded above).

Deliberate divergences from the reference (documented, both directions
parse): `ts_to_iso`/price formatting additionally accept the explicit
"UNDEF_PRICE"/"UNDEF_TIMESTAMP" sentinel strings on READ (the reference
only writes empty fields in pretty mode); everything else matches.
