# I-A9 Handoff — Family SFV3-A6-TOM-SETTLE (STOCKS-FREE-V3, family 2)

Lane: A9 (isolated implementation lane, family 2). Worktree
`.worktrees/stocks-free-v3/i-a9-family-2`, branch
`orca/stocks-free-v3-i-a9-family-2`, base `e2d7241151966b863233cc3bab4ad8593f457a87`
(verified == the `STOCKS_FREE_V3_SELECTION_SHA` expectation before any write).
Contract sources: `research/control/stocks_free_v3_run/selection_freeze.json`
(`families[1]`) — executable contract; `research/proposals/stocks_free_v3/a6_family_SFV3-A6-TOM-SETTLE.md`
— mechanism source. Machine-readable twin: `i_a9_handoff.json` (same directory).

## 1. What was built

`research/stocks_free_v3/family_tom_settle/` — configuration and schedule only:
no data access, no disk writes, no network, and **no PnL / scored metric of
any kind** in the module.

- `config.py` — the three frozen arm heads `A` / `N` / `C`
  (`SFV3-A6-TOM-SETTLE-{A,N,C}`): anchor window = last 3 regular sessions of
  month M + first 2 of M+1; neighbour window = first 3 regular sessions of M;
  causal negative control window = regular-session ordinals 8–12 of each
  month. Two frozen books: TOM = 11 cohort ETFs at `0.50/11` each (gross
  0.50), BASE = 11 at `0.30/11` (gross 0.30); CASH is the explicit residual
  leg (1 − gross), never a tradable leg. Clock: decision at the close of
  completed session T for the fill at the close of T+1 (canonical close-fill;
  fill day earns no same-day return on new weights). Shared costs 10/20 bps
  per side; the frozen ex-ante risk-matched rule
  (`VolScalingRule(63, 0.005, 0.30, 0.50)`) is reused from
  `research.stocks_free_v3.benchmarks`. Window SHAPES are frozen constants —
  any reshape is rejected at construction, not approximated.
- `schedule.py` — regular-session month ordinals
  (`SessionOrdinal`: month key, 1-based ordinal, month length; holiday-thinned
  months handled with no special cases; fail-closed below 8 sessions/month,
  real US months are 19–23), window membership per arm, and deterministic
  target-book emission `(fill_session, targets_with_explicit_CASH,
  turnover_one_way)` via **two independent code paths** (session walk vs.
  window blocks) that must agree byte-identically. No intra-window
  re-equalization; windows straddling fold/purge boundaries simply lose those
  scored sessions — the schedule makes no compensation trades.
- `dryrun.py` — the exact-arm dry run: double-generation schedule build +
  canonical `research.assets.stocks.factory.value_book` accounting +
  `factory.assert_reconciles` + the `GatedTrialLedger` publication gate on a
  **caller-owned temporary ledger**. Valuation numbers are consumed internally
  by the reconciliation assert and are structurally absent from every returned
  payload, ledger artifact and audit file (pinned by payload-walking tests).

Tests: `tests/stocks_free_v3/family_tom_settle/` (10 files), including
`_staging.py`, the READ-ONLY, pin-verified, S0-truncated staging accessor.

## 2. Arm config digests (sha256 over canonical JSON of the frozen config)

| Arm | Digest |
|---|---|
| `SFV3-A6-TOM-SETTLE-A` | `e8e5b5c0f1b44360b36790bf3a7a04358ba1c7943f3824c534da07ed4513ee6f` |
| `SFV3-A6-TOM-SETTLE-N` | `e0afac4ab7c615319e2a6943380eaea4a38efb3cd4255fe0630442bc93c7a5f4` |
| `SFV3-A6-TOM-SETTLE-C` | `f57b5580d2699a84c3ed9afbc888c7abea6f70d8ef4602a95f59660691e1bd58` |

The three literals are pinned in `test_config_digests.py::PINNED_DIGESTS`; any
change to a frozen constant breaks the suite.

## 3. Hand-computed fixtures (synthetic calendars)

Primary fixture: Jan + Feb 2021, 19 regular sessions each (MLK 01-18 and
Presidents' Day 02-15 removed). Every window session and every fill is
hand-computed and asserted exactly, e.g. anchor arm fills: establishment TOM
@01-04 (0.50 from the implicit all-CASH book), BASE @01-06 (decided 01-05),
TOM @01-27 (decided 01-26), BASE @02-03 (decided 02-02), TOM @02-24 (decided
02-23); coverage ends 02-26 inside the February window → no exit fill, no
compensation trade. The control window shows the holiday shift explicitly
(Jan ordinals 8–12 = 01-13/14/15/19/20; Feb = 02-10/11/12/16/17) and the
frozen calendar's special closures are exercised on real data (Dec 2018
national-mourning closure moves the neighbour exit to 2018-12-07).

## 4. Double-generation equality

