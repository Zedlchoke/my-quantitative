# NFL_DATA_RIGHTS_MATRIX.md — audit-only annex, cycle NBA-WINPROB-PREP-V1

- Task: `nfl-audit-1` | Lane: `NFL_AUDIT` | Role: quant-explorer
- Audit date: **2026-10-04** (all fetch attempts recorded against this date; no data files downloaded — license/metadata/README fetches only)
- Scope: data sources / rights / PIT / coverage audit for a **hypothetical $0, no-signup NFL win-probability MVP**. NO NFL cycle opened, NO model/backtest run, NO downloads of datasets, NO accounts/keys created.
- Rule applied: code license and DATA rights are quoted separately everywhere; anything not verifiable this session = `UNVERIFIED`. Blocked page = `UNVERIFIED`, attempt logged in Incidents.

---

## Tóm tắt điều hành (tiếng Việt — cho owner)

- **Kết luận chính: PASS (có điều kiện).** Một MVP NFL win-probability $0 là khả thi **chỉ bằng hệ sinh thái nflverse**: dữ liệu data releases của repo `nflverse/nflverse-data` được cấp phép **CC BY 4.0** (đã xác minh toàn văn LICENSE.md ngày 2026-10-04) — cho phép tải về, lưu trữ, nghiên cứu nội bộ/ML và phân phối lại với điều kiện ghi công (attribution).
- **Đủ 4/5 lớp dữ liệu**: lịch/kết quả (games.csv, cập nhật mỗi ~5 phút trong mùa giải, có `timestamp.json` làm mốc as-of), đội/cầu thủ (rosters/players, `gsis_id`), play-by-play **từ 1999** (nflfastR README: "The package contains NFL play-by-play data back to 1999"), chấn thương **từ 2009** (có `date_modified`, cập nhật 7AM UTC hằng ngày trong mùa giải).
- **Lớp 5 (odds): KHÔNG có nguồn $0-không-cần-đăng-ký với quyền rõ ràng.** The Odds API có tier miễn phí 500 credits/tháng (có historical odds) nhưng **bắt buộc đăng ký lấy key** → `NOT_RUN` cho chương trình này. Cột `spread_line`/moneyline trong games.csv là proxy duy nhất trong phạm vi — coi như closing line, rủi ro leakage.
- **TUYỆT ĐỐI KHÔNG** scrape Pro Football Reference: điều khoản Sports Reference mục 5(10) cấm tạo database thay thế và 5(11) cấm dùng dữ liệu cho AI/ML ("training, fine-tuning, prompting... supporting machine learning methods used to predict, classify, label, or score") → **FAIL cho ML**.
- **TUYỆT ĐỐI KHÔNG** scrape NFL.com: điều khoản cấm "Systematic retrieval of data" và cấm archiving/republishing/downloading → **FAIL cho truy cập tự động**. Dữ liệu NFL chính thức đi qua các nhà cung cấp được cấp phép (context, không overclaim).
- **Cẩn trọng nhãn dữ liệu `nflverse/nfldata` (Lee Sharpe)**: repo này **KHÔNG có file license** (GitHub license: null) — chỉ dùng các bản release tại `nflverse-data` (CC-BY-4.0); `draft_picks`/rosters cũ ghi công nguồn PFR (chuỗi quyền thượng nguồn).
- **PIT/leakage cần xử lý trước backtest**: (i) NFL chỉnh sửa pbp hồi tố giữa tuần — "Thursday's load_pbp() is the cleanest data we have"; (ii) `date_modified` của injuries KHÔNG phải thời điểm công bố lịch sử; (iii) cột betting line trong games.csv là closing line; (iv) phải snapshot `timestamp.json` + asset `updated_at` ở mỗi lần pull.
- **Phân biệt với chương trình NBA**: file này là annex audit-only của NBA-WINPROB-PREP-V1, KHÔNG mở NFL cycle, KHÔNG trộn kết luận NBA/NFL (xem mục cuối).

---

## Matrix (one row per source)

Verdict shorthand — **D+S** = download+store; **ML** = internal research+ML; **RD** = redistribution. Full verbatim evidence in blocks E1–E17 below.

