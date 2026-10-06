# VERIFY_20261006_TRIPLE_LANE — independent verification report

- Verifier: independent (did none of the verified work; adversarial re-measurement)
- Date: 2026-10-06 · Interpreter: `/Users/hoangminhlong/my-quantitative/.venv/bin/python` only
- Scope: final state after the controller's registry sync, three lanes:
  NFL-WINPROB-NG-SCORED-V1 / WNBA-PLAYERFEAT-SCORED-V1 / NBA-WINPROB-NG-SCORED-V1
- Writes: this directory + /tmp/verify_triple sandboxes only. All probe invocations ran
  with `PYTHONDONTWRITEBYTECODE=1` so no `__pycache__` was created in any worktree.
  No lane worktree, no registry file, no other file was modified (closing snapshot below).
- Cost: $0 · network: none · heavy jobs: none (unit-level probes only)

## 0. Baseline (all three lanes)

| Check | Command | Result | Verdict |
|---|---|---|---|
| NFL worktree HEAD/branch/clean | `git -C .worktrees/nfl-winprob-ng-scored-v1/integration rev-parse HEAD; branch --show-current; status --porcelain` | `8288a25e420a175c81af7a4d98e908e54b772c36`, `orca/nfl-winprob-ng-scored-v1-integration`, 0 dirty lines | PASS |
| WNBA worktree HEAD/branch/clean | same for wnba | `e4ea2a1f17e92a60faa2a0fbe58b8b4101f0e9db`, `orca/wnba-playerfeat-scored-v1-integration`, 0 dirty | PASS |
| NBA worktree HEAD/branch/clean | same for nba | `ee4fc0b52a211391dc45fa9aecb176703ac8bcd9`, `orca/nba-winprob-ng-scored-v1-integration`, 0 dirty | PASS |
| Registry rows | python json load of `/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json` | all three rows: head == measured HEAD, budget 0/9, `go_phrase_state=REGISTERED_NOT_CONSUMED`, plan paths as claimed | PASS |

## 1. LANE NFL-WINPROB-NG-SCORED-V1

### A1 — final source read (`research/control/NFL-WINPROB-NG-SCORED-V1/recorder/record_owner_go.py`, 39,589 B, disk == HEAD because tree clean)
- argparse flags exactly: `--cycle --phrase --registry --worktree --execute` (lines 780–794). NO `--a7-series-dir`, NO `--a7-verdict`; the only textual mentions are removal documentation (lines 40/47/90/185/186/687). `grep environ|getenv|config` → only law-prose comments; no env/config selection channel. **PASS**
- Series dir DERIVED: lines 709–711 `bound_worktree = Path(row["integration_worktree"]); series_dir = bound_worktree / "lanes"` — never from CLI. **PASS**
- C5 binding (exit 25): lines 550–581 — `--worktree` must `Path.resolve()` equal the row's integration_worktree; live-head measured at run time. **PASS**
- Anti-symlink fail-closed (C6): lanes-dir symlink refusal (294–299), series-entry symlink/non-dir/outside-lanes (320–337), verdict-file symlink (340–345). Highest series mandatory, no fallback (339–356). **PASS**

### A2 — owner's old-A7 attack, replayed by verifier on BYTE-COPY of the real registry
Sandbox: `/tmp/verify_triple/a2_nfl/CYCLE_REGISTRY.json` (sha256 `5eca4e0d…e4e`, byte-copy of ROOT registry) + alternate dir `alt_lanes/A7_R3/A7_R3_VERDICT.md` copied from the real committed A7_R3 verdict bytes (sha256 `8856541f…7b3`; carries `NFL-WINPROB-NG-SCORED-V1 = A7_R3_PASS` + audited sha — the exact v2-accepted attack material).
```
python record_owner_go.py --cycle NFL-WINPROB-NG-SCORED-V1 --phrase 'GO NFL WINPROB NG SCORED V1 PROSPECTIVE' \
  --registry <copy> --worktree <nfl worktree> --a7-series-dir /tmp/verify_triple/a2_nfl/alt_lanes
→ exit 2; stderr: "error: unrecognized arguments: --a7-series-dir /tmp/verify_triple/a2_nfl/alt_lanes"
registry copy sha256 after: 5eca4e0d…e4e (BYTE-IDENTICAL)
```
**PASS** — argparse usage exit 2 BEFORE any read/write.

### A3 — worktree relocation attack
```
... --worktree /tmp/verify_triple/decoy_worktree  (registry copy)
→ exit 25 "WORKTREE BINDING refused (C6 binding v3)"; registry copy byte-identical
```
**PASS** (C5, exit 25 as claimed).

