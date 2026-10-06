# Cross-root contaminant scan — vendor ohlcv-1m parquet (six roots)

Lane `INTEGRATION-FIX-V2` · task `FUTURES-DEEPRESEARCH-V2-20261003` · 2026-10-03
Script: `contaminant_scan.py` (same dir) · Data:
`/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/`
(**READ-ONLY** — vendor parquet and raw `dbn.zst` are immutable and were NOT
rewritten; this scan is a measurement + documented VIEW RULE).

> **ERRATUM 2026-10-03 (lane NONPRICE-SOURCE-FIX2, per audit A7-INTEGRATION
> F-4).** The prose total "2,637,950 spread bars" below overstated the table
> by exactly 100,000: the sum of the (correct) per-root counts is
> **2,537,950** = 641,787 + 884,863 + 375,722 + 275,066 + 189,039 +
> 171,473. Per-root numbers were always right; only the prose sum was wrong.

Scope: every ohlcv-1m line dir per root (AV1T original + AV1R delta/backfill +
AV1B backfill2): NQ (2010-06..2026-10), ES (2010-06..2026-10), 6E/6J/6B/6A
(2020-01..2026-10). 28,212,754 bars classified by `raw_symbol`.

## Totals per root

| Root | total bars | outright root-family | spread/strip | foreign outright |
|---|---:|---:|---:|---:|
| NQ | 7,330,320 | 6,688,533 (40 syms) | 641,787 (119) | **0** |
| ES | 8,710,520 | 7,825,657 (40 syms) | 884,863 (151) | **0** |
| 6E | 3,436,733 | 3,054,311 (90) | 375,722 (341) | **6,700 (2)** |
| 6J | 3,120,241 | 2,843,938 (87) | 275,066 (295) | **1,237 (1)** |
| 6B | 2,738,672 | 2,547,494 (88) | 189,039 (301) | **2,139 (1)** |
| 6A | 2,876,268 | 2,703,211 (86) | 171,473 (278) | **1,584 (1)** |

No `other` (unclassifiable) symbols exist in any root.

## Foreign-outright quarantine lists (must be excluded by every consumer)

| Root | symbol | bars | volume | first | last | note |
|---|---|---:|---:|---|---|---|
| 6E | `6JZ7` | 4,831 | 15,561 | 2020-04-23 | 2020-08-17 | JPY family inside 6E response (DEEP-6E knew) |
| 6E | `SIJ5` | 1,869 | 17,290 | 2025-09-10 | 2025-10-10 | Silver family inside 6E response (DEEP-6E knew) |
| 6J | `6AV3` | 1,237 | 2,253 | 2020-03-24 | 2020-07-13 | **NEW finding** — AUD family inside 6J response (not in DEEP-6J's report) |
| 6B | `GCQ4` | 2,139 | 6,090 | 2020-07-28 | 2020-11-16 | Gold family inside 6B response (DEEP-6B quarantined locally) |
| 6A | `6BU5` | 1,584 | 4,888 | 2020-05-12 | 2020-08-17 | GBP family inside 6A response (DEEP-6A knew) |

Pattern: every foreign stray sits in the 2020-01..2021 FX backfill2 window
(except SIJ5, a 2025 straggler in the AV1T/original generation). All reconcile
1:1 with the DEEP lanes' local counts — the strays are inside the VENDOR's
parent-symbol response, not an artifact of lane-side processing.

## Spread/strip instruments (structural, not defects)

Calendar-spread instruments (dash-joined, e.g. `6EM5-6EH5`, `NQU8-NQM9`) are
6-15% of FX rows and ~8-10% of NQ/ES rows. They are a separate instrument
class from the vendor's parent delivery — legit data, but NOT part of any
outright per-contract panel. Their prices can differ wildly (negative spread
prices are normal — DEEP-6A measured 32,694 negative bars, all on spread
instruments). Any volume/OI aggregation that mixes them into outrights is
invalid.

## Canonical filter (VIEW RULE — apply downstream, vendor stays immutable)

Keep a bar iff `raw_symbol` matches the root's exact regex
(`F,G,H,J,K,M,N,Q,U,V,X,Z` = CME month codes, `[0-9]` = decade digit):

```
NQ:  ^NQ[FGHJKMNQUVXZ][0-9]$
ES:  ^ES[FGHJKMNQUVXZ][0-9]$
6E:  ^6E[FGHJKMNQUVXZ][0-9]$
6J:  ^6J[FGHJKMNQUVXZ][0-9]$
6B:  ^6B[FGHJKMNQUVXZ][0-9]$
6A:  ^6A[FGHJKMNQUVXZ][0-9]$
```

Everything failing the regex (dash spreads, foreign outright strays, any
future oddity) is quarantined. Consumers that already apply an
outright-regex (DEEP-6E `OUTRIGHT_RE`, DEEP-NQ/ES outright builders,
DEEP-6A/6B family filters) are conformant; consumers reading parquet raw
without a filter would have absorbed the 11,660 foreign bars + **2,537,950**
spread bars listed above *(ERRATUM: was misstated as 2,637,950 — see erratum
block; the per-root table was always correct)*.

Known affected/serendipitous notes: the DEEP lanes' caches filtered by
outright regex fullmatch (`^6J[FGHJKMNQUVXZ]\d$` in 6J_deep_lib.py,
`^6A...` in 6A_deep_lib.py, OUTRIGHT_RE in DEEP-6E), so every foreign stray
above — including the newly-found `6AV3` — was already excluded from their
panels; this scan confirms their local quarantines were complete for their
windows and no dossier number changes.
