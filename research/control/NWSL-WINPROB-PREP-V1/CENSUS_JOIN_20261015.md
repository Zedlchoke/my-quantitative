# NWSL-WINPROB-PREP-V1 — DATA CENSUS + JOIN REPORT 2026-10-15 (read-only round 2)

Authority: owner instruction 2026-10-15 (second round). Mode: PREP READ-ONLY —
harvest + census + join only. **No outcome-frequency statistic (H/D/A shares)
was computed on any NWSL season this round**; windows stay outcome-unexposed.
Count-level facts (match counts, statuses, join keys) were read for the census
the owner mandated — this is the same exposure class the WSL law calls
"standings/match-count EXPOSED" and it binds every future claim: label
`COUNT_EXPOSED_BY_CENSUS_20261015`.

## 1. Harvest (raw bytes pinned)

All files in `~/.my-quantitative-data/nwsl-winprob-prep-v1/harvest_20261015/`
with `MANIFEST.json` (URL + HTTP + bytes + sha256 + fetched_utc each), taken
under the machine-wide heavy lock (role DOWNLOAD, FINISHED). Key pins:

- ESPN year scoreboards 2013–2026 (14 files, e.g. 2024 = 3b4527e6…, 2026 =
  6e38a441…) — year-granular endpoint `?dates=YYYY&limit=400`, 1.2 s politeness.
- nwslR `matches.csv` re-fetch **fb6addf8… = byte-identical** to the round-1
  pin (reproduction PASS); `teams.csv` 6e469725… (16 team ids).
- SoccerStatsUS tarball at commit 6a21eaeb (6a252fd2…) — CC BY 4.0.
- Disney/ESPN ToU rendered page af96072f… (200) — the ToU pin owed since
  round 1; ESPN/Disney terms govern the ESPN channel (internal research).
- Polymarket: `gamma_search_nwsl_50.json` (50 events), CLOB
  `prices-history` for a closed match draw token (13 timestamped daily
  points), open futures book demo.

## 2. Per-season census (count-level only)

| Season | ESPN n (reg/playoff) | ESPN result reliability | nwslR n | 2025–26 |
|---|---|---|---|---|
| 2013 | 89 (86/2/1) | **UNRELIABLE** — 29 rows still "Scheduled", 4 "First Half" (stale live statuses); venue only 63/89 | — | — |
| 2014 | 136 (133/2/1) | **UNRELIABLE** — 52 "Scheduled", 27 "In Progress"; venue 111/136 | — | — |
| 2015 | 115 (112/2/1) | **UNRELIABLE** — 18 "Scheduled", 10 "First Half"; venue 72/115 | — | — |
| 2016 | 103 (100/2/1) | reliable (99 FT, 1 Postponed, 3 ET-status) | 103 | — |
| 2017 | 123 (120/2/1) | reliable (122 FT, 1 Postponed) | 123 | — |
| 2018 | 113 (109/3/1) | reliable (110 FT, 2 Postponed, 1 Golden Goal) | 111 | — |
| 2019 | 111 (108/2/1) | reliable (110 FT, 1 ET) | 111 | — |
| 2020 | 108 regular | **HOLE — 0 results**: all rows "Postponed", all scores 0 | 41 (CC 23 + Fall 18, with results + penalty fields) | — |
| 2021 | 125 (120/2/2/1) | reliable (123 FT, 2 ET) | 125 (+CC 21 separate label) | — |
| 2022 | 137 (132/2/2/1) | reliable (136 FT, 1 ET) | 137 (+CC 39) | — |
| 2023 | 137 (132/2/2/1) | reliable (136 FT, 1 ET) | 137 (+CC 39) | — |
| 2024 | 189 (182/4/2/1) | reliable (187 FT, 1 ET, 1 Pens) | 182 — **scores valid only ≤ 2024-04-04** (`last_updated` freeze; later rows are placeholder 0-0) | — |
| 2025 | 189 (182/4/2/1) | reliable (186 FT, 2 ET, 1 Pens) — complete | 0 | **ESPN-only** |
| 2026 | 240 (240/0) | 216 FT done, 24 scheduled to 2026-11-01; playoffs not yet listed | 0 | **ESPN-only** |

No ESPN row is marked neutral-site in any year (neutral=0 measured; 2020 hub
season sits in the hole — successor law must not assume venue reliability for
any 2020 fill row).

## 3. 1:1 join ESPN ↔ nwslR (season-label years only; CC/Fall excluded)

