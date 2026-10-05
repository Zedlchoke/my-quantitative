# DRY-RUN REPORT — lane S_SYNTH · WNBA-PLAYERFEAT-SCORED-V1

Date of record: 2026-10-05 · seed 20261005 · interpreter
`/Users/hoangminhlong/my-quantitative/.venv/bin/python` (only) · worktree
`.worktrees/wnba-playerfeat-scored-v1/integration` · branch
`orca/wnba-playerfeat-scored-v1-integration` · dispatch_sha =
actual_start_sha = `5a1d0618e344844303d282923979cd949768368e` · no git commands
run · NOTHING REAL WAS SCORED: every scored row in this lane is synthetic
(`SYNTH_`-prefixed ids, seasons 2027–2030); the real OOS window [2020..2026] was
never read and no real-game value appears in any output.

Frozen inputs consumed as-is (no modification, bytes pinned and asserted):
- B0 constant `p_home = 0.603755` (T_SELECT report §3).
- B1-WNBA frozen config `K=32, HCA=50, γ=0.65` (T_SELECT report §4).
- Frozen tree: `lanes/T_SELECT/harness.py` sha256
  `b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e`,
  `lanes/T_SELECT/arms.py` sha256
  `82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3` — asserted
  at the top of every rehearsal run (`dryrun.py` refuses to start on drift).

## 1. Frozen selftest re-run (Task 1)

```
$ cd lanes/T_SELECT && /Users/hoangminhlong/my-quantitative/.venv/bin/python harness.py --selftest
SELFTEST PASS (all 14 checks) ... SELFTEST 14/14 PASS
EXIT=0
```

14/14 PASS, exit code 0 — the frozen tree is green as-of-freeze (incl.
`feature_table_sha256_vs_manifest`, `elo_update_hand_computed`,
`designed_null_byte_identity_3_synthetic_streams`,
`evaluate_oos_refuses_real_without_go_token`).

## 2. Synthetic OOS-like rehearsal (Task 2)

Driver: `lanes/S_SYNTH/dryrun.py` (imports the frozen `harness`/`arms` as-is).
It generates a deterministic synthetic corpus in the REAL corpus formats, reads
it back from disk, and runs the FULL 2-arm evaluation path on it.

```
$ cd lanes/S_SYNTH && /Users/hoangminhlong/.venv/bin/python dryrun.py \
    --out ~/.my-quantitative-data/wnba-playerfeat-scored-v1/sandbox/rehearsal_run1
REHEARSAL ok: scored=112 (seasons [2029, 2030]) warmup=56 | B0 LL 0.696354 |
B1 LL 0.661815 | dLL -0.034538 [-0.082936, 0.011913] | slope 1.0974 |
null_ok=True fixture_ok=True     EXIT=0
```

Synthetic corpus (corpus-format files in
`sandbox/rehearsal_run1/synth_corpus/`, written then re-read from disk):
- ESPN-like schedule CSVs (per season) + feature-table-format PARQUET (2 rows
  per game, real corpus column names incl. `b5_minutes_hhi`, `c_absence_share`,
  neutral-reason columns, `is_team_game1` v2 continuity rows).
- Warm-up analog seasons **2027, 2028** (56 games, stream-only, no feature rows
  — mirror of the warm-up law); scored OOS-like seasons **2029, 2030**
  (112 games, 56/season); min season 2027 ≥ 2027 law; ALL ids `SYNTH_`-prefixed;
  pairwise-distinct ids (loader asserts); 4 neutral-site rows (HCA=0 path);
  2 exact-tip doubleheaders per date (tip-batching + 28 tip-date clusters).
- Feature-neutral paths exercised on scored folds: flags `neutral_hca0` = 4,
  `neutral_x0` = 55 (rows with neutral feature reasons → x=0).

Both arms on the IDENTICAL full stream, scored folds = seasons {2029, 2030}:

