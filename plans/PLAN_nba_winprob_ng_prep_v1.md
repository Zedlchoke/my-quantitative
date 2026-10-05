# PLAN — NBA-WINPROB-NG-PREP-V1 (next-gen NBA win-prob research PREP, $0)

- cycle_id: NBA-WINPROB-NG-PREP-V1 · asset: shared · ACTIVE_LIGHT, budget 0 scored, NO GO phrase
- owner authority 2026-10-05 (NBA+WNBA coordination chat): research/PREP + bookkeeping ONLY —
  explicitly NOT a GO for any scored cycle and NOT authority to run any metric on new NBA
  outcomes. No S1/paper/live/betting/data purchases/push/merge. NFL-WINPROB-NG-PREP-V1 runs in
  a different owner chat: untouched here; coordination is limited to the shared registry (CAS,
  never overwrite). Frozen sources, results, and ledgers of NBA-WINPROB-PREP-V1 /
  NBA-WINPROB-SCORED-V1 / WINPROB-NG-PREP-V1 (and all other cycles) are immutable history —
  this cycle never edits them.

## Inheritance (read from bytes; re-measured at bootstrap)

- NBA-WINPROB-SCORED-V1 = TERMINAL, NO_PROGRAM_PASS: 9/9 arms observed per TRIAL_LEDGER;
  H1/H2 alive, T1 (rest/form layer) FAIL; repro twin byte-identical; A7 terminal CONFIRM;
  GO consumed at own gate 2026-10-05 then extinguished at close (P-8).
- Baseline law: NBA B1* = B1-d own-Elo K=32 HCA=100 (pooled LL 0.5987 vs B0 0.6769,
  n=8369, ΔLL −0.0782 [−0.0875, −0.0687]; HCA alive: −0.0215 [−0.0271, −0.0157]; calibration
  slope 0.989 PASS). Any new mechanism must beat B1*, not merely B0. B1* constants are FROZEN
  — carried verbatim, never re-tuned.
- Spent-window law: TEST seasons 2009..2015 are SPENT (K/HCA/rest/form grid-searched and
  scored there by the terminal cycle). No re-grid of K/HCA/rest/form on 2009–2015, ever, in
  any lane of this cycle. New evaluation window = NBA seasons 2016+ (hoopR corpus) only;
  2026–27 games not yet played at the cycle prospective epoch are PROSPECTIVE ONLY.