### A4 — symlink attacks on a /tmp fixture git repo (row head + integration_worktree mutated on a registry COPY — the sanctioned fixture mutation)
Fixture: `/tmp/verify_triple/a4_fixture` (2 commits; `lanes/A7_R1/A7_R1_VERDICT.md` committed at HEAD naming the NFL cycle PASS with audited sha = fixture c1 `a7b22bd5…`; ancestry trivially holds).
| Probe | Result | Verdict |
|---|---|---|
| Baseline dry-run (no attack) | exit 0, `DRY_RUN_OK`, `C6_source: derived from registry row integration_worktree (highest series A7_R1; no caller input)` | PASS |
| lanes itself → symlink to smuggle dir | exit 26 "lanes dir … is a SYMLINK" | PASS |
| real lanes + `A7_R9` entry symlink (old-series smuggle) | exit 26 "A7 series entry … is a SYMLINK" | PASS |
| real A7_R9 dir, verdict FILE is a symlink | exit 26 "A7 verdict file … is a SYMLINK" | PASS |

### A5 — default dry-run against the REAL registry (NO flags beyond `--phrase`)
```
python record_owner_go.py --phrase 'GO NFL WINPROB NG SCORED V1 PROSPECTIVE'
→ exit 0; DRY_RUN_OK; C6 selects A7_R7, audited 22d930f029bc0856eb5f0cd29fd2f817c07ffd4b;
  C5 head 8288a25e… == row head; C7 "ARMED (dry-run — nothing written)"
plans/CYCLE_REGISTRY.json      sha256 5eca4e0d…e4e BEFORE == AFTER
plans/CYCLE_REGISTRY.events…   sha256 b7870e27…ec4 BEFORE == AFTER
all three rows still REGISTERED_NOT_CONSUMED
```
**PASS** — nothing written.

### A6 — A7_R7 verdict committed + ancestry
- `git cat-file blob HEAD:lanes/A7_R7/A7_R7_VERDICT.md` OK; `cmp` disk == HEAD blob (blob sha256 `a21bda20…c8b`). Canonical block line 2: `A7VERDICT cycle=NFL-WINPROB-NG-SCORED-V1 verdict=PASS audited_sha=22d930f0…`. `git merge-base --is-ancestor 22d930f0… HEAD` → exit 0. **PASS**

### A7 — suites
- **Physical re-run: NOT_RUN** with reason: both NFL suites hard-write receipt JSONs into the lane worktree (`lanes/FIX_R6/test_record_owner_go_v3.py:810-811` → `LANE_DIR/go_tool_v3_test_evidence.json`; `lanes/FIX_R5/test_executor_gates_v3.py:218-221` → `LANE_DIR/gate_matrix_evidence_v3.json`). Running them would dirty the lane worktree — forbidden to the verifier. Per the battery, verified via committed receipts instead:
  - `lanes/FIX_R6/go_tool_v3_test_evidence.json`: `checks_total=105 checks_passed=105`, 0 failing rows, `tool_sha256_v3 = f196c76540f180ffd9f6c6442a393d0082f6088e56aaf5fc987517614b5ecd8e` **== sha256 of the current `record_owner_go.py` bytes on disk** (recomputed) → the 105/105 binds the exact v3 bytes that would gate a GO. `live_head=eb820842…` is an ancestor of HEAD (merge-base exit 0) — tool bytes unchanged since. **PASS (evidence-verified)**
  - `lanes/FIX_R6/controller_executor_rerun_at_addendum.json`: 102/102, 0 case failures, `executor_sha256 7afb635c…` **== current `execute_post_go.py` sha256** (recomputed); `git diff --stat f0117a2e HEAD -- …/execute_post_go.py` EMPTY → executor bytes unchanged since the §R5.3 anchor. Receipt committed in-tree (clean tree ⇒ disk == HEAD blob). **PASS (evidence-verified)**
  - §R5.3 addendum `lanes/FREEZE_ERRATUM_R5/CONTROLLER_ADDENDUM.md`: disk == HEAD blob; second step anchors `EXECUTOR_COMMIT_SHA_R5 = f0117a2e0bb2f0c0d66387e1aed0612f04926b1f` (prior step f3c48c08 preserved verbatim), go-tool pinned `f196c765…` == current bytes. **PASS**

**NFL overall: PASS — GO_READY (readiness label only; see §4).**

