# DELTA RE-VERIFICATION R1 — Lane D · INDEPENDENT VERIFIER (wbap-d-verify-r1)

- Cycle `WNBA-WINPROB-PREP-V1` · role quant-auditor (fresh context, delta pass over
  `lanes/D_VERIFY/VERIFICATION_REPORT.md` verdict VERIFICATION_FAIL) · 2026-10-05
- Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/wnba-winprob-prep-v1/integration`,
  branch `orca/wnba-winprob-prep-v1-integration`, HEAD measured
  `f3098d95e72deb809c072f2b83cf08e20d13020e` (= dispatch_sha = actual_start_sha). No commits,
  no repairs; write scope `lanes/D_VERIFY/**` only.
- Scope: confirm each R0 finding (D-1 MAJOR + D-2/D-3/D-4 MINOR, plus the D-5 record-keeping
  requirement) is remediated correctly **from data**, and that nothing else regressed. The R0
  cosmetic observations are NOT re-adjudicated (R0 marked them no-action).
- Method: re-measured from corpus bytes by an independent implementation written for this pass
  (`lanes/D_VERIFY/delta_verify_r1.py`, run with
  `/Users/hoangminhlong/my-quantitative/.venv/bin/python`; read-only over
  `~/.my-quantitative-data/wnba-v1/raw/` and `~/.my-quantitative-data/wnba-prep-v1/`).
  Neither lane A's `measure_a2.py` nor the R0 `verify_d.py` was executed (both rewrite their
  outputs). Schema/coverage counting only — no win-prob metric computed anywhere, per plan law.

## VERDICT: VERIFICATION_PASS

All five delta checks PASS. The remediation (task `wbap-a-data-r1`, erratum
`lanes/A_DATA/ERRATUM_TEAM_KEY_R1.md`) rebranches the canonical lineage exactly as the data
dictates, closes the three MINORs with measured values, moves only the numbers it declares,
and leaves every other law reproducing byte-for-byte. Defects remaining: **0 MAJOR, 0 MINOR,
0 BLOCKER, 0 CRITICAL** open on lane A/D artifacts. The lane C stale-count reconciliation
(former D-5) remains **open by design** as a recorded known limitation for the successor
(see Check 5) — that is the remediation instruction's intended state, not a new defect.

---

## Check 1 — D-1 (MAJOR): lineage rebranch — PASS

Re-measured season presence and row counts from stats schedule bytes (home/away slots,
per season; `delta_verify_r1.py` block `d1_stats_abbr`):

| abbr | seasons | rows/season | total |
|---|---|---|---|
| UTA | 1997–2002 (6) | 28, 30, 32, 32, 34, 37 | **193** |
| SAN | 2003–2017 (15) | 34, 34, 34, 34, 39, 43, 37, 36, 37, 36, 34, 36, 34, **34, 34** | **536** |
| LVA | 2018–2026 (9) | 34, 39, 30, 37, 46, 49, 46, 56, 47 | **384** |
| DET | 1998–2009 (12) | 30, 33, 32, 32, 32, 42, 37, 36, 44, 45, 43, 39 | **445** |
| TUL | 2010–2015 (6) | 34, 34, 34, 34, 34, 36 | **206** |
| DAL | 2016–2026 (11) | 34, 35, 35, 34, 22, 33, 39, 45, 40, 44, 47 | **408** |
| LAS | 1997–2026 (30, **continuous**) | (30 entries) | **1,111** |

- SAN display-name eras from bytes: San Antonio Silver Stars 2003–2013 (11 seasons) + San
  Antonio Stars 2014–2017 (4 seasons); union exactly 2003–2017, contiguous ✓.
- Coexistence that kills the merger story (block `d1_coexistence`): 12 distinct stats abbrs in
  each of 2015/2016/2017/2018; **SAN present AND DAL present in BOTH 2016 (SAN 34 / DAL 34)
  and 2017 (SAN 34 / DAL 35)**; TUL absent from 2016–2018, LVA absent before 2018 ✓.
- Boundaries: TUL last season 2015 → DAL first 2016; SAN last 2017 → LVA first 2018;
  UTA last 2002 → SAN first 2003; DET first 1998 ✓ — the R0 refutation of "SAN→DAL merger"
  reproduces exactly, and the corrected branch (TUL→DAL 2016, SAN→LVA 2018) is the only one
  the bytes support.
- Corrected encoding verified in `~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv`
  (parsed, not trusted by layout): **20 franchise keys** (was 21); `LVA` row carries stats
  abbrs {LVA, SAN, UTA}, seasons 1997–2026, modern key first; `DAL` row carries {DAL, DET,
  TUL}, seasons 1998–2026; `LAS` row {LAS}, 1997–2026; tokens `SAN_DAL`/`DET_TUL` appear
  **nowhere** in the file (any column) ✓. Table spans cross-checked against measured bytes
  (`d1_table_vs_bytes` all true). sha256 `20201042…58f3cd9`, 1,473 B.
- Spec §2 (`GAME_UNIVERSE_SPEC_WNBA_1997PLUS.md`): `SAN_DAL` absent, `DET_TUL` absent, the
  "merger season"/"2003–2015" wording absent from §2; corrected lines present verbatim
  ("UTA Utah Starzz 1997–2002 → SAN … → LVA Las Vegas Aces 2018–", "DET Detroit Shock
  1998–2009 → TUL Tulsa Shock 2010–2015 → DAL Dallas Wings 2016–"), LAS stated continuous /
  never relocates, "20 franchise keys" stated, and the SAN+DAL 2016+2017 coexistence evidence
  (SAN 34/34, DAL 34/35) embedded in the LVA row ✓. ERRATUM R1 pointer present at §2 head.
- `measurements_a2.json` consistent: `team_key_table_rows = 20`; keys `SAN_DAL`/`DET_TUL`
  absent; LVA eras [1997, 2026], DAL eras [1998, 2026].

**D-1 remediated correctly.**

## Check 2 — MINORs (D-2, D-3, D-4) — PASS

- **D-2 (DET/TUL mislabel span)**: ESPN rows with display name "Detroit Shock" = **318**,
  seasons exactly 2002–2009, per season 32/42/37/36/44/45/43/39; **every row** carries `TUL`
  in the Detroit slot (home 161 + away 157 = 318; 0 exceptions); abbreviation `DET` appears
  **0 times** anywhere on ESPN (any season, either slot). Stats `DET` per-season counts equal
  the ESPN Detroit per-season counts exactly (same games, mislabeled key) ✓. Spec §2 "Never
  join" paragraph now states the 2002–2009/318-row/0-times scope; erratum §2c matches bytes.
- **D-3 (alias breakdown)**: **21** ESPN alias rows, **13** distinct tokens, per-token
  (home+away slots): EAST 11, WEST 11, USA 4, **WIL 3** (seasons 2019/2022/2023), ALL 3,
  **STE 2** (2022/2023), DEL 2, PAR 1, COL 1, CLA 1, SPO 1, COOP 1, WNBASTARS 1; stats side
  **0** ✓. Spec §4 item 3 now carries this measured per-token breakdown (incl. WIL×3, STE×2).
- **D-4 (Cup finals)**: Cup rows **301**, all `season_type=2`, 2021–2026 (61/61/61/31/37/50).
  Finals measured **6** = 5 rows with headline "WNBA Commissioner's Cup Championship" +
  the single 2021 neutral-site Cup row (headline plain "WNBA Commissioner's Cup") — exactly
  one per Cup season, and **each is the last-scheduled Cup game of its season**:
  2021 SEA vs CON (neutral, ET 2021-08-12), 2022 CHI vs LVA (ET 2022-07-26), 2023 LVA vs NYL
  (ET 2023-08-15), 2024 NYL vs MIN (ET 2024-06-25), 2025 MIN vs IND (ET 2025-07-01),
  2026 NYL vs LVA (ET 2026-06-30) — identical to erratum §4d (home/away/ET dates) ✓. The
  double-counted game is confirmed a group game: `401620271` WAS–CHI 2024-06-06T23:00Z,
  neutral, Cup headline, never "Championship". `measurements_a2.json` consistent:
  `rows_championship = 6` (was 7), `championship_by_season` = 1 for each of 2021–2026 (2024
  was 2), `championship_neutral_site_rows = 1` (was 2). The fixed detector in
  `measure_a2.py` (headline "Cup Championship" ∪ the 2021 neutral Cup row) reproduces my
  independent 6 exactly.

**All three MINORs remediated correctly.**

## Check 3 — NO-REGRESSION — PASS (all laws reproduce byte-for-byte)

Recomputed independently (blocks `ng_*`):

- **Identity**: ESPN 6,029 rows / 6,029 unique `game_id` / 25 seasons; stats 7,009 / 7,009 /
  30 seasons ✓ (unchanged).
- **Filter law**: non-`post` rows **17** (all 2026, all pre-filled 0–0, 0 null scores);
  forfeit **1** (`401018942`); postponed **2** (`401507167`, `401857072`); alias rows **21**;
  TBD **7**; neutral **16**; stats 0–0 rows **1** (`1021800162`, the forfeit twin); stats
  null-pts rows **0** ✓ (unchanged).
- **Census**: ESPN real **5,988 = 5,230** RS-excl-Cup + **301** Cup + **457** PO (sum checked);
  stats real **7,008 = 6,493** RS + **515** PO (sum checked); pre-2002 real **1,022** ✓
  (unchanged). **Union 7,017 = 5,988 + 1,029** ✓.
- **Timestamps**: ESPN `date == game_date_time` **6,029/6,029** and `date == start_date`
  **6,029/6,029** (per-file ISO8601-UTC parse) ✓; `measurements_a2.json`
  `ts_espn_schedule_instant_equality_fixed` = 6,029/6,029 (100.0%) on disk, consistent.
- **Row-level join**: my independent two-pass join totals — matched **5,979**, ESPN-only
  **9** (3 regular + 6 Cup finals), stats-only **1,029** (1,022 pre-2002 + 7 in-2002+),
  union **7,017** — identical to lane A's on-disk `recon_rowlevel`
  (5,988 / 5,979 = 5,954 window + 25 score / 9 / 7,008 / 1,029) and to R0. Residual
  identities match: lane A's 9 ESPN-only rows are the same 3 regular ids (`270620018`,
  `290709009`, `400182104`) + the same 6 final ids I independently enumerated; the stats-only
  extras by season {2002: 2, 2003: 2, 2004: 3} lead with the same ids (`1040200103`,
  `1040200133`, `1020300043`, `1020300141`, …) as R0's list. The ET-date law reproduces: in
  lane A's on-disk offset distribution {0: 5954, score: 25, −1: 0, +1: 0}, and in my
  independent pass **0 matches at ±1** — all window matches at ET offset 0.
  *Methodology note (not a defect)*: my implementation keys the name pair order-insensitively,
  which aliases flip-flop home-and-home back-to-backs into pass-1 ambiguity, resolved by
  exact score in pass 2 (my split: 5,918 window + 61 score vs lane A's 5,954 + 25). Same
  final pairing, same totals, same offset law, same residual identities — the
  window/score classification split is order/orientation-dependent bookkeeping, not a data
  difference.
- **`measurements_a2.json` global consistency**: top-level blocks beyond the three the erratum
  declares moved are consistent with my recomputation — identity, filter law, census
  (`season_type_totals.stats_played` 6,493+515; `model_universe` 5,988/7,008/1,029/9/7,017),
  join (5,954+25/9/1,029), timestamp laws — i.e., the regeneration moved ONLY
  `team_key_table`, `team_key_table_rows`, and `espn_commissioners_cup`, as claimed.

## Check 4 — Scope discipline — PASS

- `git diff --name-status 18fa135b69fb75b346f0e8a0298d624bc1879598..f3098d95…` touches
  exactly: `lanes/A_DATA/ERRATUM_TEAM_KEY_R1.md` (A), `lanes/A_DATA/GAME_UNIVERSE_SPEC_WNBA_1997PLUS.md`
  (M), `lanes/A_DATA/handoff_A_r1.json` (A), `lanes/A_DATA/measure_a2.py` (M);
  `lanes/D_VERIFY/{VERIFICATION_REPORT.md, handoff_D.json, verify_d.py}` (A — the controller's
  448710a6 landing of my predecessor's R0 outputs, preceding the remediation);
  `research/control/WNBA-WINPROB-PREP-V1/event_log.jsonl` (M — controller's own
  `D_VERIFY_LANDED` + `REMEDIATION_R1_LANDED` bookkeeping events; read and confirmed to
  contain no lane-authored content beyond landing records).
- **`lanes/B_MECHANISMS/**` and `lanes/C_PROTOCOL/**`: zero diff bytes** in the range
  (`git diff --stat` over both paths empty) — byte-unchanged since the original verification ✓.
- `research/control/**`: only the event_log line; no other control file touched ✓.
- `handoff_A.json` and `measure_a.py` untouched (historical record retained, as the erratum
  states) ✓.
- **No credentials**: grep over `lanes/` for key/secret/password/token/private-key patterns →
  0 hits ✓. **0 scored outcomes still true**: grep for
  `sklearn|log_loss|brier_score|train_test_split|.fit(|predict(` over `lanes/` → only ban
  statements and verifier/dispatch prose, no computation code; registry row budget
  `{used: 0, max: 0}`, `go_phrase_state: "NOT_REGISTERED (P-8…)"` ✓.
- Corpus untouched: 8/8 spot sha256+byte checks match `raw/audit_results.json` (99 entries,
  `digest_mismatches: []`), including the lineage-decision files (ESPN 2016/2017/2026,
  stats 2017/2018 gz, `espn_sample_2025/player_box_2025.csv`, plus R0's 2020/1997 checks) ✓.
  Heavy lock `FREE_PROVEN`. Tree clean (only the three new intended `lanes/D_VERIFY/` files
  untracked). Registry row `WNBA-WINPROB-PREP-V1` ACTIVE_LIGHT, worktree/branch match,
  workers 0, s1 SEALED_UNTOUCHED.
- Observation (controller-owned, not a lane defect, recorded): registry `head` field is
  currently the all-zeros placeholder `0000…0000` (at R0 it was the stale-but-nonzero
  `673b4f27…`, itself recorded expected-pending). The measured branch HEAD remains
  `f3098d95e72deb809c072f2b83cf08e20d13020e`. The controller normalizes this field at its
  next landing; lanes never write the registry.

## Check 5 — Lane C stale-count reconciliation (former D-5) remains a recorded known limitation — PASS

- `lanes/A_DATA/ERRATUM_TEAM_KEY_R1.md` §5 "Lane C (D-5) — deliberately untouched" states the
  stale prior-memo counts (15 neutral vs measured 16; 14 All-Star rows / incomplete alias set
  vs measured 21 rows / 13-token set; the 11-row leak list USA×4/WIL×3/STE×2/COL×1/SPO×1)
  and routes the fix to the successor at the B1 freeze.
- `lanes/A_DATA/handoff_A_r1.json` `known_limitations[0]` carries the same content verbatim
  with the lane C §12.4 pointer ✓.
- The hook is real and intact: `lanes/C_PROTOCOL/PROTOCOL_DRAFT_WNBA.md` §12 item 4 ("The
  successor must re-verify (not assume): season completeness, the 1-forfeit count, alias row
  counts, neutral-site row count, and Cup-flag completeness") is present and byte-unchanged ✓.
- The stale lane C prose was NOT silently dropped and NOT silently "fixed" — it is explicitly
  inherited-with-caveat, exactly what the remediation instruction required.

## Defects table

None open on lanes A/D artifacts. (Former D-1..D-4: CLOSED, verified above. Former D-5:
OPEN-BY-DESIGN as a successor-known-limitation, properly recorded in erratum §5 +
handoff_A_r1 known_limitations + lane C §12.4 — per remediation instruction, not a defect of
the remediation.)

## Reproduction

```
git -C <worktree> rev-parse HEAD        # f3098d95e72deb809c072f2b83cf08e20d13020e
git -C <worktree> diff --name-status 18fa135b69fb75b346f0e8a0298d624bc1879598..f3098d95e72deb809c072f2b83cf08e20d13020e
/Users/hoangminhlong/my-quantitative/.venv/bin/python lanes/D_VERIFY/delta_verify_r1.py   # read-only recompute
shasum -a 256 ~/.my-quantitative-data/wnba-prep-v1/team_key_table.csv    # 20201042…58f3cd9, 1473 B
shasum -a 256 ~/.my-quantitative-data/wnba-prep-v1/measurements_a2.json  # 1efdd337…71652a1, 39548 B
grep -rniE "sklearn|log_loss|\.fit\(|predict\(" lanes/                   # ban statements only
```
