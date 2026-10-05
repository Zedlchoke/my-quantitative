# VERIFICATION REPORT — Lane D · INDEPENDENT VERIFIER (wbap-d-verify)

- Cycle `WNBA-WINPROB-PREP-V1` · role quant-auditor (A7-equivalent, fresh context) · 2026-10-05
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration`,
  branch `orca/wnba-winprob-prep-v1-integration`, HEAD measured
  `18fa135b69fb75b346f0e8a0298d624bc1879598` (= dispatch_sha = actual_start_sha). No commits,
  no repairs; write scope `lanes/D_VERIFY/**` only. Lanes A/B/C artifacts verified as committed
  (`git ls-files lanes/` lists all 10 A/B/C files).
- Method: every load-bearing number below was **recomputed from corpus bytes by an independent
  implementation** (`lanes/D_VERIFY/verify_d.py`, run with
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`; read-only over
  `~/.my-quantitative-data/wnba-v1/raw/` and `~/.my-quantitative-data/wnba-prep-v1/`).
  Lane A's `measure_a2.py` was read and audited but NOT re-executed (it rewrites its outputs).
  Schema/coverage counting only — no win-prob metric computed anywhere, per plan law.

## VERDICT: VERIFICATION_FAIL

Narrow, fully-scoped failure: the canonical team-key table resolves the flagged
franchise-lineage conflict on the wrong branch (D-1, MAJOR), and four MINOR documentation
defects ride on it. Everything else — every byte-level count, join residual, timestamp law,
hash, rights statement, PIT verdict, mechanism/protocol freeze, and boundary check —
reproduced exactly. Defect counts: **1 MAJOR, 4 MINOR, 0 BLOCKER, 0 CRITICAL** (+4 cosmetic
observations, not defects). The successor's B1 freeze remains blocked on the lineage map per
Lane C §8.3; the fix is a narrow, byte-driven rebranch (no corpus change), listed in D-1.

---

## Check 1 — Bytes vs claims

### 1a. Identity and per-season census 1997–2026 — PASS (all reproduce)

Recomputed independently (`verify_d.py`): ESPN 6,029 rows / 6,029 unique `game_id` / 25 seasons
(2002–2026) / all 9-digit ids. Stats 7,009 rows / 7,009 unique ids / 30 seasons (1997–2026);
`game_id` = `10` + type digit + YY + 5-seq: prefix `10` on 7,009/7,009; type-digit↔season_type
crosstab perfect (`2`↔regular-season 6,494; `4`↔playoffs 515); `[3:5]==YY` 100%.

Census after the filter law (mine vs claim — identical):

| season | ESPN total / real (RS-xCup+Cup+PO) | stats total / real (RS+PO) | rowdiff |
|---|---|---|---|
| 1997 | — | 115 / 115 (112+0+3) | — |
| 1998–2001 | — | 158, 203, 272, 274 (all real) | — |
| 2002 | 272 / 271 (256+0+15) | 273 / 273 (256+17) | −1 |
| 2010 | 221 / 220 | 220 / 220 | +1 |
| 2016 | 220 / 220 | 220 / 220 | 0 |
| 2019 | 221 / 220 | 220 / 220 | +1 |
| 2020 Wubble | 147 / 147 (132+0+15) | 147 / 147 (132+15) | 0 |
| 2021 | 211 / 210 (132+61+17) | 209 / 209 | +2 |
| 2025 | 312 / 311 (250+37+24) | 310 / 310 (286+24) | +2 |
| 2026 | 360 / 341 (281+50+10) + 17 pre + 2 postponed | 340 / 340 | +20 |

Totals: ESPN real **5,988 = 5,230 RS-excl-Cup + 301 Cup + 457 PO** ✓; stats real
**7,008 = 6,493 RS + 515 PO** ✓; pre-2002 stats real **1,022** ✓; rowdiff within ±3 for
2002–2025, +20 in 2026 ✓. All season shapes in SPEC §5 (1997=115, 2021 210/209, 2022 240/239,
2023 261/260, 2024 263/262, 2025 311/310, 2026 341+17+2 vs 340) match byte-for-byte.

### 1b. Filter/exclusion law (spot seasons incl. 2018 forfeit + 2026 TBD) — PASS

- Non-`post` rows: exactly **17**, all 2026, all pre-filled 0–0, 0 null scores ✓.
- Forfeit: exactly **1** row — `401018942`, ESPN date `2018-08-04T00:00Z` (ET 2018-08-03),
  Washington Mystics home vs Las Vegas Aces, 0–0, state `post`; stats twin `1021800162`
  0–0 with blank win/loss flags, the **only** 0–0 row on stats side (7,009 rows scanned,
  0 null-score rows) ✓.
- Postponed: exactly **2** — `401507167` 2023-06-07T23:00Z NYL–MIN and `401857072`
  2026-07-17T01:00Z DAL–NYL, both 0–0, both state `post` ✓.
- All-Star aliases: **21** ESPN rows, exactly one per ASG season; absent in 2008/2012/2016/2020 ✓;
  stats side **0** ✓. Abbr breakdown measured (EAST 11, WEST 11, USA 4, WIL 3, ALL 3, DEL 2,
  STE 2, CLA/COL/SPO/COOP/PAR/WNBASTARS 1 each) — see defect D-3.
- TBD placeholders: **7** rows, all state `pre`, dates 2026-10-17 … 2026-11-01 ✓.
- Neutral site: **16** rows (10 All-Star + 6 real: 2016-09-29 LAS–CHI, 2016-07-22 ATL–DAL,
  2021-08-13T01:00Z SEA–CON, 2024-06-06 WAS–CHI, 2025-08-16T02:00Z ATL–SEA, 2026-08-12T02:00Z
  LA–PHX) ✓.
- Commissioner's Cup: **301** rows, all `season_type=2`, 2021–2026 ✓.

### 1c. Union universe and cross-source reconciliation — PASS

Independent two-pass join (normalized name pair + ET date ±1 window, then exact name-pair+score):
**5,954 window matches, all at offset 0** (0 at ±1) + 24 window-ambiguous pairs resolved by
**25 score fallbacks** (24 back-to-back series games + the 2019 suspended game
`401156333`↔`1021900079`, ESPN ET 2019-08-05 vs stats 2019-07-05, identical 70–99);
**ESPN-only = 9** (3 regular: `270620018` 2007-06-20 CON home–NY 73-76; `290709009` 2009-07-09
NYL home–LAS 60-69; `400182104` 2011-06-04 IND home–CHI 65-57; plus the **6** Cup finals
2021–2026, one per season, absent from stats side); **stats-only = 1,029** = 1,022 in 1997–2001
+ **7** extras (`1040200103`, `1040200133` 2002-08-20 PO; `1020300043` 2003-06-12;
`1020300141` 2003-07-22; `1020400001`, `1020400002` 2004-05-20; `1020400014` 2004-05-25) ✓.
**Union 7,017 = 5,988 + 1,029** ✓. Zero 0-0/null-score contamination possible under the filter
law (verified directly on bytes).

### 1d. Timestamp canonicalization (≥9 sampled rows) — PASS

- ESPN schedule: `date == game_date_time` **6,029/6,029** and `date == start_date`
  **6,029/6,029** per-file ISO8601-UTC parse ✓ (attempt-1's 94.03%/360 was a parse artifact,
  superseded values confirmed still on disk in `measurements_a.json`: `equal_pct = 94.03`,
  `unequal_rows = 360`, `espn_played_only = 151`, `stats_played_only = 1170` — the four
  recorded attempt-1 corrections are real and correctly superseded).
- Rendering: 2002–2025 suffix `Z` 100%; 2026 suffix `-0400` on all 360 rows incl. Las Vegas
  (26), Phoenix (22), Seattle (22) homes ✓ — cosmetic, instants identical.
- Manual spot rows (29 printed across 2002–2026), e.g. `401857072`: `date`
  2026-07-17T01:00Z == `game_date_time` 2026-07-16T21:00:00-0400 — same instant ✓.
- ESPN box (2025 sample): instant equality **312/312**, 624/624 rows carry fixed `-0400`,
  `game_date` == ET date **100.0%**, == UTC date **53.53%** ✓. **The correction of the prior
  memo's venue-local claim is VERIFIED**: the box timestamp is the schedule instant with a
  cosmetic fixed `-0400` suffix for all venues.
- PBP `wallclock`: 100% `Z`; first event − tip median **+3.15 min** (p05 2.45, p95 6.89) ✓.
- Stats `game_date` == ET date of tip: all window matches hit at offset 0 (**5,954/5,954**,
  0 at ±1) ✓.

### 1e. Rename-map boundaries (≥4 franchise events) — PASS on boundaries, **FAIL on lineage**

Boundaries all re-measured from bytes: UTA 1997–2002 → SAN 2003–2017 (Silver Stars
2003–2013, Stars 2014–2017); DAL 2016–2026; LVA 2018–2026; DET 1998–2009 → TUL 2010–2015;
ORL 1999–2002 → CON 2003–; PHO 1997–2024 → PHX 2025–2026 (stats abbr); POR 2000–2002 vs PDX
2026 (stats) with ESPN using `POR` for both eras; defunct CHA 2006 / CLE 2003 / HOU 2008 /
SAC 2009 / MIA 2002; expansion CHI 2006 / ATL 2008 / GSV 2025 / TOR 2026 ✓. ESPN 2002
DET/TUL artifact re-confirmed (see D-2 for scope). Team count 12 distinct stats abbrs in each
of 2015/2016/2017/2018 ✓.

**FAIL — D-1 (MAJOR): the canonical team-key table resolves the flagged lineage conflict on
the wrong branch.** `team_key_table.csv` (and SPEC §2) encode:

- `SAN_DAL` = {UTA, SAN, DAL}, seasons 1997–2026 continuous, with the spec text "SAN …
  2003–2015 → DAL Dallas Wings 2016–" and "2016 overlap SAN+DAL is the merger season";
- `DET_TUL` = {DET, TUL}, seasons **1998–2015 (terminated)**;
- `LVA` = separate franchise 2018–2026 with **no prior stream**.

Measured bytes refute the table's own text: **San Antonio rows exist in 2016 AND 2017**
(San Antonio Stars = 2014–2017), and SAN + DAL coexist as two of 12 distinct teams in both
2016 and 2017 — a single franchise cannot continue SAN→DAL across two seasons of
coexistence. The real franchise-license history (as flagged by Lane C §8.3 and stated in the
cycle facts) is **TUL→DAL 2016, SAN→LVA 2018, Sparks never move**. The spec is also
internally contradictory: its own `LVA` row says "SAS→LVA relocation: SAN last season 2017,
LVA first 2018" while the `SAN_DAL` row ends SAN at 2015 and rebrands it DAL. Consequence
(per Lane C's own law): the successor's B1 stream map would give Dallas the Utah/San Antonio
history, terminate the Tulsa stream, and cold-start Las Vegas — wrong on all three counts;
W-H2 continuity would pair the wrong franchise histories. Required correction (data-driven,
narrow): rebranch DAL into the DET_TUL lineage (DET→TUL→DAL) and make LVA the modern key of
the UTA→SAN lineage; update SPEC §2, `team_key_table.csv`, and handoff_A authority claims.

### 1f. Re-hash (≥3 corpus + new files) — PASS

Byte-exact vs `raw/audit_results.json` manifest (99 entries, `digest_mismatches: []`):
`espn_schedules/wnba_schedule_2020.csv` (98,943 B), `wnba_stats_schedules/wnba_schedule_1997.csv.gz`
(2,001 B), `wnba_schedule_2002.csv` (167,142 B), `espn_sample_2025/team_box_2025.csv`
(276,125 B), `espn_sample_2025/player_box_2025.csv` (3,559,371 B). New artifacts:
`extensions/team_box_2013.csv` sha256 `e2f7510a…72d2c597` and
`extensions/game_rosters_2013.csv` sha256 `49571374…f36670` match DOWNLOAD_MANIFEST **and**
their recorded GitHub digests; `release_depth_census.json` sha256 `adf01fec…2e47a6f2d54d`
matches DOWNLOAD_MANIFEST verbatim; `team_key_table.csv` and `measurements_a2.json` hashed
(this report). measurements_a2.json's on-disk values for every block cited above equal my
recomputation.

## Check 2 — Rights / attribution / no scraping — PASS

`raw/ATTRIBUTION.md` carries the verbatim CC BY 4.0 README badge + MIT code license
(SportsDataverse `sportsdataverse-data` release store, nflverse-family pattern) and the
required attribution sentence; Lane A extensions were pulled as public GitHub release assets
(no auth/account) with api.github.com metadata archived and digested. Lane A's scripts
(`measure_a.py`, `measure_a2.py`, my `verify_d.py`) contain **zero network code** — grep for
`urllib|requests|http|url|download` over both lane scripts returns nothing; they read local
CSVs only. No lane references wnba.com / stats.wnba.com / ESPN API / Sports Reference hosts as
access targets; Sports Reference FAIL 5(11) and balldontlie BLOCKED_NO_KEY are recorded in
Lane B §1. The maintainer-confirmation caveat (needed only before external redistribution) is
honestly recorded in handoff_A known_limitations.

## Check 3 — PIT verdicts — PASS

`PIT_AUDIT_WNBA.md` adjudicates exactly **12 feature classes**: 4 PIT_SAFE-by-construction
(results, rolling form, Elo, standings), 1 PIT-safe-with-conditions (season-start continuity),
2 POST_GAME_FACT (player_box active/DNP/starter/reason; team_box current-game stats),
1 PIT-safe-only-as-strictly-prior-aggregates (PBP), 2 NOT_RUN_PIT (injury; lineups
2026-only), 1 identity-only (crosswalk), 1 out-of-scope-banned (market odds), and records
**5 measured hazards** (0–0 prefill trap, 2019 suspended-game keying, 24 b2b window
ambiguities, Cup-finals asymmetry, era boundaries). The POST_GAME_FACT ban is consistent and
binding in all three lanes (A PIT §1.5/§3; B §2 matrix + §5 binding law; C §0/§1/§8.1).
Injury/lineup NOT_RUN_PIT everywhere. The ROLLING LAW (strictly-prior canonical tip_utc) is
stated in A §0, B as-of laws, C AS-OF LAW + §8.2 same-day property test with an intraday
escalation rule. Observation (not a defect): lane A did not run lane B's W-H2 per-season
roster-coverage census (≥90% team-seasons) — only asset-level census + the 2013 sample — so
the W-H2 hard gate remains honestly PENDING/NOT_RUN under lane B's gate law (slot released
if unmet; nothing advanced W-H2 to a claim).

## Check 4 — Independence law — PASS

All NBA/NFL numbers in the lanes appear only as explicitly-labeled cross-league context
(B §0 "CITED as cross-league context … never imported as proof"; C §0/§5/§6 capacity honesty).
No NBA parameter is adopted as a WNBA value: W-H1 forces its grid to include HCA=0 and to
bracket [0,150]; C's frozen B1 grid {8,16,32}×{0,50,100}×{0.65,0.75,0.85} is explicitly a
bracketing grid ("the data picks"). T1/T2/T3, fold law, date-cluster bootstrap and negative-
first outcomes are inherited as machinery shapes from the NBA terminal cycle; the referenced
machinery file exists (`.worktrees/nba-winprob-scored-v1/integration/lanes/C_protocol/PROTOCOL_EVAL.md`)
and the machinery is fully restated in Lane C's own text — no NBA splits, windows, or
parameters are imported.

## Check 5 — Mechanisms / protocol — PASS

Frozen falsifiers are CI-based (pooled 95% paired date-cluster bootstrap ΔLL CI + half-folds
condition) for W-H1/W-H2/W-H3 and for C's H1-W/H2-W/H3-W with designed-null parents (B0 /
ρ0-parent / W-H1). Negative controls per hypothesis (outcome permutation, continuity
permutation, SOS permutation; C §7 twin law — twins diagnostic, never wins). Banned sources
appear only as ban statements (grep: 538/odds mentions are REJECTS/BANNED rows; no usage).
Arm budget: ceiling **9**, **5 allocated** (B0; B1 fresh WNBA Elo; B-C5 gated; conditional
mechanism-c; fully-pre-specifiable reserve), 4 released — meets "≤9 with B0 + fresh WNBA B1
mandatory". Era 1997–2001 frozen as **rating-stream warm-up only** (C §2.2; forbidden as
training/scoring/feature/sensitivity rows; measured 1,022 rows, all score-populated).
C §11 quotes the plan's GO law verbatim; prospective append-only ledger law present (C §3.5).

## Check 6 — Trial accounting — PASS

Grep over `lanes/` for `sklearn|log_loss|brier_score|.fit(|predict(|train_test_split`:
**zero hits**. Both measurement scripts and my verifier do schema/coverage counting only.
Registry row: `budget {used: 0, max: 0}`; `go_phrase: ""`,
`go_phrase_state: "NOT_REGISTERED …"`; no lane artifact registers or consumes any GO phrase.

## Check 7 — Boundaries — PASS

No S1-access references in lanes (the only "S1" hits are Lane C's unrelated selection-block
labels S1–S4 and the dispatch text itself). No credentials in any lane file. No commits/push
by any lane (`commit_sha: NOT_COMMITTED_CONTROLLER_LANDED` in all three handoffs; before my
writes the tree was clean; after, only `lanes/D_VERIFY/` is untracked). Foreign cycles
nfl-winprob-ng-prep-v1, winprob-ng-prep-v1, nba-winprob-ng-prep-v1 (and terminal
nba-winprob-scored-v1 worktree) present and clean — untouched. Registry row
`WNBA-WINPROB-PREP-V1` coherent: ACTIVE_LIGHT, budget 0/0, worktree/branch match, workers 0,
s1 SEALED_UNTOUCHED; `head` still `673b4f27…` — **expected-pending** the controller's
post-verification update, recorded per instruction, not a defect.

## Defects table

| id | severity | where | statement | measured evidence |
|---|---|---|---|---|
| D-1 | **MAJOR** | lanes/A_DATA spec §2 + `team_key_table.csv` + handoff_A | Canonical team-key table resolves the franchise lineage on the wrong branch: UTA→SAN→**DAL** 2016 "merger", DET/TUL stream terminated 2015, LVA a fresh stream — must be TUL→DAL 2016 and SAN→LVA 2018; internally contradicts its own LVA row ("SAN last season 2017") and the bytes (SAN rows present 2016 AND 2017; SAN+DAL coexist as 2 of 12 teams both seasons) | stats abbr seasons: SAN 2003–2017, DAL 2016–2026, LVA 2018–2026, DET 1998–2009, TUL 2010–2015; 12 distinct teams in 2016 and 2017 incl. SAN and DAL |
| D-2 | MINOR | SPEC §2 / handoff_A | DET/TUL mislabel scope understated as a "2002 file" artifact | Detroit's own ESPN abbr is `TUL` for **all** Detroit rows in every ESPN season 2002–2009 (318 rows, home and away), not just 2002 |
| D-3 | MINOR | SPEC §4 item 3 | Normative alias list omits `WIL`, `STE` | measured alias rows include WIL×3, STE×2 (5 of 21); script + handoff include them |
| D-4 | MINOR | SPEC §4 item 6 | "Cup finals: 7 rows (2021–2026, one per season)" — 6 seasons ⇒ 6 finals; §6 and bytes say 6 | lane A's championship detector double-counts one 2024 neutral-site Cup group game (2024-06-06 WAS–CHI) |
| D-5 | MINOR | PROTOCOL §2.1/§2.3/§8.6 | Stale prior-memo counts in verbatim-inherit sections: 15 neutral rows (measured 16), 14 All-Star rows + incomplete alias set (measured 21 rows / 13-token set; 11 rows would leak: USA×4, WIL×3, STE×2, COL×1, SPO×1) | alias/neutral recomputation above; mitigated by C §12.4 re-verify clause — must be reconciled at successor freeze |

Observations (cosmetic, no action required for this cycle; noted for the freeze): spec §6
ESPN-only rows use home@away order ("CON@NYL" — data has CON home); spec date labels for the
2026 postponed row and 2026 Cup final are UTC dates (ET 2026-07-16 / 2026-08-11) while the
forfeit label "2018-08-03" is an ET date; SPEC §5 "2002–2015 ≈ 220–259/season" excludes the
2002 outlier (271 real) — "≈" summary only, census table authoritative; W-H2 per-season roster
census NOT_RUN (gate honestly pending).

## Reproduction

```
git -C <worktree> rev-parse HEAD           # 18fa135b69fb75b346f0e8a0298d624bc1879598
/Users/hoangminhlong/my-quantitative/.venv/bin/python lanes/D_VERIFY/verify_d.py   # read-only recompute
shasum -a 256 <corpus/new files>           # vs raw/audit_results.json + extensions/sha256_extensions.txt
grep -rniE "sklearn|log_loss|\.fit\(|predict\(" lanes/          # 0 hits
grep -rnE "requests\.|urllib|stats\.wnba\.com" lanes/*/*.py     # 0 hits
```
