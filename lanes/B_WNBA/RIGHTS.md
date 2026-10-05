# RIGHTS — Lane B (WNBA PLAYER DATA) · cycle WINPROB-PLAYERDATA-PREP-V1 · 2026-10-05

Internal research only. **NOT legal advice.** All quotes below are VERBATIM from official
sources; retrieval timestamps are machine-local on 2026-10-05 during this lane session.

## 1. What was fetched, from where, when

| source | URL | retrieved (UTC) | method |
|---|---|---|---|
| release store README (raw) | `https://raw.githubusercontent.com/sportsdataverse/sportsdataverse-data/main/README.md` | 2026-10-05 ~07:20Z | `curl` (verbatim bytes) |
| release store LICENSE (raw) | `https://raw.githubusercontent.com/sportsdataverse/sportsdataverse-data/main/LICENSE` | 2026-10-05 ~07:20Z | WebFetch over raw URL |
| wehoop package repo (docs) | `https://github.com/sportsdataverse/wehoop` | 2026-10-05 ~07:20Z | WebFetch |
| release metadata for `espn_wnba_player_boxscores` | `https://api.github.com/repos/sportsdataverse/sportsdataverse-data/releases/tags/espn_wnba_player_boxscores` | archived verbatim by prior cycle at `~/.my-quantitative-data/wnba-prep-v1/roster_audit/release_meta_r2.json` (pull 2026-10-05T06:58:27Z); release `updated_at` 2026-10-04T10:39:56Z | archived API response |

No scraping of wnba.com / stats.wnba.com / ESPN was performed by this lane, ever. The corpus
was produced by the SportsDataverse pipelines (`wehoop-wnba-raw` → `wehoop-wnba-data` →
release store), not by us.

## 2. Verbatim quotes

### 2a. Release store `sportsdataverse/sportsdataverse-data` README (raw, line 10–11)

The data-license badge:

```
[![License: CC
BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-blue.svg?style=flat-square)](https://creativecommons.org/licenses/by/4.0/)
```

i.e. badge text **"License: CC BY 4.0"** linking to
`https://creativecommons.org/licenses/by/4.0/`.

What the store is (README, verbatim):

> This repository is the **release store** of the
> [SportsDataverse](https://sportsdataverse.org): the `load_*()` functions
> in the SportsDataverse R packages and in `sportsdataverse-py` read their
> data from the GitHub releases published here (the nflverse-parity NFL
> loaders read the nflverse-data releases instead).

Producer pipeline for our two releases (README tables, verbatim):

> **WNBA (ESPN)** — `wehoop-wnba-data` ← `wehoop-wnba-raw` — "Daily, May-Oct (dispatched by
> wehoop-wnba-raw's droplet run); rosters weekly; draft mid Apr"

Note: the repo carries exactly ONE root `LICENSE` file (see 2b) while the README badge says
CC BY 4.0 — the badge is the only data-license statement in the store; there is no separate
`LICENSE_DATA` file and no per-release license sentence.

### 2b. Release store root `LICENSE` (raw, fetched 2026-10-05)

```
MIT License

Copyright (c) 2023 SportsDataverse
```

(standard MIT text follows: permission to use/copy/modify/merge/publish/distribute/sublicse/sell
subject to including the copyright + permission notice; AS-IS, no warranty.)

Reading: the repo's *code-level* license is MIT; the README *badge* declares the published
DATA as CC BY 4.0. This matches the nflverse-family pattern already verified by
WINPROB-NG-PREP-V1 (lane A memo) and the WNBA-WINPROB-PREP-V1 lane A DOWNLOAD_MANIFEST.md.

### 2c. wehoop package repo `sportsdataverse/wehoop` (docs page, fetched 2026-10-05)

- About: "An R package to quickly obtain clean and tidy women's basketball play by play data."
- Sources: "A scraping and aggregating interface for ESPN's women's college basketball and
  WNBA statistics." / "access live play by play and box score data from ESPN". The README also
  references `load_wnba_stats_*` loaders "(WNBA Stats API, …)".
- Release linkage: "The `load_*()` functions read release assets on sportsdataverse-data."
- Code license: MIT ("License, MIT licenses found" in the repo Resources sidebar; `LICENSE` +
  `LICENSE.md` present). Citation requested: BibTeX "wehoop: Access Women's Basketball Play by
  Play Data", DOI 10.32614/CRAN.package.wehoop, authors Gilani, Saiem and Hutchinson, Geoffery.

## 3. Underlying-source rights (the layer the store does NOT grant)

The statistics originate from the **ESPN WNBA API** (schedules/box/rosters/pbp) and the
**stats.wnba.com WNBA Stats API** endpoints, scraped to release assets by the SportsDataverse
pipelines. Neither ESPN nor the WNBA is a party to any license we hold:

- CC BY 4.0 (if it applies to the release assets) is a grant **by the store maintainer**, not
  by the upstream data owner.
- No statement was found in any fetched artifact in which ESPN or the WNBA grants
  redistribution rights for derived statistics. The store README contains no
  attribution/attribution-requirement section beyond the badge.

## 4. What stays unclear (fail-closed)

1. **Publication / external redistribution**: unclear. The CC BY 4.0 claim is a README badge
   with a single MIT root LICENSE file; a maintainer confirmation that the *data assets*
   (not the repo code) are CC BY 4.0 should be obtained before any external redistribution of
   derived tables. Prior-cycle handoff (WNBA-WINPROB-PREP-V1 lane A) reached the same
   conclusion: "maintainer confirmation still required before any external redistribution".
2. **Commercial use**: unclear for the same reason, and additionally burdened by the
   underlying ESPN/WNBA terms (not fetched, not agreed by us).
3. **`athlete_headshot`/logo columns** in the corpus embed ESPN media URLs — treat as
   ESPN property; never redistribute the media, drop the columns from any derived table.
4. This memo is an evidence record, not counsel. **Internal research only.**