`build_schedule` (session walk) and `build_schedule_from_windows` (window
blocks) produce byte-identical canonical JSON, schedule digests, window
session tuples and fill tuples on: hand months, padded synthetic years,
holiday-thinned multi-year synthetic calendars, boundary slices, and the real
S0 calendar — pinned per arm.

## 5. Schedule-only feasibility (real frozen calendar, no prices touched)

S0 span 2018-04-04..2025-07-31, 1842 regular sessions, 88 months (19–23
sessions each; all 88 months qualify for the disjointness check, 0 skipped).

| Arm | Fills | Transitions | Window sessions | Complete years | Transitions/yr | Two-way/yr | Gross envelope |
|---|---|---|---|---|---|---|---|
| A | 177 | 176 | 440 | 2019–2024 | 24 every year | 4.80 every year | [0.30, 0.50] |
| N | 176 | 175 | 264 | 2019–2024 | 24 every year | 4.80 every year | [0.30, 0.50] |
| C | 177 | 176 | 440 | 2019–2024 | 24 every year | 4.80 every year | [0.30, 0.50] |

Inside the 6.0x two-way ceiling with margin, exactly as the proposal's frozen
arithmetic (24 transitions × |Δgross| 0.20 = 4.80). Anchor and control
windows are disjoint on every S0 month (guarantee holds for month length
≥ 15; every real month has 19–23 sessions).

S0 schedule digests (full-span coverage above): A
`7018cc2d715237649e647f85d030b19f12eec517acb534a9cbf08658696e5a73`, N
`246675369250c7551867bcf9a1c49c73eb7bc125f19e7b17571e022b67662c55`, C
`064b206b6d8e3d46c2bdf4470040d54006567f2ede6c1559c10b3e4da99c6f46`.

## 6. Real staged data dry run (schedule + valuation only)

Staging root (READ-ONLY, outside git): the V2 `.staging` directory. Inputs:
11 pinned `<SYM>_none_p1.json` raw-close files (sha256-verified, then
S0-truncated through `SealedSnapshotReader` with the frozen `S1Seal` +
`S0WindowPolicy`); the pinned SPDR issuer distributions workbook
(sha256 == `ISSUER_DISTRIBUTION_RECORDS_SHA256` verified before parsing,
cohort-only, ex-dates truncated to S0); the five pinned 2025-12-05 2:1 split
events (committed constants, not reads). Dry-run coverage: one padded
complete calendar year, 2018-12-03..2019-12-31 (271 sessions). In-year 2019:
24 transitions (12 entries + 12 exits), one-way turnover sum 4.80, for every
arm; boundary transitions over the padded coverage: A 26, N 25, C 26.

Each dry run: double-generation equality, canonical `value_book` accounting
with attribution identity reconciled (≤ 1e-12) and cost charged exactly once,
hand-computed zero-return cost chain matched exactly on synthetic data, and
the publication gate semantics verified (compute recorded once → first
publication → idempotent replay zero-delta → zero-result refusal path). The
`GatedTrialLedger` lived under pytest's `tmp_path`, was saved, asserted to
exist, **deleted, and asserted gone**.

## 7. Discipline statements

- **No scored metric was computed or persisted.** No PnL / expectancy / PF /
  Sharpe / MDD / alpha table exists anywhere in this lane, on synthetic or
  real data; the dry-run publication artifacts carry schedule facts and
  digests only; the ledger was temporary and deleted.
- **No S1 date was read.** All reads pass the frozen `S1Seal` (path- and
  date-level) and `S0WindowPolicy`; valuation window ends 2019-12-31; S0
  truncation of closes and distributions is asserted by test; split factors
  are committed constants.
- **No raw data in git.** The module is calendar arithmetic and configuration
  only; the only real-data access lives in the test package and touches the
  read-only staging outside the worktree.

## 8. Test evidence (gates, run from the worktree)

- `python -m pytest tests/stocks_free_v3/family_tom_settle -q` → **79 passed,
  3 skipped** (the only skips are 3 intentional short-slice parameters below
  the frozen 8-session month minimum), ~2 s.
- `python -m pytest tests/stocks_free_v3 -q` → **261 passed, 3 skipped**, ~6 s.
- `python -m compileall -q research/stocks_free_v3` → OK.
- `git diff --check` → clean; tree clean after tests.

## 9. Deviations

**None.** The freeze has no defect; nothing required interpretation beyond
two documented, strictly-in-contract choices: (i) the establishment fill at
the first coverage session is bookkeeping and is excluded from the 24
transitions/yr and turnover rates (the proposal's 24/yr counts window
entries + exits); (ii) a mid-month control window is the intersection of
ordinals 8–12 with the month's sessions — unreachable on real months
(19–23 sessions) and deterministic by construction.

## 10. NOT_RUN

None. The staged snapshot was present, so the real-data schedule-only
feasibility and exact-arm dry runs executed and passed.