| fold | arm | n | mean LL | Brier | reliability | slope |
|---|---|---|---|---|---|---|
| 2029 | B0 | 56 | 0.670033 | 0.238532 | 0.0000115 | nan (constant predictor — honest nan per frozen law) |
| 2029 | B1-WNBA | 56 | 0.662611 | 0.235358 | 0.010250 | 0.7759 |
| 2030 | B0 | 56 | 0.722675 | 0.264471 | 0.014790 | nan |
| 2030 | B1-WNBA | 56 | 0.661020 | 0.232595 | 0.049370 | 1.3210 |
| pooled | B0 | 112 | 0.696354 | 0.251501 | 0.003494 | nan |
| pooled | B1-WNBA | 112 | 0.661815 | 0.233977 | 0.021338 | 1.0974 (band [0.85,1.15] ✓) |

- Identical-game-set law: arm game-id sequences equal element-wise (scored and
  full stream); arm rows equal row-wise on (tip, season, outcome, neutral). PASS.
- Exact-arm record ids pairwise distinct within each arm (112/112 unique). PASS.
- Non-vacuous: 112 scored rows ≥ 1. PASS.
- Designed null on synthetic: φ=0 (with frozen `harness.make_x_fn` over real
  synthetic moments) and c≡1 both reproduce the frozen-B1 `p_home` stream
  **bit-for-bit** (float64 hex equality, 168 rows). PASS.
- Warm-up law: scored folds contain exactly the 112 scored-corpus rows, seasons
  {2029, 2030} only; warm-up rows (2027–28) never scored. PASS.

Hand-computed fixture cross-check (`fixtures/expected_hand_fixture.json`,
derived independently with pure math from the frozen engine-law text — no
`arms` import — then run through the SAME frozen engine by `dryrun.py`):
3-game fixture (update law, zero-sum away expectation, γ-state carry, same-tip
snapshot sharing, fresh-team entry): per-game p_home, per-game LL, per-game
Brier, both arms' mean LL/Brier, and all 3 paired ΔLL values match to
**1e-12** (14/14 checks ok). Tip-batch no-leak proven on the fixture: flipping
an outcome inside a tip batch leaves every `p_home` in the stream byte-identical
(`fixtures/hand_fixture_predictions.csv`).

Paired ΔLL + bootstrap machinery smoke (synthetic): ΔLL = LL(B1) − LL(B0),
paired per game, clusters = tip UTC date (28 clusters),
`arms.date_cluster_bootstrap_ci(..., n_resamples=10000, seed=20261005)`:
point −0.034538 [−0.082936, +0.011913]; fixed-seed rerun identical (True).
This is a machinery smoke-run on synthetic data — no real-data claim.

Internal metric-code consistency: the driver's Brier decomposition satisfies the
exact identity `BS = spread_p + REL − RES + UNC − 2·cov_uv` on every fold
(all-true in `rehearsal.json`).

## 3. OOS lock proofs (Task 3)

Probe driver: `lanes/S_SYNTH/lock_probe.py` → all PASS, exit 0; evidence
`sandbox/lock_probes/probe_results.json` (sha256
`d70f2b91d272c1cf2804a4e65bc0adbeb9604f009d37a36ed12f17a9b395bd08`).

- **A. Pre-read refusal with REAL corpora present** (in-process, frozen
  `harness.main()`): `--mode evaluate-oos --source real` →
  `OOS-GATE-REFUSED` Abort, with a `sys.addaudithook` watching
  `open`/`os.listdir`/`os.scandir`/`os.stat` on ALL real data roots
  (`playerfeat-prep-v1/wnba/features`, `wnba-prep-v1/roster_audit` (53 entries,
  present), `wnba-v1/raw/espn_schedules`, `wnba-v1/raw/wnba_stats_schedules`,
  `wnba-playerfeat-scored-v1/selection`): **0 real-data read events observed at
  refusal time** — the gate fires before any byte of real data is touched.
