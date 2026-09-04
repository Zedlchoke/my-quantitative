# STOCKS-FREE-V4 — A7 Independent Prelaunch Audit Report

- Schema: `stocks_free_v4_run/a7_prelaunch_audit@1`
- Producer role: **A7** (independent prelaunch auditor — audit only, no repairs)
- Phase: V4-Q
- Audited at: 2026-09-04T04:03:43Z
- Lane: `/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v4/q-a7-prelaunch`
- Branch: `orca/stocks-free-v4-q-a7-prelaunch`
- Audit base head / W1 under audit: `dfa099aa6246883a9e650aeebcf9ee49ec1d8e31`
- Method: the entire chain was **recomputed by measurement**; control-file self-claims were not trusted without independent re-verification.

---

## VERDICT

**STOCKS_FREE_V4_S0_LAUNCH_AUTHORIZED**

- Unresolved HIGH/CRITICAL findings: **0**
- Findings: 1 LOW (non-blocking), 2 NONE-severity notes (see Findings).

Authorization authorizes the W1 freeze state only. It does **NOT** start scoring: the
HARD STOP before the first scored cell remains in force, and scored execution requires
the explicit owner instruction **`GO STOCKS V4 SCORED EXECUTION`**.
S1 `SEALED_UNTOUCHED`; deployment `NO_PAPER_NO_LIVE_NO_ORDERS`; heavy cap 1; budget 0/6;
execution ledger empty.

---

## Section results (all measured)

| # | Section | Result | Severity |
|---|---------|--------|----------|
| S1 | V4-R Reconciliation | PASS | NONE |
| S2 | V4-P Gates | PASS | NONE |
| S3 | V4-D1 Proposal wave identity | PASS | NONE |
| S4 | V4-D2 Audits + selection freeze | PASS | NONE |
| S5 | V4-I Implementation | PASS | NONE |
| S6 | V4-Q QA evidence | PASS | NONE |
| S7 | W1 + twins | PASS | NONE |
| S8 | Safety invariants | PASS_WITH_LOW_FINDING | LOW (S8-F1) |
| S9 | Workers | PASS | NONE |
| S10 | Known pre-existing item | PASS | NONE |

### S1 — V4-R Reconciliation (PASS)

- `git -C /Users/hoangminhlong/my-quantitative rev-parse orca/stocks-free-v3-integration`
  → `4a9457ab5682b2db1d0a188a51f4715f431c3fe3` (exact match to prior terminal).
- `git merge-base --is-ancestor 6993383 4a9457a` → **YES**. `6993383` is the V3 terminal
  A7T commit `STOCKS_FREE_V3_REJECT_ALL_CONFIRMED`.
- V3 W1: `state.json` and `terminal_report.json` in `.worktrees/stocks-free-v3/integration`
  both record W1 `586f9febe29ae6ba0b176c8c9a9b1b4645f3bca4`; the object exists in the repo.
- Historical denominator: counters `historical 6 observed / 6 published` + `v3 6/6`
  → **12 observed / 12 published**; `terminal_report.json` states `statistical_denominator: 12`;
  `historical_boundary.json` carries V2 6/6 (6/6 EXACT_MATCH). All three files mutually
  consistent (phase TERMINAL, verdict REJECT_ALL, terminal A7T commit `ad897c8a...` equals
  branch `orca/stocks-free-v3-r-a7-terminal` head `ad897c8`).

### S2 — V4-P Gates (PASS)

- P1 regression suite in own worktree:
  `pytest tests/assets/stocks/test_v4_p1_factory_regression.py -q` → **16 passed in 0.87s**.
- `p2_a3_data_manifest.json` → `status: FROZEN`; `p2_a3_benchmark_contract.json` → `status: FROZEN`.
- Re-measured `shasum -a 256` of
  `/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging/MANIFEST.json`
  → `62ac324d7e683961b0d88f85153e4a072d09fe0a6745a54687b9e3b219d8f658` (exact match).

### S3 — V4-D1 Proposal Wave Identity (PASS)

- Pairwise `git merge-base` across `orca/stocks-free-v4-d1-{a4,a5,a6}-proposals`:
  all three pairs = `5022f265912e0dd398b79441023c263bc4c61b24` (wave sha, exact).
