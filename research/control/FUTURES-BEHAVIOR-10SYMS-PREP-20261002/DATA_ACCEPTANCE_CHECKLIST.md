# DATA_ACCEPTANCE_CHECKLIST — Databento GLBX.MDP3 deliveries (after owner
purchase, per data/request/request_manifest.json)

Task FUTURES-BEHAVIOR-10SYMS-PREP-20261002 · lane REQUEST-PACKET ·
2026-10-02. Audience: whoever (owner or a future registered data lane)
receives delivered Databento data produced against
`data/request/request_manifest.json`.

**Hard frame, stated up front:**

1. **Presence of delivered data is NOT itself authority to run anything
   scored.** Data arrival changes NOTHING about gates: no scored run, no
   PnL/event-study/rule sweep, no GO, no registration is triggered by
   delivery. Each further step below runs only inside its own authority
   (prep QA now; a future REGISTERED cycle for anything return-linked).
2. Everything here is QA/ingestion only — no new purchases, no re-buys
   outside the repair loop's exact-parameter re-requests, no live sessions.
3. Claims taxonomy applies to every row this checklist produces:
   FACT(sourced) / OBSERVED (script + window) / POSTULATED / NOT_RUN.
   Missing evidence is NOT_RUN, never inferred PASS.

Adapter interface names below reference the DBN-ADAPTER lane's package
`code/futbt/dbn/` (present at authoring time: `spec.py` with
`unpack_record`, `read_header`, `record_name_for_rtype`, `price_to_nanos`,
`nanos_to_price_str`, `DbnFormatError`, `UnknownRecordTypeError`,
`SPECS_BY_RTYPE`, `STAT_TYPE_*`, `FIXED_PRICE_SCALE`; more modules may land
— re-measure the checkout and use its actual QA entry points; if names have
moved, treat the FUNCTIONS described here as the contract, not the exact
identifiers).

## Step 0 — Preconditions (verify BEFORE accepting any file)

- [ ] Owner confirmed Phase-0 evidence pack (P0-1..P0-5 outputs from
      `data/request/probe_record_count.py` / `probe_cost.py` real runs) and
      the per-line spend approval for exactly the delivered lines.
- [ ] Delivery matches a manifest line id + chunk key
      (line_id, root, schema, quarter-or-window). Unsolicited chunks are
      quarantined, not ingested.
- [ ] `data/request/completion_ledger.json` exists and was written
      SUBMITTED-first; the job ids in the delivery match the ledger.

## Step 1 — Delivery integrity (per chunk)

- [ ] File list vs the batch job's `list_files` enumeration: 1:1, no
      missing, no extras.
- [ ] Checksums (sha256) recorded in the ledger for every file.
- [ ] Reported billable size vs the pre-purchase `get_billable_size` for the
      SAME exact params: reconcile; material divergence (vendor bills "the
      actual amount of bytes sent") is documented before any further chunk
      of that line is requested.
- [ ] Disk usage vs the 200 GB internal cap
      (`estimation_method`/`disk_and_checkpoint`): stop + owner consult if
      the projection from delivered sizes exceeds it.

## Step 2 — Independent ingestion QA (DBN decode; never trust the delivery
format blindly)

- [ ] DBN prelude/metadata decode: dataset == GLBX.MDP3, schema, stypes,
      version as expected; unknown rtypes must raise
      (`UnknownRecordTypeError` fail-closed) — a delivery containing
      unsupported record types is a finding, never silently skipped.
- [ ] Record decode per schema with the adapter's spec layouts
      (OhlcvMsg/StatMsg/InstrumentDefMsg/TradeMsg/Mbp1Msg/BboMsg); sizes:
      56/80/520/48/80/80 bytes; alignment and count vs file size exact.
- [ ] Price scale: all prices are int nanos at `FIXED_PRICE_SCALE` 1e-9 —
      verify `price_to_nanos`/`nanos_to_price_str` round-trips on sampled
      records; NO floats in the value path.
- [ ] Symbol resolution: instrument_id → raw_symbol via the delivery's
      SymbolMappingMsg records (stype_in of the request); every instrument
      in data chunks must resolve; unresolved ids are a blocking finding.
- [ ] Timestamp semantics: ohlcv `ts_event` = bar START (inclusive); bars
      are sparse (no trade in interval ⇒ no record) — gap checks below must
      use "expected activity" logic, not naive minute grids.
- [ ] ohlcv-1d chunks: bars are UTC-day based (vendor doc) — do NOT compare
      them 1:1 against IBKR session dailies; session dailies are built by
      our own aggregation from 1m or from statistics official values.

## Step 3 — Coverage / integrity checks (per root × schema)

- [ ] Contract universe vs `definition` records: listing (activation),
      expiration, security_update_action add/modify/delete; join
      definition.expiration ↔ IBKR lastTradeDate for every overlapping
      contract; 100% match required on the pilot (spec §5 Identity check).
