# VERDICT_TABLE — WINPROB-PLAYERDATA-PREP-V1 lane R (RIGHTS)

- Date: 2026-10-05. Verdict values: **PASS** = verbatim verified with source URL + retrieval
  UTC timestamp (raw bytes archived under `fetches/`, register in `fetch_log.txt`);
  **FAIL** = contradiction found between fetched official text and the claim; **NOT_RUN** =
  could not fetch (error recorded).
- For "underlying-rights clarity": the fetch itself always succeeded or failed; the rights
  question is answered `ack=Y` (repo acknowledges provenance) / `grant=N` (no upstream
  rights grant or ToS clearance exists in any fetched document) — an honest "clarity"
  verdict means we know exactly what remains unclear (see UNCLEAR_POINTS.md). No FAIL was
  found anywhere: every prior-cycle license claim re-verified verbatim.

| Source | Repo license | Store/distribution license | Underlying-rights clarity | Evidence |
|---|---|---|---|---|
| sportsdataverse/hoopR (code) | **PASS** — MIT verbatim, "Copyright (c) 2020 hoopR authors", raw LICENSE.md HTTP 200, 2026-10-05T07:17:01Z | n/a (code pkg; points to sportsdataverse-data) | ack=Y (ESPN + NBA Stats API + sportsdataverse-data named in README HTTP 200 07:17:01Z); grant=N | RIGHTS_MATRIX §1 |
| sportsdataverse/hoopR-nba-data (ESPN NBA producer; `espn_nba_player_boxscores`) | **PASS** — CC BY 4.0 verbatim covering "data, code, and documentation", "Copyright (c) 2026 hoopR.nba authors", HTTP 200, 07:17:31Z | **PASS** — publishes to sportsdataverse-data releases (store row below); README workflow diagram HTTP 200 07:17:31Z | ack=Y (ESPN-sourced datasets named); grant=N — ESPN ToS unexamined/unchecked | RIGHTS_MATRIX §2 |
| sportsdataverse/hoopR-nba-stats-data (stats.nba.com producer; `nba_stats_player_boxscores`/`player_game_logs`/`player_season_stats`) | **PASS** — CC BY 4.0 verbatim, "Copyright (c) 2026 hoopR.nba.stats authors", HTTP 200, 07:17:32Z | **PASS** — sportsdataverse-data release tags enumerated in README HTTP 200 07:17:33Z | ack=Y (verbatim node "S[stats.nba.com]-->A[hoopR-nba-stats-raw]"); grant=N — NBA.com ToU unexamined | RIGHTS_MATRIX §3 |
| sportsdataverse/wehoop (code) | **PASS** — MIT verbatim, "Copyright (c) 2026 wehoop authors", HTTP 200, 07:18:01Z | n/a | ack=Y (ESPN WNBA wrappers; `load_*` from sportsdataverse-data); grant=N | RIGHTS_MATRIX §4 |
| sportsdataverse/wehoop-wnba-data (ESPN WNBA producer; `espn_wnba_player_boxscores`, `espn_wnba_game_rosters`) | **PASS** — CC BY 4.0 verbatim, "Copyright (c) 2026 wehoop.wnba authors", HTTP 200, 07:18:41Z | **PASS** — sportsdataverse-data releases (corpus tags `espn_wnba_team_boxscores`, `espn_wnba_game_rosters`, `wnba_crosswalk` per prior lane-A manifest, re-read 2026-10-05) | ack=Y (ESPN WNBA API); grant=N — ESPN/WNBA terms unexamined | RIGHTS_MATRIX §4 |
| sportsdataverse/wehoop-wnba-stats-data (stats.wnba.com producer) | **PASS** — CC BY 4.0 verbatim, "Copyright (c) 2026 wehoop.wnbastats authors", HTTP 200, 07:18:42Z | **PASS** — sportsdataverse-data releases (wehoop README badge table) | ack=Y (WNBA Stats API side); grant=N | RIGHTS_MATRIX §4 |
| sportsdataverse/sportsdataverse-data (distribution store) | n/a (store) | **PASS** (dual marker, both verbatim): root LICENSE = MIT "Copyright (c) 2023 SportsDataverse" HTTP 200 07:18:03Z; README license badge = CC BY 4.0 linking creativecommons.org/licenses/by/4.0/, HTTP 200 07:18:04Z. NOTICE/NOTICE.md = 404 (07:22:42Z/43Z). LICENSE.md path = 404. | ack=Y (store README names producers + "nflverse-parity NFL loaders read the nflverse-data releases instead"); grant=N (no per-tag rights statement) | RIGHTS_MATRIX §6 |
| nflverse/nflverse-data (+ nflfastR reference) | **PASS** — CC BY 4.0 full legalcode verbatim at LICENSE.md (18,651 bytes) HTTP 200 07:18:05Z; `LICENSE` path 404. nflfastR code LICENSE header "YEAR: 2020 / COPYRIGHT HOLDER: Sebastian Carl; Ben Baldwin" HTTP 200 07:19:26Z | n/a — nflverse-data IS the store (README verbatim: "This repository holds automated data releases for nflverse projects") HTTP 200 07:19:27Z | ack=partial (nflfastR README credits third-party sources; **no league-affiliation/ToS disclaimer present at HEAD** — verified absent, 0 grep hits); grant=N — NFL rights unexamined | RIGHTS_MATRIX §5 |
| CC BY 4.0 deed (attribution requirements) | **PASS** — deed fetched creativecommons.org/licenses/by/4.0/ HTTP 200 07:19:27Z; attribution/clause text quoted verbatim | n/a | n/a | RIGHTS_MATRIX §7 |
| balldontlie Free tier (NBA/NFL/WNBA docs) | **PASS** — tier tables fetched from public docs, no key/signup: NBA docs root 200 07:20:47Z; NFL 200 07:22:10Z; WNBA 200 07:22:11Z; `balldontlie.io/pricing` = 404 07:20:47Z | n/a | grant=N (vendor ToS/license of balldontlie data not fetched — recorded UNCLEAR) | BALLDONTLIE_FREE.md |

