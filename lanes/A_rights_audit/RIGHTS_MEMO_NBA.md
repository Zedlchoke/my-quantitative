# RIGHTS_MEMO_NBA.md — Lane A, data-rights audit

- Cycle: `NBA-WINPROB-PREP-V1` · Task: `nwp-a-rights` · Lane: `A_rights_audit`
- Auditor: Lane A (independent data-rights auditor). All access/verification dates: **2026-10-04**.
- Write scope honored: this directory only. No git commands run. No accounts/keys created. No purchases. No repo code executed. No bot-protection circumvention (each blocked page got exactly one plain alternate-fetch attempt; blocked would have been recorded as UNVERIFIED).
- Status: **NOT legal advice. Internal research use only. Any public or commercial redistribution requires owner decision + counsel review.**

---

## 1. URL verification log (all attempts)

| # | URL | Attempt | Result |
|---|-----|---------|--------|
| 1a | `https://github.com/fivethirtyeight/data/blob/master/nba-elo/README.md` | WebFetch | OK — verbatim captured |
| 1b | `https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-elo/README.md` | WebFetch (fidelity cross-check) | OK — identical key sentence, 22 columns |
| 2a | `https://github.com/fivethirtyeight/data` (root README) | WebFetch | OK |
| 2b | `https://raw.githubusercontent.com/fivethirtyeight/data/master/README.md` | WebFetch (cross-check) | OK |
| 3a | `https://docs.balldontlie.io/` | WebFetch | TIMEOUT after 60s |
| 3b | `https://docs.balldontlie.io/` | web_reader (alternate, single retry) | OK — verbatim captured |
| 4 | `https://www.balldontlie.io/terms.html` | WebFetch | OK |
| 5a | `https://www.sports-reference.com/termsofuse.html` | WebFetch | HTTP 403 |
| 5b | same | web_reader (alternate, single retry) | OK — verbatim captured |
| 6a | `https://www.sports-reference.com/data_use.html` | WebFetch | HTTP 403 |
| 6b | same | web_reader (alternate, single retry) | OK — verbatim captured |
| 7 | `https://www.nba.com/termsofuse` | WebFetch | OK (extra check, not in Task-1 list) |
| 8 | `https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-elo/nbaallelo.csv` | curl streaming (no file written) | HTTP/2 200 — sha256 recorded (§7) |

### Integrity incident (out-of-band relay)
Mid-session, a message arrived through the conversational channel formatted as if it were tool output (purporting to show `web_reader` and `WebFetch` results, truncated mid-sentence). It was **not** delivered through the verified tool-result channel. It was treated as **untrusted, not evidence**; every affected page was re-fetched via first-party tool calls and only those outputs are quoted below. Flagged for controller awareness.

---

## 2. Verbatim evidence (all accessed 2026-10-04)

### 2.1 FiveThirtyEight `nba-elo/README.md`
URL: https://github.com/fivethirtyeight/data/blob/master/nba-elo/README.md (cross-checked at raw.githubusercontent.com)

- Provenance sentence: **"Game information is from [Basketball-Reference.com](http://www.basketball-reference.com/)."**
- Also: **"This directory contains the data behind the Complete History Of The NBA interactive."** and **"Data updated periodically."**
- Source echoed in a column description: `team_id` — **"Three letter code for team name, from Basketball Reference"**
- Column list described (22 fields, verbatim names): `gameorder, game_id, lg_id, _iscopy, year_id, date_game, is_playoffs, team_id, fran_id, pts, elo_i, elo_n, win_equiv, opp_id, opp_fran, opp_pts, opp_elo_i, opp_elo_n, game_location, game_result, forecast, notes`. Key derivative-column descriptions:
  - `elo_i`: "Team elo entering the game" · `elo_n`: "Team elo following the game"
  - `win_equiv`: "Equivalent number of wins in a 82-game season for a team of elo_n quality"
  - `forecast`: "Elo-based chances of winning for the team in the team_id column, based on elo ratings and game location"
