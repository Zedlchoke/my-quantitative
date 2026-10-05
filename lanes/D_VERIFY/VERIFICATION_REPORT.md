# VERIFICATION REPORT — Lane D (INDEPENDENT VERIFIER) · WINPROB-PLAYERDATA-PREP-V1 · 2026-10-05

Verifier method: recompute against the bytes with independent code written in this lane
(`verify_hashes.py`, `verify_coverage_nba.py`, `verify_coverage_wnba.py`,
`verify_coverage_nfl.py`, `verify_pit_examples.py` — all under `lanes/D_VERIFY/`, machine
outputs `*_output.json` alongside). Lane scripts were never reused. No repairs, no commits,
no scored computation. Budget: $0; 3 public URL fetches (license re-verification only),
0 re-downloads needed.

**Overall verdict: VERIFIED — every load-bearing claim in lanes A/B/C/R reproduces from the
bytes. 2 discrepancies found, both MINOR/INFO (explanatory accounting and wording); no
BLOCKER, no MAJOR. All four lane recommendations stand.**

---

## Task 1 — Provenance / hashes → **VERIFIED**

Commands: `verify_hashes.py` (independent sha256 via Python hashlib, 1 MiB chunks).

- **NBA (full manifest, 5/5 files)** vs `~/.my-quantitative-data/playerdata-prep-v1/nba/download_manifest.json`:
  player_box_2016.csv (16,687,907 B, `ffd09dec…13ec74397`), player_box_2021.csv
  (16,122,075 B, `86b12342…5110bcc638f`), player_box_2026.csv (17,729,581 B,
  `7a4868da…56f1becc89`), timestamp_refetch1.txt + timestamp_refetch2.txt (24 B,
  `142bf92a…7b1194038c` each) — **bytes AND sha256 all MATCH**. The full hashes in
  `lanes/A_NBA/DOWNLOAD_MANIFEST.md` also match byte-for-byte.
- **NFL (full manifest, 8/8 files)** vs `lanes/C_NFL/download_manifest_C_NFL.json`:
  stats_player_week_2024/2025/2026.parquet, stats_player_regpost_2025.parquet,
  snap_counts_2025/2026.parquet, timestamp_stats_player.json, timestamp_snap_counts.json —
  **bytes AND sha256 all MATCH** (e.g. week_2024 = 849,243 B / `847569d1…9d155c1`;
  week_2026 = 303,597 B / `49bc644e…6261 79`).
- **WNBA (spot sample, 6 files ≥ required 4, incl. one player_box + one game_rosters,
  incl. 2002-era and 2026)** vs prior-cycle manifest
  `~/.my-quantitative-data/wnba-prep-v1/roster_audit/download_manifest_r2.json`
  (WNBA-WINPROB-PREP-V1 lane A): player_box_2002/2013/2026.csv +
  game_rosters_2002/2013/2026.csv — **bytes AND sha256 all MATCH** (e.g. player_box_2002 =
  71,853 B / `04b24fa1…f1588ed`). Corpus byte-sum also re-measured:
  **86,572,091 B over 50 CSVs — exactly the lane B claim**.

## Task 2 — Coverage spot-recompute (independent code) → **VERIFIED**

### (a) NBA (verify_coverage_nba.py)

| season | claimed | measured | verdict |
|---|---|---|---|
| 2016 | 1317/1317, rows 33,715 | schedule 1317 rows (all `post`), box distinct games 1317, join 1317/1317, rows 33,715, dup (game_id,athlete_id) 0, orphans 0 | MATCH |
| 2021 | 1172/1204 = 0.9734; all gaps STATUS_POSTPONED | schedule 1204 `post` rows of which **32 STATUS_POSTPONED** → played 1172; box distinct 1172; join 1172/1172 = **100% of played**; rows 31,593; dups 0; the 32 gap games are all `STATUS_POSTPONED` | MATCH |
| 2026 | 1326/1330 = 0.9970 | 4 gap games, all `STATUS_POSTPONED`; join 1326/1326 played; rows 34,883; dups 0 | MATCH |

INFO (wording only): lane A's handoff sentence "ALL 36 gap games are STATUS_POSTPONED" is
true only as a **three-season total** (32 in 2021 + 4 in 2026); 2021 alone has 32. The
substance ("every gap game is postponed, hence 100% of played games covered") is verified
for all three seasons.

Supporting lane A detail claims re-measured exactly: DNP rows 5,698/6,517/6,082;
2026 NULL-athlete_id rows = 33 (0 in 2016/2021); 2021 starter flag = exactly 5 per
team-game in 2,344/2,344.

