# D1 FREEZE NOTE — STOCKS-SEARCH-V1 search-space manifest

task_id: ssearch-d1
cycle: STOCKS-SEARCH-V1 (orchestration label ZCODE-ORCHESTRATION-V3)
base: 5be14a6d6771df8ec3c23ebc70f0044e9b87ec6e, branch orca/stocks-search-v1-integration
plan: plans/PLAN_stocks_search_v1.md §5 as amended by §3b (read in full before this build)
date of freeze: 2026-09-17/18 cycle window (owner amendment §3b in force)

## What is frozen

`search_space_manifest.json` (this directory) enumerates ALL 47 configurations
of the §5 grid, inside the 120 cap:

| family       | configs | grid                                     |
|--------------|---------|------------------------------------------|
| EVENT-UNWIND | 9       | K {21,63,252} x H {5,10,20}              |
| GAP          | 12      | pctl {25,50,75} x {fade,confirm} x H {1,5} |
| 52W-HIGH     | 6       | band {2,5,10}% x H {5,20}                |
| CLV-RANGE    | 4       | k {5,10} x H {5,10}                      |
| DVOL-SHOCK   | 8       | ratio {1.5x,3.0x} x {fade,confirm} x H {1,5} |
| VOL-REGIME   | 8       | L {21,63} x {long-LOW,long-HIGH} x H {5,20} |

Per configuration: stable lexicographic ID (`SSS-<FAMILY>-<PARAMKEY>`),
verbatim construction from the P0-frozen `p0/census_configs.json`, components,
sign frozen from construction logic (long-only everywhere, both directions
enumerated as distinct configs for DVOL-SHOCK / GAP / VOL-REGIME), warmup
(252/253 base law; longer construction need wins: VOL-REGIME 272/314), and the
P0 fired census per config per fold copied verbatim from `p0/p0_census.json`.

## Carried verbatim (fail-closed required fields, plan §5)

- C-CAL-HIST bucket rule: weekday x month-half buckets, minimum twin
  population 10 fired decisions per bucket per fold; sub-floor bucket
  NOT_ADJUDICABLE and disclosed, never silently skipped.
- Cost bands {A:10, B:15, C:25} bps/fill on ADV bands {50M, 10M, 2M} +
  100 bps worst-case round-trip ceiling (25 x 2 x 2.0), stress 2.0 primary.
- §3b selection tier: families DESCENDING by P0 fired-population census
  (F3 sum of fired), round-robin <= 2 cells/family until 3 cells,
  P-20 books-distinct 0.98 at S; T_F/W_c NOT COMPUTED (D2 skipped).
- Sparse-book convention: full-window zero-fill primary +
  fired-day-conditioned rho when fired-day share < 30%; MAX consumed.
- R0 shadow inventory (17 shadows, plan §6) + its own sha256
  `0af4b3bc07f57a04...`; S0 window 2015-01-02 .. 2026-09-16; percentile
  interpolation method: linear.
- Per-family expected-DOA disclosure and per-family ancestry-search basis
  (grep records against research/wayfinder/FAMILY_FAILURES.jsonl).
- R0_NOT_RUN note: D2 SKIPPED by owner amendment §3b — R0 is NOT MEASURED,
  never an inferred PASS.
- Per-state per-fold floor 10 (controls/states NOT_ADJUDICABLE below floor);
  F8 fold floor 30 bookable fired decisions/fold (all 141 cells PASS at P0).
- Zero-range law (high == low never fires, censused: 594 EVENT-UNWIND,
  375,038,212 CLV-RANGE blocked evaluation-bars).
- §3 relaxation axes verbatim (standing AND relaxed values) + §10 result
  language law.

## §3b selection tier result (census-based ORDER, not a selection)

Family ranking by F3 fired (DESC): GAP 304,405,122 > 52W-HIGH 140,371,770 >
VOL-REGIME 135,394,900 > CLV-RANGE 19,455,398 > DVOL-SHOCK 11,695,946 >
EVENT-UNWIND 745,575. Round 1 fills all 3 cells: SSS-GAP-P25-CONFIRM-H1,
SSS-52W-HIGH-B10-H20, SSS-VOL-REGIME-L21-LOW-H20 — PENDING P-20
books-distinct at S. No performance statistic anywhere; outcome-blind.

## Integrity

- builder: `build_d1_manifest.py` (deterministic; no clock, no randomness)
- selfcheck: `--selfcheck` → 34/34 checks PASS (parses, 47 configs, IDs
  unique+lexicographic, census counts == p0_census.json, family totals,
  floors pinned 10/30, verbatim pins, no performance-field keys, self-sha)
- determinism: three consecutive builds byte-identical
  (file sha256 1ccbf668cae14dbb1e5fb31da9c87136ab70a2d1a8c9068c39ea13ed0fffb24e)
- self_sha256 (empty-field convention, documented in the manifest):
  e0b69b41cdd8cf173f1685de9877d02b0936fee585231149efd17c0cc2bdcd42

## Source artifacts pinned (read-only, sha256 at base 5be14a6d)

p0_gate.json af9c4806... | p0_census.json 9ae66062... | fold_freeze.json
3f87a41d... | cost_bands.json 55d8e324... | clock_contract.json b3a68d38... |
census_configs.json 6ffa4b8f... (p0 gate overall PASS; r0_status NOT_RUN;
d2 SKIPPED_BY_OWNER_AMENDMENT_3B)
