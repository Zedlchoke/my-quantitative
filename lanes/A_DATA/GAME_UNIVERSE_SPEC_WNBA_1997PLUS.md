# GAME UNIVERSE SPEC — WNBA 1997+ (Lane A, WNBA-WINPROB-PREP-V1)

- task `wbap-a-data` · cycle `WNBA-WINPROB-PREP-V1` · role quant-explorer · 2026-10-05
- dispatch_sha = actual_start_sha = `673b4f27e4abdefc5c54839febac29185dd6e794`
  (branch `orca/wnba-winprob-prep-v1-integration`; no git operations performed by this lane)
- MEASURED, not asserted. Machine output: `~/.my-quantitative-data/wnba-prep-v1/measurements_a2.json`
  (script `lanes/A_DATA/measure_a2.py`; re-runnable read-only). Schema/coverage counting ONLY —
  no win-prob metrics, no scored computation, no outcome modeling.
- Corpus (EXTEND-ONLY, read-only): `~/.my-quantitative-data/wnba-v1/raw/`
  (ESPN schedules 2002–2026; stats schedules 1997–2026; 2025 ESPN sample box/pbp;
  sha256 per file in `raw/audit_results.json`; attribution in `raw/ATTRIBUTION.md`).
- Prior-cycle evidence memo (read-only context): `winprob-ng-prep-v1/lanes/B_WNBA/WNBA_SOURCE_AUDIT.md`.
  This spec **corrects three of its measured claims** (§5, §6, §9) — corrections are re-measured here, not inherited.

Data attribution: SportsDataverse (wehoop) release store `sportsdataverse/sportsdataverse-data`,
data badge CC BY 4.0, code MIT; underlying upstream ESPN WNBA API and stats.wnba.com endpoints
(scraped by the SportsDataverse pipelines, not by us). No wnba.com/ESPN/SR scraping; no balldontlie.

---

## 1. Sources and identity

| | ESPN side (`espn_schedules/`) | Stats side (`wnba_stats_schedules/`) |
|---|---|---|
| seasons | 25 (2002–2026), one csv+parquet per season | 30 (1997–2026), one csv.gz per season |
| rows | **6,029** | **7,009** |
| unique game_id | 6,029 (0 dups) | 7,009 (0 dups) |
| game_id shape | 9-digit numeric, not season-structured (e.g. `401820314`) | **10-digit, `10` + season_type digit + YY + 5-digit seq** — measured 100% `[3:5]==YY`; digit `2`=regular-season (6,494 rows), `4`=playoffs (515) (e.g. `1029700001`, `1021800162`, `1042600132`) |
| columns | 77 (venue, broadcast, status block, notes, neutral_site…) | 15 (`game_id…home_pts/home_wl/away_pts/away_wl`, `season`, `season_type`) |
| status columns | YES (`status_type_state`, `_detail`, `_completed`) | NO status columns (played-ness only via win/loss flags) |
| season_type | integer 2 (regular, incl. Cup) / 3 (postseason) | string `regular-season` / `playoffs` |

**Identity law.** Within a source, `game_id` is the primary key (both sides verified 1 row per id).
Across sources there is **no shared id**: join via the canonical cross-source key of §7, never via
abbreviations. The `wnba_crosswalk` release provides an official `espn_game_id ↔ wnba_game_id`
map but **only for 2026** (403 rows incl. preseason; `match_method`, `match_confidence`) — historical
cross-source identity is established by this spec's §7 join law. (Crosswalk files downloaded and
hashed: `~/.my-quantitative-data/wnba-prep-v1/extensions/`.)

## 2. Canonical team keys (franchise-level)

> **ERRATUM R1 (2026-10-05, task wbap-a-data-r1)** — the two franchise-lineage rows below were
> rebranched from the data (verifier defect D-1, MAJOR): **LVA is the modern key of the
> UTA→SAN lineage** (not a fresh 2018 stream) and **DAL is the modern key of the DET→TUL
> lineage** (not the SAN successor — SAN and DAL coexisted in 2016 AND 2017). Full evidence:
> `lanes/A_DATA/ERRATUM_TEAM_KEY_R1.md`. This section supersedes the pre-erratum text.

20 franchise keys cover all 30 seasons; full table with per-franchise observed abbreviations and
display names (both sources): `~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv`.
Every boundary below is verified from the row data (`stats_abbr_seasons`, per-season name maps),
not from external lists.