## 2. LANE WNBA-PLAYERFEAT-SCORED-V1

### A1 — final source read (`…/WNBA-PLAYERFEAT-SCORED-V1/runner/record_owner_go.py`, 34,595 B, disk == HEAD)
- Exit map 0/1/2/10–16/70; argparse flags `--cycle --phrase --registry --worktree --execute --repo-root` (599–611). NO `--a7-series-dir`/`--a7-verdict` (only removal prose at 33/82/426/584); no env/config channel (grep hits are law prose at 84/215). `--repo-root` only selects the checkout whose `research/governance` is imported read-only for the C7 write — it cannot select an A7 verdict or series dir. **PASS**
- `series_dir_from_row()` (213–223): `os.path.join(row["integration_worktree"], "lanes")` — derived, never selected. **PASS**
- C5 exit 14 (335–370): realpath-equality binding + live head. **PASS**
- Anti-smuggle (226–292, 429–441): lanes symlink, entry symlink/non-dir/outside-lanes, verdict symlink/outside-worktree — all fail-closed exit 15; highest-N mandatory (291). **PASS**

### A2 — old-A7 attack replayed (A7_R5 old verdict bytes from the real committed `lanes/A7_R5/A7_R5_VERDICT.md`, sha256 `390c1b8f…8f6`)
```
... --a7-series-dir /tmp/verify_triple/a2_wnba/alt_lanes
→ exit 2 "error: unrecognized arguments: --a7-series-dir …"; registry copy byte-identical
```
**PASS**

### A3 — worktree relocation
```
→ exit 14 "[C5] WORKTREE-NOT-BOUND-TO-REGISTRY-ROW"; registry copy byte-identical
```
**PASS** (exit 14 as claimed).

### A4 — symlink attacks (fixture copy `/tmp/verify_triple/a4_fixture_wnba`, A7_R1 verdict rewritten for the WNBA cycle, ancestry holds)
| Probe | Result |
|---|---|
| Baseline | exit 0, `C6 PASS … series A7_R1 … binding is-ancestor-of-head`, `ALL CHECKS PASS` |
| lanes symlink | exit 15 `A7-SERIES-DIR-SYMLINK` |
| A7_R9 entry symlink | exit 15 `A7-SERIES-ENTRY-SYMLINK` |
| verdict-file symlink | exit 15 `A7-VERDICT-SYMLINK` |

**PASS**

### A5 — default dry-run, REAL registry
```
→ exit 0; C6 PASS series A7_R7 canonical-block PASS audited d8c81abe51559b5f63060ea38a30b0e44cc5428c,
  binding is-ancestor-of-head; "ALL CHECKS PASS"; registry+journal sha256 BEFORE == AFTER
```
**PASS**

### A6 — verdict committed + ancestry
- `HEAD:lanes/A7_R7/A7_R7_VERDICT.md` blob (10,832 B) == disk; canonical block `audited_sha=d8c81abe…`; `merge-base --is-ancestor d8c81abe… HEAD` exit 0; addendum line 41 `## ADDENDUM VERDICT: CONFIRMED_PASS`. **PASS**

### A7 — suites: BOTH RE-RUN BY VERIFIER (cwd=/tmp; receipts go to `~/.my-quantitative-data/…` sandboxes, worktree untouched — status re-checked clean after)
- `lanes/FIX_R4/test_record_owner_go_v3.py`: **exit 0, "GO-TOOL V3 MATRIX: 13 cases PASS, 0 FAIL · REAL registry byte-identical: True"**, including CASE B: "frozen v2 accepted the old verdict (exit 0), v3 refuses (argparse exit 2) before any write" and CASE L FIX_R3 compatibility. **PASS 13/13 (re-run)**
- `lanes/EXEC/test_runner_gates.py`: **exit 0, "GATE MATRIX: 13 case-groups PASS, 0 FAIL"** (incl. case k real-registry refusal at G1). **PASS 13/13 (re-run)**
- Real registry sha256 after both runs: `5eca4e0d…` unchanged; WNBA worktree still 0 dirty.

**WNBA overall: PASS — GO_READY (readiness label only; see §4).**

## 3. LANE NBA-WINPROB-NG-SCORED-V1

