# WNBA SOURCE AUDIT — Lane B (WINPROB-NG-PREP-V1)

- Task: `wng-b-wnba` · Cycle: `WINPROB-NG-PREP-V1` · Date: 2026-10-05
- Dispatch sha = actual start sha = `0513a0f612e0f739f41229bb86b2084b5dff6d2e`
  (branch `orca/winprob-ng-prep-v1-integration`; **no git operations performed by this lane**)
- Scope: $0, owner round 2026-10-05; audit + verified-rights sample download only. No NBA data or
  hypotheses borrowed as WNBA evidence; every measurement below comes from WNBA sources.
- Raw data: `~/.my-quantitative-data/wnba-v1/raw/` (99 files, 74.6 MB). Per-file sha256 manifest:
  `DATA_MANIFEST.md` (this directory). Census script: `audit_script.py`; machine output:
  `~/.my-quantitative-data/wnba-v1/raw/audit_results.json`.

## VERDICT: **PASS** — data layer only, with conditions (§5)

A $0 WNBA win-probability modeling program is feasible on the wehoop/sportsdataverse release
store alone: full-history schedules (1997–2026), full-history PBP (1997–2026) and box scores
(2002/2003–2026) under an open (CC BY 4.0) license, refreshed daily in-season. Conditions:
open-license confirmation nuance (§1a), modeling filters (§3.6), 1997–2001 gap shape (§5.2),
injury feed absent / NOT_RUN_PIT (§3.7). Modeling itself is a future cycle.

---

## 1. Source inventory + rights (verbatim quotes, access dates 2026-10-05)

### (a) wehoop ecosystem / sportsdataverse-data releases — PRIMARY, rights OK

Architecture (verified live): the R package `sportsdataverse/wehoop` scrapes; producer repos
`wehoop-wnba-data` (ESPN) and `wehoop-wnba-stats-data` (stats.wnba.com) build; the release store
`sportsdataverse/sportsdataverse-data` publishes per-dataset tags consumed by
`load_wnba_*()` loaders. Legacy `sportsdataverse/wehoop-data` is an archive.

