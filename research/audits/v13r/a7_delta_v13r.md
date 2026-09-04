# V13R A7 DELTA AUDIT — CRYPTO-V13

**Verdict: `V13R_LAUNCH_AUTHORIZED`** — all seven items PASS on independent recomputation; zero unresolved HIGH/CRITICAL.
Scope: independent DELTA audit before the first scored cell (V12R precedent). Audit artifacts only; no repair; no push; no merge; main untouched.
Worktree `/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v13/r-a7-delta`, branch `orca/v13-r-a7-delta`, clean at `4c217b0`. W1 = `c0d0673`, W1R = `bcb2853`.

## 1. DELTA SCOPE — PASS

`git diff c0d0673..bcb2853 --stat`: the two deltas contribute exactly
`research/control/v13_run/tools/run_v13_cell.py` + `tests/test_v13r_driver.py` (0253754, driver-only) and
`research/v13/families/oitd/plugin.py` + driver-test pin updates (bcb2853). **The only science-surface path in the entire range is `oitd/plugin.py`.**
The range is non-linear: Q-phase control-plane records (`event_log.jsonl`, `heartbeat.json`, `state.json`, `w13_freeze.json`, `worktree_manifest.json`) and the four pre-sanctioned D2 audit artifacts (`research/audits/v13d/a7n_novelty_v13.{json,md}`, `a9f_feasibility_v13.{json,md}` — cherry-picked at f73cb7b, disclosed in the authorization context as "metadata-only, W1 c0d0673 unchanged") sit between the science freeze and the deltas. Audit-plane, not science.

**Hunk-by-hunk plugin review**: docstring (traversal semantics); additive read-only imports `FAMILY_ID`, `STATUS_OK` from the unchanged strategy module; one additive reason code `REASON_CARRIED_FLAT_START`; one flat-start helper (zero legs, status OK, `carried_forward=true`); behavior change only — blanket refusal at non-retained stamps replaced by carry (byte-equal prior retained book, or flat start) for ON-schedule non-retained stamps, while OFF-schedule stamps still refuse fail-closed. **No frozen identity/parameter/schedule/cost/signal constant changed** — `oitd/strategy.py` and `liqepis/**` are byte-unchanged since c0d0673 (verified by diff).

**V12 pattern comparison** (`research/adapter_v10/runner.py`, `research/v12/families/oilev_v2/plugin.py`): the frozen runner queries `targets_at` at every non-final schedule instant (`_collect_books`) and itself marks fold-unclaimed instants `ACTION_PURGE_GAP_CARRY` (target=prior; `PURGE_GAP_ENTRY_FORBIDDEN` refuses any purge-gap target != prior); carried books become `ACTION_CARRY` (target=prior). V12's plugin answers every query by recomputing (dead book at purged stamps, discarded by the runner). V13's chained hysteresis cannot compute off-chain, so it returns the byte-equal prior book — semantically inert to the runner and strictly stronger than V12 (no signal computed at purged stamps). Plugin `decision_instants()` ≡ runner `declared_members` (same post-purge folds, same dropped-fold logic), so every non-retained queried instant is exactly a runner gap instant.

## 2. DIGESTS — PASS

All six recomputed from frozen identity via `research.v11.publication_identity.arm_config_digest`: OITD 3/3 and LIQEPIS 3/3 (`frozen_arm_digest_report()` all-match). Pairwise unique **6/6**. Values equal `w13_freeze.json` exactly (string + key-set). `w13r_freeze.json` restates the three OITD 8-char prefixes under `digest_impact: NONE` (corroborated; drift impossible — both digest input modules byte-unchanged since c0d0673). See F-1 (LOW).

## 3. TESTS — PASS (recomputed)

| Suite | Expected | Observed |
|---|---|---|
| tests/test_v13r_driver.py | 35 | **35** |
| tests/test_v13i_oitd_*.py (6 files) | 77 | **77** |
| LIQEPIS | 39 | **39** |
| tests/data_fusion | 227 | **227** |
| tests/test_v13p_accounting_regression.py | 7 | **7** |

`git diff c0d0673..bcb2853 -- 'tests/test_v13i_oitd_*'` is **empty (0 bytes)** — zero test modifications. The bcb2853 driver-test changes are pin upgrades only, and they add fail-closed pins: off-schedule still refuses; final purged Monday carries; purged Mondays carry byte-equal; drop-one-fold F0 carries; **mutation at a purged stamp leaves the carried book unchanged / mutation at a decision stamp moves the book** (bidirectional falsification of "no signal at purged stamps"); fail-closed still fires at decision stamps. No guard weakened.

## 4. DRIVER STRUCTURE — PASS (read + live fire-drills)

