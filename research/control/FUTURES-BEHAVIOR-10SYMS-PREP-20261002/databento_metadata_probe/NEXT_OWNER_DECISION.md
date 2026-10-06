# NEXT_OWNER_DECISION — proposed PILOT package (owner approval needed for SPEND only)

Task `FUTURES-BEHAVIOR-10SYMS-PREP-20261002` · lane `METADATA-PROBE` · 2026-10-02.
Evidence base: `metadata_results.json` (80 metadata-only requests, 78 ok,
2 typed 422 blockers, zero data bytes downloaded) + `DATABENTO_METADATA_PROBE.md`.

## 0. Hard frame (unchanged by anything measured here)

- This probe round made **zero purchases, zero downloads, zero subscriptions**.
- **Even a $0 quote stops at the download gate this round.** Nothing in this
  file is a GO. Any actual data request (timeseries/batch) requires the
  owner's explicit spend approval in a future step, still inside the
  manifest's chunk/ledger discipline.
- New-user credits (e.g. $125) are **not free spend** and were not visible
  through any verifiable metadata endpoint (NOT_RUN_DOC_UNCLEAR). The key is
  not a budget.
- All quotes below are from `metadata.get_billable_size` /
  `metadata.get_cost` / `metadata.list_unit_prices` captured 2026-10-02.
  No documented validity window — re-probe exact chunk params before any
  spend (manifest already mandates this per chunk).

## 1. THE ONE DECISION: approve the PILOT package below (or reject/modify)

**Package = manifest lines PILOT-01 .. PILOT-06, unchanged, NQ + CL only.**

| line | schema | symbols | exact window(s) | requests at delivery | records (measured) | billable GB | cost @ list | note |
|---|---|---|---|---|---|---|---|---|
| PILOT-01 | definition | NQ.FUT + CL.FUT (parent) | 2024-12-01 .. 2026-10-01 | 1 (or 2 per-root chunks) | 2,496,868 | 1.2984 | $2.2072 | identity/universe; 520 B/rec verified exact |
| PILOT-02 | statistics | NQ.FUT + CL.FUT | 2025-08-01 .. 2026-10-01 | 1 | 11,209,402 | 0.8968 | $0.8968 (get_cost API: $0.8352) | settlement+OI+cleared vol |
| PILOT-03 | ohlcv-1d | NQ.FUT + CL.FUT | 8 roll windows (manifest verbatim) | 8 | DERIVED 30,215 (rc NOT_RUN, cap-bound) | 0.0017 | $0.3215 | UTC-day daily reference panel |
| PILOT-04 | ohlcv-1m | 15 raw symbols per window | 14 windows (manifest verbatim) | 14 | 21,756 | 0.0012 | $0.0853 (window cross-check get_cost $0.009244) | M1 alignment vs IBKR |
| PILOT-05 | bbo-1m | same windows as PILOT-04 | 14 windows | 14 | DERIVED 23,228 (rc NOT_RUN, cap-bound) | 0.0019 | $0.0334 | synchronous spread, first executable-spread measurement |
| PILOT-06 | symbology.resolve only | {ROOT}.c.0/.n.0/.v.0 | 2010-01-01 .. 2026-10-01 | 1 | n/a | n/a | $0.00 | **requires param fix**: stype_out=raw_symbol is UNSUPPORTED (HTTP 422, vendor-cited supported-combinations docs); use stype_out=instrument_id (still free, metadata-only) |

**Totals (measured API numbers):**
- records: **13,728,026 measured** + 53,443 derived-not-measured
- storage: **2.1999 GB billable** (uncompressed DBN; ~0.9–1.3 GB on disk at the manifest's ASSUMED 0.4–0.6 zstd factor)
- cost: **$3.5442 at list unit prices**; **~$3.3** using the measured get_cost/list ratio 0.9313 (get_cost is the API's own quote and is authoritative)

**MAX-COST CEILING proposed for owner approval: $10.00.**
Basis: quote $3.3–$3.5442
+ margin for (a) extending the two front-strip windows to include 2026-10-01
(end-exclusive semantics; ~1 extra day, <$0.01), (b) price/size drift between
quote and purchase, (c) the bounded repair loop re-requesting identical
chunks. Anything above $10 for this package = stop and re-consult.

## 2. Why this is the SMALLEST acquisition that satisfies the pilot hypotheses

The pilot's purpose is the IBKR-overlap validation table
(DATA_ACCEPTANCE_CHECKLIST.md Step 4 — the acceptance bar; nothing lowered):
Identity (needs PILOT-01 definitions), Settlement + OI sanity (PILOT-02
statistics — the only schema carrying OI), Daily OHLCV + volume (PILOT-03),
M1 alignment (PILOT-04), spread sanity (PILOT-05), Roll conventions
(PILOT-06). Removing any line orphans at least one acceptance row; each line
already uses the manifest's schema_choice_discipline minimum (ohlcv-1m not
trades; bbo-1m not mbp-1; statistics not deep schemas; definition is the
only PIT-universe schema). No acceptance threshold or hypothesis floor was
lowered to shrink cost (floors per manifest: e.g. 100% identity match,
median <= 0.5 tick, >= 99% within 1 tick, M1 >= 99% aligned).

Two owner options that WOULD shrink further but are NOT recommended (flagged,
not decided by this lane):
- Phase PILOT-05 (bbo-1m, $0.0334) after PILOT-04 acceptance — saves cents, delays the
  spread-sanity row, complicates the gate.
- Trim PILOT-01's 2-month listing lead — risks missing PIT listings the
  acceptance join needs.

## 3. Context for the LATER expansion decision (no approval requested now)

EXP-01..05 as specified measure **$552.0765 at list /
~$514.15 ratio-adjusted**,
54.4457 GB billable, 433,916,711 records
(EXP-06/07/08 not enumerable yet; EXP-09 blocked on the same free-endpoint
param fix). Dominant driver: ohlcv-1m at $70/GB (EXP-04
$380.1882 of it). This is
the number to budget against, AFTER pilot acceptance per the manifest's
phase gates. All 10 roots show ohlcv-1m records > 0 over their full line
windows (OBSERVED).

## 4. What must be fixed before ANY request is submitted (next round)

1. `symbology.resolve`: use `stype_out=instrument_id` (422 evidence in
   metadata_results.json R005/R080). Free endpoint; no billing risk.
2. Chunk keys per the manifest are per-root — joined quotes above equal the
   sum of per-root chunks (sizes/counts are additive per symbol for the same
   schema+window; verified by the exact count x record-size reconciliation).
3. Front-strip windows: decide whether 2026-10-01 must be included
   (end-exclusive semantics) and re-probe those two chunks before submission.
4. data/request/probe_*.py need the {ROOT}.FUT + POST/hist.databento.com
   corrections if the owner wants THOSE scripts executable later (frozen for
   the audit lane now; corrections documented in DATABENTO_METADATA_PROBE.md §7).
