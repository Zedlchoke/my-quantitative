# NBA POST-2015 $0 Data Sources — Lane A memo (WINPROB-NG-PREP-V1)

Owner round 2026-10-05. Lane: `A_NBA_POST2015`. All fetches performed this
session (2026-10-05 UTC). Not legal advice; internal research only.

## 1. PRIMARY CANDIDATE — hoopR ecosystem (sportsdataverse), VERDICT: PASS

### 1.1 Package repo

- https://github.com/sportsdataverse/hoopR (R package, CRAN-published;
  `hoopR/hoopR_data` and org `hoopR` do NOT exist — 404 measured; the package
  moved under org `sportsdataverse`).
- CODE license (package): MIT template file — verbatim:
  > `YEAR: 2020-2026`
  > `COPYRIGHT HOLDER: hoopR authors`
- README quotes (measured 2026-10-05):
  > "The package has functions to access **live play by play and box score**
  > data from ESPN with shot locations when available. As of version 1.3.0,
  > hoopR is also a full NBA Stats API wrapper with 127 functions added in
  > this release."
  > "As of version 3.1.0, the package exports 600+ functions spanning the NBA
  > Stats API (`nba_*`), ESPN (`espn_nba_*` / `espn_mbb_*`), KenPom (`kp_*`) ..."
  > "The `load_*()` functions read release assets on sportsdataverse-data."
  > "NBA full play-by-play seasons (2002-2026) ~ 1-2 minutes"

### 1.2 Data repos + releases (the nflverse pattern, re-created for NBA)

Producer repos (pipeline + in-repo data):
- https://github.com/sportsdataverse/hoopR-nba-data — "hoopR NBA Data 2002 -
  Present", upstream source **ESPN** (per its README repo list:
  "[hoopR-nba-data repository (source: ESPN)]"). Active (last release publish
  2026-08-26/09-09; scheduled daily in-season, idle in late summer per its
  status table).
- https://github.com/sportsdataverse/hoopR-nba-stats-data — same pipeline,
  upstream source **NBA Stats** ("[hoopR-nba-stats-data repository (source:
  NBA Stats)]").
- Distribution: GitHub Releases on https://github.com/sportsdataverse/sportsdataverse-data
  (tags `espn_nba_schedules`, `espn_nba_pbp`, `espn_nba_team_boxscores`,
  `espn_nba_player_boxscores`, `nba_crosswalk`, ...), direct download,
  **no auth, no API key** (release body verbatim: "Direct download (no auth,
  no API key)").

### 1.3 DATA LICENSE — VERIFIED VERBATIM (this is the load-bearing check)

`hoopR-nba-data/LICENSE.md` (fetched raw.githubusercontent.com 2026-10-05,
full text captured; excerpt verbatim):

> "# Creative Commons Attribution 4.0 International (CC BY 4.0)
>
> Copyright (c) 2026 hoopR.nba authors
>
> The contents of this repository (data, code, and documentation) are licensed
> under the Creative Commons Attribution 4.0 International License (CC BY 4.0).
>
> You are free to:
> - **Share** — copy and redistribute the material in any medium or format
> - **Adapt** — remix, transform, and build upon the material for any purpose,
>   even commercially
>
> Under the following terms:
> - **Attribution** — You must give appropriate credit, provide a link to the
>   license, and indicate if changes were made. ...
>
> No additional restrictions — ...
> The full license text is available at:
> <https://creativecommons.org/licenses/by/4.0/legalcode>"

