# A7 — Dashboard 4th family (BTC4H-BANDRIDGE) audit

- Auditor: A7, independent fresh-context (did not write the audited code).
- Measured: 2026-09-24T04:57:53Z (11:57:53 +0700). All numbers below recomputed
  from bytes during this window; marks are LIVE (worker writes every 5 min), so
  comparisons are made within single reads.
- Target: commits `45267ddd` + `61d86b43` on branch `orca/shv1-dashboard`,
  worktree `/Users/hoangminhlong/my-quantitative/.worktrees/prospective-shadow-v1/dashboard`.
  HEAD at audit = `61d86b433fe27fd1c3876af209e82f0d6da79e5e` (worktree clean except
  untracked `build_new/`, `dist_new/`, `dist_prev_*/`).
- Method: read diffs; independently parsed the 4
  `results/prospective_shadow_v1/valuation_marks/*.jsonl` byte streams with
  `.venv/bin/python`; recomputed strict sums, gap semantics and flow-aware PnL;
  fetched `http://127.0.0.1:8791/api/snapshot.json` and compared point-by-point;
  ran the pytest suite; ran 4 adversarial counterexamples against
  `compose_combined_history` / `build_pnl_periods`.

## Check results

### 1. Commit scope / engine untouched — PASS
- `45267ddd` touches exactly: `dashboard_app/{__init__,page,pnl,store}.py`,
  `tests/{conftest.py,test_combined_history.py,test_pnl_periods.py,test_quant_shadow_app.py}`.
- `61d86b43` touches exactly: `dashboard_app/page.py`.
- No file under `research/shadow_v1/`, `results/`, engine or worker is touched.
  `dist/` is gitignored (`.gitignore:32`), so "rebuilt bundle" left no tracked
  change. `git -C integration status --short` = only the pre-existing
  ` M research/control/prospective_shadow_v1/e/valuation_worker.py`.