### (b) WNBA (verify_coverage_wnba.py — universe law re-implemented from the spec, not from measure_b.py)

| quantity | claimed | measured | verdict |
|---|---|---|---|
| ESPN-side universe 2002–2026 | 5,988 | **5,988** (filter law: `status_type_state=='post'`, drop Forfeit/Postponed, drop 13 All-Star abbreviations) | MATCH |
| player_box join | 5,624 / 5,988 = 93.92% | **5,624 = 93.92%** | MATCH |
| player_box extras | 19, all ASG | 19, **all in the alias set** (none in 2002) | MATCH |
| game_rosters join | 5,983 / 5,988 = 99.92% | **5,983 = 99.92%** | MATCH |
| season 2002 | 16/271 = 5.9% | 16/271 = 5.9% | MATCH |
| season 2004 | 214/237 = 90.3% | 214/237 = 90.3% | MATCH |
| season 2013 | 100% | 221/221 = 100% | MATCH |
| season 2026 | 100% | 341/341 = 100% | MATCH |
| dropped rows | forfeit 401018942; postponed 401507167, 401857072; 21 ASG rows | identical (re-derived independently) | MATCH |

MINOR discrepancy (explanatory accounting only): lane B's table states game_rosters
"5,997 games in files / 14 extras (13 ASG + forfeited game)". Measured:
**6,004 distinct game_ids in the rosters files; 21 extras = 20 All-Star games + the
forfeited 401018942**. The covered headline (5,983/5,988 = 99.92%) and the 5-missing-game
enumeration (1×2002, 2×2006, 1×2008, 1×2016) are correct; only the extra-game census is
undercounted by 7 ASG games (2002's ASG 220715098 is present in rosters, and all 2003–2026
non-Olympic ASGs are present). No coverage claim is affected; the successor "extras are
explainable" law still holds (all extras are ASG or the forfeit).

### (c) NFL (verify_coverage_nfl.py)

| claim | measured | verdict |
|---|---|---|
| 2024: 18,983 rows × 150 cols; 285 games; join 285/285; dups (player_id,game_id)=0; weeks 1–22; POST = 6+4+2+1 | 18,983 × 150; 285 distinct game_ids; 285/285 in games.csv, 0 orphans; 0 dups; weeks 1–22; POST games/wk {19:6, 20:4, 21:2, 22:1} | MATCH |
| 2025: 19,422 × 150; 285 games | 19,422 × 150; 285/285; 0 dups; POST 6+4+2+1 | MATCH |
| 2026: 4,379 × 150; 63 games; 63/63 | 4,379 × 150; 63/63, 0 orphans; weeks 1–4 REG; 209 season-2026 games without stats (= frozen future set) | MATCH |
| schema drift NONE 2024–2026 | column lists identical across the 3 files | MATCH |
| placeholder: 1 all-zero NaN-player row per week (22/22/4) | NaN-player rows: 22 / 22 / 4, exactly one per week (enumerated game_ids confirmed) | MATCH |
| snap_counts 2025: 26,613 × 16, 285/285, dup (pfr,game)=0; 2026: 49 games | 26,613 × 16; 285/285; 0 dups; 2026 = 4,579 rows / 49 games / 49/49 | MATCH |

## Task 3 — PIT verdict logic → **VERIFIED**

All three PIT_AUDIT.md files contain a worked example and apply the doctrine correctly:
strict inequality on tip/kickoff time for prior-game aggregation, same-game stats marked
BANNED/FORBIDDEN, and NOT_RUN_PIT (never inferred PASS) wherever pre-game publish
timestamps are absent (NBA target-game starter/DNP/active; WNBA target-game fields +
opening-roster v1; NFL injuries/rosters, F5/F7). Lane A additionally documents a
conservative-margin option; lane C documents the release-cadence availability basis and
the GSIS↔PFR crosswalk blocker; lane B correctly rules `active`/`reason` unusable and
restricts opening-roster use to v2.

End-to-end recomputation of all three worked examples (verify_pit_examples.py) — each
reproduces **exactly**:

- **NBA MIL** (lane A): target 401307387 MIL@WSH tip_utc 2021-03-15T23:00Z; prior-5 = the
  same 5 game_ids (401267680 02-28, 401267700 03-03, 401267715 03-05, 401307356 03-12,
  401307372 03-14); MIL minutes per game 240/240/240/238/239 → mean **239.4** (claim 239.4);
  strict inequality and target-absence both hold.