### B1 — registry row == measured; plan identity; ROOT registration commits
- Row: head `ee4fc0b5…`, branch, worktree, budget 0/9, plan `plans/PLAN_nba_winprob_ng_scored_v1.md`, go_phrase `GO NBA WINPROB NG SCORED V1 PROSPECTIVE` REGISTERED_NOT_CONSUMED. **PASS**
- Worktree clean at that HEAD. **PASS**
- `sha256` ROOT plan == worktree plan == `56a91dfd45dabdea3cd2fcbdc450195b5accd9cf5aa9ca36a394b944f3e3bf45`. **PASS**
- ROOT commits exist: `c795a292` (plan, +155 lines) and `5c60f880` (registry row, ACTIVE_LIGHT 0/9, "NOT a typed GO"). **PASS**

### B2 — independent freeze re-measure (§4 of `SUCCESSOR_PACKET_SCORED.md` vs FREEZE_MANIFEST.json vs my recomputation of live files)
| Artifact | Packet §4 pin | My recomputed sha256 (live file) | FREEZE manifest | Verdict |
|---|---|---|---|---|
| `~/.my-quantitative-data/nba-hoopr-v1/raw/_download_provenance.tsv` | `6bf3e729…ec66` | `6bf3e729…ec66` | same | PASS |
| `lanes/A_DATA/GAME_UNIVERSE_SPEC_NBA_2016PLUS.md` | `b9ee812c…2194` | `b9ee812c…2194` | same | PASS |
| `lanes/A_DATA/PIT_AUDIT_NBA.md` | `33d18311…970d` | `33d18311…970d` | same | PASS |
| `lanes/B_MECHANISMS/MECHANISMS_NBA_NG.md` | `9acee28d…bec2` | `9acee28d…bec2` | same | PASS |
Additionally all three md blobs re-hashed from `git cat-file blob HEAD:…` == disk. `RE_MEASUREMENT_PHASE0.md` states "RE_MEASUREMENT: ALL-MATCH". **PASS**

### B3 — evidence committed at HEAD + ancestry
- `git ls-tree -r HEAD -- research/control/NBA-WINPROB-NG-SCORED-V1/`: FREEZE/ (manifest+packet+RE_MEASUREMENT), SYNTH/ (report+synth_results+selection_ledger), DRYRUN/ (report+dryrun_result+sandbox/prediction_book_SANDBOX.jsonl), PIT/PIT_RECHECK.md, A7_R1/ (verdict+audit_a7.py+evidence/), harness/, handoffs/, state.json, event_log.jsonl — ALL present at HEAD. **PASS**
- `git merge-base --is-ancestor 50135f6177e011f52193aa71856fca7b71155bb7 HEAD` → exit 0; A7_R1 verdict canonical block `audited_sha=50135f61…`, "VERDICT: A7_R1_PASS (7/7 gates PASS, 0 unresolved HIGH/CRITICAL)". **PASS**
- Content spot-checks: SYNTH 5/5 PASS (no_lookahead / dst_boundary / fold_force_flat / tolerate_holes / designed_null); DRYRUN `dry_run_verdict=PASS`, rows 2710, arms `['B0','B1_STAR','NB-H1'..'NC-H4']` (10); book recomputed by me: 2710 rows, 2710 distinct (arm,fold,game) tuples, 0 `written_at >= tip` violations, all game_ids in the 99* synthetic namespace (incl. boundary marker `992022000B`); checks `book_laws PASS / real_ledger_absent PASS / zero_scored_cells_real PASS`; PIT re-adopted (3× PIT_PASS-conditional, spread UNVERIFIED_PIT diagnostic-only with **0 refs in harness** — my grep confirms, availability NOT_RUN_PIT slot 7 empty). **PASS**

### B4 — negative scans
- (i) `playerfeat|player_feat` in the cycle control tree: 2 hits, both FREEZE ban statements (no usage). spread fields in harness: 0 hits. `scored|outcome` mentions in harness: only law statements/synthetic machinery ("ZERO scored cells on real outcomes", synthetic corpora consumed by runners). Real data paths in harness: 0 hits. **PASS**
- (ii) B1* constants verbatim: FREEZE_PACKET lines 77/85/88 (`K=32, HCA=100, γ=0.75 … never re-tuned`); `harness/arms.py:17-19` `K = 32 / HCA = 100.0 / GAMMA = 0.75`. **PASS**
- (iii) arms table (FREEZE_PACKET §4): B0+B1* committed; NB-H1..H4 candidates with rights-conditional H4; slot 7 H-C3 "NOT_RUN_PIT — slot stays empty"; slots 8–9 "RELEASED (pre-look rule) never reallocated". Matches state.json arms block. **PASS**

