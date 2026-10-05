# RIGHTS — NBA player box data (Lane A, WINPROB-PLAYERDATA-PREP-V1)

Verified 2026-10-05 from OFFICIAL sources (raw LICENSE files at the repos
involved). **Internal research only. NOT legal advice.**

## Chain of custody for the data downloaded this lane

```
ESPN public endpoints
  └─ scraped by sportsdataverse/hoopR-nba-data pipeline (repo, no releases)
       └─ published as release assets in sportsdataverse/sportsdataverse-data
            release tag espn_nba_player_boxscores   <-- DOWNLOAD SOURCE (this lane)
       └─ read by hoopR R package load_nba_player_box()
```

## 1. License AT the download source: sportsdataverse/sportsdataverse-data

- URL: https://raw.githubusercontent.com/sportsdataverse/sportsdataverse-data/main/LICENSE
  (file is `LICENSE`, no `.md` extension; `LICENSE.md` returns 404)
- Fetched: 2026-10-05T07:20Z (HTTP 200; cached copy:
  `~/.my-quantitative-data/playerdata-prep-v1/nba/provenance/LICENSE_sportsdataverse-data.md`)
- VERBATIM QUOTE (full text of the file):

```
MIT License

Copyright (c) 2023 SportsDataverse

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Note: this matches the prior-cycle precedent (distribution store = MIT).

## 2. License of the hoopR-nba-data data repo (same ecosystem)

- URL: https://raw.githubusercontent.com/sportsdataverse/hoopR-nba-data/main/LICENSE.md
- Fetched: 2026-10-05T07:20Z (HTTP 200; cached copy:
  `provenance/LICENSE_hoopR-nba-data.md`)
- VERBATIM QUOTE (full text of the file):

```
# Creative Commons Attribution 4.0 International (CC BY 4.0)

Copyright (c) 2026 hoopR.nba authors

The contents of this repository (data, code, and documentation) are licensed
under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

You are free to:

- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material for any purpose,
  even commercially

Under the following terms:

- **Attribution** — You must give appropriate credit, provide a link to the
  license, and indicate if changes were made. You may do so in any reasonable
  manner, but not in any way that suggests the licensor endorses you or your
  use.

No additional restrictions — You may not apply legal terms or technological
measures that legally restrict others from doing anything the license
permits.

The full license text is available at:
<https://creativecommons.org/licenses/by/4.0/legalcode>

A human-readable summary is available at:
<https://creativecommons.org/licenses/by/4.0/>
```

This confirms the expected CC BY 4.0 for the hoopR NBA data repo (prior-cycle
precedent reproduced from the actual file).

## 3. hoopR package official documentation (what the loaders are documented to read)

- `hoopR` man page `hoopR_loaders.Rd`
  (https://raw.githubusercontent.com/sportsdataverse/hoopR/main/man/hoopR_loaders.Rd,
  fetched 2026-10-05T07:18Z): loaders read "pre-scraped data from the
  `sportsdataverse/hoopR-{nba,mbb}-data` releases on `sportsdataverse-data`";
  `load_nba_player_box()` maps to "NBA player boxscores".
- `hoopR` README data-status table documents pipeline repos `hoopR-nba-data`
  (NBA ESPN) and `hoopR-nba-stats-data` (NBA Stats API), all pointing at
  `sportsdataverse-data` releases. (Cached: `provenance/hoopR_README.md`.)
- `hoopR` `_pkgdown.yml` exports `load_nba_player_box` and
  `load_nba_stats_player_boxscores`. (Cached: `provenance/hoopR_pkgdown.yml`.)

## 4. Known unknowns (fail-closed, for later publication/commercial use)

1. **Underlying-data rights are NOT resolved by either license.** The scraped
   content originates from ESPN public APIs. Neither the MIT store license nor
   the CC BY 4.0 data-repo license speaks to ESPN's/NBA's own rights in the
   underlying statistics feeds, terms of service of the endpoints scraped, or
   any sport-league database-rights claims. Both licenses govern the
   sportsdataverse packaging, not the upstream rights chain.
2. CC BY 4.0 attribution obligations: any redistribution of the hoopR-nba-data
   content must carry attribution + license link + change indication. The MIT
   store license requires retention of its notice. These are compatible with
   internal research use; redistribution needs a consolidated attribution file.
3. hoopR R package code license was NOT separately verified this session
   (only data licenses were in scope). Do not assume it matches the data license.
4. balldontlie Free tier player-stats availability: NOT verified this lane
   (no key usage allowed; delegated to Lane R). No assumption either way.
5. This document is an engineering evidence note. It is **NOT legal advice**;
   any publication or commercial step requires its own rights review.

Required credit line (also in data-dir ATTRIBUTION.md): see
`~/.my-quantitative-data/playerdata-prep-v1/nba/ATTRIBUTION.md`.