| # | Source | Class | Season coverage | Granularity | As-of/PIT marker | Identity fields | Access (URL) | Fee/key/rate-limit | Completeness/risks | Leakage risk | License verdict D+S / ML / RD | Evidence + verbatim quote |
|---|--------|-------|-----------------|-------------|------------------|-----------------|--------------|--------------------|--------------------|--------------|-------------------------------|---------------------------|
| R1 | nflverse-data release `pbp` (nflfastR ecosystem) | 3 play-by-play | **1999+** (README verbatim); cp/xyac from 2006 | play level, ~372 cols | "Data updated" header; nightly during season; NFL retro-corrections Wed→Thu | `game_id` (`2021_01_ARI_TEN`), `old_game_id`, gsis | github.com/nflverse/nflverse-data/releases/tag/pbp | Free, no key, GitHub rate limits only | Post-game compilation; 1999-2000 from third-party JSON (Nick Shoemaker); FTN charting only 1999-2005 scrambles | HIGH if used naively — data is post-game; WP/EP columns are model outputs | **PASS / PASS / PASS (CC-BY-4.0, attribution required)** | E1, E2, E3 |
| R2 | nflverse-data release `schedules` (games.csv, "as maintained by Lee Sharpe") | 1 schedule & results | Doc says begin 2006 (stale DATASETS.md); current asset spans all nflverse seasons — exact earliest season UNVERIFIED (no data download this session) | game level, 46 cols | `timestamp.json`/`timestamp.txt` per release; asset `updated_at` 2026-10-04T10:16:16Z; "updates very 5 minutes during the season" [sic] | `game_id`, `gsis`, `pfr`, `pff`, `espn`, `ftn`, `nfl_detail_id`, `old_game_id` | github.com/nflverse/nflverse-data/releases/tag/schedules | Free, no key | Scores `NA` pre-game (good PIT property); betting-line cols are closing values | `spread_line`, `away/home_moneyline`, spread odds = closing lines → treat as post-kickoff unless timing proven | **PASS / PASS / PASS (CC-BY-4.0)** | E2, E4, E5, E6 |
| R3 | nflverse-data releases `rosters`/`players`/`player_stats`/`weekly_rosters` | 2 teams & players | rosters daily 7AM UTC; `players` static release 2022; player_stats week-level nightly | player-season / player-week | release asset `updated_at`; "updates every day at 7AM UTC" | `gsis_id` (primary for pbp), `pfr_id`, `espn_id`, `player_id` (00-…) | github.com/nflverse/nflverse-data/releases | Free, no key | Name-join risk acknowledged upstream (DATASETS.md warns on weak joins) | LOW for roster composition (pre-game known) | **PASS / PASS / PASS (CC-BY-4.0)** | E2, E7 |
| R4 | nflverse-data release `injuries` | 4 injuries | **2009+** (docs verbatim: "data available since 2009"); assets injuries_2009.csv… | player-week; official + practice report fields | `date_modified` = "Date and time that injury information was updated"; "updates every day at 7AM UTC throughout the season" | `gsis_id`, team, position, name | github.com/nflverse/nflverse-data/releases/tag/injuries | Free, no key | Upstream = "an API for weekly injury report data" (upstream provider UNVERIFIED); no per-report-day publication timestamps | `date_modified` is NOT historical announcement time → derive PIT from week+status, not date_modified | **PASS / PASS / PASS (CC-BY-4.0); upstream provenance UNVERIFIED** | E2, E8, E9 |
| R5 | nflverse/nfldata (Lee Sharpe: games/standings/teams/colors/logos/draft_picks legacy + DATASETS.md) | 1/2 | standings 2002+; games doc "begins with the 2006 NFL season"; draft_picks 2000+ | game/team/season | none (static repo files) | `teams.csv` abbreviation crosswalk: `team` vs `nfl`/`pfr`/`pff`/`fo` ("consistently favors JAX over JAC, and LAR over LA") | github.com/nflverse/nfldata | Free, no key | **Repo has NO license file** (GitHub license: null; LICENSE/LICENSE.md 404) → all-rights-reserved default; draft_picks/legacy rosters credit PFR upstream | Static docs stale (habitatring.com links) | **D+S: UNVERIFIED / ML: UNVERIFIED / RD: UNVERIFIED** — prefer R1–R4 equivalents | E10, E11, E12 |
| R6 | nflfastR (R package: code + WP/EP model artifacts) | tooling/3 | n/a (code) | n/a | package version | n/a | github.com/nflverse/nflfastR | Free, OSS | Code license ≠ data license; WP models ingest pre-game spread | Model WP-with-spread embeds market info | Code: **PASS** ("License: MIT + file LICENSE"); bundled model artifacts trained on scraped data: UNVERIFIED for redistribution | E13, E14 |
| R7 | nflreadr / nflreadpy (access tooling) | tooling | n/a | n/a | n/a | n/a | nflreadr.nflverse.com | Free, OSS | Explicit data disclaimer — nflverse grants no data rights | — | Code: **PASS** (MIT + file LICENSE); data disclaimer verbatim E15 | E15, E16 |
| R8 | Pro Football Reference (Sports Reference family) | 1/2/3 (site) | 1922+ (site claim not re-verified) | game/play aggregations | none contractual | pfr game/player ids | pro-football-reference.com | Free browsing; no API | — | — | **FAIL for ML** — 5(10) substitute-database + 5(11) AI/ML prohibition; 5(9) restricts automated access; license "revocable" | E17 |
| R9 | NFL.com official | 1/2/4 | n/a | n/a | n/a | n/a | nfl.com/help/terms, nfl.com/terms | Free browsing | Official distribution is via licensed providers (context statement, no overclaim) | — | **FAIL for automated access** — "Systematic retrieval… prohibited"; Subscriptions terms ban archiving/republishing/downloading + scraping | E18, E19 |
| R10 | ESPN hidden endpoints (site.api.espn.com) | 1/2/3 | current seasons | event-level JSON | none | espn event/team ids | site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard | Free, no key (probed live 2026-10-04, season 2026 returned) | **No published API terms found** → rights UNVERIFIED | Endpoint may change/break silently | **UNVERIFIED / UNVERIFIED / UNVERIFIED** — cannot be load-bearing | E20 |
| R11 | balldontlie NFL API | 1/2 | per docs, sport-specific tiers | game/player/team | none stated | their ids | docs.balldontlie.io | **API key required** ("An API key is required."); free tier 5 req/min, limited endpoints | No data license stated | — | **BLOCKED_NO_KEY** for $0-no-signup; rights UNVERIFIED | E21 |
| R12 | Tank01 NFL API (RapidAPI) | 1/2/3 | current | varies | none | their ids | rapidapi.com/tank01/api/tank01-nfl-live-in-game-real-time-statistics-nfl | RapidAPI **account + key required** (free tier exists) | No clear data license | — | **BLOCKED_NO_KEY**; rights UNVERIFIED | E22 |
| R13 | fixturedownload.com NFL schedules | 1 | current season feeds (nfl-2026 feed HTTP 200) | game level | "Fixtures are kept up to date as much as possible, but there may be changes mid-season." | their ids only | fixturedownload.com (CSV/JSON/ICS, no key) | Free, no key | Terms page is a generic website ToC: NO data license; accuracy disclaimed | Scores/updates timing unstated | **D+S: UNVERIFIED / ML: UNVERIFIED / RD: UNVERIFIED** — not needed given R2 | E23 |
| R14 | Official NFL injury-report policy (designations & timing) | 4 | current | report designations | — | — | operations.nfl.com (page not located) | — | Designations Out/Doubtful/Questionable confirmed only via secondary sources; "Probable" removed 2016 | — | **UNVERIFIED** — official policy page not found in session (attempts logged) | E24 |
| R15 | Pro Sports Transactions (football) | 2/4 (transactions) | long history (site claim unverified) | transaction rows | none | — | prosportstransactions.com/football/ | Free browsing (human) | **HTTP 403 bot-blocked this session** → content and rights UNVERIFIED | — | **UNVERIFIED** (blocked page; no circumvention attempted, per scope) | E25 |
| R16 | The Odds API | 5 odds | historical "back to 2020" | event/odds snapshots | snapshot API | their event ids | the-odds-api.com | **Signup key required**; free Starter 500 credits/mo incl. "Historical Odds"; scale = paid ($30–$249/mo) | Redistribution of odds data typically restricted — terms not audited (account-gated) | Closing vs snapshot timing must be engineered | **NOT_RUN for this program** (no-signup constraint); no alternative $0-no-signup source with clear rights found | E26 |