## Summary of contradictions: NONE

Every prior-cycle claim re-verified verbatim:
1. hoopR-family data repos LICENSE.md = CC BY 4.0 "data, code, and documentation" — CONFIRMED.
2. sportsdataverse-data root LICENSE = MIT "Copyright (c) 2023 SportsDataverse" — CONFIRMED
   (plus new finding: README badge = CC BY 4.0 for the data; no NOTICE file).
3. nflverse-data CC BY 4.0 — CONFIRMED (full legalcode; file is LICENSE.md, LICENSE 404s).
4. WNBA corpus release store — CONFIRMED at sportsdataverse-data tags produced by
   wehoop-wnba-data / wehoop-wnba-stats-data (both CC BY 4.0).
5. balldontlie Free = Teams/Players/Games only — CONFIRMED on all three sports docs pages
   with verbatim tier tables; "Game Player Stats"/"Stats"/"Player Stats" = No on Free.

NOT_RUN items (recorded with errors):
- `https://raw.githubusercontent.com/sportsdataverse/sportsdataverse-data/HEAD/LICENSE.md` → HTTP 404 (expected; root LICENSE exists).
- `https://raw.githubusercontent.com/nflverse/nflverse-data/HEAD/LICENSE` → HTTP 404 (operative file is LICENSE.md).
- `https://balldontlie.io/pricing` → HTTP 404 (tier page lives in each sport's docs "Account Tiers" section).
- `NOTICE`, `NOTICE.md` in sportsdataverse-data → HTTP 404 (no consolidated notice exists).

Standing caveats: all "grant=N" rows mean the CC BY 4.0 grants are maintainer grants over
repo contents; no upstream league/ESPN rights clearance exists in any fetched document.
See UNCLEAR_POINTS.md (U1–U9) before any publication or commercial use.