`research/control/v13_run/tools/run_v13_cell.py`:
- **(a)** Preflight fail-closed BEFORE any metric: arm-frozen check → `--publish` head pin (before data load) → staged 90/90 per-file sha256 vs `research/audits/v12p/a3_staging_manifest.json` with `staged_manifest_.json == f855ad9c…c3c40` → ALL-SIX digest equality vs `w13_freeze.json` → plugin load → frozen runner-traversal pin (all 6 cells incl. drop_one_fold). Every failure exits 2 before `compute_cell`; `preflight.json` records `no_scored_metric_yet: true`.
- **(b)** Publication only through frozen `research.v12.accounting.publish_v12_cell`, gated on `--publish` (requires `--ledger` + `--expect-head`), to the per-family shard ledger; the canonical `results/registry/experiments_v13.jsonl` is never a write target.
- **(c)** Exit codes: 0 ok/preflight-only/published/idempotent-replay/repro-match; 1 crash; 2 fail-closed (no metric); 4 honest refusal (budget consumed); 6 repro mismatch.
- **(d)** `--repro`: `--publish` forbidden by `validate_args` (ledger branch unreachable); writes only cell artifacts to its own out-root; requires `--compare-with`; returns 0/6.
- **(e)** No network, no S1: stdlib imports only; `subprocess` solely for local `git rev-parse HEAD`; S1 appears only in the no-access docstring.

Live drills from this worktree: `--preflight-only` OITD-28D → exit 0 (90/90 f855ad9c, digest match, traversal pin ok, cells_probed = baseline/fee_slippage_x1_5/plus_2_ticks/plus_1_event_delay/drop_one_symbol/drop_one_fold); LIQEPIS-28D → exit 0; negative drill (wrong manifest expectation) → **exit 2** with no data loaded, no metric computed.

## 5. TWINS — PASS

`e-exec-1` and `r-reproduce`: both **detached at `bcb2853`**, porcelain **0**, staged_data **0 writable files**, staged **90/90** vs the a3 authority with `staged_manifest_.json == f855ad9c778f7a8695d6416b1c912efd7ddc353bf70935669504016cbf3c3c40` (verified with the driver's own `verify_staged_snapshot`). Both `results/` trees hold exactly the same 5 seed files, byte-identical across twins; `registry/experiments_v13.jsonl` = **e3b0c442…b855** (empty seed). No `results/v13_phase_e/` under either twin.

## 6. BOUNDARIES — PASS

Budget **0/9** (state.json `computed_published=0`; w13 and w13r agree). **Zero scored metric artifacts anywhere** — no `v13_phase_e` directory exists under any v13 worktree. S1 `SEALED_UNTOUCHED`; delta files reference S1 only in guards. `owned_workers=0` (state.json; w13r e0_probe workers=0 cap=1; no live V13 process on host at audit time). Main untouched by this audit (no push/merge; main's tip `50e0207` is the owner's pre-existing next-cycle Forex V3 plan on a diverged line).

## 7. SCIENCE MERIT OF THE CARRY SEMANTIC — PASS

The frozen proposal (`research/proposals/v13/a8/OITD.json`) pins F0/F1/F2 with a 1-day purge imported unchanged from the frozen V12 fold contract, force-flat at fold boundaries, and a hysteresis book (enter on tercile entry, exit only beyond the median). Purged stamps are non-decisions by the proposal's own semantics — the book held there is by construction the inherited fold-interior book. The delta makes `targets_at` answer the mandatory frozen-runner query with exactly that inherited book instead of refusing: no decision changes, no signal is created, and the binding gap semantics remain the runner's (`PURGE_GAP_CARRY` target=prior; `PURGE_GAP_ENTRY_FORBIDDEN`). Positions still open only at retained stamps with fully applied fills inside a fold; the final force-flat boundary is unchanged (the runner refuses FORCE_FLAT at open instants; the plugin answers OK with the carried book).

**Drop-one-fold F0 carried-flat case cannot create a position out of nothing**: with F0 dropped there is no prior retained decision, so the plugin returns the explicit flat start (zero legs, status OK). The runner at those gap instants carries `current={}` (prior==target), and even hypothetically off-gap `ACTION_CARRY` sets target=prior — never the proposal. "No signal at purged stamps" is verified structurally (`compute_targets_at` runs only over retained stamps in the replay loop) and by the new bidirectional mutation tests. Fail-closed at retained decision stamps and at off-schedule stamps is preserved.

## FINDINGS (zero HIGH/CRITICAL)

- **F-1 (LOW)** — `w13r_freeze.json` restates only the 3 OITD digest prefixes (`digest_impact: NONE`), not the full 6-digest table. Canonical table lives in `w13_freeze.json` (verified 6/6 exact here); drift impossible (digest input modules byte-unchanged since c0d0673). Documentation compactness only; no condition.
- **F-2 (INFO)** — `heartbeat.json` stale (pre-GO phase, integration_head 1e11cd9) while `state.json`/`event_log` are current and consistent; event-log stamps non-monotonic vs append order. Cosmetic; `state.json` authoritative.
- **F-3 (INFO)** — Owner GO recorded as a Vietnamese paraphrase with an explicit form disclosure; the referenced binding precondition (A7 V13_S0_LAUNCH_AUTHORIZED, 10/10 PASS) was issued. Accepted per audit mandate.

## VERDICT

**`V13R_LAUNCH_AUTHORIZED`** — the W1R freeze (`bcb2853`) is faithful to its claims: science surface = traversal semantics only, identity and digests unchanged 6/6, driver fail-closed and publication-safe, twins byte-clean at the frozen staged snapshot, budget 0/9, seals intact. Cleared to proceed to the first scored cell under the recorded execution plan (serial, cap=1, OITD chain then LIQEPIS chain).
