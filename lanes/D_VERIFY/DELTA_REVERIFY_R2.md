# DELTA RE-VERIFICATION R2 — Lane D · INDEPENDENT VERIFIER (wbap-d-verify-r2)

- Cycle `WNBA-WINPROB-PREP-V1` · role quant-auditor (fresh context, post-fix pass over
  lane C r1 counts fix + lane A r2 roster PIT audit) · 2026-10-05
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration`,
  branch `orca/wnba-winprob-prep-v1-integration`, HEAD measured
  `b53af240e8b2124c3b976fd97e7f1e5dcc9681ec` (= dispatch_sha = actual_start_sha). No commits,
  no repairs; write scope `lanes/D_VERIFY/**` only.
- Method: every load-bearing number below re-measured from bytes by an independent
  implementation written for this pass (`lanes/D_VERIFY/delta_reverify_r2.py`, run with
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`; read-only over
  `~/.my-quantitative-data/wnba-v1/raw/` and `~/.my-quantitative-data/wnba-prep-v1/`). Neither
  lane A's `measure_r2_roster.py` / `measure_r2_download.py` nor any prior lane-D script was
  executed (they rewrite outputs); lane A's script source was read only to identify probe-key
  definitions, then re-implemented from scratch. Schema/coverage counting only — no win-prob
  metric computed anywhere, per plan law. 37/37 machine checks PASS
  (`lanes/D_VERIFY/reverify_r2_results.json`).

## VERDICT: VERIFICATION_PASS

Both fixes verify from bytes: the lane-C counts fix is byte-surgical and carries exactly the
re-measured values (21 alias rows / 13 tokens / 16 neutral; zero stale strings), and the lane-A
roster PIT audit reproduces in full — all seven dispatch legs re-measure clean, so
**PIT_PASS_BY_CONSTRUCTION (minutes-weighted continuity T ≥ 2006; roster-share continuity
T ≥ 2003) follows from the measured evidence** and the W-H2 KEEP recommendation stands.
Open defects: **0 BLOCKER, 0 CRITICAL, 0 MAJOR, 4 MINOR** (D-6…D-9) — all are supporting-text
inaccuracies in `ROSTER_PIT_AUDIT_WNBA.md` / `handoff_A_r2.json` that contradict the audit's own
machine output or the bytes; none moves the PIT verdict, the eligibility windows, the W-H2
KEEP, or any corrected count.

---

## Check 1 — Counts fix (lane C r1) — PASS

Re-measured from ESPN schedule bytes 2002–2026 (independent implementation):

- All-Star/exhibition alias rows: **21** (one per ASG season; 21 distinct seasons
  2002–2026, absent exactly in Olympic years 2008/2012/2016/2020; every row headline empty or
  `*star*`-tagged). **13 tokens**, per-token home+away slots exactly:
  EAST 11, WEST 11, USA 4, WIL 3, ALL 3, STE 2, DEL 2, PAR 1, COL 1, CLA 1, SPO 1, COOP 1,
  WNBASTARS 1. Stats side (1997–2026, 7,009 rows): **0** alias rows ✓.
- Neutral-site rows: **16** = 10 alias + **6 real** (2016-07-22 DAL@ATL; 2016-09-28 CHI@LAS;
  2021-08-12 CON@SEA; 2024-06-06 CHI@WAS; 2025-08-15 SEA@ATL; 2026-08-11 PHX@LA ET) ✓.
  (Note: the 2026 schedule file writes booleans lowercase — the 16th row is only found with a
  case-insensitive flag read; measurement now handles both.)
- Cup: **301** rows, all `season_type=2`, 2021–2026 (61/61/61/31/37/50); finals **6**
  (5 "Championship"-headline + the single neutral 2021 Cup row) ✓.
- Protocol draft (`PROTOCOL_DRAFT_WNBA.md`): exactly **5** `ERRATUM_COUNTS_R1` pointer sites;
  grep **0 hits** for `14 All-Star`, `15 rows`, and the stale 8-token string
  `EAST/WEST/ALL/DEL/PAR/CLA/COOP/WNBASTARS`; corrected values present at §2.1 (13 tokens /
  21 rows / stats side 0), §2.3 + §8 test 4 (16 rows), §8 test 6 (13 tokens + 21 rows with the
  measured per-token breakdown incl. WIL×3/STE×2), §12 item 4 (corrected reference values
  inline) ✓.
- Diff discipline: `git diff 6681486d..b53af240` on the draft = 24 insertions / 8 deletions,
  every hunk at the 5 declared count sites, each carrying its pointer note; no section
  rewritten ✓.

**Counts fix verified.**

## Check 2 — Roster PIT audit (lane A r2) — PASS on all legs (a)–(g)

All re-measured from the 50 downloaded assets + ESPN schedules (universe = lane A filter law,
recomputed: 5,988):

- **(a) Coverage**: universe games with roster rows **5,983/5,988**; the **5 missing** are
  exactly `220608015` (2002-06-08 CHA@UTA), `260523019` + `260526019` (2006 CHI, expansion
  week), `280523020` (2008-05-23 DET@ATL), `400910457` (2016-09-28 CHI@LAS playoff G1);
  **none is any team's season game-1** (checked against every franchise's first filter-law game
  by tip). Game-1 roster presence = **318/318 team-seasons (100%)** ✓.
- **(b) Duplicates**: **0** `(game_id, team_id, athlete_id)` duplicate rows across all 25
  seasons ✓.
- **(c) Game-linkage**: 0 empty/malformed `game_id` in 137,587 roster rows; **6,004 distinct
  roster game_ids all resolve** in the full ESPN schedule (6,029 ids); the **21** roster games
  outside the filter-law universe are the ASG games + the 2018 forfeit `401018942` — present in
  the schedule, removable only by the filter law, exactly as the audit's trap note states ✓.
- **(d) Minutes-side coverage / computable-continuity**: box 2002 = stub (344 rows, **16/271**
  games, `minutes` 100% `--`); missing box games by season: 2003: 61, 2004: 23, 2005: 9,
  2006–2008: 2/2/7, **2010: 1, 2012: 2, 2016: 2** (see D-7), 0 elsewhere. Expansion set
  independently derived (franchise with no universe games in T−1) =
  {CHI 2006, ATL 2008, GSV 2025, POR_PDX 2026, TOR 2026} — matches the audit's denominators.
  **Computable-continuity fraction (minutes-weighted, ≥0.8 prior-box), re-derived for
  T = 2003…2026: 0% (0/14), 38.5% (5/13), 92.3% (12/13), then 100% for every season
  T = 2006…2026** — identical to the audit's table; roster gate 100% in all 23 seasons
  2003–2025 (B-lane ≥~90% gate PASS) ✓.
- **(e) Retro-fill**: with the audit's probe key (roster rows whose **(franchise, athlete)** has
  no same-season box row; box 2002 mapped via ESPN abbreviations): **2002: 1,061 (412 starter)
  — fully explained by the stub; 2003: 10 (4); 2004: 1; 2005: 9; 2006–2026: 0** — exact ✓.
  My stricter game-level cross-probe (roster rows with no same-GAME box row) is nonzero only
  pre-2012 (2002: 5,615; 2003: 1,326; 2004: 500; 2005: 209; scattered ≤155 later) — consistent
  with the audit's own box-schema note that box files carry no DNP players before 2012, i.e. a
  source-coverage asymmetry, not retro-addition (retro-addition would show roster rows for
  games that never happened; none exist).
- **(f) 2025 starter cross-check** (universe games; the raw 2025 files hold 312 games /
  7,140 rows incl. the ASG — see D-8): **311/311 games; 622/622 team-games derive exactly 5v5
  with IDENTICAL starter-name(id)-sets; 7,115/7,115 row-level `starter` flags agree,
  0 disagreements** ✓.
- **(g) As-of law text** (audit §8): all binding clauses present verbatim — inputs bound to
  season-(T−1) game facts, knowability "by construction", "Season-T roster rows are NEVER
  inputs to T's own predictions", game-day `starter/did_not_play/active/ejected/reason`
  "forbidden as pre-game features" in any season, eligibility window T ≥ 2006 (minutes) /
  T = 2003 (roster-share), mandatory filter-law inner join, `team_display_name` joins ✓.

**Adjudication: PIT_PASS_BY_CONSTRUCTION follows.** Every consumed input is a post-game fact of
a strictly prior season; linkage is total and dated on the schedule side; coverage is sufficient
inside the stated windows; no retro-addition exists from 2006 onward. The two measured
input-availability gaps (2002 stub; 2003–2008 partial box) shrink the window exactly as the
audit's law cl. 4 freezes. W-H2 KEEP stands.

## Check 3 — Independence law — PASS

Grep `\bnba\b` over `lanes/`: the two new lane-A artifacts contain only ban statements
(`ROSTER_PIT_AUDIT_WNBA.md` §0/§9 "no NBA number, parameter or verdict entered any claim";
`measure_r2_roster.py` docstring "no NBA input anywhere"). All 11 protocol-draft hits are the
byte-unchanged FRESH-PROGRAM/context/machinery passages (R0-adjudicated); the only count-fix
line touching "NBA" (§2.3) keeps the pre-existing "better than the NBA [flag]" context clause.
Every number in the roster audit is measured from the two WNBA release tags + the WNBA corpus;
the B-lane "≥~90% of team-seasons 2003+" gate is a WNBA lane law. No WNBA constant is sourced
to NBA data ✓.

## Check 4 — No-regression — PASS

- **Census anchors re-measured**: ESPN 6,029 rows / 6,029 unique ids / 25 seasons; stats
  7,009 / 7,009 / 30 seasons; stats id shape (`10`+type-digit+YY+5seq, `2`↔regular-season,
  `4`↔playoffs crosstab perfect); ESPN real **5,988 = 5,230 RS-excl-Cup + 301 Cup + 457 PO**;
  stats real **7,008 = 6,493 + 515**; pre-2002 real 1,022; **union 7,017** by my independent
  two-pass join (matched 5,979; ESPN-only **9** = exactly `270620018`/`290709009`/`400182104` +
  the 6 Cup finals `401353913/401430112/401507376/401677672/401736430/401857321`; stats-only
  **1,029**; 0 matches at ET offset ±1 in the window pass — split vs lane A's 5,954+25 is the
  R1-noted order/orientation bookkeeping, totals identical).
- **Filter law**: non-`post` **17** (all 2026, 0–0 prefill, 0 null scores); forfeit **1**
  (`401018942`); postponed **2** (`401507167`, `401857072`); TBD **7**; alias **21**; stats 0–0
  twin **1** (`1021800162`, blank wl); post-state 0–0 rows are exactly those 3
  forfeit/postponed rows ✓.
- **Timestamp laws**: ESPN `date == game_date_time` **6,029/6,029** and `date == start_date`
  **6,029/6,029**; spot `401857072` same-instant ✓.
- **20-key lineage table**: 20 rows; `SAN_DAL`/`DET_TUL` absent from every column; LVA =
  {Las Vegas Aces, San Antonio Silver Stars, San Antonio Stars, Utah Starzz} 1997–2026;
  DAL = {Dallas Wings, Detroit Shock, Tulsa Shock} 1998–2026 ✓.
- **Diff scope**: `git diff --name-status 6681486d..b53af240` touches exactly 7 files —
  `lanes/A_DATA/{ROSTER_PIT_AUDIT_WNBA.md, handoff_A_r2.json, measure_r2_download.py,
  measure_r2_roster.py}` (all Added), `lanes/C_PROTOCOL/{ERRATUM_COUNTS_R1.md,
  handoff_C_r1.json}` (Added) + `PROTOCOL_DRAFT_WNBA.md` (Modified, surgical) — no
  `event_log.jsonl` in the committed range (the controller's `REMEDIATION_R2_LANDED` /
  `PREP_SYNTHESIS_COMPLETE` bookkeeping is working-tree only; tail read, landing records only).
  **`lanes/B_MECHANISMS/**` zero diff bytes** back to `18fa135b` ✓. No existing lane-A file
  modified by r2 ✓.
- **Corpus integrity**: 4/4 spot sha256+byte re-hashes match `raw/audit_results.json`
  (99 entries, `digest_mismatches: []`), incl. the lineage-decision files
  (`espn_schedules/wnba_schedule_2016.csv`, `wnba_schedule_2020.csv`,
  `wnba_stats_schedules/wnba_schedule_2017.csv.gz`, `espn_sample_2025/player_box_2025.csv`) ✓.

## Check 5 — Download integrity — PASS

Re-hashed **8 of 50** `roster_audit` files vs `download_manifest_r2.json`
(`game_rosters_2002/2013/2022/2026`, `player_box_2002/2016/2023/2025`): bytes and sha256 exact
**8/8**; 6 carry matching GitHub API digests, 2 (`player_box_2002/2023`) are the recorded
pre-digest assets (API `digest: null`) size-verified against API metadata — exactly as the
manifest and audit §2 state. Manifest total **86,572,091 bytes = claim** ✓. Downloader hits
public `github.com/sportsdataverse/sportsdataverse-data` release URLs with a User-Agent header
only — no auth, no account, $0; `measure_r2_roster.py` contains zero network code; no
wnba.com / stats.wnba.com / ESPN / Sports Reference access anywhere in the lane ✓.

## Check 6 — Accounting — PASS

- Grep `sklearn|log_loss|brier|train_test_split|.fit(|predict(` over `lanes/`: only metric
  *definitions* in the protocol's future-eval prose and verifier ban statements — no computation
  code in any lane script (both new lane-A scripts are pandas counting + a downloader) ✓.
- Registry row `WNBA-WINPROB-PREP-V1` (read-only): ACTIVE_LIGHT, phase REGISTERED, worktree +
  branch match this worktree, `budget {used: 0, max: 0}`, `go_phrase: ""`,
  `go_phrase_state: "NOT_REGISTERED (P-8…)"` (no lane artifact registers or consumes a GO), s1
  `SEALED_UNTOUCHED`, workers 0; `updated_at_utc` 03:26Z predates today's lane runs (06:32–08:22Z)
  — lanes never wrote it. `head` = `0000…0000` placeholder — **expected-pending** the
  controller's next landing (same recorded state as R1; the measured branch HEAD remains
  `b53af240…`), not a defect.
- No credentials in any lane file (grep 0 hits beyond the R1 report's own ban statement); no S1
  access references (only lane C's unrelated selection-block labels S1–S4 and dispatch prose);
  tree clean except `research/control/.../event_log.jsonl` (controller, uncommitted) and this
  lane's `lanes/D_VERIFY/` outputs ✓.

## Defects table

| id | severity | where | statement | measured evidence |
|---|---|---|---|---|
| D-6 | MINOR | `ROSTER_PIT_AUDIT_WNBA.md` §5 (+ machine field `game1_rows_min`) | "100% of team-seasons 2002–2026 have a game-1 roster with ≥10 rows … Minimum game-1 rows per game across all seasons: 10" is false per-team, and the machine field does not measure the claim as written: `game1_rows_min` counts **starters per game-1 GAME (both teams combined)**, not rows per team | 5/318 team-seasons have <10 game-1 roster rows: 2005 LAS **8** (`250521014`), 2022 CON **9** (`401391654`), 2022 WAS **9** (`401391650`), 2025 GSV **9** (`401736114`), 2026 CHI **9** (`401856895`); all have ≥1 row (presence gate unaffected) |
| D-7 | MINOR | `ROSTER_PIT_AUDIT_WNBA.md` §6 table + §6 sentence | "2009–2025 | complete (0 missing)" and "Every team at full 1.0 box coverage is guaranteed from T = 2010" contradict the audit's own `measurements_r2.json` and the bytes | universe games missing box rows: 2010: **1**, 2012: **2**, 2016: **2** (machine `universe_games_missing_box` identical); machine `prior_box_ratio_min` = **0.9706** at T = 2011/2013/2017 (<1.0). All ratios ≥ 0.94 ≥ 0.8 → binding ≥0.8 law and T ≥ 2006 window unaffected |
| D-8 | MINOR | `ROSTER_PIT_AUDIT_WNBA.md` §3 | "the 2025 file alone has 311 distinct game keys with 23 median rows each" — the raw file has **312** keys / **7,140** rows (includes the 2025-07-19 ASG, 25 rows); 311 / 7,115 is the universe-joined count (§4 table is consistent with the joined view; §3's own trap note says ASG rows live in the raw files) | raw `game_rosters_2025.csv` = 312 distinct game_ids / 7,140 rows; ASG game `401781604` present with 25 rows; universe-joined = 311 / 7,115 ✓ |
| D-9 | MINOR | `handoff_A_r2.json` authority_claims[2] | "(…, 5,963/5,984 covered games)" — the pair mislabels two real quantities: covered = **5,983** (machine + bytes); 5,963 = covered games with exactly 10 starters (5,983 − 20 starter-flag anomaly games; the "99.6%" next to it reproduces: 5,963/5,983 = 99.7%) | no measured quantity equals 5,984; covered = 5,983; exactly-10-starter covered = 5,963 |

None of D-6…D-9 changes: the PIT verdict (by-construction argument is untouched — presence,
not row-count, is the gate), the eligibility windows (T ≥ 2006 minutes / T ≥ 2003 roster-share),
the W-H2 KEEP recommendation, or any corrected count from Check 1. Remedy for all four is
text-only in lane A artifacts (successor carries the 5 truncated game-1 rosters and the 5
2010–2016 box-missing games as structural missingness per the audit's own §8 cl. 5 policy).

## Reproduction

```
git -C <worktree> rev-parse HEAD        # b53af240e8b2124c3b976fd97e7f1e5dcc9681ec
git -C <worktree> diff --name-status 6681486d356d04690873f25badf05500ed22f430..b53af240e8b2124c3b976fd97e7f1e5dcc9681ec
/Users/hoangminhlong/my-quantitative/.venv/bin/python lanes/D_VERIFY/delta_reverify_r2.py
        # 37/37 checks; read-only; writes only lanes/D_VERIFY/reverify_r2_results.json
grep -n "14 All-Star\|15 rows" lanes/C_PROTOCOL/PROTOCOL_DRAFT_WNBA.md      # 0 hits
grep -c "ERRATUM_COUNTS_R1" lanes/C_PROTOCOL/PROTOCOL_DRAFT_WNBA.md         # 5
shasum -a 256 ~/.my-quantitative-data/wnba-prep-v1/roster_audit/<file>      # vs download_manifest_r2.json
```
