Z1 / A3 notes — cohort rule, calendar check, SPY TR benchmark, S0/S1 partition
==============================================================================

Branch orca/stocks-free-v1-z1-cohort, bootstrap 091bb6557b8ae5e81b558cfc0df80eb81fa3a182.

Files (all lane-owned, no __init__.py — A2 owns the package init):
  research/stocks_free_v1/cohort.py         STOCKS_FREE_V1_COHORT_RULE_V1 (C1-C7),
                                            census builder, canonical cohort digest,
                                            CURRENT_SURVIVOR_LIMITATION disclosure,
                                            documentation-only seed list (SPY + sector
                                            ETFs + TLT/GLD); CohortDataSource Protocol
                                            is the minimal loader contract for A2.
  research/stocks_free_v1/calendar_check.py reconcile_session_list vs
                                            US_EQUITY_REGULAR_V1: missing/unexpected/
                                            duplicate/unsorted sessions recorded, never
                                            filled; overnight gaps are returns;
                                            halt / no-print records fail closed.
  research/stocks_free_v1/spy_benchmark.py  official SSGA NAV + distributions ingestion
                                            (stdlib xlsx reader), TR reconstruction
                                            (distribution reinvested at ex-date NAV),
                                            declared-tolerance reconciliation vs
                                            price-only and vs any adjusted series;
                                            conflicts recorded, never resolved.
  research/stocks_free_v1/partition.py      freeze_partition(coverage as INPUT) ->
                                            warmup/S0/3 force-flat folds with declared
                                            purge + sealed 12-complete-month S1;
                                            SealedPathFilter raises SealedWindowError on
                                            any S1 path; write modes always rejected.
  tests/stocks_free_v1/test_*.py            68 synthetic-golden tests (all pass offline).

Evidence in this directory:
  ssga_download_evidence.json  official URLs, access dates, sha256, sizes,
                               two-pull determinism, loader-resolved coverage,
                               per-year calendar cross-check, conflict inventory,
                               gate mapping (FD3/FD5/FD6/FD7), honest gaps.
  cohort_rule_manifest.json    the frozen pre-return rule in full.
  partition_spec.json          partition rule + NON-authoritative worked example.
  download_log.txt             raw curl transcript, probes, 404 guesses, sha256s.

Key measured facts (2026-09-03):
  NAV history 2003-12-01..2026-09-01, 5727 rows, sha256 5e055d22...
  Distributions 1993-03-19..2026-06-18, 135 SPY rows, sha256 1b952f87...
  Two pulls byte-identical. NAV-vs-calendar deltas 2010-2025: ONLY 2012 (+2:
  NAVs printed on the two Hurricane Sandy closure days) and 2014 (+1: NAV
  printed on Good Friday 2014-04-18); all other years match the frozen table
  exactly. Distribution ex-dates missing from the NAV file: 43, ALL pre-2004;
  INSIDE the frozen calendar horizon (2010+) distribution coverage is complete.

Honest limits: the real cohort census needs the A2 lane join (NOT_RUN here);
partition freeze awaits A2's accepted coverage (function takes coverage as
input; no dates fabricated in this lane). SPY split provenance is not in the
distribution workbook and remains an A2 audit item (PLAN 4.1 item 7).