- Six proposal files present in `research/control/stocks_free_v4_run/proposals/`
  (`a4_h1`, `a4_h2`, `a5_h1`, `a5_h2`, `a6_h1`, `a6_h2`), each containing an
  `outcome_blind_attestation` string (6/6).

### S4 — V4-D2 Audits and Selection Freeze (PASS)

- `d2_a7_novelty_audit.json`: 6/6 hypotheses `ELIGIBLE`; grep for `INELIGIBLE` → 0.
- `d2_a9_feasibility_audit.json`: 6/6 `FEASIBLE` / `FEASIBLE_WITH_CONDITIONS`;
  grep for `INELIGIBLE` → 0.
- `selection_freeze.json` selects **exactly 2 families × 3 arms**:
  - `SFV4-A5-H1-PARTICIPATION-SHIFT`: A / N / C (63-session clock);
  - `SFV4-A4-H1-SEMIVARIANCE-SHARE`: A / N / C (21-session clock);
  - budget `planned_scored_cells = 6`.
- Kappa fallback recorded **EX ANTE**: "KAPPA FALLBACK FROZEN EX ANTE (A9-F C1, frozen
  before any V4 return is observed): kappa_t = 1.0 flat … no in-sample refit".
- Clock anchoring pinned byte-exact to S0 start `2018-04-04` for both families.
- `not_selected_no_reassignment` = [A4-H2, A5-H2, A6-H1, A6-H2] — exactly the four
  unselected hypotheses, no reassignment mapping.
- Freeze-referenced audit heads match actual lane branch heads (`158239e` novelty, `bb5c3ee` feasibility).

### S5 — V4-I Implementation (PASS)

- `pytest tests/assets/stocks/test_v4_family_participation.py -q` → **13 passed**.
- `pytest tests/assets/stocks/test_v4_family_semivar.py -q` → **35 passed**.
- Modules exist: `research/stocks_free_v4/family_participation/{__init__,config,features,schedule}.py`;
  `research/stocks_free_v4/family_semivar/{__init__,config,schedule,signals}.py`.
- PIT spot-check: participation `test_e02_pit_no_lookahead_mutations` (line 258);
  semivar `Test02PitNoLookahead` with `test_02a_window_is_exact_trailing_completed`,
  `test_02b_future_mutation_cannot_change_past_targets`, `test_02c_mutation_inside_window_is_visible`;
  plus `test_06c_kappa_fallback_below_252_scored_sessions` covering the frozen fallback.

### S6 — V4-Q QA Evidence (PASS)

- `q_dummy_dryrun_evidence.json`: `overall: PASS`; `observed = 6`, `published = 6`;
  `replay_all_zero_delta: true`; six arm digests pairwise distinct (`digests_unique: true`);
  `scored: false`, `real_pnl: false`; temp-path ledger only; refusal path keeps key unpublished;
  `scored_artifact_files_in_control: []`.
- `q_resource_probe.json`: `heavy_cap: 1`, `workers_active: 0`.

### S7 — W1 and Execution/Reproduction Twins (PASS)

- Both twins detached at exactly `dfa099aa6246883a9e650aeebcf9ee49ec1d8e31`
  (`git rev-parse HEAD` match; `git status` shows "Not currently on any branch";
  r-reproduce clean, e-exec-1 untracked limited to ledger + checkpoint).
- Both twins' `.staging/MANIFEST.json` sha256 = `62ac324d7e68…d8f658` (== authorized value).
- Byte-identity beyond MANIFEST: **51/51 staged files** identical between twins
  (every file sha256-compared, including `cell_runner.py`, all 45 panel files, distributions,
  partition folds, split factors, both xlsx, fetch log, 6 V2-era cell artifacts).
- Exec twin `execution_ledger.json`: `observed: 0`, `published: 0`, `entries: []` — empty.
- Exec twin `counters_checkpoint.json`: budget `0/6`; historical 12/12; S1 sealed; workers 0.
- Note (NONE): inside the W1 snapshot, `state.json`/`w1_freeze.json` label `w1 = 203f685`
  (code-bearing); the freeze tip `dfa099a` adds only control metadata, and integration commit
  `a4baeab` subsequently canonicalized W1 = `dfa099a` (freeze-artifact-inclusive) with
  `203f685` recorded as superseded. Twins were already created at `dfa099a`. Metadata-only.

### S8 — Safety Invariants (PASS, 1 LOW finding)