Key: franchise-family pair (families measured: gotham↔sky blue, seattle↔OL
Reign incl. the nwslR slug typo "seatle", chicago red stars↔chicago stars,
FCKC↔Utah↔KC Current [year-disjoint], WNY Flash↔NC Courage) + date window
{UTC date, UTC−1} (UTC-vs-local skew ≤1 day).

| Year | ESPN | nwslR | matched | unmatched | classification |
|---|---:|---:|---:|---:|---|
| 2016 | 103 | 103 | 80 | 23 | WNY Flash↔NC Courage rename family + Postponed rows (with the family added, disagreements below only) |
| 2017 | 123 | 123 | 122 | 1 | 1 MOVED game: ESPN 2017-08-28 Postponed ↔ nwslR played 2017-09-27 (`MOVED_GAME_DISCLOSED`) |
| 2018 | 113 | 111 | 111 | 2 ESPN | 2 Postponed ESPN rows with no nwslR counterpart |
| 2019 | 111 | 111 | 111 | 0 | clean |
| 2021 | 125 | 125 | 125 | 0 | clean |
| 2022 | 137 | 137 | 137 | 0 | clean |
| 2023 | 137 | 137 | 137 | 0 | clean |
| 2024 | 189 | 182 | 181 | 8 ESPN / 1 nwslR | keys join near-clean; **nwslR scores unusable after 2024-04-04** (see §2) |

Duplicates: 0 same-date-same-pair rows in ESPN; 0 double-matched nwslR rows.

**Score disagreements (4 rows, all disclosed, none silently resolved):**
1. 2016 Championship (Spirit–Flash, After Penalties): ESPN "2-2" is the
   full-ET score; nwslR stores 90/120 score 1-1 + pens 2-3 — CONSISTENT
   (different semantics), and nwslR's penalty fields are the richer artifact.
2. 2017 Championship: **HOME/AWAY ORIENTATION FLIP in nwslR** (slug order
   NC-vs-Portland with (0,1) while Portland was home) — nwslR orientation
   must never be trusted over ESPN's explicit home/away.
3. 2017-06-17 FCKC–Reign: ESPN 1-1 vs nwslR 2-2 — **UNRESOLVED**, tertiary
   resolution or exclusion in the successor, counted either way.
4. 2021-09-04 Portland–Washington: ESPN 0-0 FT vs nwslR 3-0 — **UNRESOLVED,
   awarded-game candidate** (tertiary resolution owed; never imputed).

## 4. 90-minute label law (deterministic from ESPN status; no inference from playoff scores)

- `Full Time` → the final score IS the 90-minute result (regular season has
  no ET; playoff rows with Full Time were decided in 90).
- `After Extra Time` / `After Penalties` / `After Golden Goal` → the 90-minute
  outcome is **DRAW with competition-law certainty** (level after 90 is a
  precondition of extra time). The full-time/ET score is NEVER used as a
  90-minute score on these rows; their 90-min score line remains unknown and
  is not needed for H/D/A targets. Measured ET-class rows: 2016×3, 2018×1,
  2019×1, 2021×2, 2022×1, 2023×1, 2024×2, 2025×3 (+2026 playoffs pending).
- `Postponed` without a played result → `NOT_SCORED_POSTPONED` (nwslR 2020
  fill is a successor design decision, default EXCLUDE 2020, disclosed).
- The 4 disputed rows (§3) are excluded-or-resolved, counted, never imputed.

## 5. Team-identity stability

ESPN displayNames drift with rebrands (measured families above) + expansion
(2024 Bay FC; 2026 Boston Legacy FC; Denver). nwslR holds 16 stable hash team
ids but a stale universe (stops at the 2022 class) and one slug typo. Law for
the successor: **identity = franchise-lineage id under the frozen crosswalk**;
ESPN home/away orientation is authoritative; nwslR ids are a join aid only.

## 6. TRAIN / selection / OOS proposal (design only; nothing fitted)

| Window | Seasons | Class |
|---|---|---|
| Warm-up (ratings only, never scored) | 2013–2018 (2013–2015 results require SoccerStatsUS backfill or start 2016 — successor freeze decides, disclosed) | COUNT_EXPOSED + census-adjacent |
| Train-internal selection | 2019–2022 (2020 excluded-or-filled per §4) | selection territory |
| Chrono scored OOS (successor, post-GO) | 2023–2025 (+2026 rows after season completion) | count-exposed by this census, outcome-UNEXPOSED — can support a Stage-A-style candidate verdict, never called untouched-OOS |
| Fresh prospective | fixtures not yet played (2026 playoffs + 2027+) | clean; the only fresh-evidence surface |

This mirrors the WSL structure; the honest claim cap: because of the
count-level census, every historical number is partially-exposed-window
evidence, never fresh-holdout.