- [ ] Gaps: missing contract-days inside a chunk where the exchange actually
      traded. Distinguish (a) holiday closures, (b) sparse-but-active
      contracts (no-trade intervals emit no bars), (c) true delivery holes —
      only (c) triggers repair. Holiday-vs-gap typing needs a real holiday
      calendar (see SYMBOL_READINESS: still a non-vendor blocker).
- [ ] Duplicates: same (instrument_id, ts_event, schema) twice in one chunk
      → finding; overlapping chunks (same quarter bought twice) must not
      exist by construction (one-owner rule in the manifest).
- [ ] Crossed/invalid bars: high < low, non-positive prices where illegal
      (negative CL remains legal per our engine), volume < 0 — every
      occurrence listed with instrument + ts, never dropped silently.
- [ ] Statistics sanity: settlement (stat_type 3) present per expected
      contract-day with final-vs-preliminary flags typed correctly (flag
      semantics re-verified on first real data per adapter note); open
      interest (9) and cleared volume (6) next-UTC-day publication verified
      against ts_recv (PIT: OI(t) not observable before t+1).

## Step 4 — IBKR-overlap validation (PILOT lines; thresholds are the
DATA_ACQUISITION_SPEC.md §5 table — reproduced verbatim as the acceptance
bar; PREP proposed, owner/pilot adjudicates)

| Check | Metric | Proposed pass |
|---|---|---|
| Identity | definition expiry/settlement vs IBKR lastTradeDate, per contract | 100% match; SI/6J-style traps re-verified |
| Daily OHLCV | close diff in ticks; OHLC containment | median ≤ 0.5 tick; ≥ 99% days within 1 tick |
| Daily volume | IBKR vs vendor per contract-day | median ratio in [0.9, 1.1]; outliers investigated, not dropped |
| M1 alignment | bar timestamps on minute grid (bar-START convention); close diff | ≥ 99% aligned; median ≤ 0.5 tick |
| Settlement | statistics stat_type 3 (final) vs IBKR close-only bar close | ≥ 99% within 1 tick |
| OI sanity | statistics stat_type 9 vs CFTC/CME published totals spot-check | consistent on sampled dates |
| Roll conventions | symbology.resolve c/n/v intervals vs our declared rule | divergence table produced; no silent adoption |

- [ ] RTH-subset comparison only (IBKR files are useRTH=true; vendor covers
      full Globex); the full-session delta is itself recorded as a
      validation target, not an error.
- [ ] Any systematic mismatch (session stitching, volume consolidation,
      price scaling, 6J quote orientation, SI 5000oz class identity) is
      documented and resolved BEFORE any EXPANSION line is bought;
      unresolved identity mismatches BLOCK that symbol's bulk request
      (spec §5 failure handling).

## Step 5 — Repair loop (bounded, idempotent, no double-billing)

- [ ] True delivery holes only: re-request the SAME chunk with the SAME
      exact parameters (idempotent chunk key); record the re-request in the
      ledger BEFORE submitting; new job id appended to the same chunk entry.
- [ ] Re-run Steps 1–3 for the repaired chunk only; never re-buy a
      delivered-and-verified quarter (one-owner rule).
- [ ] Two consecutive failed repairs of the same chunk → stop, escalate to
      owner with the evidence (no workaround purchases).

## Step 6 — Freeze, budget registration, gates, A7 — then STOP

- [ ] Freeze: coverage manifest v2 (per root × schema × contract × date
      range, sha256 of every delivered file), stored beside
      `data/COVERAGE_MANIFEST.json` per owner's layout decision; the
      completion ledger closed out and archived.
- [ ] Budget registration: actual spend (from vendor invoice/usage page,
      owner-supplied) vs the Phase-0 estimate table recorded in the cycle's
      accounting; deviations explained.
- [ ] Cycle gate: the prep cycle's own gate procedure runs on the new
      evidence (this checklist complete = evidence, not PASS of anything
      else).
- [ ] Fresh-context A7 audit over the ingestion + QA trail.
- [ ] **STOP.** Anything beyond (backtests, scored runs, new purchases)
      requires a future REGISTERED cycle with frozen budget/trial
      accounting and explicit owner GO per workspace law. Deliveries,
      checklists and green tables grant nothing by themselves.

## Non-vendor blockers that remain AFTER perfect acceptance (do not lose
these — data acceptance does not clear them)

See SYMBOL_READINESS.md for the per-symbol list: declared slippage (owner),
exchange fees 9/10 NOT_FETCHED, real holiday calendar source, consensus /
weather-vintage / macro-vintage PIT inputs, broker execution audit trail,
serial re-fetch deadlines (SERIAL_REFETCH_MANIFEST.md), RTH-only overnight
gap on the IBKR side (vendor data closes it for vendor-covered windows
only).
