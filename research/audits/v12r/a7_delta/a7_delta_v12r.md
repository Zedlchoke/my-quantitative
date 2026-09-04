# A7 Delta Audit — V12R (independent, audit-only)

- Auditor: A7 (independent prelaunch delta auditor). No production file touched; only this `a7_delta` folder written.
- Worktree: `C:\Users\ROYAL\my-quantitative\.worktrees\crypto\v12\a7-v12r`, detached at `ccfd33e3ed302de642e1ebdecb8adb6830dba887` (W12R candidate), `git status --porcelain` empty before audit.
- W12 frozen: `f0799cae6fc47846937cf1a370719314696ee990`. Full measured evidence with commands/exit codes: `a7_delta_v12r.json` (same folder).

## Result: 9/9 items PASS, zero unresolved findings

| # | Item | Result | Key measured evidence |
|---|------|--------|------------------------|
| 1 | Six-arm identity | PASS | 6/6 `arm_config_digest`s recomputed (adapter_v10 imported first) exactly match `selection_freeze.json` |
| 2 | No strategy mutation | PASS | `f0799cae..ccfd33e`: strategy surface (`research/v12/**`, `research/adapter_v10/**`, `research/v11/families/**`) byte-identical (empty diff); lane adds exactly the 2 driver files (906+501 lines) on `39118b3` |
| 3 | Cost/fold/ledger accounting | PASS | Matrix = `derive_family_stress_matrix` over frozen folds + `freeze_family_cell_contract`; scored metrics from baseline cell only (`cells[0].name=="baseline"` enforced); cells via frozen `run_strategy`; cost model only read, never overridden; `publish_v12_cell` receives `family_contract_cells` |
| 4 | First-publish & replay | PASS | Sole ledger writer `research.v12.accounting.publish_v12_cell`; gate order replay → family-contract guard → pre-score finite → position evidence; CELL_RESULT published_delta=1, refusal one OBSERVATION observed_delta=1, replay adds no row/zero deltas; `pytest tests/test_v12r_driver.py -q` = **14 passed**, worktree still clean (tests use tmp_path only) |
| 5 | No lookahead | PASS | OILEV features strictly-before-stamp (V11 PIT primitives); BAB daily blocks break on any bar closing after the decision; one declared execution lag both families; chronological F0/F1/F2 with purge (OILEV 1 stamp; BAB force-flat by construction); runner refuses cross-fold holding and purge-gap entry; driver adds no feature/clock/universe logic |
| 6 | No S1 / network | PASS | Zero network imports in driver+tests ("binance" = local staged dir label only); single docstring mention "no S1 access" is a prohibition, zero S1 paths/usages |
| 7 | Exec/repro isolation | PASS | Both trees detached at `ccfd33e…`, status clean (staged_data/results gitignored); `--publish --repro` rejected fail-closed (exit 2); repro returns before any ledger import, writes `repro_report.json` under repro tree `results/`; exec ledger `experiments_v12.jsonl` = 0 bytes, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 8 | Staging 90/90 | PASS | 90/90 files sha256+bytes exact vs `a3_staging_manifest.json` in BOTH exec and repro trees; `staged_manifest_.json` sha256 = `f855ad9c778f7a8695d6416b1c912efd7ddc353bf70935669504016cbf3c3c40` in both; shipped files dict == a3 files dict; no extra disk files |
| 9 | No V11 hardwiring | PASS | Driver's only direct V11 import: `research.v11.publication_identity.arm_config_digest`; `research.v11.families.oilever_delev.strategy` reached only transitively via frozen oilev modules (Bar et al.); no W11 pin; `--arm` validated against frozen V12 modules + freeze JSON |

## Also checked
`state.json` / `heartbeat.json`: budget **0/9**, denominators **125 published / 128 observed**, `s1_seal: SEALED_UNTOUCHED`, scored_cells 0, clock NOT_STARTED; exec ledger empty (no CELL_RESULT/OBSERVATION rows exist anywhere).

## Verdict

**A7_DELTA_VERDICT: V12R_LAUNCH_AUTHORIZED**

All 9 audit items PASS with zero unresolved findings. Scored cells remain forbidden until A1 executes under the W12R freeze with the exactly-once `publish_v12_cell` gate; any digest, staging, isolation or ledger invariant change invalidates this verdict.

---

# Delta Re-audit — W12R2 (follow-up after OILEV TECHABORT)

Trigger: the OILEV family chain attempt-1 crashed at W12R (`ccfd33e`) with `TypeError: can only concatenate str (not bytes) to str` in the driver's `_series_digest` Mapping branch — BEFORE the preflight artifact and BEFORE any scored metric existed (TECHABORT forensic: `research/control/v12_run/TECHABORT_oilev_chain_attempt1.json`, main repo). A1 froze **W12R2 = `ce52e3e2e817806c984b3e2cdda9daace17440f7`** (driver-only fix, lane `8e0a877`) + one regression test. All evidence re-verified independently (main repo read-only; full detail in the `delta_reaudit` section of `a7_delta_v12r.json`).

| # | Item | Result | Key measured evidence |
|---|------|--------|------------------------|
| 1 | W12R1→W12R2 diff | PASS | Code changes are EXACTLY `run_v12_cell.py` (+3/-1) and `tests/test_v12r_driver.py` (+14); other changes are control metadata/gates/`w12r_freeze.json` and this audit's own integrated outputs; science surface (`research/v12/**`, `research/adapter_v10/**`, `research/v11/families/**`, `research/v11/publication_identity.py`, `contracts/**`, `selection_freeze.json`, `ledger_package/**`) has an EMPTY diff |
| 2 | `_series_digest` fix | PASS | Single hunk: `.encode()` moved outside the `f"{sym}|" + "\|".join(...)` concatenation; Bar-like branch untouched; symbols and row fields still iterated sorted (key-order-independent, deterministic); adds `test_series_digest_mapping_branch_regression` |
| 3 | TECHABORT vs exec tree | PASS | Exec tree still at `ccfd33e`, clean; `results/v12r_phase_e` contains ONLY `bab_lowbeta/` + `ledger_bab_lowbeta.jsonl`; `ledger_oilev_v2.jsonl` ABSENT, `oilev_v2/` dir ABSENT (preflight never written); BAB ledger = exactly **3 CELL_RESULT rows** (BAB-90D-W, BAB-DOWNCORR-90D-W, BAB-90D-W-INV, all producer head `ccfd33e`, validated by the frozen `read_v12_ledger`: 3 published / 0 observed); canonical registry still empty (`e3b0c442…`, 0 bytes) |
| 4 | Driver tests at W12R2 | PASS | Main-repo working tree lane files identical to `ce52e3e` (verified by empty diff); `python -m pytest tests/test_v12r_driver.py -q` → **15 passed** (exit 0), main repo git status still clean (cache provider disabled to keep the read-only tree byte-clean) |

Notes: the 3 BAB rows were published at producer head `ccfd33e` (W12R1) before the OILEV defect was hit; science bytes are identical `ccfd33e..ce52e3e`, so those rows remain valid under W12R2. Zero budget was consumed by the TECHABORT (no scored metric ever existed for OILEV).

## Delta verdict

**A7_DELTA2_VERDICT: V12R2_LAUNCH_AUTHORIZED**

