# FIRST REPORT — A1 STOCKS-FREE-V10 (PLAN_stocks_v10 §5)

measured_at_utc: 2026-09-05T23:30:12Z

## 1. Checkout (measured)

```
root        /Users/hoangminhlong/my-quantitative
branch      main
HEAD        9d16400a78a5207d427472fe64a1b6eb30b3cd71
porcelain   ?? .v2c/                     (OWNER_CHANGE — preserved, never staged)
worktrees   no stocks-free-v10 worktree existed before bootstrap (measured)
branches    no orca/stocks-free-v10* branch existed before bootstrap (measured)
V9 branch   orca/stocks-free-v9-integration @ 3a616380919cd66d1543231613295566423c8b79
```

Bootstrap (pwd measured immediately before `git worktree add`):

```
.worktrees/stocks-free-v10/integration
branch orca/stocks-free-v10-integration
HEAD   3a616380919cd66d1543231613295566423c8b79   (= V9 terminal, plan §0 frozen start)
porcelain clean
```

## 2. V9 terminal + A7 chain — VERIFIED

- terminal_report.json: `STOCKS_FREE_V9_REJECT_ALL`, closed 2026-09-05T21:31:22Z,
  A7 terminal `7/7 PASS`, 5 LOW verdict-neutral; reproduction byte-equal
  235/235 fields from detached twin `8702e5d`.
- audits/a7_prelaunch_v9.json verdict: `STOCKS_FREE_V9_S0_LAUNCH_AUTHORIZED`.
- audits/a7_terminal_v9.json verdict: `STOCKS_FREE_V9_REJECT_ALL_CONFIRMED`.
- stocks program: 30 observed / 30 published; V9 budget 3/6 (three slots died
  unused, never reassigned — dead forever per plan §1); S1 `SEALED_UNTOUCHED`;
  survivors 0; deployment NO_PAPER_NO_LIVE_NO_ORDERS.
- MAP.md and HYPOTHESIS_LEDGER.md agree with the terminal at intake
  (program-wide 197/200 read from the ledger per P-9).

## 3. Death-inclusive durable assets — re-hashed before use

| asset | measured sha256 (2026-09-06) | pin | verdict |
|---|---|---|---|
| multivintage_panel.jsonl (1,488,738,771 B; 10,073,069 rows) | 67591464ee49acc159886143a379bda5890b1df602818b600d7938df92af1447 | p0c_v9_panel_manifest.panel_out_sha256 | MATCH |
| eodhd_us_delisted.json (59,923 symbols) | bd7d969cf1ff00c1aa81e42ccccb71ef5d7ced3c9bbb4a3c38cf1e8f4792d06b | p0b_v9_delisted_cache_manifest.sha256 | MATCH |
| death_census.json | 7a993b3698e68dce301eef17879ea43a947d52dc9e1fe6dff6ed7c5278b26e51 | first pin (no prior pin existed) | RECORDED |
| cohort_v9.json | 6a95401ff84bff2144ac3c0b9426a6fa86daf3dde8d478195666249e3fa2aa62 | first pin (no prior pin existed) | RECORDED |

## 4. Timing/revision observable coverage pre-check (fundable clocks)

Method: single streaming pass over the hash-verified panel
(evidence: /tmp/stocks_v10_precheck_groups.json, mirrored into the P0
manifest when published). Counting only — no proposal, no PnL.

```
panel rows                        10,073,069
distinct filers (e)                    2,162
  alive-in-panel                         410   (= frozen V8 panel, 100%)
  dead-in-panel                        1,752   (of 1,769 dead census filers;
                                                17 carry zero panel rows —
                                                recorded, P0 census reconciles)
  gap-in-panel                             0
distinct fields (f)                    6,422
filer-field-period groups          5,453,478

TIMING observables
  filing lag = min(avail) - eff   measured on every group
  negative lags                            0   (PIT ordering clean)
  lag p05/p25/p50/p75/p95             26/35/40/58/232 days
  filers with >=2 same-type prior
    periods (own seasonal norm)         2,158
  filers with >=4 same-type prior
    periods (own seasonal norm)         2,008   (92.9% of panel filers)
  per-filer-period cells with >=2
    own-history                      5,446,114 of 5,453,478 (99.9%)

REVISION observables
  groups with >=2 vintages         1,667,422  (30.6%)
  groups whose value actually
    changed between first/last
    vintage                          147,512   (revision content exists)
  filers with >=1 revision group        2,156   (99.7%)
  top revised fields: Cash&Equivalents, StockholdersEquity, Assets,
    LiabilitiesAndStockholdersEquity, RetainedEarnings (restatement-shaped)
```

Verdict: **both axes FUNDABLE** on the death-inclusive cohort — the plan's
`BLOCKED_DATA` branch does not trigger at pre-check. Deadline-distance needs
sourced filer-category evidence that staged data does not carry — P0 census
will record it `DATA_BLOCKED_VALID` unless evidenced, never asserted.

## 5. GO/NO_GO for P0

**GO.** All pre-check gates pass with margin; worktree bootstrapped at the
frozen V9 terminal; heavy cap 1 honored (panel hash, then panel stream,
serialized).
