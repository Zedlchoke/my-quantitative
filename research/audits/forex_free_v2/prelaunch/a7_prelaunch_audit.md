# A7 PRELAUNCH AUDIT — FOREX-FREE-V2

- Role: A7-PRELAUNCH, independent prelaunch auditor (audit-only lane; no repairs performed)
- Measured UTC: 2026-09-04T06:12:42Z
- Base audited: integration `orca/forex-free-v2-integration` @ `968665b2d21860c3707f5e2b8b7e69eb76ad7220`
- W2 (code freeze): `a68764d8f1501b27d07840de6a8fce11ec8eaa5b`
- Twins: `e-exec-1` and `r-reproduce`, both detached exactly at W2
- Method: every claim re-measured against the trees (git + sha256 replay + test execution + independent dry-runs). No report trusted without recomputation.

## VERDICT: FOREX_FREE_V2_S0_LAUNCH_AUTHORIZED

Zero unresolved HIGH/CRITICAL findings; zero blockers. This authorizes nothing by itself: scoring stays HARD-STOPPED until the owner explicitly says **"GO FOREX V2 SCORED EXECUTION"**. A7 is the last independent gate before that owner checkpoint.

## C1 PIN CHAIN — PASS

- `w2_freeze.json` `FOREX_FREE_V2_W2` == `a68764d8...` == both twins' detached HEAD.
- Recomputed sha256 of all 9 `code_hashes` + 6 `spec_hashes` (15 files) against both twins' working trees: **15/15 each, 0 mismatch**; re-verified against W2 git blobs (`git show W2:path`) in both twins: **15/15 each**.
- `selection_freeze.json` selected-proposal digests (A4-P1 `e9878d43...`, A4-P2 `93e940a9...`) match the working-tree proposal files (covered by the spec_hashes replay); selection_freeze self-digest `2e5b7fa2...` verified.

## C2 STAGED MANIFEST REPLAY — PASS

- Re-hashed **all 173 entries** in each twin's `staged_data_manifest.json`: **173/173 match, 0 mismatch, 0 missing, in BOTH twins** (346 files total). Manifests byte-identical across twins.
- Composition: 152 `data_raw` + 4 `forex_free_v1_run` control files = 156 snapshot files; 17 v2 control/spec files.
- The 156 snapshot digests are **exactly** the V1 `staged_data_manifest.json` `digests_exec2` entries (identical key set both directions, identical values) in both twins; V1 `digests_repro2 == digests_exec2` also holds.
- Twins tracked-clean: `git status --porcelain` shows only the two staged untracked files per twin; unchanged after all dry-runs.

## C3 RUNNER INTEGRITY (no sidecar) — PASS

- `research/assets/forex_free_v2/scored_runner.py` imports the REAL modules: `family1`, `family2`, `accounting`, `td_loader`. `FAMILIES = {"family1": family1, "family2": family2}`.
- `compute_cell` calls `fam.compute_arm_schedule(arm, rows_by_pair, cost_tier=tier)`; both modules define it (`family1.py:584`, `family2.py:509`).
- All trades booked through `accounting.PositionBook` (open/close, cost once per side); dry-run zeroes `_pnl` only.
- Identity suite run alone in e-exec-1 (pgrep resource rule observed): **17 passed in 0.35s**.

## C4 PUBLICATION GATING — PASS

- `publish_cell` refuses: missing authorization (`LAUNCH_AUTHORIZATION_MISSING`), wrong W2 sha (`W2_SHA_MISMATCH`), dummy records (`REAL_PNL_REQUIRED_FOR_SCORED_PUBLICATION`).
- Once-only per content digest under `fcntl.flock`; replay returns `(0, 0)`; parallel writers serialize. All four behaviors covered by tests.
- `exec_driver` dummy mode never calls `publish_cell`.
- **No V2 scored ledger exists anywhere** under `.worktrees/forex-free-v2/`. Only prior-cycle V1 artifacts exist (tracked `research/control/forex_free_v1_run/scored_ledger_published.jsonl`, 6 rows, closed V1 cycle; and an untracked V1 dry-run data artifact under `data_raw/forex_free_v1/dryrun/`).

## C5 FROZEN-BEFORE-OUTCOME — PASS

- Freeze chain in history: `26e247d` (10:39+07) selection frozen + USD-leg drift gates frozen outcome-blind → `a68764d` (12:39) W2 runner code with frozen gate constants → `a034683` (12:40) `w2_freeze.json` → `968665b` (12:54) twins staged. **No scored cell exists (C4), so no outcome exists; all gates pre-date any possible outcome.**
- All 17 `frozen_gates` values in `w2_freeze.json` match the runner constants exactly: expectancy>0, PF≥1.10, ≥2 positive populated folds, populated fold PF≥0.80, fold-populated ≥30 trades, MDD≤2500 USD, fold share ≤0.50, pair share ≤0.40, stress PF≥1.00, dropout 5/7, neighbour>0, placebo reject PF 1.10, USD |corr|≤0.30, USD diag ≥60 days, Sun 21:00 → Fri 16:00 New York entry gate, folds 2020-03-01 / 2022-05-01 / 2024-07-01 / 2026-09-02, purge 14d.
- `selection_freeze.json` recorded the USD-leg D1/D2/D3 drift diagnostics **at selection time, before W2 code existed and before any outcome**; implemented as `usd_drift_corr` + `USD_DRIFT_EXPLAINS_ANCHOR`.