**Class 5 (odds) plain statement:** No $0, no-signup source with historical NFL odds and clear rights was found. The Odds API requires a key (signup) even for the free tier → outside this program's constraints → `NOT_RUN`. games.csv `spread_line`/moneyline columns (R2) are the only in-scope market proxy, carrying closing-line leakage risk.

---

## Verbatim evidence (all fetched 2026-10-04 unless noted)

### E1 — nflverse-data LICENSE.md (the DATA license)
URL: https://raw.githubusercontent.com/nflverse/nflverse-data/main/LICENSE.md — full text fetched and read; identified by GitHub API as `CC-BY-4.0` ("Creative Commons Attribution 4.0 International").
- Title: "Creative Commons Attribution 4.0 International Public License"
- Grant (Section 2(a)(1)): "the Licensor hereby grants You a worldwide, royalty-free, non-sublicensable, non-exclusive, irrevocable license to exercise the Licensed Rights in the Licensed Material to: a. reproduce and Share the Licensed Material, in whole or in part; and b. produce, reproduce, and Share Adapted Material."
- Database rights (Section 4(a)): "Section 2(a)(1) grants You the right to extract, reuse, reproduce, and Share all or a substantial portion of the contents of the database"
- Attribution (Section 3(a)(1)): must retain creator identification, copyright notice, license notice, disclaimer notice, URI "to the extent reasonably practicable", indicate modifications, and license the material under the same Public License when Shared.
- No-endorsement (Section 2(a)(6)): "Nothing in this Public License constitutes or may be construed as permission to assert or imply that You are, or that Your use of the Licensed Material is, connected with, or sponsored, endorsed, or granted official status by, the Licensor"
- Warranty (Section 5(a)): "THE LICENSOR OFFERS THE LICENSED MATERIAL AS-IS AND AS-AVAILABLE... NO REPRESENTATIONS OR WARRANTIES OF ANY KIND... ACCURACY"