- No scored-metrics claims: grep `"scored": true` and `real_pnl … true` over **both**
  control trees (q-a7 worktree and integration worktree) → **0 matches**; dummy evidence
  carries `scored=false` / `real_pnl=false`.
- S1 `SEALED_UNTOUCHED` present in `state.json`, `w1_freeze.json`, `event_log.jsonl`, and
  both twins' checkpoints.
- No push: 11/11 `stocks-free-v4` branches have **empty upstream** (`git for-each-ref upstream=`).
- No V4 merge into main: **0/11** V4 branch heads are ancestors of `main`.
- **FINDING S8-F1 (LOW, non-blocking):** `main` has moved from the expected pin `1a8b53d`
  to `047c685` "Add free multi-source data fusion plan" — a single owner doc commit adding
  `PLAN_data_fusion.md` (395 lines, unrelated to V4). `1a8b53d` remains an ancestor of
  `main`; no V4 lineage is merged; no push. Residual risk to V4 isolation: none. The
  launch-bar phrasing "main still at 1a8b53d" is technically stale.
- Integration branch `2bcfa82` is a strict **descendant** of `dfa099a` (merge-base = `dfa099a`),
  adding two metadata-only commits (`a4baeab` W1 canonicalization, `2bcfa82` worktree manifest);
  tree delta touches only `event_log.jsonl`, `state.json`, `w1_freeze.json`, `worktree_manifest.json`.

### S9 — Workers (PASS)

- `ps aux | grep -iE "pytest|backtest|scoring" | grep -v grep` → **no matches**.

### S10 — Known Pre-Existing Item: CONTINUE.md Verdict-Lineage Repair (PASS, NONE)

- At audit HEAD `dfa099a`: `pytest tests/stocks_free_v2/test_terminal_metadata.py -q`
  → **13 passed**, including `test_map_and_continue_agree`.
- At base `4a9457a` (re-run inside `.worktrees/stocks-free-v3/integration`, HEAD verified,
  with `PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`, worktree left clean):
  **1 failed** — `test_map_and_continue_agree` fails with
  `AssertionError: assert 'STOCKS_FREE_V1_REJECT_ALL' in CONTINUE.md` — confirming the
  failure pre-existed at the V3 terminal base, before V4.
- Repair classification: **metadata-only**. The only V4-chain commit touching `CONTINUE.md`
  is `203f685`; its diff is purely additive documentation (V4 plan pointer + "Verdict
  lineage" section). Every stated value cross-checks against independently measured records:
  V2 effective verdict `STOCKS_FREE_V1_REJECT_ALL` and canonical W1 `106378230abe…`
  (== `historical_boundary.json`), V3 W1 `586f9fe`, denominator 12/12, V4 budget 0/6,
  "no scored V4 PnL exists", S1 sealed. No verdict, counter, ledger, or artifact mutation.
  Severity: **NONE**.

---

## Findings

| ID | Severity | Resolved | Blocking | Summary |
|----|----------|----------|----------|---------|
| S8-F1 | LOW | no | no | `main` advanced `1a8b53d → 047c685` via unrelated owner doc commit (`PLAN_data_fusion.md`); 1a8b53d still in ancestry; 0/11 V4 heads in main; no push. Expected-pin drift only. |
| S7-N1 | NONE | yes | no | W1 label canonicalized post-freeze (`a4baeab`: W1 = `dfa099a` supersedes `203f685`); twins already at `dfa099a`; metadata-only. |
| S2-N1 | NONE | no | no | Full-suite claim "1807 passed, 4 skipped (ran alone)" not independently re-executed; per mandate, audit re-ran P1 (16 passed) + both family suites (13 + 35 passed), all green. |

## Unresolved HIGH/CRITICAL count

**0**

## Verdict

**STOCKS_FREE_V4_S0_LAUNCH_AUTHORIZED**

Authorization does NOT start scoring — A1 must stop before the first scored cell until the
owner says **`GO STOCKS V4 SCORED EXECUTION`**.

---

*Machine-readable twin: `research/control/stocks_free_v4_run/d2_q_a7_prelaunch_audit.json`.*
*Pin commit ("V4-Q A7: audit head pin") is the A7 final HEAD; its sha is reported in the
final audit message and recorded via `audit_commit_sha` (sha of the audit commit) inside the JSON.*
