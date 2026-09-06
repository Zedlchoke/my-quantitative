# A7 prelaunch audit — STOCKS-FREE-V10 (fresh context, independent)

**Verdict: `STOCKS_FREE_V10_S0_LAUNCH_REFUSED`** (2 unresolved HIGH, 0 CRITICAL)
Full artifact: `audits/a7_prelaunch_v10.json` (schema `stocks_free_v10_run/a7_prelaunch@1`).
Audited at HEAD `7764c23` on `orca/stocks-free-v10-integration`, clean tree.

## What verified clean (items 1–6, 8–10)

- **Freeze chain**: panel re-hash `67591464...af1447` MATCH; timing layer
  `b1477ea3...02337` and revision layer `7110cbf0...657c2` MATCH the P0
  manifest full values; row counts match; V9 terminal `3a61638` is the base
  (4 commits on top).
- **P0 PIT layer**: own norms prior-only (`eff' < eff AND first_avail' <=
  first_avail_E`), cohort norms month-bucket strict (group + same-month peers
  excluded — independently reproduced with a same-month-peer probe), filer-
  period dedup pinned by fixtures, 0 negative lags counted, zero asserted
  timestamps. 21/21 fixture tests pass.
- **Signal specs**: both selected families implement the frozen specs exactly
  (exposure = −value, largest-first_avail 800d window, per-field max-eff Q,
  |Q| ≥ 4, severity clean-tie 0.0, up-mirror control).
- **Two-key guard**: verified in code, in tests, and by four refusal probes
  (phrase-only, env-only, and both SystemExit refusal subprocesses).
- **Dry-run hygiene**: independent synthetic-arm re-run with a 22-key leak
  scan: zero findings, byte-identical x2, scored=false, no metrics key.
  Evidence file: 6/6 arms PASS, zero leak findings.
- **Void artifact: judged HONEST (a), not a rescue** — environmental
  union-calendar holiday artifact, uniform rule written before any scored PnL,
  disclosed per handbook §24, floors still bind. A7 measured the grid: 80
  decisions → 78 scored; the fold-3 void (2025-02-14 → fill 2025-02-17, union
  via 9 names) is exercised in the passing run. Caveats recorded (LOW-1):
  unpinned by fixtures, void-decision counts not broken out in the evidence,
  and a scored-phase unattributed-pnl window (~21 sessions per void) that must
  be disclosed at terminal.
- **Boundaries**: no push (branch absent on origin), `.staging_sec_v10/`
  gitignored (check-ignore verified), staged-by-name commits, zero key hits,
  S1 untouched. Denominators consistent (0/6, stocks 30/30, survivors 0).

## Why refused (HIGH findings)

1. **HIGH-1 — D2 `wc_stock_intensity` veto never measured.** `veto_ratio`
   passes the WC field *tuple* to `asof` before the tuple unpack → dead code →
   `n_per_veto = 0` / rho null for **all six proposals** in the published
   artifact, and `novelty_pass_le_020` treats the unmeasured entry as PASS
   (fail-open). The fields exist in the panel (124,233 `AssetsCurrent` rows),
   so the veto was computable. Both SELECTED families carry a "nine-entry
   novelty PASS" that covers only 8/9 entries.
2. **HIGH-2 — D2 `depletion_interaction` veto measured on the wrong feature.**
   The flow branch hardcodes AR/INV/AP legs and never reads `num_f`, so the
   published "depletion_interaction" rho is an accrual-flow-minus-cash proxy —
   `RetainedEarnings` (the depletion ancestor's defining field) is never read.

MEDIUM-1: no fixture test discriminates the month-bucket cohort rule.
MEDIUM-2: D2 measured A4-H1 on a mean-over-window proxy of the frozen
exposure. LOW-1..4: void caveats, tie-average convention, one pre-existing
environmental test failure (missing deleted V2 worktree file; fails identically
at the V9 base; 62/62 V10-relevant tests pass), D2 date-set convention.

## Path forward

A1: fix `veto_ratio`, re-run D2 against the frozen exposure definitions,
re-publish the audit, re-apply the selection rubric, re-freeze only if all
verdicts hold, pin the month-bucket fixture — then re-dispatch fresh-context
A7. Neither launch key may turn before that.
