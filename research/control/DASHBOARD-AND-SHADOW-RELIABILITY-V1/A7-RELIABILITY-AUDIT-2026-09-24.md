# A7 — Reliability audit: FX daemon fix + crypto 6-commit batch + ledger/dashboard integrity

- Auditor: A7, independent fresh-context (did not write any code under audit).
  Read-only audit: no file under audit was edited, fixed, committed or reverted;
  only `pytest` (authorized) and read-only commands were run.
- Measured window: 2026-09-24T08:21Z .. 08:37Z (15:21..15:37 +0700). All numbers
  recomputed from bytes and running state during this window; ledger sizes and
  the served snapshot were captured twice inside the window.
- Targets:
  - FX: commit `f8bb2b73343e50a49bcb2cbead7bdec60a2657d7` (parent `50c7a465`),
    branch `orca/fx-rangefade-2m-shadow-v1`, worktree
    `/Users/hoangminhlong/my-quantitative/.worktrees/fx-rangefade-2m-shadow-v1`.
  - Crypto: commits `302d5f52`, `12540ebe`, `887deb71`, `3bf495b7`, `28d923b2`,
    `236bf2f7` (HEAD at audit = `236bf2f7bbbf87285e7e1e6c6767782ab48f69fb`),
    branch `orca/prospective-shadow-v1-integration`, worktree
    `/Users/hoangminhlong/my-quantitative/.worktrees/prospective-shadow-v1/integration`.
  - Live surfaces: FX daemon PID 35609 (started 15:19 +0700 = 08:19Z), FX journal
    `research/control/FX-RANGEFADE-2M-SHADOW-V1/shadow_journal.jsonl` (47 rows),
    crypto ledgers `results/prospective_shadow_v1/ledgers/*.jsonl`, dashboard app
    at `http://127.0.0.1:8791` (bundle `dashboard/dist/Quant Shadow Dashboard.app`,
    dashboard worktree HEAD `61d86b43`, branch `orca/shv1-dashboard`).
- Method: `git show`/`diff-tree`/`rev-parse` blob comparison of every touched
  file; byte-level re-hash (sha256/byte_len/`git hash-object`) of identity
  manifest targets; independent re-parse of all ledger and valuation-mark JSONL
  streams with `.venv/bin/python`; point-by-point comparison against the served
  `/api/snapshot.json`; pytest suites; credential/broker-surface grep over all
  changed files of the 7 audited commits.

## Check results

### 1. FX daemon fix f8bb2b73 — PASS

- **(a) Diff scope.** `git diff --name-only 50c7a465 f8bb2b73` = exactly 2 files:
  `daemon/shadow_daemon.py` (+7, the `seed_bars` ingest edge:
  `df["ts"] = df["ts"].astype("datetime64[ns, UTC]")` plus comment) and new
  `tests/test_bar_append_dtype.py` (+88). The frozen core
  `daemon/fx_shadow_core.py` has identical blob `022b3b66` in parent and fix;
  the frozen engine (imported from
  `EURUSD-OPEN-SEARCH-V2/scripts/engine.py`) is not in the changed set.
