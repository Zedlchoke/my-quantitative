# PREP SUMMARY — WINPROB-PLAYERDATA-PREP-V1 (2026-10-05)

Controller synthesis. Sources: lanes A_NBA / B_WNBA / C_NFL / R_RIGHTS artifacts + handoffs
(at lanes/DISPATCH/), independently verified by lane D (VERIFICATION_REPORT.md: VERIFIED;
0 BLOCKER, 0 MAJOR, 1 MINOR, 2 INFO) and controller spot recompute (NBA 2016 join 1317/1317,
NFL 2024 join 285/285 zero-dup, WNBA hash spot) — all reproduced.

## Verdict (cycle)

**PREP_COMPLETE_PENDING_OWNER_DECISIONS** — budget 0/0 scored (law: PREP only), S1
SEALED_UNTOUCHED, no GO phrase registered or consumed, cost $0, no push/merge, tree clean.

## Consolidated table — league × check

| Check | NBA | WNBA | NFL |
|---|---|---|---|
| Source publishes player data (official docs) | PASS — `load_nba_player_box` → sportsdataverse-data release `espn_nba_player_boxscores` (2002–2026) | PASS — wehoop stores `espn_wnba_player_boxscores`/`game_rosters` (2002–2026) | PASS — nflverse-data release `stats_player` (weekly, CURRENT; legacy `player_stats` frozen 2025-05-07) |
| Downloaded + checked (this cycle) | PASS — 3 seasons (2016/2021/2026, 16.1–17.7 MB each) + timestamps, sha256 pinned | PASS — corpus pre-existing; 50/50 files re-hash-verified vs prior cycle manifest; 0 new downloads | PASS — 7 files (week 2024/2025/2026, regpost 2025, snap_counts 2025/2026) + timestamps, sha256 pinned |
| Re-download determinism | PASS — byte-identical refetch (`cmp` 0) | PASS (prior-cycle hashes reproduce) | PASS — byte-identical refetch (week_2025) |
| Rights (repo/store license, verbatim) | PASS — data repos CC BY 4.0; store MIT | PASS — data repos CC BY 4.0; store MIT root + CC BY badge | PASS — nflverse-data CC BY 4.0 legalcode (live refetch byte-identical) |
| Underlying-data rights (ESPN/league) clarity | NOT_RUN (fail-closed: unresolved, U1–U9) | NOT_RUN (same) | NOT_RUN (same) |
| Coverage vs game universe (join on game_id) | PASS — 100% of PLAYED games (1317/1317, 1172/1172, 1326/1326; all gaps = postponed) | PASS-with-floors — player_box 93.92% of 5,988 ESPN universe (100% from 2013+; holes 2002–2004); rosters 99.92%; era 1997–2001 playerless by source | PASS — 285/285 (2024), 285/285 (2025), 63/63 (2026); 209 future games = frozen prospective law |
| Duplicates / missing / schema drift | PASS — 0 (game,athlete) dups; 57 cols identical; play-in 2021 boxes empty; 2026: 33 identity-less rows; `active` unreliable | PASS-with-findings — 1 explained dup artifact; starters=5 99.70%; drift at 2002|2003 & 2011|2012; `reason`/`active` defective semantics | PASS — 0 (player,game) dups; 150 cols zero drift 2024–2026; one-per-week placeholder rows documented |
| PIT — prior-games aggregates (as-of tip/kickoff join) | PASS — worked example reproduced (MIL 401307387, prior-5, minutes-mass 239.4) | PASS — worked example reproduced (CON 400445816, prior-5) | PASS — ET→UTC canonicalized; worked example reproduced (KC 2024, Mahomes prior-3) |
| PIT — target-game starter/active/DNP/injury | NOT_RUN_PIT (no publish timestamps) | NOT_RUN_PIT (same) | NOT_RUN_PIT (same; injuries carried blocker) |
| PIT — pbp participation (on-disk) | n/a (not used) | n/a | NOT_RUN_PIT (separate `pbp_participation` release, not fetched) |
| Feature groups designed (no runs) | PASS — minutes-mass/load; top-3 form vs own baseline; prior-2 absence | PASS — W-H2 minutes-continuity; minutes-mass; top-player form + absence proxy | PASS — QB form/availability + backup detection; skill usage mass; key-position absence proxy |
| Ancestry adjudication vs dead families | PASS-with-partial-risk — argued vs dead T1 (calendar-rest proxies barred) | PASS (W-H2 linkage) | PASS (vs B1* K40 HCA0 bar) |
| Scored computation | NOT_RUN (by law) | NOT_RUN (by law) | NOT_RUN (by law) |