- Legacy data repo README (https://github.com/sportsdataverse/wehoop-data, accessed 2026-10-05),
  verbatim: "**ARCHIVE — this repository is not maintained.**" … successors listed as
  "`sportsdataverse/wehoop-wnba-data` — WNBA (ESPN)", "`sportsdataverse/wehoop-wnba-stats-data` —
  WNBA (WNBA Stats API)", "Published datasets are distributed through the
  [sportsdataverse-data](https://github.com/sportsdataverse/sportsdataverse-data) release ecosystem".
- Package README (https://github.com/sportsdataverse/wehoop, accessed 2026-10-05), verbatim:
  "`wehoop` is an R package for working with women's college and professional basketball data.
  The package has functions to access **live play by play and box score** data from ESPN with
  shot locations when available." — **provenance = ESPN, not WNBA.com.**
- DATA license, verbatim from the release-store README badge
  (https://github.com/sportsdataverse/sportsdataverse-data, accessed 2026-10-05):
  `[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-blue.svg?style=flat-square)](https://creativecommons.org/licenses/by/4.0/)`
  → data release assets are published under **CC BY 4.0**. The same repo's `LICENSE` file (code)
  is MIT, verbatim header: "MIT License / Copyright (c) 2023 SportsDataverse / Permission is
  hereby granted, free of charge, to any person obtaining a copy of this software and associated
  documentation files (the "Software"), to deal in the Software without restriction…". The release
  bodies themselves carry no license text (grep over full body of `espn_wnba_schedules`:
  no "license"/"CC"/"Attribution" hits) — the badge is the license statement.
  **Nuance:** MIT file + CC BY 4.0 badge mirrors the nflverse-family pattern (code MIT, data CC BY
  4.0). No verbatim "the data is CC BY 4.0" sentence exists anywhere in the repo. Internal
  research use under attribution is safe; confirm with the maintainers before any redistribution
  beyond the workspace (one GitHub issue, $0).
- Release body `espn_wnba_schedules` (accessed 2026-10-05), verbatim: "**ESPN WNBA** — the game
  schedule, one row per game." · "**25 seasons** (2002–2026) · **85 assets** · 24.1 MB · last
  asset written **2026-10-01**" · "Upstream source: ESPN WNBA API." · "Direct download (no auth,
  no API key):" · "`timestamp.txt` and `package_function.txt` are `piggyback` bookkeeping sidecars
  written by the R publisher".
- Release body `wnba_stats_schedules`, verbatim: "**WNBA Stats (stats.wnba.com)** — the game
  schedule, one row per game." · "**30 seasons** (1997–2026) · **105 assets** · 1.7 MB" ·
  "Upstream source: stats.wnba.com official endpoints."
- Coverage statements from other release bodies (accessed 2026-10-05): `espn_wnba_pbp`
  "**25 seasons** (2002–2026) · 1015.9 MB"; `espn_wnba_team_boxscores` "**24 seasons**
  (2003–2026)"; `espn_wnba_player_boxscores` "**25 seasons** (2002–2026)";
  `wnba_stats_pbp` "**30 seasons** (1997–2026) · 203.6 MB"; `espn_wnba_game_rosters`
  "25 seasons (2002–2026)"; `espn_wnba_shots` "25 seasons (2002–2026) · 140.6 MB";
  `wnba_stats_team_boxscores` "**1 season** (2026–2026)" (gap on that side);
  `wnba_stats_lineups` "**1 season** (2026–2026)".
- An ID-reconciliation asset exists: release tag `wnba_crosswalk` (team/schedule/player crosswalks,
  0.1 MB, last published 2026-09-29) — recommended for team-ID joins across sources.
- Upstream refresh cadence (READMEs, accessed 2026-10-05): ESPN pipeline daily 07:00 UTC May–Oct
  (producer window "Oct-Jul" noted as an open bug); stats pipeline "daily 14:00 UTC in May-Sep;
  days 1-20 14:00 UTC in Oct".

### (b) WNBA.com official — RESTRICTIVE, do not scrape

Terms of Use, https://www.wnba.com/terms-of-use/, section "OWNERSHIP AND USE RESTRICTIONS"
(accessed 2026-10-05), verbatim:

> "The basketball-related content and materials contained within the Services (including, but not
> limited to, video, audio, photos, text, images, **statistics**, updated scores, logos and other
> intellectual property related to the WNBA and its teams) ("Basketball Content") are either owned
> by or licensed to the Operator. **No Basketball Content from the Services may be reproduced,
> republished, uploaded, posted, transmitted, distributed, copied, publicly displayed or otherwise
> used except as provided in these Terms of Use without the written permission of the Operator.**"

> "Where the function is available, you may download material displayed on the Services to any
> single computer only for your **personal, noncommercial use** … You may not, however,
> distribute, reproduce, republish, upload, display, modify, transmit, reuse, repost, link to, or
> use any materials of the Services for **public or commercial purposes** on any other websites or
> otherwise without the written permission of the Operator."

**Verdict:** statistics are explicitly "Basketball Content"; grant is personal/noncommercial
single-computer; no automated-access allowance. Direct scraping of wnba.com or stats.wnba.com is
out for this program. (The sportsdataverse stats-side pipeline scraped stats.wnba.com upstream;
we consume their published release assets, not the site.)

### (c) balldontlie WNBA — BLOCKED_NO_KEY (+ paid for anything useful)

Docs https://wnba.balldontlie.io/ (accessed 2026-10-05), verbatim: "The API contains data from
**2008-current**. **An API key is required.**" Free tier = 5 req/min and only Teams/Players/Games;
Play-by-Play, all stats, standings, injuries and odds are paid tiers ("ALL-STAR 60 9.99",
"GOAT 600 39.99" per month). Note `docs.balldontlie.io` itself documents only the NBA API
("Welcome to the BALLDONTLIE NBA API … The API contains data from 1946-current."); WNBA lives on
its own subdomain. **Verdict:** key required (account creation outside lane authority) and the
modeling-relevant endpoints are paid → excluded from the $0 program; ESPN-side coverage (2002+)
supersedes its 2008+ anyway.

### (d) Sports Reference women's basketball — FAIL for ML

Terms of Use, https://www.sports-reference.com/termsofuse.html, "Last Updated: May 19, 2023",
section 5 (accessed 2026-10-05), verbatim prohibitions:

> 5(9): "…without our express written permission, use any automated means to access or use the
> Site, including scripts, bots, scrapers, data miners, or similar software, in a manner that
> adversely impacts site performance or access"

> 5(10): "use any material or Content from the Site, including without limitation any statistics
> or data, (i) to create any database, archive, or other data store that competes with or
> constitutes a material substitute for the services or data stores offered on the Site or by the
> Site's Data Providers…"

> 5(11): "copy or use any material or Content from the Site, including without limitation any
> statistics, data, text, graphics, or images, for purposes of **training, fine-tuning, prompting,
> or instructing artificial intelligence models** or technologies in any manner, including without
> limitation for purposes of (i) generating answers, text, scores, statistics, notes, graphics,
> images, or any other output; or (ii) **supporting machine learning methods used to predict,
> classify, label, or score inputs into the models**"

**Verdict: FAIL.** 5(11) bans exactly the intended use; 5(9)/(10) ban scraping/storage. SR offers
no $0 research license at fetch time.

### (e) Others (one-liners)

- ESPN hidden endpoints (`site.api.espn.com` WNBA scoreboard/summary): UNVERIFIED by this lane;
  ESPN content already reaches us lawfully via the wehoop releases, so direct scraping adds rights
  exposure for no new data. Do not scrape directly.
- stats.wnba.com direct JSON API: same restrictive WNBA ToU as (b); consume only via
  sportsdataverse releases.
- fixturedownload.com CSV fixtures: no clear open-data license at fetch time; UNVERIFIED; skip
  (schedules here are better anyway).
- Kaggle WNBA datasets: require a Kaggle account (no-account constraint) and carry dataset-level
  terms; BLOCKED_NO_ACCOUNT; skip.
- `wnba-stats-raw-json` season bundles (wehoop-wnba-stats-raw releases): whole-season raw JSON from
  stats.wnba.com — relevant only if a future PIT reconstruction needs raw upstream JSON; not pulled.

---

## 2. What was downloaded (all verified-rights, public GitHub release assets, no auth)

| group | release tag | seasons | files | bytes |
|---|---|---|---:|---:|
| `espn_schedules/` | `espn_wnba_schedules` | 2002–2026 (25) csv+parquet each + master.parquet + games_in_data_repo (csv+parquet) + sidecars | 55 | ~17.4 MB |
| `wnba_stats_schedules/` | `wnba_stats_schedules` | 1997–2026 (30) csv.gz each + master csv+parquet + 2025 csv + sidecar | 34 | ~0.33 MB |
| `espn_sample_2025/` | `espn_wnba_team_boxscores` / `espn_wnba_player_boxscores` / `espn_wnba_pbp` | 2025 only: team_box, player_box, play_by_play (csv+parquet each) + sidecars | 9 | ~56.8 MB |
| **total** | | | **98 + audit_results.json** | **76,352 KB** |

Integrity: sha256 of every file recorded in `DATA_MANIFEST.md`; **26 assets byte-verified against
the GitHub API `digest` field (sha256) — 0 mismatches** (73 older assets predate GitHub's digest
population; their sha256 here is the only fingerprint). Publisher sidecars: ESPN schedules
"2026-10-04 06:40:29 EDT", team_box "06:39:35", player_box "06:39:51", pbp "06:39:20",
stats schedules "2026-10-04 10:36:31 EDT". Pull time (this machine, UTC): 2026-10-05T01:46–01:51Z.
`ATTRIBUTION.md` written into the raw directory.

## 3. Audit results (measured by `audit_script.py`, not asserted)

### 3.1 Shape and keys
- ESPN schedules: **6,029 rows, 25 seasons (2002–2026), 6,029 unique game_id, 0 duplicates,
  strict one-row-per-game** (home_id/away_id unique per game_id). 77 columns incl. venue,
  broadcast, status block, `game_json_url`, PBP/box pointer flags.
- Stats schedules: **7,009 rows, 30 seasons (1997–2026), 7,009 unique game_id, 0 duplicates**;
  15 columns; game_id is season-prefixed (`1029700001`, `1021800162`, `1022500001`).
- All season files internally date-sorted ascending (monotonic); no file-order anomalies.

### 3.2 Games per season (actuals; anomalies flagged)
- ESPN side (rows = games incl. Cup/All-Star/playoffs/placeholders):
  2002:272, 2003:256, 2004:238, 2005:239, 2006:258, 2007:243, 2008:259, 2009:243, 2010:221,
  2011:225, 2012:223, 2013:222, 2014:223, 2015:226, 2016:220, 2017:220, 2018:222, 2019:221,
  **2020:147 (COVID "Wubble" season — real, not a gap)**, 2021:211, 2022:241, 2023:263, 2024:264,
  2025:312, 2026:360.
- Stats side: 1997:**115** (league's 8-team, 28-game first season — consistent), 1998:158,
  1999:203, 2000:272, 2001:274, then within ±3 of ESPN for all overlapping seasons.
- Cross-source diff (ESPN − stats), non-zero seasons: 2002:−1, 2003:−1, 2004:−2, 2005:+1, 2006:+1,
  2007:+2, 2009:+2, 2010:+1, 2011:+2, 2013:+1, 2014:+1, 2015:+1, 2017:+1, 2018:+1, 2019:+1,
  2021:+2, 2022:+2, 2023:+3, 2024:+2, 2025:+2 — small, explainable by All-Star rows and
  placeholders (see 3.5); treat as reconciliation noise, not loss.
- Expected-shape sanity: modern seasons ~220 regular-season games (pre-2025 12-team, 40-game =
  240 capacity minus byes), 2020 = 147 (22-game Wubble), 2025 = 312 with 13-team expansion +
  Commissioner's Cup + 24 playoff games; 2026 = 360 including if-necessary placeholders
  (see 3.5). No season shows an impossible count.

### 3.3 Missingness
- ESPN: **0 rows with null scores anywhere** — including unplayed future rows, which are
  **pre-filled 0–0**. status_type_state: `post` 6,012 / `pre` 17. → **Never filter on score
  presence; filter on `status_type_state=='post'` (and exclude Forfeit/Postponed details).**
- Attendance: 0 nulls (2020 wubble rows carry zeros).
- Stats side: 100% of rows carry `home_pts`/`away_pts`; forfeit row has blank `wl` flags.

### 3.4 Timezone semantics (three different flavors — measured)
1. ESPN schedule `date`/`start_date`: **UTC instant**, format `2025-10-11T00:00Z` (this is an
   8 p.m. ET tip-off the prior calendar day). Equals `game_date_time` instant for 94.03% of rows
   (remainder: null `game_date_time` on legacy rows).
2. ESPN box `game_date_time`: **venue-local with numeric offset**, e.g.
   `2025-10-10T20:00:00.000000-0400` (EDT).
3. ESPN PBP `wallclock`: **100% UTC (`Z`-suffixed)**.
4. Stats-side schedule `game_date`: **naive venue-local date** (`1997-06-21`).
→ Canonical modeling key: use stats-side `game_date` (local date) or derive ET from the UTC
instant; never mix ESPN schedule `date` with box `game_date_time` as if same-kind.

### 3.5 Season composition / playoffs / special rows
- `season_type`: 2 (regular) = 5,555 rows; 3 (postseason) = 474 rows. 2025 box: 288 type-2 games
  + 24 type-3 playoff games.
- Commissioner's Cup games are **embedded in the regular-season schedule** (301 rows mention
  "Cup", 2021+).
- All-Star Game appears as a schedule row (14 total, 2004–2026) under team aliases that pollute
  the abbreviation space: `EAST`/`WEST`/`ALL` (legacy), `DEL`/`PAR` (2018 Team Delle Donne/Parker),
  `CLA` (2025 "TEAM CLARK" vs "TEAM COLLIER"), `COOP` (2026 "TEAM COOP"/"TEAM SPOON"),
  `WNBASTARS` (2024 Team WNBA vs Team USA).
- 2026 contains **if-necessary playoff placeholders with `TBD` teams** (7 Finals + Semifinals
  rows, dates through 2026-11-01; 15 rows dated after pull) — pre-filled 0–0, state `pre`.
- Neutral-site flag TRUE on 15 rows (2013–2026, 1–2/season — Cup championships etc.).

### 3.6 Franchise rename/relocation map (verified from the data itself)
Stats-side abbreviations are stable and historically consistent (use these);
ESPN-side abbreviations changed scheme twice and carry noise:
- Utah Starzz `UTA` (ESPN spells `UTH`) 1997–2002 → San Antonio Silver Stars/Stars `SAN` (ESPN
  `SAS`) 2003–2015 → **Dallas Wings `DAL` 2016–**
- Orlando Miracle `ORL` 1999–2002 → **Connecticut Sun `CON` (ESPN `CT`, then `CONN`) 2003–**
- Detroit Shock `DET` 1998–2009 → Tulsa Shock `TUL` 2010–2015 → merges into Dallas Wings 2016
- LA Sparks `LAS` (ESPN `LOS`, then `LA`) → Las Vegas Aces `LVA` (ESPN `LV`) from **2018**
- Defunct (present in 1997–2009 data): Charlotte Sting `CHA` (to 2006), Cleveland Rockers `CLE`
  (to 2003), Houston Comets `HOU` (to 2008), Sacramento Monarchs `SAC` (to 2009), Miami Sol `MIA`
  (2000–2002), Portland Fire `POR` (2000–2002 only)
- Expansion seen in data: Atlanta `ATL` 2008, Chicago `CHI` 2006, Golden State `GSV` (ESPN `GS`)
  2025, Toronto `TOR` + Portland `PDX` (ESPN reuses `POR`) 2026
- **Measured artifact:** ESPN's 2002 file labels all 16 Detroit Shock rows
  `home_abbreviation="TUL"` while `home_display_name="Detroit Shock"` — ESPN abbreviations are
  unreliable before ~2011 and for special teams. **Join on display_name / crosswalk
  (release tag `wnba_crosswalk`), never on raw ESPN abbreviations.**

### 3.7 Ties / forfeits / postponements; injury/lineup; PIT story
- Exactly **1 forfeit in 29 seasons**: 2018-08-03 Washington Mystics vs Las Vegas Aces, recorded
  **0–0**, ESPN `status_type_detail="Forfeit"` (game_id 401018942); present on stats side too
  (game_id 1021800162) with blank win/loss flags. **0 genuine ties.**
- 1 postponement found (2026-07-17 Dallas, "Postponed — Travel Issues - Makeup date July 20").
- Convention for modeling: exclude `status_type_detail ∈ {Forfeit, Postponed}` and any
  `status_type_state != 'post'`; treat 0–0 rows as unscored regardless of completed flag.
- Injury/lineup availability: **no dedicated injury feed** in any wehoop-family release.
  Partial signal only: `player_box` carries `active` / `did_not_play` / `ejected` / `starter` /
  free-text `reason` (2025 sample: 1,224 DNP rows; reasons like "RIGHT KNEE", "ACL",
  "INJURY/ILLNESS", plus "COACH'S DECISION" 6,536 rows). Starting lineups are exactly derivable
  (`starter` median **10.0 rows/game** = 5v5; PBP has 15,299 Substitution events for on-court
  units). Dedicated assets exist but were not pulled: `espn_wnba_game_rosters` (2002–2026,
  29.0 MB), `wnba_stats_lineups` (2026 only, 18.1 MB).
- **PIT (point-in-time) story: NOT_RUN_PIT.** Release assets are current-state snapshots with no
  publication-time columns; a true as-of audit would need the `wehoop-wnba-raw` JSON capture or
  repeated daily pulls. Win-prob features must be built pre-game-safe (rolling windows on
  `game_date`) until a PIT protocol exists.

### 3.8 One-season (2025) sample depth — evidence the modeling layer exists
- `team_box_2025`: 624 rows = 312 games × 2 team-rows, 0 violations; **`points_in_paint`
  100% populated** (team-level PIT-paint available back to 2003); 57 columns incl. four-factor
  stats.
- `player_box_2025`: 7,140 rows / 312 games / 185 unique players / median 23 rows per game.
- `play_by_play_2025`: 121,342 rows / 312 games / median 386.5 plays/game / max period 6 (2OT);
  clock `end_game_seconds_remaining` monotonic-decreasing (verified >98% within sampled game);
  shot coordinates (`coordinate_x/y`) present.
- Box↔schedule gap for 2025: **0 games** (312 = 312).

## 4. Not downloaded (deliberate)

Full-history PBP (ESPN 1,015.9 MB; stats.wnba.com 203.6 MB — the latter covers 1997–2026 if the
modeling lane wants pre-2002 PBP), shots (140.6 MB), game_rosters, lineups, rosters, season
stats, officials, draft, possessions, raw-JSON bundles. Total future full mirror ≈ **+1.4 GB**.

## 5. Verdict and conditions

**PASS** for a $0 WNBA win-probability modeling program (data layer). Conditions:
1. **Rights:** rely on the sportsdataverse-data CC BY 4.0 badge + MIT repo license
   (nflverse-family pattern); internal research use with `ATTRIBUTION.md` attribution; no direct
   scraping of wnba.com / stats.wnba.com / ESPN; no SR (FAIL 5(11)); no balldontlie (key + paid);
   confirm CC BY 4.0 intent with maintainers (one GitHub issue) before any external
   redistribution.
2. **Coverage gaps:** ESPN-side box scores start 2003 (schedules/PBP/player_box 2002);
   1997–2001 available via stats-side schedules (downloaded) and stats-side PBP (available,
   not downloaded). 2020 is a real 22-game COVID season, not a gap.
3. **Filtering spec (mandatory before modeling):** keep only `status_type_state=='post'`;
   drop Forfeit/Postponed rows; drop All-Star and Cup-championship rows (or flag separately);
   drop `TBD`/if-necessary placeholders; join teams via display_name/crosswalk, not ESPN
   abbreviations; canonicalize timestamps per §3.4.
4. **NOT_RUN_PIT** + no injury feed: pre-game-safe feature construction required; injury modeling
   out of scope for $0 data layer.
5. **Operating cost estimate:** current footprint 74.6 MB / 99 files; full mirror ≈ 1.5 GB;
   upstream refresh daily 07:00/14:00 UTC in-season (May–Oct 20), weekly off-season — a weekly
   (or per-game-day) re-pull of changed release assets is negligible bandwidth; no accounts/keys.
