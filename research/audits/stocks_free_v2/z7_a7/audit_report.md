# Z7 A7 — Independent Prelaunch Audit (Stocks-Free V2, W1)

- Auditor role: Z7/A7 — independent prelaunch auditor (PLAN_stocks_free.md §12)
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z7-a7-prelaunch`
- Branch: `orca/stocks-free-v2-z7-a7-prelaunch`
- HEAD verified: `106378230abecbaefff4248eeb373794f1b73038`, branch verified, status empty at audit start
- Interpreter: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`
- Read-only audit: no .env read, no data API call, no repair; staged data read only from the z8-exec-1 `.staging/` delivery (byte-identical to z8-exec-2/z9-reproduce, verified by hash)

## VERDICT

```text
STOCKS_FREE_V1_S0_LAUNCH_AUTHORIZED
```

Zero unresolved HIGH/CRITICAL objections. The single open item (A5 ARM2 fold-level turnover ceiling interpretation, MEDIUM) is adjudicated in `adjudication_a5_arm2.json` (Option A, average-annual binding) with its consequence applied consistently: A5 proceeds with all three cells; fold spikes travel as recorded advisories.

## Checklist results (§12, recomputed independently)

1. **Pins — PASS.** All four trees at exactly `1063782` (integration + detached z8-exec-1, z8-exec-2, z9-reproduce), each status-clean. `w1_freeze.json code_freeze.head = 5046a87` is W1's parent; `git diff 5046a87..1063782` touches only the 3 control files (event_log, state.json, w1_freeze.json), so code content is identical — pin semantics consistent. All 39 `data_snapshot_hashes` recomputed with sha256 from the `.staging/` deliveries of all three detached trees: byte-identical, zero mismatch/missing. Issuer-distribution xlsx sha256 `1b952f87…` matches the freeze pin. `cohort_digest c9d4e88a…` recomputed from the canonical payload (rule id, window [2018-01-02, 2026-08-27], warmup 63, floor 1e7, 11 sorted accepted rows): exact match. `partition_digest 9b4ad799…` = sha256 of `partition.json` file bytes: match (also pinned in a5 manifest + 3 arm specs). A4 arm digest `080c503f…` recomputed via frozen `arm_config_digest(spec)`: match; A4 spec file bytes `98d5307c…` match. A5 arm digests `51aee9c7 / 2a304ff0 / 1adff19e` recomputed from the frozen module: match; all 4 A5 spec file bytes match `SPEC_FILE_SHA256`.
2. **Data authority/license — PASS.** `da1_authority.json`: Twelve Data Basic USD 0 (official pricing evidence), internal non-commercial use, storage within subscription duration, deletion within 30 days post-termination recorded, redistribution prohibited; FD0 gate PASS with battery evidence; FREE_DATA_AUTHORITY_PASS present; `snapshot_manifest.json` carries the license note. `git ls-files` at W1: zero snapshot payload hits (no `_all_p1/_none_p*/.staging/staging-td/.xlsx` tracked); `.staging/` excluded via local `.git/info/exclude` (see INFO-2).
3. **S0/S1 isolation — PASS.** S1 = 2025-08-01..2026-07-31 sealed in partition.json, w1_freeze, FD7 gate PASS. `harness.s1_denied` denies s1 path segments, `s1_` prefixes, every sealed month token and exact range dates; `tests/stocks_free_v2/test_harness.py::test_s1_denial` asserts the right accept/deny set. `SealedPathFilter` tests in `tests/stocks_free_v1/test_partition.py` (S1-dated denial, sealed-root denial, read-only open enforcement, inclusive boundaries). Tracked-tree search for S1-dated strings: only declarations/control metadata (bounds, SEALED notes, split factor 2025-12-05 provenance — a data-construction fact, not a scored value). No S1 return values exist anywhere (nothing scored).
4. **PIT/next-event ordering — PASS.** `family_a4/schedule.py`: `fill_date = calendar.next_session(decision_date)` on raw executable prices; decisions whose fill would land in sealed S1 are dropped; TR feature series separated from raw fills. `family_a5/schedule.py`: same next-session fill, one-event delay mandatory, gates evaluated only through the decision date, ramp events suppressed to unscored 100% cash, fills past `scored_end` dropped. Tests assert the right things: A4 `test_clock_and_lookahead` (fill > decision; first fill = next regular session); A5 `test_one_event_delay_and_no_purge_executions`, `test_no_lookahead_decision_uses_only_sessions_through_t` (mutation-based, both directions), `test_no_lookahead_future_value_cannot_move_sma`.
5. **Raw/TR/distribution reconciliation — PASS (INFO-1).** FD2 amended formula recorded (raw closes × issuer split factors + SSGA/SPDR distribution records) with `split_factors.json` issuer press-release provenance for the five 2:1 splits eff 2025-12-05 (inside S1; S0 unaffected). FD6: SPY vs SSGA NAV-TR 0.39% cumulative / 0.175% max yearly (a-priori tolerances), 34/34 ex-dates matched. The 5-fund TD adjust=all double-count limitation is recorded in the FD2 gate (`blockers`, diagnostic-only). Family code greps: zero `_all_p1` references. Only `z6_driver.py` loads `_all_p1` (into `adj`) — and never uses it (see INFO-1); no scoring path consumes TD adjust=all.
6. **Six unique trial identities — PASS.** `selection_freeze.json` holds 6 unique arm ids (3 A4 + 3 A5, verified unique programmatically); all arm/spec digests match W1 records and were recomputed at W1 (item 1).
7. **Dry-run — PASS (LOW-1).** `z6_driver_evidence.json`: 6 unique keys, ledger published = 6, every replay zero-delta and suppressed, `real_cycle_counters_untouched {0,0}`; driver code writes only DUMMY artifacts (`is_dummy: true`, `dummy_total_pnl: 0.0`). `value_book` is absent from the driver (defined + goldens-tested in harness only) — no real PnL was computed in Z6.
8. **Costs/stress/turnover/benchmark — PASS.** A4 spec: base 7 bps (2 spread + 3 slippage + 2 ops), stress 12 bps, Z6 ceiling ≤ 6.0x gross one-way/yr; driver measured 3.58/3.73/3.97x within. A5 specs: 10 bps/side base; stress 2x = 20 bps/side and ceiling 6.0x two-way/yr preregistered in `selection_freeze.json` O1 fix exactly as Z4 required. Flat 0% hard benchmark + SPY TR context-only declared in every family/arm spec.
9. **Family/control immutability — PASS.** Every spec sha256 at W1 equals the Z4 audit's recorded recomputations (A4 `98d5307c`, A5 manifest `d69fb046`, arms `6c301db5/8c65c0d7/5f3d93ba`, census `4f9cab6a`, partition `9b4ad799`, run_contract `65410307`, split_factors `f6665651`, PLAN `d3458d85`). `selection_freeze.json` families section = exactly Z4's six-arm freeze recommendation (ids, roles, cell orders). The O1 fix and O2 erratum are recorded as Z4 instructed. No mechanism field changed since Z4.
10. **Tests — PASS.** Run in the integration worktree at W1 (read-only; tree clean before and after): `tests/stocks_free_v2`: **110 passed**; `tests/stocks_free_v1`: **109 passed, 1 skipped** (SSGA staging-path fail-closed NOT_RUN); `tests/assets/common tests/assets/stocks`: **290 passed**.
11. **Budget/denominators/scored artifacts — PASS.** Budget 0/6, published 0, observed 0 consistent across state.json, w1_freeze.json, selection_freeze.json, heartbeat. No `results/registry/stocks_free_v1` or `-v2` scored ledger exists in any tree of the stocks-free-v2 line (nor in the v1 line). The only `results/` files under the integration tree are pre-existing tracked crypto uploads from old commit `dd01cf0` (USDT PnL, unrelated cycle, not a v1/v2 ledger). Real `TrialLedger` absent; the dry-run ledger is confined to gitignored staging.
12. **Heavy cap / resources — PASS.** `heavy_cap_measured: 1` (heartbeat) and `heavy_cap: 1` (w1_freeze environment); three detached trees exist at exactly W1 with verified staged data; 56 GiB free disk, 8 GiB RAM, 8 cores — sufficient for the mandated serial (cap-1) cell runs.

