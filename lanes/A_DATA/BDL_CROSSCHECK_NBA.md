# BDL CROSS-CHECK — hoopR vs balldontlie spot sample — Lane A, NBA-WINPROB-NG-PREP-V1

Cycle NBA-WINPROB-NG-PREP-V1 · lane A_DATA · executed 2026-10-05 (UTC), $0.
Verdict up front: **22/22 MATCH (100.0%), 11 seasons 2016–2026 covered
(incl. required 2016, 2020, 2026), 0 mismatches, 0 unmatched — PASS. No
data-contract blocker.** Tip-time agreement is EXACT (Δ = 0.0 s on all 22).

## Protocol (dispatch law)

- Spot sample only: ≤25 matched games, ≥5 seasons; targeted `dates[]` queries;
  free tier 5 req/min enforced at **≥13 s spacing** between requests; no bulk
  download; no purchases.
- Key: macOS Keychain `balldontlie`/`winprob-ng` via `bdl_adapter.py`
  (copied into this lane from the T2 pattern; fail-closed; value never
  printed, never stored, never in any artifact; the Authorization header is
  not part of any recorded URL).
- Per game, five field-level checks: `date` (BDL vs hoopR local
  `game_date`), `home`, `away` (abbreviations), `score` (home+away finals),
  `tip_utc` (BDL `datetime` vs hoopR `start_date`, tolerance 60 s).
- Deterministic targets: one mid-winter date per season file, first ≤2
  completed non-exhibition games per date by `game_id`.

## Execution history (full honesty — three runs, one script bug found and fixed)

1. **Run 1 (11 requests, all HTTP 404)** — script defect, NOT a BDL failure:
   the URL pattern doubled the `/v1` prefix (`.../v1/v1/games?...`) because
   `BDLClient.base` already ends in `/v1`. Diagnosed with 5 further requests
   (path/param probes; `/v1/teams` returned 200 with correct data → path +
   auth fine). Total 16 requests consumed, all ≥13 s apart.
2. **Run 2 (9 requests, 25 games, 9 seasons 2016–2024)**: 16 MATCH /
   0 MISMATCH / 9 UNMATCHED. Diagnosis of the 9: ALL involved exactly the
   franchises whose abbreviations differ between the two sources
   (hoopR `NY, NO, WSH, GS, UTAH, SA` vs BDL `NYK, NOP, WAS, GSW, UTA, SAS`).
   These were matcher false negatives, not data disagreements. The 25-game
   cap also consumed the budget before the 2026 season was queried — a
   protocol-coverage failure, so the run was superseded.
3. **Run 3 FINAL (11 requests, 22 games, 11 seasons)**: abbreviation
   normalization added, 2 games/date so every season fits under the cap.
   **Result: 22/22 MATCH, 0 MISMATCH, 0 UNMATCHED.**

Grand total this session: 36 BDL requests (16 + 9 + 11), every one ≥13 s
apart, all targeted `dates[]` queries — spot-sample etiquette held.

## Final run — request log (URL patterns; key never in URLs)

| season | query (path relative to `https://api.balldontlie.io/v1`) | HTTP | BDL games returned | hoopR games that date |
|---|---|---|---:|---:|
| 2016 | `/games?dates[]=2015-12-18` | 200 | 12 | 12 |
| 2017 | `/games?dates[]=2016-12-23` | 200 | 14 | 14 |
| 2018 | `/games?dates[]=2017-12-22` | 200 | 9 | 9 |
| 2019 | `/games?dates[]=2018-11-16` | 200 | 8 | 8 |
| 2020 | `/games?dates[]=2019-12-20` | 200 | 10 | 10 |
| 2021 | `/games?dates[]=2021-01-08` | 200 | 10 | 10 |
| 2022 | `/games?dates[]=2021-12-18` | 200 | 7 | 7 |
| 2023 | `/games?dates[]=2022-11-25` | 200 | 14 | 14 |
| 2024 | `/games?dates[]=2023-12-18` | 200 | 11 | 11 |
| 2025 | `/games?dates[]=2024-12-23` | 200 | 14 | 14 |
| 2026 | `/games?dates[]=2025-12-20` | 200 | 10 | 10 |

BDL's per-date coverage equals hoopR's completed-game count on every probed
date (12/12, 14/14, 9/9, 8/8, 10/10, 10/10, 7/7, 14/14, 11/11, 14/14, 10/10)
— an additional structural agreement beyond the 22 sampled games.

## Field-level results (final run)

22/22 games PASS on all five checks:
- `date`: 22/22 equal to hoopR local `game_date`.
- `home`/`away`: 22/22 (after the abbreviation map above; the map is now a
  REQUIRED constant for any future BDL consumer — hoopR is the deviant side).
- `score`: 22/22 exact (both final scores).
- `tip_utc`: 22/22 EXACT — measured delta 0.0 s on every game (tolerance
  allowed 60 s). Two independent sources agreeing on the UTC instant to the
  second across 2015-2025 tips, spanning DST boundaries, is strong evidence
  the §2 tip law of the game-universe spec is the true tip instant.

Match rate **22/22 = 100.0%** (within-sample; the two source systems agree on
date, home, away, score, and tip for every sampled game).

## Verdict

- **PASS — no BLOCKER.** No field-level disagreement was observed anywhere in
  22 games across 11 seasons; the two "failures" during execution were lane
  tooling defects (path bug, abbreviation matcher), both found, root-caused,
  fixed, and documented here — nothing was silently absorbed.
- BDL remains CROSS-CHECK ONLY (spot `dates[]` queries); hoopR stays PRIMARY
  (CC BY 4.0, no rate limit, full PBP).
- Known limitation: spot sample ≠ full audit; free-tier quota makes a
  full-population cross-check out of scope for this PREP cycle.

## Artifacts

- Aggregate: `lanes/A_DATA/BDL_CROSSCHECK_A_DATA.json` (final run; schema
  `bdl_crosscheck_a_data@1`).
- Redacted per-date responses: `~/.my-quantitative-data/nba-ng-prep-v1/bdl_spotcheck/resp_{season}_{date}.json` (11 files).
- Script: `lanes/A_DATA/bdl_crosscheck_a_data.py`; adapter:
  `lanes/A_DATA/bdl_adapter.py`.
- Prior-cycle evidence (read-only, superseded only in scope): T2c 5/5 MATCH
  at `.worktrees/winprob-ng-prep-v1/integration/lanes/T2_BDL_ADAPTER/`.