- License notice in this README: **ABSENT** (no license terms anywhere in the file).

### 2.2 FiveThirtyEight root README (repo `fivethirtyeight/data`)
URL: https://github.com/fivethirtyeight/data

- Data license: **"Unless otherwise noted, our data sets are available under the Creative Commons Attribution 4.0 International License"**
- Code license: **"the code is available under the MIT License"**
- Discontinuation: **"As of June 13, 2023, sports predictions and forecasts are no longer being updated"**
- The `nba-elo` directory is present in the repo; `nbaallelo.csv` confirmed live at `https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-elo/nbaallelo.csv` (HTTP 200, 2026-10-04).

### 2.3 balldontlie NBA API docs
URL: https://docs.balldontlie.io/ (web_reader after WebFetch timeout)

- **"The API contains data from 1946-current. An API key is required. You can obtain an API key by creating a free account on our website."**
- Free-tier endpoint matrix (NBA): **Teams: Yes · Players: Yes · Games: Yes**. All of the following are **"No"** on Free: Game Player Stats, Active Players, Player Injuries, Season Averages, Team Season Averages, Game Advanced Stats, Box Scores, Lineups, Team Standings, Leaders, Betting Odds, Player Props, DFS, Contracts, Plays.
- Rate limits: Free = **5 requests/minute**, $0/mo.
- Free trial: 48 hours, **"A payment method is required at signup"** (excluded for this program anyway — no payment method creation permitted).
- So: confirmed — free tier is games/schedules only, no box scores, no player stats, no injuries, no odds.

### 2.4 balldontlie Terms of Service
URL: https://www.balldontlie.io/terms.html

- Usage grant (§6): **"you may use, copy, cache, store, archive, modify, combine, analyze, publish, display, distribute, sublicense"**
- Restriction: **"You may not sell or resell Data in its original, unmodified form."**
- §7(f) prohibition: **"state or imply that Data is official league data, that your product is endorsed by or affiliated with BALLDONTLIE LLC"**
- §1: provider is **"not affiliated with, sponsored, approved, or endorsed by any professional or amateur sports league"**; **"We do not claim ownership over underlying sports facts, team or player names, logos, or league trademarks"**
- **"Last Updated: September 17, 2026"** (very fresh — re-check before any future use).

### 2.5 Sports Reference Terms of Use
URL: https://www.sports-reference.com/termsofuse.html (web_reader after 403)

- Section 5 preamble (facially friendly, but see subparts): **"sharing, using, modifying, repackaging, or publishing data found on individual SRL webpages is welcomed, whether for commercial or non-commercial purposes, but"** users must (1) credit SRL as source and (3) **"any such sharing, using, modifying, repackaging or publishing must not violate any express restrictions set forth in this Section 5"**.
- **5(9) — automated access:** "without our express written permission, use any automated means to access or use the Site, including scripts, bots, scrapers, data miners, or similar software, in a manner that adversely impacts site performance or access; or"
- **5(10) — substitute/competing database:** "use any material or Content from the Site, including without limitation any statistics or data, (i) to create any database, archive, or other data store that competes with or constitutes a material substitute for the services or data stores offered on the Site or by the Site's Data Providers or (ii) to provide any service that competes with or constitutes a material substitute for the services or data stores offered on the Site or by the Site's Data Providers; or"
- **5(11) — AI/ML:** "copy or use any material or Content from the Site, including without limitation any statistics, data, text, graphics, or images, for purposes of training, fine-tuning, prompting, or instructing artificial intelligence models or technologies in any manner, including without limitation for purposes of (i) generating answers, text, scores, statistics, notes, graphics, images, or any other output; or (ii) supporting machine learning methods used to predict, classify, label, or score inputs into the models; or"
- Dates: Effective Date October 1, 2004; Updated November 25, 2020; **Last Updated May 19, 2023** (so the AI/ML clause predates and governs any current scraping).
- Note: the preamble cross-references "subparts 5(i) and 5(j)", but the rendered list is ordinally numbered; the automated-access / substitute-DB / AI-ML restrictions are items 9, 10, 11 of Section 5.