## C6 INDEPENDENT DUMMY DRY-RUN — PASS

- r-reproduce → `a7_dryrun_report_r-reproduce.json`; e-exec-1 → `a7_dryrun_report_e-exec-1.json` (both in this lane).
- Each: `mode=dummy`, `scored=false`, `real_pnl=false`, **8 cells**.
- Recursive scan of every pnl-named field in every cell of both reports: **all zero (placeholder)** — no outcome information.
- All 8 cells fail Stage-A as designed; `gates==True` nowhere; publication never invoked (dummy path has no publish call).
- Twins remained tracked-clean afterwards.

## C7 SCHEDULE/FREQUENCY SANITY — PASS

- family1: caps structural (1 entry/pair/UTC-day; ≤3 RT/pair/week, governor-enforced), realized 0.73/0.80/1.15 RT/pair/week; floors met (93/pair/fold ≥ 80; 371/pair ≥ 300; fold trades ≥ 400; 1708 ≥ 1200 full).
- family2: caps held (binding pair-weeks 572), realized 1.69/1.87/2.25 RT/pair/week; minimums PASS (min pair decisions 1659 ≥ 500; 4053 trades ≥ 1800).
- Agreement with A9-F independent sims: family1 1708==1708 entries, 2767 vs 2768 decisions, 0.73 vs 0.72 RT, 85==85 cap-weeks, 9==9 dropped signals (one-trade fold-attribution boundary difference, disclosed in the lane report); family2 572 vs 571 binding weeks, 1.6853 vs 1.70 RT.
- Both lane reports attest schedule-only counts, no real-data PnL.

## C8 BOUNDARIES — PASS

- Cycle diff `bee64be..968665b`: 49 files, all `forex_free_v2` research/tests/control/audits/proposals + the two pre-cycle PLAN docs. **0 S1/forex_run paths**; added-line content scan shows only permitted V1 module/manifest references (td_loader reuse).
- No credentials/api keys/secrets; the only token-like literal is `AUTHORIZATION_TOKEN = "GO FOREX V2 SCORED EXECUTION"` (owner launch phrase = publication gate, not a secret).
- `git ls-files | grep data_raw` in integration: **empty**.
- Workers: only IDE helpers; no pytest/exec_driver/backtest processes besides this audit's own runs.
- No origin/*forex-free-v2* branches (never pushed); no merge commits in the cycle (18 linear commits).
- Main untouched: tip `b6d9790`/`e5afbbe`/`5d25d06` are owner commits; `968665b` and W2 are NOT ancestors of main; root tree clean except `?? .v2c/`.

## C9 A1 INCIDENT — PASS

- `event_log.jsonl` line 8 `A1_INCIDENT_MISCHERRY_PICK_REMEDIATED`: three proposal commits (f29e723, 6438a84, 3a038a4) cherry-picked onto MAIN by a cwd error, stacked on owner tip 047c685; remediated by `git reset --hard 047c685`; reflog-provenanced; preventive `git -C <abs-path>` rule recorded.
- No residue: none of the three commits is an ancestor of main; `047c685` IS an ancestor of main; main tip is owner-owned.

## FINDINGS

- **O1 (LOW)**: Prior-cycle V1 scored ledgers exist as tracked files in every worktree — immutable evidence of the closed V1 cycle, not V2 outcomes. No action.
- **O2 (LOW)**: family1 lane parity shows a one-trade fold-attribution boundary difference vs A9-F (499/575/634 vs 499/574/635; 2767 vs 2768) and a differing early_forced_flat event definition (15 vs 70). Disclosed in the lane report; counts-level, not a gate; non-material.

HIGH/CRITICAL findings: **none**. Blockers: **none**.

## COUNTS

| Metric | Value |
|---|---|
| Frozen digests replayed (working tree + W2 blobs, both twins) | 60 |
| Staged manifest entries independently re-hashed | 346 (173 × 2 twins), 0 mismatch |
| Runner identity tests | 17 passed / 0 failed |
| Dummy dry-run cells | 8 + 8, all placeholder-pnl, publication never invoked |
| Cycle commits examined | 18 (linear, 0 merges) |

## ATTESTATION

audit-only; no repairs; no scored PnL computed. All dry-run pnl values are placeholder zeros; no outcome was revealed, computed or recorded anywhere; all writes confined to the q-a7-prelaunch lane.

Scoring precondition remains: owner must explicitly issue **"GO FOREX V2 SCORED EXECUTION"** before the first scored cell.
