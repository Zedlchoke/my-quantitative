# V13 A7 Prelaunch Audit — CRYPTO-V13 Phase Q

- Auditor: A7 (independent; audit artifacts only, no repairs)
- Date: 2026-09-04
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v13/q-a7-prelaunch`
- Branch: `orca/v13-q-a7-prelaunch` @ `5037ea8b8ef27f67ca6d5afbc649bb27012955ed` (W1 freeze record; W1 code freeze = `c0d0673`)
- Method: every check recomputed fresh by A7; missing evidence is NOT_RUN/UNAVAILABLE_FAIL_CLOSED, never inferred PASS.

## VERDICT: `V13_S0_LAUNCH_AUTHORIZED`

10/10 items PASS on substance. Findings: **1 MEDIUM, 2 LOW, 1 OBSERVATION — zero unresolved HIGH/CRITICAL.** Scored execution remains gated by the owner-typed `GO V13 SCORED EXECUTION` and a fresh E0 probe on the final execution seat.

---

## Item results (recomputed)

### 1. AUTHORITY CHAIN — PASS
Read `PLAN_crypto_v13.md` (main worktree) and `research/control/v13_run/run_contract.json` side by side.
- Budget 0/9 ✓ (contract: eligible 9, computed_published 0).
- 5 allowed terminal outcomes identical to PLAN §2 ✓.
- Section 1.1 shadow rule: all 5 entry conditions present in contract, `binding: true` ✓.
- Hard boundaries: contract's 6 match PLAN §15 (+ ILLIQ re-open clause per §2) ✓.
- Release wording: exact literal `GO V13 SCORED EXECUTION`, owner-typed only ✓.
- PLAN blob pinned in contract verified: `b6d9790:PLAN_crypto_v13.md` = `b8b7e834...` = blob at current main HEAD (content unchanged since bootstrap).

### 2. V12 ANCHORS — PASS
- `git rev-parse origin/orca/v12-integration` = `b1529e1925ecb195920ac9f38c5b819db409218d` ✓.
- `git show b1529e1:research/control/v12_run/state.json`: `V12_REJECT_ALL`, budget **6/9**, denominators **131/134**, S1 `SEALED_UNTOUCHED`, workers **0** ✓.
- `git show b1529e1:research/audits/v12r/a7_terminal/a7_terminal_v12.json`: verdict `V12_TERMINAL_APPROVED_0_FAIL`, **8/8 items PASS** ✓.

### 3. V13-R RECONCILIATION — PASS
- Local `orca/v12-integration` = `b1529e1` = origin ✓.
- `git rev-list --merges 474d811..b1529e1` = **0** (14 linear non-merge commits) → fast-forward-only confirmed ✓. Reconciliation recorded at integration commit `ada8f21`.

### 4. FUSION ADOPTION PROVENANCE — PASS (with precision note)
- **11 cherry-picks verified independently**: matched each commit by subject against the frozen-core history of `c6a0576e` (228 commits). Full map (incl. `047c685→1df5ec4` … `c6a0576e→8b4d718`) equals the P0 gate's `cherry_pick_map` 11/11.
- **Byte identity**: `git diff c6a0576e..orca/v13-integration -- research/data_fusion tests/data_fusion` is NOT literally empty — it contains exactly **two added files** (`research/data_fusion/crypto_compat.py` +392, `tests/data_fusion/test_crypto_compat.py` +284 insertions, **0 deletions**). Diff excluding those two designed compat files = **0 bytes**; diff restricted to the 46 frozen core paths = **0 bytes**. The frozen core tree is byte-identical; the compat layer is the adoption proof PLAN §6 P0 requires. P0 gate verdict PASS, `adoption_failure_clause` NOT INVOKED.
- **Tests re-run by A7**: `pytest tests/data_fusion -q` → **227 passed**, exit 0. `pytest tests/data_fusion/test_crypto_compat.py -q` → **23 passed**, exit 0 (includes the decision-time pin: a decision at T never reads `available_time_utc > T`).

### 5. P-GATES — PASS
- `P0_FUSION_ADOPTION.json` verdict PASS (9/9 sub-gates). `P2_DATA_AUTHORITY_REPLAY.json` overall PASS (90/90 hashes, tails 20/20, S1 guard 0 violations, ILLIQ remains BLOCKED_DATA).
- Re-ran `tests/test_v13p_accounting_regression.py` → **7 passed**, exit 0.
- `v13_p_freeze.json` exists (`no_pnl_computed: true`, 5 pinned digests). **Spot-checked 4 of 5 with `shasum -a 256` — all match** (`p1_freeze` 31e0c30a…, `selection_freeze` 0b3b0865…, `data_manifest` bb8d4387…, `w12r_freeze` 10d928f1…).

### 6. SELECTION — PASS (finding F1)
- `selection_freeze_v13.json`: **A13-V13-A8-OITD** + **A13-V13-A5-LIQEPIS** (3 arms each, 6 cells); 4 rejections with reasons.
- Cross-checked every cluster rho against the A7-N matrix (`git show f71307f:research/audits/v13d/a7n_novelty_v13.json`, 52-stamp mean Spearman): EXITCAP~OITD **+0.974621**; LIQEPIS~LIQPRO **+1.0** (exact duplicate, opposite books); CAPVEL inverse **−0.914543 / −0.937082**; TCH **+0.648974**; cross-cluster |rho| 0.0929–0.2337; max shadow rho **0.1467 ≤ 0.20**. All match the freeze record.
- No rejected proposal implemented: no EXITCAP/CAPVEL/LIQPRO/TCH code under `research/v13/` or `tests/` (packets only under `research/proposals/v13/`).
- Exactly **2** family modules: `research/v13/families/{oitd,liqepis}` ✓.
- **F1 (MEDIUM)**: the D2 audit artifacts live only on local lane branches (see findings).

### 7. IMPLEMENTATION EVIDENCE — PASS (finding F2)
- Re-ran the 9 named files: **116 passed in 35.88s, exit 0** — not the 123 the checklist expected. `pytest --co` proves the 9 files contain exactly **116** tests (77 OITD + 39 LIQEPIS); 116 + 7 (P1 regression) = 123 explains the figure. No failing/skipped/missing test (see F2).
- **No scored metric anywhere**: dry-run publication is guarded by `require_temporary_ledger` (OITD reuses the frozen V12 guard at `research/v12/families/oilev_v2/audits.py:853`; LIQEPIS has its own at `families/liqepis/audits.py:525`) which refuses any ledger not named `dryrun_*.jsonl` and explicitly refuses `results/registry` paths. Dry-run ledgers are `/tmp/v13i_oitd_dryrun/...` only; metrics are labelled "fixed synthetic constant series; not strategy PnL" with `real_pnl: false`; no scored-metric fields in plugin modules; evidence tests assert the refusal behaviour.

### 8. W1 FREEZE — PASS (finding F4)
- **6/6 arm digests recomputed by import** (`FROZEN_ARM_CONFIG_DIGESTS`, `LIQEPIS_ARM_CONFIG_DIGESTS`) — all equal `w13_freeze.json`; **pairwise unique** (6 distinct values).
- **Twins**: `e-exec-1` and `r-reproduce` both detached HEAD = `c0d0673`, porcelain **0 lines** both.
- **Ledger seed**: `results/registry/experiments_v13.jsonl` sha256 = `e3b0c442…b855` (empty) in **both** twins.
- **Staging**: recomputed all **90/90** files of `research/audits/v12p/a3_staging_manifest.json` against `staged_data/` in **both** twins — bytes+sha256 OK=90, BAD=0, MISSING=0 per twin; files read-only; `staged_data/staged_manifest_.json` sha256 = `f855ad9c…c3c40` in **both** twins.
- **LIQEPIS pin closure**: disclosed in `w13_freeze.json` (`DROP_ONE_PIN`: dropped side 5@1/10, untouched side 6@1/12); present byte-identically in lane commit `c7892ca` (13:14:07Z) and in W1 `c0d0673` (14:02:33Z); freeze record `5037ea8` at 14:13:24Z — closure **precedes W1**, and zero scored metrics existed (none exist now). Note: `c7892ca` is the lane head cherry-picked into W1, hence not a git ancestor of `c0d0673`; provenance established by identical pin content + timeline.

### 9. BOUNDARIES — PASS (finding F3)
- Budget **0/9**; counters `v13_published 0 / v13_observed 0`; phase `V13_Q_W1_FROZEN`; historical 131/134 preserved separately.
- **Zero scored V13 rows anywhere**: twins' registries empty (`e3b0c442`); no canonical `experiments_v13.jsonl` exists in any tree (absent in q-a7-prelaunch, integration, root).
- **S1**: `SEALED_UNTOUCHED`; P2 guard 0 violations; all S1 references in v13_run control are seals/guards or the terminal-outcome name — no access path.
- **Deployment**: none. **Workers**: `ps` scan finds no scoring processes; owned_workers 0.
- **Integration worktree**: porcelain 0 lines. **Root**: porcelain exactly `?? .v2c/`; main HEAD is `50e0207` ≠ `b6d9790` — two post-bootstrap owner-cycle Forex commits, unrelated to V13, PLAN blob unchanged (see F3).

### 10. RESOURCES — PASS
- Live A7 measurement: MacBookAir10,1, Apple M1, 8 CPU, 8.00 GB RAM total, ≈2.0 GB available during audit (load 5.59 — audit's own test runs), disk 45 Gi free.
- **Cap=1 arithmetic confirmed from recorded intake values**: 45% free of 8.0 GB = 3.6 GB → `min(3, floor((3.6−1.5)/2.0)) = 1` = recorded `measured_safe_cap 1`.
- A probe at this audit moment would read cap 0 = STOP — which is precisely why the binding precondition stands: **a fresh E0 probe on the final execution seat precedes any scored run** (w13_freeze `host_resources`, run_contract phase order, strong-host default seat, staging-transfer artifact if the seat differs).

---

## Findings

| ID | Severity | Summary | Disposition |
|----|----------|---------|-------------|
| F1 | **MEDIUM** | D2 audit artifacts (`a7n_novelty_v13.json` @ f71307f, `a9f_feasibility_v13.json` @ 2f47f0f) are absent from the integration/W1/twin trees; `worktree_manifest.json` labels both lanes "INTEGRATED" although neither commit is an ancestor of `orca/v13-integration`; reachable only from local lane branches (no remote; L-V11-5 strand risk). Content independently verified consistent (item 6); the integrated selection freeze carries the full rho summary and cites both lane commits. | Non-blocking. **Condition for terminal closeout:** integrate both artifacts (or a pointer-verification artifact) into the branch, correct the manifest labels, keep the D2 lane branches. Scored execution under GO does not depend on these files. |
| F2 | LOW | Implementation suite observed **116 passed** vs 123 expected; collection proves the 9 files contain exactly 116 tests, all passing (116+7 P1 = 123 explains the figure). No failing/missing test. | Non-blocking; record correct per-suite counts at the next freeze artifact. |
| F3 | OBSERVATION | Main advanced `b6d9790 → 50e0207` post-bootstrap via 2 owner-cycle Forex commits (9e0d9a1, 50e0207); unrelated to V13; PLAN blob unchanged; root porcelain `?? .v2c/` as recorded. | No V13 boundary implicated; recorded. |
| F4 | LOW | `w13_freeze.json` `generated_utc` 13:05:00Z predates the lane commit (13:14:07Z) and W1 (14:02:33Z) it describes; git DAG order authoritative; material ordering verified (closure → W1 → freeze record; zero scored metrics). | Non-blocking metadata issue (same pattern as V12 OBS-1 clock-skew precedent). |

## Launch conditions (standing, per PLAN/contract — not new)
1. Owner types `GO V13 SCORED EXECUTION` (this audit is not scored-execution authority).
2. Fresh E0 probe on the chosen execution seat precedes any scored run; staging-transfer artifact if the seat differs.
3. F1 terminal-closeout condition (integrate D2 audit artifacts; correct manifest labels).

## Coverage statement
353 tests freshly re-run by A7 (116 implementation + 227+23 fusion + 7 P1 regression), 0 failures; full-suite 1966/1 skipped NOT re-run (A1-recorded at 327s). All digests, twins, staging (90/90 × 2), arm identities, counters, S1, workers and boundaries recomputed by A7 with the commands shown in `a7_prelaunch_v13.json`.
