# I-A8 handoff: family SFV3-A5-IDIO-SHOCK-REVERSAL (STOCKS-FREE-V3)

- role: A8 (isolated implementation lane, family 1)
- worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v3/i-a8-family-1`
- branch: `orca/stocks-free-v3-i-a8-family-1`
- HEAD verified at start: `e2d7241151966b863233cc3bab4ad8593f457a87` (= STOCKS_FREE_V3_SELECTION_SHA)
- contract: `research/control/stocks_free_v3_run/selection_freeze.json` families[0]
  + `research/proposals/stocks_free_v3/a5_family_idio_shock_reversal.md`,
  with adjudication **ADJ-1-EXEC-CLOCK** applied: decision at the close of
  completed session `t`, **fills at the CLOSE of `t+1`** (not the proposal's
  original open), hold close-to-close (exit fill at close of `entry+hold`),
  same-close switch allowed when both orders were decided at earlier closes.
- deviations from the freeze: **none**.

## What was built

`research/stocks_free_v3/family_idio_shock/`:

| file | contents |
|---|---|
| `features.py` | PIT features: trailing-60-session OLS beta of issuer-TR(i) on issuer-TR(SPY), window `[t-59..t]` inclusive of `t`; residuals `r_i - beta*r_SPY`; sigma = population std (ddof=0); `z = today's residual / sigma`. Fixed-order `math.fsum` reductions so identical inputs are bit-identical everywhere. |
| `arms.py` | The three stable frozen heads **A1** (z<=-3.0, smallest z, hold 5), **N1** (identical, hold 10), **C1** (z>=+3.0, largest z, hold 5), all 0.5 gross + 0.5 explicit CASH, budget 5 new entries / rolling 252 sessions, concurrency 1, tie -> alphabetically first symbol; sha256 config digests over the canonical JSON of the complete frozen payload (clocks and the verbatim constant-scale `vol_scaling_rule` included). |
| `schedule.py` | Deterministic trigger/selection/budget/concurrency state machine emitting the canonical target-weight SCHEDULE — ascending `{entry_type, fill_date, targets (explicit CASH leg), cash_weight, turnover_one_way, kind, decision_date, symbol, z_at_decision, episode}` records, consumed unchanged by `research/assets/stocks/factory.py::value_book` and the V2 harness. Plus schedule-only feasibility: entries/yr, gross check, two-way turnover/yr vs the frozen 6.0x/yr ceiling. No PnL anywhere. |
| `dryrun.py` | Exact-arm dry-run: schedule build -> canonical `factory.value_book` accounting -> `factory.assert_reconciles` (bookkeeping identity) -> `GatedTrialLedger` publication gate on a TEMP ledger, default **NO-PUBLISH** (`--publish-to-temp-ledger` publishes into the temp ledger only; always deleted). CLI: `python -m research.stocks_free_v3.family_idio_shock.dryrun --arm A1|N1|C1|ALL [--staging DIR]`. |

Tests: `tests/stocks_free_v3/family_idio_shock/` — hand-computed closed-form
fixtures on synthetic data, config digest goldens, schedule goldens
(switch / concurrency / budget / data-edge), double-generation equality, and
dry-run tests on synthetic data plus the REAL staged S0 snapshot (they RAN —
the staging directory is present).

## Arm config digests (sha256 over canonical JSON of the frozen config)

| arm | digest |
|---|---|
| `SFV3-A5-IDIO-SHOCK-REVERSAL-A1` | `c4c38f87c4b2cee68d88a9f949b4c2ed064b550a92e89d49d13a5b9a77e5f64c` |
| `SFV3-A5-IDIO-SHOCK-REVERSAL-N1` | `a8265f8c1572cf39b0ccf7683737c0ee9979a723d424af91451374923144cc2f` |
| `SFV3-A5-IDIO-SHOCK-REVERSAL-C1` | `5a07f804fbccadf98065e3084c662f8f9eabb2e52f9b68a5fd729a6e6fef1617` |

## Test evidence (interpreter: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`)

- `pytest tests/stocks_free_v3/family_idio_shock -q` → **42 passed**
- `pytest tests/stocks_free_v3 -q` → **224 passed** (no failures; the
  real-staged-data tests ran, they were not skipped)
