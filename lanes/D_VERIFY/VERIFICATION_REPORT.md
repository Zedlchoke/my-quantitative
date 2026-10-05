# VERIFICATION_REPORT — Lane D, WINPROB-NG-PREP-V1 (independent verifier)

- lane: D_VERIFY · task: wng-d-verify · measured: 2026-10-05 · owner round 2026-10-05
- Verifier is fresh; everything below was re-measured from bytes/commands this session, not
  taken from lane prose. Read-only git; no repairs; write scope = this directory only.
- Worktree HEAD measured: `0513a0f612e0f739f41229bb86b2084b5dff6d2e`
  (branch `orca/winprob-ng-prep-v1-integration`; lanes/ untracked, tree otherwise clean).

## Per-check results

| # | Check | Verdict | Evidence (measured this session) |
|---|---|---|---|
| 1 | Repo/control plane | **PASS** | See 1.1–1.4 below. |
| 2 | T1 closeout | **PASS** | See 2.1–2.4 below. |
| 3 | Lane A downloads | **PASS** | See 3.1–3.5 below. |
| 4 | Lane B downloads | **PASS** | See 4.1–4.4 below. |
| 5 | Lane C mechanisms | **PASS** | See 5.1–5.4 below. |
| 6 | Boundaries | **PASS** | See 6.1–6.4 below. |

## 1. Repo / control plane — PASS

1.1 Root `/Users/hoangminhlong/my-quantitative` on `main`. First measurement this session:
HEAD `576ddb3e` = "WINPROB-NG-PREP-V1 G0 bootstrap + T1 closeout …" — the cycle's G0
control-plane commit. DISCLOSED CONCURRENCY: during verification main advanced one commit to
`40917736` ("FUTURES-ES-PB1-V1 registry reconcile … pre-GO repair wave"), a *different*
cycle's registry reconcile touching only `plans/` files (see 6.4). "576ddb3e or later"
remains satisfied; 576ddb3e is `40917736`'s parent.

1.2 Registry rows (read from `/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json`,
schema `cycle_registry@1`), exact strings:

- NBA-WINPROB-SCORED-V1: `lifecycle = "TERMINAL"`;
  `go_phrase_state = "DEAD (consumed or extinguished at its cycle's close per P-8 / RULES §7)"`.
- NFL-WINPROB-SCORED-V1: `lifecycle = "TERMINAL"`;
  `go_phrase_state = "DEAD (consumed or extinguished at its cycle's close per P-8 / RULES §7)"`.