- Data inheritance (WINPROB-NG-PREP-V1 lanes, verified by its lane D): hoopR/sportsdataverse
  releases are rights-cleared (producer LICENSE.md CC BY 4.0 verbatim covering "data, code,
  and documentation" + MIT on the sportsdataverse-data release store); 14,254 schedule rows
  2016–2026 already downloaded outside git at ~/.my-quantitative-data/nba-hoopr-v1/ with
  sha256 provenance + ATTRIBUTION.md. EXTEND ONLY — never overwrite/delete existing bytes.
- Cross-check inheritance: balldontlie key is owner-loaded in macOS Keychain
  (balldontlie/winprob-ng; WINPROB-NG-PREP-V1 lane T2: adapter PRESENT, 5/5 MATCH spot
  cross-check). BDL free tier = Teams/Players/Games, 5 req/min, `dates[]=YYYY-MM-DD`
  array syntax. BDL role in THIS cycle = CROSS-CHECK SPOT SAMPLE ONLY (targeted `dates[]`
  queries); NEVER bulk download; key value never printed into any artifact.

## Tasks (owner round 2026-10-05)

1. Lane A — DATA NORMALIZATION (hoopR 2016+): build the normalized game-universe spec for
   seasons 2016+ from the downloaded corpus: game identity (ESPN `game_id` primary key, one
   row per game), tip-time UTC canonicalization (`game_date_time` local-with-offset → UTC;
   `start_date` UTC twin; never the coarse `date` alone), dedupe/exclusion law
   (`status_type_completed == True`; exclude All-Star EAST/WEST pseudo-team rows; flag the
   2023+ NBA In-Season/Cup final; account postponed duplicate listings; re-derive per-season
   PLAYED counts after dedupe), and season composition splits (regular `season_type=2` /
   play-in `5` / playoffs `3`, reported separately). BDL cross-check: spot sample (≤5
   req/min, dates[] targeting, ≤ ~25 games across ≥5 seasons incl. 2016/2020/2026) verifying
   date/home/away/score/tip-UTC agreement; record match rate; any mismatch = BLOCKER-class
   finding for the data contract, not silently absorbed. PIT audit: for EVERY candidate
   feature, verify pre-game knowability (inputs frozen at prior tip); injury/roster features
   only if rights AND per-record publish timestamps are PIT-proven — else NOT_RUN_PIT.
   Re-verify spread-feature (game_spread/home_favorite) coverage across 2016+ seasons
   (measured 99.7% only on the 2026 sample). No metrics on real outcomes.
2. Lane B — MECHANISMS (NBA-adjudicated): re-adjudicate the WINPROB-NG-PREP-V1 lane C
   proposals FOR NBA 2016+ only: (a) H-C1 SOS-adjusted Elo, (b) H-C2 home/away split
   ratings, (c) H-C4 fatigue×venue interaction block (b2b_away / 3in4_away /
   travel_bucket_away / tz_shift_away), (d) F8 pace/efficiency train-only aggregates as
   rating INITIALIZATION/prior. At most 3–4 hypotheses advance to the successor protocol
   draft. Banned: additive logistic-over-Elo feature layers (dead per both terminal
   cycles), MOV/blowout-weighted Elo (re-grid of a dead family), any re-grid of
   K/HCA/rest/form on 2009–2015, 538 forecasts, closing/market odds, current-game box
   scores. Each surviving mechanism: $0 source + rights, as-of law, frozen falsifier,
   negative control (time-shuffled twin), power/capacity estimate, train-internal kill
   test. Replacement-rating shape preferred.
3. Lane C — PROTOCOL (successor scored-cycle draft): train-internal selection design
   (rolling-origin inside a TRAIN sub-window of 2016+; the 2009–2015 spent window may be
   cited but never re-scored), frozen small trial budget sketch (≤9 arms incl. B0 + frozen
   NBA B1* K=32/HCA=100 as mandatory baseline), walk-forward OOS on the NEW window,
   log loss primary + Brier/calibration slope/reliability secondary, paired date-cluster
   bootstrap uncertainty, negative controls as diagnostic arms, playoffs + play-in + Cup
   reported separately from regular season, stop rules, prospective append-only prediction
   ledger law for 2026–27+ (rows timestamped strictly before tip UTC). No outcome runs.
4. Lane D — INDEPENDENT VERIFIER (after controller synthesis; never repairs): bytes vs
   claims for every lane, rights/attribution integrity, PIT verdicts, dedupe-law
   correctness on a spot sample, BDL cross-check honesty, trial accounting (0 scored),
   registry/head/worktree/lock/clean-tree coherence, spent-window non-violation.

## Boundaries

- No scored computation, no metrics on real outcomes (schema/coverage counting and PIT
  audits are allowed; win-prob metrics are not), no S1, no paper/live, no betting, no
  purchases, no push, no merge to main, no edits to frozen artifacts/ledgers of any cycle.
- Root checkout = control plane only. Lane work in the exact worktree/branch named by the
  registry + dispatch packets. Registry writes only via researchctl (CAS); on concurrent
  modification by the parallel NFL chat: re-measure + CAS retry, never overwrite; if a
  conflict cannot be resolved, report BLOCKER.
- Language law: calibration/forecasting vocabulary only — no PnL/betting/edge language.

## Artifacts

lanes/A_DATA/ · lanes/B_MECHANISMS/ · lanes/C_PROTOCOL/ · lanes/D_VERIFY/ ·
lanes/DISPATCH/ (each lane ends with handoff JSON zcode_orch_v3_handoff@1 at its dispatch
handoff_path; lane artifacts land uncommitted, controller lands them). New data outside git
under ~/.my-quantitative-data/nba-ng-prep-v1/ (BDL spot-check outputs) — the hoopR corpus at
~/.my-quantitative-data/nba-hoopr-v1/ is EXTEND-ONLY.

## Terminal outcomes (negative-first)

PREP_COMPLETE_PENDING_OWNER_DECISIONS | BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING | TECHABORT_*.
A successor scored cycle (proposed name NBA-WINPROB-NG-SCORED-V1) may be registered later
ONLY on: this cycle's PREP_COMPLETE verdict + owner instruction + fresh registration with
data/code freeze, A7 prelaunch, and owner typed GO at that cycle's own gate. This cycle
registers no GO phrase and consumes none.
