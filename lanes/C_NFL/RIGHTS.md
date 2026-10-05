# RIGHTS — Lane C (NFL PLAYER DATA) · WINPROB-PLAYERDATA-PREP-V1

**Internal research only. NOT legal advice.** Retrievals performed 2026-10-05T07:18:02Z UTC
unless noted.

## 1. Distribution repo license — nflverse/nflverse-data (live-verified)

- Repo: https://github.com/nflverse/nflverse-data
- Release store used this session (weekly player stats): the `stats_player` release
  https://github.com/nflverse/nflverse-data/releases/tag/stats_player
  (asset base `https://github.com/nflverse/nflverse-data/releases/download/stats_player/`)
- Secondary store used (snap counts): the `snap_counts` release
  https://github.com/nflverse/nflverse-data/releases/tag/snap_counts
- LICENSE retrieved live: https://raw.githubusercontent.com/nflverse/nflverse-data/main/LICENSE.md
  (HTTP 200, 2026-10-05T07:18:02Z; saved to
  `~/.my-quantitative-data/playerdata-prep-v1/nfl/rights/nflverse-data_LICENSE.md`).

Verbatim identification lines from the live LICENSE.md:

> Attribution 4.0 International

> Creative Commons Attribution 4.0 International Public License

> By exercising the Licensed Rights (defined below), You accept and agree to be bound by the
> terms and conditions of this Creative Commons Attribution 4.0 International Public License
> ("Public License").

Cross-check: the live file is byte-identical (`diff` = identical) to the prior-cycle copy at
`~/.my-quantitative-data/nfl-ng-prep-v1/rights/nflverse-data_LICENSE.md`. Expected CC BY 4.0:
CONFIRMED live.

License obligations (CC BY 4.0): attribution (credit nflverse, link the repo, name the
license), license notice, changes marking; no endorsement right.

## 2. README / release description (live)

README retrieved live: https://raw.githubusercontent.com/nflverse/nflverse-data/main/README.md
(HTTP 200, 2026-10-05T07:18:02Z; saved to
`~/.my-quantitative-data/playerdata-prep-v1/nfl/rights/nflverse-data_README.md`). Verbatim:

> # nflverse-data
>
> This repository holds automated data releases for nflverse projects
> (i.e. all of the data powered/scraped via GitHub Actions).

> You can download data hosted here with the `{nflreadr}` package, or
> manually download and access the [releases](https://github.com/nflverse/nflverse-data/releases) page.

`stats_player` release body (from the cached GitHub API listing, tag `stats_player`), verbatim:

> Player stats in different summary levels created with `nflfastR::calculate_stats()`

## 3. Underlying-data provenance disclaimer

The weekly stats are built by nflverse's pipelines (release body: `nflfastR::calculate_stats()`)
from official NFL feeds (NFL operations / GSIS; Next Gen Stats-derived fields feed parts of the
ecosystem, e.g. pbp nextgen columns). **The CC BY 4.0 license is on the nflverse-data
repository/release artifacts only; it does not and cannot grant rights in the underlying
league data.** Per the dispatch instruction, this lane records the nflverse data-sourcing
disclaimer direction (stats sourced from NFL operations / Next Gen Stats etc.) as context:
the upstream feeds' own terms govern any use beyond internal research. Attribution string to
use verbatim:

> Data: nflverse/nflverse-data releases (CC BY 4.0), https://github.com/nflverse/nflverse-data

## 4. Known-unknowns (fail-closed) for publication / commercial use

1. Whether the underlying NFL GSIS / Next Gen Stats feeds' terms permit redistribution of
   derived player-stat tables — NOT determined from public sources this session.
2. Whether "NFL operations / Next Gen Stats" branding or player names/headshots
   (`headshot_url` column is present in the weekly stats) carry publicity/rights-of-publicity
   constraints for commercial republication — NOT determined.
3. Whether nflverse's trademark/name policy restricts implying affiliation — standard
   no-endorsement clause assumed required (we state non-affiliation explicitly).
4. Scope of CC BY 4.0 "adaptation" duties when we build frozen feature tables from these
   releases — attribution practice defined above covers internal research; publication needs
   separate review.

Position: internal research use only under CC BY 4.0 attribution; any publication or
commercial use requires an independent rights review. NOT legal advice.

## 5. Budget

$0 — all fetches unauthenticated public URLs (GitHub releases, GitHub raw). No accounts, no
API keys. GitHub API consumed 1 unauthenticated call (rate limit 60/hr) this session.
