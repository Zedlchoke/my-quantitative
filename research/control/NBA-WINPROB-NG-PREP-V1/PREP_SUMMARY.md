# PREP_SUMMARY — NBA-WINPROB-NG-PREP-V1 (controller synthesis, 2026-10-05)

- Cycle: NBA-WINPROB-NG-PREP-V1 · ACTIVE_LIGHT · budget 0 scored · no GO phrase (never
  registered, never consumed). Verdict: **PREP_COMPLETE_PENDING_OWNER_DECISIONS**.
- Chain: plan commit 5276a7b8 (root main) → registry register 156ecc44 → G0 01e747e7
  (dispatch packets + state) → lanes A/B/C landed e85d9dbe → D verification landed 3f17514b.
- Independent verification: lane D **VERIFICATION_PASS** — 0 BLOCKER, 1 MEDIUM (D1:
  spec's "4 played games lack pbp" is actually 14 — 2016×3, 2018×4, 2020×6, 2026×1;
  documentation-level, adjudicated from parquet bytes by the verifier; the game-universe
  law and per-season census are unaffected), 4 LOW, 2 INFO. Defects recorded, not repaired.

## Data layer (lane A, measured)

- Corpus: hoopR/sportsdataverse schedules 2016–2026 (rights CC BY 4.0 producer + MIT
  release store, verified prior cycle + inherited) + 10 new pbp parquets 2016–2025
  (268.6 MB, sha256'd, $0) → `~/.my-quantitative-data/nba-ng-prep-v1/`.
- Game universe: 14,254 raw = **14,168 played** + 19 exhibitions + 67 postponed listings
  (zero residue, verifier-reproduced). Played = RS 1,230×9 + 1,059 (2020 COVID) + 1,080
  (2021 72-game) + play-in 37 + playoffs 919 + Cup final 3 (2024–26 flagged).
- Identity/clock: ESPN `game_id` PK unique 14,254/14,254; tip_utc == start_date == date on
  14,254/14,254, offsets Eastern-only (−0400/−0500), DST-exact; 77.33% of games cross UTC
  midnight; crosswalk 1,330/1,330 joins; 538-era seam clean (local-date+home-team join law).
- BDL cross-check (free tier, spot-only): **22/22 MATCH** (date/home/away/score/tip-UTC,
  tip delta 0.0 s; 11 requests ≤25, throttled; key value never in artifacts). BDL =
  CROSS-CHECK only, never primary (hoopR primary).
- Spread line: coverage 100% every season 2016–2026 BUT line timing UNVERIFIED_PIT →
  diagnostic-only status for any successor.
- PIT: ratings/rest-travel/box-pbp priors PIT_PASS-conditional (freeze law written);
  injury/roster NOT_RUN_PIT (no $0 source with rights + real publish timestamps).

## Mechanisms (lane B): 4 advanced, frozen falsifiers

- NB-H1 SOS-adjusted Elo; NB-H2 home/away split ratings; NB-H3 fatigue×venue joint block
  (away-restricted replacement shape); NB-H4 pace/efficiency train-only rating-init
  (gated on data rights, else released). Each: REJECT iff pooled 95% paired
  date-cluster-bootstrap CI of ΔLL vs B1* includes 0 or ≥ half folds non-negative;
  time-shuffled twins mandatory; null parents designed (β=0 / λ=0 / θ≡0 / w=0).
- Baseline law: **B1* = B1-d K=32 HCA=100 LL 0.5987 frozen verbatim** from
  NBA-WINPROB-SCORED-V1; 2009–2015 SPENT (no re-grid anywhere — verifier-confirmed).
- Rejected: additive logistic-over-Elo (dead shape), MOV-Elo (dead family), 538 forecasts/
  closing odds/current-game box (banned), rest/form mains re-tests.

## Protocol draft (lane C) for successor NBA-WINPROB-NG-SCORED-V1

- Split: warm-up 2016–17 (never scored); train-internal selection 2018–2021; frozen
  cutoff 2021-08-01T00:00:00Z; walk-forward OOS [2022, 2023, 2024, 2025, 2026];
  2026–27+ prospective-only append-only ledger (rows timestamped strictly pre-tip).
- Arms ≤9 (expected ≤6 used): B0; B1* verbatim; M1–M4 conditional mechanism arms
  (release-only, never reallocated); availability NOT_RUN_PIT; reserves released.
  Shuffled twins + B1-HCA0 ablation = DIAGNOSTIC class, outside candidate budget.
- Metrics: log loss primary; Brier/reliability/slope [0.85,1.15]; paired date-cluster
  bootstrap 10k seed 20261005; single-batch scoring; playoffs/play-in/Cup separate;
  negative-first terminals inherited.

## Successor registration conditions (exact)

1. This cycle's PREP_COMPLETE verdict (this document) + owner instruction naming the
   successor (proposed id NBA-WINPROB-NG-SCORED-V1).
2. Fresh registry registration (budget scored, GO phrase registered-not-consumed).
3. Data freeze (raw+derived sha256 manifest incl. the pbp gap of 14 games disclosed),
   code freeze, protocol constants digest — all frozen BEFORE any test-window look.
4. Independent A7 prelaunch AUTHORIZED with 0 unresolved HIGH/CRITICAL.
5. Owner typed GO, fresh, verbatim, at the successor cycle's own gate (two-key law).
6. Prohibited regardless: any scored/S1/paper/live/push/merge/purchase before all five;
   no GO survives from this or any earlier cycle (P-8).