### E2 — nflverse-data README
URL: https://github.com/nflverse/nflverse-data — "This repository holds automated data releases for nflverse projects (i.e. all of the data powered/scraped via GitHub Actions)." — "You can download data hosted here with the `{nflreadr}` package, or manually download and access the releases page." (No affiliation-with-NFL statement on the README; the CC license's no-endorsement clause is the only related protection.)

### E3 — nflfastR README (provenance + coverage)
URL: https://github.com/nflverse/nflfastR (README fetched 2026-10-04)
- "The package contains NFL play-by-play data back to 1999"
- "Hosts [a release of play-by-play data going back to 1999](https://github.com/nflverse/nflverse-data/releases/tag/pbp) for very quick access"
- "These data sets include play-by-play data of complete seasons going back to 1999 and are updated nightly during the season."
- Provenance: "To Nick Shoemaker for finding and making available JSON-formatted NFL play-by-play back to 1999 (`nflfastR` uses this source for 1999 and 2000 and previously also used it for 2001-2010)"; "To Lau Sze Yui for developing a scraping function to access JSON-formatted NFL play-by-play beginning in 2001"; "To Aaron Schatz and FTN Fantasy for providing charting data to correctly mark scrambles in the 1999-2005 seasons"; "To Lee Sharpe for curating a resource for game information"
- Win-probability relevance: "`nflfastR` includes two win probability models: one with and one without incorporating the pre-game spread."

### E4 — nflfastR DESCRIPTION / LICENSE (the CODE license)
- DESCRIPTION: "License: MIT + file LICENSE"
- LICENSE file (stub only): "YEAR: 2020 / COPYRIGHT HOLDER: Sebastian Carl; Ben Baldwin"
→ Code = MIT. **This is a different thing from data rights (E1).**

### E5 — nflreadr update-schedule article (cadence + retro corrections)
URL: https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html (fetched 2026-10-04)
- Play-by-play: "on a nightly basis after each game day (and additionally at specific points on game days) during the season"; raw JSON "usually available within 15 minutes after a game has ended"
- Games/Schedules: "updates very 5 minutes during the season" [sic — typo in source]
- Injuries: "updates every day at 7AM UTC throughout the season"
- Rosters / depth charts: "updates every day at 7AM UTC"
- Retro-correction practice: recommendation to "update the data again during the night from Wednesday to Thursday"; "Thursday's load_pbp() is the cleanest data we have."
- Depth charts post-2024: each update adds "a new ISO8601-formatted timestamp" (the only dataset with true per-update timestamps found)