- `python -m compileall -q research/stocks_free_v3` → OK
- `git diff --check` → clean

Hand-computed fixture derivation (conftest): SPY follows a period-4 cycle
`(+a, -a, 0, 0)`, `a=0.001`; every 60-session window then has mean 0 and
`sum(x^2)=30a^2`; shocked sectors are perfect `2x` fits except on their shock
day (placed on `r_SPY=0` positions). Closed forms: single shock → **beta
exactly 2**, `sigma = S*sqrt(59)/60`, `z = -60/sqrt(59) = -7.8138`; two equal
shocks in one window → `sigma = S*sqrt(29)/30`, `z = -30/sqrt(29) = -5.5707`.
Tests assert which session triggers, which arm holds what, fill dates,
weights and turnovers — never a scored PnL.

## Schedule-only feasibility on the REAL staged snapshot (S0 only)

Data: read-only, S0 window **2018-04-04..2025-07-31**, **1842 sessions**
(7.3095 years), through `SealedSnapshotReader`; distributions truncated to
pre-S1 dates before use; the pinned 2025-12-05 split factors never apply
inside S0. Canonical valuation accounting reconciles for all three arms
(bookkeeping identity only).

| | A1 | N1 | C1 |
|---|---|---|---|
| triggers observed | 68 | 68 | 57 |
| entries committed | 31 | 30 | 29 |
| entries / yr | 4.241 | 4.104 | 3.967 |
| same-close switches | 2 | 0 | 0 |
| budget rejections | 26 | 19 | 17 |
| concurrency blocks | 11 | 19 | 11 |
| fill records | 60 | 60 | 58 |
| max gross observed | 0.5 | 0.5 | 0.5 |
| turnover two-way / yr | **4.241** | **4.104** | **3.967** |
| within 6.0x/yr ceiling | yes | yes | yes |

Schedule digests (real S0): A1 `46389943f23a589a4c8b807de472599ef9ed00d69b5f133ee8e9d73814d699b1`,
N1 `7da3ee09e15f5b05362b52b4e0d34db822de318601408e7e7a5c04a914c835f0`,
C1 `b053efd7d1def97e3bbddd5adeee2ff7e3bf33e7e3997006e6de252fc01abd23`.

## Data-rule compliance

- **No S1 date was read**: every real read goes through
  `research.stocks_free_v3.isolation.SealedSnapshotReader` with
  `S0WindowPolicy`; tests assert no returned date >= 2025-08-01 and that an
  S1-bounded request raises `S1SealError`.
- **No scored metric was computed or persisted anywhere on real data**: the
  dry-run payload exposes only schedule counters, turnover/cost accounting
  facts and gate counters; a recursive key-scan test asserts no
  pnl/expectancy/profit-factor/sharpe/drawdown/equity-curve field exists.
- **No raw payload entered git** (synthetic fixtures only); the dry-run temp
  ledger is deleted after every run (`ledger_persisted_permanently: false`).

## Documented edge interpretations (not deviations)

1. `sigma == 0` → the frozen quantity `residual/sigma` does not exist; the
   session is never eligible to trigger (identical for all arms).
2. A trigger on the final session cannot fill (no `t+1`) and is dropped; a
   committed episode whose exit fill session does not exist in the window is
   closed by a terminal `FORCE_FLAT` at the last session (bookkeeping
   truncation at the data edge; the hold rule itself is never altered).
3. An exit and a new entry landing on the SAME fill session merge into one
   canonical record with the final targets and NET ETF-leg turnover —
   exactly the single fill `factory.value_book` charges (different-symbol
   switch books both legs = 1.0; same-symbol re-entry books 0.0).

## NOT_RUN

None. The scorer-facing incremental-alpha path
(`benchmarks.build_risk_matched_spy` + `incremental.compute_fold_alpha`) is
intentionally not exercised here — it is the scoring lane's job; the frozen
constant-scale rule is recorded verbatim in the arm configs
(`target_daily_vol: null`, `min_gross == max_gross`) without inventing a
numeric target vol.