### B5 — no GO typed
- `grep -c OWNER_GO_RECORDED plans/CYCLE_REGISTRY.events.jsonl` → **0**. Our three cycles appear only as CYCLE_REGISTERED/CYCLE_UPDATED. No `--execute` receipt of record_owner_go anywhere in the three control trees (OWNER_GO_TYPED_LIVE mentions are tool source/law prose/state definitions only; state.json phase = PRELAUNCH_READY_PENDING_OWNER_GO on all three). **PASS**

**NBA overall: PASS — GO_READY (readiness label only; see §4).**

## 4. Cross-cutting (C)

| Check | Command | Result | Verdict |
|---|---|---|---|
| cycle list rows | `researchctl.py cycle list` | three rows with expected heads/branches, ACTIVE_LIGHT 0/9 | PASS |
| doctor | `researchctl.py cycle doctor --json` (exit 0) | 81 findings; **0 findings reference our three cycles except 1 LOW `STALE_HEARTBEAT` (NFL, label only, "paused/planned cycles are expected-stale")**; the 14 HIGH are all `FROZEN_ARTIFACT_DRIFT` for legacy `PAUSE_CRYPTO_V17` — none mention our cycles | PASS |
| locks | `researchctl.py locks inspect` | `FREE_PROVEN`, flock free | PASS |
| ROOT tracked tree | `git status --porcelain` | 0 tracked-dirty lines; only `?? .my-quantitative-data/` untracked (foreign data dir) | PASS |
| Closing snapshot | re-hash + status at end of session | registry `5eca4e0d…` and journal `b7870e27…` unchanged from first measurement; all three worktrees 0 dirty at expected HEADs | PASS |

## 5. NOT_RUN items (with reasons)

1. **NFL FIX_R6 + FIX_R5 executor suite physical re-runs: NOT_RUN** — the suites hard-write receipts inside the lane worktree (`test_record_owner_go_v3.py:810`, `test_executor_gates_v3.py:220`); running them would modify a lane worktree, which the verifier must never do. Compensating evidence (the battery's prescribed fallback): committed receipts verified in full — 105/105 with `tool_sha256_v3` equal to the current tool bytes; 102/102 with `executor_sha256` equal to the current executor bytes and empty diff `f0117a2e..HEAD` on the executor.
2. WNBA suites WERE re-run (their receipts go to `~/.my-quantitative-data` sandboxes, worktree untouched) — no NOT_RUN.
3. No other NOT_RUN.

## 6. Observations (non-blocking)

- `go_tool_v3_test_evidence.json.live_head` is `eb820842…` (pre-A7_R7/§R5.3); this is an ancestor of HEAD and the tool bytes are unchanged since (sha equality), so the 105/105 binds the current gate.
- WNBA's `--repo-root` flag selects the governance import root for the C7 write path only; it cannot steer A7 discovery (C6 is row-derived) and is documented as a test seam. Dry-run never imports it.
- Dry-run book rows include game_id `992022000B` (10 rows) — inside the 99* synthetic namespace (boundary marker "B"); a stricter `990*` prefix check would be a verifier artifact, not a law violation.
- Pre-existing gitignored `__pycache__` dirs exist in the NFL recorder / WNBA runner dirs from the lanes' own runs; verifier probes ran with `PYTHONDONTWRITEBYTECODE=1`.

## 7. GO_READY judgments

**GO_READY is a readiness label, NOT a command to run scored, and NOT a GO.**
The owner's typed GO phrase, typed verbatim at each cycle's own gate, remains the ONLY
trigger; the tool records it, it never types it. All three lanes recorded GO_READY here:

| Lane | Overall | Old-A7 attack | Gates failed / NOT_RUN | GO_READY |
|---|---|---|---|---|
| NFL-WINPROB-NG-SCORED-V1 | PASS | DEAD — argparse exit 2 pre-read (verifier replayed it; registry byte-identical) | physical suite re-run NOT_RUN (worktree-dirtying; receipts verified per battery fallback) | **GO_READY** |
| WNBA-PLAYERFEAT-SCORED-V1 | PASS | DEAD — argparse exit 2 pre-read (verifier replayed it) + CASE B in re-run suite proves v2 accepted / v3 refuses | none (suites re-run 13/13 + 13/13 by verifier) | **GO_READY** |
| NBA-WINPROB-NG-SCORED-V1 | PASS | n/a (different cycle family; its own gates: freeze ALL-MATCH, dry-run quarantined 0 scored, A7_R1 PASS) | none | **GO_READY** |

All three cycles remain `REGISTERED_NOT_CONSUMED`, budget 0/9, zero scored cells anywhere.