- **WNBA CON 2013** (lane B): target 400445816 tip 2013-07-06T23:00Z; prior-5 = same ids
  400445826/400445854/400445709/400445771/400445798 at the same tips; CON (team_id 18)
  team-minutes **200/201/200/199/202** (claim 199–202); 9 players with minutes each; both
  leak guards hold.
- **NFL KC 2024** (lane C): target 2024_11_KC_BUF kickoff_utc 2024-11-17T21:25Z (my own
  ET→UTC canonicalization of gameday+gametime reproduces it); prior-3 = 2024_08_KC_LV
  (10-27T20:25Z), 2024_09_TB_KC (11-05T01:15Z), 2024_10_DEN_KC (11-10T18:00Z); Mahomes
  (00-0033873) prior-3 totals **819 pass yds / 6 TD / 1 INT / 124 att** (claim identical);
  strict inequality and target-absence hold.

## Task 4 — Rights honesty → **VERIFIED**

3 of lane R's license URLs re-fetched live (2026-10-05, this lane; ≤3 budget):

| URL | result |
|---|---|
| `raw.githubusercontent.com/sportsdataverse/sportsdataverse-data/HEAD/LICENSE` | HTTP 200, 1,072 B, sha256 `9c3898cc…123ea6` — **byte-identical** to lane A's `provenance/LICENSE_sportsdataverse-data.md` and lane R's `fetches/sportsdataverse_data_LICENSE`; "MIT License / Copyright (c) 2023 SportsDataverse" verbatim, "and/or sell" grant present |
| `raw.githubusercontent.com/nflverse/nflverse-data/HEAD/LICENSE.md` | HTTP 200, **18,651 B, sha256 `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111` — exactly the sha256 lane C claims**; byte-identical to lane C's `rights/nflverse-data_LICENSE.md` and lane R's fetch; both quoted identification lines ("Attribution 4.0 International", "Creative Commons Attribution 4.0 International Public License") verbatim in live bytes |
| `raw.githubusercontent.com/sportsdataverse/hoopR-nba-data/HEAD/LICENSE.md` | HTTP 200, 1,061 B — byte-identical to lane A's copy and lane R's fetch; CC BY 4.0 title, "Copyright (c) 2026 hoopR.nba authors", "(data, code, and documentation)", "even commercially" all verbatim |

No divergence between any quoted text and live bytes. The `.md`/404 variants are correctly
recorded (LICENSE.md 404 on sportsdataverse-data; LICENSE 404 on nflverse-data).

