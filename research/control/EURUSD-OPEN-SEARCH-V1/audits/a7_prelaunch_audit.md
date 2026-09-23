# A7 Prelaunch Audit — EURUSD-OPEN-SEARCH-V1

- Auditor: A7 (independent fresh-context, audit-only)
- measured_utc: 2026-09-23T14:33:46Z
- context_fresh: declared (all measurements recomputed from bytes/source this session)
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/eurusd-open-search-v1/integration`
- Branch: `orca/eurusd-open-search-v1-integration`; HEAD `bc14cb6d` (outcomes), freeze parent `bd61d200`
- Scope: prelaunch gate before the ONE historical-holdout check (program-S0) of frozen candidate FXOS-04-C4

## Verdict: AUTHORIZED

## Method

Independent recomputation from bytes/source only — no reliance on cycle claims. Git tree
inspection of both freeze commits, sha256 verification of frozen artifacts, full re-execution
of all 48 dev trials on the dev-only data plane with the frozen engine, sha256 of the data
manifest, re-execution of the fixture suite, and targeted scans (secrets, holdout references,
order/paper/live code, D2 waiver records). No files outside `audits/` were created or modified;
no commits made.

## Check 1 — Freeze chain: PASS

- `git log`: `bc14cb6d` (outcomes) is child of `bd61d200` (code freeze); commit order holds.
- `selection_freeze.json` ABSENT from `bd61d200^` tree, PRESENT in `bd61d200` tree — frozen
  before outcomes, not earlier.
- `candidates_frozen.json` + `outcomes/{campaign_dev.jsonl,dev_distribution.json}` present only
  in `bc14cb6d`.
- `engine.py` sha256 `cc868402e63db2f6b487fc544fe0799889db4c5e0e0df3f3689693f0871cb491`
  identical at `bd61d200`, `bc14cb6d`, and working tree — equals `selection_freeze.engine_sha256`.
  `selection_freeze.json` byte-identical committed vs working tree.
- Working-tree drift limited to `scripts/run_campaign.py` (see Finding F1); `build_bars.py`,
  `holdout_check.py`, `test_engine_fixtures.py` unmodified.

## Check 2 — Leak guards: PASS (with Finding F1)

- `holdout_check.py` (committed, unmodified): loads ONLY `df[df["ts"] >= 2023-07-01]` with a
  fail-closed floor of 50,000 bars (measured holdout plane: 59,885 bars), frozen baselines
  (LONG/SHORT/CASH/RANDOM seed=20260923), `run_count` tamper log, writes `holdout_check.json`.
- Committed `run_campaign.py`: fail-closed leak DETECTION — counts bars `ts >= 2023-07-01` and
  `SystemExit(FAIL_CLOSED)` if any. It does NOT silently filter; its docstring and
  `selection_freeze.leak_guards[0]` ("physically loads only") are literally true only of the
  uncommitted working-tree edit that adds the physical filter (F1).
- `outcomes/` contains no holdout-period metric: `campaign_dev.jsonl` has zero 2024/2025
  strings; fold keys are `{F1,F2,F3}` only; `candidates_frozen.json` contains holdout DATES
  only inside the preregistered SUCCESS criteria (no metrics).
- Decisive evidence: I re-ran all 48 trials on the dev-only plane (59,153 bars, `ts < 2023-07-01`)
  with the frozen engine — every record reproduced EXACTLY (all three cost tiers, fold metrics,
  digests): 0 mismatches. Dev outcomes are provably holdout-free regardless of which guard
  variant executed.
- `bars15.parquet` on disk spans the full corpus (max ts 2025-12-31 21:00 UTC) — holdout data at
  rest (Finding F2), not a selection leak.

## Check 3 — Engine semantics: PASS

`engine.py` (frozen sha) verified line-by-line:

- Opposite-side fills with stress widening: open long `b_o + k*s_o`, open short `a_o - k*s_o`,
  close long `a_c - k*s_c`, close short `b_c + k*s_c`. At k=1.0 this recovers the exact opposite
  quote (`b_o + 1.0*s_o == a_o`); k=1.5/2.0 widen beyond. Cost charged exactly once per side.
- Force-flat law: `is_day_close` marks each UTC day's last valid bar; open positions are closed
  there at day-close prices with multiplier k; `fill_ok=False` on day-close bars (and bar 0) —
  no entry fill on day-close bars, no position into rollover, by construction.
- PIT: signal `target[i-1]` is filled at bar i's open.
- Pips scaling `PIP = 1e4`.
- Fixture suite run by auditor: **7/7 PASSED** (0.77 s), including
  `test_pit_truncation_invariance` (emacross/bollfade/donchian/rsifade truncation-equality),
  fill math at k=1/2 with exact cost arithmetic, short-entry-at-bid, force-flat, no-fill-on-
  day-close, and cost-only random baseline negative.

## Check 4 — Trial accounting: PASS

- `campaign_dev.jsonl`: exactly 48 records; 48 distinct `arm_id`s; all carry
  `code_freeze_sha bd61d20075cd…`, `data_manifest_sha256 684163352…`,
  `d2 OWNER_WAIVED_EXPLORATORY`, `cycle_id EURUSD-OPEN-SEARCH-V1`.
- `config_digest` recomputed via `engine.config_digest` for ALL 48 arms (requirement was ≥5):
  100% match to records and to `selection_freeze.config_digests`.
- FXOS-04-C4 digest recomputed = `188a2070879d365a` (matches frozen).
- `digest_correction` disclosure present in `candidates_frozen.json`: hand-typed
  `9f2bd60e2545bd40` caught (INC-DEU-1 class), recomputed to `188a2070879d365a`.
- 48 trials ≤ budget cap 96.

## Check 5 — Data authority: PASS

- `census.json`: verdict `BUILD_PASS`; `bars15_valid 119038`; `nonpos_spread_minutes 0`; spread
  p50 0.3 pips (rollover window worse, as expected and disclosed); all three build gates true.
- `m1_manifest.json` sha256 recomputed =
  `684163352fd0f3754976403de190c07a8cc50cf1f00f29d644777404e196aada` — equals
  `dev_distribution.json.data_manifest_sha256` and the per-record manifest hashes.
- `probe_evidence.json`: `PROBE_PASS` at 2026-09-23T13:49:56Z — C1 OHLC invariants (8,640
  records, 0 violations), C2 offsets, C3 tick-vs-candle crosscheck (120 minutes, 0 mismatches —
  24-byte layout proven against tick ground truth), C4 price scale.
- Zero PnL before the data plane: P1 close `ac54f2fc` was `BLOCKED_SOURCE_LICENSE` (0/96 trials,
  0 PnL); data landed under amendment A1 (`7761ef1b`, Dukascopy authorized, TCU risk disclosed)
  before any outcome. `build_bars.py` verifies per-file sha on read, fail-closed. `data_local/`
  gitignored (no raw data committed).

## Check 6 — Claim consistency: PASS

- `dev_distribution.json` recomputed from `campaign_dev.jsonl`: trials 48; positive@k1.0 = 5,
  negative = 43; positive@k1.5 = 4; eligible = 1; net@1.0 min/med/max = −4520.3/−1496.7/+1203.6;
  net@1.5 = −8038.1/−2223.15/+703.95; total trades k1 = 65,756. All match the published file.
- FXOS-04-C4 is the ONLY eligible arm and ranks first by net@1.5 (703.95). Its `dev_stats` match
  `candidates_frozen.json`: net_k1 1203.6, net_k2 204.3, PF 1.1445, trades 609, hit 0.5846;
  folds −162.2/545.2/496.7 → frozen −162/545/497; net_k15 703.95 → frozen 704.0 (1-dp rounding,
  cosmetic — Finding F3).
- Near-miss FXOS-10-C3: PF 1.0919 present in the record, G2 False, eligible False, NOT frozen;
  disclosed margin-to-fail 0.0081 is accurate (1.10 − 1.0919). Not rescued.

## Check 7 — Boundaries: PASS

- No orders/paper/live/broker code anywhere: script imports are numpy/pandas/hashlib/json/
  subprocess/struct/lzma only. Plan §1: orders NONE; holdout is program-S0, NEVER S1,
  `S1 SEALED_UNTOUCHED`.
- No `outcomes/holdout_check.json`, no `holdout_run_count.json` — holdout untouched so far.
- Secret scan of committed cycle files: every match is prose about credential ABSENCE (env
  variable NAMES only, "values never read"); `selection_freeze.json` and `probe_evidence.json`
  have zero matches. No secrets committed.
- D2 recorded `OWNER_WAIVED_EXPLORATORY` in all 48 trial records and in the plan/P1 verdict —
  never evaluated, never PASS.
- Holdout SUCCESS criteria preregistered in `candidates_frozen.json`
  (frozen_utc 2026-09-23T14:23:25Z) before any holdout run; failure is final
  (`NO_CANDIDATE_NO_VALUE`, no re-tune).

## Findings

- **F1 — MEDIUM (non-blocking).** Uncommitted working-tree drift on frozen
  `scripts/run_campaign.py`. The committed runner's leak guard is fail-closed *detection*
  (SystemExit on any holdout bar), not a physical filter, while its docstring and
  `selection_freeze.leak_guards[0]` claim "physically loads only"; the physical filter exists
  only as the uncommitted edit. Drift direction is strictly safer; `engine.py` and
  `holdout_check.py` are byte-identical to freeze; and selection integrity was established by
  this audit's independent 48/48 exact recompute on dev-only data — so the finding does not
  undermine the frozen outcome. **Required before the holdout run:** commit (or revert)
  `run_campaign.py` so the prelaunch tree is clean and the freeze-artifact leak-guard claim is
  literally true of committed code.
- **F2 — INFO.** Full-corpus plane (59,885 holdout bars) and full-window census quality stats
  exist at rest pre-holdout. Data-at-rest plus aggregate quality census is not a selection leak;
  the holdout plane requirement (≥50,000 bars) is satisfied.
- **F3 — INFO.** Cosmetic rounding in `candidates_frozen.json` dev_stats (704.0 vs 703.95;
  integer folds). No effect on gates or ranking.

## Holdout conditions (binding for P3)

1. Resolve F1 first — clean tree at the holdout run.
2. Run `holdout_check.py` ONCE as committed; a second run is visible via
   `holdout_run_count.json` and is forbidden against a failed result (plan §5).
3. Judge solely against the preregistered SUCCESS criteria in `candidates_frozen.json`
   (net>0 @k=1.0 and net>0 @k=1.5 over 2023-07-01..2025-12-31); failure is final; FXOS-10-C3
   stays unfrozen; program-S0 only, never S1.

## Verdict rationale

All seven prelaunch checks pass on independent byte-level recomputation: freeze chain intact,
48/48 dev trials reproduce exactly from dev-only data with the frozen engine and digests, the
data authority chain (probe → manifest sha → census) verifies, published claims match records,
and boundaries are clean. The single MEDIUM finding is commit hygiene on the dev runner and does
not undermine selection integrity, which is established by recomputation rather than by the
runner's guard alone. **AUTHORIZED** for the single historical-holdout check under the binding
conditions above.
