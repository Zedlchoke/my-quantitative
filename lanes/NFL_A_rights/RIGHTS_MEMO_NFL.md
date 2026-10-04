# RIGHTS_MEMO_NFL.md — Lane A (NFL_A_rights), cycle NFL-WINPROB-PREP-V1

- Task: `nfl-a-rights` | Lane: `NFL_A_rights` | Role: quant-explorer
- Re-verification date: **2026-10-04** (all fetches live this date; metadata/README/license fetches ONLY — zero dataset files downloaded)
- Basis: independent live re-verification of the load-bearing subset of
  `lanes/NFL_AUDIT/NFL_DATA_RIGHTS_MATRIX.md` (annex audit, NBA-WINPROB-PREP-V1, 2026-10-04),
  then a fresh verdict for this cycle's download plan
  (`games.csv` + `timestamp.json` + 5 pbp parquets from nflverse-data releases).
- Worktree HEAD at start: `8deb036d9ebb74e24de99e8c3461e7cea9b9dc43`
  (branch `orca/nfl-winprob-prep-v1-integration`, tree clean).

---

## 1. Re-verification log (verbatim quotes, access date 2026-10-04)

### RV1 — nflverse-data LICENSE.md — CONFIRMED CC BY 4.0
URL: https://raw.githubusercontent.com/nflverse/nflverse-data/main/LICENSE.md
(fetched in full via reader + clause-by-clause via second fetcher; both agree)
- Title: **"Creative Commons Attribution 4.0 International Public License"**
- Grant, sec 2(a)(1): "the Licensor hereby grants You a worldwide, royalty-free, non-sublicensable, non-exclusive, irrevocable license" ... to "reproduce and Share the Licensed Material, in whole or in part" and "produce, reproduce, and Share Adapted Material" (full grant text matches the canonical CC BY 4.0 text and the prior audit E1).
- Database rights, sec 4: "grants You the right to extract, reuse, reproduce, and Share all or a substantial portion of the contents of the database"
- Attribution, sec 3(a)(1): "If You Share the Licensed Material (including in modified form), You must:" "retain the following if it is supplied by the Licensor with the Licensed Material:" (identification of creator, copyright notice, license notice, disclaimer notice, license URI — to the extent reasonably practicable; must indicate modifications).
- No-endorsement, sec 2(a)(6): "Nothing in this Public License constitutes or may be construed as permission to assert or imply that You are, or that Your use of the Licensed Material is, connected with, or sponsored, endorsed, or granted official status by, the Licensor"
- Warranty, sec 5(a): "THE LICENSOR OFFERS THE LICENSED MATERIAL AS-IS AND AS-AVAILABLE, AND MAKES NO REPRESENTATIONS OR WARRANTIES OF ANY KIND" (incl. accuracy — no warranty of correctness).

### RV2 — nflverse-data README — releases repo; NO NFL-affiliation statement
URL: https://github.com/nflverse/nflverse-data
- "This repository holds automated data releases for nflverse projects" "(i.e. all of the data powered/scraped via GitHub Actions)."
- "You can download data hosted here with the {nflreadr} package, or manually download and access the releases page."
- **No statement of affiliation with or endorsement by the NFL appears on the page.** Sidebar license: "CC-BY-4.0 license".

### RV3 — nflverse/nfldata API license field — NULL (all-rights-reserved default)
URL: https://api.github.com/repos/nflverse/nfldata (fetched twice, both agree)
- `"license": null` (field present, no license object)
- `"description": "NFL Data (by Lee Sharpe)"`, `"default_branch": "master"`, `"pushed_at": "2026-10-04T12:15:14Z"` (actively maintained)
→ **No license = all-rights-reserved default. Repo files (incl. draft_picks, legacy rosters) are banned for this program.** Note: the schedules release body states "Data maintained in Lee Sharpe's nfldata" — but the rights that govern what we download are those of the **nflverse-data release distribution (CC BY 4.0)**, not the upstream repo.

### RV4 — nflreadr README data disclaimer — CONFIRMED
URL: https://github.com/nflverse/nflreadr
- "The R code for this package is released as open source under the MIT License."
- "NFL data accessed by this package belong to their respective owners, and are governed by their terms of use."
→ nflverse itself grants **no data rights**; the only affirmative grant we rely on is the CC BY 4.0 LICENSE.md inside nflverse-data (RV1).

### RV5 — Sports Reference ToU 5(11) AI/ML prohibition — CONFIRMED (PFR ban basis)
URL: https://www.sports-reference.com/termsofuse.html (reader fetch; page states "Last Updated: May 19, 2023")
- 5(11) verbatim: "copy or use any material or Content from the Site, including without limitation any statistics, data, text, graphics, or images, for purposes of training, fine-tuning, prompting, or instructing artificial intelligence models or technologies in any manner, including without limitation for purposes of (i) generating answers, text, scores, statistics, notes, graphics, images, or any other output; or (ii) supporting machine learning methods used to predict, classify, label, or score inputs into the models; or"
- Also re-confirmed: 5(9) automated-access restriction and 5(10) substitute-database prohibition; license is "limited, personal, ... and revocable".
→ **Pro Football Reference: FAIL for ML and for building a data store. Do not scrape; do not ingest PFR-derived files.**

