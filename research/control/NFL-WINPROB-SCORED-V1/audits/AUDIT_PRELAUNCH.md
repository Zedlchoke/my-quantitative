# AUDIT_PRELAUNCH — NFL-WINPROB-SCORED-V1 (A7, round-1 fresh)

- auditor: A7 prelaunch, fresh context; PREP-era G4/G5 PASS verdicts are
  REOPENED and carry NO authority — every item below re-measured from bytes.
- date: 2026-10-04
- worktree HEAD measured: `2ddef0863b37ca7edd7dd21ce4887ab3958fb888`
  (branch `orca/nfl-winprob-scored-v1-integration`, clean tree)
- code freeze: `8cd0e1bcf9c9d45f5e10ae1b73b93eee7560a7b7`
  (manifest `code_freeze_sha`; predecessor tip `9639706f…`, ancestor verified)
- freeze manifest: `research/control/NFL-WINPROB-SCORED-V1/FREEZE_MANIFEST.json`
  (schema `nfl_winprob_scored_freeze@1`, created 2026-10-04T13:38:11Z;
  regen commit `2ddef086` changed only `created_utc` + `code_freeze_sha`)
- companion evidence: `lanes/E2_data_freeze/VERIFICATION_REPORT.md`
  (VERIFICATION_PASS 7/7, 0 HIGH/CRITICAL, 3 LOW)

# VERDICT: A7_PRELAUNCH_AUTHORIZED

0 HIGH, 0 CRITICAL, 4 LOW (L1–L3 disclosed defects/notes, L4 informational).
No finding invalidates the freeze, the arm identity, the data authority, the
accounting, or the owner-authority boundary. Launch remains two-key gated: this
artifact plus the owner's structured GO record typed at this cycle's own gate.

## Item-by-item verdicts

### A7-1 Hashes chain — PASS
All five manifest-pinned hashes recomputed from bytes and match (raw
`games.csv` `f1e8fe78…`, derived `games_nfl.csv` `f7909fa5…`,
`lineages_nfl.csv` `977a43e2…`, `features_nfl.csv` `4ee2175e5…`,
`ATTRIBUTION.md` `b1852975…`); `protocol_digest` `5b035a1c…` matches
`lanes/NFL_C_protocol/PROTOCOL_EVAL_NFL.md`. Raw sha equals the pull-time
value in `raw/ATTRIBUTION.md` (pulled 2026-10-04T12:31:39Z) and the PREP-era
lane D record — raw untouched end to end.

### A7-2 Exact-arm identity (9 arms, three-way + ledger) — PASS
The 9 arms are identical across (i) `FREEZE_MANIFEST.json` `arms`, (ii)
`nfl_winprob/protocol.py` `ARMS` (with `assert len(ARMS) == 9`), and (iii)
`PROTOCOL_EVAL_NFL.md` Section arm table; `TRIAL_LEDGER.jsonl` specs match
fourth-way. Exact values: B0 (floor); B1-a K=20/HCA=0; B1-b K=20/HCA=65;
B1-c K=40/HCA=0; B1-d K=40/HCA=65 (γ=2/3 all); B2-a f1–f6; B2-b f1,f5,f6;
B2-c f1,f2,f3,f4; B2-d f1. Feature map f1=`elo_diff`, f2=`rest_diff`,
f3=`short_week_home`, f4=`short_week_away`, f5=`form_home`, f6=`form_away`
verified against protocol §2; the unsuffixed `elo_diff` f1 stream is B1-a
(K=20, HCA=0) per AMENDMENT_A1, wired in `export_features.py`. Constants
identical everywhere: L2=1.0, seed=20261005, elo_init=1500.0, gamma=2/3,
TEST 2019–2025, TRAIN 2000–2018 inclusive. 11 registered comparisons match
manifest ↔ runner `REGISTERED_COMPARISONS` (comparisons are not arms; budget
unchanged). GO phrase identical in manifest / `protocol.py` / runner.

### A7-3 Data + PIT authority (kickoff-grain fixtures named) — PASS
Data authority: nflverse-data releases only, CC BY 4.0 re-verified live
(1 fetch, LICENSE.md), attribution chain in `raw/ATTRIBUTION.md`; raw+derived
outside git under `~/.my-quantitative-data/nfl-nflverse-v1/`. Kickoff-grain
law active from season 2000 (1999 kickoff timestamps 100% missing — lane-B
fact frozen; fallback law NOT further activated), enforced by named fixtures:
`test_kickoff_no_lookahead_mutation`,
`test_same_kickoff_games_never_inform_each_other`,
`test_same_kickoff_mutation_isolation` (identical-kickoff games never inform
each other; mutation-isolated). PIT items §8.1–8.12 map to named tests:
leakage → `test_static_leakage_grep` + real-header test; renames/lineages →
`test_rename_continuity_stl_la` (32 lineages, CLE/BAL separate, re-measured);
neutral → `test_neutral_zero_hca` (95 neutral rows measured); ties →
`test_tie_update_half` + `test_tie_counts_half_win_in_form` +
`test_tie_law_excluded_and_disclosed` (15 ties, 6 in TEST); REG/playoff
separation → `test_game_type_normalization` + split-count test
(1,865/89/6); rest/short-week/form → `test_rest_shortweek_form_bye`.
Quarantined by law: odds columns (QUARANTINED_COLUMNS dropped at load),
pbp-derived features, injuries — NOT_RUN_PIT, zero occurrences in feature
code (grep-verified).