## Adjudication (binding)

**Option A — average-annual binding.** 5.4545x/yr ≤ 6.0x ⇒ A5-SFV2-ARM2-SMA200-WEEKLY is ELIGIBLE; the A5 three-cell Stage-A design stands. Fold-1 6.09x/yr and fold-3 8.05x/yr are recorded as advisories with quantified drag (fold-3 ≈ 195 bps base / 389 bps stress cumulative ≈ 0.8–1.6%/yr in-fold). Justification is textual, not outcome-based (nothing scored): the O1 ceiling "matches declared neighbour upper bound" = the spec's `expected_two_way_annual` "3.0x–6.0x" (an annual-rate expectation from rule structure); PLAN §11/§14 frame the ceiling as tradeability feasibility (an annual-rate property), not a per-fold constraint; and a per-fold reading adopted after the Z6 measurement would be a post-hoc tightening no frozen text authorizes. Full record: `adjudication_a5_arm2.json`. Consistent consequence: the §14 "turnover/capacity remain feasible" gate for A5 is evaluated against the average-annual reading at Stage-A, with the advisories attached.

## Objections by severity

**CRITICAL:** none. **HIGH:** none. **MEDIUM:** none open (the referred adjudication item is resolved above).

**LOW-1 (dry-run evidence bookkeeping).** The committed `z6_driver_evidence.json` records `first=false` for all 6 keys and `ledger_observed=18` (= 3 runs × 6 over the persisted staging ledger); the 6 lifetime FIRST_PUBLICATION events exist only in the ephemeral gitignored ledger, while the gate text claims "6 first publications". TrialLedger semantics guarantee exactly one first publication per key, so the protocol held — but the committed artifact alone does not demonstrate it. *Action for A1 (optional, non-blocking):* regenerate the dry run against a fresh temporary ledger (or annotate the evidence) so the committed file alone shows the six first publications.