- **B. CLI, default source (=real)**: exit 1, `OOS-GATE-REFUSED` on stderr. PASS.
- **C. CLI, explicit `--source real`**: exit 1, `OOS-GATE-REFUSED` on stderr. PASS.
- **D. Fabricated tokens rejected**:
  - D1 token FILE path passed as `--go-token` → `OOS-GATE-REFUSED` (a path
    string is not the phrase). The fake token file
    `sandbox/fake_go_token.txt` was fabricated by this lane solely to prove
    rejection.
  - D2 `--go-token-file` → argparse `unrecognized arguments`, exit 2 — the
    frozen CLI has NO file-based token input, so a token file is invalid by
    construction.
  - D3 wrong-case phrase → `OOS-GATE-REFUSED` (exact-match equality only).
  - D4 even the exact registered phrase only opens the gate CHECK; the frozen
    tree then refuses execution: "real-data OOS execution lives POST-GO" —
    real scoring is structurally impossible pre-GO.
  - D5 control: `--source synthetic` stays allowed pre-gate (exit 0).

**Token validation law (per `plans/PLAN_wnba_playerfeat_scored_v1.md`)**: the
phrase `GO WNBA PLAYERFEAT SCORED V1 EVALUATION` is REGISTERED, never typed,
pre-gate. Post-GO unlock (exactly): (1) the owner types the phrase verbatim at
this cycle's own gate (post-A7); (2) in that owner-authorized session the
operator runs the frozen harness as `harness.py --mode evaluate-oos --source
real --go-token '<owner-typed phrase>'` with the phrase passed INLINE from the
owner-typed value — never read from a file, never stored in a script, log,
prompt or git object; (3) no token file can ever unlock (no file-based token
input exists; a path string never equals the phrase); (4) altered/case-mutated
phrases fail exact-match; (5) passing the exact phrase opens only the gate
check — the post-GO execution lane itself is separate, unbuilt code.

## 4. Determinism (Task 4)

Full rehearsal double-run into independent sandbox dirs:

```
dryrun.py --out sandbox/rehearsal_run1   EXIT=0
dryrun.py --out sandbox/rehearsal_run2   EXIT=0
diff -r rehearsal_run1 rehearsal_run2    → BYTE-IDENTICAL (no output, all 10 files)
```

sha256 (run1 == run2 for every file): rehearsal.json
`51a513b78f7b2905720ce7624634da52d4485386f640c741dbf85a4e04b8f73a`,
predictions_b0_scored.csv `9c5fe001…`, predictions_b1_scored.csv `01abf9c2…`,
hand_fixture_predictions.csv `3291a6c2…`, plus all 6 corpus files (parquet CSVs
identical; full list in the handoff). The bootstrap is fixed-seed deterministic
(verified twice in-run), and the OOS-lock probes are deterministic
refusals.

## 5. Outputs and scope

- Lane writes: `lanes/S_SYNTH/{dryrun.py, lock_probe.py, DRYRUN_REPORT.md,
  VERDICT_TABLE.md, fixtures/{expected_hand_fixture.json,
  hand_fixture_predictions.csv}}` + this handoff. `lanes/T_SELECT` untouched
  (shas re-verified unchanged).
- Sandbox writes:
  `~/.my-quantitative-data/wnba-playerfeat-scored-v1/sandbox/{rehearsal_run1/,
  rehearsal_run2/, lock_probes/, fake_go_token.txt}`.
- Known limitations: (1) synthetic-only — the frozen harness `evaluate-oos
  --source synthetic` path is a rehearsal-shape stub, so the full path runs in
  this lane's driver through the same frozen engine/metrics/bootstrap functions
  with frozen B0/B1 constants; the synthetic loaders mirror (not reuse) the
  real-corpus loaders, which are hardwired to real paths + the ≤2018 cap law
  (incl. `harness.compute_moments`; the driver recomputes synthetic moments
  with the identical population-sd formula). (2) The synthetic corpus is a
  machinery fixture: B1-vs-B0 numbers on it are evidence that the machinery
  runs and tracks planted signal (rating-vs-strength corr 0.89), not a
  performance claim. (3) B0's calibration slope is the honest frozen nan
  (constant predictor). (4) No real OOS season read anywhere in this lane.

## VERDICT: DRYRUN_PASS — prelaunch dry-run green on synthetic streams; OOS lock holding.
