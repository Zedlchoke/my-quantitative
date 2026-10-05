# PLAN — WNBA-WINPROB-PREP-V1 (independent WNBA win-prob research PREP, $0)

- cycle_id: WNBA-WINPROB-PREP-V1 · asset: shared · ACTIVE_LIGHT, budget 0 scored, NO GO phrase
- owner authority 2026-10-05 (NBA+WNBA coordination chat): research/PREP + bookkeeping ONLY —
  explicitly NOT a GO for any scored cycle and NOT authority to run any metric on real WNBA
  outcomes. No S1/paper/live/betting/data purchases/push/merge. NFL-WINPROB-NG-PREP-V1 runs
  in a different owner chat: untouched here; coordination is limited to the shared registry
  (CAS, never overwrite). Frozen sources, results, and ledgers of every prior cycle
  (incl. WINPROB-NG-PREP-V1) are immutable history — this cycle never edits them.

## Independence law (load-bearing)

- WNBA is a FRESH program on its OWN data. No NBA data, hypothesis, parameter, or verdict is
  WNBA evidence. NBA numbers may be CITED as cross-league context, never imported as proof.
- The spent-window prohibition (NBA 2009–2015) does NOT bind WNBA windows, but the same
  train-only discipline does: every WNBA parameter (fresh K/HCA/…) is selected train-internal
  and frozen before any evaluation look.
- WNBA evidence base (WINPROB-NG-PREP-V1 lane B, verified by its lane D): wehoop/sportsdataverse
  release store is the PRIMARY (rights: CC BY 4.0 badge on the release-store repo + MIT code
  license, nflverse-family pattern; internal research + attribution; no direct scraping of
  wnba.com / stats.wnba.com / ESPN; Sports Reference FAIL 5(11); balldontlie WNBA
  BLOCKED_NO_KEY/paid). Downloaded outside git at ~/.my-quantitative-data/wnba-v1/ (99 files,
  74.6 MB, sha256 manifest + ATTRIBUTION.md): ESPN schedules 2002–2026 (6,029 games), stats-side
  schedules 1997–2026 (7,009 games), 2025 sample team/player box + pbp. EXTEND ONLY.

## Tasks (owner round 2026-10-05)

1. Lane A — DATA NORMALIZATION (WNBA 1997+): build the normalized game-universe spec from the
   downloaded corpus: game identity (per-source primary keys + join law via display_name /
   `wnba_crosswalk` release — NEVER raw ESPN abbreviations, measured unreliable pre-2011);
   timestamp canonicalization across the 4 measured flavors (ESPN schedule UTC instant; ESPN
   box venue-local-with-offset; ESPN pbp UTC `wallclock`; stats-side naive local date) into
   one canonical tip-UTC law; franchise rename/relocation map verified from the data (Starzz→
   San Antonio→Dallas; Miracle→Connecticut; Shock Detroit→Tulsa→(merged) Dallas; Sparks→
   (stays LA) vs Utah→San Antonio note; San Antonio→Las Vegas 2018; defunct Charlotte/
   Cleveland/Houston/Sacramento/Miami/Portland; expansion Atlanta 2008, Chicago 2006,
   Golden State 2025, Toronto+Portland 2026); exclusion/filter law (`status_type_state=='post'`;
   drop Forfeit/Postponed details; drop or separately flag All-Star alias rows EAST/WEST/ALL/
   DEL/PAR/CLA/COOP/WNBASTARS; drop TBD if-necessary placeholders; NEVER filter on score
   presence — unplayed rows are pre-filled 0–0; the single 2018-08-03 forfeit recorded 0–0;
   2020 Wubble 147 games is a real season); neutral-site flag handling (15 rows 2013–2026);
   Commissioner's Cup games embedded in regular season (2021+) — flag, separate report;
   playoffs (`season_type=3`) separate. Coverage census per season 1997–2026 with the
   ESPN-vs-stats reconciliation (small diffs = All-Star/placeholder noise). Extend the 2025
   sample toward the seasons the successor protocol will need (full-history PBP ≈ +1.0 GB is
   OPTIONAL and owner-budget-bound: default is schedules + a box/pbp depth census per era,
   NOT a full mirror). PIT audit: release assets are current-state snapshots with NO
   publication-time columns — every feature must be built pre-game-safe (rolling windows on
   canonical game date with strictly-prior-game inputs); injury/lineup features stay
   NOT_RUN_PIT unless a rights-verified archive with real publish timestamps is proven
   (player_box active/DNP/starter fields are POST-GAME facts — never pre-game features).