| franchise_key | era keys (stats abbr / ESPN display) | seasons | event measured in data |
|---|---|---|---|
| LVA | UTA Utah Starzz 1997–2002 → SAN San Antonio Silver Stars 2003–2013 / San Antonio Stars 2014–2017 → LVA Las Vegas Aces 2018– | 1997–2026 | SAN last season **2017**, LVA first **2018**; SAN and DAL coexist as 2 of 12 distinct teams in BOTH 2016 and 2017 (SAN 34/34 rows, DAL 34/35 rows) — no SAN→DAL merger; ESPN spells Utah `UTH`, San Antonio `SA`/`SAS`, Las Vegas `LV` |
| DAL | DET Detroit Shock 1998–2009 → TUL Tulsa Shock 2010–2015 → DAL Dallas Wings 2016– | 1998–2026 | 2010 DET→TUL boundary exact; TUL last played season 2015, DAL first 2016; ESPN labels ALL Detroit rows `TUL` in every ESPN season 2002–2009 (see below) |
| CON | ORL Orlando Miracle 1999–2002 → CON Connecticut Sun 2003– | 1999–2026 | ESPN spells Connecticut `CT`/`CONN`/`CON` |
| LAS | LAS Los Angeles Sparks | 1997–2026 | ESPN `LOS`/`LA`; continuous, never relocates (measured present in all 30 seasons) |
| PHO | PHO 1997–2024 → PHX 2025– Phoenix Mercury | 1997–2026 | same franchise, stats abbr changed 2025; ESPN used `PHO` then `PHX` |
| POR_PDX | POR Portland Fire 2000–2002 → PDX Portland Fire 2026– | 2000–2002, 2026– | 2026 expansion reuses the Fire name; ESPN uses `POR` for BOTH eras (measured) |
| defunct | CHA Charlotte Sting (1997–2006) · CLE Cleveland Rockers (1997–2003) · HOU Houston Comets (1997–2008) · SAC Sacramento Monarchs (1997–2009) · MIA Miami Sol (2000–2002) | | end years exact |
| expansion | CHI 2006 · ATL 2008 · GSV Golden State Valkyries 2025 (ESPN `GS`) · TOR Toronto Tempo 2026 (ESPN+stats `TOR`) | | |
| stable | NYL (ESPN `NY`/`NYL`) · MIN · IND · SEA · WAS (ESPN `WSH`/`WAS`) | 1997/98–2026 | |

**Never join on raw ESPN abbreviations.** Measured: ESPN labels **every** Detroit Shock row
`TUL` (home AND away) in **all** ESPN seasons 2002–2009 — **318 rows** (2002:32, 2003:42,
2004:37, 2005:36, 2006:44, 2007:45, 2008:43, 2009:39); the abbreviation `DET` appears **0 times**
on ESPN, so ESPN's own labels alias Detroit 2002–2009 and Tulsa 2010–2015 (`TUL`) across the
same franchise's two eras (R1 erratum: scope was previously understated as a "2002 file"
artifact); one ESPN display_name maps to up to 3 abbreviations across seasons (Connecticut:
`CT`/`CONN`/`CON`) and ESPN reuses `POR` across a 24-year gap. Join on normalized
`display_name`/`team_name` (§7) or the 2026 crosswalk.

## 3. Timestamp canonicalization — one `tip_utc` law