- Read of pnl.py/store.py diffs: no invented constants entering PnL math; the
  only numbers are seed-derived (baseline = Σ founding seeds; flow = late
  sleeve's seed equity). No interpolation anywhere: gaps emit
  `UNAVAILABLE_FAIL_CLOSED` with `equity: null`.

### 2. Byte recompute vs served `app.combined_history` — PASS (all 3 targets + full series)
Independent strict-sum from marks bytes vs served point (status + equity):

| ts | bytes | served | verdict |
|---|---|---|---|
| 2026-09-17T02:10:00Z | OK, 298955.3289229864 (3 sleeves; BANDRIDGE absent, first mark 09-24T01:10) | OK, 298955.3289229864 | MATCH (exact) |
| 2026-09-24T01:10:00Z | OK, 397710.4074600096 (4 sleeves incl. BANDRIDGE 100,000) | OK, 397710.4074600096 | MATCH (exact) |
| 2026-09-24T04:50:00Z (latest at fetch) | OK, 398926.21469735255 | OK, 398926.2146973526 | MATCH (≤1e-6, float repr) |

- Full-series comparison: bytes union = 1,996 ts; served series = 1,996 points;
  0 presence mismatches, 0 status mismatches, 0 equity mismatches (>1e-6).
  1,946 OK + 50 `UNAVAILABLE_FAIL_CLOSED` (equity null) — byte-identical.
- Note: dispatch said "expect ~398.8k at 01:10"; the marks bytes at that exact
  ts give 397,710.4074600096 and the app serves exactly that. The app matches
  bytes; the dispatch approximation was taken at a different instant. Not a defect.

### 3. Capital-flow accounting — PASS
- Boundary marks (bytes): start = last mark strictly before 2026-09-23T17:00:00Z
  = 2026-09-23T16:55:00Z, 3-sleeve sum 299348.26665601484; end = newest marks
  2026-09-24T04:50:00Z, 4-sleeve sum 398926.21469735255.
- Served `pnl_periods.daily[key=2026-09-24]`: `end_equity` 398926.2146973526 −
  `start_equity` 299348.26665601484 − 100000.0 = **−422.05195866222493** =
  served `pnl_usdt` (diff exactly 0.0; vs bytes-recomputed −422.05195866228314,
  diff 5.8e-11 ≤ 1e-6). `capital_flows_usdt` = 100000.0,
  `capital_flow_families` = ["BTC4H-BANDRIDGE"]. The naive flow-as-profit value
  (+99,577.948…) appears nowhere. Previous days have flows=None; first daily row
  2026-09-15 `start_from_seed=True`, start_equity 300000.0.
- `baseline_equity` = **300000.0** (= Σ of the three founding
  CAPITAL_SEED_NO_MARK records of 100,000 @ 2026-09-14T23:48:01Z, NOT 400,000);
  `founding_families` = the 3 founding ids; capital_flows carries exactly one
  record: 100000.0, BTC4H-BANDRIDGE @ 2026-09-24T01:10:00Z.
- Cross-validation: engine's own strict-4 `combined.total_pnl_usdt`
  (−1073.7853026473895) equals the dashboard's independently composed flow-aware
  monthly PnL to full float precision (398,926.2147 − 300,000 − 100,000).
- Commit-message note: "-579.67" was measured against an earlier last mark; the
  value moves with the live mark (−422.05 at 04:50Z). Invariant
  `pnl == end − start − 100000` held at every measured instant.

### 4. Fail-closed challenges — PASS
- (a) 50 ts found where a mounted-family mark is not OK (e.g.
  2026-09-15T16:30/16:35/16:40Z XSECT `UNAVAILABLE_FAIL_CLOSED`). Served points
  at those ts: `UNAVAILABLE_FAIL_CLOSED`, equity null. No partial sums, no
  carry-forward. Points before all 3 founding sleeves' first marks are also gaps.
- (b) `pytest tests/test_combined_history.py tests/test_pnl_periods.py
  tests/test_dashboard.py tests/test_dashboard_purity.py
  tests/test_quant_shadow_app.py -q` → **56 passed, 1 skipped** (57 collected),
  exit 0, run by A7 from the dashboard worktree with `.venv/bin/python`.
- (c) Counterexample attempts (synthetic inputs):
  - Flow inside a bucket whose flow-ts combined point is a gap → flow still
    subtracted via cumulative flow difference (pnl 600, not 100,600). PASS.
  - Flow with unknown amount (no seed) → `pnl_usdt` None for every bucket whose
    boundary interval contains it. PASS (fail-closed).
  - Flow after the last equity mark → no bucket can claim it: cum flow
    difference is anchored to boundary marks, and no post-flow equity point
    exists, so no profit can appear. PASS.
  - Founding seed missing → `baseline_equity` None → first bucket pnl None. PASS.
  - Pre-mount leakage: BANDRIDGE enters `mounted` only from its first series ts;
    its 100,000 appears in the equity LEVEL series only at/after 2026-09-24T01:10
    and is subtracted from every PnL bucket it lands in. No path found that
    surfaces +100,000 as profit.
  - Cosmetic: a poisoned-flow row displays `capital_flows_usdt` 0.0 next to the
    family name (pnl is None) — see finding F3.

### 5. No-mutation check — PASS
- e-worker heartbeat `results/prospective_shadow_v1/runtime/heartbeat.json`:
  pid **65251** (process alive, started 07:58:11 +0700), `last_loop_utc`
  **2026-09-24T04:51:19Z**, inode-vs-path match true.
- valuation heartbeat `runtime/valuation_heartbeat.json`: pid **68885** (alive,
  started 08:11:40 +0700), `last_loop_utc` **2026-09-24T04:54:59Z**,
  `next_mark_utc` 04:55:00Z, `heavy_lock_verdict` FREE_PROVEN, inode match true.
- Integration worktree: only the pre-existing dirty
  `research/control/prospective_shadow_v1/e/valuation_worker.py`. Nothing under
  `research/shadow_v1/` or `results/` modified by the audited commits (see §1).
- Dashboard worktree: tracked files clean at HEAD `61d86b43`.

### 6. UI surface — PASS
- Served envelope: `snapshot.valuation.families` and `app.families` both have
  exactly 4 keys incl. BTC4H-BANDRIDGE. BANDRIDGE: `gross.open_positions` = 0,
  `gross.usd` = 0.0; latest mark equity 100,000.0, realized_pnl 0.0,
  unrealized_pnl 0.0, gross 0.0, status FLAT_OK, accounting_status OK;
  family `total_pnl_usdt` 0.0. No fabricated PnL anywhere for the new sleeve.
- Served page HTML is **byte-identical** to HEAD `dashboard_app.page.PAGE_HTML_BYTES`
  (65,770 bytes, sha256 prefix d0bb9183ed79fc01) — the live .app (pid 5898,
  dist bundle built 11:42 +0700) serves the audited code exactly.
- Served page: 0 occurrences of `FAM_ORDER`; 6 of `famList(env)`; strip counts
  and cards derive from the API family list; BTC4H-BANDRIDGE appears only in the
  `FAM_SHORT` display-alias map (fallback = full id), not as a list source.
- Chart fix from `61d86b43` present in served page (4 × `hist.baseline_equity`):
  pre-mount tooltip PnL measured vs 300k founding baseline; stepped dashed
  baseline 300k→400k; y-range not stretched by flow amounts.

## Findings (non-blocking)

- **F1 (cosmetic hard-code)**: display prose still hard-codes the count/capital:
  header sub "vốn ban đầu 400,000 USDT (4 sleeve crypto)", strip labels "từ vốn
  ban đầu $400,000" / "400,000 USDT gốc", trades heading "4 family crypto". The
  family LIST, cards, chart buttons and filters are dynamic; these static
  strings would go stale if a 5th sleeve mounts. No PnL number derives from
  them (PnL tab baseline box uses `pp.baseline_equity` = 300,000 correctly).
- **F2 (test invariant weakened)**: in `tests/test_quant_shadow_app.py`, the old
  `counters["order_intent_count"] <= counters["fill_count"]` assertion was
  dropped (BANDRIDGE has decision intents with 0 fills). A per-family invariant
  would have been stricter than removing the check.
- **F3 (display edge)**: `_aggregate` reports `capital_flows_usdt` 0.0 beside
  the flow family name when a flow amount is unknown (pnl None) — "0.0" could
  be misread as "no flow"; the PnL path itself is fail-closed.
- **F4 (doc drift)**: commit message's "-579.67" mount-day PnL is a moving
  number (last mark advances every 5 min); served value −422.05 at 04:50Z is
  correct per the invariant.

## Verdict

Every owner requirement measured PASS against bytes: 4th family present with
0 positions / 0 fills / 0 fabricated PnL; pre-activation 3-sleeve history
preserved (298,955.33 @ 09-17); +$100,000 accounted strictly as capital flow
(pnl = end − start − 100,000, exact); baseline 300,000; fail-closed on gaps,
unknown flows and missing seeds; engine untouched; live workers unmolested.

**A7 VERDICT: AUTHORIZED_WITH_FINDINGS**

Blockers: none. Findings F1–F4 are cosmetic/robustness notes for the owner to
queue; none refutes the audited claims.
