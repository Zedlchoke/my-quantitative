# RIGHTS_MATRIX — WINPROB-PLAYERDATA-PREP-V1 lane R (RIGHTS, cross-league)

- Cycle: WINPROB-PLAYERDATA-PREP-V1 · Lane: R_RIGHTS · Date: 2026-10-05
- Method: verbatim quotes fetched live from official sources (raw.githubusercontent.com /
  creativecommons.org / balldontlie public docs pages) on 2026-10-05, HTTP status + UTC
  timestamp per fetch recorded in `fetch_log.txt`, raw bytes archived under `fetches/`.
  Small text files only (LICENSE/README/docs pages). No datasets downloaded, no API keys,
  no accounts, $0.
- Scope note: this is internal research documentation, NOT legal advice. "UNCLEAR" means
  fail-closed: treat as NOT PERMITTED for publication/commercial use until an owner/legal
  decision resolves it.
- Key structural finding: for the SportsDataverse family, the **R code packages are MIT**
  and the **data producer repos are CC BY 4.0** ("data, code, and documentation"), while
  the **distribution store** (`sportsdataverse/sportsdataverse-data`) carries a root MIT
  LICENSE file for the store's own code plus a CC BY 4.0 badge on its README for the
  releases it hosts. The load-bearing license for any player-data corpus is therefore the
  **producer repo's CC BY 4.0 LICENSE.md**, not the store's MIT file.

---

## 1. sportsdataverse/hoopR (R code package)