## Data actually downloaded this cycle (outside git, provenance pinned)

- `~/.my-quantitative-data/playerdata-prep-v1/nba/player_box_raw/` — player_box_2016/2021/2026.csv
  (sha256 `ffd09dec…`, `86b12342…`, `7a4868da…`) + `provenance/` (licenses verbatim, release
  listing, docs, UTC-consistency + anomaly evidence) + ATTRIBUTION.md + manifest json.
- `~/.my-quantitative-data/playerdata-prep-v1/nfl/raw_stats_player/` — stats_player_week_2024/2025/2026.parquet
  (`847569d1…`, `2a461bec…`, `49bc644e…`), stats_player_regpost_2025.parquet (`44591007…`);
  `raw_snap_counts/` — snap_counts_2025/2026.parquet (`47220218…`, `fae0627d…`); ATTRIBUTION.md;
  manifests; release listing cache.
- WNBA: **no new downloads** — pre-existing 50-file corpus at
  `~/.my-quantitative-data/wnba-prep-v1/roster_audit/` hash-verified in place.

## Key laws discovered (for any successor spec)

1. NBA store season labels are ESPN ENDING-year (label 2016 = 2015-16) — matches the schedule
   corpus join but is offset vs workspace season naming; successor must pin the convention.
2. NFL weekly stats live in the `stats_player` release (auto-updating; week_2026 touched
   2026-10-05T05:30Z); `player_stats` legacy release is frozen — successors must anchor to the
   release actually used with sha256, because nflverse re-cuts whole-history files.
3. WNBA coverage floors: game-level features 2004+; minutes/DNP features 2013+; era 1997–2001
   has NO player source (union coverage ceiling 85.3%).
4. balldontlie Free = Teams/Players/Games metadata ONLY (player stats are GOAT-tier paid) —
   vendor docs quoted verbatim; the earlier "do not assume Free player stats" caution is now
   evidence-backed.
5. Target-game availability (starter/active/DNP/injury) is NOT_RUN_PIT league-wide without a
   timestamped pre-game feed; prior-games aggregates are the PIT-safe surface.

## Blockers / open items

- BLOCKER-class for commercial/publication only (not for internal PREP): underlying ESPN/NBA/
  WNBA/NFL data rights not evidenced by the CC BY 4.0 maintainer grants (U1–U9, fail-closed).
- NFL HOLD reasons: `players.parquet` GSIS↔PFR crosswalk not fetched (blocks player-level
  stats×snap joins; bucket-level joins fine); snap_counts 2026 lags stats ~3 days in-season.
- NBA minor: 2021 play-in boxes unpopulated; 2026: 33 identity-less rows; `active` unusable.
- WNBA MINOR (lane D): roster extra-game census 6,004/21 (20 ASG + 1 forfeit) vs lane-claimed
   5,997/14 — accounting-only correction; headline coverage numbers exact.

## Recommendations (feature-PREP step only — NOT a scored GO)

- NBA: **GO** (conditional on owner instruction + fresh registration).
- WNBA: **GO with conditions** (season floors + franchise-lineage keys + schema era guards).
- NFL: **HOLD** until owner decides on the crosswalk fetch (one more free download) or accepts
  bucket-level joins only.
- Any scored successor remains gated by: new cycle registration + data/code freeze + A7
  prelaunch + owner typed GO at that cycle's own gate (P-8).

## Cost

$0 (all sources free GitHub releases; no accounts; no keys; balldontlie key untouched).