### A7-4 Accounting — PASS
`TRIAL_LEDGER.jsonl`: exactly 9 rows, all `status=PREREGISTERED`,
`observed=false`, class PRIMARY, specs identical to the arm set, registered
2026-10-04T13:36:33Z; **0 COMPUTED**. Registry budget for
NFL-WINPROB-SCORED-V1: used **0** / max **9**. `results/` directory empty.
`make_freeze_manifest.py` seeds `nfl_winprob_trial_ledger@1` rows (schema
correct at seed time). (LOW-1: the post-GO append path writes COMPUTED rows
with an NBA-schema string — see Findings.)

### A7-5 Dry-run hygiene — PASS
No metric artifact exists anywhere for this cycle: `results/` empty, ledger 0
COMPUTED. Refusal paths re-executed by the auditor: `nfl_winprob.evaluate`
stub → exit 3; scored runner without GO record → exit 3 with named reasons
(A7 artifact missing [expected pre-audit], no GO record). Synthetic selftest
exit 0, touches no real data. Real-data paths exercised only by schema/row/
hash assertions (no metrics) in `test_real_features_header` /
`test_real_csv_load_and_split_counts`.

### A7-6 S1 untouched — PASS
No S1 paths or accessors in the package (grep clean). Registry records
`s1: SEALED_UNTOUCHED` for this cycle. Commits touch only `nfl_winprob/` and
the cycle control dir; worktree clean; no credentials, no accounts, no push/
merge, no betting surface anywhere in the diff.

### A7-7 No post-freeze drift — PASS
`git diff --name-only 8cd0e1bc..HEAD` = `FREEZE_MANIFEST.json` only (inside
`post_freeze_allowlist`); zero `nfl_winprob/` changes since the code freeze;
worktree clean. The regen commit `2ddef086` is exactly the allowlisted
manifest correction (code_freeze_sha 9639706f → 8cd0e1bc + created_utc) — the
prior generation predated the code commit and would have self-flagged as
drift; the regen is disclosed, allowlisted, and verified minimal. Heavy lock
measured FREE_PROVEN via `researchctl.py locks inspect` (launch-gate
condition currently satisfiable). Launch-gate drift check compensating
control verified (allowlist flags any package change; see LOW-2).

### A7-8 Twin NOT_RUN-by-design — PASS
This cycle: scored evaluation is NOT_RUN by design pre-GO (0 COMPUTED, empty
results, refusal exits verified). The NBA twin program: no NBA artifacts,
paths, or ledgers touched by this cycle's commits ("no NBA mixing" recorded
in PREP_SUMMARY_NFL; only adaptation provenance comments in the runner). The
NBA-schema remnant in the runner's post-GO ledger append (LOW-1) is a label,
not an execution: nothing NBA was computed or consumed.

### A7-9 Owner authority — PASS
No GO record exists for NFL-WINPROB-SCORED-V1 anywhere (control dir searched;
only other cycles' GO records exist, none for this cycle). `go_phrase_state`
= `REGISTERED_NOT_CONSUMED` in both the freeze manifest and the registry;
plan §0: the owner's stated intention to score is INTENT ONLY, not a typed
GO. The gate is structured-JSON enforced (`check_launch_gates`): record must
exist, parse as JSON, and carry `phrase == "GO NFL WINPROB SCORED V1
EVALUATION"`, `cycle_id == "NFL-WINPROB-SCORED-V1"`, `typed_by == "owner"`,
non-empty `typed_at` — any miss refuses with exit 3 (re-verified). This A7
artifact is pinned in the manifest (`a7_report_path`) and the runner greps
for `A7_PRELAUNCH_AUTHORIZED` in it — both satisfied by this document.

## Findings

- **LOW-1** `nfl_winprob/run_evaluation.py` (~line 407): post-GO
  `append_trial_rows` writes COMPUTED ledger rows with
  `"schema": "nba_winprob_trial_ledger@1"` (NBA adaptation remnant; seeded
  PREREGISTERED rows correctly use `nfl_winprob_trial_ledger@1`). Impact:
  post-GO bookkeeping label mismatch only; pre-GO accounting (this audit's
  scope) is exact. Repair is a code change → would require a new code commit
  + freeze-manifest regen under the drift law; owner's decision, auditor
  does not repair.
- **LOW-2** NBA copy remnants in `check_launch_gates`: explicit drift-prefix
  check references `nba_winprob/` (dead reference for this repo) and one
  refusal message says "need freeze v2 post-AMENDMENT_1" (text only; actual
  schema check is `nfl_winprob_scored_freeze@1`, correct). Compensating
  control verified: the `post_freeze_allowlist` gate flags ANY
  `nfl_winprob/` change as outside-allowlist drift, so the immutability law
  remains enforced.
- **LOW-3** Registry `head` field for this cycle is stale at `9639706f…`
  (last registry write 13:33:09Z precedes the two cycle commits); measured
  HEAD is `2ddef086…`. Recorded-not-normalized; registry writes are outside
  auditor/verifier lanes.
- **L4 (informational)** The synthetic selftest prints a trailing verdict
  JSON `PROGRAM_PASS:false / REJECT:true` — that is the pipeline's verdict
  struct computed on random synthetic data (mechanics validation only; all
  asserts pass; exit 0). Not a defect; noted to prevent misreading at GO time.

## Launch posture

Remaining preconditions for G5 (owner GO), none in auditor scope: (1) owner
types the structured GO record JSON at this cycle's own gate; (2) heavy lock
FREE at launch (currently FREE_PROVEN); (3) clean tree at launch. On GO, the
runner writes only into the pinned `results_dir` and appends COMPUTED ledger
rows (subject to LOW-1's label). Without GO: refusals exit 3, verified.

A7_PRELAUNCH_AUTHORIZED — 0 HIGH / 0 CRITICAL / 4 LOW.
