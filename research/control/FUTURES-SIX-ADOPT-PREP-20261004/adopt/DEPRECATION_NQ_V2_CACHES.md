# DEPRECATION_NQ_V2_CACHES — old NQ v2 caches SUPERSEDED

Round: FUTURES-SIX-ADOPT-PREP-20261004 · Lane ADOPT · 2026-10-04

## Declaration

**`research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache/` (panel
`nq_outright_1m.parquet` 6,688,533 rows + held chains + sessions + held-daily + registry) is
SUPERSEDED-BY `research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3/` for ALL future
research consumption.**

* The old directory is **append-only historical evidence of the v2 era and is NOT modified by this
  round** — this marker lives only in the new round. Nothing was edited, moved or deleted there.
* Any future NQ cycle, dossier, cost spec or chain build must consume **cache_v3** (or a
  successor rebuilt under the same declared rules) and must cite this marker when not doing so.
* cache_v3's own canonical status is a CANDIDATE pending owner D9 (see `CACHE_V3_PIT_STATEMENT.md`);
  deprecation of v2 does not by itself ratify v3 — it only closes v2 for consumption.

## Exact defects in the v2 caches (round-1 verify numbers; re-confirmed by this lane from the v2 bytes)

1. **92,075-bar panel hole** — `nq_outright_1m.parquet` has **6,688,533** rows vs v3's 6,780,608
   (= v2 + exactly 92,075; this lane re-measured both row counts from parquet metadata). Cause:
   the dash-excluding outright filter quarantined instrument 16908 (the true NQ June-2020 front),
   carried under vendor alias `NQU8-NQM9` 2018-08-15 → 2020-05-31. Volume missing:
   **24,686,121** contracts. Symptom window: front bars NaN 2020-03-23..2020-05-29.
2. **Dead-held 49 sessions** — baseline `held_volume_k5.parquet` holds `NQH0_2020` through
   2020-03-23..2020-05-29 **after** that contract's bars-present cessation 2020-03-20
   (**49 sessions**; this lane re-measured 49/49, and `nq_held_daily.parquet` shows close NaN on all
   49 with `depleted` on all 49 in that window). This is the same "held-a-dead-contract" failure
   mode proven on 6J 2022-09-20 (ERRATUM M-5) — the v2 NQ chain had one live manifestation.
3. **Wrong 2020-06-01 roll date** — the v2 chain's `NQH0_2020 → NQM0_2020` roll sits at
   **2020-06-01 (days-to-expiry −73)**, a dead handoff fired only because the alias hole started
   printing as `NQM0` from the cutover date. The true PIT volume crossover was **2020-03-19**
   (dte +1; old 85,489 vs new 487,005 contracts) — v3's value (this lane re-measured the roll row).
4. **Stale session table** — `nq_sessions.parquet` **11,549** rows vs v3 **11,715**; registry
   111 clusters vs v3 113 (`NQM0_2020` splits into 3 clusters under the unchanged 45-day-gap rule
   after relabel).

## What the v2 caches remain valid FOR

* Reproducing, auditing or diffing any v2-era analysis that consumed them (they are the historical
  input of record for that era — keep them byte-frozen).
* ERRATUM-F1 follow-ups: any v2-era registered artifact using NQ 2020 aggregates carries the
  re-measure obligation, which the round-1 v3 rebuild DISCHARGED (`OWNER_DECISIONS.md` D9 note).
* Negative evidence: the defect list above is itself the v2-era lesson record.

## Successor pointer

`research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3/` — hashes of every file in
`../FUTURES-SIX-ADOPT-PREP-20261004/adopt/cache_v3_hashes.json`; PIT classification in
`../FUTURES-SIX-ADOPT-PREP-20261004/adopt/CACHE_V3_PIT_STATEMENT.md`.

— This file is a deprecation marker, not a ruling; canonical ratification is owner decision D9.
