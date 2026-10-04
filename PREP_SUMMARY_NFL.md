# PREP_SUMMARY_NFL — NFL-WINPROB-PREP-V1 controller synthesis (2026-10-04)

- cycle: NFL-WINPROB-PREP-V1 (ACTIVE_LIGHT, budget 0, no GO phrase) · branch
  orca/nfl-winprob-prep-v1-integration from main @ 8deb036d · root G0 commit ad7baeed.
- owner authority: NFL directive 2026-10-04 (authorize $0 clearly-righted downloads +
  audit + PREP; explicitly NOT a typed GO; no NBA mixing).

## Gate verdicts
- G0 PASS (plan/registry/worktree). G1 PASS — lane A DATA_RIGHTS_OK (all load-bearing
  rights re-verified live; nflverse-data CC BY 4.0; nfldata no-license ban; PFR 5(11)/
  NFL.com FAIL; injuries date_modified ≠ announcement → NOT_RUN_PIT; odds columns
  quarantined). G2 PASS — lane B census + downloads (8 files from nflverse-data releases
  only; games.csv 7,548 rows 1999-2026; 7,325 finished; pbp 2021-2025 247,284 plays,
  100% game_id join; timestamp.json as-of markers recorded). G3 PASS — lane C protocol
  (9 arms: B0; B1 K∈{20,40}×HCA∈{0,65} γ=2/3; B2 variants; T1-T3/R1-R3; NOT_RUN 15 rows;
  seed 20261005). G4 PASS — nfl_winprob package 11/11 synthetic tests; real-data build +
  features export = mechanics only, NO metric (evaluate.py refuses, exit 3). G5 = lane D.

## Controller decisions & corrections
1. LINEAGE COUNT 32 (not lane B's 31): B merged CLE+BAL; standard NFL convention (and
   B's own "protocol decision" note) keeps CLE/BAL separate. Frozen in build fixture.
2. SPLIT FROZEN: TEST 2019..2025 (final 7 complete seasons; last complete = 2025; 2026
   in progress excluded), TRAIN 2000..2018. Kickoff-grain law active from season 2000
   (1999 gametime 100% missing — measured); 1999 excluded (259 rows skipped).
3. NEUTRAL SITE: flaggable via `location` (95 neutral games in build scope) → per lane C
   conditional: HCA=0 in prediction+update on neutral games (test-enforced).
4. REST SEMANTICS: floor-days between kickoffs, cap 20d; short_week ≤ 6d; bye ~13-17d
   stays uncapped. Ties (15) excluded from scoring per protocol; Elo update S=0.5.
5. Timezone: America/New_York → UTC via zoneinfo (documented ET semantics, lane B);
   uniform-offset safety argument for ordering recorded.

## Data provenance (outside git)
- raw: ~/.my-quantitative-data/nfl-nflverse-v1/raw/ (games.csv, timestamp.json, 5 pbp
  parquets 2021-2025, ATTRIBUTION.md — CC BY 4.0, release tags, per-file sha256+bytes+
  pull time). derived: games_nfl.csv (7,066 rows), lineages_nfl.csv (32),
  features_nfl.csv (7,066, sha256 1f411034…), manifests.

## NOT_RUN (this cycle, by law)
Any metric on real outcomes (log loss/Brier/calibration); injuries features (PIT
unproven); odds/betting columns (quarantined, closing-line contaminated); pbp-derived
features in v1 (post-game compilation + retro corrections); keyed/paid sources.

## Successor path
Register NFL-WINPROB-SCORED-V1 inheriting PROTOCOL_EVAL_NFL.md + frozen split + this
summary's decisions; freeze; A7; owner types at that cycle's own gate:
    GO NFL WINPROB SCORED V1 EVALUATION

## ERRATUM 2026-10-04 (round 3, owner-independent rejection — remediated)
Old G4/G5 PASS verdicts are REOPENED and SUPERSEDED: three defects confirmed
by controller re-measurement: (1) build compared game_type to 'reg' while the
raw domain is UPPERCASE {REG,WC,DIV,CON,SB} -> ALL 7,066 games were flagged
playoffs (form degenerated, primary RS empty). FIXED via GAME_TYPE_MAP
normalization; rebuild now measures n_reg=6,768 / n_post=298 / other=0, test
window 2019-2025 = 1,871 reg + 89 post (= lane B's 1,960). (2) features
credited ties 0 in form instead of 0.5 per PROTOCOL_EVAL_NFL sec2 f5. FIXED
(= now (wins + 0.5*ties)/games − 0.5, both sides). (3) Elo engine updated
sequentially, violating the identical-kickoff exclusion law. FIXED: kickoff-
batched predictions (adversarial fixtures added: same-kickoff doubleheader,
same-kickoff mutation isolation, tie-half-win form, REG normalization).
Features rebuilt twice (REG fix then elo_diff column per the scored-cycle
amendment); 15/15 tests PASS. Raw untouched. The old verifier PASS (lane D
round 1) remains as history; new verification + A7 happen in the scored cycle.
