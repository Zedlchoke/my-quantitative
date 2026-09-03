# STOCKS-FREE-V3 — A7 independent prelaunch audit

- Auditor: A7 (independent, verify-only; nothing repaired)
- Audited HEAD: `a5b3f72715ca921e63ebf74e014bde365934ae18` (branch `orca/stocks-free-v3-q-a7-prelaunch`) — matches the expected identity; every command ran from `/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v3/q-a7-prelaunch` with `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
- W1: `586f9febe29ae6ba0b176c8c9a9b1b4645f3bca4`
- Measured (UTC): 2026-09-03T15:24:53Z
- Authority: PLAN_stocks.md sections 14–16 (this tree)
- Machine-verdict: **`STOCKS_FREE_V3_S0_LAUNCH_AUTHORIZED`** — blockers: none.

All twelve checklist items were recomputed by this auditor from primary evidence, not from A1's claims. Structured results: `q_prelaunch.json` (same directory).

## 1. V2R pin — PASS

`research/control/stocks_free_v2_run/terminal_effective_verdict.json` exists; `effective_sprint_verdict` = `STOCKS_FREE_V1_REJECT_ALL`. Recomputed `sha256(terminal_report.json)` = `76bf2a66473472f40b6489d6d4fd848d3c1b15184123a7cc72408951d8d59ebe` — the V2 science evidence is byte-untouched through V3.

## 2. Counters — PASS

`state.json`, `run_contract.json`, `w1_freeze.json` and `heartbeat.json` all independently record: historical Stocks 6/6, V3 observed/published 0/0, budget 0/6, workers 0, no running cell (`current_cell: null, current_cell_running: false`), `SEALED_UNTOUCHED`, `NO_PAPER_NO_LIVE_NO_ORDERS`. No disagreements.

## 3. Selection — PASS

`selection_freeze.json` pins pool SHA `9a9f5fd5b78e124ff7fd73dcf56557f2ea2b101c`; `git merge-base --is-ancestor 9a9f5fd5 HEAD` holds. The pool at that commit contains exactly 6 proposal files, all present in this tree; both selected `source_proposal` paths exist. The freeze contains exactly 2 families (`SFV3-A5-IDIO-SHOCK-REVERSAL`, `SFV3-A6-TOM-SETTLE`) × 3 arms each (anchor/neighbour/causal control), with adjudications ADJ-1..ADJ-4 recorded.

## 4. W1, detached trees, equal-twin staging — PASS

- `git log --oneline -1 586f9fe` → the freeze commit "STOCKS_FREE_W1 (V3) freeze: …".
- `w1_freeze.json` present at the W1 commit; sha256 identical in the W1 commit, this tree, and e-exec-1 (`847976c571846f3561a786f40032ea91798b6c0aca22f12ce20e986eddd8c5c0`).
- `e-exec-1` and `r-reproduce` both detached at exactly `586f9fe…`; `git status --porcelain=v1` shows zero lines in both (`.staging/` is ignored — the only untracked artifact class, verified via `--ignored=matching` → `!! .staging/`).
- Recomputed sha256 of both `STAGING_MANIFEST.sha256` files = `4bc21789a516c20c41351d340322279c5414ff8df147020cf47525ea7e193f45` in both trees; the two files are byte-identical (diff clean). All **51** staged data files verify (`shasum -a 256 -c`) in **both** trees, 0 failures.
- `MANIFEST.json` recomputed in both trees = `62ac324d7e683961b0d88f85153e4a072d09fe0a6745a54687b9e3b219d8f658` — matches the pin. Spot-checks of three pinned files (`SPY_all_p1.json`, `XLF_all_p1.json`, `XLV_all_p1.json`) all PIN_MATCH.

## 5. Data/S1 isolation — PASS

`research/stocks_free_v3/isolation.py` exists with `S1Seal`/`S0WindowPolicy`/`SealedSnapshotReader`. Live exercise on synthetic inputs (no S1 data read): `denies_date` is False for 2025-07-31 and 2026-08-01, True for 2025-08-01, 2026-01-15, 2026-07-31; `S0WindowPolicy` allows full-S0 windows and denies any window touching ≥ 2025-08-01; path-level denial catches `s1` segments and `s1_` prefixes. `w1_freeze.json` records S1 `SEALED_UNTOUCHED 2025-08-01..2026-07-31`. Battery: `s1_leak_dates: []`, `scored_metrics_computed: 0`, S0 = 1842 sessions 2018-04-04..2025-07-31 through the pin-verified `SealedSnapshotReader`.

## 6. Six-arm identity + idempotence — PASS

Live `build_registry()` → 6 bindings, 6 distinct `trial_identity_digests`, 6 distinct config digests. Every digest byte-matches `w1_freeze.json`'s `arm_trial_identity_digests` and `arm_config_digests` (6/6 + 6/6). Publication idempotence additionally evidenced by battery section C (6 first publications, 6 replay-zero-delta rejections, 0 observed delta, zero-event publication denied).

## 7. Canonical sidecar/harness, costs-once, CASH turnover — PASS (own runs)

From this worktree: `test_factory_attribution_reconcile.py` + `test_factory_valuation.py` + `test_publication_gate.py` + `test_v2_diagnostic_replay.py` → **35 passed**; `test_arm_registry.py` → **6 passed**; `test_isolation.py` → **47 passed**; `test_benchmarks.py` → **21 passed**; `test_incremental.py` → **7 passed**. Total 116 passed, 0 failed.

## 8. Controls falsify beta — PASS

Battery section D: for both benchmark rules (`risk_matched_tom_rule`, `risk_matched_constant_rule`), beta-only alpha = 0.0 (|α| < 1e-12) and timed-edge alpha = +1% (±1e-12). A beta-only book cannot manufacture alpha; a true +1% edge is recovered exactly.

## 9. Schedule-only cost/capacity — PASS

- Selection freeze: A5-IDIO ≤ 5.0x two-way/yr structural budget; TOM-SETTLE exactly 4.80x; both inside the frozen 6.0x ceiling.
- Live re-derivation by this auditor (schedule-only, no PnL): TOM all three arms show exactly 24 transitions and 4.8 one-way turnover sum in complete year 2019, `all_arms_within_gate: true`, ceiling 6.0.
- A5-IDIO stress exercise: the rolling 5/252 budget is enforced (271/233 rejections observed under synthetic shock stress); two-way/yr 4.966/5.093/0.637 — inside the 6.0 ceiling; gross ≤ 0.5 everywhere. A8's real-loader measured values 4.241/4.104/3.967 are comfortably inside both the 5.0 structural budget and the 6.0 ceiling.

## 10. Absence of real V3 scored artifacts — PASS

`research/control/stocks_free_v3_run/` contains 12 control files and **no** cell result files and **no** V3 trial ledger; `state.json.scored_cells = []`; `event_log.jsonl` has exactly 6 events (BOOTSTRAP, P1_FROZEN, SELECTION_FROZEN, I_WIRING_COMMIT, Q_FULL_SUITE_AND_FREEZE, W1_TREES_STAGED) — zero SCORED/PUBLISH events. `results/` holds only artifacts tracked since `dd01cf0` (2026-08-19, predates V3; not a V3 output). Zero V3-related `pytest|nautilus|backtest|cell_runner` processes at every check. One unrelated foreign pytest (crypto/v12 lane, see observations) was on the host — not a V3 process.

## 11. Full suite — PASS (own run)

Pre-run: 0 V3 processes; per the checklist I waited the full 10 minutes for the unrelated foreign pytest to finish (it did not; proceeded per procedure and disclosed below). Own run of `/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest tests -q`: **1743 passed, 4 skipped** in 83.35s — exactly the W1 claim. Tree after the run: `git status --porcelain=v1` → 0 lines (fully clean, before writing the two audit files). The only session writes are the two allowed audit files.

## 12. Resource — PASS

RAM 8 GB (8589934592 B), 8 logical CPUs (Apple M1), disk free 51 Gi. Operative heavy cap **1**, consistently recorded in `w1_freeze`, `run_contract`, `heartbeat`, and `state.json`.

## Non-blocking observations

1. **OBS-1 (LOW)** — A foreign pytest (PID 11686, `tests/test_v12i_bab_*`, cwd `.worktrees/crypto/v12/i-blind-family`) was running at audit start and persisted past the prescribed 10-minute wait and through my full-suite run. It is outside the stocks-free-v3 topology, touched no V3 tree, and no V3-related process existed at any point. "Alone" holds within the stocks-free-v3 project; machine-strict host isolation was not achievable. My 1743/4 count exactly reproduces the W1 claim, so no interference is detectable.
2. **OBS-2 (INFO)** — `state.json` fields `data_manifest`/`benchmark_contract` still read "pending A3" and the P0 placeholder control files remain `PENDING_A3`; superseded by P1 (w1_freeze `data_snapshot_hashes` 39/39; `authority.py` pins reverified here). Record staleness only.
3. **OBS-3 (INFO)** — Host swap 8.37/9.22 GB used at audit time (system-wide pressure, not V3-caused); no effect on outcomes.

## Verdict

```text
STOCKS_FREE_V3_S0_LAUNCH_AUTHORIZED
```

All twelve checks pass; blockers list is empty. This verdict authorizes — but does not itself start — the scored phase; PLAN sections 14–15 still require the separate owner instruction `GO STOCKS V3 SCORED EXECUTION` before any scored cell runs.