### E6 — nflverse-data schedules release metadata (as-of evidence)
GitHub API releases/tags/schedules (fetched 2026-10-04): assets `games.csv`, `games.parquet`, `games.rds` all `updated_at 2026-10-04T10:16:16Z`, plus `timestamp.json` / `timestamp.txt` (per-pull as-of marker). pbp release tag exists (`pbp`, initial publish 2022-01-28). Injuries release tag contains `injuries_2009.csv` … (coverage from 2009 confirmed at asset level).

### E7 — nflreadr reference pages (schedules, players)
- load_schedules: "This returns game/schedule information as maintained by Lee Sharpe." — "Issues with this data should be filed here: https://github.com/nflverse/nfldata" — example output shows 46 columns including `gsis`, `nfl_detail_id`, `pfr`, `pff`, `espn`, `ftn`, `spread_line`, `away_moneyline`, `home_moneyline`.
- load_injuries: "Data collected from an API for weekly injury report data." — "data available since 2009."

### E8 — nflreadr data dictionary — injuries (PIT-relevant fields)
URL: https://nflreadr.nflverse.com/articles/dictionary_injuries.html — fields include `report_primary_injury` ("Primary injury listed on official injury report"), `report_status` ("Player's status for game on official injury report"), `practice_status` ("Player's participation in practice"), and `date_modified` ("Date and time that injury information was updated"). NOTE: `date_modified` reflects last update of the compiled row, not the historical per-report-day announcement time.

### E9 — nflreadr README Terms of Use (data disclaimer)
URL: https://github.com/nflverse/nflreadr — "The R code for this package is released as open source under the MIT License. NFL data accessed by this package belong to their respective owners, and are governed by their terms of use." — Data repositories listed: nflverse/nflverse-data, nflverse/nfldata, nflverse/espnscrapeR-data, dynastyprocess/data, ffverse/ffopportunity. DESCRIPTION: "License: MIT + file LICENSE".

### E10 — nflverse/nfldata (Lee Sharpe) — NO data license found
- GitHub API repo metadata (fetched 2026-10-04): description "NFL Data (by Lee Sharpe)", `license: null`, default branch `master`, pushed 2026-10-04 (actively maintained).
- Probes 404: `LICENSE`, `LICENSE.md` on master. → Data files in THIS repo are **all-rights-reserved by default**; rights UNVERIFIED. Use nflverse-data release equivalents (CC-BY-4.0) instead. (Repo `leesharpe/nfldata` redirects here — API returned nulls on the old slug.)

### E11 — nfldata DATASETS.md (coverage + identity mapping + upstream credit)
URL: https://raw.githubusercontent.com/nflverse/nfldata/master/DATASETS.md
- Games: "Data begins with the 2006 NFL season. Does not include preseason." (doc references stale `habitatring.com/games.csv` hosting — treat coverage statement as stale; current release spans more seasons, exact earliest UNVERIFIED)
- `game_id`: "The ID of the game as assigned by the NFL."
- teams.csv: "This consistently favors `JAX` over `JAC`, and `LAR` over `LA`." + columns `nfl` ("The team abbreviation used by the NFL"), `pfr`, `pff`, `fo` — the canonical abbreviation-crosswalk table.
- draft_picks: "comes from the excellent Pro Football Reference" — upstream chain to PFR (whose ML terms FAIL, E17).
- Rosters (legacy): "Data begins with the 2006 NFL season and comes from Pro Football Reference."
- Standings: "Data begins with the 2002 NFL season."
- Join warning (draft picks): "the weaker the join, the more likely it results the risk of false positives and duplicate rows"

### E12 — nflverse-data automation page — upstream sources
- Participation pre-2023: "from NFL NGS"; 2023+ "courtesy of FTN"; weekly NGS "provided by NFL Next Gen Stats"; snap counts/advstats from Pro Football Reference; pbp corrections attributed to "the NFL". Page contains NO license statement of its own (E1 governs).

