# lane_x vs lane I — G5 AGREEMENT REPORT (EVENT-MECHANISMS-V1, 2026-09-27)

Independent implementation (this lane, commit `33d43210`, built from
G3_FREEZE + addenda r1/r2 alone) compared against lane I decision books
(`engine/evidence/a1_decisions.jsonl.gz`, `a2_decisions.jsonl.gz`,
PRIMARY variant only).  Per P4(d): **records only — no aggregate of trade
returns computed anywhere in this comparison.**

## P1 — implementation one-liners

- A1 anchor built from the staged `a1_events.jsonl` (54,941 candidates,
  pins verified fail-closed) with R2-4 ET/DST strata, R2-3 close-anchored
  sequencing, R2-2 CA exclusion, B1/X1 bar laws → **19,708 records**.
- A1-N2 = same rule restricted to weekday S2 → **26,692 records**.
- A2 anchor built from the pinned `form4_stream.jsonl` (546,039 rows,
  37,305 P-rows) joined to the form4_xml estate (20,160 unique P-row
  accessions, 0 missing) → 4,891 issuer-day events ≥ $100k officer/director
  original-filing buys → **4,055 records**, H=10, long-only, F1 = 0
  (substrate 2018-01..2025-05, the known fact, disclosed not normalized).

## P3/P4 — agreement numbers

### Key sets (event identity per R2-3; A2 keys normalized per side's day basis)

| arm | lane_x | lane I | intersection | only lane_x | only lane I | Jaccard |
|---|---|---|---|---|---|---|
| A1_anchor | 19,708 | 14,109 | 14,090 | 5,618 | 19 | 0.714250 |
| A1_N2 | 26,692 | 14,577 | 14,548 | 12,144 | 29 | 0.544441 |
| A2_anchor | 4,055 | 2,921 | 764* | 3,291 | 2,157 | 0.122988 |

*A2 day bases differ by construction (lane_x keys issuer-days by
`transaction_date`, lane I by UTC acceptance date — unlogged ambiguity
A2-1 below).  Secondary match on the shared triggering filing
`(cik, acceptance_utc)`: **2,256 of lane I's 2,921 records matched**
(lane_x has 3,418 unique instants).

### Field-level agreement on the A1 intersections (records only)

| field | A1_anchor (n=14,090) | A1_N2 (n=14,548) |
|---|---|---|
| direction_session | 0 mism | 0 mism |
| direction (sign, LONG/SHORT normalized) | 0 | 0 |
| entry_session | 0 | 0 |
| entry_price (raw, 1e-9) | **0** | **0** |
| exit_session | 3 | 4 |
| exit_price | 3 | 4 |
| delisting_exit / fold / stratum / hold | 0 | 0 |

i.e. **14,087/14,090 and 14,544/14,548 intersection records are fully
identical on every decision field.**  All 7 exit mismatches have lane I
`forced_flat=true` (their fold-boundary clamp) vs lane_x's full raw-H
window.

### A2 secondary-matched mechanics (n=2,256)

stratum / fold / delisting_exit: **0 mismatches**.
entry_session 1,250 / exit_session 1,253 / entry_price 1,238 /
exit_price 1,240 mismatches — one mechanism, see DEFECT-1.
`direction_session` differs on all 2,256 (lane_x records none for the
long-only book; lane I populates the A1-style session) — record-shape
DATA_VARIANT, no economic content.

### Key-difference attribution (100% mapped, 0 unmapped)

only-lane_x keys mapped to lane I's own anchor/N2-arm exclusion reasons:

| lane I exclusion reason | A1_anchor | A1_N2 | classification |
|---|---|---|---|
| BELOW_DV_FLOOR_AT_DECISION | 4,019 | 9,081 | SPEC_AMBIGUITY (AMB-14: frozen DVmed60 floor at book stage vs G4 sizing stage) |
| ZERO_DIRECTION_SESSION_MOVE | 1,197 | 2,466 | SPEC_AMBIGUITY (AMB-11: record direction=0 vs exclude) |
| FOLD_BOUNDARY_NO_WINDOW | 301 | 393 | SPEC_AMBIGUITY_UNLOGGED (fold force-flat at book stage) |
| EXIT_BAR_UNFILLABLE_B1B2 | 100 | 190 | SPEC_AMBIGUITY (AMB-07: exit rolls forward vs exclude) |
| NO_ENTRY_SESSION | 1 | 9 | DATA_VARIANT (panel-guard row skipping shortens lane I grids) |
| NO_SESSION_AFTER_ACCEPTANCE | 0 | 5 | DATA_VARIANT (same) |