- WINPROB-NG-PREP-V1: `lifecycle = "ACTIVE_LIGHT"`, `budget = {"used": 0, "max": 0}`
  (0/0), `go_phrase_state = "NOT_REGISTERED (P-8: a GO is typed only at the cycle's own gate)"`,
  head = `0513a0f6…` (this worktree's HEAD), branch = `orca/winprob-ng-prep-v1-integration`.

1.3 Terminal artifacts untouched. NBA worktree
`.worktrees/nba-winprob-scored-v1/integration` HEAD `485de0c2` (= registry head, "A7 TERMINAL:
CONFIRM …"); `git log -1` on `research/control/NBA-WINPROB-SCORED-V1/TRIAL_LEDGER.jsonl` and
`.../results/scored_summary.json` → both last touched at `a1708045` ("SCORED EXECUTION
COMPLETE … 9/9 arms … PROGRAM_PASS=false"). NFL worktree HEAD `36c1e6f6` (= registry head);
both paths last touched at `2c6a22d6` ("SCORED EXECUTION COMPLETE … INCONCLUSIVE=TRUE").
`git status` on both control dirs: empty (working bytes == committed bytes).

## 2. T1 closeout — PASS

2.1 `lanes/T1_CLOSEOUT/BLOCKER.md` exists and contains the 4-field table: `lifecycle`,
`go_phrase_state`, `budget.used`, `s0` (drift, authority truth, source of truth, fix status).

2.2 `closeout_fields_proposal.py` + `tests/test_closeout_fields_proposal.py` present. Tests
RUN BY VERIFIER: `pytest lanes/T1_CLOSEOUT/tests -q` → **5 passed in 0.23s**. The tests
operate on a `shutil.copy` of the live registry into `tmp_path`, not the live file.

2.3 Live registry NOT modified by the proposal: both scored cycles still have
`budget.used = 0` (unsynced, as the BLOCKER prescribes); zero `CYCLE_CLOSEOUT_FIELD_SYNC`
events exist in `plans/CYCLE_REGISTRY.events.jsonl` (grep count 0).

2.4 CAS-field changes went through researchctl's writer only: journal records
`CYCLE_UPDATED` events at 2026-10-05T01:28:25Z for both scored cycles
(`lifecycle: ACTIVE_LIGHT → TERMINAL`, phase reconciliation, reason "Task-1 closeout
reconciliation…"). `go_phrase_state → DEAD` carries no field-level journal entry because it
is enforced INSIDE the transition writer's CAS update — `research/governance/cycle_registry.py`
lines 321–324 set it whenever `new_lifecycle == "TERMINAL"` and the state is not already
`DEAD` (P-8 terminal-GO-death invariant), exactly as BLOCKER.md describes.

## 3. Lane A — `~/.my-quantitative-data/nba-hoopr-v1/raw/` — PASS

3.1 sha256 recomputed (shasum -a 256) vs `_download_provenance.tsv`: `nba_schedule_2025.csv`
= `a7a5b6607a256c84…` MATCH; `play_by_play_2026.parquet` = `f2d1ccc1a80febd9…` MATCH;
bonus `nba_schedule_2016.csv` = `3373fb4ade99e705…` MATCH. Byte sizes match the TSV.

3.2 `ATTRIBUTION.md` present: CC BY 4.0 quoted verbatim for the producer repos
(hoopR-nba-data / hoopR-nba-stats-data), MIT noted for the release store, required credit
line, provenance pointer to the TSV.

3.3 Rows recounted: 11 season files (2016–2026) total **14,254** data rows; unique ESPN
`id` count **14,254** — exact match to the claim, all game_ids unique.

3.4 `game_date_time` tip-timestamp claim verified by sampling 9 rows across 2016/2021/2025:
values are true local tip-offs with explicit offsets switching correctly with DST
(e.g. `2024-10-22T19:30:00.000000-0400`, `2021-07-20T21:00:00.000000-0400`,
`2025-06-22T20:00:00.000000-0400`), clearly distinct from the coarse `date`/`start_date`
columns. Consistent with known tip times (opening night 2024 = 19:30 ET; 2021 Finals G6 =
21:00 ET).

3.5 Source boundary: the TSV carries `release_tag` + GitHub-API `asset_updated_at` per file
(no literal URL column — see defect D-1). All URL-bearing artifacts scanned
(ATTRIBUTION.md, NBA_POST2015_SOURCES.md, handoff_A.json): every URL is
`github.com/sportsdataverse/…` (hoopR-nba-data, hoopR-nba-stats-data, hoopR,
sportsdataverse-data/releases; download pattern
`https://github.com/sportsdataverse/sportsdataverse-data/releases/download/{tag}/{file}`).
No non-sportsdataverse download source found.

## 4. Lane B — `~/.my-quantitative-data/wnba-v1/raw/` — PASS

4.1 sha256 recomputed vs `lanes/B_WNBA/DATA_MANIFEST.md` (full digests in
`audit_results.json`): `espn_schedules/wnba_schedule_2025.csv` = `b1fe7187113b9336…` MATCH;
`espn_schedules/wnba_schedule_2011.csv` = `4057733233c71019…` MATCH;
`espn_sample_2025/team_box_2025.csv` = `f32d9ebefa40632f…` MATCH.

4.2 ESPN schedules recounted: **25** per-season csv files, **6,029** rows, **6,029** unique
game_ids — exact match to claim (6,029 / 25 seasons).

4.3 Stats-side recounted: **30** `wnba_schedule_*.csv.gz` (1997–2026), **7,009** rows,
**7,009** unique game ids — exact match to claim (7,009 / 30 seasons).

4.4 2025 sample recounted: `team_box_2025.csv` = 624 rows / **312** unique games;
`player_box_2025.csv` starter flag → **exactly 10 starters in each of all 312 games**
(min = max = mode = 10) — exact match to claim. `ATTRIBUTION.md` present (CC BY 4.0 on the
release store, attribution line, wehoop producers named).

## 5. Lane C — `lanes/C_MECHANISMS/MECHANISMS.md` — PASS

5.1 §1 PIT matrix present: F1–F11, each row with mechanism, knowable-BEFORE-game verdict,
$0 source + rights status, publish-timestamp story, leakage risk, and kill test.

5.2 §2 five hypotheses H-C1 … H-C5, each with an explicit frozen falsifier ("REJECT iff
pooled 95% CI of ΔLL(arm, B1*) includes 0 or favors B1*, …") and a kill test.

5.3 No outcome computed this cycle: lanes contain only documents, a census/audit script
(no sklearn/metrics/fit/predict anywhere in `lanes/`), and the T1 registry proposal (5 tests,
synthetic registry copy). The log-loss numbers quoted in MECHANISMS.md are citations of the
TERMINAL cycles' immutable summaries and match them: NBA B0 pooled LL 0.676852 (n=8369) →
"0.6769, n=8369"; NFL B0 0.693548 (n=1865) → "0.6935, n=1865". No new metric on real data.

5.4 No re-grid on the spent window: the doc itself declares NBA 2009–2015 SPENT for
K/HCA/rest/form (§0.2, §3.2, §4); NBA evaluation is 2016+ only; NFL new data is 2026+
prospective only (mains stay dead, only interaction framings on new windows); H-C5's K/HCA
calibration is explicitly on the FRESH WNBA program's own data (a new league under the same
train-only discipline), which is not the spent NBA window. Banned list restated (538,
closing odds, current-game box scores, re-grids).

## 6. Boundaries — PASS

6.1 No S1 references: `grep -rniE "\bs1\b"` over `lanes/` → zero hits.

6.2 No push: `orca/winprob-ng-prep-v1-integration`, `orca/nba-winprob-scored-v1-integration`,
`orca/nfl-winprob-scored-v1-integration`, `orca/nba-winprob-prep-v1-integration`,
`orca/nfl-winprob-prep-v1-integration` — all have NO upstream configured. `main` tracks
`origin/main` and is **ahead 15 / behind 0** (576ddb3e not on origin) — nothing pushed.

6.3 No accounts/keys: grep for api_key/apikey/secret/password/token/credential/account over
`lanes/` → only (a) documentation that key/account-gated sources were BLOCKED
("balldontlie BLOCKED_NO_KEY", "Kaggle … BLOCKED_NO_ACCOUNT"), and (b) the registry CAS
`write_token` governance field in T1 code. No credentials anywhere.

6.4 Futures untouched: this cycle's root commit `576ddb3e` touches only
`plans/ACTIVE_CYCLES.json`, `plans/CYCLE_REGISTRY.json`,
`plans/CYCLE_REGISTRY.events.jsonl`, `plans/PLAN_winprob_ng_prep_v1.md`. The later
`40917736` (FUTURES-ES-PB1-V1's own CAS reconcile) also touches only the three `plans/`
registry files. No futures branch/worktree file modified by this cycle.

## Defects

| ID | Severity | Description |
|---|---|---|
| D-1 | MINOR | Lane A `_download_provenance.tsv` has no literal per-file URL column (release_tag + GitHub-API asset timestamps only). URL provenance is auditable today only via ATTRIBUTION.md / NBA_POST2015_SOURCES.md / handoff_A.json — all scanned, all sportsdataverse — but a URL column would make the "no external source" claim single-file auditable. |
| D-2 | MINOR | Lane B `DATA_MANIFEST.md` table truncates each sha256 to 16 hex chars; full digests live in `audit_results.json`. Byte-verification against the markdown table alone is not self-sufficient (verifier verified 3 files against recomputed values). |
| D-3 | NOTE | Root `main` advanced `576ddb3e → 40917736` during this verification (concurrent FUTURES-ES-PB1-V1 registry reconcile, plans/-only, journal-recorded). Disclosed for timeline accuracy; affects no check. |

0 CRITICAL · 0 MAJOR · 2 MINOR · 1 NOTE.

## Final verdict

**VERIFICATION_PASS** — all six checks PASS with re-measured evidence; defects are
documentation-completeness notes only, none blocks the round.