- **(a) Root cause re-derived from bytes.** Both seed parquets measured
  `datetime64[ms, UTC]` (`FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/derived/
  bars1h.parquet`, 31,844 rows; `FX-MAJORS-SEARCH-V1/data_local/GBPUSD/.../bars1h.parquet`).
  `daemon.log` records 4 crashes; the final traceback is
  `AttributeError: Can only use .dt accessor with datetimelike values` raised at
  `EURUSD-OPEN-SEARCH-V2/scripts/engine.py:44`
  (`self.ts = (df["ts"].dt.tz_convert("UTC")...)` inside `H1Plane.__init__`),
  called from `shadow_daemon.py on_closed_bar -> targets_from_df ->
  plane_from_df -> V.H1Plane` — exactly the claimed chain (the "engine.py line
  44" of the claim is the frozen V2 engine, reached through v2_lib). The two
  earlier crash classes in the same log (`int(Timestamp)` TypeError; missing
  `json` import NameError) match the commit message narrative.
- **(b) Tests.** `cd <fx wt>/research/control/FX-RANGEFADE-2M-SHADOW-V1 &&
  .venv/bin/python -m pytest tests/ -q` → **26 passed** in 1.26s.
- **(c) Running daemon crossed the 08:00Z boundary and restarted cleanly.**
  Journal (47 rows, `seq` strictly monotone 1..47):
  - `bar_closed` at `bar_ts 1790233200` for BOTH pairs at
    `2026-09-24T08:00:08+00:00` (seq 41 EURUSD, seq 42 GBPUSD); no duplicate
    `(pair, bar_ts)` anywhere in the file. This is the first H1 boundary the
    daemon ever survived (log crash #4 was at a boundary).
  - Restart evidence at `2026-09-24T08:19:13Z`: `boot_replay` for both pairs
    with `bars_restored: 1`, `events_read: 42`, `events_dup: 0`, `events_bad: 0`;
    `parity_selftest PASS` both pairs (`n_bars` 31,845 / 32,189 = seed + 1);
    `shadow_start` replay summary `bars_restored: 2`. Daemon PID 35609 start
    time 15:19 +0700 (= 08:19Z) matches the journal boot time.

### 2. Crypto 6-commit batch — PASS

- **(a) Commit scope / no signal/target/sizing-law change.** `rev-list
  302d5f52~1..236bf2f7 --count` = 6 (contiguous, HEAD = 236bf2f7). Union of
  changed files: `e/valuation_worker.py` (FAMILY_ORDER 3→4, appending
  FAMILY_BANDRIDGE only), `dashboard/snapshot.py` (anchor_note string only, now
  derived from the `STARTING_COMBINED_EQUITY_USDT` constant), `risk.py`
  (additive fallback only), `identity/identity_recovery.json`, one audit
  artifact (evidence, 887deb71), and 7 test files. Blob-identical across the
  range: `executor.py` `a5e30c85`, `accounting.py` `86b32f66`, and the whole
  `research/shadow_v1/families/` package (signal laws) — `git diff
  302d5f52~1 236bf2f7 -- research/shadow_v1/families/` is empty.
  `risk.py` diff = one nested fallback: `adapter_weight_cap_max` → **new**
  `max_abs_weight` → None. Founding families provably unaffected (read from the
  identity manifest `score_affecting_parameters`): ILLIQ has no weight-cap key
  (None before and after); BASISLV carries `adapter_weight_cap_max: 0.3` (first
  branch, taken before the fallback); CARRY's key is
  `max_abs_weight_per_symbol` (first branch). Only BTC4H-BANDRIDGE
  (`max_abs_weight: 1.0`) reaches the new branch.
- **(b) BANDRIDGE root cause + fail-closed preserved.** Mechanism confirmed in
  code: sizing at reference price `executor.py:989`
  (`desired[symbol] = w * equity / fill_refs[symbol]`) vs opening-buy cash
  guard `accounting.py:418` (`needed = qty * primary_fill + primary_fee`
  against `self.cash`, fill at ref + 1 tick plus fee) → weight-1.0 single-leg
  long-only is infeasible under any positive cost book. Ledger
  `ledgers/BTC4H-BANDRIDGE.jsonl` (57 decisions): all 56 pre-08:00Z decisions
  have `target_weights {BTCUSDT: 1.0}`, `accounting_status
  UNAVAILABLE_FAIL_CLOSED`, **0 fills**; the `2026-09-24T08:00:00Z` decision
  has `signal_values {band_gate_on: 1.0, band_r: 0.061486, donch_state: 0.0}`,
  `target_weights {}`, `accounting_status OK`, 0 fills — a legitimate no-trade
  (gate open, Donchian state flat). The 6 commits contain no
  executor/accounting change, so the fail-closed behavior is untouched;
  the realization decision remains with the owner
  (`OWNER_DECISION_PACKET_bandridge_sizing_and_fill_law.md` verified present
  with the claimed numbers: fee 0.05% = 0.0005, fill = ref + 1 tick,
  needed ≈ **100,050.02** USDT on 100,000 cash).
- **(c) Tests.** `.venv/bin/python -m pytest tests/test_shv1_executor.py
  tests/test_shv1_identity_recovery.py tests/test_shv1_worker_config.py
  tests/test_shv1_engine_smoke.py -q` → **52 passed** in 25.20s.
- **(d) Identity manifest byte-level verification (independent re-hash).** For
  the BTC4H-BANDRIDGE entry's 3 files at the `.worktrees/`-rooted paths I
  recomputed sha256, byte_len and `git hash-object` blob sha; **all three match
  exactly**: `es1_freeze.json` (sha c8bab46e…, 4190 bytes, blob 96abc5f1),
  `shadow_group_s0.json` (sha c8f7efdd…, 4523 bytes, blob f512c3d9),
  `shadow_bandridge/SPEC.md` (sha 3a7591fb…, 3408 bytes, blob d8411a43).
  Verbatim metric quotes verified present in the pinned bytes (972763.52 and
  137080.45 beside GATE_SHUFFLE_control in shadow_group_s0.json;
  POSTHOC_DISCOVERY_CANDIDATE and the C3 gate-FAIL verdict in es1_freeze.json).
  The composite verdict label is **disclosed, not claimed as a byte quote**:
  `label_kind: "composite"` with `label_byte_components` pinning each segment
  ("ES1 C3 G5-killed", "S0 characterization", "PSV1 arm G6-control-killed"),
  and `verdict_labels_policy` explicitly declares the composite BANDRIDGE label
  NOT rewritable in cycle PROSPECTIVE-SHADOW-V1.

### 3. Ledger integrity + no-order boundary — PASS

- **event_id uniqueness**: per-file scan of all 4 ledgers — 0 duplicates
  (BASISLV 1, BANDRIDGE 57, ILLIQ 1, CARRY 10 records).
- **no_order_proof**: present on every record in all 4 ledgers (0 missing).
- **Append-only / byte growth**: e-worker heartbeat
  `runtime/heartbeat.json` `ledger_byte_counts` == on-disk byte sizes exactly,
  at two separate reads inside the audit window (sizes 1292 / 70298 / 3922 /
  27727; heartbeat last_loop 08:36:21Z; per-file record timestamps are
  ascending). No shrink or rewrite observed.
- **No fabricated fills**: 56 virtual fills total (ILLIQ 8, CARRY 48,
  BANDRIDGE 0, BASISLV 0). Every fill re-checked against the accounting law in
  `accounting.py:_fill_economics` (L345-358): fill_price = ref ± 1 tick
  (adverse), `slippage = qty * tick`, `fee = qty * ref_price * 0.0005` (fee on
  reference notional) — **0 violations** at 1e-9 tolerance.
- **No broker/order/credential surface** in the changed files of f8bb2b73 +
  the 6 crypto commits: grep finds only keyless `urllib` GETs to
  `https://webrates.truefx.com/rates/connect.html` (public rates CSV) and
  `https://fapi.binance.com/fapi/v1/premiumIndex` (public; klines URL appears
  only in test stubs). No api_key/secret/token/signed-request/order-placement
  surface.

### 4. Dashboard arithmetic (independent recompute vs running app) — PASS

- Source: `http://127.0.0.1:8791/api/snapshot.json` (fetched 08:30:02Z,
  2,033 series points) vs bytes of
  `results/prospective_shadow_v1/valuation_marks/*.jsonl`.
- Recompute rule applied independently: skip `CAPITAL_SEED_NO_MARK`; at each ts
  use each included family's LATEST mark ≤ ts and require `data_status OK`
  (a DATA_BLOCKED latest mark ⇒ gap); include BTC4H-BANDRIDGE only from its
  first mark `2026-09-24T01:10:00Z` (before that, sum only the 3 founding
  sleeves).
- Result: **1,983 complete points match exactly** — served `equity` AND served
  per-family `contributions` each within 1e-6 (0 mismatches); **50 gap points
  all have `equity: null`** in the app (status `UNAVAILABLE_FAIL_CLOSED`).
  1,983 + 50 = 2,033 = served series length.
- Mount-day PnL: `pnl_periods.daily` row `key 2026-09-24`:
  `pnl_usdt` −320.58131908945506 == `end_equity` 399027.6853369254 −
  `start_equity` 299348.26665601484 − `capital_flows_usdt` 100000.0 —
  **float-exact, diff 0.0**; start/end equity equal the series points at
  `2026-09-23T16:55:00Z` / `2026-09-24T08:25:00Z` bit-exact;
  `baseline_equity` = **300000.0**.

### 5. Status semantics honesty — PASS

- **BANDRIDGE nowhere displays as healthy RUNNING.** Served snapshot:
  valuation family status `FLAT_OK`, `status_note "flat at seed capital (no
  open positions)"`, `positions: []`, sleeve chip `{"chip": "FLAT",
  "tone": "flat"}` (gray); app-level banner `UNAVAILABLE_FAIL_CLOSED`
  ("BTC4H-BANDRIDGE: có khoảng dữ liệu không định giá được (fail-closed, không
  nội suy)", source reason "mark gap in ledger"). By contrast ILLIQ renders the
  green `RUNNING` chip — the renderer distinguishes the two, and BANDRIDGE gets
  the flat one.
- **BASISLV shows DATA BLOCKED.** Sleeve chip `{"chip": "DATA BLOCKED",
  "heartbeat_data_status": "DATA_BLOCKED"}`; its ledger decision record carries
  `data_status DATA_BLOCKED` / `accounting_status UNAVAILABLE_FAIL_CLOSED`
  (rejected `*`: "missing 286 completed bar(s) … first gap at
  2026-09-18T00:15:00Z"), plus its own fail-closed banner.
- Served page bytes (65,770 bytes from `/`) contain the same chip-rendering
  logic as `dashboard_app/page.py:405-415` (chips rendered verbatim from
  served data, `tone: flat` gray style at L78) and the fail-closed banner
  strings; the running app is the `dist/Quant Shadow Dashboard.app` bundle of
  the dashboard worktree (HEAD `61d86b43`). No GUI app was launched or quit
  during the audit.

## Findings

Blocking: none.

Non-blocking:
- **F1 (cosmetic, FX journal schema migration).** The first 15 journal rows
  (03:25–03:54Z boot attempts) carry neither `event_id` nor `seq` — both fields
  were introduced later (rows 16+ have both, consistently; all 32 event_ids
  present are unique; seq strictly monotone). Historical rows are retained
  as-is. File: `research/control/FX-RANGEFADE-2M-SHADOW-V1/shadow_journal.jsonl`
  rows 1–15.
- **F2 (evidence nuance, FX restart).** The "controlled SIGTERM" mechanism is
  not itself journaled (the journal has no shutdown event type). The restart is
  evidenced indirectly: `boot_replay` at 08:19:13Z with `bars_restored=1`,
  `events_dup=0`, `events_bad=0`, parity PASS both pairs, and the daemon
  process start time (ps: 15:19 +0700) matching the journal boot to the
  minute. Clean-replay evidence is present; the signal name is corroborated
  inference.
- **F3 (observation, BANDRIDGE mark coverage).** BANDRIDGE has 75 marks from
  its 01:10Z first mark through 08:25Z — fewer than the nominal 5-min grid —
  which is exactly what its "mark gap in ledger" fail-closed banner discloses,
  and the app's gap set matched my independent recompute point-for-point.
  Honest fail-closed behavior, not a defect.

## Verdict

Every audited claim was re-measured from bytes, git objects, running processes
and the live API, and every quantitative claim reproduced exactly: the FX fix
is confined to the ingest edge with the frozen engine byte-identical and the
daemon now surviving an H1 boundary plus a clean state-replaying restart; the
crypto batch touches no signal/executor/accounting law, the BANDRIDGE
fail-closed root cause is real and still owner-open, the identity manifest's
three provenance files re-hash to their pinned digests with the composite label
honestly disclosed; all four ledgers are append-only, event-unique,
no-order-proof-complete with all 56 fills exact against the frozen cost law;
the dashboard's 2,033-point combined history and the mount-day PnL identity
reproduce bit-exact from mark bytes; and both flagged sleeves display honest
fail-closed statuses (FLAT + banner, DATA BLOCKED) rather than healthy RUNNING.

A7 VERDICT: CONFIRM