Four flavors measured (flavor table supersedes the prior memo's §3.4):

| # | field | measured semantics |
|---|---|---|
| F1 | ESPN schedule `date` / `start_date` / `game_date_time` | **one canonical UTC instant** — all three columns are the same instant for **6,029/6,029 rows (100%)** when parsed per-file with ISO8601. Rendering varies by season (2002–2025 `…Z`; 2026 `…-0400` suffix, cosmetic). The prior memo's "94.03% equality" and "360 unequal" were a pandas mixed-format parse artifact in attempt 1 — corrected here. |
| F2 | ESPN box `game_date_time` (2025 sample) | **same UTC instant as F1 for 312/312 games**, rendered with a fixed `-0400` suffix for **all venues** (Vegas/Phoenix/Seattle included). It is NOT venue-local — the prior memo's "venue-local with numeric offset" is corrected. Box `game_date` (naive) == **Eastern calendar date** of F1 (100%); == UTC date only 53.5% (late ET games cross midnight UTC). |
| F3 | ESPN pbp `wallclock` | UTC wallclock, 100% `Z`; first event lands median **+3.1 min** after tip_utc (p05 +2.5, p95 +6.9) — confirms F1 is the tip instant. |
| F4 | stats schedule `game_date` | naive **Eastern calendar date** (no time, 100% `YYYY-MM-DD`). |

**Canonical law (normative for all successors):**
```
tip_utc      := pd.to_datetime(espn.date, utc=True, format="ISO8601")     # F1; single parse per season file
local_date   := tip_utc.tz_convert("America/New_York").date               # the modeling date key
```
- F4 measured == `local_date` for **5,954/5,954** unique-window cross-source matches (offset distribution 5,954 at 0, 0 at ±1) — the stats-side date is ET-keyed; no venue-tz reconstruction is needed or permitted.
- DST: verified through the offset/variance analysis above (2026 file carries a constant `-0400` rendering across all months/venues incl. non-DST venues; instants never shift). Never parse mixed-format columns without `format="ISO8601"` and never treat `game_date_time`'s suffix as venue tz.

## 4. Filter / exclusion law (APPLIED, measured)

> **ERRATUM R1 (2026-10-05, task wbap-a-data-r1)**: item 3 now carries the measured per-token
> alias breakdown (incl. WIL×3, STE×2); item 6 Cup finals corrected 7 → **6** (the prior
> "Cup AND neutral" detector double-counted the 2024-06-06 WAS–CHI neutral Cup GROUP game).
> See `lanes/A_DATA/ERRATUM_TEAM_KEY_R1.md`.

Never filter on score presence — unplayed rows are **pre-filled 0–0** (measured: all 17 ESPN `status_type_state != 'post'` rows are 0–0; 0 rows with null scores). Normative filter chain:

1. Keep `status_type_state == 'post'` (ESPN side only; stats side has no status column).
2. Drop `status_type_detail ∈ {Forfeit, Postponed}` — **exactly 3 rows ever**:
   forfeit 2018-08-03 WAS vs LVA 0–0 (`401018942` / stats `1021800162`, blank `wl`);
   postponed 2023-06-07 NYL vs MIN (`401507167`) and 2026-07-17 DAL vs NYL (`401857072`), both 0–0.
   (Stats side contains only the forfeit as 0–0 with blank win/loss flags — 1 row.)
3. Drop All-Star / special-team alias rows: abbreviations or names in {EAST, WEST, ALL, USA, DEL,
   PAR, WIL, STE, CLA, COL, SPO, COOP, WNBASTARS} — **21 rows** (one per ASG season 2002–2026,
   none in 2008/2012/2016/2020 Olympic years). The prior memo counted 14 with an incomplete alias
   set (missed Team Wilson/Stewart 2022–2023, Team Collier/Spoon 2025/2026, USA 2004/2010/2021/2024) — corrected. Measured per-token slots (home+away sides of the 21 rows, R1):
   EAST 11, WEST 11 (2002–2017 classic format), USA 4 (2004/2010/2021/2024 Team USA),
   WIL 3 (2019/2022/2023 Team Wilson), ALL 3 (2004/2010/2021 Team WNBA; 2024 uses `WNBASTARS`),
   STE 2 (2022/2023 Team Stewart), DEL 2 (2018/2019 Team Delle Donne), PAR 1 (2018 Team Parker),
   COL 1 + CLA 1 (2025 Team Collier/Clark), SPO 1 + COOP 1 (2026 Team Spoon/Coop).
   Stats side has **0** such rows.
4. Drop TBD if-necessary placeholders: **7 rows**, all 2026, state `pre`, dates 2026-10-17…2026-11-01.
5. Neutral-site flag carried, **not** an exclusion: 16 rows (2013–2026) = 10 All-Star + 6 real
   games incl. Cup finals (only 2021/2025/2026 finals are neutral — the 2022–2024 finals were
   home games, measured; e.g. 2021-08-12 ET SEA hosting CON, 2026-08-12 ET PHX hosting LA).
   Neutral-site also covers non-final real games (2016-09-29 LAS–CHI, 2016-07-22 ATL@DAL,
   the 2024-06-06 WAS–CHI Cup GROUP game, 2025-08-16 ATL@SEA).
6. Commissioner's Cup rows (2021+): **301 rows, all `season_type=2`** (embedded in RS) — keep in the
   modeling table but flag `is_cup` (headline contains "Cup"); report separately. Cup finals:
   **6** — exactly one per Cup season 2021–2026 (R1 erratum: the prior "7" came from a detector
   that also caught the 2024-06-06 WAS–CHI neutral Cup GROUP game; the final is the
   last-scheduled Cup game of each season, verified in all 6 seasons). ET dates, home vs away:
   2021-08-12 SEA vs CON (headline plain "WNBA Commissioner's Cup", the only neutral Cup row of
   2021); 2022-07-26 CHI vs LVA; 2023-08-15 LVA vs NYL; 2024-06-25 NYL vs MIN; 2025-07-01 MIN vs
   IND; 2026-06-30 NYL vs LVA (2022–2026 headlines "WNBA Commissioner's Cup Championship").
7. Playoffs: ESPN `season_type==3` / stats `"playoffs"` — separate table/report.
8. 2020 Wubble: **147 rows, all played, kept as real** (132 RS + 15 PO on both sides).

## 5. Per-season census 1997–2026 (after the filter law)

Full table in `measurements_a2.json` (`census_per_season`). Summary (rows = games):

- **ESPN real (post-filter) total: 5,988** = 5,230 regular-season excl. Cup + 301 Cup + 457 playoffs.
- **Stats real (post-filter) total: 7,008** = 6,493 RS + 515 PO.
- Era shape: 1997: 115 real (112+3) — 8-team 28-game first season; 1998: 158; 1999: 203; 2000: 272;
  2001: 274; 2002–2015 ≈ 220–259/season; 2016–2019 ≈ 220–222; **2020: 147 (Wubble, real)**;
  2021: 210 ESPN real / 209 stats (the 1 = Cup final, absent on stats side); 2022: 240/239;
  2023: 261/260; 2024: 263/262; 2025: 311/310 (first 13-team season; 287 ESPN RS rows incl. 37 Cup);
  **2026 (season in progress at snapshot)**: ESPN total 360 rows = 341 played-real + 17 future
  (`pre`, 0–0, incl. 7 TBD placeholders) + 2 postponed; stats total 340.
- Corpus snapshot: ESPN files published 2026-10-01; stats 2026-10-04; pulls 2026-10-05T01:46–01:51Z (prior cycle) — 2026 counts are as-of-snapshot, not final.

## 6. Cross-source reconciliation (ESPN vs stats) — definitive, two-pass join

Join law (§7) applied to all 5,988 ESPN real rows vs 7,008 stats real rows:

- **5,954 matched by unique (name-pair, ET date) window** — every single one at date offset 0.
- **25 more matched by exact (name-pair, score)** fallback: 24 are back-to-back playoff/series games
  whose ±1d windows are ambiguous in pairs (e.g. 2007-09-02/09-03 DET–IND), resolved uniquely by score;
  plus **1 suspended game** — ESPN keys 2019-08-05 completion (`401156333`, "RESUMED FROM JULY 5"),
  stats keys the original 2019-07-05 date (`1021900079`), identical 70–99 score.
- **9 ESPN-only rows** (no stats counterpart): 3 regular games — 2007-06-20 CON@NYL 73-76 (`270620018`),
  2009-07-09 NYL@LAS 60-69 (`290709009`), 2011-06-04 IND@CHI 65-57 (`400182104`) — and the
  **6 Commissioner's Cup finals 2021–2026, absent from the stats side entirely**.
- **1,029 stats-only rows**: 1,022 in 1997–2001 (no ESPN coverage by design) + **7 genuine extras** the
  ESPN schedules lack: 2002-08-20 playoff doubleheader NYL-IND 75-60 + HOU-UTA 72-75 (`1040200103`,
  `1040200133`); 2003-06-12 PHO-CHA 50-58; 2003-07-22 LAS-WAS 77-73; 2004-05-20 RS doubleheader
  HOU-SAN 55-64 + PHO-SAC 66-72; 2004-05-25 WAS-LAS 79-95.
- Per-season row-diff table (ESPN total − stats total): ±0…3 for 2002–2025 (explained by the above:
  ASG rows ESPN-only, Cup finals ESPN-only, 7 stats extras, forfeit/postponed asymmetries), **+20 in
  2026** = 17 unplayed future rows + 2 postponed + 1 Cup final that stats side has not recorded.
- **Model universe union: 7,017 rows** (5,988 ESPN real + 1,029 stats-only).

## 7. Canonical cross-source join (normative)

```
key = ( normalize(display_name) home & away,          # normalized team names, franchise-key equal
        ET calendar date of tip_utc )                  # stats game_date == this date (measured 100%)
```
- pass 1: unique match in a ±1-day window (measured: always hits at offset 0; window is defense only);
- pass 2 (residuals): exact name-pair + exact score, any date — recovers series back-to-backs and the
  2019 suspended game; a duplicate (name-pair, score) collision would block pass 2 (none in corpus);
- hard rule: never join on ESPN abbreviations (§2 artifacts); never join on venue-local time
  (F2 correction); the official `wnba_schedule_crosswalk_2026.csv` (espn_game_id ↔ wnba_game_id)
  is authoritative for 2026 where present and should be preferred there.

## 8. Depth census (optional extension, asset-level — NOT a mirror)

Measured 2026-10-05T04:05Z via GitHub release API, `sportsdataverse/sportsdataverse-data`
(full per-asset JSON: `~/.my-quantitative-data/wnba-prep-v1/release_depth_census.json`):

| release tag | seasons | assets | size | note for successor TRAIN window |
|---|---|---|---|---|
| espn_wnba_team_boxscores | 2003–2026 (24) | 76 | 6.4 MB | per-season csv/parquet/rds |
| espn_wnba_player_boxscores | 2002–2026 (25) | 79 | 64.3 MB | |
| espn_wnba_pbp | 2002–2026 (25) | 79 | 1,065.7 MB | full-history PBP ≈ +1.07 GB (ESPN side) |
| wnba_stats_pbp | 1997–2026 (30) | 99 | 213.9 MB | only source of pre-2002 PBP |
| espn_wnba_game_rosters | 2002–2026 (25) | 80 | 30.4 MB | per-game roster snapshots (starter/DNP/reason) |
| espn_wnba_shots | 2002–2026 (25) | 80 | 147.4 MB | |
| wnba_stats_team_boxscores | 2026 only | 8 | 0.1 MB | stats-side box gap confirmed |
| wnba_stats_lineups | 2026 only | 8 | 19.5 MB | |
| wnba_crosswalk | 2026 only | 16 | 0.1 MB | team/schedule/player crosswalks, current season only |

Minimal pulls to answer the census (hashed in DOWNLOAD_MANIFEST.md): crosswalks (3 csv, 72 KB),
`team_box_2013.csv` (181 KB), `game_rosters_2013.csv` (983 KB). Measured on the mid-era sample:

- team_box 2013: 444 rows = 222 games × 2, 54 cols; season_type 2:410 / 3:34; same fixed `-0400`
  rendering. **Missing vs 2025 schema: `points_in_paint`, `fast_break_points`, `turnover_points`** —
  the prior memo's claim "team-level PIT-paint available back to 2003" is **corrected: those depth
  columns are modern-era additions** (present 2025; absent 2013). Basic four-factor box is present.
- game_rosters 2013: 4,961 rows / 22 cols (`game_id`, `team_abbreviation`, `athlete_id`,
  `starter`, `did_not_play`, `active`, `ejected`, `reason`) — roster/lineup depth exists back to
  2002, sufficient for a PIT-safe continuity mechanism from strictly-prior-game rosters.

What a successor TRAIN window needs (evidence, not prescription): schedules (have, all seasons),
per-game rosters for continuity features (available 2002+; pulled only 2013 here), PBP only for
the seasons a mechanism actually consumes (203.6 MB stats-side covers 1997–2006; ESPN-side 2002+).
Full mirror (~1.5 GB) remains OPTIONAL and owner-budget-bound; NOT pulled.

## 9. Corrections vs prior evidence (all re-measured here)

1. ESPN box `game_date_time` is NOT venue-local — fixed `-0400` rendering of the F1 instant (§3 F2).
2. ESPN schedule instant equality is 100%, not 94.03% (attempt-1/memo artifact from mixed-format parsing).
3. All-Star rows = 21 (memo: 14) under the complete alias set; neutral-site rows = 16 (memo: 15; 2026 file added one).
4. `points_in_paint` is NOT available "back to 2003" — modern-era column (absent in 2013 box).
5. Attempt-1 residual numbers (151 espn-only / 1,170 stats-only) were join artifacts (UTC-vs-local
   date mixing, game_id-prefix season grouping, int-vs-string season_type); definitive residuals are
   9 / 1,029 (§6).

## 10. Reproduction

```
.venv/bin/python lanes/A_DATA/measure_a2.py    # read-only over the corpus; rewrites measurements_a2.json + team_key_table.csv
```
No network needed for the spec itself; the depth census needs only the GitHub release API (asset
metadata) and is archived in `release_depth_census.json`.
