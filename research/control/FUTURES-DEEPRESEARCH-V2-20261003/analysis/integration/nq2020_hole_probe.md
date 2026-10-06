# NQ 2020 "front-contract hole" — metadata-only probe & adjudication

Lane `INTEGRATION-FIX-V2` · task `FUTURES-DEEPRESEARCH-V2-20261003` · 2026-10-03
Script: `nq2020_hole_probe.py` (same dir) · raw JSON: `nq2020_hole_probe.json`
API law: **metadata endpoints only** (`metadata.get_record_count` /
`get_billable_size` / `get_cost`); **ZERO data downloaded**; key used in-process
only via the official client Authorization header, never printed/written;
errors redacted to type+HTTP code.

> **ERRATUM 2026-10-03 (lane NONPRICE-SOURCE-FIX2, per audit A7-INTEGRATION
> F-2 / F-5 / N-2).** Three corrections to this page; the adjudication
> itself is unchanged (it rests on the 169,992 == 169,992 parent-total
> equality, not on any corrected line):
> 1. **NQJ0 is NOT "HTTP 422 unresolvable".** The recorded raw probe
>    (`nq2020_hole_probe.json` → `vendor_metadata_live.raw_NQJ0_record_count…`)
>    says `BentoServerError HTTP504` — a gateway **timeout**, which supports
>    nothing about symbol resolvability. Whether the April-2020 serial exists
>    in GLBX.MDP3 is **NOT_RUN** (probe timed out; never re-attempted). The
>    "422 / not in feed" wording below (and the same claim inside the JSON's
>    `adjudication.reconciliation.NQJ0` narrative string, left untouched as a
>    recorded artifact) is retracted.
> 2. **Probe call count: 8, not 7** (record_count ×6 incl. the NQJ0 attempt,
>    `get_cost` ×1, `billable_size` ×1 — all free metadata endpoints; no
>    budget impact).
> 3. **"Only such alias in the entire six-root panel" is false.** A six-root
>    sweep (this lane, 28,212,754 bars) finds dash→outright label pairs on
>    THREE instrument_ids: 16908 (below), **2563** (`NQH5-NQM5`
>    2014-12-18..2016-05-31, 5,946 bars / 395,166 contracts, then `NQU6`
>    2016-06-01..09-16, 92,208 / 13,215,646 — deferred-scale dash alias), and
>    **2173** (1 stray `ESU6-ESU7` bar 2016-08-04 inside the ES delta chunk +
>    a `6BX1` outright tail 2021-08..11, 629 bars, inside the 6B backfill2
>    chunk — a cross-family instrument_id collision, not a front alias). The
>    weaker parenthetical survives: no dash label other than `NQU8-NQM9`
>    carries front-scale volume. Recommended view-rule generalization: remap
>    via instrument_id only where the dash label's legs and the outright
>    label share the root family AND the labels are time-contiguous
>    (16908 ✓, 2563 ✓, 2173 ✗ different families — leave quarantined).

## The finding under test

DEEP-NQ reported front contracts absent **2020-03-23 → 2020-05-29** (51
weekday sessions; only a deferred `NQU0` trickle ~100-1,200 contracts/day),
making 2020 vol/liquidity aggregates lower bounds and ranking the window as
the top backfill candidate (~$ quote requested but NOT executed).

## Adjudication: **(a) with a twist — A_ALIAS_NOT_ABSENCE. Records exist AND
we already have 100% of them. The "hole" is a vendor symbology alias, not
missing data. $0 to fix.**

### Evidence chain (all numbers reproducible from the script)

1. **Delivery integrity was never in doubt**: the chunk covering the window
   (`AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01`, parent `NQ.FUT`, GLBX.MDP3)
   is `MIRRORED` with QA `PASS`, `records_actual == records_quoted == 944,290`
   (0.0% drift).

