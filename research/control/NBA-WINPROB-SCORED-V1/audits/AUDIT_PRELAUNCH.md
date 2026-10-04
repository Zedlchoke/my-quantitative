# AUDIT_PRELAUNCH — NBA-WINPROB-SCORED-V1 (Lane A7, independent, fresh-context)

- Auditor role: A7 INDEPENDENT PRELAUNCH AUDITOR (repo law §19.3). Adversarial
  posture: attempted to find reasons to refuse. Read-only except this audits/
  directory. Audit date: 2026-10-04.
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/nba-winprob-scored-v1/integration`
- Branch: `orca/nba-winprob-scored-v1-integration`
- HEAD at audit start (= audit end, tree clean): `0f9f8f10b8818b92786c2655a0353a4a41d27d18`
- Code freeze sha (manifest): `39b1115632d06b159c5c78a470d2d0bff3cb8386`
- Merge-base(freeze, HEAD) = freeze sha → HEAD is a strict descendant.
- Commits after freeze: `670eb76b` (G3 freeze: manifest + ledger), `0f9f8f10`
  (E2 report). Both exclusively inside `research/control/NBA-WINPROB-SCORED-V1/`.
- Venv used: `/Users/hoangminhlong/my-quantitative/.venv/bin/python` (repo venv;
  the `.venv` path in the dispatch packet does not exist — E2's D2, confirmed).

## Per-item verdict table

| # | Item | Verdict | Key evidence |
|---|------|---------|--------------|
| 1 | Hashes chain | **PASS** | See 1a–1e below. |
| 2 | Exact-arm identity (9 arms, 3 authorities) | **PASS** | Manifest `arms[]`, `protocol.py` `ARMS`, PROTOCOL_EVAL sec5 table — pairwise distinct, byte-equal specs. |
| 3 | Data / PIT authority | **PASS** | ATTRIBUTION.md (CC BY 4.0 + BRef provenance, sha match); pytest 29/29; no-lookahead / same-day / leakage-grep tests named below; features.csv has no outcome/538 columns. |
| 4 | Accounting | **PASS** | Registry budget 0/9; ledger = denominator seed (9 PREREGISTERED, 0 COMPUTED); `test_ledger_no_duplicate_primary`. |
| 5 | Dry-run hygiene | **PASS** | No real-outcome metric anywhere; both refusal gates exit 3 live with zero writes; synthetic selftest PASS ("no real data touched"). |
| 6 | S1 seal | **PASS** | Zero S1 references in cycle artifacts; registry `s1: SEALED_UNTOUCHED`; no writes outside cycle paths. |
| 7 | No post-freeze drift beyond allowlist | **PASS** | `git diff --name-only 39b11156..HEAD` = 4 paths, all under `research/control/NBA-WINPROB-SCORED-V1/**`; `nba_winprob/` diff empty (byte-unchanged). |
| 8 | Twin integrity | **PASS (declared NOT_RUN-by-design)** | Reproduction twin is post-GO machinery (`--repro` → REPRO-class rows after a scored run). 0 REPRO rows exist; no scored run exists. Declared, not a defect. |
| 9 | Owner-authority boundary | **PASS** | No GO record file for this cycle anywhere (deep sweep); registry `go_phrase_state: REGISTERED_NOT_CONSUMED`; run gate refuses without GO record (exit 3, live-verified). |

## Item 1 detail — hashes chain

- **1a Freeze sha ∈ history**: `39b11156` is an ancestor of HEAD (merge-base =
  itself); commit subject: "NBA-WINPROB-SCORED-V1 implementation (G2):
  run_evaluation — frozen 9-arm x 7-fold walk-forward ... two-key launch
  gates ... exit 3 on refusal".
- **1b Allowlist law**: `git diff --name-only 39b11156..HEAD` returns exactly
  `FREEZE_MANIFEST.json`, `TRIAL_LEDGER.jsonl`,
  `lanes/E2_data_freeze/E2_REPORT.md`, `lanes/E2_data_freeze/handoff_E2.json`
  (all +249 lines, 0 deletions). Grep for paths outside
  `research/control/NBA-WINPROB-SCORED-V1/`: **zero matches**.
  `git diff 39b11156..HEAD -- nba_winprob/` is **empty** → nba_winprob/ is
  byte-unchanged since the code freeze.
- **1c Data hashes recomputed (all 6 pins, exceeds required raw+features)**:

  | File | Manifest sha256 (prefix) | Recomputed | Match |
  |---|---|---|---|
  | raw/nbaallelo.csv | `d46ed3540ee8…` | `d46ed3540ee8…` | YES |
  | derived/features.csv | `644cd740a500…` | `644cd740a500…` | YES |
  | derived/games.csv | `e24d9a3b1feb…` | `e24d9a3b1feb…` | YES |
  | derived/lineages.csv | `c8cdd58ac910…` | `c8cdd58ac910…` | YES |
  | derived/participants.csv | `fd7cb5394e09…` | `fd7cb5394e09…` | YES |
  | raw/ATTRIBUTION.md | `e134e20cca04…` | `e134e20cca04…` | YES |
- **1d Protocol digest**: `sha256(lanes/C_protocol/PROTOCOL_EVAL.md)` =
  `c058760d6e77863fd7f5912ccfebad64755a26c1dd76e8946496f244f9a451f7` = manifest
  `protocol_digest`. Byte-identical to the predecessor tip
  `b5b5084753d2…`'s copy (`git show b5b50847:lanes/C_protocol/PROTOCOL_EVAL.md`
  hashes equal) → "inherit sec2–6+9 verbatim" holds at file granularity.
- **1e Ledger seed**: `TRIAL_LEDGER.jsonl` = exactly 9 rows, all
  `status: PREREGISTERED`, `observed: false`, `class: PRIMARY`, specs equal to
  the manifest arms; **0 rows** with status COMPUTED (grep count 9 / 0).
  `make_freeze_manifest.py` derives manifest arms directly from
  `protocol.ARMS` (single source of truth — divergence structurally blocked).

## Item 2 detail — exact-arm identity

Pairwise-distinct spec vectors across all three authorities
(B0; B1-a K16/HCA0; B1-b K16/HCA100; B1-c K32/HCA0; B1-d K32/HCA100; B2-a f1–f6;
B2-b f1,f5,f6; B2-c f1–f4; B2-d f1):

- Manifest `arms[]` ≡ `protocol.py` `ARMS` (field-by-field: kind, K, HCA,
  ordered feature tuples). Assert `len(ARMS) == 9` in code.
- PROTOCOL_EVAL sec5 table matches after applying the sec2 f1–f6 mapping
  (f1 elo_diff, f2 rest_diff, f3 b2b_home, f4 b2b_away, f5 form_home,
  f6 form_away). B1 grid matches K∈{16,32} × HCA∈{0,100} exactly.
- Supporting tests: `test_run_evaluation.py::test_nine_arms_and_registered_comparisons`,
  `test_identity.py` (lineage continuity; Hornets/Pelicans two-lineage trap).
- Frozen constants agree across manifest/code/protocol: TEST_SEASONS 2009–2015,
  TRAIN (1947,2008), L2=1.0, seed 20261004, ELO_INIT 1500.0, ELO_GAMMA 0.75,
  GO phrase `GO NBA WINPROB SCORED V1 EVALUATION`
  (`test_go_phrase_form`).

## Item 3 detail — data / PIT authority

- `ATTRIBUTION.md` pins FiveThirtyEight nba-elo (CC BY 4.0), Basketball-Reference
  provenance disclosure, download date, sha256 (`d46ed354…`, matches manifest),
  strong etag, usage boundary (internal research only, owner veto retained).
- `pytest nba_winprob/tests/ -q` → **29 passed** in 86.6 s (zero failures).
- Named PIT tests:
  - `test_features_asof.py::test_no_lookahead_mutation_property` — flips a
    result on date d; all features for rows dated ≤ d stay byte-identical
    (strictly-previous-date law + same-day exclusion); only later rows change.
  - `test_elo.py::test_sameday_disjoint_games_do_not_inform_each_other`,
    `test_elo.py::test_sameday_doubleheader_excludes_leg1_from_leg2`,
    `test_features_asof.py::test_sameday_games_never_inform_each_other_features`
    — date-batched update law.
  - `test_identity.py::test_static_leakage_grep` — model-side sources
    (elo.py, features.py, protocol.py, evaluate.py) must not contain the
    quarantined 538 tokens (`forecast`, `elo_i`, `opp_elo`, `win_equiv`).
  - `test_run_evaluation.py::test_b1_uses_precomputed_asof_columns` — B1 eval
    consumes the as-of columns; `test_b2_train_only_standardization` — fold
    isolation; `test_b0_refit_per_fold_and_fold_isolation`.
- `features.csv` header:
  `src_game_id,gameorder,date,season,is_playoffs,home_lineage,away_lineage,rest_diff,b2b_home,b2b_away,form_home,form_away,rest_home,rest_away,elo_diff_B1-a,p_home_B1-a,…B1-d`
  — **no** `pts/opp_pts/game_result` outcomes and **no** 538 columns
  (`forecast/elo_i/elo_n/win_equiv/opp_elo_i/opp_elo_n`); targets live only in
  the raw table and enter at evaluation under the as-of law. The `p_home_B1-*`
  columns are PIT own-Elo as-of probabilities (protocol features), covered by
  the mutation-property test.

## Item 4 detail — accounting

- Registry row (plans/CYCLE_REGISTRY.json, cycle NBA-WINPROB-SCORED-V1):
  `budget {used: 0, max: 9}` — 0 consumed.
- TRIAL_LEDGER.jsonl is the denominator seed: 9 arms, all PREREGISTERED,
  observed=false; nothing observed pre-GO.
- Append discipline: `test_run_evaluation.py::test_ledger_no_duplicate_primary`
  proves a second PRIMARY append without `--repro` is a no-op (still 9 rows) and
  `--repro` appends REPRO-class rows only (9 PRIMARY + 9 REPRO). Code path
  (`append_trial_rows`) skips arm_ids already COMPUTED unless repro.

## Item 5 detail — dry-run hygiene

- Filesystem sweep: no `scored_summary.json` anywhere; cycle `results/` and
  `audits/` were empty at audit start; no summary/result artifacts under the
  cycle control tree. The two candidates found in the worktree are foreign,
  pre-freeze artifacts: `results/summary.json` (crypto backtest, commit
  `dd01cf0e` "Add files via upload", present in tree at the freeze sha) and
  `research/control/ERP1-TRACKA-COHORT-1/...` (different program). Neither is
  a product of this cycle; no real-outcome metric exists for NBA-WINPROB-SCORED-V1.
- Gate A (live): `python nba_winprob/evaluate.py` (no manifest) →
  `REFUSED: no --freeze-manifest … owner directive 2026-10-04 is explicitly NOT
  a typed GO …` **exit 3**.
- Gate B (live): `python -m nba_winprob.run_evaluation --out /tmp/a7_gate_probe/summary.json
  --worktree . --freeze-manifest <real manifest>` (no GO record) →
  `REFUSED — launch gates failed: - no GO record (…)`. **exit 3**, and the
  `--out` target directory remained **empty** (zero writes on refusal). Note:
  the only failed gate was the GO record — the same invocation re-validated
  cycle_id, code-drift, allowlist, all 5 data hashes and the protocol digest
  live, all green.
- Synthetic selftest (live): `--synthetic-selftest` → `SELFTEST PASS: 9 arms,
  7 comparisons, bootstrap deterministic, no real data touched.` exit 0
  (`test_synthetic_selftest_end_to_end` green in the suite).

## Item 6 detail — S1 seal

- `grep -rn "S1|s1_seal|SEALED"` over `research/control/NBA-WINPROB-SCORED-V1/`
  (json/md/jsonl): **zero matches**. No S1 data or sealed assets referenced.
- Registry: this cycle `s1: SEALED_UNTOUCHED`; worktree git status clean, and
  the freeze..HEAD diff touches only this cycle's control paths → program-level
  S1 status untouched. (`grep -n "s1"` hits in nba_winprob/*.py are the
  substring `s1` inside `res0, res1` identifiers — false positives.)

## Item 7 — post-freeze drift, explicit statement

`git diff --name-only 39b1115632d06b159c5c78a470d2d0bff3cb8386..0f9f8f10b881…`
= 4 paths, all matching allowlist `research/control/NBA-WINPROB-SCORED-V1/**`.
`nba_winprob/` diff empty → **no drift outside the allowlist; code surface
byte-frozen.** (`results/**` allowlist entry: see Finding F2 — nothing was
written there post-freeze.)

## Item 8 — twin integrity

Declared NOT_RUN-by-design: the reproduction twin runs only after a scored run
(`run_evaluation --repro` appends REPRO-class rows). With 0 COMPUTED rows and no
GO, there is nothing to reproduce. Recorded as declared state, **not a defect**.

## Item 9 — owner-authority boundary

- Deep sweep for GO records: `find … -iname "*GO_RECORD*"` over the whole
  worktree returns GO records for OTHER cycles only (DAYTRADE-PLAYBOOKS,
  BTC-COMBO6-SCORED-V1, ECONOMIC-ROBUSTNESS gates, PORTFOLIO-COMPOSITE-12ASSETS,
  DAILY-EXPLORATORY-V1, DAYTRADER-100-V1, EVENT-MECHANISMS-V1). **No GO record
  exists for NBA-WINPROB-SCORED-V1.** The GO phrase string appears only inside
  FREEZE_MANIFEST.json (registered phrase) and E2_REPORT.md (narrative); the
  repo-root control tree has no winprob directory; data dir has none.
- Registry: `go_phrase_state: "REGISTERED_NOT_CONSUMED"`,
  `go_phrase: "GO NBA WINPROB SCORED V1 EVALUATION"`, phase notes "G5 owner GO
  required before any scored execution".
- Enforcement (live-verified): the run gate refuses with exit 3 absent a GO
  record containing phrase + cycle id (`check_launch_gates`; malformed record
  also refused). Scored execution remains impossible until the owner types the
  phrase at this cycle's own gate — A7 authorization is key one of two.

## Findings

| ID | Severity | Finding |
|----|----------|---------|
| F1 | LOW (informational; pre-recorded by E2 as D1, independently reproduced) | `python -m nba_winprob.run_evaluation` with no `--out` exits 2 (argparse enforces required flag) before the gates run, instead of exit 3. Refusal property intact and stronger in substance: no argument vector reaches evaluation without passing `check_launch_gates`, and the gate path (with `--out`) exits 3 with zero writes (live-verified). Optional post-GO hardening: route missing `--out` through the refusal path. |
| F2 | LOW | `post_freeze_allowlist` includes `results/**` (worktree-root), a directory containing pre-existing foreign program artifacts (crypto backtest outputs from commit `dd01cf0e`). Pre-freeze, untouched, not a cycle output — but future writes under `results/**` would be indistinguishable-by-path from foreign clutter. Mitigation in practice: cycle outputs are designated to `research/control/NBA-WINPROB-SCORED-V1/results/` via `--out`. Recommend post-GO: prefer cycle-scoped results paths. |
| F3 | LOW (informational) | Dispatch venv path `/Users/hoangminhlong/.venv/bin/python` does not exist (E2's D2); repo venv `/Users/hoangminhlong/my-quantitative/.venv/bin/python` used throughout this audit. |
| F4 | LOW (informational) | `DeprecationWarning` at `run_evaluation.py:309` (`datetime.utcnow()`); cosmetic, no bearing on validity. |

No HIGH findings. No CRITICAL findings. Zero unresolved HIGH/CRITICAL.

## Final verdict

**A7_PRELAUNCH_AUTHORIZED** — 9/9 items PASS; 0 HIGH/CRITICAL; findings F1–F4
LOW/informational only. The tree satisfies the hashes chain, exact-arm identity,
data/PIT authority, accounting, dry-run hygiene, S1 seal, no-drift law, twin
declaration, and owner-authority boundary. Scored execution remains NOT_RUN and
must stay impossible until the owner types
`GO NBA WINPROB SCORED V1 EVALUATION` at this cycle's own gate (second key).
This audit authorizes nothing by itself beyond proceeding to the owner GO step.