**balldontlie Free**: BALLDONTLIE_FREE.md attributes every quote with URL + HTTP + UTC
(fetch register) and quotes the tier tables. Against lane R's own archived docs HTML I
confirmed the exact tier row sequence "Players Yes/Yes/Yes, Games Yes/Yes/Yes,
**Game Player Stats No/Yes/Yes**, Active Players No/Yes/Yes, Player Injuries No/Yes/Yes",
"Account Tiers" 3× occurrences, and the $39.99/$9.99/$0 price points. The conclusion
"Free = Teams/Players/Games metadata only; player stats paid (NBA Season Averages and Box
Scores GOAT-only; WNBA Player Stats GOAT-only)" **follows directly** from the quoted tier
tables. No key was used anywhere (only placeholder "YOUR_API_KEY" strings appear, inside
the vendor's own docs HTML).

## Task 5 — Cross-lane consistency → **VERIFIED**

(a) Store-license claims agree across lanes: A ("sportsdataverse-data LICENSE = MIT …
LICENSE.md is 404; file has no extension" + hoopR-nba-data CC BY 4.0), B ("README badge =
CC BY 4.0 (data), root LICENSE = MIT Copyright (c) 2023 SportsDataverse (code)"), R (dual
marker, both verbatim, NOTICE 404) — mutually consistent and verified against live bytes.
C (nflverse-data CC BY 4.0) verified against live bytes. All four lanes state the
fail-closed position on underlying ESPN/NBA/WNBA/NFL rights consistently (grant=N).

(b) Each lane's VERDICT_TABLE is consistent with its handoff JSON authority_claims/tests:
A 18-check table ↔ 22 handoff tests (numbers identical); B 20-check table ↔ handoff tests
(numbers identical); C table's 16 PASS / 2 NOT_RUN_PIT / 1 NOT_RUN / 1 BANNED ↔ handoff
finding_counts and verdict `PREP_DATA_VERIFIED_HOLD_FOR_FEATURE_PREP`; R table 0 FAIL /
4 recorded 404s ↔ handoff finding_counts.

(c) NBA season-label convention: player_box_2016 game dates measured **2015-10-27 …
2016-06-19** (claim exact); schedule corpus `nba_schedule_2016.csv` spans the same dates
(same ending-year labels), and the schedule corpus totals **14,254 rows over 2016..2026**
(claim exact). The empirical 100%-played join in all three seasons independently confirms
label alignment.

## Task 6 — Accounting & boundaries → **VERIFIED**

- **No scored outcomes**: grep over `lanes/` for log_loss/brier/predict/win-prob
  computation patterns → 0 hits; FEATURE_PROPOSALS content is design-only everywhere;
  data dirs contain only raw downloads, manifests, provenance logs and rights copies —
  no metric/feature artifacts.
- **No lane commits**: branch `orca/winprob-playerdata-prep-v1-integration` HEAD =
  `a025a5d2aabf65f4019ca5168f94efc3208738d5` (= dispatch SHA = bootstrap commit "…lanes
  skeleton + control state…"); nothing committed after it; local HEAD == remote head.
- **Write scope**: `git status --porcelain` untracked entries are exactly
  `lanes/{A_NBA,B_WNBA,C_NFL,R_RIGHTS,D_VERIFY}/` + `lanes/DISPATCH/handoff_*.json` —
  lanes never touched each other's dirs, ledgers, registries, or frozen artifacts; all
  heavy data lives outside git under `~/.my-quantitative-data/playerdata-prep-v1/`
  (+ read-only corpora untouched: WNBA corpus re-hash 50/50 with zero writes).
- **No secrets**: pattern sweep over `lanes/` finds no key material — all "API key" hits
  are the vendor docs' `YOUR_API_KEY` placeholders inside lane R's archived public HTML,
  plus negative statements ("no API keys used", "key untouched in Keychain").
- **Cost $0 consistent**: A = 3 public CSVs + docs (free GitHub), C = 8 public release
  assets + 1 unauthenticated API call, B = 0 downloads, R = public docs only; no purchase
  or signup records anywhere. This lane's own cost: $0, 3 URL fetches, no re-download
  needed.

## Task 7 — Recommendations check → **ALL FOUR STAND**

- **A_NBA "GO for FEATURE-PREP (not a scored GO, owner + fresh registration required)"** —
  supported: 100% of played games covered in all 3 sampled seasons, zero duplicates, PIT
  as-of join proven, caveats honestly enumerated (3/25 seasons sampled, `active`
  unreliable, rights fail-closed). Not over-claimed: the GO is explicitly conditional and
  PREP-level.
- **B_WNBA "READY — authorize FEATURE-PREP with scope conditions"** — supported: coverage
  recomputed exactly (incl. the 2002/2003/2004 backfill-hole law), PIT worked example
  reproduces, availability-semantics law measured. The conditions (≥90% seasons 2004+,
  minutes-quality 2013+, v2 as-of law, era guards) follow directly from the measured
  coverage and schema eras.
- **C_NFL "HOLD for FEATURE-PREP"** — supported and conservative: the data itself verified
  (perfect joins, zero drift), but player-level snap joins remain blocked on the not-yet-
  downloaded `players.parquet` GSIS↔PFR crosswalk and target-game status stays
  NOT_RUN_PIT; HOLD with named unblock conditions is the evidence-faithful call.
- **R_RIGHTS "PREP_RIGHTS_VERIFIED_WITH_OPEN_QUESTIONS"** — supported: 0 contradictions on
  re-verification; the four carried UNCLEAR items (underlying league rights, attribution
  compliance, scraped-endpoint ToS, balldontlie ToS) are real open questions, honestly
  fail-closed.

## Discrepancy register

| # | lane | severity | discrepancy | impact |
|---|---|---|---|---|
| 1 | B_WNBA | **MINOR** | game_rosters extra-game census undercounted: claimed "5,997 games in files / 14 extras (13 ASG + forfeit)"; measured 6,004 / 21 extras (20 ASG + forfeit 401018942) | None on coverage claims (5,983/5,988 = 99.92% verified; missing-game enumeration correct); successor should cite 20 ASG extras |
| 2 | A_NBA | **INFO** | "ALL 36 gap games are STATUS_POSTPONED" is a three-season total (32 in 2021 + 4 in 2026), not 2021 alone (2021 gap = 32) | Substance fully verified — every gap game in every sampled season is STATUS_POSTPONED and 100% of played games are covered |
| 3 | C_NFL | **INFO** | regpost_2025 measured at 2,025 rows × 148 cols; lane C's docs claim no specific shape for this file (download-only), so no conflict | None — recorded here for successor reference |

No BLOCKER or MAJOR discrepancies. Nothing required repair; nothing was repaired.