| Q | Finding |
|---|---|
| (a) data license of releasing repo | hoopR itself releases **code**; its data releases are produced by separate repos (see rows 2–3). Code license = **MIT**: |
| | Source: https://raw.githubusercontent.com/sportsdataverse/hoopR/HEAD/LICENSE.md — HTTP 200 — retrieved 2026-10-05T07:17:01Z |
| | ```\n# MIT License\n\nCopyright (c) 2020 hoopR authors\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n``` |
| (b) license of distribution store | Releases are published to `sportsdataverse/sportsdataverse-data` (see row 6). |
| (c) attribution requirement | MIT: retain copyright + permission notice in copies of the software. Data attribution: see rows 2–3 (CC BY 4.0). |
| (d) share-alike? | No (MIT; CC BY 4.0 is attribution-only, not share-alike). |
| (e) commercial-use restriction | MIT text grants right to "sell" copies of the Software. Data-side commercial terms: CC BY 4.0 permits commercial use (row 2/3); underlying-league rights UNCLEAR. |
| (f) underlying-data provenance | README (https://raw.githubusercontent.com/sportsdataverse/hoopR/HEAD/README.md, HTTP 200, 2026-10-05T07:17:01Z): "access **live play by play and box score** data from ESPN"; "full NBA Stats API wrapper"; "`load_nba_*()` / `load_mbb_*()` / `load_ncaa_mbb_*()` bulk-data loaders backed by the `sportsdataverse-data` release repos"; data-status table rows: "NBA (ESPN)" → `sportsdataverse/hoopR-nba-data`, "NBA Stats API" → `sportsdataverse/hoopR-nba-stats-data`. Acknowledges ESPN / stats.nba.com as sources. |
| (g) UNCLEAR | Underlying ESPN / NBA.com data rights (ToS of scraped endpoints) are NOT addressed anywhere in the fetched LICENSE/README. No league-affiliation disclaimer present in hoopR README at HEAD. |

## 2. sportsdataverse/hoopR-nba-data (NBA ESPN producer repo — NBA player box scores)

| Q | Finding |
|---|---|
| (a) data license | **CC BY 4.0, verbatim, covering "data, code, and documentation"** — this is the repo hoopR's docs point to for ESPN NBA data incl. `espn_nba_player_boxscores`. |
| | Source: https://raw.githubusercontent.com/sportsdataverse/hoopR-nba-data/HEAD/LICENSE.md — HTTP 200 — retrieved 2026-10-05T07:17:31Z |
| | ```\n# Creative Commons Attribution 4.0 International (CC BY 4.0)\n\nCopyright (c) 2026 hoopR.nba authors\n\nThe contents of this repository (data, code, and documentation) are licensed\nunder the Creative Commons Attribution 4.0 International License (CC BY 4.0).\n\nYou are free to:\n\n- **Share** — copy and redistribute the material in any medium or format\n- **Adapt** — remix, transform, and build upon the material for any purpose,\n  even commercially\n\nUnder the following terms:\n\n- **Attribution** — You must give appropriate credit, provide a link to the\n  license, and indicate if changes were made. You may do so in any reasonable\n  manner, but not in any way that suggests the licensor endorses you or your\n  use.\n\nNo additional restrictions — You may not apply legal terms or technological\nmeasures that legally restrict others from doing anything the license\npermits.\n\nThe full license text is available at:\n<https://creativecommons.org/licenses/by/4.0/legalcode>\n\nA human-readable summary is available at:\n<https://creativecommons.org/licenses/by/4.0/>\n``` |
| (b) distribution store | `sportsdataverse/sportsdataverse-data` releases (README workflow diagram: producer repo → release store). See row 6. |
| (c) attribution | CC BY 4.0: appropriate credit + license link + indicate changes; not in a way suggesting endorsement (see §9 deed). |
| (d) share-alike? | No — CC BY, not CC BY-SA. |
| (e) commercial use | License text itself says "even commercially" — no commercial restriction in the CC grant. |
| (f) underlying provenance | README (https://raw.githubusercontent.com/sportsdataverse/hoopR-nba-data/HEAD/README.md, HTTP 200, 2026-10-05T07:17:31Z) workflow diagram lists datasets `espn_nba_player_boxscores`, `espn_nba_team_boxscores`, `espn_nba_pbp`, `espn_nba_game_rosters`, `espn_nba_rosters`, `espn_nba_player_season_stats`, `espn_nba_shots`, etc.; scraper pipeline `scripts/daily_nba_scraper.sh` → `python/espn_nba_*.py`. ESPN provenance acknowledged by dataset naming + pipeline naming. |
| (g) UNCLEAR | Whether ESPN's own terms permit commercial downstream redistribution of ESPN-derived tables. The repo grants CC BY 4.0 over *its* contents; it is silent on ESPN's rights (no ToS statement, no disclaimer). Also: whether "data, code, and documentation" in the CC grant covers ESPN-originated statistics as a matter of law (facts/data copyrightability) is not resolved by the license text. |

## 3. sportsdataverse/hoopR-nba-stats-data (NBA stats.nba.com producer repo)

| Q | Finding |
|---|---|
| (a) data license | **CC BY 4.0, verbatim** ("data, code, and documentation"). |
| | Source: https://raw.githubusercontent.com/sportsdataverse/hoopR-nba-stats-data/HEAD/LICENSE.md — HTTP 200 — retrieved 2026-10-05T07:17:32Z |
| | ```\n# Creative Commons Attribution 4.0 International (CC BY 4.0)\n\nCopyright (c) 2026 hoopR.nba.stats authors\n\nThe contents of this repository (data, code, and documentation) are licensed\nunder the Creative Commons Attribution 4.0 International License (CC BY 4.0).\n``` (remainder identical in structure to row 2's quote: Share / Adapt even commercially / Attribution terms / No additional restrictions / links to legalcode + deed) |
| (b) distribution store | `sportsdataverse/sportsdataverse-data` releases (release tags listed in README, e.g. `nba_stats_player_boxscores`, `nba_stats_player_game_logs`, `nba_stats_player_season_stats`, each linking to sportsdataverse-data releases; README table "Last published" dates incl. 2026-10-01). |
| (c) attribution | CC BY 4.0 as row 2. |
| (d) share-alike? | No. |
| (e) commercial use | CC text permits "even commercially"; underlying stats.nba.com rights UNCLEAR. |
| (f) underlying provenance | README (https://raw.githubusercontent.com/sportsdataverse/hoopR-nba-stats-data/HEAD/README.md, HTTP 200, 2026-10-05T07:17:33Z) workflow diagram, verbatim node: "```S[stats.nba.com]-->A[hoopR-nba-stats-raw]```"; datasets `nba_stats_player_boxscores`, `nba_stats_player_game_logs`, `nba_stats_player_season_stats`. stats.nba.com provenance acknowledged. |
| (g) UNCLEAR | stats.nba.com Terms of Use (NBA.com) are NOT quoted or acknowledged by the repo; whether NBA permits commercial redistribution of stats.nba.com-derived player box scores is UNCLEAR (fail-closed). |

## 4. sportsdataverse/wehoop (R code package) + WNBA producer repos

| Q | Finding |
|---|---|
| (a) data license of releasing repo | wehoop code = **MIT**: |
| | Source: https://raw.githubusercontent.com/sportsdataverse/wehoop/HEAD/LICENSE.md — HTTP 200 — retrieved 2026-10-05T07:18:01Z |
| | ```\n# MIT License\n\nCopyright (c) 2026 wehoop authors\n``` (remainder = standard MIT grant incl. "and/or sell") |
| | WNBA data producer repos (the ones behind the on-disk WNBA player_box / game_rosters corpus): **CC BY 4.0 verbatim**. |
| | Source: https://raw.githubusercontent.com/sportsdataverse/wehoop-wnba-data/HEAD/LICENSE.md — HTTP 200 — retrieved 2026-10-05T07:18:41Z |
| | ```\n# Creative Commons Attribution 4.0 International (CC BY 4.0)\n\nCopyright (c) 2026 wehoop.wnba authors\n\nThe contents of this repository (data, code, and documentation) are licensed\nunder the Creative Commons Attribution 4.0 International License (CC BY 4.0).\n``` (Share/Adapt-even-commercially/Attribution/No-additional-restrictions, same structure as row 2) |
| | Source: https://raw.githubusercontent.com/sportsdataverse/wehoop-wnba-stats-data/HEAD/LICENSE.md — HTTP 200 — retrieved 2026-10-05T07:18:42Z |
| | ```\n# Creative Commons Attribution 4.0 International (CC BY 4.0)\n\nCopyright (c) 2026 wehoop.wnbastats authors\n``` (same CC BY 4.0 body) |
| (b) distribution store | wehoop README (https://raw.githubusercontent.com/sportsdataverse/wehoop/HEAD/README.md, HTTP 200, 2026-10-05T07:18:02Z) data-status table: "WNBA (ESPN)" → `sportsdataverse/wehoop-wnba-data`; "WNBA Stats API" → `sportsdataverse/wehoop-wnba-stats-data`; both publish to `sportsdataverse/sportsdataverse-data` releases (see row 6). NOTE vs dispatch packet: the WNBA corpus assets were pulled from **sportsdataverse/sportsdataverse-data** release tags (`espn_wnba_team_boxscores`, `espn_wnba_game_rosters`, `wnba_crosswalk` — see read-only WNBA-WINPROB-PREP-V1 lane-A DOWNLOAD_MANIFEST), which are produced by `wehoop-wnba-data`. |
| (c) attribution | CC BY 4.0 for data; MIT notice retention for wehoop code. |
| (d) share-alike? | No. |
| (e) commercial use | CC text permits "even commercially"; underlying-league rights UNCLEAR. |
| (f) underlying provenance | wehoop-wnba-data README (https://raw.githubusercontent.com/sportsdataverse/wehoop-wnba-data/HEAD/README.md, HTTP 200, 2026-10-05T07:18:41Z): "wehoop ESPN WNBA workflow diagram" with datasets `espn_wnba_player_boxscores`, `espn_wnba_game_rosters`, `espn_wnba_pbp`, `espn_wnba_shots`, etc. (ESPN WNBA API). wehoop-wnba-stats-data = stats.wnba.com side (tag family `wnba_stats_*` per wehoop README badge table). wehoop README also documents ESPN endpoint wrappers and `load_wnba_*` release datasets. |
| (g) UNCLEAR | ESPN and stats.wnba.com (WNBA/league) terms for downstream/commercial redistribution are not addressed by any fetched document. Whether the CC BY 4.0 grant by the repo owner can lawfully extend to league-originated statistics is UNCLEAR (fail-closed). |

## 5. nflverse/nflverse-data (+ nflverse/nflfastR reference)

| Q | Finding |
|---|---|
| (a) data license of releasing repo | **CC BY 4.0 — full legalcode verbatim** at LICENSE.md (the `LICENSE` path 404s; LICENSE.md is the operative file). |
| | Source: https://raw.githubusercontent.com/nflverse/nflverse-data/HEAD/LICENSE.md — HTTP 200 — retrieved 2026-10-05T07:18:05Z — 18,651 bytes. Title block verbatim: |
| | ```\nAttribution 4.0 International\n\n=======================================================================\n\nCreative Commons Corporation ("Creative Commons") is not a law firm and\ndoes not provide legal services or legal advice.\n...\nCreative Commons Attribution 4.0 International Public License\n``` |
| | (Full CC BY 4.0 legalcode; archiving a copy exists read-only at `~/.my-quantitative-data/nfl-ng-prep-v1/rights/nflverse-data_LICENSE.md` from prior cycle — upstream re-verified live here.) |
| (b) distribution store | nflverse-data IS the release store for nflverse projects. README (https://raw.githubusercontent.com/nflverse/nflverse-data/HEAD/README.md, HTTP 200, 2026-10-05T07:19:27Z) verbatim: "This repository holds automated data releases for nflverse projects (i.e. all of the data powered/scraped via GitHub Actions)." No separate distribution store; LICENSE.md at root governs the repo. |
| (c) attribution | CC BY 4.0 attribution terms (see §9 deed). |
| (d) share-alike? | No. |
| (e) commercial use | CC text permits "even commercially". nflverse-data README carries NO additional usage restrictions, no ToS statement, no league-affiliation disclaimer. |
| (f) underlying provenance | nflfastR README (https://raw.githubusercontent.com/nflverse/nflfastR/HEAD/README.md, HTTP 200, 2026-10-05T07:19:27Z) verbatim: "`nflfastR` is a set of functions to efficiently scrape NFL play-by-play data"; "we recommend downloading the data from [nflverse-data pbp releases] or using the `nflreadr` package"; special-thanks section credits Nick Shoemaker's JSON-formatted NFL play-by-play source for 1999–2000 and FTN Fantasy charting data for scramble marking. **The README at HEAD contains NO "not affiliated with the NFL" disclaimer and no ToS reference** — the underlying NFL (GSIS/NFL.com) data-rights status is not acknowledged. nflfastR code LICENSE header (short usethis form): "YEAR: 2020 / COPYRIGHT HOLDER: Sebastian Carl; Ben Baldwin" (https://raw.githubusercontent.com/nflverse/nflfastR/HEAD/LICENSE, HTTP 200, 2026-10-05T07:19:26Z). |
| (g) UNCLEAR | NFL/Next Gen Stats data rights, and whether commercial redistribution of nflverse-derived player tables is permissible under NFL IP/ToS — not addressed by any fetched document (fail-closed). |

## 6. sportsdataverse/sportsdataverse-data (distribution store)

| Q | Finding |
|---|---|
| (a) releasing repo data license | The store hosts the release assets produced by the CC BY 4.0 producer repos (rows 2, 3, 4). |
| (b) store license — **two markers, both verified verbatim** | (i) Root **LICENSE file = MIT**: |
| | Source: https://raw.githubusercontent.com/sportsdataverse/sportsdataverse-data/HEAD/LICENSE — HTTP 200 — retrieved 2026-10-05T07:18:03Z |
| | ```\nMIT License\n\nCopyright (c) 2023 SportsDataverse\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n``` |
| | (ii) **README license badge = CC BY 4.0**: Source: https://raw.githubusercontent.com/sportsdataverse/sportsdataverse-data/HEAD/README.md — HTTP 200 — retrieved 2026-10-05T07:18:04Z (292,938 bytes; README.md is generated from README.Rmd). Badge verbatim: |
| | ```\n[![License: CC\nBY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-blue.svg?style=flat-square)](https://creativecommons.org/licenses/by/4.0/)\n``` |
| | README self-description verbatim: "This repository is the **release store** of the [SportsDataverse]: the `load_*()` functions in the SportsDataverse R packages and in `sportsdataverse-py` read their data from the GitHub releases published here (the nflverse-parity NFL loaders read the nflverse-data releases instead)." |
| | Interpretation (documented, not legal advice): MIT LICENSE = the store repo's own code; CC BY 4.0 badge + per-producer LICENSE.md = the data in the releases. NO consolidated NOTICE file exists (NOTICE and NOTICE.md both HTTP 404, retrieved 2026-10-05T07:22:42Z/07:22:43Z); the README does not enumerate per-repo licenses — each producer repo carries its own CC BY 4.0 LICENSE.md. |
| (c) attribution | CC BY 4.0 per producer repo (rows 2–4). MIT copyright notice for store code if reused. |
| (d) share-alike? | No. |
| (e) commercial use | CC BY 4.0 grant says "even commercially"; no additional restriction found in store README. Underlying-league rights UNCLEAR (rows 2–4). |
| (f) underlying provenance | Store README tables list every release tag with its producer (e.g. `espn_*` tags from ESPN-based producers; `nba_stats_*` from hoopR-nba-stats-data/stats.nba.com; `wnba_crosswalk`, `espn_wnba_*` from wehoop-wnba-data). Provenance acknowledged at the naming level; no rights statement per source. |
| (g) UNCLEAR | No document in the store states which license governs which asset subdirectory/tag beyond the badge; the dual MIT-root + CC-badge pattern relies on inference from per-repo LICENSE.md files. For publication, attribute per producer repo and keep the store badge citation; treat anything beyond that as UNCLEAR. |

## 7. Creative Commons CC BY 4.0 deed (what attribution requires)

Source: https://creativecommons.org/licenses/by/4.0/ — HTTP 200 — retrieved 2026-10-05T07:19:27Z (canonical URL stated on the deed page itself: "Canonical URL https://creativecommons.org/licenses/by/4.0/").

Verbatim key passages:

```
You are free to:
Share — copy and redistribute the material in any medium or format
for any purpose, even commercially.
Adapt — remix, transform, and build upon the material
for any purpose, even commercially.
The licensor cannot revoke these freedoms as long as you follow the license terms.

Under the following terms:
Attribution — You must give appropriate credit, provide a link to the license,
and indicate if changes were made. You may do so in any reasonable manner,
but not in any way that suggests the licensor endorses you or your use.

No additional restrictions — You may not apply legal terms or technological
measures that legally restrict others from doing anything the license permits.
```

Deed "Appropriate credit" explainer (verbatim):

```
If supplied, you must provide the name of the creator and attribution parties,
a copyright notice, a license notice, a disclaimer notice, and a link to the
material. CC licenses prior to Version 4.0 also require you to provide the
title of the material if supplied, and may have other slight differences.
```

## 8. balldontlie (Free tier) — see BALLDONTLIE_FREE.md for full verbatim tables

Free tier = **Teams / Players / Games metadata only** across NBA, NFL and WNBA docs.
Player stats endpoints are paid: NBA "Game Player Stats" = No on Free; NFL "Stats"/"Season
Stats" = No on Free; WNBA "Player Stats"/"Player Season Stats" = GOAT-only. No key was
obtained or used; no account created.

## 9. Prior-cycle fact re-verification status

| Prior fact (dispatch packet) | Status today |
|---|---|
| hoopR-family data repos carry LICENSE.md = CC BY 4.0 verbatim covering "data, code, and documentation" | CONFIRMED live (rows 2, 3, 4; quotes + timestamps above) |
| sportsdataverse-data root LICENSE = MIT "Copyright (c) 2023 SportsDataverse" | CONFIRMED live verbatim (row 6) |
| nflverse-data carries CC BY 4.0 | CONFIRMED live (row 5; LICENSE.md = full legalcode) |
| WNBA corpus from a sportsdataverse/wehoop release store | CONFIRMED with precision: assets pulled from `sportsdataverse/sportsdataverse-data` release tags produced by `sportsdataverse/wehoop-wnba-data` (ESPN WNBA) and `wehoop-wnba-stats-data` (stats.wnba.com); both CC BY 4.0 (row 4) |
| balldontlie Free = Teams/Players/Games only; do NOT assume Free player stats | CONFIRMED live on all three sport docs pages (§8, BALLDONTLIE_FREE.md) |

New facts this cycle (not in dispatch packet):
- wehoop/hoopR **code packages are MIT** (data repos CC BY 4.0) — distinction matters if any
  lane reuses scraper code rather than release CSVs.
- sportsdataverse-data README carries the CC BY 4.0 badge; no NOTICE file exists.
- nflfastR README at HEAD contains **no** league-affiliation disclaimer.
- hoopR-nba-stats-data publishes NBA player box scores **from stats.nba.com** in addition to
  the ESPN-side `hoopR-nba-data` — two provenance chains for NBA player data.
