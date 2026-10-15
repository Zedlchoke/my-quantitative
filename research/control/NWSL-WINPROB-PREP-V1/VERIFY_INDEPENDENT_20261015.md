# NWSL-WINPROB-PREP-V1 — INDEPENDENT VERIFICATION 2026-10-15 (fresh-context auditor)

## Verdict: VERIFY_PASS_WITH_FINDINGS

Independent fresh-context recomputation from the raw bytes under
`~/.my-quantitative-data/nwsl-winprob-prep-v1/harvest_20261015/` (ESPN year
scoreboards 2013–2026, `nwslR_matches_refetch.csv`, `nwslR_teams.csv`,
`MANIFEST.json`, supplement probes). All join/normalization logic in this
verification was written new from the CSV/JSON in this session; the cycle's
own scripts (`analyze_census_20261015.py`, `join_v2_20261015.py`) were NOT
read or reused. Interpreter: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
No file outside the two artifacts named in the dispatch was written.

## 1. Check table

| # | Check | Expected (census/packet/dispatch) | Measured (fresh recompute) | Result |
|---|---|---|---|---|
| 1a | sha256 `espn_nwsl_scoreboard_year_2024.json` | MANIFEST `3b4527e6…` | `3b4527e65bd375cf81c478a1cd7944fb9ce1de9fa0cd3fa8799c8015af335134` | PASS |
| 1b | sha256 `nwslR_matches_refetch.csv` | MANIFEST `fb6addf8…` | `fb6addf8a7bc1c2285e6814fa09faf7fa5dfc13dbc106d5476472005355b75f3` | PASS |
| 1c | All MANIFEST entries (bonus) | 19 files hash+bytes | all 19 match; all 3 supplement probes match | PASS |
| 2a | 2013 census | 89 events (86/2/1); 29 Scheduled + 4 First Half; venue 63/89 | 89 (regular 86 / semifinals 2 / finals 1); statuses FT 56 + Scheduled 29 + First Half 4; venue 63/89 | PASS |
| 2b | 2016 census | 103 (100/2/1); 99 FT + 1 Postponed + 3 ET-status | 103 (100/2/1); FT 99, Postponed 1, AET 2 + Pens 1 = 3 ET-class | PASS |
| 2c | 2020 all-Postponed / zero-score | 108 rows, all Postponed, all scores 0 | 108 rows, slug all `regular-season`, status `Postponed` ×108, 108/108 rows 0–0 | PASS |
| 2d | 2024 counts + slug split | 189 (182/4/2/1); 187 FT + 1 ET + 1 Pens | 189 = regular 182 + QF 4 + SF 2 + championship 1; FT 187, AET 1, Pens 1 | PASS |
| 2e | 2025 counts + slug split | 189 (182/4/2/1); 186 FT + 2 ET + 1 Pens; complete | 189 = 182/4/2/1; FT 186, AET 2, Pens 1; no postponed/scheduled | PASS |
| 2f | 2026 census | 240 rows (240/0); 216 FT + 24 Scheduled to 2026-11-01; playoffs not listed | 240 all `regular-season`; FT 216, Scheduled 24, max scheduled date 2026-11-01; no playoff slugs | PASS |
| 2g | 2014/2015 stale-status claims (bonus) | 136: 52 Sched + 27 In Prog, venue 111/136; 115: 18 Sched + 10 FH, venue 72/115 | 136: 52+27 ✓ venue 111/136 ✓ (also 1 Postponed, disclosed in raw only); 115: 18+10 ✓ venue 72/115 ✓ | PASS |
| 2h | Neutral-site claim | no ESPN row marked neutral, any year | 0 rows with neutral flag in all 14 files | PASS |
| 3 | ET-class law inputs 2016–2025 | 2016×3, 2018×1, 2019×1, 2021×2, 2022×1, 2023×1, 2024×2, 2025×3 | 2016×3 (2 AET+1 Pens), 2018×1, 2019×1, 2021×2, 2022×1, 2023×1, 2024×2 (1 AET+1 Pens), 2025×3 (2 AET+1 Pens); all other years 0 | PASS |
| 4a | nwslR 2024 freeze (post-freeze) | all rows kickoff > 2024-04-04 have scores 0-0 and `last_updated` 2024-04-04 | 162/162 post-freeze rows: scores (0,0) and last_updated 2024-04-04; 0 violations; every `last_updated` in the whole file = 2024-04-04 | PASS |
| 4b | nwslR 2024 pre-freeze scores | rows ≤ 2024-04-04 have non-placeholder scores | 20 rows ≤ 2024-04-04: 19 non-zero-score; the single 0-0 (`houston-dash-vs-racing-louisville-fc-2024-03-23`) cross-checked vs ESPN event 2024-03-24T00:30Z Houston 0-0 Louisville FT = genuine draw, not placeholder | PASS |
| 5a | 2016-10-09 championship | ESPN `Final Score - After Penalties`, 2-2; nwslR 1-1 + pens 2-3 | ESPN 2016-10-09T21:00Z "NC Courage at Washington Spirit" home 2-2, `Final Score - After Penalties`, slug `finals`; nwslR `washington-spirit-vs-western-new-york-flash-2016-10-09` 1-1, pens 2-3, `won_on_penalties=TRUE` | PASS |
| 5b | 2017-10-14 orientation flip | nwslR `north-carolina-courage-vs-portland-thorns-fc-2017-10-14` (0,1); ESPN home Portland 1-0 | nwslR (0,1) ✓; ESPN 2017-10-14T20:30Z Portland home 1-0 NC away, FT, `finals` — same winner, flipped orientation | PASS |
| 5c | 2017-06-17 FCKC–Reign | ESPN 1-1 vs nwslR 2-2, UNRESOLVED | ESPN event 2017-06-18T00:00Z FC Kansas City (home) 1-1 Seattle Reign (nwslR local date 2017-06-17); nwslR `fc-kansas-city-vs-seatle-reign-fc-2017-06-17` 2-2 | PASS |
| 5d | 2021-09-04/05 Portland–Washington | ESPN 0-0 vs nwslR 3-0 | ESPN 2021-09-05T02:30Z Portland home 0-0 Washington FT; nwslR `portland-thorns-fc-vs-washington-spirit-2021-09-04` (kickoff 2021-09-04T22:30 naive local) 3-0 | PASS |
| 6a | Independent join 2019 | n ESPN == n nwslR == matched = 111 | my own join (franchise-family pair + window {UTC, UTC−1}, 1:1): 111/111/111, 0 unmatched either side, 0 duplicate keys | PASS |
| 6b | Independent join 2021 | 125 | 125/125/125, 0/0, 0 dups | PASS |
| 6c | Independent join 2022 | 137 | 137/137/137, 0/0, 0 dups | PASS |
| 6d | Independent join 2023 | 137 | 137/137/137, 0/0, 0 dups | PASS |
| 6e | Join corroboration 2016 (bonus) | 80 matched / 23 unmatched without rename family | my join without WNY↔NC unification: 80/23 exactly; with unification: 102 matched, 1 pair left (2016-05-28 Houston–WAS Postponed vs nwslR played 2016-08-18) | PASS |
| 6f | Join corroboration 2017 (bonus) | 122 matched, 1 MOVED game (ESPN 2017-08-28 Postponed ↔ nwslR 2017-09-27) | 122/1; unmatched = Houston–NC Postponed 2017-08-28 ↔ nwslR `houston-dash-vs-north-carolina-courage-2017-09-27` (0-4) | PASS |
| 6g | Join corroboration 2018 (bonus) | 111 matched, 2 ESPN Postponed with no counterpart | 111/2; the 2 = 2018-07-29 Chicago–Gotham and 2018-09-16 NC–Chicago, both Postponed | PASS |
| 6h | Join corroboration 2024 (bonus) | 181 matched, 8 ESPN / 1 nwslR unmatched | 181/8/1 exactly; 8 = 1 Bay-FC regular-season row (nwslR counterpart sits +1 day outside the {UTC, UTC−1} window as a 0-0 placeholder) + 7 playoff rows absent from the frozen nwslR file; lone nwslR unmatched = `chicago-red-stars-vs-bay-fc-2024-06-09` 0-0 placeholder | PASS |
| 7a | MANIFEST rights: Disney ToU | `tou_disney_english.html` HTTP 200 pinned | MANIFEST `http: 200`, bytes 110693, sha256 `af96072f…`; disk re-hash matches | PASS |
| 7b | MANIFEST rights: SoccerStatsUS | tarball sha256 `6a252fd2…` | MANIFEST `6a252fd256cc8a9ec2c2d1faa94ec28f660b3043125b06d3bad224295e907036`; disk re-hash matches | PASS |
| 7c | Round-1 reproduction claim (bonus) | re-fetch fb6addf8… "byte-identical to the round-1 pin" | round-1 `SURVEY_MANIFEST.json` → `key_pins.nwslR_matches_csv.sha256` = `fb6addf8…` — equal to today's hash; claim TRUE | PASS |
| 8a | No outcome frequencies computed | round claims NONE; label `COUNT_EXPOSED_BY_CENSUS_20261015` | grep of both docs: the only frequency/share vocabulary is the negative disclosure itself (census line 4); packet B0 marked "nothing computed this round" | PASS |
| 8b | Census tables counts-only | no H/D/A or W/D/L distributions | §2 = event/status/venue counts; §3 = join counts; §4 = status-class counts; §6 = design only. No outcome distribution appears anywhere | PASS |

