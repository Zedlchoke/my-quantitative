# A7 PRELAUNCH AUDIT — FOREX-FREE-V3 (V3-Q)

- Auditor: A7 (independent). Audit only; no code or data repaired.
- Date (UTC): 2026-09-04T18:16:38Z
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3/q-a7-prelaunch`
- Branch: `orca/forex-free-v3-q-a7-prelaunch`, HEAD at audit start `c9d653639d24d85ca4478cae7770e032fc5c63b3`, porcelain empty.
- Audited freeze: `FOREX_FREE_V3_W3 = 9d961103018719de51433321feb846ed274ab604`

## VERDICT: FOREX_FREE_V3_S0_LAUNCH_BLOCKED

Rule: AUTHORIZED requires all checks PASS and zero unresolved HIGH/CRITICAL. Checks 1–6 PASS; check 7 (gate review) FAIL with 3 HIGH blockers (H1, H2, H3) + 1 MEDIUM + 1 LOW. Phase E stays locked; A1 remains stopped before the first scored cell.

## Per-check results

| # | Check | Result |
|---|-------|--------|
| 1 | Pin/twin integrity + byte-identity | PASS |
| 2 | Dummy dry-run independently rerun | PASS (deterministic) |
| 3 | Zero real scored artifacts, budget 0/6 | PASS |
| 4 | Chain recomputation + control-file hashes | PASS |
| 5 | Seven code hashes vs both twin trees | PASS (7/7 both) |
| 6 | Resource probe | PASS |
| 7 | Frozen Stage-A gate review | FAIL (H1, H2, H3, M1, L1) |

### 1. Pin/twin integrity — PASS
- Both twins detached at exactly W3, clean trees: e-exec-1 and r-reproduce `git rev-parse HEAD = 9d961103...`.
- Price: recomputed all **156/156** digests (`staged_data_manifest.json` `digests_exec2`, cross-checked against `digests_repro2`) in **both** twins — 0 missing, 0 mismatch.
- Macro: JSON path verified as `w3_freeze.json → data_freeze.macro_vintages.file_sha256` (9 entries: 8 area files + fetch_manifest.json). Recomputed sha256 in **both** twins: **9/9 match each**.

### 2. Dummy dry-run — PASS (deterministic across trees)
Rerun by the auditor in its own tree (code from q-a7-prelaunch, data paths from the e-exec-1 twin), `freeze_token=None`, all six arms via `compute_cell`:

| arm | record_id | decisions | kept | scored/real_pnl/published | == freeze |
|---|---|---|---|---|---|
| family1:anchor | family1:anchor:tier1.0 | 312 | 271 | F/F/F | YES |
| family1:neighbour | family1:neighbour:tier1.0 | 302 | 263 | F/F/F | YES |
| family1:causal_negative_control | family1:causal_negative_control:tier1.0 | 154 | 138 | F/F/F | YES |
| family2:anchor | family2:anchor:tier1.0 | 138 | 113 | F/F/F | YES |
| family2:neighbour | family2:neighbour:tier1.0 | 344 | 289 | F/F/F | YES |
| family2:causal_negative_control | family2:causal_negative_control:tier1.0 | 145 | 119 | F/F/F | YES |

All 6 record_ids pairwise unique and **exactly** equal to `w3_freeze.json six_arm_dummy_dry_run.arms` (decision/kept counts match too).

### 3. Zero real scored artifacts — PASS
No `scored_ledger_published.jsonl` anywhere under `research/control/forex_free_v3_run/` (ledgers exist only for V1/V2, historical). `state.json` budget 0/6 computed, 0 published; denominators 0/0; event log records `ledger_authority: empty`.

### 4. Chain recomputation — PASS
`cafd78e (wave)` is-ancestor-of `236dcda (selection)` is-ancestor-of `9d9611 (W3)` is-ancestor-of audit HEAD — all via `git merge-base --is-ancestor`. Recomputed sha256 (working tree byte-identical to committed bytes):
- forbidden_family_inventory.json `6aefd43230a73b6e14af95da959eed0c8784d8a1d3869edb3e14d7846b60ef09`
- baseline_invariants.json `14a6fab602e0c68ae2aa2e31d07c2f5278e3f8f5c88372d55a2afd9d3d99b646`
- (also recorded: selection_freeze `16518b87…`, w3_freeze `fc2211a0…`, state `88e90881…`, run_contract `7f445e3a…`)

### 5. Code hashes — PASS
All seven `w3_freeze.json code_hashes` recomputed against **both twin trees**: 7/7 match in e-exec-1 and 7/7 in r-reproduce.

### 6. Resource probe — PASS
8 logical cores (4 performance), 8 GB RAM (memory_pressure 47% free), 42 GiB disk free. Matches the frozen resource contract; exec driver runs scored arms strictly serially; per-arm timeout 60 min frozen.

### 7. Gate review — FAIL (blockers)
All frozen gate constants in `scored_runner.py` match `baseline_invariants.json` exactly (expectancy/PF/folds/MDD 2500/shares 0.5+0.4/stress PF 1.0/dropout 5/purge 14d/clock/one-event-lag/force-flat/session gate). Financing gate implemented (stricter than baseline: fires at price-only expectancy <= 0). Timeout implemented fail-closed (TECHABORT). Mechanism sanity enforced by the driver.

**Blockers:**

- **H1 (HIGH) — incremental-alpha Stage-A gate is dead code for both selected families.** `scored_runner.py:540-542` fires `INCREMENTAL_ALPHA_NOT_POSITIVE` only `if alpha is not None`; alpha comes only from `meta.incremental_alpha` (`:509`). `family1.py` meta (L487-508) and `family2.py` meta (L672-735) never supply it; nothing in the repo computes it; no handoff discloses a deferral. PLAN §12 and `baseline_invariants.json v3_benchmark_treatment` freeze this gate as mandatory ("positive raw PnL never overrides failed incremental alpha"). As frozen, a cell could become a Stage-A survivor without the cycle's central incremental-information test ever running.
- **H2 (HIGH) — USD-drift diagnostic gate is dead for both selected families.** `scored_runner.py:478` consumes `meta.usd_index_daily_returns`; absent/None ⇒ `evaluated=False` ⇒ gate cannot fire. `family1.py` omits the key entirely (no disclosure); `family2.py:730` supplies `None` with a note deferring to "scoring integration", and `handoffs/i_family2.json` says "A7 scoring integration must supply it … at scoring time" — but no injection point exists in frozen code (driver passes family meta verbatim; runner reads meta only). Supplying it requires editing frozen files, which invalidates all seven verified W3 code hashes and forces a re-freeze. No such lane exists between S0 and Phase E.
- **H3 (HIGH) — dummy dry-run records leak real outcome information.** `compute_cell` dry-run zeroes only the four top-level book columns (`scored_runner.py:514-519`) but `stress` is booked from REAL specs (`:479-481` via `accounting.book_stress`) and `break_even_cost_bps` (`:503`) uses never-zeroed `_gross_move_pnl`. Measured by auditor on `family2:causal_negative_control` with `freeze_token=None`: record says `scored=False, real_pnl=False` yet carries stress tier1.0 `total_pnl=-644.1209630929` (expectancy −5.8029, PF 0.9300), tier1.5 `−810.62`, tier2.0 `−977.12`, `break_even_cost_bps=-1.401446`. This contradicts the module's own "no scored metric may leave this module" (L513) and the driver's "Reveals no outcome". The recorded W3 artifact stored only counts (no leak persisted), but PLAN §10 mandates this dry-run pre-authorization ("into a temporary ledger") — its records reveal arm profitability direction, contaminating outcome-blindness.
- **M1 (MEDIUM) — drop-one FOLD survival not implemented.** Baseline `v3_sample_floors` and PLAN §12 require "drop-one pair and fold survival"; runner computes drop-one over PAIRS only (`:473-476`) and gates only `DROP_ONE_PAIR_SURVIVAL_INSUFFICIENT`.
- **L1 (LOW) — timeout thread cannot be killed.** `call_family_arm` raises TechAbort fail-closed on expiry but the daemon worker keeps running (results discarded); residual CPU/RAM use only.

## Blocker disposition

Phase E must not start. Resolution requires a code delta (supply `incremental_alpha` per the frozen benchmark treatment, supply `usd_index_daily_returns` per the frozen D1 formula, zero/omit `stress`+`break_even` in dry-run records, optionally add fold drop-one) followed by a **re-freeze** (all seven code hashes change) and an A7 delta re-audit — or an explicit owner-accepted, recorded gate decision. Until then the owner conditional GO (event_log 2026-09-04T13:33:09Z) does not release: prelaunch did not return AUTHORIZED.