`hoopR-nba-stats-data/LICENSE.md`: identical CC BY 4.0 text ("Copyright (c)
2026 hoopR.nba.stats authors").

Releases repo `sportsdataverse-data` root `LICENSE`: **MIT** (verbatim header:
"MIT License / Copyright (c) 2023 SportsDataverse"; full grant includes "use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies").
GitHub license API for the repo: spdx_id MIT.

Difference from the nflverse/nfldata precedent: the CC BY 4.0 sits on the two
PRODUCER repos and explicitly covers "data, code, and documentation", while
the actual RELEASE ASSETS live on `sportsdataverse-data` (MIT only). The
producer repo's README declares those releases to be its data products
(workflow diagram: `hoopR-nba-data -> C[sportsdataverse-data Releases]` with
the exact release tags listed). Net legal position for our use: explicit open
license on the data itself (CC BY 4.0) PLUS an equally explicit permissive
license on the distribution repo (MIT). Both permit internal research, ML
training, storage, and (with attribution) redistribution. This is NOT the
"no license file → UNVERIFIED/banned" branch; the license file exists and
names data explicitly. Residual note (honest hedge, not a blocker): the CC BY
4.0 text's scope clause says "this repository"; we rely on the producer's own
README linking its releases to the repo, plus MIT on the releases repo as an
independent, sufficient grant for the asset files.

### 1.4 Provenance / upstream-rights analysis (same pattern as prior memos)

- Release body (verbatim, `espn_nba_schedules` and `espn_nba_pbp` tags):
  > "Upstream source: ESPN NBA API."
  > "**Season key.** season = the ENDING year of the season (2025 = 2024-25)."
- So the chain is: ESPN (hidden/public JSON API) -> sportsdataverse scraper ->
  CC BY 4.0 releases. The alternative chain is NBA.com/Stats -> hoopR-nba-stats-data
  (same CC BY 4.0), not exercised this round.
- Upstream analysis (facts / Feist / privity / CC-BY-on-releases pattern):
  1. The released rows are athletic-contest FACTS: date, teams, venue, final
     score, play descriptions. Under 17 U.S.C. § 102(b) facts are never
     original to copyright; Feist v. Rural (1991) denies "sweat of the head"
     protection; the thin selection/arrangement of a complete schedule is
     the weakest kind of claim. The play-by-play TEXT descriptions are
     ESPN-authored expression — those live in `play_by_play_*` and merit the
     more conservative treatment below even though the licensor released
     them CC BY 4.0.
  2. Privity: we do not contract with ESPN or NBA.com; their site ToS bind
     the scraper (sportsdataverse), not a downstream receiver of published
     files, absent click-through or knowledge of wrongful acquisition. We
     consume only the published GitHub release assets.
  3. The licensor (sportsdataverse authors) affirmatively grants CC BY 4.0 /
     MIT on exactly these files — an express license is dispositive as
     between us and the licensor.
  4. Trademark/rights of publicity: we store facts for internal research;
     no marks, logos, or player likenesses are republished.
- NOT legal advice; internal research only; owner conditional authorization
  recorded 2026-10-05 in `ATTRIBUTION.md`.
- Rate limits / keys: direct GitHub release download, no auth, no key, no
  rate-limit problems at our volume (13 files, ~95 MB total). Live ESPN
  endpoints via the package are unauthenticated (no key); we did NOT hit
  them this round — releases only.

### 1.5 Coverage (measured, not claimed)

Release-body claims (verbatim): schedules "**26 seasons** (2002–2027) · 88
assets"; pbp "**25 seasons** (2002–2026) · 79 assets". Files:
`nba_schedule_{season}.{csv,parquet,rds}`, `play_by_play_{season}.…`.
Latest complete season = 2026 (= 2025-26; Finals ended by 2026-06-14 per
measured max `game_date_time`).

## 2. OTHER SOURCES (quick verdicts)

| Source | Verdict | Evidence (this session) |
|---|---|---|
| balldontlie NBA API | **BLOCKED_NO_KEY** (unchanged) | docs.balldontlie.io verbatim: "An API key is required. You can obtain an API key by creating a free account on our website."; free tier is a "48-hour free trial"; account signup violates our no-accounts rule. |
| Wikidata (structured data) | License PASS (CC0), **not a usable primary** | wikidata.org/wiki/Wikidata:Licensing verbatim: "All structured data (i.e. the main, Property, Lexeme, and EntitySchema namespaces) is released into the public domain under Creative Commons Zero." But per-game NBA results/schedules are sparse and inconsistently modeled → NOT_RUN as source, keep as auxiliary only. |
| sportsdataverse/hoopR-data (old repo) | Superseded | Archived ("hoopR data 2002-2021", archived: True measured). Do not use; use hoopR-nba-data + sportsdataverse-data releases. |
| hoopR-kp-data (KenPom) | BLOCKED_NO_SUBSCRIPTION | README labels it "(source: KenPom, dormant)"; upstream needs paid subscription. |
| FiveThirtyEight nbaallelo (existing, in-house) | Existing asset, ends 2015 | Local file `~/.my-quantitative-data/nba-538-v1/raw/nbaallelo.csv`: 126,314 team-rows, date range 1947-01-01 → 2015-06-16. Seam to hoopR window is clean (see §4.3). |

## 3. DOWNLOADS PERFORMED (rights cleared → NOT_RUN_DOWNLOAD_RIGHTS does NOT apply)

All into `~/.my-quantitative-data/nba-hoopr-v1/raw/` (outside git), provenance
in `_download_provenance.tsv` + `ATTRIBUTION.md`. URL base:
`https://github.com/sportsdataverse/sportsdataverse-data/releases/download/{tag}/{file}`

| File | Tag | Bytes | sha256 |
|---|---|---|---|
| nba_schedule_2016.csv | espn_nba_schedules | 954,991 | 3373fb4ade99e7056228a4dfaa1c2128f7a255672e09c27dd3cab731edb53a9c |
| nba_schedule_2017.csv | espn_nba_schedules | 949,421 | d17829cbcaaa5fee9f3cbb73289357e702786b02f5bc08ea9eb9b4ab4c718f03 |
| nba_schedule_2018.csv | espn_nba_schedules | 951,431 | ce772be7fc1627c0be22d5d18a65eef3dc699683738538d922320e4546ad12aa |
| nba_schedule_2019.csv | espn_nba_schedules | 950,828 | b99913f6167a59d52150ab69fcc59df2fd588b8d255c2e5d4d3e0f8828c6c084 |
| nba_schedule_2020.csv | espn_nba_schedules | 1,648,408 | af35fed1dc55add0425f5b0f1a332fcbc433ff8f44265224107c8d46fd90bce7 |
| nba_schedule_2021.csv | espn_nba_schedules | 1,615,095 | 1857bb44da8458a6e9205ffb57ed87e43a35ad4cdbab6ee7752684bb8f7744bf |
| nba_schedule_2022.csv | espn_nba_schedules | 1,791,225 | 8cd13a11b16aa49f26e766e7af1d674aecb96ef427bfe1655740b7fd252b24ed |
| nba_schedule_2023.csv | espn_nba_schedules | 1,776,788 | 71aad62f4c082455ba7659b5cc900745a72b113b85bc22727ac04a603a9b5dca |
| nba_schedule_2024.csv | espn_nba_schedules | 1,813,321 | ae89a6e51dec1817b41e457d02ffc4cfc26d25b411d318906c1ec5f39a6c5527 |
| nba_schedule_2025.csv | espn_nba_schedules | 2,216,279 | a7a5b6607a256c84a324f819e4461248bdff90a78b1ddb675a5a117a9a94e74f |
| nba_schedule_2026.csv | espn_nba_schedules | 9,153,001 | 5a4a7473fce1c49d56382211c5955ad405f421d59869143b1d501e997e79223e |
| play_by_play_2026.parquet | espn_nba_pbp | 22,436,946 | f2d1ccc1a80febd90791d02390504d4a5331f2041169e3a85a4f052df27a0ffd |
| nba_schedule_crosswalk_2026.csv | nba_crosswalk | 150,611 | 2f35921cedcbd9bf10838e62a64271ca1b8d42a47f41d746105c5435b49a108c |

Pulled 2026-10-05T01:35–01:36 UTC. Every byte count matches the GitHub API
asset metadata exactly. Asset `updated_at` per file recorded in
`_download_provenance.tsv`.

## 4. MEASUREMENT (all from the downloaded files)

### 4.1 Rows / seasons / games-per-season

Total 14,254 schedule rows, 14,254 unique `game_id` (also unique `id`).
ESPN `season_type` codes observed: 2 = regular season, 3 = postseason,
5 = play-in. Per-season rows:

| season file (ending yr) | RS(2) | Post(3) | PlayIn(5) | date range of games |
|---|---:|---:|---:|---|
| 2016 (2015-16) | 1231 | 86 | 0 | 2015-10-28 → 2016-06-20 |
| 2017 | 1231 | 79 | 0 | 2016-10-25 → 2017-06-13 |
| 2018 | 1232 | 82 | 0 | 2017-10-18 → 2018-06-09 |
| 2019 | 1232 | 82 | 0 | 2018-10-17 → 2019-06-14 |
| 2020 (COVID) | 1064 | 92 | 1 | 2019-10-23 → 2020-10-11 |
| 2021 (shortened, 72-gm) | 1113 | 85 | 6 | 2020-12-23 → 2021-07-21 |
| 2022 | 1242 | 87 | 6 | 2021-10-19 → 2022-06-17 |
| 2023 | 1232 | 84 | 6 | 2022-10-18 → 2023-06-13 |
| 2024 | 1234 | 82 | 6 | 2023-10-24 → 2024-06-18 |
| 2025 | 1239 | 84 | 6 | 2024-10-22 → 2025-06-23 |
| 2026 | 1239 | 85 | 6 | 2025-10-21 → 2026-06-14 |

Reconciliation vs the naive "1230": RS rows include (a) the All-Star Game
listed as a `season_type=2` game with pseudo-teams EAST/WEST (11 rows, one per
season — EXCLUDE for modeling), and (b) from 2023-24 the NBA Cup final as an
extra 1231st game (notes_headline "NBA In-Season Tournament Championship"),
plus rescheduled/postponed duplicate listings (67 rows league-wide have
`status_type_completed=False`; e.g. 2026 has 4 postponed rows whose makeups
carry separate game rows — 2026: 1,330 rows − 4 postponed = 1,326 completed;
All-Star has no pbp so pbp shows 1,325 games). Dedupe law: keep
`status_type_completed == True`, exclude EAST/WEST All-Star rows, one row per
`game_id`. Measured completed-and-real RS for 2021 = 1,113 raw − All-Star −
postponed listings ⇒ actual played 2020-21 regular season ≈ 1,080 as expected
for a 72-game season; 2019-20 ≈ 1,059 played + 5 unfinished bubble listings.
Per-season played counts must be re-derived with the dedupe law in the new
cycle (raw file counts alone are NOT the game universe).

### 4.2 ID field + format + as-of grain

- Primary key: **`game_id`** (ESPN event id, numeric string, e.g.
  `401766128`; identical to `id` column; unique measured 14,254/14,254;
  stable across schedules and pbp releases — pbp `game_id` same format,
  e.g. `401859967`).
- **The schedules carry TRUE TIP-OFF TIMESTAMPS**, not date-only:
  `game_date_time` is local time with offset, e.g.
  `2016-10-25T19:30:00.000000-0400` (2016-17 opener tip 7:30pm ET), and pbp
  carries tz-aware tip times (`America/New_York`). `date`/`start_date` are the
  same instant in UTC (`2025-06-23T00:00Z` = Jun 22 8pm ET). `game_date` is
  date-only. Pre-tip as-of joins are therefore possible from this source.
- Home/away + final scores + winner flags: `home_*`/`away_*` blocks incl.
  `home_score`, `away_score`, `home_winner`, venue, broadcast.
- Bonus measured in the pbp sample: `game_spread`, `home_favorite`,
  `home_team_spread` (ESPN line) present on 1,321/1,325 games (99.7%) of the
  2026 sample — a candidate closing-line feature; historical-season spread
  coverage NOT_RUN this round.

### 4.3 Crosswalk law (hoopR ↔ 538 nbaallelo) and seam

- `nba_crosswalk` release (`nba_schedule_crosswalk_{2026,2027}.csv`) provides
  a real game-level crosswalk `espn_game_id ↔ nba_game_id ↔ nba_game_code ↔
  fox_* ↔ yahoo_*` — **but only for seasons 2026–2027** (2 seasons per the
  release body). No provider-id crosswalk exists for 2016–2025.
- 538 nbaallelo (local): `game_id` = `YYYYMMDD` + home team, e.g.
  `201506170CLE`, PLUS `gameorder` (2 rows/game). MEASURED QUIRK: the date in
  `game_id` is UTC-shifted vs `date_game` (local): tail rows show
  `game_id=201506170CLE` with `date_game=6/16/2015` (2015 Finals G6 at CLE;
  9pm ET Jun 16 = Jun 17 UTC). Any join on the `game_id` date component
  naively MISSES by one day for late games.
- 538 file ends 2015-06-16 (2015 Finals G6, GSW clinched 4-2); hoopR 2016
  file starts 2015-10-28 ⇒ **no row overlap; the two corpora are a clean
  seam, not an overlap.**
- Proposed join law for the new cycle: (i) within hoopR-era, ESPN `game_id`
  is primary; (ii) for 2026+ join to NBA.com ids via `nba_crosswalk`;
  (iii) for anything joined back to 538-era rows, join by **LOCAL game date +
  home team abbreviation** (538 `date_game`/`team_id` with
  `game_location=='H'`), never by the `game_id` date component; (iv) spot
  rule that 538 has 2 rows/game (gameorder 0/1) vs hoopR 1 row/game.

### 4.4 Spot-checks (hoopR schedules vs independently known results) — 3/3 PASS

1. 2016-17 opener, 2016-10-25: row `game_id=400899375`, CLE home **117** —
   NY away **88**, STATUS_FINAL, Rocket Mortgage FieldHouse. Matches the
   known result.
2. 2019 Finals G6, 2019-06-13 (Raptors' title game; note: that series had no
   Game 7): `game_id=401134820`, GS home **110** — TOR away **114**,
   notes "NBA FINALS - GAME 6", home_winner=False (away won). Matches.
3. 2025 Finals G7, 2025-06-22: `game_id=401766128`, OKC home **103** — IND
   away **91**, notes "NBA Finals - Game 7", home_winner=True. Matches.

## 5. VERDICTS + PROPOSAL

### Per-source verdicts

| Source | download+store | internal-research+ML | redistribution |
|---|---|---|---|
| hoopR-nba-data / espn_nba_* releases (ESPN upstream) | **PASS** (done this round, CC BY 4.0 + MIT) | **PASS** (CC BY 4.0 "Adapt ... for any purpose") | **PASS with attribution** (CC BY 4.0 credit line + license link; MIT notice on assets) |
| hoopR-nba-stats-data / NBA-Stats-source releases | PASS (not exercised; license verified verbatim) | PASS (same caveat: upstream NBA.com ToS binds the scraper, not us; facts analysis holds) | PASS with attribution (same terms) |
| balldontlie | BLOCKED_NO_KEY | BLOCKED_NO_KEY | n/a |
| Wikidata | PASS (CC0) | PASS | PASS | 
| KenPom | BLOCKED_NO_SUBSCRIPTION | same | n/a |

Pbp text fields (`text`, `short_description`) are ESPN-authored expression
released CC BY 4.0 by the licensor — fine under the license; if we ever
republish, the CC BY attribution obligation applies to them too.

### Boundary statement (required)

**Extending the TERMINAL cycle NBA-WINPROB-SCORED-V1's folds/window to 2016+
is NOT_RUN by law — it must not be done.** The terminal cycle is registered,
its gates are closed, and any new data window (2015-16 onward) is a new
research question that must live in a **NEW registered cycle** (suggested id:
`NBA-WINPROB-POST2015-V1` or fold into WINPROB-NG after PREP), with its own
gates, owner authorization, and trial accounting. Nothing in this lane touches
the terminal cycle's state.

### New-cycle data contract (sketch)

- **PRIMARY (schedules/results):** `nba_schedule_{2016..2026}.csv` from
  release tag `espn_nba_schedules` (per-season files; refresh by re-pulling
  the tag + recording sha256). 1 row/game, `game_id` primary key.
- **SECONDARY (features):** `play_by_play_{season}.parquet` from
  `espn_nba_pbp` (per-season, ~21 MB parquet each) — carries game-level
  spread features (`game_spread`, `home_favorite`, 99.7% coverage in the
  2026 sample) and play-level events; team/player box releases exist for
  rollover/form features.
- **Game-universe law:** `status_type_completed == True`; exclude
  `notes_headline` All-Star rows (EAST/WEST pseudo-teams); include
  `season_type in {2,3,5}` (RS + playoffs + play-in) or {2} per design;
  one row per `game_id`; re-derive per-season played counts after dedupe
  (raw counts over-count by All-Star/postponed rows).
- **As-of grain:** schedules carry true tip timestamps (`game_date_time`,
  local offset; UTC twin in `start_date`) — pre-tip as-of is supported;
  `game_date` alone is insufficient.
- **Crosswalk law:** ESPN `game_id` primary; 2026+ may join to NBA.com ids
  via `nba_crosswalk` (only 2026–2027 populated); to 538-era rows join by
  LOCAL date + home team (never the UTC-shifted `game_id` date; 538 has 2
  rows/game via `gameorder`).
- **Attribution law:** CC BY 4.0 credit line in any derivative output;
  attribution block fixed in `~/.my-quantitative-data/nba-hoopr-v1/raw/ATTRIBUTION.md`.

## 6. Known limitations / NOT_RUN items

- Spread-feature coverage for pre-2026 pbp seasons: NOT_RUN (only 1 sample
  season downloaded, per dispatch).
- ESPN spread semantics (closing vs opening line timestamp): UNVERIFIED —
  column provenance within ESPN payloads not documented upstream.
- No ESPN↔provider id crosswalk for 2016–2025: accepted limitation; date+team
  join law only.
- Live ESPN/NBA.com scraping: NOT exercised (releases only), no keys touched.
- Nothing committed to git (lane artifacts land uncommitted; controller
  lands). Raw data lives outside git by design.