### E13 — nflreadpy exists for Python access ("For Python access to nflverse data, please check out nflreadpy" — nflreadr README).

### E14 — nflfastR README (model/leakage note) — see E3 last bullet (WP models incorporate pre-game spread).

### E15 — nflreadr Terms of Use — see E9.

### E16 — nflreadr LICENSE.html (MIT text page) — HTTP 200 on 2026-10-04 (not re-quoted; README statement in E9 is the operative disclaimer).

### E17 — Sports Reference (Pro Football Reference) Terms of Use — **FAIL for ML**
URL: https://www.sports-reference.com/termsofuse.html (fetched 2026-10-04 via reader; re-fetch via curl returned empty and WebFetch returned 403 — bot protection; quotes below are from the successful fetch, "Last Updated: May 19, 2023")
- License grant: "a limited, personal, non-exclusive, non-sublicensable, non-assignable, non-transferable, and revocable license"
- **5(9) automated access**: "without our express written permission, use any automated means to access or use the Site, including scripts, bots, scrapers, data miners, or similar software, in a manner that adversely impacts site performance or access; or"
- **5(10) substitute database**: "use any material or Content from the Site, including without limitation any statistics or data, (i) to create any database, archive, or other data store that competes with or constitutes a material substitute for the services or data stores offered on the Site or by the Site's Data Providers or (ii) to provide any service that competes with or constitutes a material substitute for the services or data stores offered on the Site or by the Site's Data Providers; or"
- **5(11) AI/ML**: "copy or use any material or Content from the Site, including without limitation any statistics, data, text, graphics, or images, for purposes of training, fine-tuning, prompting, or instructing artificial intelligence models or technologies in any manner, including without limitation for purposes of (i) generating answers, text, scores, statistics, notes, graphics, images, or any other output; or (ii) supporting machine learning methods used to predict, classify, label, or score inputs into the models; or"
→ Verdict for ML use: **FAIL**. Storing PFR-derived data as a research store also collides with 5(10). Prohibits both direct scraping AND building ML on their data.

### E18 — NFL.com Website Terms and Conditions — **FAIL for automated access**
URL: https://www.nfl.com/help/terms/ (fetched 2026-10-04; page shows "Updated: May 16, 2024")
- Section 1.3 (Permitted Uses): "You may use the Services solely for your own individual non-commercial and informational purposes only."
- Section 1.3: "Systematic retrieval of data or other content from the Services ... is prohibited absent our express prior written consent."
- Section 11(f): "use or attempt to use any engine, software, tool, agent or other device or mechanism" "(including, browsers, spiders, robots, avatars or intelligent agents)" "to harvest or otherwise collect information from the Services to be used for any commercial purpose"

### E19 — NFL.com Subscriptions Terms (NFL+) — reinforces prohibition
URL: https://www.nfl.com/terms/ (fetched 2026-10-04; "Effective Date: June 8, 2012", "Updated: September 4, 2026"; page states it is "governed by the NFL.com Terms and Conditions" at www.NFL.com/help/terms)
- Non-commercial: "The Products and any content accessed through the Products are for your personal, non-commercial use only and may not be shared with anyone outside of your household."
- Archiving/download: "You are expressly prohibited from archiving, republishing, retransmitting, and/or reproducing the content accessible via NFL+, NFL+ Premium and/or the Add-On Product(s)... You are also expressly prohibited from downloading the content accessible via NFL+, NFL+ Premium and/or the Add-On Product(s)."
- Scraping: "You agree that you will not attempt to, or assist any third party in attempting to, bypass any robot exclusion headers or other measures we take to restrict access to the Products (or services or content therein), or use any software, technology, or device to send content or messages, scrape, spider or crawl the Products (or services or content therein), or harvest or manipulate data on or from the Products (or services or content therein)."
- Context (no overclaim): official NFL data distribution is via licensed providers; nothing on these pages grants programmatic reuse rights.