2. Lane B — MECHANISMS (fresh WNBA program): adjudicate proposals for a FRESH league:
   (a) fresh WNBA Elo baseline with own train-only K/HCA selection (new league — the NBA's
   frozen K=32/HCA=100 is a STARTING POINT to cite, not a WNBA law); (b) H-C5
   continuity-modulated rating carryover (roster-continuity × offseason rating retention —
   PIT-safe from season-start rosters; requires roster coverage check via
   `espn_wnba_game_rosters`/player_box); (c) at most ONE additional mechanism with a clear
   domain basis specific to WNBA structure (short season, high churn) if it survives
   mechanism-first scrutiny. Banned: additive logistic-over-Elo layers (dead shape per both
   terminal cycles), MOV-weighted Elo re-grid, 538 forecasts, closing/market odds,
   current-game box scores, any NBA-derived parameter presented as WNBA evidence. Each
   hypothesis: $0 source + rights, as-of law, frozen falsifier, negative control,
   capacity/power estimate (≈220–260 regular games/season pre-2025, 312 in 2025, 360-row
   2026 incl. placeholders), train-internal kill test.
3. Lane C — PROTOCOL (successor scored-cycle draft): fresh WNBA split design (train-internal
   rolling-origin selection inside TRAIN; walk-forward OOS on held-out recent seasons;
   1997–2001 stats-side-only era handled explicitly — either excluded from feature arms or
   schedules-only baseline arms, chosen and frozen in the protocol), frozen small trial
   budget sketch (≤9 arms incl. WNBA B0 + fresh WNBA B1), log loss primary + Brier/
   calibration slope secondary, paired date-cluster bootstrap uncertainty, playoffs/Cup/
   All-Star separate, negative controls as diagnostic arms, stop rules, prospective
   append-only prediction ledger law for future seasons (rows timestamped strictly before
   tip UTC). No outcome runs.
4. Lane D — INDEPENDENT VERIFIER (after controller synthesis; never repairs): bytes vs
   claims, rights/attribution integrity, PIT verdicts (incl. the 0–0/forfeit/placeholder
   filter law on a spot sample), rename-map correctness, timestamp canonicalization on
   sampled rows, trial accounting (0 scored), registry/head/worktree/lock/clean-tree
   coherence, independence law (no NBA evidence imported).

## Boundaries

- No scored computation, no metrics on real outcomes (schema/coverage counting and PIT
  audits allowed; win-prob metrics are not), no S1, no paper/live, no betting, no purchases,
  no push, no merge to main, no edits to frozen artifacts/ledgers of any cycle.
- Root checkout = control plane only. Lane work in the exact worktree/branch named by the
  registry + dispatch packets. Registry writes only via researchctl (CAS); on concurrent
  modification by the parallel NFL chat: re-measure + CAS retry, never overwrite; if a
  conflict cannot be resolved, report BLOCKER.
- Language law: calibration/forecasting vocabulary only — no PnL/betting/edge language.

## Artifacts

lanes/A_DATA/ · lanes/B_MECHANISMS/ · lanes/C_PROTOCOL/ · lanes/D_VERIFY/ ·
lanes/DISPATCH/ (each lane ends with handoff JSON zcode_orch_v3_handoff@1 at its dispatch
handoff_path; lane artifacts land uncommitted, controller lands them). New data outside git
under ~/.my-quantitative-data/wnba-prep-v1/ (extensions/audits) — the corpus at
~/.my-quantitative-data/wnba-v1/ is EXTEND-ONLY.

## Terminal outcomes (negative-first)

PREP_COMPLETE_PENDING_OWNER_DECISIONS | BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING | TECHABORT_*.
A successor scored cycle (proposed name WNBA-WINPROB-SCORED-V1) may be registered later ONLY
on: this cycle's PREP_COMPLETE verdict + owner instruction + fresh registration with
data/code freeze, A7 prelaunch, and owner typed GO at that cycle's own gate. This cycle
registers no GO phrase and consumes none.