**LOW-2 (fold-level turnover advisories).** ARM2 fold-1 6.09x/yr and fold-3 8.05x/yr exceed the 6.0x average-annual ceiling when annualized per fold. Recorded with drag quantification; binding interpretation is average-annual (above). Monitoring obligation: the after-cost Stage-A gates absorb this cost reality — no separate repair is permitted under the no-tuning declaration.

**INFO-1.** `z6_driver.py` loads the TD adjust=all series into `adj` and never uses it (the intended cross-check is inert; the variable name suggests a check that does not happen). No scoring impact; tidy before any future reuse.

**INFO-2.** `.staging/` payload exclusion relies on the machine-local `.git/info/exclude` rather than a tracked ignore rule; payloads were never tracked at any audited commit (provenance note only).

## What A1 must do before cells start

1. Carry this adjudication (`adjudication_a5_arm2.json`, this commit) into the Z8 run context: A5 runs all three cells; the A5 §14 feasibility gate binds on 5.45x/yr average-annual with the fold advisories attached. Do NOT modify any frozen field (no-tuning declaration stands).
2. Per PLAN §13, run the per-cell "verify pins and S1 denial" step in each detached tree before each cell, using the frozen hashes verified here.
3. Optional (LOW-1): regenerate/annotate the six-arm dry-run evidence so first publications are self-evident in the committed artifact.

Auditor computed no strategy returns; the only recomputations were hashes, canonical digests, and schedule-only turnover/cost arithmetic.