only-lane_I keys (lane I booked, lane_x excluded):

| decomposition | A1_anchor | A1_N2 | classification |
|---|---|---|---|
| lane I div-file case-miss (79 `_OLD`-style names never resolved exact-case) | 18 | 29 | **DEFECT (lane I)** — R2-2 requires exclusion on ANY ex-date for the name from the tables on disk |
| lane I force-flat shortened window hides the ex-date | 1 | 0 | SPEC_AMBIGUITY_UNLOGGED (follows the force-flat reading) |

### Classification totals (records)

| class | records |
|---|---|
| SPEC_AMBIGUITY (traceable to logged AMB-##) | 5,316 + 11,737 key diffs = 17,053 |
| SPEC_AMBIGUITY_UNLOGGED (found at comparison) | 301 + 393 + 7 + 1 + 2,256 A2 key-basis records |
| DEFECT (lane I) | 47 CA case-miss records + A2 entry law (~1,250 secondary-matched records) |
| DATA_VARIANT | 15 panel-guard records + A2 direction_session shape |

## P5 — verdict line

**G5_PASS_WITH_ADJUDICATIONS**

The independent implementations agree exactly on the A1 core: identical
event identity treatment, identical sequencing, identical direction signs,
and byte-equal raw entry/exit prices on 28,631 of 28,638 intersection
records (99.98%); every key-set difference is fully attributed to a named
reading on one side.  Adjudications required (all record-level, none
touching aggregates):

1. **A2 entry law (DEFECT, lane I)** — lane I books A2 with the A1-style
   entry (open of the session after the direction session; verified in
   `emv1/book.py` `resolve_direction_entry` used for A2 with only a LONG
   override).  R2-3 is explicit: "entry = first session open strictly
   after the acceptance instant".  Diverges for S1/S3/S4 acceptances
   (~55% of secondary-matched records).  Fix or owner-adjudicate before G4.
2. **Fold force-flat at book stage (unlogged ambiguity)** — lane I never
   lets a hold window cross its fold end (801 unique A1 events + 7 exit
   fields + 1 CA interaction); lane_x applies the raw H-session law and
   records `fold` as bookkeeping.  Adjudicate whether fold isolation lives
   in decision records or in evaluation.
3. **A2 issuer-day basis (unlogged ambiguity → returns to A1 per R2-3)** —
   lane_x groups by transaction_date, lane I by UTC acceptance date;
   value aggregation and the $100k floor bite differently (4,891 vs 5,606
   events).
4. **DVmed60 floor stage (AMB-14)** — lane I excludes at book stage
   (13,100 A1 anchor+N2 key diffs), lane_x defers to sizing.
5. **Zero-direction events (AMB-11)** — record (lane_x) vs exclude (lane I).
6. **Exit-bar fill failure (AMB-07)** — roll forward (lane_x) vs exclude
   (lane I).
7. **Unpriced A2 rows (AMB-06)** — panel-close fallback (lane_x, 354 rows)
   vs drop (lane I, 294 rows).
8. **Lane I div-file resolution (DEFECT, minor)** — exact-case stem lookup
   silently misses the 79 case-differing div/splits files; 47 A1 records
   booked that R2-2 requires excluded.  Recommend case-folded resolution +
   fail-loud missing-file counter.

## Sanity cross-checks (P5)

- A1 anchor strata (lane_x vs lane I): S1 8,988/4,815 · S3 10,271/8,884 ·
  S4 449/410 (gaps = attributed exclusions above, S1 hit hardest by the DV
  floor).
- Folds (lane_x/lane I, anchor): F1 6,054/3,690 · F2 5,878/4,018 ·
  F3 3,489/2,550 · F4 4,287/3,851 — same fold convention, monotone gaps.
- A2 F1 = 0 on BOTH sides (substrate fact, disclosed by both lanes).
- Determinism: lane_x double-run byte-identical
  (`../evidence/determinism.txt`); lane I full-chain 15/15 byte-identical
  (their E6).

## Artifacts

- `comparison_results.json` — per-arm key-set + field stats + samples
- `field_mismatches_full.json` — every mismatching intersection record
- `key_diff_attribution.json` — full key-diff attribution + strata sanity
- `build_comparison.py`, `attribute_diffs.py` — the comparison code

Comparison inputs were read-only; nothing under `engine/` was modified.