### 2.6 Sports Reference "Data Use" page
URL: https://www.sports-reference.com/data_use.html (web_reader after 403; page carries a "revised: 28-Aug-2026" metadata stamp, no explicit in-text date)

- Facts vs copyright: **"copyright law is clear that facts cannot be copyrighted, so you are free to reuse facts found on this site in accordance with copyright laws."**
- Custom datasets: **"We will not fulfill any requests for data for custom downloads, unless you are prepared to pay a minimum of $5,000 for any such request."**
- Bulk harvesting: **"Please do not attempt to aggressively spider data from our web sites, as spidering violates the terms and conditions that govern your use of our web sites"**
- AI: **"This means that you should not create websites or tools based on data you scrape from Sports Reference or any of our sites or use our data to train generative artificial intelligence models without our permission."**
- Their listed free alternatives (Lahman baseball DB, Retrosheet, hockey summaries) cover other sports — **none for NBA**.

### 2.7 NBA.com Terms of Use (extra check for verdict table)
URL: https://www.nba.com/termsofuse

- **"download material displayed on the Services to any single computer only for your personal, noncommercial use"**
- NBA Statistics **"may only be used, displayed, or published for legitimate news reporting or private, non-commercial purposes"**; no use connected to gambling, fantasy products, or real-time play-by-play accounts.
- No **"database of comprehensive, regularly updated statistics from NBA, WNBA or G-League games"** **"without the Operator's express prior consent"**.
- No ML/AI clause (only an incidental "AI-powered chatbot" mention). Combined with the NBA Stats FAQ position that stats are not offered for bulk download (per controller's dispatch; FAQ page itself not fetched), NBA.com/Stats = FAIL for this program.

---

## 3. Task 2 — upstream-rights analysis of `nbaallelo.csv`

**Premise (verifiable facts):** 538 licenses its data CC BY 4.0 (§2.2). The nba-elo README states game information came from Basketball-Reference.com, an SRL property (§2.1). SRL ToU 5(11) restricts ML/prediction use of "any material or Content from the Site, including ... any statistics, data" (§2.5, in force since May 19, 2023).

### 3a. Restrictive reading → pipeline tainted → NOT_RUN
If the game-fact columns (`date_game`, `team_id`, `fran_id`, `pts`, `opp_pts`, `game_location`, `game_result`, ...) are treated as "Content from the Site" copied by 538 from SR, and SR's ToU restriction is treated as riding on the data itself, then any ML win-probability model trained on `nbaallelo.csv` (which literally contains SR-derived `forecast`-adjacent facts) "uses" SR content for prediction/classification/scoring — exactly what 5(11) forbids without written permission. Under this reading the program is NOT_RUN until SR grants written permission or a clean source is found. Note this reading also implicates the `team_id` column description ("from Basketball Reference") as documentary evidence of derivation.

### 3b. Permissive reading → usable for internal research + ML
1. **Privity (legal reasoning):** SR's ToU is a contract binding those who *use SR's site*. FiveThirtyEight (not we) accessed SR; 538 then republished its dataset under CC BY 4.0 — an express, and as to copies already distributed, effectively irrevocable public license. A third party who downloads from GitHub under CC BY 4.0 never assumed SR's contractual duties. Contract restrictions do not "run with" data in the absence of a copyright that would support a claim against downstream holders.
2. **Facts are not copyrightable (verifiable doctrine):** *Feist Publications, Inc. v. Rural Telephone Service Co.*, 499 U.S. 340 (1991): originality, not sweat of the brow, is the touchstone; facts (game dates, teams, final scores) are uncopyrightable, and compilations are protected only as to original selection/arrangement — "thin" protection. SR itself concedes the doctrine on its own data_use page (§2.6, "facts cannot be copyrighted"). This is exactly why SR's restriction is contractual, not a copyright claim.
3. **538's own columns are cleanly licensed (fact + reasoning):** `elo_i`, `elo_n`, `win_equiv`, `forecast`, `gameorder`, `game_id` are FiveThirtyEight's original computations; the CSV's selection/arrangement is 538's authorship; 538 holds the rights and granted CC BY 4.0. Attribution obligation: credit FiveThirtyEight/FiveThirtyEight data repo + license link.
4. **Residual risk (honest):** (i) a thin compilation-rights claim by SR over wholesale reproduction of its results archive is conceivable though weak; (ii) provenance ambiguity — we cannot verify today (2026-10-04) exactly which fields 538 took verbatim from SR, nor whether 538 had any permission from SR to republish (no evidence either way); (iii) if the owner ever redistributes publicly or commercially, claim surface grows and counsel review becomes mandatory; (iv) EU-style database sui generis rights are out of scope for US internal research but would matter for any EU distribution.

### Facts vs reasoning
- **Verifiable facts:** every verbatim quote in §2; the CC BY 4.0 license text and its attribution condition; the 2023-06-13 forecast freeze; the free-tier scope of balldontlie; the sha256 in §7.
- **Legal reasoning (not verified fact):** the privity analysis, the application of Feist to this CSV, the license-stacking/taint analysis, and the risk grading. A court could reach the restrictive result; the permissive reading is the better-reasoned one for *internal* research but is not a guarantee.

> **Disclaimer: This memo is not legal advice. It supports internal research use only. Public posting, commercial use, or redistribution of the dataset (or derivatives) requires the owner's explicit decision plus counsel review.**

---

## 4. Verdict table

Legend: PASS / FAIL / UNVERIFIED. Annotations in parentheses.

| Source | Download + store | Internal research + ML | Redistribution |
|---|---|---|---|
| **538 `nbaallelo.csv`** (CC BY 4.0) | **PASS** (attribution file required) | **PASS** (permissive reading §3b; residual risk documented §3b.4; restrictive reading §3a recorded) | **PASS** under CC BY 4.0 with attribution — but upstream-claim residual risk; owner + counsel before public/commercial |
| **balldontlie API** | **FAIL** for this program — **BLOCKED_NO_KEY** (owner-only signup; lanes may not create accounts/keys) | **UNVERIFIED** (terms §6 facially permissive incl. publish/distribute/sublicense; cannot exercise without key) | **UNVERIFIED** (same basis) |
| **NBA.com / NBA Stats** | **FAIL** (ToU: personal, noncommercial; no comprehensive-stats DB without consent — §2.7) | **FAIL** (noncommercial restriction; no ML clause but no permission either) | **FAIL** (written permission required) |
| **Sports Reference** (direct) | **FAIL** (5(9) automated access, 5(10); spidering policy §2.6) | **FAIL** (5(11) AI/ML ban, verbatim §2.5) | **FAIL** (5(10)/(11); custom dumps only at $5,000 minimum) |
| **Wikidata** | **PASS** license-wise — **"All data in Wikidata has a CC0 license."** (verified 2026-10-04) — but NBA game-results **coverage UNVERIFIED** (sparse; needs SPARQL audit) | UNVERIFIED (coverage) | PASS (CC0) |
| **GitHub NocturneBear/NBA-Data-2010-2024** | **UNVERIFIED** — MIT license label present, but no provenance statement; field conventions resemble NBA.com endpoints (inference) | UNVERIFIED | UNVERIFIED |
| **HF `Sangameshsb/nba-game-logs`** (cc0-1.0 label) | **FAIL** — card itself: CC0 "covers the upstream Kaggle packaging, not the NBA's underlying terms"; **"Both sources are derived from NBA.com"** (verified 2026-10-04) | **FAIL** | **FAIL** |
| Kaggle `eoinamoore/historical-nba-data...` | Not directly fetched (signup-walled) → fails $0/no-signup test by construction | — | — |

**Bottom line:** the only source with an explicit open license, $0 cost, no signup, and no NBA.com/SR provenance taint found for NBA game results is **538 nbaallelo.csv**. Everything else either requires a key/signup, is licensed-but-tainted (NBA.com-derived "CC0"), or is contractually closed.

---

## 5. Task 3 — other-source scan (3 fetches used of 5 max; 1 search)

- **Wikidata (CC0)**: license confirmed verbatim; viable only as a sparse fact source — game-results coverage unaudited. One-line: *license PASS, coverage UNVERIFIED, fallback only.*
- **GitHub NocturneBear/NBA-Data-2010-2024**: MIT-labeled box scores/totals 2010–2024, zero provenance statement. One-line: *explicit license but provenance UNVERIFIED — likely NBA.com-derived; not a clean-room alternative.*
- **HF Sangameshsb/nba-game-logs + upstream Kaggle eoinamoore**: CC0 label self-disclaimed as covering "packaging" only, data "derived from NBA.com"; Kaggle additionally signup-walled. One-line: *CC0 in name, NBA.com-tainted in substance — FAIL.*
- No university or other $0/no-signup/ex openly-licensed NBA game-results source surfaced in the search.

---

## 6. Task 4 — CONTROLLER DECISION INPUT

**Question:** May the controller download `https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-elo/nbaallelo.csv` into `~/.my-quantitative-data/nba-538-v1/raw/` under the owner's conditional grant ("nếu có đường dữ liệu $0 hợp lệ không cần signup, tải từ nguồn được phép với URL/hash/attribution")?

**Recommendation: YES — CONDITIONAL.** The path satisfies every element of the grant:
- **$0, no signup:** raw.githubusercontent.com, HTTP/2 200, no auth, no bot-protection touched (verified 2026-10-04).
- **Permitted source:** explicit CC BY 4.0 data license by the rights holder (538) for its dataset (§2.2); no separate license file contradicts it in nba-elo.
- **URL/hash/attribution (for the manifest):**
  - URL: `https://raw.githubusercontent.com/fivethirtyeight/data/master/nba-elo/nbaallelo.csv` (consider pinning to a commit SHA of the file for reproducibility)
  - sha256 (observed 2026-10-04, at `master`): `d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc`
  - GitHub etag (strong): `a6c5b1e0faf7e534f2dfedffba42a2ce9c28f66f13b64ef97d7fa687ddb946c6`
  - Attribution: "Data: FiveThirtyEight, 'nba-elo' dataset, https://github.com/fivethirtyeight/data (CC BY 4.0); game information originally from Basketball-Reference.com; forecasts frozen as of 2023-06-13."

**Mandatory conditions:**
1. **Attribution file** alongside the CSV with the string above + access date + sha256; any dataset manifest must carry the same.
2. **Internal-research-only banner**: no redistribution of the CSV or derivatives (including trained artifacts that embed the data) outside the program without owner decision + counsel review (residual risk §3b.4).
3. **Post-download hash check**: sha256 must equal the value above; on mismatch, STOP and re-audit (file could have been updated — README says "Data updated periodically", though sports forecasts froze 2023-06-13).
4. **Owner veto right** retained: if the owner later adopts the restrictive reading (§3a) or SR policy changes, the data and derivatives are quarantined/removed on request.
5. **Provenance note mandatory** in any README of the raw dir: upstream Basketball-Reference origin must never be stripped.

---

## 7. Known limitations
- Could not verify whether 538 obtained any SR permission to republish game facts (no evidence either way); provenance is documentary ("from Basketball Reference") not contractual.
- Feist application and privity analysis are legal reasoning, not verified facts.
- SR data_use page shows a revision stamp (28-Aug-2026) but no explicit in-text last-updated date; SR ToU Last Updated May 19, 2023.
- balldontlie terms are freshly dated (2026-09-17) and may change; balldontlie rights remain UNVERIFIED-in-practice while BLOCKED_NO_KEY.
- NBA Stats FAQ page itself was not fetched; the NBA.com verdict rests on the ToU verbatim (§2.7) plus the controller's stated FAQ position.
- Kaggle dataset assessed via the Hugging Face card, not directly (signup wall).