### E20 — ESPN hidden endpoints
Probe 2026-10-04: `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard` returned live JSON (league id 28, season 2026). No published API terms of use found for these undocumented endpoints → **UNVERIFIED**; cannot be load-bearing for a rights-clean pipeline. (nflverse's `espn_data` release exists inside nflverse-data and is CC-BY-4.0 as distributed there — prefer that route if ESPN-derived data is needed.)

### E21 — balldontlie NFL
URL: https://docs.balldontlie.io (fetched 2026-10-04): "An API key is required." — key obtained by "creating a free account"; free tier 5 requests/min; "Paid tiers do not apply across sports." No data license/Terms quoted on docs page. → **BLOCKED_NO_KEY** for a $0-no-signup program; data rights UNVERIFIED.

### E22 — Tank01 NFL (RapidAPI)
tank01.com: "All APIs are hosted on RapidAPI." RapidAPI listing requires account + `X-RapidAPI-Key`; free tier exists (community-confirmed, not re-verified this session). No clear data license. → **BLOCKED_NO_KEY**; rights UNVERIFIED.

### E23 — fixturedownload.com
- Feed probe: `https://fixturedownload.com/feed/json/nfl-2026` HTTP 200 (no key).
- Terms page https://fixturedownload.com/terms (fetched 2026-10-04) is a generic website ToC: "You acknowledge that such information and materials may contain inaccuracies or errors and we expressly exclude liability for any such inaccuracies or errors to the fullest extent permitted by law." — **No grant of data rights, no license for reuse/redistribution** → rights UNVERIFIED. Not needed given R2.

### E24 — Official NFL injury report policy
Designations Out/Doubtful/Questionable (and removal of "Probable" in 2016, Friday game-status reports, mandatory reporting since 1947) confirmed **only via secondary sources** found in web search this session. The official operations.nfl.com policy page was NOT located (search attempts: 1 timed out at 60s, 1 filtered search returned no official page). → Publication timing (days/time) = **UNVERIFIED**; do not encode timing claims into features without direct verification.

### E25 — Pro Sports Transactions football
`https://www.prosportstransactions.com/football/` returned **HTTP 403** (bot protection) on 2026-10-04. Content and rights **UNVERIFIED**. No circumvention attempted (per audit scope: blocked page = UNVERIFIED verdict).

### E26 — The Odds API
URL: https://the-odds-api.com (fetched 2026-10-04): "Subscribe to receive your API key via email" (key required). Free "Starter" plan: "FREE", "500 credits" per month, features include "All sports", "Historical Odds"; historical snapshots "back to 2020". Paid tiers: "20K — $30", "100K — $59", "5M — $119", "15M — $249" per month. → Requires signup key → **NOT_RUN** for a $0-no-signup program; account-gated terms not audited; no other $0-no-signup historical NFL odds source with clear rights found.

---

## PIT / identity / leakage audit notes (cross-cutting)

1. **PIT markers that exist**: schedules release `timestamp.json`/`timestamp.txt` + GitHub asset `updated_at` (per-pull as-of evidence); injuries `date_modified`; depth-charts ISO8601 update timestamps (post-2024); pbp "Data updated" header. **None of these reconstruct historical announcement times** — for a win-prob backtest you must snapshot vintages yourself (store pull timestamp + release asset hash with every fetch).
2. **Retroactive corrections**: NFL corrects pbp data between Wed–Thu ("Thursday's load_pbp() is the cleanest data we have"). Never mix vintages inside one backtest; record pull dates per file.
3. **Leakage traps**: (a) games.csv `spread_line`/`total_line`/moneyline/spread-odds columns are closing values — exclude from features unless pre-game availability timing is independently proven; (b) all nflverse pbp is compiled post-game — for in-game WP you need within-game ordering from play clock/sequence fields, not file vintage; (c) injuries `date_modified` ≠ announcement time; (d) nflfastR's own WP model (with-spread variant) embeds market info.
4. **Identity mapping to audit before any join**: team abbreviations (canonical `teams.csv` favors `JAX` over `JAC`, `LAR` over `LA`; separate `nfl`/`pfr`/`pff`/`fo` columns); game crosswalks (`game_id` ↔ `gsis` ↔ `pfr` ↔ `pff` ↔ `espn` ↔ `ftn` ↔ `old_game_id`); player join must use `gsis_id` (injuries + pbp both carry it); DATASETS.md explicitly warns name-based joins produce "false positives and duplicate rows".
5. **Upstream-rights chain**: nflverse pbp/schedules are CC-BY-4.0 **as distributed by nflverse**, which scraped upstream sources (NFL JSON feeds, ESPN, FTN, PFR, NGS). The license is nflverse's grant; residual upstream-rights risk sits with nflverse's claim, not with a written NFL authorization. Acceptable research posture: use it, attribute it, do not re-sell it; revisit if commercialization is ever proposed.

---

## VERDICT — $0 NFL win-probability MVP, TODAY (2026-10-04)

**PASS (conditional)** — a $0, no-signup NFL win-probability research MVP is feasible **on nflverse-data alone** (CC-BY-4.0): schedule/results, teams/players, play-by-play 1999+, injuries 2009+. Class 5 (odds) is **NOT_RUN/BLOCKED** (no $0-no-signup source with clear rights) — the MVP proceeds without odds features or uses games.csv closing lines only as evaluation context, never as a feature.

**Numbered conditions before ANY backtest:**
1. **Attribution**: ship a CREDITS file satisfying CC-BY-4.0 Section 3(a) for every nflverse-data artifact used (creator, license notice, URI, modification indicator). Redistribution allowed only with same conditions.
2. **Vintage discipline**: every pull must persist (release tag, asset `updated_at`, `timestamp.json`, local pull time). No mixing of vintages; document the Wed→Thu NFL correction window.
3. **No forbidden sources in-pipeline**: no scraping of Pro Football Reference (E17 FAIL: 5(9)/5(10)/5(11)) and no automated collection from NFL.com (E18/E19 FAIL). This also bars ingesting PFR-derived legacy files from `nflverse/nfldata` (draft_picks, legacy rosters) without accepting the upstream chain — prefer nflverse-data releases only.
4. **Leakage quarantine**: games.csv betting columns (`spread_line`, `total_line`, moneyline, spread odds) excluded from features unless pre-game availability timing is proven by vintage snapshots; injuries features derive PIT from (season, week, `report_status`/`practice_status`), never from `date_modified`.
5. **Identity audit**: implement + test the abbreviation crosswalk (`JAX`/`JAC`, `LA`/`LAR` and the `nfl`/`pfr`/`pff`/`fo` map) and require `gsis_id` for player-level joins; log unmatched-rate per season as a gate metric.
6. **Coverage verification**: before locking a training window, empirically confirm earliest seasons of games.csv (doc says 2006; asset may span 1999+) and pbp (README says 1999) — doc claims are not measurements.
7. **Odds class stays closed**: any odds feature requires an owner decision (The Odds API key = signup; paid tiers for scale). Until then the MVP is odds-free.
8. **Injury-report timing**: official publication timing (days/time) is UNVERIFIED (E24) — do not encode timing assumptions without first locating the official policy page.
9. **Scope guard**: this annex authorizes NO NFL cycle. Any NFL build needs its own cycle, gates, and owner sign-off, per the mission invariant.

## Separation from the NBA program

This file is an **audit-only annex inside cycle NBA-WINPROB-PREP-V1** (owner addendum 2026-10-04). It opens **no NFL cycle**, runs **no NFL model/backtest**, and its verdicts are **NFL-specific**. Nothing here may be read as evidence about NBA data sources, and NBA lane conclusions must not be imported into this matrix. The two programs share only the factory process (gates, PIT discipline, trial accounting), not data or results.

## Incident log / UNVERIFIED attempts (2026-10-04)

- prosportstransactions.com/football/ → HTTP 403 (bot protection). UNVERIFIED; no circumvention attempted.
- sports-reference.com/termsofuse.html → reader fetch OK; curl re-fetch returned empty body; WebFetch re-verify returned 403. Quotes above are from the successful fetch of the same date.
- nfl.com/help/terms/ via curl → 69KB JS shell without terms text (JS-rendered); reader + WebFetch fetches succeeded and are quoted.
- First WebSearch for the official NFL injury-report policy timed out (60s); second (domain-filtered) search did not surface an operations.nfl.com policy page → E24 UNVERIFIED.
- leesharpe/nfldata GitHub API → nulls (repo moved to nflverse/nfldata; old slug redirects).
- No dataset files were downloaded (audit scope); season-coverage starts beyond documented claims are marked UNVERIFIED.
- Tank01 free-tier generosity and balldontlie NFL free-tier endpoint coverage are community/web-doc claims, not account-verified (no accounts created, per scope).
