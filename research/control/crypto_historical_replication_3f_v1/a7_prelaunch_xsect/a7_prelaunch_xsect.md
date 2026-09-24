# A7 Prelaunch Audit — XSECT-FUND-CARRY-7D (CHR3F) — REFUSED

- Schema: `chr3f_a7_prelaunch@1`
- Audit UTC: 2026-09-23T21:05:00Z
- Root HEAD measured: `d7c9d2d345b3b4e8b54bd1ccb6d79ae3f3d78b19`
- Machine verdict artifact: `a7_prelaunch_xsect.json` (same dir)
- Verdict: **REFUSED** — 7/8 checks PASS, check 5 (scored-invocation conformance) FAIL, one blocking finding. Budget untouched: 0/24 scored cells; no scored cell has run.

## Why REFUSED (one blocking finding, B1)

The planned scored invocation wires `funding_data/scan_2026 -> ../funding_data_scan/scan_2026`
into the frozen kernel. Those bundles **cannot feed the frozen code**:

- Each `<SYM>/funding.json` carries `{captured_at, symbol, rows}`.
- The frozen loader `research/funding_pit.py::load_funding_bundle` (required by the frozen
  kernel `research/funding_carry.py`) demands `{requested_start_ms, requested_end_ms, rows}`
  and raises `ValueError` otherwise.
- Reproduced with the exact recovered bytes (`recovered/v6_root`):
  - `load_funding_bundle(scan_dir, "ETHUSDT")` → `ValueError: missing audit metadata:
    ['requested_end_ms', 'requested_start_ms']`;
  - `compute_target_weights_funding_carry(...)` → `SKIP_INCOMPLETE / funding_panel_incomplete`
    for the whole cross-section → **every scored cell would be vacuous**;
  - `research/portfolio_engine._load_funding_settlements(...)` → the same `ValueError`
    **uncaught at engine init** → cell abort.
- `staging/funding/<SYM>_funding.json` (`{symbol, window, n, rows}`) is equally incompatible.

Gate 2 (DR2) could not catch this: the synthetic-panel engine bypasses the funding-bundle
path entirely. The real funding data path has never been exercised end-to-end. No disclosed
converter or regeneration step exists in the cycle dir or the plan. Launching as packeted
would either crash every cell or tempt an undisclosed data-plane mutation at launch time —
both are audit failures.

**Remediation path (for the controller, not for me to execute):** regenerate the bundles via
the frozen `research/download_funding.py::write_funding_history` format; re-verify row
equality against staging; run ONE real-data-path dry-run arm (no `--synthetic-panel`)
proving non-vacuous signal (kernel `status OK`, non-zero settlements) and zero denominator
delta; re-dispatch A7 on the changed surface.

## What passed (all independently recomputed, no verdict file trusted)

1. **Identity/provenance gate — PASS.** `git diff fbd2e9d..HEAD -- research/funding_carry.py
   research/matrix_runner.py` empty at three observed HEADs; candidate.yaml silent since
   closure (last change `574214a1`, ancestor of closure); status.yaml pinned to `5b1415e7`
   (closure-land descendant), zero changes since; shadow identity artifact at `41f4f227`
   sha256 = `845c3e87…bcd8` exact; `tests/test_funding_carry.py` 5/5 (+ `test_matrix_runner.py`
   19/19); executor disclosure present in plan §5.
2. **Disclosed-copy integrity — PASS.** Diff vs dry-run copy is exactly the one
   `locked_at_utc: null -> "2026-09-23T10:40:00Z"` hunk; copy sha256 `a3ef0405…cd45d` equals
   the DR2 manifest pin and the frozen/ copy; disclosure note accurate.
3. **Dry-run evidence — PASS.** V6P golden suite re-run: 19/19. DR2 manifest shows
   `--synthetic-panel`; panel is constant-price synthetic; run.log says "golden validation
   only"; registry row marked "synthetic panel; not scored". Dry-run metrics appear nowhere
   outside DR2 artifacts. Registry cycle-local; root `results/` has no CHR3F rows.
4. **Data authority — PASS.** 3 sampled zips (ETH 2021-06, BNB 2022-03, DOGE 2020-11):
   local sha256 == `.CHECKSUM` == live data.binance.vision CHECKSUM. Funding rows exactly
   equal scan↔staging for ETH/BNB/DOGE (4534/4534/4506). Catalog report rows == zip raw data
   rows == on-disk parquet rows (ETH 163,680; BNB 159,808). An initial −24/−23 "gap" was
   root-caused to my own header assumption: 2020/2021 zips have no header line; the builder
   is correct. No widening needed.
6. **Boundaries — PASS.** CHR3F root commits touch only plans/* + root bootstrap records.
   No S1 writes. Shadow/gateway surfaces carry only their own runtime outputs and pre-INC-1
   shadow-dashboard lane work; no CHR3F writes. Scripts write only inside the cycle dir.
   Credential grep clean.
7. **Incidents — PASS.** INC-1 and INC-2 disclosures complete; INC-2 quarantine covers basis
   only; XSECT klines+funding verified complete pre-INC-2 and fold census 0/88 stamps missing
   (fold-4 = Y2020P) re-verified.
8. **Denominators — PASS.** Budget 0/24; no scored artifacts anywhere; only the dry-run
   registry row exists; zero-denominator law respected.

## Non-blocking notes

- N1: launch cwd lacks `research/portfolio_runner.py` + the two symlinks (staging step);
  the runner copy must be byte-identical to the DR2-validated recovered copy.
- N2: root HEAD moved twice during the audit (concurrent other-cycle registry commits);
  identity checks re-verified PASS at each HEAD.
- N3: dry-run hypothesis copy has no `status.yaml`; runner falls back to candidate.yaml
  lock (disclosed in run.log).
- N4: DR2 `dirty_worktree_at_launch=true` (untracked control files), diagnostic-only.
- N5: shadow dashboard-lane mtimes precede CHR3F staging activity; attributed to that lane.

## Bottom line

Do not launch scored cells. The refusal is narrow and fixable: one data-format defect on the
funding plane, empirically proven against the frozen bytes, invisible to the synthetic dry-run.
Everything else — identity, provenance, data authority, boundaries, incidents, denominators —
reproduces clean. A7 re-review is required after the funding-bundle regeneration and a
real-data-path dry-run.
