# VERDICT_TABLE — Lane A_DATA, cycle NFL-WINPROB-NG-SCORED-V1

Audit time 2026-10-05 (runs 09:01–09:20Z). Verdict vocabulary: PASS / FAIL / NOT_RUN —
missing evidence is NOT_RUN, never inferred PASS. Evidence: DOWNLOAD_MANIFEST.md (+.json),
PBP_COVERAGE_AUDIT.md, SUCCESSOR_DATA_AUDIT.md (same directory); raw measures
`~/.my-quantitative-data/nfl-ng-scored-v1/provenance/`.

| # | check | verdict | evidence (measured) |
|---|---|---|---|
| 1 | Rights: license re-fetch live, sha256 = pin `2a82ac9b…b9111` | **PASS** | fetched 2026-10-05T09:01:18Z HTTP 200, 18,651 bytes, sha256 equal to pin; title line CC BY 4.0 verbatim; no BLOCKED_DATA_RIGHTS |
| 2 | Download pbp 2000–2017, 18 files, provenance per file | **PASS** | 18/18 HTTP 200, PAR1-verified, 315,021,834 bytes total; per-file url/http/downloaded_utc/bytes/sha256 in DOWNLOAD_MANIFEST.json; release timestamp.json held (05:28:21Z, sha `7ad032c1…`); ATTRIBUTION.md written |
| 3 | Spot re-download determinism (1 file) | **PASS** | season 2011 re-fetch byte-identical (sha `c54753b8…8795b1`, 19,117,830 bytes, identical=YES) |
| 4 | Release marker + asset metadata capture | **PASS** | release `pbp` updated_at 2026-10-05T05:28:24Z; per-asset updated_at 2000–2017 = 2024-08-25…2026-08-13; sizes match API for 18/18; API digests match local sha for the 3 assets that carry one (2000/2001/2002) |
| 5 | pbp↔games.csv join (rate; orphan census) | **PASS (gap named)** | 0 orphan game_ids in all 18 seasons; 17/18 seasons exact; 2000: 257/259 games — 2 missing named (`2000_03_SD_KC`, `2000_06_BUF_MIA`) |
| 6 | REG/POST split via `season_type` | **PASS** | REG 246/248/256 (2000/2001/2002+) + POST 11 every season; reconciles with games.csv `game_type` per season |
| 7 | Team-abbrev domain vs 32-lineage map | **PASS (documented normalization)** | pbp carries ONLY current 32-lineage codes (SD/STL/OAK absent all seasons; LAC/LA/LV present all seasons); 2000 role-aligned check 257/257 games, 0 mismatches under map {SD→LAC, STL→LA, OAK→LV}; old-abbrev expectation fails by upstream normalization, not data loss — games.csv side must apply the frozen lineage map |
| 8 | EPA availability (`epa`/`posteam`/`defteam` non-null on relevant rows) | **PASS** | epa non-null on 99.37–100.0% of team-attributable rows per season; posteam/defteam populated on identical sets; blank-posteam rows (~5% typical, 1.3% in 2000) named and excluded from per-team counts |
| 9 | Older-season schema differences relevant to C3 | **PASS (caveats disclosed)** | identical 372-column schema in all 18 files; all C3 columns present everywhere; play_type vocabulary identical (9 values) in 2000–2005 vs 2006–2017; measurable caveats: 2000 play_type blank 8.8% vs ~3%, down non-null 84–86% |
| 10 | Freeze fact: TRAIN = complete seasons 2000–2018 | **PASS** | re-measured 259/259/267×16 rows (5,057), 0 rows missing scores; 2022 = 271 REG (canceled game omitted — row-count law) |
| 11 | Freeze fact: 1999 exclusion (gametime missing) | **PASS** | re-measured 259/259 rows gametime-empty and kickoff-unparseable |
| 12 | Freeze fact: kickoff fallback X | **PASS (NOT ACTIVATED)** | gametime 100% present 2000–2026 (0 empty per season); trigger condition does not hold |
| 13 | Freeze fact: neutral-site flag (`location`, HCA=0 law) | **PASS** | values {Home, Neutral} only; 2000–2018 = 5,006 Home / 51 Neutral (per-season census recorded) |
| 14 | Fresh 2026 recount at audit time | **PASS** | 272 REG scheduled / 63 played (all finals; 0 started-without-score) / 209 future / future-with-scores 0 (law holds) / earliest future 2026-10-06T00:15Z `2026_04_ATL_NO` / week-5 opener `2026_05_TB_DAL` 2026-10-09T00:15Z (measured) / snapshot 486d7227… = compile 2026-10-05T05:46:22Z, mtime-vs-measured-at disclosed |
| 15 | C3 PIT admissibility | **PASS_PIT_SEASON_GRAIN (offseason-prior role only)** | snapshot story (completed seasons stable months-years; only the 2026 in-season asset re-cuts weekly — today's release touch = 2026 asset only); boundary margin 213.0–223.7 days measured at every boundary 2001–2017; coverage + EPA rates per #5/#8; registration-time snapshot freeze + sha disclosure required (sha256s already pinned) |
| 16 | Boundary compliance of this lane | **PASS** | no scored computation; no win-prob/calibration metric; no 2019–2025 outcome reads (archive untouched); $0; ≤2 GitHub API calls (used 2, cached); no git commands; writes only in allowed paths |

No FAIL, no NOT_RUN. STOP CONDITIONS not triggered (license matched; no download stall —
18 files in ~39 s).