## 2. Discrepancies / findings

All 8 mandated checks PASS. Two minor, non-blocking findings:

- **F1 — one harvest file is not pinned in MANIFEST.json.**
  `clob_prices_history_draw_pri_chi_20260724.json` (15 bytes, content
  `{"history":[]}` — an empty CLOB prices-history response) exists in the
  harvest directory but has no entry in `MANIFEST.json` (which covers
  19 files + 3 supplement probes = 22 of the 23 data files on disk).
  sha256 `7f8b497c3d718d756d8c2130e657c4c414d5da9bed777aa29bc3221fdbcf0dc5`.
  Materiality: nil (empty probe response, not cited by any claim), but a
  pinning-completeness gap in an otherwise fully-hashed plane.
- **F2 — DECISION_PACKET headline "~1,507 matches through 2025 plus 2026 in
  progress" is not exactly reproducible.** Measured candidates: ESPN rows
  2016–2019+2021–2026 = 1,467; +41 nwslR 2020 CC/Fall fill rows = 1,508;
  scorable (FT + ET-class) rows through 2026-to-date = 1,439; scorable
  through 2025 = 1,223. No composition yields exactly 1,507. It carries a
  "~" and sits in a design paragraph; every number in the census tables
  themselves reproduced exactly. Cosmetic.