2. **The front bars are in the file, under a dash-symbol alias**:
   `instrument_id 16908` carries the June-2020 NQ future —
   | label window | raw_symbol | bars | volume |
   |---|---|---:|---:|
   | 2018-08-15 → 2020-05-31 | `NQU8-NQM9` | 92,075 | 24,686,121 |
   | 2020-06-01 → 2020-06-19 | `NQM0` | 19,406 | 5,159,596 |
   Monthly volume ramps exactly like a deferred→front transition
   (Dec-19 2.0k → Feb-20 26.4k → Mar 6.45M → Apr 9.13M → May 9.07M contracts),
   and **2020-03-23..05-29 is fully present: 58 trading dates, 0 gaps,
   21,824,572 contracts** (Mar-23 alone: 625,650 — COVID-peak front volume).
   Every outright filter (`^NQ[FGHJKMNQUVXZ][\d]$`, dash-excluding) —
   including all six DEEP lanes' builders — quarantines dash symbols, so
   `NQM0` looked absent. ~~This is the only such alias in the entire six-root
   panel~~ *(ERRATUM: not unique — instruments 2563 and 2173 also carry
   dash+outright label pairs; see erratum block above)* (no other dash symbol
   anywhere carries front-scale volume).

3. **Live vendor metadata corroborates 1:1** (probe 2026-10-03, **8 metadata
   calls** — record_count ×6 incl. the timed-out NQJ0 attempt, `get_cost` ×1,
   `billable_size` ×1, all free; nothing downloaded *(ERRATUM: earlier prose
   and the handoff said "7 calls" — wrong)*):
   | quantity (ohlcv-1m, 2020-03-01..2020-06-30) | vendor | ours (delivered) |
   |---|---:|---:|
   | parent `NQ.FUT` record_count | **169,992** | **169,992** (all symbols) |
   | raw `NQM0` record_count | **100,034** | **100,034** (id 16908: 80,628 `NQU8-NQM9` + 19,406 `NQM0`) |
   | raw `NQH0` record_count | 17,932 | 17,932 |
   | raw `NQU0` record_count | 30,204 | 30,204 |
   | raw `NQJ0` | **HTTP 504 gateway timeout** — probe timed out; serial coverage **NOT_RUN** *(ERRATUM: was mislabeled "422 unresolvable / not in feed" — a 504 supports nothing about resolvability)* | — |
   The vendor's *current* symbology attributes all 100,034 window records to
   `NQM0` — the relabel below is vendor-corroborated, not an inference.
   Parent hole-window (2020-03-23..05-29) record_count: 76,457.

### Required fix (VIEW RULE — vendor parquet/raw immutable, no re-purchase)

Before applying the canonical outright filter to NQ, relabel:
`instrument_id == 16908 AND date < 2020-06-01` → `raw_symbol = 'NQM0'`
(92,075-bar series; 80,628 of them inside Mar-Jun 2020). Then `NQM0` resolves
to a complete front contract Mar 23 → Jun 19 2020 (58 dates = 49 weekdays +
9 Globex Sunday opens, Good Friday 2020-04-10 closed — DEEP-NQ's "51" was a
weekday-only count of the same window), and 2020 session/regime
aggregates can be re-measured. **Recommended owner action: cancel the planned
NQ 2020 backfill spend** — the re-request quote is recorded per dispatch
(`get_cost` **$0.62**, billable 9,519,552 bytes) but is NOT needed and was NOT
executed; budget untouched.

### Impact on DEEP-NQ dossier numbers (erratum for A7-DEEP-AUDIT, not edited
by this lane — dossier is another lane's output)

- "VENDOR HOLE: NQ front contracts entirely absent 2020-03-23..05-29" →
  reclassify: vendor ALIAS artifact, data present in the delivered chunk.
- 2020 held-series NaNs / "lower bound" caveats for that window are
  recoverable at $0 via the view rule above; vol/DL aggregates over the window
  should be recomputed before any registered cycle uses them.