### RV6 — nflreadr update-schedule article — PIT semantics CONFIRMED
URL: https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html
- pbp cadence: "on a nightly basis after each game day (and additionally at specific points on game days) during the season."
- raw JSON: "`nflfastR::build_nflfastR_pbp()` parses raw pbp json files we save," "usually available within 15 minutes after a game has ended."
- Retro-corrections: "In all cases, it is recommended to update the data again during the night from Wednesday to Thursday" "... in order to also receive the stat corrections that the NFL will incorporate from Monday to Wednesday at the latest." → **"Thursday's load_pbp() is the cleanest data we have."**
- games.csv cadence: "Game/Schedule data updates very 5 minutes during the season." [sic — "very" = typo for "every" in source]
- injuries cadence: "Injury Data updates every day at 7AM UTC throughout the season." (entire Injury Data section; no coverage-end warning there — the post-2024 source-change note is under **Depth Chart Data**, which switches to a new ISO8601-timestamp format from 2025 onward.)
- `date_modified` semantics (https://nflreadr.nflverse.com/articles/dictionary_injuries.html): **"Date and time that injury information was updated"** — i.e. last update of the compiled row, **NOT the historical announcement time**.
- `report_status`: "Player's status for game on official injury report"; `practice_status`: "Player's participation in practice".

### RV7 — release metadata spot checks (GitHub API; names/timestamps only, no data)
- Schedules release (`tags/schedules`): assets `games.csv` / `games.parquet` / `games.rds` / `timestamp.json` / `timestamp.txt` all `updated_at 2026-10-04T12:16:32Z`. `timestamp.json` content: `{"last_updated":"2026-10-04 08:16:30 EDT"}` (= 12:16:30 UTC) — semantics: **generation timestamp of the games data snapshot; the per-pull as-of marker**. Body: "NFL game/schedule data." / "Data maintained in Lee Sharpe's nfldata" / "Data in this release updates automatically if the linked file changes."
- pbp release (`tags/pbp`, 164 assets): `play_by_play_2021.parquet` (2026-01-08), `_2022` (2026-02-12), `_2023` (2026-02-12), `_2024` (2026-08-13), `_2025` (2026-08-13), `_2026.parquet` updated **2026-10-04T09:03:19Z** (in-season nightly flow confirmed live). The download plan's 5 pbp parquets exist.
- injuries release (`tags/injuries`): per-season CSV/parquet/rds/qs from `injuries_2009` through `injuries_2026.csv` (`updated_at 2026-10-04T06:01:21Z`) — **coverage 2009–2026, current season flowing**.

---

## 2. Verdict table — {source × download+store / internal-research+ML / redistribution}

Legend: PASS = allowed; FAIL = prohibited by terms; UNVERIFIED = no verifiable grant this session; BLOCKED_NO_KEY = requires signup/key, outside $0-no-signup program constraint; NOT_RUN_PIT = rights OK but point-in-time reconstruction NOT available.

| Source | Download + store | Internal research + ML | Redistribution | Conditions / basis |
|---|---|---|---|---|
| nflverse-data releases (games.csv, timestamp.json, pbp parquets, injuries, rosters) | **PASS** | **PASS** | **PASS (with attribution, indicate modifications)** | CC BY 4.0 (RV1); attribution string sec 3 mandatory; AS-IS (5(a)); no NFL/nflverse endorsement may be implied (2(a)(6)) |
| nflverse/nfldata repo (Lee Sharpe files, draft_picks, legacy rosters) | **UNVERIFIED — banned for this program** | **UNVERIFIED — banned** | **UNVERIFIED — banned** | `license: null` → all-rights-reserved default (RV3); draft_picks/legacy rosters carry PFR upstream chain (FAIL). Use nflverse-data release equivalents only |
| NFL.com / NFL+ (official) | **FAIL (automated)** | **FAIL** | **FAIL** | "Systematic retrieval of data ... prohibited"; archiving/republishing/downloading prohibited; anti-scraping clauses (prior audit E18/E19, unchanged basis) |
| Pro Football Reference (Sports Reference) | **FAIL (store)** | **FAIL (5(11) AI/ML)** | **FAIL** | 5(11) verbatim RV5; 5(10) substitute-database; 5(9) automated access; revocable personal license |
| ESPN hidden endpoints (site.api.espn.com) | **UNVERIFIED** | **UNVERIFIED** | **UNVERIFIED** | No published API terms; not load-bearing. If ESPN-derived data needed, prefer `espn_data` release inside nflverse-data (CC BY 4.0 as distributed) |
| Keyed APIs (The Odds API, balldontlie, Tank01/RapidAPI) | **BLOCKED_NO_KEY** | **BLOCKED_NO_KEY** | **BLOCKED_NO_KEY** | Signup/key required → outside $0-no-signup program; account-gated terms unaudited |
| injuries PIT | rights **PASS** (CC BY 4.0) | **NOT_RUN_PIT** for timing features | PASS w/ attribution | `date_modified` = "Date and time that injury information was updated" ≠ historical announcement time; no per-report-day publication timestamps exist → PIT features must derive from (season, week, `report_status`, `practice_status`), never `date_modified` |
| games.csv odds columns (`spread_line`, `total_line`, `away/home_moneyline`, spread odds) | rights PASS | **QUARANTINE — closing-line contaminated** | — | Values are closing lines: post-kickoff-consistent info; excluded from features unless pre-game availability is proven by vintage snapshots; evaluation context only |

---

## 3. Attribution string template (Lane B MUST ship a CREDITS file using this)

CC BY 4.0 sec 3(a)(1) requires: creator identification, copyright notice, license notice, disclaimer notice, license URI (to the extent reasonably practicable), and an indication of modifications. Template per artifact:

```
Data: nflverse-data release "<release_tag>" — asset "<asset_filename>"
  (GitHub asset updated_at: <iso8601>, fetched: <YYYY-MM-DD>)
Copyright: nflverse project contributors
License: Creative Commons Attribution 4.0 International (CC BY 4.0)
License URI: https://creativecommons.org/licenses/by/4.0/
License file: https://raw.githubusercontent.com/nflverse/nflverse-data/main/LICENSE.md
Modifications: <none | description of transformations applied>
Disclaimer: Data provided AS-IS, without warranty of accuracy (CC BY 4.0 sec 5(a)).
No endorsement: Neither nflverse nor the NFL sponsors or endorses this research
  (CC BY 4.0 sec 2(a)(6)).
```

For the cycle's exact download plan, instantiate the template for: release tag `schedules` — assets `games.csv` + `timestamp.json`; release tag `pbp` — assets `play_by_play_<season>.parquet` for the 5 chosen seasons. Redistribution (if ever) only under the same CC BY 4.0 terms.

---

## 4. Download-plan verdict

**Plan:** `games.csv` + `timestamp.json` from release `schedules`; 5 × `play_by_play_<season>.parquet` from release `pbp` (nflverse-data releases only).

## **VERDICT: DATA_RIGHTS_OK** — proceed with the download plan.

Conditions (binding for lane B / controller):
1. **Attribution**: CREDITS file per template in sec 3, covering every downloaded artifact; record `timestamp.json` content + GitHub asset `updated_at` + local pull time with every pull (vintage evidence).
2. **Vintage discipline**: never mix pbp vintages inside one backtest; respect the Wed→Thu NFL correction window ("Thursday's load_pbp() is the cleanest data we have").
3. **Quarantine**: `spread_line` / `total_line` / moneyline / spread-odds columns in games.csv are closing lines — never model features; evaluation context only. Injuries features derive PIT from (season, week, `report_status`, `practice_status`) — never `date_modified`.
4. **Source ban**: no NFL.com automated collection, no PFR scraping or PFR-derived files (incl. `nflverse/nfldata` draft_picks / legacy rosters). Repo `nflverse/nfldata` itself is banned; only nflverse-data release assets are in scope.
5. **pbp is post-game compiled**: in-game WP ordering must come from within-game sequence fields, not file vintage; nflverse WP/EP columns are model outputs (nflfastR WP-with-spread embeds market info — do not treat as independent features).
6. Provenance caveat (unchanged from prior audit): nflverse scraped upstream sources (NFL JSON, ESPN, FTN, PFR, NGS); the CC BY 4.0 grant is nflverse's. Acceptable research posture: use + attribute + do not resell; revisit if commercialization is proposed.

---

## 5. Re-verification deltas vs prior matrix (2026-10-04 annex)

- **No material contradiction found.** All load-bearing claims (CC BY 4.0 title + grants; nfldata license null; nflreadr no-data-rights disclaimer; PFR 5(11); pbp/games/injuries cadences; Thu-cleanest quote) reproduced verbatim live.
- Clarification: the post-2024 data-source note in the schedule article sits under **Depth Chart Data** (new ISO8601-timestamp format from 2025), NOT under Injury Data — injuries release is confirmed flowing through `injuries_2026.csv` (updated 2026-10-04T06:01:21Z), coverage 2009–2026 at asset level.
- New positive evidence: `timestamp.json` semantics pinned to content: `{"last_updated":"2026-10-04 08:16:30 EDT"}`; `play_by_play_2026.parquet` exists and updated 2026-10-04T09:03:19Z (in-season nightly flow).
- games.csv cadence retains the source typo "updates very 5 minutes during the season" (same wording as prior audit — stable quote).

## 6. Incidents / fetch notes (2026-10-04)

- WebFetch 60s timeouts on: (a) first LICENSE.md attempt, (b) schedules releases HTML page, (c) injuries release API — each recovered via an alternate allowed path (second WebFetch / web_reader / `curl` of the GitHub API returning metadata only). No blocked pages, no circumvention attempted, no dataset downloaded.
- sports-reference termsofuse: full text retrieved via reader (same-day; prior session's curl/WebFetch 403s did not recur but reader remains the working path).
- Scope guard: this memo authorizes the download plan only; it opens no model run, no backtest, no redistribution. No git operations performed beyond read-only HEAD/status measurement.