- **F3 — label shorthand (no numeric impact).** Census §4's "After Golden
  Goal" is shorthand: the raw ESPN status description is
  `Final Score - After Golden Goal` (the dispatch's three-label list omits
  the prefix on that one label). Count unaffected.

Observations that corroborate census claims: nwslR 2024 rows reference
external team id `17` (Bay FC) absent from `nwslR_teams.csv` (16 ids, max
last_season 2022) — the "stale team universe" claim is byte-true; the
`seatle` slug typo exists (69 match_ids); nwslR `last_updated` is uniformly
`2024-04-04` across all 1,170 rows; nwslR season labels are exactly as
censused (`2020 Challenge Cup` 23, `2020 Fall Series` 18, CC 21/39/39 for
2021–2023, `2024 Challenge Cup` 1); the pinned CLOB fid1440 file contains
exactly 13 timestamped daily points as the census states.

## 3. Known limitations

- Verification is count/identity/structure-level, matching the census's own
  claimed exposure class. No outcome (H/D/A) statistic was computed by this
  verifier either.
- 2013–2015 ESPN result reliability (stale live statuses) was confirmed by
  status distribution only; historical ground truth (e.g., via SoccerStatsUS)
  was not fetched — the census itself marks these UNRELIABLE and defers the
  backfill decision to the successor.
- The 2 UNRESOLVED disputed rows (2017-06-17 score, 2021-09-04 score) were
  confirmed to exist and differ exactly as disclosed; resolving which source
  is correct would require a tertiary source, which this read-only audit did
  not fetch (census defers to successor, disclosed).
- "Politeness 1.2 s", fetch-session ordering, and the exact arithmetic behind
  the packet's "~1,507" headline are not verifiable from bytes alone.
- The 2020 nwslR CC/Fall "with results" claim was verified structurally
  (score/penalty fields populated; 17/23 and 17/18 rows with non-zero
  scores; 3 penalty shootouts in CC) — the correctness of those individual
  results against history was not independently checked.
- I did not read the cycle's own analysis/join scripts (per dispatch), so
  method-level equivalence with them is not attested — only
  result-level equivalence with the published census numbers.

## 4. Artifacts

- Verdict: `research/control/NWSL-WINPROB-PREP-V1/VERIFY_INDEPENDENT_20261015.md` (this file)
- Handoff: `research/control/NWSL-WINPROB-PREP-V1/handoffs/L_VERIFY_R2.json`
- Raw bytes audited: `~/.my-quantitative-data/nwsl-winprob-prep-v1/harvest_20261015/`
